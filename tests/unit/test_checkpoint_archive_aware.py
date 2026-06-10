"""N4: controller-checkpoint.py find_report_file/find_all_report_files recurse into archive-*/.
N18: run_pre_dispatch module-boundary skip-guard (mirror of the hook's N3a).
Run: .venv/bin/python3 -m pytest tests/unit/test_checkpoint_archive_aware.py -v
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys

_SPEC = importlib.util.spec_from_file_location(
    "controller_checkpoint",
    os.path.join(os.path.dirname(__file__), "..", "..",
                 "skills", "subagent-driven-development", "scripts", "controller-checkpoint.py"),
)
cc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cc)

_MODELS = os.path.join(os.path.dirname(__file__), "..", "..",
                       "skills", "scripts", "models")
if _MODELS not in sys.path:
    sys.path.insert(0, _MODELS)
from sdd_session import TIER_PROFILES  # noqa: E402


def _impl(p):
    p.write_text("x" * 80)


def test_find_report_file_in_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    assert cc.find_report_file(str(reports), 0).endswith("archive-Core/task-000-implementer-report.md")


def test_find_report_file_prefers_live_over_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    _impl(reports / "task-000-implementer-report.md")
    # Live copy must win (sorts last).
    assert cc.find_report_file(str(reports), 0) == str(reports / "task-000-implementer-report.md")


def test_find_all_report_files_includes_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    _impl(reports / "task-002-implementer-report.md")
    found = cc.find_all_report_files(str(reports))
    bases = sorted(os.path.basename(f) for f in found)
    assert bases == ["task-000-implementer-report.md", "task-002-implementer-report.md"]


def test_detect_stale_artifacts_stays_flat(tmp_path):
    # Regression: archived reports must NOT trip the pre-execution stale scan.
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    dev = tmp_path / "deviations.md"; dev.write_text("")  # empty = no content
    result = cc.detect_stale_artifacts(str(dev), str(reports))
    assert result["status"] == "OK", result


# --- N18: pre-dispatch module-boundary skip-guard ---

# Self-hosting guard: never embed a literal task header at column 0 in fixtures.
_H = "##" + "# Task"

_PREV_TASK_CHECKS = (
    "previous_task_checkboxes",
    "previous_task_report",
    "previous_report_complete",
    "previous_spec_review",
    "previous_quality_review",
)


def _plan_for_tasks(task_ids):
    parts = ["# Plan\n"]
    for t in task_ids:
        parts.append("{} {}: Work item {}\n\n- [x] Done\n".format(_H, t, t))
    return "\n".join(parts)


def _pre_dispatch_workspace(tmp_path, task_range, plan_task_ids):
    """Git repo + manifest + plan + deviations + reports mirroring the live layout."""
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    feat_dir = tmp_path / "docs" / "imp-plans" / "test-feature"
    feat_dir.mkdir(parents=True)
    reports_dir = feat_dir / "reports"
    reports_dir.mkdir()
    (feat_dir / "plan.md").write_text(_plan_for_tasks(plan_task_ids))
    (feat_dir / "deviations.md").write_text("# Deviations\n")

    start, end = task_range
    midpoint = start + (end - start + 1) // 2
    profile = TIER_PROFILES["standard"]
    enforcement = dict(profile["enforcement"])
    if enforcement.get("context_summary_at") is None:
        enforcement["context_summary_at"] = midpoint
    manifest = {
        "schema_version": 1,
        "tier": "standard",
        "paths": {
            "feature_dir": str(feat_dir.relative_to(tmp_path)),
            "reports_dir": str(reports_dir.relative_to(tmp_path)),
            "dispatch_log": str((reports_dir / ".dispatch-log").relative_to(tmp_path)),
            "deviations_file": str((feat_dir / "deviations.md").relative_to(tmp_path)),
        },
        "plan_file": str((feat_dir / "plan.md").relative_to(tmp_path)),
        "active_module_id": None,
        "active_module_file": None,
        "task_range": list(task_range),
        "total_tasks": end - start + 1,
        "midpoint": midpoint,
        "enforcement": enforcement,
        "process_requirements": profile["process_requirements"],
        "completed_modules": [],
        "module_reports_archived": False,
        "modules": None,
        "dispatch_log_sentinel": False,
    }
    manifest_path = feat_dir / ".sdd-session.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return {"manifest_path": manifest_path, "feat_dir": feat_dir, "reports_dir": reports_dir}


def _run_pre_dispatch(ws, task_number, manifest=True):
    args = argparse.Namespace(
        manifest=str(ws["manifest_path"]) if manifest else None,
        plan_file=str(ws["feat_dir"] / "plan.md"),
        task_number=task_number,
        deviations_file=str(ws["feat_dir"] / "deviations.md"),
        reports_dir=str(ws["reports_dir"]),
    )
    return cc.run_pre_dispatch(args)


def test_boundary_task_skips_previous_task_checks(tmp_path):
    """First task of module 2 (range [8,11]): task-007 artifacts live only under
    archive-*/ — previous-task checks must SKIP, not block (live bug 2026-06-10)."""
    ws = _pre_dispatch_workspace(tmp_path, (8, 11), plan_task_ids=range(8, 12))
    arch = ws["reports_dir"] / "archive-Cleanup"; arch.mkdir()
    _impl(arch / "task-007-implementer-report.md")
    _impl(arch / "task-007-spec-review.md")
    _impl(arch / "task-007-quality-review.md")

    result = _run_pre_dispatch(ws, 8)
    assert result["status"] == "PASS", result
    assert result["blockers"] == [], result
    for name in _PREV_TASK_CHECKS:
        assert result["checks"][name]["status"] == "SKIP", (name, result["checks"][name])
        assert "prior module" in result["checks"][name]["detail"], result["checks"][name]


def test_non_boundary_task_still_blocks_on_missing_reports(tmp_path):
    """Task 9 within range [8,11]: missing task-008 reports must still block."""
    ws = _pre_dispatch_workspace(tmp_path, (8, 11), plan_task_ids=range(8, 12))
    result = _run_pre_dispatch(ws, 9)
    assert result["status"] == "FAIL", result
    for blocker in ("previous_task_report", "previous_spec_review", "previous_quality_review"):
        assert blocker in result["blockers"], result["blockers"]


def test_first_module_task_still_blocks(tmp_path):
    """Range [1,7], task 2: previous_task 1 >= task_range[0] — guard must not fire."""
    ws = _pre_dispatch_workspace(tmp_path, (1, 7), plan_task_ids=range(1, 8))
    result = _run_pre_dispatch(ws, 2)
    assert result["status"] == "FAIL", result
    assert "previous_task_report" in result["blockers"], result["blockers"]


def test_legacy_no_manifest_unchanged(tmp_path):
    """Without --manifest, previous-task checks behave exactly as before."""
    ws = _pre_dispatch_workspace(tmp_path, (1, 7), plan_task_ids=range(1, 8))
    result = _run_pre_dispatch(ws, 2, manifest=False)
    assert result["status"] == "FAIL", result
    assert "previous_task_report" in result["blockers"], result["blockers"]
