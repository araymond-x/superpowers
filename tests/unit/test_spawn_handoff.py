"""Unit matrix for spawn-handoff-session.sh (SDD auto-spawn tool).

The bash script is driven via subprocess with stub `cmux`, `claude-picker`, and
`claude-usage-pace` on a per-test PATH (harness in spawn_handoff_helpers.py).
Pattern mirrors test_context_gate_tier.py.
"""

import json
from pathlib import Path

FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"

# Contract facts frozen from live `cmux --help` (2026-07-22). If cmux renames a
# flag, the exact-argv assertions in later tasks must be updated too.
CMUX_NEW_WORKSPACE_FLAGS = ["--name", "--cwd", "--command", "--focus"]
CMUX_NOTIFY_FLAGS = ["--title", "--body"]
PICKER_CONTRACT_VERSION = "1"

# claude-picker exports FOUR forwarding vars on EVERY launch path (verified vs
# telemetry-exp launchers/claude-picker v1). The 4th (APPEND_PROMPT = base64 of
# the --append-system-prompt-file CONTENTS) is the designed remedy for a dead/temp
# append path and MUST be consumed (decode->rematerialize->substitute; Task 4).
# Telemetry-on = inherited CLAUDE_CODE_ENABLE_TELEMETRY=1 (via telemetry-vars.sh).
PICKER_EXPORTS = [
    "CLAUDE_CODE_PICKER_VERSION",
    "CLAUDE_CODE_PICKER_LABEL",
    "CLAUDE_CODE_PICKER_ARGS",
    "CLAUDE_CODE_PICKER_APPEND_PROMPT",
]


def test_fixtures_shape_matches_contract():
    valid = json.loads((FIX / "valid-manifest.json").read_text())
    assert valid["session"]["bundle_type"] == "work"
    assert valid["session"]["entry_skill"] == "superpowers:subagent-driven-development"
    assert "repo_id" in valid["project"]
    assert (
        json.loads((FIX / "wrong-type-manifest.json").read_text())["session"][
            "bundle_type"
        ]
        == "review"
    )
    assert (
        json.loads((FIX / "wrong-skill-manifest.json").read_text())["session"][
            "entry_skill"
        ]
        != "superpowers:subagent-driven-development"
    )
    assert (
        json.loads((FIX / "foreign-repo-manifest.json").read_text())["project"][
            "repo_id"
        ]
        == "/some/other/repo/.git"
    )
    assert (
        "CLAUDE_CODE_PICKER_APPEND_PROMPT" in PICKER_EXPORTS
    )  # 4th export is consumed (Task 4)


import os
import subprocess
from spawn_handoff_helpers import setup_worktree, install_bundle, run_spawn, SCRIPT


def test_script_exists_and_executable():
    assert SCRIPT.exists() and os.access(SCRIPT, os.X_OK)


def test_no_bundle_id_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path)
    assert r.returncode == 1 and "BUNDLE_ID" in (r.stdout + r.stderr)


def test_unknown_flag_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "--bogus", "b1")
    assert r.returncode == 1


def test_missing_active_feature_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    (ctx["wt"] / ".active-feature").unlink()
    subprocess.run(["git", "commit", "-aqm", "rm af"], cwd=ctx["wt"], check=True)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 1 and "active-feature" in (r.stdout + r.stderr)


def test_dirty_tree_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    (ctx["wt"] / "dirty").write_text("y")  # uncommitted
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 1 and "clean" in (r.stdout + r.stderr).lower()
