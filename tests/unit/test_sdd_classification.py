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
