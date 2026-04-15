# /mission-board — Become Mission Board-aware (superset of /johnny)

When Austin types `/mission-board`, you are starting (or resuming) work on the Mission Board Mini App — the Telegram WebApp at `~/.openclaw/workspace/mission-board/` that gives Austin an approvable queue for Johnny's proposed drafts, follow-ups, and SF sync items. This command is a **superset of `/johnny`** — one command, full context for pipeline + Mini App work. Don't split into two commands; most Mission Board work needs pipeline context (drafting diagnosis, feedback analysis, visibility-feature design, capability proposals).

## Session-start read (do this first, every time)

**Local steps (forcing functions):**

0a. **Re-read the Working Principles section of `~/Desktop/sales-tools/CLAUDE.md`** — the four Karpathy principles (Think before coding · Simplicity first · Surgical changes · Verify before stopping). State them back in one line as part of the orientation summary so Austin can see they're active.

0b. **Open any memory entry in `~/.claude/projects/-Users-austinhollsnd-Desktop-sales-tools/memory/MEMORY.md` pinned with "START HERE"** — read the actual file, don't rely on the index description.

**MBP reads (run in parallel via `ssh mbp`):**

### Pipeline foundation (inherited from /johnny)

1. **Core orientation — what the system is, how it's built, where it's headed:**
   ```
   ssh mbp "cat ~/.openclaw/workspace/johnny/framing.md ~/.openclaw/workspace/johnny/architecture.md ~/.openclaw/workspace/johnny/vision.md"
   ```

2. **Recent decisions — list last ~14 days, read anything whose filename matches likely session topics:**
   ```
   ssh mbp "ls -lt ~/.openclaw/workspace/johnny/decisions/ | head -15"
   ```
   Then `cat` any decision file from the last 3 days, plus any slug matching `mission-board`, `mini-app`, `feedback`, `queue`, `sf-sync`, or `ui`.

3. **Current wiki + pipeline state — recent compile log + metrics:**
   ```
   ssh mbp "head -60 ~/.openclaw/workspace/wiki/log.md; echo ---; ls -lt ~/.openclaw/workspace/wiki/metrics/ | head -8"
   ```

4. **Cron state — what's actually scheduled:**
   ```
   ssh mbp "crontab -l; echo ---; python3 -c \"import json,datetime; d=json.load(open('/Users/austinholland/.openclaw/cron/jobs.json')); [print(j['id'],j.get('enabled'),j.get('schedule',{}).get('expr',''),datetime.datetime.fromtimestamp(j.get('state',{}).get('lastRunAtMs',0)/1000) if j.get('state',{}).get('lastRunAtMs') else '') for j in d['jobs']]\""
   ```

### Mission Board-specific reads (added on top)

5. **Handoff brief — the Mini App's START HERE doc:**
   ```
   ssh mbp "cat ~/.openclaw/workspace/johnny/mini-app-handoff.md"
   ```
   This is the authoritative architectural reference. If it's stale (older than the most recent Mission Board-related decision file), flag that and ask Austin whether Johnny should refresh it.

6. **The three code files that matter for iteration:**
   ```
   ssh mbp "cat ~/.openclaw/workspace/mission-board/src/server.js ~/.openclaw/workspace/mission-board/src/renderer.js ~/.openclaw/workspace/mission-board/public/index.html"
   ```
   These change often. Re-read every session so you don't reason from a stale mental model.

7. **Data state snapshot (counts only — full reads happen on demand):**
   ```
   ssh mbp "wc -l ~/.openclaw/workspace/mission-board/data/feedback.jsonl ~/.openclaw/workspace/mission-board/data/locked.jsonl ~/.openclaw/workspace/mission-board/data/sf-sync-log.jsonl 2>/dev/null; echo ---; python3 -c \"import json; d=json.load(open('/Users/austinholland/.openclaw/workspace/mission-board/data/queue.json')); active=[i for i in d['items'] if i.get('status') not in ('dismissed','sent')]; print('queue total:', len(d['items']), '| active:', len(active), '| version:', d.get('version'))\""
   ```

8. **Server liveness:**
   ```
   ssh mbp "launchctl list | grep mission-board; echo ---; curl -sS http://100.122.212.128:7892/api/queue 2>&1 | head -c 120"
   ```

## After reading, orient Austin briefly

Send one short message (4–8 lines) summarizing:
- One line confirming the four Working Principles are active (proof you re-read CLAUDE.md)
- What Johnny's doing right now — active crons, most recent compile/output, any pending issues in log.md
- **Mission Board state** — server up/down per launchctl, data counts (active queue depth, total feedback count, locked count). **Flag anything that grew since the last session** (you can tell from the handoff brief and the most recent decision file)
- Anything new in Mission Board code or decisions since the last session
- Any unresolved thread from recent decisions or a pinned "START HERE" memory entry
- Ready for Austin's direction

Do not dump file contents back at him — he wrote them, he knows what they say. Summary is proof of orientation, not a briefing.

## Core facts (shortcut — still read the files, this is just the map)

### Johnny pipeline (inherited from /johnny)
- **MBP:** `100.122.212.128` via Tailscale, ssh alias `mbp`, user `austinholland`
- **Workspace:** `~/.openclaw/workspace/`
- **Foundation docs:** `workspace/johnny/{framing,architecture,vision}.md`, `decisions/`
- **Pipeline files:** `feed-pipeline.lobster`, `compile-wiki.lobster`, `analysis-pulse.lobster`, `compile-prompt.md`, `output-prompt.md`
- **Daily backup cron:** 4 AM CT (moved from 11 PM on 2026-04-15 so it captures overnight work)

### Mission Board specifics
- **Directory:** `~/.openclaw/workspace/mission-board/`
- **Server:** Node/Express on port **7892**, kept alive by LaunchAgent `com.johnny.mission-board` (RunAtLoad + KeepAlive). Logs to `/tmp/mission-board.log`.
- **Frontend:** Vanilla JS single HTML at `public/index.html`. No build step, no framework, no bundler.
- **API routes (in `src/server.js`):** `/api/queue/{push,lock,dismiss,feedback,sent}`, `/api/sf-sync/{push,approve,skip}`, `/api/board`, `/api/article/:id`
- **Renderer:** `src/renderer.js` transforms wiki markdown into structured HTML for deal / draft / person / event views
- **Data files (single source of truth — don't mirror):**
  - `data/queue.json` — active proposals with version counter on mutations
  - `data/locked.jsonl` — append-only log of approved items + Austin's edited content
  - `data/feedback.jsonl` — append-only log of dismissals/edits with Austin's stated reasons
  - `data/sf-sync.json` + `sf-sync-log.jsonl` — SF review board state + action log
  - `data/enrichment-batch{1,2,3}.json` — pre-computed deal enrichments for SF sync cards
- **Telegram WebApp integration:** frontend loads `telegram.org/js/telegram-web-app.js`, uses `tg.ready()`, `tg.expand()`, `tg.setHeaderColor()`, `tg.sendData()`, `tg.showAlert()`. initData HMAC validation is **NOT built** — acceptable while access is private (Tailscale + Telegram button only).
- **Access today:** Telegram button in the Johnny bot chat, works on phone + daily driver. Cloudflare tunnel routing is murky per Johnny's handoff (he thinks it points to `:7891`, not `:7892`) but Austin confirms the button works end-to-end. Don't re-architect tunneling until it actually breaks.

## Standing rules (Mission Board-specific — reinforced here)

- **Feedback is raw-injected into `output-prompt.md`, NOT compiled into rules.** Johnny reads `data/feedback.jsonl` + `data/locked.jsonl` directly at the start of every output turn. **Do not propose a rules file or a hand-curated behavioral surface.** The decision and reasoning are in `johnny/decisions/2026-04-15-feedback-loop-raw-injection.md` — re-read it if you're ever tempted.
- **Upgrade threshold for raw injection is ~40–60 feedback entries.** Beyond that, the upgrade path is retrieval (preferred) or periodic distillation cron. Do not pre-build the upgrade. Watch for the signals: feedback count crossing ~40, repeated mistakes after feedback was captured, Austin flagging that recent feedback isn't being applied.
- **After editing `src/server.js`, restart the LaunchAgent** so the running server picks up the change:
  ```
  ssh mbp "launchctl kickstart -k gui/$(id -u)/com.johnny.mission-board"
  ```
  Frontend edits (`public/index.html`, `src/renderer.js`) don't require a restart — just a browser refresh.
- **Code edits flow laptop → MBP via `scp`** (same pattern used for `output-prompt.md` on 2026-04-15). No local mirror — the `wiki-deploy/` fossil taught that lesson. If you need to read the current state, `ssh mbp cat`. If you need to edit, scp up.
- **Mission Board architectural decisions go to `~/.openclaw/workspace/johnny/decisions/`** — slug pattern `YYYY-MM-DD-mission-board-*`, `YYYY-MM-DD-mini-app-*`, or `YYYY-MM-DD-feedback-*`. Commit + push from inside the workspace so the nightly backup carries them.
- **After Mission Board session changes on the MBP, prompt to commit + sync before ending.** The 4 AM nightly backup catches everything, but explicit session-end commits keep history clean.

## Sibling commands

- **`/johnny`** — pipeline-only variant. Skips Mission Board reads. Use when you need pipeline foundation without the extra Mini App context. Rarely the right choice for Mission Board work since most Mini App sessions benefit from pipeline state.
- **`/johnny-testing`** — end-to-end pipeline verification. Use when running a real Telegram input through the full chain to verify compile → analysis → output is healthy. Not a substitute for `/mission-board`.

## Living command discipline

When we change the Mission Board architecture — new data file, new endpoint, new decision about how feedback flows, new UI surface, new access model — update this command file (`.claude/commands/mission-board.md`) in the same session. The cost of a stale slash command is that next session starts from the wrong map. If you add a new data file to `mission-board/data/`, add it to the core facts section here. If you change the launchctl label, update the kickstart command here. Etc.

## What this command replaces

- **Manual orientation.** No more asking Johnny for a handoff brief every session — he wrote it once at `johnny/mini-app-handoff.md`, and this command reads it automatically.
- **Splitting pipeline and Mini App context across two commands.** Most Mission Board work needs both; this merges them.
