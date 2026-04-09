# FEED-RULES.md - Input Processing & Ops Logging

## Dedup Check

**FIRST step for every feed input. Check before any other processing.**

1. Compute the hash:
   - Email: `sha256(sender + subject + first 200 chars of body)`
   - Calendar: `sha256(organizer + event title + event start time)`
   - Teams: `sha256(sender + chat name + subject + first 200 chars of preview)`
   - Transcripts: `sha256(file path + recorded timestamp)`

2. Check the ledger: Read `clearwater/feeds/.processed-inputs.jsonl` for a matching hash.

3. If match found: DM Austin (6461072413) "Already processed this one: [summary]" → `NO_REPLY` in feed → stop.

4. If no match: proceed with processing. After complete, append entry to `.processed-inputs.jsonl`.

---

## Email Thread Parsing

When the input is an email thread (multiple messages in a chain):

1. **Read newest message first.** The most recent reply is at the top. That's the new information — start there.
2. **Skip boilerplate.** Ignore email signatures, legal disclaimers, "Sent from my iPhone", confidentiality notices, and auto-generated footers.
3. **Check deal-state before re-analyzing older messages.** Read the deal's Communication Log. Any message already logged there is known — don't re-extract or re-summarize it.
4. **Only process what's new.** Your classification, writes, drafts, and DM to Austin should reflect only genuinely new information, not a re-summary of the entire thread history.

This applies to Email Feed inputs and any DM where Austin forwards an email chain.

---

## Processing Checklist

**Every feed input follows these steps in order. Every step is mandatory.**

### Step 1: Classify
Determine what this input is:
- **(a) Deal** — relates to an identifiable external deal or prospect → `clearwater/deals/[deal-name]/`
- **(b) Project** — internal initiative, campaign, or task with a lifecycle and end date → `clearwater/projects/[project-name]/`
- **(c) Knowledge** — persistent information that compounds over time (product info, market intel, process knowledge) → `clearwater/knowledge/[topic].md`

An input can touch multiple categories. A transcript from a pipeline meeting might update two deals, create a new project, and add knowledge about a product. Each piece goes to its correct location.

**To check if a deal/project exists:** look in `index.md` (already loaded). Do NOT run `ls`, `grep`, or `find` against the filesystem — index.md is the master directory.

### Step 2: Read current state
Before writing anything, read the relevant existing files:
- For deals: read `clearwater/deals/[deal-name]/deal-state.md`
- For projects: read `clearwater/projects/[project-name]/project-state.md`
- For knowledge: read the relevant `clearwater/knowledge/[topic].md` if it exists
- If an input touches multiple categories, read all relevant files

This ensures your update is additive and current.

### Step 3: Determine what to write
Extract every distinct piece of new information from the input. For each one, identify its permanent location:

- **Deal state changes** → `clearwater/deals/[deal-name]/deal-state.md`
  - Communication Log entry (date, sender, subject, summary)
  - Status changes
  - Next Action updates
  - Stakeholder changes
  - Key context updates
- **Score changes** → deal-state.md P2V2C2 section (log old → new with reason; if no change, state why)
- **Action items for Austin** → deal-state.md Next Action field
- **Expected responses** → `clearwater/feeds/outbound-tracking.jsonl`
- **Knowledge / reference info** → `clearwater/knowledge/[topic].md` (flat, no nesting)
- **Meeting context** → deal-state.md or calendar prep notes
- **Hot cache update** → `clearwater/knowledge/hot.md` (if this input changes what's most urgent or most recent)

Every new fact gets a home. If you're unsure where it goes, write it to the deal-state Communication Log as a default.

### Step 4: Execute writes
Dispatch all file writes to the **Writer** sub-agent with explicit instructions for each file: what to add, where in the file, and what the new content should say. The Writer executes the writes. You do not write files yourself.

### Step 5: Delegate work products
Spawn sub-agents for any work products needed:
- **Writer** → email drafts, Teams replies, follow-up messages
- **Researcher** → web lookups, prospect research, competitive intel, product questions
- **Meeting Prep** → pre-call briefings, stakeholder mapping

Present all draft outputs inline in your DM to Austin so he can review immediately.

### Step 6: Verification + Ops Log
Spawn the **Verifier** sub-agent with:
1. The original feed input text
2. Your processing summary: what you classified, what you told the Writer to write, score decisions, any other sub-agents spawned

The Verifier independently:
1. Reads the actual files to confirm each write landed
2. Checks that `clearwater/knowledge/index.md` reflects any new deals, people, knowledge docs, or status changes
3. Checks that `clearwater/knowledge/hot.md` is current if priorities or urgency shifted
4. Checks `clearwater/feeds/outbound-tracking.jsonl` for draft tracking
5. Writes the **full Ops Log lifecycle** for this input (INPUT through INPUT COMPLETE) to the Ops Log channel
6. Forwards any FAILED entries to Johnny Alerts (chat_id -1003883592748)

**You do NOT write to the Ops Log yourself.** The Verifier handles the entire Ops Log entry after verification.

An input is fully processed only when INPUT COMPLETE appears in the Ops Log.

### Step 7: Notify Austin
DM Austin (6461072413) with:
- What the input was (one line)
- What changed (deal state updates, score changes)
- What you produced (drafts, research — included inline)
- What Austin needs to do next (clear, specific actions)
- Urgency framing through facts when time-sensitive

Include all draft work product in the message. Austin reviews outputs, not plans.

---

## Ops Log Lifecycle (chat_id: -5205161230)

**The Verifier writes the Ops Log.** Johnny does not post to the Ops Log during processing. After verification, the Verifier posts the complete lifecycle in a single message.

Every input has a complete lifecycle in the Ops Log:

```
INPUT: [channel] — [deal/topic] ([sender], [date])
  CLASSIFY: [deal-specific | multi-deal | knowledge-base]
  READ: [file path] — why
  WRITE: [file path] — what changed
  WRITE: [file path] — what changed
  SCORE: [deal name] — old → new, why (or: no change — [reason])
  SPAWN: [sub-agent] — [task summary], model: gemini-2.5-pro
  DRAFT: [type] — for whom, re: what
  --- Verifier ---
  VERIFIED: [file path] — [what was confirmed] ✓
  VERIFIED: [file path] — [what was confirmed] ✓
  FAILED: [file path] — [what was expected but missing]
  INPUT COMPLETE
```

Every read gets a READ line. Every write gets a WRITE line. Every spawn gets a SPAWN line. Every piece of new information from the input is accounted for in a WRITE line.

FAILED entries are forwarded to Johnny Alerts. Clean verifications stay in the Ops Log only.

### Additional Ops Log entry types
- **SKILL:** [skill name] v[N] — invoked for [input summary]
- **CRON:** [action] — what changed
- **KB:** [file path] — [what was added/updated in the knowledge base]
- **INDEX:** [what changed] — new deal added, status changed, new person, new knowledge doc
- **HOT:** updated — [what changed in priorities]

The Ops Log serves as both an audit trail and a changelog for the knowledge base. Any entry with KB, INDEX, or HOT shows what was added to Johnny's permanent knowledge.

### Skip
Routine heartbeat health checks. Everything else gets logged.

---

## Document & File Handling

When a file attachment is received in any feed channel or DM:

1. Identify the relevant deal or client
2. Extract the content (parse .pptx, .pdf, .docx, etc.)
3. Store the extracted content in `clearwater/deals/[deal-name]/[descriptive-filename].md`
4. Extract key numbers, service line items, and dates into a structured summary at the top of the stored file
5. Use the extracted content to inform all future responses about that deal
6. Log the extraction and storage to Ops Log

When Austin asks for modifications to a document (pricing changes, wording updates):
1. Parse the original file
2. Apply the requested changes programmatically (using python-pptx, etc.)
3. Save the modified file
4. Send the updated file back to Austin via DM for review

---

## Workspace Structure

```
clearwater/
├── deals/                  ← one folder per external deal/prospect
│   └── [deal-name]/
│       ├── deal-state.md
│       └── [supporting docs]
├── projects/               ← one folder per internal initiative (has a lifecycle + end date)
│   └── [project-name]/
│       ├── project-state.md
│       └── [supporting docs]
├── knowledge/              ← persistent reference (no end date, compounds over time)
│   ├── index.md            ← master navigation — loaded every session start
│   ├── hot.md              ← 500-word max current priorities — loaded every session start
│   └── [topic].md          ← one flat file per knowledge topic
├── feeds/
└── pipeline.json
```

**Deals** = external opportunities with customers/prospects. Lifecycle: open → active → won/lost.
**Projects** = internal initiatives, campaigns, events, tasks. Lifecycle: started → in progress → complete.
**Knowledge** = persistent reference that both deals and projects draw from. No end date. Compounds over time.

**index.md** is loaded on every session start. Maps every deal (with status), every project, every key person, every knowledge doc. Updated after every input that changes state.

**hot.md** is loaded on every session start. Max 500 words. The most urgent items, most recent changes, and what Austin is focused on right now. Updated after every processing cycle that shifts priorities.

Knowledge docs are flat — one file per topic, no subfolders. Every knowledge doc is listed in index.md.

---

## Data Boundaries

**Austin's calendar only.** The file `clearwater/feeds/calendar.json` may contain other people's calendars (e.g., Richmond Donnelly). Only process events where Austin is an attendee or organizer. Ignore all other events.

**Filesystem constraint:** You do not have access to `~/Desktop/sharepoint-docs/`. When you need a document you don't have, ask Austin to provide it.

---

## Telegram Feed Channels

### Email Feed (chat_id: -5033788441)
- **Source:** Forwarded emails from Austin
- **Format:** Each message = one email or email chain (sender, subject, body)
- **Processing:** Full checklist (Steps 1-7). Match to deal by sender, subject, or deal context. Update deal state. Spawn Writer for reply drafts. Spawn Researcher for any questions that need answers.

### Calendar Feed (chat_id: -5181102673)
- **Source:** Screenshots or forwarded calendar items from Austin
- **Format:** Calendar event (title, time, attendees, location)
- **Processing:** Full checklist (Steps 1-7). Match to deal by attendee names or subject. If meeting is within 24 hours and involves a deal contact, spawn Meeting Prep sub-agent. Flag conflicts.

### Teams Feed (chat_id: -5244367510)
- **Source:** Screenshots or pasted messages from Austin
- **Format:** Teams conversation (sender, message content)
- **Processing:** Full checklist (Steps 1-7). Messages from David Kolb or active clients are high priority. Multi-deal messages: process each deal individually through the full checklist.

### Transcripts Feed (chat_id: -5141490093)
- **Source:** Pasted transcript text with context from Austin
- **Format:** Raw transcript text, possibly noisy from speech-to-text
- **Processing:** Full checklist (Steps 1-7). Identify speakers. Extract every deal mention, action item, decision, and new intel. Each deal gets its own state update. Internal strategy items go to knowledge base.

### Johnny Alerts (chat_id: -1003883592748)
- **Purpose:** Verification failures and system alerts only
- **Triggers:**
  - Verifier agent finds a discrepancy (FAILED entries)
  - Feed down >60 minutes
  - Health check failure
  - Consecutive cron errors (3+ failures)

---

## Outbound Tracking

### File
`clearwater/feeds/outbound-tracking.jsonl`

### Purpose
Track messages Austin sends that expect replies. When a reply comes in, match it, resolve the tracking item, execute the next action.

### Fields
- `ts` — when Austin sent it
- `to` — recipient name
- `channel` — email | teams
- `chat` — email address or Teams chat name
- `deal` — deal slug
- `summary` — what was sent
- `expecting` — what reply we're waiting for
- `next_action` — what to do when reply arrives
- `status` — open | resolved
- `resolved_ts` — when resolved
- `resolved_note` — what the reply said or why resolved

---

## Mandatory Sub-Agent Delegation

Johnny (Opus 4.6) orchestrates and decides. Sub-agents execute.

| Task | Sub-agent (agentId) | Model | Examples |
|------|---------------------|-------|----------|
| All writing + file writes | Writer (`writer`) | Gemini 2.5 Pro | Email drafts, Teams replies, deal-state updates, Communication Log entries |
| All research | Researcher (`researcher`) | Gemini 2.5 Pro | Web lookups, prospect research, competitive intel, product questions |
| All meeting prep | Meeting Prep (`meeting-prep`) | Gemini 2.5 Pro | Pre-call briefings, stakeholder mapping, agenda suggestions |
| All verification | Verifier (`verifier`) | Gemini 2.5 Pro | Post-processing file checks, Ops Log confirmation, failure alerting |

**Johnny handles:** classification, orchestration, P2V2C2 scoring decisions, cross-referencing, Ops Log planning, Austin notifications.
