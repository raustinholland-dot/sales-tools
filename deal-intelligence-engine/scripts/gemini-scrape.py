"""
Gemini Conversation Scraper (Playwright)

Scrapes Gemini conversations using your existing Chrome profile (already logged in).
Saves each conversation as a .txt file in the backfill folder.

Usage:
    python3 scripts/gemini-scrape.py

Requirements:
    pip3 install playwright
    python3 -m playwright install chromium
"""

import asyncio
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright

# ── CONFIG ──────────────────────────────────────────────────────────────────

CONVERSATIONS = [
    {
        "url": "https://gemini.google.com/app/831d8ced4f32efee",
        "filename": "gemini-02.txt"
    },
    {
        "url": "https://gemini.google.com/app/1511a5c57246b9f8",
        "filename": "gemini-01.txt"  # already have this one, will overwrite with full version
    },
]

OUTPUT_DIR = Path(__file__).parent.parent / "backfill" / "velentium"

# Your Chrome profile path (already logged into Google)
CHROME_USER_DATA = os.path.expanduser("~/Library/Application Support/Google/Chrome")
CHROME_PROFILE = "Default"  # change to "Profile 1" etc. if needed

# ── EXTRACTION SCRIPT (injected into page) ──────────────────────────────────

EXTRACT_JS = """
async function extract() {
  // Scroll to top to trigger lazy loading
  const scrollContainer =
    document.querySelector('[data-test-id="chat-history-container"]') ||
    document.querySelector('chat-window') ||
    document.querySelector('main') ||
    document.documentElement;

  scrollContainer.scrollTop = 0;
  window.scrollTo(0, 0);

  // Wait for lazy load spinner to clear
  await new Promise(resolve => {
    let stable = 0;
    const check = () => {
      const spinner = document.querySelector('mat-progress-bar.mdc-linear-progress--indeterminate');
      if (spinner) { stable = 0; setTimeout(check, 300); }
      else { stable++; if (stable >= 5) resolve(); else setTimeout(check, 300); }
    };
    setTimeout(check, 800);
  });

  const turns = document.querySelectorAll('user-query, model-response');
  if (!turns.length) return null;

  const title = document.title.replace(/^Gemini\\s*[-–]\\s*/i, '').trim() || 'untitled';
  const url = window.location.href;
  const date = new Date().toISOString().split('T')[0];

  const lines = [
    'GEMINI CONVERSATION EXPORT',
    'Title: ' + title,
    'Exported: ' + date,
    'URL: ' + url,
    'Turns: ' + turns.length,
    '='.repeat(60),
    ''
  ];

  let count = 0;
  for (const turn of turns) {
    const tag = turn.tagName.toLowerCase();
    if (tag === 'user-query') {
      const el = turn.querySelector('div.query-content') ||
                 turn.querySelector('.query-text') || turn;
      const text = el.innerText.trim();
      if (text) { lines.push('--- AUSTIN ---'); lines.push(text); lines.push(''); count++; }
    } else if (tag === 'model-response') {
      const el = turn.querySelector('message-content .markdown') ||
                 turn.querySelector('message-content') || turn;
      const text = el.innerText.trim();
      if (text) { lines.push('--- GEMINI ---'); lines.push(text); lines.push(''); count++; }
    }
  }

  lines.push('='.repeat(60));
  lines.push('END OF EXPORT — ' + count + ' message turns captured');
  return lines.join('\\n');
}
return extract();
"""

# ── MAIN ────────────────────────────────────────────────────────────────────

async def scrape():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        # Copy Chrome profile to a temp dir so we can open it while Chrome is running
        import shutil, tempfile
        tmp_profile = tempfile.mkdtemp(prefix="gemini_scrape_")
        src_profile = os.path.join(CHROME_USER_DATA, CHROME_PROFILE)
        dst_profile = os.path.join(tmp_profile, CHROME_PROFILE)
        print(f"Copying Chrome profile to temp dir (this takes ~30s)...")
        shutil.copytree(src_profile, dst_profile, ignore_dangling_symlinks=True)

        print(f"Launching Chrome...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=tmp_profile,
            channel="chrome",
            headless=False,
            args=["--profile-directory=" + CHROME_PROFILE],
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        for conv in CONVERSATIONS:
            url = conv["url"]
            filename = conv["filename"]
            output_path = OUTPUT_DIR / filename

            print(f"\nOpening: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for conversation to render
            print("  Waiting for conversation to load...")
            try:
                await page.wait_for_selector("user-query, model-response", timeout=15000)
            except Exception:
                print(f"  ⚠️  No messages found at {url} — skipping")
                continue

            # Give extra time for full render
            await asyncio.sleep(3)

            print("  Extracting conversation...")
            result = await page.evaluate(EXTRACT_JS)

            if not result:
                print(f"  ⚠️  Extraction returned empty — skipping")
                continue

            # Clean unusual line terminators
            result = result.replace('\u2028', '\n').replace('\u2029', '\n')

            output_path.write_text(result, encoding="utf-8")
            turn_count = result.count("--- AUSTIN ---") + result.count("--- GEMINI ---")
            print(f"  ✅ Saved {turn_count} turns → {output_path.name}")

            await asyncio.sleep(2)

        await browser.close()
        print(f"\nDone. Files saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    asyncio.run(scrape())
