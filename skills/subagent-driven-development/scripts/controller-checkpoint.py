#!/usr/bin/env python3
"""
controller-checkpoint.py

Verifies controller discipline at key checkpoints during subagent-driven-development.
Replaces self-assessment with deterministic mechanical verification.

Exit codes:
  0 - PASS (all checks passed)
  1 - FAIL (one or more blocking checks failed)
  2 - WARNING (all checks passed but warnings were raised)
  3 - Script error (bad arguments, file not found, etc.)

Usage:
  python scripts/controller-checkpoint.py \\
    --phase pre-execution \\
    --plan-file docs/plans/feature-plan.md \\
    --deviations-file DEVIATIONS.md \\
    --reports-dir reports/

  python scripts/controller-checkpoint.py \\
    --phase pre-dispatch \\
    --task-number 3 \\
    --plan-file docs/plans/feature-plan.md \\
    --deviations-file DEVIATIONS.md \\
    --reports-dir reports/

  python scripts/controller-checkpoint.py \\
    --phase pre-completion \\
    --plan-file docs/plans/feature-plan.md \\
    --deviations-file DEVIATIONS.md \\
    --reports-dir reports/
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))
from _base import CURRENT_SCHEMA_VERSION
from checkpoint_result import CheckpointResult, CheckResult, Progress
from sdd_session import SddSession

# Character-to-token approximation (standard industry estimate: 1 token = 4 chars)
CHARS_PER_TOKEN = 4

# Context load threshold above which the controller should compress execution state.
# 400KB of accumulated files is roughly 100K tokens.
CONTEXT_LOAD_WARNING_BYTES = 400 * 1024  # 400KB

# Pattern for task headers: "### Task N" or "### Task N:" with optional title
TASK_HEADER_PATTERN = re.compile(r"^###\s+Task\s+(\d+)", re.MULTILINE | re.IGNORECASE)

# Pattern for unchecked checkboxes
UNCHECKED_PATTERN = re.compile(r"^\s*-\s+\[ \]", re.MULTILINE)

# Pattern for checked checkboxes
CHECKED_PATTERN = re.compile(r"^\s*-\s+\[x\]", re.MULTILINE | re.IGNORECASE)

# Pattern for "Source Contracts" — matches ATX headers and bold markdown variants
SOURCE_CONTRACTS_PATTERN = re.compile(
    r"(?:^#+\s*Source\s+Contracts?\s*:?\s*$|\*\*Source\s+Contracts?:?\*\*\s*:?|\*\*Source\s+Contracts?\*\*\s*:?)",
    re.MULTILINE | re.IGNORECASE,
)

# Pattern for pending entries in DEVIATIONS.md
# Matches rows in a markdown table where the last non-whitespace cell is "Pending"
PENDING_DEVIATION_PATTERN = re.compile(
    r"\|\s*Pending\s*\|?\s*$", re.MULTILINE | re.IGNORECASE
)


# Report filename patterns for task N
def report_filename_pattern(task_number: int) -> str:
    """Return a glob pattern matching implementer report files for the given task.

    Uses zero-padded 3-digit format (task-007-*) exclusively. Non-padded names
    (task-7-*) are not matched — they indicate stale reports from a prior session
    that used an older naming convention.
    """
    return "task-{:03d}-implementer-report*".format(task_number)


# --- Utility functions ---


def read_file(path: str) -> str:
    """Read a file and return its contents. Raises OSError on failure."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def file_size_bytes(path: str) -> int:
    """Return the size of a file in bytes."""
    return os.path.getsize(path)


def count_tasks(plan_content: str) -> int:
    """Count the number of task headers in the plan (### Task N patterns)."""
    return len(TASK_HEADER_PATTERN.findall(plan_content))


def count_checkboxes(plan_content: str) -> dict:
    """Return counts of checked and unchecked checkboxes in the plan."""
    checked = len(CHECKED_PATTERN.findall(plan_content))
    unchecked = len(UNCHECKED_PATTERN.findall(plan_content))
    return {"checked": checked, "unchecked": unchecked, "total": checked + unchecked}


def count_pending_deviations(deviations_content: str) -> int:
    """Count entries in DEVIATIONS.md with 'Pending' disposition."""
    return len(PENDING_DEVIATION_PATTERN.findall(deviations_content))


def find_report_file(reports_dir: str, task_number: int) -> str:
    """
    Return the path to the implementer report for the given task, or "" if not found.
    Searches for files matching task-N-implementer-report*.
    """
    pattern = os.path.join(reports_dir, report_filename_pattern(task_number))
    matches = glob.glob(pattern)
    return sorted(matches)[-1] if matches else ""


def detect_stale_artifacts(deviations_file: str, reports_dir: str) -> dict:
    """
    Check for SDD artifacts from a prior session that exist before execution starts.

    At pre-execution time, DEVIATIONS.md should not have content and reports/
    should not contain task reports or audit files — their presence indicates
    a prior SDD session's artifacts that need archival.

    Returns:
        dict with keys: status ("OK" or "WARNING"), detail (str), found (list of str)
    """
    found = []

    # Check DEVIATIONS.md for substantive content
    if os.path.isfile(deviations_file):
        try:
            content = read_file(deviations_file)
            # Only flag if it has real content (not empty or just whitespace)
            if content.strip():
                found.append("DEVIATIONS.md (has content from prior session)")
        except OSError:
            pass

    # Check reports/ for task report files
    if os.path.isdir(reports_dir):
        task_reports = sorted(glob.glob(os.path.join(reports_dir, "task-*")))
        if task_reports:
            found.append(
                "{} task report file(s) in {}".format(len(task_reports), reports_dir)
            )

        audit_files = sorted(glob.glob(os.path.join(reports_dir, "pre-execution-audit*")))
        if audit_files:
            found.append(
                "{} pre-execution audit file(s) in {}".format(len(audit_files), reports_dir)
            )

    if not found:
        return {"status": "OK", "detail": "No stale artifacts detected", "found": []}

    return {
        "status": "WARNING",
        "detail": (
            "Stale SDD artifacts from a prior session detected: {}. "
            "Archive these before proceeding (see Plan Ingestion archival protocol). "
            "Log as FYI in pre-execution audit report".format("; ".join(found))
        ),
        "found": found,
    }


def find_all_report_files(reports_dir: str) -> list:
    """Return all report files in the reports directory (any task)."""
    pattern = os.path.join(reports_dir, "task-*-implementer-report*")
    return sorted(glob.glob(pattern))


def _count_review_tiers(reports_dir, review_type):
    # type: (str, str) -> tuple
    """Count total and minimum-tier reviews of a given type in reports/.

    Args:
        reports_dir: Path to the reports directory.
        review_type: Either "quality-review" or "partner-review".

    Returns:
        (total_count, minimum_tier_count)
    """
    if review_type == "quality-review":
        full_pattern = os.path.join(reports_dir, "task-*-quality-review.md")
        min_pattern = os.path.join(reports_dir, "task-*-quality-review-minimum-tier.md")
    elif review_type == "partner-review":
        full_pattern = os.path.join(reports_dir, "partner-review-*.md")
        min_pattern = os.path.join(reports_dir, "partner-review-*-minimum-tier.md")
    else:
        return (0, 0)

    full_files = set(glob.glob(full_pattern))
    min_files = set(glob.glob(min_pattern))
    # Minimum-tier files also match the broader glob, so subtract them
    full_only = full_files - min_files
    return (len(full_only) + len(min_files), len(min_files))


def validate_report_sections(report_content: str) -> dict:
    """
    Validate that a report has the 5 required prose sections.
    Returns {"complete": bool, "sections_found": int, "sections_total": int}.
    """
    required_patterns = [
        (r"implementation\s+summary", "Implementation Summary"),
        (r"source\s+files?\s+read", "Source Files Read"),
        (r"deviations?\s+from\s+plan", "Deviations from Plan"),
        (r"self[\-\s]review\s+findings?", "Self-Review Findings"),
        (r"concerns?", "Concerns"),
    ]

    header_pattern = re.compile(r"(?:\*\*([^*]+)\*\*|^#{1,4}\s+(.+))", re.MULTILINE)
    headers = []
    for match in header_pattern.finditer(report_content):
        text = match.group(1) or match.group(2)
        if text:
            headers.append(text.strip())

    found_count = 0
    for pattern_str, _ in required_patterns:
        compiled = re.compile(pattern_str, re.IGNORECASE)
        if any(compiled.search(h) for h in headers):
            found_count += 1

    total = len(required_patterns)
    return {
        "complete": found_count == total,
        "sections_found": found_count,
        "sections_total": total,
    }


def estimate_context_load(
    plan_file: str, deviations_file: str, reports_dir: str
) -> dict:
    """
    Estimate the accumulated context load by summing file sizes.
    Returns dict with total_bytes, total_tokens, and contributing files.
    """
    files_measured = {}
    total_bytes = 0

    for path in [plan_file, deviations_file]:
        if os.path.isfile(path):
            size = file_size_bytes(path)
            files_measured[path] = size
            total_bytes += size

    for report_path in find_all_report_files(reports_dir):
        if os.path.isfile(report_path):
            size = file_size_bytes(report_path)
            files_measured[report_path] = size
            total_bytes += size

    approx_tokens = total_bytes // CHARS_PER_TOKEN

    return {
        "total_bytes": total_bytes,
        "total_kb": round(total_bytes / 1024, 1),
        "approx_tokens": approx_tokens,
        "file_count": len(files_measured),
    }


def has_task_zero(plan_content: str) -> bool:
    """Return True if the plan contains a Task 0 header."""
    return bool(
        re.search(r"^###\s+Task\s+0\b", plan_content, re.MULTILINE | re.IGNORECASE)
    )


def task_zero_is_first(plan_content: str) -> bool:
    """Return True if Task 0 appears before any other task in the plan."""
    tasks = TASK_HEADER_PATTERN.findall(plan_content)
    return bool(tasks and tasks[0] == "0")


def source_contracts_present(plan_content: str) -> bool:
    """Return True if the plan has a 'Source Contracts:' section."""
    return bool(SOURCE_CONTRACTS_PATTERN.search(plan_content))


def source_contracts_non_empty(plan_content: str) -> bool:
    """
    Return True if the Source Contracts section contains at least one non-trivial
    line after the header (i.e., not just 'None' or empty).
    """
    match = SOURCE_CONTRACTS_PATTERN.search(plan_content)
    if not match:
        return False

    # Extract text after the header until the next header or end-of-file
    after = plan_content[match.end() :]
    # Get the first non-blank, non-separator lines
    body_lines = [
        line.strip()
        for line in after.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not body_lines:
        return False
    first_line = body_lines[0].lower()
    # "None" or "N/A" means no contracts listed
    return first_line not in {"none", "n/a", "na", "-", "—"}


def get_task_checkbox_range(plan_content: str, task_number: int) -> dict:
    """
    Extract checkbox counts for a specific task section.
    Returns {"checked": N, "unchecked": N, "total": N}.
    """
    # Find the start of the target task section
    task_match = re.search(
        rf"^###\s+Task\s+{task_number}\b",
        plan_content,
        re.MULTILINE | re.IGNORECASE,
    )
    if not task_match:
        return {"checked": 0, "unchecked": 0, "total": 0}

    start = task_match.start()

    # Find the start of the NEXT task section (or end of file)
    next_task_match = re.search(
        r"^###\s+Task\s+\d+\b",
        plan_content[task_match.end() :],
        re.MULTILINE | re.IGNORECASE,
    )
    if next_task_match:
        end = task_match.end() + next_task_match.start()
    else:
        end = len(plan_content)

    section = plan_content[start:end]
    checked = len(CHECKED_PATTERN.findall(section))
    unchecked = len(UNCHECKED_PATTERN.findall(section))
    return {"checked": checked, "unchecked": unchecked, "total": checked + unchecked}


def all_tasks_have_reports(plan_content: str, reports_dir: str) -> dict:
    """
    Check whether every task in the plan has a corresponding report file.
    Returns {"pass": bool, "missing": list_of_task_numbers}.
    """
    task_numbers = [int(n) for n in TASK_HEADER_PATTERN.findall(plan_content)]
    missing = []
    for n in task_numbers:
        if not find_report_file(reports_dir, n):
            missing.append(n)
    return {"pass": not missing, "missing": missing}


# --- Manifest loader ---


def _resolve_git_root(manifest_path: Path) -> str:
    """Resolve git root from manifest path via `git rev-parse`.

    Prefers `git -C <manifest_parent> rev-parse --show-toplevel` (matches
    transition-module.py:115-123). Falls back to `parent.parent.parent` with a
    stderr warning when git is unavailable or the path is outside a repo.
    """
    git_result = subprocess.run(
        ["git", "-C", str(manifest_path.parent), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if git_result.returncode == 0:
        return git_result.stdout.strip()

    fallback = str(manifest_path.resolve().parent.parent.parent)
    print(
        json.dumps({
            "warning": (
                f"git rev-parse failed for {manifest_path}; "
                f"falling back to parent.parent.parent ({fallback})"
            )
        }),
        file=sys.stderr,
    )
    return fallback


def _load_manifest_config(args: argparse.Namespace) -> Tuple[Optional[str], Optional[dict]]:
    """Load and validate the SDD session manifest when --manifest is provided.

    Side effects:
      - Mutates args.plan_file in place. Prefers active_module_file over plan_file.
      - On unrecoverable error (missing file, invalid JSON, schema validation
        failure), prints a JSON error to stderr and calls sys.exit(3).

    Returns:
      (tier, enforcement_dict) when args.manifest is set, otherwise (None, None).
    """
    if not args.manifest:
        return None, None

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(
            json.dumps({"error": f"Manifest not found: {args.manifest}"}),
            file=sys.stderr,
        )
        sys.exit(3)

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(
            json.dumps({"error": f"Cannot parse manifest {args.manifest}: {exc}"}),
            file=sys.stderr,
        )
        sys.exit(3)

    try:
        manifest = SddSession.model_validate(manifest_data)
    except Exception as exc:  # pydantic.ValidationError or otherwise
        print(
            json.dumps({"error": f"Manifest failed validation: {exc}"}),
            file=sys.stderr,
        )
        sys.exit(3)

    git_root = _resolve_git_root(manifest_path)

    # Prefer active_module_file when set; otherwise use plan_file.
    if manifest.active_module_file:
        args.plan_file = os.path.join(git_root, manifest.active_module_file)
    else:
        args.plan_file = os.path.join(git_root, manifest.plan_file)

    return manifest.tier, manifest.enforcement.model_dump()


# --- Phase handlers ---


def run_pre_execution(args: argparse.Namespace) -> dict:
    """
    Phase: pre-execution
    Checks that all structural prerequisites exist before any task is dispatched.
    """
    _load_manifest_config(args)

    checks = {}
    blockers = []
    warnings = []

    # Check 1: Plan file exists and is readable
    if not os.path.isfile(args.plan_file):
        status = "FAIL"
        detail = f"Plan file not found: {args.plan_file}"
        blockers.append("plan_file")
        checks["plan_file"] = {"status": "FAIL", "detail": detail}
        # Cannot continue without plan
        return _build_result(
            "pre-execution", None, "FAIL", checks, warnings, blockers, None
        )

    try:
        plan_content = read_file(args.plan_file)
        checks["plan_file"] = {
            "status": "PASS",
            "detail": f"{args.plan_file} readable ({len(plan_content)} chars)",
        }
    except OSError as e:
        checks["plan_file"] = {
            "status": "FAIL",
            "detail": f"Cannot read plan file: {e}",
        }
        blockers.append("plan_file")
        return _build_result(
            "pre-execution", None, "FAIL", checks, warnings, blockers, None
        )

    # Check 2: DEVIATIONS.md exists (optional for pre-execution)
    if args.deviations_file is None:
        checks["deviations_file"] = {
            "status": "SKIP",
            "detail": "Not provided — will be created during execution",
        }
    elif os.path.isfile(args.deviations_file):
        checks["deviations_file"] = {
            "status": "PASS",
            "detail": f"{args.deviations_file} exists",
        }
    else:
        checks["deviations_file"] = {
            "status": "FAIL",
            "detail": f"DEVIATIONS.md not found at: {args.deviations_file}",
        }
        blockers.append("deviations_file")

    # Check 3: reports/ directory exists (optional for pre-execution)
    if args.reports_dir is None:
        checks["reports_dir"] = {
            "status": "SKIP",
            "detail": "Not provided — will be created during execution",
        }
    elif os.path.isdir(args.reports_dir):
        checks["reports_dir"] = {
            "status": "PASS",
            "detail": f"{args.reports_dir} exists",
        }
    else:
        checks["reports_dir"] = {
            "status": "FAIL",
            "detail": f"Reports directory not found: {args.reports_dir}",
        }
        blockers.append("reports_dir")

    # Check 4: Source Contracts verification (if section present)
    if source_contracts_present(plan_content):
        if source_contracts_non_empty(plan_content):
            checks["source_contracts"] = {
                "status": "PASS",
                "detail": "Source Contracts section present and non-empty",
            }
        else:
            checks["source_contracts"] = {
                "status": "FAIL",
                "detail": "Source Contracts section present but contains 'None' or is empty — update or remove the section",
            }
            blockers.append("source_contracts")
    else:
        checks["source_contracts"] = {
            "status": "OK",
            "detail": "No Source Contracts section — Task 0 not required",
        }

    # Check 5: Task 0 ordering (if Task 0 exists)
    if has_task_zero(plan_content):
        if task_zero_is_first(plan_content):
            checks["task_zero_ordering"] = {
                "status": "PASS",
                "detail": "Task 0 is first in task list",
            }
        else:
            checks["task_zero_ordering"] = {
                "status": "FAIL",
                "detail": "Task 0 found but is NOT the first task — reorder the plan",
            }
            blockers.append("task_zero_ordering")
    else:
        checks["task_zero_ordering"] = {
            "status": "OK",
            "detail": "No Task 0 in plan",
        }

    # Check 6: Stale artifacts from prior SDD session
    dev_path = args.deviations_file if args.deviations_file else ""
    rep_dir = args.reports_dir if args.reports_dir else ""
    if dev_path or rep_dir:
        stale = detect_stale_artifacts(dev_path, rep_dir)
        checks["stale_artifacts"] = {
            "status": stale["status"],
            "detail": stale["detail"],
        }
        if stale["status"] == "WARNING":
            warnings.append(stale["detail"])

    # Informational: task and checkbox counts
    task_count = count_tasks(plan_content)
    checkbox_counts = count_checkboxes(plan_content)

    progress = {
        "tasks_total": task_count,
        "checkboxes_total": checkbox_counts["total"],
        "checkboxes_checked": checkbox_counts["checked"],
        "checkboxes_unchecked": checkbox_counts["unchecked"],
    }

    overall = "FAIL" if blockers else "PASS"
    return _build_result(
        "pre-execution", None, overall, checks, warnings, blockers, progress
    )


def run_pre_dispatch(args: argparse.Namespace) -> dict:
    """
    Phase: pre-dispatch
    Checks before dispatching task N that the previous task is fully complete.
    """
    _load_manifest_config(args)

    if args.task_number is None:
        print(
            json.dumps({"error": "--task-number is required for phase pre-dispatch"}),
            file=sys.stderr,
        )
        sys.exit(3)

    if args.deviations_file is None:
        print(
            json.dumps(
                {"error": "--deviations-file is required for phase pre-dispatch"}
            ),
            file=sys.stderr,
        )
        sys.exit(3)

    if args.reports_dir is None:
        print(
            json.dumps({"error": "--reports-dir is required for phase pre-dispatch"}),
            file=sys.stderr,
        )
        sys.exit(3)

    task_number = args.task_number
    checks = {}
    blockers = []
    warnings = []

    # Read plan file
    if not os.path.isfile(args.plan_file):
        print(
            json.dumps({"error": f"Plan file not found: {args.plan_file}"}),
            file=sys.stderr,
        )
        sys.exit(3)
    try:
        plan_content = read_file(args.plan_file)
    except OSError as e:
        print(json.dumps({"error": f"Cannot read plan file: {e}"}), file=sys.stderr)
        sys.exit(3)

    # Read deviations file
    deviations_content = ""
    if os.path.isfile(args.deviations_file):
        try:
            deviations_content = read_file(args.deviations_file)
        except OSError:
            pass

    # Checkbox progress across entire plan
    checkbox_counts = count_checkboxes(plan_content)
    task_count = count_tasks(plan_content)
    pct = (
        round(100 * checkbox_counts["checked"] / checkbox_counts["total"])
        if checkbox_counts["total"] > 0
        else 0
    )

    previous_task = task_number - 1

    # Check 1: Previous task checkboxes (only if task > 0)
    if task_number > 0:
        prev_cbs = get_task_checkbox_range(plan_content, previous_task)
        if prev_cbs["total"] == 0:
            # Task exists but has no checkboxes — treat as OK (some tasks may not have them)
            checks["previous_task_checkboxes"] = {
                "status": "OK",
                "detail": f"Task {previous_task}: no checkboxes found in task section",
            }
        elif prev_cbs["unchecked"] == 0:
            checks["previous_task_checkboxes"] = {
                "status": "PASS",
                "detail": f"Task {previous_task}: {prev_cbs['checked']}/{prev_cbs['total']} checked",
            }
        else:
            checks["previous_task_checkboxes"] = {
                "status": "FAIL",
                "detail": (
                    f"Task {previous_task}: {prev_cbs['checked']}/{prev_cbs['total']} checked — "
                    f"{prev_cbs['unchecked']} unchecked checkbox(es) remain"
                ),
            }
            blockers.append("previous_task_checkboxes")
    else:
        checks["previous_task_checkboxes"] = {
            "status": "OK",
            "detail": "First task (task 0) — no previous task to verify",
        }

    # Check 2: Previous task report file exists (only if task > 0)
    if task_number > 0:
        report_path = find_report_file(args.reports_dir, previous_task)
        if report_path:
            checks["previous_task_report"] = {
                "status": "PASS",
                "detail": f"{report_path} exists",
            }
        else:
            checks["previous_task_report"] = {
                "status": "FAIL",
                "detail": (
                    f"No implementer report found for Task {previous_task} in {args.reports_dir}. "
                    f"Expected a file matching: {report_filename_pattern(previous_task)}"
                ),
            }
            blockers.append("previous_task_report")
            report_path = ""
    else:
        checks["previous_task_report"] = {
            "status": "OK",
            "detail": "First task — no previous report to verify",
        }
        report_path = ""

    # Check 3: Previous task report is COMPLETE (inline validate-report logic)
    if task_number > 0 and report_path:
        try:
            report_content = read_file(report_path)
            validation = validate_report_sections(report_content)
            if validation["complete"]:
                checks["previous_report_complete"] = {
                    "status": "PASS",
                    "detail": f"{validation['sections_found']}/{validation['sections_total']} sections present",
                }
            else:
                checks["previous_report_complete"] = {
                    "status": "FAIL",
                    "detail": (
                        f"Report incomplete: {validation['sections_found']}/{validation['sections_total']} sections present — "
                        "re-dispatch implementer to complete missing sections"
                    ),
                }
                blockers.append("previous_report_complete")
        except OSError as e:
            checks["previous_report_complete"] = {
                "status": "FAIL",
                "detail": f"Could not read report file: {e}",
            }
            blockers.append("previous_report_complete")
    elif task_number > 0 and not report_path:
        # Already flagged as missing — skip validation
        checks["previous_report_complete"] = {
            "status": "SKIP",
            "detail": "Skipped — report file not found (see previous_task_report check)",
        }
    else:
        checks["previous_report_complete"] = {
            "status": "OK",
            "detail": "First task — no previous report to validate",
        }

    # Check 4: Previous task spec review report exists
    if task_number > 0:
        prev_padded = "{:03d}".format(previous_task)
        spec_review_pattern = os.path.join(args.reports_dir, "task-{}-spec-review*".format(prev_padded))
        spec_review_files = sorted(glob.glob(spec_review_pattern))
        if spec_review_files:
            checks["previous_spec_review"] = {
                "status": "PASS",
                "detail": "reports/task-{}-spec-review exists".format(prev_padded),
            }
        else:
            checks["previous_spec_review"] = {
                "status": "FAIL",
                "detail": "No spec review report for Task {}. Dispatch spec compliance review and save to reports/task-{}-spec-review.md".format(previous_task, prev_padded),
            }
            blockers.append("previous_spec_review")
    else:
        checks["previous_spec_review"] = {
            "status": "OK",
            "detail": "First task — no previous spec review to verify",
        }

    # Check 5: Previous task quality review report exists
    if task_number > 0:
        prev_padded = "{:03d}".format(previous_task)
        quality_review_pattern = os.path.join(args.reports_dir, "task-{}-quality-review*".format(prev_padded))
        quality_review_files = sorted(glob.glob(quality_review_pattern))
        if quality_review_files:
            checks["previous_quality_review"] = {
                "status": "PASS",
                "detail": "reports/task-{}-quality-review exists".format(prev_padded),
            }
        else:
            checks["previous_quality_review"] = {
                "status": "FAIL",
                "detail": "No quality review report for Task {}. Dispatch code quality review and save to reports/task-{}-quality-review.md (or save reports/task-{}-quality-review-minimum-tier.md if minimum tier declared)".format(previous_task, prev_padded, prev_padded),
            }
            blockers.append("previous_quality_review")
    else:
        checks["previous_quality_review"] = {
            "status": "OK",
            "detail": "First task — no previous quality review to verify",
        }

    # Check 6: Pending deviations count
    pending_count = count_pending_deviations(deviations_content)
    if pending_count == 0:
        checks["pending_deviations"] = {
            "status": "PASS",
            "detail": "0 pending",
        }
    else:
        checks["pending_deviations"] = {
            "status": "FAIL",
            "detail": (
                f"{pending_count} pending deviation(s) in {args.deviations_file} — "
                "disposition all entries before dispatching next task"
            ),
        }
        blockers.append("pending_deviations")

    # Check 7: Context load estimate
    load = estimate_context_load(args.plan_file, args.deviations_file, args.reports_dir)
    load_detail = (
        f"Accumulated files: ~{load['total_kb']}KB "
        f"(~{load['approx_tokens']:,} tokens, {load['file_count']} file(s))"
    )
    if load["total_bytes"] >= CONTEXT_LOAD_WARNING_BYTES:
        checks["context_load_estimate"] = {"status": "WARNING", "detail": load_detail}
        warnings.append(
            "Context load is high. Consider running context-summary.py to compress state "
            "before proceeding to avoid response quality degradation."
        )
    else:
        checks["context_load_estimate"] = {"status": "OK", "detail": load_detail}

    progress = {
        "tasks_completed": max(0, task_number - 1) if task_number > 0 else 0,
        "tasks_total": task_count,
        "checkboxes_checked": checkbox_counts["checked"],
        "checkboxes_total": checkbox_counts["total"],
        "percentage": pct,
    }

    overall = "FAIL" if blockers else "PASS"
    return _build_result(
        "pre-dispatch", task_number, overall, checks, warnings, blockers, progress
    )


def run_pre_completion(args: argparse.Namespace) -> dict:
    """
    Phase: pre-completion
    Checks before declaring implementation complete.
    """
    tier, _enforcement = _load_manifest_config(args)

    if args.deviations_file is None:
        print(
            json.dumps(
                {"error": "--deviations-file is required for phase pre-completion"}
            ),
            file=sys.stderr,
        )
        sys.exit(3)

    if args.reports_dir is None:
        print(
            json.dumps({"error": "--reports-dir is required for phase pre-completion"}),
            file=sys.stderr,
        )
        sys.exit(3)

    checks = {}
    blockers = []
    warnings = []

    # Read plan file
    if not os.path.isfile(args.plan_file):
        print(
            json.dumps({"error": f"Plan file not found: {args.plan_file}"}),
            file=sys.stderr,
        )
        sys.exit(3)
    try:
        plan_content = read_file(args.plan_file)
    except OSError as e:
        print(json.dumps({"error": f"Cannot read plan file: {e}"}), file=sys.stderr)
        sys.exit(3)

    # Read additional plan files for multi-module aggregation
    all_plan_contents = [plan_content]
    if getattr(args, "additional_plan_files", None):
        for path in args.additional_plan_files:
            if os.path.isfile(path):
                try:
                    all_plan_contents.append(read_file(path))
                except OSError:
                    pass

    # Read deviations file
    deviations_content = ""
    if os.path.isfile(args.deviations_file):
        try:
            deviations_content = read_file(args.deviations_file)
        except OSError:
            pass

    # Aggregate checkbox and task counts across all plan files
    checkbox_counts = {"checked": 0, "unchecked": 0, "total": 0}
    task_count = 0
    for content in all_plan_contents:
        cb = count_checkboxes(content)
        checkbox_counts["checked"] += cb["checked"]
        checkbox_counts["unchecked"] += cb["unchecked"]
        checkbox_counts["total"] += cb["total"]
        task_count += count_tasks(content)

    # Aggregate plan content for task-report matching (all_tasks_have_reports)
    combined_plan_content = "\n".join(all_plan_contents)

    # Check 1: All checkboxes checked
    if checkbox_counts["total"] == 0:
        checks["all_checkboxes_checked"] = {
            "status": "OK",
            "detail": "No checkboxes found in plan",
        }
    elif checkbox_counts["unchecked"] == 0:
        checks["all_checkboxes_checked"] = {
            "status": "PASS",
            "detail": f"{checkbox_counts['checked']}/{checkbox_counts['total']} checked",
        }
    else:
        checks["all_checkboxes_checked"] = {
            "status": "FAIL",
            "detail": (
                f"{checkbox_counts['checked']}/{checkbox_counts['total']} checked — "
                f"{checkbox_counts['unchecked']} unchecked checkbox(es) remain"
            ),
        }
        blockers.append("all_checkboxes_checked")

    # Check 2: No pending deviations
    pending_count = count_pending_deviations(deviations_content)
    if pending_count == 0:
        checks["no_pending_deviations"] = {
            "status": "PASS",
            "detail": "All DEVIATIONS.md entries are dispositioned",
        }
    else:
        checks["no_pending_deviations"] = {
            "status": "FAIL",
            "detail": (
                f"{pending_count} pending deviation(s) remain in {args.deviations_file} — "
                "all entries must have a disposition other than Pending"
            ),
        }
        blockers.append("no_pending_deviations")

    # Check 3: All tasks have report files (across all plan files)
    report_check = all_tasks_have_reports(combined_plan_content, args.reports_dir)
    if report_check["pass"]:
        checks["all_tasks_have_reports"] = {
            "status": "PASS",
            "detail": f"All {task_count} task(s) have report files in {args.reports_dir}",
        }
    else:
        missing_list = ", ".join(f"Task {n}" for n in report_check["missing"])
        checks["all_tasks_have_reports"] = {
            "status": "FAIL",
            "detail": f"Missing reports for: {missing_list}",
        }
        blockers.append("all_tasks_have_reports")

    # Check 4: All report files are COMPLETE
    report_files = find_all_report_files(args.reports_dir)
    incomplete_reports = []
    for report_path in report_files:
        try:
            report_content = read_file(report_path)
            validation = validate_report_sections(report_content)
            if not validation["complete"]:
                incomplete_reports.append(
                    f"{os.path.basename(report_path)} "
                    f"({validation['sections_found']}/{validation['sections_total']} sections)"
                )
        except OSError:
            incomplete_reports.append(f"{os.path.basename(report_path)} (unreadable)")

    if not incomplete_reports:
        checks["all_reports_complete"] = {
            "status": "PASS",
            "detail": f"All {len(report_files)} report(s) have required sections",
        }
    else:
        checks["all_reports_complete"] = {
            "status": "FAIL",
            "detail": f"Incomplete reports: {'; '.join(incomplete_reports)}",
        }
        blockers.append("all_reports_complete")

    # Check 5: Honesty check artifact exists (reports/honesty-check-YYYY-MM-DD.md)
    if tier == "micro":
        checks["honesty_check_missing"] = {
            "status": "SKIP",
            "detail": "Micro tier — honesty check skipped per manifest",
        }
    else:
        honesty_matches = sorted(glob.glob(
            os.path.join(args.reports_dir, "honesty-check-*.md")
        ))
        honesty_found = any(
            os.path.isfile(p) and file_size_bytes(p) >= 50
            for p in honesty_matches
        )
        if honesty_found:
            checks["honesty_check_missing"] = {
                "status": "PASS",
                "detail": "Honesty check response present",
            }
        else:
            checks["honesty_check_missing"] = {
                "status": "FAIL",
                "detail": (
                    "Missing or empty reports/honesty-check-YYYY-MM-DD.md — "
                    "the honesty check must be completed before the Pre-Completion Gate. "
                    "Present the honesty check prompt to the user, save their response, "
                    "then re-run this checkpoint."
                ),
            }
            blockers.append("honesty_check_missing")

    # Check 6: Execution trace audit artifact exists
    if tier == "micro":
        checks["trace_audit_missing"] = {
            "status": "SKIP",
            "detail": "Micro tier — trace audit skipped per manifest",
        }
    else:
        trace_path = os.path.join(args.reports_dir, "execution-trace-audit.md")
        if os.path.isfile(trace_path) and file_size_bytes(trace_path) >= 50:
            checks["trace_audit_missing"] = {
                "status": "PASS",
                "detail": "Execution trace audit present",
            }
        else:
            checks["trace_audit_missing"] = {
                "status": "FAIL",
                "detail": (
                    "Missing or empty reports/execution-trace-audit.md — "
                    "run extract-execution-trace.py and dispatch the trace auditor "
                    "subagent before declaring completion."
                ),
            }
            blockers.append("trace_audit_missing")

    # Check 7: Minimum-tier review ratio cap (>50% triggers blocker)
    quality_total, quality_min = _count_review_tiers(args.reports_dir, "quality-review")
    partner_total, partner_min = _count_review_tiers(args.reports_dir, "partner-review")

    if quality_total > 0 and quality_min / quality_total > 0.5:
        checks["excessive_minimum_tier_quality"] = {
            "status": "FAIL",
            "detail": (
                f"{quality_min}/{quality_total} quality reviews are minimum-tier "
                f"({round(100 * quality_min / quality_total)}%). "
                "Tasks touching shared files, multi-file changes, or Pattern References "
                "should use full dispatched reviews."
            ),
        }
        blockers.append("excessive_minimum_tier_quality")
    else:
        checks["excessive_minimum_tier_quality"] = {
            "status": "PASS",
            "detail": (
                f"{quality_min}/{quality_total} quality reviews are minimum-tier"
                if quality_total > 0
                else "No quality reviews found"
            ),
        }

    if partner_total > 0 and partner_min / partner_total > 0.5:
        checks["excessive_minimum_tier_partner"] = {
            "status": "FAIL",
            "detail": (
                f"{partner_min}/{partner_total} partner reviews are minimum-tier "
                f"({round(100 * partner_min / partner_total)}%). "
                "Tasks with Pattern References, Shared Constants, or multi-file changes "
                "should have full partner dispatches."
            ),
        }
        blockers.append("excessive_minimum_tier_partner")
    else:
        checks["excessive_minimum_tier_partner"] = {
            "status": "PASS",
            "detail": (
                f"{partner_min}/{partner_total} partner reviews are minimum-tier"
                if partner_total > 0
                else "No partner reviews found"
            ),
        }

    pct = (
        round(100 * checkbox_counts["checked"] / checkbox_counts["total"])
        if checkbox_counts["total"] > 0
        else 0
    )

    progress = {
        "tasks_completed": task_count,
        "tasks_total": task_count,
        "checkboxes_checked": checkbox_counts["checked"],
        "checkboxes_total": checkbox_counts["total"],
        "percentage": pct,
    }

    overall = "FAIL" if blockers else "PASS"
    return _build_result(
        "pre-completion", None, overall, checks, warnings, blockers, progress
    )


def _build_result(
    phase: str,
    task_number,
    overall_status: str,
    checks: dict,
    warnings: list,
    blockers: list,
    progress,
) -> dict:
    """Assemble the final result dict via CheckpointResult model."""
    check_models = {
        name: CheckResult(status=v["status"], detail=v["detail"])
        for name, v in checks.items()
    }
    progress_model = Progress(**progress) if progress else None
    result = CheckpointResult(
        schema_version=CURRENT_SCHEMA_VERSION,
        phase=phase,
        status=overall_status,
        task_number=task_number,
        checks=check_models,
        warnings=warnings,
        blockers=blockers,
        progress=progress_model,
    )
    return result.model_dump(exclude_none=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Controller discipline checkpoint for subagent-driven-development. "
            "Verifies pre-execution, pre-dispatch, or pre-completion conditions "
            "and outputs JSON results. "
            "Exit code 0=PASS, 1=FAIL, 2=WARNING, 3=script error."
        )
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["pre-execution", "pre-dispatch", "pre-completion"],
        help="Checkpoint phase to run.",
    )
    parser.add_argument(
        "--plan-file",
        required=False,
        default=None,
        metavar="PATH",
        help=(
            "Path to the implementation plan markdown file. "
            "Required unless --manifest is provided."
        ),
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help=(
            "Path to .sdd-session.json. When provided, reads plan_file, "
            "enforcement, task_range, and midpoint from manifest instead of "
            "command-line arguments."
        ),
    )
    parser.add_argument(
        "--deviations-file",
        required=False,
        default=None,
        metavar="PATH",
        help=(
            "Path to DEVIATIONS.md. "
            "Optional for --phase pre-execution (skipped with SKIP status if absent). "
            "Required for --phase pre-dispatch and pre-completion."
        ),
    )
    parser.add_argument(
        "--reports-dir",
        required=False,
        default=None,
        metavar="PATH",
        help=(
            "Path to the reports/ directory where task report files are stored. "
            "Optional for --phase pre-execution (skipped with SKIP status if absent). "
            "Required for --phase pre-dispatch and pre-completion."
        ),
    )
    parser.add_argument(
        "--task-number",
        required=False,
        type=int,
        default=None,
        metavar="N",
        help=(
            "Task number about to be dispatched. "
            "Required for --phase pre-dispatch. "
            "The script checks that task N-1 is fully complete."
        ),
    )
    parser.add_argument(
        "--additional-plan-files",
        nargs="+",
        metavar="PATH",
        default=None,
        help=(
            "Additional module plan files. Checkbox counts and task counts are "
            "aggregated across the primary plan file and all additional files. "
            "Useful for multi-module plans where checkboxes span multiple files."
        ),
    )
    parser.add_argument(
        "--feature-dir",
        help="Active feature directory. When provided, --reports-dir and --deviations-file "
             "are resolved relative to this path (if not explicitly set).",
        default=None,
    )
    args = parser.parse_args()

    if args.manifest is None and args.plan_file is None:
        print(
            json.dumps({
                "error": "Either --plan-file or --manifest is required."
            }),
            file=sys.stderr,
        )
        return 3

    if args.feature_dir:
        if not args.reports_dir:
            args.reports_dir = f"{args.feature_dir}/reports/"
        if not args.deviations_file:
            args.deviations_file = f"{args.feature_dir}/deviations.md"

    # Dispatch to the appropriate phase handler
    try:
        if args.phase == "pre-execution":
            result = run_pre_execution(args)
        elif args.phase == "pre-dispatch":
            result = run_pre_dispatch(args)
        elif args.phase == "pre-completion":
            result = run_pre_completion(args)
        else:
            # Should be unreachable due to choices= above
            print(
                json.dumps({"error": f"Unknown phase: {args.phase}"}), file=sys.stderr
            )
            return 3
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {e}"}), file=sys.stderr)
        return 3

    print(json.dumps(result, indent=2))

    # Determine exit code
    if result["status"] == "FAIL":
        return 1
    if result.get("warnings"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
