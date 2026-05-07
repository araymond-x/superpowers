---
schema_version: 1
task_id: 2
status: DONE
files_changed:
  - path: "skills/requesting-code-review/code-reviewer.md"
    description: "Inserted bulleted severity list (Critical/Important/Minor/Needs Context) and pre-writing reflection paragraph into the Calibration section"
tests:
  written: 0
  passing: 0
  command: "python3 tests/ARaymond-skill-regression/validate-all-skills.py"
  result: FAIL
contract_compliance:
  - constraint: "**Needs Context** must appear in code-reviewer.md post-migration"
    status: compliant
    detail: "Inserted as 4th bullet in Issue severity categories list with exact handoff wording"
  - constraint: "Reflection step must appear before Output Format section"
    status: compliant
    detail: "Inserted as paragraph after severity list, before 'If you find...' paragraph"
  - constraint: "superpowers-code-reviewer must NOT appear in skills/"
    status: not_applicable
    detail: "Task 3 handles dispatch-string replacements"
  - constraint: "Task tool (general-purpose): at line 10"
    status: not_applicable
    detail: "Not modified by this task"
  - constraint: "Dead code findings remain BLOCKING"
    status: not_applicable
    detail: "Not modified by this task"
  - constraint: "[NEEDS_CONTEXT] and IMPLEMENTER_REPORT remain"
    status: not_applicable
    detail: "Not modified by this task"
---

**Implementation Summary:**
Inserted the bulleted severity list (4 categories) and the pre-writing reflection paragraph into the Calibration section of `code-reviewer.md`. Preserves four-space indentation inside the fenced code block.

**Source Files Read:**
- `skills/requesting-code-review/code-reviewer.md` — target file

**CLAUDE.md Files Read:**
- Project root CLAUDE.md; no subdirectory CLAUDE.md in `skills/requesting-code-review/`

**Deviations from Plan:**
None — implemented exactly as specified.

**Self-Review Findings:**
- 2 template invariants now PASS; 2 dispatch-ref invariants still FAIL (expected for Task 3)
- Grep count = 2, no duplication

**Concerns:**
None.
