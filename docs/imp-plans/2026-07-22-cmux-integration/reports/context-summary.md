# Context Summary — cmux-integration repo-3 SDD (through Task 5)

> Midpoint context summary (manifest `context_summary_at: 3`). Regenerated at the Task-5-complete handoff boundary. Rich resume guidance is in the handoff bundle's CONTINUE.md; this file is the flight-recorder digest.

## Status: Module 1 active (tasks 0–6). Tasks 0–5 COMPLETE. Resume at **Task 6** (last task of Module 1).

| Task | State | Commit | Notes |
|------|-------|--------|-------|
| 0 | ✅ done (reviewed) | `56210f1` | Contract fixtures + harness + prereq assertions. All prereqs live-green. |
| 1 | ✅ done (reviewed) | `2557250` | Script foundation + 5 basic-refusal tests. |
| 2 | ✅ done (reviewed) | `c176b4e` | `validate_bundle()` (git-common-dir identity) + cmux/hop preconditions. |
| 3 | ✅ done (reviewed) | `7131698` + fix `926ab60` | Fail-open quota. **Both plan-snippet defects confirmed empirically.** Fix round added numeric env validation + 3 tests. |
| 4 | ✅ done (reviewed) | `77537bc` | Decode/strip-guard/label/telemetry. **Bash floor ≥ 3.2** (plan's "≥4.x" is wrong). Autouse hermetic-env fixture added. |
| 5 | ✅ done (reviewed) | `e7d5fe1` + fix `eae39dc` | Auto preflight + compose-side quoting. **First task with NO plan-fence defect.** Quality review "with fixes" → 5 fixes → **re-review PASS**. |
| 6 | ⬜ **NEXT** | — | Spawn sequence, reservation ordering, exit codes, `--dry-run`. **Carries a required plan deviation — see ⚠ below.** |
| 7–9 | ⬜ pending | — | Module 2: protocol rewrite, e2e Step 14, docs. Run `transition-module.py` after Task 6. |

Full unit suite: **42/42** on `test_spawn_handoff.py`; **595 passed** across `tests/unit/`. Checkpoint 006 PASS, 0 pending deviations, working tree clean at `db25500`. Module 1 at **71%** of checkboxes (27/38).

## ⚠ READ FIRST — the two things that will bite you at Task 6

1. **THE SPAWN-ID PLACEHOLDER — Task 6's plan text WILL NOT FIX IT.** Both the spec reviewer and the quality re-reviewer independently confirmed this. The auto-mode `SUCCESSOR_CMD` composed in Task 5 embeds `printf '%s %s runtime-picker-failure hop=%s\n' "$(date …)" spawn "$SP_HOP"` — the second field is the **literal word `spawn`**, not the spawn uuid that spec §5.4d's log format requires. The string is baked at compose time; `module-1-spawn-script.md` Task 6 Step 2 generates `SPAWN_ID` *after* the dry-run short-circuit, i.e. **after** the compose block. **Task 6 must deviate from its own plan text**: either generate `SPAWN_ID` before the compose block, or re-compose the fallback tail once the id exists. Shipping the plan verbatim ships a §5.4d contract violation.
2. **Task 6 is the test-debt sweep point.** A substantial list has accumulated in `deviations.md` → "Deferred Work" → "Task 6 test-debt sweep". Read that section in full before writing the Task-6 dispatch. Highlights: the two env-validation regression tests (from the Task-3 fix round), the Task-4 cleanup trio (`max(0,…)` label slice, surrogate `try`-wrap, `mkdir` gating), and **six mutation-proven gaps** from the Task-5 reviews — the `-x` half of the version predicate, `command -v claude-picker`, `--telemetry off` on the composed line (these three need a new knob in `spawn_handoff_helpers.py`, which Task 6 MAY modify), `shq` rc-propagation, `_successor_cmd`'s `lines[0]` newline truncation, and the contract probe's missing timeout.

## Contract facts frozen (Task 0, verified live)
- `--command <text>` = cmux "send text+Enter after creation" → shell-typed (zsh); composed successor cmd must be POSIX/zsh-safe.
- Picker exports 4 vars every launch path: VERSION/LABEL/ARGS/APPEND_PROMPT. append-file exit-3 is `--non-interactive`-only. `versions/<v>` = executable regular file.
- Repo identity = `realpath(git rev-parse --git-common-dir)`, NOT `--show-toplevel`.
- **Bash floor: construct floor 3.1 (`FORWARDED+=`), verified floor 3.2.57.** Task 9 documents ≥ 3.2.
- Composed flag order (spec.md:157, verified exact): `claude-picker --non-interactive --pick-version <v> --telemetry <on|off> [--session-label <l>] <forwarded args> "/pickup <id>"`.

## Plan-defect ledger (the plan is NOT fully trustworthy as written)
Three confirmed defects, all empirically proven by reviewers, all still present in `module-1-spawn-script.md`:
- **Task 3 Step 2 timeout snippet** — command-substitution + background watcher stalls the FULL timeout on the SUCCESS path. Shipped code uses `mktemp` + `wait`.
- **Task 3 Step 2 tool resolution** — the plan's line makes its own Step 1 tests impossible to pass. Shipped code adds a default-only `command -v` fallback.
- **Task 4 "Bash version caveat"** — says ≥ 4.x; actual floor is 3.2.

**Task 5 broke the streak** — its Step-2 fence was correct as written and adopted verbatim (spec reviewer re-derived and executed it). So the ledger stays at 3, not 4. **But see ⚠ #1: Task 6's plan text has a fourth, different kind of defect — an ordering defect, not a syntax one.**

➡ **Treat plan code fences as drafts to verify, not gospel.** Have implementers prove the fence works before adopting it.

## Process gotchas for the resuming controller (NOT re-derivable from deviations.md)
1. **Report field rule**: `tests.passing` ≤ `tests.written`, **per-task** counts, not the cumulative file total. Bake into every implementer prompt.
2. **The plan's Step-3 `-k` filters are contaminated.** Task 5's `-k "auto or picker_manual or contract or codec"` also selects the pre-existing `test_fixtures_shape_matches_contract` (substring `contract`). Check any `-k` the plan gives you with `--collect-only -q` before letting an implementer derive counts from it.
3. **Mutation-test the assertions, don't just read them.** This is what caught the two real gaps in Task 5: the plan's own compose assertion passes with `shq()` replaced by an identity function, and the entire picker-manual composed command could be replaced with `"TOTALLY-BROKEN"` with 41/41 still green. Ask implementers to prove a new test FAILS when the behavior is broken.
4. **Environment .py file-watcher** cosmetically line-wraps test files post-write — benign; verify tests pass + committed content faithful.
5. **The ambient env is picker-populated.** The autouse `_hermetic_picker_env` fixture (Task 4) is **load-bearing** — do not remove or narrow it.
6. **Tick the plan checkboxes before running the next checkpoint.** A missed tick FAILed the Task-4 checkpoint.
7. **Advisor tool ↔ background subagents:** an earlier session died to an unrecoverable API 400 (orphaned `advisor_tool_result`) when an advisor call was in flight as a background agent completed. **Never call advisor while any subagent is live** — only in the quiet gap between a completed review and the next dispatch.
8. **Do NOT add `set -u`** to `spawn-handoff-session.sh`. `${FORWARDED[*]}` on an empty array raises `unbound variable` under `set -u` on bash 3.2 while passing on 4.4+. Silent breakage on the supported floor.
9. **Disposition deviations before dispatching.** The pre-dispatch hook hard-blocks on any `| Pending |` row. Log concerns after a task, then disposition them once its reviews land — otherwise the next dispatch is blocked.

## Enforcement scaffolding (all satisfied through Task 5)
Manifest `.sdd-session.json` (gitignored, on disk): standard tier, active_module_id 1, task_range [0,6], midpoint 3. Per-task: `checkpoint-pre-dispatch-NNN.json` + `partner-review-NNN.md` (Task 0 exempt) + spec + quality reviews, all dispatched (provenance in `reports/.dispatch-log`). Tasks 3 and 5 also have `task-00N-quality-review-fix.md` (fix rounds); Task 5's quality-review file carries the **re-review PASS** appended at the bottom. Pre-execution-audit.md present (ORDERS_ISSUED → both RESOLVED). **Checkpoint 006 PASS**, 0 pending deviations.
