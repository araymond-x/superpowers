# Pydantic Phase 1 Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Add Pydantic v2.7+ validation for Plan and HandoffPackage artifacts, replacing regex-based validation with typed schemas that produce explanatory errors.

**Architecture:** New `skills/scripts/models/` package contains Pydantic models, error formatter, and CLI entry points. Existing shell hooks call the Python CLI via subprocess. Prompt templates updated atomically with validators.

**Tech Stack:** Python 3.14, Pydantic v2.7+, pytest, bash (hooks)

**Source Contracts:** None

**Contract Constraints:** All contract facts are defined in the distilled spec: `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md` (Contract Facts section, lines 10–91). Key constraints:
- `CURRENT_SCHEMA_VERSION = 1`
- Two base classes: `StrictModel` (nested, `extra="forbid"`) and `SchemaVersionedModel` (top-level, adds `schema_version: int` pinned to `CURRENT_SCHEMA_VERSION`)
- Three distinct error block headers: `YAML PARSE FAILED`, `VALIDATION FAILED`, `SAMPLE FILE MISSING`
- Exit codes: 0 pass / 1 producer-fix / 2 infrastructure
- Bypass env var: `SUPERPOWERS_VALIDATOR_BYPASS=1`

**Shared Constants:** None — this plan introduces the first shared constants (`CURRENT_SCHEMA_VERSION`). Future phases will reference them.

**Pattern References:**
- `skills/subagent-driven-development/scripts/validate-plan.py` — CLI validation pattern (argparse, JSON stdout, exit codes 0/1/2/3)
- `skills/writing-plans/scripts/plan-validation-gate-hook.sh` — hook JSON-wrapping pattern (`jq -Rs .` for stderr)
- `tests/unit/test_sdd_partner_gate.py` — test subprocess pattern (subprocess.run, returncode assertions)
- `tests/unit/sdd_test_helpers.py` — test helper pattern (workspace setup, fixture creation)

**Feature Archetype:** Migration

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| New | `skills/scripts/models/__init__.py` | Create | — |
| New | `skills/scripts/models/_base.py` | Create | — |
| New | `skills/scripts/models/plan.py` | Create | _base.py |
| New | `skills/scripts/models/handoff.py` | Create | _base.py |
| New | `skills/scripts/models/errors.py` | Create | — |
| New | `skills/scripts/models/validators.py` | Create | plan.py, handoff.py, errors.py |
| New | `requirements.txt` | Create | — |
| New | `tests/unit/conftest.py` | Create | — |
| New | `tests/unit/test_models/*.py` (4 files) | Create | models package |
| New | `tests/unit/test_validators/*.py` (2 files) | Create | validators.py |
| New | `tests/unit/test_hooks_pydantic.py` | Create | hook scripts |
| New | `tests/unit/test_smoke_real_plans.py` | Create | validators.py |
| New | `tests/fixtures/plans/` | Create | — |
| New | `tests/fixtures/handoffs/` | Create | — |
| Modified | `skills/subagent-driven-development/scripts/validate-plan.py` | Add YAML frontmatter detection | Existing callers (plan-validation-gate-hook.sh) |
| Modified | `skills/writing-plans/scripts/plan-validation-gate-hook.sh` | Call Python validator, JSON-wrap stderr | settings.json hook entry |
| Modified | `skills/handoff-acceptance/scripts/check-handoff.sh` | Call Python validator | handoff-gate-hook.sh |
| Modified | `skills/handoff-acceptance/scripts/handoff-gate-hook.sh` | JSON-wrap Python validator stderr | settings.json hook entry |
| Modified | `skills/writing-plans/SKILL.md` | Add YAML frontmatter section | — |
| Modified | `skills/handoff-acceptance/references/handoff-package-spec.md` | Replace prose template with YAML template | — |
| Modified | `skills/subagent-driven-development/SKILL.md` | One-line note about YAML frontmatter | Word count (currently 5029, limit 5000) |
| Modified | `CLAUDE.md` | Add Pydantic section | — |
| Modified | `tests/ARaymond-installation/verify-symlink-install.sh` | Add 2 Pydantic checks | — |
| Obsolete | Legacy regex in `validate-plan.py` (`check_sections()`, `TASK_HEADER_RE`) | Keep (routed around) | Phase 7 cleanup |
| Obsolete | First-50-lines grep in `check-handoff.sh` | Keep (routed around) | Phase 7 cleanup |

---

## Module Inventory

| Module | File | Goal | Tasks |
|--------|------|------|-------|
| Parent | This file | Coordination | — |
| 1 | `2026-04-24-pydantic-phase-1-module-1-models.md` | Core Pydantic models + unit tests | 1–5 |
| 2 | `2026-04-24-pydantic-phase-1-module-2-cli-hooks.md` | CLI validators + hook integration | 6–9 |
| 3 | `2026-04-24-pydantic-phase-1-module-3-cutover.md` | Prompt templates, docs, smoke test, obsolescence verification | 10–13 |

## Module Dependency Graph

```
Module 1 (Core Models)
  └── Module 2 (CLI + Hooks) ← depends on Module 1
      └── Module 3 (Cutover) ← depends on Module 2
```

No parallel candidates — strict serial dependency (models must exist before CLI wraps them; CLI must work before hooks call it; hooks must work before templates instruct authors to use the new format).

## Shared Contract: Base Classes

All modules share this contract from `skills/scripts/models/_base.py` (created in Module 1):

```python
CURRENT_SCHEMA_VERSION = 1

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class SchemaVersionedModel(StrictModel):
    schema_version: int  # must equal CURRENT_SCHEMA_VERSION
```

Module 2 imports `Plan`, `HandoffPackage`, error formatters from Module 1's output.
Module 3 modifies hook scripts to call Module 2's CLI entry points.

## File Map

```
skills/scripts/models/           # NEW — Module 1
├── __init__.py
├── _base.py
├── plan.py
├── handoff.py
├── errors.py
└── validators.py                # Module 2

tests/
├── unit/
│   ├── conftest.py              # NEW — Module 1 (sys.path setup)
│   ├── test_models/             # NEW — Module 1
│   │   ├── test_plan_model.py
│   │   ├── test_handoff_model.py
│   │   ├── test_schema_versioning.py
│   │   └── test_error_formatter.py
│   ├── test_validators/         # NEW — Module 2
│   │   ├── test_validate_plan_pydantic.py
│   │   └── test_validate_handoff_pydantic.py
│   ├── test_hooks_pydantic.py   # NEW — Module 2
│   └── test_smoke_real_plans.py # NEW — Module 3
└── fixtures/
    ├── plans/                   # NEW — Module 1
    │   ├── valid/
    │   └── invalid/
    ├── handoffs/                # NEW — Module 1
    │   ├── valid/
    │   └── invalid/
    └── _smoke-test-plans/       # NEW — Module 3 (deleted post-merge)
```

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 1 | requirements.txt, skills/scripts/models/__init__.py, tests/unit/conftest.py, tests/fixtures/plans/\*, tests/fixtures/handoffs/\* | — | — |
| Task 2 | skills/scripts/models/_base.py, tests/unit/test_models/test_schema_versioning.py | — | Task 1 |
| Task 3 | skills/scripts/models/plan.py, tests/unit/test_models/test_plan_model.py | _base.py | Task 2 |
| Task 4 | skills/scripts/models/handoff.py, tests/unit/test_models/test_handoff_model.py | _base.py | Task 2 |
| Task 5 | skills/scripts/models/errors.py, tests/unit/test_models/test_error_formatter.py | — | Task 1 |
| Task 6 | skills/scripts/models/validators.py (plan part), tests/unit/test_validators/test_validate_plan_pydantic.py | plan.py, errors.py | Task 3, 5 |
| Task 7 | skills/scripts/models/validators.py (handoff part), tests/unit/test_validators/test_validate_handoff_pydantic.py | handoff.py, errors.py | Task 4, 6 |
| Task 8 | plan-validation-gate-hook.sh, handoff-gate-hook.sh, check-handoff.sh, tests/unit/test_hooks_pydantic.py | validators.py | Task 7 |
| Task 9 | validate-plan.py | — | Task 6 |
| Task 10 | writing-plans/SKILL.md, handoff-package-spec.md, SDD SKILL.md | — | Task 8 |
| Task 11 | CLAUDE.md, requirements.txt (already created T1), verify-symlink-install.sh | — | Task 10 |
| Task 12 | tests/unit/test_smoke_real_plans.py, tests/fixtures/_smoke-test-plans/\* | validators.py | Task 9 |
| Task 13 | (grep audit only — no file creation) | All modified files | Task 12 |

## Acceptance Criteria

See distilled spec `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md` lines 286–313 for the complete 28-item acceptance criteria list. All items must pass before the Pre-Completion Gate.
