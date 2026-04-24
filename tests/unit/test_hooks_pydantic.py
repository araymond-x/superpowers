"""Integration tests for hook scripts calling Pydantic validators."""

import os
import subprocess
import tempfile
import json
from pathlib import Path

VALIDATORS_PATH = str(
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "scripts"
    / "models"
    / "validators.py"
)


class TestJqAvailability:
    """jq must be available for hook JSON wrapping."""

    def test_jq_is_on_path(self):
        result = subprocess.run(["which", "jq"], capture_output=True, text=True)
        assert result.returncode == 0, (
            "jq is not installed — required for hook JSON wrapping"
        )

    def test_jq_can_wrap_string(self):
        result = subprocess.run(
            ["jq", "-Rs", "."],
            input="test\nstring",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "test" in parsed


class TestPlanValidatorFromHookPerspective:
    """Verify validator produces output hooks can consume."""

    def test_valid_plan_exits_zero(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(
                "---\nschema_version: 1\nfeature_archetype: greenfield\ntasks:\n  - id: 0\n    title: x\n---\n"
            )
            f.flush()
            result = subprocess.run(
                [".venv/bin/python3", VALIDATORS_PATH, "plan", f.name],
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/Users/araymond/projects/claude-custom/superpowers",
            )
        os.unlink(f.name)
        assert result.returncode == 0

    def test_invalid_plan_stderr_wrappable_with_jq(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nschema_version: 1\n---\n")
            f.flush()
            val_result = subprocess.run(
                [".venv/bin/python3", VALIDATORS_PATH, "plan", f.name],
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/Users/araymond/projects/claude-custom/superpowers",
            )
        os.unlink(f.name)
        assert val_result.returncode == 1
        jq_result = subprocess.run(
            ["jq", "-Rs", "."],
            input=val_result.stderr,
            capture_output=True,
            text=True,
        )
        assert jq_result.returncode == 0
        parsed = json.loads(jq_result.stdout)
        assert "VALIDATION FAILED" in parsed

    def test_no_frontmatter_stderr_contains_cutover_message(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Old plan\nNo frontmatter.\n")
            f.flush()
            result = subprocess.run(
                [".venv/bin/python3", VALIDATORS_PATH, "plan", f.name],
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/Users/araymond/projects/claude-custom/superpowers",
            )
        os.unlink(f.name)
        assert result.returncode == 1
        assert "frontmatter" in result.stderr.lower()


class TestHandoffValidatorFromHookPerspective:
    """Verify handoff validator produces output hooks can consume."""

    def test_valid_handoff_exits_zero(self, tmp_path):
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        (pkg_dir / "README.md").write_text(
            "---\nschema_version: 1\npackage_name: test\nfeeds_into: x\n"
            "one_sentence_purpose: test\ncontract_constraints:\n  - name: a\n    kind: string\n"
            "samples:\n  - path: s.csv\n    description: d\n---\n"
        )
        (pkg_dir / "s.csv").write_text("data")
        result = subprocess.run(
            [".venv/bin/python3", VALIDATORS_PATH, "handoff", str(pkg_dir)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/Users/araymond/projects/claude-custom/superpowers",
        )
        assert result.returncode == 0

    def test_missing_sample_shows_distinct_header(self, tmp_path):
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        (pkg_dir / "README.md").write_text(
            "---\nschema_version: 1\npackage_name: test\nfeeds_into: x\n"
            "one_sentence_purpose: test\ncontract_constraints:\n  - name: a\n    kind: string\n"
            "samples:\n  - path: missing.csv\n    description: d\n---\n"
        )
        result = subprocess.run(
            [".venv/bin/python3", VALIDATORS_PATH, "handoff", str(pkg_dir)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/Users/araymond/projects/claude-custom/superpowers",
        )
        assert result.returncode == 1
        assert "SAMPLE FILE MISSING" in result.stderr
        assert "VALIDATION FAILED" not in result.stderr
