# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Task 1 | IndependentDecision | Moved os/subprocess/sys/textwrap imports and VALIDATORS path constant to module level instead of inline mid-file; dropped unused tempfile import. Content/behavior unchanged from plan. | Accepted |
| Task 1 | IndependentDecision | Repo pre-commit hook (formatter) reformatted plan.py/test_plan_model.py slightly at commit time (multi-line Literal wrap, wrapped path join, whitespace). Content/behavior unchanged; all 56 tests in file pass post-format. | Accepted |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]

| 2026-08-04T21:45:49Z | Module transition: Consent model + YAML coercion (N83) → Plan-time consent UX + author docs | FYI | Accepted |

| 2026-08-04T22:05:12Z | Module transition: Plan-time consent UX + author docs → Discoverability sweep + kill switch | FYI | Accepted |
