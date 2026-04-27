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
  - name: "phase-1-model-tests"
    source_files: ["tests/unit/test_models/test_plan_model.py"]
    reason: "Test structure for model validation: golden inputs, per-field failures, validator edge cases"
tasks:
  - id: 0
    title: "Contract Verification"
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION", "skills.scripts.models._base.StrictModel", "skills.scripts.models._base.SchemaVersionedModel"]
    pattern_references: ["phase-1-plan-model"]
  - id: 1
    title: "ImplementerReport Model"
    depends_on: [0]
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION", "skills.scripts.models._base.StrictModel", "skills.scripts.models._base.SchemaVersionedModel"]
    pattern_references: ["phase-1-plan-model"]
  - id: 2
    title: "ImplementerReport Unit Tests"
    depends_on: [1]
    pattern_references: ["phase-1-model-tests"]
  - id: 3
    title: "CheckpointResult Model"
    depends_on: [0]
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION", "skills.scripts.models._base.StrictModel", "skills.scripts.models._base.SchemaVersionedModel"]
    pattern_references: ["phase-1-plan-model"]
  - id: 4
    title: "CheckpointResult Unit Tests"
    depends_on: [3]
    pattern_references: ["phase-1-model-tests"]
  - id: 5
    title: "Test Fixtures"
    depends_on: [1, 3]
---

# Pydantic Phase 2 — Module 1: Models + Unit Tests

> **Parent plan:** `docs/imp-plans/2026-04-25-pydantic-phase-2-plan.md`
> **Module:** 1 of 3
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first.

**Module Goal:** Create ImplementerReport and CheckpointResult Pydantic models with comprehensive unit tests and validation fixtures.

**Source Contracts:** `docs/specs/2026-04-25-pydantic-phase-2-design-distilled.md` — Contract Facts section defines all field types, validators, and invariants.

**Contract Constraints:**
- ImplementerReport: `schema_version`, `task_id`, `status` (4 Literal values), `files_changed` (list[FileChange]), `tests` (TestSummary), `contract_compliance` (optional list)
- CheckpointResult: `schema_version`, `phase` (3 Literal values), `status` (PASS/FAIL), `task_number` (optional), `checks` (dict[str, CheckResult]), `warnings`, `blockers`, `progress` (optional)
- ImplementerReport model validators: `test_counts_consistent`, `files_changed_non_empty_for_done`
- CheckpointResult model validators: `fail_requires_blockers`, `blockers_reference_check_names`, `task_number_required_for_pre_dispatch`

**Feature Archetype:** Extension

## File Map

| File | Responsibility |
|------|----------------|
| `skills/scripts/models/implementer_report.py` | ImplementerReport model + nested types + 2 validators |
| `skills/scripts/models/checkpoint_result.py` | CheckpointResult model + nested types + 3 validators |
| `tests/unit/test_models/test_implementer_report_model.py` | ~15 model unit tests |
| `tests/unit/test_models/test_checkpoint_result_model.py` | ~12 model unit tests |
| `tests/fixtures/reports/valid/minimal-report.md` | Minimal valid report fixture (DONE, 1 file, no contracts) |
| `tests/fixtures/reports/valid/full-featured-report.md` | Full report fixture (DONE_WITH_CONCERNS, multiple files, contracts) |
| `tests/fixtures/reports/invalid/missing-status.md` | Missing status field |
| `tests/fixtures/reports/invalid/bad-status-enum.md` | Invalid status value |
| `tests/fixtures/reports/invalid/test-counts-inconsistent.md` | passing > written |
| `tests/fixtures/reports/invalid/no-files-for-done.md` | DONE with empty files_changed |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 0 | `tests/fixtures/reports/contracts/` | `skills/scripts/models/_base.py`, `skills/scripts/models/plan.py`, distilled spec | — |
| Task 1 | `skills/scripts/models/implementer_report.py` | `skills/scripts/models/_base.py` | Task 0 |
| Task 2 | `tests/unit/test_models/test_implementer_report_model.py` | `skills/scripts/models/implementer_report.py` | Task 1 |
| Task 3 | `skills/scripts/models/checkpoint_result.py` | `skills/scripts/models/_base.py` | Task 0 |
| Task 4 | `tests/unit/test_models/test_checkpoint_result_model.py` | `skills/scripts/models/checkpoint_result.py` | Task 3 |
| Task 5 | `tests/fixtures/reports/valid/`, `tests/fixtures/reports/invalid/` | `skills/scripts/models/implementer_report.py` | Tasks 1, 3 |

## Acceptance Criteria

- [ ] `implementer_report.py` defines `ImplementerReport(SchemaVersionedModel)`, `FileChange`, `TestSummary`, `ContractComplianceItem`, `Status`, `TestResult`, `ComplianceStatus`
- [ ] ImplementerReport has 2 model validators: `test_counts_consistent`, `files_changed_non_empty_for_done`
- [ ] `checkpoint_result.py` defines `CheckpointResult(SchemaVersionedModel)`, `CheckResult`, `Progress`, `Phase`, `CheckStatus`
- [ ] CheckpointResult has 3 model validators: `fail_requires_blockers`, `blockers_reference_check_names`, `task_number_required_for_pre_dispatch`
- [ ] ~27 model unit tests pass
- [ ] 6 test fixtures exist: 2 valid, 4 invalid
- [ ] `schema_version` mismatch rejected by both models

---

## Tasks

### Task 0: Contract Verification (BLOCKING)

**Files:**
- Read: `skills/scripts/models/_base.py`, `skills/scripts/models/plan.py`, `docs/specs/2026-04-25-pydantic-phase-2-design-distilled.md`
- Create: `tests/fixtures/reports/contracts/schema_facts.json`
- Create: `tests/unit/test_models/test_phase2_contracts.py`

**Pattern References:**
- `skills/scripts/models/plan.py` — follow the same pattern for Literal types, nested StrictModels, model_validators

- [ ] **Step 1: Read source contracts**

  Read the distilled spec's Contract Facts section. Extract:
  - ImplementerReport fields: `schema_version: int`, `task_id: int`, `status: Literal[4 values]`, `files_changed: list[FileChange]`, `tests: TestSummary`, `contract_compliance: list[ContractComplianceItem] = []`
  - CheckpointResult fields: `schema_version: int`, `phase: Literal[3 values]`, `status: Literal["PASS", "FAIL"]`, `task_number: int | None`, `checks: dict[str, CheckResult]`, `warnings: list[str]`, `blockers: list[str]`, `progress: Progress | None`
  - Validator rules (2 for ImplementerReport, 3 for CheckpointResult)

  Read `_base.py` to confirm `CURRENT_SCHEMA_VERSION = 1`, `StrictModel`, `SchemaVersionedModel` exist and are importable.

  Read `plan.py` to study the established pattern: how Literal types are defined, how nested StrictModels are structured, how `@model_validator(mode="after")` is used.

- [ ] **Step 2: Create ground-truth fixtures**

  Create `tests/fixtures/reports/contracts/schema_facts.json`:

  ```json
  {
    "implementer_report": {
      "status_values": ["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"],
      "test_result_values": ["PASS", "FAIL"],
      "compliance_status_values": ["compliant", "non_compliant", "partial", "not_applicable"],
      "required_fields": ["schema_version", "task_id", "status", "files_changed", "tests"],
      "optional_fields": ["contract_compliance"],
      "validator_count": 2,
      "validator_names": ["test_counts_consistent", "files_changed_non_empty_for_done"]
    },
    "checkpoint_result": {
      "phase_values": ["pre-execution", "pre-dispatch", "pre-completion"],
      "check_status_values": ["PASS", "FAIL", "SKIP", "OK", "WARNING"],
      "top_status_values": ["PASS", "FAIL"],
      "required_fields": ["schema_version", "phase", "status", "checks", "warnings", "blockers"],
      "optional_fields": ["task_number", "progress"],
      "validator_count": 3,
      "validator_names": ["fail_requires_blockers", "blockers_reference_check_names", "task_number_required_for_pre_dispatch"]
    },
    "current_schema_version": 1
  }
  ```

- [ ] **Step 3: Write contract verification test**

  Create `tests/unit/test_models/test_phase2_contracts.py`:

  ```python
  """Contract verification for Phase 2 models.

  Anchors implementation to ground-truth spec facts.
  Must pass before any model code is written.
  """
  import json
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "skills" / "scripts" / "models"))

  FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "reports" / "contracts"


  def test_schema_facts_file_exists():
      assert (FIXTURES_DIR / "schema_facts.json").is_file()


  def test_schema_facts_has_required_structure():
      with open(FIXTURES_DIR / "schema_facts.json") as f:
          facts = json.load(f)
      assert "implementer_report" in facts
      assert "checkpoint_result" in facts
      assert "current_schema_version" in facts


  def test_base_classes_importable():
      from _base import CURRENT_SCHEMA_VERSION, StrictModel, SchemaVersionedModel
      assert CURRENT_SCHEMA_VERSION == 1
      assert hasattr(StrictModel, "model_config")
      assert hasattr(SchemaVersionedModel, "model_fields")


  def test_schema_version_matches_base():
      from _base import CURRENT_SCHEMA_VERSION
      with open(FIXTURES_DIR / "schema_facts.json") as f:
          facts = json.load(f)
      assert facts["current_schema_version"] == CURRENT_SCHEMA_VERSION


  def test_implementer_report_status_values_complete():
      with open(FIXTURES_DIR / "schema_facts.json") as f:
          facts = json.load(f)
      expected = {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"}
      assert set(facts["implementer_report"]["status_values"]) == expected


  def test_checkpoint_result_check_status_values_complete():
      with open(FIXTURES_DIR / "schema_facts.json") as f:
          facts = json.load(f)
      expected = {"PASS", "FAIL", "SKIP", "OK", "WARNING"}
      assert set(facts["checkpoint_result"]["check_status_values"]) == expected
  ```

- [ ] **Step 4: Run and verify**

  Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_phase2_contracts.py -v`
  Expected: PASS — all contract assertions hold.

- [ ] **Step 5: Commit**

  ```bash
  git add tests/fixtures/reports/contracts/schema_facts.json tests/unit/test_models/test_phase2_contracts.py
  git commit -m "test: add Phase 2 contract verification fixtures"
  ```

---

### Task 1: ImplementerReport Model

**Files:**
- Create: `skills/scripts/models/implementer_report.py`
- Read: `skills/scripts/models/_base.py`, `skills/scripts/models/plan.py`

**Pattern References:**
- `skills/scripts/models/plan.py` — follow the same structure: Literal type aliases at module level, nested StrictModel classes, SchemaVersionedModel for top-level, `@model_validator(mode="after")` for cross-field checks

- [ ] **Step 1: Create implementer_report.py**

  Create `skills/scripts/models/implementer_report.py`:

  ```python
  """Pydantic model for ImplementerReport artifacts (YAML frontmatter)."""
  from typing import Literal

  from pydantic import Field, model_validator

  from _base import StrictModel, SchemaVersionedModel

  Status = Literal["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"]
  TestResult = Literal["PASS", "FAIL"]
  ComplianceStatus = Literal["compliant", "non_compliant", "partial", "not_applicable"]


  class FileChange(StrictModel):
      path: str
      description: str


  class TestSummary(StrictModel):
      written: int
      passing: int
      command: str
      result: TestResult


  class ContractComplianceItem(StrictModel):
      constraint: str
      status: ComplianceStatus
      detail: str


  class ImplementerReport(SchemaVersionedModel):
      task_id: int
      status: Status
      files_changed: list[FileChange]
      tests: TestSummary
      contract_compliance: list[ContractComplianceItem] = Field(default_factory=list)

      @model_validator(mode="after")
      def test_counts_consistent(self) -> "ImplementerReport":
          if self.tests.passing > self.tests.written:
              raise ValueError(
                  f"tests.passing ({self.tests.passing}) cannot exceed "
                  f"tests.written ({self.tests.written})"
              )
          return self

      @model_validator(mode="after")
      def files_changed_non_empty_for_done(self) -> "ImplementerReport":
          if self.status in ("DONE", "DONE_WITH_CONCERNS") and not self.files_changed:
              raise ValueError(
                  f"status is {self.status} but files_changed is empty — "
                  f"completed tasks must list at least one file"
              )
          return self
  ```

- [ ] **Step 2: Verify import works**

  Run: `.venv/bin/python3 -c "import sys; sys.path.insert(0, 'skills/scripts/models'); from implementer_report import ImplementerReport; print('OK')"`
  Expected: `OK`

- [ ] **Step 3: Commit**

  ```bash
  git add skills/scripts/models/implementer_report.py
  git commit -m "feat(pydantic): add ImplementerReport model with 2 validators"
  ```

---

### Task 2: ImplementerReport Unit Tests

**Files:**
- Create: `tests/unit/test_models/test_implementer_report_model.py`
- Read: `skills/scripts/models/implementer_report.py`, `tests/unit/test_models/test_plan_model.py`

**Pattern References:**
- `tests/unit/test_models/test_plan_model.py` — follow test structure: golden inputs, per-field missing/wrong-type, validator edge cases

- [ ] **Step 1: Write unit tests**

  Create `tests/unit/test_models/test_implementer_report_model.py`:

  ```python
  """Unit tests for ImplementerReport Pydantic model."""
  import sys
  from pathlib import Path

  import pytest
  from pydantic import ValidationError

  sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "skills" / "scripts" / "models"))

  from implementer_report import (
      ImplementerReport, FileChange, TestSummary, ContractComplianceItem,
      Status, TestResult, ComplianceStatus,
  )
  from _base import CURRENT_SCHEMA_VERSION


  def _minimal_data(**overrides):
      """Golden-path minimal data dict."""
      data = {
          "schema_version": CURRENT_SCHEMA_VERSION,
          "task_id": 1,
          "status": "DONE",
          "files_changed": [{"path": "src/foo.py", "description": "added feature"}],
          "tests": {"written": 2, "passing": 2, "command": "pytest -v", "result": "PASS"},
      }
      data.update(overrides)
      return data


  class TestGoldenPath:
      def test_minimal_valid(self):
          report = ImplementerReport(**_minimal_data())
          assert report.task_id == 1
          assert report.status == "DONE"
          assert report.contract_compliance == []

      def test_full_featured(self):
          data = _minimal_data(
              status="DONE_WITH_CONCERNS",
              contract_compliance=[{
                  "constraint": "Must use async",
                  "status": "compliant",
                  "detail": "All endpoints async",
              }],
          )
          report = ImplementerReport(**data)
          assert len(report.contract_compliance) == 1
          assert report.contract_compliance[0].status == "compliant"


  class TestStatusEnum:
      @pytest.mark.parametrize("status", ["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"])
      def test_valid_statuses(self, status):
          report = ImplementerReport(**_minimal_data(
              status=status,
              files_changed=[] if status in ("BLOCKED", "NEEDS_CONTEXT") else [{"path": "x.py", "description": "y"}],
          ))
          assert report.status == status

      def test_invalid_status_rejected(self):
          with pytest.raises(ValidationError, match="status"):
              ImplementerReport(**_minimal_data(status="INVALID"))


  class TestTestResultEnum:
      @pytest.mark.parametrize("result", ["PASS", "FAIL"])
      def test_valid_results(self, result):
          report = ImplementerReport(**_minimal_data(
              tests={"written": 1, "passing": 1 if result == "PASS" else 0, "command": "pytest", "result": result},
          ))
          assert report.tests.result == result

      def test_invalid_result_rejected(self):
          with pytest.raises(ValidationError, match="result"):
              ImplementerReport(**_minimal_data(
                  tests={"written": 1, "passing": 1, "command": "pytest", "result": "SKIP"},
              ))


  class TestComplianceStatusEnum:
      @pytest.mark.parametrize("cs", ["compliant", "non_compliant", "partial", "not_applicable"])
      def test_valid_compliance_statuses(self, cs):
          data = _minimal_data(contract_compliance=[{
              "constraint": "test", "status": cs, "detail": "detail",
          }])
          report = ImplementerReport(**data)
          assert report.contract_compliance[0].status == cs

      def test_invalid_compliance_status_rejected(self):
          with pytest.raises(ValidationError, match="status"):
              ImplementerReport(**_minimal_data(contract_compliance=[{
                  "constraint": "test", "status": "invalid", "detail": "detail",
              }]))


  class TestRequiredFields:
      @pytest.mark.parametrize("field", ["schema_version", "task_id", "status", "files_changed", "tests"])
      def test_missing_required_field(self, field):
          data = _minimal_data()
          del data[field]
          with pytest.raises(ValidationError):
              ImplementerReport(**data)


  class TestExtraFieldsForbidden:
      def test_extra_field_rejected(self):
          with pytest.raises(ValidationError, match="extra"):
              ImplementerReport(**_minimal_data(surprise_field="oops"))


  class TestSchemaVersion:
      def test_wrong_version_rejected(self):
          with pytest.raises(ValidationError, match="schema_version"):
              ImplementerReport(**_minimal_data(schema_version=99))


  class TestTestCountsConsistentValidator:
      def test_passing_exceeds_written_fails(self):
          with pytest.raises(ValidationError, match="cannot exceed"):
              ImplementerReport(**_minimal_data(
                  tests={"written": 2, "passing": 5, "command": "pytest", "result": "PASS"},
              ))

      def test_passing_equals_written_passes(self):
          report = ImplementerReport(**_minimal_data(
              tests={"written": 3, "passing": 3, "command": "pytest", "result": "PASS"},
          ))
          assert report.tests.passing == 3

      def test_zero_tests_passes(self):
          report = ImplementerReport(**_minimal_data(
              status="BLOCKED",
              files_changed=[],
              tests={"written": 0, "passing": 0, "command": "pytest", "result": "FAIL"},
          ))
          assert report.tests.written == 0


  class TestFilesChangedNonEmptyForDoneValidator:
      def test_done_with_empty_files_fails(self):
          with pytest.raises(ValidationError, match="files_changed is empty"):
              ImplementerReport(**_minimal_data(files_changed=[]))

      def test_done_with_concerns_with_empty_files_fails(self):
          with pytest.raises(ValidationError, match="files_changed is empty"):
              ImplementerReport(**_minimal_data(status="DONE_WITH_CONCERNS", files_changed=[]))

      def test_blocked_with_empty_files_passes(self):
          report = ImplementerReport(**_minimal_data(status="BLOCKED", files_changed=[]))
          assert report.files_changed == []

      def test_needs_context_with_empty_files_passes(self):
          report = ImplementerReport(**_minimal_data(status="NEEDS_CONTEXT", files_changed=[]))
          assert report.files_changed == []
  ```

- [ ] **Step 2: Run tests**

  Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_implementer_report_model.py -v`
  Expected: All ~15 tests PASS

- [ ] **Step 3: Commit**

  ```bash
  git add tests/unit/test_models/test_implementer_report_model.py
  git commit -m "test: add ImplementerReport model unit tests"
  ```

---

### Task 3: CheckpointResult Model

**Files:**
- Create: `skills/scripts/models/checkpoint_result.py`
- Read: `skills/scripts/models/_base.py`, `skills/scripts/models/plan.py`

**Pattern References:**
- `skills/scripts/models/plan.py` — same pattern as Task 1

- [ ] **Step 1: Create checkpoint_result.py**

  Create `skills/scripts/models/checkpoint_result.py`:

  ```python
  """Pydantic model for CheckpointResult artifacts (pure JSON)."""
  from typing import Literal

  from pydantic import model_validator

  from _base import StrictModel, SchemaVersionedModel

  Phase = Literal["pre-execution", "pre-dispatch", "pre-completion"]
  CheckStatus = Literal["PASS", "FAIL", "SKIP", "OK", "WARNING"]


  class CheckResult(StrictModel):
      status: CheckStatus
      detail: str


  class Progress(StrictModel):
      tasks_total: int
      tasks_completed: int | None = None
      checkboxes_total: int
      checkboxes_checked: int
      checkboxes_unchecked: int | None = None
      percentage: int | None = None


  class CheckpointResult(SchemaVersionedModel):
      phase: Phase
      status: Literal["PASS", "FAIL"]
      task_number: int | None = None
      checks: dict[str, CheckResult]
      warnings: list[str]
      blockers: list[str]
      progress: Progress | None = None

      @model_validator(mode="after")
      def fail_requires_blockers(self) -> "CheckpointResult":
          if self.status == "FAIL" and not self.blockers:
              raise ValueError(
                  "status is FAIL but blockers is empty — "
                  "a FAIL without named blockers is untraceable"
              )
          return self

      @model_validator(mode="after")
      def blockers_reference_check_names(self) -> "CheckpointResult":
          for blocker in self.blockers:
              if blocker not in self.checks:
                  raise ValueError(
                      f"blocker '{blocker}' is not a key in checks — "
                      f"available check names: {list(self.checks.keys())}"
                  )
          return self

      @model_validator(mode="after")
      def task_number_required_for_pre_dispatch(self) -> "CheckpointResult":
          if self.phase == "pre-dispatch" and self.task_number is None:
              raise ValueError(
                  "task_number is required when phase is 'pre-dispatch'"
              )
          return self
  ```

- [ ] **Step 2: Verify import works**

  Run: `.venv/bin/python3 -c "import sys; sys.path.insert(0, 'skills/scripts/models'); from checkpoint_result import CheckpointResult; print('OK')"`
  Expected: `OK`

- [ ] **Step 3: Commit**

  ```bash
  git add skills/scripts/models/checkpoint_result.py
  git commit -m "feat(pydantic): add CheckpointResult model with 3 validators"
  ```

---

### Task 4: CheckpointResult Unit Tests

**Files:**
- Create: `tests/unit/test_models/test_checkpoint_result_model.py`
- Read: `skills/scripts/models/checkpoint_result.py`, `tests/unit/test_models/test_plan_model.py`

**Pattern References:**
- `tests/unit/test_models/test_plan_model.py` — follow test structure

- [ ] **Step 1: Write unit tests**

  Create `tests/unit/test_models/test_checkpoint_result_model.py`:

  ```python
  """Unit tests for CheckpointResult Pydantic model."""
  import sys
  from pathlib import Path

  import pytest
  from pydantic import ValidationError

  sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "skills" / "scripts" / "models"))

  from checkpoint_result import (
      CheckpointResult, CheckResult, Progress,
      Phase, CheckStatus,
  )
  from _base import CURRENT_SCHEMA_VERSION


  def _minimal_data(**overrides):
      """Golden-path minimal data dict for a passing pre-execution checkpoint."""
      data = {
          "schema_version": CURRENT_SCHEMA_VERSION,
          "phase": "pre-execution",
          "status": "PASS",
          "checks": {
              "plan_exists": {"status": "PASS", "detail": "Plan file found"},
          },
          "warnings": [],
          "blockers": [],
      }
      data.update(overrides)
      return data


  def _pre_dispatch_data(**overrides):
      """Pre-dispatch checkpoint with required task_number."""
      data = _minimal_data(phase="pre-dispatch", task_number=3)
      data.update(overrides)
      return data


  class TestGoldenPath:
      def test_pre_execution_pass(self):
          result = CheckpointResult(**_minimal_data())
          assert result.phase == "pre-execution"
          assert result.status == "PASS"
          assert result.task_number is None
          assert result.progress is None

      def test_pre_dispatch_pass(self):
          result = CheckpointResult(**_pre_dispatch_data())
          assert result.task_number == 3

      def test_pre_completion_pass(self):
          result = CheckpointResult(**_minimal_data(phase="pre-completion"))
          assert result.phase == "pre-completion"

      def test_with_progress(self):
          result = CheckpointResult(**_pre_dispatch_data(
              progress={"tasks_total": 10, "checkboxes_total": 50, "checkboxes_checked": 25, "tasks_completed": 3, "percentage": 50},
          ))
          assert result.progress.tasks_total == 10
          assert result.progress.percentage == 50


  class TestPhaseEnum:
      @pytest.mark.parametrize("phase", ["pre-execution", "pre-dispatch", "pre-completion"])
      def test_valid_phases(self, phase):
          data = _minimal_data(phase=phase)
          if phase == "pre-dispatch":
              data["task_number"] = 1
          result = CheckpointResult(**data)
          assert result.phase == phase

      def test_invalid_phase_rejected(self):
          with pytest.raises(ValidationError, match="phase"):
              CheckpointResult(**_minimal_data(phase="post-mortem"))


  class TestCheckStatusEnum:
      @pytest.mark.parametrize("cs", ["PASS", "FAIL", "SKIP", "OK", "WARNING"])
      def test_valid_check_statuses(self, cs):
          result = CheckpointResult(**_minimal_data(
              checks={"test_check": {"status": cs, "detail": "test"}},
          ))
          assert result.checks["test_check"].status == cs

      def test_invalid_check_status_rejected(self):
          with pytest.raises(ValidationError, match="status"):
              CheckpointResult(**_minimal_data(
                  checks={"test_check": {"status": "WARN", "detail": "test"}},
              ))


  class TestFailRequiresBlockers:
      def test_fail_without_blockers_rejected(self):
          with pytest.raises(ValidationError, match="blockers is empty"):
              CheckpointResult(**_minimal_data(
                  status="FAIL",
                  checks={"bad_check": {"status": "FAIL", "detail": "broken"}},
              ))

      def test_fail_with_blockers_passes(self):
          result = CheckpointResult(**_minimal_data(
              status="FAIL",
              checks={"bad_check": {"status": "FAIL", "detail": "broken"}},
              blockers=["bad_check"],
          ))
          assert result.status == "FAIL"


  class TestBlockersReferenceCheckNames:
      def test_blocker_not_in_checks_rejected(self):
          with pytest.raises(ValidationError, match="not a key in checks"):
              CheckpointResult(**_minimal_data(
                  status="FAIL",
                  checks={"real_check": {"status": "FAIL", "detail": "broken"}},
                  blockers=["typo_check"],
              ))

      def test_blocker_matching_check_passes(self):
          result = CheckpointResult(**_minimal_data(
              status="FAIL",
              checks={"real_check": {"status": "FAIL", "detail": "broken"}},
              blockers=["real_check"],
          ))
          assert result.blockers == ["real_check"]


  class TestTaskNumberRequiredForPreDispatch:
      def test_pre_dispatch_without_task_number_rejected(self):
          with pytest.raises(ValidationError, match="task_number is required"):
              CheckpointResult(**_minimal_data(phase="pre-dispatch"))

      def test_pre_execution_without_task_number_passes(self):
          result = CheckpointResult(**_minimal_data(phase="pre-execution"))
          assert result.task_number is None

      def test_pre_completion_without_task_number_passes(self):
          result = CheckpointResult(**_minimal_data(phase="pre-completion"))
          assert result.task_number is None


  class TestSchemaVersion:
      def test_wrong_version_rejected(self):
          with pytest.raises(ValidationError, match="schema_version"):
              CheckpointResult(**_minimal_data(schema_version=99))


  class TestExtraFieldsForbidden:
      def test_extra_field_rejected(self):
          with pytest.raises(ValidationError, match="extra"):
              CheckpointResult(**_minimal_data(surprise="oops"))


  class TestModelDump:
      def test_exclude_none_omits_absent_optionals(self):
          result = CheckpointResult(**_minimal_data())
          dumped = result.model_dump(exclude_none=True)
          assert "task_number" not in dumped
          assert "progress" not in dumped
          assert "schema_version" in dumped
  ```

- [ ] **Step 2: Run tests**

  Run: `.venv/bin/python3 -m pytest tests/unit/test_models/test_checkpoint_result_model.py -v`
  Expected: All ~12 tests PASS

- [ ] **Step 3: Commit**

  ```bash
  git add tests/unit/test_models/test_checkpoint_result_model.py
  git commit -m "test: add CheckpointResult model unit tests"
  ```

---

### Task 5: Test Fixtures

**Files:**
- Create: `tests/fixtures/reports/valid/minimal-report.md`
- Create: `tests/fixtures/reports/valid/full-featured-report.md`
- Create: `tests/fixtures/reports/invalid/missing-status.md`
- Create: `tests/fixtures/reports/invalid/bad-status-enum.md`
- Create: `tests/fixtures/reports/invalid/test-counts-inconsistent.md`
- Create: `tests/fixtures/reports/invalid/no-files-for-done.md`

- [ ] **Step 1: Create valid minimal fixture**

  Create `tests/fixtures/reports/valid/minimal-report.md`:

  ```markdown
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
  ```

- [ ] **Step 2: Create valid full-featured fixture**

  Create `tests/fixtures/reports/valid/full-featured-report.md`:

  ```markdown
  ---
  schema_version: 1
  task_id: 5
  status: DONE_WITH_CONCERNS
  files_changed:
    - path: "src/api/endpoints.py"
      description: "Added user profile endpoint"
    - path: "src/models/user.py"
      description: "Added UserProfile response model"
    - path: "tests/unit/test_user.py"
      description: "Added 4 unit tests for profile endpoint"
  tests:
    written: 4
    passing: 4
    command: ".venv/bin/python3 -m pytest tests/unit/test_user.py -v"
    result: PASS
  contract_compliance:
    - constraint: "Response must include avatar_url"
      status: compliant
      detail: "Field added to UserProfile model"
    - constraint: "Must use async database queries"
      status: partial
      detail: "Endpoint is async but uses sync ORM call for avatar lookup"
  ---

  **Implementation Summary:**
  Added user profile endpoint with GET /api/users/{id}/profile. Includes avatar URL and bio fields. Used async handler but one ORM call is sync (see concerns).

  **Source Files Read:**
  - `src/api/endpoints.py` — existing endpoint patterns
  - `docs/imp-plans/plan.md` — task 5 requirements

  **Deviations from Plan:**
  - Used sync ORM call for avatar lookup instead of async as specified

  **Self-Review Findings:**
  - Found that the sync ORM call blocks the event loop briefly; acceptable for now but should be converted to async in a follow-up

  **Concerns:**
  - The sync ORM call for avatar lookup may cause latency under load
  ```

- [ ] **Step 3: Create invalid fixtures**

  Create `tests/fixtures/reports/invalid/missing-status.md`:

  ```markdown
  ---
  schema_version: 1
  task_id: 1
  files_changed:
    - path: "src/foo.py"
      description: "change"
  tests:
    written: 1
    passing: 1
    command: "pytest"
    result: PASS
  ---

  **Implementation Summary:**
  Did the thing.
  ```

  Create `tests/fixtures/reports/invalid/bad-status-enum.md`:

  ```markdown
  ---
  schema_version: 1
  task_id: 1
  status: COMPLETED
  files_changed:
    - path: "src/foo.py"
      description: "change"
  tests:
    written: 1
    passing: 1
    command: "pytest"
    result: PASS
  ---

  **Implementation Summary:**
  Did the thing.
  ```

  Create `tests/fixtures/reports/invalid/test-counts-inconsistent.md`:

  ```markdown
  ---
  schema_version: 1
  task_id: 1
  status: DONE
  files_changed:
    - path: "src/foo.py"
      description: "change"
  tests:
    written: 2
    passing: 5
    command: "pytest"
    result: PASS
  ---

  **Implementation Summary:**
  Did the thing.
  ```

  Create `tests/fixtures/reports/invalid/no-files-for-done.md`:

  ```markdown
  ---
  schema_version: 1
  task_id: 1
  status: DONE
  files_changed: []
  tests:
    written: 1
    passing: 1
    command: "pytest"
    result: PASS
  ---

  **Implementation Summary:**
  Did the thing.
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add tests/fixtures/reports/
  git commit -m "test: add report validation fixtures (2 valid, 4 invalid)"
  ```
