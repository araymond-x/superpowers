"""Unit matrix for the cmux-spawn-v2 rework. Task 0 seeds the fixture contracts;
Modules 3-4 append behavior tests.

These fixtures are the ONLY record of facts establishable solely inside Task 0's
live-cmux window. Task 0's quality review found 17 fixture mutations surviving a
green suite, so the assertions below deliberately pin VALUES and not merely
presence: a fixture that can be silently inverted is worse than one that is
absent, because Module 3 would build against the opposite of measured truth.
"""

import json
import math
import re
import sys
from pathlib import Path

from spawn_handoff_helpers import (
    NO_AMBIENT_HOP_KNOBS,
    _commit,
    _spawn_log_text_or_empty,
    append_outcome,
    encode_args,
    install_bundle,
    install_version,
    make_stub,
    run_spawn,
    setup_worktree,
    write_done_report,
    write_manifest,
)

FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"


def _reach_gate(tmp_path, ctx, **knobs):
    """Env that reaches the policy/hop gates in launch=auto mode, with the
    developer's ambient SUPERPOWERS_CMUX_* knobs neutralized (run_spawn copies
    os.environ, so an ambient MAX_HOPS would skew every derived-ceiling test)."""
    install_bundle(tmp_path, "b1", "valid-manifest.json", ctx["repo_id"])
    install_version(tmp_path, "2.1.218")
    env = {
        "CLAUDE_CODE_PICKER_VERSION": "2.1.218",
        "CLAUDE_CODE_PICKER_LABEL": "Proj",
        "CLAUDE_CODE_PICKER_ARGS": encode_args(
            ["--append-system-prompt-file", "/tmp/x.md"]
        ),
    }
    env.update(NO_AMBIENT_HOP_KNOBS)
    env.update(knobs)
    return env


def _hops(ctx, value):
    (ctx["reports"] / ".handoff-hops").write_text(f"{value}\n")


def _cmux_log(tmp_path):
    p = tmp_path / "cmux.log"
    return p.read_text() if p.exists() else ""


def _verb_shapes():
    return json.loads((FIX / "cmux-verb-shapes.json").read_text())


def test_verb_shapes_fixture_contract():
    d = _verb_shapes()
    ns = d["new_surface"]["stdout"].split()
    assert ns[0] == "OK" and ns[1].startswith("surface:")
    ws = d["workspace_create"]["stdout"].split()
    assert ws[0] == "OK" and ws[1].startswith("workspace:")
    rt = d["rename_tab"]["stdout"].split()
    assert rt[1] == "action=rename", "rename-tab field 2 must never be treated as a ref"

    # The cold read-screen is a NEGATIVE fixture: Module 3 relies on a
    # never-driven surface erroring rather than returning an empty screen.
    # Assert the error CLASS on stderr, not merely that something failed.
    # (stdout is "" by construction -- stdout/stderr are captured separately --
    # so an `in stdout` disjunct here would be permanently dead.)
    rsc = d["read_screen_cold"]
    assert "internal_error" in rsc["stderr"], (
        "read_screen_cold must pin the internal_error class, not just a failure"
    )
    assert rsc["exit"] != 0


def test_verb_shapes_provenance_pinned():
    """`captured: "live"` is the plan's own blocked-path discriminator.

    Task 0's blocked path writes `captured: "matrix-fallback"` with synthesized
    shapes. If that value can drift unasserted, the fixture can claim provenance
    it does not have, and every downstream module inherits fabricated contracts.
    """
    d = _verb_shapes()
    assert d["captured"] == "live", (
        "fixture must declare live capture; 'matrix-fallback' is the blocked-path value"
    )
    assert d["cmux_version"].startswith("cmux "), (
        "cmux_version must hold a verbatim `cmux --version` string"
    )


def test_selected_row_marker_shape():
    """list-pane-surfaces prefixes the SELECTED row with `* ` (finding 4).

    Under awk's default FS the marker is its own field, so $1 on a selected row
    is `*`, NOT the ref. Module 3's `create_workspace_target` lists a freshly
    created workspace, whose single surface is always selected -- so the marker
    is on the only row the production fallback path ever parses. Losing this
    fact from the fixture is what made a broken parser look green against a
    marker-less stub.
    """
    d = _verb_shapes()

    single = d["list_pane_surfaces"]["stdout"]
    assert single.startswith("* "), "the single-row production shape carries the marker"

    multi = d["list_pane_surfaces_multi"]
    assert multi["exit"] == 0
    rows = multi["stdout"].splitlines()
    assert len(rows) == 2, "the multi fixture must retain both rows"
    assert rows[0].startswith("* "), (
        "row 1 is the selected row and carries the `* ` marker"
    )
    assert rows[0].split()[0] == "*", "awk $1 on a marker row is `*`, never the ref"
    assert rows[0].split()[1].startswith("surface:"), (
        "the ref is field 2 on a marker row"
    )
    assert rows[1].startswith("  "), "non-selected rows are two-space indented"
    assert rows[1].split()[0].startswith("surface:"), (
        "awk $1 on a non-selected row IS the ref"
    )

    marker = d["selected_row_marker"]
    assert marker["production_shape"].startswith("SINGLE-ROW"), (
        "Module 3 must be told which shape the fallback path actually parses"
    )
    assert marker["awk_consequence"].strip(), (
        "the parser consequence must stay recorded"
    )


def test_unplanned_discoveries_pinned():
    """The two unplanned contract discoveries must not be deletable or invertible.

    `ref_resolution_scoping` was empirically INVERTIBLE: emptying
    requires_workspace_flag and moving every verb to resolves_cross_workspace_bare
    left the suite green, which would tell Module 3 the exact opposite of
    measured truth.
    """
    d = _verb_shapes()

    scoping = d["ref_resolution_scoping"]
    requires = scoping["requires_workspace_flag"]
    bare = scoping["resolves_cross_workspace_bare"]
    for verb in ("rename-tab", "close-surface"):
        assert verb in requires, (
            f"{verb} was MEASURED to need --workspace; removing it inverts the finding"
        )
        assert verb not in bare, f"{verb} does not resolve cross-workspace bare"
    for verb in ("send", "send-key", "read-screen"):
        assert verb in bare, f"{verb} was measured to resolve cross-workspace bare"
    assert scoping["evidence"], "the scoping finding must retain its evidence"

    trust = d["trust_dialog_screen"]
    assert trust["observed"] is True
    assert trust["screen"].strip(), (
        "the trust-modal screen is Module 3's diagnosis fixture"
    )
    assert trust["candidate_anchors"], "trust-dialog anchors must be non-empty"
    for anchor in trust["candidate_anchors"]:
        assert anchor.strip()
        assert anchor in trust["screen"], (
            "each anchor must actually occur in the captured screen"
        )


def test_cold_start_default_derivation():
    """Encode the derivation RULE, not a one-directional lower bound.

    Module 3 Task 9's import assertion is only a CONSISTENCY check against this
    fixture, so this test is the sole guard on a shipped production timeout.
    An unconditional equality is required: gating on `measured` let a mutation
    flip `measured` to false and disable the check entirely.
    """
    d = json.loads((FIX / "cold-start-timing.json").read_text())

    # `type(...) is int` rather than isinstance(): isinstance(True, int) is True.
    assert type(d["default_seconds"]) is int
    assert type(d["p95_seconds"]) is int
    assert d["measured"] is True, "the blocked path is not licensed for this run"

    runs = d["runs_seconds"]
    assert runs and all(type(r) is int for r in runs)
    assert d["p95_seconds"] == max(runs), "p95 of 5 samples is the max sample"

    # Plan Step 5: default = max(60, 2 x max_sample), rounded UP to the nearest 10.
    # Rounding the outer max and rounding the doubled sample are equivalent here
    # for every input, because 60 is itself a multiple of 10 and round-up-to-10
    # is monotone -- so the two readings of the rule cannot disagree.
    expected = math.ceil(max(60, 2 * max(runs)) / 10) * 10
    assert d["default_seconds"] == expected, (
        f"default_seconds must equal max(60, 2 x {max(runs)}) rounded up to 10 = {expected}"
    )
    assert d["default_seconds"] >= 60, "the spec floor is 60s"
    assert d["derivation"].strip(), "the derivation must stay recorded"
    assert d["method"].strip(), "the measurement method must stay recorded"


def test_audit_ordered_probe_keys_present():
    """A1/A2/A3a probes must be recorded — including negative results.

    These three keys are the only record of facts that can be established
    solely inside Task 0's live-cmux window. An absent key is indistinguishable
    from an unrun probe, so presence is asserted even when the answer is "no".

    Values are asserted too, not just presence: Module 1 Step 2c makes
    `latching: false` and `available: false` STOP-and-escalate outcomes, and an
    unrun probe recorded as `false` with blank evidence must not be able to
    masquerade as a run one.
    """
    d = _verb_shapes()

    assert "surface_uuid_source" in d
    uuid_src = d["surface_uuid_source"]
    assert uuid_src.get("available") is True, (
        "Step 2c escalation trigger: available=false converts operator addendum #1 "
        "into a recorded refusal and must reach the controller, not pass silently"
    )
    assert uuid_src.get("transcript", "").strip(), (
        "an escalation-bearing probe result requires its transcript as evidence"
    )
    assert uuid_src.get("key_path", "").strip(), (
        "the UUID key path is what Task 13 consumes"
    )

    assert "wait_for_latching" in d
    latch = d["wait_for_latching"]
    assert latch.get("latching") is True, (
        "Step 2c escalation trigger: latching=false means Task 10's two-call re-wait "
        "is unsound as designed and must STOP for a plan amendment"
    )
    assert latch.get("evidence", "").strip(), (
        "latching must be backed by evidence; an unrun probe must not look like a run one"
    )
    assert latch.get("transcript", "").strip()

    assert "rc_confirmation_screen" in d
    rc = d["rc_confirmation_screen"]
    assert rc.get("rc_screen"), (
        "the /rc confirmation text is Task 11's verification anchor"
    )
    # The anchor's whole purpose is to be unmatchable by the echoed sent line.
    assert rc["rc_anchor"] in rc["rc_screen"]
    assert rc["rc_anchor"] not in rc["rc_sent_line"], (
        "an anchor the sent line contains is the 'shell echo defeats verify' defeat"
    )
    assert rc["rename_anchor"] in rc["rename_screen"]
    assert rc["rename_anchor"] not in rc["rename_sent_line"]


# ══ Task 8: policy gate ═══════════════════════════════════════════════════════


class TestPolicyDial:
    def test_off_refuses_pre_reservation(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=3, spawn_policy="off")
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3 and "reason=policy-off" in r.stderr
        assert not (ctx["reports"] / ".handoff-hops").exists()  # no hop consumed
        assert "intent" not in _spawn_log_text_or_empty(ctx)

    def test_ask_without_flag_refuses_retryable(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=3, spawn_policy="ask")
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3 and "reason=policy-ask" in r.stderr
        assert "--user-approved" in r.stderr  # retry instruction printed
        assert not (ctx["reports"] / ".handoff-hops").exists()  # pre-reservation
        assert "intent" not in _spawn_log_text_or_empty(ctx)

    def test_ask_with_flag_proceeds(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=3, spawn_policy="ask")
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", "--user-approved", env_extra=env)
        assert (
            "reason=policy-ask" not in r.stderr
        )  # gate passed (later gates may still act)
        assert r.returncode == 0, r.stderr

    # SPLIT deliberately: "absent file" and "present file, absent handoff block" are
    # two DIFFERENT code paths (shell `[ -f ]` short-circuit vs Python `auto` return).
    # One test named "or" pins only whichever the fixture happens to build.
    def test_absent_manifest_file_is_auto(self, tmp_path):
        # No .sdd-session.json at all -> the shell never calls the CLI. This
        # DELIBERATELY disagrees with the CLI (which fails closed to `ask` on a
        # nonexistent manifest path): every pre-v2 handoff ships without a
        # manifest and must still spawn. Do not "harmonize" the two layers.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "reason=policy" not in r.stderr

    def test_present_manifest_without_handoff_block_is_auto(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, omit_handoff=True)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "reason=policy" not in r.stderr

    def test_cli_failure_is_non_consent(self, tmp_path):
        # THE ONLY test pinning the *) -> ask arm: both siblings above pass even if
        # the gate is deleted. Do not weaken or drop it. There is NO SUPPORT_CLI
        # override — it is derived from SCRIPT_DIR. Seam: set SUPERPOWERS_ROOT so
        # $PYTHON falls back to bare `python3`, and put a python3 stub first on PATH
        # that DISPATCHES ON ARGV — fail only the `spawn-policy` call and `exec` the
        # real interpreter otherwise (validate_bundle makes four $PYTHON calls and
        # runs BEFORE this gate, so a blanket stub dies at bundle validation).
        # `exec` BY ABSOLUTE PATH: the stub is first on PATH and is itself named
        # python3, so a bare `exec python3 "$@"` re-enters it and, since exec does
        # not fork, spins forever — a HANG inside the untimed full-suite run.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=3, spawn_policy="auto")
        _commit(ctx)
        stubs = tmp_path / "stubs"
        stubs.mkdir(exist_ok=True)
        make_stub(
            stubs,
            "python3",
            f'case "$*" in *spawn-policy*) exit 1 ;; esac\nexec {sys.executable} "$@"',
        )
        env["SUPERPOWERS_ROOT"] = str(tmp_path / "no-venv-here")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3, r.stderr
        assert "reason=policy-ask" in r.stderr


# ══ Task 8: stall + ceiling ═══════════════════════════════════════════════════


class TestStallAndCeiling:
    def test_progress_never_refused_below_ceiling(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        for t in (0, 1, 2, 3, 4):
            write_done_report(ctx, t)
        append_outcome(ctx, 1, 2)
        append_outcome(ctx, 2, 4)
        _hops(ctx, 2)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "reason=stall" not in r.stderr

    def test_one_stall_allowed(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        for t in (0, 1, 2):
            write_done_report(ctx, t)
        append_outcome(ctx, 1, 3)  # streak 1, MAX_STALL_HOPS default 1
        _hops(ctx, 1)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "reason=stall" not in r.stderr

    def test_two_stalls_refused_with_progress_message(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        for t in (0, 1, 2):
            write_done_report(ctx, t)
        append_outcome(ctx, 1, 3)
        append_outcome(ctx, 2, 3)  # streak 2 > 1
        _hops(ctx, 2)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3, r.stderr
        assert "reason=stall" in r.stderr
        assert "tasks 3/5" in r.stderr
        assert "hops" in r.stderr
        assert "SUPERPOWERS_CMUX_MAX_STALL_HOPS" in r.stderr
        # refusal is pre-spawn: the reservation block sits after this gate
        assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "2"

    def test_first_hop_baseline_not_stall(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "reason=stall" not in r.stderr
        # Fail-LOUD guard on the P7-8 handler order: with `except FileNotFoundError`
        # removed or ordered after `except OSError`, an absent spawn log returns
        # `indeterminate`, the check SKIPs, and the script still proceeds — so
        # "returncode == 0" alone cannot tell a working first hop from a disabled
        # stall guard. This assertion is what makes that mutation visible.
        assert "stall=indeterminate" not in r.stderr

    def test_malformed_prior_outcome_indeterminate_skips(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        write_done_report(ctx, 0)
        (ctx["reports"] / "handoff-spawn.log").write_text(
            "2026-07-30T00:00:01Z u1 outcome hop=1 workspace=w launch=auto\n"
        )
        _hops(ctx, 1)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "stall=indeterminate" in r.stderr

    def test_ceiling_derived_from_expected_hops(self, tmp_path):
        # expected_hops=5 -> ceiling max(6, 2*5)=10; "9" proceeds, "10" refuses.
        # MUST exceed the floor: at expected_hops=2 the max() picks 6 and the `* 2`
        # branch decides nothing, so `* 1`/`* 3`/deleting the derivation all SURVIVE.
        # This is the ONLY pin on the shell's CEILING_FACTOR literal (the Python twin
        # is pinned by test_handoff_support.py::test_floor_factor_and_none, in its
        # `hop_ceiling(8) == 16` assertion — NOT the `hop_ceiling(None)` line, which
        # pins the FLOOR) — so this test is the SSOT divergence guard.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        _hops(ctx, 9)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, (
            f"hop 9 must proceed under a derived ceiling of 10: {r.stderr}"
        )

    def test_ceiling_derived_from_expected_hops_refuses_at_the_ceiling(self, tmp_path):
        # The refusing half of the pair above (separate tmp_path: the proceeding
        # half consumes a hop and dirties the fixture tree).
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        _hops(ctx, 10)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3 and "ceiling" in r.stderr
        assert "10/10" in r.stderr

    def test_env_ceiling_wins_absolutely(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, SUPERPOWERS_CMUX_MAX_HOPS="1")
        write_manifest(
            ctx, expected_hops=5, total_tasks=5
        )  # derived ceiling would be 10
        _hops(ctx, 1)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3 and "1/1" in r.stderr

    def test_over_expected_notifies_never_refuses(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=1, total_tasks=1)  # ceiling floors to 6
        _hops(ctx, 1)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "budget=over-expected" in r.stderr
        assert "expected" in _cmux_log(tmp_path)

    def test_intent_record_carries_tasks_done(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_done_report(ctx, 0)
        write_done_report(ctx, 1)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        log = _spawn_log_text_or_empty(ctx)
        assert re.search(r" intent hop=\d+ tasks_done=2$", log, re.M), log

    def test_ambient_hop_knob_neutralizer_actually_bites(self, tmp_path):
        """Positive control on _reach_gate's neutralizer.

        An empty-string override and an absent ambient var are indistinguishable
        from a passing test, so prove the channel works in BOTH directions: an
        ambient ceiling of 1 must REFUSE at hop 1, and neutralizing it must let
        the derived ceiling (10) through at the same hop.
        """
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        _hops(ctx, 1)
        _commit(ctx)
        hostile = dict(env, SUPERPOWERS_CMUX_MAX_HOPS="1")
        assert run_spawn(ctx, tmp_path, "b1", env_extra=hostile).returncode == 3
        assert run_spawn(ctx, tmp_path, "b1", env_extra=env).returncode == 0

    def test_unknown_tasks_done_skips_the_stall_check_and_is_recorded(self, tmp_path):
        """The shell's `unknown` branch is what makes P7-4 a non-issue.

        `stall-streak --tasks-done` is `type=int`, so feeding it the sentinel is
        argparse exit 2 — an empty STREAK that matches neither the `indeterminate`
        arm nor the numeric arm, and therefore proceeds SILENTLY. Deleting this
        branch is invisible without an assertion on the message, so pin it here.
        Degradation is forced the only honest way: a yaml-less interpreter (both
        /usr/bin/python3 and the venv ship PyYAML, so shadow the module).
        """
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        write_done_report(ctx, 0)
        _commit(ctx)
        shadow = tmp_path / "noyaml"
        shadow.mkdir(exist_ok=True)
        (shadow / "yaml.py").write_text("raise ImportError('shadowed')\n")
        env["PYTHONPATH"] = str(shadow)
        env["SUPERPOWERS_ROOT"] = str(tmp_path / "no-venv-here")  # force bare python3
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "stall=indeterminate" in r.stderr
        assert "tasks_done could not be counted" in r.stderr
        assert " intent hop=1 tasks_done=unknown" in _spawn_log_text_or_empty(ctx)

    def test_unknown_tasks_done_control_same_fixture_counts_normally(self, tmp_path):
        """Positive control for the test above: BYTE-IDENTICAL fixture minus the
        yaml shadow. Without this pair, `stall=indeterminate` could be coming from
        the fixture rather than from the forced degradation."""
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        write_done_report(ctx, 0)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "stall=indeterminate" not in r.stderr
        assert " intent hop=1 tasks_done=1" in _spawn_log_text_or_empty(ctx)
