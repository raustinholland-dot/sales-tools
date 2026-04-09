# /johnny-audit — Johnny Forsyth Daily Performance Audit

Run `python3 ~/Desktop/sales-tools/johnny-audit.py $ARGUMENTS` to pull all Telegram feeds for the specified date (default: today).

If Telethon prompts for phone number or auth code, ask Austin to enter it in the terminal with `!`.

After the script completes:

1. Read the generated `audits/audit-YYYY-MM-DD.json` file
2. Load the testing criteria from `johnny-rebuild-2026-04-06.md` (the "Scoring Each Input" section)
3. Load `system-context.md` for channel architecture reference

## Analysis Steps

For each feed input Austin sent (messages in Email Feed, Calendar Feed, Teams Feed, or Transcripts):

1. **Identify the input** — what was sent, which channel, timestamp
2. **Find Johnny's response** — match it in Johnny DM by timestamp proximity and content
3. **Find the Ops Log lifecycle** — trace INPUT → CLASSIFY → READ/WRITE/SCORE/SPAWN → VERIFIED/FAILED → INPUT COMPLETE
4. **Score against the 10-point criteria:**
   - Classified correctly
   - All new info written to permanent files
   - Ops Log has complete lifecycle
   - Sub-agents spawned (SPAWN entries)
   - Verifier ran (VERIFIED/FAILED/INPUT COMPLETE)
   - Drafts presented inline (not "should I?")
   - Cross-referenced with prior inputs
   - index.md updated if needed
   - hot.md updated if needed
   - P2V2C2 scoring considered
5. **Flag any issues** — missed writes, broken lifecycle, missing spawns, permission-seeking, etc.

## Output Format

Present a structured report:
- **Timeline summary** — what happened chronologically
- **Per-input scorecard** — each input scored 0-10
- **Session reset analysis** — evidence of whether 5-min idle resets fired
- **Patterns** — recurring issues across inputs
- **Recommended tweaks** — specific changes to FEED-RULES.md, VERIFIER-RULES.md, etc.
- **Overall score** — weighted average across all inputs

Keep the analysis sharp and actionable. Lead with findings, not descriptions.
