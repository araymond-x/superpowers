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
from pathlib import Path

FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"


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
    assert rows[0].startswith("* "), "row 1 is the selected row and carries the `* ` marker"
    assert rows[0].split()[0] == "*", "awk $1 on a marker row is `*`, never the ref"
    assert rows[0].split()[1].startswith("surface:"), "the ref is field 2 on a marker row"
    assert rows[1].startswith("  "), "non-selected rows are two-space indented"
    assert rows[1].split()[0].startswith("surface:"), "awk $1 on a non-selected row IS the ref"

    marker = d["selected_row_marker"]
    assert marker["production_shape"].startswith("SINGLE-ROW"), (
        "Module 3 must be told which shape the fallback path actually parses"
    )
    assert marker["awk_consequence"].strip(), "the parser consequence must stay recorded"


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
    assert trust["screen"].strip(), "the trust-modal screen is Module 3's diagnosis fixture"
    assert trust["candidate_anchors"], "trust-dialog anchors must be non-empty"
    for anchor in trust["candidate_anchors"]:
        assert anchor.strip()
        assert anchor in trust["screen"], "each anchor must actually occur in the captured screen"


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
    assert uuid_src.get("key_path", "").strip(), "the UUID key path is what Task 13 consumes"

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
    assert rc.get("rc_screen"), "the /rc confirmation text is Task 11's verification anchor"
    # The anchor's whole purpose is to be unmatchable by the echoed sent line.
    assert rc["rc_anchor"] in rc["rc_screen"]
    assert rc["rc_anchor"] not in rc["rc_sent_line"], (
        "an anchor the sent line contains is the 'shell echo defeats verify' defeat"
    )
    assert rc["rename_anchor"] in rc["rename_screen"]
    assert rc["rename_anchor"] not in rc["rename_sent_line"]
