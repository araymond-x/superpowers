# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Pre-exec | AuditOrder | Order #1: Task 7/8 interaction — added note to Task 7 dispatch about validate_report_sections() return dict | Resolved |
| Pre-exec | AuditOrder | Order #2: Task 7 yaml import — used unconditional `import yaml` per audit recommendation | Resolved |
| Pre-exec | AuditOrder | Order #4: Task 9 Progress strict model — all 3 progress dict constructions verified, only Progress model fields used | Resolved |
| Pre-exec | AuditOrder | Order #5: extract-execution-trace.py VALID_STATUSES fallback after STATUS_VALUE_PATTERN removal — accepted gap, fallback values match | Pending (Module 2) |
| Task 2 | Observation | pytest warns about TestSummary Pydantic class name collision (PytestCollectionWarning). Renaming would change spec-defined class name. Cosmetic only. | Accepted |
| Task 10 | ExpectedBreakage | 4 tests in test_sdd_hard_gates.py fail — old-format test reports lack YAML frontmatter. Fixed by Task 13 (IMPLEMENTER_REPORT_TEMPLATE updated). | Resolved |
| Task 10 | IndependentDecision | Hook Check 4b used system python3 which lacks PyYAML — added $PYTHON variable preferring .venv/bin/python3. Also reverted validate-report.py yaml import to conditional. Extra commit e43796f. | Accepted |
| Task 13 | IndependentDecision | Fixed hook $PYTHON from relative (.venv/bin/python3) to absolute ($(pwd)/.venv/bin/python3). Relative broke after cd $CWD. Assumes hook CWD is project root. | Accepted |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]
