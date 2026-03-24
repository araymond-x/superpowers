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
  # Read task text directly from a file:
  python scripts/estimate-task-tokens.py \
    --task-file /path/to/task-section.txt \
    --constraints-file /path/to/constraints.txt \
    --context "additional context string" \
    --context-budget 200000

  # Extract a task section from a plan file by task number:
  python scripts/estimate-task-tokens.py \
    --plan-file /path/to/plan.md \
    --task 3 \
    --constraints-file /path/to/constraints.txt \
    --context "additional context string"

When --plan-file and --task are both provided they take precedence over
--task-file.  The script extracts the text from the matching "### Task N"
header through the next "### Task" header (or end of file).
"""

import argparse
import json
import os
import re
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


def extract_task_from_plan(plan_path: str, task_number: int) -> str:
    """
    Read a plan markdown file and extract the text for the given task number.

    Finds the section starting at "### Task N" (case-insensitive) and ending
    at the next "### Task" header or end of file.

    Args:
        plan_path: Path to the plan markdown file.
        task_number: The task number to extract (matches "### Task N").

    Returns:
        The extracted task text as a string.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If no matching task section is found.
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the start of the target task section
    start_pattern = re.compile(
        rf"^###\s+Task\s+{task_number}\b",
        re.MULTILINE | re.IGNORECASE,
    )
    start_match = start_pattern.search(content)
    if not start_match:
        raise ValueError(f"Task {task_number} not found in plan file: {plan_path}")

    # Find the start of the next task section
    next_task_pattern = re.compile(
        r"^###\s+Task\s+\d+\b",
        re.MULTILINE | re.IGNORECASE,
    )
    next_match = next_task_pattern.search(content, start_match.end())
    end = next_match.start() if next_match else len(content)

    return content[start_match.start() : end]


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
        required=False,
        default=None,
        metavar="PATH",
        help=(
            "Path to the file containing the task text. "
            "Mutually exclusive with --plan-file/--task. "
            "One of --task-file or (--plan-file + --task) is required."
        ),
    )
    parser.add_argument(
        "--plan-file",
        required=False,
        default=None,
        metavar="PATH",
        help=(
            "Path to the implementation plan markdown file. "
            "Use with --task to extract a specific task section. "
            "Takes precedence over --task-file when both are provided."
        ),
    )
    parser.add_argument(
        "--task",
        required=False,
        default=None,
        type=int,
        metavar="N",
        help=(
            "Task number to extract from the plan file (used with --plan-file). "
            "Matches '### Task N' headers (case-insensitive)."
        ),
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

    # Determine task input mode and resolve task text
    use_plan_mode = args.plan_file is not None and args.task is not None
    use_file_mode = args.task_file is not None

    if not use_plan_mode and not use_file_mode:
        print(
            json.dumps(
                {"error": ("One of --task-file or (--plan-file + --task) is required.")}
            ),
            file=sys.stderr,
        )
        return 2

    if use_plan_mode:
        # --plan-file + --task mode: extract the task section from the plan
        if not os.path.isfile(args.plan_file):
            print(
                json.dumps({"error": f"Plan file not found: {args.plan_file}"}),
                file=sys.stderr,
            )
            return 2
        try:
            task_text = extract_task_from_plan(args.plan_file, args.task)
        except ValueError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 2
        except OSError as e:
            print(
                json.dumps({"error": f"Could not read plan file: {e}"}),
                file=sys.stderr,
            )
            return 2
        task_tokens = chars_to_tokens(len(task_text))
    else:
        # --task-file mode: read the file directly
        if not os.path.isfile(args.task_file):
            print(
                json.dumps({"error": f"Task file not found: {args.task_file}"}),
                file=sys.stderr,
            )
            return 2
        try:
            task_tokens = read_file_tokens(args.task_file)
        except OSError as e:
            print(
                json.dumps({"error": f"Could not read task file: {e}"}),
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

    # Compute constraints token estimate
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
