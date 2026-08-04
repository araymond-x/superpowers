---
schema_version: 1
task_id: 1
task_type: implementation
status: DONE
files_changed:
  - path: "skills/scripts/models/plan.py"
    description: "Added _coerce_yaml_bool_handoff_spawn mode='before' field_validator on Plan.handoff_spawn: maps YAML-coerced False->'off', rejects True with an actionable message naming 'on'."
  - path: "tests/unit/test_models/test_plan_model.py"
    description: "Extended TestHandoffSpawn with test_unquoted_off_coerces_to_off and test_bare_on_rejected_with_actionable_message; added module-level _write_plan helper plus test_validators_cli_accepts_unquoted_off / test_validators_cli_rejects_bare_on subprocess tests proving the real Gate 1b (validators.py plan <file>) behavior."
tests:
  written: 4
  passing: 4
  command: ".venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -v"
  result: PASS
contract_compliance:
  - constraint: "Do not change the handoff_spawn value set or the auto default"
    status: compliant
    detail: "Literal[\"auto\",\"ask\",\"off\"] = \"auto\" untouched; validator only coerces/rejects at mode='before'."
  - constraint: "Primary test layer must be validators.py plan <file> (Gate 1b), not validate-plan.py"
    status: compliant
    detail: "Added subprocess tests invoking validators.py under sys.executable (the venv python), asserting exit 0 for unquoted off and exit 1 for bare on."
  - constraint: "Do not add eager pydantic import to validate-plan.py or _report_utils"
    status: not_applicable
    detail: "Only plan.py and its test file were touched."
  - constraint: "Quoted \"off\" must remain untouched"
    status: compliant
    detail: "Validator only special-cases v is False / v is True; any other input passes through unchanged."
---

**Implementation Summary:**
Added a mode="before" field_validator on Plan.handoff_spawn following the IntegrationTest.path_must_be_relative_and_safe idiom, mapping YAML 1.1's False (unquoted off) to "off", rejecting True (unquoted on) with an actionable "on"-mentioning message. Extended TestHandoffSpawn with two model-level tests and added two subprocess-level tests proving the real Gate 1b gate accepts/rejects correctly.

**Source Files Read:**
- skills/scripts/models/plan.py — confirmed the field and the IntegrationTest validator pattern to mirror.
- tests/unit/test_models/test_plan_model.py — confirmed existing TestHandoffSpawn contents, MINIMAL_PLAN fixture, existing imports.

**CLAUDE.md Files Read:**
None found in modified directories.

**Deviations from Plan:**
- Moved os/subprocess/sys/textwrap imports and the VALIDATORS path constant to module level (top of file) instead of inline mid-file, for import hygiene. Dropped the unused `tempfile` import (pytest's `tmp_path` fixture used instead). Behavior/content otherwise exactly as specified.
- A repo pre-commit hook (formatter) reformatted both files slightly at commit time (e.g. multi-line Literal wrapping, wrapped path join, whitespace) — content/behavior unchanged; all 56 tests in the file still pass post-format.

**Self-Review Findings:**
No issues found. All 4 new tests pass; all 56 tests in the file pass; all 182 tests in tests/unit/test_models/ pass (no regressions).

**Concerns:**
No concerns.

**Controller note:** implementer marked status DONE despite listing two Deviations entries; per the SDD skill's own rule ("Use DONE_WITH_CONCERNS if you have any entries in Deviations") this should have been DONE_WITH_CONCERNS. Controller is logging both deviations to deviations.md as if DONE_WITH_CONCERNS was reported, since both are minor/cosmetic and self-disclosed. The Pyright diagnostics on this file (pytest/plan/_base import resolution) are the same runtime-vs-static-analysis false positive already documented for Task 0 — the pytest run in this report (56/56 passing) confirms imports resolve correctly at runtime via the project's actual venv/pytest configuration.
