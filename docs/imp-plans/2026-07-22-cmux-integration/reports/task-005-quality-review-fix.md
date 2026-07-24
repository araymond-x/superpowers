---
schema_version: 1
task_id: 5
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "FIX 3 `echo \"${parts[*]}\"` → `printf '%s\\n' \"${parts[*]}\"` (xpg_echo backslash-mangling immunity). FIX 4 hoisted `PICKUP_ARG=\"$(shq \"/pickup $BUNDLE_ID\")\"` to one global assignment consumed at all three former sites (:309 in `build_successor_cmd`, the auto fallback tail, the picker-manual branch) — SSOT plus 2 fewer Python spawns. FIX 5 `[ -n \"$LABEL\" ] && parts+=(…)` → explicit `if/fi`. Plus the reviewer's optional worked-example comment (verbatim real output, verified). Composed output byte-identical."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "FIX 1 added `assert _successor_cmd(r) == \"claude-picker '/pickup b1'\"` to the parametrized `test_picker_manual_when_metadata_degraded` (covers both cases), closing the picker-manual branch's zero-assertion gap. FIX 2 added `test_empty_label_omits_session_label` — `_meta(label=\"\")` asserting `launch=auto` still holds while `--session-label` is absent and the surrounding flags still compose."
tests:
  written: 1
  passing: 1
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v"
  result: PASS
contract_compliance:
  - constraint: "FIX 3/4/5 are pure refactors — composed output must be byte-identical"
    status: compliant
    detail: "Captured 5 composed cases (auto-standard with hostile argv, auto-empty-label, auto-no-args, auto-telemetry-off, picker-manual) against a FIXED tmp path so `$SPAWN_LOG` is stable. `diff before.txt after.txt` → empty, re-verified after the mutation restores and again after the final comment edit."
  - constraint: "Do NOT add `set -u`; bash floor 3.2.57 (construct floor 3.1)"
    status: compliant
    detail: "No `set -u` added. New constructs are `if/fi`, `printf '%s\\n'`, and a plain global assignment — all bash 3.1. Verified empirically: `/bin/bash 3.2.57 -n` clean, and the full 42-test file re-run with `bash` shimmed to /bin/bash 3.2.57 → 42 passed."
  - constraint: "Use `$PYTHON` for Python calls; never pipe a producer into `grep -q` under pipefail"
    status: compliant
    detail: "`PICKUP_ARG` reuses the existing `shq()`, which already calls `$PYTHON`. No new Python invocation and no new pipeline introduced (the change removes two `$PYTHON` spawns)."
  - constraint: "Only two files may be modified; `spawn_handoff_helpers.py` is read-only"
    status: compliant
    detail: "`git show --stat HEAD` = exactly 2 files, 44 insertions / 5 deletions. `spawn_handoff_helpers.py` was read but not written; no new harness knob added."
  - constraint: "Do not remove or narrow the autouse `_hermetic_picker_env` fixture"
    status: compliant
    detail: "Untouched (test file diff is a single +24 hunk in the Task-5 section; the fixture at :271-274 is outside it)."
  - constraint: "Do not take the out-of-scope items (shq rc-propagation, `-x`/picker-missing/`telemetry off` gaps, spawn-id placeholder, 3 Task-4 cleanups)"
    status: compliant
    detail: "`build_successor_cmd`'s error handling is unchanged beyond FIX 4/5 — `shq` still has no rc check and `printf` still supplies the function's exit status. No harness knob added, so none of the three knob-gated tests were attempted. The literal `spawn` spawn-id and the three Task-4 cleanups are untouched (verified by reading the diff)."
  - constraint: "shellcheck --severity=warning introduces no new findings"
    status: compliant
    detail: "Exactly the 2 pre-existing SC2034s (`FEATURE_NAME:60`, `QUOTA_STATUS:197`). `PICKUP_ARG` is consumed on both branches so it adds no SC2034; all three expansion sites are already double-quoted contexts so no SC2086."
---

**Implementation Summary:**
Applied the five bounded review fixes. Script side: `printf '%s\n'` replaces `echo` in `build_successor_cmd` (FIX 3); the thrice-computed `$(shq "/pickup $BUNDLE_ID")` is hoisted to a single `PICKUP_ARG` assignment placed after the function definitions and before the auto/picker-manual branch (FIX 4); the `&&` label guard becomes an explicit `if/fi` (FIX 5). Each carries a *why* comment matching the block's existing convention. Test side: the picker-manual branch's composed command is now asserted (FIX 1), and a new test pins spec §5.4b's empty-label omission rule (FIX 2). The reviewer's optional worked-example comment was added, but only after capturing the string verbatim from a real run.

**Source Files Read:**
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — the full Task-5 block (:283-324) plus `SPAWN_LOG:62`, `SP_HOP:132`, `PICKER_CONTRACT:35`, `PYTHON:17` to confirm `PICKUP_ARG`'s placement is after `shq()` is defined and after `BUNDLE_ID` is set, and that no `set -e` exists.
- `tests/unit/test_spawn_handoff.py` — `_hermetic_picker_env:271`, `_meta:277` (confirmed `label=""` is passed through, not treated as absent), `_spawnable:163`, and the whole Task-5 section.
- `tests/unit/spawn_handoff_helpers.py` (read-only) — `run_spawn`'s PATH/HOME construction and the default `picker_body` answering `--handoff-contract` with `1`, to build the fixed-path baseline capture.
- `docs/imp-plans/2026-07-22-cmux-integration/reports/task-005-quality-review.md` and `task-005-spec-review.md` — the exact mutations to reproduce.
- `docs/imp-plans/2026-07-22-cmux-integration/reports/task-005-implementer-report.md` — prior deviations and the four logged concerns.

**CLAUDE.md Files Read:**
- `CLAUDE.md` (repo root) — "Hook Development Gotchas" (no `set -u`, `$PYTHON` for Python calls, no producer piped into `grep -q` under pipefail) and the shell-lint harness note. No subdirectory CLAUDE.md applies to either modified path.

**Deviations from Plan:**
None. All five fixes applied as specified; nothing from the out-of-scope list taken.

**Self-Review Findings:**

*Mutation proof — FIX 1.* Run against the **final refactored** line (`SUCCESSOR_CMD="claude-picker $PICKUP_ARG"` → `SUCCESSOR_CMD="TOTALLY-BROKEN"`), not the pre-FIX-4 form, so the proof targets shipped code. Result: `test_picker_manual_when_metadata_degraded[env_extra0]` and `[env_extra1]` both **FAILED** with `assert 'TOTALLY-BROKEN' == "claude-picker '/pickup b1'"`. Restored from backup, `bash -n` clean, 42 passed. Before this change the same mutation left 41/41 green.

*Mutation proof — FIX 2.* Run by dropping the FIX-5 guard (making `parts+=("--session-label" "$(shq "$LABEL")")` unconditional), not by reverting to the old `&&` form. Result: `test_empty_label_omits_session_label` **FAILED** — the composed line carried `--telemetry on --session-label '' '/pickup b1'`. Note the `launch=auto` assertion still **held** under the mutation, which confirms the test discriminates on the omission rule specifically and not on preflight. Restored, 42 passed.

*Byte-identity for FIX 3/4/5.* Baseline captured **before** any edit across 5 cases with a fixed tmp path (so `$SPAWN_LOG` interpolates identically): auto-standard (hostile argv `/tmp/a b.md` + `he said "hi"; rm -rf /x`), auto-empty-label, auto-no-args, auto-telemetry-off, picker-manual. `diff before.txt after.txt` → **zero difference**, re-confirmed twice more (post-mutation-restore, and post-comment-edit).

*Worked-example comment accuracy.* The first draft claimed the example was "real output captured by running this script", but the string shown was not one of the five captured cases (the captured auto-standard case also carries `--foo`). Re-ran the script with exactly the inputs the comment names and compared programmatically: after replacing only the absolute log path with `<log>` and unwrapping the line continuations, comment == real output, **True**. Wording corrected to state precisely what is elided. This correction was folded into the same commit via `--amend` (local, unpushed, single-commit-per-task); the final tree has exactly one commit with the required message and exactly the two in-scope files.

*FIX 1 scope choice.* The assertion was added to the parametrized test (2 of the 4 picker-manual cases) per the brief's "at least one". The other three cases (`contract_wrong`, `bad_codec`, `corrupt_v1_body`) still assert mode only — the mutation proof shows 2 failures is sufficient to catch a broken branch, and duplicating the assertion four times would add no discriminating power.

*Verification runs.* `bash -n` clean under both bash 5.3.9 and /bin/bash 3.2.57. `shellcheck --severity=warning` → exactly the 2 pre-existing SC2034s. `tests/unit/test_spawn_handoff.py` → 42 passed (41 + 1). Full `tests/unit/` → **595 passed** (was 594; +1 is consistent with exactly one new collected case). Full file re-run with `bash` shimmed to /bin/bash 3.2.57 → 42 passed. Scratch files removed; `git status` shows no stray untracked files from this round.

*Report-count convention.* `written`/`passing` count **new test functions added in this fix round only**: 1 (`test_empty_label_omits_session_label`, 1 collected case). FIX 1 hardens an existing parametrized test with an added assertion — it is not a new function, which is why the file total moved 41→42 rather than 41→43. The mutation runs are proofs, not tests, and are not counted.

**Concerns:**
None. The three deferred items remain correctly owned by Task 6 and are untouched: the `shq` rc-propagation restructure, the three harness-knob test gaps (`-x` predicate, `picker missing`, `--telemetry off` on the composed line), and the CRITICAL carry-forward that Task 6 must generate `SPAWN_ID` **before** the compose block or re-compose the fallback tail — its plan text as written will not fix the literal `spawn` placeholder.

---

## Controller independent verification (added post-report)

Both mutation proofs were **re-run by the controller**, not accepted from the report:

- **FIX 1 mutation** (`SUCCESSOR_CMD="claude-picker $PICKUP_ARG"` → `"TOTALLY-BROKEN"`): `test_picker_manual_when_metadata_degraded[env_extra0]` and `[env_extra1]` both FAIL. Before this fix round the identical mutation left 41/41 green.
- **FIX 2 mutation** (label guard removed, `--session-label` unconditional): `test_empty_label_omits_session_label` FAILS. Before this fix round the identical mutation left 41/41 green.
- Script restored byte-identical after both (`git diff --stat` empty); `tests/unit/test_spawn_handoff.py` → 42 passed; full `tests/unit/` → **595 passed**.
- Commit `eae39dc`: exactly 2 files, +44/−5. No stray scratch files (`find . -name capture.py` returns only pytest's own vendored module).
