# Context Summary — cmux-integration repo-3 SDD (through Task 4)

> Midpoint context summary (manifest `context_summary_at: 3`). Regenerated at the Task-4-complete handoff boundary. Rich resume guidance is in the handoff bundle's CONTINUE.md; this file is the flight-recorder digest.

## Status: Module 1 active (tasks 0–6). Tasks 0, 1, 2, 3, 4 COMPLETE. Resume at **Task 5**.

| Task | State | Commit | Notes |
|------|-------|--------|-------|
| 0 | ✅ done (reviewed) | `56210f1` | Contract fixtures + harness + prereq assertions. All prereqs live-green. |
| 1 | ✅ done (reviewed) | `2557250` | Script foundation + 5 basic-refusal tests. |
| 2 | ✅ done (reviewed) | `c176b4e` | `validate_bundle()` (git-common-dir identity) + cmux/hop preconditions. |
| 3 | ✅ done (reviewed) | `7131698` + fix `926ab60` | Fail-open quota. **Both plan-snippet defects confirmed empirically** (see below). Fix round added numeric env validation + 3 tests. |
| 4 | ✅ done (reviewed) | `77537bc` | Decode/strip-guard/label/telemetry. **Bash floor determined ≥ 3.2** (plan's "≥4.x" is wrong). Autouse hermetic-env fixture added. |
| 5–6 | ⬜ pending | — | Composition B (auto preflight + compose-side quoting), then spawn sequence/exit codes/`--dry-run`. |
| 7–9 | ⬜ pending | — | Module 2: protocol rewrite, e2e Step 14, docs. Run `transition-module.py` after Task 6. |

Full unit suite: **34/34** on `test_spawn_handoff.py`; **587 passed** across `tests/unit/`. No out-of-scope files touched (hook / baseline / SKILL.md / verify-install all clean, verified per commit).

## ⚠ READ FIRST — the two things that will bite you at Task 5

1. **TEST-ECHO COLLISION.** Task 4's diagnostic echo (`spawn-handoff-session.sh:281`) already emits `--append-system-prompt-file` and `a b.md` to stderr. Task 5's planned `test_auto_mode_composes_exact_command` asserts `"a b.md" in out` against combined stdout+stderr — **it can pass without the compose line ever running.** Anchor Task 5's greps on the `[spawn-handoff] successor command:` / `launch=` line. Discriminating tokens with no Task-4 emitter: `--non-interactive`, `--pick-version 2.1.218`, `--telemetry on`, `--session-label`, `/pickup b1`.
2. **Do not add `set -u`.** `${FORWARDED[*]}` on an empty array raises `unbound variable` under `set -u` on bash 3.2 (the verified floor) while passing on 4.4+. Silent breakage.

## Contract facts frozen (Task 0, verified live)
- `--command <text>` = cmux "send text+Enter after creation" → shell-typed (zsh); composed successor cmd must be POSIX/zsh-safe.
- Picker exports 4 vars every launch path: VERSION/LABEL/ARGS/APPEND_PROMPT. append-file exit-3 is `--non-interactive`-only. `versions/<v>` = executable regular file.
- Repo identity = `realpath(git rev-parse --git-common-dir)`, NOT `--show-toplevel`.
- **Bash floor: construct floor 3.1 (`FORWARDED+=`), verified floor 3.2.57.** Task 9 documents ≥ 3.2.

## Plan-defect ledger (the plan is NOT fully trustworthy as written)
Three confirmed defects so far, all empirically proven by reviewers, all still present in `module-1-spawn-script.md`:
- **Task 3 Step 2 timeout snippet** — command-substitution + background watcher stalls the FULL timeout on the SUCCESS path (fd inheritance by the `sleep` grandchild). Shipped code uses `mktemp` + `wait`.
- **Task 3 Step 2 tool resolution** — the plan's line makes its own Step 1 tests impossible to pass (harness remaps `HOME`). Shipped code adds a default-only `command -v` fallback.
- **Task 4 "Bash version caveat"** — says ≥ 4.x; actual floor is 3.2.

➡ **Treat plan code fences as drafts to verify, not gospel.** Two of three Task-3/4 fences were broken. Have implementers prove the fence works before adopting it.

## Process gotchas for the resuming controller (NOT re-derivable from deviations.md)
1. **Report field rule**: `tests.passing` ≤ `tests.written`, **per-task** counts, not the cumulative file total. Bake into every implementer prompt. (Task 4 used a "collected cases" convention — state whichever you pick.)
2. **Pre-execution audit orders are resolved and folded into the plan** — do NOT re-litigate plan edits visible in `git diff`.
3. **Environment .py file-watcher** cosmetically line-wraps test files post-write — benign; verify tests pass + committed content faithful.
4. **The ambient env is picker-populated.** This machine's own session exports the five `CLAUDE_CODE_PICKER_*`/`ENABLE_TELEMETRY` vars, and `run_spawn` copies `os.environ`. The autouse `_hermetic_picker_env` fixture (Task 4) is **load-bearing** — do not remove or narrow it; Task 5's `env_extra={}` "metadata absent" cases depend on it.
5. **Tick the plan checkboxes before running the next checkpoint.** A missed Step-4 tick FAILed the Task-4 checkpoint this session — the gate works, use it as the verification it is.
6. **Advisor tool ↔ background subagents:** the session before this one died to an unrecoverable API 400 (orphaned `advisor_tool_result` with no paired `server_tool_use`) when an advisor call was in flight as a background agent completed. **Never call advisor while any subagent is live.**

## Enforcement scaffolding (all satisfied through Task 4)
Manifest `.sdd-session.json` (gitignored, on disk): standard tier, active_module_id 1, task_range [0,6], midpoint 3. Per-task: `checkpoint-pre-dispatch-NNN.json` + `partner-review-NNN.md` (Task 0 exempt) + spec + quality reviews, all dispatched (provenance in `reports/.dispatch-log`). Task 3 also has `task-003-quality-review-fix.md` (the `[task 3 fix]` round). Pre-execution-audit.md present (ORDERS_ISSUED → both RESOLVED). Checkpoint 005 PASS, 0 pending deviations.
