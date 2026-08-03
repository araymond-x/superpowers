#!/usr/bin/env python3
"""
Unit tests for controller-checkpoint.py pre-completion phase gates:
  - Honesty check artifact gate
  - Trace auditor artifact gate
  - Minimum-tier ratio cap

Run: python3 -m pytest tests/unit/test_pre_completion_gates.py -v
"""

import importlib.util
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


def _load_checkpoint_module():
    """Load controller-checkpoint.py as a module for in-process helper testing.

    The script filename contains hyphens, so it is not importable by name.
    """
    spec = importlib.util.spec_from_file_location("controller_checkpoint", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_checkpoint = _load_checkpoint_module()

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
            sys.executable,
            SCRIPT_PATH,
            "--phase",
            "pre-completion",
            "--plan-file",
            plan_path,
            "--deviations-file",
            dev_path,
            "--reports-dir",
            reports_dir,
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
        files[f"task-{n:03d}-quality-review.md"] = (
            f"# Quality Review Task {n}\n" + "x" * 100
        )
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
                f"# Quality Review Task {n} — Minimum Tier\nRationale: single config file\n"
                + "x" * 100
            )
        else:
            files[f"task-{n:03d}-quality-review.md"] = (
                f"# Quality Review Task {n}\n" + "x" * 100
            )

        if n in partner_minimum_tasks:
            files[f"partner-review-{n:03d}-minimum-tier.md"] = (
                f"# Partner Review Task {n} — Minimum Tier\nRationale: trivial change\n"
                + "x" * 100
            )
        else:
            files[f"partner-review-{n:03d}.md"] = (
                f"# Partner Review Task {n}\n" + "x" * 100
            )
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
            FOUR_TASK_PLAN,
            report_files=reports,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert result["exit_code"] == 1, (
            f"Expected FAIL, got exit {result['exit_code']}"
        )
        assert "honesty_check_missing" in result["output"].get("blockers", [])

    def test_present_honesty_check_passes(self):
        """honesty-check-YYYY-MM-DD.md exists with content → no blocker."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "honesty_check_missing" not in result["output"].get("blockers", [])

    def test_tiny_honesty_check_is_blocker(self):
        """honesty-check-*.md under 50 bytes → FAIL (stub file)."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content="stub",
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "honesty_check_missing" in result["output"].get("blockers", [])

    def test_blocker_message_explains_requirement(self):
        """Blocker detail should mention what's needed."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
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
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
        )
        assert result["exit_code"] == 1, (
            f"Expected FAIL, got exit {result['exit_code']}"
        )
        assert "trace_audit_missing" in result["output"].get("blockers", [])

    def test_present_trace_audit_passes(self):
        """execution-trace-audit.md exists with content → no blocker."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "trace_audit_missing" not in result["output"].get("blockers", [])

    def test_tiny_trace_audit_is_blocker(self):
        """execution-trace-audit.md under 50 bytes → FAIL."""
        reports = _make_full_reports(4)
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
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
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" not in result["output"].get(
            "blockers", []
        )
        assert "excessive_minimum_tier_partner" not in result["output"].get(
            "blockers", []
        )

    def test_minority_minimum_tier_passes(self):
        """1 of 4 quality reviews minimum-tier (25%) → no blocker."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0])
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" not in result["output"].get(
            "blockers", []
        )

    def test_majority_minimum_tier_quality_blocked(self):
        """3 of 4 quality reviews minimum-tier (75%) → FAIL."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1, 2])
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" in result["output"].get("blockers", [])

    def test_majority_minimum_tier_partner_blocked(self):
        """3 of 4 partner reviews minimum-tier (75%) → FAIL."""
        reports = _make_reports_with_minimum_tier(4, partner_minimum_tasks=[0, 1, 2])
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_partner" in result["output"].get("blockers", [])

    def test_exactly_half_minimum_tier_passes(self):
        """2 of 4 quality reviews minimum-tier (50%) → no blocker (>50% threshold)."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1])
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" not in result["output"].get(
            "blockers", []
        )

    def test_all_minimum_tier_quality_blocked(self):
        """4 of 4 quality reviews minimum-tier (100%) → FAIL."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1, 2, 3])
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" in result["output"].get("blockers", [])

    def test_all_minimum_tier_partner_blocked(self):
        """4 of 4 partner reviews minimum-tier (100%) → FAIL."""
        reports = _make_reports_with_minimum_tier(4, partner_minimum_tasks=[0, 1, 2, 3])
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_partner" in result["output"].get("blockers", [])

    def test_blocker_message_includes_counts(self):
        """Blocker detail should show N/M ratio."""
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1, 2])
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        checks = result["output"].get("checks", {})
        detail = checks.get("excessive_minimum_tier_quality", {}).get("detail", "")
        assert "3" in detail and "4" in detail, (
            f"Blocker should show 3/4 ratio: {detail}"
        )

    def test_both_quality_and_partner_can_fail_independently(self):
        """Quality passes (1/4 min-tier), partner fails (3/4 min-tier)."""
        reports = _make_reports_with_minimum_tier(
            4,
            quality_minimum_tasks=[0],
            partner_minimum_tasks=[0, 1, 2],
        )
        result = run_pre_completion(
            FOUR_TASK_PLAN,
            report_files=reports,
            honesty_check_content=HONESTY_CHECK_CONTENT,
            trace_audit_content=TRACE_AUDIT_CONTENT,
        )
        assert "excessive_minimum_tier_quality" not in result["output"].get(
            "blockers", []
        )
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
    @pytest.mark.parametrize(
        "declared,q_min,p_min,q_block,p_block",
        [
            (
                [0, 1, 2],
                [0, 1, 2],
                [],
                False,
                False,
            ),  # declared-min quality excluded -> PASS
            ([], [0, 1, 2], [], True, False),  # undeclared 3/4 min -> block
            (
                [0, 1, 2],
                [],
                [0, 1, 2],
                False,
                False,
            ),  # declared-min partner excluded -> PASS
            ([0], [0, 1, 2], [], True, False),  # 1 excluded; 2/3 remaining min -> block
            (
                [0, 1, 2, 3],
                [0, 1, 2, 3],
                [],
                False,
                False,
            ),  # all declared -> zero denom -> PASS
        ],
    )
    def test_declared_minimum_exclusion(self, declared, q_min, p_min, q_block, p_block):
        plan = _plan_with_review_tiers(4, minimum_task_ids=declared)
        reports = _make_reports_with_minimum_tier(
            4, quality_minimum_tasks=q_min, partner_minimum_tasks=p_min
        )
        blockers = run_pre_completion(plan, report_files=reports)["output"].get(
            "blockers", []
        )
        assert ("excessive_minimum_tier_quality" in blockers) == q_block
        assert ("excessive_minimum_tier_partner" in blockers) == p_block

    def test_unparseable_plan_falls_back(self):
        """No YAML frontmatter -> empty exclusion set -> current behavior (3/4 min -> block)."""
        plan = "# Plan no frontmatter\n### Task 0\n### Task 1\n### Task 2\n### Task 3\n"
        reports = _make_reports_with_minimum_tier(4, quality_minimum_tasks=[0, 1, 2])
        blockers = run_pre_completion(plan, report_files=reports)["output"].get(
            "blockers", []
        )
        assert "excessive_minimum_tier_quality" in blockers

    def test_declared_minimum_across_module_files(self, tmp_path):
        """Multi-file (acceptance 'all module plan files read'): declared-minimum
        tasks in a SECOND plan file are excluded. Without the cross-file scan,
        3/4 quality reviews are minimum -> block; with it -> PASS. Uses
        --additional-plan-files (same all_plan_contents path Step 3b feeds)."""
        (tmp_path / "plan.md").write_text(
            _plan_with_review_tiers(4, minimum_task_ids=[])
        )
        (tmp_path / "mod-b.md").write_text(
            _plan_with_review_tiers(4, minimum_task_ids=[1, 2, 3])
        )
        (tmp_path / "DEVIATIONS.md").write_text("")
        rdir = tmp_path / "reports"
        rdir.mkdir()
        for name, c in _make_reports_with_minimum_tier(
            4, quality_minimum_tasks=[1, 2, 3]
        ).items():
            (rdir / name).write_text(c)
        r = subprocess.run(
            [
                sys.executable,
                SCRIPT_PATH,
                "--phase",
                "pre-completion",
                "--plan-file",
                str(tmp_path / "plan.md"),
                "--additional-plan-files",
                str(tmp_path / "mod-b.md"),
                "--deviations-file",
                str(tmp_path / "DEVIATIONS.md"),
                "--reports-dir",
                str(rdir),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
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
            assert f"Task {tid}" in detail, (
                f"Blocker detail should name Task {tid}: {detail}"
            )

    def test_ratio_with_no_tasks_passes(self):
        """Empty plan (no tasks) → PASS (no divide-by-zero)."""
        plan = _plan_with_task_types(0, verification_task_ids=[])
        result = run_pre_completion(plan)
        check = result["output"].get("checks", {}).get("verification_ratio", {})
        assert check.get("status") == "PASS", f"Expected PASS for empty plan: {check}"


# ---------------------------------------------------------------------------
# Tests: Git reality check — verification tasks must not modify files
# ---------------------------------------------------------------------------


def _init_temp_git_repo():
    """Create an isolated temp git repo with local identity configured."""
    repo = tempfile.mkdtemp()
    subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", repo, "config", "user.email", "test@example.com"], check=True
    )
    subprocess.run(["git", "-C", repo, "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", repo, "config", "commit.gpgsign", "false"], check=True)
    return repo


def _commit_file_at(repo, filename, iso_date):
    """Create + commit a file with a fixed author/committer date (ISO 8601)."""
    with open(os.path.join(repo, filename), "w") as f:
        f.write("content\n")
    subprocess.run(["git", "-C", repo, "add", filename], check=True)
    env = dict(os.environ)
    env["GIT_AUTHOR_DATE"] = iso_date
    env["GIT_COMMITTER_DATE"] = iso_date
    subprocess.run(
        ["git", "-C", repo, "commit", "-q", "-m", f"add {filename}"],
        check=True,
        env=env,
    )


def _commit_files_at(repo, filenames, iso_date):
    """Create + commit MULTIPLE files in a single commit with a fixed date.

    Creates parent directories as needed so subdirectory filenames (e.g.
    feature-dir bookkeeping paths) work without a separate mkdir step.
    """
    for filename in filenames:
        full_path = os.path.join(repo, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write("content\n")
    subprocess.run(["git", "-C", repo, "add"] + list(filenames), check=True)
    env = dict(os.environ)
    env["GIT_AUTHOR_DATE"] = iso_date
    env["GIT_COMMITTER_DATE"] = iso_date
    subprocess.run(
        ["git", "-C", repo, "commit", "-q", "-m", "bookkeeping commit"],
        check=True,
        env=env,
    )


class TestGitRealityCheck:
    """_check_verification_git_reality flags file-modifying commits in a
    verification task's dispatch window."""

    def test_no_verification_tasks_skips(self):
        """Empty verification_ids → [] regardless of log/repo."""
        findings = _checkpoint._check_verification_git_reality(
            set(), "/nonexistent/.dispatch-log"
        )
        assert findings == []

    def test_missing_dispatch_log_passes(self):
        """Nonexistent dispatch log → [] (best-effort, no crash)."""
        findings = _checkpoint._check_verification_git_reality(
            {3}, "/nonexistent/path/.dispatch-log"
        )
        assert findings == []

    def test_clean_window_passes(self):
        """A bounded verification window with NO commit inside → [].

        Non-vacuity: the repo's only commit is dated BEFORE the window AND
        git_root points at the isolated temp repo, so `git -C <repo> log`
        cannot see the host superpowers repo's commits. The test passes
        BECAUSE of this isolation — without git_root it would inspect the
        host repo and see unrelated commits.
        """
        repo = _init_temp_git_repo()
        try:
            # Commit dated 2026-01-01, well before the verification window.
            _commit_file_at(repo, "before.txt", "2026-01-01T00:00:00")

            log_dir = tempfile.mkdtemp()
            try:
                log_path = os.path.join(log_dir, ".dispatch-log")
                # Verification task 3 at T1, bounding task 4 at T2.
                with open(log_path, "w") as f:
                    f.write(
                        "2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer\n"
                    )
                    f.write(
                        "2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer\n"
                    )

                findings = _checkpoint._check_verification_git_reality(
                    {3}, log_path, git_root=repo
                )
                assert findings == [], (
                    f"Expected no findings (clean window): {findings}"
                )
            finally:
                shutil.rmtree(log_dir, ignore_errors=True)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_file_modifying_commits_fails(self):
        """A commit dated INSIDE the verification window → non-empty findings
        whose entry['task'] == the verification task id."""
        repo = _init_temp_git_repo()
        try:
            # Commit dated 2026-03-01T10:30:00 — between task=3 (10:00) and task=4 (11:00).
            _commit_file_at(repo, "modified.txt", "2026-03-01T10:30:00")

            log_dir = tempfile.mkdtemp()
            try:
                log_path = os.path.join(log_dir, ".dispatch-log")
                with open(log_path, "w") as f:
                    f.write(
                        "2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer\n"
                    )
                    f.write(
                        "2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer\n"
                    )

                findings = _checkpoint._check_verification_git_reality(
                    {3}, log_path, git_root=repo
                )
                assert findings, (
                    f"Expected non-empty findings (commit in window): {findings}"
                )
                assert findings[0]["task"] == 3, (
                    f"Finding should name task 3: {findings}"
                )
            finally:
                shutil.rmtree(log_dir, ignore_errors=True)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_bookkeeping_commit_in_window_passes(self):
        """A commit inside the window touching ONLY feature-dir bookkeeping
        files (handoff-spawn.log + .handoff-hops under reports/) produces no
        finding when exclude_dir names the feature dir (Decision 17)."""
        repo = _init_temp_git_repo()
        try:
            _commit_files_at(
                repo,
                [
                    "docs/imp-plans/feat/reports/handoff-spawn.log",
                    "docs/imp-plans/feat/reports/.handoff-hops",
                ],
                "2026-03-01T10:30:00",
            )

            log_dir = tempfile.mkdtemp()
            try:
                log_path = os.path.join(log_dir, ".dispatch-log")
                with open(log_path, "w") as f:
                    f.write(
                        "2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer\n"
                    )
                    f.write(
                        "2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer\n"
                    )

                findings = _checkpoint._check_verification_git_reality(
                    {3},
                    log_path,
                    git_root=repo,
                    exclude_dir="docs/imp-plans/feat",
                )
                assert findings == [], (
                    f"Expected no findings (bookkeeping-only commit excluded): {findings}"
                )
            finally:
                shutil.rmtree(log_dir, ignore_errors=True)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_source_commit_in_window_still_fails(self):
        """A commit inside the window touching a SOURCE file (outside the
        excluded feature dir) still produces a finding even with exclude_dir
        set — only feature-dir bookkeeping is exempted."""
        repo = _init_temp_git_repo()
        try:
            _commit_file_at(repo, "src-file.py", "2026-03-01T10:30:00")

            log_dir = tempfile.mkdtemp()
            try:
                log_path = os.path.join(log_dir, ".dispatch-log")
                with open(log_path, "w") as f:
                    f.write(
                        "2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer\n"
                    )
                    f.write(
                        "2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer\n"
                    )

                findings = _checkpoint._check_verification_git_reality(
                    {3},
                    log_path,
                    git_root=repo,
                    exclude_dir="docs/imp-plans/feat",
                )
                assert findings, (
                    f"Expected finding (source file outside exclude_dir): {findings}"
                )
                assert findings[0]["task"] == 3
            finally:
                shutil.rmtree(log_dir, ignore_errors=True)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_no_exclude_dir_keeps_old_behavior(self):
        """Backward-compat pin: exclude_dir=None (the default) still flags a
        bookkeeping-only commit — the exclusion is opt-in via exclude_dir."""
        repo = _init_temp_git_repo()
        try:
            _commit_files_at(
                repo,
                [
                    "docs/imp-plans/feat/reports/handoff-spawn.log",
                    "docs/imp-plans/feat/reports/.handoff-hops",
                ],
                "2026-03-01T10:30:00",
            )

            log_dir = tempfile.mkdtemp()
            try:
                log_path = os.path.join(log_dir, ".dispatch-log")
                with open(log_path, "w") as f:
                    f.write(
                        "2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer\n"
                    )
                    f.write(
                        "2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer\n"
                    )

                findings = _checkpoint._check_verification_git_reality(
                    {3}, log_path, git_root=repo
                )
                assert findings, (
                    f"Expected finding without exclude_dir (old behavior): {findings}"
                )
                assert findings[0]["task"] == 3
            finally:
                shutil.rmtree(log_dir, ignore_errors=True)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_no_exclude_dir_does_not_add_exclude_pathspec(self):
        """Mutation-discriminating variant of test_no_exclude_dir_keeps_old_behavior
        (advisory Finding 3, Task 15 fix round).

        The original test passes identically whether `if exclude_dir:` guards
        the pathspec extension or is mutated to `if True:` — with
        exclude_dir=None, ``:(exclude)None`` is a literal path fragment that
        matches nothing real, so the commit gets flagged either way.

        This variant creates a directory literally NAMED "None" and commits
        a file inside it. Correct code (guard False, exclude_dir is the
        Python value None, not the string "None") never adds the exclude
        pathspec, so the commit still produces a finding. A `if True:`
        mutant would stringify exclude_dir into the literal pathspec
        ``:(exclude)None`` and exclude that directory — the commit would
        vanish and the test would fail, killing the mutant.
        """
        repo = _init_temp_git_repo()
        try:
            _commit_files_at(repo, ["None/inside.txt"], "2026-03-01T10:30:00")

            log_dir = tempfile.mkdtemp()
            try:
                log_path = os.path.join(log_dir, ".dispatch-log")
                with open(log_path, "w") as f:
                    f.write(
                        "2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer\n"
                    )
                    f.write(
                        "2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer\n"
                    )

                findings = _checkpoint._check_verification_git_reality(
                    {3}, log_path, git_root=repo, exclude_dir=None
                )
                assert findings, (
                    "Expected a finding even though a directory literally "
                    f"named 'None' exists — the exclude_dir guard must not "
                    f"stringify None into a pathspec: {findings}"
                )
                assert findings[0]["task"] == 3
            finally:
                shutil.rmtree(log_dir, ignore_errors=True)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_git_failure_produces_error_finding_not_silent_pass(self):
        """Round 4 structural fix: git itself failing (rc != 0) must NOT be
        swallowed into an empty findings list the way a genuinely clean
        window is — it must produce its OWN distinguishable finding shaped
        with an "error" key (not "commits"), so the caller can tell
        "couldn't look" from "found nothing" instead of reporting both as
        the same PASS.

        _check_verification_git_reality does not sanitize its exclude_dir
        argument itself (that is the caller's job, via
        _sanitize_exclude_dir in run_pre_completion) — this drives a raw
        git failure directly at the function under test, proving the
        swallow fix at its source rather than only through the CLI-level
        fallback behavior exercised elsewhere in this file.
        """
        repo = _init_temp_git_repo()
        try:
            _commit_file_at(repo, "src-file.py", "2026-03-01T10:30:00")

            log_dir = tempfile.mkdtemp()
            try:
                log_path = os.path.join(log_dir, ".dispatch-log")
                with open(log_path, "w") as f:
                    f.write(
                        "2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer\n"
                    )
                    f.write(
                        "2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer\n"
                    )

                # An exclude_dir git cannot resolve as an in-repo pathspec
                # makes `git log` exit non-zero (128, "is outside
                # repository").
                findings = _checkpoint._check_verification_git_reality(
                    {3},
                    log_path,
                    git_root=repo,
                    exclude_dir="/nonexistent/outside/feat",
                )
                assert findings, (
                    "Expected a finding when git itself fails, not a "
                    f"silent empty list: {findings}"
                )
                assert findings[0]["task"] == 3
                assert "error" in findings[0], (
                    "Expected an 'error'-shaped finding, not a "
                    f"'commits'-shaped one: {findings}"
                )
                assert "commits" not in findings[0]
                assert (
                    "128" in findings[0]["error"] or "exited" in findings[0]["error"]
                ), f"Expected the git exit code surfaced in the error: {findings}"
            finally:
                shutil.rmtree(log_dir, ignore_errors=True)
        finally:
            shutil.rmtree(repo, ignore_errors=True)


class TestCheck9ArchiveAware:
    """N27: Check 9 merges archived dispatch logs + live log."""

    def test_merged_dispatch_times_includes_archive(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        (archive / ".dispatch-log").write_text(
            "2026-01-01T00:00:00Z DISPATCH implementer task=3 type=implementer\n"
        )
        (reports / ".dispatch-log").write_text(
            "2026-01-02T00:00:00Z DISPATCH implementer task=5 type=implementer\n"
        )
        times = _checkpoint._merged_dispatch_times(str(reports / ".dispatch-log"))
        assert times == {3: "2026-01-01T00:00:00Z", 5: "2026-01-02T00:00:00Z"}

    def test_merged_dispatch_times_live_overwrites(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        (archive / ".dispatch-log").write_text(
            "2026-01-01T00:00:00Z DISPATCH implementer task=3 type=implementer\n"
        )
        (reports / ".dispatch-log").write_text(
            "2026-02-02T00:00:00Z DISPATCH implementer task=3 type=implementer\n"
        )
        times = _checkpoint._merged_dispatch_times(str(reports / ".dispatch-log"))
        assert times == {3: "2026-02-02T00:00:00Z"}  # live (later) wins

    def test_merged_dispatch_times_ignores_fix_lines(self, tmp_path):
        # N26/N27 contract: type=fix / type=fix-unattributed never open a window.
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / ".dispatch-log").write_text(
            "2026-01-01T00:00:00Z DISPATCH fix task=3 type=fix\n"
            "2026-01-01T00:00:01Z DISPATCH adhoc type=fix-unattributed\n"
        )
        times = _checkpoint._merged_dispatch_times(str(reports / ".dispatch-log"))
        assert times == {}

    def test_archived_window_file_modification_fails(self):
        """A verification task dispatched ONLY in an archived log, with a
        file-modifying commit inside its window, FAILs after the merge (today
        the live-only read silently skips it)."""
        repo = _init_temp_git_repo()
        try:
            _commit_file_at(repo, "modified.txt", "2026-03-01T10:30:00")
            log_dir = tempfile.mkdtemp()
            try:
                reports = os.path.join(log_dir, "reports")
                archive = os.path.join(reports, "archive-Mod1")
                os.makedirs(archive)
                with open(os.path.join(archive, ".dispatch-log"), "w") as f:
                    f.write(
                        "2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer\n"
                    )
                    f.write(
                        "2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer\n"
                    )
                live = os.path.join(reports, ".dispatch-log")
                open(live, "w").close()  # truncated live log (post-transition)
                findings = _checkpoint._check_verification_git_reality(
                    {3}, live, git_root=repo
                )
                assert findings, f"Expected finding from archived window: {findings}"
                assert findings[0]["task"] == 3
            finally:
                shutil.rmtree(log_dir, ignore_errors=True)
        finally:
            shutil.rmtree(repo, ignore_errors=True)


class TestReviewTiersArchiveAware:
    """N27: _review_tiers_per_task globs archive-*/ with live-wins."""

    def test_review_tiers_includes_archived(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        (archive / "task-001-quality-review-minimum-tier.md").write_text("x")
        (archive / "task-002-quality-review-minimum-tier.md").write_text("x")
        (archive / "task-003-quality-review-minimum-tier.md").write_text("x")
        (reports / "task-004-quality-review.md").write_text("x")
        tiers = dict(_checkpoint._review_tiers_per_task(str(reports), "quality-review"))
        assert tiers == {1: True, 2: True, 3: True, 4: False}

    def test_review_tiers_live_wins_over_archive(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        # Same task id: archived as minimum, re-reviewed live as full.
        (archive / "task-005-quality-review-minimum-tier.md").write_text("x")
        (reports / "task-005-quality-review.md").write_text("x")
        tiers = dict(_checkpoint._review_tiers_per_task(str(reports), "quality-review"))
        assert tiers[5] is False  # live full wins over archived minimum

    def test_review_tiers_partner_archive(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        (archive / "partner-review-001-minimum-tier.md").write_text("x")
        (reports / "partner-review-002.md").write_text("x")
        tiers = dict(_checkpoint._review_tiers_per_task(str(reports), "partner-review"))
        assert tiers == {1: True, 2: False}


# ---------------------------------------------------------------------------
# Tests: run_pre_completion's OWN derivation of exclude_dir_for_check /
# git_root_for_check (Task 15 fix round — spec review Finding 1 + Finding 2)
#
# TestGitRealityCheck above only exercises _check_verification_git_reality()
# directly with a hand-supplied exclude_dir string. Nothing there proves the
# CLI's own "elif args.reports_dir:" / "if getattr(args, 'manifest', ...)"
# derivation wires it correctly. These tests drive controller-checkpoint.py
# as a real subprocess against a real temp git repo, in BOTH modes.
# ---------------------------------------------------------------------------

from sdd_session import TIER_PROFILES  # noqa: E402


def _verification_plan_two_tasks() -> str:
    """2-task plan: Task 0 implementation, Task 1 task_type:verification.

    Matches the _plan_with_task_types(2, verification_task_ids=[1]) shape
    used elsewhere in this file (frontmatter tasks[] + matching ### Task N
    headers), inlined here so this section has no ordering dependency on
    TestVerificationRatioCheck's helper.
    """
    return _plan_with_task_types(2, verification_task_ids=[1])


def _init_git_repo_at(path):
    """git init + local identity at an existing directory (Path or str)."""
    path = str(path)
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", path, "config", "user.email", "test@example.com"], check=True
    )
    subprocess.run(["git", "-C", path, "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", path, "config", "commit.gpgsign", "false"], check=True)


def _build_verification_workspace(repo_root):
    """Lay out docs/imp-plans/feat/{reports/,plan.md,deviations.md} under
    repo_root (already git-init'd), with a dispatch log opening an
    OPEN-ENDED verification window for task 1 (only one DISPATCH line, so
    end_ts is None and the window covers "now" — matches how
    _check_verification_git_reality treats the last dispatched task).

    Returns (feat_dir, reports_dir, plan_path, dev_path) as plain str paths.
    """
    feat_dir = os.path.join(repo_root, "docs", "imp-plans", "feat")
    reports_dir = os.path.join(feat_dir, "reports")
    os.makedirs(reports_dir)

    plan_path = os.path.join(feat_dir, "plan.md")
    with open(plan_path, "w") as f:
        f.write(_verification_plan_two_tasks())

    dev_path = os.path.join(feat_dir, "deviations.md")
    with open(dev_path, "w") as f:
        f.write("")

    with open(os.path.join(reports_dir, ".dispatch-log"), "w") as f:
        f.write("2026-03-01T10:00:00 DISPATCH implementer task=1 type=implementer\n")

    return feat_dir, reports_dir, plan_path, dev_path


def _run_pre_completion_cli(
    plan_file=None, deviations_file=None, reports_dir=None, manifest=None, cwd=None
):
    """Invoke controller-checkpoint.py --phase pre-completion as a real
    subprocess, mirroring run_pre_completion()'s own invocation above but
    adding --manifest support and a controllable subprocess cwd (needed for
    the Finding-2 regression test, which must prove the derivation is
    independent of the process's actual OS cwd)."""
    cmd = [sys.executable, SCRIPT_PATH, "--phase", "pre-completion"]
    if manifest:
        cmd.extend(["--manifest", str(manifest)])
    if plan_file:
        cmd.extend(["--plan-file", str(plan_file)])
    cmd.extend(
        ["--deviations-file", str(deviations_file), "--reports-dir", str(reports_dir)]
    )
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=cwd)
    output = json.loads(result.stdout) if result.stdout.strip() else {}
    return {"exit_code": result.returncode, "output": output, "stderr": result.stderr}


def _write_manifest(repo_root, feat_dir, reports_dir, plan_path, dev_path):
    """Write a standard-tier .sdd-session.json manifest whose paths are
    git-root-relative (Decision 17 / CLAUDE.md "Manifest is git-root-relative").
    Mirrors setup_checkpoint_workspace() in test_controller_checkpoint_stale.py.
    """
    profile = TIER_PROFILES["standard"]
    manifest = {
        "schema_version": 1,
        "tier": "standard",
        "paths": {
            "feature_dir": os.path.relpath(feat_dir, repo_root),
            "reports_dir": os.path.relpath(reports_dir, repo_root),
            "dispatch_log": os.path.relpath(
                os.path.join(reports_dir, ".dispatch-log"), repo_root
            ),
            "deviations_file": os.path.relpath(dev_path, repo_root),
        },
        "plan_file": os.path.relpath(plan_path, repo_root),
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
    manifest_path = os.path.join(feat_dir, ".sdd-session.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path


class TestGitRealityCallerDerivationReportsDirMode:
    """Finding 1: run_pre_completion's `elif args.reports_dir:` derivation of
    exclude_dir_for_check / git_root_for_check, exercised via the real CLI —
    no --manifest."""

    def test_bookkeeping_commit_passes(self, tmp_path):
        """A commit inside the window touching ONLY feature-dir bookkeeping
        (reports/handoff-spawn.log, reports/.handoff-hops) → Check 9 PASSes,
        proving the exclude wiring works end-to-end through the real CLI."""
        repo_root = str(tmp_path)
        _init_git_repo_at(repo_root)
        feat_dir, reports_dir, plan_path, dev_path = _build_verification_workspace(
            repo_root
        )
        _commit_files_at(
            repo_root,
            [
                "docs/imp-plans/feat/reports/handoff-spawn.log",
                "docs/imp-plans/feat/reports/.handoff-hops",
            ],
            "2026-03-01T10:30:00",
        )

        result = _run_pre_completion_cli(
            plan_file=plan_path, deviations_file=dev_path, reports_dir=reports_dir
        )
        check = result["output"].get("checks", {}).get("verification_git_reality", {})
        assert check.get("status") == "PASS", (
            f"Expected PASS (bookkeeping-only commit excluded): {check}, "
            f"stderr={result['stderr']}"
        )
        # Round 4 fix, Step 4 (MU3 coverage gap from the round-3 spec
        # review): nothing previously pinned the NEGATIVE of
        # exclude_dir_narrowing_failed — a hardcoded True there would leave
        # every passing bookkeeping-commit test green with a spurious
        # narrowing-failed note in `detail`. This is a normal layout where
        # narrowing genuinely succeeds, so the note must be absent.
        assert "could not exclude bookkeeping commits" not in check.get("detail", ""), (
            f"Unexpected narrowing-failed note on a successful-narrowing PASS: {check}"
        )

    def test_source_commit_fails(self, tmp_path):
        """A commit inside the window touching a SOURCE file OUTSIDE the
        feature dir → Check 9 FAILs, proving exclude_dir doesn't
        over-broadly exempt everything."""
        repo_root = str(tmp_path)
        _init_git_repo_at(repo_root)
        feat_dir, reports_dir, plan_path, dev_path = _build_verification_workspace(
            repo_root
        )
        _commit_files_at(repo_root, ["src/feature.py"], "2026-03-01T10:30:00")

        result = _run_pre_completion_cli(
            plan_file=plan_path, deviations_file=dev_path, reports_dir=reports_dir
        )
        check = result["output"].get("checks", {}).get("verification_git_reality", {})
        assert check.get("status") == "FAIL", (
            f"Expected FAIL (source file outside feature dir): {check}, "
            f"stderr={result['stderr']}"
        )
        assert "verification_git_reality" in result["output"].get("blockers", [])


class TestGitRealityCallerDerivationManifestMode:
    """Finding 1: run_pre_completion's `if getattr(args, "manifest", ...)`
    derivation of exclude_dir_for_check / git_root_for_check, exercised via
    the real CLI with --manifest."""

    def test_bookkeeping_commit_passes(self, tmp_path):
        repo_root = str(tmp_path)
        _init_git_repo_at(repo_root)
        feat_dir, reports_dir, plan_path, dev_path = _build_verification_workspace(
            repo_root
        )
        manifest_path = _write_manifest(
            repo_root, feat_dir, reports_dir, plan_path, dev_path
        )
        _commit_files_at(
            repo_root,
            [
                "docs/imp-plans/feat/reports/handoff-spawn.log",
                "docs/imp-plans/feat/reports/.handoff-hops",
            ],
            "2026-03-01T10:30:00",
        )

        result = _run_pre_completion_cli(
            manifest=manifest_path, deviations_file=dev_path, reports_dir=reports_dir
        )
        check = result["output"].get("checks", {}).get("verification_git_reality", {})
        assert check.get("status") == "PASS", (
            f"Expected PASS (bookkeeping-only commit excluded): {check}, "
            f"stderr={result['stderr']}"
        )

    def test_source_commit_fails(self, tmp_path):
        repo_root = str(tmp_path)
        _init_git_repo_at(repo_root)
        feat_dir, reports_dir, plan_path, dev_path = _build_verification_workspace(
            repo_root
        )
        manifest_path = _write_manifest(
            repo_root, feat_dir, reports_dir, plan_path, dev_path
        )
        _commit_files_at(repo_root, ["src/feature.py"], "2026-03-01T10:30:00")

        result = _run_pre_completion_cli(
            manifest=manifest_path, deviations_file=dev_path, reports_dir=reports_dir
        )
        check = result["output"].get("checks", {}).get("verification_git_reality", {})
        assert check.get("status") == "FAIL", (
            f"Expected FAIL (source file outside feature dir): {check}, "
            f"stderr={result['stderr']}"
        )
        assert "verification_git_reality" in result["output"].get("blockers", [])


class TestGitRealityCwdIndependence:
    """Finding 2 regression test: before the fix, reports_dir-mode left
    git_root_for_check as None, so _git_run invoked git WITHOUT -C and the
    `-- . :(exclude)<dir>` pathspec resolved against the PROCESS's actual OS
    cwd rather than the repo root. When that cwd was outside the repo
    entirely (as in a subprocess test harness, or any caller invoked from a
    directory other than the repo root), `git log -- .` silently found
    nothing and Check 9 spuriously PASSED — a fail-closed integrity gate
    going fail-open.

    This test drives the exact same source-file-outside-feature-dir scenario
    as TestGitRealityCallerDerivationReportsDirMode.test_source_commit_fails,
    but pins the subprocess's cwd to an unrelated temp directory that is NOT
    the repo root (and not even inside the repo). Before the fix this
    spuriously PASSED; after the fix it must still FAIL.
    """

    def test_source_commit_still_fails_with_unrelated_process_cwd(self, tmp_path):
        repo_root = str(tmp_path / "repo")
        os.makedirs(repo_root)
        _init_git_repo_at(repo_root)
        feat_dir, reports_dir, plan_path, dev_path = _build_verification_workspace(
            repo_root
        )
        _commit_files_at(repo_root, ["src/feature.py"], "2026-03-01T10:30:00")

        # A directory that shares no ancestry with repo_root at all — the
        # scenario the spec reviewer used to empirically prove the bug.
        unrelated_cwd = str(tmp_path / "unrelated-cwd")
        os.makedirs(unrelated_cwd)

        result = _run_pre_completion_cli(
            plan_file=plan_path,
            deviations_file=dev_path,
            reports_dir=reports_dir,
            cwd=unrelated_cwd,
        )
        check = result["output"].get("checks", {}).get("verification_git_reality", {})
        assert check.get("status") == "FAIL", (
            "Expected FAIL regardless of process cwd (fail-closed) — a PASS "
            f"here reproduces the Finding 2 fail-open bug: {check}, "
            f"stderr={result['stderr']}"
        )
        assert "verification_git_reality" in result["output"].get("blockers", [])


# ---------------------------------------------------------------------------
# Tests: Task 15 fix round 3 — quality review Critical findings C1 + C2
# (docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-015-quality-review.md)
# ---------------------------------------------------------------------------


class TestGitRealityUnresolvedTempRepoPath:
    """C1: the round-2 fix's realpath() (not abspath()) correction on BOTH
    sides of the reports_dir-mode relpath call has zero coverage from the
    existing caller-derivation tests, because pytest's tmp_path fixture is
    ALREADY realpath-canonicalized on this machine
    (os.path.realpath(tmp_path) == tmp_path) — unlike a raw
    tempfile.mkdtemp() call, which on macOS returns the UNRESOLVED
    /var/folders/... form (realpath resolves it to /private/var/folders/...).
    A workspace built under a directly-created mkdtemp() repo (mirroring
    _init_temp_git_repo(), used elsewhere in this file exactly to get this
    unresolved form) exercises the discrepancy.

    test_bookkeeping_commit_passes_unresolved_repo_path is the mutation
    killer: reverting realpath to abspath makes the two relpath operands
    share no common path prefix at all (/var/folders/... vs
    /private/var/folders/...), so the derived exclude_dir candidate comes
    out "../../.../var/folders/.../docs/imp-plans/feat" — which
    _sanitize_exclude_dir correctly rejects (leading ".."), falling back to
    an UNNARROWED Check 9 that then flags the bookkeeping-only commit as a
    violation (FAIL instead of the expected PASS). Empirically confirmed
    against a hand-mutated copy of this fix during implementation.
    test_source_commit_fails_unresolved_repo_path does NOT kill this
    mutation on its own (both shipped and mutant code correctly FAIL a real
    source commit — under the mutant via the same unnarrowed fallback) but
    is kept as a straightforward fail-closed sanity check.
    """

    def test_bookkeeping_commit_passes_unresolved_repo_path(self):
        repo_root = _init_temp_git_repo()
        try:
            feat_dir, reports_dir, plan_path, dev_path = _build_verification_workspace(
                repo_root
            )
            _commit_files_at(
                repo_root,
                [
                    "docs/imp-plans/feat/reports/handoff-spawn.log",
                    "docs/imp-plans/feat/reports/.handoff-hops",
                ],
                "2026-03-01T10:30:00",
            )

            result = _run_pre_completion_cli(
                plan_file=plan_path, deviations_file=dev_path, reports_dir=reports_dir
            )
            check = (
                result["output"].get("checks", {}).get("verification_git_reality", {})
            )
            assert check.get("status") == "PASS", (
                "Expected PASS (bookkeeping-only commit excluded) on an "
                "unresolved-symlink repo path — a FAIL here reproduces the "
                "C1 realpath-vs-abspath regression: mismatched operands "
                "produce a malformed '..'-prefixed exclude_dir that gets "
                f"rejected, disabling narrowing entirely: {check}, "
                f"stderr={result['stderr']}"
            )

        finally:
            shutil.rmtree(repo_root, ignore_errors=True)

    def test_source_commit_fails_unresolved_repo_path(self):
        repo_root = _init_temp_git_repo()
        try:
            feat_dir, reports_dir, plan_path, dev_path = _build_verification_workspace(
                repo_root
            )
            _commit_files_at(repo_root, ["src/feature.py"], "2026-03-01T10:30:00")

            result = _run_pre_completion_cli(
                plan_file=plan_path, deviations_file=dev_path, reports_dir=reports_dir
            )
            check = (
                result["output"].get("checks", {}).get("verification_git_reality", {})
            )
            assert check.get("status") == "FAIL", (
                "Expected FAIL on an unresolved-symlink repo path: "
                f"{check}, stderr={result['stderr']}"
            )
            assert "verification_git_reality" in result["output"].get("blockers", [])
        finally:
            shutil.rmtree(repo_root, ignore_errors=True)


def _build_verification_workspace_at_root(repo_root):
    """Like _build_verification_workspace, but lays reports/, plan.md, and
    deviations.md directly at repo_root — i.e. reports_dir's PARENT (the
    feature dir) IS the git root itself. --reports-dir is free-form and
    unvalidated, so nothing stops a caller from pointing it at
    <git_root>/reports; this is the exact layout that makes
    relpath(feature_dir, git_root) == "." (Critical Finding C2).

    Returns (feat_dir, reports_dir, plan_path, dev_path) as plain str paths.
    """
    feat_dir = repo_root
    reports_dir = os.path.join(feat_dir, "reports")
    os.makedirs(reports_dir)

    plan_path = os.path.join(feat_dir, "plan.md")
    with open(plan_path, "w") as f:
        f.write(_verification_plan_two_tasks())

    dev_path = os.path.join(feat_dir, "deviations.md")
    with open(dev_path, "w") as f:
        f.write("")

    with open(os.path.join(reports_dir, ".dispatch-log"), "w") as f:
        f.write("2026-03-01T10:00:00 DISPATCH implementer task=1 type=implementer\n")

    return feat_dir, reports_dir, plan_path, dev_path


class TestGitRealityExcludeDirNormalizesToRoot:
    """C2: when reports_dir's parent (the feature dir) IS the git root
    itself, relpath(feature_dir, git_root) yields ".", and an unsanitized
    `git log -- . :(exclude).` excludes the ENTIRE repository (rc=0, empty
    stdout) — a full, silent fail-open, not merely a partial narrowing.
    _sanitize_exclude_dir must reject this candidate so Check 9 falls back
    to running unnarrowed and still sees real source-file commits. Both
    branches share the fix (manifest mode has the identical latent shape via
    feature_dir: ".") so both are exercised here."""

    def test_source_commit_fails_reports_dir_mode(self, tmp_path):
        repo_root = str(tmp_path)
        _init_git_repo_at(repo_root)
        feat_dir, reports_dir, plan_path, dev_path = (
            _build_verification_workspace_at_root(repo_root)
        )
        _commit_files_at(repo_root, ["src/feature.py"], "2026-03-01T10:30:00")

        result = _run_pre_completion_cli(
            plan_file=plan_path, deviations_file=dev_path, reports_dir=reports_dir
        )
        check = result["output"].get("checks", {}).get("verification_git_reality", {})
        assert check.get("status") == "FAIL", (
            "Expected FAIL — reports_dir's parent resolves to git root, so "
            "an unsanitized exclude_dir of '.' would exclude the WHOLE repo: "
            f"{check}, stderr={result['stderr']}"
        )
        assert "verification_git_reality" in result["output"].get("blockers", [])
        assert "resolves to the git root" in check.get("detail", ""), (
            f"Expected the narrowing-failed note surfaced in check detail: {check}"
        )

    def test_source_commit_fails_manifest_mode(self, tmp_path):
        repo_root = str(tmp_path)
        _init_git_repo_at(repo_root)
        feat_dir, reports_dir, plan_path, dev_path = (
            _build_verification_workspace_at_root(repo_root)
        )
        manifest_path = _write_manifest(
            repo_root, feat_dir, reports_dir, plan_path, dev_path
        )
        _commit_files_at(repo_root, ["src/feature.py"], "2026-03-01T10:30:00")

        result = _run_pre_completion_cli(
            manifest=manifest_path, deviations_file=dev_path, reports_dir=reports_dir
        )
        check = result["output"].get("checks", {}).get("verification_git_reality", {})
        assert check.get("status") == "FAIL", (
            "Expected FAIL — manifest feature_dir resolves to '.' (git "
            f"root), the same latent shape as reports_dir mode: {check}, "
            f"stderr={result['stderr']}"
        )
        assert "verification_git_reality" in result["output"].get("blockers", [])
        assert "resolves to the git root" in check.get("detail", ""), (
            f"Expected the narrowing-failed note surfaced in check detail: {check}"
        )


# ---------------------------------------------------------------------------
# Tests: Task 15 fix round 4 — quality re-review findings I-A + I-B
# (structural fix for the git-failure swallow in
# _check_verification_git_reality, plus the isabs guard in
# _sanitize_exclude_dir and its zero-coverage ".." guard)
# ---------------------------------------------------------------------------


class TestGitRealityExcludeDirRejectsTraversalManifestMode:
    """I-B: the ".."-prefix guard in _sanitize_exclude_dir is load-bearing
    and had ZERO shipped-code coverage — no existing test ever produces a
    ".."-prefixed candidate under shipped code (only under a hand-applied
    mutant), so the clause could be silently deleted and every existing
    test would stay green.

    A manifest feature_dir of "../outside-the-repo/feat" is exactly the
    shape the guard exists to reject: _sanitize_exclude_dir must reject it
    (reason "resolves outside the repository"), Check 9 falls back to
    running unnarrowed, and a real source-file commit is still caught.

    Discriminates from the round-4 structural fix's own safety net: if the
    ".." guard were removed, the unsanitized candidate would reach the git
    pathspec directly, `git log` would exit 128 ("is outside repository"),
    and the round-4 fix in _check_verification_git_reality would surface
    THAT as an "error"-shaped finding ("could not verify — git log exited
    128: ...") with no narrowing note — still a FAIL, but a different
    detail message. Asserting on "file modifications detected" (not
    "could not verify") and on the narrowing note being present pins the
    guard's specific behavior, not just the fallback safety net's.
    """

    def test_source_commit_fails_traversal_feature_dir(self, tmp_path):
        repo_root = str(tmp_path)
        _init_git_repo_at(repo_root)
        feat_dir, reports_dir, plan_path, dev_path = _build_verification_workspace(
            repo_root
        )
        manifest_path = _write_manifest(
            repo_root, feat_dir, reports_dir, plan_path, dev_path
        )
        # Overwrite feature_dir with a ".."-prefixed candidate after the
        # manifest is written — reports_dir/dispatch_log stay correct so
        # Check 9 still finds the real dispatch log; only the exclude_dir
        # derivation input is malformed.
        with open(manifest_path) as f:
            manifest = json.load(f)
        manifest["paths"]["feature_dir"] = "../outside-the-repo/feat"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        _commit_files_at(repo_root, ["src/feature.py"], "2026-03-01T10:30:00")

        result = _run_pre_completion_cli(
            manifest=manifest_path, deviations_file=dev_path, reports_dir=reports_dir
        )
        check = result["output"].get("checks", {}).get("verification_git_reality", {})
        assert check.get("status") == "FAIL", (
            "Expected FAIL — a '..'-prefixed feature_dir must be rejected "
            "by _sanitize_exclude_dir, falling back to unnarrowed Check 9, "
            f"which must still catch the source commit: {check}, "
            f"stderr={result['stderr']}"
        )
        assert "verification_git_reality" in result["output"].get("blockers", [])
        detail = check.get("detail", "")
        assert "resolves outside the repository" in detail, (
            f"Expected the narrowing-failed note to name the real cause: {check}"
        )
        assert "file modifications detected" in detail, (
            "Expected the unnarrowed fallback to catch the source commit "
            f"directly (not via the git-error path): {check}"
        )
        assert "could not verify" not in detail, (
            f"A working '..' guard means git never sees the bad pathspec: {check}"
        )


class TestGitRealityExcludeDirRejectsAbsoluteOutOfRepoManifestMode:
    """I-A (round-4 quality re-review): an absolute, out-of-repo
    feature_dir reached the Check 9 git pathspec and silently certified a
    modified repo as clean — `git log -- . ':(exclude)/abs/outside'` exits
    128, and the pre-round-4 gate collapsed "git failed" and "found
    nothing" into the same PASS. Reachable via materialize-manifest.py's
    git_root_relative(), which only WARNS (doesn't reject) an
    absolute/out-of-repo feature_dir.

    Proves the round-4 Step 2 defense-in-depth fix specifically (the
    explicit os.path.isabs guard in _sanitize_exclude_dir), not merely the
    Step 1 structural fallback: asserts the narrowing-failed note names the
    real cause and that Check 9 catches the commit via the unnarrowed
    fallback (not via the git-error path), mirroring the discrimination in
    TestGitRealityExcludeDirRejectsTraversalManifestMode above.
    """

    def test_source_commit_fails_absolute_feature_dir(self, tmp_path):
        repo_root = str(tmp_path)
        _init_git_repo_at(repo_root)
        feat_dir, reports_dir, plan_path, dev_path = _build_verification_workspace(
            repo_root
        )
        manifest_path = _write_manifest(
            repo_root, feat_dir, reports_dir, plan_path, dev_path
        )
        with open(manifest_path) as f:
            manifest = json.load(f)
        manifest["paths"]["feature_dir"] = "/nonexistent/outside/feat"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        _commit_files_at(repo_root, ["src/feature.py"], "2026-03-01T10:30:00")

        result = _run_pre_completion_cli(
            manifest=manifest_path, deviations_file=dev_path, reports_dir=reports_dir
        )
        check = result["output"].get("checks", {}).get("verification_git_reality", {})
        assert check.get("status") == "FAIL", (
            "Expected FAIL — an absolute out-of-repo feature_dir must be "
            "rejected by _sanitize_exclude_dir's isabs guard, falling back "
            f"to unnarrowed Check 9, which must still catch the source "
            f"commit: {check}, stderr={result['stderr']}"
        )
        assert "verification_git_reality" in result["output"].get("blockers", [])
        detail = check.get("detail", "")
        assert "resolves outside the repository" in detail, (
            f"Expected the narrowing-failed note to name the real cause: {check}"
        )
        assert "file modifications detected" in detail, (
            "Expected the unnarrowed fallback to catch the source commit "
            f"directly (not via the git-error path): {check}"
        )
        assert "could not verify" not in detail, (
            f"A working isabs guard means git never sees the bad pathspec: {check}"
        )
