---
schema_version: 1
task_id: 1
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "Replaced _review_tiers_per_task (lines 200-233) with the archive-aware version: a _classify_dir inner helper applied to each sorted reports/archive-*/ dir then the live reports dir last (live-wins), deduped by task id, returning the same list of (task_id, is_minimum) tuples."
  - path: "tests/unit/test_pre_completion_gates.py"
    description: "Added TestReviewTiersArchiveAware class (3 tests) after TestGitRealityCheck: archived ids are included, live full wins over archived minimum for a shared id, and partner-review archive globbing works."
tests:
  written: 3
  passing: 3
  command: ".venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v"
  result: PASS
contract_compliance:
  - constraint: "None — no external contract"
    status: not_applicable
    detail: "Task 1 widens an internal glob; no external contract. Output contract (list of (task_id, is_minimum) tuples consumed by _ratio_check) is preserved — verified against the caller at :1468-1475."
---

**Implementation Summary:** Made `controller-checkpoint.py`'s `_review_tiers_per_task` archive-aware by mirroring the existing `find_report_file`/`find_all_report_files` precedent (lines 125-197). It now globs each `reports/archive-*/` directory in sorted (module) order, then the live reports dir last, deduping by globally-unique task id so the live entry wins for any re-reviewed id. The output contract (a list of `(task_id, is_minimum)` tuples) is unchanged, so the caller `_ratio_check` is untouched.

**Source Files Read:** `module-1-aggregate-visibility.md` lines 97-228 (authoritative task); `controller-checkpoint.py` lines 125-197 (the archive-glob + live-wins precedent), 200-233 (edit target), 1455-1484 (the `_ratio_check` caller); imports (lines 35-52, all of `glob`/`os`/`re` present); `tests/unit/test_pre_completion_gates.py` (structure — `_checkpoint` module handle at line 43, `TestGitRealityCheck` at 668, file end at 755).

**CLAUDE.md Files Read:** Repo-root `CLAUDE.md` (the superpowers-fork guide). No subdirectory CLAUDE.md exists in the two modified directories.

**Deviations from Plan:** None — implemented the function-replacement and all 3 test cases verbatim from the on-disk code blocks.

**Self-Review Findings:** (1) Completeness — all 3 plan test cases + the full function replacement are present; commit `c27fd79` contains exactly the 2 scoped files. (2) RED was genuine for the two archive-globbing tests (`includes_archived`, `partner_archive`); the `live_wins` test passed pre-change because the old flat glob already picks the live same-id file — it remains a valid regression guard and the plan mandates all 3. (3) Python 3.9 compatibility — new code uses only `# type:` comments, `.items()`, `glob.glob`, `os.path.join/isdir`, `dict.update/setdefault`; no `X | Y` unions, no lowercase builtin generics; `ast.parse` succeeds. (4) Discipline — only `_review_tiers_per_task` and the new test class changed; no other functions, files, or refactoring touched. The pre-existing single-dir ratio tests (`TestMinimumTierRatioCap`, `TestDeclaredMinimumExclusion`) all still pass, confirming unchanged behavior for archive-free workspaces.

**Concerns:** No concerns. (Note: the venv interpreter is Python 3.14.5, not 3.9; I verified 3.9-syntax safety by inspection and `ast.parse` rather than a real 3.9 runtime, since no 3.9 interpreter is installed here — but the code introduces no version-specific syntax.)
