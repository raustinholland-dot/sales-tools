# /johnny-ops — Johnny Forsyth Operations Context

Read and internalize these files:
1. `~/Desktop/sales-tools/johnny-rebuild-2026-04-06.md` — **START HERE.** Complete rebuild doc from 4/6. Architecture, every deployed file, config state, testing plan.
2. `~/Desktop/sales-tools/system-context.md` — Telegram architecture, Johnny's environment, channel chat IDs
3. `~/Desktop/sales-tools/meta-harness.md` — skill evolution architecture

## Current Status

**System was fully rebuilt on 2026-04-06.** Johnny is deployed on Opus 4.6 with a new 6-step processing checklist, 4 sub-agents (Writer, Researcher, Meeting Prep, Verifier), a knowledge system (index.md + hot.md), agent-specific rules files, and 5-minute idle session resets. The rebuild doc has every detail.

**Phase: TESTING.** Send real feed inputs and evaluate against the testing criteria in the rebuild doc. Key things to watch: Ops Log lifecycle (INPUT through INPUT COMPLETE), SPAWN entries, Verifier VERIFIED/FAILED results, inline drafts in DM, index.md and hot.md updates.

## Architecture Summary

- **Johnny** (Opus 4.6 on remote MBP at 100.122.212.128) orchestrates — classifies, decides, scores, plans, notifies Austin
- **Writer** (Gemini 2.5 Flash) executes all file writes and drafts
- **Researcher** (Gemini 2.5 Flash) handles all research tasks
- **Meeting Prep** (Gemini 2.5 Flash) handles all meeting preparation
- **Verifier** (Gemini 2.5 Flash) independently confirms every write after processing
- **Austin** sends inputs to 5 Telegram feed channels (Email, Calendar, Teams, Transcripts, Johnny Alerts)
- **Ops Log** (chat_id: `-5205161230`) is the audit trail + knowledge changelog
- Sessions reset after 5 minutes idle — every session starts fresh from files

## Key Technical Details
- Johnny bot: @johnny_forsyth_bot
- Johnny's MBP: `austinholland@100.122.212.128` (Tailscale)
- Johnny's workspace: `~/.openclaw/workspace/`
- Default model: `anthropic/claude-opus-4-6`
- Sub-agent model: `google/gemini-2.5-flash`
- Gateway: `http://127.0.0.1:18789` on Johnny's MBP
- Gateway token: `f18f7ebeb4a20e270fb7e859372441b1f087da793d65a14f`
- Nerve UI: `http://100.122.212.128:3080`

## Workflow

1. Load this context (`/johnny-ops`)
2. Read the rebuild doc for full detail on any area
3. For troubleshooting: SSH into Johnny's MBP, check gateway logs, check Ops Log
4. For crafting instructions: draft message for Austin to send via Telegram DM
5. For testing: evaluate Johnny's response against the criteria in the rebuild doc
6. Austin sends all messages — do NOT send to Johnny directly without Austin's approval

## After Loading

1. Confirm the rebuild doc and system context are loaded
2. State the current phase (testing) and what you're ready to do
3. Wait for Austin's instructions
