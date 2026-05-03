# Per-Feature Directory Migration — Distilled Implementation Spec

> **Source**: `docs/specs/2026-05-02-per-feature-directory-design.md` (v1.1, 8 decisions)
> **Distilled**: 2026-05-02
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

## Contract Facts

- Feature directory path: `docs/imp-plans/YYYY-MM-DD-<feature-name>/`
- `.active-feature` file: single-line plaintext at project root, contains relative path to active feature directory. Gitignored.
- `.allow-main` is unchanged — remains at project root as branch safety opt-in
- Feature name: kebab-case, user-confirmed at entry-point skill prompt
- `deviations.md` is lowercase (was `DEVIATIONS.md`)
- All hooks read `.active-feature` via `FEAT=$(cat .active-feature)` after `cd "$CWD"`
- When `$FEAT` is empty (no `.active-feature`), hooks fall back to root-level paths (backwards compat)
- Hooks that currently use hardcoded absolute paths must add `SUPERPOWERS_ROOT` self-resolution preamble

## Open Decisions

| # | Decision | Options | Resolution Required By |
|---|----------|---------|----------------------|

(All decisions resolved)

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Artifact consolidation | Move everything (specs, plans, execution artifacts) into per-feature dirs |
| 2 | Migration approach | Hard cutover, single coordinated change. Hooks include root-level fallback. |
| 3 | Discovery mechanism | `.active-feature` file at project root (explicit path, not auto-discovery) |
| 4 | Feature name establishment | User prompted at entry-point skills — agent suggests name, user confirms/overrides |
| 5 | `.active-feature` git status | Gitignored (workspace state, not project state) |
| 6 | Cleanup mechanism | Automated: finishing skill on happy path, conflict detection at entry on forgotten path |
| 7 | `.allow-main` relationship | Separate files — `.allow-main` keeps single purpose, `.active-feature` works on all branches |
| 8 | Gate enforcement | Extend existing gates (plan-validation-gate, sdd-pre-dispatch) — no new gates |

## Component Specifications

### Feature Directory Structure

```
docs/imp-plans/YYYY-MM-DD-<feature-name>/
  ├── spec.md
  ├── spec-distilled.md
  ├── plan.md
  ├── module-N-<name>.md
  ├── plan-manifest.txt
  ├── plan-review-report.md
  ├── deviations.md
  └── reports/
      ├── pre-execution-audit.md
      ├── pre-execution-audit-self-assessment.md
      ├── task-NNN-implementer-report.md
      ├── task-NNN-spec-review.md
      ├── task-NNN-quality-review.md
      ├── partner-review-NNN.md
      ├── checkpoint-pre-dispatch-NNN.json
      ├── context-summary.md
      ├── honesty-check-YYYY-MM-DD.md
      ├── execution-trace.json
      ├── execution-trace-audit.md
      ├── .dispatch-log
      └── archive-<timestamp>/
```

SDD re-run archival: detect existing reports → create `reports/archive-<timestamp>/` → move existing reports + deviations into it → create fresh `deviations.md`.

### `.active-feature` Lifecycle

**Creation** — three entry-point skills:
- `brainstorming`: after 1-2 clarifying questions. Abandoned brainstorming cleaned up by next entry-point conflict detection.
- `writing-plans`: at start if no `.active-feature` exists
- `handoff-acceptance`: when verdict is ACCEPTED and starts new feature

Prompt: *"All artifacts for this work will be organized under a feature directory. I suggest: **`<name>`**. Press enter to accept, or type a different name."*

**Conflict detection** — when entry-point skill finds existing `.active-feature`:
- Dir doesn't exist → auto-clean, proceed
- Dir exists, all tasks completed (count `### Task N` headers, verify matching `task-NNN-implementer-report.md`) → auto-clean, proceed
- Dir exists, incomplete work → prompt: resume or archive
- Dir exists, no plan yet → prompt: resume or start fresh

**Cleanup** — `finishing-a-development-branch` removes `.active-feature` + `.allow-main` after any of its 4 options complete.

**Gate** — `plan-validation-gate` blocks SDD/executing-plans if no `.active-feature` exists.

### Hook Changes

**Common preamble** (all hooks, after `cd "$CWD"`):
```bash
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi
```

**`sdd-pre-dispatch-hook.sh`** (~30 path refs):
- All artifact paths prefixed with `$FEAT/`: `DEVIATIONS.md` → `$FEAT/deviations.md`, `reports/` → `$FEAT/reports/`, etc.
- `task_report_glob()` returns `$FEAT/reports/task-${padded}-${type}*`
- Plan search: `docs/imp-plans/*.md docs/plans/*.md` → `$FEAT/*.md` (intentionally scopes Source Contracts to current feature — do NOT add back old multi-dir search)
- All BLOCKED error messages and SDD REMINDER `additionalContext` must dynamically interpolate `$FEAT/` prefix

**`plan-validation-gate-hook.sh`**:
- Add `SUPERPOWERS_ROOT` self-resolution preamble
- Replace hardcoded `VALIDATE_PLAN_SCRIPT` with `$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/validate-plan.py`
- Replace `.venv/bin/python3` with `$PYTHON` (from superpowers venv)
- If `.active-feature`: go directly to `$FEAT/plan-manifest.txt`. Else: existing search as fallback.
- New gate: block if no `.active-feature` when SDD/executing-plans invoked

**`sdd-report-guard.sh`**:
- Detection regex (`reports/task-`) — no change needed (matches substring anywhere)
- Suspicious-pattern regexes need `\S*` before `reports/`:
  - `touch\s+reports/` → `touch\s+\S*reports/`
  - `>\s*reports/task-` → `>\s*\S*reports/task-`
  - `>\s*reports/` → `>\s*\S*reports/`

**`sdd-stop-hook.sh`**:
- Add `SUPERPOWERS_ROOT` self-resolution preamble
- Replace hardcoded `CHECKPOINT_SCRIPT` with `$SUPERPOWERS_ROOT/...`
- SDD detection: read `.active-feature` → check `$FEAT/reports` + `$FEAT/deviations.md`
- Fallback to root-level paths for pre-migration artifacts only
- All path args to checkpoint script use `$FEAT/` prefix

**`controller-checkpoint.py`**: add optional `--feature-dir` argument, resolve paths relative to it.

**`context-summary.py`**: add optional `--feature-dir` argument, same pattern.

### Skill Changes

**Entry-point skills** (add feature name prompt + conflict detection + new output paths):
- `brainstorming/SKILL.md`: spec output → `<feature-dir>/spec.md` and `spec-distilled.md`
- `writing-plans/SKILL.md`: plan → `<feature-dir>/plan.md`, manifest → `<feature-dir>/plan-manifest.txt`, review → `<feature-dir>/plan-review-report.md`
- `handoff-acceptance/SKILL.md`: feature name prompt on ACCEPTED

**Execution skills** (read `.active-feature`, use for artifact paths):
- `subagent-driven-development/SKILL.md`: create `<feature-dir>/deviations.md` + `<feature-dir>/reports/`, all report paths use feature dir, checkpoint/context-summary commands pass `--feature-dir`
- `executing-plans/SKILL.md`: same path changes as SDD
- `finishing-a-development-branch/SKILL.md`: add cleanup of `.active-feature` + `.allow-main`

**Prompt templates** (report save paths → `<feature-dir>/reports/...`):
- `implementer-prompt.md`, `spec-compliance-reviewer-prompt.md`, `code-quality-reviewer-prompt.md`, `controller-partner-prompt.md`, `pre-execution-audit-prompt.md`, `trace-auditor-prompt.md`

**References** (update example paths):
- `report-naming-convention.md`, `deviations-template.md`, `task-0-template.md`, `module-template.md`

**Unchanged skills**: `using-superpowers`, `using-git-worktrees`, `systematic-debugging`, `test-driven-development`, `requesting-code-review`, `receiving-code-review`, `dispatching-parallel-agents`, `writing-skills`, `verification-before-completion`

### Cutover Order

1. Add `.active-feature` to `.gitignore`
2. Update hook scripts (with root-level fallback)
3. Update Python scripts (`--feature-dir` arg)
4. Update SKILL.md files (entry-point prompts, execution paths)
5. Update prompt templates
6. Update references
7. Update unit tests
8. Update POC tests (switch to real hooks, add lifecycle tests)
9. Update regression tests
10. Delete `tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh`
11. Update CLAUDE.md

### Obsolescence

- `sdd-pre-dispatch-hook-patched.sh` → delete
- Root-level `DEVIATIONS.md`, `reports/`, `docs/specs/` as default outputs → superseded (existing files stay)
- Top-level `docs/imp-plans/plan-manifest.txt` → superseded
- Plan-validation-gate subdirectory search → retained as fallback, primary path is direct

## Acceptance Criteria

- [ ] Entry-point skills prompt for feature name and create `<feature-dir>/` + `.active-feature`
- [ ] All hooks resolve artifact paths from `.active-feature` when present
- [ ] All hooks fall back to root-level paths when `.active-feature` absent
- [ ] `plan-validation-gate` blocks SDD/executing-plans without `.active-feature`
- [ ] Conflict detection at entry-point skills handles: stale pointer, completed feature, incomplete feature
- [ ] `finishing-a-development-branch` removes `.active-feature` + `.allow-main`
- [ ] Path resolution works identically on main and in worktrees
- [ ] `sdd-report-guard` detects suspicious patterns on feature-dir report paths
- [ ] All hardcoded absolute paths in hooks replaced with `SUPERPOWERS_ROOT`-derived paths
- [ ] Unit tests cover `.active-feature` resolution, fallback, and conflict detection
- [ ] POC tests use real hooks (patched hook deleted)
- [ ] Regression tests verify `.active-feature` in `.gitignore` and skill path references
- [ ] Existing root-level artifacts in projects are not broken (backwards compat)
