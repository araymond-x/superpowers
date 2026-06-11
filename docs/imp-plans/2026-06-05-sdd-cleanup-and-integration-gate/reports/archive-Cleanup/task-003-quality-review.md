# Task 3 Code Quality Review (N5+N13)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=3 type=quality-review). Replaces a
> controller-written file logged as a provenance violation in deviations.md.
> Reviewed: commit fef298d against module-1-cleanup.md Task 3 (base 58e875d).
> Resolution of Critical Issue 1: see deviations.md Task 3 rows (controller-applied doc fix).

### Strengths

- **N5 coverage exceeds the plan**: All 7+1 prescribed sites are routed through `_unfenced_content`, plus two additional sites the plan missed — `task_zero_is_first` (controller-checkpoint.py:465) and the `run_pre_completion` verification-ratio `all_task_ids` extraction (controller-checkpoint.py:1296). I grepped both scripts for every `TASK_HEADER_RE`/`TASK_HEADER_PATTERN`/`^###\s+Task` usage: **zero fence-blind task-header parsing sites remain**. The N9 helpers (`_task_ids_where`) parse YAML frontmatter, not headers, so they're correctly unaffected.
- **Sound core design**: blank-line substitution (validate-plan.py:104-124, controller-checkpoint.py:99-119) preserves line count, so `analyse_tasks`'s span measurement against original `lines` stays index-valid — exactly the property the plan demanded. Verified the loop detects headers on `unfenced_lines` (validate-plan.py:182-185) while spans use originals.
- **Audit Order 4 honored**: `get_task_checkbox_range` unfences inside the function body (controller-checkpoint.py:503-504), so fenced headers can't act as section boundaries and fenced checkboxes aren't counted — confirmed by `test_checkbox_range_ignores_fenced_headers`.
- **Tests verify real behavior**: `tests/unit/test_fence_aware_parsing.py` loads the actual scripts via `importlib` (no mocks), and the `_H = "##" + "# Task"` self-hosting guard is a necessary, well-documented trick. The fixture's ```` ```markdown ```` fence also covers the language-tag case.
- **Test results I observed**: target suites `test_fence_aware_parsing.py` + `test_validate_plan.py` + `test_pre_completion_gates.py` = **66 passed, 0 failed**; full unit suite = **426 passed, 0 failed** (no regressions).

### Issues

#### Critical (Must Fix)

1. **N13 is not actually fixed — the backported mkdir lines are the wrong lines at the wrong location** (`docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md:803-804`). This is a **plan defect, not implementer error** — module-1-cleanup.md Step 5 (lines 620-624) prescribed exactly these lines, and the implementer followed it faithfully. But the actual N13 deviation (hardening `deviations.md` rows 21/30) and the shipped test (`tests/unit/test_ssot_minimum_agreement.py:110-111`) say the real fix is `(tmp_path / "hook").mkdir()` + `(tmp_path / "trans").mkdir()` at the top of `test_minimum_signal_agreement` — the drivers `git init` those subdirs before creating them. The plan snippet at line ~881 still lacks them, so it **remains un-runnable as written** (the documented FileNotFoundError fires inside `setup_manifest_workspace` before line 803 ever executes). Worse, the two added lines are pure no-ops: `setup_manifest_workspace` already does `reports_dir.mkdir()` (sdd_test_helpers.py:437), and line 804's `(reports / ".dispatch-log").parent` *is* `reports` — a redundant duplicate of line 803. Net effect: commit `fef298d` claims `fix(N13)` while leaving N13 open and adding dead/misleading content to the snippet. Fix (2 lines of doc): remove plan.md:803-804 and insert the two correct `mkdir()` lines at the top of `test_minimum_signal_agreement` (plan.md:~881), matching the shipped test. Do this before the BACKLOG N13 row flips to done.

#### Important (Should Fix)

2. **`_unfenced_content` duplicated into both scripts** (validate-plan.py:104, controller-checkpoint.py:99 — byte-identical). The plan explicitly prescribed "add the helper to each script," so this is a plan-level decision, but it contradicts the repo's own convention (`_report_utils.py` is "single source of truth — do NOT duplicate logic"; `_midpoint.py` exists precisely because this formula-triplication pattern had to be cleaned up before). Both scripts already import from sibling shared modules, so a shared home costs nothing and standalone invocation is unaffected. The drift risk is concrete: when tilde-fence or unclosed-fence handling is added (see Minor below), it must now be added twice. Acceptable to land as-is given the plan prescribed it, but consolidate into `_report_utils.py` as a small follow-up (Module 1 still has tasks touching `controller-checkpoint.py` — fold it in).

#### Minor (Nice to Have)

3. **Tilde fences (`~~~`) not handled** — I probed: a task header inside `~~~ ... ~~~` is still counted. CommonMark-legal, but repo plans use backticks exclusively; fine to leave with a note.
4. **Unclosed fence at EOF blanks the remainder of the file — untested**. I probed: a real header after an unclosed ``` is dropped. In `validate-plan.py` this fails closed (frontmatter/header mismatch blocker), but in `all_tasks_have_reports` it fails *open* (missing tasks silently skipped). Worth one characterization test documenting the intended behavior.
5. **Two extra routed sites and no Task 3 deviation row**: the beneficial extras (`task_zero_is_first`, `run_pre_completion`) and the implementer-reported "agent timed out, controller committed manually" deviation appear nowhere in the feature's `deviations.md` (no Task 3 rows exist). Per this repo's ledger discipline, both belong there.

### Recommendations

- Fix the N13 backport now (Issue 1) — it's a 4-line doc edit and the context is fresh; re-stamp the BACKLOG row only after.
- When fixing Issue 1, also log the Task 3 deviation rows (Issue 5) in the same pass.
- Schedule the `_unfenced_content` consolidation into `_report_utils.py` alongside the next `controller-checkpoint.py`-touching task in this module (Task 4 touches it next).

### Assessment

**Ready to merge?** With fixes

**Reasoning:** The N5 portion is complete, well-designed, and over-delivers (9 sites routed, 0 fence-blind sites remaining, 66/66 targeted and 426/426 full-suite tests passing). The N13 portion, however, does not fix N13 — the plan prescribed the wrong backport, so the commit falsely closes a tracked BACKLOG item; the trivial doc correction must land before Task 3 can be called done.
