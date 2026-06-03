"""N3a (Check 4c skip-guard) + N10 (Check 5 archive glob) for sdd-pre-dispatch-hook.sh.
Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_hook_hardening.py -v
"""
import json
import os
import subprocess
from datetime import datetime, timezone

from sdd_test_helpers import make_hook_input, setup_manifest_workspace

HOOK_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh",
))
NOW = "2026-06-01T00:00:00Z"


def run_hook(stdin_data):
    return subprocess.run(["bash", HOOK_PATH], input=stdin_data,
                          capture_output=True, text=True, timeout=10)


def _impl(p):
    p.write_text("x" * 80)


def _full_support(reports, task_num, *, partner=True):
    """Create audit + checkpoint (+ partner review & provenance) so that the ONLY
    gate that could fire for `task_num` is Check 4c. Returns nothing."""
    _impl(reports / "pre-execution-audit.md")
    padded = f"{task_num:03d}"
    (reports / f"checkpoint-pre-dispatch-{padded}.json").write_text(
        json.dumps({"status": "PASS", "phase": "pre-dispatch", "detail": "x" * 60}))
    if partner:
        _impl(reports / f"partner-review-{padded}.md")
        with open(reports / ".dispatch-log", "a") as f:
            f.write(f"{NOW} DISPATCH reviewer task={task_num} type=partner-review\n")


def test_check4c_skipped_for_module_first_task(tmp_path):
    # Module 2 active (task_range starts at 2); empty log (post-truncation).
    # Dispatching task 2 must ALLOW: PREV=1 < START=2 -> skip-guard. Non-vacuous:
    # pre-fix Check 4c looks for `task=1 type=spec-review` in the empty log -> BLOCK.
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(2, 3), total_tasks=4)
    reports = ws["reports_dir"]
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    _full_support(reports, 2)
    r = run_hook(make_hook_input(description="Implement task 2",
                                 prompt="You are implementing task 2", cwd=str(ws["root"])))
    assert r.returncode == 0, f"stderr={r.stderr}"


def test_check4c_enforced_within_module(tmp_path):
    # Within-module dispatch (PREV >= START) still requires provenance.
    # task_range (2,3); dispatch task 3; PREV=2 >= START=2 -> check runs; no
    # task=2 provenance in log -> BLOCK.
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(2, 3), total_tasks=4)
    reports = ws["reports_dir"]
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    # Task 2 reports exist (so N-1 file checks pass) but NO spec/quality provenance.
    for kind in ("implementer-report", "spec-review", "quality-review"):
        _impl(reports / f"task-002-{kind}.md")
    _full_support(reports, 3)
    r = run_hook(make_hook_input(description="Implement task 3",
                                 prompt="You are implementing task 3", cwd=str(ws["root"])))
    assert r.returncode == 2
    assert "spec-review dispatch recorded for Task 2" in r.stderr


def test_check4c_skipped_for_no_task0_single_module(tmp_path):
    # Acceptance criterion #3: no-Task-0 single-module plan starting at Task 1
    # (no transition, no archive). task_range (1,2); dispatch task 1; PREV=0 <
    # START=1 -> skip-guard -> ALLOW. Non-vacuous: pre-fix Check 4c greps the
    # empty log for `task=0 type=spec-review` and BLOCKS, forcing a forged task=0
    # entry. (Check 6b is inert here: TASK_NUMBER=1 is not > 1.)
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(1, 2), total_tasks=2)
    reports = ws["reports_dir"]
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    _full_support(reports, 1)
    r = run_hook(make_hook_input(description="Implement task 1",
                                 prompt="You are implementing task 1", cwd=str(ws["root"])))
    assert r.returncode == 0, f"stderr={r.stderr}"


def test_check5_finds_archived_task0(tmp_path):
    # N10: Source-Contracts plan, Task 0 report archived; dispatching task 2 must
    # NOT block on the Task-0 gate (Check 5 globs archive-*/).
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(2, 3), total_tasks=4)
    root, reports, feat = ws["root"], ws["reports_dir"], ws["feat_dir"]
    # Give the plan real Source Contracts so Check 5 activates.
    plan = feat / "plan.md"
    plan.write_text(plan.read_text().replace("**Source Contracts:** None",
                                             "**Source Contracts:** docs/spec.md"))
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")     # archived Task 0
    _full_support(reports, 2)
    r = run_hook(make_hook_input(description="Implement task 2",
                                 prompt="You are implementing task 2", cwd=str(root)))
    # Must not block for the Task-0 reason (skip-guard handles Check 4c via PREV<START).
    assert "no Task 0 report found" not in r.stderr.lower()
    assert r.returncode == 0, f"stderr={r.stderr}"
