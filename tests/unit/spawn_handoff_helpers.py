"""Harness for spawn-handoff-session.sh subprocess tests."""

import base64
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = (
    ROOT
    / "skills"
    / "subagent-driven-development"
    / "scripts"
    / "spawn-handoff-session.sh"
)
FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"

PACE_OK = 'echo "{\\"windows\\":[{\\"key\\":\\"session\\",\\"remaining_pct\\":63.0}]}"'
PACE_LOW = 'echo "{\\"windows\\":[{\\"key\\":\\"session\\",\\"remaining_pct\\":8.0}]}"'
PACE_MALFORMED = 'echo "not json {{{"'
PACE_MISSING_FIELD = 'echo "{\\"windows\\":[{\\"key\\":\\"session\\"}]}"'
PACE_MISSING_WINDOW = (
    'echo "{\\"windows\\":[{\\"key\\":\\"week_all\\",\\"remaining_pct\\":50.0}]}"'
)
PACE_NONZERO = "exit 7"


def encode_args(argv):
    return "v1:" + base64.b64encode(json.dumps(argv).encode()).decode()


def make_stub(dirpath, name, body):
    p = dirpath / name
    p.write_text("#!/usr/bin/env bash\n" + body + "\n")
    os.chmod(p, 0o755)


def setup_worktree(tmp_path):
    """Clean git worktree with .active-feature + reports dir. Returns context dict."""
    wt = tmp_path / "wt"
    wt.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=wt, check=True)
    feat = "docs/imp-plans/feat"
    (wt / feat / "reports").mkdir(parents=True)
    (wt / ".active-feature").write_text(feat + "\n")
    (wt / "seed").write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=wt, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=wt, check=True)
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"], cwd=wt, capture_output=True, text=True
    ).stdout.strip()
    repo_id = os.path.realpath(
        str(wt / common) if not os.path.isabs(common) else common
    )
    return {
        "wt": wt,
        "feat": feat,
        "reports": wt / feat / "reports",
        "repo_id": repo_id,
    }


def install_bundle(tmp_path, bundle_id, manifest_src, repo_id):
    bdir = tmp_path / "home" / ".claude-codex-handoff" / "bundles" / bundle_id
    bdir.mkdir(parents=True)
    m = json.loads((FIX / manifest_src).read_text())
    if m["project"]["repo_id"] == "__REPO_ID__":
        m["project"]["repo_id"] = repo_id
    (bdir / "manifest.json").write_text(json.dumps(m))
    return bdir


def install_version(tmp_path, version):
    # Version MUST be an executable regular file (picker: `find -type f -perm -u+x`).
    vdir = tmp_path / "home" / ".local" / "share" / "claude" / "versions"
    vdir.mkdir(parents=True, exist_ok=True)
    binf = vdir / version
    binf.write_text("#!/bin/sh\n")
    os.chmod(binf, 0o755)


def run_spawn(
    ctx,
    tmp_path,
    *args,
    env_extra=None,
    in_cmux=True,
    pace_body=PACE_OK,
    picker_body=None,
    cmux_body=None,
):
    stubs = tmp_path / "stubs"
    stubs.mkdir(exist_ok=True)
    make_stub(
        stubs,
        "cmux",
        cmux_body
        or (
            'if [ "$1" = "ping" ]; then [ -n "$CMUX_PING_FAIL" ] && { echo NOPE; exit 1; }; echo PONG; exit 0; fi\n'
            'echo "$@" >> "$CMUX_LOG"; exit 0'
        ),
    )
    make_stub(
        stubs,
        "claude-picker",
        picker_body
        or ('if [ "$1" = "--handoff-contract" ]; then echo 1; exit 0; fi\nexit 0'),
    )
    make_stub(stubs, "claude-usage-pace", pace_body)
    env = dict(os.environ)
    env["PATH"] = f"{stubs}:{env['PATH']}"
    env["HOME"] = str(tmp_path / "home")
    env["CMUX_LOG"] = str(tmp_path / "cmux.log")
    env["SUPERPOWERS_ROOT"] = str(ROOT)
    if in_cmux:
        env["CMUX_WORKSPACE_ID"] = "TEST-WS"
    else:
        env.pop("CMUX_WORKSPACE_ID", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=str(ctx["wt"]),
        capture_output=True,
        text=True,
        env=env,
    )
