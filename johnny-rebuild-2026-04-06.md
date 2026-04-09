# Johnny Forsyth System Rebuild — 2026-04-06

## Status: TESTED, ARCHITECTURE CONFIRMED WORKING

Built and deployed April 6, 2026. Tested with 6 real feed inputs on April 7, 2026. Last two runs scored 10/10. See "Testing Session Results (2026-04-07)" section at the bottom for full details.

---

## What Happened Tonight

### The Problem
Johnny's performance had been degrading for days. He was:
- Summarizing inputs instead of writing to permanent files
- Asking permission instead of acting
- Never delegating to sub-agents (Writer, Researcher, Meeting Prep)
- Not scoring P2V2C2 changes
- Not connecting dots across inputs
- Producing stale briefings that didn't reflect same-session updates
- Lecturing Austin ("don't let this slip again")
- Reading Richmond Donnelly's calendar data
- Calling David Kolb "Cobb" (hallucination sourced from USER.md)

### Root Causes Found
1. **Billing lockout** — Anthropic API key had 2,335 billing errors and was locally disabled. Johnny was stuck in a model-switching loop (Gemini Flash ↔ Sonnet) and couldn't process any messages.
2. **Wrong model** — Johnny was on `claude-sonnet-4-5`, not Opus 4.6.
3. **Session persistence** — `sessions.json` (not `.jsonl`) was caching the stuck session across gateway restarts.
4. **Vague instructions** — FEED-RULES said "consider" and "check if" instead of giving a rigid processing checklist.
5. **No verification** — no mechanism to confirm writes actually happened.
6. **No knowledge architecture** — daily logs accumulated without being processed into structured knowledge.
7. **Context bloat** — too many always-on files, stale data everywhere.

### What Was Fixed

**Infrastructure:**
- Cleared Anthropic billing disable flag (account refunded to $249.33)
- Set Johnny's model to `anthropic/claude-opus-4-6` in openclaw.json
- Set all sub-agents to `google/gemini-2.5-flash` as primary
- Deleted stuck sessions and `sessions.json`
- Added session idle reset at 5 minutes (`openclaw.json` → `session.reset.mode: "idle", idleMinutes: 5`)
- Removed 33 Richmond Donnelly calendar events from `calendar.json`
- Added Verifier sub-agent to `openclaw.json` agent list + main agent's `allowAgents`
- Fixed `auth-profiles.json` — added Anthropic provider to main agent's `models.json`
- Gateway running clean on Opus 4.6, PID confirmed, no model switch loop

**Architecture — Complete Rebuild of Context Files:**

| File | Location | What It Does |
|------|----------|-------------|
| SOUL.md | workspace/ | Identity, foundational write rule, bias to action, tone, boundaries |
| FEED-RULES.md | workspace/ | 6-step processing checklist, classification (deal/project/knowledge), Ops Log lifecycle, workspace structure, delegation, file size thresholds, complex transcript protocol, standing rules |
| AGENTS.md | workspace/ | Session startup (4 always-load files), sub-agent directory, delegation model with sequential flow diagram |
| HEARTBEAT.md | workspace/ | Cron schedules, briefing instructions (reads hot.md + index.md) |
| WRITER-RULES.md | ~/.openclaw/agents/writer/ | Formatting standards for deal-state, project-state, index, hot, knowledge docs. Voice/style rules. Document extraction. Outbound tracking schema. |
| VERIFIER-RULES.md | ~/.openclaw/agents/verifier/ | Audit criteria, verification process, output format (VERIFIED/FAILED/INPUT COMPLETE), failure alerting to Johnny Alerts, file size thresholds |
| index.md | clearwater/knowledge/ | Master navigation — all deals (with status), projects, key people, knowledge docs, reference files |
| hot.md | clearwater/knowledge/ | 500-word max current priorities cache — Urgent, This Week, Austin's Focus |
| project-state-template.md | clearwater/projects/ | Template for new internal projects |

**Files Updated:**
- USER.md — fixed "David Kolb (Cobb)" → "David Kolb"
- MEMORY.md — updated architecture section for new system, fixed brain dump path, updated stale deal intel, fixed model references

**Files Archived (in workspace/.archive/):**
IDENTITY.md, HANDOFF.md, JOHNNY-RECOVERY.md, NEXT-SESSION-PLAN.md, ROADMAP.md, STATE.md, KANBAN.md, RULES.md

**Files Remaining (unchanged, on-demand):**
- TOOLS.md — technical environment reference (Salesforce CLI, webhook server, pipeline server, etc.)
- USER.md — Austin's profile and preferences
- MEMORY.md — supplementary long-term state
- openclaw-brain-dump.md — legacy foundational context (28K words, never auto-loaded)

---

## The Architecture

### Processing Flow (Every Feed Input) — Updated 2026-04-07
```
Input arrives in feed channel
  ↓
Step 1: CLASSIFY + READ
  → Johnny classifies (deal / project / knowledge / multi-category)
  → Reads current state (deal-state, project-state, knowledge, outbound tracking)
  ↓
Step 2: RESCORE
  → Always run P2V2C2 scoring
  → If scores changed → write new scores
  → If scores same → log "no change"
  ↓
Step 3: BUNDLE + DISPATCH
  → ONE Writer spawn with everything bundled (capture + draft + tracking)
  → Researcher / Meeting Prep in parallel if needed
  → If Writer crashes → Johnny completes remaining writes, then continues pipeline
  ↓
Step 4: VERIFY (unconditional — always runs, no exceptions)
  → Verifier reads original input + Ops Log entries + actual files
  → Checks outbound-tracking.jsonl (every DRAFT must have entry)
  → Posts VERIFIED/FAILED to Ops Log
  → Posts INPUT COMPLETE
  → Forwards FAILED entries to Johnny Alerts
  ↓
Step 5: NOTIFY
  → Johnny DMs Austin with summary + inline work products
```

**Key principle:** No branching. Everything always runs. Every draft = outbound tracking entry.

### Workspace Structure
```
clearwater/
├── deals/           ← external deals (lifecycle: open → active → won/lost)
├── projects/        ← internal initiatives (lifecycle: started → in progress → complete)
├── knowledge/       ← persistent reference (no end date, compounds over time)
│   ├── index.md     ← master navigation — loaded every session
│   ├── hot.md       ← 500-word current priorities — loaded every session
│   └── [topic].md   ← flat, one per topic
├── feeds/
└── pipeline.json
```

### Session Startup (Every Session)
**Always load:** SOUL.md, FEED-RULES.md, index.md, hot.md
**On demand:** USER.md, deal-state files, project-state files, knowledge docs
**Legacy:** MEMORY.md, daily logs

### Delegation Model
- **Johnny (Opus 4.6):** classification, orchestration, P2V2C2 scoring decisions, cross-referencing, Ops Log planning, Austin notifications
- **Writer (Gemini 2.5 Pro):** all file writes + drafts. Loads WRITER-RULES.md.
- **Researcher (Gemini 2.5 Pro):** all research. Receives task brief per spawn.
- **Meeting Prep (Gemini 2.5 Pro):** all meeting prep. Receives task brief per spawn.
- **Verifier (Gemini 2.5 Pro):** post-processing verification. Loads VERIFIER-RULES.md. Checks original input against actual files.

### Three-Step Verification
1. Johnny plans (posts intended writes to Ops Log)
2. Writer executes (writes files per Johnny's instructions)
3. Verifier confirms (independently checks original input against actual files, flags failures to Johnny Alerts)

### Key Design Principles
- **"Every piece of information is written to its permanent location the moment it arrives."** — The foundational rule. If it's not written, the system degrades.
- **Bias to action** — Johnny drafts and presents results. Austin reviews outputs, not plans. Exception: closing deals or sending externally.
- **Positive framing** — SOUL.md describes what Johnny IS, not what he isn't.
- **Agent-specific context** — each agent loads only what it needs. Johnny gets decision logic, Writer gets formatting standards, Verifier gets audit criteria. Saves tokens, reduces confusion.
- **5-minute idle session reset** — every session starts fresh from files. Files are the memory, not conversation context.
- **Flat knowledge base** — one markdown file per topic, no nesting. Everything discoverable through index.md.
- **Projects have lifecycles** — separate from persistent knowledge. Like deals but for internal initiatives.

---

## Testing Plan

### What to Test
Send real feed inputs and evaluate Johnny's response against these criteria:

1. **Does he classify correctly?** (deal / project / knowledge / multi-category)
2. **Does he write everything?** (check Ops Log for WRITE entries, then check actual files)
3. **Does he spawn sub-agents?** (check Ops Log for SPAWN entries)
4. **Does the Verifier run?** (check Ops Log for VERIFIED/FAILED/INPUT COMPLETE)
5. **Does he present drafts inline?** (not "should I draft?" but actual drafts in DM)
6. **Does he connect dots across inputs?** (if Brian's email relates to David's Teams message, does he link them?)
7. **Does he update index.md and hot.md?** (check after each input)
8. **Does the briefing reflect current state?** (run Tomorrow's Briefing after processing inputs)

### Test Inputs — Rerun the Same Inputs from 4/6

Prompt Austin: "Let's rerun the same 5 inputs from last night so we can compare old vs new behavior."

**Input 1: Holistic Wellness email (Email Feed)**
Sarah Schulte missed the 4/3 call, asked if Austin is available at 12pm or 1pm CST.
- **Old behavior:** Johnny said "Already documented, recovery email drafted 4/5, awaiting Austin's send. No new action." Passive. No draft inline. No urgency framing.
- **Correct behavior:** Recognize this is 3 days cold. Present the recovery draft inline. Recommend sending immediately. Update deal-state Next Action. Flag urgency through facts. Spawn Writer for the draft.

**Input 2: Exer email from Brian Chao (Email Feed)**
Budget confirmed, requesting updated one-page pricing + KnowBe4 Aida demo/info.
- **Old behavior:** Good summary and energy detection. But asked "Want me to draft the reply or research KnowBe4 Aida first?" instead of doing both. No SPAWN entries. Told Austin to "pull the original proposal from SharePoint and get updated pricing from Carter."
- **Correct behavior:** Spawn Writer for reply draft (Johnny has the proposal in the deal folder now). Spawn Researcher for KnowBe4 Aida intel. Present both inline. Update deal-state (budget confirmed, status change). Update index.md and hot.md.

**Input 3: Exer proposal attachment (DM or Email Feed)**
The Clearwater-Exer_Urgent_CatchUp_Proposal_11.14.25.pptx file.
- **Old behavior:** Extracted and filed correctly. Good summary of key numbers. But responded in wrong channel (calendar feed instead of DM). Didn't connect it to Brian's email or proactively produce the pricing sheet Brian asked for.
- **Correct behavior:** Extract, file in deal folder, log to Ops Log. Immediately connect to Brian's email — "Now I have the pricing. Here's the updated one-page sheet Brian requested." Spawn Writer for the pricing sheet + reply draft. Update index.md with the reference doc.

**Input 4: David Kolb Teams message (Teams Feed)**
Three items: kill Dedicated Sleep, asking about Exer response, SCA Pharma NS→NC update.
- **Old behavior:** Good identification of all three deals. Connected the Exer dot (Brian responded today). But no SPAWN entries. Set Dedicated Sleep to "CLOSING" instead of asking Austin to confirm. Didn't translate "NS→NC." Told Austin what to do instead of doing it.
- **Correct behavior:** For each deal: update deal-state, spawn Writer for needed drafts. Dedicated Sleep: propose close with reason, ask Austin to confirm. Exer: flag that Brian responded with budget — fold into DK reply. SCA Pharma: update deal-state, translate abbreviations. Spawn Writer for reply to DK covering all three items + email to Shauna. Present everything inline.

**Input 5: Pipeline build transcript (Transcripts Feed)**
Long multi-speaker transcript covering PantherRx, Family Resource, Kane Capital, White Wilson, Nashville strategy, PE targeting, McGuire Woods, meeting restructure, no BDR concern.
- **Old behavior:** Excellent extraction across all topics. Correctly identified PantherRx close imminent, Family Resource risk analysis only, all action items. But no SPAWN entries. No delegation.
- **Correct behavior:** Use complex transcript protocol (3+ deals). Classify as multi-category. Plan all writes in Ops Log first. ONE Writer spawn with all instructions bundled. Spawn Researcher for White Wilson Medical Center intel. Create project-state files for Nashville strategy, PE targeting refresh, etc. Update index.md with new projects and people. Update hot.md. ONE Verifier spawn checks everything.

### Scoring Each Input

For each input, score:
| Criteria | Pass/Fail |
|----------|-----------|
| Classified correctly | |
| All new info written to permanent files | |
| Ops Log has complete lifecycle (INPUT → INPUT COMPLETE) | |
| Sub-agents spawned (SPAWN entries in Ops Log) | |
| Verifier ran (VERIFIED/FAILED/INPUT COMPLETE in Ops Log) | |
| Drafts presented inline (not "should I?") | |
| Cross-referenced with prior inputs | |
| index.md updated if needed | |
| hot.md updated if needed | |
| P2V2C2 scoring considered | |

### What to Watch
- **Ops Log** — the complete lifecycle for each input (INPUT → CLASSIFY → READ/WRITE/SCORE/SPAWN → VERIFIED/FAILED → INPUT COMPLETE)
- **Johnny Alerts** — any FAILED entries from the Verifier
- **Johnny DM** — quality of summaries, presence of inline drafts, urgency framing
- **Actual files** — spot-check deal-state.md files after processing to confirm writes landed

---

## Config State (openclaw.json key settings)

```
agents.defaults.model.primary: "anthropic/claude-opus-4-6"
agents.defaults.model.fallbacks: ["anthropic/claude-sonnet-4-5", "google/gemini-2.5-pro"]
session.reset.mode: "idle"
session.reset.idleMinutes: 5

Sub-agents (updated 2026-04-07 — Flash → Pro):
  writer: google/gemini-2.5-pro (fallback: ollama/mistral:7b)
  researcher: google/gemini-2.5-pro (fallback: ollama/qwen2.5:7b)
  meeting-prep: google/gemini-2.5-pro (fallback: ollama/llama3.1:8b)
  verifier: google/gemini-2.5-pro

Google API key: AIzaSyAnJnn_N_IvSGVsCzo7T2lSs-H73ej4ccE (Johnny1 project, replaced 2026-04-07)
Google baseUrl: https://generativelanguage.googleapis.com/v1beta

Main agent allowAgents: [writer, researcher, meeting-prep, verifier]
```

---

## Billing
- Anthropic API: $249.33 remaining (refunded 4/6, $274.38 credit grant)
- Google Gemini: active, Tier 1
- Claude Code: Max subscription
- API key: sk-ant-api03--M56j... (confirmed matching console)

---

## Local Files (on Austin's MBP)
All updated source files are in `/Users/austinhollsnd/Desktop/sales-tools/johnny-updates/`:
- SOUL.md, FEED-RULES.md, AGENTS.md, HEARTBEAT.md, WRITER-RULES.md, VERIFIER-RULES.md, index.md, hot.md, project-state-template.md

These are the authoritative copies that were pushed to Johnny's MBP.

---

## Additions Identified After Rebuild (Apply in Next Session)

### Email Thread Parsing
When an email thread is input, Johnny must parse it into individual messages (each with sender, date, content). Dedup check runs per-message, not per-thread. This ensures that when a longer version of the same thread is input later, only truly new messages are processed while already-seen messages are recognized.

### Draft Superseding
When a new input shows that a conversation has moved past a point where Johnny previously generated a draft, that old draft is no longer relevant. Johnny must:
1. Recognize that the thread has advanced beyond the prior draft
2. Produce a NEW draft responding to the current state of the thread
3. Supersede the old draft (update deal-state Next Action, replace the draft reference)

### Communication Sequence Numbering
Each deal gets a sequential counter for communication events in the Communication Log:

```
Exer #1 — Brian Chao → Austin (inbound, 4/6) — budget confirmed, requesting pricing
Exer #2 — DRAFT: Austin → Brian (Johnny's proposed reply, 4/6) — pricing + Aida info
Exer #3 — Austin → Brian (actual sent, 4/7) — supersedes #2
Exer #4 — Brian → Austin (inbound, 4/8) — follow-up question
Exer #5 — DRAFT: Austin → Brian (Johnny's proposed reply, 4/8)
```

Rules:
- Every communication event (inbound, outbound, draft) gets the next number
- DRAFTs are explicitly labeled as drafts
- When an actual sent message arrives from Austin to the same recipient, it supersedes the prior DRAFT
- Johnny automatically identifies the actual vs. the draft by sequence: if the prior entry is a DRAFT and the next FROM Austin entry goes to the same recipient, it's the actual
- The comparison (draft vs. actual) is captured as an artifact for skill evolution

This numbering makes the deal's communication history easy to follow and makes draft-vs-actual comparison automatic.

### Artifact Capture for Skill Evolution
When parsing an email thread, if any message was sent BY Austin, Johnny must check whether he previously drafted a response for that same deal/context. If yes:
1. Match Austin's actual sent message to Johnny's prior draft
2. Log an artifact to `~/johnny-evolution/artifacts/email-feed/` with both `johnny_output` (the draft) and `austin_actual` (what Austin sent)
3. Compute the delta — what was different, why
4. The Wednesday skill evolution cron uses these deltas to identify patterns and propose prompt improvements

This closes the feedback loop: Johnny drafts → Austin sends (possibly different) → Johnny captures the comparison → weekly evolution improves future drafts.

**All three changes were deployed to FEED-RULES.md and WRITER-RULES.md on Johnny's MBP on 2026-04-06 (same session as the rebuild).** Email thread parsing, communication sequence numbering, and artifact capture are live.

---

## Testing Session Results (2026-04-07)

### Infrastructure Fixes Applied During Testing

These were discovered and fixed progressively as each test input revealed issues:

1. **Google API key replaced** — old key `AIzaSyALNd8wklrtnt--0XgX3Pd2ahE0bOEHa9E` was invalid. New key: `AIzaSyAnJnn_N_IvSGVsCzo7T2lSs-H73ej4ccE` (project: Johnny1). Updated in: openclaw.json, writer/models.json, researcher/models.json, meeting-prep/models.json, verifier/models.json, main/agent/models.json.
2. **Google baseUrl fixed** — openclaw.json was missing `/v1beta`. Now consistent: `https://generativelanguage.googleapis.com/v1beta`
3. **Sub-agent workspace symlinks created** — THIS WAS THE BIGGEST FIX. Sub-agents had empty sandboxed workspace directories (`~/.openclaw/workspace-writer/`, etc.) with no access to `clearwater/`. Created symlinks:
   - `workspace-writer/clearwater` -> `workspace/clearwater`
   - `workspace-writer/WRITER-RULES.md` -> `agents/writer/WRITER-RULES.md`
   - `workspace-verifier/clearwater` -> `workspace/clearwater`
   - `workspace-verifier/VERIFIER-RULES.md` -> `agents/verifier/VERIFIER-RULES.md`
   - `workspace-researcher/clearwater` -> `workspace/clearwater`
   - `workspace-meeting-prep/clearwater` -> `workspace/clearwater`
   Before this fix, NO sub-agent had ever successfully read or written a file.
4. **Sub-agents upgraded from Gemini 2.5 Flash to Gemini 2.5 Pro** — Flash was crashing mid-session with "An unknown error occurred" (zero output tokens). Pro is stable.
5. **Verifier auth-profiles.json created** — was completely missing.
6. **Verifier SKILL.md replaced** — was a competing lighter copy of VERIFIER-RULES.md. Replaced with pointer: "Load and follow VERIFIER-RULES.md"
7. **IDENTITY.md archived** — stale file moved to .archive/
8. **Comm log prefix bug fixed** — WRITER-RULES.md used "Exer" as example prefix, Writer applied "Exer #N" to ALL deals. Fixed rules to clarify deal name is a variable. Fixed entries in Youth Villages (now "YV #N") and FRHC (now "FRHC #N").

### Architecture Changes Applied

1. **FEED-RULES.md completely rewritten** — replaced 6-step branching checklist with 5-step no-branching pipeline:
   - Step 1: CLASSIFY + READ (Johnny thinks, reads current state)
   - Step 2: RESCORE (always run P2V2C2 — if different write it, if same log "no change")
   - Step 3: BUNDLE + DISPATCH (one Writer spawn with everything; Researcher/Meeting Prep in parallel if needed)
   - Step 4: VERIFY (unconditional, always runs, no exceptions — even after Writer failure recovery)
   - Step 5: NOTIFY (DM Austin with results)
   Key principle: no branching, everything always runs. Every draft = outbound tracking entry.
   Writer failure recovery rule: if Writer crashes, Johnny completes remaining writes then continues pipeline including Verifier.

2. **VERIFIER-RULES.md updated** — added outbound-tracking.jsonl verification (every DRAFT must have tracking entry), added open item resolution check.

3. **system-context.md updated** — fixed stale references: default model now Opus 4.6, sub-agents now Gemini 2.5 Pro, always-load files updated, workspace structure updated, IDENTITY.md removed.

### Test Results (Chronological)

| # | Input | Score | Notes |
|---|-------|-------|-------|
| 1 | Holistic Wellness (sent to DM by mistake) | N/A | Good draft, no pipeline. Confirmed DM doesn't trigger feed processing. |
| 2 | Exer/Brian Chao (first run) | 7/10 | Pipeline fired. Writer/Verifier failed on path + auth. Johnny covered. Good output quality. |
| 2r | Exer/Brian Chao (rerun after API key fix) | 9/10 | Full pipeline. Writer + Researcher spawned. Verifier spawned but had path issue. |
| 3 | Trustwell Living (after symlink fix) | 8/10 | Writer partially succeeded (FIRST EVER sub-agent file write). Flash crashed mid-session. Johnny completed. No Verifier. |
| 4 | Youth Villages (after Pro upgrade) | **10/10** | Full pipeline. Writer completed full bundle. Verifier passed independently. First perfect run. |
| 5 | Family Resource Home Care | **10/10** | Writer + Meeting Prep spawned in parallel. Verifier passed. Meeting prep file created. |

### Known Issues for Next Session

- **DM pipeline gap:** Johnny needs logic to trigger feed processing on DM inputs that contain actionable information, not just feed channel inputs.
- **Gemini Flash instability:** Switched to Pro as workaround. May revisit Flash later if Google stabilizes it.
- **Comm log prefix bug:** Fixed in rules and in YV/FRHC files, but older deals (Exer, Trustwell) may still have "Exer" prefixes from before the fix.
---

## What's NOT Done Yet (Future)
- Graph API automation (email/calendar/Teams auto-flow to channels) — weeks out
- Test environment (clone workspace for safe testing) — decided to test in prod first
- Approach deck generation from templates — Austin has examples, needs template .pptx stored
- Knowledge docs (knowbe4.md, clearadvantage.md, hipaa-landscape.md) — marked "to be created" in index, will be created as inputs arrive
- Project directories — exist but empty, will be populated as inputs reference them
- DM pipeline gap — needs FEED-RULES.md update so DM inputs with actionable info trigger the full pipeline
