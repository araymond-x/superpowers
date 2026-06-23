"""Item 1/3/5: 3-stage manifest-mode classification + non-manifest guard.
Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v
"""
import os
import subprocess

from sdd_test_helpers import (
    create_checkpoint_file,
    make_hook_input,
    setup_full_sdd_workspace,
    setup_sdd_workspace,
)

HOOK_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh",
))


def run_hook(stdin_data):
    return subprocess.run(["bash", HOOK_PATH], input=stdin_data,
                          capture_output=True, text=True, timeout=10)


def _write_frontmatter_plan(tmpdir, total_tasks, task_types):
    """Overwrite docs/imp-plans/plan.md (the manifest's plan_file) with a YAML
    frontmatter plan that declares task_type per task id.

    The helpers' manifest points plan_file at docs/imp-plans/plan.md and leaves
    active_module_file null, so the hook's EFFECTIVE_PLAN_FILE resolves to this
    file and get_task_type reads its frontmatter. The default helper plans are
    frontmatter-LESS (every task reads back as "implementation"), which would
    make a verification test pass vacuously — this rewrite is what makes the
    fixture actually exercise task_type.

    Keeps "### Task N" markdown headers (token estimation needs them) and
    "**Source Contracts:** None" (so the Task 0 source-contract gate stays off).

    Args:
        tmpdir: SDD workspace root (str).
        total_tasks: number of tasks to declare (ids 0..total_tasks-1).
        task_types: dict {task_id: "verification"|"implementation"}; ids absent
            from the dict default to "implementation".
    """
    plan_path = os.path.join(tmpdir, "docs", "imp-plans", "plan.md")
    tasks_yaml = "".join(
        f"  - id: {i}\n    task_type: {task_types.get(i, 'implementation')}\n"
        for i in range(total_tasks)
    )
    body = "".join(
        f"### Task {i} -- Step {i}\n- [ ] Do step {i}\n\n" for i in range(total_tasks)
    )
    with open(plan_path, "w") as f:
        f.write(
            "---\nschema_version: 1\ntasks:\n" + tasks_yaml + "---\n\n"
            "# Implementation Plan\n\n**Source Contracts:** None\n\n" + body
        )


def test_general_purpose_reviewer_is_logged(tmp_path):
    # Item 1 bug: a general-purpose reviewer must be logged, not passed through.
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=5)
    log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
    if os.path.exists(log_path):
        os.remove(log_path)
    result = run_hook(make_hook_input(
        description="Review task 2 spec compliance",
        subagent_type="general-purpose", cwd=tmpdir))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert os.path.isfile(log_path) and "task=2" in open(log_path).read()


def test_general_purpose_implementer_is_enforced(tmp_path):
    # Task 0 reports missing -> implementer for task 1 must be blocked.
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=3)
    result = run_hook(make_hook_input(
        description="Implement task 1", prompt="You are implementing task 1",
        subagent_type="general-purpose", cwd=tmpdir))
    assert result.returncode == 2, f"stderr: {result.stderr}"


def test_adhoc_dispatch_passes_through(tmp_path):
    # Non-reviewer, non-implementer -> Stage 3 allow, no log entry.
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=3)
    log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
    before = open(log_path).read() if os.path.exists(log_path) else ""
    result = run_hook(make_hook_input(
        description="Investigate the database schema",
        prompt="Look at the schema", subagent_type="general-purpose", cwd=tmpdir))
    after = open(log_path).read() if os.path.exists(log_path) else ""
    assert result.returncode == 0 and after == before, f"stderr: {result.stderr}"


def test_no_manifest_no_artifacts_allowed(tmp_path):
    tmpdir = str(tmp_path)
    subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
    result = run_hook(make_hook_input(
        description="Implement task 1", prompt="You are implementing task 1", cwd=tmpdir))
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_no_manifest_with_artifacts_blocked(tmp_path):
    tmpdir = str(tmp_path)
    subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
    os.makedirs(os.path.join(tmpdir, "docs", "imp-plans", "x", "reports"))
    with open(os.path.join(tmpdir, ".active-feature"), "w") as f:
        f.write("docs/imp-plans/x")
    result = run_hook(make_hook_input(
        description="Implement task 1", prompt="You are implementing task 1", cwd=tmpdir))
    assert result.returncode == 2 and "manifest" in result.stderr.lower(), f"stderr: {result.stderr}"


class TestValidationErrorSurfacing:
    def test_validation_error_excerpt_inline(self, tmp_path):
        """When the prev task's implementer report fails validation, the hook
        error must include excerpt lines from validate-report.py, not just the exit code."""
        tmpdir = str(tmp_path)
        setup_sdd_workspace(tmpdir, task_count=3)
        reports_dir = os.path.join(tmpdir, "reports")
        # Task 0 report present but with BROKEN frontmatter (fails Pydantic validation),
        # large enough to pass the size gate so validation actually runs.
        with open(os.path.join(reports_dir, "task-000-implementer-report.md"), "w") as f:
            f.write("---\nschema_version: 1\ntask_id: not_an_int\nstatus: BOGUS\n---\n\n"
                    + "Body padding to exceed the 50-byte size gate. " * 5)
        create_checkpoint_file(tmpdir, task_number=1)
        hook_input = make_hook_input(
            description="Implement task 1", prompt="You are implementing task 1", cwd=tmpdir,
        )
        result = run_hook(hook_input)
        assert result.returncode == 2, f"stderr: {result.stderr}"
        # The excerpt must surface the FAILING FIELD NAME, not just the banner.
        # (task_id: not_an_int is the first failing field, at output line 6 —
        # reachable only with head -n 12, not head -n 5.) Assert on task_id
        # specifically: "status" would spuriously match the trailing JSON line.
        low = result.stderr.lower()
        assert "validation" in low and "task_id" in low, \
            f"Expected an inline validation excerpt naming task_id. stderr: {result.stderr}"


class TestImplementerDispatchLogging:
    """Stage 2 implementer detection logs to the dispatch log.

    The implementer log line is written in Stage 2 BEFORE the enforcement
    checks run, so it appears even when the hook ultimately blocks (exit 2).
    Downstream consumers (git reality check, Task 5) rely on these timestamps.
    """

    @staticmethod
    def _log_lines(tmpdir):
        log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
        if not os.path.exists(log_path):
            return []
        with open(log_path) as f:
            return f.read().splitlines()

    def test_implementer_dispatch_logged_even_when_blocked(self, tmp_path):
        # Task 0 reports missing -> implementer for task 1 is BLOCKED (exit 2),
        # but the Stage-2 log line must still be written before the gate fires.
        tmpdir = str(tmp_path)
        setup_sdd_workspace(tmpdir, task_count=3)
        result = run_hook(make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1", cwd=tmpdir))
        assert result.returncode == 2, f"stderr: {result.stderr}"
        lines = self._log_lines(tmpdir)
        assert any(
            "DISPATCH implementer task=1 type=implementer" in line for line in lines
        ), f"No implementer log line written. log: {lines}"

    def test_implementer_dispatch_logged_when_allowed(self, tmp_path):
        # Full workspace: task 0 complete, all gates satisfied for task 1.
        # Hook ALLOWS (exit 0) and the implementer line is present.
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=3, completed_tasks=1)
        result = run_hook(make_hook_input(
            description="Implement task 1",
            prompt="You are implementing task 1", cwd=tmpdir))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = self._log_lines(tmpdir)
        assert any(
            "DISPATCH implementer task=1 type=implementer" in line for line in lines
        ), f"No implementer log line written. log: {lines}"

    def test_implementer_log_line_exact_format(self, tmp_path):
        # The writer format is the reader contract for Task 5's git reality check:
        #   <ISO-8601> DISPATCH implementer task=N type=implementer
        # Assert the full shape via the exact regex the reader uses.
        import re
        tmpdir = str(tmp_path)
        setup_sdd_workspace(tmpdir, task_count=3)
        run_hook(make_hook_input(
            description="Implement task 2",
            prompt="You are implementing task 2", cwd=tmpdir))
        lines = self._log_lines(tmpdir)
        pattern = re.compile(
            r"^\S+\s+DISPATCH\s+implementer\s+task=2\s+type=implementer$"
        )
        assert any(pattern.match(line) for line in lines), \
            f"Implementer line does not match the reader contract. log: {lines}"

    def test_prompt_only_implementer_is_logged(self, tmp_path):
        # Implementer detected via PROMPT (not description) is logged too.
        tmpdir = str(tmp_path)
        setup_sdd_workspace(tmpdir, task_count=3)
        run_hook(make_hook_input(
            description="Run the next step",
            prompt="You are implementing task 1 of the plan.", cwd=tmpdir))
        lines = self._log_lines(tmpdir)
        assert any(
            "DISPATCH implementer task=1 type=implementer" in line for line in lines
        ), f"Prompt-triggered implementer not logged. log: {lines}"


class TestVerificationTaskCheckSkipping:
    """Task 3: a verification task is dispatched as an implementer (still logged,
    still files an implementer report) but is exempt from the review cycle.

    - Current task = verification  -> Check 5d (partner review) skipped.
    - Previous task = verification -> Checks 4b (spec/quality review reports) and
      4c (dispatch provenance) skipped for that prior task.
    - Implementation tasks are completely unchanged (positive control).

    Fixtures use a FULL workspace (all prerequisites met) with total_tasks=8 so the
    midpoint (4) is past task 2 — the context-summary gate (Check 6b) does not fire.
    The manifest's plan_file is then rewritten WITH frontmatter so get_task_type
    reads real task_type values (see _write_frontmatter_plan). The implementation
    positive control (identical setup, task_type implementation, flips ALLOW->BLOCK)
    proves the fixtures are non-vacuous.
    """

    TOTAL = 8
    COMPLETED = 2  # dispatch target is task 2; previous task is task 1

    def test_current_verification_skips_partner_review(self, tmp_path):
        # CURRENT task 2 declared verification; its partner-review file is absent.
        # Check 5d must be skipped -> ALLOW.
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=self.TOTAL, completed_tasks=self.COMPLETED)
        _write_frontmatter_plan(tmpdir, self.TOTAL, {2: "verification"})
        os.remove(os.path.join(tmpdir, "reports", "partner-review-002.md"))
        result = run_hook(make_hook_input(
            description="Implement task 2", prompt="You are implementing task 2", cwd=tmpdir))
        assert result.returncode == 0, f"Expected ALLOW (5d skipped). stderr: {result.stderr}"

    def test_previous_verification_skips_review_reports(self, tmp_path):
        # PREVIOUS task 1 declared verification; its spec/quality review reports AND
        # dispatch-log provenance entries are absent (the impl report still exists).
        # Current task 2 is not first-in-module, so 4b/4c would normally fire.
        # Checks 4b + 4c must be skipped -> ALLOW.
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=self.TOTAL, completed_tasks=self.COMPLETED)
        _write_frontmatter_plan(tmpdir, self.TOTAL, {1: "verification"})
        os.remove(os.path.join(tmpdir, "reports", "task-001-spec-review.md"))
        os.remove(os.path.join(tmpdir, "reports", "task-001-quality-review.md"))
        log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
        kept = [
            line for line in open(log_path).read().splitlines()
            if "task=1 type=spec-review" not in line
            and "task=1 type=quality-review" not in line
        ]
        with open(log_path, "w") as f:
            f.write("\n".join(kept) + "\n")
        # Sanity: task 1 implementer report is still present (verification still files one).
        assert os.path.isfile(os.path.join(tmpdir, "reports", "task-001-implementer-report.md"))
        result = run_hook(make_hook_input(
            description="Implement task 2", prompt="You are implementing task 2", cwd=tmpdir))
        assert result.returncode == 0, f"Expected ALLOW (4b/4c skipped). stderr: {result.stderr}"

    def test_implementation_task_still_requires_reviews(self, tmp_path):
        # Positive control: identical setup but every task is implementation
        # (no task_type override). The missing partner review AND missing prior
        # reviews/provenance must still BLOCK -> exit 2. This proves the fixture
        # genuinely reads task_type rather than passing vacuously.
        tmpdir = str(tmp_path)
        setup_full_sdd_workspace(tmpdir, total_tasks=self.TOTAL, completed_tasks=self.COMPLETED)
        _write_frontmatter_plan(tmpdir, self.TOTAL, {})  # all implementation
        os.remove(os.path.join(tmpdir, "reports", "partner-review-002.md"))
        os.remove(os.path.join(tmpdir, "reports", "task-001-spec-review.md"))
        os.remove(os.path.join(tmpdir, "reports", "task-001-quality-review.md"))
        log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
        kept = [
            line for line in open(log_path).read().splitlines()
            if "task=1 type=spec-review" not in line
            and "task=1 type=quality-review" not in line
        ]
        with open(log_path, "w") as f:
            f.write("\n".join(kept) + "\n")
        result = run_hook(make_hook_input(
            description="Implement task 2", prompt="You are implementing task 2", cwd=tmpdir))
        assert result.returncode == 2, \
            f"Expected BLOCK (implementation still enforces reviews). stderr: {result.stderr}"


def _read_log(tmpdir):
    log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
    if not os.path.exists(log_path):
        return ""
    with open(log_path) as f:
        return f.read()


def test_marked_fix_logs_type_fix_not_implementer(tmp_path):
    # N26a: [task N fix] → type=fix line, and NEVER a type=implementer line.
    tmpdir = str(tmp_path)
    setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=2)
    run_hook(make_hook_input(
        description="[task 3 fix] fix the parser regression",
        prompt="", cwd=tmpdir))
    log = _read_log(tmpdir)
    assert "task=3 type=fix" in log
    assert "task=3 type=implementer" not in log  # must NOT move Check 9 window


def test_marked_rereview_logs_reviewer_passthrough(tmp_path):
    # N26a: [task N re-review:quality] → reviewer log entry + passthrough (rc 0).
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=5)
    result = run_hook(make_hook_input(
        description="[task 4 re-review:quality] re-review after fix",
        prompt="", cwd=tmpdir))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "task=4 type=quality-review" in _read_log(tmpdir)


def test_markerless_fix_logs_unattributed(tmp_path):
    # N26a Stage-3 fallback: markerless fix → fix-unattributed, passthrough.
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=5)
    result = run_hook(make_hook_input(
        description="fix the broken merge logic", prompt="", cwd=tmpdir))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "type=fix-unattributed" in _read_log(tmpdir)


def test_check3b_allows_gate_artifact_names(tmp_path):
    # N26b: honesty-check-*, execution-trace-audit.md, final-code-review.md
    # must not trip Check 3b non-standard-naming.
    tmpdir = str(tmp_path)
    setup_full_sdd_workspace(tmpdir, total_tasks=5, completed_tasks=2)
    reports = os.path.join(tmpdir, "reports")
    open(os.path.join(reports, "final-code-review.md"), "w").write("x" * 60)
    open(os.path.join(reports, "execution-trace-audit.md"), "w").write("x" * 60)
    open(os.path.join(reports, "honesty-check-2026.md"), "w").write("x" * 60)
    result = run_hook(make_hook_input(
        description="implement task 2", prompt="", cwd=tmpdir))
    assert "non-standard naming" not in result.stderr
