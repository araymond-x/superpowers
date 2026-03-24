#!/usr/bin/env python3
"""
validate-plan.py

Mechanically verify plan structure before the plan-document-reviewer subagent is
dispatched.  Catches structural issues deterministically (line counts, section
presence) so the reviewer can focus on semantic issues (contract accuracy, snippet
correctness).

Exit codes:
  0 - PASS   (no blockers, no warnings)
  1 - FAIL   (one or more blocking checks failed)
  2 - WARNING (warnings only, no blockers)
  3 - Script error (bad arguments, file not found, etc.)

Usage:
  python validate-plan.py --plan-file /path/to/plan.md
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

# -----------------------------------------------------------------------
# Thresholds
# -----------------------------------------------------------------------

# Plans longer than this (in lines) require explicit modular decomposition to pass.
PLAN_LINE_LIMIT = 800

# Individual tasks longer than this (in lines) raise a warning.
TASK_LINE_LIMIT = 200

# Number of lines from the top of the document considered the "header area" for
# required-section checks.
HEADER_AREA_LINES = 50

# -----------------------------------------------------------------------
# Compiled patterns
# -----------------------------------------------------------------------

# Matches "### Task N" task headers (any optional title after the number)
TASK_HEADER_RE = re.compile(r"^###\s+Task\s+(\d+)", re.MULTILINE | re.IGNORECASE)

# Matches a "Module" header anywhere in the document (signals modular decomposition)
MODULE_HEADER_RE = re.compile(r"^#{1,4}\s+Module\b", re.MULTILINE | re.IGNORECASE)

# Source Contracts header/inline (flexible: with or without colon, any heading level)
SOURCE_CONTRACTS_RE = re.compile(
    r"(?:^#{1,4}\s*Source\s+Contracts?\s*:?|^\*{0,2}Source\s+Contracts?:)",
    re.MULTILINE | re.IGNORECASE,
)

# Contract Constraints header/inline
CONTRACT_CONSTRAINTS_RE = re.compile(
    r"(?:^#{1,4}\s*Contract\s+Constraints?\s*:?|\bContract\s+Constraints?\b)",
    re.MULTILINE | re.IGNORECASE,
)

# Feature Archetype header/inline
FEATURE_ARCHETYPE_RE = re.compile(
    r"(?:^#{1,4}\s*Feature\s+Archetype\s*:?|\*{0,2}Feature\s+Archetype\s*:)",
    re.MULTILINE | re.IGNORECASE,
)

# Code Footprint — any occurrence in the header area
CODE_FOOTPRINT_RE = re.compile(r"\bCode\s+Footprint\b", re.IGNORECASE)

# Write-Scope Partitioning section anywhere in the document
WRITE_SCOPE_RE = re.compile(
    r"^#{1,4}\s*Write[\-\s]+Scope\s+Partitioning",
    re.MULTILINE | re.IGNORECASE,
)

# File Map / New Files / Modified Files section
FILE_MAP_RE = re.compile(
    r"^#{1,4}\s*(?:File\s+Map|New\s+Files?|Modified\s+Files?)",
    re.MULTILINE | re.IGNORECASE,
)

# Unchecked checkbox
UNCHECKED_RE = re.compile(r"^\s*-\s+\[ \]", re.MULTILINE)

# Checked checkbox (case-insensitive x)
CHECKED_RE = re.compile(r"^\s*-\s+\[x\]", re.MULTILINE | re.IGNORECASE)


# -----------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------


def read_file(path: str) -> str:
    """Read a file and return its text contents. Raises OSError on failure."""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def header_area(lines: List[str]) -> str:
    """Return the first HEADER_AREA_LINES lines joined as a single string."""
    return "\n".join(lines[:HEADER_AREA_LINES])


def extract_inline_value(content: str, pattern: re.Pattern) -> Optional[str]:
    """
    Given a regex that matches a header or label, return the text on the same
    line after the colon (if any).  Returns None if the pattern is not found or
    there is nothing after the colon.
    """
    match = pattern.search(content)
    if not match:
        return None
    rest_of_line = content[match.end() :].split("\n", 1)[0].strip(" :*")
    return rest_of_line if rest_of_line else None


# -----------------------------------------------------------------------
# Size analysis
# -----------------------------------------------------------------------


def analyse_tasks(lines: List[str]) -> Tuple[List[Dict], List[str], List[str]]:
    """
    Walk the line list, find every ### Task N header, and measure the line span
    for each task section.

    Returns:
        tasks     - list of dicts with keys: number, name, lines, status
        warnings  - human-readable warning strings
        blockers  - human-readable blocker strings (currently unused; size is a warning)
    """
    tasks: List[Dict] = []
    warnings: List[str] = []
    blockers: List[str] = []

    # Collect (line_index, task_number, task_name) for all task headers
    header_positions: List[Tuple[int, int, str]] = []
    for idx, line in enumerate(lines):
        m = re.match(r"^###\s+Task\s+(\d+)\s*(.*)", line, re.IGNORECASE)
        if m:
            task_num = int(m.group(1))
            task_name = m.group(2).lstrip(":- ").strip() or f"Task {task_num}"
            header_positions.append((idx, task_num, task_name))

    for i, (start_idx, task_num, task_name) in enumerate(header_positions):
        if i + 1 < len(header_positions):
            end_idx = header_positions[i + 1][0]
        else:
            end_idx = len(lines)

        task_lines = end_idx - start_idx
        status = "OK"

        if task_lines > TASK_LINE_LIMIT:
            status = "TOO_LARGE"
            warnings.append(
                "Task {} ({}) exceeds {}-line limit ({} lines)".format(
                    task_num, task_name, TASK_LINE_LIMIT, task_lines
                )
            )

        tasks.append(
            {
                "number": task_num,
                "name": task_name,
                "lines": task_lines,
                "status": status,
            }
        )

    return tasks, warnings, blockers


# -----------------------------------------------------------------------
# Section checks
# -----------------------------------------------------------------------


def check_sections(lines: List[str], full_content: str) -> Dict:
    """
    Check for the presence of all required plan sections.

    Returns a dict keyed by section name, each with at least {"present": bool}
    and optionally {"value": str} for sections where a value can be extracted.
    """
    area = header_area(lines)

    # Source Contracts
    sc_match = SOURCE_CONTRACTS_RE.search(area)
    sc_value = None
    if sc_match:
        rest = area[sc_match.end() :].split("\n", 1)[0].strip(" :*")
        sc_value = rest if rest else None
    sections: Dict = {
        "source_contracts": {
            "present": bool(sc_match),
        }
    }
    if sc_value is not None:
        sections["source_contracts"]["value"] = sc_value

    # Contract Constraints
    sections["contract_constraints"] = {
        "present": bool(CONTRACT_CONSTRAINTS_RE.search(area))
    }

    # Feature Archetype
    fa_match = FEATURE_ARCHETYPE_RE.search(area)
    fa_value = None
    if fa_match:
        rest = area[fa_match.end() :].split("\n", 1)[0].strip(" :*")
        fa_value = rest if rest else None
    sections["feature_archetype"] = {"present": bool(fa_match)}
    if fa_value is not None:
        sections["feature_archetype"]["value"] = fa_value

    # Code Footprint
    sections["code_footprint"] = {"present": bool(CODE_FOOTPRINT_RE.search(area))}

    # Write-Scope Partitioning (full document)
    sections["write_scope_partitioning"] = {
        "present": bool(WRITE_SCOPE_RE.search(full_content))
    }

    # Task 0 / Contract Verification
    task_zero_match = re.search(
        r"^###\s+Task\s+0\b", full_content, re.MULTILINE | re.IGNORECASE
    )
    task_zero_present = bool(task_zero_match)
    # Is task 0 the first task header that appears?
    first_task = TASK_HEADER_RE.search(full_content)
    is_first = False
    if task_zero_present and first_task:
        first_num = int(first_task.group(1))
        is_first = first_num == 0

    sections["task_0"] = {"present": task_zero_present, "is_first": is_first}

    # File Map
    sections["file_map"] = {"present": bool(FILE_MAP_RE.search(full_content))}

    return sections


# -----------------------------------------------------------------------
# Checkbox analysis
# -----------------------------------------------------------------------


def analyse_checkboxes(content: str) -> Dict:
    """Count checked/unchecked checkboxes and compute progress percentage."""
    checked = len(CHECKED_RE.findall(content))
    unchecked = len(UNCHECKED_RE.findall(content))
    total = checked + unchecked
    pct = round(100 * checked / total) if total > 0 else 0
    return {
        "unchecked": unchecked,
        "checked": checked,
        "total": total,
        "progress_pct": pct,
    }


# -----------------------------------------------------------------------
# Source Contracts "has real content" helper
# -----------------------------------------------------------------------


def source_contracts_non_none(content: str) -> bool:
    """
    Return True if the Source Contracts section contains substantive content
    (i.e., not just 'None', 'N/A', or blank).
    """
    match = SOURCE_CONTRACTS_RE.search(content)
    if not match:
        return False
    after = content[match.end() :]
    body_lines = [
        line.strip()
        for line in after.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not body_lines:
        return False
    first = body_lines[0].lower().strip("*: ")
    return first not in {"none", "n/a", "na", "-", "\u2014"}


# -----------------------------------------------------------------------
# Main validation logic
# -----------------------------------------------------------------------


def validate_plan(content: str) -> Dict:
    """
    Run all structural checks on plan content.

    Returns a dict matching the specified output schema with keys:
      status, plan_lines, task_count, tasks, checkboxes, sections,
      warnings, blockers.
    """
    lines = content.splitlines()
    plan_lines = len(lines)
    warnings: List[str] = []
    blockers: List[str] = []

    # --- Size: total plan length ---
    has_modules = bool(MODULE_HEADER_RE.search(content))
    if plan_lines > PLAN_LINE_LIMIT and not has_modules:
        blockers.append(
            "Plan exceeds {}-line limit ({} lines) without a 'Module' header "
            "indicating modular decomposition".format(PLAN_LINE_LIMIT, plan_lines)
        )

    # --- Task analysis ---
    tasks, task_warnings, task_blockers = analyse_tasks(lines)
    warnings.extend(task_warnings)
    blockers.extend(task_blockers)
    task_count = len(tasks)

    # --- Checkbox analysis ---
    checkboxes = analyse_checkboxes(content)

    # --- Section checks ---
    sections = check_sections(lines, content)

    # --- Cross-section rules ---

    # If Source Contracts is present and non-empty, Task 0 must exist
    sc_present = sections["source_contracts"]["present"]
    if sc_present and source_contracts_non_none(content):
        if not sections["task_0"]["present"]:
            blockers.append(
                "Source Contracts is present and non-empty but Task 0 "
                "(Contract Verification) is missing"
            )

    # Task 0 must be first if it exists
    if sections["task_0"]["present"] and not sections["task_0"]["is_first"]:
        blockers.append("Task 0 exists but is not the first task in the plan")

    # --- Overall status ---
    if blockers:
        status = "FAIL"
    elif warnings:
        status = "WARNING"
    else:
        status = "PASS"

    return {
        "status": status,
        "plan_lines": plan_lines,
        "task_count": task_count,
        "tasks": tasks,
        "checkboxes": checkboxes,
        "sections": sections,
        "warnings": warnings,
        "blockers": blockers,
    }


# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------


def main() -> int:
    """Parse arguments, run validation, emit JSON, and return exit code."""
    parser = argparse.ArgumentParser(
        description=(
            "Mechanically verify plan document structure before the "
            "plan-document-reviewer subagent is dispatched. "
            "Outputs JSON to stdout. "
            "Exit code 0=PASS, 1=FAIL (blockers), 2=WARNING, 3=script error."
        )
    )
    parser.add_argument(
        "--plan-file",
        required=True,
        metavar="PATH",
        help="Path to the implementation plan markdown file to validate.",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.plan_file):
        print(
            json.dumps({"error": "Plan file not found: {}".format(args.plan_file)}),
            file=sys.stderr,
        )
        return 3

    try:
        content = read_file(args.plan_file)
    except OSError as exc:
        print(
            json.dumps({"error": "Could not read plan file: {}".format(exc)}),
            file=sys.stderr,
        )
        return 3

    if not content.strip():
        print(
            json.dumps({"error": "Plan file is empty."}),
            file=sys.stderr,
        )
        return 3

    try:
        result = validate_plan(content)
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps({"error": "Unexpected error during validation: {}".format(exc)}),
            file=sys.stderr,
        )
        return 3

    print(json.dumps(result, indent=2))

    if result["status"] == "FAIL":
        return 1
    if result["status"] == "WARNING":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
