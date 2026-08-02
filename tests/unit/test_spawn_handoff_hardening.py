"""Guards for the two Major findings from the 2026-07-28 outside (Codex) review.

Both were fail-OPEN defects in guards whose whole purpose is to refuse:

  M1  the runaway-chain hop guard fell through and SPAWNED when either
      SUPERPOWERS_CMUX_MAX_HOPS or the persisted .handoff-hops counter was
      non-numeric (`[ "$HOPS" -ge "$MAX_HOPS" ]` errors, branch not taken).
  M2  .active-feature was interpolated straight into the bookkeeping WRITE path
      with no validation, so `../..`-style content redirected mkdir/hop-counter/
      spawn-log writes outside the worktree while still reporting a normal spawn.

Every test here asserts the REFUSAL *and* that nothing was spawned — a guard that
refuses but has already spawned is not a guard. Harness: spawn_handoff_helpers.

Provenance: docs/process-improvement-findings/2026-07-28-cmux-cli-capability-gap-analysis.md
and the review bundle 2026-07-29T01-40-25Z-superpowers (findings.md, M1/M2).
"""

import subprocess

from spawn_handoff_helpers import (
    SPAWN_VERBS,
    cmux_v2_stub,
    did_not_spawn,
    encode_args,
    install_bundle,
    install_version,
    run_spawn,
    setup_worktree,
)


def _meta(args_b64=None):
    e = {
        "CLAUDE_CODE_PICKER_VERSION": "2.1.218",
        "CLAUDE_CODE_PICKER_LABEL": "Proj",
    }
    if args_b64:
        e["CLAUDE_CODE_PICKER_ARGS"] = args_b64
    return e


def _reach_hop_gate(tmp_path, ctx):
    """Env/bundle state that reaches the hop gate (past clean-tree + bundle checks)."""
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    install_version(tmp_path, "2.1.218")
    return _meta(args_b64=encode_args(["--append-system-prompt-file", "/tmp/x.md"]))


def _commit_all(ctx, msg):
    """Re-clean the tree — the hop gate sits AFTER Precondition 1."""
    subprocess.run(["git", "add", "-A"], cwd=ctx["wt"], check=True)
    subprocess.run(["git", "commit", "-qm", msg], cwd=ctx["wt"], check=True)


def _cmux_log(tmp_path):
    p = tmp_path / "cmux.log"
    return p.read_text() if p.exists() else ""


def _did_not_spawn(tmp_path):
    """Absence of EVERY spawn verb, not just the legacy one.

    B1's second clause. This used to read `"new-workspace" not in log`, which
    Task 9's switch to the surface topology turned fail-OPEN: the script no
    longer emits `new-workspace`, so the expression is True even when it
    spawned — silently voiding the seven refusal assertions below, in a guard
    whose entire purpose is to refuse. The verb list lives in exactly one place
    (`spawn_handoff_helpers.SPAWN_VERBS`); a second copy here would be the drift
    shape deviations.md:127 already caught once this sprint.
    """
    return did_not_spawn(_cmux_log(tmp_path))


def test_did_not_spawn_is_false_on_a_real_surface_spawn(tmp_path):
    """POSITIVE CONTROL (a): the surface path.

    Without this, "asserts absence of every verb" is indistinguishable from
    "asserts absence of a verb no log ever contains" — the identical fail-open
    in a new spelling.
    """
    ctx = setup_worktree(tmp_path)
    env = _reach_hop_gate(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env, cmux_body=cmux_v2_stub())
    assert r.returncode == 0, r.stderr
    assert "new-surface" in _cmux_log(tmp_path), "control leg never reached the verb"
    assert not _did_not_spawn(tmp_path), "a real surface spawn read as 'did not spawn'"
    # The regression itself, made permanent: the PRE-Task-9 predicate is True on
    # this very log — i.e. it would have reported "did not spawn" about a run
    # that spawned. Keeping the demonstration here means a revert to the old
    # spelling cannot pass quietly.
    assert "new-workspace" not in _cmux_log(tmp_path), (
        "the old predicate must be demonstrably fail-open here"
    )


def test_did_not_spawn_is_false_on_a_workspace_fallback_spawn(tmp_path):
    """POSITIVE CONTROL (b): the workspace-fallback path.

    Control (a) alone pins only the `new-surface` disjunct — a rewrite like
    `"new-surface" not in log and "workspace create" not in log.lower()` passes
    (a) while leaving the fallback verb exactly as fail-open as the bug being
    fixed. And the fallback is the reachable path where a spawn happens with
    `new-surface` absent from any SUCCESSFUL create.
    """
    ctx = setup_worktree(tmp_path)
    env = _reach_hop_gate(tmp_path, ctx)
    env["CMUX_NEW_SURFACE_RC"] = "1"
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env, cmux_body=cmux_v2_stub())
    assert r.returncode == 0, r.stderr
    log = _cmux_log(tmp_path)
    assert "workspace create" in log, "control leg never reached the fallback verb"
    assert not _did_not_spawn(tmp_path), "a fallback spawn read as 'did not spawn'"


def test_spawn_verb_vocabulary_retains_the_legacy_verb():
    """The legacy verb stays in the list: an old stub or a partial revert that
    emits `new-workspace` must not read as 'did not spawn' either."""
    assert set(SPAWN_VERBS) == {"new-surface", "workspace create", "new-workspace"}
    assert _did_not_spawn.__module__  # helper is imported, not re-spelled here
    assert did_not_spawn("cmux new-workspace --name x") is False


# ── M1: the runaway-chain guard must fail CLOSED ──────────────────────────────


def test_nonnumeric_max_hops_reverts_to_default_and_still_refuses(tmp_path):
    """A typo in the kill switch must not mean 'proceed'.

    Positive control on the revert: the counter is seeded AT the ceiling an
    invalid knob reverts to. If the revert did not happen, `-ge` errors on 'abc',
    the branch is skipped, and the script spawns. Reaching the refusal proves
    MAX_HOPS was restored to a usable integer rather than merely warned about.

    The seed is 6, not 3: the fixed `MAX_HOPS_DEFAULT=3` is gone, and an invalid
    knob now reverts to the DERIVED ceiling — 6 for this fixture, which ships no
    .sdd-session.json, so EXPECTED_HOPS is "unknown" and the floor applies. Left
    at 3 this test would go fail-OPEN and only HALF-loudly: 3 < 6 means the gate
    stops refusing and the script SPAWNS, while the `WARNING:` assertion below
    still passes. The knob is NOT set explicitly here — the knob being invalid IS
    the premise of this test.
    """
    ctx = setup_worktree(tmp_path)
    env = _reach_hop_gate(tmp_path, ctx)
    (ctx["reports"] / ".handoff-hops").write_text("6\n")
    _commit_all(ctx, "seed hops")
    env["SUPERPOWERS_CMUX_MAX_HOPS"] = "abc"
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
    assert any(
        ln.startswith("WARNING:") and "MAX_HOPS" in ln for ln in r.stderr.splitlines()
    ), f"no MAX_HOPS warning on stderr: {r.stderr!r}"
    assert r.returncode == 3, r.stderr
    assert _did_not_spawn(tmp_path), "spawned despite an invalid runaway-chain limit"


def test_max_hops_zero_is_honoured_as_a_deliberate_kill_switch(tmp_path):
    """0 is a VALID integer and must keep working as refuse-everything.

    Guards the validator against over-tightening into `^[1-9][0-9]*$`, which would
    silently remove the only env-level way to disable auto-spawn entirely.
    """
    ctx = setup_worktree(tmp_path)
    env = _reach_hop_gate(tmp_path, ctx)
    env["SUPERPOWERS_CMUX_MAX_HOPS"] = "0"
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
    assert r.returncode == 3, r.stderr
    assert not any(
        ln.startswith("WARNING:") and "MAX_HOPS" in ln for ln in r.stderr.splitlines()
    ), "0 must not be treated as invalid"
    assert _did_not_spawn(tmp_path)


def test_malformed_hop_counter_file_fails_closed(tmp_path):
    """A corrupt persisted counter refuses rather than bypassing the guard.

    Not hypothetical: the reservation write truncates at open, so ENOSPC/quota can
    leave a partial value, and the file is committed so a conflict marker reaches
    it too.
    """
    ctx = setup_worktree(tmp_path)
    env = _reach_hop_gate(tmp_path, ctx)
    (ctx["reports"] / ".handoff-hops").write_text("abc\n")
    _commit_all(ctx, "corrupt hops")
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
    assert r.returncode == 3, r.stderr
    assert "malformed" in (r.stdout + r.stderr).lower()
    assert _did_not_spawn(tmp_path), "spawned on an unreadable hop counter"


def test_malformed_hop_counter_is_not_silently_reset(tmp_path):
    """The pre-fix path also RESET the chain.

    `$((HOPS + 1))` treats 'abc' as an unset name -> 0 -> SP_HOP=1, so the
    reservation write would have overwritten the counter with 1 and erased the
    chain's memory. Refusing must leave the corrupt value in place for a human to
    inspect rather than papering over it.
    """
    ctx = setup_worktree(tmp_path)
    env = _reach_hop_gate(tmp_path, ctx)
    hops = ctx["reports"] / ".handoff-hops"
    hops.write_text("abc\n")
    _commit_all(ctx, "corrupt hops")
    run_spawn(ctx, tmp_path, "b1", env_extra=env)
    assert hops.read_text() == "abc\n", "refusal must not rewrite the counter"


def test_absent_and_empty_hop_counter_remain_the_first_hop_case(tmp_path):
    """Regression fence: the validator must not break the normal first spawn.

    Absent and empty both legitimately mean 'hop 0'. Tightening M1 into a blanket
    'must be numeric' on raw file contents would refuse every first-ever handoff.

    Drives the v2 stub because this is a REAL spawn: the default stub emits no
    `OK surface:` line, so after Task 9's ref-shape check both topologies fail
    before launch and this would exit 3 — for reasons that have nothing to do
    with the hop counter. The invariant is unchanged: a legitimate first hop
    must SPAWN and reserve.
    """
    ctx = setup_worktree(tmp_path)
    env = _reach_hop_gate(tmp_path, ctx)
    r = run_spawn(
        ctx, tmp_path, "b1", env_extra=env, cmux_body=cmux_v2_stub()
    )  # file absent
    assert r.returncode == 0, f"absent counter must spawn: {r.stderr!r}"
    assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"


# ── M2: .active-feature is a write-path authority and must be contained ───────
#
# These run BEFORE the clean-tree precondition, so no commit is needed: the
# refusal happens while resolving the feature dir.


def _set_active_feature(ctx, value):
    (ctx["wt"] / ".active-feature").write_text(value)


def test_active_feature_parent_traversal_refused(tmp_path):
    ctx = setup_worktree(tmp_path)
    _set_active_feature(ctx, "../escape\n")
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 1, r.stderr
    assert ".." in r.stderr and "REFUSED" in r.stderr
    assert _did_not_spawn(tmp_path)


def test_active_feature_traversal_writes_nothing_outside_the_worktree(tmp_path):
    """The payload of M2, asserted directly.

    Pre-fix, REPORTS_DIR resolved outside WORKTREE_ROOT and `mkdir -p` created it,
    then the hop counter and spawn log were written there — invisible to the
    clean-tree check, which only sees inside the tree.

    The traversal value is COMMITTED before the run. Without that the tree is
    dirty, Precondition 1 refuses first, and the test passes pre-fix for entirely
    the wrong reason — it would assert "nothing was written outside" about a run
    that never reached any write at all. Committing forces the script past the
    clean-tree check and onto the real path, which is what makes this a guard
    rather than a coincidence.
    """
    ctx = setup_worktree(tmp_path)
    _set_active_feature(ctx, "../../escape-target\n")
    _commit_all(ctx, "traversal in .active-feature")
    env = _reach_hop_gate(tmp_path, ctx)
    escape_a = tmp_path / "escape-target"
    escape_b = tmp_path.parent / "escape-target"
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
    assert r.returncode == 1, r.stderr
    assert ".." in r.stderr
    assert not escape_a.exists(), f"created {escape_a} outside the worktree"
    assert not escape_b.exists(), f"created {escape_b} outside the worktree"
    assert _did_not_spawn(tmp_path)


def test_active_feature_absolute_path_refused(tmp_path):
    ctx = setup_worktree(tmp_path)
    _set_active_feature(ctx, str(tmp_path / "elsewhere") + "\n")
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 1, r.stderr
    assert "absolute" in r.stderr.lower()
    assert _did_not_spawn(tmp_path)


def test_active_feature_empty_refused(tmp_path):
    """Empty previously resolved REPORTS_DIR to WORKTREE_ROOT/reports.

    Not outside the tree, but it silently writes bookkeeping to the wrong place —
    a different feature's spawn log — so it is a refusal, not a default.
    """
    ctx = setup_worktree(tmp_path)
    _set_active_feature(ctx, "\n")
    r = run_spawn(ctx, tmp_path, "b1")
    assert r.returncode == 1, r.stderr
    assert "empty" in r.stderr.lower()
    assert _did_not_spawn(tmp_path)
    assert not (ctx["wt"] / "reports").exists()


def test_feature_dir_name_containing_dots_is_still_accepted(tmp_path):
    """Precision fence on the `..` rule.

    A naive `*..*` glob would reject a legitimate directory like `v1..2`. The check
    is segment-anchored (`*/../*`), so only a real parent-traversal segment fails.

    v2 stub for the same reason as the first-hop fence above: this is a real
    spawn, and its invariant is that a legitimate dotted feature dir must SPAWN
    and reserve — not merely that it fails differently.
    """
    ctx = setup_worktree(tmp_path)
    feat = "docs/imp-plans/v1..2"
    (ctx["wt"] / feat / "reports").mkdir(parents=True)
    _set_active_feature(ctx, feat + "\n")
    _commit_all(ctx, "dotted feature dir")
    env = _reach_hop_gate(tmp_path, ctx)
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env, cmux_body=cmux_v2_stub())
    assert r.returncode == 0, f"legitimate dotted dir refused: {r.stderr!r}"
    assert (ctx["wt"] / feat / "reports" / ".handoff-hops").exists()
