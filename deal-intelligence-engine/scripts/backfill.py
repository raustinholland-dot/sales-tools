"""
Historical Backfill Script — Clearwater Deal Intelligence Engine

Ingests historical deal content in chronological batches, scoring after
each batch to build a real score progression over time.

Usage:
    python3 scripts/backfill.py --deal velentium              # full run
    python3 scripts/backfill.py --deal velentium --dry-run    # parse only, no writes

What it does:
1. Reads all files from backfill/<deal>/
2. Extracts dates from content/filenames
3. Sorts files chronologically
4. Splits into batches (one per unique date or weekly bucket)
5. For each batch:
   a. Chunk + embed via OpenAI
   b. Write vectors to Qdrant
   c. Write rows to Postgres ingestion_log
   d. Fire CW-02 webhook → wait 120s for scoring
   e. Print the resulting score
6. Outputs full score history at the end

Requirements:
    pip3 install openai psycopg2-binary qdrant-client python-dotenv requests
"""

import argparse
import hashlib
import os
import re
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Load env ─────────────────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
POSTGRES_HOST     = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT     = os.getenv("POSTGRES_PORT", "5433")
POSTGRES_DB       = os.getenv("POSTGRES_DB", "clearwater_deals")
POSTGRES_USER     = os.getenv("POSTGRES_USER", "clearwater")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
QDRANT_URL        = os.getenv("QDRANT_URL", "http://localhost:6333")
N8N_WEBHOOK_BASE  = os.getenv("N8N_WEBHOOK_BASE", "http://localhost:5678")

BACKFILL_DIR = Path(__file__).parent.parent / "backfill"
CHUNK_SIZE   = 400   # approximate tokens (words)
CHUNK_OVERLAP = 50
SCORE_WAIT_SECS = 120  # wait for CW-02 to finish scoring

# ── Deal config ───────────────────────────────────────────────────────────────
DEAL_CONFIG = {
    "velentium": {
        "deal_id": "cw_velentiummedical_2026",
        "company_name": "Velentium Medical",
        "sender_domain": "velentiummedical.com",
        "deal_stage": "Discover",
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + chunk_size]))
        i += chunk_size - overlap
    return chunks


def extract_date(text, filename):
    """Extract earliest date from content or filename. Returns datetime."""
    patterns = [
        (r'Date:\s+\w+,\s+(\w+ \d+,\s+\d{4})', "%B %d, %Y"),
        (r'Exported:\s+(\d{4}-\d{2}-\d{2})',     "%Y-%m-%d"),
        (r'(\d{4}-\d{2}-\d{2})',                  "%Y-%m-%d"),
        (r'(\w+ \d{1,2},\s+\d{4})',               "%B %d, %Y"),
    ]
    for pattern, fmt in patterns:
        m = re.search(pattern, text[:3000])
        if m:
            try:
                return datetime.strptime(m.group(1).strip(), fmt)
            except ValueError:
                continue
    # Try filename
    m = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now() - timedelta(days=30)


def detect_doc_type(filename, text):
    fn = filename.lower()
    if "transcript" in fn or "call" in fn:
        return "call_transcript"
    if "email" in fn or "from:" in text[:200].lower():
        return "email_thread"
    if "gemini" in fn:
        return "gemini_chat"
    if fn.endswith(".pdf"):
        return "pdf"
    if fn.endswith(".pptx"):
        return "presentation"
    return "document"


def embed_texts(texts):
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [item.embedding for item in response.data]


def write_to_qdrant(deal_config, chunks_with_embeddings):
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    client = QdrantClient(url=QDRANT_URL, check_compatibility=False)
    points = []
    for item in chunks_with_embeddings:
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=item["embedding"],
            payload={
                "deal_id":                deal_config["deal_id"],
                "company_name":           deal_config["company_name"],
                "sender_domain":          deal_config["sender_domain"],
                "deal_stage":             deal_config["deal_stage"],
                "doc_type":               item["doc_type"],
                "date_created":           item["date"].isoformat(),
                "chunk_index":            item["chunk_index"],
                "attribution_confidence": "high",
                "source_file":            item["filename"],
                "text":                   item["text"],
            }
        ))
    if points:
        client.upsert(collection_name="deals", points=points)
    return len(points)


def write_to_postgres(deal_config, file_rows):
    import psycopg2
    conn = psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD
    )
    cur = conn.cursor()
    # Ensure deal record exists
    cur.execute("""
        INSERT INTO deals (deal_id, company_name, sender_domains, deal_stage, is_active)
        VALUES (%s, %s, %s::text[], %s, true)
        ON CONFLICT (deal_id) DO NOTHING
    """, (deal_config["deal_id"], deal_config["company_name"],
          "{" + deal_config["sender_domain"] + "}", deal_config["deal_stage"]))

    for row in file_rows:
        msg_id = hashlib.md5(
            f"{deal_config['deal_id']}_{row['filename']}_{row['chunk_index']}".encode()
        ).hexdigest()
        cur.execute("""
            INSERT INTO ingestion_log
                (message_id, deal_id, doc_type, sender_domain,
                 attribution_confidence, attribution_status,
                 subject, qdrant_namespace, chunk_count)
            VALUES (%s, %s, %s, %s, 'high', 'confirmed', %s, %s, 1)
            ON CONFLICT (message_id) DO NOTHING
        """, (msg_id, deal_config["deal_id"], row["doc_type"],
              deal_config["sender_domain"],
              row["filename"],
              deal_config["deal_id"]))
    conn.commit()
    cur.close()
    conn.close()


def fire_cw02(deal_id, batch_label):
    url = f"{N8N_WEBHOOK_BASE}/webhook/deal-health-trigger"
    try:
        requests.post(url, json={"deal_id": deal_id, "trigger_type": "backfill",
                                 "batch_label": batch_label}, timeout=5)
    except requests.exceptions.Timeout:
        pass  # fire-and-forget


def fetch_latest_score(deal_id):
    """Query Postgres for the most recent deal_health row."""
    import psycopg2
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST, port=POSTGRES_PORT,
            dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT p2v2c2_total, pain_score, power_score, vision_score,
                   value_score, change_score, control_score,
                   critical_activity_stage, scored_at
            FROM deal_health
            WHERE deal_id = %s
            ORDER BY scored_at DESC
            LIMIT 1
        """, (deal_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception as e:
        print(f"  ⚠️  Could not fetch score: {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deal", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    deal_name = args.deal.lower()
    if deal_name not in DEAL_CONFIG:
        print(f"Unknown deal '{deal_name}'. Available: {list(DEAL_CONFIG.keys())}")
        sys.exit(1)

    deal_config = DEAL_CONFIG[deal_name]
    deal_dir = BACKFILL_DIR / deal_name

    files = sorted([f for f in deal_dir.iterdir()
                    if f.is_file() and f.suffix in {".txt", ".pdf", ".pptx", ".csv"}
                    and not f.name.startswith(".")])

    if not files:
        print(f"No files in {deal_dir}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Backfill: {deal_config['company_name']}")
    print(f"Files: {len(files)}")
    print(f"{'='*60}\n")

    # ── Step 1: Parse all files, extract dates ────────────────────────────────
    parsed = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        text = text.replace('\u2028', '\n').replace('\u2029', '\n')
        date = extract_date(text, f.name)
        doc_type = detect_doc_type(f.name, text)
        parsed.append({"file": f, "text": text, "date": date, "doc_type": doc_type})
        print(f"  {f.name:30s} → {doc_type:20s} | {date.strftime('%Y-%m-%d')}")

    # ── Step 2: Sort chronologically ─────────────────────────────────────────
    parsed.sort(key=lambda x: x["date"])

    # ── Step 3: Group into batches (one per file, sorted by date) ────────────
    # Each file is its own batch — score after each one for maximum granularity
    batches = [(p["date"].strftime("%Y-%m-%d") + f"_{p['doc_type']}", [p])
               for p in parsed]

    print(f"\nBatches (score after each):")
    for label, items in batches:
        print(f"  {label}: {len(items)} file(s)")

    if args.dry_run:
        print("\nDry run complete — no writes.")
        return

    # ── Step 4: Process each batch ────────────────────────────────────────────
    score_history = []

    for batch_idx, (batch_label, batch_files) in enumerate(batches):
        print(f"\n{'─'*60}")
        print(f"Batch {batch_idx+1}/{len(batches)}: {batch_label}")
        print(f"{'─'*60}")

        # Build chunks for this batch
        all_chunks = []
        for item in batch_files:
            context_header = (
                f"[DEAL CONTEXT]\n"
                f"Deal: {deal_config['company_name']} (ID: {deal_config['deal_id']})\n"
                f"Document Type: {item['doc_type']}\n"
                f"Date: {item['date'].strftime('%Y-%m-%d')}\n"
                f"Source File: {item['file'].name}\n"
                f"[END CONTEXT]\n\n"
            )
            chunks = chunk_text(item["text"])
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": context_header + chunk,
                    "date": item["date"],
                    "doc_type": item["doc_type"],
                    "filename": item["file"].name,
                    "chunk_index": i,
                })

        print(f"  Chunks: {len(all_chunks)}")

        # Embed
        print(f"  Embedding...")
        texts = [c["text"] for c in all_chunks]
        embeddings = []
        for i in range(0, len(texts), 100):
            batch_texts = texts[i:i+100]
            embeddings.extend(embed_texts(batch_texts))
            time.sleep(0.3)

        for i, emb in enumerate(embeddings):
            all_chunks[i]["embedding"] = emb

        # Write to Qdrant
        print(f"  Writing to Qdrant...")
        n = write_to_qdrant(deal_config, all_chunks)
        print(f"  ✅ {n} vectors")

        # Write to Postgres
        print(f"  Writing to Postgres...")
        write_to_postgres(deal_config, all_chunks)
        print(f"  ✅ ingestion_log updated")

        # Fire CW-02
        print(f"  Firing CW-02 health scoring...")
        fire_cw02(deal_config["deal_id"], batch_label)

        # Wait for scoring to complete
        print(f"  Waiting {SCORE_WAIT_SECS}s for CW-02 to score...", end="", flush=True)
        for _ in range(SCORE_WAIT_SECS // 10):
            time.sleep(10)
            print(".", end="", flush=True)
        print()

        # Fetch result
        row = fetch_latest_score(deal_config["deal_id"])
        if row:
            total, pain, power, vision, value, change, control, cas, scored_at = row
            print(f"\n  Score: {total}/30  CAS: {cas}")
            print(f"  P={pain} Po={power} V={vision} Va={value} Ch={change} Co={control}")
            score_history.append({
                "batch": batch_label,
                "total": total, "cas": cas,
                "pain": pain, "power": power, "vision": vision,
                "value": value, "change": change, "control": control,
            })
        else:
            print(f"  ⚠️  No score found yet (CW-02 may still be running)")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"SCORE HISTORY — {deal_config['company_name']}")
    print(f"{'='*60}")
    for s in score_history:
        print(f"  {s['batch']:45s} → {s['total']:2d}/30  CAS: {s['cas']}")
    print()


if __name__ == "__main__":
    main()
