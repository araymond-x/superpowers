"""SP1 regression: context-probe.py must not double-count multi-iteration turns.

A single assistant turn can contain several sequential model calls. Claude Code
records them in `message.usage.iterations` and the TOP-LEVEL `usage` fields are
the sum of the `type: "message"` iterations ONLY -- a non-`message` iteration
(e.g. `advisor_message`) is excluded from them. `cache_read_input_tokens` is the
same cached prompt re-read by each `message` call, so it is counted once per
`message` iteration and the naive top-level sum reports roughly N x the true
context, where N is the number of `message` iterations (~2x on the common
two-`message` shape; `test_three_message_iterations_scale_beyond_2x` pins that
this is not a structural constant).

`usage.iterations` is an undocumented, version-unstable internal shape, so
`usage_total` falls back to the top-level reading whenever the preferred
iteration is missing, INCOMPLETE (not all four token fields present as genuine
ints), or yields no usable total. The completeness requirement is what stops a
partially readable iteration from being returned as a small-but-truthy
"measurement"; `test_legitimate_zero_field_is_not_over_rejected` is its
over-rejection control, and `test_all_zero_iteration_falls_back_to_top_level`
pins the truthiness branch the guard does not subsume.

Root cause and evidence:
docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md

Each multi-iteration test is DIFFERENTIAL: it asserts the corrected value AND
that the value is not the legacy top-level sum, so a revert cannot pass. The
fallback tests pin the branches where the top-level fields remain the only
usable reading; `test_single_iteration_is_a_no_op` pins the majority path,
where the two agree by construction.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
PROBE = ROOT / "skills" / "subagent-driven-development" / "scripts" / "context-probe.py"
FIX = Path(__file__).parent / "fixtures" / "context-probe"

FIELDS = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)


def run_probe(fixture):
    result = subprocess.run(
        [sys.executable, str(PROBE), "--transcript", str(FIX / fixture)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return int(result.stdout.strip())


def legacy_total(fixture):
    """The pre-fix reading: naive 4-field sum of the last top-level usage block.

    Reimplemented here rather than imported, so the differential assertions
    compare the probe against an independent statement of the old behavior.
    """
    for line in reversed((FIX / fixture).read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        usage = (json.loads(line).get("message") or {}).get("usage")
        if isinstance(usage, dict):
            return sum(
                v if isinstance(v, int) and not isinstance(v, bool) else 0
                for v in (usage.get(f) for f in FIELDS)
            )
    raise AssertionError("fixture has no usage block")


# --- multi-iteration turns: corrected, and provably not the legacy value -----


def test_advisor_triple_is_not_double_counted():
    """The real archived block behind BACKLOG N76.

    cmux-transport session d8a9d842, 2026-07-30T00:55:22Z -- the turn that
    wrote `tokens=373139` to context-observations.log. Its two `message`
    iterations read 180,524 and 181,567 cached tokens; summing both reports a
    ~373k context that never existed. The turn's last model call saw 189,929.
    """
    assert legacy_total("iterations-advisor-triple.jsonl") == 373139
    assert run_probe("iterations-advisor-triple.jsonl") == 189929


def test_message_pair_is_not_double_counted():
    """Multi-iteration is not advisor-specific -- ('message','message') occurs."""
    assert legacy_total("iterations-message-pair.jsonl") == 405004
    assert run_probe("iterations-message-pair.jsonl") == 204202


def test_three_message_iterations_scale_beyond_2x():
    """The inflation ratio scales with the `message` iteration count.

    The commonly observed shape has two `message` iterations and inflates ~2x
    (measured range 1.94-2.00, never exactly 2.0). That is not structural: a
    three-`message` turn inflates ~2.93x here. Pinned so any tuning rule
    keyed on a fixed "2.0x" discriminator is visibly wrong against a fixture
    rather than only against prose.
    """
    assert legacy_total("iterations-message-triple.jsonl") == 315406
    assert run_probe("iterations-message-triple.jsonl") == 107802


def test_non_dict_iteration_entries_are_skipped():
    """Junk entries in `iterations` must not crash or capture the reading.

    The non-dict entries sit AFTER the valid `message` iteration, so the
    reverse scan reaches them first -- without the `isinstance(iteration,
    dict)` guard the very first entry (`null`) raises AttributeError and the
    probe exits non-zero.
    """
    assert legacy_total("iterations-non-dict-entries.jsonl") == 250000
    assert run_probe("iterations-non-dict-entries.jsonl") == 182001


def test_zero_summing_message_iteration_falls_back_to_top_level():
    """A preferred-but-unusable iteration must never read as a measurement.

    This fixture's iteration carries NONE of the four token fields, so it is
    rejected by the completeness guard (see
    `test_partial_iteration_one_surviving_field_falls_back`), not by the
    `if total:` branch -- that branch is pinned separately by
    `test_all_zero_iteration_falls_back_to_top_level`.

    Either way the requirement is the same: returning the iteration's 0 would
    discard a well-formed top-level reading and present as a SUCCESSFUL probe
    of an empty context. The pre-dispatch gate reads `tier=below action=allow`
    and a poisoned `action=allow` row also resets an in-progress fallback
    streak. `iterations` is version-unstable, so this is the degradation path
    for a future shape change as well.
    """
    assert run_probe("iterations-message-no-fields.jsonl") == 250000
    assert legacy_total("iterations-message-no-fields.jsonl") == 250000


# --- completeness guard: a PARTIALLY readable iteration is not a measurement --
#
# `_coerce_int` maps every unreadable field to 0, so an iteration that lost one
# field still sums to a small TRUTHY number and would be returned as a
# successful measurement. `cache_read_input_tokens` is a median ~98% of a real
# iteration's four-field total, so losing it alone collapses a large context to
# a small ALLOWED number in a blocking gate: the real archived 493,759-token
# block reads as 24,234 with that one field renamed. The guard therefore
# requires all four fields present as genuine ints before trusting the
# iteration, and degrades to the legacy top-level reading otherwise -- a
# known-wrong-HIGH reading fails safe where a wrong-LOW one does not.


def test_partial_iteration_one_surviving_field_falls_back():
    """One surviving int field must not be read as the turn's context.

    Without the guard this returns `1` -- the survivor -- and the gate allows.
    The assertion is the TOP-LEVEL value, so it cannot pass on the small number.
    """
    assert legacy_total("iterations-message-one-int-field.jsonl") == 250000
    assert run_probe("iterations-message-one-int-field.jsonl") == 250000


def test_partial_iteration_renamed_field_falls_back():
    """The realistic case: `iterations` drifts and renames one field.

    `cache_read_input_tokens` is renamed; the other three are intact and
    genuine. Without the guard the probe returns `1902` and reports it as a
    measurement. `iterations` is documented as an undocumented, non-
    version-stable shape, so a partial rename is the expected way it breaks.
    """
    assert legacy_total("iterations-message-renamed-field.jsonl") == 250000
    assert run_probe("iterations-message-renamed-field.jsonl") == 250000


def test_bool_in_an_int_slot_falls_back():
    """`True` is an `int` subclass -- the guard must reject it anyway.

    `_coerce_int` maps `True` to 0, so an iteration with a bool in one slot
    sums to an UNDERCOUNT (181900 here) that is still truthy. Drop the
    `not isinstance(..., bool)` clause and that undercount is returned.
    """
    assert legacy_total("iterations-message-bool-field.jsonl") == 250000
    assert run_probe("iterations-message-bool-field.jsonl") == 250000


def test_legitimate_zero_field_is_not_over_rejected():
    """OVER-REJECTION CONTROL. A real `0` is a reading, not a missing field.

    The guard's own failure mode is over-rejection: silently discarding a
    good iteration and reverting to the double-counted top-level reading. A
    `message` iteration whose `cache_creation_input_tokens` is a legitimate
    `0` (the ordinary shape when nothing new was cached) is COMPLETE --
    `isinstance(0, int)` is True -- and must be used.

    Differential: the top-level sum is 250000, so this can only pass by way of
    the iteration.
    """
    assert legacy_total("iterations-message-legit-zero-field.jsonl") == 250000
    assert run_probe("iterations-message-legit-zero-field.jsonl") == 182001


def test_all_zero_iteration_falls_back_to_top_level():
    """Pins `if total:`, which the completeness guard does NOT subsume.

    All four fields are present as genuine int `0`, so the guard admits the
    iteration; only the truthiness test rescues it. Without `if total:` the
    probe returns 0 and the gate reads `tier=below action=allow`. This is the
    branch that keeps `if total:` from looking like dead code after the guard.
    """
    assert legacy_total("iterations-message-all-zero-fields.jsonl") == 250000
    assert run_probe("iterations-message-all-zero-fields.jsonl") == 250000


def test_last_message_iteration_wins_when_advisor_is_last():
    """Unobserved shape, pinned so the behavior is chosen rather than accidental.

    The fixture's top-level fields are a sentinel no real transcript carries;
    the assertion can only pass by way of the last `message` iteration.
    """
    assert legacy_total("iterations-advisor-last.jsonl") == 999999
    assert run_probe("iterations-advisor-last.jsonl") == 190000


# --- fallback branches: top-level fields are the only usable reading ---------


@pytest.mark.parametrize(
    "fixture",
    [
        "iterations-empty.jsonl",  # iterations == []
        "iterations-not-a-list.jsonl",  # iterations is a NON-ITERABLE scalar
        "iterations-string.jsonl",  # iterations is a str: iterable, not a list
        "iterations-no-message-type.jsonl",  # no `message` iteration present
        "below.jsonl",  # pre-SP1 fixture: no `iterations` key
    ],
)
def test_falls_back_to_top_level(fixture):
    assert run_probe(fixture) == legacy_total(fixture) == 250000


def test_single_iteration_is_a_no_op():
    """The majority path. Across the retained transcript corpus every
    single-iteration turn's top-level fields equal `iterations[0]` exactly, so
    the fix cannot move those readings; the count is reported in the findings
    doc alongside the command that recomputes it."""
    assert (
        run_probe("iterations-single.jsonl")
        == legacy_total("iterations-single.jsonl")
        == 250000
    )
