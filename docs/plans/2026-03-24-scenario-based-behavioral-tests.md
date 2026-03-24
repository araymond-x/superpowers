# Scenario-Based Behavioral Tests — Future Implementation Plan

**Date**: 2026-03-24
**Status**: Planned (not yet implemented)
**Priority**: High — tests the exact failure modes from the Statement Reconciliation incident
**Location**: `tests/ARaymond-skill-behavior/` (extend existing suite)

---

## What Exists Today

- **Knowledge recall tests** (`test-sdd-content.sh`, `test-custom-skills.sh`): Ask Claude questions about skill content, assert keywords in response. Tests that Claude loaded and can describe the skills.
- **Invocation tests** (`test-explicit-requests.sh`, `test-implicit-triggers.sh`): Test that skills trigger from various prompt phrasings. Tests the auto-invocation behavior.

## What's Missing

**Decision-making tests** that verify Claude makes the right choice when faced with a scenario our customizations were designed to handle. These test actual behavior under pressure, not just knowledge of rules.

---

## Proposed Test Scenarios

### Handoff Acceptance (5 scenarios)

| ID | Scenario | Input | Expected Behavior | Customization |
|----|----------|-------|-------------------|---------------|
| HA-1 | Buried contract info | README with field types at line 200 | FAIL or ACCEPTED_WITH_REMEDIATION | Contract summary in first 50 lines |
| HA-2 | Non-executable snippet | Code snippet missing imports | Flag as not executable | Executable snippet check |
| HA-3 | Contextually illustrative snippet | Snippet under "How to Use" header, no label | Accept as contextually illustrative | F7: third snippet category |
| HA-4 | Missing fixtures | Handoff with no samples/ directory | Flag as BLOCKING | Acceptance fixtures check |
| HA-5 | Producer mode trigger | "I need to create a handoff package" | Load skill AND read handoff-package-spec.md | Producer mode + auto-discovery |

### Controller Discipline (4 scenarios)

| ID | Scenario | Input | Expected Behavior | Customization |
|----|----------|-------|-------------------|---------------|
| CD-1 | Skip review pressure | "This task was simple, skip the review" | Refuse — cite review enforcement | Review enforcement |
| CD-2 | Task 0 bypass | Plan with Source Contracts, "start with Task 1" | Insist Task 0 first | Task 0 blocking |
| CD-3 | DONE_WITH_CONCERNS routing | Report with DONE_WITH_CONCERNS status | Log to DEVIATIONS.md before review | DEVIATIONS.md accumulator |
| CD-4 | TOO_LARGE task | Task that estimate script flags | Must be split, not dispatched | Context budget management |

### Plan Writing (4 scenarios)

| ID | Scenario | Input | Expected Behavior | Customization |
|----|----------|-------|-------------------|---------------|
| PW-1 | Large plan decomposition | 20-task feature request | Mention modules, cite 800-line limit | Plan modularization |
| PW-2 | Replacement archetype | "Replaces existing CSV import" | Produce Code Footprint with Obsolete entries | Feature footprint |
| PW-3 | Unverified handoff | Reference unaccepted handoff package | Insist on handoff-acceptance first | Cross-skill gate |
| PW-4 | Two-layer validation | "validate-plan.py passed, are we good?" | No — reviewer dispatch also required | Two-layer validation |

### Subagent Feedback (3 scenarios)

| ID | Scenario | Input | Expected Behavior | Customization |
|----|----------|-------|-------------------|---------------|
| SF-1 | Incomplete report | Report missing Source Files Read + Contract Compliance | Flag incomplete, require re-dispatch | 9-section report |
| SF-2 | Dead code in review | Code with unused imports | Flag as blocking, not minor | Dead code blocking |
| SF-3 | Contract violation | Implementation using float where contract says string | Flag as [BLOCKING] [CONTRACT] | Contract verification |

### Spec Distillation (2 scenarios)

| ID | Scenario | Input | Expected Behavior | Customization |
|----|----------|-------|-------------------|---------------|
| SD-1 | Distillation trigger | After brainstorming, move to planning | Produce distilled spec first | Spec distillation step |
| SD-2 | Artifact detection | Distilled spec with "Options Considered" column | Flag as exploration artifact | Distillation review |

---

## Implementation Notes

- Each scenario needs a **fixture** (a crafted input that triggers the behavior) and an **assertion** (what to check in the response)
- Scenarios that test controller behavior (CD-1 through CD-4) may need multi-turn conversations
- Some scenarios can reuse existing upstream multiturn test infrastructure (`--continue` flag)
- Budget: ~18 API calls at ~90s each = ~27 minutes for the full suite
- Recommend implementing in priority order: CD (controller discipline) > HA (handoff) > PW (plan writing) > SF (feedback) > SD (distillation)
