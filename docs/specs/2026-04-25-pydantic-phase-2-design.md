# Pydantic Phase 2 — ImplementerReport + CheckpointResult Design

**Date:** 2026-04-25
**Status:** Draft
**Feature archetype:** Extension
**Companion docs:**
- Meta-design: `docs/plans/2026-04-24-pydantic-meta-design.md`
- Phase 1 spec: `docs/specs/2026-04-24-pydantic-phase-1-design.md`
- Adoption plan: `docs/external-references/2026-04-23-pydantic-adoption-plan.md`

---

## 1. Purpose

Add Pydantic validation models for two Tier A artifacts:

- **A1: ImplementerReport** — the highest-volume artifact in SDD, currently validated by regex in `_report_utils.py`. Migrates to YAML frontmatter + markdown body, consistent with Phase 1's Plan model.
- **A2: CheckpointResult** — the JSON output of `controller-checkpoint.py`, already structured. Wraps in Pydantic for typed construction and downstream consumer safety.

Phase 2 extends the Phase 1 infrastructure (`_base.py`, `errors.py`, `validators.py`) without deleting or replacing existing code. `_report_utils.py` transitions to a re-export wrapper sourcing constants from the Pydantic model.

### Out of Scope

- Cross-artifact contract validation (deferred to Phase 3 — see Section 10)
- Renderer methods (`.to_markdown()` or separate `renderers/` module)
- Shadow mode / parallel old+new validators (meta-design Section 10.1 locks hard cutover)
- Instructor / forced tool-use output (meta-design Appendix A rejects this)
- Hypothesis property-based tests (meta-design Section 12.4 defers indefinitely)

---

## 2. Decisions

| # | Decision | Chosen | Alternatives Considered |
|---|----------|--------|------------------------|
| 1 | ImplementerReport format | YAML frontmatter + markdown body (same pattern as Plan) | Markdown-only with `from_markdown()` parser; JSON via tool-use (rejected by meta-design Appendix A) |
| 2 | CheckpointResult format | Pure JSON (locked by meta-design Section 3.2) | N/A — machine-emitted artifacts use JSON |
| 3 | Frontmatter scope | Structured fields in YAML; prose sections stay in markdown body | Minimal frontmatter (status only); everything in frontmatter (LLM YAML compliance risk) |
| 4 | `_report_utils.py` fate | Model owns constants, utils re-exports for backwards compat. Cleanup in Phase 7. | Keep utils as-is; delete utils immediately |
| 5 | Renderer | None — humans read the file as-is | `.to_markdown()` on model; separate `renderers.py` module |
| 6 | Cross-artifact validation | Deferred to Phase 3 (documented as candidate) | Lightweight cross-check in Phase 2 |
| 7 | Migration | Hard cutover (locked by meta-design Section 10.1) | Shadow mode (overridden by meta-design) |
| 8 | `schema_version` in CheckpointResult output | Include in JSON output (additive, non-breaking) | Validate internally but strip from output |

---

## 3. ImplementerReport Model

### 3.1 Format

Reports use YAML frontmatter (between `---` delimiters) for typed/structured fields, with a markdown body below for prose sections. This matches the Phase 1 Plan format and uses the existing `_extract_frontmatter()` function in `validators.py`.

### 3.2 Frontmatter Fields

```yaml
---
schema_version: 1
task_id: 3
status: DONE
files_changed:
  - path: "app/services/user.py"
    description: "Added get_user_by_id endpoint"
  - path: "tests/unit/test_user.py"
    description: "Added 3 unit tests"
tests:
  written: 3
  passing: 3
  command: ".venv/bin/python3 -m pytest tests/unit/test_user.py -v"
  result: PASS
contract_compliance:
  - constraint: "Response must include avatar_url"
    status: compliant
    detail: "Field added to UserResponse model"
---
```

### 3.3 Markdown Body (prose sections)

Below the frontmatter, the markdown body contains prose sections checked for presence by `_report_utils.py`:

- **Implementation Summary** — 2-3 sentences describing what was built
- **Source Files Read** — files read and what was learned
- **CLAUDE.md Files Read** — CLAUDE.md files found in modified directories
- **Deviations from Plan** — decisions that differed from plan instructions
- **Self-Review Findings** — issues found during self-review
- **Concerns** — uncertainties or items the controller should know

### 3.4 Pydantic Model Shape

File: `skills/scripts/models/implementer_report.py`

```python
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
```

### 3.5 Model Validators

Three `@model_validator(mode="after")` rules:

1. **`test_counts_consistent`** — `tests.passing` must be `<= tests.written`. A report claiming more tests passing than written is always a mistake.

2. **`files_changed_non_empty_for_done`** — if `status` is `DONE` or `DONE_WITH_CONCERNS`, `files_changed` must contain at least one entry. A completed task with no files changed is suspicious (setup-only tasks should use a description-only file entry).

3. **`done_with_concerns_requires_flag`** — warning-level: if `status` is `DONE` but the markdown body (passed via validation context) has non-empty Deviations or Concerns sections, the validator notes this mismatch. This is informational, not blocking — the controller uses status as a routing signal, and the section-presence check in `_report_utils.py` provides the prose-level enforcement.

Note: Validator #3 touches the markdown body, which raises a question about the pure-model/IO split (meta-design Section 5.3). The prose content would need to be passed via Pydantic's `model_validate(data, context={"markdown_body": body})` mechanism. If this feels like a violation of the pure-model principle, this validator can be moved to the CLI wrapper instead.

---

## 4. CheckpointResult Model

### 4.1 Format

Pure JSON, unchanged from current output. `controller-checkpoint.py` constructs via `CheckpointResult(...)` and calls `.model_dump()`. The only visible change is the addition of `schema_version` to the output.

### 4.2 Pydantic Model Shape

File: `skills/scripts/models/checkpoint_result.py`

```python
from typing import Literal
from pydantic import model_validator
from _base import StrictModel, SchemaVersionedModel

Phase = Literal["pre-execution", "pre-dispatch", "pre-completion"]
CheckStatus = Literal["PASS", "FAIL", "WARN", "SKIP", "OK", "WARNING"]


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
```

### 4.3 Model Validators

Three `@model_validator(mode="after")` rules:

1. **`fail_requires_blockers`** — if `status` is `FAIL`, `blockers` must be non-empty. A FAIL without named blockers is useless — the consumer can't determine what to fix.

2. **`blockers_reference_check_names`** — every entry in `blockers` must be a key in `checks`. Prevents typos in blocker names that would make the FAIL reason untraceable.

3. **`task_number_required_for_pre_dispatch`** — `task_number` is required when `phase` is `pre-dispatch`. Pre-execution and pre-completion don't require it.

### 4.4 Integration with `controller-checkpoint.py`

The `_build_result()` function changes from returning a raw dict to constructing via `CheckpointResult`:

```python
from skills.scripts.models._base import CURRENT_SCHEMA_VERSION
from skills.scripts.models.checkpoint_result import CheckpointResult, Progress

def _build_result(phase, task_number, overall_status, checks, warnings, blockers, progress):
    progress_model = Progress(**progress) if progress else None
    result = CheckpointResult(
        schema_version=CURRENT_SCHEMA_VERSION,
        phase=phase,
        status=overall_status,
        checks=checks,
        warnings=warnings,
        blockers=blockers,
        task_number=task_number,
        progress=progress_model,
    )
    return result.model_dump()
```

The downstream JSON output is identical except for the added `schema_version` field. All consumers (hooks, SDD skill, dispatch log readers) access specific keys and are unaffected by the addition.

---

## 5. `_report_utils.py` Migration

### 5.1 Phase 2 Changes

The Pydantic model becomes the single source of truth for report constants. `_report_utils.py` re-exports from the model for backwards compatibility.

**Constants that migrate to the model:**
- `VALID_STATUSES` → `Status` Literal type on `ImplementerReport`
- `STATUS_VALUE_PATTERN` → no longer needed (status comes from typed frontmatter)
- `extract_implementer_status()` → no longer needed (status is a typed field)

**Re-export pattern:**
```python
# _report_utils.py
from skills.scripts.models.implementer_report import Status
VALID_STATUSES = set(Status.__args__)  # {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"}
```

### 5.2 What Stays in `_report_utils.py`

Prose section-presence checking remains in `_report_utils.py`:
- `REQUIRED_SECTIONS` — still needed for markdown body section detection
- `find_sections()`, `section_is_present()` — prose header detection
- `section_contains_content()`, `is_placeholder_text()` — content heuristics
- `validate_report_sections()` — orchestrates prose section checks
- `SECTION_HEADER_PATTERN`, `PLACEHOLDER_VALUES` — supporting constants

### 5.3 Documentation

- Docstring at top of `_report_utils.py` updated to note re-export pattern and Phase 7 cleanup target
- `VALID_STATUSES` and `extract_implementer_status()` docstrings note they are sourced from the Pydantic model

### 5.4 Pre-existing Duplication

`controller-checkpoint.py` contains its own `validate_report_sections()` function (lines 207-244) that duplicates `_report_utils.py`'s logic. Phase 2 does not fix this — it is a pre-existing issue. Noted as a Phase 7 cleanup candidate.

---

## 6. Prompt Template Changes

### 6.1 `implementer-prompt.md`

The report format template gains a YAML frontmatter block prepended to the existing prose section template. The instruction changes from:

```
When done, report using this exact structure. Do not omit sections.

**Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
```

To:

```
When done, report using this exact structure. Do not omit sections.

Your report MUST begin with a YAML frontmatter block (between --- delimiters),
followed by the prose sections below.

---
schema_version: 1
task_id: [your task number]
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
  - constraint: "[constraint text from plan]"
    status: compliant | non_compliant | partial | not_applicable
    detail: "[how you complied]"
---

**Implementation Summary:**
[2-3 sentences: what you built and the approach taken]

**Source Files Read:**
...
```

The prose section template below the frontmatter is unchanged from today.

### 6.2 Atomicity

The prompt template change ships in the same commit as the validator changes, per meta-design Section 10.4.

### 6.3 Other Files Unchanged

- `controller-checkpoint.py` — gains `schema_version` via `CheckpointResult` construction, but its invocation interface doesn't change
- No other prompt templates affected

---

## 7. CLI and Hook Integration

### 7.1 `validators.py` — New `report` Subcommand

```bash
.venv/bin/python3 validators.py report <path/to/report.md>
```

Implementation follows the established `validate_plan()` pattern:
1. Check file exists (exit 2 if not)
2. Check bypass env var (exit 0 with warning if set)
3. Read file, extract YAML frontmatter (hard FAIL exit 1 if absent)
4. `yaml.safe_load()` frontmatter
5. On YAML error: `format_yaml_error()` to stderr, exit 1
6. `ImplementerReport.model_validate(data)`
7. On validation error: `format_validation_error()` to stderr, exit 1
8. Success: exit 0

### 7.2 `validate-report.py` — Pydantic Validation Step

The existing `validate-report.py` gains a Pydantic validation step before the prose section check:

1. Extract frontmatter → validate with `ImplementerReport.model_validate()`
2. If frontmatter absent → hard FAIL ("report predates Phase 2 cutover — add YAML frontmatter")
3. If frontmatter invalid → `format_validation_error()`
4. If frontmatter valid → proceed to prose section-presence check via `_report_utils.validate_report_sections()`

The `sdd-pre-dispatch-hook.sh` already calls `validate-report.py` — no hook changes needed.

### 7.3 CheckpointResult — No CLI Subcommand

`CheckpointResult` validates at construction time inside `controller-checkpoint.py`. No external CLI invocation needed. If construction fails, the script produces a Pydantic error — this indicates a developer bug in the checkpoint script, not a producer error.

### 7.4 Exit Code Convention

Unchanged from Phase 1: `0` = pass, `1` = validation fail, `2` = infrastructure error.

---

## 8. Testing Strategy

### 8.1 New Test Files

```
tests/
├── fixtures/
│   └── reports/
│       ├── valid/
│       │   ├── minimal-report.md        # DONE, 1 file, no contracts
│       │   └── full-featured-report.md  # DONE_WITH_CONCERNS, multiple files, contracts
│       └── invalid/
│           ├── missing-status.md
│           ├── bad-status-enum.md
│           ├── test-counts-inconsistent.md
│           └── no-files-for-done.md
├── unit/
│   ├── test_models/
│   │   ├── test_implementer_report_model.py   # ~15 tests
│   │   └── test_checkpoint_result_model.py    # ~12 tests
│   └── test_validators/
│       └── test_validate_report_pydantic.py   # ~10 tests
```

### 8.2 ImplementerReport Model Tests (~15)

- Golden-input parse: valid minimal fixture, valid full-featured fixture
- Per-field missing/wrong-type failures: `status`, `task_id`, `files_changed`, `tests`
- Status enum validation: all 4 valid values pass, invalid value rejected
- `test_counts_consistent` validator: `passing > written` fails
- `files_changed_non_empty_for_done` validator: DONE with empty list fails; BLOCKED with empty list passes
- Contract compliance `status` enum: all 4 values pass, invalid rejected
- Empty `contract_compliance` list allowed (tasks without contract constraints)
- `schema_version` mismatch rejected

### 8.3 CheckpointResult Model Tests (~12)

- Golden-input parse for each phase: pre-execution, pre-dispatch, pre-completion
- `fail_requires_blockers` validator: FAIL with empty blockers fails
- `blockers_reference_check_names` validator: blocker referencing non-existent check fails
- `task_number_required_for_pre_dispatch` validator: pre-dispatch without task_number fails
- `schema_version` present in `.model_dump()` output
- `CheckStatus` enum covers all 6 values: PASS, FAIL, WARN, SKIP, OK, WARNING
- Optional fields (`task_number`, `progress`) absent for pre-execution passes
- All 3 phases produce valid output from golden inputs

### 8.4 CLI Entry-Point Tests (~10)

- `validators.py report` subcommand: valid fixture → exit 0
- `validators.py report` subcommand: invalid fixture → exit 1, stderr contains `VALIDATION FAILED`
- Missing file → exit 2
- Bypass env var → exit 0, stderr contains `BYPASS`
- Missing frontmatter → exit 1, message references "Phase 2 cutover"
- YAML parse error → exit 1, stderr contains `YAML PARSE FAILED`

### 8.5 Pre-Ship Smoke Test

- Copy real implementer reports from `reports/` (from Phase 1 SDD session) into `tests/fixtures/_smoke-test-reports/`
- Add YAML frontmatter to copies (never modify originals)
- Run validator against all copies — all must PASS
- Delete `_smoke-test-reports/` in the merge commit

### 8.6 Estimated Test Counts

| Layer | Before Phase 2 | After Phase 2 | Delta |
|-------|---------------|--------------|-------|
| Unit tests (pytest) | ~163 | ~200 | +37 |
| Regression checks | 122 | 122 | 0 |
| Install checks | 105 | 105 | 0 |

---

## 9. Migration and Rollback

### 9.1 Cutover Procedure

All changes ship atomically (meta-design Section 10.4):
- Models (`implementer_report.py`, `checkpoint_result.py`)
- `validators.py` report subcommand
- `validate-report.py` Pydantic validation step
- `implementer-prompt.md` frontmatter instructions
- `controller-checkpoint.py` `CheckpointResult` construction
- `_report_utils.py` re-export changes
- Test files and fixtures

Existing reports without frontmatter produce a hard FAIL if re-validated (expected — same behavior as archived plans in Phase 1).

### 9.2 Rollback Ladder

1. Fix the schema, push, reinstall (typical)
2. `export SUPERPOWERS_VALIDATOR_BYPASS=1` (emergency unblock)
3. `git revert <phase-2-commits>` (nuclear)

---

## 10. Meta-Design Updates

Phase 2 updates `docs/plans/2026-04-24-pydantic-meta-design.md`:

| Section | Update |
|---------|--------|
| 2 (Roadmap) | Phase 2 status → "Complete" |
| 2 (Roadmap) | Phase 3 scope note: add cross-artifact contract validation (PlanExecutionContract) as first-class design question — user-requested candidate |
| 5.1 (Location) | `implementer_report.py` and `checkpoint_result.py` confirmed in file tree |
| 11 (Lessons Learned) | Phase 2 post-mortem (added after implementation) |
| 12.1 (Renderer) | Resolved → "No renderer; humans read file as-is. Revisit only if future phase discovers a need." |
| 12.2 (Subagent output) | Resolved → "YAML frontmatter, same as Plan. Consistent with Phase 1 pattern." |
| 12.3 (Cross-artifact) | Updated → "User-requested Phase 3 candidate. PlanExecutionContract checking: report contract compliance covers plan constraints, report task_id exists in plan, files_changed cross-task ownership." |

---

## 11. Directory Structure (New Additions)

```
skills/scripts/models/                    # EXISTING — Phase 1 infra
├── implementer_report.py                 # NEW — Phase 2
└── checkpoint_result.py                  # NEW — Phase 2

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
├── test_implementer_report_model.py      # NEW — Phase 2
└── test_checkpoint_result_model.py       # NEW — Phase 2

tests/unit/test_validators/               # EXISTING
└── test_validate_report_pydantic.py      # NEW — Phase 2

tests/fixtures/_smoke-test-reports/       # NEW — throwaway, deleted post-ship
```

---

## 12. Acceptance Criteria

- [ ] `skills/scripts/models/implementer_report.py` exists with `ImplementerReport(SchemaVersionedModel)`, `FileChange`, `TestSummary`, `ContractComplianceItem` nested models
- [ ] `ImplementerReport` validates 3 cross-field relationships: `test_counts_consistent`, `files_changed_non_empty_for_done`, `done_with_concerns_requires_flag`
- [ ] `skills/scripts/models/checkpoint_result.py` exists with `CheckpointResult(SchemaVersionedModel)`, `CheckResult`, `Progress` nested models
- [ ] `CheckpointResult` validates 3 cross-field relationships: `fail_requires_blockers`, `blockers_reference_check_names`, `task_number_required_for_pre_dispatch`
- [ ] `validators.py` has a `report` subcommand that validates implementer report files
- [ ] `validators.py report` exit codes: 0 pass / 1 validation fail / 2 infrastructure
- [ ] `validate-report.py` runs Pydantic validation before prose section-presence check
- [ ] Reports without YAML frontmatter produce hard FAIL with message referencing "Phase 2 cutover"
- [ ] `controller-checkpoint.py` `_build_result()` constructs via `CheckpointResult` and includes `schema_version` in JSON output
- [ ] `implementer-prompt.md` report format template includes YAML frontmatter block
- [ ] Prompt template and validators ship atomically (same commit)
- [ ] `_report_utils.py` re-exports `VALID_STATUSES` from the Pydantic model's `Status` type
- [ ] `_report_utils.py` docstring notes Phase 7 cleanup target
- [ ] `_report_utils.py` `extract_implementer_status()` documented as deprecated (status now from frontmatter)
- [ ] Pre-existing `validate_report_sections()` duplication in `controller-checkpoint.py` noted as Phase 7 cleanup candidate (not fixed in Phase 2)
- [ ] Meta-design Sections 2, 5, 11, 12 updated per Section 10 of this spec
- [ ] Meta-design Phase 3 scope includes cross-artifact contract validation as user-requested candidate
- [ ] ~37 new unit tests pass across `test_implementer_report_model.py`, `test_checkpoint_result_model.py`, `test_validate_report_pydantic.py`
- [ ] Test fixtures exist: `tests/fixtures/reports/valid/` (2 files), `tests/fixtures/reports/invalid/` (4 files)
- [ ] Pre-ship smoke test with real reports passes
- [ ] `tests/fixtures/_smoke-test-reports/` deleted in merge commit
- [ ] All existing tests continue to pass after changes
- [ ] `SUPERPOWERS_VALIDATOR_BYPASS=1` env var honored by `report` subcommand
