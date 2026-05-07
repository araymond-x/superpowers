"""Tests for validators.py plan subcommand."""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path

VALIDATORS_PATH = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills" / "scripts" / "models" / "validators.py"
)

VALID_PLAN = """\
---
schema_version: 1
feature_archetype: greenfield
tasks:
  - id: 0
    title: "Setup"
  - id: 1
    title: "Build"
    depends_on: [0]
---

# Test Plan
"""

INVALID_PLAN_BAD_ARCHETYPE = """\
---
schema_version: 1
feature_archetype: bogus
tasks:
  - id: 0
    title: "x"
---

# Bad Plan
"""

NO_FRONTMATTER_PLAN = """\
# Old-Style Plan

No YAML frontmatter here.
"""

MALFORMED_YAML = """\
---
schema_version: 1
feature_archetype: [invalid yaml
---
"""


def _run_validator(plan_content: str, extra_args: list[str] | None = None, env_override: dict | None = None) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(plan_content)
        f.flush()
        path = f.name
    try:
        env = os.environ.copy()
        if env_override:
            env.update(env_override)
        cmd = [".venv/bin/python3", VALIDATORS_PATH, "plan", path]
        if extra_args:
            cmd.extend(extra_args)
        return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
    finally:
        os.unlink(path)


class TestPlanValidatorHappyPath:
    def test_valid_plan_exits_zero(self):
        result = _run_validator(VALID_PLAN)
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_valid_plan_no_stderr(self):
        result = _run_validator(VALID_PLAN)
        assert result.stderr.strip() == ""


class TestPlanValidatorFailures:
    def test_invalid_archetype_exits_one(self):
        result = _run_validator(INVALID_PLAN_BAD_ARCHETYPE)
        assert result.returncode == 1

    def test_invalid_archetype_shows_validation_failed(self):
        result = _run_validator(INVALID_PLAN_BAD_ARCHETYPE)
        assert "VALIDATION FAILED" in result.stderr

    def test_no_frontmatter_exits_one(self):
        result = _run_validator(NO_FRONTMATTER_PLAN)
        assert result.returncode == 1

    def test_no_frontmatter_message(self):
        result = _run_validator(NO_FRONTMATTER_PLAN)
        assert "predates" in result.stderr or "YAML frontmatter" in result.stderr

    def test_malformed_yaml_exits_one(self):
        result = _run_validator(MALFORMED_YAML)
        assert result.returncode == 1

    def test_malformed_yaml_shows_yaml_parse_failed(self):
        result = _run_validator(MALFORMED_YAML)
        assert "YAML PARSE FAILED" in result.stderr


class TestPlanValidatorInfrastructure:
    def test_missing_file_exits_two(self):
        result = subprocess.run(
            [".venv/bin/python3", VALIDATORS_PATH, "plan", "/nonexistent/plan.md"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 2

    def test_bypass_env_exits_zero(self):
        result = _run_validator(INVALID_PLAN_BAD_ARCHETYPE, env_override={"SUPERPOWERS_VALIDATOR_BYPASS": "1"})
        assert result.returncode == 0

    def test_bypass_env_emits_warning(self):
        result = _run_validator(INVALID_PLAN_BAD_ARCHETYPE, env_override={"SUPERPOWERS_VALIDATOR_BYPASS": "1"})
        assert "BYPASS" in result.stderr


class TestParentModularPlan:
    """Parent plans have tasks: [] and delegate task details to module files."""

    PARENT_PLAN = """\
---
schema_version: 1
feature_archetype: extension
tasks: []
modules:
  - id: 1
    title: "Backend"
    task_ids: [0, 1, 2]
  - id: 2
    title: "Frontend"
    task_ids: [0, 1]
---

# Parent Plan

Delegates all tasks to module files.
"""

    def test_parent_plan_with_empty_tasks_exits_zero(self):
        """tasks: [] is valid for parent modular plans (was IndexError crash before fix)."""
        result = _run_validator(self.PARENT_PLAN)
        assert result.returncode == 0, f"Expected pass, got stderr: {result.stderr}"

    def test_parent_plan_no_crash_message(self):
        """Validator must not emit VALIDATOR CRASHED for empty task list."""
        result = _run_validator(self.PARENT_PLAN)
        assert "VALIDATOR CRASHED" not in result.stderr

    def test_parent_plan_no_stderr(self):
        result = _run_validator(self.PARENT_PLAN)
        assert result.stderr.strip() == ""


class TestSchemaVersionFlag:
    def test_forensic_flag_stub_accepted(self):
        """Forensic --schema-version flag is a CLI stub -- accepted but does not alter validation."""
        result = _run_validator(VALID_PLAN, extra_args=["--schema-version", "1"])
        assert result.returncode == 0
