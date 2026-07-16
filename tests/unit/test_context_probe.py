"""Subprocess tests for context-probe.py (--transcript / --json path).

Drives the probe as a subprocess under sys.executable to mirror how the SDD
pre-dispatch hook (Module 2) invokes it. Validates the token totals against the
8 Task-0 fixtures plus a two-usage reverse-scan proof and the exit-code
contracts (no transcript / no usage block / missing file).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
PROBE = ROOT / "skills" / "subagent-driven-development" / "scripts" / "context-probe.py"
FIX = Path(__file__).parent / "fixtures" / "context-probe"


def run_probe(*args):
    return subprocess.run(
        [sys.executable, str(PROBE), *args],
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "fixture,expected",
    [
        ("below.jsonl", "250000"),
        ("soft.jsonl", "350000"),
        ("hard.jsonl", "450000"),
        ("malformed-trailing.jsonl", "250000"),
        ("missing-fields.jsonl", "110000"),
        ("non-numeric.jsonl", "100000"),
    ],
)
def test_transcript_totals(fixture, expected):
    result = run_probe("--transcript", str(FIX / fixture))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


def test_json_output_shape():
    result = run_probe("--transcript", str(FIX / "below.jsonl"), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["total_tokens"] == 250000
    assert payload["transcript"].endswith("below.jsonl")
    assert payload["source_version"]


def test_transcript_prefers_most_recent_usage():
    result = run_probe("--transcript", str(FIX / "two-usage.jsonl"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "350000"


def test_no_usage_nonzero_exit():
    result = run_probe("--transcript", str(FIX / "no-usage.jsonl"))
    assert result.returncode != 0
    assert "usage" in result.stderr.lower()


def test_empty_nonzero_exit():
    result = run_probe("--transcript", str(FIX / "empty.jsonl"))
    assert result.returncode != 0


def test_missing_transcript_nonzero_exit():
    result = run_probe("--transcript", str(FIX / "does-not-exist.jsonl"))
    assert result.returncode != 0
