---
schema_version: 1
feature_archetype: refactor
# enforcement_tier: standard — added by this plan's own Task 3
source_contracts: "docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/spec-distilled.md"
shared_constants:
  - path: "skills.scripts.models._base.CURRENT_SCHEMA_VERSION"
    value: "1"
    reason: "All models pin to this version"
pattern_references:
  - name: "checkpoint-result-model"
    source_files: ["skills/scripts/models/checkpoint_result.py"]
    reason: "SchemaVersionedModel pattern with Literal types and cross-field validators"
  - name: "plan-model"
    source_files: ["skills/scripts/models/plan.py"]
    reason: "Existing Plan model to extend with enforcement_tier and Module.file"
  - name: "plan-model-tests"
    source_files: ["tests/unit/test_models/test_plan_model.py"]
    reason: "Pydantic test patterns: MINIMAL fixtures, ValidationError assertions, parameterized archetypes"
tasks:
  - id: 0
    title: "Contract verification"
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION"]
    pattern_references: ["checkpoint-result-model", "plan-model"]
  - id: 1
    title: "SddSession Pydantic model"
    depends_on: [0]
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION"]
    pattern_references: ["checkpoint-result-model"]
  - id: 2
    title: "SddSession model tests"
    depends_on: [1]
    pattern_references: ["plan-model-tests"]
  - id: 3
    title: "Plan model extension"
    depends_on: [0]
    pattern_references: ["plan-model"]
  - id: 4
    title: "Manifest writer script"
    depends_on: [1, 3]
  - id: 5
    title: "Manifest writer tests"
    depends_on: [4]
---

# Module 1: Pydantic Models and Manifest Writer

**Goal:** Create the `SddSession` Pydantic model, extend the `Plan` model with `enforcement_tier` and `Module.file`, build the manifest writer script, and test all of them.

**Source Contracts:** `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/spec-distilled.md` — §Component Specifications

**Contract Constraints:**
- `Tier = Literal["micro", "standard"]`
- `ReviewMode = Literal["dispatched", "self_review", "skip"]`
- `DispatchMode = Literal["required", "controller_direct"]`
- `RequirementLevel = Literal["required", "skip"]`
- `SddSession` extends `SchemaVersionedModel` (from `_base.py`)
- All paths in `ArtifactPaths` are git-root-relative strings
- `tier`, `enforcement`, `process_requirements` are immutable after creation
- Midpoint formula: `task_range[0] + (range_size + 1) // 2`

**Pattern References:**
- `skills/scripts/models/checkpoint_result.py` — `SchemaVersionedModel` usage, `Literal` types, `model_validator`
- `skills/scripts/models/plan.py` — existing `Plan` model structure, `Module` class
- `tests/unit/test_models/test_plan_model.py` — `MINIMAL_PLAN` fixture pattern, `ValidationError` assertions

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `skills/scripts/models/sdd_session.py` | Create | `SddSession`, `Enforcement`, `ProcessRequirements`, `ArtifactPaths`, `ModuleState` models + `TIER_PROFILES` constant |
| `skills/scripts/models/plan.py` | Modify | Add `enforcement_tier` to `Plan`, `file` to `Module` |
| `skills/subagent-driven-development/scripts/materialize-manifest.py` | Create | CLI script: reads plan frontmatter, computes profile from tier, writes `.sdd-session.json` |
| `tests/unit/test_models/test_sdd_session_model.py` | Create | Unit tests for `SddSession` model |
| `tests/unit/test_materialize_manifest.py` | Create | Unit tests for manifest writer |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 0 | `tests/unit/test_models/test_sdd_session_model.py` (fixture only) | `skills/scripts/models/_base.py`, `skills/scripts/models/checkpoint_result.py`, `skills/scripts/models/plan.py` | — |
| Task 1 | `skills/scripts/models/sdd_session.py` | `skills/scripts/models/_base.py` | Task 0 |
| Task 2 | `tests/unit/test_models/test_sdd_session_model.py` | `skills/scripts/models/sdd_session.py` | Task 1 |
| Task 3 | `skills/scripts/models/plan.py` | — | Task 0 |
| Task 4 | `skills/subagent-driven-development/scripts/materialize-manifest.py` | `skills/scripts/models/sdd_session.py`, `skills/scripts/models/plan.py` | Task 1, 3 |
| Task 5 | `tests/unit/test_materialize_manifest.py` | `skills/subagent-driven-development/scripts/materialize-manifest.py` | Task 4 |

## Acceptance Criteria

- [ ] `SddSession` model validates correctly for both tier profiles
- [ ] `SddSession` rejects invalid tiers, overlapping task ranges, and extra fields
- [ ] `Plan` model accepts `enforcement_tier` (optional, defaults to None)
- [ ] `Module` class accepts `file` (optional, defaults to None)
- [ ] Existing `Plan` model tests still pass (backward compatible)
- [ ] `materialize-manifest.py` produces correct JSON for single-module and multi-module plans
- [ ] Manifest writer is idempotent (no-op when manifest matches plan)

---

### Task 0: Contract Verification

**Files:**
- Read: `skills/scripts/models/_base.py`, `skills/scripts/models/checkpoint_result.py`, `skills/scripts/models/plan.py`
- Read: `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/spec-distilled.md`

**Pattern References:**
- `skills/scripts/models/checkpoint_result.py` — follow `SchemaVersionedModel` pattern
- `skills/scripts/models/plan.py` — understand existing `Module` class and `Plan` fields

- [x] **Step 1: Read base classes and verify contract facts**

Read `skills/scripts/models/_base.py` and confirm:
- `CURRENT_SCHEMA_VERSION` = 1
- `StrictModel` uses `extra="forbid"`
- `SchemaVersionedModel` extends `StrictModel` with `schema_version` field and version validator

Read `skills/scripts/models/checkpoint_result.py` and note:
- Uses `Literal` for enum-like fields
- Uses `model_validator(mode="after")` for cross-field validation
- Uses `int | None` union syntax

- [x] **Step 2: Read existing Plan model and note extension points**

Read `skills/scripts/models/plan.py` and confirm:
- `Module` class has: `id: int`, `title: str`, `task_ids: list[int]`
- `Plan` class has: `feature_archetype: FeatureArchetype`, `modules: list[Module] | None`
- Validator `module_task_ids_are_consistent` already checks for cross-module task ID collisions

- [x] **Step 3: Record contract facts as fixtures**

Create a contract facts comment in the test file header (to be expanded in Task 2):

```python
# Contract facts from spec-distilled.md:
# - Tier = Literal["micro", "standard"]
# - ArtifactPaths fields: feature_dir, reports_dir, dispatch_log, deviations_file (all git-root-relative str)
# - Enforcement fields: pre_execution_audit, partner_review, dispatch_provenance, context_summary_at, checkpoint_files
# - ProcessRequirements fields: subagent_dispatch, spec_review_mode, quality_review_mode, partner_review_mode, deviations_log, checkpoint_script
# - SddSession.tier, .enforcement, .process_requirements are immutable after creation
# - Midpoint formula: task_range[0] + (range_size + 1) // 2
```

- [x] **Step 4: Commit contract verification**

```bash
git add tests/unit/test_models/test_sdd_session_model.py
git commit -m "test: add contract facts fixtures for SddSession model"
```

---

### Task 1: SddSession Pydantic Model

**Files:**
- Create: `skills/scripts/models/sdd_session.py`

**Pattern References:**
- `skills/scripts/models/checkpoint_result.py` — follow `SchemaVersionedModel`, `Literal`, `model_validator` pattern

- [x] **Step 1: Write the model file**

Create `skills/scripts/models/sdd_session.py`:

```python
"""Pydantic model for SDD session manifest (.sdd-session.json)."""
from typing import Literal

from pydantic import Field, model_validator

from _base import StrictModel, SchemaVersionedModel

Tier = Literal["micro", "standard"]
ReviewMode = Literal["dispatched", "self_review", "skip"]
DispatchMode = Literal["required", "controller_direct"]
RequirementLevel = Literal["required", "skip"]


class ArtifactPaths(StrictModel):
    """All paths are git-root-relative."""
    feature_dir: str
    reports_dir: str
    dispatch_log: str
    deviations_file: str


class ModuleState(StrictModel):
    id: int
    title: str
    file: str
    task_ids: list[int]


class Enforcement(StrictModel):
    pre_execution_audit: bool
    partner_review: bool
    dispatch_provenance: bool
    context_summary_at: int | None
    checkpoint_files: bool


class ProcessRequirements(StrictModel):
    subagent_dispatch: DispatchMode
    spec_review_mode: ReviewMode
    quality_review_mode: ReviewMode
    partner_review_mode: ReviewMode
    deviations_log: RequirementLevel
    checkpoint_script: RequirementLevel


TIER_PROFILES: dict[str, dict] = {
    "micro": {
        "enforcement": {
            "pre_execution_audit": False,
            "partner_review": False,
            "dispatch_provenance": False,
            "context_summary_at": None,
            "checkpoint_files": False,
        },
        "process_requirements": {
            "subagent_dispatch": "controller_direct",
            "spec_review_mode": "self_review",
            "quality_review_mode": "self_review",
            "partner_review_mode": "skip",
            "deviations_log": "required",
            "checkpoint_script": "skip",
        },
    },
    "standard": {
        "enforcement": {
            "pre_execution_audit": True,
            "partner_review": True,
            "dispatch_provenance": True,
            "context_summary_at": None,  # computed at materialization time
            "checkpoint_files": True,
        },
        "process_requirements": {
            "subagent_dispatch": "required",
            "spec_review_mode": "dispatched",
            "quality_review_mode": "dispatched",
            "partner_review_mode": "dispatched",
            "deviations_log": "required",
            "checkpoint_script": "required",
        },
    },
}


class SddSession(SchemaVersionedModel):
    tier: Tier
    paths: ArtifactPaths
    plan_file: str
    active_module_id: int | None = None
    active_module_file: str | None = None
    task_range: tuple[int, int]
    total_tasks: int
    midpoint: int
    enforcement: Enforcement
    process_requirements: ProcessRequirements
    completed_modules: list[str] = Field(default_factory=list)
    module_reports_archived: bool = False
    modules: list[ModuleState] | None = None
    dispatch_log_sentinel: bool = False

    @model_validator(mode="after")
    def task_range_valid(self) -> "SddSession":
        start, end = self.task_range
        if start > end:
            raise ValueError(
                f"task_range start ({start}) > end ({end})"
            )
        if end - start + 1 > self.total_tasks:
            raise ValueError(
                f"task_range covers {end - start + 1} tasks but total_tasks is {self.total_tasks}"
            )
        return self

    @model_validator(mode="after")
    def midpoint_in_range(self) -> "SddSession":
        start, end = self.task_range
        if not (start <= self.midpoint <= end):
            raise ValueError(
                f"midpoint ({self.midpoint}) outside task_range [{start}, {end}]"
            )
        return self

    @model_validator(mode="after")
    def module_fields_consistent(self) -> "SddSession":
        if self.modules is not None:
            if self.active_module_id is None:
                raise ValueError(
                    "modules is set but active_module_id is None"
                )
            valid_ids = {m.id for m in self.modules}
            if self.active_module_id not in valid_ids:
                raise ValueError(
                    f"active_module_id ({self.active_module_id}) not in modules: {valid_ids}"
                )
        return self
```

- [x] **Step 2: Verify import works**

```bash
cd skills/scripts/models && ../.venv/bin/python3 -c "from sdd_session import SddSession, TIER_PROFILES; print('OK')"
```

Expected: `OK`

- [x] **Step 3: Commit**

```bash
git add skills/scripts/models/sdd_session.py
git commit -m "feat: add SddSession Pydantic model for session manifest"
```

---

### Task 2: SddSession Model Tests

**Files:**
- Create: `tests/unit/test_models/test_sdd_session_model.py`

**Pattern References:**
- `tests/unit/test_models/test_plan_model.py` — `MINIMAL_PLAN` fixture pattern, `ValidationError` assertions

- [x] **Step 1: Write the test file**

```python
"""Tests for SddSession Pydantic model."""
import pytest
from pydantic import ValidationError

from sdd_session import (
    SddSession, Enforcement, ProcessRequirements, ArtifactPaths,
    ModuleState, TIER_PROFILES, Tier,
)
from _base import CURRENT_SCHEMA_VERSION


MINIMAL_PATHS = {
    "feature_dir": "docs/imp-plans/2026-05-10-my-feature",
    "reports_dir": "docs/imp-plans/2026-05-10-my-feature/reports",
    "dispatch_log": "docs/imp-plans/2026-05-10-my-feature/reports/.dispatch-log",
    "deviations_file": "docs/imp-plans/2026-05-10-my-feature/deviations.md",
}

MINIMAL_SESSION = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "tier": "standard",
    "paths": MINIMAL_PATHS,
    "plan_file": "docs/imp-plans/2026-05-10-my-feature/plan.md",
    "task_range": [0, 7],
    "total_tasks": 8,
    "midpoint": 4,
    "enforcement": TIER_PROFILES["standard"]["enforcement"],
    "process_requirements": TIER_PROFILES["standard"]["process_requirements"],
}


class TestSddSessionGoldenInput:
    def test_minimal_session_parses(self):
        session = SddSession.model_validate(MINIMAL_SESSION)
        assert session.tier == "standard"
        assert session.total_tasks == 8

    def test_roundtrip_through_json(self):
        session = SddSession.model_validate(MINIMAL_SESSION)
        dumped = session.model_dump()
        reparsed = SddSession.model_validate(dumped)
        assert reparsed == session

    def test_micro_tier_parses(self):
        data = {
            **MINIMAL_SESSION,
            "tier": "micro",
            "task_range": [0, 1],
            "total_tasks": 2,
            "midpoint": 1,
            "enforcement": TIER_PROFILES["micro"]["enforcement"],
            "process_requirements": TIER_PROFILES["micro"]["process_requirements"],
        }
        session = SddSession.model_validate(data)
        assert session.tier == "micro"
        assert session.enforcement.pre_execution_audit is False


class TestSddSessionValidation:
    def test_invalid_tier_rejected(self):
        data = {**MINIMAL_SESSION, "tier": "comprehensive"}
        with pytest.raises(ValidationError) as exc:
            SddSession.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"

    def test_extra_field_rejected(self):
        data = {**MINIMAL_SESSION, "bogus_field": "nope"}
        with pytest.raises(ValidationError):
            SddSession.model_validate(data)

    def test_task_range_start_exceeds_end(self):
        data = {**MINIMAL_SESSION, "task_range": [5, 2]}
        with pytest.raises(ValidationError, match="start.*>.*end"):
            SddSession.model_validate(data)

    def test_task_range_exceeds_total(self):
        data = {**MINIMAL_SESSION, "task_range": [0, 20], "total_tasks": 8}
        with pytest.raises(ValidationError, match="total_tasks"):
            SddSession.model_validate(data)

    def test_midpoint_outside_range(self):
        data = {**MINIMAL_SESSION, "midpoint": 99}
        with pytest.raises(ValidationError, match="midpoint"):
            SddSession.model_validate(data)


class TestSddSessionModuleConsistency:
    def test_modules_require_active_module_id(self):
        data = {
            **MINIMAL_SESSION,
            "modules": [{"id": 1, "title": "Core", "file": "m1.md", "task_ids": [0, 1]}],
            "active_module_id": None,
        }
        with pytest.raises(ValidationError, match="active_module_id is None"):
            SddSession.model_validate(data)

    def test_active_module_id_must_exist_in_modules(self):
        data = {
            **MINIMAL_SESSION,
            "modules": [{"id": 1, "title": "Core", "file": "m1.md", "task_ids": [0, 1]}],
            "active_module_id": 99,
        }
        with pytest.raises(ValidationError, match="not in modules"):
            SddSession.model_validate(data)

    def test_valid_multi_module_session(self):
        data = {
            **MINIMAL_SESSION,
            "modules": [
                {"id": 1, "title": "Core", "file": "m1.md", "task_ids": [0, 1, 2, 3]},
                {"id": 2, "title": "API", "file": "m2.md", "task_ids": [4, 5, 6, 7]},
            ],
            "active_module_id": 1,
            "active_module_file": "m1.md",
        }
        session = SddSession.model_validate(data)
        assert len(session.modules) == 2


class TestTierProfiles:
    @pytest.mark.parametrize("tier", ["micro", "standard"])
    def test_tier_profile_produces_valid_enforcement(self, tier):
        enforcement = Enforcement.model_validate(TIER_PROFILES[tier]["enforcement"])
        assert isinstance(enforcement.pre_execution_audit, bool)

    @pytest.mark.parametrize("tier", ["micro", "standard"])
    def test_tier_profile_produces_valid_process_requirements(self, tier):
        pr = ProcessRequirements.model_validate(TIER_PROFILES[tier]["process_requirements"])
        assert pr.deviations_log == "required"

    def test_micro_skips_partner_review(self):
        pr = ProcessRequirements.model_validate(TIER_PROFILES["micro"]["process_requirements"])
        assert pr.partner_review_mode == "skip"

    def test_standard_requires_dispatched_reviews(self):
        pr = ProcessRequirements.model_validate(TIER_PROFILES["standard"]["process_requirements"])
        assert pr.spec_review_mode == "dispatched"
        assert pr.quality_review_mode == "dispatched"
```

- [x] **Step 2: Run tests**

```bash
.venv/bin/python3 -m pytest tests/unit/test_models/test_sdd_session_model.py -v
```

Expected: All tests PASS

- [x] **Step 3: Commit**

```bash
git add tests/unit/test_models/test_sdd_session_model.py
git commit -m "test: add SddSession model unit tests"
```

---

### Task 3: Plan Model Extension

**Files:**
- Modify: `skills/scripts/models/plan.py`

**Pattern References:**
- `skills/scripts/models/plan.py` — existing `Module` and `Plan` classes

- [x] **Step 1: Write failing test**

Add to `tests/unit/test_models/test_plan_model.py`:

```python
class TestEnforcementTierField:
    def test_plan_accepts_enforcement_tier(self):
        data = {**MINIMAL_PLAN, "enforcement_tier": "standard"}
        plan = Plan.model_validate(data)
        assert plan.enforcement_tier == "standard"

    def test_plan_accepts_micro_tier(self):
        data = {**MINIMAL_PLAN, "enforcement_tier": "micro"}
        plan = Plan.model_validate(data)
        assert plan.enforcement_tier == "micro"

    def test_plan_without_tier_defaults_to_none(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        assert plan.enforcement_tier is None

    def test_invalid_tier_rejected(self):
        data = {**MINIMAL_PLAN, "enforcement_tier": "comprehensive"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"


class TestModuleFileField:
    def test_module_accepts_file_field(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [{"id": 1, "title": "Core", "task_ids": [0, 1], "file": "module-1-core.md"}],
        }
        plan = Plan.model_validate(data)
        assert plan.modules[0].file == "module-1-core.md"

    def test_module_without_file_defaults_to_none(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [{"id": 1, "title": "Core", "task_ids": [0, 1]}],
        }
        plan = Plan.model_validate(data)
        assert plan.modules[0].file is None
```

- [x] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py::TestEnforcementTierField -v
```

Expected: FAIL — `enforcement_tier` field not recognized (extra_forbidden)

- [x] **Step 3: Implement the changes**

In `skills/scripts/models/plan.py`:

1. Add import of `Tier` from `sdd_session` (single source of truth — do NOT redefine):

```python
from sdd_session import Tier
```

Note: `sdd_session.py` must be created first (Task 1) before this import works. Task dependency already enforces this.

3. Add to `Module` class:

```python
file: str | None = None
```

4. Add to `Plan` class (after `feature_archetype`):

```python
enforcement_tier: Tier | None = None
```

- [x] **Step 4: Run all plan model tests**

```bash
.venv/bin/python3 -m pytest tests/unit/test_models/test_plan_model.py -v
```

Expected: All tests PASS (existing + new)

- [x] **Step 5: Commit**

```bash
git add skills/scripts/models/plan.py tests/unit/test_models/test_plan_model.py
git commit -m "feat: add enforcement_tier to Plan model and file to Module"
```

---

### Task 4: Manifest Writer Script

**Files:**
- Create: `skills/subagent-driven-development/scripts/materialize-manifest.py`

- [x] **Step 1: Write the manifest writer**

Create `skills/subagent-driven-development/scripts/materialize-manifest.py`:

```python
#!/usr/bin/env python3
"""
materialize-manifest.py

Reads plan frontmatter, computes enforcement profile from tier,
writes .sdd-session.json to the feature directory.

Exit codes:
  0 - Success (manifest written or already up-to-date)
  1 - Validation failure (bad frontmatter, missing fields)
  2 - Script error (bad arguments, file not found)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Add models to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))

try:
    import yaml
except ImportError:
    print("PyYAML required. Install: .venv/bin/pip install pyyaml", file=sys.stderr)
    sys.exit(2)

from sdd_session import SddSession, TIER_PROFILES, ArtifactPaths, Enforcement, ProcessRequirements, ModuleState


def extract_frontmatter(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    raw = text[3:end]
    return yaml.safe_load(raw)


def compute_midpoint(start: int, end: int) -> int:
    range_size = end - start + 1
    return start + (range_size + 1) // 2


def materialize(plan_file: str, feature_dir: str) -> int:
    plan_path = Path(plan_file)
    if not plan_path.is_file():
        print(f"Plan file not found: {plan_file}", file=sys.stderr)
        return 2

    text = plan_path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(text)
    if frontmatter is None:
        print(f"No YAML frontmatter in {plan_file}", file=sys.stderr)
        return 1

    tier = frontmatter.get("enforcement_tier", "standard")
    if tier not in TIER_PROFILES:
        print(f"Invalid enforcement_tier: {tier}", file=sys.stderr)
        return 1

    tasks = frontmatter.get("tasks", [])
    total_tasks = len(tasks)
    if total_tasks == 0:
        print("No tasks found in plan frontmatter", file=sys.stderr)
        return 1

    modules_raw = frontmatter.get("modules")
    modules = None
    active_module_id = None
    active_module_file = None

    if modules_raw:
        modules = []
        for m in modules_raw:
            modules.append(ModuleState(
                id=m["id"],
                title=m["title"],
                file=m.get("file", ""),
                task_ids=m["task_ids"],
            ))
        first = modules[0]
        task_range = (first.task_ids[0], first.task_ids[-1])
        active_module_id = first.id
        active_module_file = os.path.join(feature_dir, first.file) if first.file else None
    else:
        all_ids = sorted(t["id"] for t in tasks)
        task_range = (all_ids[0], all_ids[-1])

    midpoint = compute_midpoint(task_range[0], task_range[1])

    profile = TIER_PROFILES[tier]
    enforcement_data = dict(profile["enforcement"])
    if enforcement_data["context_summary_at"] is None and tier == "standard":
        enforcement_data["context_summary_at"] = midpoint

    # Normalize feature_dir to git-root-relative
    # The hook resolves paths as $GIT_ROOT/$path — absolute paths would break this.
    if os.path.isabs(feature_dir):
        git_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        ).stdout.strip()
        if git_root and feature_dir.startswith(git_root):
            feature_dir = os.path.relpath(feature_dir, git_root)
        else:
            print(f"WARNING: feature_dir '{feature_dir}' is absolute but not under git root", file=sys.stderr)

    paths = ArtifactPaths(
        feature_dir=feature_dir,
        reports_dir=os.path.join(feature_dir, "reports"),
        dispatch_log=os.path.join(feature_dir, "reports/.dispatch-log"),
        deviations_file=os.path.join(feature_dir, "deviations.md"),
    )

    session = SddSession(
        schema_version=1,
        tier=tier,
        paths=paths,
        plan_file=plan_file,
        active_module_id=active_module_id,
        active_module_file=active_module_file,
        task_range=task_range,
        total_tasks=total_tasks,
        midpoint=midpoint,
        enforcement=Enforcement.model_validate(enforcement_data),
        process_requirements=ProcessRequirements.model_validate(profile["process_requirements"]),
        modules=modules,
    )

    manifest_path = Path(feature_dir) / ".sdd-session.json"

    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        new_data = json.loads(session.model_dump_json())
        if existing == new_data:
            print(f"Manifest up-to-date: {manifest_path}")
            return 0
        print(f"WARNING: Manifest exists but differs from plan. Re-materializing.", file=sys.stderr)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(session.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"Manifest written: {manifest_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Materialize SDD session manifest")
    parser.add_argument("--plan-file", required=True, help="Path to plan.md")
    parser.add_argument("--feature-dir", required=True, help="Feature directory (git-root-relative)")
    args = parser.parse_args()
    sys.exit(materialize(args.plan_file, args.feature_dir))


if __name__ == "__main__":
    main()
```

- [x] **Step 2: Make executable and verify import**

```bash
chmod +x skills/subagent-driven-development/scripts/materialize-manifest.py
.venv/bin/python3 -c "import importlib.util; spec = importlib.util.spec_from_file_location('m', 'skills/subagent-driven-development/scripts/materialize-manifest.py'); print('OK')"
```

- [x] **Step 3: Commit**

```bash
git add skills/subagent-driven-development/scripts/materialize-manifest.py
git commit -m "feat: add manifest writer script for SDD session materialization"
```

---

### Task 5: Manifest Writer Tests

**Files:**
- Create: `tests/unit/test_materialize_manifest.py`

- [x] **Step 1: Write test file**

```python
"""Tests for materialize-manifest.py."""
import json
import os
import subprocess
import sys
import tempfile

import pytest

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "skills",
    "subagent-driven-development",
    "scripts",
    "materialize-manifest.py",
)

PYTHON = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    ".venv",
    "bin",
    "python3",
)


def make_plan(tier="standard", tasks=None, modules=None):
    if tasks is None:
        tasks = [{"id": 0, "title": "Setup"}, {"id": 1, "title": "Build"}]
    lines = ["---"]
    lines.append("schema_version: 1")
    lines.append("feature_archetype: greenfield")
    lines.append(f"enforcement_tier: {tier}")
    lines.append("tasks:")
    for t in tasks:
        deps = f"\n    depends_on: {t['depends_on']}" if "depends_on" in t else ""
        lines.append(f"  - id: {t['id']}\n    title: \"{t['title']}\"{deps}")
    if modules:
        lines.append("modules:")
        for m in modules:
            lines.append(f"  - id: {m['id']}")
            lines.append(f"    title: \"{m['title']}\"")
            lines.append(f"    task_ids: {m['task_ids']}")
            if "file" in m:
                lines.append(f"    file: \"{m['file']}\"")
    lines.append("---")
    lines.append("# Plan\n### Task 0: Setup\n- [ ] Do thing")
    return "\n".join(lines)


def run_materialize(plan_content, feature_dir=None):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(plan_content)
        plan_path = f.name

    if feature_dir is None:
        feature_dir = tempfile.mkdtemp()

    try:
        result = subprocess.run(
            [PYTHON, SCRIPT_PATH, "--plan-file", plan_path, "--feature-dir", feature_dir],
            capture_output=True,
            text=True,
            timeout=10,
        )
        manifest_path = os.path.join(feature_dir, ".sdd-session.json")
        manifest = None
        if os.path.isfile(manifest_path):
            manifest = json.loads(open(manifest_path).read())
        return {
            "exit_code": result.returncode,
            "manifest": manifest,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    finally:
        os.unlink(plan_path)


class TestManifestWriter:
    def test_standard_tier_produces_manifest(self):
        result = run_materialize(make_plan("standard"))
        assert result["exit_code"] == 0
        assert result["manifest"] is not None
        assert result["manifest"]["tier"] == "standard"

    def test_micro_tier_produces_manifest(self):
        result = run_materialize(make_plan("micro"))
        assert result["exit_code"] == 0
        assert result["manifest"]["tier"] == "micro"
        assert result["manifest"]["enforcement"]["pre_execution_audit"] is False

    def test_default_tier_is_standard(self):
        """When enforcement_tier line is absent from frontmatter, default to standard."""
        plan_lines = make_plan("standard").splitlines()
        plan_lines = [l for l in plan_lines if not l.strip().startswith("enforcement_tier:")]
        plan_no_tier = "\n".join(plan_lines)
        result = run_materialize(plan_no_tier)
        assert result["exit_code"] == 0
        assert result["manifest"]["tier"] == "standard"

    def test_invalid_tier_fails(self):
        result = run_materialize(make_plan("comprehensive"))
        assert result["exit_code"] == 1

    def test_midpoint_computation(self):
        tasks = [{"id": i, "title": f"T{i}"} for i in range(10)]
        result = run_materialize(make_plan("standard", tasks=tasks))
        assert result["exit_code"] == 0
        # range [0, 9], size 10, midpoint = 0 + (10+1)//2 = 5
        assert result["manifest"]["midpoint"] == 5

    def test_paths_are_git_root_relative(self):
        result = run_materialize(make_plan("standard"), feature_dir="docs/imp-plans/test-feat")
        assert result["manifest"]["paths"]["feature_dir"] == "docs/imp-plans/test-feat"
        assert result["manifest"]["paths"]["reports_dir"] == "docs/imp-plans/test-feat/reports"
        assert result["manifest"]["paths"]["dispatch_log"] == "docs/imp-plans/test-feat/reports/.dispatch-log"

    def test_idempotent_rerun(self):
        feature_dir = tempfile.mkdtemp()
        plan = make_plan("standard")
        result1 = run_materialize(plan, feature_dir=feature_dir)
        result2 = run_materialize(plan, feature_dir=feature_dir)
        assert result1["exit_code"] == 0
        assert result2["exit_code"] == 0
        assert "up-to-date" in result2["stdout"]


class TestMultiModuleManifest:
    def test_multi_module_sets_active_module(self):
        tasks = [{"id": i, "title": f"T{i}"} for i in range(8)]
        modules = [
            {"id": 1, "title": "Core", "task_ids": [0, 1, 2, 3], "file": "m1.md"},
            {"id": 2, "title": "API", "task_ids": [4, 5, 6, 7], "file": "m2.md"},
        ]
        result = run_materialize(make_plan("standard", tasks=tasks, modules=modules))
        assert result["exit_code"] == 0
        assert result["manifest"]["active_module_id"] == 1
        assert result["manifest"]["modules"] is not None
        assert len(result["manifest"]["modules"]) == 2
```

- [x] **Step 2: Run tests**

```bash
.venv/bin/python3 -m pytest tests/unit/test_materialize_manifest.py -v
```

Expected: All tests PASS

- [x] **Step 3: Commit**

```bash
git add tests/unit/test_materialize_manifest.py
git commit -m "test: add manifest writer unit tests"
```
