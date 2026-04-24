# Pydantic Phase 1 — Distilled Implementation Spec

> **Source**: `docs/specs/2026-04-24-pydantic-phase-1-design.md` (v1.0, 11 decisions)
> **Distilled**: 2026-04-24
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.
> **Companion**: `docs/plans/2026-04-24-pydantic-meta-design.md` (cross-phase architecture)

---

## Contract Facts

### Format
- Artifacts use **YAML frontmatter** (`---` delimiters) for typed fields + **markdown body** for prose
- Detection: file starts with `---` → Pydantic path; otherwise → hard FAIL ("predates Phase 1 cutover — add YAML frontmatter")

### Base Classes (`_base.py`)
- `CURRENT_SCHEMA_VERSION = 1`
- `StrictModel(BaseModel)` — for **nested** types. Enforces `extra="forbid"`. No `schema_version`.
- `SchemaVersionedModel(StrictModel)` — for **top-level** artifacts. Adds required `schema_version: int` field, pinned to `CURRENT_SCHEMA_VERSION` via `@field_validator`.

### Plan Schema Fields (`plan.py`)
Top-level `Plan(SchemaVersionedModel)`:
- `schema_version: int` (required, must equal `CURRENT_SCHEMA_VERSION`)
- `feature_archetype: Literal["greenfield", "replacement", "extension", "refactor", "migration"]`
- `source_contracts: str | None = None`
- `shared_constants: list[SharedConstant] = []`
- `pattern_references: list[PatternReference] = []`
- `modules: list[Module] | None = None`
- `tasks: list[Task]` (required)

Nested types (all inherit `StrictModel`):
- `SharedConstant`: `path: str`, `value: str`, `reason: str`
- `PatternReference`: `name: str`, `source_files: list[str]`, `reason: str`
- `Task`: `id: int`, `title: str`, `module_id: int | None = None`, `depends_on: list[int] = []`, `pattern_references: list[str] = []`, `shared_constants_used: list[str] = []`
- `Module`: `id: int`, `title: str`, `task_ids: list[int]`

Plan cross-field validators (5 total):
1. `tasks_have_unique_sequential_ids` — IDs must be sequential ascending with no duplicates
2. `depends_on_references_valid_ids` — each `depends_on` entry must reference an existing task ID with a lower value (no forward refs)
3. `shared_constants_used_are_declared` — each task's `shared_constants_used` entries must exist in `plan.shared_constants`
4. `pattern_references_are_declared` — each task's `pattern_references` entries must exist in `plan.pattern_references`
5. `module_task_ids_are_consistent` — no task claimed by multiple modules; no orphan tasks

### HandoffPackage Schema Fields (`handoff.py`)
Top-level `HandoffPackage(SchemaVersionedModel)`:
- `schema_version: int` (required, must equal `CURRENT_SCHEMA_VERSION`)
- `package_name: str`
- `feeds_into: str`
- `one_sentence_purpose: str`
- `contract_constraints: list[FieldType]`
- `format_rules: list[FormatRule] = []`
- `samples: list[Sample]` (required)

Nested types (all inherit `StrictModel`):
- `FieldType`: `name: str`, `kind: Literal["string", "integer", "float", "boolean", "date", "enum"]`, `format_hint: str | None = None`, `nullable: bool = False`
- `FormatRule`: `applies_to: list[str]`, `rule: str`
- `Sample`: `path: str`, `description: str`

HandoffPackage cross-field validators (2 in-model):
1. `format_rules_reference_declared_fields` — each `FormatRule.applies_to` entry must exist in `contract_constraints` names
2. `at_least_one_sample` — `samples` must be non-empty

Filesystem post-check (CLI wrapper, NOT in model):
- After model validation passes, CLI verifies each `sample.path` exists as a file under `package_dir`
- On failure: emits `SAMPLE FILE MISSING` error block (distinct header from model validation)

### Error Block Headers (Three Distinct Layers)
1. `YAML PARSE FAILED` — YAML syntax error, Pydantic not attempted
2. `VALIDATION FAILED` — Pydantic schema/validator failure (field-path + expected + got + hint)
3. `SAMPLE FILE MISSING` — filesystem check after Pydantic passes (CLI wrapper only)

### Exit Codes
- `0` = pass
- `1` = validation failure (producer must fix artifact)
- `2` = infrastructure/setup problem (missing dependency, missing file, validator crash)

### CLI Invocation
```bash
python3 -m skills.scripts.models.validators plan <path/to/plan.md>
python3 -m skills.scripts.models.validators handoff <path/to/package-dir/>
python3 -m skills.scripts.models.validators plan <path> --schema-version N  # forensic only
```

### Environment Variables
- `SUPERPOWERS_VALIDATOR_BYPASS=1` — emergency skip; exits 0 with stderr warning containing `BYPASS`

### Pure Model / IO Split
- Pydantic models validate **data shape only**
- Filesystem, network, subprocess I/O lives in CLI wrapper (`validators.py`)
- `HandoffPackage` validates `samples: list[Sample]` shape; CLI checks `sample.path` exists on disk AFTER model validation
- Forensic flag `--schema-version N` is for human archival review only — hooks NEVER use it

---

## Open Decisions

(None — all 11 decisions resolved during brainstorm.)

---

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Phase 1 scope | A3 Plan + B4 HandoffPackage + meta-design doc |
| 2 | Format | YAML frontmatter + markdown body |
| 3 | Dependency | Pydantic v2.7+ only (no Instructor) |
| 4 | Migration | Hard cutover, no migration script, archived plans stay archival |
| 5 | Pre-ship test | Yes, against recent plans (post 2026-04-08) |
| 6 | Model location | `skills/scripts/models/` |
| 7 | Schema versioning | Validator-pinned; forensic `--schema-version N` for legacy |
| 8 | YAML/Pydantic errors | Split into separate blocks (3 distinct headers) |
| 9 | Exit codes | 0 pass / 1 producer-fix / 2 infrastructure |
| 10 | Bypass env var | `SUPERPOWERS_VALIDATOR_BYPASS=1` |
| 11 | Approach tier | Full Phase 1 + forward-compat infrastructure |

---

## Component Specifications

### `skills/scripts/models/_base.py`
Defines `CURRENT_SCHEMA_VERSION`, `StrictModel`, and `SchemaVersionedModel`. See Contract Facts above for field details. The `SchemaVersionedModel.must_match_current` field validator raises `ValueError` with an explanatory message pointing the producer at both fix options (update frontmatter OR use `--schema-version N`).

### `skills/scripts/models/plan.py`
Defines `Plan`, `Task`, `Module`, `SharedConstant`, `PatternReference`, `FeatureArchetype`. All 5 model validators are `mode="after"`. See Contract Facts for field layouts and validator descriptions.

### `skills/scripts/models/handoff.py`
Defines `HandoffPackage`, `FieldType`, `FormatRule`, `Sample`, `FieldTypeKind`. Both model validators are `mode="after"`. See Contract Facts for field layouts and validator descriptions.

### `skills/scripts/models/errors.py`
Two formatter functions:

**`format_validation_error(e: ValidationError, artifact_path: str) -> str`**
- Box-drawing border with header `VALIDATION FAILED: <path>`
- Per-error: `[N] Field: <dotted.path>`, `Problem: <msg>`, `Got: <repr(input)>`
- Conditional `Expected:` line for `literal_error` and `missing` types
- Special hint for missing `schema_version`: "Add `schema_version: 1` as the first line of your YAML frontmatter."

**`format_yaml_error(yaml_err: Exception, artifact_path: str) -> str`**
- Box-drawing border with header `YAML PARSE FAILED: <path>`
- Body: exception class name + message
- Note: "Pydantic validation was not attempted — fix the YAML first."

### `skills/scripts/models/validators.py`
CLI entry points invoked by hooks via subprocess. Two subcommands: `plan` and `handoff`.

**`plan` subcommand:**
1. Check file exists (exit 2 if not)
2. Check Pydantic importable (exit 2 if not, with install hint)
3. Check bypass env var (exit 0 with stderr warning if set)
4. Read file, check for `---` frontmatter (hard FAIL exit 1 if absent)
5. Extract YAML between `---` delimiters, parse with `yaml.safe_load()`
6. On YAML error: `format_yaml_error()` to stderr, exit 1
7. `Plan.model_validate(frontmatter_dict)`
8. On validation error: `format_validation_error()` to stderr, exit 1
9. On unexpected exception: "VALIDATOR CRASHED" message, exit 2
10. Success: exit 0

**`handoff` subcommand:**
Same as plan steps 1–9, plus:
- Step 7: `HandoffPackage.model_validate(frontmatter_dict)` (from `<package-dir>/README.md`)
- Step 7b (filesystem post-check): iterate `pkg.samples`, verify each `sample.path` resolves to existing file under `package_dir`. On failure: `SAMPLE FILE MISSING` block to stderr, exit 1

### Hook Integration (Modified Shell Scripts)
Three existing shell scripts modified to call the Python validator:

**`plan-validation-gate-hook.sh`** — wraps validator stderr in JSON:
```bash
if ! python3 -m skills.scripts.models.validators plan "$PLAN_FILE" 2>/tmp/validator-err; then
  cat <<EOF
{"decision":"block","reason":$(jq -Rs . < /tmp/validator-err)}
EOF
  exit 0
fi
```

**`check-handoff.sh`** — calls `validators.py handoff <package-dir>`

**`validate-plan.py`** — routes to Pydantic when YAML frontmatter detected; hard FAIL without it

### Prompt Template Updates (Ship Atomically With Validators)

| File | Change |
|------|--------|
| `skills/writing-plans/SKILL.md` | New section: plan files must begin with YAML frontmatter block |
| `skills/handoff-acceptance/references/handoff-package-spec.md` | Replace prose Contract Constraints template with YAML frontmatter template |
| `skills/subagent-driven-development/SKILL.md` | One-line note: plans now have YAML frontmatter |
| `CLAUDE.md` (fork root) | New section: Pydantic schema location, version bumps, bypass env var |

---

## Directory Structure (New Additions)

```
skills/scripts/models/          # NEW — shared Pydantic models
├── __init__.py
├── _base.py
├── plan.py
├── handoff.py
├── errors.py
└── validators.py

tests/fixtures/plans/           # NEW — canonical plan fixtures
├── valid/
│   ├── minimal-plan.md
│   └── full-featured-plan.md
└── invalid/
    ├── missing-required-field.md
    ├── bad-dependency.md
    └── ...

tests/fixtures/handoffs/        # NEW — canonical handoff fixtures
tests/fixtures/_smoke-test-plans/  # NEW — throwaway, deleted post-ship

tests/unit/test_models/         # NEW
├── test_plan_model.py
├── test_handoff_model.py
├── test_schema_versioning.py
└── test_error_formatter.py

tests/unit/test_validators/     # NEW
├── test_validate_plan_pydantic.py
└── test_validate_handoff_pydantic.py
```

---

## Testing Strategy

### Test Layers

| Layer | Scope | Location | Count |
|-------|-------|----------|-------|
| Model unit tests | Each Pydantic model in isolation | `tests/unit/test_models/` | ~30 |
| Cross-field validator tests | `@model_validator` invariants | `tests/unit/test_models/` | ~35 |
| CLI entry-point tests | `validators.py` subprocess interface | `tests/unit/test_validators/` | ~25 |
| Hook integration tests | Shell hooks calling Python | `tests/unit/test_hooks_pydantic.py` | ~8 |
| Pre-ship smoke test | Real recent plans vs schema | `tests/unit/test_smoke_real_plans.py` | dynamic |
| Installation verification | Pydantic import + model import | `verify-symlink-install.sh` | +2 |

### Post-Phase 1 Test Counts

| Layer | Before | After | Delta |
|-------|--------|-------|-------|
| Unit tests (pytest) | 70 | ~115 | +45 |
| Regression checks | 122 | 122 | 0 |
| Install checks | 103 | 105 | +2 |

### Installation Verification Additions
Two new checks in `verify-symlink-install.sh`:
1. Pydantic v2.7+ importable
2. Model modules (`plan`, `handoff`, `errors`, `validators`) import cleanly

### Pre-Ship Smoke Test
- Copy recent plans (post 2026-04-08) into `tests/fixtures/_smoke-test-plans/`
- Add YAML frontmatter to copies (never modify originals)
- Run `test_smoke_real_plans.py` — auto-discovers fixtures, parametrizes per fixture
- All PASS → merge. FAIL → triage as schema bug (fix) or real plan mistake (document)
- Delete `_smoke-test-plans/` in the merge commit

---

## Migration

- **Hard cutover**: no shadow mode, no batch migration, no fallback to legacy regex
- **Archived plans**: stay as-is, will hard FAIL if re-validated (expected — add frontmatter manually if needed)
- **Prompt templates + validators ship atomically**: same commit, prevents format/validator desync
- **Nothing deleted in Phase 1**: legacy regex branches kept but routed around when frontmatter present
- **Phase 7 cleanup**: delete legacy regex paths after 6+ months of Pydantic-only authoring

### Rollback Ladder
1. Fix schema, push, reinstall (typical)
2. `export SUPERPOWERS_VALIDATOR_BYPASS=1` (emergency unblock)
3. `git revert <phase-1-commit>` (nuclear)

### Cutover Procedure
1. Merge Phase 1 branch to main
2. `git pull` in fork (symlinks pick up changes)
3. `bash tests/ARaymond-installation/verify-symlink-install.sh`
4. `.venv/bin/python3 -m pytest tests/unit/ -v` + `python3 tests/ARaymond-skill-regression/validate-all-skills.py`

---

## Acceptance Criteria

- [ ] `skills/scripts/models/` exists with `__init__.py`, `_base.py`, `plan.py`, `handoff.py`, `errors.py`, `validators.py`
- [ ] `Plan` validates 5 cross-field relationships
- [ ] `HandoffPackage` validates 2 in-model cross-field relationships
- [ ] `validators.py` handoff subcommand performs filesystem post-check with `SAMPLE FILE MISSING` header
- [ ] Two base classes: `StrictModel` (nested, `extra="forbid"`) and `SchemaVersionedModel` (top-level, `schema_version` + pin)
- [ ] Only `Plan` and `HandoffPackage` inherit `SchemaVersionedModel`; all nested types inherit `StrictModel`
- [ ] Error formatter produces split YAML-parse vs Pydantic-validation blocks with field paths, expected/got, hints
- [ ] CLI supports `plan`, `handoff`, `--schema-version N` forensic flag
- [ ] CLI honors `SUPERPOWERS_VALIDATOR_BYPASS=1` (exit 0 + stderr warning with `BYPASS`)
- [ ] Exit codes: 0/1/2
- [ ] Unit test pins `err["ctx"]["expected"]` shape for `literal_error`
- [ ] `jq` availability verified in hook execution (distinct infrastructure-failure message if missing)
- [ ] `plan-validation-gate-hook.sh` invokes Python validator, wraps stderr in JSON
- [ ] `check-handoff.sh` invokes Python validator with `package_dir`
- [ ] `validate-plan.py` hard-FAILs without YAML frontmatter
- [ ] `writing-plans/SKILL.md` instructs YAML frontmatter format
- [ ] `handoff-acceptance/references/handoff-package-spec.md` updated with YAML template
- [ ] `CLAUDE.md` has Pydantic section (schema location, version bumps, bypass)
- [ ] Pydantic v2.7+ in `requirements.txt`
- [ ] `verify-symlink-install.sh` has 2 new Pydantic checks (total 105)
- [ ] ~45 new unit tests pass
- [ ] Pre-ship smoke test present with auto-discovery fixture parametrization
- [ ] `_smoke-test-plans/` populated with 5+ frontmatter-ified plans, all PASS
- [ ] `_smoke-test-plans/` deleted in merge commit
- [ ] Meta-design doc exists with all 12 sections
- [ ] All existing tests continue to pass
