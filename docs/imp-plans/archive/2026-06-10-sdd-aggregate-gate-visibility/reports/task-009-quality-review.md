# Task 9 — Code Quality Review (N25b+d+f)

**Verdict:** APPROVED — Ready to merge: Yes
**Range:** `c79531b..077cd92` (every changed line read; slicing equivalence verified empirically; tests run independently)

## Strengths
- `_frontmatter_block` is a genuine SSOT within scope — both consumers (`_task_ids_where:280`, `_integration_test_paths:447`) delegate; zero `find("---")` calls remain in controller-checkpoint.py. Cohesive, well-named, docstring explains the *why* (N25b premature-close hazard).
- Line-anchor fix empirically behavior-preserving: old `content.find("---", 3)` vs new `content[3 : 3 + m.start()]` diffed across 6 cases (well-formed, EOF-no-newline, no-opening, no-closing, empty-body, inline-`---`) — identical bodies in every case except the inline-`---` case being fixed. `3 + m.start()` index arithmetic correct.
- Edge cases correct: empty content, no opening `---`, no closing `^---$` all return `None` matching old short-circuits.
- `_plan_label` computed once (:1696), reused across all three malformed branches (:1708/:1730/:1756); `None`-fallback to "the plan" handles manifest-only mode.
- N25d directory branch correctly nested inside `not os.path.isfile` (:1762-1765).
- Tests verify real behavior, not mocks: `test_directory_path_says_is_a_directory` does a real `mkdir` + subprocess against a real `git init` repo + real JSON parse; line-anchoring tests use a genuine `---` inside a quoted value.
- 3.9-compat respected: `Optional`/`Tuple` (imported); zero PEP-604 unions; regression Category-8 0 FAIL.

## Issues
**Critical:** None. **Important:** None.

**Minor (out of scope, informational):**
1. **Cross-script duplication of the same bug-class.** 7 other sites still use the naive `content.find("---", 3)`: `validators.py:56`, `materialize-manifest.py:48`, `validate-plan.py:540`, `transition-module.py:68`, `validate-report.py:95`, `context-summary.py:165,187`. Correctly NOT a Task 9 defect (plan scoped write to controller-checkpoint.py; `_frontmatter_block` is a local helper). Recommendation: BACKLOG item to promote `_frontmatter_block` into `_report_utils.py` and migrate all 8 sites (true codebase-wide SSOT). The implementer already flagged the `validate-report.py`/`_report_utils` instance in deviations.md.
2. **N25f multi-module attribution is approximate (documented).** `os.path.basename(args.plan_file)` names the active module, which in a multi-module plan may not be the declaring file. Deliberate option-(b) choice for minimal blast radius (plan delegated it). Acceptable; precise attribution = option (a). Not blocking.

## Recommendations
- File a BACKLOG item for the codebase-wide `_frontmatter_block` SSOT migration + the N25f precise-attribution option.
- No code changes required for this task.

## Assessment
**Ready to merge?** Yes
**Reasoning:** Correct, behavior-preserving (empirically verified), SSOT within scope, no dead code, no PEP-604 unions, genuine non-mock tests; 36 C2 + 497 full-suite + 145/0/3 regression all green. Two Minor items pre-existing, out-of-scope, already documented in deviations.md.
