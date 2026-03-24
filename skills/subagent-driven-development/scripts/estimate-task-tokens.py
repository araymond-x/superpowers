#!/usr/bin/env python3
"""
estimate-task-tokens.py

Estimates the token count of a subagent prompt before dispatch.
Uses a 1 token = 4 characters approximation (standard industry estimate).
Adds a fixed overhead for the implementer prompt template.

Exit codes:
  0 - OK or WARNING (caller should inspect JSON status field)
  1 - TOO_LARGE (caller should split the task before dispatching)
  2 - Script error (bad arguments, file not found, etc.)

Usage:
  python scripts/estimate-task-tokens.py \
    --task-file /path/to/task-section.txt \
    --constraints-file /path/to/constraints.txt \
    --context "additional context string" \
    --context-budget 200000
"""

import argparse
import json
import os
import sys

# Approximate token overhead for the implementer-prompt.md template itself
# (system instructions, structural text, formatting). Conservative estimate.
TEMPLATE_OVERHEAD_TOKENS = 2000

# Threshold at which the task is considered large but still dispatchable.
# 25% of the default 200K context budget.
WARNING_THRESHOLD_FRACTION = 0.25

# Threshold at which the task must NOT be dispatched — it needs splitting.
# 50% of the default 200K context budget.
TOO_LARGE_THRESHOLD_FRACTION = 0.50

CHARS_PER_TOKEN = 4


def chars_to_tokens(char_count: int) -> int:
    """Convert character count to an approximate token count."""
    return max(0, char_count // CHARS_PER_TOKEN)


def read_file_tokens(path: str) -> int:
    """Read a file and return its approximate token count."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return chars_to_tokens(len(content))


def build_result(
    task_tokens: int,
    constraints_tokens: int,
    context_tokens: int,
    template_overhead: int,
    context_budget: int,
) -> dict:
    """Build the result dict with status and warning fields."""
    total = task_tokens + constraints_tokens + context_tokens + template_overhead
    budget_remaining = context_budget - total

    warning_threshold = int(context_budget * WARNING_THRESHOLD_FRACTION)
    too_large_threshold = int(context_budget * TOO_LARGE_THRESHOLD_FRACTION)

    if total >= too_large_threshold:
        status = "TOO_LARGE"
        warning = (
            f"Estimated prompt size ({total:,} tokens) exceeds {int(TOO_LARGE_THRESHOLD_FRACTION * 100)}% "
            f"of the context budget ({context_budget:,} tokens). "
            "Do NOT dispatch this task. Split it into smaller subtasks before proceeding."
        )
    elif total >= warning_threshold:
        status = "WARNING"
        warning = (
            f"Estimated prompt size ({total:,} tokens) exceeds {int(WARNING_THRESHOLD_FRACTION * 100)}% "
            f"of the context budget ({context_budget:,} tokens). "
            "Proceed with dispatch but instruct the subagent to focus narrowly and ask "
            "questions rather than reading broadly."
        )
    else:
        status = "OK"
        warning = None

    return {
        "task_tokens": task_tokens,
        "constraints_tokens": constraints_tokens,
        "context_tokens": context_tokens,
        "template_overhead": template_overhead,
        "total_estimated": total,
        "budget_remaining": budget_remaining,
        "status": status,
        "warning": warning,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate the token count of a subagent prompt before dispatch. "
            "Outputs JSON to stdout. "
            "Exit code 1 if status is TOO_LARGE, 0 otherwise."
        )
    )
    parser.add_argument(
        "--task-file",
        required=True,
        metavar="PATH",
        help="Path to the file containing the task text extracted from the plan.",
    )
    parser.add_argument(
        "--constraints-file",
        required=False,
        default=None,
        metavar="PATH",
        help=(
            "Path to the file containing the Contract Constraints section. "
            "Omit or leave empty if the plan has no Contract Constraints."
        ),
    )
    parser.add_argument(
        "--context",
        required=False,
        default="",
        metavar="STRING",
        help=(
            "Additional context string to include in the token estimate "
            "(e.g., scene-setting text, source file excerpts passed inline)."
        ),
    )
    parser.add_argument(
        "--context-budget",
        required=False,
        type=int,
        default=200000,
        metavar="TOKENS",
        help=(
            "Total context window budget in tokens. "
            "Thresholds are computed as fractions of this value. "
            "Default: 200000 (200K)."
        ),
    )
    args = parser.parse_args()

    # Validate task file
    if not os.path.isfile(args.task_file):
        print(
            json.dumps({"error": f"Task file not found: {args.task_file}"}),
            file=sys.stderr,
        )
        return 2

    # Validate constraints file (optional)
    if args.constraints_file and not os.path.isfile(args.constraints_file):
        print(
            json.dumps(
                {"error": f"Constraints file not found: {args.constraints_file}"}
            ),
            file=sys.stderr,
        )
        return 2

    # Validate context budget
    if args.context_budget <= 0:
        print(
            json.dumps({"error": "--context-budget must be a positive integer"}),
            file=sys.stderr,
        )
        return 2

    # Compute token estimates
    try:
        task_tokens = read_file_tokens(args.task_file)
    except OSError as e:
        print(json.dumps({"error": f"Could not read task file: {e}"}), file=sys.stderr)
        return 2

    constraints_tokens = 0
    if args.constraints_file:
        try:
            constraints_tokens = read_file_tokens(args.constraints_file)
        except OSError as e:
            print(
                json.dumps({"error": f"Could not read constraints file: {e}"}),
                file=sys.stderr,
            )
            return 2

    context_tokens = chars_to_tokens(len(args.context))

    result = build_result(
        task_tokens=task_tokens,
        constraints_tokens=constraints_tokens,
        context_tokens=context_tokens,
        template_overhead=TEMPLATE_OVERHEAD_TOKENS,
        context_budget=args.context_budget,
    )

    print(json.dumps(result, indent=2))

    # Exit 1 for TOO_LARGE so scripts/callers can check exit code directly
    return 1 if result["status"] == "TOO_LARGE" else 0


if __name__ == "__main__":
    sys.exit(main())
