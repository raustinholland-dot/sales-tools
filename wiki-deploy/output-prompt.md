# Output Task Instructions

You have two files to read:

1. `~/.openclaw/workspace/.tmp-output-context.json` — Gemini's analysis of which deals need action, what's missing, and what type of output Austin needs
2. `~/.openclaw/workspace/.tmp-analysis-context.txt` — The full deal context (wiki articles, scoring history, index)

Read both now.

## Your job

For each deal where `output_needed` is not "none":

### If output_needed = "email_draft"
Draft the email in Austin's voice. Include:
- To/Subject line
- Full body text ready to send
- Any attachments to reference

### If output_needed = "call_prep"
Prepare a call brief:
- Who's on the call, their roles, what they care about
- Key points to cover
- Questions to ask
- Desired outcome

### If output_needed = "action_reminder"
Write a clear action item:
- What needs to happen
- By when
- Why it matters now

### If output_needed = "deal_update"
Summarize what shifted:
- What changed and why
- Impact on deal trajectory
- What's next

## Delivery

Send each output to Austin's DM (chat_id 6461072413) as a separate message. Lead with the deal name and output type. No preamble.

## Voice

Austin's voice: direct, conversational, warm enough. Right word over impressive word. No corporate speak. Write like Austin writes — check the wiki articles for examples of his actual emails.

## Important

- Use the Gemini analysis as your starting point, but apply your own judgment. If something doesn't feel right, say so.
- The analysis tells you WHAT to produce. You decide HOW to make it compelling.
- If multiple deals need output, handle the most urgent first.
