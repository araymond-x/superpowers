# Spec Compliance Review — Task 2 (N27 Check 9 archive-aware dispatch-log merge)

**Verdict: PASS** — spec + contract compliant (verified by code reading + test run). Diff `c27fd79..9039c97`.

- **`_merged_dispatch_times` present + correct ordering** (controller-checkpoint.py:325-358): archives `sorted(glob.glob(...archive-*/.dispatch-log))` ingested FIRST, live `dispatch_log_path` LAST → later wins per task id (confirmed by `test_merged_dispatch_times_live_overwrites`).
- **`_ingest`** (342-352): no-ops missing files; swallows OSError. Correct.
- **Rewire** (374-381): `os.path.isfile` guard dropped → `if not verification_ids: return []` then `_merged_dispatch_times(dispatch_log_path)`. Correct.
- **LOAD-BEARING CONTRACT verified:** regex `(\S+)\s+DISPATCH\s+implementer\s+task=(\d+)\s+type=implementer` empirically probed — `type=fix` NO match, `type=fix-unattributed` NO match, `type=implementer` match. `test_merged_dispatch_times_ignores_fix_lines` feeds both fix-line types and asserts `== {}` (PASS). Fix lines can NEVER open a Check-9 window.
- **UNCHANGED loop:** findings/sorted_tasks/window/git-log loop below the rewire is byte-identical to the original (full read).
- **Dropped-guard safety:** pre-existing `test_missing_dispatch_log_passes` ({3}, nonexistent path → empty map → []) still PASSES.
- **EXTRA — none.** Exactly 2 files; single commit `9039c97`. (`TestReviewTiersArchiveAware` in diff context is Task 1's, pre-existing.)
- **Python 3.9 — clean.** `# type:` comments only; source parses.
- **Tests:** `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v` → **38 passed** (all 4 new).

**ADVISORY (non-blocking, pre-existing):** the regex is not end-anchored, so a hypothetical `type=implementer-fix` would match — but it is verbatim from spec, identical to the replaced original code, not a real dispatch-log type, and not a regression introduced by this task.

**Controller disposition:** PASS. The advisory is pre-existing spec behavior, not introduced here — no action.
