# FEED-RULES.md — Capture + Triage + Compile

This file governs how feed channel inputs are handled. The wiki schema (`wiki-schema.md`) governs compilation details.

## Pipeline Orchestration

**The feed pipeline is orchestrated by `feed-pipeline.lobster`.** When a feed input arrives, invoke the Lobster tool to run the pipeline. Do not self-orchestrate the steps below — the Lobster workflow handles sequencing, file reading, and prompt injection. Your job within each Lobster step is to execute the creative work (compile, score, assess) with the context that has been provided to you.

All required prompt files (wiki-schema.md, scoring-prompt.md, scoring-methodology.md, scoring-services.md, needs-assessment-prompt.md) are read by the pipeline and injected into your context. Do not re-read files marked with `=== ... (MANDATORY) ===` delimiters — they are already loaded.

---

## Pipeline Steps (for reference)

### 1. DEDUP CHECK
- Hash the input, check `clearwater/feeds/.processed-inputs.jsonl`
- If duplicate → DM Austin "Already processed". Stop.

### 2. CAPTURE
- Append to `raw/YYYY-MM-DD.md` in this format:

```
---
[channel] HH:MM CT
from: [sender]
to: [recipient if applicable]
subject: [if email]
---

[full verbatim text — preserve everything including signatures, disclaimers, typos]
```

- Log hash to `.processed-inputs.jsonl`

### 3. TRIAGE
Classify the input:

**URGENT** if ANY of:
- Client or prospect asking a direct question or requesting action
- Meeting in less than 24 hours that needs prep
- Deal status change (budget approved, SOW signed, close, loss)
- Austin explicitly says "need this now" or "urgent"

**NORMAL** — everything else.

Also classify: is it a transcript? Does it update a deal?

### 4. NOTIFY
- DM Austin with capture acknowledgment
- Post initial entry to Ops Log

### 5. COMPILE
- wiki-schema.md content is injected by the pipeline — follow it exactly.
- Identify which wiki articles the input touches (check the index).
- Read those articles, update or create per the schema.
- Maintain bidirectional wikilinks and related fields.
- Update wiki/index.md.
- Prepend entry to wiki/log.md.

### 6. SCORE (if transcript)
- scoring-prompt.md, scoring-methodology.md, and scoring-services.md are injected by the pipeline.
- Apply P2V2C2 rubric, produce 12-element deal ledger.
- Write to scores.jsonl, DM Austin.

### 7. NEEDS ASSESSMENT (if deal article updated)
- needs-assessment-prompt.md is injected by the pipeline.
- Follow its analytical process, produce output if warranted.
- Also runs on cron (1-2x daily) and on explicit ask.

---

## Email Thread Parsing

When an email thread arrives:
1. Read the newest message first — that's usually the new information
2. Skip boilerplate: signatures, disclaimers, legal footers, forwarding headers
3. Check wiki for existing deal/person articles before re-analyzing older messages in the thread
4. Only capture genuinely new information — don't re-capture what the wiki already knows

---

## What This File Does NOT Cover

- **Salesforce updates** — handled by the SF sync cron reading from the wiki
- **Verification** — the lint cron checks wiki integrity

The pipeline is: **capture → compile → (score if transcript) → (needs assessment if deal) → ops log**. This is orchestrated by `feed-pipeline.lobster`.
