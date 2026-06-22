# Example Workflow

> Part of the Subagent-Driven Development skill (`skills/subagent-driven-development/SKILL.md`).
> This annotated example shows Task 0 catch, DEVIATIONS.md logging, review cycles, and Pre-Completion Gate verification.

```
You: I'm using Subagent-Driven Development to execute this plan.

[Read full plan file: <feature-dir>/plan.md]
[Extract Contract Constraints section (verbatim)]
[Plan has Source Contracts — read source files: src/api/contracts.py, src/models/user.py]
[Extract Write-Scope Partitioning table — Tasks 1-4 own distinct files, no conflicts]
[Create DEVIATIONS.md at project root with header template]
[Plan includes Task 0 — verify it is first in task list]
[Create TodoWrite with Task 0 first, then Tasks 1-4]

Task 0: Contract Verification (BLOCKING)

[Dispatch Task 0 implementer — verify contract test against source files]
Implementer: "Contract test written and passing. Confirmed: UserResponse has field 'account_id'
  (not 'accountId' as stated in plan section 2.3). Plan has a typo — field is snake_case."

[STOP. Plan assumption is wrong. This will break Task 2 which references 'accountId'.]
You (to human): "Task 0 revealed a discrepancy: plan says 'accountId' but source uses 'account_id'.
  Task 2 references the wrong field name. Should I update the plan before proceeding?"
Human: "Yes, update the plan."
[Update plan, re-extract Contract Constraints, proceed]

Task 1: Hook installation script (review tier: standard)

[Dispatch implementer with full task text + Contract Constraints passthrough]
Implementer: "Before I begin — should the hook be installed at user or system level?"
You: "User level (~/.config/superpowers/hooks/)"

Implementer:
  Status: DONE
  - Implemented install-hook command
  - Added tests, 5/5 passing
  - Self-review: Found I missed --force flag, added it
  - Committed

[No concerns to log — DEVIATIONS.md unchanged]
[Dispatch spec compliance reviewer — tier: standard]
Spec reviewer: PASS — all requirements met, nothing extra

[Dispatch code quality reviewer]
Code reviewer: Strengths: Good test coverage, clean. Issues: None. Approved.

[Mark Task 1 complete in TodoWrite]
[Update plan file: "- [ ] Task 1" -> "- [x] Task 1"]

Task 2: Recovery modes (review tier: standard)

[Dispatch implementer with full task text + Contract Constraints passthrough]
Implementer:
  Status: DONE_WITH_CONCERNS
  - Added verify/repair modes
  - 8/8 tests passing
  - Self-review: All good
  - Concern: The repair mode touches a file that Task 3 also modifies (repair_utils.py).
    I made conservative changes to avoid conflicts, but Task 3 should be aware.

[DONE_WITH_CONCERNS — log to DEVIATIONS.md]
[Append: "| Task 2 | IndependentDecision | repair_utils.py also modified by Task 3; conservative changes made | Pending |"]

[Dispatch spec compliance reviewer]
Spec reviewer: FAIL:
  - Missing: Progress reporting (spec says "report every 100 items")
  - Extra: Added --json flag (not requested)

[Implementer fixes issues]
Implementer: Removed --json flag, added progress reporting

[Spec reviewer reviews again]
Spec reviewer: PASS

[Dispatch code quality reviewer]
Code reviewer: Important issue: Magic number (100) should be a named constant

[Implementer fixes]
Implementer: Extracted PROGRESS_INTERVAL = 100

[Code reviewer reviews again]
Code reviewer: Approved

[Mark Task 2 complete in TodoWrite]
[Update plan file: "- [ ] Task 2" -> "- [x] Task 2"]
[Note Task 3 about repair_utils.py dependency — include in dispatch context]

...

[After all tasks]
[Read DEVIATIONS.md — 2 entries, both Pending]
[Disposition entries: repair_utils.py concern → Task 3 was given explicit context, no conflict materialized → Accepted]
[All entries dispositioned]

[Pre-Completion Gate check:]
[1. All TodoWrite tasks complete: YES]
[2. All plan checkboxes checked: YES]
[3. DEVIATIONS.md fully dispositioned: YES]
[4. Final reviewer will receive DEVIATIONS.md: YES — including in context]
[5. Contract trace: account_id used correctly throughout: PASS]

[Dispatch final code reviewer with DEVIATIONS.md included in context]
Final reviewer: All requirements met, deviations reviewed and accepted, ready to merge.

Done — invoking superpowers:finishing-a-development-branch.
```
