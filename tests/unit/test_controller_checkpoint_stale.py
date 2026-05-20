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


# ---------------------------------------------------------------------------
# Manifest-mode tests (Task 15 — Module 3)
# ---------------------------------------------------------------------------

CHECKPOINT_SCRIPT = SCRIPT_PATH
PYTHON = os.path.join(
    os.path.dirname(__file__), "..", "..", ".venv", "bin", "python3"
)

# Import TIER_PROFILES — conftest.py already adds skills/scripts/models to sys.path,
# but add it explicitly for clarity (matches test_transition_module.py pattern).
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "skills", "scripts", "models"),
)
from sdd_session import TIER_PROFILES  # noqa: E402


def setup_checkpoint_workspace(tmp_path, tier="standard"):
    """Create a workspace with manifest, plan, deviations, and reports for checkpoint testing.

    Initializes a git repo at ``tmp_path`` so controller-checkpoint.py's
    ``git -C <manifest_parent> rev-parse --show-toplevel`` resolves to ``tmp_path``
    rather than the brittle ``parent.parent.parent`` fallback (which lands one
    directory short and double-nests ``docs/`` when joining git-root-relative
    manifest paths). Pattern matches ``create_manifest`` in
    ``test_transition_module.py`` (Task 13 fixture, deviations row 13).
    """
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)

    feat_dir = tmp_path / "docs" / "imp-plans" / "test-feature"
    feat_dir.mkdir(parents=True)
    reports_dir = feat_dir / "reports"
    reports_dir.mkdir()

    plan_content = "# Plan\n\n### Task 0: Setup\n- [x] Done\n\n### Task 1: Build\n- [x] Done\n"
    (feat_dir / "plan.md").write_text(plan_content)
    (feat_dir / "deviations.md").write_text("# Deviations\n")

    profile = TIER_PROFILES[tier]
    manifest = {
        "schema_version": 1,
        "tier": tier,
        "paths": {
            "feature_dir": str(feat_dir.relative_to(tmp_path)),
            "reports_dir": str(reports_dir.relative_to(tmp_path)),
            "dispatch_log": str((reports_dir / ".dispatch-log").relative_to(tmp_path)),
            "deviations_file": str((feat_dir / "deviations.md").relative_to(tmp_path)),
        },
        "plan_file": str((feat_dir / "plan.md").relative_to(tmp_path)),
        "active_module_id": None,
        "active_module_file": None,
        "task_range": [0, 1],
        "total_tasks": 2,
        "midpoint": 1,
        "enforcement": profile["enforcement"],
        "process_requirements": profile["process_requirements"],
        "completed_modules": [],
        "module_reports_archived": False,
        "modules": None,
        "dispatch_log_sentinel": False,
    }
    manifest_path = feat_dir / ".sdd-session.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return {"manifest_path": manifest_path, "feat_dir": feat_dir, "reports_dir": reports_dir}


def run_checkpoint_cli(phase, manifest_path=None, plan_file=None, task_number=None,
                       deviations_file=None, reports_dir=None):
    """Invoke controller-checkpoint.py with the given arguments and return parsed output."""
    cmd = [PYTHON, CHECKPOINT_SCRIPT, "--phase", phase]
    if manifest_path:
        cmd.extend(["--manifest", str(manifest_path)])
    if plan_file:
        cmd.extend(["--plan-file", str(plan_file)])
    if task_number is not None:
        cmd.extend(["--task-number", str(task_number)])
    if deviations_file:
        cmd.extend(["--deviations-file", str(deviations_file)])
    if reports_dir:
        cmd.extend(["--reports-dir", str(reports_dir)])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    output = json.loads(result.stdout) if result.stdout.strip() else {}
    return {"exit_code": result.returncode, "output": output, "stderr": result.stderr}


class TestManifestMode:
    """Tests for --manifest argument on controller-checkpoint.py (Task 14)."""

    def test_manifest_overrides_plan_file(self, tmp_path):
        """When --manifest is provided, plan_file is resolved from the manifest."""
        ws = setup_checkpoint_workspace(tmp_path)
        result = run_checkpoint_cli(
            "pre-execution",
            manifest_path=ws["manifest_path"],
            deviations_file=str(ws["feat_dir"] / "deviations.md"),
            reports_dir=str(ws["reports_dir"]),
        )
        # Exit code 3 = script error (manifest parse / plan-file resolution failure).
        # Any other exit code (0/1/2) means the script successfully read the plan
        # via the manifest and produced JSON output.
        assert result["exit_code"] != 3, f"Script error: {result['stderr']}"

    def test_micro_tier_skips_honesty_check(self, tmp_path):
        """Pre-completion with micro tier should SKIP honesty check (and trace audit).

        Task 14 sets ``checks["honesty_check_missing"]`` (not ``honesty_check``)
        and ``checks["trace_audit_missing"]`` to ``{"status": "SKIP", ...}`` when
        ``tier == "micro"``. Plan reference test code used the wrong key
        (``honesty_check``); deviations row 29 (ForwardConcern from Task 14)
        flagged this for Task 15 to reconcile.
        """
        ws = setup_checkpoint_workspace(tmp_path, tier="micro")
        result = run_checkpoint_cli(
            "pre-completion",
            manifest_path=ws["manifest_path"],
            deviations_file=str(ws["feat_dir"] / "deviations.md"),
            reports_dir=str(ws["reports_dir"]),
        )
        checks = result["output"].get("checks", {})
        honesty = checks.get("honesty_check_missing", {})
        assert honesty.get("status") == "SKIP", f"Expected SKIP, got {honesty}"

    def test_backward_compat_without_manifest(self, tmp_path):
        """When --manifest is absent, --plan-file works as before."""
        ws = setup_checkpoint_workspace(tmp_path)
        result = run_checkpoint_cli(
            "pre-execution",
            plan_file=str(ws["feat_dir"] / "plan.md"),
            deviations_file=str(ws["feat_dir"] / "deviations.md"),
            reports_dir=str(ws["reports_dir"]),
        )
        assert result["exit_code"] != 3, f"Script error: {result['stderr']}"
