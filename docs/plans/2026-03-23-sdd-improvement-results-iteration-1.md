# SDD Improvement Results — Iteration 1: Plan Decomposition & Module System

**Date**: 2026-03-23
**Skill Modified**: `skills/writing-plans/SKILL-v0.1.md` (364 lines, up from 145)
**Baseline**: `skills/writing-plans/SKILL.md` (original, preserved)
**Snapshot**: `snapshot-pre-sdd-improvements-v1` at `f352ea9`

---

## Changes Made

| Addition | Purpose |
|----------|---------|
| Plan Size & Modularization (800-line gate) | Prevents monolithic plans that exhaust context |
| Module file naming + parent plan template | Enables parallel execution of independent modules |
| Contract References in plan header | Forces declaration of external dependencies upfront |
| Contract Constraints in plan header | Records non-negotiable facts before implementation |
| Write-Scope Partitioning table | Prevents parallel tasks from editing same files |
| Ground-Truth Fixtures / Task 0 template | Anchors implementation to real contract data |
| Task size limit (200 lines) | Prevents individual tasks from exhausting subagent context |
| Enhanced Plan Review Checklist (9 new categories) | Mechanical verification beyond "does it look right" |
| Module Template | Standardized format for decomposed plan modules |

---

## Evaluation Against Known Issues

| Verdict | Count | Issues |
|---------|-------|--------|
| **PREVENTED** | 6 | BUG-2, BUG-3, PF-4, EG-5, UI-1, UI-2 |
| **PARTIALLY ADDRESSED** | 3 | BUG-1, PF-1, PF-3 |
| **NOT ADDRESSED** | 11 | PF-2, PF-5, EG-1, EG-2, EG-3, EG-4, UI-3, UI-4, UI-5, UI-6 |

### Full Issue Table

| Issue ID | Issue | Verdict | Explanation |
|----------|-------|---------|-------------|
| BUG-2 | Gate 4 rejected valid amounts (float vs string) | PREVENTED | Task 0 extracts actual field types from source; contract test encodes `isinstance(str)` |
| BUG-3 | Balance/rate parsing failed on strings | PREVENTED | Same mechanism as BUG-2; contract fixtures enforce string types |
| PF-4 | TDD validated wrong assumptions | PREVENTED | Task 0 prohibits invented fixtures; must derive from source |
| EG-5 | Test fixtures use wrong types | PREVENTED | Direct target of Task 0 ground-truth requirement |
| UI-1 | Plan too large (2816 lines) | PREVENTED | 800-line decomposition gate rejects monolithic plans |
| UI-2 | Subagents out of context | PREVENTED | Module + 200-line task limit reduces context load |
| BUG-1 | Missing error_details field | PARTIALLY | Task 0 helps IF the handoff package defines the field |
| PF-1 | Plan had wrong code snippets | PARTIALLY | Size reduction + review checklist help; still advisory |
| PF-3 | Subagents didn't read source files | PARTIALLY | Task 0 compensates structurally; individual subagents still not directed to read source |
| PF-2 | Controller skipped all 34 reviews | NOT ADDRESSED | Requires Iteration 3 (controller discipline) |
| PF-5 | No deviation tracking | NOT ADDRESSED | Requires Iteration 4 (feedback structure) |
| EG-1 | TestModeControls never wired | NOT ADDRESSED | Requires Iteration 5 (completion gate) |
| EG-2 | Dead code deferred, untracked | NOT ADDRESSED | Requires Iterations 4+5 |
| EG-3 | Plan checkboxes never updated | NOT ADDRESSED | Requires Iteration 3 |
| EG-4 | 4th column data dropped | NOT ADDRESSED | Requires Iteration 4 |
| UI-3 | Controller not following plans | NOT ADDRESSED | Requires Iteration 3 |
| UI-4 | Poor subagent feedback | NOT ADDRESSED | Requires Iteration 4 |
| UI-5 | Dead code not addressed | NOT ADDRESSED | Requires Iterations 4+5 |
| UI-6 | No QA testing for completion | NOT ADDRESSED | Requires Iteration 5 |

---

## Root Cause Coverage

| Root Cause | Status | Addressed By |
|-----------|--------|-------------|
| RC-1: Plan size | Fully addressed | 800-line gate, 200-line task limit, module system |
| RC-2: No ground-truth | Substantially addressed | Contract Constraints, Task 0, fixture prohibition |
| RC-3: Controller discipline | NOT addressed | Needs Iteration 3 |
| RC-4: Feedback loop | NOT addressed | Needs Iteration 4 |
| RC-5: No completion gate | NOT addressed | Needs Iteration 5 |
| RC-6: Plan quality | Partially addressed | 9 new review categories, advisory not mechanical |

---

## Identified Weaknesses in v0.1

1. **Task 0 is only as good as the source contract** — If the handoff package itself is incomplete (e.g., `error_details` missing), Task 0 won't catch the gap. No mechanism to flag underspecified contracts.

2. **Review checklist is advisory, not mechanical** — "Contract Accuracy" check requires the reviewer to read source files AND plan snippets. Current reviewer dispatch provides plan + spec paths, NOT handoff/source file paths. Reviewer may not have the information needed.

3. **No enforcement that Task 0 actually blocks Task 1** — The SDD skill (not yet updated) controls execution order. If controller skips Task 0 the same way it skipped reviews, ground-truth anchoring is lost.

4. **Contract Constraints visible in plan header but not in task prompts** — Subagents receive individual task text. Even if the plan header documents contracts accurately, the implementer subagent only sees its task section.

5. **Plan decomposition doesn't help if controller skips execution** — Smaller plans are only valuable if the controller follows them. RC-3 (controller discipline) is the dominant remaining risk.

---

## Recommendations for Next Iteration

**Priority**: Iteration 3 (Controller Discipline) is the highest-leverage next step.

Rationale: Improvements from Iterations 1 and 2 are neutralized if the controller bypasses them. Task 0, reviews, and checkpoints all depend on the controller executing them. The reconciliation post-mortem's most catastrophic failure was the controller skipping 34 reviews — this must be addressed before further iteration on plan quality or subagent feedback.

**Specific gaps to address in Iteration 3:**
- Add Task 0 blocking enforcement to SDD SKILL.md
- Add review-skip NEVER directives
- Add checkpoint update requirement (controller updates plan checkboxes)
- Add Contract Constraints passthrough (controller includes constraints in each subagent prompt)

**Also address (folded into Iteration 3):**
- Reviewer dispatch should include source contract file paths, not just plan + spec
- Add mechanism to flag when a source contract is underspecified
