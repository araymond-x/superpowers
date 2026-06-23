# Spec Compliance Review — Task 1 (N27 Check 7 archive-aware review-tier inputs)

**Verdict: PASS** — spec compliant AND contract compliant (verified by code inspection + independent test run).

Diff reviewed: `fb5285d..c27fd79` (controller-checkpoint.py + test_pre_completion_gates.py).

- **MISSING — all present.** Archive-globbing (controller-checkpoint.py:248-251), live-wins (live `tiers.update(_classify_dir(reports_dir))` runs LAST, overwriting archived same-id entries), dedup-by-int-task-id (dict keys). All 3 plan test cases present verbatim; 2 are genuine RED (`includes_archived`, `partner_archive`), the 3rd (`live_wins`) is a valid plan-mandated regression guard (implementer honestly flagged it passed pre-change). Mirrors the `find_report_file`/`find_all_report_files` precedent (125-197) as required.
- **Partner `-minimum-tier.md` overlap handled:** `_classify_dir` skips full-glob hits already in `min_paths` and uses `setdefault` (lines 239, 243) — minimum is never downgraded.
- **CONTRACT preserved:** returns `list` of `(int, bool)` 2-tuples (line 253); caller `_ratio_check` unpacks `for (t, m) in ...` unchanged (1490-1492); `else: return []` for unknown review types intact.
- **EXTRA — none.** Scoped to `_review_tiers_per_task` + the new `TestReviewTiersArchiveAware` class only.
- **Python 3.9 — clean.** No `X | Y` unions / lowercase builtin generics on changed lines (annotations are `# type:` comments); `ast.parse` OK.
- **Tests GREEN (independently run):** `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v` → 34 passed (3 new + all pre-existing ratio tests), confirming unchanged single-dir behavior.
- **REPORT COMPLETE:** frontmatter + all 5 prose sections present; Python-3.14-venv caveat in Concerns is honest, not a defect.
