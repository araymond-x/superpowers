---
schema_version: 1
task_id: 8
status: DONE
files_changed:
  - path: "tests/integration/sdd-e2e-test.sh"
    description: "Added Step 9 (validate-plan accepts a task_type: verification plan, asserts non-FAIL) and Step 10 (verification task with 'Create' keyword asserts WARNING) before the summary; bumped summary 8→10. +89/-1."
tests:
  written: 2
  passing: 2
  command: "bash tests/integration/sdd-e2e-test.sh"
  result: PASS
contract_compliance:
  - constraint: "Use $WORK (script's real temp dir), NOT $TEMP_DIR"
    status: compliant
    detail: "Both new steps write fixtures to $WORK/plan-verif.md and $WORK/plan-verif-kw.md; no $TEMP_DIR introduced."
  - constraint: "Both RESULT=$(...) substitutions keep || true"
    status: compliant
    detail: "Step 9 and Step 10 each retain `|| true` (validate-plan exits 2 on WARNING under set -e + ERR trap)."
  - constraint: "Test must PASS end-to-end (all 10 steps)"
    status: compliant
    detail: "Ran the script; output ends with 'E2E PIPELINE PASS - 10 steps composed correctly'."
  - constraint: "Surgical: add 2 steps + update summary count; don't alter Steps 1-8"
    status: compliant
    detail: "Single Edit inserted Steps 9/10 immediately before the summary and bumped 8→10; +89/-1, none touching Steps 1-8."
---

**Implementation Summary**
Inserted two new steps into the e2e smoke test, immediately before the final `E2E PIPELINE PASS` summary line, and bumped the count 8→10:
- **Step 9** writes a plan with a `task_type: verification` task (id 94, "Audit orphaned references" — no write keyword) and asserts `validate-plan.py` does not return `FAIL` (returns `PASS` — verification tasks accepted).
- **Step 10** writes a plan with a verification task whose title contains "Create" (id 95) and asserts `validate-plan.py` returns `WARNING` (the Task 1 verification-keyword heuristic fires).

Snippets came from the task prompt; substituted `$WORK` for `$TEMP_DIR` throughout (the script's actual mktemp dir / cwd) and kept `|| true` on both command substitutions. `$PROJECT` resolves to the worktree root via `BASH_SOURCE`, so both steps exercise the NEW worktree `validate-plan.py`.

**Source Files Read**
- `tests/integration/sdd-e2e-test.sh` (full, pre-edit) — confirmed `$WORK`/`$PROJECT`/`$PYTHON` vars, `set -e` + ERR trap, summary + `rm -rf "$WORK"` tail.

**CLAUDE.md Files Read**
- None in `tests/integration/` (confirmed absent). Repo-root + global CLAUDE.md already in context.

**Deviations from Plan**
None. Snippets applied verbatim with the required `$TEMP_DIR` → `$WORK` adaptation.

**Self-Review Findings**
Independently re-ran both fixtures outside the harness to rule out a false pass (non-vacuous):
- Step 9 fixture → `"status": "PASS"`, exit 0 (both tasks OK, no warnings/blockers).
- Step 10 fixture → `"status": "WARNING"`, exit 2, with an explicit `verification_keyword_heuristic` section: "Task 95 ('Create cleanup script') is task_type: verification but its title contains write-suggesting keyword(s): Create." The WARNING comes from the real heuristic, not a missing-section artifact.

Final test output (proof of 10 passing steps):
```
=== Step 9: Verification task type ===
PASS: Step 9 — verification task validation

=== Step 10: Verification keyword WARNING ===
PASS: Step 10 — verification keyword WARNING

E2E PIPELINE PASS - 10 steps composed correctly
```

**Concerns**
None. Committed as `ea34a64`.
