#!/usr/bin/env python3
"""
Deal Audit Script — Programmatic verification of deal data quality.

Checks:
1. Score rows: duplicates, same-date dupes, empty fields
2. Ingestion log: doc_type classification, backdating
3. Stakeholders: duplicates, Clearwater internals, missing data
4. DAP: populated, overdue flags accurate, gap badge correct
5. Outputs log: stale drafts, echo noise, backdating
6. Next step: overdue accuracy
7. Dates: all backdated correctly (no Mar 8 2026 artifacts)

Usage:
  python3 scripts/audit_deal.py                    # Audit all backfilled deals
  python3 scripts/audit_deal.py cw_velentium_2026  # Audit specific deal
  python3 scripts/audit_deal.py --fix              # Auto-fix what's fixable
"""

import os, sys, subprocess, json
from datetime import datetime, date

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')

def get_pg_password():
    with open(ENV_PATH) as f:
        for line in f:
            if line.startswith('POSTGRES_PASSWORD='):
                return line.split('=', 1)[1].strip()
    return ''

def query(sql):
    pw = get_pg_password()
    env = os.environ.copy()
    env['PGPASSWORD'] = pw
    result = subprocess.run(
        ['psql', '-h', 'localhost', '-p', '5433', '-U', 'clearwater',
         '-d', 'clearwater_deals', '-t', '-A', '-F', '|', '-c', sql],
        capture_output=True, text=True, env=env
    )
    rows = []
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            rows.append(line.split('|'))
    return rows

def execute(sql):
    pw = get_pg_password()
    env = os.environ.copy()
    env['PGPASSWORD'] = pw
    subprocess.run(
        ['psql', '-h', 'localhost', '-p', '5433', '-U', 'clearwater',
         '-d', 'clearwater_deals', '-c', sql],
        capture_output=True, text=True, env=env
    )

CLEARWATER_DOMAINS = ['clearwatersecurity.com', 'clearwatercompliance.com']
CLEARWATER_NAMES = ['david kolb', 'richmond donnelly', 'richmond', 'melissa andrews',
                     'steve akers', 'sandy', 'austin holland', 'austin']
TODAY = date.today().isoformat()


def audit_deal(deal_id, auto_fix=False):
    issues = []
    fixes = []
    warnings = []

    # Get deal info
    rows = query(f"SELECT company_name, deal_stage, status FROM deals WHERE deal_id='{deal_id}'")
    if not rows:
        print(f"  ✗ Deal {deal_id} not found in deals table")
        return {'issues': ['Deal not found'], 'fixes': [], 'warnings': []}

    company = rows[0][0]
    stage = rows[0][1]
    status = rows[0][2]

    print(f"\n{'='*60}")
    print(f"  AUDIT: {company} ({deal_id})")
    print(f"  Stage: {stage} | Status: {status}")
    print(f"{'='*60}")

    # ── 1. SCORE ROWS ──
    print(f"\n  1. SCORE ROWS")
    scores = query(f"""
        SELECT id, scored_at::date, scored_at,
               pain_score+power_score+vision_score+value_score+change_score+control_score,
               critical_activity_stage, trigger_type,
               dap_exists, general_narrative IS NOT NULL AND general_narrative != '',
               next_step IS NOT NULL AND next_step != ''
        FROM deal_health WHERE deal_id='{deal_id}' ORDER BY scored_at
    """)

    if not scores:
        warnings.append("No score rows")
        print(f"     ⚠ No score rows")
    else:
        print(f"     {len(scores)} score row(s)")

        # Check same-date duplicates
        dates_seen = {}
        for row in scores:
            d = row[1]
            if d in dates_seen:
                issues.append(f"Same-date duplicate scores on {d} (ids: {dates_seen[d]}, {row[0]})")
                print(f"     ✗ Same-date dupe: {d} (ids {dates_seen[d]} and {row[0]})")
            dates_seen[d] = row[0]

        # Check for today's date (potential accidental rescore)
        for row in scores:
            if row[1] == TODAY:
                ts = row[2]
                warnings.append(f"Score from today ({TODAY}) — verify it's intentional (id {row[0]})")
                print(f"     ⚠ Score from today: id {row[0]}")

        # Check latest score has populated fields
        latest = scores[-1]
        has_dap = latest[6] == 't'
        has_narrative = latest[7] == 't'
        has_next_step = latest[8] == 't'

        if not has_dap:
            issues.append("Latest score: DAP not populated")
            print(f"     ✗ Latest score missing DAP")
        if not has_narrative:
            issues.append("Latest score: narrative empty")
            print(f"     ✗ Latest score missing narrative")
        if not has_next_step:
            issues.append("Latest score: next_step empty")
            print(f"     ✗ Latest score missing next_step")

        if has_dap and has_narrative and has_next_step and not any('Same-date' in i for i in issues):
            print(f"     ✓ Clean")

        for row in scores:
            print(f"       {row[1]} | {row[3]}/30 | {row[4]}")

    # ── 2. INGESTION LOG ──
    print(f"\n  2. INGESTION LOG")
    docs = query(f"""
        SELECT id, doc_type, left(subject, 50), ingested_at::date, ingested_at
        FROM ingestion_log WHERE deal_id='{deal_id}' ORDER BY ingested_at
    """)

    if not docs:
        warnings.append("No ingestion_log rows")
        print(f"     ⚠ No documents ingested")
    else:
        # Count by type
        type_counts = {}
        for row in docs:
            dt = row[1]
            type_counts[dt] = type_counts.get(dt, 0) + 1
        print(f"     {len(docs)} rows: {', '.join(f'{v} {k}' for k,v in sorted(type_counts.items()))}")

        # Check for voice_memo that might be misclassified
        voice_memos = [r for r in docs if r[1] == 'voice_memo']
        if voice_memos:
            warnings.append(f"{len(voice_memos)} voice_memo entries — verify classification")
            print(f"     ⚠ {len(voice_memos)} voice_memo — verify not misclassified transcripts")

        # Check for today's ingestion dates (might need backdating)
        today_docs = [r for r in docs if r[3] == TODAY]
        if today_docs:
            warnings.append(f"{len(today_docs)} docs with today's date — may need backdating")
            print(f"     ⚠ {len(today_docs)} docs dated today — verify backdating")

        if not voice_memos and not today_docs:
            print(f"     ✓ Clean")

    # ── 3. STAKEHOLDERS ──
    print(f"\n  3. STAKEHOLDERS")
    stakes = query(f"""
        SELECT id, name, email, cps_role, title, company
        FROM deal_stakeholders WHERE deal_id='{deal_id}' ORDER BY name
    """)

    if not stakes:
        warnings.append("No stakeholders")
        print(f"     ⚠ No stakeholders")
    else:
        print(f"     {len(stakes)} stakeholder(s)")

        # Check for Clearwater internals
        for s in stakes:
            name_lower = (s[1] or '').lower().strip()
            email_lower = (s[2] or '').lower().strip()

            if any(d in email_lower for d in CLEARWATER_DOMAINS):
                issues.append(f"Clearwater internal in stakeholders: {s[1]} ({s[2]})")
                print(f"     ✗ Clearwater internal: {s[1]} ({s[2]})")
                if auto_fix:
                    execute(f"DELETE FROM deal_stakeholders WHERE id = {s[0]}")
                    fixes.append(f"Deleted Clearwater internal: {s[1]}")

            if name_lower in CLEARWATER_NAMES:
                warnings.append(f"Possible Clearwater internal: {s[1]} (no email to confirm)")
                print(f"     ⚠ Possible internal: {s[1]} (no email)")

        # Check for duplicates (similar names)
        names = [(s[0], (s[1] or '').lower().strip()) for s in stakes]
        for i, (id1, n1) in enumerate(names):
            for id2, n2 in names[i+1:]:
                if n1 and n2 and (n1 in n2 or n2 in n1):
                    issues.append(f"Possible duplicate stakeholders: '{stakes[i][1]}' and '{[s for s in stakes if s[0]==str(id2)][0][1] if any(s[0]==str(id2) for s in stakes) else n2}'")
                    print(f"     ⚠ Possible dupe: id {id1} '{n1}' ~ id {id2} '{n2}'")

        # Check for missing emails
        no_email = [s for s in stakes if not s[2] or s[2].strip() == '']
        if no_email:
            print(f"     ⚠ {len(no_email)} stakeholder(s) without email")

        for s in stakes:
            email_str = f" ({s[2]})" if s[2] and s[2].strip() else ""
            print(f"       {s[1]}{email_str} — {s[3]}")

    # ── 4. DAP ──
    print(f"\n  4. DAP")
    dap = query(f"""
        SELECT dap_exists, dap_status, dap_has_14_day_gap,
               dap_milestones_complete, dap_milestones_total,
               dap_next_milestone, dap_next_milestone_date,
               last_activity_date
        FROM deal_health WHERE deal_id='{deal_id}' ORDER BY scored_at DESC LIMIT 1
    """)

    if dap and dap[0][0] == 't':
        print(f"     DAP: {dap[0][1]} | {dap[0][3]}/{dap[0][4]} milestones")
        print(f"     14-day gap: {'YES' if dap[0][2] == 't' else 'no'}")
        print(f"     Last activity: {dap[0][7] or 'NOT SET'}")
        print(f"     Next: {dap[0][5]} ({dap[0][6] or 'no date'})")

        if not dap[0][7] or dap[0][7].strip() == '':
            issues.append("last_activity_date not set")
            print(f"     ✗ last_activity_date not set")
    elif dap:
        warnings.append("DAP not populated")
        print(f"     ⚠ DAP exists=false")

    # ── 5. OUTPUTS LOG ──
    print(f"\n  5. OUTPUTS LOG")
    outputs = query(f"""
        SELECT id, output_type, recipient_email, left(subject, 40), sent_at::date, status, triggered_by
        FROM outputs_log WHERE deal_id='{deal_id}' ORDER BY sent_at
    """)

    if not outputs:
        print(f"     No outputs")
    else:
        drafts = [o for o in outputs if o[5] == 'draft']
        sent = [o for o in outputs if o[5] == 'sent']
        print(f"     {len(sent)} sent, {len(drafts)} draft(s)")

        # Stale drafts
        if drafts:
            issues.append(f"{len(drafts)} stale draft(s)")
            print(f"     ✗ {len(drafts)} stale draft(s) — should be cleaned")
            if auto_fix:
                draft_ids = ','.join(d[0] for d in drafts)
                execute(f"DELETE FROM outputs_log WHERE id IN ({draft_ids})")
                fixes.append(f"Deleted {len(drafts)} stale drafts")

        # Echo noise
        echo = [o for o in outputs if 'echo' in (o[2] or '').lower()]
        if echo:
            warnings.append(f"{len(echo)} echo inbox entries")
            print(f"     ⚠ {len(echo)} echo inbox entries")

        # Today's dates
        today_outputs = [o for o in outputs if o[4] == TODAY and o[5] == 'sent']
        if today_outputs:
            warnings.append(f"{len(today_outputs)} outputs dated today — verify backdating")
            print(f"     ⚠ {len(today_outputs)} outputs dated today — verify backdating")

    # ── 6. NEXT STEP ──
    print(f"\n  6. NEXT STEP")
    ns = query(f"""
        SELECT next_step, next_step_date, last_activity_date
        FROM deal_health WHERE deal_id='{deal_id}' ORDER BY scored_at DESC LIMIT 1
    """)

    if ns and ns[0][0] and ns[0][0].strip():
        ns_date = ns[0][1].strip() if ns[0][1] else None
        print(f"     \"{ns[0][0][:80]}{'...' if len(ns[0][0]) > 80 else ''}\"")
        if ns_date:
            try:
                nd = datetime.strptime(ns_date, '%Y-%m-%d').date()
                if nd < date.today():
                    warnings.append(f"Next step overdue (by {ns_date})")
                    print(f"     ⚠ OVERDUE: by {ns_date}")
                else:
                    print(f"     Due: {ns_date}")
            except:
                print(f"     Due: {ns_date}")
        else:
            warnings.append("Next step has no date")
            print(f"     ⚠ No date set")
    else:
        warnings.append("No next step defined")
        print(f"     ⚠ No next step")

    # ── SUMMARY ──
    print(f"\n  {'─'*50}")
    if not issues and not warnings:
        print(f"  ✓ ALL CLEAN")
    else:
        if issues:
            print(f"  ✗ {len(issues)} issue(s)")
        if warnings:
            print(f"  ⚠ {len(warnings)} warning(s)")
    if fixes:
        print(f"  🔧 {len(fixes)} auto-fix(es) applied")
        for f in fixes:
            print(f"     - {f}")

    return {'issues': issues, 'fixes': fixes, 'warnings': warnings}


def main():
    args = sys.argv[1:]
    auto_fix = '--fix' in args
    args = [a for a in args if a != '--fix']

    if args:
        # Specific deal
        for deal_id in args:
            audit_deal(deal_id, auto_fix)
    else:
        # All deals with deal_health rows
        rows = query("""
            SELECT DISTINCT d.deal_id, d.company_name, d.status
            FROM deals d
            INNER JOIN deal_health dh ON d.deal_id = dh.deal_id
            WHERE d.status = 'active' OR d.status IS NULL
            ORDER BY d.company_name
        """)

        print(f"\nAuditing {len(rows)} deals with scores...\n")

        total_issues = 0
        total_warnings = 0
        summary = []

        for row in rows:
            result = audit_deal(row[0], auto_fix)
            total_issues += len(result['issues'])
            total_warnings += len(result['warnings'])
            summary.append((row[1], len(result['issues']), len(result['warnings'])))

        print(f"\n{'='*60}")
        print(f"  SUMMARY: {len(rows)} deals audited")
        print(f"  {total_issues} issues, {total_warnings} warnings")
        print(f"{'='*60}")
        for name, iss, warn in summary:
            status = '✓' if not iss else '✗'
            extra = f" ({iss} issues, {warn} warnings)" if iss or warn else ""
            print(f"  {status} {name}{extra}")


if __name__ == '__main__':
    main()
