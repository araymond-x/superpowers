"""
TDD red-phase tests for SDD hard gate enforcement.

Tests cover:
  - Token estimation blocking when task header not found in plan (TestTokenEstimationBlocking)
  - Context summary blocking past midpoint (TestContextSummaryBlocking)
  - Checkpoint file gate before dispatch (TestCheckpointFileGate)

Expected failures (TDD red):
  - Token estimation SKIPPED is currently a WARNING, not a BLOCK
  - Context summary past midpoint is currently a WARNING, not a BLOCK
  - No checkpoint file gate exists yet

Expected passes:
  - "allows" tests verify existing permissive behavior

Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v
"""

import json
import os
import subprocess

import pytest

from sdd_test_helpers import (
    create_checkpoint_file,
    create_task_reports,
    make_hook_input,
    setup_full_sdd_workspace,
)

# Resolve hook path relative to this test file
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.join(_TESTS_DIR, "..", "..")

HOOK_PATH = os.path.normpath(os.path.join(
    _REPO_ROOT, "skills", "subagent-driven-development", "scripts",
    "sdd-pre-dispatch-hook.sh",
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


class TestTokenEstimationBlocking:
    """Token estimation should BLOCK (not warn) when the task header is not found in the plan."""

    def test_blocks_when_task_header_not_in_plan(self, tmp_path):
        """Dispatching task 99 (not in plan) should be blocked with exit 2."""
        tmpdir = str(tmp_path)
        # 3 total tasks (0, 1, 2), task 0 completed
        setup_full_sdd_workspace(tmpdir, total_tasks=3, completed_tasks=1)

        # Create checkpoint for task 99 (the hook requires checkpoint per Task 6,
        # but we're testing token estimation here so provide the checkpoint)
        create_checkpoint_file(tmpdir, task_number=99)

        hook_input = make_hook_input(
            description="Implement task 99",
            prompt="You are implementing task 99",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        # Should BLOCK because task 99 doesn't exist in the plan.
        # Currently: exits 0 with TOKEN_WARNING in additionalContext (soft warning).
        # Expected after fix: exit 2 with blocking message.
        assert result.returncode == 2, (
            f"Should block dispatch for task not in plan. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}, "
            f"stdout: {result.stdout}"
        )
        stderr_lower = result.stderr.lower()
        assert "token" in stderr_lower or "blocked" in stderr_lower, (
            f"Error should mention token estimation or BLOCKED. stderr: {result.stderr}"
        )

    def test_allows_when_task_header_found(self, tmp_path):
        """Dispatching task 1 (exists in plan) should be allowed."""
        tmpdir = str(tmp_path)
        # 5 total tasks (0-4), task 0 completed
        setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=1)

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Should allow dispatch for task found in plan. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )


class TestContextSummaryBlocking:
    """Context summary should BLOCK (not warn) when past midpoint without summary file."""

    def test_blocks_past_midpoint_without_summary(self, tmp_path):
        """Task 6 of 10 (past midpoint of 5) without context-summary.md should be blocked."""
        tmpdir = str(tmp_path)
        # 10 total tasks (0-9), 6 completed (tasks 0-5)
        setup_full_sdd_workspace(tmpdir, total_tasks=10, completed_tasks=6)

        # Verify no context-summary.md exists
        summary_path = os.path.join(tmpdir, "reports", "context-summary.md")
        assert not os.path.isfile(summary_path), "Precondition: no context-summary.md"

        hook_input = make_hook_input(
            description="Implement task 6",
            prompt="You are implementing task 6",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        # Should BLOCK because we're past midpoint without context summary.
        # Currently: exits 0 with CONTEXT_SUMMARY_WARNING in additionalContext.
        # Expected after fix: exit 2 with blocking message.
        assert result.returncode == 2, (
            f"Should block dispatch past midpoint without context summary. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}, "
            f"stdout: {result.stdout}"
        )
        stderr_lower = result.stderr.lower()
        assert "context" in stderr_lower or "midpoint" in stderr_lower, (
            f"Error should mention context summary or midpoint. stderr: {result.stderr}"
        )

    def test_allows_past_midpoint_with_summary(self, tmp_path):
        """Task 6 of 10 with context-summary.md present should be allowed."""
        tmpdir = str(tmp_path)
        # 10 total tasks (0-9), 6 completed (tasks 0-5)
        setup_full_sdd_workspace(tmpdir, total_tasks=10, completed_tasks=6)

        # Create context-summary.md (>50 bytes)
        summary_path = os.path.join(tmpdir, "reports", "context-summary.md")
        with open(summary_path, "w") as f:
            f.write(
                "# Context Summary\n\n"
                "## Completed Tasks\n"
                "Tasks 0-5 completed successfully. All reviews passed.\n"
                "Key decisions: used standard architecture pattern.\n"
            )

        hook_input = make_hook_input(
            description="Implement task 6",
            prompt="You are implementing task 6",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Should allow dispatch past midpoint with context summary present. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_allows_before_midpoint_without_summary(self, tmp_path):
        """Task 2 of 10 (before midpoint of 5) without context-summary.md should be allowed."""
        tmpdir = str(tmp_path)
        # 10 total tasks (0-9), 2 completed (tasks 0-1)
        setup_full_sdd_workspace(tmpdir, total_tasks=10, completed_tasks=2)

        # Verify no context-summary.md exists
        summary_path = os.path.join(tmpdir, "reports", "context-summary.md")
        assert not os.path.isfile(summary_path), "Precondition: no context-summary.md"

        hook_input = make_hook_input(
            description="Implement task 2",
            prompt="You are implementing task 2",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Should allow dispatch before midpoint without context summary. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )


class TestCheckpointFileGate:
    """Checkpoint file must exist (>50 bytes) before dispatch is allowed."""

    def test_blocks_without_checkpoint_file(self, tmp_path):
        """Dispatch should be blocked when checkpoint-pre-dispatch-NNN.json is missing."""
        tmpdir = str(tmp_path)
        # 3 total tasks (0-2), task 0 completed
        setup_full_sdd_workspace(tmpdir, total_tasks=3, completed_tasks=1)

        # Remove the checkpoint file for task 1 (created by setup_full_sdd_workspace)
        checkpoint_path = os.path.join(
            tmpdir, "reports", "checkpoint-pre-dispatch-001.json"
        )
        assert os.path.isfile(checkpoint_path), "Precondition: checkpoint exists from setup"
        os.remove(checkpoint_path)

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        # Should BLOCK because no checkpoint file for this task.
        # Currently: no checkpoint gate exists, exits 0.
        # Expected after fix: exit 2.
        assert result.returncode == 2, (
            f"Should block dispatch without checkpoint file. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}, "
            f"stdout: {result.stdout}"
        )
        assert "checkpoint" in result.stderr.lower(), (
            f"Error should mention checkpoint. stderr: {result.stderr}"
        )

    def test_allows_with_checkpoint_file(self, tmp_path):
        """Dispatch should be allowed when checkpoint file exists with valid content."""
        tmpdir = str(tmp_path)
        # 3 total tasks (0-2), task 0 completed (includes checkpoint for task 1)
        setup_full_sdd_workspace(tmpdir, total_tasks=3, completed_tasks=1)

        # Verify checkpoint exists
        checkpoint_path = os.path.join(
            tmpdir, "reports", "checkpoint-pre-dispatch-001.json"
        )
        assert os.path.isfile(checkpoint_path), "Precondition: checkpoint should exist"

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Should allow dispatch with valid checkpoint file. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_blocks_with_tiny_checkpoint_file(self, tmp_path):
        """Dispatch should be blocked when checkpoint file exists but is below 50-byte minimum."""
        tmpdir = str(tmp_path)
        # 3 total tasks (0-2), task 0 completed
        setup_full_sdd_workspace(tmpdir, total_tasks=3, completed_tasks=1)

        # Overwrite checkpoint with trivial content (2 bytes, below 50-byte minimum)
        checkpoint_path = os.path.join(
            tmpdir, "reports", "checkpoint-pre-dispatch-001.json"
        )
        with open(checkpoint_path, "w") as f:
            f.write("{}")

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        # Should BLOCK because checkpoint is too small.
        # Currently: no checkpoint gate exists, exits 0.
        # Expected after fix: exit 2.
        assert result.returncode == 2, (
            f"Should block dispatch with tiny checkpoint file. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}, "
            f"stdout: {result.stdout}"
        )
        assert "checkpoint" in result.stderr.lower(), (
            f"Error should mention checkpoint. stderr: {result.stderr}"
        )
