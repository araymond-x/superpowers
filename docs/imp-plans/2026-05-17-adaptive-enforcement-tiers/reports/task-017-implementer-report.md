---
schema_version: 1
task_id: 17
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/validate-plan.py"
    description: "Added YAML frontmatter parsing + three enforcement_tier checks (invalid blocker; appropriateness + micro_with_modules warnings)."
  - path: "tests/unit/test_validate_plan.py"
    description: "Added TestEnforcementTierValidation class (2 tests) + 2 plan fixture constants."
tests:
  written: 2
  passing: 2
  command: ".venv/bin/python3 -m pytest tests/unit/test_validate_plan.py -v"
  result: PASS
---

# Task 17 — validate-plan.py Tier and Module Checks

## What I Built

Extended `validate-plan.py`'s `validate_plan()` function with three new enforcement-tier checks driven by parsed YAML frontmatter:

1. **`enforcement_tier_invalid`** (BLOCKER) — fires when `enforcement_tier` is set to a value outside `{"micro", "standard"}`. Values match `sdd_session.Tier`.
2. **`enforcement_tier_appropriateness`** (WARNING) — fires when `enforcement_tier == "micro"` AND `task_count > 3`. Suggests upgrading to `standard`.
3. **`micro_with_modules`** (WARNING) — fires when `enforcement_tier == "micro"` AND the frontmatter declares `modules`. Multi-module plans typically need standard enforcement.

YAML frontmatter is parsed in-process via `yaml.safe_load()` with the import scoped inside `validate_plan()` (matches the pattern suggested in the task; `yaml` was not yet imported at module top). Parse failures fall back silently to `frontmatter = None` so non-frontmatter plans continue to work.

## TDD Trail

1. Added `TestEnforcementTierValidation` (2 tests) to `tests/unit/test_validate_plan.py`.
2. Ran — confirmed the `test_micro_with_many_tasks_warns` test failed (`assert 0 == 2`, no tier check existed yet). The `test_valid_micro_tier_passes` test happened to already pass (exit_code 0 was already valid per its assertion).
3. Implemented YAML parsing block + the three tier checks (blocker/warning placement before final status computation, following the existing `blockers.append(...)` + `sections[<key>] = {...}` pattern used by `duplicate_task_numbers` and `cross_module_task_collision`).
4. Re-ran — both new tests PASS. All 15 pre-existing `test_validate_plan.py` tests still PASS (17 total).
5. Ran the full unit suite (`tests/unit/`) — 326 tests PASS, 0 failures, 1 unrelated pre-existing pytest collection warning.

## Deviations from Plan

The plan-reference fixture `PLAN_WITH_MICRO_TOO_MANY_TASKS` used `**Task N**` bold-markdown task markers, but the existing `TASK_HEADER_RE` regex matches `^###\s+Task\s+(\d+)`. Bold markers don't count as tasks — that would have made `task_count = 0`, and the `> 3` warning would never fire. I changed the fixture to use `### Task N` so the validator actually counts the 5 tasks. This is a fixture correction to match the validator's real task-detection contract, not a contract change. No other deviations.

## Files Modified

- `/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/validate-plan.py` — added frontmatter parsing (~10 LOC) + three tier checks (~35 LOC) inside `validate_plan()`.
- `/Users/araymond/projects/claude-custom/superpowers/tests/unit/test_validate_plan.py` — added `TestEnforcementTierValidation` class with 2 tests + 2 fixture constants.

## Type-Hint Style

Matched the file's existing legacy `typing` style (`Optional[Dict]`, `List[str]`) per the task brief. Did NOT modernize to PEP-604 syntax inside this file.

## Verification

- `.venv/bin/python3 -m pytest tests/unit/test_validate_plan.py -v` → 17 PASS
- `.venv/bin/python3 -m pytest tests/unit/ -q` → 326 PASS
- Pre-existing tests unaffected (clean plans without `enforcement_tier` still PASS).

## Open Concerns

None.
