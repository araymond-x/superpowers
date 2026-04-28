"""CLI entry-point tests for validators.py report subcommand."""

import os
import subprocess
import sys
from pathlib import Path


VALIDATOR_SCRIPT = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "scripts"
    / "models"
    / "validators.py"
)
FIXTURES_DIR = str(
    Path(__file__).resolve().parent.parent.parent / "fixtures" / "reports"
)
PYTHON = sys.executable


class TestValidReport:
    def test_minimal_valid_report_passes(self):
        result = subprocess.run(
            [
                PYTHON,
                VALIDATOR_SCRIPT,
                "report",
                f"{FIXTURES_DIR}/valid/minimal-report.md",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_full_featured_report_passes(self):
        result = subprocess.run(
            [
                PYTHON,
                VALIDATOR_SCRIPT,
                "report",
                f"{FIXTURES_DIR}/valid/full-featured-report.md",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestInvalidReport:
    def test_missing_status_fails(self):
        result = subprocess.run(
            [
                PYTHON,
                VALIDATOR_SCRIPT,
                "report",
                f"{FIXTURES_DIR}/invalid/missing-status.md",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "VALIDATION FAILED" in result.stderr

    def test_bad_status_enum_fails(self):
        result = subprocess.run(
            [
                PYTHON,
                VALIDATOR_SCRIPT,
                "report",
                f"{FIXTURES_DIR}/invalid/bad-status-enum.md",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "VALIDATION FAILED" in result.stderr

    def test_inconsistent_test_counts_fails(self):
        result = subprocess.run(
            [
                PYTHON,
                VALIDATOR_SCRIPT,
                "report",
                f"{FIXTURES_DIR}/invalid/test-counts-inconsistent.md",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_no_files_for_done_fails(self):
        result = subprocess.run(
            [
                PYTHON,
                VALIDATOR_SCRIPT,
                "report",
                f"{FIXTURES_DIR}/invalid/no-files-for-done.md",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1


class TestInfrastructureErrors:
    def test_missing_file_returns_exit_2(self):
        result = subprocess.run(
            [PYTHON, VALIDATOR_SCRIPT, "report", "/nonexistent/path.md"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2

    def test_no_frontmatter_hard_fail(self, tmp_path):
        no_fm = tmp_path / "no-frontmatter.md"
        no_fm.write_text("# Just markdown\nNo frontmatter here.\n")
        result = subprocess.run(
            [PYTHON, VALIDATOR_SCRIPT, "report", str(no_fm)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Phase 2" in result.stderr or "cutover" in result.stderr.lower()


class TestBypass:
    def test_bypass_env_var_skips_validation(self, tmp_path):
        bad_report = tmp_path / "bad.md"
        bad_report.write_text("---\nbogus: true\n---\n")
        env = {**os.environ, "SUPERPOWERS_VALIDATOR_BYPASS": "1"}
        result = subprocess.run(
            [PYTHON, VALIDATOR_SCRIPT, "report", str(bad_report)],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0
        assert "BYPASS" in result.stderr
