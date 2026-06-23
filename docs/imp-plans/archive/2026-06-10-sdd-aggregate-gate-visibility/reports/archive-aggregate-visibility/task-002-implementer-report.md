---
schema_version: 1
task_id: 2
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "Added module-level _merged_dispatch_times (globs reports/archive-*/.dispatch-log sorted=module order, ingests archives FIRST then the live log LAST for latest-wins per task id; nested _ingest no-ops on missing files and swallows OSError; parses ONLY type=implementer lines). Rewired _check_verification_git_reality to drop the os.path.isfile guard (now `if not verification_ids: return []`) and replace the inline parser with a call to _merged_dispatch_times. The findings/window/git-log loop is unchanged."
  - path: "tests/unit/test_pre_completion_gates.py"
    description: "Added TestCheck9ArchiveAware (4 tests): merged map includes archived log; live overwrites archived for same id (latest wins); ignores type=fix / type=fix-unattributed lines (asserts {}); archived-window file-modification FAILs after the merge (live-only read previously skipped it)."
tests:
  written: 4
  passing: 4
  command: ".venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v"
  result: PASS
contract_compliance:
  - constraint: "Dispatch-log grammar: ONLY type=implementer lines open a Check-9 verification window"
    status: compliant
    detail: "_merged_dispatch_times regex (\\S+)\\s+DISPATCH\\s+implementer\\s+task=(\\d+)\\s+type=implementer is byte-identical to the original inline parser; the literal 'DISPATCH implementer ... type=implementer' requirement means type=fix and type=fix-unattributed lines cannot match. test_merged_dispatch_times_ignores_fix_lines feeds one of each and asserts the merged map == {}."
---

**Implementation Summary:** Added `_merged_dispatch_times(dispatch_log_path)` immediately above `_check_verification_git_reality` in `controller-checkpoint.py`. It globs `reports/archive-*/.dispatch-log` (sorted = lexicographic = module order) and ingests them FIRST, then ingests the live `dispatch_log_path` LAST, so a re-dispatched task id's latest timestamp wins. The nested `_ingest` helper no-ops on nonexistent files and swallows `OSError`. Rewired `_check_verification_git_reality` to drop the `os.path.isfile(dispatch_log_path)` guard (now `if not verification_ids: return []`) and replace the inline parser with `dispatch_times = _merged_dispatch_times(dispatch_log_path)`. The findings/window/git-log loop below is unchanged. TDD: 4 tests in new class `TestCheck9ArchiveAware` written first → RED (tests 1-3 AttributeError; test 4 `findings == []` because live-only read skipped the archived task) → helper+rewire → GREEN. Commit `9039c97`.

**Source Files Read:**
- `controller-checkpoint.py` — `_check_verification_git_reality` (anchor text at lines 337-349, NOT the plan's stale "317-329"); `find_report_file`/`find_all_report_files` (archive-glob + sorted precedent); imports (glob/os/re present); production call site lines 1587-1607 — BOTH manifest-mode and `--reports-dir` mode place `.dispatch-log` directly in the reports dir, so `os.path.dirname(dispatch_log_path)` lands on the archive-containing dir → N27 works in the real post-transition path, not just hand-built test trees.
- `tests/unit/test_pre_completion_gates.py` — existing imports (os/shutil/tempfile), `_init_temp_git_repo`/`_commit_file_at`, `TestGitRealityCheck` style.
- Plan: module-1-aggregate-visibility.md Task 2 only (lines 232-405).

**CLAUDE.md Files Read:**
- Repo-root CLAUDE.md — SDD gate scripts must be Python-3.9-safe stdlib: no `X | Y` unions, no lowercase `list[]`/`dict[]` annotations; use `# type:` comments. New helper uses only `# type: (str) -> dict` and `# type: dict` (scan CLEAN).
- No subdirectory CLAUDE.md in `skills/subagent-driven-development/scripts/` or `tests/unit/`.

**Deviations from Plan:** None. Implemented the plan's code blocks verbatim. The plan's line numbers were stale (Task 1 shifted functions down ~20 lines, as warned); located by function name + anchor text and confirmed the quoted OLD block matched on-disk before editing.

**Self-Review Findings:**
- Completeness: helper added, rewire done, 4 tests RED→GREEN, committed `9039c97`, only the 2 scoped files touched.
- type=implementer-only invariant: verified by the unchanged regex + the dedicated fix-lines test.
- Python 3.9 safety: scan found no PEP-604 unions or lowercase generics; full source parses.
- Regression guard `test_missing_dispatch_log_passes` ({3}, nonexistent path → []) still PASSES (dropped `os.path.isfile` guard handled internally via empty merged map → []).
- Full suite: 473 passed. Regression: 145 PASS / 3 advisory WARNING / 0 FAIL.

**Concerns:**
- **Docstring "5 documented archive-aware lookups (see CLAUDE.md)" vs CLAUDE.md's current "3":** The new docstring matches the plan's prescribed text. CLAUDE.md currently documents 3 archive-aware lookups (N4's two + N10's Check 5). Task 1 + Task 2 bring the code total to 5; Task 12 (planned) updates CLAUDE.md to 5 sites and Task 13 verifies. Flagged so the cross-task reconciliation isn't lost — out of this task's two-file scope guard.
- The `sorted(glob(...))` lexicographic-as-module-order assumption matches the existing `find_report_file`/N4 precedent; live-ingests-last makes re-dispatch latest-wins robust regardless of archive ordering. Consistent with precedent, not a new risk.
