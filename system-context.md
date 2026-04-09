# System Context — Johnny Forsyth Operations

Reference doc for the Telegram channel architecture, Johnny's environment, feed processing rules, and the Meta-Harness evolution system.

---

## Telegram Channel Architecture

All communication flows through Telegram. No SSH, no middleware.

| Channel | Chat ID | Purpose |
|---|---|---|
| **Johnny Forsyth DM** | — | Austin's direct line to Johnny |
| **Johnny Alerts** | `-1003883592748` | System health/error alerts |
| **Email Feed** | `-5033788441` | Austin forwards emails → Johnny processes |
| **Calendar Feed** | `-5181102673` | Calendar items → Johnny processes |
| **Teams Feed** | `-5244367510` | Teams messages → Johnny processes |
| **Transcripts** | `-5141490093` | Voice memos/transcripts → Johnny processes |
| **Ops Log** | `-5205161230` | Johnny logs all reads/writes/scores/drafts |

**Key constraint:** Telegram bots cannot see messages from other bots in groups. All instructions to Johnny come from Austin (via Telegram DM or feed channels).

---

## Johnny's Environment (Verified 2026-04-07)

**Johnny's MBP:** `austinholland@100.122.212.128` (Tailscale)
**Johnny's workspace:** `~/.openclaw/workspace/`
**Gateway:** `http://127.0.0.1:18789` (WebSocket + HTTP control)
**Gateway token:** `f18f7ebeb4a20e270fb7e859372441b1f087da793d65a14f`
**Nerve UI:** `http://100.122.212.128:3080`
**Kanban:** `/api/kanban/tasks`
**Crons:** `/api/crons`
**Default model:** `anthropic/claude-opus-4-6`

### Always-Load Context Files (Every Session)
- `SOUL.md` — core identity, personality, decision style, foundational write rule
- `FEED-RULES.md` — 5-step no-branching pipeline, classification, Ops Log lifecycle, delegation
- `index.md` — master navigation (all deals, projects, people, knowledge docs) — `clearwater/knowledge/`
- `hot.md` — 500-word current priorities cache (Urgent, This Week, Austin's Focus) — `clearwater/knowledge/`

### On-Demand Context Files
- `USER.md` — user context
- `AGENTS.md` — sub-agent directory, delegation model, session startup
- `HEARTBEAT.md` — cron schedules, briefing instructions
- `TOOLS.md` — available tools
- `MEMORY.md` — supplementary long-term state (legacy)
- Deal-state files, project-state files, knowledge docs — loaded as needed

### Workspace Structure
```
~/.openclaw/workspace/
├── clearwater/
│   ├── deals/          # external deals (lifecycle: open → active → won/lost)
│   ├── projects/       # internal initiatives (lifecycle: started → in progress → complete)
│   ├── knowledge/      # persistent reference (no end date, compounds over time)
│   │   ├── index.md    # master navigation — loaded every session
│   │   ├── hot.md      # 500-word current priorities — loaded every session
│   │   └── [topic].md  # flat, one per topic
│   ├── feeds/          # email-inbound.jsonl, email-outbound.jsonl,
│   │                   # teams-messages.jsonl, calendar-updates.jsonl,
│   │                   # outbound-tracking.jsonl, .processed-inputs.jsonl
│   ├── hyperagent/     # skills, tests, runs
│   ├── pipeline.json   # served via localhost:7890
│   ├── reference/      # colleague-directory.md, product info
│   └── scripts/
├── memory/             # daily logs (YYYY-MM-DD.md) — legacy
├── transcripts/
└── [context files: SOUL, FEED-RULES, AGENTS, HEARTBEAT, TOOLS, USER, MEMORY]
```

### Deal Ledger
- **Location:** `clearwater/deals/[deal-name]/deal-state.md`
- **24 deal folders:** 4 "deep" deals with full state tracking, 20 skeleton
- **Deep deals:** Velentium, Paradigm, Pyramids Pharmacy (+ 1 more)
- **Schema:** Catalyst, Next Action, P2V2C2 Scores, Key Context, Communication Log, Salesforce Link
- **Source of truth:** Salesforce (~27 active deals, $1.59M pipeline)
- **Gap:** No automated sync between Salesforce and deal-state.md files
- **Salesforce CLI:** `sf data query --query "SOQL" --target-org clearwater --json`
- **Austin's SF Owner ID:** `005Nv000006n8QwIAI`

### Deal Scoring — P2V2C2
- **Pain** (0-10), **Power** (0-10), **Vision** (0-10), **Value** (0-10), **Change** (0-10), **Control** (0-10)
- Salesforce calculates `P2V2C2_Total__c` automatically
- SF fields: `Pain__c`, `Power__c`, `Vision__c`, `Value__c`, `Change__c`, `Control__c`, `Critical_Activity_Stage__c`, `NextStep`

### Knowledge System
- **index.md** — master navigation: all deals (with status), projects, key people, knowledge docs, reference files — `clearwater/knowledge/`
- **hot.md** — 500-word current priorities cache (Urgent, This Week, Austin's Focus) — `clearwater/knowledge/`
- **[topic].md** — flat knowledge docs, one per topic — `clearwater/knowledge/`
- **MEMORY.md** — supplementary long-term state (legacy)
- **memory/YYYY-MM-DD.md** — raw daily session logs (legacy)
- **clearwater/reference/** — colleague directory, deal-specific docs

### Johnny's Tools
- `read`, `write`, `edit`, `exec`, `process`
- `web_search`, `web_fetch`, `browser`
- `message` (Telegram), `cron`
- `memory_search`, `memory_get`
- `sf` (Salesforce CLI)
- `sessions_spawn` — sub-agents (all `google/gemini-2.5-pro`):
  - **Writer** — all file writes + drafts (loads WRITER-RULES.md)
  - **Researcher** — all research tasks
  - **Meeting Prep** — all meeting preparation
  - **Verifier** — post-processing verification (loads VERIFIER-RULES.md, posts VERIFIED/FAILED/INPUT COMPLETE)

### Outbound Tracking
- **File:** `clearwater/feeds/outbound-tracking.jsonl`
- **Schema:** `{deal, recipient, action, status, next_action, sent_date}`
- Tracks open items requiring follow-up

---

## Feed Processing Rules

### Dedup Check (ALL channels)
Before any processing, Johnny computes a hash of the input and checks `clearwater/feeds/.processed-inputs.jsonl`. If already processed → DMs Austin "Already processed this one" + `NO_REPLY` in feed channel. If new → proceeds with normal processing and appends to the ledger. Live since 2026-04-05.

### Email Feed
1. Consider WHY the email was sent — what is it about?
2. If deal-specific:
   - Update `clearwater/deals/[deal-name]/deal-state.md` with new state
   - Update Communication Log section
   - Check if P2V2C2 scores should change based on new information
3. If Johnny has questions → ask Austin in Johnny Forsyth DM
4. If follow-up needed → draft response and send to Austin for review

### Calendar Feed
1. Check if event affects any active deal or requires prep
2. If meeting is within 24 hours and involves a deal contact:
   - Start meeting prep (spawn Meeting Prep sub-agent with Llama 3.1)
   - Pull deal-state.md for context
   - Send prep summary to Austin in Johnny Forsyth DM
3. Check for scheduling conflicts

### Teams Feed
1. Determine if deal-relevant or action-required
2. If deal-relevant:
   - Update `clearwater/deals/[deal-name]/deal-state.md`
   - Sync related components (outbound-tracking, pipeline.json if needed)
3. If action required → execute or send output to Austin
4. If from David Kolb or active client → treat as high priority

### Transcripts
1. Match to calendar items — determine what meeting/call it's from
2. Infer if deal-related based on attendees and content
3. If deal-related:
   - Update `clearwater/deals/[deal-name]/deal-state.md`
   - Re-score P2V2C2 based on new information
   - Sync deal ledger and all corresponding components
4. Extract action items, key decisions, and commitments
5. Generate necessary outputs and send to Austin

### General Principle
Every input updates Johnny's understanding — not just deals, but internal tasks, knowledge base, anything in his environment.

### Ops Log
For every feed interaction, Johnny posts to the Ops Log channel with a complete lifecycle:

**Lifecycle:** `INPUT → CLASSIFY → READ/WRITE/SCORE/SPAWN → VERIFIED/FAILED → INPUT COMPLETE`

Entry types:
- `INPUT: [channel] — [summary]`
- `CLASSIFY: [deal / project / knowledge / multi-category]`
- `READ: [file path] — why`
- `WRITE: [file path] — what changed`
- `SCORE: [deal name] — old score → new score, why`
- `SPAWN: [agent name] — [task summary]`
- `DRAFT: [type] — for whom, re: what`
- `VERIFIED: [verifier confirms all writes landed correctly]`
- `FAILED: [what was missing or wrong] → forwarded to Johnny Alerts`
- `INPUT COMPLETE: [channel] — [summary]`
- `SKILL: [skill name] v[N] — invoked for [input summary]`
- `CRON: [action] — what changed`

Does NOT log routine heartbeats. Only feed-triggered actions and direct instructions.
Rules are in `FEED-RULES.md` on Johnny's MBP.

---

## Input Delivery (Current vs. Future)

### Current (Manual)
Austin manually forwards/pastes everything into the appropriate Telegram channel.

### Future (When Ready)
- **Email:** Outlook forwarding rule → `@etlgr_bot` email address → Telegram Email Feed (instant, free)
- **Calendar:** IFTTT applet — Office 365 Calendar trigger → Telegram Calendar Feed (~5 min delay, free or $3.49/mo)
- **Teams:** Integrately or Albato webhook trigger → Telegram Teams Feed (free tier available, instant)
- **Transcripts:** Manual for now

---

## How to Reach Johnny

Message Johnny through **Johnny Forsyth DM** in Telegram. Austin sends all instructions directly — there is no intermediary bot.

For system changes on Johnny's MBP, craft the instruction in Claude Code (terminal), then send it to Johnny via Telegram.

---

## Key People

- **Austin Holland** — sales professional at Clearwater, the user
- **David Kolb** — important contact, messages from him are high priority
- **Johnny Forsyth** — the AI agent (OpenClaw) on Austin's other MBP, handles day-to-day deal ops

---

## Scheduled Routines on Johnny's MBP

| Cron | Schedule | What |
|---|---|---|
| **Tomorrow's Briefing** | 9 PM CT Sun–Thu | Next day's meetings, action items, deal next steps → Johnny Forsyth DM |
| **SF Pipeline Sync** | 9:45 PM CT Sunday | Pull open opportunities via SF CLI, diff against deal-state files, present stale field summary → Johnny Forsyth DM |
| **SF Pipeline Sync** | 10 PM CT Tuesday | Mid-week Salesforce pipeline sync (same process as Sunday) → Johnny Forsyth DM |
| **Weekly Skill Evolution** | Wed 9 PM CT | Analyze artifact deltas, propose prompt improvements → Johnny Alerts |
| **Daily GitHub Backup** | 11 PM CT daily | Auto-commit and push workspace to `raustinholland-dot/johnny-workspace-backup` (private) |

---

## Workspace Backup

Johnny's workspace is backed up nightly to a private GitHub repo.
- **Repo:** `raustinholland-dot/johnny-workspace-backup`
- **Script:** `clearwater/scripts/daily-backup.sh`
- **Log:** `clearwater/logs/backup.log`
- **Auth:** HTTPS with personal access token (embedded in remote URL)
- Only commits and pushes if there are changes

---

## What NOT to Do

- Don't process feed inputs yourself — that's Johnny's job
- Don't take external actions (API calls, pushes, messages to Johnny) without asking Austin first
- Don't expand scope beyond what Austin asks
- Don't delete with `rm` — use `mv ~/.Trash/`
- Don't SSH into Johnny's MBP unless Austin explicitly asks
