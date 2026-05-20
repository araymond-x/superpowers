"""
TDD red-phase tests for SDD hard gate enforcement.

Tests cover:
  - Token estimation blocking when task header not found in plan (TestTokenEstimationBlocking)
  - Context summary blocking past midpoint (TestContextSummaryBlocking)
  - Checkpoint file gate before dispatch (TestCheckpointFileGate)
  - Feature-dir layout support (TestFeatureDirLayout)
  - Backwards-compat fallback without .active-feature (TestBackwardsCompatFallback)
  - Plan-validation-gate blocking without .active-feature (TestPlanValidationGate)

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
    make_hook_input,
    setup_full_sdd_workspace,
    setup_manifest_workspace,
)

# Resolve hook path relative to this test file
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

# Alias for consistency with new test naming convention
SDD_PRE_DISPATCH_HOOK_PATH = HOOK_PATH

PLAN_VALIDATION_GATE_PATH = os.path.normpath(
    os.path.join(
        _REPO_ROOT,
        "skills",
        "writing-plans",
        "scripts",
        "plan-validation-gate-hook.sh",
    )
)


def run_hook(
    hook_path: str, stdin_data: str, timeout: int = 10
) -> subprocess.CompletedProcess:
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
        assert os.path.isfile(checkpoint_path), (
            "Precondition: checkpoint exists from setup"
        )
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


# ─── Feature-dir fixture ──────────────────────────────────────────────────────


@pytest.fixture
def feature_dir_workspace(tmp_path):
    """Create a workspace with per-feature directory layout.

    Returns:
        Tuple of (tmp_path, feat_path_str, feat_dir, reports_dir) where:
          - tmp_path: the project root (pathlib.Path)
          - feat_path_str: relative path to feature dir (str)
          - feat_dir: absolute pathlib.Path to feature dir
          - reports_dir: absolute pathlib.Path to feature dir's reports/
    """
    feat_path = "docs/imp-plans/2026-05-02-test-feature"
    feat_dir = tmp_path / feat_path
    reports_dir = feat_dir / "reports"
    reports_dir.mkdir(parents=True)

    (feat_dir / "deviations.md").write_text(
        "# Deviations\n\n| # | Description | Disposition |\n"
    )
    (feat_dir / "plan.md").write_text("### Task 0: Setup\n### Task 1: Build\n")

    active_feature = tmp_path / ".active-feature"
    active_feature.write_text(feat_path)

    return tmp_path, feat_path, feat_dir, reports_dir


def _setup_feature_dir_sdd_workspace(
    tmp_path: object,
    feat_path: str,
    feat_dir: object,
    reports_dir: object,
    total_tasks: int,
    completed_tasks: int,
) -> None:
    """Set up a full SDD workspace using per-feature directory layout.

    Writes plan, pre-execution-audit, git init, task reports, checkpoints,
    and partner reviews — all under feat_dir, with .active-feature at root.

    Args:
        tmp_path: project root (pathlib.Path)
        feat_path: relative path to feature dir (str)
        feat_dir: absolute pathlib.Path to feature dir
        reports_dir: absolute pathlib.Path to reports/ within feat_dir
        total_tasks: total number of tasks in the plan
        completed_tasks: number of tasks already completed
    """
    import subprocess as _sp
    from datetime import datetime, timezone

    # Write plan with requested task count
    plan_content = "# Implementation Plan\n\n**Source Contracts:** None\n\n"
    for i in range(total_tasks):
        plan_content += f"### Task {i} -- Step {i}\n- [ ] Do step {i}\n\n"
    (feat_dir / "plan.md").write_text(plan_content)

    # Pre-execution audit (>50 bytes)
    audit_path = reports_dir / "pre-execution-audit.md"
    audit_path.write_text(
        "# Pre-Execution Audit\n\n"
        "## Self-Assessment\n"
        "All prerequisites verified. Plan ingested. Deviations register created.\n\n"
        "## Auditor Verdict\n"
        "CLEAR -- No remediation orders.\n"
    )

    # Git init on feature branch (required by token estimation check)
    _sp.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    _sp.run(
        ["git", "checkout", "-b", "feature-test"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    _sp.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True, check=True)
    _sp.run(
        ["git", "commit", "-m", "initial"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@test.com",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@test.com",
        },
    )

    # Task reports, checkpoints, and partner reviews for completed tasks
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for i in range(completed_tasks):
        padded = f"{i:03d}"

        # Implementer report with full YAML frontmatter + 5 prose sections
        (reports_dir / f"task-{padded}-implementer-report.md").write_text(
            f"---\nschema_version: 1\ntask_id: {i}\nstatus: DONE\n"
            f"files_changed:\n  - path: src/m.py\n    description: modified\n"
            f"tests:\n  written: 1\n  passing: 1\n  command: pytest\n  result: PASS\n---\n\n"
            f"**Implementation Summary:**\nDone.\n\n"
            f"**Source Files Read:**\n- plan.md\n\n"
            f"**Deviations from Plan:**\nNone\n\n"
            f"**Self-Review Findings:**\nNone\n\n"
            f"**Concerns:**\nNone\n"
        )

        # Spec and quality reviews
        (reports_dir / f"task-{padded}-spec-review.md").write_text(
            f"# Spec Review {padded}\n# Verdict: PASS\nImplementation matches plan.\n"
        )
        (reports_dir / f"task-{padded}-quality-review.md").write_text(
            f"# Quality Review {padded}\n# Verdict: PASS\nCode quality acceptable.\n"
        )

        # Dispatch log
        log_path = reports_dir / ".dispatch-log"
        with open(str(log_path), "a") as lf:
            lf.write(f"{now} DISPATCH reviewer task={i} type=spec-review\n")
            lf.write(f"{now} DISPATCH reviewer task={i} type=quality-review\n")

        # Checkpoint for task i
        _write_feature_checkpoint(reports_dir, i)

        # Partner review (Task 0 is exempt)
        if i > 0:
            (reports_dir / f"partner-review-{padded}.md").write_text(
                f"# Partner Review Task {padded}\n**Status:** APPROVED\n" + "x" * 60
            )
            with open(str(log_path), "a") as lf:
                lf.write(f"{now} DISPATCH reviewer task={i} type=partner-review\n")

    # Checkpoint and partner review for the next task to be dispatched
    if completed_tasks < total_tasks:
        _write_feature_checkpoint(reports_dir, completed_tasks)
        if completed_tasks > 0:
            padded = f"{completed_tasks:03d}"
            (reports_dir / f"partner-review-{padded}.md").write_text(
                f"# Partner Review Task {padded}\n**Status:** APPROVED\n" + "x" * 60
            )
            log_path = reports_dir / ".dispatch-log"
            with open(str(log_path), "a") as lf:
                lf.write(
                    f"{now} DISPATCH reviewer task={completed_tasks} type=partner-review\n"
                )


def _write_feature_checkpoint(reports_dir: object, task_number: int) -> None:
    """Write a pre-dispatch checkpoint JSON file inside a feature-dir reports/ folder."""
    padded = f"{task_number:03d}"
    checkpoint_path = reports_dir / f"checkpoint-pre-dispatch-{padded}.json"
    checkpoint_path.write_text(
        '{"status": "PASS", "phase": "pre-dispatch", '
        f'"task": {task_number}, "detail": "checkpoint for pre-dispatch verification"}}'
    )


# ─── Feature-dir layout tests ─────────────────────────────────────────────────


class TestFeatureDirLayout:
    """Tests verifying the hook correctly finds artifacts in per-feature directories."""

    def test_allows_dispatch_with_feature_dir_layout(self, feature_dir_workspace):
        """Hook allows dispatch when artifacts are in feature-dir and .active-feature is set."""
        tmp_path, feat_path, feat_dir, reports_dir = feature_dir_workspace
        tmpdir = str(tmp_path)
        _setup_feature_dir_sdd_workspace(
            tmp_path,
            feat_path,
            feat_dir,
            reports_dir,
            total_tasks=3,
            completed_tasks=1,
        )

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Should allow dispatch with feature-dir layout. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_blocks_without_pre_execution_audit_in_feature_dir(
        self, feature_dir_workspace
    ):
        """Hook blocks when pre-execution-audit.md is missing from feature-dir reports/."""
        tmp_path, feat_path, feat_dir, reports_dir = feature_dir_workspace
        tmpdir = str(tmp_path)
        _setup_feature_dir_sdd_workspace(
            tmp_path,
            feat_path,
            feat_dir,
            reports_dir,
            total_tasks=3,
            completed_tasks=1,
        )

        # Remove the pre-execution audit
        audit_path = reports_dir / "pre-execution-audit.md"
        audit_path.unlink()

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 2, (
            f"Should block when pre-execution-audit.md missing from feature-dir. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
        assert (
            "audit" in result.stderr.lower() or "pre-execution" in result.stderr.lower()
        ), f"Error should mention audit. stderr: {result.stderr}"

    def test_blocks_without_deviations_in_feature_dir(self, feature_dir_workspace):
        """Hook blocks when deviations.md is missing from feature-dir."""
        tmp_path, feat_path, feat_dir, reports_dir = feature_dir_workspace
        tmpdir = str(tmp_path)
        _setup_feature_dir_sdd_workspace(
            tmp_path,
            feat_path,
            feat_dir,
            reports_dir,
            total_tasks=3,
            completed_tasks=1,
        )

        # Remove deviations.md from feature dir
        deviations_path = feat_dir / "deviations.md"
        deviations_path.unlink()

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 2, (
            f"Should block when deviations.md missing from feature-dir. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
        assert "deviation" in result.stderr.lower(), (
            f"Error should mention deviations. stderr: {result.stderr}"
        )

    def test_blocks_without_previous_task_reports_in_feature_dir(
        self, feature_dir_workspace
    ):
        """Hook blocks when task 0 reports are missing from feature-dir reports/."""
        tmp_path, feat_path, feat_dir, reports_dir = feature_dir_workspace
        tmpdir = str(tmp_path)
        _setup_feature_dir_sdd_workspace(
            tmp_path,
            feat_path,
            feat_dir,
            reports_dir,
            total_tasks=3,
            completed_tasks=1,
        )

        # Remove task 0's implementer report to trigger the "previous task report" gate
        (reports_dir / "task-000-implementer-report.md").unlink()

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 2, (
            f"Should block when previous task reports missing in feature-dir. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_blocks_without_checkpoint_in_feature_dir(self, feature_dir_workspace):
        """Hook blocks when checkpoint file is missing from feature-dir reports/."""
        tmp_path, feat_path, feat_dir, reports_dir = feature_dir_workspace
        tmpdir = str(tmp_path)
        _setup_feature_dir_sdd_workspace(
            tmp_path,
            feat_path,
            feat_dir,
            reports_dir,
            total_tasks=3,
            completed_tasks=1,
        )

        # Remove the checkpoint for task 1
        checkpoint_path = reports_dir / "checkpoint-pre-dispatch-001.json"
        assert checkpoint_path.exists(), "Precondition: checkpoint exists from setup"
        checkpoint_path.unlink()

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 2, (
            f"Should block when checkpoint missing in feature-dir. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
        assert "checkpoint" in result.stderr.lower(), (
            f"Error should mention checkpoint. stderr: {result.stderr}"
        )

    def test_blocks_without_partner_review_in_feature_dir(self, feature_dir_workspace):
        """Hook blocks when partner review is missing from feature-dir reports/ (Task 1+)."""
        tmp_path, feat_path, feat_dir, reports_dir = feature_dir_workspace
        tmpdir = str(tmp_path)
        _setup_feature_dir_sdd_workspace(
            tmp_path,
            feat_path,
            feat_dir,
            reports_dir,
            total_tasks=3,
            completed_tasks=1,
        )

        # Remove the partner review for task 1
        partner_path = reports_dir / "partner-review-001.md"
        assert partner_path.exists(), "Precondition: partner review exists from setup"
        partner_path.unlink()

        hook_input = make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1",
            cwd=tmpdir,
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 2, (
            f"Should block when partner review missing in feature-dir. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
        assert "partner" in result.stderr.lower(), (
            f"Error should mention partner review. stderr: {result.stderr}"
        )


# ─── Plan-validation-gate tests ───────────────────────────────────────────────


class TestPlanValidationGate:
    """Tests for plan-validation-gate-hook.sh .active-feature enforcement."""

    def test_plan_validation_gate_blocks_without_active_feature(self, tmp_path):
        """plan-validation-gate should block SDD invocation when no .active-feature exists."""
        hook_input = json.dumps(
            {
                "tool_input": {"skill": "superpowers:subagent-driven-development"},
                "cwd": str(tmp_path),
            }
        )
        result = subprocess.run(
            ["bash", PLAN_VALIDATION_GATE_PATH],
            input=hook_input,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2, (
            f"Should block SDD invocation without .active-feature. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
        assert ".active-feature" in result.stderr, (
            f"Error should mention .active-feature. stderr: {result.stderr}"
        )


# ─── Backwards-compat fallback tests ─────────────────────────────────────────


class TestBackwardsCompatFallback:
    """Tests verifying that without .active-feature the hook falls back to root paths."""

    def test_pre_dispatch_falls_back_to_root_without_active_feature(self, tmp_path):
        """Without .active-feature, hook should check root-level reports/ and DEVIATIONS.md."""
        tmpdir = str(tmp_path)

        # Root-level layout (old style)
        (tmp_path / "reports").mkdir()
        (tmp_path / "DEVIATIONS.md").write_text("# Deviations")
        (tmp_path / "reports" / "pre-execution-audit.md").write_text("x" * 100)

        hook_input = make_hook_input(
            description="Implement task 0",
            prompt="you are implementing task 0",
            cwd=tmpdir,
        )
        result = subprocess.run(
            ["bash", SDD_PRE_DISPATCH_HOOK_PATH],
            input=hook_input,
            capture_output=True,
            text=True,
        )

        # Should not fail on "missing .active-feature" — falls back to root paths.
        # May fail on other checks (missing task reports, etc.) but not on path resolution.
        assert ".active-feature" not in result.stderr, (
            f"Hook should not complain about missing .active-feature on root layout. "
            f"stderr: {result.stderr}"
        )


# ─── Manifest-mode tests ──────────────────────────────────────────────────────


def _write_manifest_prereqs_for_task(
    feat_dir,
    reports_dir,
    task_number: int,
    include_partner: bool = True,
    include_dispatch_log: bool = True,
) -> None:
    """Write all prerequisites needed to dispatch task ``task_number`` in manifest mode.

    Creates:
    - Pre-execution audit (>50 bytes) in reports_dir/
    - Task (task_number - 1) reports: implementer, spec, quality
    - Dispatch log entries for task (task_number - 1) reviews (if include_dispatch_log)
    - Checkpoint for task_number
    - Partner review for task_number (if include_partner and task_number > 0)

    Designed for standard-tier manifests with task_number > MANIFEST_TASK_START.

    Args:
        feat_dir: pathlib.Path to the feature directory.
        reports_dir: pathlib.Path to the reports directory.
        task_number: The implementer task being dispatched.
        include_partner: Whether to write a partner review for task_number.
        include_dispatch_log: Whether to write dispatch log entries for reviews.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Pre-execution audit
    audit_path = reports_dir / "pre-execution-audit.md"
    audit_path.write_text(
        "# Pre-Execution Audit\n\n"
        "## Self-Assessment\n"
        "All prerequisites verified. Plan ingested. Deviations register created.\n\n"
        "## Auditor Verdict\n"
        "CLEAR -- No remediation orders.\n"
    )

    # Task N-1 reports (implementer, spec, quality)
    prev = task_number - 1
    padded_prev = f"{prev:03d}"

    (reports_dir / f"task-{padded_prev}-implementer-report.md").write_text(
        f"---\nschema_version: 1\ntask_id: {prev}\nstatus: DONE\n"
        f"files_changed:\n  - path: src/m.py\n    description: modified\n"
        f"tests:\n  written: 1\n  passing: 1\n  command: pytest\n  result: PASS\n---\n\n"
        f"**Implementation Summary:**\nDone.\n\n"
        f"**Source Files Read:**\n- plan.md\n\n"
        f"**Deviations from Plan:**\nNone\n\n"
        f"**Self-Review Findings:**\nNone\n\n"
        f"**Concerns:**\nNone\n"
    )
    (reports_dir / f"task-{padded_prev}-spec-review.md").write_text(
        f"# Spec Review {padded_prev}\n# Verdict: PASS\nImplementation matches plan.\n"
    )
    (reports_dir / f"task-{padded_prev}-quality-review.md").write_text(
        f"# Quality Review {padded_prev}\n# Verdict: PASS\nCode quality acceptable.\n"
    )

    # Dispatch log entries for task N-1 reviews
    log_path = reports_dir / ".dispatch-log"
    if include_dispatch_log:
        with open(str(log_path), "a") as lf:
            lf.write(f"{now} DISPATCH reviewer task={prev} type=spec-review\n")
            lf.write(f"{now} DISPATCH reviewer task={prev} type=quality-review\n")

    # Checkpoint for task_number
    padded = f"{task_number:03d}"
    checkpoint_path = reports_dir / f"checkpoint-pre-dispatch-{padded}.json"
    checkpoint_path.write_text(
        '{"status": "PASS", "phase": "pre-dispatch", '
        f'"task": {task_number}, "detail": "checkpoint for pre-dispatch verification"}}'
    )

    # Partner review for task_number
    if include_partner and task_number > 0:
        partner_path = reports_dir / f"partner-review-{padded}.md"
        partner_path.write_text(
            f"# Partner Review Task {padded}\n**Status:** APPROVED\n" + "x" * 60
        )
        with open(str(log_path), "a") as lf:
            lf.write(
                f"{now} DISPATCH reviewer task={task_number} type=partner-review\n"
            )


class TestManifestModeDispatchDetection:
    """Tests for manifest-mode hook behavior: tier gating, range validation, passthrough, injection."""

    def test_micro_tier_skips_partner_review_check(self, tmp_path):
        """Micro-tier manifest: dispatch task 1 with no partner review should return 0.

        Micro tier sets enforcement.partner_review=false so the partner review
        gate is skipped entirely. The test provides task 0 reports (Check 4 still
        runs for task N > MANIFEST_TASK_START) but omits the partner review.
        """
        ws = setup_manifest_workspace(
            tmp_path, tier="micro", task_range=(0, 1), total_tasks=2
        )
        # Provide task 0 reports and checkpoint for task 1.
        # No partner review, no dispatch log (dispatch_provenance=false in micro).
        # No pre-execution audit (pre_execution_audit=false in micro).
        reports_dir = ws["reports_dir"]
        prev = 0
        padded_prev = f"{prev:03d}"
        (reports_dir / f"task-{padded_prev}-implementer-report.md").write_text(
            "---\nschema_version: 1\ntask_id: 0\nstatus: DONE\n"
            "files_changed:\n  - path: src/m.py\n    description: modified\n"
            "tests:\n  written: 1\n  passing: 1\n  command: pytest\n  result: PASS\n---\n\n"
            "**Implementation Summary:**\nDone.\n\n"
            "**Source Files Read:**\n- plan.md\n\n"
            "**Deviations from Plan:**\nNone\n\n"
            "**Self-Review Findings:**\nNone\n\n"
            "**Concerns:**\nNone\n"
        )
        (reports_dir / f"task-{padded_prev}-spec-review.md").write_text(
            "# Spec Review 000\n# Verdict: PASS\nImplementation matches plan.\n"
        )
        (reports_dir / f"task-{padded_prev}-quality-review.md").write_text(
            "# Quality Review 000\n# Verdict: PASS\nCode quality acceptable.\n"
        )
        (reports_dir / "checkpoint-pre-dispatch-001.json").write_text(
            '{"status": "PASS", "phase": "pre-dispatch", "task": 1, "detail": "checkpoint"}'
        )

        hook_input = make_hook_input(
            description="Implement task 1",
            cwd=str(tmp_path),
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Micro tier should not block on missing partner review. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_standard_tier_blocks_without_partner_review(self, tmp_path):
        """Standard-tier manifest: dispatch task 1 without partner review should return 2.

        Standard tier sets enforcement.partner_review=true so the partner review
        gate fires. The test provides all other prerequisites but omits the partner
        review file and dispatch log entry.
        """
        ws = setup_manifest_workspace(
            tmp_path, tier="standard", task_range=(0, 7), total_tasks=8
        )
        _write_manifest_prereqs_for_task(
            ws["feat_dir"],
            ws["reports_dir"],
            task_number=1,
            include_partner=False,
        )

        hook_input = make_hook_input(
            description="Implement task 1",
            cwd=str(tmp_path),
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 2, (
            f"Standard tier should block when partner review is missing. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
        assert "partner" in result.stderr.lower(), (
            f"Error should mention partner review. stderr: {result.stderr}"
        )

    def test_task_outside_range_blocked(self, tmp_path):
        """Manifest task_range=(0,3): dispatch task 99 should be blocked with task_range in stderr."""
        ws = setup_manifest_workspace(
            tmp_path, tier="standard", task_range=(0, 3), total_tasks=4
        )

        hook_input = make_hook_input(
            description="Implement task 99",
            cwd=str(tmp_path),
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 2, (
            f"Should block when task is outside manifest task_range. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
        assert "task_range" in result.stderr, (
            f"Error should mention task_range. stderr: {result.stderr}"
        )

    def test_explore_agent_passes_through(self, tmp_path):
        """Manifest mode: Explore subagent_type should pass through immediately (exit 0)."""
        _ws = setup_manifest_workspace(tmp_path)

        hook_input = make_hook_input(
            description="Search for relevant files",
            prompt="",
            cwd=str(tmp_path),
            subagent_type="Explore",
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Explore agent should pass through in manifest mode. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_process_requirements_injected(self, tmp_path):
        """Standard-tier manifest: on allowed dispatch, additionalContext contains SESSION CONTRACT."""
        ws = setup_manifest_workspace(
            tmp_path, tier="standard", task_range=(0, 7), total_tasks=8
        )
        _write_manifest_prereqs_for_task(
            ws["feat_dir"],
            ws["reports_dir"],
            task_number=1,
            include_partner=True,
            include_dispatch_log=True,
        )

        hook_input = make_hook_input(
            description="Implement task 1",
            cwd=str(tmp_path),
        )
        result = run_hook(HOOK_PATH, hook_input)

        assert result.returncode == 0, (
            f"Should allow dispatch when all prerequisites are satisfied. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )
        output = json.loads(result.stdout)
        additional_context = output.get("hookSpecificOutput", {}).get(
            "additionalContext", ""
        )
        assert "SESSION CONTRACT" in additional_context, (
            f"additionalContext should contain SESSION CONTRACT. "
            f"additionalContext: {additional_context!r}"
        )

    def test_unparseable_reviewer_skips_sentinel_write(self, tmp_path):
        """Reviewer dispatch with no task number: sentinel NOT written (REVIEW_TASK is empty).

        The hook's sentinel write is inside ``if [ -n "$REVIEW_TASK" ]``.
        When REVIEW_TASK is empty (unparseable reviewer description), the log
        entry is skipped and the sentinel is never written.  The subsequent
        implementer dispatch then emits a WARNING about the missing sentinel.

        This covers the carry-forward concern from the Task 9 quality reviewer.
        """
        ws = setup_manifest_workspace(
            tmp_path, tier="standard", task_range=(0, 7), total_tasks=8
        )
        reports_dir = ws["reports_dir"]
        log_path = reports_dir / ".dispatch-log"

        # Pre-create the dispatch log with NO sentinel (simulates unparseable reviewer dispatch)
        # Write a log entry that lacks a task number so the hook's reviewer branch
        # produced no REVIEW_TASK and therefore wrote no sentinel.
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_path.write_text(f"{now} DISPATCH reviewer task= type=unknown\n")
        # No "# sdd-hook-sentinel" line — sentinel was skipped

        # Now dispatch an implementer — the hook should WARN about missing sentinel
        hook_input = make_hook_input(
            description="Implement task 0",
            cwd=str(tmp_path),
        )
        result = run_hook(HOOK_PATH, hook_input)

        # The hook WARNs (stderr) about the missing sentinel but does not block
        assert "warn" in result.stderr.lower() or "sentinel" in result.stderr.lower(), (
            f"Should emit WARN about missing dispatch log sentinel. "
            f"stderr: {result.stderr!r}"
        )
