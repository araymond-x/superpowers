---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code. Supports modular plans for large features.
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This skill is designed to follow `superpowers:brainstorming`, which produces a spec and sets up a worktree. If invoked directly (skipping brainstorming), provide:
- Path to the spec or requirements document
- Path to any handoff packages (verify they passed `superpowers:handoff-acceptance` first)
- The working directory for the plan output

**Save plans to:** `docs/imp-plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## Plan Size & Modularization

**If the plan will exceed 800 lines, decompose it into independent modules.**

A single massive plan file exhausts subagent context windows, makes parallelism impossible, and obscures dependencies. Modular plans solve all three.

### Module File Naming

```
docs/imp-plans/YYYY-MM-DD-<feature>-plan.md          ← parent plan
docs/imp-plans/YYYY-MM-DD-<feature>-module-1-<name>.md
docs/imp-plans/YYYY-MM-DD-<feature>-module-2-<name>.md
```

### Module Decomposition Criteria

Decompose by whichever boundary is most natural:

- **Layer boundary** — backend vs. frontend vs. infrastructure
- **Feature boundary** — each independently shippable capability
- **External contract boundary** — each module that consumes a different external schema or API

### Parent Plan Requirements

The parent plan is a coordination document, not an implementation plan. It must include:

1. **Module inventory** — list of all module files and their goals
2. **Module Dependency Graph** — which modules block which
3. **Parallel execution annotations** — modules with disjoint write sets can run in parallel
4. **Shared contract section** — any external schemas consumed by multiple modules

```markdown
## Module Dependency Graph

Module 1 (DB schema)
  └── Module 2 (backend API) ← depends on Module 1
  └── Module 3 (frontend)   ← depends on Module 2
      Module 4 (tests)      ← depends on Module 2 and Module 3

Parallel candidates: Module 2 and Module 3 may not be parallel
(Module 3 depends on Module 2's API contract).
```

### Each Module Must Contain

- Its own **Goal** statement
- Its own **Source Contracts** and **Contract Constraints**
- Its own **File Map**
- Its own **Write-Scope Partitioning** table
- Its own **Tasks** (including Task 0 if it has external contracts)
- Its own **Acceptance Criteria**

See the Module Template section at the end of this skill for the full format.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility. Subagents implement one task at a time. A file with multiple responsibilities will be partially owned by multiple tasks, requiring serialization.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

**Task size limit:** The plan text for a single task (from its header to the next task header) should be under 200 lines. If a task exceeds 200 lines, it likely needs to be split into subtasks. Large tasks exhaust subagent context windows, leaving less room for actual code. Prefer many small focused tasks over few large complex ones.

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Source Contracts:** [List of external schemas, APIs, handoff packages this plan consumes. Write "None" if this plan is self-contained.]

**Contract Constraints:** [Non-negotiable facts from source contracts — types, formats, invariants. Write "None" if no external contracts.]

**Feature Archetype:** [Greenfield | Replacement | Extension | Refactor | Migration]

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| New | `path/to/new/file` | Create | — |
| Obsolete | `path/to/old/function` | Remove after verification | Check: [consumers] |
| Retained | `path/to/kept/function` | Keep | — |
| Modified | `path/to/changed/file` | Extend/modify | [existing consumers] |

---
```

The **Source Contracts** field forces you to declare upfront what external data shapes this plan depends on. The **Contract Constraints** field forces you to record the non-negotiable facts before any implementation begins — field types, required formats, invariants the code must preserve.

If either field is "None", verify that the plan truly has no external dependencies before proceeding.

If Source Contracts reference a handoff package from another agent or team, verify it has passed `superpowers:handoff-acceptance` before writing the plan. If no acceptance report exists, run the acceptance checklist first — do not plan against an unverified handoff.

## Write-Scope Partitioning

**Every plan intended for subagent execution should include this section before the task list.**

```markdown
## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 0        | tests/fixtures/...  | contracts/...   | —          |
| Task 1        | src/models/foo.py   | config.py       | Task 0     |
| Task 2        | src/routes/foo.py   | src/models/foo.py | Task 1   |
| Task 3        | tests/test_foo.py   | src/routes/foo.py | Task 2   |
```

Rules:
- No two parallel tasks may write to the same file.
- If two tasks must touch the same file, they MUST be serialized (one depends on the other).
- Each file appears in exactly one task's "Owned Files" column.

This table is the authoritative source of truth for parallelism decisions. If the write sets overlap, the tasks are not parallel candidates regardless of how they look otherwise. Once you have written the Write-Scope Partitioning table, treat task ownership as settled. Do not revise file assignments mid-plan.

## Feature Footprint

**Every plan should classify its feature archetype and map its code footprint.**

### Feature Archetypes

| Archetype | Description | Obsolescence Pattern |
|-----------|-------------|---------------------|
| **Greenfield** | New capability, no existing code replaced | No obsolescence — purely additive |
| **Replacement** | New code replaces existing functionality | Explicit: list what becomes obsolete, verify no other consumers |
| **Extension** | Adds to existing capability | Partial: some interfaces change, existing consumers must continue working |
| **Refactor** | Restructures without changing behavior | Full: old structure obsolete, all consumers migrated |
| **Migration** | Moves data/interfaces from old to new | Phased: co-existence then removal |

### Why This Matters

Without an explicit footprint, subagents discover dependencies at runtime — one agent tries to delete a function, finds it's still referenced, defers the deletion, and the deferral gets lost in ephemeral context. The footprint makes this visible at planning time.

### Obsolescence Verification

For **Replacement**, **Refactor**, and **Migration** archetypes, the plan MUST include an **Obsolescence Verification Task** that:
1. Greps for every function/component marked "Obsolete" in the footprint
2. Verifies no remaining consumers outside the plan's scope
3. Removes confirmed dead code OR logs blockers to DEVIATIONS.md
4. Final grep audit to confirm no stale references

This task should be scheduled AFTER all implementation tasks are complete but BEFORE the Pre-Completion Gate.

For **Greenfield** and **Extension** archetypes, the footprint still documents what's created and modified — it just won't have an "Obsolete" category.

### Obsolescence Verification Task Template

See `references/obsolescence-verification-template.md` for the complete Obsolescence Verification task template with grep commands and DEVIATIONS.md logging. Copy it into your plan for Replacement/Refactor/Migration archetypes.

## Ground-Truth Fixtures

**If the plan has any Source Contracts (external APIs, schemas, handoff packages), include a Task 0 (Contract Verification).**

Task 0 is a contract verification task. It reads actual source files, extracts concrete facts, and creates test fixtures from real data. It is a blocking dependency — no other task may start until Task 0 completes and its contract test passes.

Rationale: Plans written from descriptions of contracts (rather than the contracts themselves) introduce type drift, field name drift, and format assumptions. Task 0 anchors all subsequent implementation to ground truth before any code is written.

### Task 0 Template

See `references/task-0-template.md` for the complete Task 0: Contract Verification task template with all 6 steps. Copy it into your plan and fill in the bracketed placeholders.

Before writing tasks, read the core files your plan will modify. After each read, assess whether you now understand the relevant interfaces. When you can answer "where does this logic live?" for each planned task, you have enough context.

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Remember
- Exact file paths always — subagents receiving a task prompt do not have your codebase knowledge. An ambiguous path forces them to search the repo before implementing.
- Complete code in every step — if a step changes code, show the code. Vague instructions leave the implementation decision to the subagent, who has no context about your validation patterns or error message formats.
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD, frequent commits
- Feature archetype declared in header
- Code Footprint table with obsolete items and their dependencies
- Obsolescence Verification task for Replacement/Refactor/Migration archetypes

## Plan Review Loop

After writing the complete plan:

### Automated Plan Validation

Before dispatching the plan reviewer, run the deterministic plan validator:

```bash
python ~/.claude/skills/superpowers/subagent-driven-development/scripts/validate-plan.py --plan-file <plan.md>
```

This checks: plan size (<800 lines), task size (<200 lines), required sections (Source Contracts, Contract Constraints, Feature Archetype, Code Footprint, Write-Scope Partitioning), Task 0 presence when Source Contracts exist, and checkbox syntax. Fix any FAIL or WARNING issues before dispatching the human reviewer.

**Two-layer validation:** The `validate-plan.py` script catches structural issues (missing sections, oversized tasks, absent Task 0). It does NOT catch semantic issues — type mismatches between plan snippets and source contracts, tolerance inconsistencies, implicit return type conventions, or cross-document drift. A structural PASS does not mean the plan is correct.

The plan-document-reviewer dispatch below is the semantic layer. It reads source contracts independently and compares them against the plan's code snippets, field names, and assumptions. Both layers are required — do not skip the reviewer dispatch because the script passed.

1. Dispatch a single plan-document-reviewer subagent (see plan-document-reviewer-prompt.md) with precisely crafted review context — never your session history. This keeps the reviewer focused on the plan, not your thought process.
   - Provide: path to the plan document, path to spec document

### Reviewer Dispatch Example

```
Agent tool (general-purpose):
  description: "Review plan document"
  prompt: |
    [Fill in the template from plan-document-reviewer-prompt.md with:]
    - PLAN_FILE_PATH: path to the plan you wrote
    - SPEC_FILE_PATH: path to the spec (or distilled spec)
    - SOURCE_FILE_PATHS: paths to handoff/contract files (or "None")
```

2. If Issues Found: fix the issues, re-dispatch reviewer for the whole plan
3. If Approved: proceed to execution handoff

**Review loop guidance:**
- Same agent that wrote the plan fixes it (preserves context)
- If loop exceeds 3 iterations, surface to human for guidance
- Reviewers are advisory — explain disagreements if you believe feedback is incorrect

### Reviewer Checklist

Dispatch the reviewer with the following expanded checklist. The reviewer checks all categories and flags only issues that would cause real problems during implementation.

| Category | What to Check |
|----------|---------------|
| Completeness | TODOs, placeholders, incomplete tasks, missing steps |
| Spec Alignment | Plan covers spec requirements, no major scope creep |
| Task Decomposition | Tasks have clear boundaries, steps are actionable |
| Buildability | Could an engineer follow this plan without getting stuck? |
| Contract Accuracy | Do code snippets match source contract types? Are field types verified against source files, not descriptions? |
| Canonical Names | Do enum values, source names, and status strings match the actual codebase — not invented names? |
| Snippet Safety | Are code snippets copy-safe? Required imports included? Paths match repo conventions? |
| Query Cardinality | Are JOINs verified for 1:1 vs 1:many? History rows handled correctly? |
| Schema Consistency | Do storage and API schemas use consistent naming? Is field mapping explicit? |
| Write-Scope Disjointness | Do parallel tasks have disjoint write sets? Does the partitioning table reflect actual task boundaries? |
| Spec Lock | Does the plan diverge from the approved spec? Are any deviations documented and intentional? |
| Legacy Removal | Are removed features fully traced? Is there a grep step to catch stale references? |
| Cross-Document Consistency | Do handoff package, spec, and plan agree on types, field names, behaviors, and naming conventions? |

**Calibration:** Only flag issues that would cause real problems during implementation. An implementer building the wrong thing or getting stuck is an issue. Minor wording, stylistic preferences, and "nice to have" suggestions are not.

Approve unless there are serious gaps — missing requirements from the spec, contradictory steps, placeholder content, type mismatches against source contracts, or tasks so vague they cannot be acted on.

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/imp-plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:executing-plans
- Batch execution with checkpoints for review

---

## Module Template

See `references/module-template.md` for the complete module file template. Use when a plan is decomposed into modules (plan exceeds 800 lines or decomposes cleanly by boundary).
