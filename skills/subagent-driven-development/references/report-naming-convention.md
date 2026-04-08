# Report Naming Convention (enforced by hooks)

> Part of the subagent-driven-development skill. Referenced from SKILL.md.

All reports use **three-digit zero-padded sequential numbering** across all modules:

```
reports/task-000-implementer-report.md   (first task in the plan)
reports/task-000-spec-review.md
reports/task-000-quality-review.md
reports/task-001-implementer-report.md   (second task)
reports/task-001-spec-review.md
...
```

| Rule | Convention |
|------|-----------|
| Format | `task-NNN-{type}.md` where NNN is zero-padded sequential |
| Numbering | Sequential across ALL modules (not per-module). Module 1 tasks 0-3, Module 2 tasks 4-11, Module 3 tasks 12-19, etc. |
| Types | `implementer-report`, `spec-review`, `quality-review`, `quality-review-minimum-tier` |
| Why sequential | The pre-dispatch hook checks task N-1 reports before allowing task N. Module-prefixed names (m2-task-1) break this check. |
| Why zero-padded | Clean sorting up to 999 tasks. `task-009` sorts before `task-010`. |

**During Plan Ingestion**, when extracting tasks from multiple modules, assign sequential numbers starting from 000. Map each module's internal task numbers to the global sequence and include the mapping in the TodoWrite.
