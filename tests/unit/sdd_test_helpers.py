"""
Shared test helpers for SDD hook tests.

Provides workspace setup, report generation, and hook input construction
for testing sdd-pre-dispatch-hook.sh and sdd-report-guard.sh.
"""

import importlib.util
import json
import os
import subprocess
from datetime import datetime, timezone

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_script(name, filename):
    """Load a hyphenated SDD script (validate-plan.py, controller-checkpoint.py)
    as an importable module. Single source of truth (D15) — previously
    duplicated in test_fence_aware_parsing.py and test_c2_integration_gate.py."""
    path = os.path.join(
        ROOT, "skills", "subagent-driven-development", "scripts", filename
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_hook_input(
    description: str,
    prompt: str = "",
    cwd: str = "",
    subagent_type: str = "",
) -> str:
    """JSON payload matching Claude Code PreToolUse hook input.

    Args:
        description: The tool_input.description field (dispatch description).
        prompt: The tool_input.prompt field (first 500 chars used by hook).
        cwd: Working directory for the hook. Empty string if not needed.
        subagent_type: Optional subagent_type for manifest-mode passthrough check.

    Returns:
        JSON string ready to pipe to the hook via stdin.
    """
    tool_input: dict = {
        "description": description,
        "prompt": prompt,
    }
    if subagent_type:
        tool_input["subagent_type"] = subagent_type
    payload = {
        "tool_input": tool_input,
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


IMPLEMENTER_REPORT_TEMPLATE = """\
---
schema_version: 1
task_id: {task_number}
status: DONE
files_changed:
  - path: "src/module.py"
    description: "modified"
  - path: "tests/test_module.py"
    description: "created"
tests:
  written: 2
  passing: 2
  command: "pytest tests/test_module.py -v"
  result: PASS
---

**Implementation Summary:**
Implemented the feature as specified in the plan. All requirements met.

**Source Files Read:**
- docs/imp-plans/plan.md
- src/existing_module.py

**Deviations from Plan:**
None — implemented exactly as specified

**Self-Review Findings:**
No issues found during self-review.

**Concerns:**
No concerns
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


def _write_manifest(root, feature_dir, reports_rel, deviations_rel, plan_rel,
                    task_count, tier="standard"):
    """Write .active-feature + .sdd-session.json for manifest-mode hook testing.

    Args:
        root: workspace root (str) — the git root / hook CWD.
        feature_dir: feature dir relative to root ('.' or 'docs/imp-plans/x').
        reports_rel, deviations_rel, plan_rel: git-root-relative paths.
        task_count: number of tasks (task_range = [0, task_count-1]).
        tier: 'standard' or 'micro'.
    The manifest is written at <root>/<feature_dir>/.sdd-session.json.
    """
    import sys as _sys
    from pathlib import Path as _Path
    _models = str(_Path(__file__).resolve().parent.parent.parent
                  / "skills" / "scripts" / "models")
    if _models not in _sys.path:
        _sys.path.insert(0, _models)
    from sdd_session import TIER_PROFILES  # noqa: PLC0415

    start, end = 0, max(task_count - 1, 0)
    range_size = end - start
    midpoint = start + (range_size + 1) // 2  # Module 1 deviation-row-1 formula

    profile = TIER_PROFILES[tier]
    enforcement = dict(profile["enforcement"])
    if tier == "standard" and enforcement.get("context_summary_at") is None:
        enforcement["context_summary_at"] = midpoint

    manifest = {
        "schema_version": 1,
        "tier": tier,
        "paths": {
            "feature_dir": feature_dir,
            "reports_dir": reports_rel,
            "dispatch_log": os.path.join(reports_rel, ".dispatch-log"),
            "deviations_file": deviations_rel,
        },
        "plan_file": plan_rel,
        "active_module_id": None,
        "active_module_file": None,
        "task_range": [start, end],
        "total_tasks": max(task_count, 1),
        "midpoint": midpoint,
        "enforcement": enforcement,
        "process_requirements": dict(profile["process_requirements"]),
        "completed_modules": [],
        "module_reports_archived": False,
        "modules": None,
        "dispatch_log_sentinel": False,
    }
    with open(os.path.join(root, ".active-feature"), "w") as f:
        f.write(feature_dir)
    manifest_dir = os.path.join(root, feature_dir) if feature_dir != "." else root
    os.makedirs(manifest_dir, exist_ok=True)
    with open(os.path.join(manifest_dir, ".sdd-session.json"), "w") as f:
        json.dump(manifest, f, indent=2)


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
        f.write(
            "# Deviations Register\n\n"
            "> Auto-maintained by controller during subagent-driven-development execution.\n\n"
            "| Task | Type | Description | Disposition |\n"
            "|------|------|-------------|-------------|\n"
        )

    # Create pre-execution audit (>50 bytes)
    audit_path = os.path.join(reports_dir, "pre-execution-audit.md")
    with open(audit_path, "w") as f:
        f.write(
            "# Pre-Execution Audit\n\n"
            "## Self-Assessment\n"
            "All prerequisites verified. Plan ingested. Deviations register created.\n\n"
            "## Auditor Verdict\n"
            "CLEAR -- No remediation orders.\n"
        )

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

    # Manifest-mode activation (root-level feature dir keeps reports/ at root)
    _write_manifest(
        tmpdir,
        feature_dir=".",
        reports_rel="reports",
        deviations_rel="DEVIATIONS.md",
        plan_rel=os.path.join("docs", "imp-plans", "plan.md"),
        task_count=task_count,
    )

    # Git init on feature branch
    subprocess.run(
        ["git", "init"],
        cwd=tmpdir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "feature-test"],
        cwd=tmpdir,
        capture_output=True,
        check=True,
    )
    # Initial commit so git is functional
    subprocess.run(
        ["git", "add", "."],
        cwd=tmpdir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmpdir,
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


def create_task_reports(
    tmpdir: str, task_number: int, include_dispatch_log: bool = True
) -> None:
    """Create implementer-report, spec-review, and quality-review for a task.

    All files use zero-padded 3-digit naming (task-NNN-*).
    Implementer report has YAML frontmatter + 5 prose sections and is >50 bytes.
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
        f.write(
            IMPLEMENTER_REPORT_TEMPLATE.format(
                task_number=task_number,
                title=f"Step {task_number}",
                date=now,
            )
        )

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
    checkpoint_path = os.path.join(
        reports_dir, f"checkpoint-pre-dispatch-{padded}.json"
    )
    with open(checkpoint_path, "w") as f:
        json.dump(
            {
                "status": "PASS",
                "phase": "pre-dispatch",
                "task": task_number,
                "detail": "checkpoint for pre-dispatch verification",
            },
            f,
        )


def setup_full_sdd_workspace(
    tmpdir: str, total_tasks: int, completed_tasks: int
) -> None:
    """Full workspace: plan, DEVIATIONS.md, audit, reports + dispatch log + checkpoint files for all completed tasks.

    Args:
        tmpdir: Path to temporary directory to set up.
        total_tasks: Total number of tasks in the plan.
        completed_tasks: Number of tasks already completed (0..N-1).
    """
    setup_sdd_workspace(tmpdir, total_tasks)

    reports_dir = os.path.join(tmpdir, "reports")
    log_path = os.path.join(reports_dir, ".dispatch-log")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for i in range(completed_tasks):
        create_task_reports(tmpdir, i, include_dispatch_log=True)
        # Create checkpoint for the NEXT task (which was checked before dispatching task i)
        # The checkpoint for task N is created before dispatching task N
        create_checkpoint_file(tmpdir, i)
        # Create partner review for task i (Task 0 is exempt — no prior context to verify)
        if i > 0:
            padded = f"{i:03d}"
            partner_path = os.path.join(reports_dir, f"partner-review-{padded}.md")
            with open(partner_path, "w") as f:
                f.write(
                    f"# Partner Review Task {padded}\n**Status:** APPROVED\n" + "x" * 60
                )
            with open(log_path, "a") as f:
                f.write(f"{now} DISPATCH reviewer task={i} type=partner-review\n")

    # Create checkpoint and partner review for the next task to be dispatched
    if completed_tasks < total_tasks:
        create_checkpoint_file(tmpdir, completed_tasks)
        if completed_tasks > 0:
            padded = f"{completed_tasks:03d}"
            partner_path = os.path.join(reports_dir, f"partner-review-{padded}.md")
            with open(partner_path, "w") as f:
                f.write(
                    f"# Partner Review Task {padded}\n**Status:** APPROVED\n" + "x" * 60
                )
            with open(log_path, "a") as f:
                f.write(
                    f"{now} DISPATCH reviewer task={completed_tasks} type=partner-review\n"
                )


def setup_manifest_workspace(
    tmp_path,
    tier: str = "standard",
    task_range: tuple = (0, 7),
    total_tasks: int = 8,
) -> dict:
    """Set up a git workspace with .sdd-session.json for manifest-mode hook testing.

    Initializes a git repo so that ``git rev-parse --show-toplevel`` works, which
    the pre-dispatch hook requires for manifest-based path resolution.

    The midpoint formula used here is the one adopted in Module 1 (deviation row 1):
        range_size = end - start        (NOT end - start + 1)
        midpoint   = start + (range_size + 1) // 2

    Args:
        tmp_path: A pathlib.Path pointing to a temporary directory (from pytest's
            ``tmp_path`` fixture or ``Path(tmpdir)``).
        tier: SDD enforcement tier — "micro" or "standard".
        task_range: Inclusive ``(start, end)`` tuple of task IDs in this module.
        total_tasks: Total number of tasks across all modules (used for the
            Pydantic ``SddSession.total_tasks`` field; must be >= range size).

    Returns:
        A dict with keys:
          ``root``          — pathlib.Path to the git root (tmp_path)
          ``feat_dir``      — pathlib.Path to the feature directory
          ``reports_dir``   — pathlib.Path to the reports directory
          ``manifest_path`` — pathlib.Path to .sdd-session.json
    """
    import sys
    from pathlib import Path

    # Ensure the models directory is on sys.path (same as conftest.py)
    _models_dir = str(
        Path(__file__).resolve().parent.parent.parent / "skills" / "scripts" / "models"
    )
    if _models_dir not in sys.path:
        sys.path.insert(0, _models_dir)

    from sdd_session import TIER_PROFILES  # noqa: PLC0415

    # ── Git repo setup ──────────────────────────────────────────────────────
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "checkout", "-b", "test-feature"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )

    # ── Feature directory layout ────────────────────────────────────────────
    feat_dir = tmp_path / "docs" / "imp-plans" / "test-feature"
    feat_dir.mkdir(parents=True)
    reports_dir = feat_dir / "reports"
    reports_dir.mkdir()

    # .active-feature — relative path, no trailing slash
    feat_rel = str(feat_dir.relative_to(tmp_path))
    (tmp_path / ".active-feature").write_text(feat_rel)

    # ── Midpoint formula (Module 1 deviation row 1: range_size = end - start) ──
    start, end = task_range
    range_size = end - start  # NOT end - start + 1
    midpoint = start + (range_size + 1) // 2

    # ── Manifest JSON ───────────────────────────────────────────────────────
    profile = TIER_PROFILES[tier]
    enforcement = dict(profile["enforcement"])
    # Standard tier leaves context_summary_at as None; fill with computed midpoint.
    if tier == "standard" and enforcement.get("context_summary_at") is None:
        enforcement["context_summary_at"] = midpoint

    manifest: dict = {
        "schema_version": 1,
        "tier": tier,
        "paths": {
            "feature_dir": str(feat_rel),
            "reports_dir": str(feat_dir.relative_to(tmp_path) / "reports"),
            "dispatch_log": str(
                feat_dir.relative_to(tmp_path) / "reports" / ".dispatch-log"
            ),
            "deviations_file": str(feat_dir.relative_to(tmp_path) / "deviations.md"),
        },
        "plan_file": str(feat_dir.relative_to(tmp_path) / "plan.md"),
        "active_module_id": None,
        "active_module_file": None,
        "task_range": list(task_range),
        "total_tasks": total_tasks,
        "midpoint": midpoint,
        "enforcement": enforcement,
        "process_requirements": dict(profile["process_requirements"]),
        "completed_modules": [],
        "module_reports_archived": False,
        "modules": None,
        "dispatch_log_sentinel": False,
    }

    (feat_dir / ".sdd-session.json").write_text(json.dumps(manifest, indent=2))

    # Stub supporting files
    (feat_dir / "deviations.md").write_text(
        "# Deviations\n\n"
        "| Task | Category | Description | Disposition |\n"
        "|------|----------|-------------|-------------|\n"
    )
    # Plan with task headers for all tasks in range (supports token estimation check)
    plan_lines = ["# Implementation Plan\n\n**Source Contracts:** None\n\n"]
    for i in range(start, end + 1):
        plan_lines.append(f"### Task {i} -- Step {i}\n- [ ] Do step {i}\n\n")
    (feat_dir / "plan.md").write_text("".join(plan_lines))

    return {
        "root": tmp_path,
        "feat_dir": feat_dir,
        "reports_dir": reports_dir,
        "manifest_path": feat_dir / ".sdd-session.json",
    }
