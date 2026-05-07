"""
TDD red-phase tests for SDD dispatch provenance logging and verification.

Tests cover:
  - Reviewer dispatches create .dispatch-log entries (TestReviewerDispatchLogging)
  - Implementer dispatches blocked without prior dispatch log (TestDispatchProvenanceVerification)
  - Report guard warns on .dispatch-log manipulation (TestReportGuardDispatchLog)

These tests are expected to FAIL until the hook code implements dispatch provenance.
The failure mode should be assertion failures (not import/infrastructure errors).

Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_dispatch_log.py -v
"""

import json
import os
import subprocess

import pytest

from sdd_test_helpers import (
    create_checkpoint_file,
    create_task_reports,
    make_guard_input,
    make_hook_input,
    setup_full_sdd_workspace,
    setup_sdd_workspace,
)

# Resolve hook paths relative to this test file
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.join(_TESTS_DIR, "..", "..")

HOOK_PATH = os.path.normpath(os.path.join(
    _REPO_ROOT, "skills", "subagent-driven-development", "scripts",
    "sdd-pre-dispatch-hook.sh",
))

GUARD_PATH = os.path.normpath(os.path.join(
    _REPO_ROOT, "skills", "subagent-driven-development", "scripts",
    "sdd-report-guard.sh",
))


def run_hook(hook_path: str, stdin_data: str, timeout: int = 10) -> subprocess.CompletedProcess:
    """Run a hook script with JSON on stdin and return the result."""
    return subprocess.run(
        ["bash", hook_path],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class TestReviewerDispatchLogging:
    """Tests for when the hook adds entries to reports/.dispatch-log on reviewer dispatches."""

    def test_reviewer_dispatch_creates_log_entry(self, tmp_path):
        """A spec-review dispatch should create a .dispatch-log entry with task number and type."""
        tmpdir = str(tmp_path)
        reports_dir = os.path.join(tmpdir, "reports")
        os.makedirs(reports_dir)

        hook_input = make_hook_input(
            description="Review task 3 spec compliance",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, f"Hook should allow reviewer dispatch, stderr: {result.stderr}"

        log_path = os.path.join(reports_dir, ".dispatch-log")
        assert os.path.isfile(log_path), "Hook should create .dispatch-log for reviewer dispatch"

        log_content = open(log_path).read()
        assert "task=3" in log_content, f"Log should contain task=3, got: {log_content}"
        assert "type=spec-review" in log_content, f"Log should contain type=spec-review, got: {log_content}"

    def test_quality_reviewer_dispatch_logged(self, tmp_path):
        """A quality-review dispatch should be logged with the correct type."""
        tmpdir = str(tmp_path)
        reports_dir = os.path.join(tmpdir, "reports")
        os.makedirs(reports_dir)

        hook_input = make_hook_input(
            description="Dispatch code quality review for task 5",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, f"Hook should allow reviewer dispatch, stderr: {result.stderr}"

        log_path = os.path.join(reports_dir, ".dispatch-log")
        assert os.path.isfile(log_path), "Hook should create .dispatch-log for quality review dispatch"

        log_content = open(log_path).read()
        assert "task=5" in log_content, f"Log should contain task=5, got: {log_content}"
        assert "type=quality-review" in log_content, f"Log should contain type=quality-review, got: {log_content}"

    def test_non_reviewer_dispatch_does_not_add_log_entry(self, tmp_path):
        """A non-reviewer, non-implementer dispatch should not add a reviewer entry to .dispatch-log."""
        tmpdir = str(tmp_path)

        # Set up workspace with task 0 completed and checkpoint for task 1
        setup_sdd_workspace(tmpdir, task_count=3)
        create_task_reports(tmpdir, task_number=0, include_dispatch_log=True)
        create_checkpoint_file(tmpdir, task_number=1)

        # Record the dispatch log state before the hook run
        log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
        log_before = open(log_path).read() if os.path.isfile(log_path) else ""

        hook_input = make_hook_input(
            description="Write test helpers",
            prompt="You are writing tests",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        # The hook should allow this (exit 0) since it's not an implementer pattern
        assert result.returncode == 0, f"Non-SDD dispatch should be allowed, stderr: {result.stderr}"

        # No NEW reviewer entry should be added
        log_after = open(log_path).read() if os.path.isfile(log_path) else ""
        assert log_after == log_before, (
            f"Non-reviewer dispatch should not modify .dispatch-log.\n"
            f"Before: {log_before!r}\nAfter: {log_after!r}"
        )


class TestDispatchProvenanceVerification:
    """Tests for blocking implementer dispatches when dispatch log is missing."""

    def test_blocked_without_dispatch_log(self, tmp_path):
        """Implementer dispatch for task 1 should be blocked if task 0 has no dispatch log entries."""
        tmpdir = str(tmp_path)

        setup_sdd_workspace(tmpdir, task_count=3)
        # Create task 0 reports WITHOUT dispatch log
        create_task_reports(tmpdir, task_number=0, include_dispatch_log=False)
        create_checkpoint_file(tmpdir, task_number=1)

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 2, (
            f"Should block dispatch without dispatch log. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
        assert "dispatch" in result.stderr.lower(), (
            f"Error message should mention dispatch provenance. stderr: {result.stderr}"
        )

    def test_allowed_with_valid_dispatch_log(self, tmp_path):
        """Implementer dispatch for task 1 should be allowed when task 0 has valid dispatch log."""
        tmpdir = str(tmp_path)

        setup_sdd_workspace(tmpdir, task_count=3)
        # Create task 0 reports WITH dispatch log
        create_task_reports(tmpdir, task_number=0, include_dispatch_log=True)
        create_checkpoint_file(tmpdir, task_number=1)
        # Partner review for task 1 (required by Check 5d) + dispatch provenance entry
        reports_dir = os.path.join(tmpdir, "reports")
        with open(os.path.join(reports_dir, "partner-review-001.md"), "w") as f:
            f.write("# Partner Review Task 001\n**Status:** APPROVED\n" + "x" * 60)
        with open(os.path.join(reports_dir, ".dispatch-log"), "a") as f:
            f.write("2026-05-07T00:00:00Z DISPATCH reviewer task=1 type=partner-review\n")

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Should allow dispatch with valid dispatch log. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_minimum_tier_quality_allowed_without_dispatch(self, tmp_path):
        """Minimum-tier quality review should be allowed even without a quality-review dispatch log entry."""
        tmpdir = str(tmp_path)

        setup_sdd_workspace(tmpdir, task_count=3)
        create_task_reports(tmpdir, task_number=0, include_dispatch_log=False)

        # Write dispatch log with ONLY spec-review (no quality-review)
        log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
        with open(log_path, "w") as f:
            f.write("2026-04-07T10:00:00Z DISPATCH reviewer task=0 type=spec-review\n")

        # Replace quality-review with minimum-tier variant
        reports_dir = os.path.join(tmpdir, "reports")
        qual_standard = os.path.join(reports_dir, "task-000-quality-review.md")
        qual_minimum = os.path.join(reports_dir, "task-000-quality-review-minimum-tier.md")
        if os.path.isfile(qual_standard):
            os.rename(qual_standard, qual_minimum)

        create_checkpoint_file(tmpdir, task_number=1)
        # Partner review for task 1 (required by Check 5d) + dispatch provenance entry
        with open(os.path.join(reports_dir, "partner-review-001.md"), "w") as f:
            f.write("# Partner Review Task 001\n**Status:** APPROVED\n" + "x" * 60)
        with open(log_path, "a") as f:
            f.write("2026-05-07T00:00:00Z DISPATCH reviewer task=1 type=partner-review\n")

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Minimum-tier quality review should exempt quality dispatch requirement. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )


class TestReportGuardDispatchLog:
    """Tests for the report guard warning on .dispatch-log manipulation."""

    def test_warns_on_dispatch_log_echo(self):
        """Guard should warn when a Bash command writes to .dispatch-log."""
        guard_input = make_guard_input('echo "fake" >> reports/.dispatch-log')
        result = run_hook(GUARD_PATH, guard_input)

        assert result.returncode == 0, "Guard should always exit 0 (warning only)"
        stderr_lower = result.stderr.lower()
        assert "warning" in stderr_lower, (
            f"Guard should warn about .dispatch-log manipulation. stderr: {result.stderr}"
        )
        assert "dispatch" in stderr_lower, (
            f"Warning should mention dispatch log. stderr: {result.stderr}"
        )

    def test_no_warning_for_unrelated_command(self):
        """Guard should not warn for commands that don't touch .dispatch-log."""
        guard_input = make_guard_input("ls -la reports/")
        result = run_hook(GUARD_PATH, guard_input)

        assert result.returncode == 0, "Guard should always exit 0"
        assert "dispatch" not in result.stderr.lower(), (
            f"Should not warn about dispatch for unrelated command. stderr: {result.stderr}"
        )
