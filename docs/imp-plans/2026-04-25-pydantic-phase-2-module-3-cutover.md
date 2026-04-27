---
schema_version: 1
feature_archetype: extension
source_contracts: null
shared_constants: []
pattern_references: []
tasks:
  - id: 13
    title: "Prompt Template + SKILL.md + Test Helper Updates"
  - id: 14
    title: "Documentation Updates"
    depends_on: [13]
  - id: 15
    title: "Smoke Test + Regression Verification"
    depends_on: [13, 14]
---

# Pydantic Phase 2 — Module 3: Cutover

> **Parent plan:** `docs/imp-plans/2026-04-25-pydantic-phase-2-plan.md`
> **Module:** 3 of 3
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first.

**Module Goal:** Update prompt templates, SKILL.md report instructions, test helpers, and documentation. Run smoke tests and regression verification to confirm the hard cutover is clean.

**Source Contracts:** None

**Contract Constraints:**
- `implementer-prompt.md`: report format template must include YAML frontmatter block before prose sections
- `SKILL.md`: report persistence prefix must be `---` not `# Task...`
- `sdd_test_helpers.py`: `IMPLEMENTER_REPORT_TEMPLATE` must use frontmatter + 5 prose sections
- Prompt template + validators must ship atomically
- `CLAUDE.md` Pydantic section must list new models and CLI subcommand
- Meta-design sections 2, 5, 11, 12 must be updated

**Feature Archetype:** Extension

## File Map

| File | Responsibility |
|------|----------------|
| `skills/subagent-driven-development/implementer-prompt.md` | Add YAML frontmatter block to report format template |
| `skills/subagent-driven-development/SKILL.md` | Update report persistence prefix |
| `tests/unit/sdd_test_helpers.py` | Update `IMPLEMENTER_REPORT_TEMPLATE` to new format |
| `CLAUDE.md` | Update Pydantic section |
| `docs/plans/2026-04-24-pydantic-meta-design.md` | Update sections 2, 5, 11, 12 |
| `skills/scripts/models/__init__.py` | Update docstring |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 13 | `implementer-prompt.md`, `SKILL.md`, `sdd_test_helpers.py` | — | Module 2 |
| Task 14 | `CLAUDE.md`, meta-design, `__init__.py` | — | Task 13 |
| Task 15 | (no writes — verification only) | All modified files | Tasks 13, 14 |

## Acceptance Criteria

- [ ] `implementer-prompt.md` has YAML frontmatter block in report format template
- [ ] `SKILL.md` report persistence says reports start with `---`
- [ ] `sdd_test_helpers.py` `IMPLEMENTER_REPORT_TEMPLATE` uses frontmatter + 5 prose sections
- [ ] `CLAUDE.md` Pydantic section lists `implementer_report.py`, `checkpoint_result.py`, `validators.py report`
- [ ] Meta-design sections 2, 5, 11, 12 updated; Phase 3 cross-artifact noted
- [ ] `__init__.py` docstring updated
- [ ] All existing tests pass after changes
- [ ] `validate-all-skills.py` passes (122 checks)
- [ ] `verify-symlink-install.sh` passes (105 checks)

---

## Tasks

### Task 13: Prompt Template + SKILL.md + Test Helper Updates

**Files:**
- Modify: `skills/subagent-driven-development/implementer-prompt.md`
- Modify: `skills/subagent-driven-development/SKILL.md`
- Modify: `tests/unit/sdd_test_helpers.py`

- [ ] **Step 1: Update implementer-prompt.md report format**

  In `skills/subagent-driven-development/implementer-prompt.md`, replace the Report Format section (lines 186-236) with the new format that includes YAML frontmatter before prose sections:

  Replace:
  ```
      ## Report Format

      When done, report using this exact structure. Do not omit sections.

      **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT

      **Implementation Summary:**
      ...
  ```

  With:
  ```
      ## Report Format

      When done, report using this exact structure. Your report MUST begin with a YAML
      frontmatter block (between --- delimiters), followed by the prose sections below.
      Do not omit sections.

      ---
      schema_version: 1
      task_id: [your task number]
      status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
      files_changed:
        - path: "path/to/file.py"
          description: "what changed and why"
      tests:
        written: [count]
        passing: [count]
        command: "[exact command run]"
        result: PASS | FAIL
      contract_compliance:
        - constraint: "[constraint text from plan]"
          status: compliant | non_compliant | partial | not_applicable
          detail: "[how you complied]"
      ---

      **Implementation Summary:**
      [2-3 sentences: what you built and the approach taken]

      **Source Files Read:**
      - `path/to/source.py` — [what you learned from reading it]
      - (Write "None — no source files listed for this task" if applicable)

      **CLAUDE.md Files Read:**
      - `path/to/CLAUDE.md` — [key conventions or patterns found]
      - (Write "None found in modified directories" if no CLAUDE.md files exist)

      **Deviations from Plan:**
      - [Any decisions you made that differ from the plan's instructions]
      - [Anything you skipped, deferred, or did differently]
      - [Any dead code you identified but did not remove, and why]
      - (Write "None — implemented exactly as specified" if applicable)

      **Self-Review Findings:**
      - [Issues found during self-review and how you resolved them]
      - (Write "No issues found" if applicable)

      **Concerns:**
      - [Anything you're uncertain about, worried about, or think the controller should know]
      - (Write "No concerns" if applicable)

      Use DONE_WITH_CONCERNS if you have any entries in Deviations or Concerns.
      Use BLOCKED if you cannot complete the task.
      Use NEEDS_CONTEXT if you need information that wasn't provided.
      Never silently produce work you're unsure about.

      (The controller uses DONE_WITH_CONCERNS as a routing signal — it triggers reading deviations before review. A DONE report with concerns buried in the body will be reviewed without the controller knowing to look for them.)
  ```

- [ ] **Step 2: Update SKILL.md report persistence prefix**

  In `skills/subagent-driven-development/SKILL.md`, replace the report file format block (lines 426-431):

  From:
  ```
  **Report file format**: Each report file should contain the implementer's or reviewer's full output, prefixed with:
  ```
  # Task NNN Report — [task name]
  # Date: [ISO timestamp]
  # Status: [DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT]
  ```
  ```

  To:
  ```
  **Report file format**: Implementer report files must begin with YAML frontmatter (between `---` delimiters) containing structured fields (schema_version, task_id, status, files_changed, tests, contract_compliance), followed by prose sections. Reviewer and spec-review reports retain their existing markdown format.
  ```

- [ ] **Step 3: Update sdd_test_helpers.py report template**

  In `tests/unit/sdd_test_helpers.py`, replace `IMPLEMENTER_REPORT_TEMPLATE` (lines 52-88):

  ```python
  IMPLEMENTER_REPORT_TEMPLATE = """\
  ---
  schema_version: 1
  task_id: {task_number}
  status: DONE
  files_changed:
    - path: "src/module.py"
      description: "modified"
    - path: "tests/test_module.py"
      description: "created"
  tests:
    written: 2
    passing: 2
    command: "pytest tests/test_module.py -v"
    result: PASS
  ---

  **Implementation Summary:**
  Implemented the feature as specified in the plan. All requirements met.

  **Source Files Read:**
  - docs/imp-plans/plan.md
  - src/existing_module.py

  **Deviations from Plan:**
  None — implemented exactly as specified

  **Self-Review Findings:**
  No issues found during self-review.

  **Concerns:**
  No concerns
  """
  ```

  Also update the docstring for `create_task_reports()` (line 175): change "all 9 required sections" to "YAML frontmatter + 5 prose sections".

- [ ] **Step 4: Run existing tests to verify no breakage**

  Run: `.venv/bin/python3 -m pytest tests/unit/ -v`
  Expected: All existing tests pass (existing hook/checkpoint tests use the updated template)

- [ ] **Step 5: Commit**

  ```bash
  git add skills/subagent-driven-development/implementer-prompt.md skills/subagent-driven-development/SKILL.md tests/unit/sdd_test_helpers.py
  git commit -m "feat(pydantic): update prompt template, SKILL.md, and test helpers for frontmatter format"
  ```

---

### Task 14: Documentation Updates

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/plans/2026-04-24-pydantic-meta-design.md`
- Modify: `skills/scripts/models/__init__.py`

- [ ] **Step 1: Update CLAUDE.md Pydantic section**

  In `CLAUDE.md`, find the "Pydantic Validation (Phase 1)" section and update it to include Phase 2:

  Update the header to: `## Pydantic Validation (Phase 1 + Phase 2)`

  Add to the models list:
  ```
  - `implementer_report.py` — ImplementerReport model (YAML frontmatter + markdown body), 2 validators
  - `checkpoint_result.py` — CheckpointResult model (pure JSON), 3 validators
  ```

  Add to the CLI section:
  ```
  - CLI: `python3 validators.py report <path>` — validates implementer report frontmatter
  - `validate-report.py` runs Pydantic validation before prose section checks
  ```

  Update the "Plans without YAML frontmatter" note to include reports:
  ```
  - Plans and reports without YAML frontmatter are hard FAILs — add frontmatter to validate.
  ```

- [ ] **Step 2: Update __init__.py docstring**

  Update `skills/scripts/models/__init__.py`:

  ```python
  """Shared Pydantic models for the Superpowers custom fork.

  Modules:
    _base.py - Base classes (StrictModel, SchemaVersionedModel) and CURRENT_SCHEMA_VERSION
    plan.py - Plan artifact model (YAML frontmatter)
    handoff.py - HandoffPackage artifact model (YAML frontmatter)
    implementer_report.py - ImplementerReport artifact model (YAML frontmatter)
    checkpoint_result.py - CheckpointResult artifact model (pure JSON)
    errors.py - Human-readable error formatters
    validators.py - CLI entry points (plan, handoff, report subcommands)
  """
  ```

- [ ] **Step 3: Update meta-design**

  Read `docs/plans/2026-04-24-pydantic-meta-design.md` and update:
  - Section 2 (Roadmap): Phase 2 status → "Complete"
  - Section 2 (Roadmap): Add note to Phase 3 scope: "Cross-artifact contract validation (PlanExecutionContract) — user-requested candidate. Validates relationships between Plan and ImplementerReport: task_id exists in plan, files_changed cross-task ownership, contract_compliance covers plan constraints."
  - Section 5.1 (Location): Confirm `implementer_report.py` and `checkpoint_result.py` in file tree
  - Section 12.1: "Resolved — No renderer; humans read file as-is."
  - Section 12.2: "Resolved — YAML frontmatter, same as Plan."
  - Section 12.3: "Updated — Phase 3 candidate for PlanExecutionContract."
  - Section 11: Add Phase 2 post-mortem (brief: what went well, what to improve)

- [ ] **Step 4: Commit**

  ```bash
  git add CLAUDE.md skills/scripts/models/__init__.py docs/plans/2026-04-24-pydantic-meta-design.md
  git commit -m "docs: update CLAUDE.md, meta-design, and __init__.py for Phase 2"
  ```

---

### Task 15: Smoke Test + Regression Verification

**Files:**
- No files created or modified — verification only

- [ ] **Step 1: Run full unit test suite**

  Run: `.venv/bin/python3 -m pytest tests/unit/ -v`
  Expected: All tests pass (existing + ~37 new from Modules 1-2)

- [ ] **Step 2: Run skill regression tests**

  Run: `python3 tests/ARaymond-skill-regression/validate-all-skills.py`
  Expected: 122 checks pass (prompt template change adds content but doesn't alter skill structure)

- [ ] **Step 3: Run installation verification**

  Run: `bash tests/ARaymond-installation/verify-symlink-install.sh`
  Expected: 105 checks pass

- [ ] **Step 4: Smoke test with real reports**

  Copy a completed Phase 1 implementer report, add YAML frontmatter, validate:
  ```bash
  mkdir -p tests/fixtures/_smoke-test-reports
  cp reports/task-001-implementer-report.md tests/fixtures/_smoke-test-reports/
  ```
  Add YAML frontmatter to the copy (manually, matching the report's actual content), then:
  ```bash
  .venv/bin/python3 skills/scripts/models/validators.py report tests/fixtures/_smoke-test-reports/task-001-implementer-report.md
  ```
  Expected: exit 0

  After verification:
  ```bash
  rm -rf tests/fixtures/_smoke-test-reports
  ```

- [ ] **Step 5: Verify validate-report.py end-to-end**

  Run the two-layer validation against a valid fixture:
  ```bash
  python3 skills/subagent-driven-development/scripts/validate-report.py --report-file tests/fixtures/reports/valid/minimal-report.md
  ```
  Expected: exit 0, JSON output with `"status": "COMPLETE"`, 5 sections found

- [ ] **Step 6: Final commit**

  If smoke test reports were committed, clean up. Otherwise just verify working tree is clean:
  ```bash
  git status
  ```
  Expected: clean working tree (all changes committed in prior tasks)
