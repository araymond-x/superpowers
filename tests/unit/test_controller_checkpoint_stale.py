#!/usr/bin/env python3
"""
Unit tests for controller-checkpoint.py — stale artifact detection in pre-execution phase.

Tests cover:
  - Clean workspace (no stale artifacts) → no warning
  - Existing DEVIATIONS.md with content → WARNING
  - Existing reports/task-* files → WARNING
  - Existing pre-execution-audit files → WARNING
  - Combined stale artifacts → single WARNING listing all
  - Empty DEVIATIONS.md → no warning (freshly created, no content)
  - Empty reports/ directory → no warning

Run: python3 -m pytest tests/unit/test_controller_checkpoint_stale.py -v
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "skills",
    "subagent-driven-development",
    "scripts",
    "controller-checkpoint.py",
)

MINIMAL_PLAN = """\
# Implementation Plan

### Task 1 — Setup
- [ ] Create scaffolding

### Task 2 — Build
- [ ] Build it
"""


def run_checkpoint(plan_content, deviations_content=None, report_files=None):
    """
    Set up a temp directory with the given artifacts and run controller-checkpoint
    in pre-execution phase. Returns parsed result dict.

    Args:
        plan_content: Content for the plan file.
        deviations_content: If not None, create DEVIATIONS.md with this content.
        report_files: Dict of {filename: content} to create in reports/.
    """
    tmpdir = tempfile.mkdtemp()

    # Write plan file
    plan_path = os.path.join(tmpdir, "plan.md")
    with open(plan_path, "w") as f:
        f.write(plan_content)

    # Write DEVIATIONS.md if provided
    dev_path = os.path.join(tmpdir, "DEVIATIONS.md")
    if deviations_content is not None:
        with open(dev_path, "w") as f:
            f.write(deviations_content)

    # Create reports directory and files
    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    if report_files:
        for filename, content in report_files.items():
            with open(os.path.join(reports_dir, filename), "w") as f:
                f.write(content)

    try:
        cmd = [
            sys.executable, SCRIPT_PATH,
            "--phase", "pre-execution",
            "--plan-file", plan_path,
            "--deviations-file", dev_path,
            "--reports-dir", reports_dir,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = json.loads(result.stdout) if result.stdout.strip() else {}
        return {
            "exit_code": result.returncode,
            "output": output,
            "stderr": result.stderr,
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


PRIOR_DEVIATIONS = """\
# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Task 2 | IndependentDecision | Used regex fallback | Accepted |

## Deferred Work
- Refactor parser module
"""

PRIOR_REPORT = """\
# Task 001 Report — Build extraction service
# Date: 2026-03-28T14:30:00Z
# Status: DONE

**Implementation Summary**
Built the extraction service...
"""


class TestStaleArtifactDetection:
    """Pre-execution should warn when stale SDD artifacts exist from a prior session."""

    def test_clean_workspace_no_warning(self):
        """No DEVIATIONS.md, empty reports/ → no stale artifact warning."""
        result = run_checkpoint(MINIMAL_PLAN)
        checks = result["output"].get("checks", {})
        stale_check = checks.get("stale_artifacts", {})
        if stale_check:
            assert stale_check.get("status") != "WARNING"

    def test_existing_deviations_with_content_warns(self):
        """DEVIATIONS.md with prior session content → WARNING."""
        result = run_checkpoint(MINIMAL_PLAN, deviations_content=PRIOR_DEVIATIONS)
        checks = result["output"].get("checks", {})
        stale_check = checks.get("stale_artifacts", {})
        assert stale_check.get("status") == "WARNING", \
            f"Expected WARNING for stale DEVIATIONS.md, got: {stale_check}"

    def test_existing_task_reports_warns(self):
        """reports/task-* files from prior session → WARNING."""
        result = run_checkpoint(
            MINIMAL_PLAN,
            report_files={"task-001-implementer-report.md": PRIOR_REPORT},
        )
        checks = result["output"].get("checks", {})
        stale_check = checks.get("stale_artifacts", {})
        assert stale_check.get("status") == "WARNING", \
            f"Expected WARNING for stale task reports, got: {stale_check}"

    def test_existing_pre_execution_audit_warns(self):
        """Pre-execution audit files from prior session → WARNING."""
        result = run_checkpoint(
            MINIMAL_PLAN,
            report_files={"pre-execution-audit.md": "# Prior audit\nVerdict: CLEAR"},
        )
        checks = result["output"].get("checks", {})
        stale_check = checks.get("stale_artifacts", {})
        assert stale_check.get("status") == "WARNING", \
            f"Expected WARNING for stale audit files, got: {stale_check}"

    def test_combined_stale_artifacts_single_warning(self):
        """Multiple stale artifacts → single WARNING listing all of them."""
        result = run_checkpoint(
            MINIMAL_PLAN,
            deviations_content=PRIOR_DEVIATIONS,
            report_files={
                "task-001-implementer-report.md": PRIOR_REPORT,
                "pre-execution-audit.md": "# Prior audit",
            },
        )
        checks = result["output"].get("checks", {})
        stale_check = checks.get("stale_artifacts", {})
        assert stale_check.get("status") == "WARNING"
        detail = stale_check.get("detail", "").lower()
        assert "deviations" in detail, "Should mention DEVIATIONS.md"
        assert "report" in detail, "Should mention report files"

    def test_stale_artifacts_is_warning_not_blocker(self):
        """Stale artifacts produce WARNING exit code (2), not FAIL (1)."""
        result = run_checkpoint(
            MINIMAL_PLAN,
            deviations_content=PRIOR_DEVIATIONS,
        )
        assert result["exit_code"] != 1, "Stale artifacts should be WARNING, not BLOCKER"

    def test_empty_deviations_no_warning(self):
        """DEVIATIONS.md exists but is empty → no stale artifact warning."""
        result = run_checkpoint(MINIMAL_PLAN, deviations_content="")
        checks = result["output"].get("checks", {})
        stale_check = checks.get("stale_artifacts", {})
        if stale_check:
            assert stale_check.get("status") != "WARNING", \
                "Empty DEVIATIONS.md should not trigger stale warning"

    def test_warning_detail_mentions_archival(self):
        """Warning message should reference the archival protocol."""
        result = run_checkpoint(
            MINIMAL_PLAN,
            deviations_content=PRIOR_DEVIATIONS,
        )
        checks = result["output"].get("checks", {})
        stale_check = checks.get("stale_artifacts", {})
        detail = stale_check.get("detail", "").lower()
        assert any(word in detail for word in ["archive", "prior session", "clean"]), \
            f"Warning should reference archival or prior session: {stale_check.get('detail', '')}"
