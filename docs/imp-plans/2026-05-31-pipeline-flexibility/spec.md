# Pipeline Flexibility — Design Spec

**Feature Name**: pipeline-flexibility
**Date**: 2026-05-31
**Feature Archetype**: Extension
**Sprint**: Superpowers Sprint 2

## Overview

Three improvements to the superpowers pipeline that reduce friction for common workflows without weakening enforcement:

1. **P1 — Direct-to-writing-plans entry mode**: Make `writing-plans` a first-class entry point parallel to `brainstorming`, with proper setup guardrails (conflict detection, worktree guard, optional spec validation, entry mode recording).

2. **B6 — Verification/no-code task type**: Add `task_type: verification` for read-only tasks (grep, test suite runs, consistency audits) that skip the review cycle while retaining dispatch audit trail. Defense-in-depth prevents abuse.

3. **N2 — SSOT audit (investigation-only)**: Audit all SKILL.md files for manual prescriptions that hooks already enforce automatically. Produce a findings document; fixes become sprint 3 quick wins.

## Motivation

The superpowers pipeline is mature and battle-tested for large/medium projects (skill evaluation, 2026-05-21). Two friction points remain:

- **Entry rigidity**: `brainstorming → writing-plans → SDD` is a monolithic chain. When a vetted handoff or spec already exists, brainstorming's 10-step question/design/review process is unnecessary. A 1-task config change still produces ~7-10 artifact files because there is no way to enter downstream of brainstorming.

- **Dispatch ceremony for non-code tasks**: Verification tasks (grep for orphaned code, run tests, consistency audits) go through the full dispatch/review cycle despite producing no code changes. In the BTD consolidation session, Task 9 (grep-only) cost 39 minutes.

- **Manual/hook drift**: C6 confirmed that SDD SKILL.md prescribed a manual `estimate-task-tokens.py` step that the hook already enforced automatically, with drifted arguments. Controllers who correctly skipped the redundant manual step logged false honesty-check violations. Other instances likely exist.

## Decisions

### D1: Entry Architecture

**Decision**: Parallel entry points, not serial chain.

Brainstorming and writing-plans become independent entry points into the same downstream pipeline (plan validation gate → SDD). Brainstorming remains the collaborative design tool. Writing-plans gains setup guardrails for direct entry.

```
                  ┌─── brainstorming ──→ spec ──┐
  idea/handoff ───┤                              ├──→ writing-plans ──→ SDD
                  └─── direct entry (P1) ───────┘
```

**Rejected alternative**: "Skinny brainstorming" — making brainstorming detect vetted handoffs and fast-track. Rejected because: after skipping Steps 3-7.5 (questions, approaches, design, spec, review, distillation), what remains is Steps 1, 3.5, 9, 10 — a setup shim, not a design skill. The skill's CRITICAL CONSTRAINT ("do NOT implement until design is approved") actively fights the user when the design is already done.

**Rejected alternative**: Evolving `/handoff` to produce spec-compatible output. Promising but touches a different repo (claude-codex-handoff), changes the handoff contract for all use cases, and is a bigger scope. Better as a future complement, not a replacement.

### D2: Verification Task Ceremony

**Decision**: Dispatch subagent, skip reviews (option B from clarifying questions).

Verification tasks are dispatched as subagents (preserving audit trail via dispatch log and implementer report) but skip all review dispatches (spec review, quality review, partner review).

**Rejected alternative**: Skip dispatch entirely (option A) — controller runs verification inline. Loses audit trail and pollutes controller context window.

### D3: Verification Task Abuse Prevention

**Decision**: Four-layer defense-in-depth.

1. **Plan-time WARNING** (`validate-plan.py`): Warn on write-suggesting keywords in verification task titles (`create`, `add`, `implement`, `fix`, `modify`, `write`, `update`, `refactor`, `migrate`).

2. **Pre-completion ratio cap** (`controller-checkpoint.py`): Verification tasks capped at ≤30% of total tasks. Same pattern as the ≤50% minimum-tier review ratio.

3. **Git-based reality check** (`controller-checkpoint.py`): At pre-completion, for each verification task, check whether any commits modified tracked files between that task's report timestamp and the next task's report. If a verification task produced file-modifying commits, **FAIL**.

4. **Implementer prompt restriction**: Verification tasks use a modified dispatch prompt: "You are a read-only auditor. Do not create, modify, or delete any repository files. Your report text is your only output."

Layer 3 is the strongest — it checks objective reality (git log) and is unforgeable by the controller.

### D4: N2 Scope

**Decision**: Investigation-only. No code changes.

The audit reads all 15 SKILL.md files and compares prescribed manual steps against hook enforcement. Each finding is classified: retire (hook is authoritative), strengthen (manual step is better), or keep (genuinely complementary). Output is a findings document in `docs/process-improvement-findings/` plus new `BACKLOG.md` rows. Fixes are sprint 3 quick wins.

### D5: Plan Structure

**Decision**: Single plan file, standard enforcement tier, ~10 tasks.

The three items share enough file surface (plan model, SDD SKILL.md, hook, checkpoint) that sequencing them in one plan avoids merge conflicts. If the plan exceeds 800 lines during writing, split into Module 1 (P1) and Module 2 (B6 + N2).

Enforcement tier: **standard** (10 tasks across model, hook, checkpoint, and skill files).

## Component Specifications

### C1: Plan Model Extension (`skills/scripts/models/plan.py`)

Two new fields on existing models:

**Plan model** — `entry_mode`:
- Type: `Literal["brainstorming", "direct"]`
- Default: `"brainstorming"`
- Purpose: Audit trail for how the plan originated
- No behavioral impact on downstream gates (informational only)
- No schema version bump (backwards-compatible optional field, same precedent as `review_tier`)

**Task model** — `task_type`:
- Type: `Literal["implementation", "verification"]`
- Default: `"implementation"`
- Purpose: Controls whether the task goes through the review cycle
- Orthogonal to `review_tier` — `review_tier` controls HOW reviews happen; `task_type` controls WHETHER they happen
- No schema version bump

### C2: Writing-Plans SKILL.md Enhancement

**Step 0.5 upgrade** — replaces the current minimal "create `.active-feature` if missing" with a full direct-entry path:

1. **Conflict detection** (ported from brainstorming Step 3.5):
   - If `.active-feature` exists, read the referenced directory
   - Dir doesn't exist → auto-clean `.active-feature`, proceed
   - Dir exists, all plan tasks completed → auto-clean, proceed
   - Dir exists, incomplete work → prompt: resume or archive
   - Dir exists, no plan → prompt: resume or start fresh

2. **Worktree/branch guard**:
   - Check current branch after resolving feature directory
   - If on `main` (or base branch): offer worktree creation via `using-git-worktrees`
   - Allow proceeding on `main` with acknowledgment (respects user preference for reduced worktree friction)

3. **Optional spec input**:
   - If a spec or handoff acceptance report is provided, record its path in `Source Contracts`
   - If a distilled spec is provided, run `check-distillation.sh` to validate
   - Neither is required — direct-to-planning with conversation context is valid

4. **Entry mode recording**:
   - Set `entry_mode: direct` in plan YAML frontmatter
   - The skill detects direct entry (no prior brainstorming artifacts in the feature directory)

**Context block update** — rewrite the "Context" section to describe direct entry as a first-class path, not a fallback with manual setup instructions.

### C3: SDD Pre-Dispatch Hook Changes (`sdd-pre-dispatch-hook.sh`)

The hook needs to know `task_type` for both the current task and the previous task. It reads this from the plan's YAML frontmatter `tasks:` array by parsing with `$PYTHON` (PyYAML). This is a different mechanism than token estimation (which greps markdown task headers) — YAML parsing is required because `task_type` is a structured per-task field, not a text pattern. The hook already calls `$PYTHON` for `estimate-task-tokens.py` and other scripts, so this is consistent. A small helper function (inline or extracted) takes a plan file path and task ID, returns `task_type` (defaulting to `"implementation"` if absent for backwards compatibility).

**Implementer dispatch logging** (new): The hook's Stage 2 (implementer detection) currently enforces checks but does not log to the dispatch log. Add a dispatch log entry (`task=N type=implementer ts=<ISO-8601>`) for every implementer dispatch that passes enforcement. This gives the git reality check (C4) reliable timestamps without relying on file mtime. Existing Check 4c (dispatch provenance) only looks for reviewer entries, so adding implementer entries is non-breaking.

**When the current task is `verification`**:
- Check 5d (partner review): **Skip**. No partner review required.

**When the previous task was `verification`** (and current task is being dispatched):
- Check 4b (previous task's spec/quality review reports): **Skip**. No reviews to check.
- Check 4c (dispatch provenance for previous task's reviews): **Skip**. No dispatches to verify.

All other checks remain unchanged (pre-execution audit, checkpoint files, Task 0 verification, deviations, token estimation, context summary).

### C4: Controller Checkpoint Changes (`controller-checkpoint.py`)

**Pre-completion phase** — two additions:

1. **Verification ratio check**: Count verification tasks as a fraction of total tasks. If > 30%, FAIL with message naming the verification tasks and suggesting reclassification.

2. **Git reality check**: For each verification task N:
   - Read the dispatch log (`reports/.dispatch-log`) for timestamps of task N's implementer dispatch and the next task's implementer dispatch (the hook writes these entries with timestamps, so they're reliable)
   - Check `git log --oneline --after=<dispatch_N_ts> --before=<dispatch_N+1_ts>` for commits that modified tracked files
   - If any file-modifying commits found in that window, FAIL with message: "Verification task N produced file modifications — requires review."
   - For the last verification task (no next dispatch timestamp), use current time as the upper bound
   - This is a best-effort heuristic — the plan-time warning and ratio cap are the primary defenses; the git check is a backstop that catches the most common abuse pattern (subagent modifies files and commits during a verification task)

Both checks are added to the existing pre-completion phase alongside the honesty check, trace audit, and minimum-tier ratio.

### C5: Validate-Plan Script Changes (`validate-plan.py`)

**New WARNING** for verification task titles containing write-suggesting keywords:

Keywords: `create`, `add`, `implement`, `fix`, `modify`, `write`, `update`, `refactor`, `migrate`, `delete`, `remove`

Match is case-insensitive, word-boundary-aware. Emits WARNING (not FAIL) because edge cases exist (e.g., "Verify update script output"). The plan reviewer provides the semantic check.

### C6: SDD SKILL.md Documentation

**New section**: "Verification Tasks" documenting (note: SDD SKILL.md is at 4753 words with a 5000-word soft limit — the planner may need to extract existing content to `references/` to stay under the limit):
- When to use `task_type: verification`
- The simplified controller flow (dispatch → report → done, no reviews)
- The modified implementer prompt (read-only auditor instruction)
- The defense-in-depth layers

**Modified process flow diagram**: Add a branch after "Declare review tier" that checks task_type — verification tasks skip directly to "Mark task complete."

### C7: Writing-Plans SKILL.md — Verification Task Guidance

**New subsection** under task structure or near `review_tier` guidance:

Table of appropriate vs inappropriate `verification` classification with the bright-line rule: if the task modifies any file in the repo, it's `implementation`.

### C8: SSOT Audit Investigation

**Scope**: All 15 SKILL.md files compared against the 4 active hooks registered in `~/.claude/settings.json`:
- `sdd-pre-dispatch-hook.sh` (PreToolUse → Agent)
- `sdd-report-guard.sh` (PreToolUse → Bash)
- `plan-validation-gate-hook.sh` (PreToolUse → Skill)
- `session-start` hook (SessionStart)

Note: `sdd-skill-enforcement-hook.sh` and `sdd-stop-hook.sh` exist on disk but are not registered in settings.json. Findings about inactive hooks would be misleading — exclude them from the audit scope.

**For each manual prescription found**:
- Which SKILL.md, which line range
- Which hook enforces it, which check
- Any drift between the two (args, thresholds, behavior)
- Classification: retire / strengthen / keep

**Output**: `docs/process-improvement-findings/2026-05-31-ssot-audit.md`
**Backlog updates**: New rows in `BACKLOG.md` for each actionable finding.

## Files Modified

| File | Action | Component |
|------|--------|-----------|
| `skills/scripts/models/plan.py` | Modify — add `entry_mode` to Plan, `task_type` to Task | C1 |
| `skills/writing-plans/SKILL.md` | Modify — enhance Step 0.5, update Context block, add verification guidance | C2, C7 |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Modify — add task_type branching for checks 4b, 4c, 5d | C3 |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Modify — add verification ratio + git reality check | C4 |
| `skills/subagent-driven-development/scripts/validate-plan.py` | Modify — add verification keyword WARNING | C5 |
| `skills/subagent-driven-development/SKILL.md` | Modify — add Verification Tasks section | C6 |
| `docs/process-improvement-findings/2026-05-31-ssot-audit.md` | Create — audit findings | C8 |
| `docs/process-improvement-findings/BACKLOG.md` | Modify — mark P1/B6/N2 status, add new rows | C8 |
| `tests/unit/` | Modify — extend existing test files for new fields and behavior | All |
| `tests/integration/sdd-e2e-test.sh` | Modify — add verification task step | B6 |

## Acceptance Criteria

- [ ] `writing-plans` invoked directly (no prior brainstorming) successfully creates `.active-feature`, feature directory, and plan with `entry_mode: direct`
- [ ] Stale `.active-feature` from a prior feature is detected and resolved (4-branch conflict detection)
- [ ] Worktree/branch guard offers worktree creation when on `main`
- [ ] `check-distillation.sh` runs on user-supplied distilled specs during direct entry
- [ ] Plan with `task_type: verification` tasks passes `validate-plan.py` (with keyword WARNING where appropriate)
- [ ] SDD hook logs implementer dispatches to dispatch log with timestamps
- [ ] SDD hook skips review checks (4b, 4c, 5d) for verification tasks
- [ ] SDD hook enforces review checks for implementation tasks unchanged
- [ ] Verification tasks dispatched with read-only auditor prompt
- [ ] Pre-completion gate caps verification tasks at ≤30%
- [ ] Pre-completion gate detects file modifications by verification tasks via git log
- [ ] SSOT audit findings document produced with actionable backlog rows
- [ ] All existing tests pass (regression: 145 PASS / 3 WARNING, unit: 351 tests, e2e: 8 steps)
- [ ] New tests cover: `entry_mode` field, `task_type` field, hook branching, validate-plan warning, checkpoint ratio, checkpoint git check

## Non-Goals

- Changing brainstorming's behavior or entry flow
- Modifying the handoff acceptance skill or `/handoff` CLI tool
- Fixing the SSOT audit findings (sprint 3)
- Adding `entry_mode` to the SDD manifest (informational field stays in plan only)
- Changing the plan-validation-gate hook (it's already entry-mode-agnostic)
