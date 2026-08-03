"""Unit tests for hooks/session-start's cmux-spawn-v2 handshake signal.

When SUPERPOWERS_SPAWN_ID is set and cmux is on PATH, the hook must fire a
backgrounded `cmux wait-for -S sdd-hop-<id>` without ever affecting the hook's
own exit code or JSON stdout contract (the hook runs under `set -euo
pipefail`). Covers: signal fires, no spawn id -> no signal, cmux absent, cmux
failing, cmux hanging (proves true backgrounding, not just `set -e` survival).

Run: .venv/bin/python3 -m pytest tests/unit/test_session_start_signal.py -v
"""

import json
import os
import time

import pytest

HOOK_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "hooks", "session-start")
)


def _path_without(path, name):
    """`path` with every entry that provides `name` removed (real absence, not
    just a shadowed stub — mirrors spawn_handoff_helpers._path_without)."""
    import os as _os

    return _os.pathsep.join(
        d
        for d in path.split(_os.pathsep)
        if d and not _os.path.exists(_os.path.join(d, name))
    )


def _make_cmux_stub(dirpath, body):
    p = dirpath / "cmux"
    p.write_text("#!/usr/bin/env bash\n" + body + "\n")
    os.chmod(p, 0o755)
    return p


def _run_hook(tmp_path, env_extra=None, stub_body=None, cmux_absent=False):
    """Run hooks/session-start with a controllable cmux stub on PATH."""
    stubs = tmp_path / "stubs"
    stubs.mkdir(exist_ok=True)
    env = dict(os.environ)
    if cmux_absent:
        env["PATH"] = _path_without(env["PATH"], "cmux")
    else:
        _make_cmux_stub(stubs, stub_body or 'echo "$@" >> "$CMUX_LOG"; exit 0')
        env["PATH"] = f"{stubs}:{env['PATH']}"
    env["CLAUDE_PLUGIN_ROOT"] = str(
        tmp_path
    )  # branch selector only, not path resolution
    env["CMUX_LOG"] = str(tmp_path / "cmux.log")
    if env_extra:
        env.update(env_extra)
    import subprocess

    start = time.monotonic()
    result = subprocess.run(
        ["bash", HOOK_PATH], capture_output=True, text=True, timeout=10, env=env
    )
    elapsed = time.monotonic() - start
    return result, elapsed


def _poll_log_contains(tmp_path, substring, timeout=2.0):
    log_path = tmp_path / "cmux.log"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if log_path.exists() and substring in log_path.read_text():
            return True
        time.sleep(0.05)
    return log_path.exists() and substring in log_path.read_text()


def test_signal_fires_when_spawn_id_set(tmp_path):
    result, _ = _run_hook(tmp_path, env_extra={"SUPERPOWERS_SPAWN_ID": "abc"})
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert (
        "hookSpecificOutput" in data
        or "additional_context" in data
        or "additionalContext" in data
    )
    assert _poll_log_contains(tmp_path, "wait-for -S sdd-hop-abc")


def test_no_spawn_id_no_signal(tmp_path):
    result, _ = _run_hook(tmp_path, env_extra={"SUPERPOWERS_SPAWN_ID": ""})
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)  # still valid JSON
    # Give the (nonexistent) background job the same window as the positive
    # test before concluding absence.
    time.sleep(0.3)
    log_path = tmp_path / "cmux.log"
    assert not log_path.exists() or "wait-for" not in log_path.read_text()


def test_cmux_absent_never_breaks_hook(tmp_path):
    result, _ = _run_hook(
        tmp_path, env_extra={"SUPERPOWERS_SPAWN_ID": "abc"}, cmux_absent=True
    )
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)  # valid JSON despite cmux being unresolvable


def test_cmux_present_but_failing_never_breaks_hook(tmp_path):
    result, _ = _run_hook(
        tmp_path,
        env_extra={"SUPERPOWERS_SPAWN_ID": "abc"},
        stub_body='echo "$@" >> "$CMUX_LOG"; exit 1',
    )
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)  # valid JSON despite the binary failing


def test_cmux_present_but_hanging_never_blocks_hook(tmp_path):
    result, elapsed = _run_hook(
        tmp_path,
        env_extra={"SUPERPOWERS_SPAWN_ID": "abc"},
        stub_body='echo "$@" >> "$CMUX_LOG"; sleep 5',
    )
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)
    assert elapsed < 2.0, f"hook took {elapsed:.2f}s — not truly backgrounded"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
