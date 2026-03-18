# Statement Reconciliation Development — Lessons Learned

**Date**: 2026-03-16 14:55 MST
**Feature**: Statement Cycle Reconciliation (Phase 8)
**Plan**: `docs/plans/2026-03-15-statement-reconciliation-implementation-v1.0.md`
**Spec**: `docs/plans/2026-03-15-statement-reconciliation-ui-design.md` (v1.1, 75 decisions)
**Branch**: `feature/statement-reconciliation` (20 commits)

---

## What Happened

We executed a 17-task implementation plan across backend (9 tasks) and frontend (8 tasks) using the superpowers subagent-driven-development workflow. The plan was generated from a thorough 75-decision design spec. 20 commits were produced. During localhost testing, we discovered 3 bugs and several execution gaps.

## Bugs Found During Testing

| Bug | Root Cause | How Discovered |
|---|---|---|
| **500 on job status polling** | `AsyncJobStatus` class missing `error_details` field that the router tried to access | Manual testing — modal hung on "Starting" |
| **Gate 4 rejected all valid amounts** | `validate_amount_format` used `isinstance(float)` but Bedrock schemas define amounts as `"type": "string"` with commas | Real Bedrock call returned `"-11,350.00"` |
| **Balance and rate parsing failed on strings** | `_compute_balances` called `float()` directly on `"1,500.00"`, `_map_rate_fields` stored raw strings to NUMERIC columns | Found during field-by-field audit |

**Common thread**: All three bugs stem from the same disconnect — the handoff schemas define every field as `"type": "string"`, but the implementation assumed numeric types throughout.

## Execution Gaps (Not Bugs, But Missing Work)

| Gap | What Should Have Happened |
|---|---|
| **TestModeControls never wired into pages** | Task 15 built the components but no page imports them — fixture picker is unreachable from the UI |
| **Dead code removal deferred** | Task 10 planned to remove old hooks/API functions, but they're still used by `StatementsPage.tsx` — subagent correctly skipped but the plan was wrong |
| **Plan checkboxes never updated** | All 89 `- [ ]` items remain unchecked — the plan file doesn't reflect completion status |
| **4th column data silently dropped** | `cardholder`, `order_number`, `check_number`, `reference_number` are extracted by Bedrock but not consumed — noted as "MVP deferral" but not tracked |
| **Test fixtures use numeric amounts** | Fixtures don't match real Bedrock output format (strings with commas), so they don't catch the parsing bugs they're supposed to test |

## Process Failures

### 1. Plan contained wrong code snippets

The implementation plan had 2800+ lines of specific-looking code that encoded wrong assumptions (numeric types). Subagents executed those assumptions faithfully. The plan review step should have caught this by cross-referencing the handoff schema files.

### 2. Controller skipped subagent reviews

The subagent-driven-development skill requires spec compliance + code quality review after each task. All reviews were skipped for speed (would have been 34 extra subagent dispatches). This is where the string/numeric mismatch would have been caught.

### 3. Subagents didn't read source files

The controller gave subagents the plan text but not the actual handoff schemas. Task 3's subagent wrote validation code from the plan's description without ever reading the schema files that define `"type": "string"`.

### 4. TDD validated wrong assumptions

Tests passed because they were written against the same wrong contract. Testing against real Bedrock output (or the handoff sample files) would have caught it immediately.

### 5. No mechanism for tracking subagent deviations

When subagents made independent decisions (skip dead code removal, use `size="lg"` instead of `"md"`, leave unused types), those decisions were reported in response text but not accumulated into any persistent artifact.

### 6. Plugin customizations silently lost

The CLAUDE.md enforcement modifications (added to superpowers 4.3.1) were overwritten when the plugin updated to 5.0.2. Only 1 of 3 safety layers was active during this implementation. See `docs/subagents/subagent-claude-md-enforcement.md` for the original modifications.

## Improvements Identified

| Improvement | What It Prevents |
|---|---|
| **Ground-truth fixtures before implementation** | Create test fixtures from real system output (handoff samples) before any code is written. Makes wrong type assumptions fail immediately. |
| **Controller reads source files, not just plan text** | Don't delegate understanding of external contracts to subagents. Digest handoff schemas and include concrete facts (all fields are strings) in prompts. |
| **Don't skip reviews** | At minimum, do spec compliance review on tasks that consume external contracts. The cost of 34 review dispatches is less than debugging 3 production bugs. |
| **Deviation register** | A persistent `DEVIATIONS.md` that the controller appends to whenever a subagent reports `DONE_WITH_CONCERNS` or the controller observes a scope change. Reviewed before merge. |
| **Smaller plan scope** | 17 tasks with parallel subagents is too many degrees of freedom. 5-7 tasks where the controller reads every file would catch more issues. |
| **Post-implementation contract audit** | Standard step before merge: trace every field from source schema through implementation to verify correct parsing. What we did manually should be automated. |
| **Fork plugin for durable customizations** | CLAUDE.md rules for project-specific behavior, forked plugin for workflow-level customizations. Don't patch plugin cache files. |

## The Core Lesson

**Detailed plans and TDD don't prevent bugs when the contract is wrong.** The plan was thorough, the tests were comprehensive, and TDD was followed — but everything was built against an assumed contract (numeric types) that differed from the actual contract (string types). The fix is to anchor implementation to ground-truth data samples before writing any code or tests.
