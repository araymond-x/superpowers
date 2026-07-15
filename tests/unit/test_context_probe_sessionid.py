"""Subprocess tests for context-probe.py --session-id / env-var resolution.

Exercises the Task-2 resolver additions: --session-id globs
~/.claude/projects/*/<id>.jsonl by filename, and $CLAUDE_CODE_SESSION_ID is the
standalone fallback. Each test redirects HOME to a tmp_path so the probe globs a
sandboxed projects dir. The differential test asserts byte-for-byte parity with
the installed claude-ctx-check on a well-formed fixture (skipped where the tool
is absent).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
PROBE = ROOT / "skills" / "subagent-driven-development" / "scripts" / "context-probe.py"
FIX = Path(__file__).parent / "fixtures" / "context-probe"


def test_session_id_resolution(tmp_path):
    projects = tmp_path / ".claude" / "projects" / "proj"
    projects.mkdir(parents=True)
    sid = "test-session-xyz"
    shutil.copy(FIX / "below.jsonl", projects / f"{sid}.jsonl")
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, str(PROBE), "--session-id", sid],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "250000"


def test_no_session_id_nonzero_exit():
    env = dict(os.environ)
    env.pop("CLAUDE_CODE_SESSION_ID", None)
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode != 0


def test_env_var_resolution(tmp_path):
    projects = tmp_path / ".claude" / "projects" / "p"
    projects.mkdir(parents=True)
    shutil.copy(FIX / "soft.jsonl", projects / "env-sess.jsonl")
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env["CLAUDE_CODE_SESSION_ID"] = "env-sess"
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "350000"


@pytest.mark.skipif(
    not (Path.home() / ".claude" / "bin" / "claude-ctx-check").is_file(),
    reason="claude-ctx-check not installed on this machine",
)
def test_differential_parity_with_ctx_check(tmp_path):
    ctx_check = Path.home() / ".claude" / "bin" / "claude-ctx-check"
    projects = tmp_path / ".claude" / "projects" / "proj"
    projects.mkdir(parents=True)
    shutil.copy(FIX / "hard.jsonl", projects / "diff-sess.jsonl")
    env = dict(os.environ)
    env["HOME"] = str(tmp_path)
    env["CLAUDE_CODE_SESSION_ID"] = "diff-sess"
    probe = subprocess.run(
        [sys.executable, str(PROBE)],
        capture_output=True,
        text=True,
        env=env,
    )
    ctx = subprocess.run(
        [sys.executable, str(ctx_check), "--json"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert probe.returncode == 0, probe.stderr
    assert ctx.returncode == 0, ctx.stderr
    assert int(probe.stdout.strip()) == json.loads(ctx.stdout)["total_tokens"]
