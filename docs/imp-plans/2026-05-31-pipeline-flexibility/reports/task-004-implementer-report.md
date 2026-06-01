---
schema_version: 1
task_id: 4
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "Added _verification_task_ids() helper (lines 254-274, mirroring _declared_minimum_task_ids) and the Check 8 verification ratio block in run_pre_completion() (lines 1169-1197, after the two _ratio_check calls)."
  - path: "tests/unit/test_pre_completion_gates.py"
    description: "Added TestVerificationRatioCheck (4 tests) + a _plan_with_task_types() fixture builder emitting frontmatter tasks[] with id/task_type AND matching ### Task N headers."
tests:
  written: 4
  passing: 4
  command: ".venv/bin/python3 -m pytest tests/unit/ -q"
  result: PASS
contract_compliance:
  - constraint: "Python 3.9 compat (comment-style # type: for the helper)"
    status: compliant
    detail: "_verification_task_ids uses `# type: (list) -> set`; regression suite Python 3.9 checks 145 PASS / 0 FAIL."
  - constraint: "Threshold > 0.3 (strictly greater — exactly 30% PASSES)"
    status: compliant
    detail: "test_30_percent_passes (3/10) → PASS; test_over_30_percent_fails (4/10) → FAIL. Boundary confirmed."
  - constraint: "Must PASS on empty plans (no divide-by-zero, guarded by if total_tasks > 0)"
    status: compliant
    detail: "test_ratio_with_no_tasks_passes → PASS with detail 'No tasks to ratio'."
  - constraint: "FAIL message names the verification tasks"
    status: compliant
    detail: "verif_list joins `Task {t}` for sorted intersected IDs; test asserts all 4 task labels present in detail."
---

**Implementation Summary**
Added a pre-completion gate (Check 8) to `controller-checkpoint.py` that caps verification-type tasks at ≤30% of all tasks. Two changes, both verbatim from the plan:
1. New `_verification_task_ids(plan_contents)` helper inserted after `_declared_minimum_task_ids` (now at lines 254-274), mirroring that function's raw-YAML-parse pattern but reading `task_type=='verification'`.
2. The ratio check inserted in `run_pre_completion()` immediately after the two `_ratio_check(...)` calls (now lines 1169-1197). It builds `all_task_ids` from `### Task N` headers via `TASK_HEADER_PATTERN`, intersects with the frontmatter-declared verification IDs, and FAILs (appending `verification_ratio` to `blockers`) when `verif_count / total_tasks > 0.3`.

TDD followed strictly: wrote 4 failing tests first (RED: all returned empty `{}` — no check existed), then implemented to GREEN. Test fixtures use a new `_plan_with_task_types()` builder (mirroring the existing `_plan_with_review_tiers`) that emits BOTH frontmatter `tasks:` with `id:` on all + `task_type: verification` on the verification ones AND a matching `### Task N` header per task — so the frontmatter IDs and header numbers agree, which is the load-bearing correctness point for the ratio.

**Source Files Read**
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — confirmed `_declared_minimum_task_ids`@224-251, `TASK_HEADER_PATTERN`@58, `run_pre_completion`@887, `all_plan_contents` built @928-948, `_ratio_check` def @1113 / calls @1142-1143. All plan coordinates verified accurate (file unchanged by prior tasks).
- `tests/unit/test_pre_completion_gates.py` — reused the `run_pre_completion` subprocess harness and mirrored the `_plan_with_review_tiers` fixture pattern + the `result["output"]["checks"][...]["status"]` assertion style.
- `docs/imp-plans/2026-05-31-pipeline-flexibility/module-2-enforcement.md` — full Task 4 spec.

**CLAUDE.md Files Read**
- Project-root `CLAUDE.md` — Python 3.9 compat requirement, tests use `.venv/bin/python3`, regression-suite invocation.
- Checked `skills/subagent-driven-development/`, `skills/subagent-driven-development/scripts/`, `tests/`, `tests/unit/` — no CLAUDE.md.

**Deviations from Plan**
None. Implementation is byte-identical to the plan's Step 3 and Step 4 code blocks; tests follow the file's existing patterns.

**Self-Review Findings**
- Helper mirrors `_declared_minimum_task_ids` exactly (raw `yaml.safe_load` on frontmatter, swallows parse errors so an unrelated YAML issue can't take down the check).
- Boundary correct: `> 0.3` is strictly greater; 30% passes, verified by a dedicated test.
- The `verification_ids & all_task_ids` intersection (rather than raw `verification_ids`) means a frontmatter task_type declaration with no matching `### Task N` header is correctly excluded from both numerator and the named list — defensive and consistent with how the denominator is derived.
- Python 3.9 safe: `# type:` comment annotations, f-strings, `set`/`sorted` builtins only. No 3.10+ syntax.
- Scope clean: only the two intended files changed; no scratch files.

**Concerns**
None. Committed as `3c118ac`. Task 5 (git reality check, also in `controller-checkpoint.py` + `test_pre_completion_gates.py`) is the serialized follow-up and depends on this task's `verification_ids` plumbing.
