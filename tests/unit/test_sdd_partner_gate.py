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
        # Remove the partner review created by the helper — we're testing its absence
        partner_file = os.path.join(tmpdir, "reports", "partner-review-001.md")
        if os.path.exists(partner_file):
            os.remove(partner_file)

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


class TestPartnerReviewDispatchProvenance:
    """Tests for dispatch provenance added to Check 5d.

    Full-tier partner reviews require a dispatch log entry (type=partner-review task=N)
    written by the hook when the Agent call passed through it. Minimum-tier reviews
    are controller-written and exempt from provenance checks — consistent with the
    quality-review minimum-tier exemption in Check 4c.
    """

    def _remove_partner_dispatch_entries(self, tmpdir: str) -> None:
        log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
        if not os.path.exists(log_path):
            return
        with open(log_path) as f:
            lines = f.readlines()
        with open(log_path, "w") as f:
            f.writelines(l for l in lines if "type=partner-review" not in l)

    def test_full_tier_without_dispatch_entry_blocks(self, tmp_path):
        """Full-tier partner review file with no dispatch log entry should be blocked.

        This is the exact gap the wells-fargo run exploited: controller self-wrote
        partner-review files without dispatching the partner agent.
        """
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=1)
        # Surgically remove the partner-review dispatch log entry to simulate self-writing
        self._remove_partner_dispatch_entries(tmpdir)

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )

        result = run_hook(hook_input)

        assert result.returncode == 2, f"Should block self-written partner review. stderr: {result.stderr}"
        assert "partner" in result.stderr.lower(), (
            f"Error should mention partner review. stderr: {result.stderr}"
        )
        assert "dispatch" in result.stderr.lower(), (
            f"Error should mention dispatch. stderr: {result.stderr}"
        )

    def test_full_tier_with_dispatch_entry_passes(self, tmp_path):
        """Full-tier partner review with matching dispatch log entry should be allowed."""
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=1)
        # setup_full_sdd_workspace now writes partner-review dispatch log entries

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )

        result = run_hook(hook_input)

        assert result.returncode == 0, f"Should allow with dispatch provenance. stderr: {result.stderr}"

    def test_minimum_tier_exempt_from_dispatch_requirement(self, tmp_path):
        """Minimum-tier partner review does not require a dispatch log entry."""
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=1)
        # Remove the full-tier file and its dispatch log entry
        partner_file = os.path.join(tmpdir, "reports", "partner-review-001.md")
        if os.path.exists(partner_file):
            os.remove(partner_file)
        self._remove_partner_dispatch_entries(tmpdir)
        # Create minimum-tier only — no dispatch log entry
        create_partner_review(tmpdir, task_number=1, minimum_tier=True, size=100)

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )

        result = run_hook(hook_input)

        assert result.returncode == 0, f"Minimum-tier should not require dispatch entry. stderr: {result.stderr}"
