"""
Tests for Check 6b (context summary midpoint) in sdd-pre-dispatch-hook.sh.

Covers two bugs found in the min-payment-extraction SDD session (2026-04-10):

  1. Multi-line grep bug: `grep -c <pat> <file> || echo "0"` produces
     "0\\n0" on zero-match files because grep -c already prints "0" and
     also returns exit 1 on no match, causing the defensive || echo to
     APPEND a second "0" on a new line. The resulting multi-line value
     crashes subsequent bash arithmetic with "bad math expression".

  2. Wrong plan scoping: Check 6b counts task headers across ALL `.md`
     files in docs/imp-plans/ and docs/plans/, including stale plans from
     prior features. TOTAL_TASKS gets inflated, midpoint gets pushed past
     the real halfway point, and the context-summary trigger silently
     delays beyond the intended enforcement point.

Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_midpoint_check.py -v
"""

import os
import subprocess
from pathlib import Path

from sdd_test_helpers import (
    make_hook_input,
    setup_full_sdd_workspace,
)

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.join(_TESTS_DIR, "..", "..")

HOOK_PATH = os.path.normpath(
    os.path.join(
        _REPO_ROOT,
        "skills",
        "subagent-driven-development",
        "scripts",
        "sdd-pre-dispatch-hook.sh",
    )
)


def run_hook(
    hook_path: str, stdin_data: str, timeout: int = 10
) -> subprocess.CompletedProcess:
    """Run the pre-dispatch hook with JSON on stdin."""
    return subprocess.run(
        ["bash", hook_path],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _write_aux_plan(tmpdir: str, filename: str, task_count: int) -> None:
    """Create an auxiliary plan file in docs/imp-plans/ with N task headers.

    Used to simulate stale plans from other features sitting alongside the
    current feature's plan.
    """
    plan_dir = Path(tmpdir) / "docs" / "imp-plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / filename
    lines = ["# Auxiliary Plan\n\n"]
    for i in range(task_count):
        lines.append(f"### Task {i} -- Aux step {i}\n")
        lines.append(f"- [ ] Do aux step {i}\n\n")
    plan_path.write_text("".join(lines))


class TestCheck6bMultiLineGrepBug:
    """Check 6b's `grep -c ... || echo '0'` idiom must not produce multi-line
    TASK_COUNT values that crash bash arithmetic."""

    def test_tolerates_plan_file_with_zero_task_headers(self, tmp_path):
        """A plan-shaped file with zero '### Task N' headers must not crash
        the hook.

        Setup: current plan has 4 tasks, tasks 0-2 completed; plus a
        'placeholder' .md file in docs/imp-plans/ with no task headers.
        Dispatching task 3 must not trigger a 'bad math expression' bash
        runtime crash from multi-line TASK_COUNT.
        """
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=4, completed_tasks=3)

        placeholder = Path(tmpdir) / "docs" / "imp-plans" / "zero-tasks.md"
        placeholder.write_text(
            "# Placeholder Plan\n\nNo task headers yet — design doc in progress.\n"
        )

        hook_input = make_hook_input(
            description="Implement task 3",
            prompt="You are implementing task 3",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        stderr_lower = result.stderr.lower()
        assert "bad math expression" not in stderr_lower, (
            "Hook crashed on zero-count plan file — the multi-line grep bug "
            "triggered 'bad math expression' from $(( )) on multi-line input. "
            f"stderr: {result.stderr}"
        )
        assert "syntax error" not in stderr_lower, (
            "Hook hit an unexpected syntax error on zero-count plan file. "
            f"stderr: {result.stderr}"
        )


class TestCheck6bPlanScoping:
    """Check 6b must count tasks only in the plan containing the current task,
    not across all `.md` files under docs/imp-plans/ + docs/plans/."""

    def test_stale_plan_does_not_inflate_total_tasks(self, tmp_path):
        """A stale plan from another feature must not inflate TOTAL_TASKS.

        Setup: current plan has 4 tasks (0-3), tasks 0-2 completed; plus a
        6-task stale plan from a different feature sits alongside it.
        Dispatching task 3 should BLOCK — task 3 is past the midpoint of
        the 4-task current plan (midpoint = (4+1)/2 = 2, task 3 >= 2) and
        no context-summary.md exists.

        Without the scoping fix: TOTAL_TASKS = 4 + 6 = 10, midpoint = 5,
        task 3 < 5, hook ALLOWS (wrong).
        """
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=4, completed_tasks=3)

        _write_aux_plan(tmpdir, "stale-other-feature.md", task_count=6)

        assert not (
            tmp_path / "reports" / "context-summary.md"
        ).exists(), "Precondition: no context-summary.md should exist"

        hook_input = make_hook_input(
            description="Implement task 3",
            prompt="You are implementing task 3",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 2, (
            "Stale plan should not inflate TOTAL_TASKS. Task 3 is past the "
            "midpoint of the 4-task current plan and should block. "
            f"Exit: {result.returncode}, stderr: {result.stderr}"
        )
        stderr_lower = result.stderr.lower()
        assert "midpoint" in stderr_lower or "context" in stderr_lower, (
            f"Error should mention midpoint/context. stderr: {result.stderr}"
        )

    def test_allows_before_midpoint_with_stale_plans_present(self, tmp_path):
        """A task before midpoint must be allowed even with stale plans around.

        Setup: current plan has 10 tasks, tasks 0-1 completed; plus a 6-task
        stale plan and a zero-task empty plan file. Dispatching task 2 should
        ALLOW — midpoint of the 10-task current plan is 5, task 2 < 5.
        """
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=10, completed_tasks=2)

        _write_aux_plan(tmpdir, "stale-other-feature.md", task_count=6)
        _write_aux_plan(tmpdir, "empty-placeholder.md", task_count=0)

        hook_input = make_hook_input(
            description="Implement task 2",
            prompt="You are implementing task 2",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            "Task 2 is before the midpoint of the 10-task current plan and "
            "should be allowed even with stale/empty plans alongside. "
            f"Exit: {result.returncode}, stderr: {result.stderr}"
        )
