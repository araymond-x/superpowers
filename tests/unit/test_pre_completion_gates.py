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

import pytest

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
    honesty_check_filename: str = "honesty-check-2026-04-17.md",
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
        with open(os.path.join(reports_dir, honesty_check_filename), "w") as f:
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
    """Pre-completion must require reports/honesty-check-*.md."""

    def test_missing_honesty_check_is_blocker(self):
        """No honesty-check-*.md → FAIL."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert result["exit_code"] == 1, f"Expected FAIL, got exit {result['exit_code']}"
        assert "honesty_check_missing" in result["output"].get("blockers", [])

    def test_present_honesty_check_passes(self):
        """honesty-check-YYYY-MM-DD.md exists with content → no blocker."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN, report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "honesty_check_missing" not in result["output"].get("blockers", [])

    def test_tiny_honesty_check_is_blocker(self):
        """honesty-check-*.md under 50 bytes → FAIL (stub file)."""
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


# ---------------------------------------------------------------------------
# Tests: Declared review_tier:minimum exclusion from ratio denominator
# ---------------------------------------------------------------------------


def _plan_with_review_tiers(task_count: int, minimum_task_ids: list[int]) -> str:
    """Plan markdown with YAML frontmatter declaring review_tier per task."""
    lines = ["---", "schema_version: 1", "feature_archetype: extension", "tasks:"]
    for n in range(task_count):
        lines.append(f"  - id: {n}")
        lines.append(f"    title: 'Task {n}'")
        if n in minimum_task_ids:
            lines.append("    review_tier: minimum")
    lines.append("---")
    lines.append("")
    for n in range(task_count):
        lines.append(f"### Task {n} -- Task {n}")
        lines.append("- [x] done")
    return "\n".join(lines) + "\n"


class TestDeclaredMinimumExclusion:
    # (declared_min, quality_min, partner_min, expect_quality_block, expect_partner_block)
    @pytest.mark.parametrize("declared,q_min,p_min,q_block,p_block", [
        ([0, 1, 2],    [0, 1, 2],    [],           False, False),  # declared-min quality excluded -> PASS
        ([],           [0, 1, 2],    [],           True,  False),  # undeclared 3/4 min -> block
        ([0, 1, 2],    [],           [0, 1, 2],    False, False),  # declared-min partner excluded -> PASS
        ([0],          [0, 1, 2],    [],           True,  False),  # 1 excluded; 2/3 remaining min -> block
        ([0, 1, 2, 3], [0, 1, 2, 3], [],           False, False),  # all declared -> zero denom -> PASS
    ])
    def test_declared_minimum_exclusion(self, declared, q_min, p_min, q_block, p_block):
        plan = _plan_with_review_tiers(4, minimum_task_ids=declared)
        reports = _make_reports_with_minimum_tier(
            4, quality_minimum_tasks=q_min, partner_minimum_tasks=p_min)
        blockers = run_pre_completion(plan, report_files=reports)["output"].get("blockers", [])
        assert ("excessive_minimum_tier_quality" in blockers) == q_block
        assert ("excessive_minimum_tier_partner" in blockers) == p_block

    def test_unparseable_plan_falls_back(self):
        """No YAML frontmatter -> empty exclusion set -> current behavior (3/4 min -> block)."""
        plan = "# Plan no frontmatter\n### Task 0\n### Task 1\n### Task 2\n### Task 3\n"
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1, 2])
        blockers = run_pre_completion(plan, report_files=reports)["output"].get("blockers", [])
        assert "excessive_minimum_tier_quality" in blockers

    def test_declared_minimum_across_module_files(self, tmp_path):
        """Multi-file (acceptance 'all module plan files read'): declared-minimum
        tasks in a SECOND plan file are excluded. Without the cross-file scan,
        3/4 quality reviews are minimum -> block; with it -> PASS. Uses
        --additional-plan-files (same all_plan_contents path Step 3b feeds)."""
        (tmp_path / "plan.md").write_text(_plan_with_review_tiers(4, minimum_task_ids=[]))
        (tmp_path / "mod-b.md").write_text(_plan_with_review_tiers(4, minimum_task_ids=[1, 2, 3]))
        (tmp_path / "DEVIATIONS.md").write_text("")
        rdir = tmp_path / "reports"; rdir.mkdir()
        for name, c in _make_reports_with_minimum_tier(4, quality_minimum_tasks=[1, 2, 3]).items():
            (rdir / name).write_text(c)
        r = subprocess.run([sys.executable, SCRIPT_PATH, "--phase", "pre-completion",
                            "--plan-file", str(tmp_path / "plan.md"),
                            "--additional-plan-files", str(tmp_path / "mod-b.md"),
                            "--deviations-file", str(tmp_path / "DEVIATIONS.md"),
                            "--reports-dir", str(rdir)],
                           capture_output=True, text=True, timeout=10)
        assert r.stdout.strip(), f"checkpoint produced no output: {r.stderr}"
        out = json.loads(r.stdout)
        assert "excessive_minimum_tier_quality" not in out.get("blockers", [])


# ---------------------------------------------------------------------------
# Tests: Verification task ratio cap (>30% triggers blocker)
# ---------------------------------------------------------------------------


def _plan_with_task_types(task_count: int, verification_task_ids: list[int]) -> str:
    """Plan markdown with YAML frontmatter declaring task_type per task AND a
    matching `### Task N` header for each task.

    The frontmatter ids and the header numbers MUST agree: _verification_task_ids
    reads task_type from frontmatter while the ratio denominator is counted from
    `### Task N` headers (TASK_HEADER_PATTERN).
    """
    lines = ["---", "schema_version: 1", "feature_archetype: extension", "tasks:"]
    for n in range(task_count):
        lines.append(f"  - id: {n}")
        lines.append(f"    title: 'Task {n}'")
        if n in verification_task_ids:
            lines.append("    task_type: verification")
    lines.append("---")
    lines.append("")
    for n in range(task_count):
        lines.append(f"### Task {n} -- Task {n}")
        lines.append("- [x] done")
    return "\n".join(lines) + "\n"


class TestVerificationRatioCheck:
    """Pre-completion verification task ratio capped at 30%."""

    def test_no_verification_tasks_passes(self):
        """Plan with all implementation tasks (no task_type) → PASS."""
        plan = _plan_with_task_types(5, verification_task_ids=[])
        result = run_pre_completion(plan)
        check = result["output"].get("checks", {}).get("verification_ratio", {})
        assert check.get("status") == "PASS", f"Expected PASS: {check}"

    def test_30_percent_passes(self):
        """7 implementation + 3 verification = 10 tasks (exactly 30%) → PASS.

        30% is NOT strictly greater than 30%, so it must pass.
        """
        plan = _plan_with_task_types(10, verification_task_ids=[0, 1, 2])
        result = run_pre_completion(plan)
        check = result["output"].get("checks", {}).get("verification_ratio", {})
        assert check.get("status") == "PASS", f"Expected PASS at exactly 30%: {check}"

    def test_over_30_percent_fails(self):
        """6 implementation + 4 verification = 10 tasks (40%) → FAIL.

        The blocker detail must name the verification tasks.
        """
        plan = _plan_with_task_types(10, verification_task_ids=[0, 1, 2, 3])
        result = run_pre_completion(plan)
        check = result["output"].get("checks", {}).get("verification_ratio", {})
        assert check.get("status") == "FAIL", f"Expected FAIL at 40%: {check}"
        assert "verification_ratio" in result["output"].get("blockers", [])
        detail = check.get("detail", "")
        for tid in (0, 1, 2, 3):
            assert f"Task {tid}" in detail, \
                f"Blocker detail should name Task {tid}: {detail}"

    def test_ratio_with_no_tasks_passes(self):
        """Empty plan (no tasks) → PASS (no divide-by-zero)."""
        plan = _plan_with_task_types(0, verification_task_ids=[])
        result = run_pre_completion(plan)
        check = result["output"].get("checks", {}).get("verification_ratio", {})
        assert check.get("status") == "PASS", f"Expected PASS for empty plan: {check}"
