"""Tests for validators.py handoff subcommand."""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path

VALIDATORS_PATH = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills" / "scripts" / "models" / "validators.py"
)

VALID_HANDOFF_README = """\
---
schema_version: 1
package_name: test-pkg
feeds_into: brainstorming
one_sentence_purpose: "Test handoff."
contract_constraints:
  - name: amount
    kind: float
samples:
  - path: samples/example.csv
    description: "Example data"
---

# Test Handoff Package
"""

INVALID_HANDOFF_README = """\
---
schema_version: 1
package_name: test-pkg
feeds_into: brainstorming
one_sentence_purpose: "Test."
contract_constraints:
  - name: amount
    kind: complex
samples:
  - path: samples/example.csv
    description: "Example"
---
"""


def _setup_package(tmpdir: Path, readme_content: str, sample_files: list[str] | None = None) -> Path:
    pkg_dir = tmpdir / "test-pkg"
    pkg_dir.mkdir()
    (pkg_dir / "README.md").write_text(readme_content)
    if sample_files:
        for sf in sample_files:
            (pkg_dir / sf).parent.mkdir(parents=True, exist_ok=True)
            (pkg_dir / sf).write_text("sample data")
    return pkg_dir


def _run_validator(pkg_dir: str, env_override: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    return subprocess.run(
        [".venv/bin/python3", VALIDATORS_PATH, "handoff", str(pkg_dir)],
        capture_output=True, text=True, env=env, timeout=10,
    )


class TestHandoffValidatorHappyPath:
    def test_valid_handoff_exits_zero(self, tmp_path):
        pkg = _setup_package(tmp_path, VALID_HANDOFF_README, ["samples/example.csv"])
        result = _run_validator(str(pkg))
        assert result.returncode == 0, f"stderr: {result.stderr}"


class TestHandoffValidatorFailures:
    def test_invalid_field_type_exits_one(self, tmp_path):
        pkg = _setup_package(tmp_path, INVALID_HANDOFF_README, ["samples/example.csv"])
        result = _run_validator(str(pkg))
        assert result.returncode == 1
        assert "VALIDATION FAILED" in result.stderr

    def test_missing_sample_file_exits_one(self, tmp_path):
        pkg = _setup_package(tmp_path, VALID_HANDOFF_README)  # no sample files created
        result = _run_validator(str(pkg))
        assert result.returncode == 1
        assert "SAMPLE FILE MISSING" in result.stderr

    def test_missing_readme_exits_two(self, tmp_path):
        pkg_dir = tmp_path / "empty-pkg"
        pkg_dir.mkdir()
        result = _run_validator(str(pkg_dir))
        assert result.returncode == 2


class TestHandoffBypass:
    def test_bypass_exits_zero(self, tmp_path):
        pkg = _setup_package(tmp_path, INVALID_HANDOFF_README, ["samples/example.csv"])
        result = _run_validator(str(pkg), env_override={"SUPERPOWERS_VALIDATOR_BYPASS": "1"})
        assert result.returncode == 0

    def test_bypass_emits_warning(self, tmp_path):
        pkg = _setup_package(tmp_path, INVALID_HANDOFF_README, ["samples/example.csv"])
        result = _run_validator(str(pkg), env_override={"SUPERPOWERS_VALIDATOR_BYPASS": "1"})
        assert "BYPASS" in result.stderr
