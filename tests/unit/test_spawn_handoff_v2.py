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
    cmux_log_text,
    cmux_v2_stub,
    encode_args,
    install_bundle,
    install_version,
    make_stub,
    setup_worktree,
    write_done_report,
    write_manifest,
)
from spawn_handoff_helpers import run_spawn as _run_spawn_raw

FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"


def run_spawn(ctx, tmp_path, *args, **kw):
    """Every spawn in THIS file drives the v2-topology cmux stub by default.

    Deliberately shadows the harness import rather than being threaded through
    ~16 call sites by hand: the harness's DEFAULT stub emits no `OK surface:`
    line, so after Task 9's ref-shape check both topologies fail before launch
    and every real-spawn test in this file would exit 3 for a reason that has
    nothing to do with what it is testing. A per-site edit is a per-site chance
    to miss one. A test that needs a different body still passes `cmux_body=`
    explicitly and wins.
    """
    kw.setdefault("cmux_body", cmux_v2_stub())
    return _run_spawn_raw(ctx, tmp_path, *args, **kw)


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
    # `>= 2`, not `== 2`: two is an accidental property of the capture, so a
    # future re-capture with a third surface would go RED for the wrong reason.
    # What must hold is "at least one marker row and at least one plain row".
    assert len(rows) >= 2, "the multi fixture must retain a selected and a plain row"
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

    # The marker <-> `[selected]` CORRELATION — the semantic content of finding 4,
    # and previously unpinned: 5 inversion mutations survived, i.e. the `* ` marker
    # and the `[selected]` token could be moved onto DIFFERENT rows unnoticed. Row
    # shape alone cannot see that; assert the two travel together, in both
    # directions, on every row of both captures.
    for shape, text in (
        ("single", single),
        ("multi", multi["stdout"]),
        (
            "marker.single_row_state",
            d["selected_row_marker"]["single_row_state_same_session"],
        ),
    ):
        for row in text.splitlines():
            marked = row.startswith("* ")
            selected = "[selected]" in row
            assert marked == selected, (
                f"{shape}: the `* ` marker and `[selected]` must name the SAME row "
                f"(marker={marked}, selected={selected}): {row!r}"
            )
        assert sum(1 for row in text.splitlines() if row.startswith("* ")) == 1, (
            f"{shape}: exactly one row is selected"
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

    Values are asserted too, not just presence: an unrun probe recorded as
    `false` with blank evidence must not be able to masquerade as a run one.
    The two fields are pinned for DIFFERENT reasons, and an earlier version of
    this docstring collapsed them: `wait_for_latching.latching` is a Step 2c
    STOP-and-escalate outcome, whereas `surface_uuid_source.available` is
    defined by Step **2b**, which calls `false` a LEGITIMATE documented outcome
    rather than an escalation.
    """
    d = _verb_shapes()

    assert "surface_uuid_source" in d
    uuid_src = d["surface_uuid_source"]
    assert uuid_src.get("available") is True, (
        "Step 2b field: this run MEASURED available=true, which is what makes "
        "operator addendum #1 buildable (deferred order B3 -> IMPLEMENT). A "
        "silent flip to false would retire that decision without a record. "
        "(`false` is itself a legitimate Step 2b outcome — it is the undocumented "
        "flip that is not.)"
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
        # No knob is set here, so the invalid-knob branch must stay silent. The
        # outer `[ -n "$SUPERPOWERS_CMUX_MAX_HOPS" ]` guard was otherwise
        # unpinned: replacing it with `if true` kept MAX_HOPS correct and passed
        # the whole suite while printing an invalid-knob WARNING on EVERY run —
        # noise in the same diagnostic channel this file treats as load-bearing
        # elsewhere (the stall and tasks_done assertions bite on the message).
        #
        # M3: narrowed from a bare `"WARNING:" not in r.stderr`, which was
        # fail-closed but MISATTRIBUTING — any future warning on the no-knob path
        # would trip it and blame the knob. Narrowing risks vacuousness, so this
        # form was positive-controlled against the `if true` mutation and
        # confirmed still RED (Task 9 report, Step 1b/M3).
        assert "invalid SUPERPOWERS_CMUX_MAX_HOPS" not in r.stderr, (
            f"no knob is set — nothing may warn about one: {r.stderr}"
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
        # expected_hops=1 would derive a ceiling of 2; the floor clamp lifts it
        # to 6. Hop 5 is chosen DELIBERATELY: it proceeds only because the floor
        # applied. This is the sole behavioural pin on the clamp — the previous
        # version used hop 1, which passes at a ceiling of 2 just as well, under
        # a comment that claimed "ceiling floors to 6". Deleting the clamp now
        # makes this refuse with exit 3 instead of spawning.
        write_manifest(ctx, expected_hops=1, total_tasks=1)
        _hops(ctx, 5)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "budget=over-expected" in r.stderr
        assert "expected" in cmux_log_text(tmp_path)
        # BUDGET_FLAG's CONSUMER. Task 8 set the variable with nothing reading it
        # (a recorded SC2034, deferred to this task on the understanding that
        # Task 9's outcome printf would consume it). Landing Task 9 without this
        # assertion would leave the flag consumed-but-unpinned, which is how a
        # field silently stops being emitted.
        assert " budget=over-expected" in _spawn_log_text_or_empty(ctx)

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


# ══ Task 8 quality-review remediation ═════════════════════════════════════════
# Four mutations survived the shipped suite. Each test below exists to kill one.


class TestCeilingDerivationIsSingle:
    """The invalid-knob path must reach the SAME derivation as the default path.

    Before this pair the ceiling was derived TWICE — once as the invalid-knob
    revert target, once as the else-branch default — and only the second copy was
    reachable by a test, so `* 99` in the first SURVIVED all 107 spawn tests. The
    remediation collapses the two into one derivation; these tests pin the
    invalid-knob path onto it.

    LOAD-BEARING PRECONDITION: this pin only covers the invalid-knob path because
    the derivation is SINGLE. If anyone re-duplicates it, these tests silently
    stop covering the second copy — exactly the failure they were written for.

    expected_hops=5 -> derived ceiling max(6, 2*5) = 10, which EXCEEDS the floor,
    so the `* 2` factor decides the outcome (at expected_hops=2 the max() picks 6
    and `* 1`/`* 3`/deletion all survive).
    """

    def test_invalid_knob_reverts_to_the_derived_ceiling_and_proceeds_below_it(
        self, tmp_path
    ):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, SUPERPOWERS_CMUX_MAX_HOPS="abc")
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        _hops(ctx, 9)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert any(
            ln.startswith("WARNING:") and "MAX_HOPS" in ln
            for ln in r.stderr.splitlines()
        ), f"no MAX_HOPS warning on stderr: {r.stderr!r}"
        assert r.returncode == 0, (
            f"hop 9 must proceed under the DERIVED ceiling of 10 an invalid knob "
            f"reverts to: {r.stderr}"
        )

    def test_invalid_knob_reverts_to_the_derived_ceiling_and_refuses_at_it(
        self, tmp_path
    ):
        # Separate tmp_path: the proceeding half consumes a hop and dirties the tree.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, SUPERPOWERS_CMUX_MAX_HOPS="abc")
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        _hops(ctx, 10)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3, r.stderr
        assert "10/10" in r.stderr, (
            f"the invalid-knob revert target must be the derived 10, not the "
            f"floor or a drifted factor: {r.stderr}"
        )


class TestMaxStallHopsKnob:
    """Both halves of the validate-warn-revert contract its siblings already have.

    Mirrors test_spawn_handoff.py's quota-knob pair (invalid value still leaves
    the gate live / the knob is actually read). Neither half existed for
    MAX_STALL_HOPS: deleting the validation block AND making the env read inert
    both left the suite green, and the first is a genuine fail-OPEN — with the
    block gone, `[ 2 -gt abc ]` errors, the branch is not taken, and a two-stall
    chain that must refuse EXITS 0 AND SPAWNS.
    """

    def _two_stall_fixture(self, tmp_path, **knobs):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, **knobs)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        for t in (0, 1, 2):
            write_done_report(ctx, t)
        append_outcome(ctx, 1, 3)
        append_outcome(ctx, 2, 3)  # streak 2
        _hops(ctx, 2)
        _commit(ctx)
        return ctx, env

    def test_invalid_knob_warns_and_the_stall_gate_still_refuses(self, tmp_path):
        ctx, env = self._two_stall_fixture(
            tmp_path, SUPERPOWERS_CMUX_MAX_STALL_HOPS="abc"
        )
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert any(
            ln.startswith("WARNING:") and "MAX_STALL_HOPS" in ln
            for ln in r.stderr.splitlines()
        ), f"no MAX_STALL_HOPS warning on stderr: {r.stderr!r}"
        assert r.returncode == 3, (
            f"an invalid stall knob must revert to 1 and still refuse a two-stall "
            f"chain, not fall through and spawn: {r.stderr}"
        )
        assert "reason=stall" in r.stderr

    def test_raised_knob_is_honoured_and_the_same_chain_proceeds(self, tmp_path):
        # The env read itself: byte-identical fixture, knob raised to 5, streak 2
        # is no longer > 5. Distinct mutation from the test above — making the
        # `${SUPERPOWERS_CMUX_MAX_STALL_HOPS:-...}` read inert kills only this one.
        ctx, env = self._two_stall_fixture(
            tmp_path, SUPERPOWERS_CMUX_MAX_STALL_HOPS="5"
        )
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, (
            f"the knob the refusal message tells the user to raise must actually "
            f"be read: {r.stderr}"
        )
        assert "reason=stall" not in r.stderr


class TestPolicyOffIsNotBypassable:
    def test_off_refuses_even_with_user_approved(self, tmp_path):
        """`off` is the plan author's HARD refusal — the flag cannot override it.

        The two policy branches are adjacent and both consult SPAWN_POLICY, so
        folding them into one `[ "$SPAWN_POLICY" != "auto" ] && [ "$USER_APPROVED"
        != "1" ]` is the most natural simplification anyone will reach for — and it
        converts a hard refusal into a soft one with a green suite, because
        test_off_refuses_pre_reservation never passes the flag.
        """
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=3, spawn_policy="off")
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", "--user-approved", env_extra=env)
        assert r.returncode == 3, r.stderr
        assert "reason=policy-off" in r.stderr
        assert not (ctx["reports"] / ".handoff-hops").exists()
        assert "intent" not in _spawn_log_text_or_empty(ctx)


class TestTasksDoneFallbackAndDenominator:
    def test_failed_tasks_done_cli_degrades_to_unknown_with_a_diagnostic(
        self, tmp_path
    ):
        """The `|| TASKS_DONE="unknown"` fallback is load-bearing, not defensive.

        Sibling of test_unknown_tasks_done_skips_the_stall_check_and_is_recorded,
        but forcing the OTHER degradation: that one shadows yaml so the CLI exits 0
        printing `unknown`; this one kills the CLI outright so stdout is EMPTY.
        Delete the fallback and the empty value reaches
        `stall-streak --tasks-done ""` -> argparse exit 2 -> empty STREAK ->
        matches NEITHER arm -> a two-stall chain spawns with no diagnostic at all.
        Exit code cannot see it (both spawn), so assert the diagnostic.

        The stub DISPATCHES ON ARGV and `exec`s by ABSOLUTE path: validate_bundle
        makes four $PYTHON calls before this point (a blanket stub dies there), and
        the stub is itself named python3 first on PATH, so a bare `exec python3`
        re-enters it and spins forever inside the untimed suite.
        """
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=5, total_tasks=5)
        write_done_report(ctx, 0)
        _commit(ctx)
        stubs = tmp_path / "stubs"
        stubs.mkdir(exist_ok=True)
        make_stub(
            stubs,
            "python3",
            f'case "$*" in *tasks-done*) exit 1 ;; esac\nexec {sys.executable} "$@"',
        )
        env["SUPERPOWERS_ROOT"] = str(tmp_path / "no-venv-here")  # force bare python3
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "tasks_done could not be counted" in r.stderr
        assert "stall=indeterminate" in r.stderr
        assert " intent hop=1 tasks_done=unknown" in _spawn_log_text_or_empty(ctx)

    def test_stall_refusal_keeps_its_denominator_placeholder(self, tmp_path):
        """`TOTAL_DISP="?"` was overwritten by the substitution meant to replace it.

        A malformed manifest makes the total_tasks one-liner raise; stdout is empty
        and the refusal rendered "tasks 3/" with the denominator silently gone.
        Route: malformed JSON -> spawn-policy fails closed to `ask` -> pass
        --user-approved to reach the stall gate. The file must be PRESENT (an
        absent manifest short-circuits and never runs the substitution).
        """
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        for t in (0, 1, 2):
            write_done_report(ctx, t)
        append_outcome(ctx, 1, 3)
        append_outcome(ctx, 2, 3)  # streak 2 > default 1
        _hops(ctx, 2)
        (ctx["wt"] / ctx["feat"] / ".sdd-session.json").write_text("{not json")
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", "--user-approved", env_extra=env)
        assert r.returncode == 3, r.stderr
        assert "reason=stall" in r.stderr
        assert "tasks 3/?" in r.stderr, (
            f"the denominator placeholder must survive an unreadable manifest: "
            f"{r.stderr}"
        )


# ══ Task 9: surface topology, shared launch wrapper, workspace fallback ═══════


def _argv(tmp_path, subcmd):
    """Recorded argv of `cmux <subcmd>`, ONE ELEMENT PER LINE.

    The flat log's `echo "$@"` cannot tell a flag's VALUE from the next token,
    and every value here carries spaces or colons. Keyed on `$1`, so
    `cmux workspace create …` lives under `workspace` with `create` at argv[1].
    """
    p = Path(str(tmp_path / "cmux.log") + f".{subcmd}.argv")
    assert p.exists(), f"cmux stub recorded no `{subcmd}` call"
    return p.read_text().splitlines()


def _flag(argv, flag):
    assert flag in argv, f"{flag} absent from argv: {argv!r}"
    i = argv.index(flag)
    assert i + 1 < len(argv), f"{flag} has no value in argv: {argv!r}"
    return argv[i + 1]


def _verbs(tmp_path):
    """First token of every logged cmux call, in call order."""
    return [ln.split()[0] for ln in cmux_log_text(tmp_path).splitlines() if ln.split()]


def _outcome(ctx):
    """Fields of the single outcome record."""
    for ln in _spawn_log_text_or_empty(ctx).splitlines():
        f = ln.split()
        if len(f) > 2 and f[2] == "outcome":
            return dict(p.split("=", 1) for p in f[3:] if "=" in p)
    raise AssertionError(f"no outcome record: {_spawn_log_text_or_empty(ctx)!r}")


def _intent_spawn_id(ctx):
    for ln in _spawn_log_text_or_empty(ctx).splitlines():
        f = ln.split()
        if len(f) > 2 and f[2] == "intent":
            return f[1]
    raise AssertionError("no intent record")


def _sent_text(tmp_path):
    """The text `cmux send` delivered (argv element after the surface ref)."""
    argv = _argv(tmp_path, "send")
    return argv[-1]


class TestSurfaceTopology:
    def test_surface_happy_path(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=3, total_tasks=5)
        _commit(ctx)  # the manifest is new content; Precondition 1 wants it clean
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr

        # ORDER is the contract, not mere presence: renaming after the launch, or
        # waiting before it, would each pass a presence-only check.
        verbs = [v for v in _verbs(tmp_path) if v != "notify"]
        assert verbs == ["new-surface", "rename-tab", "send", "wait-for"], verbs

        ns = _argv(tmp_path, "new-surface")
        assert _flag(ns, "--workspace") == "TEST-WS"  # the CALLER's workspace
        assert _flag(ns, "--type") == "terminal"
        assert _flag(ns, "--focus") == "false"  # never steal the user's attention

        rt = _argv(tmp_path, "rename-tab")
        assert _flag(rt, "--workspace") == "TEST-WS"
        assert _flag(rt, "--surface") == "surface:7"

        sd = _argv(tmp_path, "send")
        assert _flag(sd, "--surface") == "surface:7"

        out = _outcome(ctx)
        assert out["workspace"] == "TEST-WS"
        assert out["surface"] == "surface:7"
        assert out["handshake"] == "ok"
        assert "topology" not in out, "the surface path is the default, not a variant"

    def test_sent_command_ends_with_the_successor_command(self, tmp_path):
        # The launch payload must actually carry the composed command: an inline
        # env prefix with nothing after it would `send` a no-op and still leave
        # every env assertion below green.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        marker = "[spawn-handoff] successor command: "
        composed = [
            ln[len(marker) :] for ln in r.stderr.splitlines() if ln.startswith(marker)
        ]
        assert composed, "no composed successor command emitted"
        sent = _sent_text(tmp_path)
        assert sent.endswith(composed[0] + "\\n"), (
            f"sent text must END with the composed command plus the Enter "
            f"escape: sent={sent!r} composed={composed[0]!r}"
        )

    def test_sent_command_carries_inline_env(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, SUPERPOWERS_CMUX_MAX_STALL_HOPS="2")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        sent = _sent_text(tmp_path)
        assert sent.startswith("export SUPERPOWERS_SPAWN_ID=")
        # IDENTITY, not shape. `startswith("export SUPERPOWERS_SPAWN_ID=")` is
        # satisfied by an EMPTY value — which is exactly what composing
        # INLINE_ENV before SPAWN_ID is generated would produce. The id the
        # successor exports must be the id this hop recorded.
        assert f"export SUPERPOWERS_SPAWN_ID={_intent_spawn_id(ctx)}" in sent
        # A knob set on the parent reaches the child inline; settings files are
        # not read by an already-running session, so this is the only channel.
        assert "SUPERPOWERS_CMUX_MAX_STALL_HOPS=2" in sent

    def test_unset_knobs_are_not_forwarded_as_empty(self, tmp_path):
        # Positive control's mirror: without this, an INLINE_ENV that forwarded
        # every knob unconditionally (`KNOB=` with an empty value) would satisfy
        # the test above and silently override the child's own defaults with
        # empty strings.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "SUPERPOWERS_CMUX_MAX_STALL_HOPS" not in _sent_text(tmp_path)

    def test_forwarded_knob_values_are_shell_quoted(self, tmp_path):
        """`shq` on the forwarded knob VALUES, which nothing else exercises.

        The composed line is delivered verbatim into a live terminal by `cmux
        send`, so quoting is the only thing between an operator-controlled env
        value and command execution in the successor's shell. Every other
        assertion in this class forwards a single-token value (`2`), which
        quotes to ITSELF — so dropping `shq` is invisible to all of them.

        SUBSTRING TRAP, defeated by the `KNOB=` anchor: the bare payload is a
        substring of the quoted form, so a bare `in` check on the VALUE alone
        would be true in both arms and prove nothing. Anchoring each assertion
        on the `KNOB=` prefix is what makes them discriminate — `KNOB='a b; …'`
        (quote's leading `'` immediately after the `=`) and `KNOB=a b; …` are
        mutually exclusive renderings of the same variable.

        BOTH legs independently kill the mutant, and neither is redundant.
        MEASURED under `$(shq "$v")` → `$v`: the PRESENCE assertion is the one
        that fired — the quoted form is absent from the mutant output — while
        the raw output confirms the bare form IS present, so the absence leg
        would have fired too. Do not delete either as vacuous. Both are asserted
        against the rendered `send` payload, the only place INLINE_ENV appears
        (the `successor command:` stderr echo carries no env prefix).
        """
        payload = "a b; touch /tmp/PWNED"
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, SUPERPOWERS_CMUX_TITLE_FORMAT=payload)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        sent = _sent_text(tmp_path)
        assert "SUPERPOWERS_CMUX_TITLE_FORMAT='a b; touch /tmp/PWNED'" in sent, (
            f"forwarded knob value is not shell-quoted: {sent!r}"
        )
        assert f"SUPERPOWERS_CMUX_TITLE_FORMAT={payload}" not in sent, (
            f"the bare value reached the sent line — the `;` would execute: {sent!r}"
        )

    def test_tab_title_renders_hop_and_feature(self, tmp_path):
        # rename-tab failure is warn-and-continue, so a title rendered as
        # `hop SDD feat` (TAB_TITLE composed before SP_HOP exists) or a literal
        # `hop{hop} SDD {feature}` would never fail anything. Pin the VALUE.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert _argv(tmp_path, "rename-tab")[-1] == "hop1 SDD feat"

    def test_tab_title_format_knob_is_read(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(
            tmp_path, ctx, SUPERPOWERS_CMUX_TITLE_FORMAT="X{feature}/{hop}"
        )
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert _argv(tmp_path, "rename-tab")[-1] == "Xfeat/1"

    def test_rename_failure_still_launches(self, tmp_path):
        # A missing tab title is cosmetic; it must never cost the handoff.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, CMUX_RENAME_RC="1")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "rename-tab failed" in r.stderr
        assert "send" in _verbs(tmp_path), "a cosmetic failure blocked the launch"
        assert _outcome(ctx)["handshake"] == "ok"
        # Still the SURFACE path: a rename failure must not trigger the fallback.
        assert "workspace create" not in cmux_log_text(tmp_path)

    def test_rename_tab_carries_workspace_on_both_topologies(self, tmp_path):
        """deviations.md:17 — rename-tab resolves refs ONLY in the caller's
        workspace unless --workspace is passed (MEASURED: `not_found: Tab not
        found`, exit 1). On the fallback path its absence is fatal to the rename:
        the successor surface is BY DEFINITION not in the caller's workspace.
        And because rename failure is warn-and-continue, a permanently-failing
        rename would stay green forever without this pin.

        BOTH topologies genuinely run here. This test previously drove the
        surface path only, while a sibling covered the fallback — so scoping
        rename-tab to the CALLER's workspace killed the sibling and left THIS
        test, under its "both topologies" name, green against its own subject.
        That is the shape where a later reader deletes the sibling believing
        this one covers it.

        Per-leg tmp dirs: every harness path (`stubs/`, `home/`, `cmux.log` and
        its per-verb argv files) is keyed on tmp_path, so two subdirs give two
        independent runs — and two independent `.rename-tab.argv` files, which
        one shared log could not tell apart.
        """
        # Consume the frozen fixture rather than restating the flag.
        rename_argv = _verb_shapes()["rename_tab"]["argv"]
        assert "--workspace" in rename_argv, "frozen contract lost the flag"

        surf = tmp_path / "surface-leg"
        surf.mkdir()
        ctx_s = setup_worktree(surf)
        r_s = run_spawn(ctx_s, surf, "b1", env_extra=_reach_gate(surf, ctx_s))
        assert r_s.returncode == 0, r_s.stderr
        assert _flag(_argv(surf, "rename-tab"), "--workspace") == "TEST-WS"

        fb = tmp_path / "fallback-leg"
        fb.mkdir()
        ctx_f = setup_worktree(fb)
        r_f = run_spawn(
            ctx_f, fb, "b1", env_extra=_reach_gate(fb, ctx_f, CMUX_NEW_SURFACE_RC="1")
        )
        assert r_f.returncode == 0, r_f.stderr
        # The CREATED workspace's ref, NOT the caller's — this is the leg where
        # a bare rename-tab was measured to fail outright.
        assert _flag(_argv(fb, "rename-tab"), "--workspace") == "workspace:9"

    def test_rename_tab_success_is_never_ref_parsed(self, tmp_path):
        # Shared Contract §1: rename-tab's field 2 is `action=rename`, NOT a ref.
        # Parsing it back would poison the surface ref the send then addresses.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert _flag(_argv(tmp_path, "send"), "--surface") == "surface:7"
        assert _outcome(ctx)["surface"] == "surface:7"
        assert "action=rename" not in _spawn_log_text_or_empty(ctx)

    def test_new_surface_failure_falls_back_to_workspace_once(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, CMUX_NEW_SURFACE_RC="1")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        log = cmux_log_text(tmp_path)
        # The CANONICAL verb (Decision 19), never the deprecated alias.
        assert "workspace create" in log
        assert "new-workspace" not in log
        wc = _argv(tmp_path, "workspace")
        assert wc[:2] == ["workspace", "create"]
        assert _flag(wc, "--focus") == "false"
        assert _flag(wc, "--name") == "SDD resume: feat"
        out = _outcome(ctx)
        assert out["topology"] == "workspace-fallback"
        assert out["workspace"] == "workspace:9"
        # Resolved from the marker-bearing `* surface:11 … [selected]` row: a
        # parser reading awk's $1 gets `*` and fails the ref-shape gate.
        assert out["surface"] == "surface:11"
        assert out["handshake"] == "ok"

    def test_fallback_refuses_when_no_surface_ref_can_be_resolved(self, tmp_path):
        """`create_workspace_target`'s ref-shape gate, made reachable.

        The gate is REDUNDANT with the awk parser under every other shape the
        stub can emit (the parser yields `^surface:[0-9]+$` or nothing), so
        without a stub that returns zero surface tokens no assertion can
        distinguish it from `if true`. `CMUX_LIST_SURFACES_NO_REF` returns a row
        with no `surface:N` token — the parser SKIPS it, the gate fires.

        There is no stderr message unique to this refusal (both the capture's
        shape check and this gate return 1 silently), so the pin is an evidence
        COMBINATION, not a message: the workspace WAS created, the launch never
        happened, and the outcome names no surface. Without the gate the empty
        ref flows into `rename-tab --surface ''` and `send --surface ''`, the
        stub answers OK to both, and the run reports success while addressing
        nothing — the exact production failure Task 0 measured.

        DISCRIMINATOR, asserted FIRST: every other leg of that combination —
        including `rc == 3` — is equally true of any abort EARLIER in
        `create_workspace_target` (MEASURED: a `return 1` right after the
        `workspace create` rc check leaves the rest of this test green, and so
        does `CMUX_WS_CREATE_RC=1`). Only `list-pane-surfaces` having been
        invoked becomes FALSE in that world, so it is the one assertion proving
        the run actually reached the gate this test names. It runs before the
        `returncode` pin so a regression attributes here, not to a bare rc.
        """
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(
            tmp_path, ctx, CMUX_NEW_SURFACE_RC="1", CMUX_LIST_SURFACES_NO_REF="1"
        )
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        verbs = _verbs(tmp_path)
        assert "list-pane-surfaces" in verbs, (
            f"never reached the ref-resolve step — this run aborted earlier in "
            f"create_workspace_target, so the ref-shape gate was never exercised: "
            f"{verbs!r}"
        )
        assert r.returncode == 3, r.stderr
        assert "workspace create" in cmux_log_text(tmp_path), (
            "control leg: the fallback workspace must actually have been created"
        )
        assert "rename-tab" not in verbs, "launched against an unresolvable ref"
        assert "send" not in verbs, "launched against an unresolvable ref"
        out = _outcome(ctx)
        assert out["workspace"] == "spawn-failed"
        assert out["surface"] == "-", (
            "an unresolved ref must not be reported as a target"
        )
        assert out["topology"] == "workspace-fallback"
        assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"

    def test_selected_row_wins_over_the_first_row_on_the_fallback(self, tmp_path):
        """The `[selected]` branch, separated from `END{print first}`.

        On the default ONE-row stub the first row IS the selected row, so the
        two branches agree on every input and `if(index($0,"[selected]"))` is
        indistinguishable from `if(0)`. Two rows with the marker on the SECOND
        make them disagree. (`END{if(!f)print first}` stays unpinned — both stub
        shapes carry a selected row; noted so it is not re-filed as new.)
        """
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(
            tmp_path, ctx, CMUX_NEW_SURFACE_RC="1", CMUX_LIST_SURFACES_TWO_ROWS="1"
        )
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert _flag(_argv(tmp_path, "send"), "--surface") == "surface:11", (
            "launched into the FIRST surface rather than the selected one"
        )
        assert _outcome(ctx)["surface"] == "surface:11"

    def test_timeout_record_keeps_its_topology_and_budget_suffixes(self, tmp_path):
        """The `handshake=timeout` record's two trailing fields.

        `budget=over-expected` was pinned only on the `handshake=ok` record, and
        no test reached fallback + timeout together, so BOTH suffixes could be
        dropped from this printf unnoticed — losing exactly the diagnostics a
        failed hop is investigated with. Reaching the two conditions at once
        pins both on the one record.
        """
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, CMUX_NEW_SURFACE_RC="1", CMUX_WAITFOR_RC="1")
        # Same clamp arithmetic as test_over_expected_notifies_never_refuses:
        # hop 6 > expected 1 sets BUDGET_FLAG while the ceiling floor of 6
        # still allows the spawn.
        write_manifest(ctx, expected_hops=1, total_tasks=1)
        _hops(ctx, 5)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3, r.stderr
        out = _outcome(ctx)
        assert out["handshake"] == "timeout"
        assert out["topology"] == "workspace-fallback"
        assert out["budget"] == "over-expected"

    def test_fallback_is_attempted_exactly_once(self, tmp_path):
        # "One-shot" is the containment property: a retry loop around a broken
        # cmux would create a workspace per attempt.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, CMUX_NEW_SURFACE_RC="1", CMUX_WS_CREATE_RC="1")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3, r.stderr
        assert _verbs(tmp_path).count("workspace") == 1
        assert _outcome(ctx)["workspace"] == "spawn-failed"
        assert _outcome(ctx)["handshake"] == "none"
        assert _outcome(ctx)["topology"] == "workspace-fallback"
        assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"

    def test_send_failure_on_surface_falls_back(self, tmp_path):
        # The launch command is not "accepted" until `cmux send` returns 0, so a
        # failure THERE is still before the point of no return.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, CMUX_SEND_FAIL_COUNT="1")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert "workspace create" in cmux_log_text(tmp_path)
        assert _outcome(ctx)["topology"] == "workspace-fallback"
        assert _verbs(tmp_path).count("send") == 2

    def test_second_send_failure_is_spawn_failed(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, CMUX_SEND_FAIL_COUNT="2")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3, r.stderr
        out = _outcome(ctx)
        assert out["workspace"] == "spawn-failed"
        assert out["handshake"] == "none"
        assert out["surface"] == "surface:11"  # the fallback target is still named
        assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"
        assert "Manual resume required" in r.stdout

    def test_no_double_spawn_after_accepted_send(self, tmp_path):
        # THE containment invariant: `cmux send` rc 0 means the command is
        # accepted. After that, a handshake timeout is a DIAGNOSIS problem, never
        # a reason to create a second target — that is how a runaway chain starts.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, CMUX_WAITFOR_RC="1")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3, r.stderr
        verbs = _verbs(tmp_path)
        assert verbs.count("new-surface") == 1
        assert "workspace create" not in cmux_log_text(tmp_path)
        assert _outcome(ctx)["handshake"] == "timeout"
        assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"

    def test_token_is_the_only_exit_zero_path(self, tmp_path):
        # The wait-for name must be derived from THIS hop's spawn id, or the
        # handshake would latch on some other session's token.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        wf = _argv(tmp_path, "wait-for")
        assert wf[1] == f"sdd-hop-{_intent_spawn_id(ctx)}"
        assert _flag(wf, "--timeout") == "60"

    def test_wait_timeout_knob_is_read_and_validated(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT="7")
        assert run_spawn(ctx, tmp_path, "b1", env_extra=env).returncode == 0
        assert _flag(_argv(tmp_path, "wait-for"), "--timeout") == "7"

    def test_invalid_wait_timeout_warns_and_reverts(self, tmp_path):
        # Validate-warn-revert, like every other knob. Unvalidated, the value
        # reaches `cmux wait-for --timeout` as garbage.
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx, SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT="abc")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert any(
            ln.startswith("WARNING:") and "SPAWN_WAIT_TIMEOUT" in ln
            for ln in r.stderr.splitlines()
        ), r.stderr
        assert _flag(_argv(tmp_path, "wait-for"), "--timeout") == "60"

    def test_wait_timeout_default_matches_the_frozen_fixture(self):
        # Consistency check against Task 0's measurement record. NOTE the 60 is
        # the SPEC FLOOR, not a measured cold start — `max(60, 2 x 11) = 60`.
        d = json.loads((FIX / "cold-start-timing.json").read_text())
        src = (
            Path(__file__).resolve().parent.parent.parent
            / "skills"
            / "subagent-driven-development"
            / "scripts"
            / "spawn-handoff-session.sh"
        ).read_text()
        m = re.search(r"^SPAWN_WAIT_TIMEOUT_DEFAULT=(\d+)$", src, re.M)
        assert m, "SPAWN_WAIT_TIMEOUT_DEFAULT must be a column-0 literal assignment"
        assert int(m.group(1)) == d["default_seconds"]

    def test_dry_run_names_the_surface_topology_and_spawns_nothing(self, tmp_path):
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(tmp_path, ctx)
        write_manifest(ctx, expected_hops=3, total_tasks=5)
        write_done_report(ctx, 0)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", "--dry-run", env_extra=env)
        assert r.returncode == 0, r.stderr
        out = r.stdout + r.stderr
        assert "would spawn surface in TEST-WS" in out
        assert "workspace fallback armed" in out
        assert "policy=auto" in out and "tasks_done=1" in out
        assert "new-surface" not in cmux_log_text(tmp_path)
        assert not (ctx["reports"] / ".handoff-hops").exists()

    def test_spawn_claude_workspace_is_gone(self):
        # The old workspace-only core is superseded by create_workspace_target +
        # the shared launch wrapper. A dead copy would be a second, untested
        # spawn path in a script whose whole risk is spawning twice.
        src = (
            Path(__file__).resolve().parent.parent.parent
            / "skills"
            / "subagent-driven-development"
            / "scripts"
            / "spawn-handoff-session.sh"
        ).read_text()
        assert "spawn_claude_workspace" not in src
        # Comment lines are stripped: the rationale comment legitimately NAMES
        # the deprecated alias to explain why it is gone. What must not survive
        # is an executable reference to it.
        code = "\n".join(
            ln for ln in src.splitlines() if not ln.lstrip().startswith("#")
        )
        assert "EXPECTED_HOPS" in code, "comment-stripping removed live code"
        assert "new-workspace" not in code, "the deprecated verb must be gone"


# --- Task 10: handshake, re-wait, read-screen diagnosis --------------------

SCREENS = FIX / "screens"


def _screen(name):
    return str(SCREENS / name)


def _wait_for_lines(tmp_path):
    """Every logged `wait-for` CALL — one entry per call, in call order.

    Deliberately NOT `_flag(_argv(tmp_path, "wait-for"), "--timeout")`. The
    `.argv` sidecar is `printf '%s\n' "$@"`, i.e. one line per TOKEN, appended
    across BOTH calls with no separator, and `_flag` resolves only the FIRST
    occurrence — so that spelling would assert one value once and leave the
    re-wait half of "both waits use the same duration" entirely VACUOUS. The
    flat log is one line per call, and `--timeout 60` contains no spaces, so
    splitting each line is sound.
    """
    return [
        ln for ln in cmux_log_text(tmp_path).splitlines() if ln.startswith("wait-for ")
    ]


def _timeout_ctx(tmp_path, screen=None, waitfor_rc="1", **knobs):
    """A spawnable ctx whose handshake times out, optionally showing a screen."""
    ctx = setup_worktree(tmp_path)
    extra = {"CMUX_WAITFOR_RC": waitfor_rc}
    if screen is not None:
        extra["CMUX_SCREEN_FILE"] = _screen(screen)
    extra.update(knobs)
    env = _reach_gate(tmp_path, ctx, **extra)
    write_manifest(ctx, expected_hops=3, total_tasks=5)
    _commit(ctx)
    return ctx, env


def _diagnose(tmp_path, screen=None, **knobs):
    """Run a timing-out spawn against `screen` and return (result, ctx)."""
    ctx, env = _timeout_ctx(tmp_path, screen=screen, **knobs)
    r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
    return r, ctx


class TestHandshakeFixtureProvenance:
    """The derived screen fixtures must keep EQUALLING the frozen captures.

    A fixture authored to agree with the code under test proves only that the
    same string can be spelled twice; these three are written FROM
    `cmux-verb-shapes.json` and pinned back to it byte-for-byte so neither side
    can drift. Comparison is exact — no `.strip()`, which would turn a
    byte-exact anti-drift pin into a fuzzy one.
    """

    def test_trust_dialog_fixture_matches_the_frozen_capture(self):
        d = _verb_shapes()
        assert (SCREENS / "trust-dialog.txt").read_text(encoding="utf-8") == d[
            "trust_dialog_screen"
        ]["screen"]

    def test_banner_fixture_matches_the_frozen_capture(self):
        # banner.txt is ALSO derived from a live capture, so it needs the same
        # anti-drift pin as trust-dialog.txt — a derived fixture with no
        # equality test can drift from the capture it claims to derive from
        # with every other test still green.
        d = _verb_shapes()
        assert (SCREENS / "banner.txt").read_text(encoding="utf-8") == d[
            "rc_confirmation_screen"
        ]["rc_screen"]

    def test_noise_fixture_matches_the_frozen_capture(self):
        # noise.txt is derived from `read_screen_warm` — a LIVE capture of a
        # plain shell surface — rather than hand-authored. Same pin, same
        # reason.
        d = _verb_shapes()
        assert (SCREENS / "noise.txt").read_text(encoding="utf-8") == d[
            "read_screen_warm"
        ]["stdout"]

    def test_synthetic_fixtures_declare_themselves_synthetic(self):
        # The two un-captured screens must SAY so where they live: an anchor
        # nobody measured is a hypothesis, not a contract, and the next reader
        # must not mistake one for the other.
        for name in ("picker-error.txt", "both-anchors.txt"):
            text = (SCREENS / name).read_text(encoding="utf-8")
            assert "SYNTHETIC FIXTURE (not a capture)" in text, name

    def test_derived_fixtures_do_not_claim_to_be_synthetic(self):
        # Positive control for the assertion above: it must be capable of
        # telling the two families apart, not merely of finding a string.
        for name in ("trust-dialog.txt", "banner.txt", "noise.txt"):
            text = (SCREENS / name).read_text(encoding="utf-8")
            assert "SYNTHETIC FIXTURE" not in text, name


class TestHandshake:
    def test_token_is_only_success(self, tmp_path):
        # A full Claude banner on screen with NO token is NOT success. Three
        # live incidents came from treating "something is visible" as done.
        r, ctx = _diagnose(tmp_path, screen="banner.txt")
        assert r.returncode == 3, r.stderr
        o = _outcome(ctx)
        assert o["handshake"] == "timeout"
        assert o["diagnosis"] == "banner"

    def test_token_success_exits_0_handshake_ok(self, tmp_path):
        ctx, env = _timeout_ctx(tmp_path, waitfor_rc="0")
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 0, r.stderr
        assert _outcome(ctx)["handshake"] == "ok"
        # Success never diagnoses: read-screen is enrichment for FAILURE only.
        assert "diagnosis" not in _outcome(ctx)
        assert len(_wait_for_lines(tmp_path)) == 1, "a received token must not re-wait"

    def test_timeout_rewaits_once_same_duration(self, tmp_path):
        r, ctx = _diagnose(tmp_path, screen="noise.txt")
        assert r.returncode == 3, r.stderr
        lines = _wait_for_lines(tmp_path)
        assert len(lines) == 2, f"expected exactly one re-wait: {lines!r}"
        timeouts = []
        for ln in lines:
            f = ln.split()
            assert "--timeout" in f, ln
            timeouts.append(f[f.index("--timeout") + 1])
        # BOTH values compared, from BOTH calls — see _wait_for_lines' docstring
        # for why the `.argv` sidecar cannot express this.
        assert timeouts == ["60", "60"], timeouts

    def test_diagnosis_trust_dialog_names_dialog_and_steers_to_tab(self, tmp_path):
        r, ctx = _diagnose(tmp_path, screen="trust-dialog.txt")
        assert r.returncode == 3, r.stderr
        assert _outcome(ctx)["diagnosis"] == "trust-dialog"
        err = r.stderr
        assert "trust" in err.lower()
        assert "surface:7" in err, err
        # The discriminator vs picker-error/none: trust-dialog and banner steer
        # the operator to the EXISTING tab, so the fresh-session block (printed
        # on stdout by print_manual_instructions) must be ABSENT.
        assert "Manual resume required" not in r.stdout, r.stdout

    def test_real_trust_capture_diagnoses_trust_not_banner(self, tmp_path):
        # The screen driven here IS the frozen capture (pinned byte-exact
        # above), so this asserts against measured reality rather than against
        # a fixture written to agree with the patterns.
        r, ctx = _diagnose(tmp_path, screen="trust-dialog.txt")
        assert _outcome(ctx)["diagnosis"] == "trust-dialog", (
            "the real trust modal must never be classified `banner` — that "
            "would tell the operator to attach and continue instead of to "
            "answer the dialog"
        )

    def test_ordering_trust_beats_banner_on_a_both_anchors_screen(self, tmp_path):
        # Removing `claude code` from the banner pattern DISSOLVED the overlap
        # that once made ordering load-bearing on a captured screen, so
        # "reorder the greps and confirm RED" now yields GREEN against every
        # capture. Ordering is still correct defense-in-depth — a trust modal
        # CAN be raised over a pane that already painted a statusline — so it
        # is pinned here with an explicitly SYNTHETIC screen carrying both
        # MEASURED anchors. THIS is the test whose positive control goes RED
        # when the two greps are swapped.
        r, ctx = _diagnose(tmp_path, screen="both-anchors.txt")
        assert r.returncode == 3, r.stderr
        assert _outcome(ctx)["diagnosis"] == "trust-dialog"

    def test_diagnosis_banner_steers_to_tab_and_omits_manual_block(self, tmp_path):
        r, ctx = _diagnose(tmp_path, screen="banner.txt")
        assert _outcome(ctx)["diagnosis"] == "banner"
        assert "surface:7" in r.stderr
        assert "Manual resume required" not in r.stdout, r.stdout

    def test_both_live_session_captures_diagnose_banner(self, tmp_path):
        # rc_screen AND rename_screen are two live captures of a running Claude
        # session. Driven verbatim from the fixture, not from banner.txt, so
        # this covers the capture banner.txt is NOT derived from.
        d = _verb_shapes()
        screen = tmp_path / "rename_screen.txt"
        screen.write_text(
            d["rc_confirmation_screen"]["rename_screen"], encoding="utf-8"
        )
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(
            tmp_path, ctx, CMUX_WAITFOR_RC="1", CMUX_SCREEN_FILE=str(screen)
        )
        write_manifest(ctx, expected_hops=3, total_tasks=5)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3, r.stderr
        assert _outcome(ctx)["diagnosis"] == "banner"

    def test_diagnosis_picker_error(self, tmp_path):
        r, ctx = _diagnose(tmp_path, screen="picker-error.txt")
        assert _outcome(ctx)["diagnosis"] == "picker-error"
        # picker-error DOES print the manual block: there is no live session to
        # attach to, so a manual resume is the correct next move.
        assert "Manual resume required" in r.stdout, r.stdout

    def test_diagnosis_none_on_noise(self, tmp_path):
        r, ctx = _diagnose(tmp_path, screen="noise.txt")
        assert _outcome(ctx)["diagnosis"] == "none"
        assert "Manual resume required" in r.stdout, r.stdout

    def test_diagnosis_unreadable_when_read_screen_fails_outright(self, tmp_path):
        # Disjunct (a)+(b) together: the stub's natural failure emits
        # `internal_error` AND exits 1, and the script reads with 2>&1.
        r, ctx = _diagnose(tmp_path, screen=None)
        assert r.returncode == 3, r.stderr
        assert _outcome(ctx)["diagnosis"] == "unreadable"

    def test_diagnosis_unreadable_on_internal_error_text_with_rc_zero(self, tmp_path):
        # Isolates the SECOND disjunct: rc 0, but the literal in the output.
        screen = tmp_path / "quiet_internal_error.txt"
        screen.write_text("internal_error: Failed to read terminal text\n")
        ctx = setup_worktree(tmp_path)
        env = _reach_gate(
            tmp_path, ctx, CMUX_WAITFOR_RC="1", CMUX_SCREEN_FILE=str(screen)
        )
        write_manifest(ctx, expected_hops=3, total_tasks=5)
        _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
        assert r.returncode == 3, r.stderr
        assert _outcome(ctx)["diagnosis"] == "unreadable"

    def test_diagnosis_unreadable_on_nonzero_rc_with_clean_output(self, tmp_path):
        # Isolates the FIRST disjunct, which NOTHING else can reach: a non-zero
        # read-screen rc whose output carries no `internal_error` at all. The
        # screen is `noise.txt`, which diagnoses `none` at rc 0 — so if the rc
        # test were deleted this would fall through to `none` and go RED.
        r, ctx = _diagnose(tmp_path, screen="noise.txt", CMUX_READ_SCREEN_RC="3")
        assert r.returncode == 3, r.stderr
        assert _outcome(ctx)["diagnosis"] == "unreadable", (
            "a non-zero read-screen rc must diagnose `unreadable` on its own, "
            "independently of the `internal_error` literal"
        )

    def test_timeout_notifies_and_keeps_hop(self, tmp_path):
        r, ctx = _diagnose(tmp_path, screen="banner.txt")
        assert r.returncode == 3, r.stderr
        # The hop stays consumed: a successor WAS launched.
        assert (ctx["reports"] / ".handoff-hops").read_text().strip() == "1"
        assert "notify" in _verbs(tmp_path)
        notify = _argv(tmp_path, "notify")
        body = " ".join(notify)
        assert "banner" in body, body
        # Positive content, not merely an absence: the operator must be told
        # WHERE the successor is and that the hop was spent. Without these the
        # "never claims nothing was spawned" assertion below would still pass
        # if the whole branch were deleted.
        assert "surface:7" in r.stderr
        assert "hop 1 consumed" in r.stderr, r.stderr
        combined = r.stdout + r.stderr
        for lie in ("nothing was spawned", "no spawn attempted", "nothing spawned"):
            assert lie not in combined, lie
