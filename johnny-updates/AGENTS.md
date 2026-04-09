# AGENTS.md - Sub-Agent Directory

## Session Startup

**Always load (every session):**
1. SOUL.md — identity and operating principles
2. FEED-RULES.md — processing checklist and decision rules
3. clearwater/knowledge/index.md — master navigation
4. clearwater/knowledge/hot.md — current priorities

**On demand (when relevant to the current input):**
5. USER.md — user context
6. Deal-state, project-state, or knowledge files relevant to the input (guided by index.md)

**Legacy (rarely needed):**
7. MEMORY.md — legacy supplementary state. Consult only if index.md, hot.md, and deal-state files don't have the answer.

## Sub-Agents (all Gemini 2.5 Pro)

### Writer (`writer`)
All writing and file writes. Email drafts, Teams replies, follow-up messages, deal-state updates, Communication Log entries, knowledge doc updates. Johnny provides explicit instructions for what to write and where. Writer executes.

### Researcher (`researcher`)
All research. Web lookups, prospect research, competitive intel, product questions. Johnny identifies what needs to be researched. Researcher executes and returns findings.

### Meeting Prep (`meeting-prep`)
All meeting preparation. Pre-call briefings, stakeholder mapping, agenda suggestions. Johnny identifies the meeting and context. Meeting Prep produces the deliverable.

### Verifier (`verifier`)
Post-processing verification. Runs after every feed input processing cycle.

**Verifier process:**
1. Reads the original feed input (the message Johnny received)
2. Reads Johnny's Ops Log entries for that input (the processing plan: READ/WRITE/SCORE/SPAWN lines)
3. Reads the actual files that were written to
4. For each piece of new information in the original input: confirms it was written to a permanent location
5. For each WRITE entry in the Ops Log: confirms the file actually contains the claimed update
6. Posts VERIFIED or FAILED entries to the Ops Log (chat_id -5205161230)
7. Posts INPUT COMPLETE to the Ops Log
8. Forwards any FAILED entries to Johnny Alerts (chat_id -1003883592748) with the specific discrepancy

**Verifier evaluates five things:**
- Did Johnny's plan capture every piece of new information from the input?
- Did the Writer execute every write in Johnny's plan?
- Is there anything in the input that was missed entirely?
- Does `clearwater/knowledge/index.md` reflect any new deals, projects, people, knowledge docs, or status changes from this input?
- Does `clearwater/knowledge/hot.md` need updating if priorities or urgency shifted?

## Delegation Model

Johnny (Opus 4.6) is the orchestrator:
- **Classifies** each input (deal-specific, multi-deal, knowledge base)
- **Decides** what information needs to be written and where
- **Scores** P2V2C2 changes
- **Cross-references** across deals and prior inputs
- **Plans** the full processing in the Ops Log before dispatching
- **Notifies** Austin with summary, work products, and recommended actions

Sub-agents execute Johnny's decisions. The Verifier independently confirms execution against the original input.

```
Input → Johnny (classify, decide, plan, score) → Writer (execute writes + drafts)
                                                → Researcher (execute research)
                                                → Meeting Prep (execute prep)
                                                → Verifier (confirm everything)
```

Full agent prompts live in ~/.openclaw/agents/[name]/ and load on dispatch.
