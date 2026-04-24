# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Pre-Task | IndependentDecision | Created N/A placeholder reports for Task 0 (task-000-*) and dispatch log entries to satisfy pre-dispatch hook gate. Plan has no Task 0 (Source Contracts: None). Hook Check 4 assumes sequential tasks from 0 and Check 5 false-positives on "Source Contracts" text in older plan files' body text. | Accepted |
| Task 3 | IndependentDecision | Sequential ID check improved from sort-order-only (`ids != sorted(ids)`) to contiguous-range check (`ids != list(range(...))`). Plan's version would accept [0, 5] as "sequential" — the fix enforces contiguity. | Accepted |
| Task 8 | IndependentDecision | Used PYDANTIC_HANDOFF_DIR instead of HANDOFF_DIR in handoff-gate-hook.sh to avoid shadowing existing variable on line 51. | Accepted |
| Task 8 | IndependentDecision | Added exit-code-2 handling in check-handoff.sh (plan only showed exit-code-1 handling) for consistency with other hooks. | Accepted |
| Task 8 | BugFix | Quality review found `if ! cmd; then PYDANTIC_EXIT=$?` pattern broken in all 3 hooks — `$?` after `!` is always 0. Fixed with direct capture pattern. Used `|| PYDANTIC_EXIT=$?` in check-handoff.sh due to `set -e`. | Resolved |

## Obsolescence Verification Findings

| Finding | Location | Disposition |
|---------|----------|-------------|
| Legacy regex patterns (`TASK_HEADER_RE`, `MODULE_HEADER_RE`, `check_sections()`) still run unconditionally for both frontmatter and non-frontmatter plans | `validate-plan.py:48-51, 206-268, 389-406` | Kept -- Phase 7 cleanup |
| First-50-lines contract grep in check-handoff.sh runs alongside Pydantic path | `check-handoff.sh:32-48` | Kept -- Phase 7 cleanup |
| "First 50 lines" instruction in handoff-acceptance skill and spec | `handoff-acceptance/SKILL.md:47`, `handoff-package-spec.md:225,229` | Kept -- Phase 7 cleanup (handoff skill, not plan templates) |
| All 3 prompt templates reference YAML frontmatter format | `writing-plans/SKILL.md:216`, `handoff-package-spec.md:26,30`, `subagent-driven-development/SKILL.md:162` | Verified -- cutover complete |
| No prompt template instructs old format exclusively | Grep of `skills/` directory | Verified -- no regression |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]
