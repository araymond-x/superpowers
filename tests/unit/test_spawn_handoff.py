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


# --- Task 4: launch composition A (decode / strip guard / label / telemetry) ---

from spawn_handoff_helpers import encode_args, install_version

# The forwarding metadata this file exercises is REAL ambient env on any machine
# whose own session was launched through claude-picker (the developer's is). Since
# run_spawn snapshots os.environ, an "absent var" case would silently inherit that
# live value — telemetry-off and append-prompt-empty would both test the opposite
# of what they claim. Scrub the five vars for every test in this module so absent
# means absent (and so the pre-Task-4 tests never decode a real payload either).
PICKER_ENV_VARS = [
    "CLAUDE_CODE_PICKER_VERSION",
    "CLAUDE_CODE_PICKER_LABEL",
    "CLAUDE_CODE_PICKER_ARGS",
    "CLAUDE_CODE_PICKER_APPEND_PROMPT",
    "CLAUDE_CODE_ENABLE_TELEMETRY",
]


@pytest.fixture(autouse=True)
def _hermetic_picker_env(monkeypatch):
    for var in PICKER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def _meta(
    version="2.1.218",
    args_b64=None,
    label="Proj-Session-2",
    telem="1",
    append_b64=None,
):
    e = {"CLAUDE_CODE_PICKER_VERSION": version}
    if args_b64 is not None:
        e["CLAUDE_CODE_PICKER_ARGS"] = args_b64
    if label is not None:
        e["CLAUDE_CODE_PICKER_LABEL"] = label
    if telem is not None:
        e["CLAUDE_CODE_ENABLE_TELEMETRY"] = telem
    if append_b64 is not None:
        e["CLAUDE_CODE_PICKER_APPEND_PROMPT"] = append_b64
    return e


def test_decoded_args_and_strip_guard(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    args = ["--append-system-prompt-file", "/tmp/a b.md", "/pickup old-bundle"]
    r = run_spawn(
        ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64=encode_args(args))
    )
    out = r.stdout + r.stderr
    assert "forwarded=" in out
    assert "--append-system-prompt-file" in out and "a b.md" in out
    assert "/pickup old-bundle" not in out  # stale /pickup stripped


def test_telemetry_on_and_off(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r_on = run_spawn(
        ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64=encode_args([]))
    )
    assert "telemetry=on" in (r_on.stdout + r_on.stderr)
    r_off = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra=_meta(args_b64=encode_args([]), telem=None),
    )
    assert "telemetry=off" in (r_off.stdout + r_off.stderr)


@pytest.mark.parametrize(
    "in_label,expect",
    [
        ("", ""),  # empty stays empty
        ("Proj", "Proj-Session-2"),  # unsuffixed gains -Session-2
        ("Proj-Session-4", "Proj-Session-5"),
        ("!!!", ""),  # empty-after-sanitize
    ],
)
def test_label_rule(tmp_path, in_label, expect):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra=_meta(args_b64=encode_args([]), label=in_label),
    )
    assert f"label=[{expect}]" in (r.stdout + r.stderr)


def test_label_255_boundary(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra=_meta(args_b64=encode_args([]), label="A" * 300),
    )
    import re

    m = re.search(r"label=\[([^\]]*)\]", r.stdout + r.stderr)
    assert m and len(m.group(1)) <= 255 and m.group(1).endswith("-Session-2")


@pytest.mark.parametrize(
    "argv",
    [
        ["--append-system-prompt-file", "/tmp/gone-temp.md"],  # space form
        ["--append-system-prompt-file=/tmp/gone-temp.md"],  # =-joined form
    ],
)
def test_append_prompt_substituted_in_forwarded(tmp_path, argv):
    # APPEND_PROMPT content present -> dead path substituted with rematerialized path.
    import base64

    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    env = _meta(
        args_b64=encode_args(argv),
        append_b64=base64.b64encode(b"prompt body").decode(),
    )
    out = (lambda r: r.stdout + r.stderr)(
        run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env)
    )
    assert "/tmp/gone-temp.md" not in out and "append-prompts/b1-hop1.md" in out


def test_append_prompt_empty_keeps_original_path(tmp_path):
    # Empty-but-flag-present (APPEND_PROMPT absent): cannot rematerialize -> keep path.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    env = _meta(
        args_b64=encode_args(["--append-system-prompt-file", "/tmp/orig.md"])
    )  # no APPEND_PROMPT
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env)
    assert "/tmp/orig.md" in (r.stdout + r.stderr)


# --- Task 5: launch composition B (auto preflight + compose-side quoting) ------

MARKER = "[spawn-handoff] successor command: "


def _successor_cmd(r):
    """Isolate the composed `--command` string from every other diagnostic line.

    Task 4's `forwarded=` line ALREADY echoes `--append-system-prompt-file` and
    `a b.md` to stderr, so asserting those tokens against raw stdout+stderr would
    pass even if this task's compose block never ran. Every compose assertion
    anchors on this line so it can only be satisfied by the composed command.
    """
    lines = [
        ln for ln in (r.stdout + r.stderr).splitlines() if ln.startswith(MARKER)
    ]
    assert lines, "no `successor command:` line emitted"
    return lines[0][len(MARKER) :]


def test_auto_mode_composes_exact_command(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    args = ["--append-system-prompt-file", "/tmp/a b.md"]
    r = run_spawn(
        ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64=encode_args(args))
    )
    assert "launch=auto" in (r.stdout + r.stderr)
    cmd = _successor_cmd(r)
    for tok in [
        "claude-picker",
        "--non-interactive",
        "--pick-version 2.1.218",
        "--telemetry on",
        "--session-label",
        "/pickup b1",
    ]:
        assert tok in cmd
    assert "a b.md" in cmd  # compose-side quoting preserved the space
    assert "runtime-picker-failure" in cmd  # embedded residual fallback chain


def test_composed_command_reparses_with_correct_arity(tmp_path):
    # The composed string is re-parsed by a shell INSIDE the spawned workspace, so
    # substring presence is not enough: each space-bearing element must arrive as
    # ONE argv element. A naive space-join would split `/tmp/a b.md` in two and
    # send the picker a bare `/pickup` plus a stray `b1`.
    import shlex

    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    args = ["--append-system-prompt-file", "/tmp/a b.md"]
    r = run_spawn(
        ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64=encode_args(args))
    )
    argv = shlex.split(_successor_cmd(r).split(" || ", 1)[0])
    assert argv[0] == "claude-picker"
    assert "/tmp/a b.md" in argv
    assert argv[-1] == "/pickup b1"


@pytest.mark.parametrize("env_extra", [{}, {"CLAUDE_CODE_PICKER_VERSION": "9.9.9"}])
def test_picker_manual_when_metadata_degraded(tmp_path, env_extra):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env_extra)
    assert "launch=picker-manual" in (r.stdout + r.stderr)
    # The picker-manual branch is the user-facing safety net — assert what it
    # actually composes, not just the mode. Without this the branch could emit
    # anything at all and the suite would stay green.
    assert _successor_cmd(r) == "claude-picker '/pickup b1'"


def test_empty_label_omits_session_label(tmp_path):
    # spec §5.4b: an empty label result omits --session-label entirely. Every other
    # auto-path case passes a non-empty label, so without this the omission guard
    # can be deleted with the suite still green.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra=_meta(args_b64=encode_args([]), label=""),
    )
    assert "launch=auto" in (r.stdout + r.stderr)  # an empty label never blocks auto
    cmd = _successor_cmd(r)
    assert "--session-label" not in cmd
    assert "--telemetry on" in cmd  # the flags around the omitted pair still compose


def test_picker_manual_when_contract_wrong(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra=_meta(args_b64=encode_args([])),
        picker_body='if [ "$1" = "--handoff-contract" ]; then echo 2; exit 0; fi\nexit 0',
    )
    assert "launch=picker-manual" in (r.stdout + r.stderr)


def test_bad_codec_degrades_to_picker_manual(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(
        ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64="not-a-v1-codec")
    )
    assert "launch=picker-manual" in (r.stdout + r.stderr)


def test_corrupt_v1_body_degrades_to_picker_manual(tmp_path):
    # A valid `v1:` prefix but a garbage base64/JSON body must set ARGS_OK=0 and
    # degrade to picker-manual — never launch=auto with the forwarded args dropped.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(
        ctx, tmp_path, "b1", "--dry-run", env_extra=_meta(args_b64="v1:!!!not-base64!!!")
    )
    assert "launch=picker-manual" in (r.stdout + r.stderr)


# --- Task 6: spawn sequence, reservation ordering, exit codes, --dry-run -------

import re

UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def _reach_spawn(tmp_path, ctx):
    """Env that reaches the spawn sequence in launch=auto mode."""
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    return _meta(args_b64=encode_args(["--append-system-prompt-file", "/tmp/x.md"]))


def _fallback_spawn_id(cmd):
    """Spawn-id field of the composed runtime-picker-failure tail (spec §5.4d).

    Anchored on the runtime-deferred `$(date …)` substitution so it reads the
    ACTUAL positional field rather than "some uuid somewhere in the string" —
    the composed command also carries a `/pickup` id and a log path, and a loose
    search would keep passing with the field itself still wrong.
    """
    tail = cmd.split(" || ", 1)[1] if " || " in cmd else ""
    m = re.search(r'"\$\(date[^)]*\)"\s+(\S+)', tail)
    assert m, f"no spawn-id field in composed fallback tail: {tail!r}"
    return m.group(1).strip('"')


def _spawn_log_records(ctx):
    """[(record_type, spawn_id)] from handoff-spawn.log, in file order."""
    lines = (ctx["reports"] / "handoff-spawn.log").read_text().splitlines()
    return [(f[2], f[1]) for f in (ln.split() for ln in lines) if len(f) > 2]


def test_dry_run_spawns_nothing(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(
        ctx, tmp_path, "b1", "--dry-run", env_extra=_reach_spawn(tmp_path, ctx)
    )
    assert r.returncode == 0
    logged = (
        (tmp_path / "cmux.log").read_text() if (tmp_path / "cmux.log").exists() else ""
    )
    assert "new-workspace" not in logged
    assert not (ctx["reports"] / ".handoff-hops").exists()
    assert not (ctx["reports"] / "handoff-spawn.log").exists()


def test_auto_spawn_success_exit_0(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx))
    assert r.returncode == 0
    logged = (tmp_path / "cmux.log").read_text()
    assert "new-workspace" in logged
    for tok in ["--name", "--cwd", "--command", "--focus false"]:
        assert tok in logged
    assert "notify" in logged and "--title" in logged
    records = _spawn_log_records(ctx)
    kinds = [k for k, _ in records]
    assert kinds.index("intent") < kinds.index("outcome")
    assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"
    # §5.4d: ONE spawn id ties the whole hop together — the intent record, the
    # success outcome, and the runtime-failure record the CHILD may append from
    # the composed fallback tail. Assert identity across all three, not shape:
    # two independently generated uuids satisfy every "is a uuid" check while
    # destroying the correlation the id exists for.
    ids = {i for _, i in records}
    assert len(ids) == 1, f"spawn ids diverge across records: {records}"
    spawn_id = ids.pop()
    assert UUID_RE.fullmatch(spawn_id)
    assert _fallback_spawn_id(_successor_cmd(r)) == spawn_id


def test_spawn_failure_keeps_hop_exits_3(tmp_path):
    ctx = setup_worktree(tmp_path)
    body = (
        'if [ "$1" = "ping" ]; then echo PONG; exit 0; fi\n'
        'if [ "$1" = "new-workspace" ]; then echo "$@" >> "$CMUX_LOG"; exit 5; fi\n'
        'echo "$@" >> "$CMUX_LOG"; exit 0'
    )
    r = run_spawn(
        ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx), cmux_body=body
    )
    assert r.returncode == 3
    # The hop stays consumed even though the spawn FAILED — only possible if the
    # reservation ran first. This, not log ordering, is Decision 21's real guard.
    assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"
    assert "spawn-failed" in (ctx["reports"] / "handoff-spawn.log").read_text()
    assert "/pickup b1" in (r.stdout + r.stderr)
    records = _spawn_log_records(ctx)
    ids = {i for _, i in records}
    assert len(ids) == 1, f"spawn ids diverge across records: {records}"
    assert UUID_RE.fullmatch(ids.pop())


def test_notify_failure_still_exit_0(tmp_path):
    ctx = setup_worktree(tmp_path)
    body = (
        'if [ "$1" = "ping" ]; then echo PONG; exit 0; fi\n'
        'if [ "$1" = "notify" ]; then exit 9; fi\n'
        'echo "$@" >> "$CMUX_LOG"; exit 0'
    )
    r = run_spawn(
        ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx), cmux_body=body
    )
    assert r.returncode == 0


def test_picker_manual_spawn_uses_interactive_command(tmp_path):
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)  # no metadata => picker-manual
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 0
    logged = (tmp_path / "cmux.log").read_text()
    assert "new-workspace" in logged
    assert "--non-interactive" not in logged
    assert "/pickup b1" in logged


def test_append_prompt_file_written_on_real_spawn(tmp_path):
    # On a real (non-dry-run) spawn, the append-prompt CONTENT is rematerialized
    # to the stable path and the forwarded --append-system-prompt-file points at
    # it. This is the FIRST test to drive that write path (every Task-4 case was
    # --dry-run), so it is also what covers the makedirs-with-the-write fix.
    import base64

    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    content = b"# forwarded system prompt\nBe concise.\n"
    env = _meta(
        args_b64=encode_args(["--append-system-prompt-file", "/tmp/gone.md"]),
        append_b64=base64.b64encode(content).decode(),
    )
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
    assert r.returncode == 0
    target = (
        tmp_path / "home" / ".claude-codex-handoff" / "append-prompts" / "b1-hop1.md"
    )
    assert target.read_bytes() == content
    assert "append-prompts/b1-hop1.md" in (tmp_path / "cmux.log").read_text()


def test_fallback_tail_spawn_id_is_a_uuid(tmp_path):
    # spec §5.4d names the spawn id as the second field of EVERY record type,
    # including `runtime-picker-failure`. The composed tail shipped a literal
    # `spawn` there; the pre-existing `runtime-picker-failure` token assertion
    # passes with that bug fully present, so this is the discriminating check.
    ctx = setup_worktree(tmp_path)
    r = run_spawn(
        ctx, tmp_path, "b1", "--dry-run", env_extra=_reach_spawn(tmp_path, ctx)
    )
    assert r.returncode == 0
    assert UUID_RE.fullmatch(_fallback_spawn_id(_successor_cmd(r)))


def test_fallback_tail_spawn_id_correlates_with_intent_record(tmp_path):
    # Identity, not shape: generating a second uuid inside the spawn sequence
    # leaves every "is a uuid" assertion green while the child's runtime-failure
    # record no longer correlates to the parent's intent record.
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx))
    assert r.returncode == 0
    intent = [i for k, i in _spawn_log_records(ctx) if k == "intent"]
    assert len(intent) == 1
    assert _fallback_spawn_id(_successor_cmd(r)) == intent[0]


def test_reservation_lands_before_cmux_new_workspace_runs(tmp_path):
    # Decision 21 is about WHEN the reservation happens, not the order the lines
    # end up in the file. Writing `intent` AFTER the spawn but before the outcome
    # leaves the file order intact and every ordering assertion green — verified
    # by mutation. So ask the spawn itself: the stub snapshots both reservation
    # artifacts at `new-workspace` time, which is the only moment that proves the
    # hop was already consumed when the workspace was created.
    ctx = setup_worktree(tmp_path)
    body = (
        'if [ "$1" = "ping" ]; then echo PONG; exit 0; fi\n'
        'if [ "$1" = "new-workspace" ]; then\n'
        '  cp "$SPAWN_LOG_PROBE" "$CMUX_LOG.log-at-spawn" 2>/dev/null\n'
        '  cp "$HOPS_PROBE" "$CMUX_LOG.hops-at-spawn" 2>/dev/null\n'
        "fi\n"
        'echo "$@" >> "$CMUX_LOG"; exit 0'
    )
    env = _reach_spawn(tmp_path, ctx)
    env["SPAWN_LOG_PROBE"] = str(ctx["reports"] / "handoff-spawn.log")
    env["HOPS_PROBE"] = str(ctx["reports"] / ".handoff-hops")
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env, cmux_body=body)
    assert r.returncode == 0
    at_spawn = tmp_path / "cmux.log.log-at-spawn"
    assert at_spawn.exists(), "cmux stub never reached new-workspace"
    kinds = [
        f[2] for f in (ln.split() for ln in at_spawn.read_text().splitlines())
        if len(f) > 2
    ]
    assert kinds == ["intent"]  # reserved, and not yet resolved
    assert (tmp_path / "cmux.log.hops-at-spawn").read_text().strip() == "1"


# --- Task 6 fix: workspace ref capture (spec §5.4d steps 3-4) -----------------
# `cmux new-workspace` prints `OK <ref>` on stdout (verified live: `OK workspace:8`).
# The ref must reach all THREE consumers the spec names — the outcome record's
# `workspace=` field, the notify body, and the script's stdout — with `(spawned)`
# surviving only as the empty-capture fallback.


def _outcome_workspace(ctx):
    """`workspace=` value of the outcome record (spec §5.4d Log format)."""
    for ln in (ctx["reports"] / "handoff-spawn.log").read_text().splitlines():
        f = ln.split()
        if len(f) > 2 and f[2] == "outcome":
            kv = dict(p.split("=", 1) for p in f[3:] if "=" in p)
            return kv.get("workspace")
    return None


def _notify_line(tmp_path):
    """The stub-recorded `cmux notify …` argv line."""
    lines = [
        ln
        for ln in (tmp_path / "cmux.log").read_text().splitlines()
        if ln.startswith("notify ")
    ]
    assert lines, "cmux stub recorded no notify call"
    return lines[-1]


def _stdout_result_line(r):
    """The final stdout line (step 4). NOT stdout+stderr: the captured cmux bytes
    are relayed to stderr, so a combined assertion would pass with the ref
    missing from the printed result."""
    lines = [ln for ln in r.stdout.splitlines() if "spawned successor" in ln]
    assert lines, f"no success line on stdout: {r.stdout!r}"
    return lines[0]


def _cmux_stub_emitting(ref_emit):
    return (
        'if [ "$1" = "ping" ]; then echo PONG; exit 0; fi\n'
        'if [ "$1" = "new-workspace" ]; then echo "$@" >> "$CMUX_LOG"; '
        + ref_emit
        + "; exit 0; fi\n"
        'echo "$@" >> "$CMUX_LOG"; exit 0'
    )


def test_workspace_ref_reaches_outcome_notify_and_stdout(tmp_path):
    ctx = setup_worktree(tmp_path)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        env_extra=_reach_spawn(tmp_path, ctx),
        cmux_body=_cmux_stub_emitting('echo "OK workspace:42"'),
    )
    assert r.returncode == 0
    assert _outcome_workspace(ctx) == "workspace:42"
    assert "successor spawned in workspace:42" in _notify_line(tmp_path)
    assert "workspace:42" in _stdout_result_line(r)
    # The placeholder is an implementation token, never user-visible output.
    assert "{workspace}" not in (tmp_path / "cmux.log").read_text()


def test_workspace_ref_capture_survives_missing_trailing_newline(tmp_path):
    # A `while read` parse silently drops a final unterminated line, degrading
    # every real spawn to `(spawned)` while an echo-based stub stays green.
    ctx = setup_worktree(tmp_path)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        env_extra=_reach_spawn(tmp_path, ctx),
        cmux_body=_cmux_stub_emitting("printf 'OK workspace:9'"),
    )
    assert r.returncode == 0
    assert _outcome_workspace(ctx) == "workspace:9"
    assert "successor spawned in workspace:9" in _notify_line(tmp_path)
    assert "workspace:9" in _stdout_result_line(r)


def test_workspace_ref_falls_back_when_cmux_emits_nothing(tmp_path):
    # Empty capture must degrade to the `(spawned)` constant — never an empty
    # field in the outcome record or a dangling "spawned in " notify body.
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx))
    assert r.returncode == 0
    assert _outcome_workspace(ctx) == "(spawned)"
    assert "successor spawned in (spawned)" in _notify_line(tmp_path)
    assert "(spawned)" in _stdout_result_line(r)


def test_cmux_stdout_is_relayed_not_swallowed(tmp_path):
    # Capturing stdout must not hide what cmux printed.
    ctx = setup_worktree(tmp_path)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        env_extra=_reach_spawn(tmp_path, ctx),
        cmux_body=_cmux_stub_emitting('echo "OK workspace:42"; echo "extra cmux note"'),
    )
    assert r.returncode == 0
    assert "extra cmux note" in r.stderr


def test_spawn_failure_rc_survives_stdout_capture(tmp_path):
    # A command substitution or pipe around `cmux new-workspace` would clobber
    # `$?`; the exit ladder (non-zero -> exit 3, hop consumed) depends on it.
    ctx = setup_worktree(tmp_path)
    body = (
        'if [ "$1" = "ping" ]; then echo PONG; exit 0; fi\n'
        'if [ "$1" = "new-workspace" ]; then echo "$@" >> "$CMUX_LOG"; '
        'echo "OK workspace:42"; exit 5; fi\n'
        'echo "$@" >> "$CMUX_LOG"; exit 0'
    )
    r = run_spawn(
        ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx), cmux_body=body
    )
    assert r.returncode == 3
    assert _outcome_workspace(ctx) == "spawn-failed"
    assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"
