"""Unit matrix for the cmux-spawn-v2 rework. Task 0 seeds the fixture contracts;
Modules 3-4 append behavior tests."""

import json
from pathlib import Path

FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"


def test_verb_shapes_fixture_contract():
    d = json.loads((FIX / "cmux-verb-shapes.json").read_text())
    ns = d["new_surface"]["stdout"].split()
    assert ns[0] == "OK" and ns[1].startswith("surface:")
    ws = d["workspace_create"]["stdout"].split()
    assert ws[0] == "OK" and ws[1].startswith("workspace:")
    rt = d["rename_tab"]["stdout"].split()
    assert rt[1] == "action=rename", "rename-tab field 2 must never be treated as a ref"
    assert "internal_error" in d["read_screen_cold"]["stdout"] or d["read_screen_cold"]["exit"] != 0


def test_cold_start_default_derivation():
    d = json.loads((FIX / "cold-start-timing.json").read_text())
    assert isinstance(d["default_seconds"], int) and d["default_seconds"] >= 60
    if d["measured"]:
        assert d["default_seconds"] >= 2 * max(d["runs_seconds"])


def test_audit_ordered_probe_keys_present():
    """A1/A2/A3a probes must be recorded — including negative results.

    These three keys are the only record of facts that can be established
    solely inside Task 0's live-cmux window. An absent key is indistinguishable
    from an unrun probe, so presence is asserted even when the answer is "no".
    """
    d = json.loads((FIX / "cmux-verb-shapes.json").read_text())

    assert "surface_uuid_source" in d
    assert isinstance(d["surface_uuid_source"].get("available"), bool)

    assert "wait_for_latching" in d
    assert isinstance(d["wait_for_latching"].get("latching"), bool)

    assert "rc_confirmation_screen" in d
    rc = d["rc_confirmation_screen"]
    assert rc.get("rc_screen"), "the /rc confirmation text is Task 11's verification anchor"
