# Meta-Harness — Skill Evolution Architecture

## Overview

Johnny Forsyth improves his own output quality through a weekly self-evaluation cycle. He observes his input-output artifacts, compares his outputs against Austin's actual outputs, diagnoses failure patterns, proposes targeted changes to his skill prompts and harness configs, and validates changes before deploying.

This uses the existing infrastructure at `~/johnny-evolution/` on Johnny's MBP.

---

## The Loop

```
Austin sends input ──► Johnny processes ──► Johnny outputs draft
       │                                          │
       │                                          ▼
       │                                   Austin reviews
       │                                          │
       ▼                                          ▼
Austin sends actual ──► Johnny logs artifact:
output (training)       {input, reasoning_trace, johnny_output,
                         austin_actual, delta, skill_used, timestamp}
                                          │
                                          ▼
                              ~/johnny-evolution/artifacts/
                                          │
                         ┌────────────────┘
                         ▼
                    Weekly cron (Wed 9 PM CT)
                    Johnny collects artifacts with austin_actual
                         │
                         ▼
                    Johnny diagnoses patterns
                    ("Prompt fails to X because Y")
                         │
                         ▼
                    Johnny proposes change to skill prompt
                    OR harness config (SOUL, RULES, HEARTBEAT, etc.)
                         │
                         ▼
                    Johnny runs new version against test cases
                         │
                         ▼
                    Johnny compares scores vs prior version
                    Reports results to Johnny Alerts
                         │
                    ┌────┴────┐
                    ▼         ▼
                Improved   Not improved
                    │         │
                    ▼         ▼
              Wait for     Iterate/discard
              Austin's
              approval
```

---

## What Can Be Evolved

### Layer 1: Harness Configs
Johnny's always-on context files that shape his behavior:

| File | What it controls |
|---|---|
| `SOUL.md` | Core identity, personality, decision style |
| `RULES.md` | Standing policies, communication rules |
| `HEARTBEAT.md` | Check priorities, alert thresholds, routines |
| `AGENTS.md` | Sub-agent architecture |
| `FEED-RULES.md` | How each Telegram feed channel is processed |

### Layer 2: Skill Prompts (at ~/johnny-evolution/skills/)

| Skill | File | What it produces |
|---|---|---|
| `email-drafter` | `prompts/v{N}.md` | Email responses in Austin's voice |
| `teams-drafter` | `prompts/v{N}.md` | Teams message responses |
| `call-summarizer` | `prompts/v{N}.md` | Call/meeting summaries |
| `deal-updater` | `prompts/v{N}.md` | Deal state file updates |
| `meeting-prep` | `prompts/v{N}.md` | Pre-meeting briefing docs |

### Layer 3: Skill Selection Logic
Which skill gets invoked for which input type. If Johnny is using email-drafter when he should be using deal-updater, that's a routing problem the evolution cycle can diagnose.

---

## Artifact Logging (Johnny's responsibility)

For every feed interaction, Johnny writes a structured artifact to `~/johnny-evolution/artifacts/`:

```
~/johnny-evolution/artifacts/
├── email-feed/
│   ├── 2026-04-04_001.json
│   ├── 2026-04-04_002.json
├── calendar-feed/
├── teams-feed/
├── transcripts/
```

Each artifact:
```json
{
  "id": "email-feed-2026-04-04-001",
  "timestamp": "2026-04-04T09:15:00Z",
  "source_channel": "email-feed",
  "input": "the raw input Austin forwarded",
  "reasoning_trace": "what Johnny considered, what rules he applied",
  "skill_used": "email-drafter",
  "skill_version": "v1",
  "johnny_output": "the draft Johnny produced",
  "austin_actual": null,
  "delta": null,
  "scores": null
}
```

When Austin sends a completed output back (training), Johnny updates:
```json
{
  "austin_actual": "what Austin actually sent",
  "delta": "specific differences",
  "scores": {
    "voice": 2,
    "accuracy": 3,
    "task_completion": 1,
    "format": 2,
    "total": 8,
    "pass": true
  }
}
```

---

## Weekly Evolution Cycle (Wednesday 9 PM CT)

A cron triggers Johnny to:
1. Collect all artifacts where `austin_actual` is populated
2. Diagnose failure patterns across all 5 skills
3. Propose a new prompt version for the weakest skill
4. Test it against existing test cases
5. Report results to Johnny Alerts — old score vs new score
6. Wait for Austin's approval before deploying

Austin can also trigger ad-hoc evolution runs by messaging Johnny directly.

---

## Existing Infrastructure (don't rebuild)

### Uses:
- `~/johnny-evolution/skills/` — skill prompts with version directories
- `~/johnny-evolution/candidates/` — candidate harness evaluation logs
- `~/johnny-evolution/benchmark/scenarios/` — benchmark test scenarios
- `clearwater/hyperagent/tests/` — test cases with rubrics
- `clearwater/hyperagent/skills/` — active skill prompts Johnny uses day-to-day
- `evolution_log.jsonl` — full run history

### What changed from original design:
- The evolution proposer is now Johnny himself (via the Wednesday cron), not a separate external agent
- Austin's actual outputs remain the ground truth for scoring
- No bot-to-bot communication needed — Johnny self-evaluates
