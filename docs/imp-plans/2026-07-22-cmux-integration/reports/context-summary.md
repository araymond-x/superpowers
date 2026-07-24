# Context Summary — cmux-integration repo-3 SDD (through Task 2)

> Midpoint context summary (manifest `context_summary_at: 3`). Generated at the Task-2-complete handoff boundary. Rich resume guidance is in the handoff bundle's CONTINUE.md; this file is the flight-recorder digest.

## Status: Module 1 active (tasks 0–6). Tasks 0, 1, 2 COMPLETE. Resume at **Task 3**.

| Task | State | Commit | Notes |
|------|-------|--------|-------|
| 0 | ✅ done (reviewed) | `56210f1` | Contract fixtures + harness + prereq assertions. All prereqs live-green (picker `--handoff-contract`=1, 4 cmux symlinks, cmux ping=PONG). DONE_WITH_CONCERNS: cosmetic .py reformat (Accepted). |
| 1 | ✅ done (reviewed) | `2557250` | Script foundation + 5 basic-refusal tests. 4 marker comments in place. |
| 2 | ✅ done (reviewed) | `c176b4e` | validate_bundle() (git-common-dir identity) + cmux/hop preconditions. DONE_WITH_CONCERNS: `.handoff-hops` commit fix in test_hop_limit (Accepted, spec-review-confirmed). |
| 3–6 | ⬜ pending | — | Quota (3, midpoint), launch composition A/B (4,5 — densest), spawn sequence (6). |
| 7–9 | ⬜ pending | — | Module 2: protocol rewrite, e2e Step 14, docs. Run `transition-module.py` after Task 6. |

Full unit suite: 14/14 passing on `test_spawn_handoff.py`. No out-of-scope files touched (hook/baseline/SKILL.md/verify-install all clean).

## Contract facts frozen (Task 0, verified live)
- `--command <text>` = cmux "Send text+Enter to the new workspace after creation" → shell-typed (zsh); composed successor cmd must be POSIX/zsh-safe. (Order-1 audit finding, resolved into Task 0 Step 5.)
- Picker exports 4 vars every launch path: VERSION/LABEL/ARGS/APPEND_PROMPT. append-file exit-3 is `--non-interactive`-only. versions/<v> = executable regular file.
- Repo identity = `realpath(git rev-parse --git-common-dir)`, NOT `--show-toplevel`.

## Process gotchas for the resuming controller (NOT re-derivable from deviations.md)
1. **Report field rule**: implementer report frontmatter `tests.passing` must be ≤ `tests.written` — report PER-TASK counts (tests written this task + how many pass), NOT the cumulative file total. This blocked the Task 2 dispatch until Task 1's report was fixed (6→5). Bake it into every implementer prompt.
2. **Pre-execution audit orders are already resolved + folded into the plan** — do NOT re-litigate the plan edits you'll see in `git diff` (module-1 Task 0 Step 5 `--command` sub-check; module-2 commit-message task numbers 5/6/7→7/8/9).
3. **Environment .py file-watcher** cosmetically reformats (line-wraps) test files post-write — benign, verify tests pass + committed content faithful.
4. **You will hit soft nudge (~300k) again** before Task 9 — hand off at the next clean boundary rather than pushing to a HARD block. (This is why Task 3 is being handed off, not squeezed.)

## Enforcement scaffolding (all satisfied through Task 2)
Manifest `.sdd-session.json` (gitignored, on disk): standard tier, active_module_id 1, task_range [0,6], midpoint 3. Per-task: checkpoint-pre-dispatch-NNN.json + partner-review-NNN.md (Task 0 exempt from partner) + spec + quality reviews, all dispatched (provenance in `reports/.dispatch-log`). Pre-execution-audit.md present (ORDERS_ISSUED → both RESOLVED).
