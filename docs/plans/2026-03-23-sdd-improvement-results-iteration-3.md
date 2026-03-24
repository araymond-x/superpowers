# SDD Improvement Results — Iteration 3: Controller Discipline & Review Enforcement

**Date**: 2026-03-23
**Skill Modified**: `skills/subagent-driven-development/SKILL-v0.1.md` (523 lines, up from 277)
**Combined With**: `skills/writing-plans/SKILL-v0.1.md` (Iteration 1)
**Baseline**: `skills/subagent-driven-development/SKILL.md` (original, preserved)

---

## Changes Made

| Addition | Purpose |
|----------|---------|
| Plan Ingestion Phase (6 steps) | Controller reads full plan, source files, creates DEVIATIONS.md before any dispatch |
| Task 0 Enforcement (blocking) | Contract verification must pass before any implementation task starts |
| Contract Constraints Passthrough | Verbatim injection of contract facts into every implementer prompt |
| Review Enforcement — Non-Negotiable | 7 named rationalizations invalidated; mandatory review sequence; risk-tiered depth |
| DEVIATIONS.md Accumulator | Persistent artifact for concerns, deferrals, independent decisions, scope changes |
| Plan Status Tracking | Controller updates plan checkboxes after each task |
| Pre-Completion Gate (5 checks) | All tasks, checkboxes, deviations, reviewer context, contract trace verified |
| Extended Example Workflow | Shows Task 0 catch, DEVIATIONS.md logging, pre-completion gate check |
| Expanded Red Flags | 5 new NEVER items for Task 0 bypass, constraint omission, deviation skip |

---

## Combined Evaluation (writing-plans v0.1 + SDD v0.1)

| Verdict | Iter 1 Only | Combined (Iter 1+3) | Change |
|---------|------------|---------------------|--------|
| PREVENTED | 6 | 9 | +3 (PF-2, PF-5, EG-3) |
| SUBSTANTIALLY ADDRESSED | 0 | 2 | +2 (PF-3, UI-3) |
| PARTIALLY ADDRESSED | 3 | 8 | +5 (promoted from NOT ADDRESSED) |
| NOT ADDRESSED | 11 | 1 | -10 |

### Issue-Level Results

| Issue ID | Issue | Iter 1 | Combined | Explanation |
|----------|-------|--------|----------|-------------|
| BUG-1 | Missing error_details field | PARTIAL | PARTIAL | Depends on contract completeness |
| BUG-2 | Gate 4 float vs string | PREVENTED | PREVENTED | Task 0 + fixtures |
| BUG-3 | Balance/rate parsing | PREVENTED | PREVENTED | Task 0 + fixtures |
| PF-1 | Wrong code snippets | PARTIAL | PARTIAL | Ingestion + review help; still advisory |
| PF-2 | Controller skipped 34 reviews | NOT | **PREVENTED** | Review Enforcement section directly targets this |
| PF-3 | Subagents didn't read source files | PARTIAL | **SUBSTANTIAL** | Controller reads source files + Constraints passthrough |
| PF-4 | TDD wrong assumptions | PREVENTED | PREVENTED | Task 0 fixtures |
| PF-5 | No deviation tracking | NOT | **PREVENTED** | DEVIATIONS.md with append triggers + disposition gate |
| EG-1 | TestModeControls unwired | NOT | PARTIAL | Pre-completion gate checks checkboxes; depends on plan quality |
| EG-2 | Dead code untracked | NOT | PARTIAL | DEVIATIONS.md surfaces it; doesn't guarantee removal |
| EG-3 | Plan checkboxes never updated | NOT | **PREVENTED** | 3 enforcement points: flow diagram, tracking section, gate |
| EG-4 | 4th column data dropped | NOT | PARTIAL | Constraints passthrough; depends on plan documenting columns |
| EG-5 | Test fixtures wrong types | PREVENTED | PREVENTED | Task 0 fixtures |
| UI-1 | Plan too large | PREVENTED | PREVENTED | 800-line gate |
| UI-2 | Subagents out of context | PREVENTED | PREVENTED | Module + task limits |
| UI-3 | Controller not following plans | NOT | **SUBSTANTIAL** | 6-step ingestion, NEVER directives, structured flow |
| UI-4 | Poor subagent feedback | NOT | PARTIAL | DEVIATIONS.md helps; report format not yet standardized |
| UI-5 | Dead code not addressed | NOT | PARTIAL | Same as EG-2 |
| UI-6 | No QA for completion | NOT | PARTIAL | Pre-completion gate helps; no full test suite mandate |

---

## Root Cause Coverage

| Root Cause | Status | Notes |
|-----------|--------|-------|
| RC-1: Plan size | Fully addressed | 800-line gate, 200-line task limit |
| RC-2: No ground-truth | Substantially addressed | Task 0, Contract Constraints, fixtures |
| RC-3: Controller discipline | Substantially addressed | Review enforcement, ingestion, gate |
| RC-4: Feedback loop | Partially addressed | DEVIATIONS.md exists; report format unstructured |
| RC-5: Completion gate | Substantially addressed | 5-condition pre-completion gate |
| RC-6: Plan quality | Partially addressed | 9 new review categories; advisory |

---

## Identified Weaknesses in Combined v0.1

1. **Skill complexity** — SDD v0.1 is 523 lines with multiple flow graphs, 6 ingestion steps, 4 status handlers, 5 gate conditions. Risk: controller satisfies the letter (creates DEVIATIONS.md, declares tiers) without following the intent.

2. **Review tier self-assessment** — Controller declares its own review tier. Minimum tier allows code quality skip. Given documented history of controller rationalizing, minimum may become default.

3. **DEVIATIONS.md is append-only by instruction** — No structural protection against accidental overwrite.

4. **Contract Constraints passthrough is unverified** — Spec reviewer is not told to check that the implementer received constraints.

5. **Task 0 blocking relies on controller self-discipline** — Same actor that skipped 34 reviews can skip Task 0.

6. **Modular plan ingestion undefined** — SDD v0.1 describes single-document ingestion. No guidance for multi-module plans from writing-plans v0.1's module system.

7. **No full test suite mandate** — Pre-completion gate has contract trace but no "run all tests from clean state" step.

---

## Recommendations for Iteration 4

1. **Standardize implementer report format** (RC-4) — Mandatory structured fields in implementer-prompt.md
2. **Spec reviewer verifies Constraints were received** — Converts passthrough from honor-system to verified checkpoint
3. **Harden minimum review tier** — Either remove or require spec reviewer confirmation of no external dependencies
4. **Modular plan ingestion guidance** — Add SDD section for multi-module execution
5. **QA gate: full test suite** — Add 6th pre-completion condition: all tests pass from clean state
