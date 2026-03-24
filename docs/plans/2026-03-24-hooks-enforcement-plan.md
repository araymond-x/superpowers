# Hooks-Based Enforcement Implementation Plan

> **Goal**: Replace advisory prompt instructions with process-level enforcement (exit 2 hooks) for critical Superpowers skill checkpoints.
> **Motivation**: Controller agents read, understand, and ignore prompt-based discipline instructions. Documented across 8 Claude Code GitHub issues and our own Statement Reconciliation re-implementation where all reviews were skipped despite explicit "Non-Negotiable" enforcement text.
> **Test Case**: Statement Reconciliation Module 3 execution with hooks active.

---

## Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: P0 — SDD hook + checkpoint extension | Pending | |
| Phase 2: Live test against Module 3 | Pending | Depends on Phase 1 |
| Phase 3: Iterate and refine | Pending | Depends on Phase 2 |
| Phase 4: P1-P2 — Remaining skill hooks | Pending | Depends on Phase 3 |
| Phase 5: Final validation | Pending | Depends on Phase 4 |

---

## Phase 1: P0 Implementation (SDD Enforcement)

### Files to Create

| File | Purpose |
|------|---------|
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Main enforcement: blocks Agent dispatches without review reports, DEVIATIONS.md, Task 0, branch safety |
| `skills/subagent-driven-development/scripts/check-safe-branch.sh` | Shared: blocks if on main/master |

### Files to Modify

| File | Change |
|------|--------|
| `skills/subagent-driven-development/SKILL.md` | Add `hooks:` block to YAML frontmatter |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Extend pre-dispatch to check spec-review + quality-review report files |
| `tests/ARaymond-skill-regression/validate-all-skills.py` | Add checks for hook frontmatter presence |

### SDD Hook Logic (`sdd-pre-dispatch-hook.sh`)

```
Read tool_input from stdin
Extract description field

IF description matches "Implement Task N" (implementer dispatch):
  IF N > 0:
    CHECK: reports/task-(N-1)-implementer-report* exists
    CHECK: reports/task-(N-1)-spec-review* exists
    CHECK: reports/task-(N-1)-quality-review* exists
    IF any missing → exit 2 "Task (N-1) review incomplete"

  IF plan has Source Contracts AND N > 0:
    CHECK: reports/task-0-* exists
    IF missing → exit 2 "Task 0 must complete first"

IF description matches any "Implement Task" or "Review spec" or "Review quality":
  CHECK: DEVIATIONS.md exists
  IF missing → exit 2 "DEVIATIONS.md required"

  CHECK: git branch --show-current != main/master
  IF on main → exit 2 "Not on a feature branch"

IF description matches "Review spec" or "Review quality" (reviewer dispatch):
  No blocking — reviewers are always allowed

EXIT 0 (allow dispatch)
```

### Verification Criteria

- [ ] Hook blocks implementer dispatch when previous task has no spec-review report
- [ ] Hook blocks implementer dispatch when previous task has no quality-review report
- [ ] Hook allows implementer dispatch when all 3 reports exist for previous task
- [ ] Hook blocks any dispatch when DEVIATIONS.md doesn't exist
- [ ] Hook blocks any dispatch when on main branch
- [ ] Hook allows reviewer dispatches (spec/quality review) without blocking
- [ ] Hook allows Task 0 dispatch without checking previous task (no Task -1)
- [ ] Hook blocks Task 1+ when Task 0 report doesn't exist (if Source Contracts present)
- [ ] Hook produces clear error messages that tell the controller exactly what to do
- [ ] Hook does NOT fire in non-SDD sessions (frontmatter scoping)

---

## Phase 2: Live Test

### Test Protocol

1. Have the implementing agent load the SDD skill for Module 3
2. The hook should activate via frontmatter
3. Attempt to dispatch Task 1 of Module 3 — hook should allow (Module 2 tasks are complete with reports)
4. After Task 1 implementer returns, attempt Task 2 WITHOUT dispatching reviews — hook should BLOCK
5. Dispatch spec review, dispatch quality review, save both reports
6. Attempt Task 2 again — hook should ALLOW
7. Document every hook fire: what it checked, what it decided, any false positives

### Success Criteria

- Zero false positives (hook doesn't block legitimate dispatches)
- Zero false negatives (hook doesn't allow dispatches that should be blocked)
- Controller receives clear error messages when blocked
- Controller successfully completes Module 3 with all reviews done

---

## Phase 3: Iterate and Refine

Based on Phase 2 observations:
- Fix any false positives (legitimate dispatches blocked)
- Fix any false negatives (skipped reviews not caught)
- Adjust the task number extraction regex if needed
- Handle edge cases: re-dispatches after BLOCKED, minimum review tier, non-standard task numbering

---

## Phase 4: P1-P2 Remaining Hooks

### P1: Branch Safety for executing-plans

| File | Change |
|------|--------|
| `skills/executing-plans/SKILL.md` | Add `hooks:` frontmatter for Bash tool branch check |

### P2: Brainstorming Gate

| File | Change |
|------|--------|
| `skills/brainstorming/SKILL.md` | Add `hooks:` frontmatter for Skill tool gate |
| `skills/brainstorming/scripts/brainstorming-gate-hook.sh` | NEW: check spec exists before implementation skills |

### P2: Writing-Plans Auto-Validate

| File | Change |
|------|--------|
| `skills/writing-plans/SKILL.md` | Add `hooks:` frontmatter for Write tool post-hook |
| `skills/writing-plans/scripts/auto-validate-plan-hook.sh` | NEW: auto-run validate-plan.py on plan write |

### P2: Handoff Acceptance Gate

| File | Change |
|------|--------|
| `skills/handoff-acceptance/SKILL.md` | Add `hooks:` frontmatter for Skill tool gate |
| `skills/handoff-acceptance/scripts/handoff-gate-hook.sh` | NEW: check acceptance report before planning |

---

## Phase 5: Final Validation

### Automated Tests
- Run `validate-all-skills.py` (static regression — verify hooks in frontmatter)
- Run `verify-symlink-install.sh` (verify hook scripts exist via symlink)
- Run `test-sdd-content.sh` (behavioral — verify SDD skill loads with hooks)

### Skeptical Review
- Dispatch a skeptical reviewer subagent to:
  1. Read every hook script and verify the logic matches this plan
  2. Read every modified SKILL.md frontmatter and verify hook configuration is correct
  3. Verify the hooks don't fire in non-SDD sessions (scoping)
  4. Verify error messages are actionable
  5. Check for bypass paths (can the controller work around the hooks?)

### Live Execution Test
- Run a fresh small SDD execution (2-3 tasks) with all hooks active
- Verify: every task gets reviewed, DEVIATIONS.md is maintained, reports are filed
- Compare against the Statement Reconciliation re-implementation where reviews were skipped

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Hooks fire in non-SDD sessions | Frontmatter scoping — hooks only active while skill is loaded |
| False positives block legitimate work | Phase 2 live test catches these before propagation |
| Hook scripts have bugs | Skeptical review + behavioral tests in Phase 5 |
| Controller finds a bypass (e.g., not using Agent tool) | The hook matches on the Agent tool — the only way to dispatch subagents. There is no alternative dispatch mechanism. |
| Hook adds latency to every Agent call | Script runs `ls` and `git branch` — milliseconds. No API calls. |
| Upstream merge breaks hooks | Hooks are in our frontmatter additions, not upstream code. Merge conflicts are contained to the frontmatter block. |
