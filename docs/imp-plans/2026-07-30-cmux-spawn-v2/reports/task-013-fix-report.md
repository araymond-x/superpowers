---
schema_version: 1
task_id: 13
task_type: implementation
status: DONE
files_changed:
  - path: skills/subagent-driven-development/scripts/spawn-handoff-session.sh
    description: "Fix 1 (Important, quality review round): the N64 bookkeeping commit block previously did `git add \"$HOPS_FILE\" \"$SPAWN_LOG\"` (+ conditional handoff-mechanics.md add) followed by a BARE `git commit -m ...`, which commits the WHOLE index, not just those paths — a concurrent `git add` elsewhere in the ~2-min spawn window would ride along. Kept the `git add` calls (needed so the three bookkeeping files are tracked on their first hop) and added a `BK_PATHS` bash-3.2-safe array, passing `-- \"${BK_PATHS[@]}\"` to `git commit` so only the bookkeeping paths are committed regardless of what else is staged."
  - path: tests/unit/test_spawn_handoff_v2.py
    description: "Added TestBookkeepingCommit::test_staged_stray_does_not_ride_into_bookkeeping_commit — stages (git add, not merely creates) an unrelated file from inside the same extra-injection hook the existing -A discriminator test uses, then asserts the bookkeeping commit excludes it (exact 3-file set) while it remains staged-but-uncommitted afterward. Added TestDurableOutcome::test_unwritable_log_on_timeout_path_still_exit_3 — closes the last untested leg of N63's checked-outcome-write coverage (success and spawn-failed already had fault-injection tests) by forcing CMUX_WAITFOR_RC=1 (timeout) with CMUX_SABOTAGE_ON_WAITFOR targeting the spawn log, asserting exit 3 unchanged, the warn text, and the intent-present/outcome-absent audit-trail gap."
tests:
  written: 2
  passing: 2
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff_v2.py -v (96 passed, 94 pre-existing + 2 new)"
  result: PASS
contract_compliance:
  - constraint: "Bash floor >= 3.2; no set -u/-e/pipefail added"
    status: compliant
    detail: "BK_PATHS is a plain bash array (declared inline, no `declare -a`), append via `+=`, which the file already relies on elsewhere (FORWARDED+=). No set -u/-e/pipefail added or touched; grep for those strings in the diff shows nothing new."
  - constraint: "Explicit git paths only — never git add -A; naive `git commit -- ...` avoided because it errors on untracked first-hop files"
    status: compliant
    detail: "Used the prescribed shape verbatim: kept `git add \"$HOPS_FILE\" \"$SPAWN_LOG\"` (untracked-safe) then `git commit ... -- \"${BK_PATHS[@]}\"` (pathspec-scoped, and since the files were just `git add`-ed they are now tracked/staged, so the pathspec resolves without the untracked-pathspec error a bare `git commit -- <untracked paths>` would raise)."
  - constraint: "Restore mutations by cp+diff, never git checkout --/git stash"
    status: compliant
    detail: "Backed up the fixed script to the scratchpad via `cp`, reverted Fix 1 in place to the bare `git commit` to prove RED, then restored via `cp` from the scratchpad copy + `diff -q` confirming byte-identical restoration. No git checkout/stash used at any point."
  - constraint: "Exit-code invariant intact (success 0, timeout 3, spawn-failed 3)"
    status: compliant
    detail: "Fix 1 only changes the arguments to `git add`/`git commit` inside the success branch's existing warn-and-continue block — no exit/return added or removed. Full suite run confirms test_timeout_path_does_not_commit and the two pre-existing TestDurableOutcome exit-code assertions (0 and 3) still pass, plus the new timeout-leg test asserting exit 3."
---

## Implementation Summary

Applied the two fully-specified fixes from the task-13 adversarial quality review, no scope creep:

**Fix 1** — `spawn-handoff-session.sh`'s bookkeeping-commit block replaced the bare `git commit -m "chore(sdd): record handoff hop $SP_HOP"` with a pathspec-scoped commit (`-- "${BK_PATHS[@]}"`), built from a `BK_PATHS` array seeded with `$HOPS_FILE`/`$SPAWN_LOG` and conditionally extended with `handoff-mechanics.md`. The `git add` calls are unchanged (still required since these files are untracked on hop 1), so no new untracked-pathspec failure mode is introduced.

**Fix 2** (test) — `test_staged_stray_does_not_ride_into_bookkeeping_commit` in `TestBookkeepingCommit`: reuses the existing `cmux_v2_stub(extra=...)` injection point but has the stub `git add` (not merely create) an unrelated file mid-run, after Precondition 1's clean-tree check has already passed. Asserts the bookkeeping commit's file set is exactly the 3 expected artifacts and that the stray remains staged (`git status --porcelain` line starting with `A`) but uncommitted.

**Fix 3** (test) — `test_unwritable_log_on_timeout_path_still_exit_3` in `TestDurableOutcome`: near-copy of the spawn-failed sibling test, driving the timeout leg instead (`CMUX_WAITFOR_RC=1` + `CMUX_SABOTAGE_ON_WAITFOR=1` + `SABOTAGE_TARGET` on the spawn log). Asserts exit 3 (unchanged), the warn text, and the `intent`-present/`outcome`-absent audit-trail gap — closing the one leg of N63's checked-write coverage that had no fault-injection test.

## Deviations

None. All three fixes were applied exactly as specified in the task prompt; no ambiguity required a judgment call.

## Self-Review

- Form C (explicit-paths) committed: `git add skills/.../spawn-handoff-session.sh tests/unit/test_spawn_handoff_v2.py` then `git commit`; verified `git status --porcelain` before commit showed only those two files staged (the pre-existing dirty/untracked SDD artifacts from the task-13 round were left alone).
- Staged-stray test positive-controlled: reverted Fix 1 to the bare `git commit` in place (via a temporary Edit), ran the new test alone — RED, with the failure showing `stray-staged.txt` present in the commit's file list (`AssertionError: ... 'stray-staged.txt' in [...]`), i.e. the defect reproduced exactly as described. Restored via `cp` from a scratchpad backup + `diff -q` confirming byte-identical restoration (never `git checkout --`/`git stash`). Re-ran `TestBookkeepingCommit` (all 9 tests) — GREEN.
- Timeout-leg test added and passing as part of the full 96-test run; not separately mutation-tested (the task instructions marked this positive control "if practical" rather than required, and the RED/GREEN cycle was already spent proving Fix 2 against the actual defect under fix).
- No `set -u`, `set -e`, or `pipefail` added anywhere — confirmed by re-reading the diff (`git diff -- skills/.../spawn-handoff-session.sh` shows only the 4-line block change).
- Exit-code invariant intact: full suite (96 tests) passing, including all existing exit-0/exit-3 assertions across `TestDurableOutcome` and `TestBookkeepingCommit`, plus `bash -n` syntax check on the modified script.

## Concerns

None. Full test suite (`tests/unit/test_spawn_handoff_v2.py`, 96 tests) passes; the controller's full-suite run remains the authoritative gate per the task instructions.
