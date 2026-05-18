---
schema_version: 1
feature_archetype: refactor
# enforcement_tier: standard — added by this plan's own Task 3
source_contracts: "docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/spec-distilled.md"
shared_constants:
  - path: "skills.scripts.models._base.CURRENT_SCHEMA_VERSION"
    value: "1"
    reason: "All Pydantic models pin to this version"
  - path: "skills.scripts.models.sdd_session.TIER_PROFILES"
    value: "dict mapping tier name to enforcement + process_requirements"
    reason: "Manifest writer and tests both reference the canonical tier-to-profile mapping"
pattern_references:
  - name: "checkpoint-result-model"
    source_files: ["skills/scripts/models/checkpoint_result.py"]
    reason: "Pydantic model using SchemaVersionedModel with Literal types and cross-field validators"
  - name: "plan-model"
    source_files: ["skills/scripts/models/plan.py"]
    reason: "Existing Plan model to extend with enforcement_tier and Module.file"
  - name: "validators-cli"
    source_files: ["skills/scripts/models/validators.py"]
    reason: "CLI pattern for adding session subcommand"
  - name: "sdd-hook-tests"
    source_files: ["tests/unit/test_sdd_hard_gates.py", "tests/unit/sdd_test_helpers.py"]
    reason: "Hook test patterns: make_hook_input, setup_full_sdd_workspace, subprocess invocation"
  - name: "plan-model-tests"
    source_files: ["tests/unit/test_models/test_plan_model.py"]
    reason: "Pydantic model test patterns: MINIMAL_PLAN fixtures, ValidationError assertions"
modules:
  - id: 1
    title: "Pydantic models and manifest writer"
    task_ids: [0, 1, 2, 3, 4, 5]
  - id: 2
    title: "Pre-dispatch hook rewrite"
    task_ids: [6, 7, 8, 9, 10, 11]
  - id: 3
    title: "Module transitions and controller checkpoint"
    task_ids: [12, 13, 14, 15]
  - id: 4
    title: "Skill docs, plan validation, and regression"
    task_ids: [16, 17, 18, 19, 20]
tasks:
  - id: 0
    title: "Contract verification"
    module_id: 1
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION"]
    pattern_references: ["checkpoint-result-model", "plan-model"]
  - id: 1
    title: "SddSession Pydantic model"
    module_id: 1
    depends_on: [0]
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION"]
    pattern_references: ["checkpoint-result-model"]
  - id: 2
    title: "SddSession model tests"
    module_id: 1
    depends_on: [1]
    pattern_references: ["plan-model-tests"]
  - id: 3
    title: "Plan model extension"
    module_id: 1
    depends_on: [0]
    pattern_references: ["plan-model"]
  - id: 4
    title: "Manifest writer script"
    module_id: 1
    depends_on: [1, 3]
    shared_constants_used: ["skills.scripts.models.sdd_session.TIER_PROFILES"]
  - id: 5
    title: "Manifest writer tests"
    module_id: 1
    depends_on: [4]
  - id: 6
    title: "Hook path resolution rewrite"
    module_id: 2
    depends_on: [4]
  - id: 7
    title: "Hook dispatch detection rewrite"
    module_id: 2
    depends_on: [6]
  - id: 8
    title: "Hook conditional checks by tier"
    module_id: 2
    depends_on: [7]
  - id: 9
    title: "Hook process requirements injection and dispatch log sentinel"
    module_id: 2
    depends_on: [8]
  - id: 10
    title: "Hook legacy fallback"
    module_id: 2
    depends_on: [9]
  - id: 11
    title: "Hook rewrite tests"
    module_id: 2
    depends_on: [10]
    pattern_references: ["sdd-hook-tests"]
  - id: 12
    title: "Transition-module script"
    module_id: 3
    depends_on: [4]
  - id: 13
    title: "Transition-module tests"
    module_id: 3
    depends_on: [12]
  - id: 14
    title: "Controller checkpoint --manifest support"
    module_id: 3
    depends_on: [4]
  - id: 15
    title: "Controller checkpoint tests"
    module_id: 3
    depends_on: [14]
  - id: 16
    title: "Validators CLI session subcommand"
    module_id: 4
    depends_on: [1]
    pattern_references: ["validators-cli"]
  - id: 17
    title: "validate-plan.py tier and module checks"
    module_id: 4
    depends_on: [3]
  - id: 18
    title: "SDD SKILL.md updates"
    module_id: 4
    depends_on: [4, 6]
  - id: 19
    title: "Writing-plans SKILL.md updates"
    module_id: 4
    depends_on: [3]
  - id: 20
    title: "Regression test updates"
    module_id: 4
    depends_on: [16, 17, 18, 19]
---

# Adaptive Enforcement Tiers — Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Replace SDD enforcement hooks' filesystem inference with a declared session manifest, adding tier-based enforcement profiles and module-aware transitions.

**Architecture:** Plan authors declare `enforcement_tier` in plan frontmatter. SDD ingestion materializes `.sdd-session.json` in the feature directory. Hooks read the manifest exclusively (when present), falling back to legacy filesystem inference for pre-existing sessions. A new `transition-module.py` script manages module boundary lifecycle.

**Tech Stack:** Python 3.12+ (Pydantic v2), Bash (hooks), YAML (plan frontmatter), JSON (manifest)

**Source Contracts:** `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/spec-distilled.md`

**Contract Constraints:**
- Tier values: `micro` or `standard` only (no "comprehensive")
- All manifest paths are git-root-relative
- `tier`, `enforcement`, `process_requirements` are immutable after manifest creation
- Midpoint formula: `task_range[0] + (range_size + 1) // 2`
- Micro tier: no real-time hook enforcement (intentional)
- Self-reviews must pass `validate-report.py` regardless of tier
- Task 0 (source contracts) required regardless of tier when plan has `source_contracts`
- Legacy fallback preserved when no manifest exists

**Shared Constants:**
- `CURRENT_SCHEMA_VERSION` from `skills/scripts/models/_base.py` — all models pin to this
- `TIER_PROFILES` from `skills/scripts/models/sdd_session.py` (new) — canonical tier-to-enforcement mapping

**Pattern References:**
- `skills/scripts/models/checkpoint_result.py` — Pydantic model using `SchemaVersionedModel`, `Literal` types, cross-field validators
- `skills/scripts/models/plan.py` — existing `Plan` model to extend
- `skills/scripts/models/validators.py` — CLI subcommand pattern
- `tests/unit/test_sdd_hard_gates.py` + `tests/unit/sdd_test_helpers.py` — hook test patterns
- `tests/unit/test_models/test_plan_model.py` — Pydantic model test patterns

**Feature Archetype:** Refactor (restructuring enforcement from inferred to declared)

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| New | `skills/scripts/models/sdd_session.py` | Create | imports from `_base.py` |
| New | `skills/subagent-driven-development/scripts/materialize-manifest.py` | Create | imports from `sdd_session.py` |
| New | `skills/subagent-driven-development/scripts/transition-module.py` | Create | imports from `sdd_session.py` |
| New | `tests/unit/test_models/test_sdd_session_model.py` | Create | — |
| New | `tests/unit/test_materialize_manifest.py` | Create | — |
| New | `tests/unit/test_transition_module.py` | Create | — |
| Modified | `skills/scripts/models/plan.py` | Extend `Plan` + `Module` | existing `test_plan_model.py` tests must pass |
| Modified | `skills/scripts/models/validators.py` | Add `session` subcommand | existing CLI tests |
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Major rewrite — manifest-based | all `test_sdd_*.py` tests |
| Modified | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Add `--manifest` arg | `test_controller_checkpoint_stale.py`, `test_pre_completion_gates.py` |
| Modified | `skills/subagent-driven-development/SKILL.md` | Add ingestion + transition sections | — |
| Modified | `skills/writing-plans/SKILL.md` | Add tier to template | — |
| Modified | `skills/subagent-driven-development/scripts/validate-plan.py` | Add tier + module checks | `test_validate_plan.py` |
| Modified | `tests/ARaymond-skill-regression/validate-all-skills.py` | Update check counts | — |

## Module Dependency Graph

```
Module 1 (Pydantic models + manifest writer)
  └── Module 2 (pre-dispatch hook rewrite) ← depends on Module 1
  └── Module 3 (module transitions + checkpoint) ← depends on Module 1
  └── Module 4 (skill docs + plan validation + regression) ← depends on Modules 1, 2, 3
```

Parallel candidates: Module 2 and Module 3 have disjoint write sets and both depend only on Module 1. They CAN run in parallel after Module 1 completes.

## Shared Contract Section

All modules consume the distilled spec at `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/spec-distilled.md`. The canonical tier-to-profile mapping lives in `sdd_session.py` (Module 1) and is imported by all other modules.

## Module Inventory

| Module | File | Goal | Tasks |
|--------|------|------|-------|
| 1 | `module-1-models-and-manifest.md` | Pydantic models (`SddSession`, `Plan` extension) + manifest writer script + tests | 0-5 |
| 2 | `module-2-hook-rewrite.md` | Pre-dispatch hook rewrite to read manifest, conditionalize checks, inject process requirements | 6-11 |
| 3 | `module-3-transitions-and-checkpoint.md` | `transition-module.py` + `controller-checkpoint.py` `--manifest` support + tests | 12-15 |
| 4 | `module-4-skill-docs-and-regression.md` | SDD SKILL.md, writing-plans SKILL.md, validate-plan.py, regression test updates | 16-20 |
