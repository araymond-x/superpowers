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


import pytest


@pytest.mark.parametrize(
    "bundle_id,manifest,needle",
    [
        ("bad id!", "valid-manifest.json", "charset"),
        ("b1", "wrong-type-manifest.json", "bundle_type"),
        ("b1", "wrong-skill-manifest.json", "entry_skill"),
        ("b1", "foreign-repo-manifest.json", "repo"),
    ],
)
def test_bundle_validation_failures_exit_1(tmp_path, bundle_id, manifest, needle):
    ctx = setup_worktree(tmp_path)
    if bundle_id == "b1":
        install_bundle(tmp_path, "b1", manifest, ctx["repo_id"])
    r = run_spawn(ctx, tmp_path, bundle_id)
    assert r.returncode == 1 and needle in (r.stdout + r.stderr).lower()


def test_bundle_dir_missing_exits_1(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "does-not-exist")
    assert r.returncode == 1


def test_not_in_cmux_exits_3_with_instructions(tmp_path):
    ctx = setup_worktree(tmp_path)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    r = run_spawn(ctx, tmp_path, "b1", in_cmux=False)
    assert r.returncode == 3 and "/pickup b1" in (r.stdout + r.stderr)


def test_ping_failure_exits_3(tmp_path):
    ctx = setup_worktree(tmp_path)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    r = run_spawn(ctx, tmp_path, "b1", env_extra={"CMUX_PING_FAIL": "1"})
    assert r.returncode == 3


def test_hop_limit_exits_3(tmp_path):
    ctx = setup_worktree(tmp_path)
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    (ctx["reports"] / ".handoff-hops").write_text("3\n")
    # .handoff-hops is tracked (spec.md L164); at the moment the hop gate runs in
    # the real flow it is always committed (the successor's step-2 commit folds it
    # in before the next spawn invocation). Commit the seed here so the fixture is
    # faithful to that invariant and doesn't spuriously trip Precondition 1 (clean
    # tree) — mirrors the commit pattern in test_missing_active_feature_exits_1.
    subprocess.run(["git", "add", "-A"], cwd=ctx["wt"], check=True)
    subprocess.run(["git", "commit", "-qm", "seed hops"], cwd=ctx["wt"], check=True)
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 3 and "hop" in (r.stdout + r.stderr).lower()


from spawn_handoff_helpers import (
    PACE_OK,
    PACE_LOW,
    PACE_MALFORMED,
    PACE_MISSING_FIELD,
    PACE_MISSING_WINDOW,
    PACE_NONZERO,
)


def _spawnable(tmp_path, ctx):
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])


def test_quota_low_exits_3(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", pace_body=PACE_LOW)
    assert r.returncode == 3 and "quota" in (r.stdout + r.stderr).lower()


@pytest.mark.parametrize(
    "pace_body",
    [PACE_MALFORMED, PACE_MISSING_FIELD, PACE_MISSING_WINDOW, PACE_NONZERO],
)
def test_quota_unchecked_classes_proceed(tmp_path, pace_body):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", pace_body=pace_body)
    assert r.returncode == 0 and "quota=unchecked" in (r.stdout + r.stderr)


def test_quota_tool_absent_proceeds(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra={"SUPERPOWERS_CMUX_QUOTA_TOOL": str(tmp_path / "nope")},
    )
    assert r.returncode == 0 and "quota=unchecked" in (r.stdout + r.stderr)


def test_quota_ok_proceeds(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", pace_body=PACE_OK)
    assert r.returncode == 0 and "quota=ok" in (r.stdout + r.stderr)


def test_quota_threshold_reads_env_not_hardcoded_default(tmp_path):
    # Shared-constant guard: the healthy PACE_OK reading (63.0%) may only classify
    # `low` if $QUOTA_MIN_PCT is genuinely consulted. A hardcoded 15 passes every
    # other quota test in this file but fails this one.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        pace_body=PACE_OK,
        env_extra={"SUPERPOWERS_CMUX_QUOTA_MIN_PCT": "70"},
    )
    assert r.returncode == 3 and "quota=low" in (r.stdout + r.stderr).lower()


def test_quota_threshold_boundary_is_strict_less_than(tmp_path):
    # pct == threshold is NOT low (the comparison is strict `<`).
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        pace_body=PACE_OK,
        env_extra={"SUPERPOWERS_CMUX_QUOTA_MIN_PCT": "63"},
    )
    assert r.returncode == 0 and "quota=ok" in (r.stdout + r.stderr)


def test_quota_tool_timeout_proceeds(tmp_path):
    # Timeout class: the watchdog kills a hung tool, rc != 0 => fail-open.
    # Bounded at 1s deliberately — this must never approach a CI stall.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        pace_body="exec sleep 20",
        env_extra={"SUPERPOWERS_CMUX_QUOTA_TIMEOUT": "1"},
    )
    assert r.returncode == 0 and "quota=unchecked" in (r.stdout + r.stderr)
