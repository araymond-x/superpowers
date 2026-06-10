"""N1: Regression test proving multi-error accumulation in sdd-pre-dispatch-hook.sh.

The hook uses an ERRORS=() array and appends via ERRORS+=("...") at each gate
check. At the end (~L702-709), ALL accumulated errors are emitted to stderr
before exit 2. This test drives the hook with three simultaneous violations
(previous task has NO implementer report, NO spec review, NO quality review)
and asserts all three BLOCKED messages are reported in ONE hook invocation,
on distinct lines — i.e. the hook does not short-circuit on the first failure.

Every other gate is satisfied so exactly these three checks fire:
- pre-execution audit present (Check 2)
- deviations.md + reports/ from setup_manifest_workspace (Check 3)
- dispatch log carries task=1 spec/quality provenance (Check 4c)
- plan has "Source Contracts: None" (Check 5 inert)
- checkpoint-pre-dispatch-002.json present (Check 5c)
- partner-review-002.md + task=2 partner provenance (Check 5d)
- plan has the Task 2 header (Check 6 token estimation)
- context-summary.md present (Check 6b; midpoint for range (1,3) is 2)

Run: .venv/bin/python3 -m pytest tests/unit/test_n1_multi_error_accumulation.py -v
"""
import json
import os
import subprocess

from sdd_test_helpers import make_hook_input, setup_manifest_workspace

HOOK_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh",
))
NOW = "2026-06-10T00:00:00Z"


def run_hook(stdin_data: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", HOOK_PATH], input=stdin_data,
                          capture_output=True, text=True, timeout=10)


class TestMultiErrorAccumulation:
    def test_multiple_violations_all_reported(self, tmp_path):
        """Missing implementer report + missing spec review + missing quality
        review for the previous task -> all three BLOCKED messages in one run."""
        ws = setup_manifest_workspace(
            tmp_path, tier="standard", task_range=(1, 3), total_tasks=3
        )
        reports = ws["reports_dir"]

        # Dispatch log: sentinel + provenance entries so Check 4c (dispatch
        # provenance) and Check 5d (partner provenance) are satisfied — the
        # review REPORT files for task 1 are deliberately absent.
        (reports / ".dispatch-log").write_text(
            "# sdd-hook-sentinel abc123\n"
            f"{NOW} DISPATCH reviewer task=1 type=spec-review\n"
            f"{NOW} DISPATCH reviewer task=1 type=quality-review\n"
            f"{NOW} DISPATCH reviewer task=2 type=partner-review\n"
        )

        # Task 1 report artifacts: NONE (missing impl report, spec, quality).
        # Everything else needed to reach those three checks is satisfied:
        (reports / "pre-execution-audit.md").write_text("x" * 80)
        (reports / "checkpoint-pre-dispatch-002.json").write_text(
            json.dumps({"status": "PASS", "phase": "pre-dispatch", "detail": "x" * 60})
        )
        (reports / "partner-review-002.md").write_text("x" * 80)
        # Midpoint for task_range (1,3) is 2 -> Check 6b fires at task 2
        # unless the context summary exists.
        (reports / "context-summary.md").write_text("# Context Summary\n" + "x" * 60)

        result = run_hook(make_hook_input(
            description="Implement task 2",
            prompt="You are implementing task 2",
            cwd=str(tmp_path),
        ))

        assert result.returncode == 2, f"stderr: {result.stderr}"

        # All three missing-artifact messages appear (exact hook wording from
        # ERRORS+= sites at hook lines ~428/470/484), not just the first.
        expected = [
            "No implementer report found for Task 1",
            "No spec review found for Task 1",
            "No quality review found for Task 1",
        ]
        lines = result.stderr.splitlines()
        matched_line_indices = set()
        for msg in expected:
            hits = [i for i, line in enumerate(lines) if msg in line]
            assert hits, f"Missing error message: {msg!r}\nstderr: {result.stderr}"
            matched_line_indices.add(hits[0])

        # The three messages occupy DISTINCT error lines of the single
        # invocation — accumulation, not one merged/first-only message.
        assert len(matched_line_indices) == 3, (
            f"Expected 3 distinct error lines, got indices "
            f"{sorted(matched_line_indices)}\nstderr: {result.stderr}"
        )
        blocked_count = sum(1 for line in lines if "BLOCKED:" in line)
        assert blocked_count >= 3, (
            f"Expected >=3 BLOCKED lines, got {blocked_count}\n"
            f"stderr: {result.stderr}"
        )
