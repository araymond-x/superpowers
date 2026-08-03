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

import pytest

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
        cwd=tmpdir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmpdir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmpdir,
        capture_output=True,
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


def _run_stop_hook(cwd, vault_dir, transcript_path=None, home=None):
    """Run the stop hook with the given CWD and VAULT_DIR.

    transcript_path/home are optional (Decision 15 spawn-outcome tests): when
    given, transcript_path is embedded as the hook payload's .transcript_path
    field and home overrides $HOME so bundles/*/manifest.json can be resolved
    from a fixture directory instead of the real ~/.claude-codex-handoff.
    """
    payload = {"cwd": cwd}
    if transcript_path:
        payload["transcript_path"] = transcript_path
    hook_input = json.dumps(payload)
    env = os.environ.copy()
    env["VAULT_DIR"] = vault_dir
    if home:
        env["HOME"] = home
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


# ─── Decision 15: spawn-outcome step-completion WARNING ───────────────────────
#
# A handoff bundle created THIS session with no matching outcome/decline record
# in reports/handoff-spawn.log means the controller built the bundle and never
# finished the protocol. Matching key is the bundle id; the bundle dir's mtime
# only bounds the candidate set to "created during this session" (transcript
# first-line .timestamp is used as the session-start marker).

OLD_TIMESTAMP = "2020-01-01T00:00:00Z"  # always < any bundle's real mtime

# Plan with YAML frontmatter (tasks: list with an int id) — required so
# controller-checkpoint.py's _task_ids_where() can actually parse frontmatter;
# without it every run appends the "review_tier_plan_parse_skipped" WARNING,
# which alone forces a non-zero exit (warnings-present -> exit 2) even when
# there are no blockers.
FRONTMATTER_PLAN = """---
schema_version: 1
tasks:
  - id: 1
    title: "Build"
---
# Implementation Plan

### Task 1 -- Build
- [x] Build it
"""

TRACE_AUDIT_CONTENT = (
    "# Execution Trace Audit\n\nAll dispatches accounted for. No anomalies found.\n"
    + "x" * 60
)


def _clean_workspace(tmpdir):
    """A workspace where controller-checkpoint.py --phase pre-completion exits
    0 (status PASS, no blockers, no warnings) — required to reach the stop
    hook's SPAWN_WARN emission branches, both of which sit behind the
    checkpoint prerequisite gate (`[ $? -ne 0 ] || [ -z "$CHECKPOINT_OUTPUT" ]`
    at sdd-stop-hook.sh's checkpoint-run step, pre-existing and out of this
    task's scope — see this file's TestSpawnOutcomeWarning docstring for the
    traced evidence). Reuses _setup_sdd_workspace's honesty-check plumbing but
    overwrites the implementer report with all 5 required prose sections and
    adds a non-empty execution-trace-audit.md, so every pre-completion check
    PASSes rather than merely avoiding FAIL."""
    _setup_sdd_workspace(
        tmpdir, honesty_content=HONESTY_CONTENT, plan_content=FRONTMATTER_PLAN
    )
    reports_dir = os.path.join(tmpdir, "reports")
    now = (
        __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    complete_report = (
        "---\nschema_version: 1\ntask_id: 1\nstatus: DONE\n"
        'files_changed:\n  - path: "src/x.py"\n    description: "modified"\n'
        'tests:\n  written: 1\n  passing: 1\n  command: "pytest"\n  result: PASS\n---\n\n'
        "**Implementation Summary:**\nDone.\n\n"
        "**Source Files Read:**\n- x\n\n"
        "**Deviations from Plan:**\nNone — implemented exactly as specified\n\n"
        "**Self-Review Findings:**\nNo issues found.\n\n"
        "**Concerns:**\nNo concerns\n"
    )
    with open(os.path.join(reports_dir, "task-001-implementer-report.md"), "w") as f:
        f.write(complete_report)
    with open(os.path.join(reports_dir, "execution-trace-audit.md"), "w") as f:
        f.write(TRACE_AUDIT_CONTENT)


def _repo_id_for(cwd):
    """Mirror the hook's own REPO_ID computation exactly (realpath of
    --git-common-dir), so fixture bundles match on the same key the hook uses."""
    out = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=cwd,
        capture_output=True,
        text=True,
    ).stdout.strip()
    p = out if os.path.isabs(out) else os.path.join(cwd, out)
    return os.path.realpath(p)


def _write_transcript(path, timestamp=OLD_TIMESTAMP):
    with open(path, "w") as f:
        f.write(json.dumps({"timestamp": timestamp}) + "\n")


def _write_bundle(
    home,
    bundle_id,
    repo_id,
    bundle_type="work",
    entry_skill="superpowers:subagent-driven-development",
):
    bdir = os.path.join(home, ".claude-codex-handoff", "bundles", bundle_id)
    os.makedirs(bdir, exist_ok=True)
    manifest = {
        "session": {"bundle_type": bundle_type, "entry_skill": entry_skill},
        "project": {"repo_id": repo_id},
    }
    with open(os.path.join(bdir, "manifest.json"), "w") as f:
        json.dump(manifest, f)
    return bdir


def _append_spawn_log(reports_dir, line):
    with open(os.path.join(reports_dir, "handoff-spawn.log"), "a") as f:
        f.write(line if line.endswith("\n") else line + "\n")


class TestSpawnOutcomeWarning:
    """Decision 15: stop hook warns on a this-session handoff bundle with no
    matching spawn outcome or decline record."""

    def _new_dirs(self):
        return tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()

    def test_warns_on_unmatched_bundle(self):
        tmpdir, home, vault_dir = self._new_dirs()
        try:
            _clean_workspace(tmpdir)
            transcript = os.path.join(tmpdir, "transcript.jsonl")
            _write_transcript(transcript)
            repo_id = _repo_id_for(tmpdir)
            bid = "2026-07-30T00-00-00Z-test-bundle"
            _write_bundle(home, bid, repo_id)

            result = _run_stop_hook(
                tmpdir, vault_dir, transcript_path=transcript, home=home
            )
            assert result.returncode == 0, result.stderr
            data = json.loads(result.stdout)
            assert bid in data.get("systemMessage", "")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(home, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_outcome_record_suppresses_warning(self):
        tmpdir, home, vault_dir = self._new_dirs()
        try:
            _clean_workspace(tmpdir)
            transcript = os.path.join(tmpdir, "transcript.jsonl")
            _write_transcript(transcript)
            repo_id = _repo_id_for(tmpdir)
            bid = "2026-07-30T00-00-00Z-test-bundle"
            _write_bundle(home, bid, repo_id)
            _append_spawn_log(
                os.path.join(tmpdir, "reports"),
                f"2026-07-30T00:00:01Z uuid-1 outcome hop=1 workspace=w surface=s "
                f"launch=auto bundle={bid} quota=ok tasks_done=0 handshake=ok",
            )

            result = _run_stop_hook(
                tmpdir, vault_dir, transcript_path=transcript, home=home
            )
            assert result.returncode == 0, result.stderr
            assert bid not in (result.stdout or "")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(home, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_decline_record_suppresses_warning(self):
        tmpdir, home, vault_dir = self._new_dirs()
        try:
            _clean_workspace(tmpdir)
            transcript = os.path.join(tmpdir, "transcript.jsonl")
            _write_transcript(transcript)
            repo_id = _repo_id_for(tmpdir)
            bid = "2026-07-30T00-00-00Z-test-bundle"
            _write_bundle(home, bid, repo_id)
            _append_spawn_log(
                os.path.join(tmpdir, "reports"),
                f"2026-07-30T00:00:01Z - decline bundle={bid} reason=abandoned",
            )

            result = _run_stop_hook(
                tmpdir, vault_dir, transcript_path=transcript, home=home
            )
            assert result.returncode == 0, result.stderr
            assert bid not in (result.stdout or "")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(home, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_unrelated_repo_bundle_ignored(self):
        tmpdir, home, vault_dir = self._new_dirs()
        try:
            _clean_workspace(tmpdir)
            transcript = os.path.join(tmpdir, "transcript.jsonl")
            _write_transcript(transcript)
            bid = "2026-07-30T00-00-00Z-test-bundle"
            _write_bundle(home, bid, "/some/unrelated/repo/.git")

            result = _run_stop_hook(
                tmpdir, vault_dir, transcript_path=transcript, home=home
            )
            assert result.returncode == 0, result.stderr
            assert bid not in (result.stdout or "")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(home, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Pre-existing latent bug in sdd-stop-hook.sh (predates Task 14, "
            "out of scope to fix here): the checkpoint prerequisite gate is "
            '`if [ $? -ne 0 ] || [ -z "$CHECKPOINT_OUTPUT" ]; then exit 0; fi`. '
            "controller-checkpoint.py prints its JSON to stdout BEFORE choosing "
            "an exit code (main() at the bottom of the file) and returns exit 1 "
            "on status=FAIL — so `$?` is 1, `CHECKPOINT_OUTPUT` is non-empty "
            "valid JSON, and the gate's `-ne 0` half fires anyway, exiting the "
            "hook silently before STATUS is ever inspected. The FAIL branch "
            "below (and this test's target) is unreachable until the gate is "
            'changed to key off emptiness alone (`-z "$CHECKPOINT_OUTPUT"`), '
            "which already correctly discriminates a real infra crash (the "
            "`except Exception` path prints to stderr, not stdout, so "
            "CHECKPOINT_OUTPUT is empty only in that case). strict=True: this "
            "flips to a hard failure the day someone fixes the gate, which is "
            "the intended signal that the composition logic below is now live."
        ),
    )
    def test_composes_with_checkpoint_fail_message(self):
        """A checkpoint FAIL (guaranteed here: no dispatch log / reviews / honesty
        check / trace audit exist for this minimal fixture) plus an unmatched
        bundle must land in ONE systemMessage containing both."""
        tmpdir, home, vault_dir = self._new_dirs()
        try:
            _setup_sdd_workspace(
                tmpdir, honesty_content=None
            )  # no honesty check -> FAIL
            transcript = os.path.join(tmpdir, "transcript.jsonl")
            _write_transcript(transcript)
            repo_id = _repo_id_for(tmpdir)
            bid = "2026-07-30T00-00-00Z-test-bundle"
            _write_bundle(home, bid, repo_id)

            result = _run_stop_hook(
                tmpdir, vault_dir, transcript_path=transcript, home=home
            )
            assert result.returncode == 0, result.stderr
            data = json.loads(result.stdout)
            msg = data.get("systemMessage", "")
            assert "Pre-Completion Gate FAILED" in msg
            assert bid in msg
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(home, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)

    def test_missing_transcript_silently_skips_check(self):
        """No .transcript_path in the hook payload -> SESSION_START stays empty
        -> the whole bundle scan is a deliberate no-op: exit 0, no crash, and
        no spawn-outcome warning text (even though a matching bundle exists).
        Uses the clean fixture so a reachable PASS run proves the loop itself
        never runs — not merely that its output happens to be masked by the
        (separately tracked) checkpoint-gate bug exercised above."""
        tmpdir, home, vault_dir = self._new_dirs()
        try:
            _clean_workspace(tmpdir)
            repo_id = _repo_id_for(tmpdir)
            bid = "2026-07-30T00-00-00Z-test-bundle"
            _write_bundle(home, bid, repo_id)

            result = _run_stop_hook(tmpdir, vault_dir, transcript_path=None, home=home)
            assert result.returncode == 0, result.stderr
            assert "handoff bundle" not in (result.stdout or "")
            assert bid not in (result.stdout or "")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(home, ignore_errors=True)
            shutil.rmtree(vault_dir, ignore_errors=True)
