"""
Shared test helpers for SDD hook tests.

Provides workspace setup, report generation, and hook input construction
for testing sdd-pre-dispatch-hook.sh and sdd-report-guard.sh.
"""

import json
import os
import subprocess
from datetime import datetime, timezone


def make_hook_input(description: str, prompt: str = "", cwd: str = "") -> str:
    """JSON payload matching Claude Code PreToolUse hook input.

    Args:
        description: The tool_input.description field (dispatch description).
        prompt: The tool_input.prompt field (first 500 chars used by hook).
        cwd: Working directory for the hook. Empty string if not needed.

    Returns:
        JSON string ready to pipe to the hook via stdin.
    """
    payload = {
        "tool_input": {
            "description": description,
            "prompt": prompt,
        },
        "cwd": cwd,
    }
    return json.dumps(payload)


def make_guard_input(command: str) -> str:
    """JSON payload matching Claude Code PreToolUse hook input for Bash tool.

    Args:
        command: The bash command being checked by the guard.

    Returns:
        JSON string ready to pipe to the guard hook via stdin.
    """
    payload = {
        "tool_input": {
            "command": command,
        },
    }
    return json.dumps(payload)


# The 9 required sections from _report_utils.py REQUIRED_SECTIONS
IMPLEMENTER_REPORT_TEMPLATE = """\
# Task {task_number:03d} Report -- {title}
# Date: {date}
# Status: DONE

## Status
DONE

## Implementation Summary
Implemented the feature as specified in the plan. All requirements met.

## Files Changed
- src/module.py (modified)
- tests/test_module.py (created)

## Source Files Read
- docs/imp-plans/plan.md
- src/existing_module.py

## Tests
- test_feature_basic: PASS
- test_feature_edge_case: PASS
All tests passing.

## Contract Compliance
All contracts verified. Input/output types match spec.

## Deviations from Plan
None.

## Self-Review Findings
No issues found during self-review.

## Concerns
None.
"""

SPEC_REVIEW_TEMPLATE = """\
# Spec Compliance Review -- Task {task_number:03d}
# Date: {date}
# Verdict: PASS

The implementation matches the plan specification.
All required files were created/modified as specified.
No deviations detected.
"""

QUALITY_REVIEW_TEMPLATE = """\
# Code Quality Review -- Task {task_number:03d}
# Date: {date}
# Verdict: PASS

Code quality is acceptable. No major issues found.
Style follows project conventions. Tests are adequate.
"""


def setup_sdd_workspace(tmpdir: str, task_count: int) -> None:
    """Create minimal SDD workspace: reports/, DEVIATIONS.md, pre-execution-audit, plan, git init on feature branch.

    Args:
        tmpdir: Path to temporary directory to set up.
        task_count: Number of task headers to include in the plan.
    """
    # Create reports directory
    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # Create DEVIATIONS.md
    dev_path = os.path.join(tmpdir, "DEVIATIONS.md")
    with open(dev_path, "w") as f:
        f.write("# Deviations Register\n\n"
                "> Auto-maintained by controller during subagent-driven-development execution.\n\n"
                "| Task | Type | Description | Disposition |\n"
                "|------|------|-------------|-------------|\n")

    # Create pre-execution audit (>50 bytes)
    audit_path = os.path.join(reports_dir, "pre-execution-audit.md")
    with open(audit_path, "w") as f:
        f.write("# Pre-Execution Audit\n\n"
                "## Self-Assessment\n"
                "All prerequisites verified. Plan ingested. Deviations register created.\n\n"
                "## Auditor Verdict\n"
                "CLEAR -- No remediation orders.\n")

    # Create plan with task headers in docs/imp-plans/
    plan_dir = os.path.join(tmpdir, "docs", "imp-plans")
    os.makedirs(plan_dir, exist_ok=True)
    plan_path = os.path.join(plan_dir, "plan.md")
    with open(plan_path, "w") as f:
        f.write("# Implementation Plan\n\n")
        f.write("**Source Contracts:** None\n\n")
        for i in range(task_count):
            f.write(f"### Task {i} -- Step {i}\n")
            f.write(f"- [ ] Do step {i}\n\n")

    # Git init on feature branch
    subprocess.run(
        ["git", "init"],
        cwd=tmpdir, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "feature-test"],
        cwd=tmpdir, capture_output=True, check=True,
    )
    # Initial commit so git is functional
    subprocess.run(
        ["git", "add", "."],
        cwd=tmpdir, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmpdir, capture_output=True, check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@test.com",
             "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@test.com"},
    )


def create_task_reports(tmpdir: str, task_number: int, include_dispatch_log: bool = True) -> None:
    """Create implementer-report, spec-review, and quality-review for a task.

    All files use zero-padded 3-digit naming (task-NNN-*).
    Implementer report has all 9 required sections and is >50 bytes.
    Optionally appends reviewer dispatch entries to .dispatch-log.

    Args:
        tmpdir: Path to the SDD workspace root.
        task_number: The task number to create reports for.
        include_dispatch_log: Whether to append dispatch log entries.
    """
    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    padded = f"{task_number:03d}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Implementer report with all 9 sections
    impl_path = os.path.join(reports_dir, f"task-{padded}-implementer-report.md")
    with open(impl_path, "w") as f:
        f.write(IMPLEMENTER_REPORT_TEMPLATE.format(
            task_number=task_number, title=f"Step {task_number}", date=now,
        ))

    # Spec review
    spec_path = os.path.join(reports_dir, f"task-{padded}-spec-review.md")
    with open(spec_path, "w") as f:
        f.write(SPEC_REVIEW_TEMPLATE.format(task_number=task_number, date=now))

    # Quality review
    qual_path = os.path.join(reports_dir, f"task-{padded}-quality-review.md")
    with open(qual_path, "w") as f:
        f.write(QUALITY_REVIEW_TEMPLATE.format(task_number=task_number, date=now))

    # Dispatch log entries
    if include_dispatch_log:
        log_path = os.path.join(reports_dir, ".dispatch-log")
        with open(log_path, "a") as f:
            f.write(f"{now} DISPATCH reviewer task={task_number} type=spec-review\n")
            f.write(f"{now} DISPATCH reviewer task={task_number} type=quality-review\n")


def create_checkpoint_file(tmpdir: str, task_number: int) -> None:
    """Create a pre-dispatch checkpoint file for a task (>50 bytes).

    Args:
        tmpdir: Path to the SDD workspace root.
        task_number: The task number for the checkpoint.
    """
    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    padded = f"{task_number:03d}"
    checkpoint_path = os.path.join(reports_dir, f"checkpoint-pre-dispatch-{padded}.json")
    with open(checkpoint_path, "w") as f:
        json.dump({
            "status": "PASS",
            "phase": "pre-dispatch",
            "task": task_number,
            "detail": "checkpoint for pre-dispatch verification",
        }, f)


def setup_full_sdd_workspace(tmpdir: str, total_tasks: int, completed_tasks: int) -> None:
    """Full workspace: plan, DEVIATIONS.md, audit, reports + dispatch log + checkpoint files for all completed tasks.

    Args:
        tmpdir: Path to temporary directory to set up.
        total_tasks: Total number of tasks in the plan.
        completed_tasks: Number of tasks already completed (0..N-1).
    """
    setup_sdd_workspace(tmpdir, total_tasks)

    for i in range(completed_tasks):
        create_task_reports(tmpdir, i, include_dispatch_log=True)
        # Create checkpoint for the NEXT task (which was checked before dispatching task i)
        # The checkpoint for task N is created before dispatching task N
        create_checkpoint_file(tmpdir, i)

    # Create checkpoint for the next task to be dispatched
    if completed_tasks < total_tasks:
        create_checkpoint_file(tmpdir, completed_tasks)
