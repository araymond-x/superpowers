"""Contract test: fixture transcripts encode their documented token totals.

Reproduces the claude-ctx-check 4-field sum by hand (missing/non-numeric -> 0,
malformed trailing line skipped) so the fixtures are pinned independently of
context-probe.py. Task 1's probe is then validated against these same fixtures.
"""
import json
from pathlib import Path

FIX = Path(__file__).parent / "fixtures" / "context-probe"
FIELDS = ("input_tokens", "cache_creation_input_tokens",
          "cache_read_input_tokens", "output_tokens")


def _coerce_int(value) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _sum_latest(path: Path):
    for line in reversed(path.read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if isinstance(usage, dict):
            return sum(_coerce_int(usage.get(f)) for f in FIELDS)
    return None


def test_below_total():
    assert _sum_latest(FIX / "below.jsonl") == 250000

def test_soft_total():
    assert _sum_latest(FIX / "soft.jsonl") == 350000

def test_hard_total():
    assert _sum_latest(FIX / "hard.jsonl") == 450000

def test_malformed_trailing_skipped():
    assert _sum_latest(FIX / "malformed-trailing.jsonl") == 250000

def test_missing_fields_count_zero():
    assert _sum_latest(FIX / "missing-fields.jsonl") == 110000

def test_non_numeric_counts_zero():
    assert _sum_latest(FIX / "non-numeric.jsonl") == 100000

def test_no_usage_returns_none():
    assert _sum_latest(FIX / "no-usage.jsonl") is None

def test_empty_returns_none():
    assert _sum_latest(FIX / "empty.jsonl") is None
