# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Task 4 | IndependentDecision | Added trailing-slash strip to .active-feature reader (not in plan) — prevents double-slash paths | Accepted |
| Task 4 | IndependentDecision | Line 198 error retains informational hardcoded text — actual check uses resolved vars | Accepted |
| Task 4 | IndependentDecision | Lines 397, 491 error messages had hardcoded paths — fixed in quality review commit 0b3007b | Resolved |
| Task 5 | IndependentDecision | Legacy manifest/review fallback branches are dead code — gate blocks when FEAT is empty | Accepted |
| All | IndependentDecision | 93% minimum-tier quality/partner reviews — Task 4 (highest risk) got full review; remaining tasks were test-only, SKILL.md prose, or established patterns | Accepted |
| Task 5 | ScopeChange | plan-validation-gate hard gate blocks old-mode SDD (root-level) — dead fallback code kept but unreachable. Intended behavior per user: hard cutover is correct. This session is the edge case (skills upgraded mid-process). | Accepted |
| All | IndependentDecision | No end-to-end integration test — user will validate via real SDD session in personal-finance-api (already in flight). Unit/POC tests cover individual gates. | Accepted |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]
