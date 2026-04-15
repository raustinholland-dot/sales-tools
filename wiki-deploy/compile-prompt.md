# Compile Task Instructions

You have a context file at `~/.openclaw/workspace/.tmp-compile-articles.txt`. Read it now.

It contains:
- The wiki schema (rules for compilation)
- The current wiki index
- All relevant existing wiki articles (pre-selected for you)
- A new input (email, transcript, calendar event, or Teams message)

## Your job

1. **Compile the input into the wiki** per wiki-schema.md:
   - Update existing articles with new information
   - Create new articles for entities not yet in the wiki (people, deals, orgs)
   - Maintain bidirectional wikilinks and `related:` fields
   - Update `wiki/index.md` with any status changes, new entries, or updated dates
   - Prepend a compile log entry to `wiki/log.md` in the standard format

2. **Assess the input** — does it require Austin to act?
   - If someone asked a question → draft a reply in Austin's voice
   - If a meeting is coming up → flag prep needed
   - If a deal status changed → note what shifted and what's next
   - If it's purely informational → just summarize what was captured

3. **Send Austin a DM** (chat_id 6461072413) with:
   - What was updated (1-2 lines)
   - The work product if action is needed (draft reply, action items, prep notes)
   - If no action needed, just the summary

## Voice

Write outputs in Austin's voice: direct, warm enough, gets to the point. No filler. Right word over impressive word.

## After Compiling

Once the wiki is updated and you've sent Austin your summary, run the analysis pipeline:

```
lobster run --mode tool --file ~/.openclaw/workspace/analysis-pulse.lobster
```

This triggers a Gemini gap analysis on the deals you just updated. If Austin needs a work product (email draft, call prep, etc.), it will trigger a second session to produce it.

## Important

- Bias toward creating articles — the wiki self-prunes via lint
- Only capture what's NEW — don't re-capture information the wiki already has
- For email threads, read newest first, check existing articles before re-analyzing old messages
