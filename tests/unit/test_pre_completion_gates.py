#!/usr/bin/env python3
"""
Unit tests for controller-checkpoint.py pre-completion phase gates:
  - Honesty check artifact gate
  - Trace auditor artifact gate
  - Minimum-tier ratio cap

Run: python3 -m pytest tests/unit/test_pre_completion_gates.py -v
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

# Minimal valid plan with 4 tasks (enough for ratio testing)
FOUR_TASK_PLAN = """\
# Implementation Plan

**Source Contracts**: None

### Task 0 — Setup
- [x] Scaffolding

### Task 1 — Build feature A
- [x] Write code

### Task 2 — Build feature B
- [x] Write code

### Task 3 — Tests
- [x] Write tests
"""

# Implementer report matching the 9 required sections in _report_utils.py
REPORT_CONTENT = """\
# Task {n:03d} Report — Description
# Date: 2026-04-17T10:00:00Z
# Status: DONE

**Implementation Summary**
Implemented the feature.

**Files Changed**
- app/services/feature.py

**Source Files Read**
- app/models/feature.py

**Tests**
All 5 tests pass.

**Contract Compliance**
All contracts honored.

**Deviations from Plan**
None.

**Self-Review Findings**
No issues found.

**Concerns**
None.
"""

HONESTY_CHECK_CONTENT = """\
# Honesty Check Response

## 1. Did you invoke SDD via the Skill tool?
Yes.

## 2. Did you skip any steps?
No.
"""

TRACE_AUDIT_CONTENT = """\
# Execution Trace Audit

## Verdict: CLEAN
No anomalies found.
"""

MIN_REPORT_BYTES = 50


def run_pre_completion(
    plan_content: str,
    report_files: dict | None = None,
    deviations_content: str = "",
    honesty_check_content: str | None = None,
    trace_audit_content: str | None = None,
) -> dict:
    """
    Set up a temp directory with artifacts and run controller-checkpoint
    in pre-completion phase. Returns parsed result dict.
    """
    tmpdir = tempfile.mkdtemp()

    plan_path = os.path.join(tmpdir, "plan.md")
    with open(plan_path, "w") as f:
        f.write(plan_content)

    dev_path = os.path.join(tmpdir, "DEVIATIONS.md")
    with open(dev_path, "w") as f:
        f.write(deviations_content)

    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    if report_files:
        for filename, content in report_files.items():
            with open(os.path.join(reports_dir, filename), "w") as f:
                f.write(content)

    if honesty_check_content is not None:
        with open(os.path.join(reports_dir, "honesty-check-response.md"), "w") as f:
            f.write(honesty_check_content)

    if trace_audit_content is not None:
        with open(os.path.join(reports_dir, "execution-trace-audit.md"), "w") as f:
            f.write(trace_audit_content)

    try:
        cmd = [
            sys.executable, SCRIPT_PATH,
            "--phase", "pre-completion",
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


def _make_full_reports(task_count: int) -> dict:
    """Create implementer + spec + quality review + partner review for N tasks."""
    files = {}
    for n in range(task_count):
        files[f"task-{n:03d}-implementer-report.md"] = REPORT_CONTENT.format(n=n)
        files[f"task-{n:03d}-spec-review.md"] = f"# Spec Review Task {n}\n" + "x" * 100
        files[f"task-{n:03d}-quality-review.md"] = f"# Quality Review Task {n}\n" + "x" * 100
        files[f"partner-review-{n:03d}.md"] = f"# Partner Review Task {n}\n" + "x" * 100
    return files


def _make_reports_with_minimum_tier(
    task_count: int,
    quality_minimum_tasks: list[int] | None = None,
    partner_minimum_tasks: list[int] | None = None,
) -> dict:
    """Create reports where specified tasks use minimum-tier for quality/partner reviews."""
    quality_minimum_tasks = quality_minimum_tasks or []
    partner_minimum_tasks = partner_minimum_tasks or []
    files = {}
    for n in range(task_count):
        files[f"task-{n:03d}-implementer-report.md"] = REPORT_CONTENT.format(n=n)
        files[f"task-{n:03d}-spec-review.md"] = f"# Spec Review Task {n}\n" + "x" * 100

        if n in quality_minimum_tasks:
            files[f"task-{n:03d}-quality-review-minimum-tier.md"] = (
                f"# Quality Review Task {n} — Minimum Tier\nRationale: single config file\n" + "x" * 100
            )
        else:
            files[f"task-{n:03d}-quality-review.md"] = f"# Quality Review Task {n}\n" + "x" * 100

        if n in partner_minimum_tasks:
            files[f"partner-review-{n:03d}-minimum-tier.md"] = (
                f"# Partner Review Task {n} — Minimum Tier\nRationale: trivial change\n" + "x" * 100
            )
        else:
            files[f"partner-review-{n:03d}.md"] = f"# Partner Review Task {n}\n" + "x" * 100
    return files


# ---------------------------------------------------------------------------
# Tests: Honesty check artifact gate
# ---------------------------------------------------------------------------


class TestHonestyCheckGate:
    """Pre-completion must require reports/honesty-check-response.md."""

    def test_missing_honesty_check_is_blocker(self):
        """No honesty-check-response.md → FAIL."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert result["exit_code"] == 1, f"Expected FAIL, got exit {result['exit_code']}"
        assert "honesty_check_missing" in result["output"].get("blockers", [])

    def test_present_honesty_check_passes(self):
        """honesty-check-response.md exists with content → no blocker."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "honesty_check_missing" not in result["output"].get("blockers", [])

    def test_tiny_honesty_check_is_blocker(self):
        """honesty-check-response.md under 50 bytes → FAIL (stub file)."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content="stub",
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "honesty_check_missing" in result["output"].get("blockers", [])

    def test_blocker_message_explains_requirement(self):
        """Blocker detail should mention what's needed."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        checks = result["output"].get("checks", {})
        detail = checks.get("honesty_check_missing", {}).get("detail", "").lower()
        assert "honesty" in detail


# ---------------------------------------------------------------------------
# Tests: Trace auditor artifact gate
# ---------------------------------------------------------------------------


class TestTraceAuditGate:
    """Pre-completion must require reports/execution-trace-audit.md."""

    def test_missing_trace_audit_is_blocker(self):
        """No execution-trace-audit.md → FAIL."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
        )
        assert result["exit_code"] == 1, f"Expected FAIL, got exit {result['exit_code']}"
        assert "trace_audit_missing" in result["output"].get("blockers", [])

    def test_present_trace_audit_passes(self):
        """execution-trace-audit.md exists with content → no blocker."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "trace_audit_missing" not in result["output"].get("blockers", [])

    def test_tiny_trace_audit_is_blocker(self):
        """execution-trace-audit.md under 50 bytes → FAIL."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content="stub",
        )
        assert "trace_audit_missing" in result["output"].get("blockers", [])


# ---------------------------------------------------------------------------
# Tests: Minimum-tier ratio cap
# ---------------------------------------------------------------------------


class TestMinimumTierRatioCap:
    """Pre-completion must block when >50% of reviews are minimum-tier."""

    def test_all_full_reviews_passes(self):
        """0% minimum-tier → no blocker."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" not in result["output"].get("blockers", [])
        assert "excessive_minimum_tier_partner" not in result["output"].get("blockers", [])

    def test_minority_minimum_tier_passes(self):
        """1 of 4 quality reviews minimum-tier (25%) → no blocker."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0])
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" not in result["output"].get("blockers", [])

    def test_majority_minimum_tier_quality_blocked(self):
        """3 of 4 quality reviews minimum-tier (75%) → FAIL."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1, 2])
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" in result["output"].get("blockers", [])

    def test_majority_minimum_tier_partner_blocked(self):
        """3 of 4 partner reviews minimum-tier (75%) → FAIL."""
        reports = _make_reports_with_minimum_tier(4, partner_minimum_tasks=[0, 1, 2])
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_partner" in result["output"].get("blockers", [])

    def test_exactly_half_minimum_tier_passes(self):
        """2 of 4 quality reviews minimum-tier (50%) → no blocker (>50% threshold)."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1])
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" not in result["output"].get("blockers", [])

    def test_all_minimum_tier_quality_blocked(self):
        """4 of 4 quality reviews minimum-tier (100%) → FAIL."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1, 2, 3])
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" in result["output"].get("blockers", [])

    def test_all_minimum_tier_partner_blocked(self):
        """4 of 4 partner reviews minimum-tier (100%) → FAIL."""
        reports = _make_reports_with_minimum_tier(4, partner_minimum_tasks=[0, 1, 2, 3])
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_partner" in result["output"].get("blockers", [])

    def test_blocker_message_includes_counts(self):
        """Blocker detail should show N/M ratio."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1, 2])
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        checks = result["output"].get("checks", {})
        detail = checks.get("excessive_minimum_tier_quality", {}).get("detail", "")
        assert "3" in detail and "4" in detail, \
            f"Blocker should show 3/4 ratio: {detail}"

    def test_both_quality_and_partner_can_fail_independently(self):
        """Quality passes (1/4 min-tier), partner fails (3/4 min-tier)."""
        reports = _make_reports_with_minimum_tier(
            4,
            quality_minimum_tasks=[0],
            partner_minimum_tasks=[0, 1, 2],
        )
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" not in result["output"].get("blockers", [])
        assert "excessive_minimum_tier_partner" in result["output"].get("blockers", [])
