# Pydantic Phase 1 — Module 1: Core Models

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first.

**Goal:** Create the Pydantic model package (`skills/scripts/models/`) with base classes, Plan schema, HandoffPackage schema, and error formatter — all with comprehensive unit tests.

**Source Contracts:** None

**Contract Constraints:** See `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md` Contract Facts section for all field types, validators, and invariants.

**Pattern References:**
- `tests/unit/test_sdd_partner_gate.py` — test structure pattern (pytest, subprocess, assertions)

**Feature Archetype:** Migration

## File Map

```
skills/scripts/models/           # NEW — all files created in this module
├── __init__.py                  # Task 1
├── _base.py                    # Task 2
├── plan.py                     # Task 3
├── handoff.py                  # Task 4
└── errors.py                   # Task 5

tests/unit/
├── conftest.py                 # Task 1 (sys.path setup)
└── test_models/                # Tasks 2–5
    ├── test_schema_versioning.py
    ├── test_plan_model.py
    ├── test_handoff_model.py
    └── test_error_formatter.py

tests/fixtures/
├── plans/valid/                # Task 1
├── plans/invalid/              # Task 1
├── handoffs/valid/             # Task 1
└── handoffs/invalid/           # Task 1

requirements.txt                # Task 1
```

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 1 | requirements.txt, __init__.py, conftest.py, fixtures dirs | — | — |
| Task 2 | _base.py, test_schema_versioning.py | — | Task 1 |
| Task 3 | plan.py, test_plan_model.py | _base.py | Task 2 |
| Task 4 | handoff.py, test_handoff_model.py | _base.py | Task 2 |
| Task 5 | errors.py, test_error_formatter.py | — | Task 1 |

Tasks 3 and 4 have disjoint write sets and both depend only on Task 2. They are parallel candidates.

Task 5 depends only on Task 1 (no model imports). It is a parallel candidate with Tasks 2–4.

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `skills/scripts/models/__init__.py`
- Create: `tests/unit/conftest.py`
- Create: `tests/fixtures/plans/valid/` (directory)
- Create: `tests/fixtures/plans/invalid/` (directory)
- Create: `tests/fixtures/handoffs/valid/` (directory)
- Create: `tests/fixtures/handoffs/invalid/` (directory)

- [ ] **Step 1: Create requirements.txt**

```
pydantic>=2.7,<3
pyyaml>=6.0
```

- [ ] **Step 2: Install Pydantic**

Run: `.venv/bin/pip install -r requirements.txt`
Expected: Pydantic v2.7+ installed successfully

- [ ] **Step 3: Verify installation**

Run: `.venv/bin/python3 -c "import pydantic; print(pydantic.VERSION)"`
Expected: Version starting with `2.` and minor >= 7

- [ ] **Step 4: Create models package**

```python
# skills/scripts/models/__init__.py
"""Shared Pydantic models for the Superpowers custom fork."""
```

- [ ] **Step 5: Create conftest.py for model imports**

```python
# tests/unit/conftest.py
"""Pytest configuration — adds Pydantic models to import path."""
import sys
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scripts" / "models"
sys.path.insert(0, str(MODELS_DIR))
```

- [ ] **Step 6: Create fixture directories**

```bash
mkdir -p tests/fixtures/plans/valid tests/fixtures/plans/invalid
mkdir -p tests/fixtures/handoffs/valid tests/fixtures/handoffs/invalid
```

- [ ] **Step 7: Create minimal valid plan fixture**

```markdown
<!-- tests/fixtures/plans/valid/minimal-plan.md -->
---
schema_version: 1
feature_archetype: greenfield
tasks:
  - id: 0
    title: "Setup"
  - id: 1
    title: "Implement"
    depends_on: [0]
---

# Minimal Plan

## Setup
- [x] Create files

## Implement
- [ ] Build it
```

- [ ] **Step 8: Create full-featured plan fixture**

```markdown
<!-- tests/fixtures/plans/valid/full-featured-plan.md -->
---
schema_version: 1
feature_archetype: migration
source_contracts: "docs/specs/example-spec.md"
shared_constants:
  - path: "app.config.RETENTION_DAYS"
    value: "90"
    reason: "Used in cleanup task"
pattern_references:
  - name: "db-migration-pattern"
    source_files: ["migrations/001.py"]
    reason: "Follow existing migration style"
modules:
  - id: 1
    title: "Core"
    task_ids: [0, 1]
  - id: 2
    title: "Integration"
    task_ids: [2]
tasks:
  - id: 0
    title: "Setup"
    module_id: 1
    shared_constants_used: ["app.config.RETENTION_DAYS"]
  - id: 1
    title: "Implement"
    module_id: 1
    depends_on: [0]
    pattern_references: ["db-migration-pattern"]
  - id: 2
    title: "Integrate"
    module_id: 2
    depends_on: [1]
---

# Full-Featured Plan

> **For agentic workers:** Invoke SDD first.

**Goal:** Example full plan.
```

- [ ] **Step 9: Create invalid plan fixtures**

```markdown
<!-- tests/fixtures/plans/invalid/missing-required-field.md -->
---
schema_version: 1
---

# Missing feature_archetype and tasks
```

```markdown
<!-- tests/fixtures/plans/invalid/bad-dependency.md -->
---
schema_version: 1
feature_archetype: greenfield
tasks:
  - id: 0
    title: "Setup"
  - id: 1
    title: "Implement"
    depends_on: [5]
---

# Bad Dependency — Task 1 depends on non-existent Task 5
```

- [ ] **Step 10: Commit**

```bash
git add requirements.txt skills/scripts/models/__init__.py tests/unit/conftest.py tests/fixtures/
git commit -m "feat(pydantic): project setup — requirements, package init, test fixtures"
```

---

### Task 2: Base Classes + Schema Versioning Tests

**Files:**
- Create: `skills/scripts/models/_base.py`
- Create: `tests/unit/test_models/test_schema_versioning.py`

**Pattern References:**
- `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md` lines 14–19 — base class contract

- [ ] **Step 1: Write failing tests for base classes**

```python
# tests/unit/test_models/test_schema_versioning.py
"""Tests for StrictModel and SchemaVersionedModel base classes."""
import pytest
from pydantic import ValidationError

from _base import StrictModel, SchemaVersionedModel, CURRENT_SCHEMA_VERSION


class TestStrictModel:
    """StrictModel enforces extra='forbid'."""

    def test_rejects_unknown_fields(self):
        class Nested(StrictModel):
            name: str

        with pytest.raises(ValidationError) as exc:
            Nested(name="ok", bogus="nope")
        assert exc.value.errors()[0]["type"] == "extra_forbidden"

    def test_accepts_valid_fields(self):
        class Nested(StrictModel):
            name: str

        obj = Nested(name="ok")
        assert obj.name == "ok"


class TestSchemaVersionedModel:
    """SchemaVersionedModel requires schema_version == CURRENT_SCHEMA_VERSION."""

    def test_accepts_current_version(self):
        class Artifact(SchemaVersionedModel):
            title: str

        obj = Artifact(schema_version=CURRENT_SCHEMA_VERSION, title="test")
        assert obj.schema_version == CURRENT_SCHEMA_VERSION

    def test_rejects_wrong_version(self):
        class Artifact(SchemaVersionedModel):
            title: str

        with pytest.raises(ValidationError) as exc:
            Artifact(schema_version=999, title="test")
        errors = exc.value.errors()
        assert any("schema_version" in str(e["loc"]) for e in errors)
        assert "999" in str(exc.value)
        assert str(CURRENT_SCHEMA_VERSION) in str(exc.value)

    def test_missing_version_is_error(self):
        class Artifact(SchemaVersionedModel):
            title: str

        with pytest.raises(ValidationError) as exc:
            Artifact(title="test")
        assert exc.value.errors()[0]["loc"] == ("schema_version",)
        assert exc.value.errors()[0]["type"] == "missing"

    def test_rejects_unknown_fields(self):
        class Artifact(SchemaVersionedModel):
            title: str

        with pytest.raises(ValidationError) as exc:
            Artifact(schema_version=CURRENT_SCHEMA_VERSION, title="ok", extra="bad")
        assert exc.value.errors()[0]["type"] == "extra_forbidden"

    def test_current_schema_version_is_one(self):
        assert CURRENT_SCHEMA_VERSION == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_schema_versioning.py -v`
Expected: ImportError — `_base` module does not exist yet

- [ ] **Step 3: Implement _base.py**

```python
# skills/scripts/models/_base.py
"""Base classes for Pydantic validation models."""
from pydantic import BaseModel, field_validator, ConfigDict

CURRENT_SCHEMA_VERSION = 1


class StrictModel(BaseModel):
    """Base for nested models. Forbids unknown fields."""
    model_config = ConfigDict(extra="forbid")


class SchemaVersionedModel(StrictModel):
    """Base for top-level artifact models. Requires schema_version."""
    schema_version: int

    @field_validator("schema_version")
    @classmethod
    def must_match_current(cls, v: int) -> int:
        if v != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version={v} but validator is pinned to v{CURRENT_SCHEMA_VERSION}. "
                f"Update the frontmatter to schema_version: {CURRENT_SCHEMA_VERSION}, "
                f"or invoke the validator with --schema-version {v} for forensic review."
            )
        return v
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_schema_versioning.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/scripts/models/_base.py tests/unit/test_models/test_schema_versioning.py
git commit -m "feat(pydantic): add StrictModel + SchemaVersionedModel base classes"
```

---

### Task 3: Plan Model + Tests

**Files:**
- Create: `skills/scripts/models/plan.py`
- Create: `tests/unit/test_models/test_plan_model.py`

**Pattern References:**
- `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md` lines 21–51 — Plan schema fields and validators

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_models/test_plan_model.py
"""Tests for Plan Pydantic model and its cross-field validators."""
import pytest
from pydantic import ValidationError

from plan import (
    Plan, Task, Module, SharedConstant, PatternReference, FeatureArchetype,
)
from _base import CURRENT_SCHEMA_VERSION


MINIMAL_PLAN = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "feature_archetype": "greenfield",
    "tasks": [{"id": 0, "title": "Setup"}, {"id": 1, "title": "Build"}],
}


class TestPlanGoldenInput:
    def test_minimal_plan_parses(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        assert plan.feature_archetype == "greenfield"
        assert len(plan.tasks) == 2

    def test_roundtrip_through_json(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        dumped = plan.model_dump()
        reparsed = Plan.model_validate(dumped)
        assert reparsed == plan


class TestPlanFieldValidation:
    def test_missing_tasks_fails(self):
        data = {"schema_version": CURRENT_SCHEMA_VERSION, "feature_archetype": "greenfield"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["loc"] == ("tasks",)

    def test_missing_feature_archetype_fails(self):
        data = {"schema_version": CURRENT_SCHEMA_VERSION, "tasks": [{"id": 0, "title": "x"}]}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["loc"] == ("feature_archetype",)

    def test_invalid_archetype_fails(self):
        data = {**MINIMAL_PLAN, "feature_archetype": "expansion"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"

    def test_extra_field_rejected(self):
        data = {**MINIMAL_PLAN, "bogus_field": "nope"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["type"] == "extra_forbidden"

    @pytest.mark.parametrize("archetype", ["greenfield", "replacement", "extension", "refactor", "migration"])
    def test_all_valid_archetypes_accepted(self, archetype):
        data = {**MINIMAL_PLAN, "feature_archetype": archetype}
        plan = Plan.model_validate(data)
        assert plan.feature_archetype == archetype

    def test_literal_error_ctx_expected_shape(self):
        """Pin the shape of Pydantic v2 ctx.expected for literal_error."""
        data = {**MINIMAL_PLAN, "feature_archetype": "bogus"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        err = exc.value.errors()[0]
        assert err["type"] == "literal_error"
        assert "expected" in err.get("ctx", {}), \
            f"Pydantic literal_error ctx must contain 'expected' key; got {err.get('ctx')}"


class TestTaskUniqueSequentialIds:
    def test_non_sequential_fails(self):
        data = {**MINIMAL_PLAN, "tasks": [{"id": 0, "title": "a"}, {"id": 5, "title": "b"}]}
        with pytest.raises(ValidationError, match="sequential ascending"):
            Plan.model_validate(data)

    def test_duplicate_ids_fail(self):
        data = {**MINIMAL_PLAN, "tasks": [{"id": 0, "title": "a"}, {"id": 0, "title": "b"}]}
        with pytest.raises(ValidationError, match="Duplicate"):
            Plan.model_validate(data)

    def test_sequential_ids_pass(self):
        data = {**MINIMAL_PLAN, "tasks": [{"id": 0, "title": "a"}, {"id": 1, "title": "b"}, {"id": 2, "title": "c"}]}
        plan = Plan.model_validate(data)
        assert len(plan.tasks) == 3


class TestDependsOnValidation:
    def test_invalid_dependency_fails(self):
        data = {**MINIMAL_PLAN, "tasks": [
            {"id": 0, "title": "a"},
            {"id": 1, "title": "b", "depends_on": [99]},
        ]}
        with pytest.raises(ValidationError, match="don't exist"):
            Plan.model_validate(data)

    def test_forward_dependency_fails(self):
        data = {**MINIMAL_PLAN, "tasks": [
            {"id": 0, "title": "a", "depends_on": [1]},
            {"id": 1, "title": "b"},
        ]}
        with pytest.raises(ValidationError, match="cannot depend on"):
            Plan.model_validate(data)

    def test_valid_backward_dependency_passes(self):
        data = {**MINIMAL_PLAN, "tasks": [
            {"id": 0, "title": "a"},
            {"id": 1, "title": "b", "depends_on": [0]},
        ]}
        plan = Plan.model_validate(data)
        assert plan.tasks[1].depends_on == [0]


class TestSharedConstantsValidation:
    def test_undeclared_constant_fails(self):
        data = {
            **MINIMAL_PLAN,
            "tasks": [{"id": 0, "title": "a", "shared_constants_used": ["app.config.X"]}],
        }
        with pytest.raises(ValidationError, match="not in plan.shared_constants"):
            Plan.model_validate(data)

    def test_declared_constant_passes(self):
        data = {
            **MINIMAL_PLAN,
            "shared_constants": [{"path": "app.config.X", "value": "1", "reason": "test"}],
            "tasks": [{"id": 0, "title": "a", "shared_constants_used": ["app.config.X"]}],
        }
        plan = Plan.model_validate(data)
        assert len(plan.shared_constants) == 1


class TestPatternReferencesValidation:
    def test_undeclared_pattern_fails(self):
        data = {
            **MINIMAL_PLAN,
            "tasks": [{"id": 0, "title": "a", "pattern_references": ["nonexistent"]}],
        }
        with pytest.raises(ValidationError, match="not in plan.pattern_references"):
            Plan.model_validate(data)

    def test_declared_pattern_passes(self):
        data = {
            **MINIMAL_PLAN,
            "pattern_references": [{"name": "p1", "source_files": ["f.py"], "reason": "test"}],
            "tasks": [{"id": 0, "title": "a", "pattern_references": ["p1"]}],
        }
        plan = Plan.model_validate(data)
        assert plan.tasks[0].pattern_references == ["p1"]


class TestModuleValidation:
    def test_task_claimed_by_two_modules_fails(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [
                {"id": 1, "title": "A", "task_ids": [0]},
                {"id": 2, "title": "B", "task_ids": [0]},
            ],
        }
        with pytest.raises(ValidationError, match="claimed by Module"):
            Plan.model_validate(data)

    def test_orphan_task_fails(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [{"id": 1, "title": "A", "task_ids": [0]}],
        }
        with pytest.raises(ValidationError, match="not claimed"):
            Plan.model_validate(data)

    def test_valid_modules_pass(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [{"id": 1, "title": "All", "task_ids": [0, 1]}],
        }
        plan = Plan.model_validate(data)
        assert len(plan.modules) == 1

    def test_no_modules_is_valid(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        assert plan.modules is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -v`
Expected: ImportError — `plan` module does not exist yet

- [ ] **Step 3: Implement plan.py**

```python
# skills/scripts/models/plan.py
"""Pydantic model for Plan artifacts (YAML frontmatter)."""
from typing import Literal

from pydantic import Field, model_validator

from _base import StrictModel, SchemaVersionedModel

FeatureArchetype = Literal["greenfield", "replacement", "extension", "refactor", "migration"]


class SharedConstant(StrictModel):
    path: str
    value: str
    reason: str


class PatternReference(StrictModel):
    name: str
    source_files: list[str]
    reason: str


class Task(StrictModel):
    id: int
    title: str
    module_id: int | None = None
    depends_on: list[int] = Field(default_factory=list)
    pattern_references: list[str] = Field(default_factory=list)
    shared_constants_used: list[str] = Field(default_factory=list)


class Module(StrictModel):
    id: int
    title: str
    task_ids: list[int]


class Plan(SchemaVersionedModel):
    feature_archetype: FeatureArchetype
    source_contracts: str | None = None
    shared_constants: list[SharedConstant] = Field(default_factory=list)
    pattern_references: list[PatternReference] = Field(default_factory=list)
    modules: list[Module] | None = None
    tasks: list[Task]

    @model_validator(mode="after")
    def tasks_have_unique_sequential_ids(self) -> "Plan":
        ids = [t.id for t in self.tasks]
        if ids != sorted(ids):
            raise ValueError(f"Task IDs must be sequential ascending; got {ids}")
        if len(ids) != len(set(ids)):
            dupes = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate task IDs: {sorted(set(dupes))}")
        return self

    @model_validator(mode="after")
    def depends_on_references_valid_ids(self) -> "Plan":
        valid_ids = {t.id for t in self.tasks}
        for task in self.tasks:
            invalid = [d for d in task.depends_on if d not in valid_ids]
            if invalid:
                raise ValueError(
                    f"Task {task.id} depends_on={invalid} but those task IDs don't exist in plan"
                )
            forward = [d for d in task.depends_on if d >= task.id]
            if forward:
                raise ValueError(
                    f"Task {task.id} cannot depend on task(s) {forward} — dependencies must have lower IDs"
                )
        return self

    @model_validator(mode="after")
    def shared_constants_used_are_declared(self) -> "Plan":
        declared_paths = {c.path for c in self.shared_constants}
        for task in self.tasks:
            undeclared = [p for p in task.shared_constants_used if p not in declared_paths]
            if undeclared:
                raise ValueError(
                    f"Task {task.id} uses shared_constants {undeclared} but they're not in plan.shared_constants"
                )
        return self

    @model_validator(mode="after")
    def pattern_references_are_declared(self) -> "Plan":
        declared = {p.name for p in self.pattern_references}
        for task in self.tasks:
            undeclared = [p for p in task.pattern_references if p not in declared]
            if undeclared:
                raise ValueError(
                    f"Task {task.id} references patterns {undeclared} but they're not in plan.pattern_references"
                )
        return self

    @model_validator(mode="after")
    def module_task_ids_are_consistent(self) -> "Plan":
        if self.modules is None:
            return self
        seen: dict[int, int] = {}
        for mod in self.modules:
            for tid in mod.task_ids:
                if tid in seen:
                    raise ValueError(
                        f"Task {tid} claimed by Module {seen[tid]} AND Module {mod.id}"
                    )
                seen[tid] = mod.id
        all_task_ids = {t.id for t in self.tasks}
        claimed = set(seen.keys())
        orphans = all_task_ids - claimed
        if orphans:
            raise ValueError(f"Tasks {sorted(orphans)} are not claimed by any module")
        return self
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -v`
Expected: All 21 tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/scripts/models/plan.py tests/unit/test_models/test_plan_model.py
git commit -m "feat(pydantic): add Plan model with 5 cross-field validators"
```

---

### Task 4: HandoffPackage Model + Tests

**Files:**
- Create: `skills/scripts/models/handoff.py`
- Create: `tests/unit/test_models/test_handoff_model.py`

**Pattern References:**
- `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md` lines 53–75 — HandoffPackage schema

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_models/test_handoff_model.py
"""Tests for HandoffPackage Pydantic model."""
import pytest
from pydantic import ValidationError

from handoff import HandoffPackage, FieldType, FormatRule, Sample
from _base import CURRENT_SCHEMA_VERSION


MINIMAL_HANDOFF = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "package_name": "test-package",
    "feeds_into": "brainstorming",
    "one_sentence_purpose": "Test handoff for unit tests.",
    "contract_constraints": [
        {"name": "amount", "kind": "float"},
    ],
    "samples": [
        {"path": "samples/example.csv", "description": "Example data"},
    ],
}


class TestHandoffGoldenInput:
    def test_minimal_handoff_parses(self):
        pkg = HandoffPackage.model_validate(MINIMAL_HANDOFF)
        assert pkg.package_name == "test-package"
        assert len(pkg.samples) == 1

    def test_roundtrip_through_json(self):
        pkg = HandoffPackage.model_validate(MINIMAL_HANDOFF)
        reparsed = HandoffPackage.model_validate(pkg.model_dump())
        assert reparsed == pkg


class TestHandoffFieldValidation:
    def test_missing_package_name_fails(self):
        data = {k: v for k, v in MINIMAL_HANDOFF.items() if k != "package_name"}
        with pytest.raises(ValidationError) as exc:
            HandoffPackage.model_validate(data)
        assert exc.value.errors()[0]["loc"] == ("package_name",)

    def test_invalid_field_type_kind_fails(self):
        data = {**MINIMAL_HANDOFF, "contract_constraints": [{"name": "x", "kind": "complex"}]}
        with pytest.raises(ValidationError) as exc:
            HandoffPackage.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"

    @pytest.mark.parametrize("kind", ["string", "integer", "float", "boolean", "date", "enum"])
    def test_all_valid_field_type_kinds(self, kind):
        data = {**MINIMAL_HANDOFF, "contract_constraints": [{"name": "x", "kind": kind}]}
        pkg = HandoffPackage.model_validate(data)
        assert pkg.contract_constraints[0].kind == kind

    def test_extra_field_rejected(self):
        data = {**MINIMAL_HANDOFF, "bogus": "nope"}
        with pytest.raises(ValidationError) as exc:
            HandoffPackage.model_validate(data)
        assert exc.value.errors()[0]["type"] == "extra_forbidden"

    def test_field_type_nullable_default_false(self):
        data = {**MINIMAL_HANDOFF}
        pkg = HandoffPackage.model_validate(data)
        assert pkg.contract_constraints[0].nullable is False

    def test_field_type_format_hint_optional(self):
        data = {**MINIMAL_HANDOFF, "contract_constraints": [
            {"name": "date", "kind": "date", "format_hint": "YYYY-MM-DD"},
        ]}
        pkg = HandoffPackage.model_validate(data)
        assert pkg.contract_constraints[0].format_hint == "YYYY-MM-DD"


class TestFormatRulesValidation:
    def test_undeclared_field_in_applies_to_fails(self):
        data = {**MINIMAL_HANDOFF, "format_rules": [
            {"applies_to": ["nonexistent"], "rule": "must be positive"},
        ]}
        with pytest.raises(ValidationError, match="aren't declared"):
            HandoffPackage.model_validate(data)

    def test_declared_field_in_applies_to_passes(self):
        data = {**MINIMAL_HANDOFF, "format_rules": [
            {"applies_to": ["amount"], "rule": "must be positive"},
        ]}
        pkg = HandoffPackage.model_validate(data)
        assert len(pkg.format_rules) == 1


class TestAtLeastOneSample:
    def test_empty_samples_fails(self):
        data = {**MINIMAL_HANDOFF, "samples": []}
        with pytest.raises(ValidationError, match="at least one sample"):
            HandoffPackage.model_validate(data)

    def test_one_sample_passes(self):
        pkg = HandoffPackage.model_validate(MINIMAL_HANDOFF)
        assert len(pkg.samples) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_handoff_model.py -v`
Expected: ImportError — `handoff` module does not exist yet

- [ ] **Step 3: Implement handoff.py**

```python
# skills/scripts/models/handoff.py
"""Pydantic model for HandoffPackage artifacts (YAML frontmatter)."""
from typing import Literal

from pydantic import Field, model_validator

from _base import StrictModel, SchemaVersionedModel

FieldTypeKind = Literal["string", "integer", "float", "boolean", "date", "enum"]


class FieldType(StrictModel):
    name: str
    kind: FieldTypeKind
    format_hint: str | None = None
    nullable: bool = False


class FormatRule(StrictModel):
    applies_to: list[str]
    rule: str


class Sample(StrictModel):
    path: str
    description: str


class HandoffPackage(SchemaVersionedModel):
    package_name: str
    feeds_into: str
    one_sentence_purpose: str
    contract_constraints: list[FieldType]
    format_rules: list[FormatRule] = Field(default_factory=list)
    samples: list[Sample]

    @model_validator(mode="after")
    def format_rules_reference_declared_fields(self) -> "HandoffPackage":
        declared = {f.name for f in self.contract_constraints}
        for rule in self.format_rules:
            undeclared = [f for f in rule.applies_to if f not in declared]
            if undeclared:
                raise ValueError(
                    f"FormatRule applies_to={undeclared} but those fields aren't declared in contract_constraints"
                )
        return self

    @model_validator(mode="after")
    def at_least_one_sample(self) -> "HandoffPackage":
        if not self.samples:
            raise ValueError("HandoffPackage must include at least one sample")
        return self
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_handoff_model.py -v`
Expected: All 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add skills/scripts/models/handoff.py tests/unit/test_models/test_handoff_model.py
git commit -m "feat(pydantic): add HandoffPackage model with 2 cross-field validators"
```

---

### Task 5: Error Formatter + Tests

**Files:**
- Create: `skills/scripts/models/errors.py`
- Create: `tests/unit/test_models/test_error_formatter.py`

**Pattern References:**
- `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md` lines 77–83 — error block headers

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/test_models/test_error_formatter.py
"""Tests for the validation error and YAML error formatters."""
import pytest
from pydantic import ValidationError

from errors import format_validation_error, format_yaml_error
from plan import Plan
from _base import CURRENT_SCHEMA_VERSION


class TestFormatValidationError:
    def _get_validation_error(self, data: dict) -> ValidationError:
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        return exc.value

    def test_header_contains_validation_failed(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test-plan.md")
        assert "VALIDATION FAILED" in output
        assert "test-plan.md" in output

    def test_shows_field_path(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test.md")
        assert "feature_archetype" in output

    def test_shows_issue_count(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test.md")
        assert "issue(s) found" in output

    def test_literal_error_shows_expected(self):
        err = self._get_validation_error({
            "schema_version": CURRENT_SCHEMA_VERSION,
            "feature_archetype": "bogus",
            "tasks": [{"id": 0, "title": "x"}],
        })
        output = format_validation_error(err, "test.md")
        assert "Expected:" in output

    def test_missing_field_shows_required(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test.md")
        assert "required" in output

    def test_missing_schema_version_shows_hint(self):
        err = self._get_validation_error({"feature_archetype": "greenfield", "tasks": []})
        output = format_validation_error(err, "test.md")
        assert "schema_version: 1" in output
        assert "Hint:" in output

    def test_box_drawing_borders_present(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test.md")
        assert "═" in output


class TestFormatYamlError:
    def test_header_contains_yaml_parse_failed(self):
        output = format_yaml_error(ValueError("bad yaml"), "test.md")
        assert "YAML PARSE FAILED" in output
        assert "test.md" in output

    def test_shows_exception_details(self):
        output = format_yaml_error(ValueError("unexpected ':'"), "test.md")
        assert "unexpected ':'" in output

    def test_notes_pydantic_not_attempted(self):
        output = format_yaml_error(ValueError("x"), "test.md")
        assert "Pydantic validation was not attempted" in output

    def test_distinct_from_validation_header(self):
        yaml_output = format_yaml_error(ValueError("x"), "test.md")
        assert "YAML PARSE FAILED" in yaml_output
        assert "VALIDATION FAILED" not in yaml_output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_error_formatter.py -v`
Expected: ImportError — `errors` module does not exist yet

- [ ] **Step 3: Implement errors.py**

```python
# skills/scripts/models/errors.py
"""Human-readable error formatters for Pydantic validation and YAML parse errors."""
from pydantic import ValidationError


def format_validation_error(e: ValidationError, artifact_path: str) -> str:
    """Transform a Pydantic ValidationError into a hook-friendly explanatory block."""
    lines = [
        "═══════════════════════════════════════════════════════════════════",
        f" VALIDATION FAILED: {artifact_path}",
        f" {len(e.errors())} issue(s) found. Fix each and re-validate.",
        "═══════════════════════════════════════════════════════════════════",
        "",
    ]
    for i, err in enumerate(e.errors(), 1):
        path = ".".join(str(p) for p in err["loc"])
        lines.append(f"[{i}] Field:    {path}")
        lines.append(f"    Problem:  {err['msg']}")
        lines.append(f"    Got:      {err.get('input', '<unavailable>')!r}")
        if err["type"] == "literal_error":
            lines.append(f"    Expected: one of {err.get('ctx', {}).get('expected', '?')}")
        elif err["type"] == "missing":
            lines.append(f"    Expected: this field is required")
        if path == "schema_version" and err["type"] == "missing":
            lines.append(
                f"    Hint:     Add `schema_version: 1` as the first line of your YAML frontmatter."
            )
        lines.append("")
    lines.append("═══════════════════════════════════════════════════════════════════")
    return "\n".join(lines)


def format_yaml_error(yaml_err: Exception, artifact_path: str) -> str:
    """YAML parse errors use a distinct block — separate layer from Pydantic."""
    lines = [
        "═══════════════════════════════════════════════════════════════════",
        f" YAML PARSE FAILED: {artifact_path}",
        " Your YAML frontmatter is syntactically invalid.",
        " Pydantic validation was not attempted — fix the YAML first.",
        "═══════════════════════════════════════════════════════════════════",
        "",
        f"  {type(yaml_err).__name__}: {yaml_err}",
        "",
        "═══════════════════════════════════════════════════════════════════",
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_error_formatter.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Run full Module 1 test suite**

Run: `.venv/bin/python3 -m pytest tests/unit/test_models/ -v`
Expected: All ~52 tests PASS (7 + 21 + 13 + 11)

- [ ] **Step 6: Commit**

```bash
git add skills/scripts/models/errors.py tests/unit/test_models/test_error_formatter.py
git commit -m "feat(pydantic): add validation and YAML error formatters"
```

## Module 1 Acceptance Criteria

- [ ] `skills/scripts/models/` exists with `__init__.py`, `_base.py`, `plan.py`, `handoff.py`, `errors.py`
- [ ] `StrictModel` enforces `extra="forbid"`; `SchemaVersionedModel` enforces `schema_version` pinning
- [ ] `Plan` validates 5 cross-field relationships
- [ ] `HandoffPackage` validates 2 in-model cross-field relationships
- [ ] Error formatter produces split blocks with field paths, expected/got, hints
- [ ] ~52 unit tests pass in `tests/unit/test_models/`
- [ ] `requirements.txt` contains `pydantic>=2.7,<3`
- [ ] Test fixture files exist in `tests/fixtures/plans/` and `tests/fixtures/handoffs/`
