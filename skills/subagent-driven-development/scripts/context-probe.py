#!/usr/bin/env python3
"""
context-probe.py — context-window token sensor for a Claude Code transcript.

Vendored stdlib-only mirror of ~/.claude/bin/claude-ctx-check's
`find_latest_usage`: scan a transcript JSONL from the end for the most recent
assistant `message.usage` block and sum four token fields:

    T = input_tokens + cache_creation_input_tokens
        + cache_read_input_tokens + output_tokens

Unlike claude-ctx-check this probe is window-less and percentage-less — it
emits ONLY the absolute token total. Thresholds (SOFT / HARD / FALLBACK_STREAK)
belong to the SDD pre-dispatch hook that consumes this probe, not here.

Stdlib-only by design: the hook invokes it under bare `python3`, which has no
pydantic/PyYAML. No third-party imports may be added.

Parity divergence from the source (deliberate, documented): claude-ctx-check
sums with naive `usage.get(f, 0)` and would raise TypeError on a non-numeric
field; this probe coerces non-numeric fields to 0 via `_coerce_int`. The
differential parity test (Task 2) therefore compares the two only on
well-formed fixtures.

Resolution priority: `--transcript` → `--session-id` → $CLAUDE_CODE_SESSION_ID.
Task 1 implements ONLY the `--transcript` path; `--session-id` and env-var
resolution are Task 2 (resolve_transcript currently returns None for those).

Exit codes:
    0  printed the token total (bare int, or JSON with --json)
    1  no transcript resolvable, or no usage block found in the transcript
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Recorded from Task 0: shasum -a 256 ~/.claude/bin/claude-ctx-check | cut -c1-12
SOURCE_VERSION = "f83727ff80c0"

PROJECTS_DIR = Path.home() / ".claude" / "projects"

FIELDS = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)


def _coerce_int(value) -> int:
    """Numeric int → itself; anything else (missing, str, float, bool) → 0."""
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def find_latest_total(transcript_path: Path) -> Optional[int]:
    """Scan the transcript from the end for the most recent assistant `usage`
    block and return the 4-field token sum. Malformed (non-JSON) lines are
    skipped. Returns None if no usage block exists."""
    for line in reversed(transcript_path.read_text().splitlines()):
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


def resolve_transcript(args) -> Optional[Path]:
    """Task-1 stub: resolves ONLY --transcript to a file path.

    Task 2 extends this with --session-id / env-var resolution.
    """
    if args.transcript:
        p = Path(args.transcript)
        return p if p.is_file() else None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Context-window token sensor.")
    parser.add_argument("--transcript", help="path to a transcript JSONL file")
    parser.add_argument(
        "--session-id", help="session UUID (Task 2 — not yet resolved)"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON"
    )
    args = parser.parse_args()

    transcript = resolve_transcript(args)
    if transcript is None:
        print(
            "context-probe: no transcript resolvable (missing id or file)",
            file=sys.stderr,
        )
        return 1

    total = find_latest_total(transcript)
    if total is None:
        print(
            "context-probe: no usage block found in transcript "
            "(no completed turn)",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "total_tokens": total,
                    "transcript": str(transcript),
                    "source_version": SOURCE_VERSION,
                }
            )
        )
    else:
        print(total)

    return 0


if __name__ == "__main__":
    sys.exit(main())
