# Task 1 Spec Compliance Review — Script foundation + basic-refusal preconditions

**Verdict: PASS**

## Scope Verified

Diff reviewed: `git diff 56210f1..2557250` (commit `2557250`, "feat(cmux-int): spawn-handoff foundation + basic-refusal preconditions (Task 1)").

Files in commit (exactly 2, matches plan's Files list):
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (new, 76 lines, mode 100755)
- `tests/unit/test_spawn_handoff.py` (modified, +38 lines)

No out-of-scope files present. `sdd-pre-dispatch-hook.sh`, the hook baseline, SKILL.md bodies, and `verify-symlink-install.sh` are untouched by this commit. The two module plan files (`module-1-spawn-script.md`, `module-2-protocol-e2e-docs.md`) show unstaged working-tree checkbox edits from Task 0 — confirmed these are NOT part of commit `2557250` (`git diff 56210f1..2557250 --stat` shows only the two expected files).

## Byte-Level Transcription Check

Programmatically diffed the plan's Step 2 code block (module-1-spawn-script.md, "Task 1 → Step 2") against the committed script content. Result: **exact match except a single trailing newline** after the final `exit 0` (spec's fenced block ends with a newline; the committed file does not). No logic, identifier, or string differs. This is the strongest possible transcription-fidelity result.

## Marker Comments — VERBATIM (load-bearing, checked individually)

All four markers present, byte-exact, at lines 71–74:
```
# (Task 2 inserts bundle validation + cmux + hop preconditions here.)
# (Task 3 inserts the quota check here.)
# (Tasks 4-5 insert launch composition here.)
# (Task 6 inserts the spawn sequence + exit here.)
```
These are the exact strings Tasks 2–6 will replace by string match. No alteration, no premature fill-in.

## Contract Points

- **Shared Constants (no hardcoding):** `MAX_HOPS="${SUPERPOWERS_CMUX_MAX_HOPS:-3}"` and `QUOTA_MIN_PCT="${SUPERPOWERS_CMUX_QUOTA_MIN_PCT:-15}"` — both env-with-default, exactly as specified. Confirmed by direct read, not by report claim.
- **`--show-toplevel` usage:** appears exactly once (`WORKTREE_ROOT="$(git rev-parse --show-toplevel ...)"`), used only for the worktree root. No repo-identity logic (git-common-dir) present in this task — correct; that's a Task 2 concern per the plan and the implementer report correctly marks it `not_applicable`/`compliant` as appropriate.
- **House bash style:** grep confirms no `set -u` anywhere in the script (only the explanatory comment mentions it); no `grep -q` piping pattern present.
- **No Task 2–6 logic leaked into Task 1:** confirmed — everything past Precondition 1 is the four marker comments plus the skeleton `echo …; exit 0`. No bundle validation, cmux ping, hop check, quota, or launch composition code exists yet.
- **Executable:** `git ls-tree 2557250` shows mode `100755`; `ls -la` on the working file confirms `-rwxr-xr-x`.

## Tests

Ran `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v`:
```
6 passed in 0.73s
```
1 Task-0 test (`test_fixtures_shape_matches_contract`) + 5 new Task-1 tests, all PASS.

The 5 new tests match the plan's Step 1 code block verbatim (diffed the committed test append against the plan's fenced Python block — identical apart from `import os` / `import subprocess` placement, which the plan left unspecified in exact position; implementer placed both directly before the `spawn_handoff_helpers` import instead of at the top of the file — cosmetic only, does not affect test behavior, and the implementer's own Deviations section flags this transparently).

Test-strength check (not just "did they pass"):
- `test_script_exists_and_executable` — inspects `os.access(SCRIPT, os.X_OK)`, real check.
- `test_no_bundle_id_exits_1` — runs the real script via subprocess (`spawn_handoff_helpers.run_spawn`, confirmed to shell out to the actual committed script path), asserts both exit code and "BUNDLE_ID" in output. Real exercise of the arg-parse empty-check + usage message.
- `test_unknown_flag_exits_1` — asserts `rc==1` only (no message assertion). This is the weakest of the five, but it matches the plan's own test body verbatim, and by code inspection the `-*)` arm of the arg-parse loop is what's actually hit before any git/worktree logic runs, so it exercises the right code path. Non-blocking; noting for completeness rather than as a defect.
- `test_missing_active_feature_exits_1` — deletes `.active-feature`, commits the removal, re-installs a valid bundle, and asserts both `rc==1` and "active-feature" in output — a real precondition-2-boundary exercise (proves the failure is the `.active-feature` check specifically, not an earlier one).
- `test_dirty_tree_exits_1` — installs a valid bundle then writes an uncommitted file, asserts `rc==1` and "clean" in output — confirms Precondition 1 (clean tree) fires correctly and specifically.

One item from the plan's "Verify" checklist — extra positional arg → exit 1 — has no dedicated automated test in Task 1 (the plan's own Step 1 test list doesn't include one either; it's deferred/implicit). Verified by code inspection instead: the arg-parse `else` branch (`echo "...unexpected extra arg..."; exit 1`) is present and correct. This is a coverage gap inherited from the plan itself, not an implementer omission — noting for completeness, non-blocking.

## Report Completeness

`docs/imp-plans/2026-07-22-cmux-integration/reports/task-001-implementer-report.md` reviewed — all required sections present and populated, none suspiciously empty:
- YAML frontmatter: `task_id`, `status: DONE`, `files_changed` (both files with accurate descriptions), `tests` block (written: 5, passing: 6, command, result), `contract_compliance` (9 constraints itemized, each correctly scoped `not_applicable`/`compliant` for a Task 1 slice — no false compliance claims for later-task concerns).
- Implementation Summary — accurate, matches verified evidence.
- Source Files Read — plan section, helpers, existing test file, pattern-reference hook file.
- CLAUDE.md Files Read — explicitly states none found in the relevant subdirectories, root CLAUDE.md gotchas honored.
- Deviations from Plan — transparently discloses the import-placement ambiguity resolution; correctly framed as plan-directed, not a divergence.
- Self-Review Findings — includes an honest shellcheck note (9 SC2034 "unused variable" warnings for foundation constants that Tasks 2–6 will consume at the marker points) — expected and correctly explained, not concealed.
- Concerns — "No concerns," consistent with the clean verification above.

## Findings Summary

No BLOCKING findings. No CONTRACT/MISSING findings. Two ADVISORY notes (both non-blocking, already covered above): (1) `import os`/`import subprocess` placed mid-file rather than at top of test module — cosmetic; (2) missing trailing newline in the script file — cosmetic, does not affect subsequent tasks' exact-string marker replacement since all markers are mid-file.

**PASS** — spec-compliant, markers intact and verbatim, no out-of-scope files, all tests genuinely exercise the described behavior, report complete and honest.
