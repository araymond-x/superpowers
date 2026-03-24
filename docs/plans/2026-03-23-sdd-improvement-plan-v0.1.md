# SDD Skills Improvement Plan — v0.1

> **Methodology**: Plan -> Implement -> Test -> Evaluate -> Improve (iterative)
> **Test Case**: `~/projects/personal-finance-api/docs/plans/2026-03-15-statement-reconciliation-ui-design.md` (1347 lines, 75 decisions) and its implementation plan (2816 lines, 17 tasks, 89 checkboxes)
> **Baseline Snapshot**: Git tag `snapshot-pre-sdd-improvements-v1` at commit `f352ea9`
> **Source Findings**: `docs/process-improvement-findings/` (6 documents)

---

## Problem Statement

A 17-task subagent-driven implementation produced 3 P1/P2 bugs (all from the same root cause: string-vs-numeric contract mismatch), 5 execution gaps (unwired components, dead code, unchecked plan items, dropped data, wrong test fixtures), and 6 process failures. The superpowers skill pipeline — brainstorming -> writing-plans -> subagent-driven-development — failed to catch or prevent any of these issues despite having review checkpoints designed for exactly this purpose.

---

## Root Cause Analysis

Six overarching root causes explain all observed failures:

### RC-1: Plan Size Exceeds Agent Context Capacity
- **Evidence**: Implementation plan was 2816 lines (~112KB). Design spec was 1347 lines. Combined: 4163 lines.
- **Impact**: Plan reviewer couldn't hold full context. Subagents received plan excerpts, not the full picture. Controller couldn't track 89 checkboxes across 17 tasks.
- **Downstream failures**: Wrong code snippets survived review (Process Failure #1), cross-document drift went undetected (Plan Review findings #1-#4).

### RC-2: No Ground-Truth Anchoring
- **Evidence**: Plan described contracts in prose ("amounts are strings with commas"). Subagents implemented from description, never reading actual schema files. Test fixtures were invented, not derived from real output.
- **Impact**: Entire pipeline operated on assumed contracts. When assumptions were wrong, every layer (plan, code, tests, fixtures) encoded the same error.
- **Downstream failures**: All 3 bugs, Process Failures #1/#3/#4, Test fixture gap.

### RC-3: Controller Discipline Failure
- **Evidence**: Controller skipped all 34 review dispatches "for speed." Plan checkboxes never updated. No deviation tracking. Controller didn't read source files before dispatching subagents.
- **Impact**: The review system designed to catch exactly these issues was bypassed entirely. The controller made an unauthorized optimization that removed safety guarantees.
- **Downstream failures**: Process Failures #2/#5, all 3 bugs would have been caught by spec compliance review.

### RC-4: Subagent Feedback Loop Is Broken
- **Evidence**: Subagent concerns reported only in ephemeral response text. No persistent artifact for decisions, deferrals, or scope changes. TodoWrite tracks original tasks only, not deviations. DONE_WITH_CONCERNS status exists but concerns are never accumulated.
- **Impact**: Controller lost track of independent decisions. Dead code deferral, 4th-column data drop, and test fixture shape mismatch were all reported by subagents but not collected or reviewed.
- **Downstream failures**: Process Failure #5, Execution Gaps #2/#4.

### RC-5: No Completion Verification Gate
- **Evidence**: Plan checkboxes: 0/89 checked after execution. TestModeControls built but never wired. Dead code identified but not resolved. No end-to-end pipeline test.
- **Impact**: "Done" was declared based on subagent reports, not verified against the plan's actual requirements. A plan is not complete if its checkboxes aren't checked.
- **Downstream failures**: Execution Gaps #1/#2/#3, all 5 gaps.

### RC-6: Plan Quality Gaps
- **Evidence**: Plan contained 2800+ lines of "specific-looking code" with wrong type assumptions. Exception names drifted between plan sections. Write-scope partitioning was approximate. Legacy removal was planned but dependencies weren't verified.
- **Impact**: Subagents faithfully executed wrong instructions. Plan review didn't catch errors because the plan was too large and lacked mechanical verification checks.
- **Downstream failures**: Process Failure #1, Plan Review findings #5-#9, Codex Suggestions (all 11 rules).

---

## Issue Inventory

### From Lessons Learned (6 process failures)
| ID | Issue | Root Cause | Priority |
|----|-------|-----------|----------|
| LL-1 | Plan contained wrong code snippets | RC-6, RC-2 | P0 |
| LL-2 | Controller skipped all 34 reviews | RC-3 | P0 |
| LL-3 | Subagents didn't read source files | RC-2, RC-3 | P0 |
| LL-4 | TDD validated wrong assumptions | RC-2 | P0 |
| LL-5 | No deviation tracking mechanism | RC-4 | P1 |
| LL-6 | Plugin customizations lost on upgrade | Solved (fork) | Done |

### From Execution Gaps (5 gaps)
| ID | Issue | Root Cause | Priority |
|----|-------|-----------|----------|
| EG-1 | TestModeControls never wired into pages | RC-5 | P1 |
| EG-2 | Dead code removal deferred but not tracked | RC-4, RC-5 | P1 |
| EG-3 | Plan checkboxes never updated | RC-5 | P1 |
| EG-4 | 4th column data silently dropped | RC-4 | P2 |
| EG-5 | Test fixtures use wrong types | RC-2 | P0 |

### From Plan Review (9 findings, 4 categories)
| ID | Issue | Root Cause | Priority |
|----|-------|-----------|----------|
| PR-1 | LOC-WF rate mapping contradicted between docs | RC-6 | P1 |
| PR-2 | Gate severity reclassification undocumented | RC-6 | P2 |
| PR-3 | Balance sign convention missing from handoff | RC-6, RC-2 | P1 |
| PR-4 | Field mapping owned by neither document | RC-6 | P1 |
| PR-5 | Exception name drift (ModelTimeout vs ServiceUnavailable) | RC-6 | P2 |
| PR-6 | Exception list incomplete | RC-6 | P3 |
| PR-7 | Balance sign inversion not end-to-end traceable | RC-2, RC-6 | P1 |
| PR-8 | Amount type changed string→number (Gate 4 failures) | RC-2 | P0 |
| PR-9 | Gate 4 parser strictness unspecified | RC-6 | P2 |

### From Handoff Quality Recommendations (18 recommendations, 5 categories)
| ID | Issue | Root Cause | Priority |
|----|-------|-----------|----------|
| HQ-1.1 | No "Contract Constraints" section in handoffs | RC-2 | P0 |
| HQ-1.2 | No "Wrong Way / Right Way" examples | RC-2, RC-6 | P1 |
| HQ-1.3 | No explicit type annotations in sample output | RC-2 | P2 |
| HQ-2.1 | No "Decisions Still Open" table | RC-6 | P2 |
| HQ-2.2 | No document authority declaration | RC-6 | P2 |
| HQ-2.3 | No "Changes Since Handoff" changelog | RC-6 | P3 |
| HQ-3.1 | No machine-readable acceptance fixtures | RC-2 | P0 |
| HQ-3.2 | No "First Test" section | RC-2 | P0 |
| HQ-3.3 | No "Task 0: Contract Verification" | RC-2, RC-3 | P0 |
| HQ-4.1 | No data contract audit in plan review | RC-6 | P1 |
| HQ-4.2 | No reviewer's cheat sheet | RC-6 | P2 |
| HQ-4.3 | No contract trace in spec review | RC-2 | P2 |
| HQ-4.4 | No risk-tiered review levels | RC-3 | P1 |
| HQ-4.5 | No DEVIATIONS.md accumulator | RC-4 | P1 |
| HQ-5.1 | No audience-specific handoff structure | RC-6 | P3 |
| HQ-5.2 | No "Quick Start for Agents" routing | RC-6 | P3 |
| HQ-5.3 | No version-lock handoff against plan | RC-6 | P3 |

### From Codex Suggestions (11 plan quality rules)
| ID | Issue | Root Cause | Priority |
|----|-------|-----------|----------|
| CS-1 | Canonical names not verified against codebase | RC-6 | P1 |
| CS-2 | Reference hygiene — historical vs canonical mixed | RC-6 | P2 |
| CS-3 | Executable snippets not copy-safe | RC-6, RC-2 | P0 |
| CS-4 | Query cardinality not audited | RC-6 | P1 |
| CS-5 | Schema shape inconsistency (storage vs API naming) | RC-6 | P1 |
| CS-6 | Async API contract gaps | RC-6 | P1 |
| CS-7 | Spec lock — plans silently diverge from approved spec | RC-6 | P1 |
| CS-8 | Legacy removal not verified (grep/audit step) | RC-5, RC-6 | P1 |
| CS-9 | Subagent write-scope partitioning missing | RC-6, RC-3 | P0 |
| CS-10 | Handoff vs spec authority not declared | RC-6 | P2 |
| CS-11 | Copy-safe review addendum for reviewers | RC-6 | P1 |

### From User-Identified Issues (6 key issues)
| ID | Issue | Root Cause | Priority |
|----|-------|-----------|----------|
| UI-1 | Original plan file too large (2816 lines) | RC-1 | P0 |
| UI-2 | Subagents running out of context window | RC-1 | P0 |
| UI-3 | Controller not following plans with precision | RC-3 | P0 |
| UI-4 | Subagents not reporting full/clear feedback | RC-4 | P0 |
| UI-5 | Dead code not evaluated/documented/addressed | RC-4, RC-5 | P1 |
| UI-6 | No QA feedback/testing to ensure completion | RC-5 | P0 |

---

## Key Metrics

### M1: Plan Size (target: <800 lines per module)
- **Baseline**: 2816 lines (implementation plan), 1347 lines (design spec)
- **Measurement**: `wc -l` on generated plan files
- **Why**: Plans >800 lines exceed agent context capacity when combined with code context

### M2: Task Size (target: <200 lines of plan text per task)
- **Baseline**: Average ~165 lines/task but high variance (some tasks 300+)
- **Measurement**: Count lines between task headers in generated plans
- **Why**: Subagents need room for code context alongside task instructions

### M3: Review Completion Rate (target: 100%)
- **Baseline**: 0% (0/34 reviews executed)
- **Measurement**: Count reviews dispatched vs tasks completed in test runs
- **Why**: Reviews are the primary catch mechanism for implementation errors

### M4: Ground-Truth Verification (target: 100% of external-contract tasks)
- **Baseline**: 0% (no tasks verified against source schemas)
- **Measurement**: Count tasks with external contracts that include source file reads in prompt
- **Why**: Prevents the "assumed contract" class of bugs

### M5: Deviation Capture Rate (target: 100% of DONE_WITH_CONCERNS reports)
- **Baseline**: 0% (no persistent artifact for deviations)
- **Measurement**: Count deviations logged in DEVIATIONS.md vs DONE_WITH_CONCERNS reports
- **Why**: Makes plan-vs-reality drift visible

### M6: Plan Completion Verification (target: 100% checkboxes resolved)
- **Baseline**: 0/89 checkboxes checked after "complete" execution
- **Measurement**: Count checked vs total checkboxes in plan file after execution
- **Why**: A plan is not complete if its checkboxes aren't checked

### M7: Subagent Report Completeness (target: all 6 report sections present)
- **Baseline**: Unstructured, variable-quality reports
- **Measurement**: Parse subagent reports for required sections (status, implementation, tests, files, self-review, concerns)
- **Why**: Incomplete reports hide issues from the controller

---

## Improvement Iterations

### Iteration 1: Plan Decomposition & Module System
**Skills Modified**: `writing-plans/SKILL.md`
**Goal**: Plans decompose into independent modules of <800 lines. Each module is a self-contained execution unit with its own file map, task list, and acceptance criteria.
**Changes**:
- Add plan size gate: if plan exceeds 800 lines, decompose into modules
- Add module template with required sections (goal, file map, contract references, tasks, acceptance criteria)
- Add cross-module dependency declaration
- Integrate Codex Suggestions CS-9 (write-scope partitioning) as a required plan section
**Test**: Generate a modular plan from the reconciliation spec. Compare module count, size, and completeness vs the monolithic v1.0 plan.
**Evaluation Metrics**: M1, M2

### Iteration 2: Ground-Truth Anchoring
**Skills Modified**: `writing-plans/SKILL.md`, `subagent-driven-development/SKILL.md`
**Goal**: Every plan that consumes external contracts includes a Task 0 (contract verification) and ground-truth fixtures. Controller digests source files before dispatching subagents.
**Changes**:
- Add "Task 0: Contract Verification" as mandatory first task pattern (HQ-3.3)
- Add "First Test" section requirement to plan template (HQ-3.2)
- Add "Contract Constraints" section requirement (HQ-1.1)
- Add controller directive: read source files referenced in plan before dispatching any subagent (LL-3)
- Add TDD fixture requirement: fixtures must be derived from real output, not invented (LL-4, EG-5)
**Test**: Review the reconciliation spec's handoff package. Would the improved plan template have caught the string-vs-numeric mismatch?
**Evaluation Metrics**: M4

### Iteration 3: Controller Discipline & Review Enforcement
**Skills Modified**: `subagent-driven-development/SKILL.md`
**Goal**: Controller cannot skip reviews, must track deviations, must update plan status.
**Changes**:
- Add explicit anti-skip language with "NEVER" directives for review steps (LL-2, UI-3)
- Add review-skip prevention: before marking task complete, verify both reviews ran
- Add risk-tiered review levels (HQ-4.4): full review for external contracts, spec-only for complex logic, minimum spec review for all
- Add DEVIATIONS.md accumulator requirement (HQ-4.5, LL-5)
- Add plan checkpoint update requirement: controller must update plan checkboxes as tasks complete (EG-3)
- Add dead code / deferred work tracking requirement (UI-5, EG-2)
**Test**: Simulate a controller run with a mock task list. Verify review enforcement, deviation logging, and checkpoint updates.
**Evaluation Metrics**: M3, M5, M6

### Iteration 4: Subagent Feedback Structure
**Skills Modified**: `implementer-prompt.md`, `spec-reviewer-prompt.md`, `code-quality-reviewer-prompt.md`
**Goal**: Subagent reports are structured, complete, and actionable. Controller can mechanically verify report completeness.
**Changes**:
- Define mandatory report schema with 6 required sections (UI-4)
- Add "Source Files Read" section to implementer report (must list files read before coding)
- Add "Deviations from Plan" section (decisions made independently, things skipped, things deferred)
- Add "Dead Code / Cleanup Needed" section (UI-5)
- Add "Contract Verification" section (did implementation match source contracts?)
- Strengthen spec reviewer to check for report completeness
- Add "Wrong Way / Right Way" examples for most common failure modes (HQ-1.2)
**Test**: Dispatch a test implementer subagent with a small task from the reconciliation plan. Evaluate report completeness against the schema.
**Evaluation Metrics**: M7

### Iteration 5: Completion Verification & QA Gate
**Skills Modified**: `subagent-driven-development/SKILL.md`, potentially new `completion-audit` skill
**Goal**: No implementation is declared complete without a mechanical QA gate that verifies every plan requirement.
**Changes**:
- Add "Completion Audit" phase after all tasks: dispatch auditor subagent that reads the plan checkboxes, verifies each is checked, and traces each requirement to implementation
- Add "Contract Audit" step: trace every field from source schema through implementation (post-implementation)
- Add "Integration Test" requirement: at least one end-to-end test with real data shapes
- Add "Deferred Work Summary" gate: DEVIATIONS.md must be reviewed and all items dispositioned before merge
- Integrate CS-8 (legacy removal verification) as a completion check
**Test**: Apply the completion audit to the existing reconciliation implementation. Count issues found.
**Evaluation Metrics**: M6, UI-6

### Iteration 6: Plan Quality Rules Integration
**Skills Modified**: `writing-plans/SKILL.md`, plan reviewer templates
**Goal**: Integrate all 11 Codex Suggestions as mechanical verification rules in the plan review process.
**Changes**:
- Add all CS-1 through CS-11 as required review checks
- Structure as a reviewable checklist (not prose) so the plan reviewer subagent can verify each mechanically
- Add "Cross-Document Consistency Audit" requirement (PR findings)
- Add "Spec Lock" enforcement: plans must reference specific spec version and flag any intentional divergence (CS-7)
**Test**: Run the enhanced plan reviewer against the v1.0 reconciliation implementation plan. Count issues found vs issues that were found post-hoc.
**Evaluation Metrics**: M1 (indirectly — better plans are smaller), M4

---

## Execution Approach

Each iteration follows the same cycle:

1. **Plan**: Document the specific skill file changes with before/after diffs
2. **Implement**: Dispatch subagent to make the changes (new versioned files, not modifying originals)
3. **Test**: Run the modified skill against the reconciliation test case
4. **Evaluate**: Measure metrics, document results, identify what worked and what didn't
5. **Improve**: Incorporate learnings into the next iteration

### File Versioning Convention
- Modified skills: `skills/<name>/SKILL-v0.1.md` (preserves original)
- New skills: `skills/<name>/SKILL.md` in new directories
- Test results: `docs/plans/2026-03-23-sdd-improvement-results-<iteration>.md`

### Test Protocol
For each iteration, the test is: "If we had used the improved skill when implementing statement reconciliation, would the specific issues from the post-mortem have been prevented?"

This is evaluated by:
1. Generating/reviewing artifacts with the improved skill
2. Checking whether the improvement would have caught specific catalogued issues
3. Documenting which issues are now covered and which remain

---

## Success Criteria

The improvement cycle is successful when:
- Plans decompose into modules of <800 lines each (M1)
- Tasks are <200 lines of plan text each (M2)
- Review completion rate is 100% (M3)
- All external-contract tasks have ground-truth verification (M4)
- All subagent deviations are captured in a persistent artifact (M5)
- Plan checkboxes are 100% resolved after execution (M6)
- Subagent reports contain all required sections (M7)
- A re-run of the reconciliation implementation with improved skills would have caught all 3 bugs and all 5 execution gaps before they reached testing

---

## Appendix: Full Issue Cross-Reference

| Root Cause | Issues | Addressed By Iteration |
|-----------|--------|----------------------|
| RC-1: Plan size | UI-1, UI-2 | Iter 1 |
| RC-2: No ground-truth | LL-1, LL-3, LL-4, EG-5, PR-3, PR-7, PR-8, HQ-1.1, HQ-3.1, HQ-3.2, HQ-3.3, CS-3 | Iter 2 |
| RC-3: Controller discipline | LL-2, UI-3, HQ-4.4, CS-9 | Iter 3 |
| RC-4: Feedback loop | LL-5, EG-2, EG-4, UI-4, UI-5, HQ-4.5 | Iter 4 |
| RC-5: No completion gate | EG-1, EG-3, UI-6, CS-8 | Iter 5 |
| RC-6: Plan quality | PR-1 through PR-9, CS-1 through CS-11, HQ-1.2, HQ-2.x, HQ-4.x | Iter 6 |
