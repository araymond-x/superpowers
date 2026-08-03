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
        tiers = dict(
            _checkpoint._review_tiers_per_task(str(reports), "quality-review")
        )
        assert tiers == {1: True, 2: True, 3: True, 4: False}

    def test_review_tiers_live_wins_over_archive(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        # Same task id: archived as minimum, re-reviewed live as full.
        (archive / "task-005-quality-review-minimum-tier.md").write_text("x")
        (reports / "task-005-quality-review.md").write_text("x")
        tiers = dict(
            _checkpoint._review_tiers_per_task(str(reports), "quality-review")
        )
        assert tiers[5] is False  # live full wins over archived minimum

    def test_review_tiers_partner_archive(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        (archive / "partner-review-001-minimum-tier.md").write_text("x")
        (reports / "partner-review-002.md").write_text("x")
        tiers = dict(
            _checkpoint._review_tiers_per_task(str(reports), "partner-review")
        )
        assert tiers == {1: True, 2: False}
