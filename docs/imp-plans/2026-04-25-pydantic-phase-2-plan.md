---
schema_version: 1
feature_archetype: extension
source_contracts: "docs/specs/2026-04-25-pydantic-phase-2-design-distilled.md"
shared_constants:
  - path: "skills.scripts.models._base.CURRENT_SCHEMA_VERSION"
    value: "1"
    reason: "All models pin schema_version to this constant"
  - path: "skills.scripts.models._base.StrictModel"
    value: "BaseModel subclass with extra=forbid"
    reason: "All nested types inherit from this"
  - path: "skills.scripts.models._base.SchemaVersionedModel"
    value: "StrictModel subclass with schema_version field"
    reason: "All top-level artifact models inherit from this"
pattern_references:
  - name: "phase-1-plan-model"
    source_files: ["skills/scripts/models/plan.py"]
    reason: "Established pattern for SchemaVersionedModel with Literal types, nested StrictModels, and model_validators"
  - name: "phase-1-validators"
    source_files: ["skills/scripts/models/validators.py"]
    reason: "Established pattern for CLI entry points: _extract_frontmatter, validate_X(), bypass check, exit codes"
  - name: "phase-1-model-tests"
    source_files: ["tests/unit/test_models/test_plan_model.py"]
    reason: "Test structure for model validation: golden inputs, per-field failures, validator edge cases"
  - name: "phase-1-cli-tests"
    source_files: ["tests/unit/test_validators/test_validate_plan_pydantic.py"]
    reason: "Test structure for CLI subprocess tests: exit codes, stderr content, bypass env var"
modules:
  - id: 1
    title: "Models + Unit Tests"
    task_ids: [0, 1, 2, 3, 4, 5]
  - id: 2
    title: "CLI + Consumer Updates"
    task_ids: [6, 7, 8, 9, 10, 11, 12]
  - id: 3
    title: "Cutover"
    task_ids: [13, 14, 15]
tasks:
  - id: 0
    title: "Contract Verification"
    module_id: 1
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION", "skills.scripts.models._base.StrictModel", "skills.scripts.models._base.SchemaVersionedModel"]
    pattern_references: ["phase-1-plan-model"]
  - id: 1
    title: "ImplementerReport Model"
    depends_on: [0]
    module_id: 1
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION", "skills.scripts.models._base.StrictModel", "skills.scripts.models._base.SchemaVersionedModel"]
    pattern_references: ["phase-1-plan-model"]
  - id: 2
    title: "ImplementerReport Unit Tests"
    depends_on: [1]
    module_id: 1
    pattern_references: ["phase-1-model-tests"]
  - id: 3
    title: "CheckpointResult Model"
    depends_on: [0]
    module_id: 1
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION", "skills.scripts.models._base.StrictModel", "skills.scripts.models._base.SchemaVersionedModel"]
    pattern_references: ["phase-1-plan-model"]
  - id: 4
    title: "CheckpointResult Unit Tests"
    depends_on: [3]
    module_id: 1
    pattern_references: ["phase-1-model-tests"]
  - id: 5
    title: "Test Fixtures"
    depends_on: [1, 3]
    module_id: 1
  - id: 6
    title: "validators.py report Subcommand"
    depends_on: [1]
    module_id: 2
    pattern_references: ["phase-1-validators"]
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION"]
  - id: 7
    title: "validate-report.py Pydantic Pre-Check"
    depends_on: [6]
    module_id: 2
  - id: 8
    title: "_report_utils.py Re-Export + Cleanup"
    depends_on: [1]
    module_id: 2
  - id: 9
    title: "controller-checkpoint.py Updates"
    depends_on: [3, 8]
    module_id: 2
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION"]
  - id: 10
    title: "sdd-pre-dispatch-hook.sh Updates"
    depends_on: [7]
    module_id: 2
  - id: 11
    title: "context-summary.py Frontmatter Parsing"
    depends_on: [1]
    module_id: 2
  - id: 12
    title: "CLI + Consumer Tests"
    depends_on: [6, 7, 8, 9, 10, 11]
    module_id: 2
    pattern_references: ["phase-1-cli-tests"]
  - id: 13
    title: "Prompt Template + SKILL.md + Test Helper Updates"
    depends_on: [8]
    module_id: 3
  - id: 14
    title: "Documentation Updates"
    depends_on: [1, 3, 6, 9]
    module_id: 3
  - id: 15
    title: "Smoke Test + Regression Verification"
    depends_on: [13, 14]
    module_id: 3
---

# Pydantic Phase 2 — Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Add Pydantic validation models for ImplementerReport (YAML frontmatter + markdown body) and CheckpointResult (pure JSON), update all consumers of the old report format, and cut over atomically.

**Architecture:** Two new models extend Phase 1 infrastructure (`_base.py`, `errors.py`). ImplementerReport uses YAML frontmatter extraction (same as Plan). CheckpointResult wraps existing `controller-checkpoint.py` dict construction with typed model. All old-format consumers (hook, checkpoint inline validator, context-summary, test helpers) updated to new format. Old-format helpers removed, not deprecated.

**Tech Stack:** Python 3.12+, Pydantic v2.7+, PyYAML, pytest, bash (hooks)

**Source Contracts:** `docs/specs/2026-04-25-pydantic-phase-2-design-distilled.md`

**Contract Constraints:**
- ImplementerReport: 2 model validators (`test_counts_consistent`, `files_changed_non_empty_for_done`), `done_with_concerns_check` in CLI wrapper only
- CheckpointResult: 3 model validators (`fail_requires_blockers`, `blockers_reference_check_names`, `task_number_required_for_pre_dispatch`)
- Exit codes: validators.py = 0/1/2, controller-checkpoint.py = 0/1/2/3
- Hard cutover, no backward compatibility, rollback = git revert
- `exclude_none=True` on checkpoint `model_dump()` to preserve output shape
- Reports without YAML frontmatter → hard FAIL

**Shared Constants:**
- `CURRENT_SCHEMA_VERSION` from `skills/scripts/models/_base.py` — all models pin to this
- `StrictModel` from `skills/scripts/models/_base.py` — nested types inherit this
- `SchemaVersionedModel` from `skills/scripts/models/_base.py` — top-level artifacts inherit this

**Pattern References:**
- `skills/scripts/models/plan.py` — established model pattern: Literal types, nested StrictModels, `@model_validator(mode="after")`
- `skills/scripts/models/validators.py` — CLI pattern: `_extract_frontmatter()`, `validate_X()`, bypass check, exit codes
- `tests/unit/test_models/test_plan_model.py` — model test pattern: golden inputs, per-field failures, validator edge cases
- `tests/unit/test_validators/test_validate_plan_pydantic.py` — CLI test pattern: subprocess, exit codes, stderr content

**Feature Archetype:** Extension

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| New | `skills/scripts/models/implementer_report.py` | Create | — |
| New | `skills/scripts/models/checkpoint_result.py` | Create | — |
| New | `tests/unit/test_models/test_implementer_report_model.py` | Create | — |
| New | `tests/unit/test_models/test_checkpoint_result_model.py` | Create | — |
| New | `tests/unit/test_validators/test_validate_report_pydantic.py` | Create | — |
| New | `tests/fixtures/reports/valid/minimal-report.md` | Create | — |
| New | `tests/fixtures/reports/valid/full-featured-report.md` | Create | — |
| New | `tests/fixtures/reports/invalid/missing-status.md` | Create | — |
| New | `tests/fixtures/reports/invalid/bad-status-enum.md` | Create | — |
| New | `tests/fixtures/reports/invalid/test-counts-inconsistent.md` | Create | — |
| New | `tests/fixtures/reports/invalid/no-files-for-done.md` | Create | — |
| Modified | `skills/scripts/models/validators.py` | Add `report` subcommand | Existing `plan`, `handoff` subcommands |
| Modified | `skills/scripts/models/__init__.py` | Update docstring | — |
| Modified | `skills/subagent-driven-development/scripts/validate-report.py` | Add Pydantic pre-check | `_report_utils.validate_report_sections()` |
| Modified | `skills/subagent-driven-development/scripts/_report_utils.py` | Re-export + remove old helpers + fix placeholders | `validate-report.py`, `controller-checkpoint.py`, `context-summary.py` |
| Modified | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | `CheckpointResult` construction + inline validator fix | `_build_result()`, `validate_report_sections()` |
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Exit code handling + section count | Check 4b block |
| Modified | `skills/subagent-driven-development/scripts/context-summary.py` | Frontmatter file extraction | `extract_files_changed()` |
| Modified | `skills/subagent-driven-development/implementer-prompt.md` | Add frontmatter block | Report Format section |
| Modified | `skills/subagent-driven-development/SKILL.md` | Report persistence prefix | Lines 426-431 |
| Modified | `tests/unit/sdd_test_helpers.py` | Update report template | `IMPLEMENTER_REPORT_TEMPLATE` |
| Modified | `CLAUDE.md` | Pydantic section | — |
| Modified | `docs/plans/2026-04-24-pydantic-meta-design.md` | Sections 2, 5, 11, 12 | — |
| Obsolete | `_report_utils.STATUS_VALUE_PATTERN` | Remove | `extract-execution-trace.py` has own fallback |
| Obsolete | `_report_utils.extract_implementer_status()` | Remove | Only caller is `validate_report_sections()` return dict |
| Obsolete | `controller-checkpoint.validate_report_sections()` | Replace (inline 9-section) | Lines 632, 883 |

---

## Module Dependency Graph

```
Module 1 (Models + Unit Tests)
  └── Module 2 (CLI + Consumer Updates) ← depends on Module 1 models
  └── Module 3 (Cutover) ← depends on Module 2 consumer updates
```

Module 2 depends on Module 1 completing first (needs model imports).
Module 3 depends on Module 2 completing first (prompt template + SKILL.md ship with validators).

**No parallel candidates** — each module depends on the previous.

**Intermediate test breakage note:** Between Module 2 completion (validate-report.py requires frontmatter) and Module 3 Task 13 (test helper template updated), existing hook/checkpoint tests will fail because they generate old-format reports without frontmatter. This is expected — do not run the full test suite mid-cutover. Task 15 (smoke test + regression) is the verification point.

---

## Module Inventory

| Module | File | Goal | Tasks |
|--------|------|------|-------|
| 1 | `2026-04-25-pydantic-phase-2-module-1-models.md` | Create ImplementerReport + CheckpointResult models with unit tests and fixtures | 0–5 |
| 2 | `2026-04-25-pydantic-phase-2-module-2-cli-consumers.md` | Add validators.py report subcommand + update all consumers of old report format | 6–12 |
| 3 | `2026-04-25-pydantic-phase-2-module-3-cutover.md` | Update prompt templates, docs, smoke test, regression verification | 13–15 |

---

## Shared Contract Section

All modules share the Phase 1 base infrastructure:

```python
# skills/scripts/models/_base.py
CURRENT_SCHEMA_VERSION = 1

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class SchemaVersionedModel(StrictModel):
    schema_version: int  # pinned to CURRENT_SCHEMA_VERSION
```

Import pattern for all new model files:
```python
from _base import StrictModel, SchemaVersionedModel, CURRENT_SCHEMA_VERSION
```

Import pattern for consumer scripts (outside models/ directory):
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))
```

---

## Acceptance Criteria (Plan-Level)

- [ ] All Module 1 acceptance criteria pass
- [ ] All Module 2 acceptance criteria pass
- [ ] All Module 3 acceptance criteria pass
- [ ] `pytest tests/unit/ -v` — all existing + new tests pass
- [ ] `python3 tests/ARaymond-skill-regression/validate-all-skills.py` — 122 checks pass
- [ ] `bash tests/ARaymond-installation/verify-symlink-install.sh` — 105 checks pass
