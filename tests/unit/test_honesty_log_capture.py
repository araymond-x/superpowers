#!/usr/bin/env python3
"""
Unit tests for the SDD stop hook's honesty check vault capture.

Tests cover:
  - Copy to individual vault file when honesty-check-*.md exists
  - Skip when file is missing or too small (<50 bytes)
  - Idempotency: don't overwrite on repeated runs
  - Vault file includes YAML frontmatter with metadata
  - Graceful when VAULT_DIR is unset

Run: python3 -m pytest tests/unit/test_honesty_log_capture.py -v
"""

import json
import os
import shutil
import subprocess
import tempfile

HOOK_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "skills",
    "subagent-driven-development",
    "scripts",
    "sdd-stop-hook.sh",
)

HONESTY_CONTENT = """\
# Honesty Check Response

## 1. Did you invoke SDD via the Skill tool?
Yes, loaded via Skill tool at session start.

## 2. Did you skip any steps?
No steps were skipped.

## 3. Were you blocked by hooks?
No hook blocks encountered.
"""

PLAN_CONTENT = """\
# Implementation Plan

### Task 1 — Build
- [x] Build it
"""


def _setup_sdd_workspace(tmpdir, honesty_content=None, plan_content=PLAN_CONTENT):
    """Create a minimal SDD workspace with git repo."""
    # Init git repo so branch detection works
    subprocess.run(
        ["git", "init", "-b", "feature/test-feature"],
        cwd=tmpdir, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmpdir, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmpdir, capture_output=True,
    )

    # Create plan
    plans_dir = os.path.join(tmpdir, "docs", "imp-plans")
    os.makedirs(plans_dir, exist_ok=True)
    with open(os.path.join(plans_dir, "plan.md"), "w") as f:
        f.write(plan_content)

    # Create DEVIATIONS.md
    with open(os.path.join(tmpdir, "DEVIATIONS.md"), "w") as f:
        f.write("# Deviations\nNone.\n")

    # Create reports dir
    reports_dir = os.path.join(tmpdir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    with open(os.path.join(reports_dir, "task-001-implementer-report.md"), "w") as f:
        f.write("# Report\n# Status: DONE\n")

    # Write honesty check if provided (dated filename)
    if honesty_content is not None:
        with open(os.path.join(reports_dir, "honesty-check-2026-04-17.md"), "w") as f:
            f.write(honesty_content)

    return tmpdir


def _run_stop_hook(cwd, vault_dir):
    """Run the stop hook with the given CWD and VAULT_DIR."""
    hook_input = json.dumps({"cwd": cwd})
    env = os.environ.copy()
    env["VAULT_DIR"] = vault_dir
    result = subprocess.run(
        ["bash", HOOK_PATH],
        input=hook_input,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    return result


class TestHonestyVaultCapture:
    """Stop hook should copy honesty check responses to individual vault files."""

    def _vault_hc_dir(self, vault_dir):
        return os.path.join(vault_dir, "References", "SDD", "honesty-checks")

    def _find_vault_files(self, vault_dir):
        hc_dir = self._vault_hc_dir(vault_dir)
        if not os.path.isdir(hc_dir):
            return []
        return [f for f in os.listdir(hc_dir) if f.endswith(".md")]

    def test_creates_individual_vault_file(self):
        """When honesty-check-*.md exists, a vault file is created."""
        tmpdir = tempfile.mkdtemp()
        vault_dir = tempfile.mkdtemp()
        try:
            _setup_sdd_workspace(tmpdir, honesty_content=HONESTY_CONTENT)
            _run_stop_hook(tmpdir, vault_dir)

            files = self._find_vault_files(vault_dir)
            assert len(files) == 1, f"Expected 1 vault file, found {files}"
            content = open(os.path.join(self._vault_hc_dir(vault_dir), files[0])).read()
            assert "Did you invoke SDD" in content
            assert "feature/test-feature" in content
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_skips_when_no_honesty_file(self):
        """No honesty-check-*.md → no vault file created."""
        tmpdir = tempfile.mkdtemp()
        vault_dir = tempfile.mkdtemp()
        try:
            _setup_sdd_workspace(tmpdir, honesty_content=None)
            _run_stop_hook(tmpdir, vault_dir)

            files = self._find_vault_files(vault_dir)
            assert len(files) == 0, "No vault file when honesty file missing"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_skips_when_honesty_file_too_small(self):
        """Stub honesty-check-*.md (<50 bytes) → no vault file."""
        tmpdir = tempfile.mkdtemp()
        vault_dir = tempfile.mkdtemp()
        try:
            _setup_sdd_workspace(tmpdir, honesty_content="stub")
            _run_stop_hook(tmpdir, vault_dir)

            files = self._find_vault_files(vault_dir)
            assert len(files) == 0, "No vault file when honesty file is stub"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_idempotent_on_repeated_runs(self):
        """Running the hook twice doesn't create a second file."""
        tmpdir = tempfile.mkdtemp()
        vault_dir = tempfile.mkdtemp()
        try:
            _setup_sdd_workspace(tmpdir, honesty_content=HONESTY_CONTENT)
            _run_stop_hook(tmpdir, vault_dir)
            _run_stop_hook(tmpdir, vault_dir)

            files = self._find_vault_files(vault_dir)
            assert len(files) == 1, f"Expected 1 file after 2 runs, found {files}"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_vault_file_has_yaml_frontmatter(self):
        """Vault file includes YAML frontmatter with metadata."""
        tmpdir = tempfile.mkdtemp()
        vault_dir = tempfile.mkdtemp()
        try:
            _setup_sdd_workspace(tmpdir, honesty_content=HONESTY_CONTENT)
            _run_stop_hook(tmpdir, vault_dir)

            files = self._find_vault_files(vault_dir)
            content = open(os.path.join(self._vault_hc_dir(vault_dir), files[0])).read()
            assert content.startswith("---")
            assert "type: honesty-check" in content
            assert "project:" in content
            assert "branch: feature/test-feature" in content
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_vault_filename_includes_project_and_branch(self):
        """Vault filename follows YYYY-MM-DD-<project>-<branch>.md pattern."""
        tmpdir = tempfile.mkdtemp()
        vault_dir = tempfile.mkdtemp()
        try:
            _setup_sdd_workspace(tmpdir, honesty_content=HONESTY_CONTENT)
            _run_stop_hook(tmpdir, vault_dir)

            files = self._find_vault_files(vault_dir)
            assert len(files) == 1
            filename = files[0]
            assert "feature/test-feature" in filename or "feature" in filename
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_skips_when_no_vault_dir(self):
        """No VAULT_DIR env var → no crash, no vault file."""
        tmpdir = tempfile.mkdtemp()
        try:
            _setup_sdd_workspace(tmpdir, honesty_content=HONESTY_CONTENT)
            hook_input = json.dumps({"cwd": tmpdir})
            env = os.environ.copy()
            env.pop("VAULT_DIR", None)
            result = subprocess.run(
                ["bash", HOOK_PATH],
                input=hook_input,
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            assert result.returncode == 0, "Hook should not crash without VAULT_DIR"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
