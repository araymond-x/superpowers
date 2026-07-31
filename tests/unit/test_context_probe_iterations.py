"""SP1 regression: context-probe.py must not double-count multi-iteration turns.

A single assistant turn can contain several sequential model calls. Claude Code
records them in `message.usage.iterations` and the TOP-LEVEL `usage` fields are
their SUM -- so `cache_read_input_tokens`, which is the same cached prompt
re-read by each call, is counted once per iteration. The naive top-level sum
therefore reports roughly N x the true context.

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

FIELDS = ("input_tokens", "cache_creation_input_tokens",
          "cache_read_input_tokens", "output_tokens")


def run_probe(fixture):
    result = subprocess.run(
        [sys.executable, str(PROBE), "--transcript", str(FIX / fixture)],
        capture_output=True, text=True,
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
            return sum(v if isinstance(v, int) and not isinstance(v, bool) else 0
                       for v in (usage.get(f) for f in FIELDS))
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


def test_last_message_iteration_wins_when_advisor_is_last():
    """Unobserved shape, pinned so the behavior is chosen rather than accidental.

    The fixture's top-level fields are a sentinel no real transcript carries;
    the assertion can only pass by way of the last `message` iteration.
    """
    assert legacy_total("iterations-advisor-last.jsonl") == 999999
    assert run_probe("iterations-advisor-last.jsonl") == 190000


# --- fallback branches: top-level fields are the only usable reading ---------

@pytest.mark.parametrize("fixture", [
    "iterations-empty.jsonl",           # iterations == []
    "iterations-not-a-list.jsonl",      # iterations is a scalar
    "iterations-no-message-type.jsonl",  # no `message` iteration present
    "below.jsonl",                      # pre-SP1 fixture: no `iterations` key
])
def test_falls_back_to_top_level(fixture):
    assert run_probe(fixture) == legacy_total(fixture) == 250000


def test_single_iteration_is_a_no_op():
    """The majority path. Across the retained transcript corpus every
    single-iteration turn's top-level fields equal `iterations[0]` exactly, so
    the fix cannot move those readings; the count is reported in the findings
    doc alongside the command that recomputes it."""
    assert run_probe("iterations-single.jsonl") == legacy_total("iterations-single.jsonl") == 250000
