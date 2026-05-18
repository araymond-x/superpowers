# Adaptive Enforcement Tiers — Design Spec

> **Version**: 1.0
> **Date**: 2026-05-17
> **Brainstorm source**: `docs/specs/2026-05-17-adaptive-enforcement-tiers-brainstorm.md`
> **Feature directory**: `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/`
> **Feature archetype**: Refactor (restructuring enforcement from inferred to declared)

---

## 1. Overview

Replace the SDD enforcement system's filesystem inference with a declared session manifest. Plan authors declare an enforcement tier in plan frontmatter. SDD ingestion materializes this into a `.sdd-session.json` manifest that hooks read exclusively — eliminating glob/grep-based plan file resolution, regex-based dispatch detection, and the single-enforcement-profile assumption.

### Problem Summary

Five documented friction categories across 6+ SDD sessions, 3 projects:

1. **Hook regex mismatch** — dispatch descriptions that don't match `(implement|dispatch).*task\s*[0-9]` bypass enforcement entirely
2. **Small plan over-ceremony** — 1-2 task plans require ~8 structural prerequisites
3. **Skill compliance drift** — controllers silently downgrade ceremony when context budget pressure rises
4. **Minimum-tier as default** — informal tier judgments happen without a declared framework
5. **Multi-module structural assumptions** — numbering, glob resolution, module transitions all break

### Design Principle

Hooks should validate against a declared contract (the manifest), not infer state from filesystem patterns. The enforcement profile is metadata about the plan — not something to be inferred from each task dispatch.

---

## 2. Enforcement Tiers

Two tiers, declared by the plan author in plan frontmatter:

| Tier | Typical Use | Task Count Guideline |
|------|-------------|---------------------|
| `micro` | Bug fixes, config changes, 1-2 task features | 1-2 tasks |
| `standard` | All other features, including multi-module | 3+ tasks |

Task count is a guideline, not a hard rule. The plan reviewer validates tier appropriateness against overall complexity.

Multi-module support is orthogonal to tier — it activates when the plan declares a `modules` field in frontmatter, regardless of tier. A standard-tier plan with `modules` gets module transition support; a standard-tier plan without `modules` gets single-module behavior. There is no separate "comprehensive" tier because the enforcement profile is identical to standard — the only difference was module support, which is now driven by plan structure rather than tier declaration.

### Enforcement Profile by Tier

| Check | Micro | Standard |
|-------|-------|----------|
| Pre-execution audit | skip | required |
| Spec review | self-review | dispatched |
| Quality review | self-review | dispatched |
| Partner review | skip | dispatched |
| Dispatch provenance | skip | required |
| Context summary | skip | at midpoint (per-module if `modules` declared) |
| Checkpoint files | skip | required |
| Deviations log | required | required |

### Process Requirements by Tier

| Requirement | Micro | Standard |
|-------------|-------|----------|
| `subagent_dispatch` | `controller_direct` | `required` |
| `spec_review_mode` | `self_review` | `dispatched` |
| `quality_review_mode` | `self_review` | `dispatched` |
| `partner_review_mode` | `skip` | `dispatched` |
| `deviations_log` | `required` | `required` |
| `checkpoint_script` | `skip` | `required` |

**Quality bar for self-review (micro tier):** Report files must still pass `validate-report.py` (Pydantic frontmatter + 5 prose sections). Self-review allows controller-written reports; it does not allow stub/empty reports.

**Micro tier real-time enforcement limitation:** When `subagent_dispatch` is `controller_direct`, the controller executes tasks via Bash/Edit, not the Agent tool. The pre-dispatch hook only fires on Agent calls, so micro-tier sessions get no real-time hook enforcement. This is intentional — micro-tier plans trade real-time enforcement for reduced ceremony. The manifest still serves as the declared contract, and post-hoc audits (honesty checks, trace audits) can verify compliance. The `validate-report.py` quality bar on report files provides the minimum mechanical enforcement for micro-tier sessions.

---

## 3. Plan Frontmatter Extension

The writing-plans skill adds two fields to plan YAML frontmatter:

```yaml
---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard        # required — micro | standard
source_contracts: "..."
modules:                           # existing field — extended with `file` per module
  - id: 1
    title: "Core models and data layer"
    task_ids: [0, 1, 2, 3]
    file: module-1-core.md         # NEW — path to module plan file (relative to feature dir)
  - id: 2
    title: "API layer"
    task_ids: [4, 5, 6, 7, 8]
    file: module-2-api.md
# ... existing fields unchanged
---
```

### Validation Rules

- `enforcement_tier` is required on all new plans. Valid values: `micro`, `standard`. Plans without it default to `standard` (backward compatibility).
- The existing `Module` class in `plan.py` gains an optional `file: str | None` field. Existing plans without `file` per module are unaffected.
- When `modules` is present and modules have `file` set:
  - Each module's `task_ids` array must be a contiguous range of integers
  - Task ranges across modules must not overlap (existing validator `module_task_ids_are_consistent` already enforces this)
  - The union of all module task ranges must cover `[0, total_tasks - 1]`
  - `file` must reference a real `.md` file in the feature directory
- The Pydantic `Plan` model (`skills/scripts/models/plan.py`) gains `enforcement_tier` field and the existing `Module` class gains `file` field.

---

## 4. Session Manifest (`.sdd-session.json`)

### 4.1 Schema

Top-level artifact using `SchemaVersionedModel`:

```python
# skills/scripts/models/sdd_session.py

Tier = Literal["micro", "standard"]
ReviewMode = Literal["dispatched", "self_review", "skip"]
DispatchMode = Literal["required", "controller_direct"]
RequirementLevel = Literal["required", "skip"]

class ModuleState(StrictModel):
    id: int                          # from Plan.Module.id
    title: str                       # from Plan.Module.title
    file: str                        # from Plan.Module.file
    task_ids: list[int]              # from Plan.Module.task_ids

class Enforcement(StrictModel):
    pre_execution_audit: bool
    partner_review: bool
    dispatch_provenance: bool
    context_summary_at: int | None  # task number, or None to skip
    checkpoint_files: bool

class ProcessRequirements(StrictModel):
    subagent_dispatch: DispatchMode
    spec_review_mode: ReviewMode
    quality_review_mode: ReviewMode
    partner_review_mode: ReviewMode
    deviations_log: RequirementLevel
    checkpoint_script: RequirementLevel

class SddSession(SchemaVersionedModel):
    tier: Tier
    feature_dir: str
    plan_file: str
    active_module_id: int | None = None    # from ModuleState.id
    active_module_file: str | None = None  # from ModuleState.file
    task_range: tuple[int, int]  # inclusive [start, end]
    total_tasks: int
    midpoint: int
    enforcement: Enforcement
    process_requirements: ProcessRequirements
    completed_modules: list[str] = Field(default_factory=list)
    module_reports_archived: bool = False
    modules: list[ModuleState] | None = None
```

### 4.2 Lifecycle

1. **Creation**: SDD ingestion reads plan frontmatter, computes `enforcement` and `process_requirements` from tier, writes `.sdd-session.json` to the feature directory.
2. **Updates**: Only `active_module_id`, `active_module_file`, `task_range`, `midpoint`, `completed_modules`, and `module_reports_archived` are mutable. `tier`, `enforcement`, and `process_requirements` are immutable after creation.
3. **Persistence**: Committed to git in the feature directory. Handoff bundles include the manifest path. Re-materialization from plan frontmatter is the recovery path (idempotent — re-running ingestion on an existing manifest is a no-op unless the plan frontmatter changed).
4. **Cleanup**: Removed by the `finishing-a-development-branch` skill alongside other feature artifacts.

### 4.3 Materialization Logic

```python
# Pseudocode for SDD ingestion manifest writer

def materialize_manifest(plan_frontmatter, feature_dir):
    tier = plan_frontmatter.get("enforcement_tier", "standard")
    
    TIER_PROFILES = {
        "micro": {
            "enforcement": Enforcement(
                pre_execution_audit=False,
                partner_review=False,
                dispatch_provenance=False,
                context_summary_at=None,
                checkpoint_files=False,
            ),
            "process_requirements": ProcessRequirements(
                subagent_dispatch="controller_direct",
                spec_review_mode="self_review",
                quality_review_mode="self_review",
                partner_review_mode="skip",
                deviations_log="required",
                checkpoint_script="skip",
            ),
        },
        "standard": {
            "enforcement": Enforcement(
                pre_execution_audit=True,
                partner_review=True,
                dispatch_provenance=True,
                context_summary_at=midpoint,
                checkpoint_files=True,
            ),
            "process_requirements": ProcessRequirements(
                subagent_dispatch="required",
                spec_review_mode="dispatched",
                quality_review_mode="dispatched",
                partner_review_mode="dispatched",
                deviations_log="required",
                checkpoint_script="required",
            ),
        },
    }
    
    # Compute task range and midpoint
    modules = plan_frontmatter.get("modules")
    if modules:
        first_module = modules[0]
        task_range = (first_module["task_ids"][0], first_module["task_ids"][-1])
        active_module_id = first_module["id"]
        active_module_file = first_module["file"]
    else:
        task_range = (0, total_tasks - 1)
        active_module_id = None
        active_module_file = None
    
    # Midpoint: 1-indexed ceiling, matching existing hook behavior
    # (TOTAL_TASKS + 1) / 2 for full plan; adapted for task_range
    range_size = task_range[1] - task_range[0] + 1
    midpoint = task_range[0] + (range_size + 1) // 2
    
    return SddSession(
        schema_version=1,
        tier=tier,
        feature_dir=feature_dir,
        plan_file=plan_file,
        active_module_id=active_module_id,
        active_module_file=active_module_file,
        task_range=task_range,
        total_tasks=total_tasks,
        midpoint=midpoint,
        enforcement=TIER_PROFILES[tier]["enforcement"],
        process_requirements=TIER_PROFILES[tier]["process_requirements"],
        modules=[ModuleState(**m) for m in modules] if modules else None,
    )
```

---

## 5. Pre-Dispatch Hook Changes

### 5.1 Dispatch Detection (replaces regex)

Current: regex `(implement|dispatch).*task\s*[0-9]` on dispatch description.

New: Check whether `.sdd-session.json` exists in the feature directory (resolved via `.active-feature`). If present, any Agent dispatch is subject to enforcement — the hook reads the manifest and applies tier-appropriate checks.

**Passthrough logic**: The hook reads `tool_input.subagent_type` from the JSON payload. **Implementation note**: Verify that `subagent_type` is exposed in the PreToolUse hook payload via `claude-code-guide` before implementation — if not available, fall back to description-based detection with the reviewer patterns. Non-implementer dispatches are handled as follows:

- `subagent_type` is `Explore`, `general-purpose`, `Plan`, `debugger`, or any non-default type → pass through without enforcement
- `subagent_type` is absent/default AND description matches reviewer patterns → log to dispatch log, then allow (preserves current reviewer provenance tracking)
- `subagent_type` is absent/default AND description doesn't match reviewer patterns → treat as implementer dispatch, apply enforcement

This uses structured fields from the hook payload rather than regex on description text, avoiding the same fragility the manifest approach eliminates from plan file resolution. The reviewer description patterns remain as a secondary check only for dispatch log provenance — they don't gate enforcement.

### 5.2 Task Number Extraction

Current: Extracted from dispatch description via `grep -oiE 'task\s*[0-9]+'`.

New: Still extracted from description (the description must reference a task number for the hook to know which task's prerequisites to check). But the hook validates the extracted number against the manifest's `task_range` — if the number falls outside the range, the hook emits a clear error referencing the manifest's expected range instead of silently mismatching.

### 5.3 Check Conditionalization

Each check reads the manifest and skips if the tier doesn't require it:

| Current Check | Manifest Field | Behavior |
|---------------|---------------|----------|
| Check 2 (pre-execution audit) | `enforcement.pre_execution_audit` | Skip if `false` |
| Check 4 (N-1 reports) | Always runs | Validates against `task_range` — task at `task_range[0]` has no N-1 requirement |
| Check 4b (report validation) | Always runs | Even self-reviews must pass `validate-report.py` |
| Check 4c (dispatch provenance) | `enforcement.dispatch_provenance` | Skip if `false` |
| Check 5 (Task 0 / source contracts) | Plan's `source_contracts` field | Always required when plan has `source_contracts` (regardless of tier). Task 0 is a plan task, not an audit gate — even micro-tier plans with source contracts need contract verification. |
| Check 5c (checkpoint file) | `enforcement.checkpoint_files` | Skip if `false` |
| Check 5d (partner review) | `enforcement.partner_review` | Skip if `false` |
| Check 6 (token estimation) | Always runs | Reads `active_module_file` from manifest instead of globbing |
| Check 6b (context summary) | `enforcement.context_summary_at` | Skip if `null`; use manifest's `midpoint` instead of computing |

### 5.4 Plan File Resolution

Current: Glob `$FEAT/*.md`, grep for `### Task N`, break on first match.

New: Read `active_module_file` (or `plan_file` for single-module plans) directly from the manifest. No globbing.

### 5.5 Process Requirements Injection

On every allowed dispatch, inject the manifest's `process_requirements` into `additionalContext`:

```
SDD SESSION CONTRACT (from .sdd-session.json):
- Tier: standard
- Subagent dispatch: required (do NOT execute tasks directly)
- Spec review: dispatched (dispatch subagent, do NOT self-write)
- Quality review: dispatched
- Partner review: dispatched
- Deviations log: required
- Checkpoint script: required
```

This makes the declared contract visible to the controller on every dispatch, addressing compliance drift by persistent reminder.

---

## 6. Module Transition Protocol

New script: `skills/subagent-driven-development/scripts/transition-module.py`

### 6.1 Invocation

```bash
python3 ~/.claude/skills/superpowers/subagent-driven-development/scripts/transition-module.py \
  --manifest <feature-dir>/.sdd-session.json \
  --completed-module module-1-core \
  --next-module module-2-api
```

### 6.2 Steps

1. **Validate manifest**: Read `.sdd-session.json`, confirm it's a multi-module plan
2. **Validate completion**: For each task in the completed module's range, verify required report files exist:
   - `task-NNN-implementer-report.md` (pass `validate-report.py`)
   - `task-NNN-spec-review.md` (if `spec_review_mode != "skip"`)
   - `task-NNN-quality-review.md` (if `quality_review_mode != "skip"`)
3. **Archive reports**: Move completed module's task reports to `reports/archive-{module-name}/`. Preserve non-task-specific files (pre-execution-audit, context-summary) in the main reports directory.
4. **Update manifest**:
   - `active_module_id` → next module's id
   - `active_module_file` → next module's file path
   - `task_range` → next module's task range
   - `midpoint` → computed from new task range
   - `completed_modules` → append completed module name
   - `module_reports_archived` → `true`
5. **Archive dispatch log**: Copy `.dispatch-log` to `reports/archive-{module-name}/.dispatch-log`, then truncate the original to an empty file (not deleted — the hook appends entries, so it must exist). The archived log preserves provenance for the completed module; the truncated log gives the new module a clean start.
6. **Log transition**: Append a module-transition row to `deviations.md`

### 6.3 Exit Codes

- `0` — Transition complete
- `1` — Validation failure (missing reports, module not found in manifest)
- `2` — Script error (bad arguments, manifest not found)

### 6.4 Hook Integration

The pre-dispatch hook validates module state consistency:
- If `completed_modules` is non-empty and `module_reports_archived` is `false`, block with a message directing the controller to run `transition-module.py`
- If the extracted task number falls outside `task_range`, block with a message showing the expected range

---

## 7. Controller Checkpoint Changes

`controller-checkpoint.py` gains a `--manifest` argument that replaces `--plan-file`:

### 7.1 Pre-execution Phase

- Reads `plan_file` from manifest instead of `--plan-file` argument
- Reads `enforcement` to determine which checks to run
- Skips stale artifact detection for `completed_modules` (those are intentionally archived)

### 7.2 Pre-dispatch Phase

- Reads `task_range` to validate the task number is in scope
- Reads `active_module_file` for task header lookup instead of globbing
- Uses manifest's `midpoint` for context summary check
- Conditionally runs checks based on `enforcement` flags

### 7.3 Pre-completion Phase

- Reads `process_requirements` to determine minimum review ratio thresholds
- For micro tier: skip honesty check and trace audit entirely. Micro-tier plans have no real-time enforcement and reduced ceremony — adding post-hoc audits would reintroduce the overhead that micro tier is designed to avoid.
- For standard: unchanged behavior

### 7.4 Backward Compatibility

When `--manifest` is not provided but `--plan-file` is, fall back to current behavior. This allows existing SDD sessions without a manifest to continue working during migration.

---

## 8. SDD Skill Changes

### 8.1 Plan Ingestion

Add to the ingestion flow (after reading the plan, before creating TodoWrite):

1. Read `enforcement_tier` from plan frontmatter (default: `standard` if absent)
2. Read `modules` from plan frontmatter (if present)
3. Compute enforcement profile and process requirements from tier
4. Write `.sdd-session.json` to the feature directory
5. If `.sdd-session.json` already exists (resume scenario), validate it matches the plan frontmatter. If not, warn and offer to re-materialize.

### 8.2 Controller Instructions

Add to the SDD controller's visible instructions (the part the controller reads at session start):

> **Session manifest**: This session is governed by `.sdd-session.json` in the feature directory. Your enforcement tier is `{tier}`. Process requirements are:
> - Subagent dispatch: `{subagent_dispatch}`
> - Spec review: `{spec_review_mode}`
> - Quality review: `{quality_review_mode}`
> - Partner review: `{partner_review_mode}`
> 
> These requirements are immutable — declared at planning time, not execution time.

### 8.3 Module Transitions

Add to the SDD process flow (after task loop, before completion):

> **Module transition** (multi-module plans only): When all tasks in the current module are complete, run `transition-module.py` before starting the next module. Do not manually archive reports or update the manifest.

---

## 9. Writing-Plans Skill Changes

### 9.1 Plan Template

Add `enforcement_tier` to the plan template as a required field:

```markdown
---
schema_version: 1
feature_archetype: <archetype>
enforcement_tier: <micro|standard>
source_contracts: <contracts or "None">
...
---
```

### 9.2 Tier Selection Guidance

Add to the writing-plans skill (after task decomposition, before writing the plan):

> **Enforcement tier selection**: Based on the plan's task count and complexity:
> - **micro** (1-2 tasks): Bug fixes, config changes, simple additions. Self-review OK, no partner review, no real-time hook enforcement.
> - **standard** (3+ tasks): Typical features and multi-module plans. Full two-stage review, partner review, checkpoint files. Multi-module support activates when `modules` is declared in frontmatter.
>
> Task count is a guideline. The plan reviewer validates tier appropriateness.

### 9.3 Module Declaration

For modular plans, the writing-plans skill already produces module files. Add the `modules` field to the parent plan's frontmatter with file references and task ranges.

---

## 10. Plan Validation Changes

### 10.1 validate-plan.py

Add checks for:
- `enforcement_tier` is a valid value (`micro`, `standard`)
- If `modules` is present, task ranges don't overlap and cover all tasks
- If `enforcement_tier` is `micro` and task count > 3, warn (tier may be too low)
- If `modules` is present and `enforcement_tier` is `micro`, warn (multi-module plans typically need standard enforcement)

### 10.2 plan-validation-gate-hook.sh

No structural changes. The gate continues to run `validate-plan.py` — the new validation rules are added there, not in the hook.

---

## 11. Backward Compatibility

### Two Mechanisms (Distinct Triggers)

**Mechanism A — Default tier for new plans**: Plans that go through SDD ingestion but lack `enforcement_tier` in frontmatter get `standard` by default. A manifest IS created with standard-tier enforcement. This applies to all newly-authored plans going forward.

**Mechanism B — Legacy fallback for in-flight sessions**: SDD sessions already in progress (pre-existing feature directories with reports but no `.sdd-session.json`) continue using the current filesystem inference. No manifest is created; the hook detects the absence of a manifest and runs legacy logic (including the existing regex-based dispatch detection). The legacy code path is preserved in the hook, gated behind the manifest-absence check. This applies only to sessions that were started before this feature ships.

When each fires:
- `.sdd-session.json` exists → use manifest (Mechanism A behavior)
- `.sdd-session.json` absent AND `.active-feature` points to a dir with `reports/` → legacy fallback (Mechanism B)
- `.sdd-session.json` absent AND no active feature / no reports → no SDD enforcement (non-SDD session)

### Migration Path

- `controller-checkpoint.py` accepts both `--manifest` and `--plan-file` (manifest takes precedence)
- No existing plans or in-flight SDD sessions break

### Deprecation Timeline

- v1.0: Manifest and tiers are opt-in. Legacy inference is the fallback.
- v1.1: Emit deprecation warnings when hooks fall back to legacy mode.
- v2.0 (future): Remove legacy inference. All SDD sessions require a manifest.

---

## 12. Testing Strategy

### 12.1 Pydantic Model Tests (unit)

- `SddSession` validation: valid/invalid tiers, task ranges, module consistency
- `Enforcement` and `ProcessRequirements`: tier-to-profile mapping
- Immutability: verify `tier`, `enforcement`, `process_requirements` can't be changed after creation
- Backward compatibility: missing `enforcement_tier` defaults to `standard`

### 12.2 Manifest Writer Tests (unit)

- Single-module plan → correct manifest
- Multi-module plan → correct manifest with module state
- Plan without `enforcement_tier` → `standard` default
- Idempotent re-materialization

### 12.3 Pre-Dispatch Hook Tests (unit — extend existing test suite)

- Manifest-presence detection (replaces regex tests)
- Passthrough allowlist (Explore agents, reviewers)
- Tier-conditional check skipping (micro skips partner review, etc.)
- Task range validation (out-of-range task number → clear error)
- Process requirements injection in `additionalContext`
- Legacy fallback (no manifest → current behavior)

### 12.4 Transition-Module Tests (unit)

- Validates completion before allowing transition
- Archives reports to correct subdirectory
- Updates manifest fields correctly
- Resets dispatch log for new module
- Rejects transition when reports are missing
- Rejects transition for single-module plans

### 12.5 Controller Checkpoint Tests (unit — extend existing)

- `--manifest` argument reads from manifest
- Conditional check execution based on enforcement flags
- Backward compatibility: `--plan-file` without `--manifest`

### 12.6 Regression Tests (extend validate-all-skills.py)

- Plan frontmatter includes `enforcement_tier` in template
- SDD SKILL.md references manifest ingestion
- Manifest schema file exists and is importable

### 12.7 Behavioral Tests

- End-to-end: micro-tier plan → SDD ingestion → dispatch with reduced ceremony
- End-to-end: multi-module plan → ingestion → module transition → continued dispatch
- End-to-end: standard plan without `enforcement_tier` → legacy fallback works

---

## 13. Acceptance Criteria

- [ ] Plans can declare `enforcement_tier: micro|standard` in frontmatter
- [ ] SDD ingestion materializes `.sdd-session.json` from plan frontmatter
- [ ] Pre-dispatch hook reads manifest exclusively when present (no glob/grep inference)
- [ ] Micro-tier plans can dispatch tasks without pre-execution audit, partner review, or checkpoint files
- [ ] Standard-tier plans have identical enforcement to current behavior
- [ ] Multi-module plans can transition between modules via `transition-module.py`
- [ ] Plans without `enforcement_tier` default to `standard` with legacy fallback
- [ ] Process requirements are injected into `additionalContext` on every allowed dispatch
- [ ] Self-reviews (micro tier) must pass `validate-report.py`
- [ ] `controller-checkpoint.py` reads from manifest when `--manifest` is provided
- [ ] All existing unit tests pass (backward compatible)
- [ ] New unit tests cover manifest schema, tier profiles, hook conditionalization, and module transitions
- [ ] Regression test suite (validate-all-skills.py) passes with updated check count
- [ ] Installation verification (verify-symlink-install.sh) passes with updated script count

---

## 14. Files to Create or Modify

### New Files
| File | Purpose |
|------|---------|
| `skills/scripts/models/sdd_session.py` | Pydantic model for `.sdd-session.json` |
| `skills/subagent-driven-development/scripts/transition-module.py` | Module transition lifecycle script |
| `skills/subagent-driven-development/scripts/materialize-manifest.py` | Manifest writer (called from SDD ingestion) |
| `tests/unit/test_sdd_session_model.py` | Unit tests for manifest Pydantic model |
| `tests/unit/test_transition_module.py` | Unit tests for module transition script |
| `tests/unit/test_materialize_manifest.py` | Unit tests for manifest materialization |

### Modified Files
| File | Change |
|------|--------|
| `skills/scripts/models/plan.py` | Add `enforcement_tier` field to `Plan` model; add `file` field to existing `Module` class |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Replace regex dispatch detection with manifest-presence; conditionalize checks by tier; inject process requirements |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Add `--manifest` argument; read enforcement flags from manifest |
| `skills/subagent-driven-development/SKILL.md` | Add manifest ingestion step; add module transition instructions; add tier-based controller instructions |
| `skills/writing-plans/SKILL.md` | Add `enforcement_tier` to plan template; add tier selection guidance |
| `skills/writing-plans/scripts/validate-plan.py` | Add tier and module validation rules |
| `skills/scripts/models/validators.py` | Add `session` subcommand for manifest validation |
| `tests/unit/test_validate_plan.py` | Add tests for tier and module validation |
| `tests/unit/test_sdd_pre_dispatch_hook.py` | Add manifest-based dispatch detection tests; tier-conditional tests |
| `tests/unit/test_controller_checkpoint.py` | Add `--manifest` argument tests |
| `tests/ARaymond-skill-regression/validate-all-skills.py` | Update check count for new plan frontmatter fields |

---

## 15. Out of Scope

### `executing-plans` skill

The `executing-plans` skill (parallel-session plan execution) is out of scope for v1. It has a different execution model (no SDD controller, no subagent dispatch loop) and doesn't use the pre-dispatch hook. If `executing-plans` sessions need tier-aware enforcement in the future, they can read the manifest independently — the manifest schema is designed to be consumed by any execution skill, not just SDD.

### Honesty check / trace audit changes

The existing honesty check (9 questions) and trace audit (`extract-execution-trace.py`) are unchanged. They already compare actual behavior against expected process — the manifest gives them a more precise "expected" to compare against, but no code changes are needed. The post-hoc audit improvement is a natural consequence of the manifest existing, not a deliverable.

---

## 16. Deferred Features

See `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/deferred-features.md` for the full list:

- v1.1: Computed tier recommendation heuristics
- v1.1: Context budget estimation integration
- v1.1: Per-module context summaries
- v1.1: Dispatch pattern customization
- Future: Cross-artifact validation (Pydantic Phase 3)
