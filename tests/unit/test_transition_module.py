"""Tests for transition-module.py."""

import json
import os
import subprocess
import sys


SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "skills",
    "subagent-driven-development",
    "scripts",
    "transition-module.py",
)

PYTHON = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    ".venv",
    "bin",
    "python3",
)

# Import helpers
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "skills", "scripts", "models"),
)
from sdd_session import TIER_PROFILES


def create_manifest(tmp_path, tier="standard"):
    # transition-module.py runs `git rev-parse --show-toplevel` from the
    # manifest's parent directory; without a real git repo it exits 2.
    # See deviations.md (Task 13) for the empirical diagnosis.
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)

    feat_dir = tmp_path / "docs" / "imp-plans" / "test-feature"
    feat_dir.mkdir(parents=True)
    reports_dir = feat_dir / "reports"
    reports_dir.mkdir()
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
        "active_module_id": 1,
        "active_module_file": "m1.md",
        "task_range": [0, 3],
        "total_tasks": 8,
        "midpoint": 2,
        "enforcement": {**profile["enforcement"], "context_summary_at": 2},
        "process_requirements": profile["process_requirements"],
        "completed_modules": [],
        "module_reports_archived": False,
        "modules": [
            {"id": 1, "title": "Core", "file": "m1.md", "task_ids": [0, 1, 2, 3]},
            {"id": 2, "title": "API", "file": "m2.md", "task_ids": [4, 5, 6, 7]},
        ],
        "dispatch_log_sentinel": False,
    }

    manifest_path = feat_dir / ".sdd-session.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Create dispatch log
    (reports_dir / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")

    return manifest_path, reports_dir, feat_dir


def create_task_reports(reports_dir, task_ids):
    """Create implementer, spec-review, quality-review reports AND dispatch-log
    provenance for each task (N3b requires provenance at transition time)."""
    log = reports_dir / ".dispatch-log"
    for tid in task_ids:
        padded = f"{tid:03d}"
        for report_type in ["implementer-report", "spec-review", "quality-review"]:
            (reports_dir / f"task-{padded}-{report_type}.md").write_text(
                f"# {report_type} for task {tid}\n" + "x" * 100)
        with open(log, "a") as f:
            f.write(f"2026-06-01T00:00:00Z DISPATCH reviewer task={tid} type=spec-review\n")
            f.write(f"2026-06-01T00:00:00Z DISPATCH reviewer task={tid} type=quality-review\n")


def run_transition(manifest_path, completed, next_mod):
    result = subprocess.run(
        [
            PYTHON,
            SCRIPT_PATH,
            "--manifest",
            str(manifest_path),
            "--completed-module",
            completed,
            "--next-module",
            next_mod,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result


class TestTransitionModule:
    def test_successful_transition(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        result = run_transition(manifest_path, "Core", "API")
        assert result.returncode == 0
        assert "Transition complete" in result.stdout

    def test_manifest_updated_after_transition(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        run_transition(manifest_path, "Core", "API")
        updated = json.loads(manifest_path.read_text())
        assert updated["active_module_id"] == 2
        assert updated["task_range"] == [4, 7]
        assert "Core" in updated["completed_modules"]
        assert updated["enforcement"]["context_summary_at"] == 6

    def test_reports_archived(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        run_transition(manifest_path, "Core", "API")
        archive = reports_dir / "archive-Core"
        assert archive.is_dir()
        assert (archive / "task-000-implementer-report.md").is_file()

    def test_dispatch_log_archived_and_truncated(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        run_transition(manifest_path, "Core", "API")
        archive = reports_dir / "archive-Core"
        assert (archive / ".dispatch-log").is_file()
        assert (reports_dir / ".dispatch-log").read_text() == ""

    def test_blocks_when_reports_missing(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        # Don't create reports
        result = run_transition(manifest_path, "Core", "API")
        assert result.returncode == 1
        assert "INCOMPLETE" in result.stderr

    def test_rejects_single_module_plan(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        # Remove modules from manifest
        data = json.loads(manifest_path.read_text())
        data["modules"] = None
        manifest_path.write_text(json.dumps(data))
        result = run_transition(manifest_path, "Core", "API")
        assert result.returncode == 1

    def test_deviations_log_updated(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        run_transition(manifest_path, "Core", "API")
        devs = (feat_dir / "deviations.md").read_text()
        assert "Module transition" in devs


def test_blocks_when_provenance_missing(tmp_path):
    manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
    # Reports present but NO provenance lines (log only has the sentinel).
    for tid in [0, 1, 2, 3]:
        padded = f"{tid:03d}"
        for rt in ["implementer-report", "spec-review", "quality-review"]:
            (reports_dir / f"task-{padded}-{rt}.md").write_text(f"# {rt}\n" + "x" * 100)
    result = run_transition(manifest_path, "Core", "API")
    assert result.returncode == 1
    # Assert BOTH review types are caught — isolates the quality-provenance branch
    # so deleting it does not silently pass on the spec-review error alone.
    assert "spec review not provenance-logged" in result.stderr
    assert "quality review not provenance-logged" in result.stderr


def test_minimum_tier_file_waives_quality_provenance(tmp_path):
    manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
    log = reports_dir / ".dispatch-log"
    for tid in [0, 1, 2, 3]:
        padded = f"{tid:03d}"
        (reports_dir / f"task-{padded}-implementer-report.md").write_text("# impl\n" + "x" * 100)
        (reports_dir / f"task-{padded}-spec-review.md").write_text("# spec\n" + "x" * 100)
        # Quality via the FILE signal (minimum-tier), NOT a full quality review.
        (reports_dir / f"task-{padded}-quality-review-minimum-tier.md").write_text("# min\n" + "x" * 100)
        with open(log, "a") as f:
            f.write(f"2026-06-01T00:00:00Z DISPATCH reviewer task={tid} type=spec-review\n")
            # NO quality-review provenance line — the file signal must waive it.
    result = run_transition(manifest_path, "Core", "API")
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_verification_task_exempt_from_reviews(tmp_path):
    manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
    # Declare task 3 as verification in the completing module's plan file.
    (feat_dir / "m1.md").write_text(
        "---\nschema_version: 1\ntasks:\n"
        "  - id: 0\n  - id: 1\n  - id: 2\n  - id: 3\n    task_type: verification\n---\n# M1\n")
    # Tasks 0-2 full (reports + provenance); task 3 implementer report ONLY.
    create_task_reports(reports_dir, [0, 1, 2])
    (reports_dir / "task-003-implementer-report.md").write_text("# impl\n" + "x" * 100)
    result = run_transition(manifest_path, "Core", "API")
    assert result.returncode == 0, f"stderr={result.stderr}"
