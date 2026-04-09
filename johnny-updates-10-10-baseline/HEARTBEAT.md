# HEARTBEAT.md

## How Johnny Works Now
All work is triggered by Telegram messages: feed inputs (Email/Calendar/Teams/Transcripts) or direct instructions from Austin in DM (chat_id 6461072413). No polling. No scheduled health checks. See **FEED-RULES.md** for full processing rules and ops logging format.

## Scheduled Crons (Still Active)

### Tomorrow's Briefing
- **When:** 9:00 PM CT, Sunday–Thursday
- **What:** Prepare Austin for the next day
- **Where:** Austin's DM (chat_id 6461072413)
- **How:** Read `clearwater/knowledge/hot.md` for current priorities. Read `clearwater/knowledge/index.md` for deal/project status. Check deal-state files for any deals with meetings or deadlines tomorrow. For each deal or project with a pending action or upcoming meeting: current status, next action, urgency. Include any draft work products ready for Austin to send. Present as a concise, actionable briefing. Meeting data comes from hot.md and deal-state files (not calendar.json, which is deprecated).

### Weekly Skill Evolution
- **When:** 9:00 PM CT, Wednesday
- **What:** Analyze artifact deltas, propose prompt improvements for worst-performing skill, test against rubrics, report to Johnny Alerts for approval
- **Where:** Johnny Alerts (chat_id -1003883592748)

### Friday Wiki Lint
- **When:** 7:00 PM CT, Friday
- **What:** Health-check the entire wiki. Find and fix issues before the weekend.
- **Where:** Ops Log (chat_id -5205161230) for findings. Johnny Alerts for critical issues.
- **How:**
  1. **Stale deals** — any deal-state.md with `last_updated` older than 14 days → flag
  2. **Orphan pages** — any deal/project/knowledge file not linked from index.md → flag
  3. **Index drift** — compare index.md entries against actual files in deals/, projects/, knowledge/ → flag mismatches
  4. **hot.md drift** — compare hot.md entries against actual deal statuses and next actions → flag stale entries
  5. **Missing cross-references** — deals that reference people/products without corresponding knowledge pages → flag
  6. **Schema compliance** — spot-check 5 deal-state files for rigid schema conformance (frontmatter, required sections) → flag non-compliant
  7. **Outbound tracking cleanup** — any open entries in outbound-tracking.jsonl older than 14 days → flag for Austin review
  8. **Contradictions** — check if any deal-state status contradicts index.md status → fix
  9. **File sizes** — check all files against thresholds → flag exceeded
- **Output:** Single summary message to Ops Log with all findings. Critical issues (contradictions, orphans) forwarded to Johnny Alerts. Self-fix what can be fixed (contradictions, index drift). Flag everything else for Austin.

### SF Pipeline Sync - Sunday
- **When:** 9:45 PM CT, Sunday
- **What:** Pull all open opportunities via SF CLI, diff against deal state files, present Austin with stale field summary for approval before updating Salesforce
- **Where:** Austin's DM (chat_id 6461072413)

### SF Pipeline Sync - Tuesday
- **When:** 10:00 PM CT, Tuesday
- **What:** Mid-week Salesforce pipeline sync (same process as Sunday)
- **Where:** Austin's DM (chat_id 6461072413)
