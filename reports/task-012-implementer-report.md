---
schema_version: 1
task_id: 12
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/controller-partner-prompt.md"
    description: "Updated partner save path to <feature-dir>/reports/"
  - path: "skills/subagent-driven-development/pre-execution-audit-prompt.md"
    description: "Updated audit paths to <feature-dir>/reports/"
  - path: "skills/subagent-driven-development/trace-auditor-prompt.md"
    description: "Updated DEVIATIONS.md → <feature-dir>/deviations.md, reports/ → <feature-dir>/reports/"
  - path: "skills/subagent-driven-development/references/report-naming-convention.md"
    description: "Updated example paths with <feature-dir>/ prefix and explanatory note"
  - path: "skills/writing-plans/references/module-template.md"
    description: "Updated parent plan path to <feature-dir>/plan.md"
tests:
  written: 0
  passing: 0
  command: "N/A — markdown template changes"
  result: PASS
contract_compliance:
  - constraint: "deviations.md is lowercase"
    status: compliant
    detail: "trace-auditor-prompt uses <feature-dir>/deviations.md"
---

**Implementation Summary:**
Updated 5 prompt template/reference files with <feature-dir>/ path prefix. Checked implementer/spec-reviewer/code-quality-reviewer prompts — none had save paths to update. Committed at `25d0174`.

**Source Files Read:**
All 8 files read. 5 modified, 3 unchanged (implementer/reviewer prompts don't contain save paths).

**Deviations from Plan:**
None.

**Self-Review Findings:**
No issues found.

**Concerns:**
No concerns.
