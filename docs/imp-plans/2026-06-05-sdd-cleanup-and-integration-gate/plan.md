---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: null
shared_constants: []
pattern_references:
  - name: "checkpoint-tests"
    source_files: ["tests/unit/test_pre_completion_gates.py"]
    reason: "Test patterns for pre-completion checks (Check 8/9, ratio caps, git-reality)"
  - name: "validate-plan-tests"
    source_files: ["tests/unit/test_validate_plan.py"]
    reason: "Test patterns for validate-plan.py structural checks"
  - name: "transition-tests"
    source_files: ["tests/unit/test_transition_module.py"]
    reason: "Test patterns for transition-module.py (manifest workspace, provenance, verification exemption)"
  - name: "hook-subprocess-tests"
    source_files: ["tests/unit/test_sdd_classification.py"]
    reason: "Bash hook subprocess testing patterns (make_hook_input, setup_manifest_workspace)"
  - name: "model-tests"
    source_files: ["tests/unit/test_models/test_implementer_report_model.py"]
    reason: "Pydantic model validation test patterns"
modules:
  - id: 1
    title: "Cleanup"
    task_ids: [1, 2, 3, 4, 5, 6, 7]
    file: module-1-cleanup.md
  - id: 2
    title: "C2-integration-gate"
    task_ids: [8, 9, 10, 11]
    file: module-2-integration-gate.md
tasks:
  - id: 1
    title: "N16: ImplementerReport task_type exemption"
  - id: 2
    title: "N9: _task_ids_where + _load_all_plan_contents helpers"
  - id: 3
    title: "N5+N13: Fence-aware task-header parsing"
    depends_on: [2]
  - id: 4
    title: "N7: Source Contracts None equals valid-absent"
    depends_on: [3]
  - id: 5
    title: "N12: Split file-existence from provenance gating"
  - id: 6
    title: "N17: Main-plan fallback for verification-id lookup"
    depends_on: [5]
  - id: 7
    title: "N1: Multi-error accumulation regression test"
    review_tier: minimum
  - id: 8
    title: "C2: IntegrationTest model + Plan field + path validator"
  - id: 9
    title: "C2: validate-plan.py risk-surface WARNING"
    depends_on: [8]
  - id: 10
    title: "C2: Pre-completion Check 10 integration-test gate"
    depends_on: [9]
  - id: 11
    title: "C2: Docs + e2e extension"
    depends_on: [10]
    review_tier: minimum
---

# SDD Cleanup + Integration-Test Gate — Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Close 8 enforcement-pipeline bugs (N16, N5, N7, N9, N12, N13, N17, N1) and add a new pre-completion integration-test gate (C2) as a 2-module feature.

**Architecture:** Module 1 cleans up existing enforcement scripts (controller-checkpoint.py, validate-plan.py, transition-module.py, implementer_report.py) with targeted fixes. Module 2 adds the C2 integration-test gate that consumes M1's new `_load_all_plan_contents` helper. All changes are in the SDD enforcement pipeline — no external APIs, no database, no frontend.

**Tech Stack:** Python 3.12, Pydantic v2, Bash (hooks), pytest, PyYAML

**Source Contracts:** None

**Contract Constraints:** None (internal refactor/extension of own enforcement scripts)

**Shared Constants:** None

**Pattern References:**
- `tests/unit/test_pre_completion_gates.py` — pre-completion check test patterns
- `tests/unit/test_validate_plan.py` — validate-plan structural test patterns
- `tests/unit/test_transition_module.py` — transition-module test patterns
- `tests/unit/test_sdd_classification.py` — bash hook subprocess test patterns
- `tests/unit/test_models/test_implementer_report_model.py` — Pydantic model test patterns

**Feature Archetype:** Extension

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| Modified | `skills/scripts/models/implementer_report.py` | Add `task_type` field + exempt validator | Existing tests in test_models/ |
| Modified | `skills/scripts/models/plan.py` | Add `IntegrationTest` model + `Plan.integration_test` field | validate-plan.py, controller-checkpoint.py |
| Modified | `skills/subagent-driven-development/scripts/validate-plan.py` | Fence-aware parsing + C2 WARNING | Plan-validation-gate hook |
| Modified | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Fence-aware parsing, N7 fix, N9 helpers, C2 Check 10 | Pre-dispatch hook, e2e tests |
| Modified | `skills/subagent-driven-development/scripts/transition-module.py` | N12 split + N17 main-plan fallback | e2e transition step |
| Retained | `skills/subagent-driven-development/scripts/validate-report.py` | N16 verification tested against (not modified) | Report validation in hook |
| Modified | `skills/subagent-driven-development/implementer-prompt.md` | Add `task_type` to report template | Subagent report generation |
| Modified | `skills/subagent-driven-development/SKILL.md` | N16 verification emit guidance | 5000-word ceiling |
| Modified | `skills/writing-plans/SKILL.md` | C2 integration_test docs | 5000-word ceiling |
| Modified | `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md` | N13 mkdir backport | Historical doc fix |
| New | `tests/unit/test_n16_verification_report.py` | N16 verification report validation tests | — |
| New | `tests/unit/test_fence_aware_parsing.py` | N5 fence-aware parsing tests | — |
| New | `tests/unit/test_n9_plan_loading_helpers.py` | N9 helper tests | — |
| New | `tests/unit/test_n1_multi_error_accumulation.py` | N1 regression test | — |
| New | `tests/unit/test_c2_integration_gate.py` | C2 model + Check 10 + validate-plan tests | — |

## Module Inventory

| Module | File | Goal | Tasks |
|--------|------|------|-------|
| 1 — Cleanup | `module-1-cleanup.md` | Close N16, N5+N13, N9, N7, N12, N17, N1 | 1–7 |
| 2 — C2 Integration Gate | `module-2-integration-gate.md` | Add integration-test pre-completion gate | 8–11 |

## Module Dependency Graph

```
Module 1 (Cleanup)
  └── Module 2 (C2 Integration Gate) ← depends on Module 1
      (consumes _load_all_plan_contents from N9)
```

Module 2 MUST execute after Module 1 — it imports the `_load_all_plan_contents` helper added by Task 2 (N9).

**Parallel candidates:** None — Module 2 depends on Module 1.

## Self-Hosting Hazards

This feature fixes bugs in the same enforcement scripts that gate its own SDD run. Live hooks resolve to **main** (via symlink), not the worktree.

1. **N5 (fence-blind validate-plan):** Main's `validate-plan.py` counts `### Task <digit>` at column 0 regardless of fencing. Plan and module files MUST NOT contain fenced task-header examples with real digits. Use `### Task N` (letter) or indent examples.

2. **N7 (Source Contracts: None):** Main's pre-execution gate FAILs on `Source Contracts: None`. Pre-log an accepted deviation at SDD ingestion.

3. **N16 (verification report):** Main's `validate-report.py` rejects empty `files_changed` on DONE status. Do NOT use `task_type: verification` for any task in this plan — the fix isn't live until merge.

## Shared Contract Section

No external schemas consumed by multiple modules. The internal contract between M1 and M2 is:

- M1 Task 2 (N9) adds `_load_all_plan_contents(manifest) -> list[str]` to `controller-checkpoint.py`
- M2 Task 10 (C2 Check 10) calls this helper to aggregate `integration_test` paths across parent + modules

## Execution

After Module 1, run `transition-module.py` to archive M1 reports and advance the manifest to Module 2. This 2-module execution validates the live multi-module transition path.
