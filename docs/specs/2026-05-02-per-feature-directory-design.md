# Per-Feature Directory Migration — Design Spec

> **Version**: 1.1
> **Date**: 2026-05-02
> **Status**: Draft (post-review, 9 issues resolved)
> **Archetype**: Migration (phased transition from flat to nested artifact layout)

## Problem Statement

Superpowers execution artifacts are scattered across the project root — `DEVIATIONS.md` at root, `reports/` at root, specs in `docs/specs/`, plans in `docs/imp-plans/`. This causes:

1. **Cross-contamination between features**: The plan-validation-gate hook validated old February plans alongside the current feature because all plans live in the same flat directory. This motivated the `plan-manifest.txt` scoping workaround.
2. **Stale artifact conflicts**: Starting a new feature without cleaning up the prior one's artifacts creates ambiguity about which `reports/` and `DEVIATIONS.md` belong to which feature.
3. **No self-contained feature record**: Understanding what happened during a feature's implementation requires piecing together files from 4+ locations.
4. **Naming drift**: Feature names are inferred independently by brainstorming (spec filename), writing-plans (plan filename), and worktrees (branch/directory name). These can and do diverge.

## Design Overview

Consolidate all Superpowers artifacts for a feature into a single self-contained directory at `docs/imp-plans/YYYY-MM-DD-<feature-name>/`. Introduce an `.active-feature` file at project root as the canonical pointer to the active feature directory — read by all hooks, created by entry-point skills, cleaned up by the finishing skill.

## Decision Log

| # | Decision | Options Considered | Chosen | Rationale |
|---|----------|--------------------|--------|-----------|
| 1 | Artifact consolidation strategy | (A) Move everything into per-feature dirs, (B) Move only execution artifacts, keep specs/plans flat | A — Move everything | Full self-containment eliminates cross-contamination; one directory = one feature's complete record |
| 2 | Migration approach | (A) Hard cutover, (B) Incremental with backwards compat layer | A — Hard cutover | Backwards compat adds complexity to every hook (check both locations). Single coordinated change is cleaner. Hooks include a fallback to root-level paths for projects that haven't adopted the new layout yet. |
| 3 | Feature directory discovery mechanism | (A) Manifest search + branch matching, (B) Environment variable, (C) Marker file, (D) `.active-feature` file (explicit path) | D — `.active-feature` file | Mirrors the POC's explicit-argument pattern. Survives session restarts, works with stop hooks, works identically on main and in worktrees. Eliminates auto-discovery ambiguity. |
| 4 | Feature name establishment | (A) Inferred from context, (B) User prompted at entry-point skill | B — User prompted | With per-feature directories, the name is structural — it determines the directory path. Agent suggests a name, user confirms or overrides. Eliminates naming drift across skills. |
| 5 | `.active-feature` git status | (A) Committed, (B) Gitignored | B — Gitignored | It's workspace state, not project state. Committing it would cause merge conflicts between branches, leave stale pointers after merge, and conflict between worktrees. |
| 6 | Cleanup mechanism | (A) Manual, (B) Automated via finishing skill + conflict detection at entry | B — Automated | User explicitly requested no manual steps. Two-layer: finishing skill cleans up on happy path, entry-point skills detect stale `.active-feature` on forgotten path. |
| 7 | `.allow-main` relationship | (A) Enhance `.allow-main` to carry feature dir, (B) Keep `.allow-main` as-is, introduce separate `.active-feature` | B — Separate files | `.allow-main` keeps its single purpose (branch safety opt-in). `.active-feature` works identically on main and feature branches — no branching logic in hooks. |
| 8 | Enforcement via existing gates | (A) New dedicated gates, (B) Extend existing gates | B — Extend existing | plan-validation-gate adds `.active-feature` existence check. sdd-pre-dispatch updates path resolution. Path resolution IS consistency enforcement — artifacts in the wrong location become invisible to gates. |

## Feature Directory Structure

```
docs/imp-plans/YYYY-MM-DD-<feature-name>/
  ├── spec.md                          # full design spec (from brainstorming)
  ├── spec-distilled.md                # distilled spec (for implementation agents)
  ├── plan.md                          # parent implementation plan
  ├── module-N-<name>.md               # module plans (if modular)
  ├── plan-manifest.txt                # scoping file (paths relative to this dir)
  ├── plan-review-report.md            # plan review output
  ├── deviations.md                    # execution deviations register
  └── reports/
      ├── pre-execution-audit.md
      ├── pre-execution-audit-self-assessment.md
      ├── task-NNN-implementer-report.md
      ├── task-NNN-spec-review.md
      ├── task-NNN-quality-review.md        # or task-NNN-quality-review-minimum-tier.md
      ├── partner-review-NNN.md             # or partner-review-NNN-minimum-tier.md
      ├── checkpoint-pre-dispatch-NNN.json
      ├── context-summary.md
      ├── honesty-check-YYYY-MM-DD.md
      ├── execution-trace.json
      ├── execution-trace-audit.md
      ├── .dispatch-log
      └── archive-<prior-run>/              # if SDD re-run on same feature

### Archival Within a Feature Directory

When SDD is re-invoked on a feature that already has completed reports (e.g., re-running after a failed attempt), the existing reports must be archived before the new run begins. The SDD skill's Plan Ingestion step handles this:

1. Detect existing `task-NNN-*.md` files in `<feature-dir>/reports/`
2. Create `<feature-dir>/reports/archive-<timestamp>/`
3. Move all existing task reports, checkpoint files, dispatch log, and context summary into the archive
4. `deviations.md` is archived as `<feature-dir>/reports/archive-<timestamp>/deviations.md` and a fresh one is created

This is the same mechanism as the current root-level archival (`reports/archive-<prior-feature>/`), scoped to the feature directory instead of the project root.
```

### Naming Convention

- Date prefix: `YYYY-MM-DD` — date brainstorming or planning started
- Feature name: kebab-case, chosen by user at entry-point prompt
- `deviations.md` is lowercase (no longer at root, doesn't need to stand out)
- Report filenames unchanged (task-NNN zero-padded, same naming convention)

### Artifact Migration Map

| Artifact | Old Location | New Location |
|----------|-------------|-------------|
| Design specs | `docs/specs/YYYY-MM-DD-*-design.md` | `<feature-dir>/spec.md` |
| Distilled specs | `docs/specs/YYYY-MM-DD-*-distilled.md` | `<feature-dir>/spec-distilled.md` |
| Plans | `docs/imp-plans/YYYY-MM-DD-*.md` | `<feature-dir>/plan.md` + `module-N-*.md` |
| Plan manifest | `docs/imp-plans/plan-manifest.txt` | `<feature-dir>/plan-manifest.txt` |
| Plan review | `docs/imp-plans/plan-review-report.md` | `<feature-dir>/plan-review-report.md` |
| Deviations register | `DEVIATIONS.md` (project root) | `<feature-dir>/deviations.md` |
| All execution reports | `reports/` (project root) | `<feature-dir>/reports/` |
| `.allow-main` | Project root | **Unchanged** — not feature-scoped |

## `.active-feature` File

### Format

Single-line plaintext file at project root containing the relative path to the active feature directory:

```
docs/imp-plans/2026-05-02-pydantic-phase-2
```

No YAML, no JSON. Hooks read it with `cat .active-feature`. Added to `.gitignore`.

### Lifecycle

#### Creation (Entry-Point Skills)

Three skills can create `.active-feature`:

| Skill | When | Behavior |
|-------|------|----------|
| **brainstorming** | After 1-2 clarifying questions (scope is clear) | Suggests feature name from context, user confirms or overrides. Creates directory + `.active-feature`. If brainstorming is abandoned before producing a spec, the empty feature directory and `.active-feature` are cleaned up by the next entry-point skill's conflict detection. |
| **writing-plans** | At start, if no `.active-feature` exists | Same prompt — covers the case where brainstorming was skipped. |
| **handoff-acceptance** | When verdict is ACCEPTED and work starts a new feature | Same prompt. |

The feature name prompt:

> "All artifacts for this work will be organized under a feature directory. I suggest: **`<suggested-name>`**. Press enter to accept, or type a different name."

The skill derives its suggestion from available context — spec title, user's initial description, or handoff package name.

On creation, the skill:
1. Creates `docs/imp-plans/YYYY-MM-DD-<feature-name>/`
2. Writes the relative path to `.active-feature`
3. All subsequent artifact writes target this directory

#### Conflict Detection (Entry-Point Skills)

When an entry-point skill starts and `.active-feature` already exists:

| State | Action |
|-------|--------|
| Feature dir doesn't exist (stale pointer) | Auto-clean `.active-feature`, proceed with new feature |
| Feature dir exists, all plan tasks completed | Auto-clean `.active-feature`, proceed with new feature. Completion is detected by counting `### Task N` headers in `plan.md` and verifying a matching `task-NNN-implementer-report.md` exists for each. |
| Feature dir exists, has incomplete work | Prompt: *"You have an active feature '<name>' with unfinished tasks. (A) Resume it (B) Archive it and start fresh"* |
| Feature dir exists, no plan yet (only spec) | Prompt: *"You have an incomplete feature setup for '<name>'. (A) Resume it (B) Start fresh"* |

"Archive" removes `.active-feature` only. The feature directory persists as historical record.

#### Cleanup

| Trigger | Who | What |
|---------|-----|------|
| Normal completion | `finishing-a-development-branch` | Removes `.active-feature` + `.allow-main` (if present) after any of its 4 options complete |
| User forgot to finish, starts new work | Entry-point skill conflict detection | Prompts to archive or resume (see above) |
| Completed feature, never ran finishing skill | Entry-point skill auto-clean | Detects all tasks done, auto-removes `.active-feature` |

#### Gate Enforcement

`plan-validation-gate-hook.sh` adds one check: `.active-feature` must exist before SDD/executing-plans can start. Blocks with message directing user to establish feature name via an entry-point skill.

## Hook Script Changes

All hooks change the same way: read `.active-feature` after `cd "$CWD"`, use its content as a path prefix.

### Common Preamble

Added to each hook after CWD resolution:

```bash
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi
```

When `$FEAT` is empty (no `.active-feature`), hooks fall back to root-level paths. This provides backwards compatibility for projects not using per-feature directories.

### `sdd-pre-dispatch-hook.sh`

~30 path references change. Key transformations:

| Check | Current Path | New Path |
|-------|-------------|----------|
| Check 1: Branch safety | `[ -d "reports" ] && [ -f "DEVIATIONS.md" ]` | `[ -d "$FEAT/reports" ] && [ -f "$FEAT/deviations.md" ]` |
| Check 1: `.allow-main` | `[ ! -f ".allow-main" ]` | **Unchanged** (remains at root) |
| Check 2: Audit | `reports/pre-execution-audit*` | `$FEAT/reports/pre-execution-audit*` |
| Check 3: Deviations | `DEVIATIONS.md` | `$FEAT/deviations.md` |
| Check 3: Reports dir | `reports/` | `$FEAT/reports/` |
| Check 3b: Naming | `reports/*.md` | `$FEAT/reports/*.md` |
| Check 4: Task reports | `reports/task-NNN-*` | `$FEAT/reports/task-NNN-*` |
| Check 4c: Dispatch log | `reports/.dispatch-log` | `$FEAT/reports/.dispatch-log` |
| Check 5: Plan search | `docs/imp-plans/*.md docs/plans/*.md` | `$FEAT/*.md` |
| Check 5b: Deviations | `DEVIATIONS.md` | `$FEAT/deviations.md` |
| Check 5c: Checkpoint | `reports/checkpoint-pre-dispatch-NNN.json` | `$FEAT/reports/checkpoint-pre-dispatch-NNN.json` |
| Check 5d: Partner review | `reports/partner-review-NNN.md` | `$FEAT/reports/partner-review-NNN.md` |
| Check 6: Token estimate | `docs/imp-plans/*.md docs/plans/*.md` | `$FEAT/*.md` |
| Check 6b: Context summary | `reports/context-summary.md` | `$FEAT/reports/context-summary.md` |
| Check 7: Context load | Sum of plans + deviations + reports | Same files, `$FEAT`-prefixed |
| Reviewer logging | `reports/.dispatch-log` | `$FEAT/reports/.dispatch-log` |
| `task_report_glob()` | `reports/task-${padded}-${type}*` | `$FEAT/reports/task-${padded}-${type}*` |
| Error/advisory messages | Hardcoded paths in BLOCKED strings and SDD REMINDER `additionalContext` | Dynamically interpolate `$FEAT/` prefix into all user-facing path strings when `$FEAT` is non-empty |

**Note on Check 5 (Source Contracts):** The plan search change from `docs/imp-plans/*.md docs/plans/*.md` to `$FEAT/*.md` intentionally scopes the Source Contracts search to the current feature only. This eliminates false Task 0 requirements caused by Source Contracts in prior features' plans — a documented pain point under the flat layout. Implementers should NOT add back the old multi-directory search.

### `plan-validation-gate-hook.sh`

| Aspect | Current | New |
|--------|---------|-----|
| Manifest discovery | Search `docs/imp-plans/plan-manifest.txt`, then `find -maxdepth 2` | If `.active-feature`: go directly to `$FEAT/plan-manifest.txt`. Else: existing search as fallback. |
| Review report | `find $dir -name "*plan-review-report*"` | `$FEAT/plan-review-report.md` |
| New gate | N/A | Block if no `.active-feature` when SDD/executing-plans invoked |
| `SUPERPOWERS_ROOT` resolution | Not present (hardcoded absolute paths) | Add self-resolution preamble (same pattern as `sdd-pre-dispatch-hook.sh`). Replace hardcoded `VALIDATE_PLAN_SCRIPT` with `$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/validate-plan.py`. |
| Pydantic validator python | `.venv/bin/python3` (project venv) | `$PYTHON` resolved from `$SUPERPOWERS_ROOT/.venv/bin/python3` (superpowers venv) |

### `sdd-report-guard.sh`

The detection regex on line 40 (`grep -qiE 'reports/task-'`) matches the substring anywhere — works for both old and new paths.

However, the suspicious-pattern regexes on line 46 need updating. Patterns like `touch\s+reports/` and `>\s*reports/task-` anchor to `reports/` without a preceding path. A command like `touch docs/imp-plans/feature/reports/task-001-...` would NOT match `touch\s+reports/`. Update the suspicious-pattern regex to match `reports/` anywhere after the command:

| Pattern | Current | New |
|---------|---------|-----|
| touch detection | `touch\s+reports/` | `touch\s+\S*reports/` |
| redirect detection | `>\s*reports/task-` | `>\s*\S*reports/task-` |
| echo detection | `>\s*reports/` | `>\s*\S*reports/` |
| cat/null detection | `>\s*reports/` | `>\s*\S*reports/` |

The `.dispatch-log` detection (line 27) uses `grep -qiE '\.dispatch-log'` — matches anywhere, no changes needed.

### `sdd-stop-hook.sh`

| Aspect | Current | New |
|--------|---------|-----|
| SDD detection | `[ -d "${CWD}/reports" ] && [ -f "${CWD}/DEVIATIONS.md" ]` | Read `.active-feature` → check `$FEAT/reports` + `$FEAT/deviations.md` |
| Plan discovery | `${CWD}/docs/imp-plans/*.md` | `${CWD}/$FEAT/*.md` |
| Honesty check | `${CWD}/reports/honesty-check-*.md` | `${CWD}/$FEAT/reports/honesty-check-*.md` |
| Checkpoint args | `--deviations-file ${CWD}/DEVIATIONS.md --reports-dir ${CWD}/reports/` | `--deviations-file ${CWD}/$FEAT/deviations.md --reports-dir ${CWD}/$FEAT/reports/` |
| Fallback | N/A | If no `.active-feature`, fall back to root-level paths for **pre-migration artifacts only** (backwards compat). For migrated features, `.active-feature` is always present during active sessions — the finishing skill removes it as a final step, but the stop hook fires during the session before cleanup. |
| `SUPERPOWERS_ROOT` resolution | Not present (hardcoded `CHECKPOINT_SCRIPT` path) | Add self-resolution preamble. Replace hardcoded `CHECKPOINT_SCRIPT` with `$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/controller-checkpoint.py`. |

### Python Scripts

| Script | Change |
|--------|--------|
| `controller-checkpoint.py` | Add optional `--feature-dir` argument. When provided, resolve `--reports-dir` and `--deviations-file` relative to it. |
| `context-summary.py` | Add optional `--feature-dir` argument. Same resolution pattern. |

## Skill & Prompt Template Changes

### Entry-Point Skills

| Skill | Changes |
|-------|---------|
| **brainstorming/SKILL.md** | Add feature name prompt step after initial clarifying questions. Change spec output from `docs/specs/YYYY-MM-DD-<topic>-design.md` to `<feature-dir>/spec.md` and `<feature-dir>/spec-distilled.md`. Add conflict detection logic. |
| **writing-plans/SKILL.md** | Add feature name prompt at start if no `.active-feature`. Change plan output to `<feature-dir>/plan.md` + `module-N-*.md`. Change manifest to `<feature-dir>/plan-manifest.txt`. Change review report to `<feature-dir>/plan-review-report.md`. |
| **handoff-acceptance/SKILL.md** | Add feature name prompt when verdict is ACCEPTED and work starts a new feature. |

### Execution Skills

| Skill | Changes |
|-------|---------|
| **subagent-driven-development/SKILL.md** | Plan Ingestion step 5: create `<feature-dir>/deviations.md` and `<feature-dir>/reports/`. All report save instructions use `<feature-dir>/reports/task-NNN-*.md`. Checkpoint and context-summary commands pass `--feature-dir`. |
| **executing-plans/SKILL.md** | Same path changes as SDD where it references report locations. |
| **finishing-a-development-branch/SKILL.md** | Add cleanup step: remove `.active-feature` and `.allow-main` (if present) after any of the 4 options complete. |

### Prompt Templates

| Template | Change |
|----------|--------|
| **implementer-prompt.md** | Report save path: `<feature-dir>/reports/task-NNN-implementer-report.md` |
| **spec-compliance-reviewer-prompt.md** | Report save path uses feature dir |
| **code-quality-reviewer-prompt.md** | Report save path uses feature dir |
| **controller-partner-prompt.md** | Partner review path: `<feature-dir>/reports/partner-review-NNN.md` |
| **pre-execution-audit-prompt.md** | Audit report path: `<feature-dir>/reports/pre-execution-audit.md` |
| **trace-auditor-prompt.md** | Trace paths: `<feature-dir>/reports/execution-trace*` |

### References

| File | Change |
|------|--------|
| **references/report-naming-convention.md** | Update example paths to show feature-dir prefix |
| **references/deviations-template.md** | Reference `<feature-dir>/deviations.md` |
| **writing-plans/references/task-0-template.md** | Output path in feature dir |
| **writing-plans/references/module-template.md** | Plan file paths within feature dir |

### Unchanged Skills

These skills do not reference SDD artifact paths and require no changes: `using-superpowers`, `using-git-worktrees`, `systematic-debugging`, `test-driven-development`, `requesting-code-review`, `receiving-code-review`, `dispatching-parallel-agents`, `writing-skills`, `verification-before-completion`.

## Path Resolution: Main vs Worktree

Both scenarios resolve identically. No branching logic required.

### Main Branch

```
CWD:              /Users/user/projects/my-project
.active-feature:  docs/imp-plans/2026-05-02-pydantic-phase-2
.allow-main:      (exists — safety opt-in)
Artifact paths:   $CWD/docs/imp-plans/2026-05-02-pydantic-phase-2/reports/task-NNN-*.md
```

### Worktree

```
CWD:              /Users/user/projects/my-project/.worktrees/pydantic-phase-2
.active-feature:  docs/imp-plans/2026-05-02-pydantic-phase-2
Artifact paths:   $CWD/docs/imp-plans/2026-05-02-pydantic-phase-2/reports/task-NNN-*.md
```

Hooks do `cd "$CWD"` then `FEAT=$(cat .active-feature)` then `$FEAT/reports/...`. CWD is the only variable — whether it's the main repo or a worktree is irrelevant to path resolution.

## Testing Strategy

### Layer 1: Unit Tests (`tests/unit/`)

| Test Area | Changes |
|-----------|---------|
| **test_sdd_hard_gates.py** | Update fixture paths from `reports/task-NNN-*` to `$FEAT/reports/task-NNN-*`. Add: hook with `.active-feature` resolves correctly, hook without `.active-feature` falls back to root, hook blocks when `.active-feature` missing and SDD invoked. |
| **test_checkpoint.py** | Add `--feature-dir` argument tests. Verify paths resolve relative to feature dir. |
| **test_sdd_report_guard.py** | Verify regex matches feature-dir paths (expected to pass without code changes). |
| **New: test_active_feature.py** | Conflict detection: stale pointer, completed feature, incomplete feature. Feature name validation. |

### Layer 2: POC / Integration Tests (`tests/poc-feature-directory/`)

| Test | Change |
|------|--------|
| Tests 1-7 | Switch from patched hook to real production hooks (they now natively support `.active-feature`) |
| Test 8 (new) | `.active-feature` lifecycle: create → hooks resolve → cleanup → hooks fall back |
| Test 9 (new) | Conflict detection: existing `.active-feature` + new skill invocation |
| Cleanup | Delete `sdd-pre-dispatch-hook-patched.sh` (obsolete) |

### Layer 3: Regression Tests

| Suite | Change |
|-------|--------|
| **validate-all-skills.py** | Add checks: entry-point skills reference `.active-feature`, no SKILL.md uses root-level `DEVIATIONS.md` or bare `reports/` without feature-dir context. |
| **verify-symlink-install.sh** | Add check: `.gitignore` includes `.active-feature`. |

## Migration & Cutover Order

Single coordinated change — no phased rollout.

1. Add `.active-feature` to `.gitignore`
2. Update hook scripts (enforcement layer — includes root-level fallback)
3. Update Python scripts (`controller-checkpoint.py`, `context-summary.py` — add `--feature-dir`)
4. Update SKILL.md files (entry-point skills: feature name prompt + conflict detection; execution skills: new paths)
5. Update prompt templates (subagent report paths)
6. Update references (templates, naming conventions)
7. Update unit tests (fixture paths, new test cases)
8. Update POC tests (switch to real hooks, add lifecycle tests)
9. Update regression tests (new checks)
10. Delete obsolete files (`tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh`)
11. Update CLAUDE.md (document `.active-feature`, new directory structure, updated test counts)

### Backwards Compatibility

Hooks fall back to root-level paths when no `.active-feature` exists. Projects that haven't adopted per-feature directories continue to work unchanged. The next time an entry-point skill is invoked, it prompts for a feature name and begins using the new layout.

### Existing Artifacts

Existing SDD artifacts at project root (e.g., Pydantic Phase 2 `reports/` and `DEVIATIONS.md` in the superpowers repo) remain as-is. They are historical. The next feature will use the new layout.

## Obsolescence Register

| Item | Status After Migration | Action |
|------|----------------------|--------|
| `tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh` | Obsolete — real hooks now support feature dirs | Delete |
| `docs/specs/` as default spec output location | Superseded — specs go into feature dirs | No delete (existing specs stay; new specs use feature dirs) |
| Root-level `DEVIATIONS.md` convention | Superseded — `<feature-dir>/deviations.md` | No delete of existing files |
| Root-level `reports/` convention | Superseded — `<feature-dir>/reports/` | No delete of existing files |
| `docs/imp-plans/plan-manifest.txt` (top-level) | Superseded — manifest moves into feature dir | Existing manifests stay; new ones go in feature dir |
| Plan-validation-gate subdirectory search (`find -maxdepth 2`) | Simplified — `.active-feature` provides direct path | Logic retained as fallback but primary path is direct |
