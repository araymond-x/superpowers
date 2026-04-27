---
schema_version: 1
task_id: 1
status: DONE
files_changed:
  - path: "src/feature.py"
    description: "Added feature implementation"
tests:
  written: 2
  passing: 2
  command: ".venv/bin/python3 -m pytest tests/unit/test_feature.py -v"
  result: PASS
---

**Implementation Summary:**
Implemented the feature as specified. All tests pass.

**Source Files Read:**
- `docs/imp-plans/plan.md` — task requirements

**Deviations from Plan:**
None — implemented exactly as specified

**Self-Review Findings:**
No issues found

**Concerns:**
No concerns
