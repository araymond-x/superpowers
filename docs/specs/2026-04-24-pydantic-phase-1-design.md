# Pydantic Adoption — Phase 1 Design Spec

**Date:** 2026-04-24
**Status:** Draft — pending spec review loop
**Scope:** Phase 1 of multi-phase Pydantic adoption across the Superpowers custom fork
**Feature archetype:** Migration (phased transition from regex-based validation to Pydantic-typed validation)
**Targets:** A3 Plan + B4 HandoffPackage + cross-phase meta-design doc
**Companion doc:** `docs/plans/2026-04-24-pydantic-meta-design.md` (cross-phase architecture)
**Source context:**
- `docs/external-references/2026-04-21-claude-code-production-guardrails.md`
- `docs/external-references/2026-04-21-production-guardrails-gap-analysis.md`
- `docs/external-references/2026-04-23-pydantic-adoption-plan.md`

---

## Executive Summary

Adopt Pydantic v2.7+ to replace regex/grep-based validation of two high-leverage gate artifacts:

- **A3 Plan** (`docs/imp-plans/*.md`) — consumed by `plan-validation-gate-hook.sh` and `subagent-driven-development` skill
- **B4 HandoffPackage** (handoff package directories) — consumed by `handoff-acceptance` skill

Plans and handoffs adopt a **YAML frontmatter + markdown body** structure. Typed fields live in YAML; prose content lives in markdown. Pydantic models validate the frontmatter at hook time. Explanatory errors (field-path + expected + actual + hint) are surfaced back to the producer so authoring iteration becomes a tight feedback loop rather than cryptic grep failures.

Phase 1 ships with **schema versioning built in from day one** (forward-compatibility infrastructure) plus a companion **meta-design doc** that locks in cross-phase architectural decisions so Phase 2+ don't re-litigate them.

**Migration policy:** hard cutover, no migration script, archived plans stay archival. Pre-ship fixture smoke test against plans post 2026-04-08 guards against schema design bugs before merge.

---

## Locked Decisions Summary

| # | Decision | Choice |
|---|----------|--------|
| 1 | Phase 1 scope | A3 Plan + B4 HandoffPackage + meta-design doc |
| 2 | Format | YAML frontmatter + markdown body (both artifacts) |
| 3 | Dependency | Pydantic v2.7+ only (no Instructor) |
| 4 | Migration | Hard cutover, no migration script |
| 5 | Pre-ship test | Yes, against recent plans (post 2026-04-08) |
| 6 | Model location | `skills/scripts/models/` |
| 7 | Schema versioning | Validator-pinned; forensic flag `--schema-version N` for legacy |
| 8 | YAML/Pydantic errors | Split into separate blocks |
| 9 | Exit codes | 0 pass / 1 producer-fix / 2 infrastructure |
| 10 | Bypass env var | `SUPERPOWERS_VALIDATOR_BYPASS=1` — included (emergency unblock) |
| 11 | Approach tier | Approach 3 (full Phase 1 + forward-compat infrastructure) |

---

## Section 1 — Architecture Overview

### 1.1 Directory Structure (new additions only)

```
skills/
├── scripts/                          # existing shared utilities
│   ├── strip-frontmatter.sh          # existing
│   └── models/                       # NEW — shared Pydantic models
│       ├── __init__.py
│       ├── _base.py                  # SchemaVersionedModel, versioning helpers
│       ├── plan.py                   # Plan, Task, Module, SharedConstant, PatternReference
│       ├── handoff.py                # HandoffPackage, ContractConstraints, FieldType
│       ├── errors.py                 # ValidationError → human-readable formatter
│       └── validators.py             # CLI entry points for hook consumption
├── subagent-driven-development/
│   └── scripts/
│       └── validate-plan.py          # MODIFIED — routes to Pydantic when YAML frontmatter detected
├── writing-plans/
│   └── scripts/
│       └── plan-validation-gate-hook.sh  # MODIFIED — calls new validator
└── handoff-acceptance/
    └── scripts/
        ├── check-handoff.sh          # MODIFIED — calls new validator
        └── handoff-gate-hook.sh      # MODIFIED — calls new validator

tests/
├── fixtures/
│   ├── honesty-checks/               # existing (seeded for future Phase 3)
│   ├── plans/                        # NEW — canonical plan fixtures
│   │   ├── valid/
│   │   │   ├── minimal-plan.md       # smallest valid plan
│   │   │   └── full-featured-plan.md # exercises every field
│   │   └── invalid/
│   │       ├── missing-required-field.md
│   │       ├── bad-dependency.md
│   │       └── ...
│   ├── handoffs/                     # NEW — canonical handoff fixtures
│   └── _smoke-test-plans/            # NEW — throwaway, deleted post-ship
└── unit/
    ├── test_models/                  # NEW
    │   ├── test_plan_model.py
    │   ├── test_handoff_model.py
    │   ├── test_schema_versioning.py
    │   └── test_error_formatter.py
    └── test_validators/              # NEW
        ├── test_validate_plan_pydantic.py
        └── test_validate_handoff_pydantic.py

docs/
├── specs/
│   ├── 2026-04-24-pydantic-phase-1-design.md          # THIS SPEC
│   └── 2026-04-24-pydantic-phase-1-design-distilled.md
└── plans/
    └── 2026-04-24-pydantic-meta-design.md             # CROSS-PHASE ARCHITECTURE DOC
```

### 1.2 Key Architectural Decisions

1. **Models live at `skills/scripts/models/`.** Extends the existing `skills/scripts/` shared-utilities pattern (where `strip-frontmatter.sh` already lives), stays inside the skills symlink (accessible at `~/.claude/skills/superpowers/scripts/models/`), and doesn't introduce a new top-level directory. Cross-skill imports flow through this neutral location — `writing-plans` doesn't depend on `subagent-driven-development`'s scripts.

2. **Shell hooks stay shell; Python does the typed work.** Existing `.sh` hooks remain the entry points (preserving the hook-path infrastructure). They invoke new Python validators via subprocess. No bash is rewritten in Python — the division of labor matches what already works.

3. **Schema versioning with validator-pinned current version.** Every YAML frontmatter block has a required `schema_version: int` field that must equal the validator's `CURRENT_SCHEMA_VERSION`. Versioning exists for audit trail and drift detection, not runtime dispatch. Backward-compat validation requires an explicit `--schema-version N` flag (hooks never use it; humans do, for forensics).

4. **Detection-by-frontmatter for legacy plans.** If a plan file starts with `---` → Pydantic validator path. Otherwise → hard FAIL with message: "this plan predates Phase 1 Pydantic cutover — if you need to re-execute it, add YAML frontmatter first." No automatic fallback to old regex path.

5. **Existing scripts are *modified*, not replaced, in Phase 1.** Function signatures don't change; hook callers don't need updates. This keeps the blast radius of Phase 1 small.

### 1.3 Obsolescence Targets (Phase 7 cleanup — not in Phase 1 scope)

- Legacy regex branches in `validate-plan.py` (kept as "no YAML frontmatter" fallback; unreachable once all active plans are converted)
- `check_sections()` regex logic in `validate-plan.py`
- String-parsing logic in `check-handoff.sh` for the Contract Constraints first-50-lines block

These are deletion candidates only after Phase 7 audit confirms no active consumers remain.

---

## Section 2 — Components (Schemas, Validators, Error Formatter)

### 2.1 Shared Base — `skills/scripts/models/_base.py`

```python
from pydantic import BaseModel, field_validator, ConfigDict
from typing import ClassVar

CURRENT_SCHEMA_VERSION = 1

class SchemaVersionedModel(BaseModel):
    """Base class for all versioned schema models."""
    model_config = ConfigDict(extra="forbid")  # reject unknown fields — catches typos
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

**Key design choices:**
- `extra="forbid"` — unknown fields are rejected (catches `task_deps:` vs `depends_on:` typos at validation time)
- `SchemaVersionedModel` is the only place `CURRENT_SCHEMA_VERSION` is checked — every downstream model inherits the check automatically

### 2.2 `Plan` Schema — `skills/scripts/models/plan.py`

```python
from typing import Literal
from pydantic import Field, model_validator
from ._base import SchemaVersionedModel

FeatureArchetype = Literal["greenfield", "replacement", "extension", "refactor", "migration"]

class SharedConstant(SchemaVersionedModel):
    path: str              # e.g., "app.config.RETENTION_DAYS"
    value: str             # stringified — actual import verification is in Task 0
    reason: str            # why this constant matters for the plan

class PatternReference(SchemaVersionedModel):
    name: str              # e.g., "db-migration-pattern"
    source_files: list[str]
    reason: str

class Task(SchemaVersionedModel):
    id: int                # zero-padded sequential across all modules
    title: str
    module_id: int | None = None
    depends_on: list[int] = Field(default_factory=list)
    pattern_references: list[str] = Field(default_factory=list)
    shared_constants_used: list[str] = Field(default_factory=list)

class Module(SchemaVersionedModel):
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
            raise ValueError(
                f"Tasks {sorted(orphans)} are not claimed by any module"
            )
        return self
```

**What this unlocks that `validate-plan.py` doesn't do today:**
- Dependency-reference validation (`depends_on` → valid task IDs, no forward refs)
- Shared-constants cross-reference
- Pattern-reference cross-reference
- Module task-ID collision detection
- Module-orphan detection

### 2.3 `HandoffPackage` Schema — `skills/scripts/models/handoff.py`

```python
from typing import Literal
from pydantic import Field, model_validator
from ._base import SchemaVersionedModel

FieldTypeKind = Literal["string", "integer", "float", "boolean", "date", "enum"]

class FieldType(SchemaVersionedModel):
    name: str
    kind: FieldTypeKind
    format_hint: str | None = None
    nullable: bool = False

class FormatRule(SchemaVersionedModel):
    applies_to: list[str]
    rule: str

class Sample(SchemaVersionedModel):
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

    @model_validator(mode="after")
    def samples_point_to_real_files(self, info) -> "HandoffPackage":
        pkg_dir = info.context.get("package_dir") if info.context else None
        if pkg_dir is None:
            return self
        from pathlib import Path
        for sample in self.samples:
            full = Path(pkg_dir) / sample.path
            if not full.is_file():
                raise ValueError(
                    f"Sample references {sample.path} but file does not exist at {full}"
                )
        return self
```

**What this unlocks that `check-handoff.sh` doesn't do today:**
- Typed contract constraints (vs. prose bullets in the first 50 lines)
- Format rules cross-referenced to declared field types
- Sample files verified to exist on disk
- Machine-readable contract for downstream pipeline agents

### 2.4 Error Formatter — `skills/scripts/models/errors.py`

```python
from pydantic import ValidationError

def format_validation_error(e: ValidationError, artifact_path: str) -> str:
    """Transform a Pydantic ValidationError into a hook-friendly explanatory block."""
    lines = [
        "═══════════════════════════════════════════════════════════════════",
        f" VALIDATION FAILED: {artifact_path}",
        f" {len(e.errors())} issue(s) found. Fix each and re-validate.",
        "═══════════════════════════════════════════════════════════════════",
        ""
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

**Example output a producer sees:**

```
═══════════════════════════════════════════════════════════════════
 VALIDATION FAILED: docs/imp-plans/2026-04-24-retention-cleanup.md
 2 issue(s) found. Fix each and re-validate.
═══════════════════════════════════════════════════════════════════

[1] Field:    tasks.1.depends_on
    Problem:  Value error, Task 1 cannot depend on task(s) [3] — dependencies must have lower IDs
    Got:      [3]

[2] Field:    feature_archetype
    Problem:  Input should be 'greenfield', 'replacement', 'extension', 'refactor' or 'migration'
    Got:      'expansion'
    Expected: one of ('greenfield', 'replacement', 'extension', 'refactor', 'migration')

═══════════════════════════════════════════════════════════════════
```

### 2.5 Validator CLI Entry Points — `skills/scripts/models/validators.py`

Thin wrappers invoked by hooks via subprocess:

```bash
# Called from plan-validation-gate-hook.sh
python3 -m skills.scripts.models.validators plan path/to/plan.md
# Called from handoff-gate-hook.sh
python3 -m skills.scripts.models.validators handoff path/to/package-dir/
# Forensic escape hatch (humans only)
python3 -m skills.scripts.models.validators plan path/to/plan.md --schema-version 1
```

**Exit code convention:** 0 = pass, 1 = validation failure (producer fix needed), 2 = infrastructure/setup/usage problem.

---

## Section 3 — Data Flow

### 3.1 Plan Authoring Flow (Post-Phase 1)

```
Author/agent invokes writing-plans skill
    ↓
Skill produces plan .md file with YAML frontmatter + markdown body
    ↓
Plan Completion Gate runs:
    1. validate-plan.py (MODIFIED)
         ├─ YAML frontmatter present? ── NO → HARD FAIL (see 1.2#4)
         └─ YES → extract, parse with Plan.model_validate(...)
              ├─ PASS → continue
              └─ FAIL → format_validation_error → stderr → exit 1 → gate blocks
    2. plan-document-reviewer subagent (unchanged)
    3. plan-review-report.md saved (unchanged)
    4. plan-manifest.txt written (unchanged)
    ↓
Gate PASS → plan ready for executing-plans or SDD
```

Only step 1 changes. Steps 2–4 see the same markdown file humans read — the YAML frontmatter is a typed leading block the plan-document-reviewer ignores.

### 3.2 Handoff Acceptance Flow (Post-Phase 1)

```
Producer agent writes handoff package directory (README.md has YAML frontmatter)
    ↓
Consumer agent invokes superpowers:handoff-acceptance
    ↓
handoff-gate-hook.sh:
    1. check-handoff.sh (MODIFIED)
         ├─ YAML frontmatter in README.md? ── NO → HARD FAIL
         └─ YES → extract, parse with HandoffPackage.model_validate(
              frontmatter_dict, context={"package_dir": <path>}
            )
              ├─ PASS → continue
              └─ FAIL → format_validation_error → stderr → exit 1 → gate blocks
    2. (existing) Contract summary surface check (unchanged in Phase 1)
    ↓
Gate PASS → consumer proceeds with brainstorming/planning
```

The `context={"package_dir": <path>}` injection enables the `samples_point_to_real_files` validator to cross-check filesystem state.

### 3.3 Producer Iteration Loop (Headline Feature)

```
Producer writes artifact with N bugs
    ↓
Validator produces structured block listing ALL N bugs in one pass
    ↓
Producer reads field-path + expected + got + hint for each
    ↓
Producer edits all N in one cycle
    ↓
Re-run validator → PASS (or another iteration if schema-adjacent bugs surfaced)
```

**Measurable improvement:** count `validate-plan.py` invocations per plan in before/after corpora. Drop in average invocations = explanatory-error property is paying off.

### 3.4 Hook Error-Surface Integration

Hook shells wrap the Python validator's stderr in a JSON block that Claude Code surfaces intact to the subagent:

```bash
if ! python3 -m skills.scripts.models.validators plan "$PLAN_FILE" 2>/tmp/validator-err; then
  cat <<EOF
{"decision":"block","reason":$(jq -Rs . < /tmp/validator-err)}
EOF
  exit 0
fi
```

The JSON wrapping preserves box-drawing characters and newlines so the producer sees the explanatory block intact.

---

## Section 4 — Error Handling (Edge Cases)

### 4.1 Malformed YAML
Handler catches `yaml.YAMLError` BEFORE attempting Pydantic parsing. Uses the distinct `format_yaml_error` block so producers know it's a YAML-layer failure, not a schema-layer failure.

### 4.2 Missing `schema_version`
Regular Pydantic `missing` error with a first-class hint added by `format_validation_error`: *"Add `schema_version: 1` as the first line of your YAML frontmatter."*

### 4.3 Pydantic Not Installed
CLI import check exits with code 2 and message pointing at `.venv/bin/pip install -r requirements.txt`. Installation verification (`verify-symlink-install.sh`) adds a Pydantic import check so installers hit this early, not at first hook fire.

### 4.4 Validator Crashes (Unexpected Python Exception)
CLI wraps all validation in try/except. Unexpected exceptions produce a "VALIDATOR CRASHED (this is a bug in the validator, not your artifact)" message and exit code 2. Gives producers an escape hatch if our code has a bug.

### 4.5 Artifact File Doesn't Exist
CLI checks file existence first. Missing file = exit 2 (invocation problem, not producer mistake).

### 4.6 Rollback Path
Layered escape in order of preference:
1. **Fix the schema, push, reinstall** — typical bug fix cycle
2. **`export SUPERPOWERS_VALIDATOR_BYPASS=1`** — emergency unblock with stderr warning on every skip
3. **`git revert <phase-1-commit>`** — nuclear option

---

## Section 5 — Migration / Obsolescence

### 5.1 What Becomes Obsolete (And When)

**Phase 1 cutover (nothing deleted immediately):**

| Code / behavior | Status after Phase 1 | Deletion timeline |
|-----------------|---------------------|-------------------|
| `validate-plan.py` regex-based section checks | Routed around when YAML frontmatter present; still fires on plans without frontmatter (hard FAIL) | Phase 7 cleanup |
| `check-handoff.sh` first-50-lines grep | Routed around when YAML frontmatter present; still fires on legacy handoffs | Phase 7 cleanup |
| Prose "Contract Constraints" section template | Superseded by YAML frontmatter | Phase 7 cleanup |
| Prompt template instructions for markdown-only authoring | **Updated in Phase 1 itself** | N/A (updated now) |

**Explicitly NOT deleted in Phase 1:** any existing script, hook, CLAUDE.md section, historical artifact, or test file.

### 5.2 Dependency Verification Before Phase 7 Deletion

Per the fork's audit-all-callers rule, Phase 7 cleanup requires:
- Grep every remaining call site of the symbol
- Verify no prompt template instructs authors to use the deprecated format
- Verify no test file exercises the legacy path

Phase 7 is NOT in scope here. Phase 1 documents the future audit checklist only.

### 5.3 Updated Prompt Templates (Shipping In Phase 1)

These ship in the same commit as the validator — authoring and validation cut over atomically:

| File | Update |
|------|--------|
| `skills/writing-plans/SKILL.md` | New section: "Your plan file must begin with a YAML frontmatter block including `schema_version: 1` and the declared fields. See the design spec for the schema." Replaces the old section-header checklist. |
| `skills/handoff-acceptance/references/handoff-package-spec.md` | Replaces prose "Contract Constraints" section template with YAML frontmatter template. |
| `skills/subagent-driven-development/SKILL.md` | One-line note that plans consumed by SDD now have YAML frontmatter. |
| `CLAUDE.md` (fork root) | New section: Pydantic schema location, how to bump versions, bypass env var. |

### 5.4 Cutover Procedure

```
1. Merge Phase 1 branch to main
2. Reinstall: `git pull` in fork — symlinks pick up changes immediately
3. Run installation verification:
   bash tests/ARaymond-installation/verify-symlink-install.sh
4. Run full test suite:
   .venv/bin/python3 -m pytest tests/unit/ -v
   python3 tests/ARaymond-skill-regression/validate-all-skills.py
5. Phase 1 is live. Next plan authored uses new format.
```

**Rollback ladder:** see 4.6.

### 5.5 Archived Plans (Not In Scope)

Plans written before cutover live in project repos as-is. They:
- Are not modified
- Will FAIL the new validator if re-run (no YAML frontmatter → hard FAIL)
- Are not expected to be re-validated (per decision #4 — hard cutover)
- Have a forensic escape via `--schema-version N` flag (hooks never use it)

If a project needs to re-execute an archived plan (rare), manually add YAML frontmatter to that plan file. This is a one-per-plan manual task, not a batch migration.

### 5.6 Pre-Ship Fixture Smoke Test (Pre-Merge Gate)

Before Phase 1 is merged to main:

1. Identify recent plans (post 2026-04-08) from project trees
2. Copy each into `tests/fixtures/_smoke-test-plans/` (never modify originals)
3. Manually add YAML frontmatter to each copy reflecting what the author would have written in the new format
4. Run `.venv/bin/python3 -m pytest tests/unit/test_smoke_real_plans.py -v`
5. Triage results:
   - All PASS → merge
   - FAIL reveals schema bug → fix schema, re-run
   - FAIL reveals real plan-authoring mistake → document, don't relax schema

`tests/fixtures/_smoke-test-plans/` is deleted in the same merge commit.

---

## Section 6 — Testing Strategy

### 6.1 Test Layers For Phase 1

| Layer | Scope | Location | Runs when |
|-------|-------|----------|-----------|
| 1. Model unit tests | Each Pydantic model in isolation | `tests/unit/test_models/` | Every edit (<1s) |
| 2. Cross-field validator tests | `@model_validator` invariants | `tests/unit/test_models/` | Every edit |
| 3. CLI entry-point tests | `validators.py` subprocess interface | `tests/unit/test_validators/` | Every edit |
| 4. Hook integration tests | Shell hooks calling Python | `tests/unit/test_hooks_pydantic.py` | Every edit |
| 5. Pre-ship smoke test | Real recent plans vs. schema | `tests/unit/test_smoke_real_plans.py` | Pre-merge gate |
| 6. Installation verification | Pydantic import + model import | `tests/ARaymond-installation/verify-symlink-install.sh` | After install changes |

### 6.2 Model Unit Tests

Every top-level model gets:
- Golden-input test (canonical valid instance parses + round-trips)
- Per-field failure tests (parameterized — missing required / wrong type / invalid enum)
- `extra="forbid"` tests (typos rejected)
- Schema version enforcement tests (wrong version → explanatory error)

~15–20 tests per top-level model.

### 6.3 Cross-Field Validator Tests

One test class per `@model_validator`. Each class has ≥1 failing test (bad input → expected error) and ≥1 passing test (edge case at the boundary of valid).

Plan model: 5 validators × 5–8 tests each = 25–40 tests.
HandoffPackage model: 3 validators × 3–5 tests each = 9–15 tests.

### 6.4 CLI Entry-Point Tests

Happy path + each error exit code + bypass env var + missing file + YAML-before-Pydantic. ~10–15 tests per artifact type × 2 = 20–30 tests.

### 6.5 Hook Integration Tests

Each hook × (pass path + block path + broken input) ≈ 8 tests total.

### 6.6 Pre-Ship Smoke Test

Auto-discovers every fixture in `tests/fixtures/_smoke-test-plans/` and parameterizes the test per fixture. Runs as pre-merge pytest gate. `conftest.py` skips the test if the fixture directory is empty (post-merge state).

### 6.7 Installation Verification Updates

Adds 2 checks to `verify-symlink-install.sh`:

```bash
check "Pydantic v2.7+ importable" \
  ".venv/bin/python3 -c 'import pydantic; assert pydantic.VERSION.startswith(\"2.\") and int(pydantic.VERSION.split(\".\")[1]) >= 7'"

check "Pydantic model modules import cleanly" \
  ".venv/bin/python3 -c 'from skills.scripts.models import plan, handoff, errors, validators'"
```

New total: 105 (from 103).

### 6.8 Post-Adoption Test Counts (Phase 1 Complete)

| Layer | Before | After | Delta |
|-------|--------|-------|-------|
| Unit tests (pytest) | 70 | ~115 | +45 |
| Regression checks | 122 | 122 | 0 |
| Install checks | 103 | 105 | +2 |
| Behavioral scenarios | ~10 | ~12 | +2 |

---

## Section 7 — Cross-Phase Meta-Design Doc

A companion doc at `docs/plans/2026-04-24-pydantic-meta-design.md` locks in architectural decisions that apply across all future phases. See that file for the full content.

**What the meta-design doc locks in (future phases don't re-debate):**
- Format pattern (YAML frontmatter + markdown body)
- Schema versioning mechanics
- Model organization (`skills/scripts/models/`)
- Validator CLI pattern
- Exit code convention
- Error formatter pattern
- Hook integration pattern
- Test layer pattern
- Rollback/migration pattern

**Left intentionally open:**
- Which schema(s) each phase tackles
- Whether that phase needs a renderer (probably Phase 2+)
- Whether that phase needs tool-use integration (probably Phase 2+)
- Whether the phase adds new fixtures or test layers

**Evolution mechanism:** Section 11 of the meta-design appends per-phase post-mortems. If a post-mortem invalidates a locked decision, the doc's relevant section is updated with a dated note.

---

## Acceptance Criteria

- [ ] `skills/scripts/models/` directory exists with `__init__.py`, `_base.py`, `plan.py`, `handoff.py`, `errors.py`, `validators.py`
- [ ] `Plan` Pydantic model validates the 5 cross-field relationships (unique-sequential IDs, depends_on resolution, shared_constants_used declared, pattern_references declared, module_task_ids consistent)
- [ ] `HandoffPackage` Pydantic model validates the 3 cross-field relationships (format_rules reference declared fields, at_least_one_sample, samples_point_to_real_files)
- [ ] `SchemaVersionedModel` base enforces `CURRENT_SCHEMA_VERSION` match and `extra="forbid"`
- [ ] Error formatter produces split YAML-parse vs Pydantic-validation blocks with field paths, expected/got, and schema_version hint
- [ ] CLI entry point supports `plan`, `handoff`, and `--schema-version N` forensic flag
- [ ] CLI honors `SUPERPOWERS_VALIDATOR_BYPASS=1` env var with stderr warning
- [ ] CLI exit codes: 0 pass / 1 validation fail / 2 infrastructure
- [ ] `plan-validation-gate-hook.sh` invokes the Python validator and wraps stderr in JSON block
- [ ] `check-handoff.sh` invokes the Python validator and passes `package_dir` context
- [ ] `validate-plan.py` hard-FAILs on plans without YAML frontmatter
- [ ] `skills/writing-plans/SKILL.md` instructs authors to use the new YAML frontmatter format
- [ ] `skills/handoff-acceptance/references/handoff-package-spec.md` updated with YAML frontmatter template
- [ ] `CLAUDE.md` (fork root) has a new Pydantic section documenting schema location, version bumps, bypass env var
- [ ] Pydantic v2.7+ added to `requirements.txt`
- [ ] `verify-symlink-install.sh` includes 2 new Pydantic checks (total 105)
- [ ] ~45 new unit tests pass across `tests/unit/test_models/`, `tests/unit/test_validators/`, `tests/unit/test_hooks_pydantic.py`
- [ ] Pre-ship smoke test file (`tests/unit/test_smoke_real_plans.py`) present with auto-discovery fixture parametrization
- [ ] `tests/fixtures/_smoke-test-plans/` populated with 5+ YAML-frontmatter-ified copies of post-2026-04-08 plans — all PASS the validator before merge
- [ ] `tests/fixtures/_smoke-test-plans/` deleted in the merge commit
- [ ] Meta-design doc (`docs/plans/2026-04-24-pydantic-meta-design.md`) exists and covers all 12 sections per its table of contents
- [ ] Distilled spec (`2026-04-24-pydantic-phase-1-design-distilled.md`) exists, <500 lines, has Contract Facts section, no exploration artifacts
- [ ] All existing tests continue to pass after changes (`pytest tests/unit/`, `validate-all-skills.py`, `verify-symlink-install.sh`)

---

## Open Questions / Decisions Deferred To Implementation

None — all architectural decisions locked via brainstorm. Implementation plan (next step: writing-plans skill) will decompose acceptance criteria into task-sized work items.
