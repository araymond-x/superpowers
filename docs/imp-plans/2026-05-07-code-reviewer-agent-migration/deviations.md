# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Task 1 | IndependentDecision | Implementer reported DEVIATIONS.md deletion included in commit — controller verified false: commit `8a3469d` contains only the 2 test files | Resolved |
| Task 6 | IndependentDecision | Implementer found and `git rm`'d `code-quality-reviewer-prompt-original.md` (dead backup file with zero consumers, contained stale `superpowers-code-reviewer` reference) | Accepted |
| Task 6 | IndependentDecision | Implementer removed dead `|superpowers-code-reviewer` alternation from `sdd-pre-dispatch-hook.sh:123` grep pattern (no behavior change — the alternation was unreachable after dispatch-type migration) | Accepted |
| All | ProcessDeviation | Minimum-tier quality reviews: 4/7 (57%) — Tasks 0 (verbatim script), 4 (docs-only), 5 (docs-only), 6 (file deletion). Minimum-tier partner reviews: 6/7 (86%). Justified: text-migration with no code logic; all behavioral changes (Tasks 1-3) got standard reviews | Accepted |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]
