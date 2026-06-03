"""D6: SSOT agreement on the FILE-based minimum signal between
sdd-pre-dispatch-hook.sh (Check 4c) and transition-module.py
(validate_module_completion). Both must require quality-review provenance UNLESS
task-NNN-quality-review-minimum-tier.md exists.
Run: .venv/bin/python3 -m pytest tests/unit/test_ssot_minimum_agreement.py -v
"""
import json
import os
import subprocess

import pytest
from sdd_test_helpers import make_hook_input, setup_manifest_workspace

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh")
TRANSITION = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", "transition-module.py")
PYTHON = os.path.join(ROOT, ".venv", "bin", "python3")
NOW = "2026-06-01T00:00:00Z"


def _impl(p):
    p.write_text("x" * 80)


def _hook_requires_quality_prov(tmp_path, min_file, provenance):
    """Decision from Check 4c: does the hook block on MISSING quality provenance
    for the previous task? Set up a single module [0,1]; dispatch task 1 (PREV=0,
    within-module so Check 4c runs). Returns True if it blocks for quality."""
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(0, 1), total_tasks=2)
    reports = ws["reports_dir"]
    log = reports / ".dispatch-log"
    log.write_text("# sdd-hook-sentinel abc123\n")
    # Task 0 fully present + spec provenance (isolate the quality decision).
    for kind in ("implementer-report", "spec-review"):
        _impl(reports / f"task-000-{kind}.md")
    with open(log, "a") as f:
        f.write(f"{NOW} DISPATCH reviewer task=0 type=spec-review\n")
    if min_file:
        _impl(reports / "task-000-quality-review-minimum-tier.md")
    else:
        _impl(reports / "task-000-quality-review.md")
    if provenance:
        with open(log, "a") as f:
            f.write(f"{NOW} DISPATCH reviewer task=0 type=quality-review\n")
    # Support files so only Check 4c quality can fire for task 1.
    _impl(reports / "pre-execution-audit.md")
    (reports / "checkpoint-pre-dispatch-001.json").write_text(
        json.dumps({"status": "PASS", "detail": "x" * 60}))
    _impl(reports / "partner-review-001.md")
    with open(log, "a") as f:
        f.write(f"{NOW} DISPATCH reviewer task=1 type=partner-review\n")
    r = subprocess.run(["bash", HOOK],
                       input=make_hook_input(description="Implement task 1",
                                             prompt="You are implementing task 1",
                                             cwd=str(ws["root"])),
                       capture_output=True, text=True, timeout=10)
    return "quality-review dispatch recorded for Task 0" in r.stderr


def _transition_requires_quality_prov(tmp_path, min_file, provenance):
    """Decision from validate_module_completion: does the transition error on
    MISSING quality provenance for task 0 of the completing module?"""
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    feat = tmp_path / "docs" / "imp-plans" / "f"; (feat / "reports").mkdir(parents=True)
    reports = feat / "reports"
    (feat / "deviations.md").write_text("# Deviations\n")
    log = reports / ".dispatch-log"; log.write_text("# sdd-hook-sentinel abc\n")
    _impl(reports / "task-000-implementer-report.md")
    _impl(reports / "task-000-spec-review.md")
    with open(log, "a") as f:
        f.write(f"{NOW} DISPATCH reviewer task=0 type=spec-review\n")
    if min_file:
        _impl(reports / "task-000-quality-review-minimum-tier.md")
    else:
        _impl(reports / "task-000-quality-review.md")
    if provenance:
        with open(log, "a") as f:
            f.write(f"{NOW} DISPATCH reviewer task=0 type=quality-review\n")
    import sys
    sys.path.insert(0, os.path.join(ROOT, "skills", "scripts", "models"))
    from sdd_session import TIER_PROFILES
    profile = TIER_PROFILES["standard"]
    manifest = {
        "schema_version": 1, "tier": "standard",
        "paths": {"feature_dir": str(feat.relative_to(tmp_path)),
                  "reports_dir": str(reports.relative_to(tmp_path)),
                  "dispatch_log": str(log.relative_to(tmp_path)),
                  "deviations_file": str((feat / "deviations.md").relative_to(tmp_path))},
        "plan_file": str((feat / "plan.md").relative_to(tmp_path)),
        "active_module_id": 1, "active_module_file": "m1.md",
        "task_range": [0, 0], "total_tasks": 2, "midpoint": 0,
        "enforcement": profile["enforcement"], "process_requirements": profile["process_requirements"],
        "completed_modules": [], "module_reports_archived": False,
        "modules": [{"id": 1, "title": "Core", "file": "m1.md", "task_ids": [0]},
                    {"id": 2, "title": "API", "file": "m2.md", "task_ids": [1]}],
        "dispatch_log_sentinel": False,
    }
    mp = feat / ".sdd-session.json"; mp.write_text(json.dumps(manifest))
    r = subprocess.run([PYTHON, TRANSITION, "--manifest", str(mp),
                       "--completed-module", "Core", "--next-module", "API"],
                      capture_output=True, text=True, timeout=10)
    return "Task 0: quality review not provenance-logged" in r.stderr


@pytest.mark.parametrize("min_file,provenance", [(True, False), (False, False), (False, True), (True, True)])
def test_minimum_signal_agreement(tmp_path, min_file, provenance):
    # Deviation from verbatim plan code: the two drivers each git-init their own
    # root before mkdir-ing it; pytest creates only the base tmp_path, so these
    # subdirs must exist first. (The plan code needs the same fix upstream.)
    (tmp_path / "hook").mkdir()
    (tmp_path / "trans").mkdir()
    hook = _hook_requires_quality_prov(tmp_path / "hook", min_file, provenance)
    trans = _transition_requires_quality_prov(tmp_path / "trans", min_file, provenance)
    assert hook == trans, (
        f"Disagreement (min_file={min_file}, provenance={provenance}): "
        f"hook_requires={hook} transition_requires={trans}")
    # Anchor the expected decision: require ONLY when no min-file AND no provenance.
    assert hook == (not min_file and not provenance)
