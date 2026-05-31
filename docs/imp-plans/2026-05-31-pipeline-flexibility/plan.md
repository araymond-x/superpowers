---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: "docs/imp-plans/2026-05-31-pipeline-flexibility/spec-distilled.md"
shared_constants: []
pattern_references:
  - name: "review-tier-model-precedent"
    source_files: ["skills/scripts/models/plan.py"]
    reason: "review_tier field shows how to add optional Literal fields to Task model"
  - name: "review-tier-test-precedent"
    source_files: ["tests/unit/test_models/test_plan_model.py"]
    reason: "TestReviewTier class shows test pattern for new optional Task fields"
  - name: "review-tier-heuristic-precedent"
    source_files: ["skills/subagent-driven-development/scripts/validate-plan.py"]
    reason: "check_review_tier_heuristic shows WARNING pattern for keyword-based checks"
  - name: "hook-task-type-parsing"
    source_files: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    reason: "3-stage classification pipeline for dispatch enforcement"
  - name: "checkpoint-pre-completion"
    source_files: ["skills/subagent-driven-development/scripts/controller-checkpoint.py"]
    reason: "Pre-completion phase check patterns (ratio checks, file-based gates)"
modules:
  - id: 1
    title: "Model and Validation"
    task_ids: [0, 1]
    file: module-1-model-and-validation.md
  - id: 2
    title: "Enforcement"
    task_ids: [2, 3, 4, 5]
    file: module-2-enforcement.md
  - id: 3
    title: "Documentation and Audit"
    task_ids: [6, 7, 8, 9]
    file: module-3-docs-and-audit.md
tasks:
  - id: 0
    title: "Plan model: add entry_mode and task_type fields"
    module_id: 1
    depends_on: []
    pattern_references: ["review-tier-model-precedent", "review-tier-test-precedent"]
  - id: 1
    title: "validate-plan: add verification keyword WARNING"
    module_id: 1
    depends_on: [0]
    pattern_references: ["review-tier-heuristic-precedent"]
  - id: 2
    title: "Hook: add task_type YAML reader and implementer dispatch logging"
    module_id: 2
    depends_on: []
    pattern_references: ["hook-task-type-parsing"]
  - id: 3
    title: "Hook: skip review checks for verification tasks"
    module_id: 2
    depends_on: [2]
    pattern_references: ["hook-task-type-parsing"]
  - id: 4
    title: "Checkpoint: add verification ratio check"
    module_id: 2
    depends_on: []
    pattern_references: ["checkpoint-pre-completion"]
  - id: 5
    title: "Checkpoint: add git reality check for verification tasks"
    module_id: 2
    depends_on: [2, 4]
    pattern_references: ["checkpoint-pre-completion"]
  - id: 6
    title: "Writing-plans SKILL.md: direct entry path and verification guidance"
    module_id: 3
    depends_on: []
    review_tier: minimum
  - id: 7
    title: "SDD SKILL.md: verification tasks documentation"
    module_id: 3
    depends_on: []
    review_tier: minimum
  - id: 8
    title: "Integration test: add verification task e2e step"
    module_id: 3
    depends_on: []
    review_tier: minimum
  - id: 9
    title: "SSOT audit investigation"
    module_id: 3
    depends_on: []
    review_tier: minimum
---

# Pipeline Flexibility Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Add direct-to-writing-plans entry mode (P1), verification/no-code task type (B6), and produce an SSOT audit findings document (N2).

**Architecture:** Extends the existing plan model with two new optional fields (`entry_mode`, `task_type`), threads `task_type` awareness through the SDD hook's classification pipeline and checkpoint pre-completion checks, enhances `writing-plans` SKILL.md with direct-entry guardrails, and adds keyword-based heuristic warnings to `validate-plan.py`. The SSOT audit is a read-only investigation task that produces a findings document.

**Tech Stack:** Python 3.12+ (Pydantic models, pytest), Bash (hook scripts), Markdown (SKILL.md documentation)

**Source Contracts:** None

**Contract Constraints:**
- Plan model `Task` uses `extra="forbid"` (via `StrictModel`) — new fields must be declared explicitly
- No schema version bump for new optional fields with defaults (precedent: `review_tier`)
- SDD SKILL.md is at 4753 words with 5000-word soft limit — additions may require extracting content to `references/`
- Dispatch log format: `task=N type={spec-review|quality-review|partner-review} ts=<ISO-8601>` — implementer entries are additive
- Hook uses `$PYTHON` for PyYAML/Pydantic scripts; system `python3` for `jq`-like operations
- `check-distillation.sh` takes a single path argument, returns JSON with `status: PASS|FAIL`

**Shared Constants:** None

**Pattern References:**
- `skills/scripts/models/plan.py` — `review_tier` field on Task (optional Literal with default, no schema version bump)
- `tests/unit/test_models/test_plan_model.py` — `TestReviewTier` class (test pattern for optional Task fields)
- `skills/subagent-driven-development/scripts/validate-plan.py` — `check_review_tier_heuristic()` (WARNING pattern for keyword-based plan checks)
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — 3-stage classification pipeline, `$PYTHON` usage, dispatch log writes
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — pre-completion phase checks (`_ratio_check`, `_declared_minimum_task_ids`)

**Feature Archetype:** Extension

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| Modified | `skills/scripts/models/plan.py` | Add `entry_mode` to Plan, `task_type` to Task | Tests: `test_plan_model.py`; Consumers: `validate-plan.py`, `materialize-manifest.py`, validators.py |
| Modified | `skills/subagent-driven-development/scripts/validate-plan.py` | Add `check_verification_keyword_heuristic()` | Tests: `test_validate_plan.py`; Called by: plan-validation-gate-hook |
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Add task_type reader, implementer logging, verification skip logic | Tests: `test_sdd_classification.py`, `test_sdd_hard_gates.py`; Called from: settings.json PreToolUse |
| Modified | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Add verification ratio + git reality check | Tests: `test_pre_completion_gates.py`; Called from: SDD skill, hook Check 5c |
| Modified | `skills/writing-plans/SKILL.md` | Enhance Step 0.5, add verification guidance | No code consumers |
| Modified | `skills/subagent-driven-development/SKILL.md` | Add Verification Tasks section | No code consumers |
| Modified | `tests/unit/test_models/test_plan_model.py` | Add tests for `entry_mode` and `task_type` | — |
| Modified | `tests/unit/test_validate_plan.py` | Add tests for verification keyword warning | — |
| Modified | `tests/unit/test_sdd_classification.py` | Add tests for task_type hook behavior | — |
| Modified | `tests/unit/test_pre_completion_gates.py` | Add tests for verification ratio + git check | — |
| Modified | `tests/integration/sdd-e2e-test.sh` | Add verification task step | — |
| Created | `docs/process-improvement-findings/2026-05-31-ssot-audit.md` | SSOT audit findings | — |
| Modified | `docs/process-improvement-findings/BACKLOG.md` | Update P1/B6/N2 status + new rows | — |

---

## Module Inventory

| Module | File | Goal | Tasks |
|--------|------|------|-------|
| 1 — Model and Validation | `module-1-model-and-validation.md` | Add `entry_mode` and `task_type` fields to Pydantic models, add verification keyword WARNING to validate-plan.py | 0-1 |
| 2 — Enforcement | `module-2-enforcement.md` | Thread `task_type` through the SDD hook and checkpoint pre-completion checks | 2-5 |
| 3 — Documentation and Audit | `module-3-docs-and-audit.md` | Update SKILL.md documentation, add integration tests, produce SSOT audit | 6-9 |

## Module Dependency Graph

```
Module 1 (Model + Validation)
  ├── Module 2 (Enforcement) ← depends on Module 1 (hook reads task_type from model)
  └── Module 3 (Docs + Audit) ← depends on Module 1 (docs reference new fields) + Module 2 (integration test needs enforcement)
```

Execution order: Module 1 → Module 2 → Module 3 (strictly sequential — shared file surface prevents parallelism).

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 0 | `skills/scripts/models/plan.py`, `tests/unit/test_models/test_plan_model.py` | `_base.py`, `sdd_session.py` | — |
| Task 1 | `validate-plan.py`, `tests/unit/test_validate_plan.py` | `plan.py` | Task 0 |
| Task 2 | `sdd-pre-dispatch-hook.sh`, `tests/unit/test_sdd_classification.py` (partial) | `plan.py` | Task 0 |
| Task 3 | `sdd-pre-dispatch-hook.sh` (cont.), `test_sdd_classification.py` (cont.) | Task 2 output | Task 2 |
| Task 4 | `controller-checkpoint.py`, `tests/unit/test_pre_completion_gates.py` (partial) | `plan.py` | Task 0 |
| Task 5 | `controller-checkpoint.py` (cont.), `test_pre_completion_gates.py` (cont.) | Task 4 output, dispatch log (Task 2) | Task 2, 4 |
| Task 6 | `skills/writing-plans/SKILL.md` | — | Task 0, 1 |
| Task 7 | `skills/subagent-driven-development/SKILL.md` | — | Task 3 |
| Task 8 | `tests/integration/sdd-e2e-test.sh` | All scripts | Task 2, 3, 4, 5 |
| Task 9 | `2026-05-31-ssot-audit.md`, `BACKLOG.md` | All 15 SKILL.md files | — |

Note: Tasks 2+3 both write `sdd-pre-dispatch-hook.sh` — strictly serialized. Tasks 4+5 both write `controller-checkpoint.py` — strictly serialized.

## Acceptance Criteria

- [x] `entry_mode` field on Plan model accepts `"brainstorming"` and `"direct"`, defaults to `"brainstorming"`
- [x] `task_type` field on Task model accepts `"implementation"` and `"verification"`, defaults to `"implementation"`
- [x] Both new fields are optional with defaults — backwards-compatible, no schema version bump
- [x] `validate-plan.py` emits WARNING for verification task titles with write-suggesting keywords
- [x] SDD hook logs implementer dispatches to dispatch log with timestamps
- [x] SDD hook reads `task_type` from plan YAML frontmatter via `$PYTHON`
- [x] SDD hook skips Check 5d (partner review) for current verification tasks
- [x] SDD hook skips Checks 4b/4c (reviews/provenance) when previous task was verification
- [x] Pre-completion verification ratio check FAILs when >30% of tasks are verification
- [x] Pre-completion git reality check detects file-modifying commits during verification task windows
- [x] `writing-plans` SKILL.md documents direct entry path with conflict detection and worktree guard
- [x] `writing-plans` SKILL.md documents verification task classification guidance
- [x] SDD SKILL.md documents verification task controller flow
- [x] Integration test covers verification task dispatch through the pipeline
- [x] SSOT audit findings document produced with BACKLOG.md rows
- [x] All existing tests pass: regression 145/3/0, unit 351, e2e 8 steps
- [x] New tests cover all changed components
