# Pydantic Phase 2 — Distilled Implementation Spec

> **Source**: `docs/specs/2026-04-25-pydantic-phase-2-design.md` (v1.0, 8 decisions)
> **Distilled**: 2026-04-25
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

---

## Contract Facts

### Format
- **ImplementerReport**: YAML frontmatter (`---` delimiters) for typed fields + markdown body for prose sections. Same pattern as Phase 1 Plan.
- **CheckpointResult**: Pure JSON, unchanged from current output shape. Gains `schema_version` field.
- Detection: file starts with `---` → Pydantic path; otherwise → hard FAIL ("predates Phase 2 cutover")

### Base Classes (from Phase 1, unchanged)
- `StrictModel(BaseModel)` — nested types, `extra="forbid"`
- `SchemaVersionedModel(StrictModel)` — top-level artifacts, adds `schema_version: int` pinned to `CURRENT_SCHEMA_VERSION`
- All models share `CURRENT_SCHEMA_VERSION = 1` from `_base.py` (per-module split deferred until first version divergence)

### ImplementerReport Schema Fields (`implementer_report.py`)

Top-level `ImplementerReport(SchemaVersionedModel)`:
- `schema_version: int` (required, must equal `CURRENT_SCHEMA_VERSION`)
- `task_id: int`
- `status: Literal["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"]`
- `files_changed: list[FileChange]`
- `tests: TestSummary`
- `contract_compliance: list[ContractComplianceItem] = []`

Nested types (all inherit `StrictModel`):
- `FileChange`: `path: str`, `description: str`
- `TestSummary`: `written: int`, `passing: int`, `command: str`, `result: Literal["PASS", "FAIL"]`
- `ContractComplianceItem`: `constraint: str`, `status: Literal["compliant", "non_compliant", "partial", "not_applicable"]`, `detail: str`

ImplementerReport model validators (2 total, both `mode="after"`):
1. `test_counts_consistent` — `tests.passing <= tests.written`
2. `files_changed_non_empty_for_done` — if status is DONE or DONE_WITH_CONCERNS, `files_changed` must be non-empty

CLI-level check (NOT a model validator):
- `done_with_concerns_check` — if status is DONE but markdown body has non-empty Deviations or Concerns, emit warning. Lives in CLI wrapper per pure-model principle (meta-design Section 5.3).

### CheckpointResult Schema Fields (`checkpoint_result.py`)

Top-level `CheckpointResult(SchemaVersionedModel)`:
- `schema_version: int` (required, must equal `CURRENT_SCHEMA_VERSION`)
- `phase: Literal["pre-execution", "pre-dispatch", "pre-completion"]`
- `status: Literal["PASS", "FAIL"]`
- `task_number: int | None = None`
- `checks: dict[str, CheckResult]`
- `warnings: list[str]`
- `blockers: list[str]`
- `progress: Progress | None = None`

Nested types (all inherit `StrictModel`):
- `CheckResult`: `status: Literal["PASS", "FAIL", "SKIP", "OK", "WARNING"]`, `detail: str`
- `Progress`: `tasks_total: int`, `tasks_completed: int | None = None`, `checkboxes_total: int`, `checkboxes_checked: int`, `checkboxes_unchecked: int | None = None`, `percentage: int | None = None`

CheckpointResult model validators (3 total, all `mode="after"`):
1. `fail_requires_blockers` — if status is FAIL, blockers must be non-empty
2. `blockers_reference_check_names` — every blocker must be a key in checks
3. `task_number_required_for_pre_dispatch` — task_number required when phase is pre-dispatch

Progress field population varies by phase:

| Field | pre-execution | pre-dispatch | pre-completion |
|-------|:---:|:---:|:---:|
| `tasks_total` | yes | yes | yes |
| `tasks_completed` | no | yes | yes |
| `checkboxes_total` | yes | yes | yes |
| `checkboxes_checked` | yes | yes | yes |
| `checkboxes_unchecked` | yes | no | no |
| `percentage` | no | yes | yes |

### Exit Codes
- `validators.py`: `0` = pass, `1` = validation fail, `2` = infrastructure error
- `controller-checkpoint.py`: retains its own convention (`0` = PASS, `1` = FAIL, `2` = WARNING, `3` = script error). Pydantic `ValidationError` during construction caught by existing `except Exception` handler → exit 3.

### CLI Invocation
```bash
.venv/bin/python3 validators.py report <path/to/report.md>
```
No CLI subcommand for CheckpointResult — validates at construction time inside `controller-checkpoint.py`.

### Environment Variables
- `SUPERPOWERS_VALIDATOR_BYPASS=1` — emergency skip; exits 0 with stderr warning

---

## Open Decisions

(None — all 8 decisions resolved during brainstorm.)

---

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | ImplementerReport format | YAML frontmatter + markdown body |
| 2 | CheckpointResult format | Pure JSON (meta-design locked) |
| 3 | Frontmatter scope | Structured fields in YAML; prose in body |
| 4 | `_report_utils.py` fate | Model owns constants, utils re-exports. Phase 7 cleanup. |
| 5 | Renderer | None — humans read file as-is |
| 6 | Cross-artifact validation | Deferred to Phase 3 (documented as candidate) |
| 7 | Migration | Hard cutover (meta-design locked) |
| 8 | `schema_version` in checkpoint output | Include (additive, non-breaking) |

---

## Component Specifications

### `skills/scripts/models/implementer_report.py`
Defines `ImplementerReport`, `FileChange`, `TestSummary`, `ContractComplianceItem`, `Status`, `TestResult`, `ComplianceStatus`. Two model validators: `test_counts_consistent`, `files_changed_non_empty_for_done`. See Contract Facts for field layouts.

### `skills/scripts/models/checkpoint_result.py`
Defines `CheckpointResult`, `CheckResult`, `Progress`, `Phase`, `CheckStatus`. Three model validators: `fail_requires_blockers`, `blockers_reference_check_names`, `task_number_required_for_pre_dispatch`. See Contract Facts for field layouts.

### `skills/scripts/models/validators.py` — New `report` Subcommand
Same pattern as `validate_plan()`:
1. Check file exists (exit 2)
2. Check bypass env var (exit 0 with warning)
3. Read file, extract YAML frontmatter (hard FAIL exit 1 if absent)
4. `yaml.safe_load()` → `ImplementerReport.model_validate(data)`
5. On YAML error: `format_yaml_error()` to stderr, exit 1
6. On validation error: `format_validation_error()` to stderr, exit 1
7. Success: exit 0

### `validate-report.py` — Pydantic Pre-Check
Calls `validate_report()` from `validators.py` for Pydantic frontmatter validation, then runs prose section-presence check via `_report_utils.validate_report_sections()`. Reports without frontmatter hard FAIL and never reach the prose check. `sdd-pre-dispatch-hook.sh` calls `validate-report.py` — no hook changes needed.

### `controller-checkpoint.py` — CheckpointResult Construction
`_build_result()` changes from returning a raw dict to constructing via `CheckpointResult(schema_version=CURRENT_SCHEMA_VERSION, ...)` and calling `.model_dump()`. Requires `sys.path.insert(0, ...)` for models directory import. JSON output gains `schema_version` field.

### `_report_utils.py` — Re-Export Wrapper
- `VALID_STATUSES` re-exported from `Status` Literal type: `set(Status.__args__)`
- `STATUS_VALUE_PATTERN` and `extract_implementer_status()` deprecated (status from frontmatter)
- `REQUIRED_SECTIONS` reduced from 9 to 5: removes Status, Files Changed, Tests, Contract Compliance (now in frontmatter)
- Remaining prose sections: Implementation Summary, Source Files Read, Deviations from Plan, Self-Review Findings, Concerns
- "CLAUDE.md Files Read" is prose-only but NOT in `REQUIRED_SECTIONS` — present in prompt template, not mechanically validated
- Docstring updated to note Phase 7 cleanup target
- Pre-existing `validate_report_sections()` duplication in `controller-checkpoint.py` NOT fixed (Phase 7 candidate)

### `implementer-prompt.md` — Frontmatter Instructions
Report format template gains YAML frontmatter block prepended to existing prose sections:
```yaml
---
schema_version: 1
task_id: [task number]
status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
files_changed:
  - path: "path/to/file.py"
    description: "what changed and why"
tests:
  written: [count]
  passing: [count]
  command: "[exact command run]"
  result: PASS | FAIL
contract_compliance:
  - constraint: "[constraint text]"
    status: compliant | non_compliant | partial | not_applicable
    detail: "[how you complied]"
---
```
Ships atomically with validators (meta-design Section 10.4).

### Documentation Updates (Ship With Implementation)

**`CLAUDE.md` (fork root):**
- Add `implementer_report.py` and `checkpoint_result.py` to models list
- Document `validators.py report <path>` subcommand
- Note `validate-report.py` Pydantic pre-check

**Meta-design (`docs/plans/2026-04-24-pydantic-meta-design.md`):**
- Section 2: Phase 2 → "Complete"; Phase 3 scope adds cross-artifact validation (user-requested)
- Section 5.1: confirm file tree
- Section 11: Phase 2 post-mortem (after implementation)
- Section 12.1: Resolved — no renderer
- Section 12.2: Resolved — YAML frontmatter
- Section 12.3: Updated — Phase 3 candidate for PlanExecutionContract

**`skills/scripts/models/__init__.py`:** Docstring updated.

---

## Directory Structure (New Additions)

```
skills/scripts/models/                    # EXISTING
├── implementer_report.py                 # NEW
└── checkpoint_result.py                  # NEW

tests/fixtures/reports/                   # NEW
├── valid/
│   ├── minimal-report.md
│   └── full-featured-report.md
└── invalid/
    ├── missing-status.md
    ├── bad-status-enum.md
    ├── test-counts-inconsistent.md
    └── no-files-for-done.md

tests/unit/test_models/                   # EXISTING
├── test_implementer_report_model.py      # NEW
└── test_checkpoint_result_model.py       # NEW

tests/unit/test_validators/               # EXISTING
└── test_validate_report_pydantic.py      # NEW

tests/fixtures/_smoke-test-reports/       # NEW — throwaway, deleted post-ship
```

---

## Testing Strategy

### Test Layers

| Layer | Scope | Location | New Tests |
|-------|-------|----------|-----------|
| Model unit tests | ImplementerReport fields + validators | `test_implementer_report_model.py` | ~15 |
| Model unit tests | CheckpointResult fields + validators | `test_checkpoint_result_model.py` | ~12 |
| CLI entry-point tests | `validators.py report` subprocess | `test_validate_report_pydantic.py` | ~10 |
| Pre-ship smoke test | Real reports vs schema | `_smoke-test-reports/` | dynamic |
| Regression check | `validate-all-skills.py` after prompt edit | existing | 0 new |

### Post-Phase 2 Test Counts

| Layer | Before | After | Delta |
|-------|--------|-------|-------|
| Unit tests (pytest) | 163 | ~200 | +37 |
| Regression checks | 122 | 122 | 0 |
| Install checks | 105 | 105 | 0 |

---

## Migration

- **Hard cutover**: models, validators, prompt template, controller changes ship atomically
- **Old reports**: hard FAIL if re-validated (expected — add frontmatter to validate)
- **No batch conversion** of historical reports

### Rollback Ladder
1. Fix the schema, push, reinstall
2. `export SUPERPOWERS_VALIDATOR_BYPASS=1`
3. `git revert <phase-2-commits>`

---

## Acceptance Criteria

- [ ] `implementer_report.py` exists with `ImplementerReport(SchemaVersionedModel)`, `FileChange`, `TestSummary`, `ContractComplianceItem`
- [ ] `ImplementerReport` has 2 model validators: `test_counts_consistent`, `files_changed_non_empty_for_done`
- [ ] `done_with_concerns_check` in CLI wrapper (warns, not blocks)
- [ ] `checkpoint_result.py` exists with `CheckpointResult(SchemaVersionedModel)`, `CheckResult`, `Progress`
- [ ] `CheckpointResult` has 3 model validators: `fail_requires_blockers`, `blockers_reference_check_names`, `task_number_required_for_pre_dispatch`
- [ ] `validators.py` has `report` subcommand (exit codes 0/1/2, bypass honored)
- [ ] `validate-report.py` calls `validate_report()` from `validators.py` (shared code)
- [ ] Reports without frontmatter → hard FAIL referencing "Phase 2 cutover"
- [ ] `controller-checkpoint.py` constructs via `CheckpointResult`, output includes `schema_version`
- [ ] `controller-checkpoint.py` has `sys.path.insert` for models import
- [ ] `implementer-prompt.md` has YAML frontmatter block in report format template
- [ ] Prompt template + validators ship atomically
- [ ] `_report_utils.py` re-exports `VALID_STATUSES` from model's `Status` type
- [ ] `_report_utils.py` `REQUIRED_SECTIONS` reduced from 9 to 5
- [ ] `_report_utils.py` docstring notes Phase 7 cleanup
- [ ] `CLAUDE.md` Pydantic section updated
- [ ] Meta-design Sections 2, 5, 11, 12 updated; Phase 3 cross-artifact noted
- [ ] `__init__.py` docstring updated
- [ ] ~37 new unit tests pass
- [ ] Test fixtures: `reports/valid/` (2), `reports/invalid/` (4)
- [ ] Pre-ship smoke test passes; `_smoke-test-reports/` deleted post-ship
- [ ] All existing tests continue to pass
- [ ] `validate-all-skills.py` passes after prompt template change
