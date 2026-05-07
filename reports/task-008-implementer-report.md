---
schema_version: 1
task_id: 8
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "Added --feature-dir argument with resolution logic for reports-dir and deviations-file"
  - path: "skills/subagent-driven-development/scripts/context-summary.py"
    description: "Added --feature-dir, changed required=True to required=False with post-parse validation"
tests:
  written: 0
  passing: 0
  command: "--help verified for both scripts"
  result: PASS
contract_compliance:
  - constraint: "Feature dir format is docs/imp-plans/YYYY-MM-DD-<feature-name>/"
    status: compliant
    detail: "--feature-dir resolves paths relative to this format"
---

**Implementation Summary:**
Added `--feature-dir` to both scripts. controller-checkpoint.py derives reports-dir and deviations-file. context-summary.py changed `required=True` to `required=False` with post-parse validation for all three args (reports-dir, deviations-file, output). Committed at `7260bbb`.

**Source Files Read:**
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — argparse section
- `skills/subagent-driven-development/scripts/context-summary.py` — argparse section

**Deviations from Plan:**
None — implemented exactly as specified.

**Self-Review Findings:**
No issues found.

**Concerns:**
No concerns.
