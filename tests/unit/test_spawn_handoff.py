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
    # The ceiling is DERIVED now (floor 6) — this test's premise was the old fixed
    # MAX_HOPS_DEFAULT=3, so pin it explicitly or the seed of 3 no longer refuses.
    r = run_spawn(ctx, tmp_path, "b1", env_extra={"SUPERPOWERS_CMUX_MAX_HOPS": "3"})
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

from spawn_handoff_helpers import encode_args, install_version, NO_AMBIENT_HOP_KNOBS

# The ambient picker-env scrub every test in this file depends on (absent must
# mean absent) is the autouse `_hermetic_picker_env` fixture in tests/unit/
# conftest.py — moved there in Task 8 so it is not module-scoped. PICKER_ENV_VARS
# is defined there as its single source.


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
    lines = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.startswith(MARKER)]
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
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra=_meta(args_b64="v1:!!!not-base64!!!"),
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
    e = _meta(args_b64=encode_args(["--append-system-prompt-file", "/tmp/x.md"]))
    # run_spawn copies os.environ; empty string neutralizes both consumers
    # (`${VAR:-default}` and the derivation's `[ -n "$VAR" ]`) so an ambient
    # SUPERPOWERS_CMUX_MAX_HOPS cannot skew the derived-ceiling assertions.
    e.update(NO_AMBIENT_HOP_KNOBS)
    return e


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
    """[(record_type, spawn_id, fields)] from handoff-spawn.log, in file order.

    `fields` is the record's trailing `k=v` payload (§5.4d Log format: hop for
    every record; workspace/launch/bundle/quota for outcomes) — carried here so
    value assertions have ONE parser instead of a per-field one-off.
    """
    lines = (ctx["reports"] / "handoff-spawn.log").read_text().splitlines()
    return [
        (f[2], f[1], dict(p.split("=", 1) for p in f[3:] if "=" in p))
        for f in (ln.split() for ln in lines)
        if len(f) > 2
    ]


def _spawn_log_fields(ctx, kind):
    """Fields of the single record of type `kind` (asserts there is exactly one)."""
    recs = [fl for k, _, fl in _spawn_log_records(ctx) if k == kind]
    assert len(recs) == 1, f"expected exactly one {kind} record, got {len(recs)}"
    return recs[0]


def _worktree_root(ctx):
    """The path the script itself computes (`git rev-parse --show-toplevel`).

    NOT `realpath(ctx['wt'])`: git canonicalizes macOS's /var -> /private/var, so
    a realpath-derived expectation can drift from what the script passes.
    """
    import subprocess

    return subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(ctx["wt"]),
        capture_output=True,
        text=True,
    ).stdout.strip()


def _cmux_stub_recording_argv():
    """cmux stub that records each subcommand's argv ONE ELEMENT PER LINE.

    The default stub's `echo "$@"` flattens argv into a space-joined line, which
    cannot distinguish a flag's VALUE from the next token — `--name "SDD resume:
    feat"` and `--cwd <path>` both carry spaces. Per-subcommand files keep the
    new-workspace and notify argvs from interleaving.
    """
    return (
        'if [ "$1" = "ping" ]; then echo PONG; exit 0; fi\n'
        'printf \'%s\\n\' "$@" >> "$CMUX_LOG.$1.argv"\n'
        'echo "$@" >> "$CMUX_LOG"; exit 0'
    )


def _recorded_argv(tmp_path, subcmd):
    p = Path(str(tmp_path / "cmux.log") + f".{subcmd}.argv")
    assert p.exists(), f"cmux stub recorded no `{subcmd}` call"
    return p.read_text().splitlines()


def _flag_value(argv, flag):
    """Value FOLLOWING `flag` in a recorded argv (asserts the flag is present)."""
    assert flag in argv, f"{flag} absent from argv: {argv!r}"
    i = argv.index(flag)
    assert i + 1 < len(argv), f"{flag} has no value in argv: {argv!r}"
    return argv[i + 1]


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
    # Consume the Task-0 frozen contract constants (SSOT) rather than restating
    # them: if cmux renames a flag, exactly one place changes. Values are pinned
    # separately in test_new_workspace_and_notify_argv_values_match_spec.
    for flag in CMUX_NEW_WORKSPACE_FLAGS:
        assert flag in logged
    assert "notify" in logged
    for flag in CMUX_NOTIFY_FLAGS:
        assert flag in logged
    records = _spawn_log_records(ctx)
    kinds = [k for k, _, _ in records]
    assert kinds.index("intent") < kinds.index("outcome")
    assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"
    # §5.4d: ONE spawn id ties the whole hop together — the intent record, the
    # success outcome, and the runtime-failure record the CHILD may append from
    # the composed fallback tail. Assert identity across all three, not shape:
    # two independently generated uuids satisfy every "is a uuid" check while
    # destroying the correlation the id exists for.
    ids = {i for _, i, _ in records}
    assert len(ids) == 1, f"spawn ids diverge across records: {records}"
    spawn_id = ids.pop()
    assert UUID_RE.fullmatch(spawn_id)
    assert _fallback_spawn_id(_successor_cmd(r)) == spawn_id


def test_new_workspace_and_notify_argv_values_match_spec(tmp_path):
    # Flag PRESENCE is not coverage: `--cwd /tmp`, `--name BOGUS` and
    # `--title "BOGUS TITLE"` all survive a presence-only check. Each of these is
    # a spec-named string (§5.4d steps 2-3), and a wrong --cwd is not cosmetic —
    # per CLAUDE.md "Worktree Sessions" hooks resolve CWD from session start, so
    # the successor's whole SDD session would be silently mis-rooted.
    ctx = setup_worktree(tmp_path)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        env_extra=_reach_spawn(tmp_path, ctx),
        cmux_body=_cmux_stub_recording_argv(),
    )
    assert r.returncode == 0

    nw = _recorded_argv(tmp_path, "new-workspace")
    for flag in CMUX_NEW_WORKSPACE_FLAGS:  # Task-0 frozen contract (SSOT)
        assert flag in nw
    assert _flag_value(nw, "--name") == f"SDD resume: {Path(ctx['feat']).name}"
    assert _flag_value(nw, "--cwd") == _worktree_root(ctx)
    assert _flag_value(nw, "--focus") == "false"
    assert _flag_value(nw, "--command") == _successor_cmd(r)

    notify = _recorded_argv(tmp_path, "notify")
    for flag in CMUX_NOTIFY_FLAGS:
        assert flag in notify
    assert _flag_value(notify, "--title") == "SDD handoff"
    # `Hop $SP_HOP/$MAX_HOPS`: 6, not 3 — no .sdd-session.json here, so the
    # ceiling derivation falls to its floor. A RENDERED dependency on the
    # moved default, invisible to any grep for the identifier.
    assert _flag_value(notify, "--body").startswith("Hop 1/6 ")


def test_spawn_log_record_fields_match_spec_log_format(tmp_path):
    # §5.4d Log format pins hop on every record and workspace/launch/bundle/quota
    # on outcomes. Only `workspace=` was ever checked, so corrupting any other
    # field left the suite green.
    ctx = setup_worktree(tmp_path)
    r = run_spawn(ctx, tmp_path, "b1", env_extra=_reach_spawn(tmp_path, ctx))
    assert r.returncode == 0
    # Exact equality, so step (f)'s new tasks_done= field must be listed here.
    # 0 done reports in this fixture => a real 0, not the degraded "unknown".
    assert _spawn_log_fields(ctx, "intent") == {"hop": "1", "tasks_done": "0"}
    outcome = _spawn_log_fields(ctx, "outcome")
    assert outcome["hop"] == "1"
    assert outcome["workspace"] == "(spawned)"  # stub emits no `OK <ref>`
    assert outcome["launch"] == "auto"
    assert outcome["bundle"] == "b1"
    assert outcome["quota"].startswith("ok:")  # PACE_OK => remaining 63.0%


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
    # Spec §5.5: every non-spawn path prints the manual instructions — the
    # protocol never dead-ends. Asserted on text ONLY print_manual_instructions
    # emits, and on r.stdout ALONE: `/pickup b1` against stdout+stderr is already
    # satisfied by the Task-5 `successor command:` echo on stderr, so it never
    # observed this call at all (the Task-5 test-echo collision class).
    assert "Manual resume required" in r.stdout
    assert "Then STOP the current session" in r.stdout
    # The failure branch's own `cmux notify` had no assertion at all — deleting it
    # left the suite green. Asserted on the recorded notify argv (not stdout+stderr)
    # so only an actual notify call satisfies it.
    assert "Spawn failed after reservation" in _notify_line(tmp_path)
    records = _spawn_log_records(ctx)
    ids = {i for _, i, _ in records}
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
    intent = [i for k, i, _ in _spawn_log_records(ctx) if k == "intent"]
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
        f[2]
        for f in (ln.split() for ln in at_spawn.read_text().splitlines())
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
    return _spawn_log_fields(ctx, "outcome").get("workspace")


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


# --- Task 7 (Sweep A): zero-protection regression coverage --------------------
# Four behaviors below were verified by executing them during Module 1 review but
# had NO test: deleting the code left the 58-test suite green. Each test here is
# mutation-proven (report records the mutation + observed RED).


def _only_failing_predicate_is(tmp_path, ctx, **install_kwargs):
    """Env where EVERY auto-preflight predicate holds except the one under test.

    picker-manual is easy to reach by accident (any one missing predicate does it),
    so an under-specified fixture makes these tests pass for the wrong reason.
    """
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218", **install_kwargs)
    return _meta(args_b64=encode_args([]))


def test_picker_absent_degrades_to_picker_manual(tmp_path):
    # spec §7 pins "picker missing -> launch=picker-manual". No test had ever run
    # the script with claude-picker unresolvable, so the preflight's picker
    # requirement could be dropped entirely with the suite green.
    ctx = setup_worktree(tmp_path)
    env = _only_failing_predicate_is(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env, picker_stub=False)
    assert r.returncode == 0
    assert "launch=picker-manual" in (r.stdout + r.stderr)
    # Assert what the degraded branch COMPOSES, not just the mode label: the
    # attended-picker command is the user-facing safety net.
    assert _successor_cmd(r) == "claude-picker '/pickup b1'"


def test_non_executable_version_degrades_to_picker_manual(tmp_path):
    # The preflight deliberately matches the picker's own discovery predicate
    # (`find -type f -perm -u+x`) rather than a lenient `-e`. Neither half of that
    # `-f && -x` conjunction was individually covered: the one pre-existing param
    # that reaches it (test_picker_manual_when_metadata_degraded's "9.9.9", a
    # version name with no file at all) fails BOTH halves, so it pins the
    # conjunction rather than either operand. This test isolates the `-x` half.
    # The `-f` half stays unpinned — drop it and a version stored as a DIRECTORY
    # (mode 0755, so `-x` passes) reports launch=auto for a path the picker's
    # `-type f` scan will never find. Tracked as Task 8 Step 4b in module-2-protocol-e2e-docs.md.
    ctx = setup_worktree(tmp_path)
    env = _only_failing_predicate_is(tmp_path, ctx, executable=False)
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env)
    assert r.returncode == 0
    assert "launch=picker-manual" in (r.stdout + r.stderr)
    assert _successor_cmd(r) == "claude-picker '/pickup b1'"


def test_telemetry_off_value_on_composed_command(tmp_path):
    # The --telemetry flag PAIR is pinned by test_auto_mode_composes_exact_command,
    # but every auto-path test inherits telem="1", so the `off` value was never
    # asserted: hardcoding "on" in the composition passed the whole suite.
    # Anchored on the composed command line — the Task-4 `telemetry=off` diagnostic
    # echo would satisfy a stdout+stderr assertion without the composition running.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra=_meta(args_b64=encode_args([]), telem=None),
    )
    assert "launch=auto" in (r.stdout + r.stderr)  # telemetry-off never blocks auto
    cmd = _successor_cmd(r)
    assert "--telemetry off" in cmd
    assert "--telemetry on" not in cmd


# --- Task 7: env-validation regressions (owed since the Task-3 fix round) -----
# Both values are interpolated into other programs ($QUOTA_MIN_PCT into an awk
# program, $QUOTA_TIMEOUT into `sleep`), and both guards revert to a default rather
# than exiting — the quota gate's contract is fail-open. Deleting either regex
# block left the suite green.

QUOTA_WARN_PREFIX = "WARNING: invalid SUPERPOWERS_CMUX_QUOTA_"


def _warning_lines(r, var):
    """stderr lines that are the script's own invalid-env WARNING for `var`.

    stderr only, and prefix-anchored: this script is chatty on stderr and a
    substring search over stdout+stderr is satisfiable by unrelated diagnostics.
    """
    return [
        ln for ln in r.stderr.splitlines() if ln.startswith(QUOTA_WARN_PREFIX + var)
    ]


def test_invalid_quota_min_pct_warns_and_reverts_to_default(tmp_path):
    # Unvalidated, a non-numeric threshold reaches awk as an uninitialized
    # variable (== 0), so NOTHING is ever below it and the refusal gate goes
    # permanently inert. PACE_LOW (8.0%) is below the script's default, so `low`
    # can only be reached if the revert actually happened.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        pace_body=PACE_LOW,
        env_extra={"SUPERPOWERS_CMUX_QUOTA_MIN_PCT": "abc"},
    )
    assert _warning_lines(r, "MIN_PCT"), f"no MIN_PCT warning on stderr: {r.stderr!r}"
    assert r.returncode == 3
    assert "quota=low" in r.stderr


def test_invalid_quota_timeout_warns_and_quota_gate_stays_live(tmp_path):
    # Unvalidated, `sleep abc` fails instantly, the watchdog kills the tool at
    # once, and every reading classifies `unchecked` — the gate is inert with no
    # diagnostic. The 1s tool outlives that instant kill but finishes well inside
    # the reverted default, so a live gate still reads the `low` value and refuses.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        pace_body="sleep 1; " + PACE_LOW,
        env_extra={"SUPERPOWERS_CMUX_QUOTA_TIMEOUT": "abc"},
    )
    assert _warning_lines(r, "TIMEOUT"), f"no TIMEOUT warning on stderr: {r.stderr!r}"
    assert r.returncode == 3
    assert "quota=low" in r.stderr


# --- Task 8 (Sweep B): reservation durability + residual coverage --------------

from spawn_handoff_helpers import make_stub


def _cmux_log_text(tmp_path):
    p = tmp_path / "cmux.log"
    return p.read_text() if p.exists() else ""


RESERVATION_WARN = "[spawn-handoff] reservation write failed:"
DECODE_WARN = "[spawn-handoff] warn: forwarded-args decode failed"


def _decode_warning_lines(r):
    """stderr lines that are the decoder's OWN degrade diagnostic.

    Prefix-anchored on stderr for the same reason as the helpers around it: the
    script is chatty, and the only other signal the surrogate test had
    (`launch=picker-manual`) is reachable from any of five preflight predicates.
    """
    return [ln for ln in r.stderr.splitlines() if ln.startswith(DECODE_WARN)]


def _reservation_warning_lines(r, needle):
    """stderr lines that are this reservation write's OWN warning.

    Prefix-anchored because the post-reservation SPAWN failure also prints the
    manual instructions and exits 3 — rc and instruction text cannot tell the two
    branches apart, and bash's own `cannot create` diagnostic would satisfy a
    loose match. `needle` then separates the two reservation writes from each
    other: an unwritable reports dir fails BOTH, so a check that accepted either
    warning would stay green with the write under test left unchecked.
    """
    return [
        ln
        for ln in r.stderr.splitlines()
        if ln.startswith(RESERVATION_WARN) and needle in ln
    ]


def _spawn_log_text(ctx):
    p = ctx["reports"] / "handoff-spawn.log"
    return p.read_text() if p.exists() else ""


def test_hops_write_failure_exits_3_without_spawning(tmp_path):
    # Decision 21 durability: with neither `set -e` nor pipefail, an unchecked
    # failed redirection would spawn anyway — reserving nothing while the
    # reserve-before-spawn ORDERING still looked intact.
    #
    # The FIRST write, ISOLATED (mirrors leg B's technique). An unwritable reports
    # dir — what this test used to do — fails BOTH reservation writes, so the
    # DOWNSTREAM intent guard supplied the rc 3 and the absent spawn that the
    # assertions below read: deleting THIS guard's `exit 3` left the suite green.
    # Occupying only the hops path with a DIRECTORY (`>` onto a dir is EISDIR)
    # fails this write alone, so the intent write can no longer stand in. An empty
    # directory is invisible to git, so the clean-tree precondition still holds,
    # and `cat` of a directory yields nothing => HOPS=0 => the hop-limit gate is
    # not what stops us.
    ctx = setup_worktree(tmp_path)
    env = _reach_spawn(tmp_path, ctx)
    (ctx["reports"] / ".handoff-hops").mkdir()
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
    assert _reservation_warning_lines(r, "cannot record hop"), (
        f"no hops-write warning: {r.stderr!r}"
    )
    # The two legs that pin STOPPING rather than merely detecting. Both survive
    # only if this guard's own `exit 3` runs: with it removed the intent write
    # succeeds and the spawn proceeds to rc 0.
    assert r.returncode == 3
    assert "new-workspace" not in _cmux_log_text(tmp_path)
    # Leg A's distinguishing signature: NOTHING was reserved. (Leg B's mirror is
    # `.handoff-hops == "1"` — there the hop IS consumed before its write fails.)
    assert "intent" not in _spawn_log_text(ctx)
    assert "Manual resume required" in r.stdout


def test_intent_write_failure_exits_3_without_spawning(tmp_path):
    # The SECOND write, isolated. An unwritable reports dir fails BOTH writes and
    # exits at the first, leaving this check unpinned — so make only the log write
    # fail, by occupying its path with a DIRECTORY (`>>` onto a dir is EISDIR).
    # A read-only FILE would work too but is untracked content in reports/, which
    # trips the clean-tree precondition and exits 1 for the wrong reason; an empty
    # directory is invisible to git.
    ctx = setup_worktree(tmp_path)
    env = _reach_spawn(tmp_path, ctx)
    (ctx["reports"] / "handoff-spawn.log").mkdir()
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
    assert r.returncode == 3
    assert _reservation_warning_lines(r, "cannot append intent record"), (
        f"no intent-write warning: {r.stderr!r}"
    )
    assert "new-workspace" not in _cmux_log_text(tmp_path)
    # Discriminates this leg from the hops-write leg: the hop IS consumed here.
    assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"
    assert "Manual resume required" in r.stdout


def _install_failing_mktemp(tmp_path):
    """Force every `mktemp` in the script to fail (PATH stub)."""
    stubs = tmp_path / "stubs"
    stubs.mkdir(exist_ok=True)
    make_stub(stubs, "mktemp", "exit 1")


def test_mktemp_failure_still_spawns_uncaptured(tmp_path):
    # The spawn core captures cmux's stdout through a temp FILE; when mktemp is
    # unavailable it must still spawn (uncaptured) rather than skip the spawn.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    _install_failing_mktemp(tmp_path)
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 0
    assert "new-workspace" in _cmux_log_text(tmp_path)
    assert _outcome_workspace(ctx) == "(spawned)"  # nothing captured to parse


def test_mktemp_failure_preserves_spawn_failure_rc(tmp_path):
    # The uncaptured branch must propagate cmux's own exit code: the whole ladder
    # (non-zero -> exit 3, hop consumed) hangs off that `rc=$?`.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    _install_failing_mktemp(tmp_path)
    body = (
        'if [ "$1" = "ping" ]; then echo PONG; exit 0; fi\n'
        'if [ "$1" = "new-workspace" ]; then echo "$@" >> "$CMUX_LOG"; exit 5; fi\n'
        'echo "$@" >> "$CMUX_LOG"; exit 0'
    )
    r = run_spawn(ctx, tmp_path, "b1", cmux_body=body)
    assert r.returncode == 3
    assert _outcome_workspace(ctx) == "spawn-failed"
    assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"


def test_version_installed_as_directory_degrades_to_picker_manual(tmp_path):
    # The `-f` half of the preflight's `-f && -x` conjunction. A DIRECTORY named
    # like a version is mode 0755, so `-x` passes and only `-f` refuses — while
    # the picker's own `find -type f -perm -u+x` discovery would never find it.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    vdir = tmp_path / "home" / ".local" / "share" / "claude" / "versions"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "2.1.218").mkdir()
    env = _meta(args_b64=encode_args([]))
    r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env)
    assert r.returncode == 0
    assert "launch=picker-manual" in (r.stdout + r.stderr)
    assert _successor_cmd(r) == "claude-picker '/pickup b1'"
    # POSITIVE CONTROL. preflight is a five-way AND, so picker-manual above is
    # only evidence about `-f` if EVERY other predicate holds in this fixture.
    # Same env, same everything — only the version becomes a regular executable.
    (vdir / "2.1.218").rmdir()
    install_version(tmp_path, "2.1.218")
    r2 = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env)
    assert "launch=auto" in (r2.stdout + r2.stderr), "control leg never reached auto"


# 63.0 is PACE_OK's reading; 13.0 sits BETWEEN a fractional threshold of 12.5 and
# the script's integer default of 15, which is what makes the fractional regex
# half behaviorally observable. Derived from PACE_OK rather than re-escaped by
# hand, and defined here because spawn_handoff_helpers.py is Task 7's file.
PACE_BETWEEN = PACE_OK.replace("63.0", "13.0")


def test_fractional_quota_min_pct_is_accepted(tmp_path):
    # A fractional threshold is legitimate (the regex blesses `12.5`), so it must
    # not trip the invalid-value warning.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        pace_body=PACE_OK,
        env_extra={"SUPERPOWERS_CMUX_QUOTA_MIN_PCT": "12.5"},
    )
    assert r.returncode == 0
    assert not _warning_lines(r, "MIN_PCT"), f"fractional value warned: {r.stderr!r}"
    assert "quota=ok" in r.stderr


def test_fractional_quota_min_pct_threshold_is_honoured(tmp_path):
    # The behavioral half of the same guard: at 13.0% the fractional threshold
    # (12.5) proceeds, while a silent revert to the default (15) would refuse with
    # exit 3. Unlike the absence assertion above, this flips an OUTCOME.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        pace_body=PACE_BETWEEN,
        env_extra={"SUPERPOWERS_CMUX_QUOTA_MIN_PCT": "12.5"},
    )
    assert r.returncode == 0, f"13.0% refused against a 12.5% threshold: {r.stderr!r}"
    assert "quota=ok:13.0" in r.stderr


def test_lone_surrogate_arg_degrades_without_traceback(tmp_path):
    # A lone surrogate cannot be UTF-8 encoded, so the decoder's final write
    # raises. The degrade (ARGS_OK=0 -> picker-manual) was always correct; the
    # DIAGNOSTIC was a raw Python traceback on the script's stderr.
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra=_meta(args_b64=encode_args(["\udcff"])),
    )
    assert r.returncode == 0
    assert "launch=picker-manual" in (r.stdout + r.stderr)
    assert "Traceback" not in r.stderr
    # `launch=picker-manual` above discriminates nothing here: preflight is a
    # five-way AND and ANY missing predicate reaches the same mode, so before this
    # line the only real signal was the absence of a traceback — i.e. the test
    # could not tell "decode failed and was reported" from "decode never ran".
    # The named diagnostic is what actually pins the degrade to THIS cause.
    assert _decode_warning_lines(r), f"no decode-failure warning: {r.stderr!r}"


def test_label_slice_does_not_leak_base_when_suffix_exceeds_ceiling(tmp_path):
    # A pathological `-Session-<250 digits>` label makes the suffix alone exceed
    # the 255 ceiling. Without max(0, …) the negative bound truncates the base
    # from the RIGHT, leaking a fragment of the old label into the new one.
    # (No result can be under 255 here; this pins deterministic truncation.)
    ctx = setup_worktree(tmp_path)
    _spawnable(tmp_path, ctx)
    install_version(tmp_path, "2.1.218")
    r = run_spawn(
        ctx,
        tmp_path,
        "b1",
        "--dry-run",
        env_extra=_meta(
            args_b64=encode_args([]), label="ProjectXYZ-Session-" + "9" * 250
        ),
    )
    m = re.search(r"label=\[([^\]]*)\]", r.stdout + r.stderr)
    assert m, "no label diagnostic emitted"
    assert m.group(1).startswith("-Session-")
    assert "Proje" not in m.group(1)
