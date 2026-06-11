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
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Tuple

# Sibling scripts dir — importlib-loaded consumers (tests) don't put it on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_utils import _unfenced_content  # noqa: E402  (single source of truth)

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

# Matches a heading containing "Module" anywhere (signals modular decomposition)
MODULE_HEADER_RE = re.compile(r"^#{1,4}\s+.*\bModule\b", re.MULTILINE | re.IGNORECASE)

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

# File Map / File Structure / New Files / Modified Files section
FILE_MAP_RE = re.compile(
    r"^#{1,4}\s*(?:File\s+(?:Map|Structure)|New\s+Files?|Modified\s+Files?|Code\s+Footprint)",
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


def _frontmatter_end_line(lines: List[str]) -> int:
    """Return the index of the first line after YAML frontmatter, or 0 if none."""
    if not lines or lines[0].strip() != "---":
        return 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i + 1
    return 0


def header_area(lines: List[str]) -> str:
    """Return the first HEADER_AREA_LINES of plan body, skipping YAML frontmatter."""
    offset = _frontmatter_end_line(lines)
    return "\n".join(lines[offset : offset + HEADER_AREA_LINES])


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


def extract_task_numbers(content: str) -> List[int]:
    """Extract all task numbers from ### Task N headers in the given content."""
    return [int(m) for m in TASK_HEADER_RE.findall(_unfenced_content(content))]


def analyse_tasks(lines: List[str]) -> Tuple[List[Dict], List[str], List[str]]:
    """
    Walk the line list, find every ### Task N header, and measure the line span
    for each task section.

    Returns:
        tasks     - list of dicts with keys: number, name, lines, status
        warnings  - human-readable warning strings
        blockers  - human-readable blocker strings
    """
    tasks: List[Dict] = []
    warnings: List[str] = []
    blockers: List[str] = []

    # Unfence: replace fenced lines with blanks to skip code-block task headers.
    # Line count is preserved so span indices remain valid.
    unfenced_lines = _unfenced_content("\n".join(lines)).splitlines()

    # Collect (line_index, task_number, task_name) for all task headers
    header_positions: List[Tuple[int, int, str]] = []
    for idx, line in enumerate(unfenced_lines):
        m = re.match(r"^###\s+Task\s+(\d+)\s*(.*)", line, re.IGNORECASE)
        if m:
            task_num = int(m.group(1))
            task_name = m.group(2).lstrip(":- ").strip() or f"Task {task_num}"
            header_positions.append((idx, task_num, task_name))

    # Check for duplicate task numbers within this file
    seen: Dict[int, int] = {}
    for _, task_num, _ in header_positions:
        seen[task_num] = seen.get(task_num, 0) + 1
    duplicates = {num: count for num, count in seen.items() if count > 1}
    if duplicates:
        dup_details = ", ".join(
            "Task {} appears {} times".format(num, count)
            for num, count in sorted(duplicates.items())
        )
        blockers.append(
            "Duplicate task numbers: {} — task numbers must be sequential "
            "and unique; duplicates cause report files to overwrite each other".format(
                dup_details
            )
        )

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

    # Task 0 / Contract Verification — use unfenced content to ignore code blocks
    unfenced_full = _unfenced_content(full_content)
    task_zero_match = re.search(
        r"^###\s+Task\s+0\b", unfenced_full, re.MULTILINE | re.IGNORECASE
    )
    task_zero_present = bool(task_zero_match)
    # Is task 0 the first task header that appears?
    first_task = TASK_HEADER_RE.search(unfenced_full)
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
# review_tier heuristic (Item 4c)
# -----------------------------------------------------------------------

# Titles matching these always warrant a full review.
_ALWAYS_FULL_KEYWORDS = ("refactor", "service", "security", "business logic", "auth")
# "migration" only warrants full review when paired with data-manipulation terms.
_MIGRATION_DATA_KEYWORDS = ("backfill", "update", "delete", "transform", "data")


def check_review_tier_heuristic(frontmatter: Optional[Dict]) -> List[str]:
    """Return warning strings for tasks declaring review_tier=minimum on high-risk titles."""
    warnings: List[str] = []
    if not isinstance(frontmatter, dict):
        return warnings
    tasks = frontmatter.get("tasks")
    if not isinstance(tasks, list):
        return warnings
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("review_tier") != "minimum":
            continue
        title = str(task.get("title", "")).lower()
        tid = task.get("id")
        suspicious = any(kw in title for kw in _ALWAYS_FULL_KEYWORDS)
        if not suspicious and "migration" in title:
            suspicious = any(kw in title for kw in _MIGRATION_DATA_KEYWORDS)
        if suspicious:
            warnings.append(
                "review_tier_minimum_on_high_risk_task: Task {} ('{}') declares "
                "review_tier: minimum but its title suggests full review is warranted. "
                "Confirm this is genuinely mechanical.".format(tid, task.get("title", ""))
            )
    return warnings


# -----------------------------------------------------------------------
# verification keyword heuristic
# -----------------------------------------------------------------------

_VERIFICATION_WRITE_KEYWORDS = (
    "create", "add", "implement", "fix", "modify",
    "write", "update", "refactor", "migrate", "delete", "remove",
)

_VERIFICATION_KEYWORD_RE = re.compile(
    r"\b(?:{})\b".format("|".join(_VERIFICATION_WRITE_KEYWORDS)),
    re.IGNORECASE,
)


def check_verification_keyword_heuristic(frontmatter: Optional[Dict]) -> List[str]:
    """Return warning strings for verification tasks whose titles contain write-suggesting keywords."""
    warnings: List[str] = []
    if not isinstance(frontmatter, dict):
        return warnings
    tasks = frontmatter.get("tasks")
    if not isinstance(tasks, list):
        return warnings
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("task_type") != "verification":
            continue
        title = str(task.get("title", ""))
        tid = task.get("id")
        matched = _VERIFICATION_KEYWORD_RE.findall(title)
        if matched:
            warnings.append(
                "verification_keyword_warning: Task {} ('{}') is task_type: verification "
                "but its title contains write-suggesting keyword(s): {}. "
                "Verification tasks must not modify files. "
                "If this task modifies files, change it to task_type: implementation.".format(
                    tid, task.get("title", ""), ", ".join(matched)
                )
            )
    return warnings


# -----------------------------------------------------------------------
# integration-test risk-surface heuristic (C2)
# -----------------------------------------------------------------------

_C2_RISK_PATTERNS = re.compile(
    r"\b(?:router|routes/|middleware|auth|migration|cache|cors|security)\b",
    re.IGNORECASE,
)


def check_integration_test_risk(content: str, frontmatter: Optional[Dict]) -> List[str]:
    """Warn when plan content matches risk-surface patterns but has no integration_test."""
    warnings: List[str] = []
    has_integration_test = (
        isinstance(frontmatter, dict)
        and frontmatter.get("integration_test") is not None
    )
    if has_integration_test:
        return warnings
    if _C2_RISK_PATTERNS.search(content):
        warnings.append(
            "integration_test_risk_surface: Plan content matches risk-surface patterns "
            "(router/middleware/auth/migration/cache/cors/security) but no "
            "integration_test is declared in frontmatter. Consider adding "
            "integration_test: {path: 'tests/integration/...'} to declare the "
            "integration test that validates this feature."
        )
    return warnings


# -----------------------------------------------------------------------
# Main validation logic
# -----------------------------------------------------------------------


def check_cross_module_collisions(
    primary_content: str, additional_contents: List[str]
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Check for task number collisions across the primary plan file and
    additional module files.

    Returns:
        (check_dict, blocker_name) — check_dict is the check entry for the
        output JSON; blocker_name is non-None if this is a blocker.
        Returns (None, None) if no additional files were provided.
    """
    if not additional_contents:
        return None, None

    primary_tasks = set(extract_task_numbers(primary_content))
    all_tasks: Dict[int, List[str]] = {}
    for num in primary_tasks:
        all_tasks.setdefault(num, []).append("primary plan")

    for i, content in enumerate(additional_contents, 1):
        for num in extract_task_numbers(content):
            all_tasks.setdefault(num, []).append("additional file {}".format(i))

    collisions = {
        num: sources for num, sources in all_tasks.items() if len(sources) > 1
    }

    if not collisions:
        return {
            "status": "PASS",
            "detail": "No task number collisions across {} file(s)".format(
                1 + len(additional_contents)
            ),
        }, None

    collision_details = ", ".join(
        "Task {} in {}".format(num, " and ".join(sources))
        for num, sources in sorted(collisions.items())
    )
    return {
        "status": "FAIL",
        "detail": (
            "Cross-module task number collision: {} — task numbers must be "
            "sequential across all modules; duplicates cause report files to "
            "overwrite each other".format(collision_details)
        ),
    }, "cross_module_task_collision"


def validate_plan(
    content: str, additional_contents: Optional[List[str]] = None
) -> Dict:
    """
    Run all structural checks on plan content.

    Args:
        content: The primary plan file content.
        additional_contents: Optional list of additional module plan file contents
            to check for cross-module task number collisions.

    Returns a dict matching the specified output schema with keys:
      status, plan_lines, task_count, tasks, checkboxes, sections,
      warnings, blockers.
    """
    lines = content.splitlines()
    has_frontmatter = content.startswith("---")
    plan_lines = len(lines)
    warnings: List[str] = []
    blockers: List[str] = []

    # Parse YAML frontmatter into dict for in-process checks (enforcement_tier, modules)
    frontmatter: Optional[Dict] = None
    if has_frontmatter:
        end_idx = content.find("---", 3)
        if end_idx != -1:
            try:
                import yaml

                frontmatter = yaml.safe_load(content[3:end_idx])
            except Exception:
                frontmatter = None

    # --- Size: total plan length ---
    has_modules = bool(MODULE_HEADER_RE.search(content))
    if plan_lines > PLAN_LINE_LIMIT and not has_modules:
        blockers.append(
            "Plan exceeds {}-line limit ({} lines) without a 'Module' header "
            "indicating modular decomposition".format(PLAN_LINE_LIMIT, plan_lines)
        )

    # --- Task analysis (includes within-file duplicate detection) ---
    tasks, task_warnings, task_blockers = analyse_tasks(lines)
    warnings.extend(task_warnings)
    blockers.extend(task_blockers)
    task_count = len(tasks)

    # --- Checkbox analysis ---
    checkboxes = analyse_checkboxes(content)

    # --- Section checks ---
    sections = check_sections(lines, content)

    # --- Cross-section rules ---

    # If File Map is absent, emit a warning (not a blocker)
    if not sections["file_map"]["present"]:
        warnings.append(
            "No File Map / File Structure / Code Footprint section found — recommended for plan clarity"
        )

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

    # --- Cross-module collision check ---
    if additional_contents:
        cross_check, cross_blocker = check_cross_module_collisions(
            content, additional_contents
        )
        if cross_check is not None:
            sections["cross_module_task_collision"] = cross_check
            if cross_blocker:
                blockers.append(cross_blocker)

    # --- Within-file duplicate check (surface in checks dict) ---
    task_numbers = [t["number"] for t in tasks]
    seen_counts: Dict[int, int] = {}
    for num in task_numbers:
        seen_counts[num] = seen_counts.get(num, 0) + 1
    duplicates = {num: count for num, count in seen_counts.items() if count > 1}
    if duplicates:
        dup_details = ", ".join(
            "Task {} appears {} times".format(num, count)
            for num, count in sorted(duplicates.items())
        )
        sections["duplicate_task_numbers"] = {
            "status": "FAIL",
            "detail": (
                "Duplicate task numbers: {} — task numbers must be sequential "
                "and unique; duplicates cause report files to overwrite each other".format(
                    dup_details
                )
            ),
        }
        if "duplicate_task_numbers" not in blockers:
            blockers.append("duplicate_task_numbers")
    else:
        sections["duplicate_task_numbers"] = {
            "status": "PASS",
            "detail": "All task numbers are unique",
        }

    # --- Pydantic validation (Phase 1) ---
    if has_frontmatter:
        validators_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "scripts",
            "models",
            "validators.py",
        )
        if os.path.isfile(validators_path):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                pydantic_result = subprocess.run(
                    [sys.executable, validators_path, "plan", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if pydantic_result.returncode == 1:
                    blockers.append(
                        f"Pydantic validation failed:\n{pydantic_result.stderr.strip()}"
                    )
            finally:
                os.unlink(tmp_path)
    else:
        warnings.append(
            "No YAML frontmatter detected. Post-Phase 1 plans should include "
            "frontmatter with schema_version, feature_archetype, and tasks fields."
        )

    # --- Enforcement tier appropriateness ---
    # Valid tier values match sdd_session.Tier (Literal["micro", "standard"]).
    if frontmatter and isinstance(frontmatter, dict):
        tier = frontmatter.get("enforcement_tier")
        if tier is not None:
            if tier not in ("micro", "standard"):
                blockers.append("enforcement_tier_invalid")
                sections["enforcement_tier_invalid"] = {
                    "status": "FAIL",
                    "detail": (
                        "enforcement_tier '{}' is not valid. "
                        "Must be 'micro' or 'standard'.".format(tier)
                    ),
                }
            elif tier == "micro" and task_count > 3:
                warnings.append("enforcement_tier_appropriateness")
                sections["enforcement_tier_appropriateness"] = {
                    "status": "WARNING",
                    "detail": (
                        "enforcement_tier is 'micro' but plan has {} tasks. "
                        "Micro tier is designed for 1-2 tasks. "
                        "Consider 'standard' for better enforcement.".format(task_count)
                    ),
                }

            modules = frontmatter.get("modules")
            if modules and tier == "micro":
                warnings.append("micro_with_modules")
                sections["micro_with_modules"] = {
                    "status": "WARNING",
                    "detail": (
                        "enforcement_tier is 'micro' but plan has modules. "
                        "Multi-module plans typically need standard enforcement."
                    ),
                }

    # --- review_tier heuristic (Item 4c) ---
    rt_warnings = check_review_tier_heuristic(frontmatter)
    for w in rt_warnings:
        warnings.append(w)
    if rt_warnings:
        sections["review_tier_heuristic"] = {
            "status": "WARNING",
            "detail": " | ".join(rt_warnings),
        }

    # --- verification keyword heuristic ---
    vk_warnings = check_verification_keyword_heuristic(frontmatter)
    for w in vk_warnings:
        warnings.append(w)
    if vk_warnings:
        sections["verification_keyword_heuristic"] = {
            "status": "WARNING",
            "detail": " | ".join(vk_warnings),
        }

    # --- integration-test risk-surface heuristic (C2) ---
    it_warnings = check_integration_test_risk(content, frontmatter)
    for w in it_warnings:
        warnings.append(w)
    if it_warnings:
        sections["integration_test_risk"] = {
            "status": "WARNING",
            "detail": " | ".join(it_warnings),
        }

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
    parser.add_argument(
        "--additional-plan-files",
        nargs="+",
        metavar="PATH",
        default=None,
        help=(
            "Additional module plan files to check for cross-module task number "
            "collisions. Task numbers must be unique across all files."
        ),
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

    # Read additional module files if provided
    additional_contents: Optional[List[str]] = None
    if args.additional_plan_files:
        additional_contents = []
        for path in args.additional_plan_files:
            if not os.path.isfile(path):
                print(
                    json.dumps(
                        {"error": "Additional plan file not found: {}".format(path)}
                    ),
                    file=sys.stderr,
                )
                return 3
            try:
                additional_contents.append(read_file(path))
            except OSError as exc:
                print(
                    json.dumps(
                        {"error": "Could not read additional plan file: {}".format(exc)}
                    ),
                    file=sys.stderr,
                )
                return 3

    try:
        result = validate_plan(content, additional_contents)
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
