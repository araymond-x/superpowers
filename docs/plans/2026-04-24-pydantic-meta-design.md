# Pydantic Adoption — Meta-Design (Cross-Phase Architecture)

**Date:** 2026-04-24
**Status:** Living document — evolves across phases
**Companion phase-1 spec:** `docs/specs/2026-04-24-pydantic-phase-1-design.md`
**Authoritative inventory of candidates:** `docs/external-references/2026-04-23-pydantic-adoption-plan.md`

---

## 1. Purpose

This document captures **cross-phase architectural decisions** for the Pydantic adoption effort across the Superpowers custom fork.

**This doc IS:**
- A record of architectural decisions that apply uniformly to every Phase (1, 2, 3, ...)
- The source of truth for patterns each phase should follow
- A living document that appends per-phase lessons learned

**This doc is NOT:**
- A phase-specific design spec (those live in `docs/specs/`)
- An implementation plan (those live in `docs/imp-plans/`)
- A project roadmap (roadmap is Section 2 below, briefly)

**Lifetime:** evolves. Each completed phase updates Section 11 with a post-mortem. If a post-mortem invalidates a previously-locked decision in Sections 3–10, the relevant section is updated with a dated note explaining the change.

---

## 2. Scope Across Phases (Roadmap)

| Phase | Candidates | Status |
|-------|-----------|--------|
| 1 | A3 Plan + B4 HandoffPackage | In progress (this session) |
| 2 | A1 ImplementerReport + A2 CheckpointResult | Deferred |
| 3 | B1 DeviationsRegister + B2 HonestyCheck + B3 TraceAudit | Deferred |
| 4 | C1 SpecReview + C2 QualityReview + C3 PartnerReview | Deferred |
| 5 | C4 PlanReview + C5 PreExecutionAudit + C6 DispatchLogEntry + C7 PlanManifest + C8 ContextSummary | Deferred |
| 6 | D1 TokenEstimate + D2 DesignSpec + D2 DistilledSpec | Stretch |
| 7 | Legacy regex code cleanup | Cleanup phase |

See `docs/external-references/2026-04-23-pydantic-adoption-plan.md` for the full candidate inventory.

---

## 3. Format Pattern (Locked — Phase 1)

### 3.1 Human-Readable Artifacts
Artifacts that are primarily human-authored or human-reviewed use:
- **YAML frontmatter** (between `---` delimiters at the top of the file) for typed/structured fields
- **Markdown body** (below the frontmatter) for prose, narrative, examples, and anything a human reads

Partial overlap via indexing keys (task IDs, section references) is allowed. Full content duplication is a design bug.

**Applies to:** Plan, HandoffPackage, DesignSpec, DistilledSpec, and any future human-facing artifact.

### 3.2 Machine-Emitted Artifacts
Artifacts emitted entirely by scripts (not subagents, not humans) use **pure JSON**. No markdown, no YAML. The validator operates directly on the JSON.

**Applies to:** CheckpointResult, TokenEstimate, and any future script-emitted artifact.

### 3.3 Why NOT Mix
Choosing YAML frontmatter for machine-only artifacts would add parsing surface area for no human-readability benefit. Choosing JSON-only for human artifacts would destroy readability. Each format fits its audience.

---

## 4. Schema Versioning Policy (Locked — Phase 1)

### 4.1 Field and Constant
- Every Pydantic model descending from `SchemaVersionedModel` has a required `schema_version: int` field
- `CURRENT_SCHEMA_VERSION` is defined per module (Plan may be v3 while HandoffPackage is v1 — they're independent)
- Validator pins to the current version; producers cannot game version dispatch

### 4.2 When To Bump schema_version

| Change | Action |
|--------|--------|
| Add a required field | BUMP |
| Add an optional field with sensible default | NO BUMP |
| Tighten an enum (remove a variant) | BUMP |
| Loosen an enum (add a variant) | NO BUMP |
| Add a new `@model_validator` rule | BUMP (new rule might reject previously-valid input) |
| Rename a field | BUMP |
| Remove a field | BUMP |
| Change a field's type | BUMP |
| Add a new custom error message | NO BUMP |

Rule of thumb: if previously-valid input could now fail validation, BUMP. Otherwise don't.

### 4.3 How To Bump (Checklist)
1. Update `CURRENT_SCHEMA_VERSION` constant in the affected module
2. Update the affected Pydantic model(s)
3. Update prompt templates that reference the schema shape
4. Update fixtures under `tests/fixtures/<artifact>/`
5. Add an entry to the CHANGELOG section of this meta-design (Section 11)

### 4.4 Forensic Access to Older Versions
Validators accept `--schema-version N` as an explicit CLI flag. This opts into validating against an older model class. Used by humans for archival review, never by hooks.

**Current implementation status:** the flag is accepted; Phase 1 is version 1, so there is no older class yet. When Phase N bumps a schema, the implementation adds a keyed version dispatch.

---

## 5. Model Organization (Locked — Phase 1)

### 5.1 Location
All shared Pydantic models live in `skills/scripts/models/`:

```
skills/scripts/models/
├── __init__.py
├── _base.py              # StrictModel, SchemaVersionedModel, CURRENT_SCHEMA_VERSION
├── plan.py               # Phase 1
├── handoff.py            # Phase 1
├── errors.py             # Formatter
├── validators.py         # CLI entry
├── implementer_report.py # Phase 2
├── checkpoint_result.py  # Phase 2
├── deviations.py         # Phase 3
└── ...
```

### 5.2 Two-Base-Class Pattern (Locked — Phase 1)

`_base.py` defines two base classes with clear division of responsibility:

| Base class | For | Enforces |
|-----------|-----|----------|
| `StrictModel(BaseModel)` | **Nested types** (Task, Module, SharedConstant, FieldType, Sample, etc.) | `extra="forbid"` (unknown fields rejected) |
| `SchemaVersionedModel(StrictModel)` | **Top-level artifacts** (Plan, HandoffPackage, ImplementerReport, etc.) | Adds required `schema_version: int` + pinning check |

**Rule:** nested types inherit `StrictModel`. Top-level artifacts (things that exist as files on disk) inherit `SchemaVersionedModel`. Never make a nested type inherit `SchemaVersionedModel` — it forces verbose YAML (every list entry needs its own `schema_version` line) and conflates artifact identity with data shape.

### 5.3 Pure Model / External I/O Split (Locked — Phase 1)

Pydantic models validate **data shape only**. I/O against external state (filesystem, network, database, subprocess) lives in the caller — typically the CLI wrapper (`validators.py`) or a hook helper.

**Rationale:**
- Pure models are unit-testable without mocking filesystem / network
- Avoids Pydantic-v2 validator signature complexities around context injection
- Separates "shape is valid" from "external state agrees with shape" as distinct failure categories

**Example (Phase 1):** the `HandoffPackage` model validates that `samples` is a non-empty list of `Sample` records with `path: str`. The CLI wrapper checks that each `sample.path` exists as a file under the package directory AFTER model validation succeeds, and emits a distinct "SAMPLE FILE MISSING" error block.

### 5.4 Principles
- One file per top-level schema
- Nested models for a given schema live in the same file (e.g., `Task`, `Module`, `SharedConstant` all live in `plan.py`)
- Cross-cutting utilities (base classes, formatter, CLI) live in `_base.py`, `errors.py`, `validators.py`
- Cross-skill imports flow through `skills/scripts/models/` as a neutral location — no skill depends on another skill's scripts directly

### 5.5 Why Not Per-Skill Model Directories
Placing `Plan` in `skills/writing-plans/scripts/models/` would force `subagent-driven-development` to import from `writing-plans`, introducing directional skill coupling. The neutral shared location avoids this.

---

## 6. Validator CLI Pattern (Locked — Phase 1)

### 6.1 Entry Point
```bash
python3 -m skills.scripts.models.validators <schema> <path> [--schema-version N]
```

Where `<schema>` is one of: `plan`, `handoff`, `implementer-report`, `checkpoint`, `deviations`, ... (added as each phase ships).

### 6.2 Exit Code Convention
- `0` = validation passed
- `1` = validation failed (producer needs to fix their artifact)
- `2` = infrastructure/setup problem (missing dependency, missing file, validator crash)

Hooks route `1` and `2` differently: `1` blames the producer; `2` raises an infrastructure alarm.

### 6.3 Environment Variables
- `SUPERPOWERS_VALIDATOR_BYPASS=1` — emergency skip; exit 0 with stderr warning printed

Introduced in Phase 1. If future phases identify additional env var needs, add them here.

---

## 7. Error-Formatter Pattern (Locked — Phase 1)

### 7.1 Two Error Block Types

**YAML parse errors** (thrown by `yaml.safe_load()` before Pydantic runs):
```
═══════════════════════════════════════════════════════════════════
 YAML PARSE FAILED: <artifact_path>
 Your YAML frontmatter is syntactically invalid.
 Pydantic validation was not attempted — fix the YAML first.
═══════════════════════════════════════════════════════════════════
  <YAMLError details>
═══════════════════════════════════════════════════════════════════
```

**Pydantic validation errors**:
```
═══════════════════════════════════════════════════════════════════
 VALIDATION FAILED: <artifact_path>
 <N> issue(s) found. Fix each and re-validate.
═══════════════════════════════════════════════════════════════════
[1] Field:    <dotted.field.path>
    Problem:  <pydantic message>
    Got:      <input value>
    Expected: <schema constraint>
    Hint:     <optional custom hint>
...
═══════════════════════════════════════════════════════════════════
```

### 7.2 Special Hints
Common first-time mistakes get first-class hints:
- Missing `schema_version` → "Add `schema_version: N` as the first line of your YAML frontmatter"
- (future phases add their own as patterns emerge)

### 7.3 Hook JSON Wrapping
Hooks wrap stderr in a `{"decision":"block","reason":...}` JSON object so Claude Code surfaces the block intact to the subagent.

---

## 8. Hook Integration Pattern (Locked — Phase 1)

### 8.1 Division of Labor
- **Shell hooks** own: receiving hook events from Claude Code, extracting artifact paths, invoking subprocess, wrapping stderr in JSON, producing the `{"decision":"block","reason":...}` response
- **Python validators** own: YAML parsing, Pydantic validation, error formatting

### 8.2 Why Not Rewrite Hooks in Python
Shell hooks are the existing, tested, installed-via-settings.json entry points. Rewriting them in Python would require settings.json changes, permissions updates, and risk breaking the hook dispatch mechanism for no clear benefit. Shell-calls-Python matches what already works.

---

## 9. Test Layer Pattern (Locked — Phase 1)

### 9.1 Canonical Test Structure Per Schema

```
tests/
├── fixtures/
│   └── <artifact>/
│       ├── valid/
│       │   ├── minimal.md
│       │   └── full-featured.md
│       └── invalid/
│           ├── missing-X.md
│           └── bad-Y.md
└── unit/
    ├── test_models/
    │   ├── test_<artifact>_model.py
    │   ├── test_<artifact>_validators.py
    │   └── test_<artifact>_schema_versioning.py
    ├── test_validators/
    │   └── test_validate_<artifact>_pydantic.py
    └── test_hooks_pydantic.py
```

### 9.2 Per-Schema Test Count Target
- Model unit tests: ~15–20
- Cross-field validator tests: ~5–8 per `@model_validator` × number of validators
- CLI entry-point tests: ~10–15
- Hook integration tests: ~4
- Pre-ship smoke test: dynamic, auto-discover fixtures

Phase 1 adds ~45 tests. Future phases expected to add 20–40 each depending on schema complexity.

### 9.3 Pre-Ship Smoke Test (Per Phase)
Each phase identifies a "recent artifact corpus" (real-world examples written since the last stable template) and runs the new validator against those copies (not the originals) before merge. `tests/fixtures/_smoke-test-<artifact>/` is throwaway — deleted in the merge commit.

---

## 10. Migration Pattern For Future Phases (Locked — Phase 1)

### 10.1 Default Policy: Hard Cutover
- No shadow mode (parallel old + new validators)
- No batch migration script for archived artifacts
- Archived artifacts stay archival — never re-validated, never converted
- Cutover is atomic: validators + prompt templates + test fixtures ship in one commit

### 10.2 Rollback Ladder
In order of preference:
1. **Fix the schema, push, reinstall** — typical bug fix
2. **`export SUPERPOWERS_VALIDATOR_BYPASS=1`** — emergency unblock with stderr warning
3. **`git revert <phase-N-commit>`** — nuclear option

No rollback requires database migrations, per-project coordination, or data conversion — everything is fork-local file state.

### 10.3 Pre-Merge Gate
Each phase's pre-ship fixture smoke test (see 9.3) is a mandatory pre-merge gate. All PASS → merge. Any FAIL → triage as schema bug (fix schema) or real artifact mistake (document, don't relax schema).

### 10.4 Prompt Template + Validator Atomicity
Prompt templates and validators ship in the same commit. Decoupling creates a window where authors write in the old format but the validator expects the new — guaranteed breakage. Atomic cutover prevents this.

---

## 11. Cross-Phase Lessons Learned (Evolves)

### Phase 1 — 2026-04-24 (In Progress)
_This section will be updated post-implementation with a post-mortem._

Placeholder for:
- What worked as expected
- What needed adjustment
- Adjustments that invalidate locked decisions above (if any)
- New patterns that might generalize

### CHANGELOG of Locked-Decision Updates
_No updates yet. Each future change lands a dated entry here._

---

## 12. Open Questions Deferred To Future Phases

These were raised during Phase 1 brainstorm but intentionally not committed. They get revisited in the phase that first needs them.

### 12.1 Renderer Pattern
**Question:** Should Pydantic models have a `.to_markdown()` method, or should rendering live in a separate `renderers/` module?

**Deferred to:** Phase 2 (A1 ImplementerReport is the first schema where subagent-emission-then-human-rendering actually matters — in Phase 1, authors write YAML + markdown directly).

### 12.2 Sub-Agent Tool-Use Integration
**Question:** Should subagents emit JSON via forced tool-use (Instructor-style), or write YAML frontmatter + markdown by hand?

**Deferred to:** Phase 2 for the same reason — ImplementerReport is emitted by subagents; Plan/HandoffPackage in Phase 1 are written by skills + humans.

### 12.3 Cross-Artifact Contract Validation
**Question:** Should there be a `PlanExecutionContract` meta-model that validates relationships *between* artifacts (e.g., `Plan.contracts_implemented` must be a superset of next `Task.depends_on`)?

**Deferred to:** Phase 2+ — this is only meaningful once multiple schemas coexist at runtime and their relationships become load-bearing.

### 12.4 Hypothesis Property-Based Tests
**Question:** Should the test suite include Hypothesis-driven property tests?

**Deferred indefinitely.** Revisit if schema complexity warrants (likely not before Phase 4–5).

### 12.5 Legacy Regex Path Deletion
**Question:** When do we delete the regex fallback branches in `validate-plan.py` and `check-handoff.sh`?

**Deferred to:** Phase 7 cleanup. Prerequisite: all active authoring has been on the Pydantic path for ≥6 months with no regressions.

---

## Appendix A — Dependency Policy

### Required
- **Pydantic** `>=2.7,<3` — added to `requirements.txt` in Phase 1

### Rejected
- **Instructor** — not a fit for this architecture. The fork dispatches subagents via Claude Code's Agent tool; the harness owns the API call. Instructor wraps direct API clients, which the fork doesn't use.

### Future Consideration
- **Hypothesis** — for property-based testing, deferred (see 12.4)

---

## Appendix B — File Path Conventions

- Design specs: `docs/specs/YYYY-MM-DD-pydantic-phase-N-design.md`
- Distilled specs: `docs/specs/YYYY-MM-DD-pydantic-phase-N-design-distilled.md`
- Implementation plans: `docs/imp-plans/YYYY-MM-DD-pydantic-phase-N.md`
- This meta-design: `docs/plans/2026-04-24-pydantic-meta-design.md`
- External references: `docs/external-references/YYYY-MM-DD-<topic>.md`
