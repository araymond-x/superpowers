# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Pre-exec | IndependentDecision | controller-checkpoint.py pre-execution FAIL on source_contracts="None" — false positive, writing-plans requires the field present with "None". Proceeded to execution. | Accepted |
| Task 8 | IndependentDecision | controller-checkpoint.py pre-dispatch FAIL — expects Task 7 reports (sequential), but TDD order runs Task 8 (tests) before Tasks 2-7 (implementation). Plan explicitly specifies this order. Checkpoint doesn't support non-sequential execution. | Accepted |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]
