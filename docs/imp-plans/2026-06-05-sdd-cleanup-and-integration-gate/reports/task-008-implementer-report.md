---
schema_version: 1
task_id: 8
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/scripts/models/plan.py"
    description: "Added import os, field_validator import, IntegrationTest StrictModel with path_must_be_relative_and_safe validator (rejects absolute paths and '..' segments), and optional Plan.integration_test field (default None). No CURRENT_SCHEMA_VERSION bump."
  - path: "tests/unit/test_c2_integration_gate.py"
    description: "New test file with TestIntegrationTestModel (5 tests). Module-level imports at top; class self-contained — appendable for Tasks 9-10."
tests:
  written: 5
  passing: 5
  command: ".venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py -v (5 passed); tests/unit/test_models/ (162 passed); tests/unit/ -q (441 passed); validate-all-skills.py (145 PASS / 0 FAIL / 3 advisory WARNING)"
  result: PASS
contract_compliance:
  - constraint: "None"
    status: not_applicable
    detail: "No external contract dependencies"
---

## Implementation Summary
TDD red-green per plan. Step 1 wrote the 5 prescribed model tests; Step 2 confirmed RED (3 ImportError on `IntegrationTest`, 2 `extra_forbidden` ValidationError on `Plan.integration_test`). Step 3 added `IntegrationTest` to `plan.py` — placed after `PatternReference`/before `Task` consistent with the file's small-model-then-Plan layout — plus the optional `Plan.integration_test: IntegrationTest | None = None` field (placed with the other optional fields, before `tasks`). `field_validator` was NOT previously imported; added alongside the existing `model_validator` import. `import os` added. Step 4 GREEN. Full unit suite 441 passed (436 prior + 5 new); regression suite PASS-with-3-advisory-WARNINGs (known baseline). Committed as `0f26fb4` with only the two task files staged.

## Source Files Read
- `skills/scripts/models/plan.py` (fully, before editing)
- `skills/scripts/models/_base.py` semantics via repo CLAUDE.md + observed `extra_forbidden` behavior in RED run
- `tests/unit/conftest.py`, `tests/unit/test_models/test_plan_model.py`, `tests/unit/test_n16_verification_report.py` (import conventions)
- module-2-integration-gate.md Task 8 verbatim text

## CLAUDE.md Files Read
Repo-root CLAUDE.md (Pydantic Validation — schema-bump precedent confirmed). No CLAUDE.md under tests/ or skills/scripts/ (verified with find).

## Deviations from Plan
1. **sys.path correction (flagged in dispatch):** prescribed `parent.parent / "skills/scripts/models"` resolves to `tests/skills/scripts/models` (nonexistent). Used `parent.parent.parent` (repo root), matching the working test_n16_verification_report.py ROOT convention; conftest.py also inserts this path (redundant-but-conventional).
2. **Step 2 expected-failure mode:** plan said "ImportError"; the two Plan tests failed with `extra_forbidden` ValidationError instead (IntegrationTest tests did ImportError). All 5 RED — TDD semantics intact.
3. Commit message includes body + trailer per git-workflow rules (plan showed subject-only).

## Self-Review Findings
- `IntegrationTest` inherits StrictModel → extra="forbid" holds for the nested object. Validator covers `tests/../x`, leading-`..`, bare `..`, absolute paths; backslash traversal (`..\\x`) not caught — acceptable for this posix repo; `os.path.isabs` platform-correct.
- `test_smoke_real_plans.py` passed in full suite — the new optional field doesn't break this feature's own (self-hosting) plan frontmatter validation.
- Did not touch validate-plan.py / controller-checkpoint.py / _report_utils.py (Tasks 9-10 scope respected).

## Concerns
- None blocking. Watch item: Tasks 9-10 append to test_c2_integration_gate.py; its sys.path insert points at the models dir only — Task 9/10 tests touching validate-plan.py/controller-checkpoint.py need their own import setup (consistent with other script tests).
