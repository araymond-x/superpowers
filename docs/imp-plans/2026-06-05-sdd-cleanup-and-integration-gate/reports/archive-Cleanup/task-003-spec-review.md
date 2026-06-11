# Task 3 Spec Compliance Review (N5+N13)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=3 type=spec-review). Replaces a
> controller-written file logged as a provenance violation in deviations.md.
> Reviewed: commit fef298d against module-1-cleanup.md Task 3 (base 58e875d).

**PASS — Spec compliant AND contract compliant**

Independently verified by reading the full diff (`58e875d..fef298d`), the current state of both scripts, the test file, the N13 plan edit, and the implementer report, and by re-running all test commands.

**Site-by-site verification (grep + read, not trusted from report):**

validate-plan.py — all 3 spec'd sites routed through `_unfenced_content`:
1. `extract_task_numbers` (validate-plan.py:161) — `TASK_HEADER_RE.findall(_unfenced_content(content))` ✓
2. `analyse_tasks` (validate-plan.py:180) — header detection iterates `unfenced_lines`; span measurement remains index-based (`end_idx - start_idx`, last-task fallback `len(lines)` against original lines). The helper preserves line count (fenced/delimiter lines become `"\n"`), so indices stay valid — the "keep original lines for span measurement" requirement is satisfied via line-count preservation ✓
3. `check_sections` Task 0 (validate-plan.py:289-295) — both the Task 0 search AND the `first_task` is-first check use `unfenced_full` ✓

controller-checkpoint.py — all 4+1 spec'd sites routed:
1. `count_tasks` (:127) ✓
2. `has_task_zero` (:457) ✓
3. `get_task_checkbox_range` (:504) — unfences INTERNALLY at the top of the function body, per Audit Order 4 (test passes raw fenced content) ✓
4. `all_tasks_have_reports` (:539) — the 8th site ✓

**Helper:** `_unfenced_content` matches the plan's exact implementation in both scripts (in_fence toggle, fence-delimiter and fenced lines → `"\n"`). Duplication into each script is per-spec ("Add a helper function to each script").

**Tests:** `tests/unit/test_fence_aware_parsing.py` is verbatim per the plan — all 6 tests present (3 TestValidatePlanFenceAware + 3 TestCheckpointFenceAware), including the SELF-HOSTING GUARD `_H = "##" + "# Task"`; no literal task header at column 0 inside fixtures. Pre-change code was plainly fence-blind (raw `findall`), so the RED phase is credible.

**N13:** The two mkdir lines (`reports.mkdir(exist_ok=True)` and `(reports / ".dispatch-log").parent.mkdir(parents=True, exist_ok=True)`) are present in the hardening plan's Task 4 `_hook_requires_quality_prov` snippet (plan.md ~line 803-804), immediately after `reports = ws["reports_dir"]` — slightly earlier than "before the first `_impl(reports / ...)`" but this still satisfies the spec and is the only correct placement (`log.write_text` needs `reports/` to exist first).

**Actual pytest output observed:**
- `tests/unit/test_fence_aware_parsing.py tests/unit/test_validate_plan.py tests/unit/test_pre_completion_gates.py`: **66 passed** (6 new + 60 existing, matching the report's claim exactly)
- Full suite `tests/unit/`: **426 passed, 1 warning, 0 failed** — no regressions anywhere from the script changes

**Advisory observations (none affect correctness; no action required):**
- [ADVISORY] [EXTRA]: Two additional sites beyond the spec's enumerated list were also routed through `_unfenced_content`: `task_zero_is_first` (controller-checkpoint.py:465) and `run_pre_completion`'s `all_task_ids` extraction (controller-checkpoint.py:1296). These are not mentioned in the report's files_changed descriptions ("routed 4+1 sites"). They are beneficial and necessary for consistency — leaving them fence-blind would have made task counts disagree between `count_tasks` and the verification-ratio denominator — and they align with the "all callers" intent of N5 and the commit message's "7+1". Extra-but-correct.
- [ADVISORY]: Test file docstring says "all 7+1 sites" vs plan's "all 7 sites" — cosmetic only.

**Report completeness:** All required sections present and substantive: frontmatter (schema_version, task_id, status DONE, files_changed, tests, contract_compliance) plus Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations from Plan (the timeout/manual-commit deviation is disclosed and consistent with what I observed — the commit exists and matches the spec'd message), Self-Review Findings, Concerns. Contract Constraints: None — correctly marked not_applicable.
