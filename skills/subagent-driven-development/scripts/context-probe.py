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

Parity divergences from the source (both deliberate and documented; this is a
PARTIAL mirror):

  1. claude-ctx-check sums with naive `usage.get(f, 0)` and would raise
     TypeError on a non-numeric field; this probe coerces non-numeric fields
     to 0 via `_coerce_int`.

  2. Multi-iteration turns (SP1, 2026-07-30). A single assistant turn can
     contain several sequential model calls — Claude Code records them in
     `usage.iterations`, and the TOP-LEVEL `usage` fields are the sum of the
     `type: "message"` iterations ONLY; a non-`message` iteration (e.g.
     `advisor_message`) is excluded from them. Each `message` call re-reads
     the same cached prompt, so `cache_read_input_tokens` is counted once per
     `message` iteration and the naive top-level sum reports close to — but
     ALWAYS STRICTLY BELOW — N x the true context, where N is the number of
     `message` iterations. Strictly below because the last iteration's own
     `cache_creation_input_tokens` and `output_tokens` are not duplicated;
     only the re-read prompt is. Measured: two-`message` turns run 1.94x-2.00x
     and are exactly 2.0 in none of them; a three-`message` turn measures
     ~2.9x (2.9258 on the committed fixture, 2.9679 on the quality review's).
     This probe therefore reads the LAST `type: "message"` iteration — the
     turn's final model call, whose prompt is the accumulated context — and
     falls back to the top-level fields when no such iteration exists or when
     the one it finds yields no usable total. See
     docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md.
     claude-ctx-check still carries the uncorrected behavior; fixing it is out
     of this script's scope. The statusline `ctx:` field does NOT carry it —
     that claim was falsified by pre-registered experiment on 2026-07-31; the
     statusline is harness-computed (see the same findings doc).

     `usage.iterations` is an UNDOCUMENTED internal shape and is NOT
     version-stable. Claude Code's own documentation states: "the transcript
     entry format is internal to Claude Code and changes between versions, so
     it's not a stable contract." The fallback in `usage_total` is what makes
     a future shape change degrade to the legacy top-level reading rather
     than to a silent zero.

Divergence 2 is a no-op on single-iteration turns: their top-level fields equal
`iterations[0]` exactly. Verified across the retained transcript corpus — the
count is reproduced by the audit script quoted in the findings doc above, not
memorized here. The differential parity test compares probe against source only
on well-formed, single-iteration fixtures.

Resolution priority: `--transcript` → `--session-id` → $CLAUDE_CODE_SESSION_ID.
`--session-id` and $CLAUDE_CODE_SESSION_ID both resolve by globbing
~/.claude/projects/*/<id>.jsonl by filename (the session UUID is unique).

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


def _sum_fields(block) -> int:
    """4-field token sum over a usage dict or a single iteration dict."""
    return sum(_coerce_int(block.get(f)) for f in FIELDS)


def _last_message_iteration(usage) -> Optional[dict]:
    """The turn's final `type: "message"` iteration, or None.

    A turn may interleave non-`message` iterations (an `advisor_message` is a
    separate model's call against its own copied context, so its tokens are not
    this session's context). Scanning from the end for the last `message`
    iteration yields the turn's final model call whichever way they interleave.
    None means the top-level fields are the only usable reading — `iterations`
    absent, not a list, empty, or carrying no `message` iteration at all.
    """
    iterations = usage.get("iterations")
    if not isinstance(iterations, list):
        return None
    for iteration in reversed(iterations):
        if isinstance(iteration, dict) and iteration.get("type") == "message":
            return iteration
    return None


def usage_total(usage) -> int:
    """Context-token total for one assistant `usage` block.

    Prefers the last `message` iteration (parity divergence 2 in the module
    docstring — the top-level fields sum the `type: "message"` iterations, so
    they double-count `cache_read_input_tokens` across a multi-iteration
    turn). Falls back to the top-level fields, which is the legacy behavior
    and is exactly equal on single-iteration turns.

    The preferred iteration is trusted only when it is COMPLETE: all four
    `FIELDS` present on it as genuine ints (`bool` excluded, since
    `_coerce_int` maps `True` to 0). A partially readable iteration is not a
    partial measurement — it is a small wrong number. `_coerce_int` maps every
    unreadable field to 0, so an iteration that lost one field reports the sum
    of the survivors and exits 0, presenting as a successful measurement. That
    matters because `cache_read_input_tokens` is the overwhelming majority of a
    real iteration's total, so losing it alone collapses a genuinely large
    context to a small allowed number: a real archived 493,759-token block
    reads as 24,234 with that one field renamed. This probe feeds a BLOCKING
    pre-dispatch gate, where a small total reads as `tier=below action=allow`
    and additionally resets an in-progress fallback streak — worse than a probe
    failure, which routes to the byte-proxy and eventually blocks.

    What the completeness guard trades, stated because it is deliberate: an
    `iterations` shape that changes in a way the guard does not recognize now
    degrades to the LEGACY TOP-LEVEL READING, which is the known double-
    counting path this divergence exists to correct. That is the intended
    failure direction. In a blocking gate a known-wrong-HIGH reading fails
    safe — it can only over-block, and an over-block is retryable by a human —
    while a wrong-LOW reading silently disarms the gate. `iterations` is an
    undocumented, version-unstable shape, so this is the degradation path for a
    future shape change as much as for corruption today.

    `if total:` survives the guard and is NOT dead code: it covers the one
    shape the guard admits but cannot use — all four fields present as int `0`,
    summing to 0. A `0` from the PREFERRED-ITERATION source must never be
    mistaken for a measurement. (The top-level fallback source is not held to
    that rule; a top-level block carrying no recognized fields still yields 0.
    That is pre-existing legacy behavior, unchanged here.)
    """
    iteration = _last_message_iteration(usage)
    if iteration is not None and not all(
        isinstance(iteration.get(f), int) and not isinstance(iteration.get(f), bool)
        for f in FIELDS
    ):
        iteration = None
    if iteration is not None:
        total = _sum_fields(iteration)
        if total:
            return total
    return _sum_fields(usage)


def find_latest_total(transcript_path: Path) -> Optional[int]:
    """Scan the transcript from the end for the most recent assistant `usage`
    block and return its context-token total (see `usage_total`). Malformed
    (non-JSON) lines are skipped. Returns None if no usage block exists."""
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
            return usage_total(usage)
    return None


def find_transcript(session_id: str) -> Optional[Path]:
    """Glob ~/.claude/projects/*/<session_id>.jsonl by filename.

    Mirrors claude-ctx-check's resolver: the session id is a globally unique
    UUID, so a filename search across project dirs is exact and immune to
    Claude Code's sanitized-cwd directory-naming rule (which is deliberately
    NOT reconstructed here). Returns None if no matching transcript exists.
    """
    if not PROJECTS_DIR.is_dir():
        return None
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        candidate = project_dir / f"{session_id}.jsonl"
        if candidate.is_file():
            return candidate
    return None


def resolve_transcript(args) -> Optional[Path]:
    """Resolve a transcript path by priority: --transcript → --session-id →
    $CLAUDE_CODE_SESSION_ID. Returns None if none resolves to an existing file.
    """
    if args.transcript:
        p = Path(args.transcript)
        return p if p.is_file() else None
    session_id = args.session_id or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        return None
    return find_transcript(session_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Context-window token sensor.")
    parser.add_argument("--transcript", help="path to a transcript JSONL file")
    parser.add_argument(
        "--session-id",
        help="session UUID; resolved via ~/.claude/projects/*/<id>.jsonl",
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
            "context-probe: no usage block found in transcript (no completed turn)",
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
