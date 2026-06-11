---
schema_version: 1
task_id: 2
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "Replaced _declared_minimum_task_ids and _verification_task_ids with generic _task_ids_where helper; added _load_all_plan_contents helper; retrofitted run_pre_completion to use both"
  - path: "tests/unit/test_n9_plan_loading_helpers.py"
    description: "Created 7 tests covering _task_ids_where (4 tests) and _load_all_plan_contents (3 tests)"
tests:
  written: 7
  passing: 7
  command: ".venv/bin/python3 -m pytest tests/unit/test_n9_plan_loading_helpers.py -v"
  result: PASS
contract_compliance:
  - constraint: "None"
    status: not_applicable
    detail: "No external contract dependencies"
---

**Implementation Summary:**
Collapsed `_declared_minimum_task_ids` and `_verification_task_ids` into a single generic `_task_ids_where(plan_contents, field, value)` function. Added `_load_all_plan_contents(manifest_data, git_root)` with realpath-based deduplication. Retrofitted `run_pre_completion` to use `_load_all_plan_contents` as full replacement in manifest mode (Audit Order 2 double-count prevention), preserving `--additional-plan-files` in non-manifest fallback.

**Source Files Read:**
- `controller-checkpoint.py` — full file for function locations and callers
- `test_pre_completion_gates.py` — test patterns
- `sdd_test_helpers.py` — manifest workspace shape

**CLAUDE.md Files Read:**
- Project CLAUDE.md at repo root

**Deviations from Plan:**
None — implemented exactly as specified

**Self-Review Findings:**
Preserved `--additional-plan-files` CLI flag in non-manifest branch (used by existing tests). Manifest-mode has try/except fallback to `[plan_content]` if manifest parsing fails.

**Concerns:**
No concerns
