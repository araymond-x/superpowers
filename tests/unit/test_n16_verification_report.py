"""N16: ImplementerReport task_type field + verification exemption.
Run: .venv/bin/python3 -m pytest tests/unit/test_n16_verification_report.py -v
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "skills", "scripts", "models"))
from implementer_report import ImplementerReport


def _base_report(**overrides):
    defaults = {
        "schema_version": 1,
        "task_id": 5,
        "status": "DONE",
        "files_changed": [{"path": "foo.py", "description": "changed"}],
        "tests": {"written": 1, "passing": 1, "command": "pytest", "result": "PASS"},
    }
    defaults.update(overrides)
    return defaults


class TestTaskTypeField:
    def test_default_is_implementation(self):
        r = ImplementerReport(**_base_report())
        assert r.task_type == "implementation"

    def test_explicit_verification(self):
        r = ImplementerReport(**_base_report(task_type="verification"))
        assert r.task_type == "verification"

    def test_invalid_value_rejected(self):
        with pytest.raises(Exception):
            ImplementerReport(**_base_report(task_type="audit"))


class TestVerificationExemption:
    def test_verification_done_empty_files_passes(self):
        """N16 core fix: verification task with DONE + empty files_changed is valid."""
        r = ImplementerReport(
            **_base_report(
                task_type="verification",
                status="DONE",
                files_changed=[],
            )
        )
        assert r.status == "DONE"
        assert r.files_changed == []

    def test_implementation_done_empty_files_still_fails(self):
        """Implementation tasks must still have files_changed when DONE."""
        with pytest.raises(ValueError, match="files_changed is empty"):
            ImplementerReport(
                **_base_report(
                    task_type="implementation",
                    status="DONE",
                    files_changed=[],
                )
            )

    def test_verification_blocked_empty_files_passes(self):
        """Non-DONE statuses with empty files always pass (existing behavior)."""
        r = ImplementerReport(
            **_base_report(
                task_type="verification",
                status="BLOCKED",
                files_changed=[],
            )
        )
        assert r.status == "BLOCKED"


class TestValidateReportCLI:
    """Verify N16 fix flows through the full CLI validation pipeline."""

    VALIDATE_SCRIPT = os.path.join(
        ROOT, "skills", "subagent-driven-development", "scripts", "validate-report.py"
    )
    PYTHON = os.path.join(ROOT, ".venv", "bin", "python3")

    PROSE_SECTIONS = (
        "**Implementation Summary:**\nVerified all checks pass.\n\n"
        "**Source Files Read:**\n- `foo.py` — read it\n\n"
        "**CLAUDE.md Files Read:**\nNone found\n\n"
        "**Deviations from Plan:**\nNone\n\n"
        "**Self-Review Findings:**\nNo issues found\n\n"
        "**Concerns:**\nNo concerns\n"
    )

    def _write_report(self, tmp_path: Path, frontmatter: str) -> Path:
        report = f"---\n{frontmatter}---\n\n{self.PROSE_SECTIONS}"
        p = tmp_path / "report.md"
        p.write_text(report)
        return p

    def test_verification_done_empty_files_cli_passes(self, tmp_path):
        """validate-report.py exits 0 for verification task with empty files_changed."""
        fm = (
            "schema_version: 1\n"
            "task_id: 7\n"
            "task_type: verification\n"
            "status: DONE\n"
            "files_changed: []\n"
            "tests:\n"
            "  written: 0\n"
            "  passing: 0\n"
            '  command: "grep -r TODO"\n'
            "  result: PASS\n"
            "contract_compliance: []\n"
        )
        report_path = self._write_report(tmp_path, fm)
        result = subprocess.run(
            [self.PYTHON, self.VALIDATE_SCRIPT, "--report-file", str(report_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Expected exit 0, got {result.returncode}.\nstderr: {result.stderr}\nstdout: {result.stdout}"
        )

    def test_implementation_done_empty_files_cli_fails(self, tmp_path):
        """validate-report.py exits 1 for implementation task with empty files_changed."""
        fm = (
            "schema_version: 1\n"
            "task_id: 7\n"
            "task_type: implementation\n"
            "status: DONE\n"
            "files_changed: []\n"
            "tests:\n"
            "  written: 1\n"
            "  passing: 1\n"
            "  command: pytest\n"
            "  result: PASS\n"
            "contract_compliance: []\n"
        )
        report_path = self._write_report(tmp_path, fm)
        result = subprocess.run(
            [self.PYTHON, self.VALIDATE_SCRIPT, "--report-file", str(report_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"Expected exit 1, got {result.returncode}.\nstderr: {result.stderr}\nstdout: {result.stdout}"
        )
