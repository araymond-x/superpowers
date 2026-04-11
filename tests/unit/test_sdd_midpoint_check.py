"""
Tests for Check 6b (context summary midpoint) in sdd-pre-dispatch-hook.sh.

Initial test: multi-line grep bug. The idiom
`grep -c <pat> <file> || echo "0"` produces "0\\n0" on zero-match files
because grep -c already prints "0" and also returns exit 1 on no match,
causing the defensive || echo to APPEND a second "0" on a new line. The
resulting multi-line value crashes subsequent bash arithmetic with
"bad math expression".

This file will grow as additional Check 6b tests are added.

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
