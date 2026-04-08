"""
Tests for SDD controller partner review gate (Check 5d).

Tests cover:
  - Dispatch blocked without partner-review file
  - Dispatch allowed with valid partner-review file
  - Dispatch allowed with minimum-tier partner-review
  - Dispatch blocked with tiny partner-review (< 50 bytes)
  - Task 0 exempt from partner review requirement

Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_partner_gate.py -v
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

HOOK_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "skills",
    "subagent-driven-development",
    "scripts",
    "sdd-pre-dispatch-hook.sh",
)


def run_hook(hook_input: str) -> subprocess.CompletedProcess:
    """Run the pre-dispatch hook with JSON input on stdin."""
    return subprocess.run(
        ["bash", HOOK_PATH],
        input=hook_input,
        capture_output=True,
        text=True,
    )


def create_partner_review(
    tmpdir: str, task_number: int, minimum_tier: bool = False, size: int = 100
) -> None:
    """Create a partner-review file for the given task.

    Args:
        tmpdir: Workspace root directory.
        task_number: Task number (zero-padded to 3 digits in filename).
        minimum_tier: If True, creates minimum-tier variant.
        size: Approximate file size in bytes.
    """
    padded = f"{task_number:03d}"
    suffix = "-minimum-tier" if minimum_tier else ""
    filepath = os.path.join(tmpdir, "reports", f"partner-review-{padded}{suffix}.md")
    content = f"# Partner Review Task {padded}\n**Status:** APPROVED\n"
    if size > len(content):
        content += "x" * (size - len(content))
    with open(filepath, "w") as f:
        f.write(content)


class TestPartnerReviewGate:
    """Tests for Check 5d: partner review evidence before implementer dispatch."""

    def test_blocks_without_partner_review(self, tmp_path):
        """Dispatch should be blocked when no partner-review file exists."""
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=1)
        # All other gates satisfied (reports, dispatch log, checkpoint) but NO partner review

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )

        result = run_hook(hook_input)

        assert result.returncode == 2, f"Should block without partner review. stderr: {result.stderr}"
        assert "partner" in result.stderr.lower(), (
            f"Error should mention partner review. stderr: {result.stderr}"
        )

    def test_allows_with_partner_review(self, tmp_path):
        """Dispatch should be allowed when partner-review file exists (>50 bytes)."""
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=1)
        create_partner_review(tmpdir, task_number=1, size=100)

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )

        result = run_hook(hook_input)

        assert result.returncode == 0, f"Should allow with partner review. stderr: {result.stderr}"

    def test_allows_with_minimum_tier(self, tmp_path):
        """Dispatch should be allowed with minimum-tier partner review."""
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=1)
        create_partner_review(tmpdir, task_number=1, minimum_tier=True, size=100)

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )

        result = run_hook(hook_input)

        assert result.returncode == 0, f"Should allow minimum tier. stderr: {result.stderr}"

    def test_blocks_with_tiny_partner_review(self, tmp_path):
        """Dispatch should be blocked when partner-review is under 50 bytes."""
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=1)
        create_partner_review(tmpdir, task_number=1, size=10)

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )

        result = run_hook(hook_input)

        assert result.returncode == 2, f"Should block with tiny file. stderr: {result.stderr}"

    def test_no_partner_required_for_task_zero(self, tmp_path):
        """Task 0 should be exempt from partner review (no prior context to verify)."""
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=0)
        # No partner review for task 0 -- should still be allowed

        hook_input = make_hook_input(
            description="Implement task 0",
            prompt="You are implementing task 0",
            cwd=tmpdir,
        )

        result = run_hook(hook_input)

        assert result.returncode == 0, f"Task 0 should be exempt. stderr: {result.stderr}"
