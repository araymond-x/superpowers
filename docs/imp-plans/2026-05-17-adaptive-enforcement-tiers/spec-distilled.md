# Adaptive Enforcement Tiers — Distilled Implementation Spec

> **Source**: `spec.md` (v1.1 with M16 amendments, 12 resolved decisions)
> **Distilled**: 2026-05-17 (updated 2026-05-18 with Amendment 4 + dispatch log sentinel)
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

## Contract Facts

- Two enforcement tiers: `micro` and `standard` (no "comprehensive" — module support is orthogonal to tier)
- Tier is declared by the plan author in plan frontmatter `enforcement_tier: micro | standard`
- Plans without `enforcement_tier` default to `standard`
- Multi-module support activates when plan frontmatter includes `modules` with `file` fields
- SDD ingestion materializes `.sdd-session.json` in the feature directory — hooks read this exclusively when present
- `tier`, `enforcement`, and `process_requirements` in the manifest are immutable after creation
- Mutable manifest fields: `active_module_id`, `active_module_file`, `task_range`, `midpoint`, `completed_modules`, `module_reports_archived`
- Manifest is committed to git; handoff bundles include its path
- All artifact paths in manifest are git-root-relative; hook resolves via `git rev-parse --show-toplevel` (CWD-stable)
- Hook finds manifest via `$GIT_ROOT/.active-feature` → `$GIT_ROOT/$FEAT/.sdd-session.json` (not CWD-relative)
- Dispatch log has a sentinel line written by the hook on first reviewer dispatch (anti-forgery)
- Micro tier has no real-time hook enforcement (controller uses Bash/Edit, not Agent tool) — this is intentional
- Even micro-tier self-reviews must pass `validate-report.py`
- Task 0 (source contracts) is always required when plan has `source_contracts`, regardless of tier
- Midpoint formula: `task_range[0] + (range_size + 1) // 2` (matches existing 1-indexed ceiling)

## Open Decisions

| # | Decision | Options | Resolution Required By |
|---|----------|---------|----------------------|
| 1 | Is `subagent_type` available in PreToolUse hook payload? | Yes (use it) / No (fall back to description patterns) | Task implementing hook dispatch detection |

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Who declares tier | Plan author (writing-plans skill) |
| 2 | Manifest persistence | Git-committed in feature dir; handoff bundles include path |
| 3 | Module boundary handling | `transition-module.py` script (archive, update manifest, archive dispatch log) |
| 4 | Dispatch detection | Manifest-presence check (`.sdd-session.json` exists) replaces regex |
| 5 | Micro self-review quality | Must pass `validate-report.py` |
| 6 | Backward compatibility | Default to `standard`; legacy fallback when no manifest |
| 7 | Tier count | Two (micro, standard) — comprehensive folded into standard + modules |
| 8 | Dispatch log at module transition | Copy to archive, truncate original (not delete) |
| 9 | Micro pre-completion | Skip honesty check and trace audit entirely |
| 10 | `executing-plans` skill | Out of scope for v1 |
| 11 | CWD drift prevention | All paths git-root-relative in manifest `paths` object; hook resolves from `git rev-parse --show-toplevel` |
| 12 | Dispatch log forgery | Sentinel line on first reviewer dispatch; WARN (not BLOCK) if missing on implementer dispatch |

## Enforcement Profile by Tier

| Check | Micro | Standard |
|-------|-------|----------|
| Pre-execution audit | skip | required |
| Spec review | self-review | dispatched |
| Quality review | self-review | dispatched |
| Partner review | skip | dispatched |
| Dispatch provenance | skip | required |
| Context summary | skip | at midpoint (per-module if modules declared) |
| Checkpoint files | skip | required |
| Deviations log | required | required |

## Process Requirements by Tier

| Requirement | Micro | Standard |
|-------------|-------|----------|
| `subagent_dispatch` | `controller_direct` | `required` |
| `spec_review_mode` | `self_review` | `dispatched` |
| `quality_review_mode` | `self_review` | `dispatched` |
| `partner_review_mode` | `skip` | `dispatched` |
| `deviations_log` | `required` | `required` |
| `checkpoint_script` | `skip` | `required` |

## Component Specifications

### Pydantic Models (`skills/scripts/models/sdd_session.py`)

New file. Uses `SchemaVersionedModel` (from `_base.py`).

Types:
- `Tier = Literal["micro", "standard"]`
- `ReviewMode = Literal["dispatched", "self_review", "skip"]`
- `DispatchMode = Literal["required", "controller_direct"]`
- `RequirementLevel = Literal["required", "skip"]`

Models:
- `ModuleState(StrictModel)`: `id: int`, `title: str`, `file: str`, `task_ids: list[int]`
- `ArtifactPaths(StrictModel)`: `feature_dir: str`, `reports_dir: str`, `dispatch_log: str`, `deviations_file: str` — all git-root-relative
- `Enforcement(StrictModel)`: `pre_execution_audit: bool`, `partner_review: bool`, `dispatch_provenance: bool`, `context_summary_at: int | None`, `checkpoint_files: bool`
- `ProcessRequirements(StrictModel)`: `subagent_dispatch: DispatchMode`, `spec_review_mode: ReviewMode`, `quality_review_mode: ReviewMode`, `partner_review_mode: ReviewMode`, `deviations_log: RequirementLevel`, `checkpoint_script: RequirementLevel`
- `SddSession(SchemaVersionedModel)`: `tier`, `paths: ArtifactPaths`, `plan_file`, `active_module_id: int | None`, `active_module_file: str | None`, `task_range: tuple[int, int]`, `total_tasks: int`, `midpoint: int`, `enforcement: Enforcement`, `process_requirements: ProcessRequirements`, `completed_modules: list[str]`, `module_reports_archived: bool`, `modules: list[ModuleState] | None`, `dispatch_log_sentinel: bool`

### Plan Model Extension (`skills/scripts/models/plan.py`)

Modify existing file:
- Add `enforcement_tier: Tier | None = None` to `Plan` class (None = default to `standard`)
- Add `file: str | None = None` to existing `Module` class

### Manifest Writer (`skills/subagent-driven-development/scripts/materialize-manifest.py`)

New script. Reads plan frontmatter, computes enforcement profile from tier, writes `.sdd-session.json`.

Input: `--plan-file <path>` `--feature-dir <path>`
Output: `.sdd-session.json` in feature dir
Exit codes: 0 (success), 1 (validation failure), 2 (script error)

Tier-to-profile mapping is a hardcoded dict (two entries: micro, standard). Midpoint: `task_range[0] + (range_size + 1) // 2`.

Idempotent: if manifest exists and matches plan frontmatter, no-op. If plan frontmatter changed, warn and offer to re-materialize.

### Pre-Dispatch Hook (`sdd-pre-dispatch-hook.sh`)

Modify existing 634-line script. Changes:

1. **Path resolution**: `GIT_ROOT=$(git rev-parse --show-toplevel)` → `cat "$GIT_ROOT/.active-feature"` → `$GIT_ROOT/$FEAT/.sdd-session.json`. All paths from manifest's `paths` object, resolved against `$GIT_ROOT`. CWD-stable.
2. **Dispatch detection**: Replace regex with manifest-presence. If `.sdd-session.json` exists → read manifest, apply enforcement. If no → legacy fallback (preserve existing regex logic).
3. **Passthrough**: Check `tool_input.subagent_type` if available; fall back to description patterns. Reviewers logged to dispatch log and allowed.
4. **Task range validation**: Extracted task number must fall within manifest's `task_range`. Clear error if not.
5. **Conditional checks**: Each check reads manifest `enforcement.*` field and skips if not required by tier.
6. **Plan file resolution**: Read `active_module_file` or `plan_file` from manifest. No globbing.
7. **Process requirements injection**: Add manifest's `process_requirements` to `additionalContext` on every allowed dispatch.
8. **Module state validation**: If `completed_modules` non-empty and `module_reports_archived` false → block.
9. **Dispatch log sentinel**: On first reviewer dispatch, write `# sdd-hook-sentinel <sha256>` as first line of dispatch log. On implementer dispatch, WARN if sentinel missing/malformed. Set `dispatch_log_sentinel: true` in manifest.

### Module Transition Script (`transition-module.py`)

New script. Manages module boundary lifecycle.

Input: `--manifest <path>` `--completed-module <name>` `--next-module <name>`
Exit codes: 0 (complete), 1 (validation failure), 2 (script error)

Steps:
1. Validate manifest is multi-module
2. Validate all tasks in completed module have required reports (per `process_requirements`)
3. Move task reports to `reports/archive-{module-name}/`
4. Update manifest: `active_module_id`, `active_module_file`, `task_range`, `midpoint`, `completed_modules`, `module_reports_archived`
5. Copy `.dispatch-log` to archive, truncate original to empty
6. Append module-transition row to `deviations.md`

### Controller Checkpoint (`controller-checkpoint.py`)

Modify existing 1150-line script. Add `--manifest <path>` argument.

When manifest provided: read plan_file, enforcement flags, task_range, midpoint from manifest instead of arguments/globbing. When absent: fall back to existing `--plan-file` behavior.

Pre-completion: micro tier skips honesty check and trace audit.

### SDD SKILL.md Changes

Add to Plan Ingestion:
1. Read `enforcement_tier` from frontmatter
2. Call `materialize-manifest.py` to write `.sdd-session.json`
3. Display session contract to controller

Add Module Transition section for multi-module plans.

### Writing-Plans SKILL.md Changes

- Add `enforcement_tier` to plan frontmatter template
- Add tier selection guidance (micro: 1-2 tasks; standard: 3+)
- Add `file` field to module entries in modular plan template

### Plan Validation (`validate-plan.py`)

Add checks:
- `enforcement_tier` in `{micro, standard}` (or None for default)
- `micro` with >3 tasks → warn
- `modules` present with `micro` → warn
- Module `file` fields reference existing files

## Backward Compatibility

Two mechanisms:
- **Manifest present** → use manifest (new behavior)
- **Manifest absent, reports exist** → legacy fallback (existing regex + filesystem inference)
- **Manifest absent, no reports** → non-SDD session, no enforcement

Legacy regex code preserved in hook, gated behind manifest-absence.

## Files to Create

| File | Purpose |
|------|---------|
| `skills/scripts/models/sdd_session.py` | Pydantic manifest model |
| `skills/subagent-driven-development/scripts/transition-module.py` | Module transition lifecycle |
| `skills/subagent-driven-development/scripts/materialize-manifest.py` | Manifest writer |
| `tests/unit/test_sdd_session_model.py` | Manifest model tests |
| `tests/unit/test_transition_module.py` | Module transition tests |
| `tests/unit/test_materialize_manifest.py` | Manifest writer tests |

## Files to Modify

| File | Change |
|------|--------|
| `skills/scripts/models/plan.py` | Add `enforcement_tier` to `Plan`; add `file` to `Module` |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Manifest-presence detection; conditional checks; process requirements injection; git-root path resolution; dispatch log sentinel |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | `--manifest` argument; conditional checks |
| `skills/subagent-driven-development/SKILL.md` | Manifest ingestion; module transitions; controller instructions |
| `skills/writing-plans/SKILL.md` | `enforcement_tier` in template; tier guidance |
| `skills/writing-plans/scripts/validate-plan.py` | Tier + module validation |
| `skills/scripts/models/validators.py` | `session` subcommand |
| `tests/unit/test_validate_plan.py` | Tier + module tests |
| `tests/unit/test_sdd_pre_dispatch_hook.py` | Manifest-based tests |
| `tests/unit/test_controller_checkpoint.py` | `--manifest` tests |
| `tests/ARaymond-skill-regression/validate-all-skills.py` | Updated check count |

## Acceptance Criteria

- [ ] Plans declare `enforcement_tier: micro|standard` in frontmatter
- [ ] SDD ingestion materializes `.sdd-session.json` from plan frontmatter
- [ ] Pre-dispatch hook reads manifest exclusively when present
- [ ] Micro-tier skips pre-execution audit, partner review, checkpoint files
- [ ] Standard-tier identical to current behavior
- [ ] Multi-module transition via `transition-module.py`
- [ ] Plans without tier default to `standard` with legacy fallback
- [ ] Process requirements injected into `additionalContext` on every dispatch
- [ ] Self-reviews pass `validate-report.py`
- [ ] `controller-checkpoint.py` reads manifest when `--manifest` provided
- [ ] Hook resolves all paths via git root + manifest `paths` object (CWD-stable)
- [ ] Dispatch log sentinel written on first reviewer dispatch; WARN on missing sentinel
- [ ] All existing tests pass
- [ ] New tests cover manifest, tiers, hook conditionalization, transitions, path resolution, sentinel
