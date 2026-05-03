---
schema_version: 1
feature_archetype: extension
source_contracts: null
shared_constants:
  - path: "skills.scripts.models._base.CURRENT_SCHEMA_VERSION"
    value: "1"
    reason: "Used in CheckpointResult construction"
pattern_references:
  - name: "phase-1-validators"
    source_files: ["skills/scripts/models/validators.py"]
    reason: "Established pattern for CLI entry points: _extract_frontmatter, validate_X(), bypass check, exit codes"
  - name: "phase-1-cli-tests"
    source_files: ["tests/unit/test_validators/test_validate_plan_pydantic.py"]
    reason: "Test structure for CLI subprocess tests: exit codes, stderr content, bypass env var"
tasks:
  - id: 6
    title: "validators.py report Subcommand"
    pattern_references: ["phase-1-validators"]
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION"]
  - id: 7
    title: "validate-report.py Pydantic Pre-Check"
    depends_on: [6]
  - id: 8
    title: "_report_utils.py Re-Export + Cleanup"
  - id: 9
    title: "controller-checkpoint.py Updates"
    depends_on: [8]
    shared_constants_used: ["skills.scripts.models._base.CURRENT_SCHEMA_VERSION"]
  - id: 10
    title: "sdd-pre-dispatch-hook.sh Updates"
    depends_on: [7]
  - id: 11
    title: "context-summary.py Frontmatter Parsing"
  - id: 12
    title: "CLI + Consumer Tests"
    depends_on: [6, 7, 8, 9, 10, 11]
    pattern_references: ["phase-1-cli-tests"]
---

# Pydantic Phase 2 — Module 2: CLI + Consumer Updates

> **Parent plan:** `docs/imp-plans/2026-04-25-pydantic-phase-2-plan.md`
> **Module:** 2 of 3
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first.

**Module Goal:** Add `validators.py report` subcommand, update `validate-report.py` with Pydantic pre-check, and update all consumers of the old report format: `_report_utils.py`, `controller-checkpoint.py`, `sdd-pre-dispatch-hook.sh`, `context-summary.py`.

**Source Contracts:** None

**Contract Constraints:**
- `validators.py` exit codes: 0 pass, 1 validation fail, 2 infrastructure error
- `controller-checkpoint.py` exit codes: 0 PASS, 1 FAIL, 2 WARNING, 3 script error (unchanged)
- `validate-report.py` must call `validate_report()` from `validators.py` (shared code)
- Reports without frontmatter → hard FAIL referencing "Phase 2 cutover"
- `_report_utils.py`: `STATUS_VALUE_PATTERN` and `extract_implementer_status()` removed, `REQUIRED_SECTIONS` from 9 to 5
- `controller-checkpoint.py`: `_build_result()` uses `CheckpointResult` + `.model_dump(exclude_none=True)`
- `controller-checkpoint.py`: inline `validate_report_sections()` updated from 9 to 5 sections
- `sdd-pre-dispatch-hook.sh`: capture exit code from `validate-report.py`, block on nonzero, update "9" to "5"
- `context-summary.py`: parse `files_changed` from YAML frontmatter, not prose section

**Feature Archetype:** Extension

## File Map

| File | Responsibility |
|------|----------------|
| `skills/scripts/models/validators.py` | Add `validate_report()` function + `report` CLI subcommand |
| `skills/subagent-driven-development/scripts/validate-report.py` | Pydantic pre-check before prose section check |
| `skills/subagent-driven-development/scripts/_report_utils.py` | Re-export VALID_STATUSES, remove old helpers, fix placeholders, shrink REQUIRED_SECTIONS |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | CheckpointResult construction + inline validator update |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Exit code handling + section count message |
| `skills/subagent-driven-development/scripts/context-summary.py` | Frontmatter-based file extraction |
| `tests/unit/test_validators/test_validate_report_pydantic.py` | CLI entry-point tests |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 6 | `skills/scripts/models/validators.py` | `skills/scripts/models/implementer_report.py`, `skills/scripts/models/errors.py` | Module 1 |
| Task 7 | `skills/subagent-driven-development/scripts/validate-report.py` | `skills/scripts/models/validators.py` | Task 6 |
| Task 8 | `skills/subagent-driven-development/scripts/_report_utils.py` | `skills/scripts/models/implementer_report.py` | Module 1 |
| Task 9 | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | `skills/scripts/models/checkpoint_result.py`, `_report_utils.py` | Task 8 |
| Task 10 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | `validate-report.py` | Task 7 |
| Task 11 | `skills/subagent-driven-development/scripts/context-summary.py` | `skills/scripts/models/implementer_report.py` | Module 1 |
| Task 12 | `tests/unit/test_validators/test_validate_report_pydantic.py` | all modified files | Tasks 6–11 |

## Acceptance Criteria

- [x] `validators.py` has `report` subcommand with exit codes 0/1/2 and bypass support
- [x] `validate-report.py` calls `validate_report()` from `validators.py` for Pydantic check before prose check
- [x] Reports without frontmatter → hard FAIL with "Phase 2 cutover" message
- [x] `_report_utils.py` re-exports `VALID_STATUSES` from model, `STATUS_VALUE_PATTERN` and `extract_implementer_status()` removed
- [x] `_report_utils.py` `REQUIRED_SECTIONS` has exactly 5 entries
- [x] `_report_utils.py` placeholder detection handles "None — implemented exactly as specified"
- [x] `controller-checkpoint.py` `_build_result()` uses `CheckpointResult` + `.model_dump(exclude_none=True)`
- [x] `controller-checkpoint.py` inline `validate_report_sections()` updated to 5 sections
- [x] `sdd-pre-dispatch-hook.sh` captures exit code and blocks on nonzero, message says "5 required sections"
- [x] `context-summary.py` extracts files from YAML frontmatter
- [x] ~10 CLI entry-point tests pass (9 passing)

---

## Tasks

### Task 6: validators.py report Subcommand

**Files:**
- Modify: `skills/scripts/models/validators.py`
- Read: `skills/scripts/models/implementer_report.py`, `skills/scripts/models/errors.py`

**Pattern References:**
- `skills/scripts/models/validators.py` — follow the `validate_plan()` function pattern exactly

- [x] **Step 1: Add validate_report() function**

  Add to `skills/scripts/models/validators.py`, after the existing `validate_handoff()` function and before `main()`. Also add the import for `ImplementerReport` at the top with the other model imports:

  ```python
  # Add to imports section (after existing imports)
  from implementer_report import ImplementerReport

  # Add after validate_handoff() function
  def validate_report(path: str, schema_version: int | None = None) -> int:
      """Validate an implementer report file. Returns exit code."""
      report_path = Path(path)
      if not report_path.is_file():
          print(f"File not found: {path}", file=sys.stderr)
          return 2

      if _check_bypass():
          return 0

      text = report_path.read_text(encoding="utf-8")
      frontmatter_yaml = _extract_frontmatter(text)

      if frontmatter_yaml is None:
          print(
              f"No YAML frontmatter found in {path}. "
              "This report predates the Phase 2 Pydantic cutover — "
              "add YAML frontmatter to validate it.",
              file=sys.stderr,
          )
          return 1

      try:
          data = yaml.safe_load(frontmatter_yaml)
      except yaml.YAMLError as e:
          print(format_yaml_error(e, path), file=sys.stderr)
          return 1

      if data is None:
          data = {}

      try:
          ImplementerReport.model_validate(data)
      except ValidationError as e:
          print(format_validation_error(e, path), file=sys.stderr)
          return 1
      except Exception as e:
          print(
              f"VALIDATOR CRASHED (this is a bug in the validator, not your artifact): "
              f"{type(e).__name__}: {e}",
              file=sys.stderr,
          )
          return 2

      return 0
  ```

- [x] **Step 2: Update main() to accept "report" command**

  In `main()`, update the `choices` list and add the elif branch:

  ```python
  def main() -> None:
      parser = argparse.ArgumentParser(description="Pydantic artifact validator")
      parser.add_argument("command", choices=["plan", "handoff", "report"])
      parser.add_argument("path", help="Path to plan file, handoff package directory, or report file")
      parser.add_argument(
          "--schema-version",
          type=int,
          default=None,
          help="Forensic: validate against older schema version (stub — not yet implemented)",
      )
      args = parser.parse_args()

      if args.command == "plan":
          sys.exit(validate_plan(args.path, args.schema_version))
      elif args.command == "handoff":
          sys.exit(validate_handoff(args.path, args.schema_version))
      elif args.command == "report":
          sys.exit(validate_report(args.path, args.schema_version))
  ```

- [x] **Step 3: Verify it runs**

  Run: `.venv/bin/python3 skills/scripts/models/validators.py report tests/fixtures/reports/valid/minimal-report.md`
  Expected: exit code 0

  Run: `.venv/bin/python3 skills/scripts/models/validators.py report tests/fixtures/reports/invalid/missing-status.md`
  Expected: exit code 1, stderr contains `VALIDATION FAILED`

- [x] **Step 4: Commit** (60d74d0)

  ```bash
  git add skills/scripts/models/validators.py
  git commit -m "feat(pydantic): add validators.py report subcommand"
  ```

---

### Task 7: validate-report.py Pydantic Pre-Check

**Files:**
- Modify: `skills/subagent-driven-development/scripts/validate-report.py`
- Read: `skills/scripts/models/validators.py`

- [x] **Step 1: Add Pydantic pre-check to validate-report.py**

  Replace the current `main()` function in `validate-report.py`. The new version calls `validate_report()` from `validators.py` first for Pydantic frontmatter validation, then falls through to prose section check only if Pydantic passes:

  ```python
  #!/usr/bin/env python3
  """
  validate-report.py

  Two-layer report validation:
  1. Pydantic frontmatter validation (via validators.py)
  2. Prose section-presence check (via _report_utils.py)

  Reports without frontmatter hard FAIL at layer 1 and never reach layer 2.

  Exit codes:
    0 - COMPLETE (Pydantic valid + all required prose sections present)
    1 - INCOMPLETE (Pydantic invalid or prose sections missing)
    2 - Script error (bad arguments, file not found, etc.)

  Usage:
    python validate-report.py --report-file /path/to/report.md
  """

  import argparse
  import json
  import os
  import sys
  from pathlib import Path

  # Add the script directory to the path so _report_utils can be imported
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  from _report_utils import validate_report_sections

  # Add models directory for Pydantic validation
  MODELS_DIR = str(Path(__file__).resolve().parent / "../../scripts/models")
  sys.path.insert(0, MODELS_DIR)
  from validators import validate_report


  def main():
      parser = argparse.ArgumentParser(
          description=(
              "Validate that an implementer report has valid Pydantic frontmatter "
              "and contains all required prose sections. "
              "Outputs JSON to stdout. "
              "Exit code 1 if validation fails, 0 if complete."
          )
      )
      parser.add_argument(
          "--report-file",
          required=True,
          metavar="PATH",
          help="Path to the implementer report markdown file to validate.",
      )
      args = parser.parse_args()

      if not os.path.isfile(args.report_file):
          print(
              json.dumps({"error": "Report file not found: {}".format(args.report_file)}),
              file=sys.stderr,
          )
          return 2

      # Layer 1: Pydantic frontmatter validation
      pydantic_exit = validate_report(args.report_file)
      if pydantic_exit != 0:
          # Pydantic validation failed — report as INCOMPLETE
          # Error details already printed to stderr by validate_report()
          print(json.dumps({
              "status": "INCOMPLETE",
              "sections_found": [],
              "sections_missing": ["YAML frontmatter validation failed"],
          }))
          return 1

      # Layer 2: Prose section-presence check
      try:
          with open(args.report_file, "r", encoding="utf-8") as f:
              content = f.read()
      except OSError as e:
          print(
              json.dumps({"error": "Could not read report file: {}".format(e)}),
              file=sys.stderr,
          )
          return 2

      result = validate_report_sections(content)

      # Layer 3: done_with_concerns_check (CLI-level warning, not blocking)
      # If status is DONE but markdown body has non-empty Deviations or Concerns,
      # emit a warning to stderr. Per spec: informational only, exit code unchanged.
      if pydantic_exit == 0:
          try:
              fm_end = content.find("---", 3)
              if fm_end != -1:
                  fm_data = yaml.safe_load(content[3:fm_end])
                  if isinstance(fm_data, dict) and fm_data.get("status") == "DONE":
                      if result.get("has_deviations") or result.get("has_concerns"):
                          print(
                              "WARNING: status is DONE but report has non-empty "
                              "Deviations or Concerns. Consider DONE_WITH_CONCERNS.",
                              file=sys.stderr,
                          )
          except Exception:
              pass  # Warning check should never block validation

      print(json.dumps(result, indent=2))

      return 1 if result["status"] == "INCOMPLETE" else 0


  if __name__ == "__main__":
      sys.exit(main())
  ```

  Also add `yaml` import near the top of the file (after the existing imports):

  ```python
  try:
      import yaml
  except ImportError:
      yaml = None
  ```

- [x] **Step 2: Verify both layers work**

  Run against a valid fixture:
  ```bash
  python3 skills/subagent-driven-development/scripts/validate-report.py --report-file tests/fixtures/reports/valid/minimal-report.md
  ```
  Expected: exit 0, JSON output with `"status": "COMPLETE"`

  Run against a fixture with no frontmatter (create a temporary one):
  ```bash
  echo "# No frontmatter report" > /tmp/no-frontmatter.md
  python3 skills/subagent-driven-development/scripts/validate-report.py --report-file /tmp/no-frontmatter.md
  ```
  Expected: exit 1, stderr contains "Phase 2" or "frontmatter"

- [x] **Step 3: Commit** (bbd3385)

  ```bash
  git add skills/subagent-driven-development/scripts/validate-report.py
  git commit -m "feat(pydantic): add Pydantic pre-check to validate-report.py"
  ```

---

### Task 8: _report_utils.py Re-Export + Cleanup

**Files:**
- Modify: `skills/subagent-driven-development/scripts/_report_utils.py`
- Read: `skills/scripts/models/implementer_report.py`

- [x] **Step 1: Update _report_utils.py**

  Make the following changes to `skills/subagent-driven-development/scripts/_report_utils.py`:

  **1a. Update module docstring:**

  ```python
  """
  _report_utils.py

  Shared utilities for report parsing, section detection, and content heuristics.
  Used by validate-report.py, controller-checkpoint.py, and context-summary.py.

  VALID_STATUSES is re-exported from the Pydantic model (single source of truth).
  Prose section validation covers the 5 sections that remain in the markdown body
  after Phase 2 moved Status, Files Changed, Tests, and Contract Compliance to
  YAML frontmatter.
  """
  ```

  **1b. Re-export VALID_STATUSES from model, remove old helpers:**

  Replace the constants section (lines 18-39) with the following. Preserve the existing `import re` at line 11 — only replace lines 18-39:

  ```python
  import sys
  from pathlib import Path

  # Re-export VALID_STATUSES from the Pydantic model (single source of truth)
  sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))
  from implementer_report import Status
  VALID_STATUSES = set(Status.__args__)

  # Required prose sections — 5 remain after Phase 2 moved 4 to frontmatter
  REQUIRED_SECTIONS = [
      ("Implementation Summary", [r"implementation\s+summary"]),
      ("Source Files Read", [r"source\s+files?\s+read"]),
      ("Deviations from Plan", [r"deviations?\s+from\s+plan"]),
      ("Self-Review Findings", [r"self[\-\s]review\s+findings?"]),
      ("Concerns", [r"\bconcerns?\b"]),
  ]
  ```

  **1c. Remove `STATUS_VALUE_PATTERN` and `extract_implementer_status()`:**

  Delete lines 37-39 (`STATUS_VALUE_PATTERN = re.compile(...)`) and lines 75-83 (the `extract_implementer_status()` function).

  **1d. Update placeholder detection in `section_contains_content()`:**

  Update the `PLACEHOLDER_VALUES` set and the heuristic logic (around line 45 and lines 110-116):

  ```python
  PLACEHOLDER_VALUES = {"none", "n/a", "na", "-", "—", ""}

  # Phrases used in the implementer prompt template as "no content" placeholders
  PROMPT_PLACEHOLDER_PHRASES = [
      "none — implemented exactly as specified",
      "no issues found",
      "no concerns",
      "none — no source files listed for this task",
      "none found in modified directories",
      "no contract constraints for this task",
  ]
  ```

  In `section_contains_content()`, replace the heuristic block (lines 110-116) with:

  ```python
      body = match.group(1).strip()
      if not body or body.lower() in PLACEHOLDER_VALUES:
          return False
      # Check against prompt template placeholder phrases
      body_lower = body.lower()
      for phrase in PROMPT_PLACEHOLDER_PHRASES:
          if body_lower.startswith(phrase):
              return False
      if len(body) <= 10:
          return False
      return True
  ```

  **1e. Update `validate_report_sections()` return dict:**

  Remove `extract_implementer_status()` call from the return dict. Replace line 154 with status from frontmatter (but since this function doesn't have frontmatter data, just remove the field — the caller gets status from the Pydantic model now):

  ```python
  return {
      "status": "COMPLETE" if not sections_missing else "INCOMPLETE",
      "sections_found": sections_found,
      "sections_missing": sections_missing,
      "has_deviations": section_contains_content("Deviations from Plan", content),
      "has_concerns": section_contains_content("Concerns", content),
  }
  ```

- [x] **Step 2: Verify imports work**

  Run: `python3 -c "import sys; sys.path.insert(0, 'skills/subagent-driven-development/scripts'); from _report_utils import VALID_STATUSES, REQUIRED_SECTIONS; print(len(REQUIRED_SECTIONS), VALID_STATUSES)"`
  Expected: `5 {'DONE', 'DONE_WITH_CONCERNS', 'BLOCKED', 'NEEDS_CONTEXT'}`

- [x] **Step 3: Commit** (43badb5)

  ```bash
  git add skills/subagent-driven-development/scripts/_report_utils.py
  git commit -m "refactor: update _report_utils.py — re-export from model, remove old helpers, fix placeholders"
  ```

---

### Task 9: controller-checkpoint.py Updates

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py`
- Read: `skills/scripts/models/checkpoint_result.py`, `skills/subagent-driven-development/scripts/_report_utils.py`

- [x] **Step 1: Add model imports**

  Near the top of `controller-checkpoint.py`, after the existing `sys` and `os` imports, add:

  ```python
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))
  from _base import CURRENT_SCHEMA_VERSION
  from checkpoint_result import CheckpointResult, CheckResult, Progress
  ```

- [x] **Step 2: Update inline validate_report_sections()**

  Replace the `validate_report_sections()` function (lines 207-244) — update the `required_patterns` list from 9 to 5 sections:

  ```python
  def validate_report_sections(report_content: str) -> dict:
      """
      Validate that a report has the 5 required prose sections.
      Returns {"complete": bool, "sections_found": int, "sections_total": int}.
      """
      required_patterns = [
          (r"implementation\s+summary", "Implementation Summary"),
          (r"source\s+files?\s+read", "Source Files Read"),
          (r"deviations?\s+from\s+plan", "Deviations from Plan"),
          (r"self[\-\s]review\s+findings?", "Self-Review Findings"),
          (r"concerns?", "Concerns"),
      ]

      header_pattern = re.compile(r"(?:\*\*([^*]+)\*\*|^#{1,4}\s+(.+))", re.MULTILINE)
      headers = []
      for match in header_pattern.finditer(report_content):
          text = match.group(1) or match.group(2)
          if text:
              headers.append(text.strip())

      found_count = 0
      for pattern_str, _ in required_patterns:
          compiled = re.compile(pattern_str, re.IGNORECASE)
          if any(compiled.search(h) for h in headers):
              found_count += 1

      total = len(required_patterns)
      return {
          "complete": found_count == total,
          "sections_found": found_count,
          "sections_total": total,
      }
  ```

- [x] **Step 3: Update _build_result()**

  Replace the `_build_result()` function (lines 1013-1034) with the Pydantic construction:

  ```python
  def _build_result(
      phase: str,
      task_number,
      overall_status: str,
      checks: dict,
      warnings: list,
      blockers: list,
      progress,
  ) -> dict:
      """Assemble the final result dict via CheckpointResult model."""
      check_models = {
          name: CheckResult(status=v["status"], detail=v["detail"])
          for name, v in checks.items()
      }
      progress_model = Progress(**progress) if progress else None
      result = CheckpointResult(
          schema_version=CURRENT_SCHEMA_VERSION,
          phase=phase,
          status=overall_status,
          task_number=task_number,
          checks=check_models,
          warnings=warnings,
          blockers=blockers,
          progress=progress_model,
      )
      return result.model_dump(exclude_none=True)
  ```

- [x] **Step 4: Verify checkpoint still runs**

  Run a quick check that the script still starts up correctly:
  ```bash
  python3 skills/subagent-driven-development/scripts/controller-checkpoint.py --help
  ```
  Expected: Help text prints, no import errors

- [x] **Step 5: Commit** (3e5026d)

  ```bash
  git add skills/subagent-driven-development/scripts/controller-checkpoint.py
  git commit -m "feat(pydantic): update controller-checkpoint.py — CheckpointResult construction + 5-section validator"
  ```

---

### Task 10: sdd-pre-dispatch-hook.sh Updates

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`

- [x] **Step 1: Update Check 4b to capture exit code**

  Replace the Check 4b block (lines 254-266) with:

  ```bash
    # Check 4b: Previous task implementer report is structurally COMPLETE
    # Size check (above) catches empty/trivial files; this catches files that pass
    # the size check but are missing required sections (Swiss Cheese layer 2).
    if [ "$RESULT" = "OK" ] && [ -f "$VALIDATE_REPORT_SCRIPT" ]; then
      IMPL_LATEST=$(ls $IMPL_GLOB 2>/dev/null | sort | tail -1)
      if [ -n "$IMPL_LATEST" ]; then
        VALIDATE_OUTPUT=$(python3 "$VALIDATE_REPORT_SCRIPT" --report-file "$IMPL_LATEST" 2>&1)
        VALIDATE_EXIT=$?
        if [ "$VALIDATE_EXIT" -ne 0 ]; then
          ERRORS+=("BLOCKED: Implementer report for Task $PREV ($IMPL_LATEST) failed validation (exit $VALIDATE_EXIT). Re-dispatch the implementer to fix Pydantic frontmatter or complete all 5 required prose sections before proceeding.")
        else
          VALIDATE_STATUS=$(echo "$VALIDATE_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
          if [ "$VALIDATE_STATUS" = "INCOMPLETE" ]; then
            MISSING_SECTIONS=$(echo "$VALIDATE_OUTPUT" | python3 -c "import json,sys; print(', '.join(json.load(sys.stdin).get('sections_missing',[])))" 2>/dev/null)
            ERRORS+=("BLOCKED: Implementer report for Task $PREV ($IMPL_LATEST) is structurally incomplete — missing sections: $MISSING_SECTIONS. Re-dispatch the implementer to complete all 5 required prose sections before proceeding.")
          fi
        fi
      fi
    fi
  ```

  Key changes:
  - `2>/dev/null` → `2>&1` to capture stderr (Pydantic errors go to stderr)
  - Added `VALIDATE_EXIT=$?` check before JSON parsing
  - Nonzero exit code → immediate BLOCKED error (covers both Pydantic failures and prose failures)
  - Zero exit code → proceed to JSON status check as before
  - "9 required sections" → "5 required prose sections" in both error messages

- [x] **Step 2: Commit** (fea142c)

  ```bash
  git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
  git commit -m "fix: update hook to capture validate-report.py exit code and block on Pydantic failures"
  ```

---

### Task 11: context-summary.py Frontmatter Parsing

**Files:**
- Modify: `skills/subagent-driven-development/scripts/context-summary.py`

- [x] **Step 1: Add YAML frontmatter extraction**

  Add a YAML import and a frontmatter extraction helper near the top of `context-summary.py` (after the existing imports):

  ```python
  try:
      import yaml
  except ImportError:
      yaml = None
  ```

  Add a new function after the existing `extract_files_changed()`:

  ```python
  def extract_files_from_frontmatter(content: str) -> list:
      """
      Extract file paths from YAML frontmatter's files_changed field.
      Returns a list of file path strings. Returns empty list if no frontmatter
      or yaml not available.
      """
      if yaml is None:
          return []
      if not content.startswith("---"):
          return []
      end = content.find("---", 3)
      if end == -1:
          return []
      try:
          data = yaml.safe_load(content[3:end])
      except yaml.YAMLError:
          return []
      if not isinstance(data, dict):
          return []
      files_changed = data.get("files_changed", [])
      if not isinstance(files_changed, list):
          return []
      return [
          fc["path"] for fc in files_changed
          if isinstance(fc, dict) and "path" in fc
      ]
  ```

- [x] **Step 2: Update parse_report() to use frontmatter**

  In the `parse_report()` function (around line 176), replace the status and files extraction with frontmatter-only parsing. No old-format fallback (hard cutover):

  ```python
  result["status"] = extract_status_from_frontmatter(content)
  result["files_changed"] = extract_files_from_frontmatter(content)
  ```

  Add the status extraction helper alongside `extract_files_from_frontmatter()`:

  ```python
  def extract_status_from_frontmatter(content: str) -> str:
      """Extract status from YAML frontmatter. Returns 'UNKNOWN' if not found."""
      if yaml is None or not content.startswith("---"):
          return "UNKNOWN"
      end = content.find("---", 3)
      if end == -1:
          return "UNKNOWN"
      try:
          data = yaml.safe_load(content[3:end])
      except yaml.YAMLError:
          return "UNKNOWN"
      if isinstance(data, dict) and "status" in data:
          return data["status"]
      return "UNKNOWN"
  ```

- [x] **Step 3: Commit** (fe1b45a)

  ```bash
  git add skills/subagent-driven-development/scripts/context-summary.py
  git commit -m "feat: update context-summary.py to parse files from YAML frontmatter"
  ```

---

### Task 12: CLI + Consumer Tests

**Files:**
- Create: `tests/unit/test_validators/test_validate_report_pydantic.py`
- Read: `tests/unit/test_validators/test_validate_plan_pydantic.py`

**Pattern References:**
- `tests/unit/test_validators/test_validate_plan_pydantic.py` — follow the subprocess test pattern

- [x] **Step 1: Write CLI entry-point tests**

  Create `tests/unit/test_validators/test_validate_report_pydantic.py`:

  ```python
  """CLI entry-point tests for validators.py report subcommand."""
  import os
  import subprocess
  import sys
  from pathlib import Path

  import pytest

  VALIDATOR_SCRIPT = str(
      Path(__file__).resolve().parent.parent.parent.parent
      / "skills" / "scripts" / "models" / "validators.py"
  )
  FIXTURES_DIR = str(
      Path(__file__).resolve().parent.parent.parent / "fixtures" / "reports"
  )
  PYTHON = sys.executable


  class TestValidReport:
      def test_minimal_valid_report_passes(self):
          result = subprocess.run(
              [PYTHON, VALIDATOR_SCRIPT, "report", f"{FIXTURES_DIR}/valid/minimal-report.md"],
              capture_output=True, text=True,
          )
          assert result.returncode == 0

      def test_full_featured_report_passes(self):
          result = subprocess.run(
              [PYTHON, VALIDATOR_SCRIPT, "report", f"{FIXTURES_DIR}/valid/full-featured-report.md"],
              capture_output=True, text=True,
          )
          assert result.returncode == 0


  class TestInvalidReport:
      def test_missing_status_fails(self):
          result = subprocess.run(
              [PYTHON, VALIDATOR_SCRIPT, "report", f"{FIXTURES_DIR}/invalid/missing-status.md"],
              capture_output=True, text=True,
          )
          assert result.returncode == 1
          assert "VALIDATION FAILED" in result.stderr

      def test_bad_status_enum_fails(self):
          result = subprocess.run(
              [PYTHON, VALIDATOR_SCRIPT, "report", f"{FIXTURES_DIR}/invalid/bad-status-enum.md"],
              capture_output=True, text=True,
          )
          assert result.returncode == 1
          assert "VALIDATION FAILED" in result.stderr

      def test_inconsistent_test_counts_fails(self):
          result = subprocess.run(
              [PYTHON, VALIDATOR_SCRIPT, "report", f"{FIXTURES_DIR}/invalid/test-counts-inconsistent.md"],
              capture_output=True, text=True,
          )
          assert result.returncode == 1

      def test_no_files_for_done_fails(self):
          result = subprocess.run(
              [PYTHON, VALIDATOR_SCRIPT, "report", f"{FIXTURES_DIR}/invalid/no-files-for-done.md"],
              capture_output=True, text=True,
          )
          assert result.returncode == 1


  class TestInfrastructureErrors:
      def test_missing_file_returns_exit_2(self):
          result = subprocess.run(
              [PYTHON, VALIDATOR_SCRIPT, "report", "/nonexistent/path.md"],
              capture_output=True, text=True,
          )
          assert result.returncode == 2

      def test_no_frontmatter_hard_fail(self, tmp_path):
          no_fm = tmp_path / "no-frontmatter.md"
          no_fm.write_text("# Just markdown\nNo frontmatter here.\n")
          result = subprocess.run(
              [PYTHON, VALIDATOR_SCRIPT, "report", str(no_fm)],
              capture_output=True, text=True,
          )
          assert result.returncode == 1
          assert "Phase 2" in result.stderr or "cutover" in result.stderr.lower()


  class TestBypass:
      def test_bypass_env_var_skips_validation(self, tmp_path):
          bad_report = tmp_path / "bad.md"
          bad_report.write_text("---\nbogus: true\n---\n")
          env = {**os.environ, "SUPERPOWERS_VALIDATOR_BYPASS": "1"}
          result = subprocess.run(
              [PYTHON, VALIDATOR_SCRIPT, "report", str(bad_report)],
              capture_output=True, text=True, env=env,
          )
          assert result.returncode == 0
          assert "BYPASS" in result.stderr
  ```

- [x] **Step 2: Run tests** (9 passed)

  Run: `.venv/bin/python3 -m pytest tests/unit/test_validators/test_validate_report_pydantic.py -v`
  Expected: All ~10 tests PASS

- [x] **Step 3: Commit** (204039f)

  ```bash
  git add tests/unit/test_validators/test_validate_report_pydantic.py
  git commit -m "test: add CLI entry-point tests for validators.py report subcommand"
  ```
