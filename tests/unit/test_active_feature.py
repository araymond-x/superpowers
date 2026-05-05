"""Tests for .active-feature file resolution and conflict detection.

These tests validate the shell logic that hooks will use to read .active-feature.
We test the behavior via subprocess calls to small bash snippets that mirror
the hook preamble.
"""
import os
import subprocess
import tempfile

import pytest


FEAT_PREAMBLE = '''
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi
echo "$FEAT"
'''


class TestActiveFeatureResolution:
    """Test reading .active-feature and resolving the feature directory."""

    def test_reads_feature_dir_from_file(self, tmp_path):
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-my-feature")
        result = subprocess.run(
            ["bash", "-c", FEAT_PREAMBLE],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "docs/imp-plans/2026-05-02-my-feature"

    def test_returns_empty_when_file_missing(self, tmp_path):
        result = subprocess.run(
            ["bash", "-c", FEAT_PREAMBLE],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == ""

    def test_returns_empty_when_file_is_empty(self, tmp_path):
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("")
        result = subprocess.run(
            ["bash", "-c", FEAT_PREAMBLE],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == ""

    def test_strips_trailing_newline(self, tmp_path):
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-feature\n")
        result = subprocess.run(
            ["bash", "-c", FEAT_PREAMBLE],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "docs/imp-plans/2026-05-02-feature"

    def test_path_prefixing_works(self, tmp_path):
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-my-feature")
        feat_dir = tmp_path / "docs" / "imp-plans" / "2026-05-02-my-feature"
        feat_dir.mkdir(parents=True)
        reports_dir = feat_dir / "reports"
        reports_dir.mkdir()
        (reports_dir / "task-000-implementer-report.md").write_text("x" * 100)

        script = '''
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi
if [ -d "$FEAT/reports" ]; then
  echo "FOUND"
else
  echo "MISSING"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "FOUND"


class TestConflictDetection:
    """Test detection of stale/conflicting .active-feature files."""

    def test_stale_pointer_detected(self, tmp_path):
        """Feature dir doesn't exist — stale pointer."""
        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-01-01-deleted-feature")

        script = '''
FEAT=$(cat .active-feature 2>/dev/null)
if [ -n "$FEAT" ] && [ ! -d "$FEAT" ]; then
  echo "STALE"
else
  echo "OK"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "STALE"

    def test_completed_feature_detected(self, tmp_path):
        """Feature dir exists with plan where all tasks have matching reports."""
        feat_dir = tmp_path / "docs" / "imp-plans" / "2026-05-02-done-feature"
        reports_dir = feat_dir / "reports"
        reports_dir.mkdir(parents=True)

        plan = feat_dir / "plan.md"
        plan.write_text("### Task 0: Setup\n### Task 1: Build\n")

        (reports_dir / "task-000-implementer-report.md").write_text("x" * 100)
        (reports_dir / "task-001-implementer-report.md").write_text("x" * 100)

        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-done-feature")

        script = '''
FEAT=$(cat .active-feature)
if [ -d "$FEAT" ] && [ -f "$FEAT/plan.md" ]; then
  TASK_COUNT=$(grep -c "^### Task " "$FEAT/plan.md" 2>/dev/null || echo 0)
  REPORT_COUNT=$(ls "$FEAT/reports/"task-*-implementer-report*.md 2>/dev/null | wc -l | tr -d " ")
  if [ "$TASK_COUNT" -gt 0 ] && [ "$REPORT_COUNT" -ge "$TASK_COUNT" ]; then
    echo "COMPLETED"
  else
    echo "INCOMPLETE"
  fi
else
  echo "NO_PLAN"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "COMPLETED"

    def test_incomplete_feature_detected(self, tmp_path):
        """Feature dir exists with plan but missing reports."""
        feat_dir = tmp_path / "docs" / "imp-plans" / "2026-05-02-wip-feature"
        reports_dir = feat_dir / "reports"
        reports_dir.mkdir(parents=True)

        plan = feat_dir / "plan.md"
        plan.write_text("### Task 0: Setup\n### Task 1: Build\n### Task 2: Test\n")

        (reports_dir / "task-000-implementer-report.md").write_text("x" * 100)

        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-wip-feature")

        script = '''
FEAT=$(cat .active-feature)
if [ -d "$FEAT" ] && [ -f "$FEAT/plan.md" ]; then
  TASK_COUNT=$(grep -c "^### Task " "$FEAT/plan.md" 2>/dev/null || echo 0)
  REPORT_COUNT=$(ls "$FEAT/reports/"task-*-implementer-report*.md 2>/dev/null | wc -l | tr -d " ")
  if [ "$TASK_COUNT" -gt 0 ] && [ "$REPORT_COUNT" -ge "$TASK_COUNT" ]; then
    echo "COMPLETED"
  else
    echo "INCOMPLETE"
  fi
else
  echo "NO_PLAN"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "INCOMPLETE"

    def test_no_plan_detected(self, tmp_path):
        """Feature dir exists but has no plan (abandoned brainstorming)."""
        feat_dir = tmp_path / "docs" / "imp-plans" / "2026-05-02-abandoned"
        feat_dir.mkdir(parents=True)
        (feat_dir / "spec.md").write_text("# Some spec")

        feat_file = tmp_path / ".active-feature"
        feat_file.write_text("docs/imp-plans/2026-05-02-abandoned")

        script = '''
FEAT=$(cat .active-feature)
if [ -d "$FEAT" ] && [ -f "$FEAT/plan.md" ]; then
  echo "HAS_PLAN"
else
  echo "NO_PLAN"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "NO_PLAN"

    def test_fallback_to_root_when_no_active_feature(self, tmp_path):
        """Without .active-feature, paths resolve to root level (backwards compat)."""
        (tmp_path / "reports").mkdir()
        (tmp_path / "DEVIATIONS.md").write_text("# Deviations")

        script = '''
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi
if [ -n "$FEAT" ]; then
  REPORTS="$FEAT/reports"
  DEVS="$FEAT/deviations.md"
else
  REPORTS="reports"
  DEVS="DEVIATIONS.md"
fi
if [ -d "$REPORTS" ] && [ -f "$DEVS" ]; then
  echo "RESOLVED"
else
  echo "MISSING"
fi
'''
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=str(tmp_path), capture_output=True, text=True
        )
        assert result.stdout.strip() == "RESOLVED"


class TestFeatureNameValidation:
    """Test that feature names follow kebab-case convention."""

    @pytest.mark.parametrize("name,expected", [
        ("pydantic-phase-2", True),
        ("statement-reconciliation-v3", True),
        ("fix-login-bug", True),
        ("a", True),
        ("2026-feature", True),
        ("PascalCase", False),
        ("camelCase", False),
        ("has spaces", False),
        ("has_underscores", False),
        ("ALLCAPS", False),
        ("has.dots", False),
        ("has/slashes", False),
        ("", False),
        ("has--double-dashes", False),
        ("-starts-with-dash", False),
        ("ends-with-dash-", False),
    ])
    def test_feature_name_validation(self, name, expected):
        """Validate kebab-case: lowercase letters, digits, single hyphens, no leading/trailing hyphens."""
        import re
        pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
        result = bool(re.match(pattern, name)) if name else False
        assert result == expected, f"Expected {name!r} to be {'valid' if expected else 'invalid'}"

    def test_feature_dir_path_construction(self):
        """Verify the complete path format."""
        import re
        name = "pydantic-phase-2"
        date = "2026-05-02"
        path = f"docs/imp-plans/{date}-{name}"
        assert re.match(r'^docs/imp-plans/\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$', path)
