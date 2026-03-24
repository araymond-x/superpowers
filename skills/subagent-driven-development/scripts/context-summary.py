#!/usr/bin/env python3
"""
context-summary.py

Generates a condensed execution context summary from completed task reports
and DEVIATIONS.md. Intended to replace the need to re-read all individual
report files when the controller's context window is under pressure.

The output is a single markdown file the controller can read to reconstruct
full execution state — one file instead of N report files.

Exit codes:
  0 - Summary generated successfully
  1 - Partial success (some reports could not be parsed; summary still written)
  2 - Script error (bad arguments, unreadable inputs, cannot write output)

Usage:
  python scripts/context-summary.py \\
    --reports-dir reports/ \\
    --deviations-file DEVIATIONS.md \\
    --output context-summary.md
"""

import argparse
import datetime
import glob
import json
import os
import re
import sys

# Pattern to extract task number from report filename (task-N-implementer-report*)
TASK_NUMBER_PATTERN = re.compile(r"task-(\d+)-implementer-report", re.IGNORECASE)

# Pattern for implementer status values
STATUS_PATTERN = re.compile(r"\b(DONE_WITH_CONCERNS|DONE|BLOCKED|NEEDS_CONTEXT)\b")

# Section patterns for implementer report content.
#
# The implementer prompt uses bold headers with the colon inside the bold span:
#   **Files Changed:**
#   **Concerns:**
#   **Deviations from Plan:**
#
# Each pattern matches the header (with optional colon inside or outside the **),
# then captures body content up to the next bold header or end-of-string.
# The lookahead uses \*\*\S to match the next bold marker without constraining
# the first character to uppercase.

FILES_CHANGED_PATTERN = re.compile(
    r"\*\*Files?\s+Changed[:\s]*\*\*[:\s]*(.*?)(?=\*\*\S|\Z)",
    re.DOTALL | re.IGNORECASE,
)

CONCERNS_PATTERN = re.compile(
    r"\*\*Concerns?[:\s]*\*\*[:\s]*(.*?)(?=\*\*\S|\Z)",
    re.DOTALL | re.IGNORECASE,
)

DEVIATIONS_FROM_PLAN_PATTERN = re.compile(
    r"\*\*Deviations?\s+from\s+Plan[:\s]*\*\*[:\s]*(.*?)(?=\*\*\S|\Z)",
    re.DOTALL | re.IGNORECASE,
)

# Pattern to match deviation table rows in DEVIATIONS.md
# Matches lines like: | Task 2 | IndependentDecision | description | Pending |
DEVIATION_ROW_PATTERN = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
)

# Header row markers to exclude from deviation rows
DEVIATION_HEADER_MARKERS = {"task", "type", "description", "disposition", "---"}


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_status(content: str) -> str:
    """Extract the implementer status value from report content."""
    match = STATUS_PATTERN.search(content)
    return match.group(1) if match else "UNKNOWN"


def extract_section_content(pattern: re.Pattern, content: str) -> str:
    """
    Extract the body of a section matched by pattern.
    Returns a single clean line summarizing the content, or "—" if empty/None/None-like.
    """
    match = pattern.search(content)
    if not match:
        return "—"
    body = match.group(1).strip()
    if not body:
        return "—"
    # Collapse to first meaningful line for table display
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return "—"
    # Extract descriptions from bullet/list items, skipping None/N/A placeholders
    items = []
    for line in lines[:5]:  # Cap at 5 items to keep table readable
        # Strip leading "- " or "* " or "1. " list markers
        cleaned = re.sub(r"^[-*\d.]+\s+", "", line).strip()
        # Skip placeholder values
        if cleaned.lower() in {"none", "n/a", "na", "-", "—", ""}:
            continue
        # Skip "None -- ..." style sentences (implementer placeholder text)
        if re.match(r"^none\b", cleaned, re.IGNORECASE):
            continue
        if cleaned:
            items.append(cleaned)
    if not items:
        return "—"
    return "; ".join(items) if len(items) > 1 else items[0]


def extract_files_changed(content: str) -> list:
    """
    Extract a list of file paths from the Files Changed section.
    Returns a list of strings (file paths or descriptions).
    """
    match = FILES_CHANGED_PATTERN.search(content)
    if not match:
        return []
    body = match.group(1).strip()
    if not body or body.lower() in {"none", "n/a", "na"}:
        return []

    files = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip list markers ("- ", "* ", "1. ", etc.)
        cleaned = re.sub(r"^[-*\d.]+\s+", "", line).strip()
        # Strip surrounding backticks from file paths: `src/file.py`
        cleaned = cleaned.strip("`")
        # Strip inline descriptions separated by em-dash, en-dash, or double-dash
        # Handles: "src/file.py -- description", "src/file.py -- desc", "src/file.py — desc"
        path_part = re.split(r"\s+(?:--+|—|–)\s+", cleaned)[0].strip().strip("`")
        if path_part:
            files.append(path_part)
    return files


def parse_report(report_path: str) -> dict:
    """
    Parse a single implementer report file.
    Returns a dict with task_number, status, files_changed, concerns, deviations, parse_error.
    """
    filename = os.path.basename(report_path)
    task_match = TASK_NUMBER_PATTERN.search(filename)
    task_number = int(task_match.group(1)) if task_match else None

    result = {
        "task_number": task_number,
        "filename": filename,
        "status": "UNKNOWN",
        "files_changed": [],
        "concerns": "—",
        "deviations_from_plan": "—",
        "parse_error": None,
    }

    try:
        content = read_file(report_path)
    except OSError as e:
        result["parse_error"] = str(e)
        return result

    result["status"] = extract_status(content)
    result["files_changed"] = extract_files_changed(content)
    result["concerns"] = extract_section_content(CONCERNS_PATTERN, content)
    result["deviations_from_plan"] = extract_section_content(
        DEVIATIONS_FROM_PLAN_PATTERN, content
    )
    return result


def parse_deviations(deviations_path: str) -> list:
    """
    Parse DEVIATIONS.md and extract all table row entries.
    Returns a list of dicts with keys: task, type, description, disposition.
    Excludes header rows and separator rows.
    """
    entries = []
    if not os.path.isfile(deviations_path):
        return entries

    try:
        content = read_file(deviations_path)
    except OSError:
        return entries

    for match in DEVIATION_ROW_PATTERN.finditer(content):
        task = match.group(1).strip()
        dtype = match.group(2).strip()
        description = match.group(3).strip()
        disposition = match.group(4).strip()

        # Skip header rows and separator rows (--- patterns)
        if (
            task.lower() in DEVIATION_HEADER_MARKERS
            or dtype.replace("-", "").strip() == ""
            or re.match(r"^[-:]+$", task)
        ):
            continue

        entries.append(
            {
                "task": task,
                "type": dtype,
                "description": description,
                "disposition": disposition,
            }
        )

    return entries


def collect_cumulative_files(reports: list) -> list:
    """
    Build a deduplicated list of all files modified across all tasks.
    Returns a list of (path, task_number) tuples, ordered by task_number.
    """
    seen = {}  # path -> first task_number that modified it
    for report in reports:
        task_n = report.get("task_number")
        for f in report.get("files_changed", []):
            if f and f not in seen:
                seen[f] = task_n
    # Sort by task number, then file path
    return sorted(
        seen.items(), key=lambda x: (x[1] if x[1] is not None else 9999, x[0])
    )


def format_key_notes(report: dict) -> str:
    """
    Produce a concise key-notes string for the task summary table.
    Prioritizes concerns, then deviations from plan.
    """
    notes = []
    if report["concerns"] != "—":
        # Truncate long concern descriptions for table display
        concern_text = report["concerns"]
        if len(concern_text) > 80:
            concern_text = concern_text[:77] + "..."
        notes.append(f"Concern: {concern_text}")
    elif report["deviations_from_plan"] != "—":
        dev_text = report["deviations_from_plan"]
        if len(dev_text) > 80:
            dev_text = dev_text[:77] + "..."
        notes.append(f"Deviation: {dev_text}")

    return "; ".join(notes) if notes else "—"


def format_files_changed_cell(files: list) -> str:
    """Format the files changed list for a table cell."""
    if not files:
        return "—"
    if len(files) == 1:
        return files[0]
    if len(files) <= 3:
        return "; ".join(files)
    return "; ".join(files[:3]) + f" (+{len(files) - 3} more)"


def generate_summary(
    reports: list,
    deviations: list,
    cumulative_files: list,
    total_tasks_in_plan: int,
) -> str:
    """
    Generate the context summary markdown document.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    completed_count = len(reports)

    lines = [
        "# Execution Context Summary",
        "",
        f"**Generated**: {timestamp}",
        f"**Tasks completed**: {completed_count} of {total_tasks_in_plan}",
        "",
        "---",
        "",
        "## Task Summaries",
        "",
        "| Task | Status | Files Changed | Key Notes |",
        "|------|--------|--------------|-----------|",
    ]

    for report in sorted(reports, key=lambda r: r.get("task_number") or 0):
        task_label = (
            str(report["task_number"]) if report["task_number"] is not None else "?"
        )
        status = report["status"]
        files_cell = format_files_changed_cell(report["files_changed"])
        notes_cell = format_key_notes(report)

        # Escape pipe characters in cell content to avoid breaking the table
        files_cell = files_cell.replace("|", "/")
        notes_cell = notes_cell.replace("|", "/")

        lines.append(f"| {task_label} | {status} | {files_cell} | {notes_cell} |")

    lines.append("")

    # Active deviations section
    lines += [
        "## Active Deviations",
        "",
    ]

    if deviations:
        lines.append("| Task | Type | Description | Disposition |")
        lines.append("|------|------|-------------|-------------|")
        for entry in deviations:
            task = entry["task"].replace("|", "/")
            dtype = entry["type"].replace("|", "/")
            desc = entry["description"].replace("|", "/")
            disp = entry["disposition"].replace("|", "/")
            lines.append(f"| {task} | {dtype} | {desc} | {disp} |")
    else:
        lines.append("_No deviations logged._")

    lines.append("")

    # Cumulative files modified section
    lines += [
        "## Files Modified (cumulative)",
        "",
    ]

    if cumulative_files:
        for path, task_n in cumulative_files:
            task_label = f"Task {task_n}" if task_n is not None else "unknown task"
            lines.append(f"- `{path}` ({task_label})")
    else:
        lines.append("_No files recorded._")

    lines.append("")

    # Parse errors section (if any)
    errored_reports = [r for r in reports if r.get("parse_error")]
    if errored_reports:
        lines += [
            "## Parse Errors",
            "",
            "_The following reports could not be fully parsed:_",
            "",
        ]
        for r in errored_reports:
            lines.append(f"- `{r['filename']}`: {r['parse_error']}")
        lines.append("")

    return "\n".join(lines)


def find_report_files(reports_dir: str) -> list:
    """Return all implementer report files in the reports directory, sorted."""
    pattern = os.path.join(reports_dir, "task-*-implementer-report*")
    return sorted(glob.glob(pattern))


def count_plan_tasks(reports_dir: str) -> int:
    """
    Estimate the total number of tasks by finding the highest task number
    in any report file. Returns 0 if no reports exist.
    """
    max_task = 0
    found_any = False
    for path in find_report_files(reports_dir):
        found_any = True
        match = TASK_NUMBER_PATTERN.search(os.path.basename(path))
        if match:
            n = int(match.group(1))
            if n > max_task:
                max_task = n
    return max_task + 1 if found_any else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a condensed execution context summary from completed task reports. "
            "Produces a single markdown file the controller can read to reconstruct "
            "full execution state without re-reading all individual reports. "
            "Exit code 0=success, 1=partial success, 2=error."
        )
    )
    parser.add_argument(
        "--reports-dir",
        required=True,
        metavar="PATH",
        help="Path to the reports/ directory containing implementer report files.",
    )
    parser.add_argument(
        "--deviations-file",
        required=True,
        metavar="PATH",
        help="Path to DEVIATIONS.md.",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="PATH",
        help="Path where the context summary markdown file will be written.",
    )
    parser.add_argument(
        "--total-tasks",
        required=False,
        type=int,
        default=None,
        metavar="N",
        help=(
            "Total number of tasks in the plan. "
            "If omitted, estimated from the highest task number in report files."
        ),
    )
    args = parser.parse_args()

    # Validate inputs
    if not os.path.isdir(args.reports_dir):
        print(
            json.dumps({"error": f"Reports directory not found: {args.reports_dir}"}),
            file=sys.stderr,
        )
        return 2

    # Parse all report files
    report_files = find_report_files(args.reports_dir)
    if not report_files:
        print(
            json.dumps(
                {"error": f"No implementer report files found in {args.reports_dir}"}
            ),
            file=sys.stderr,
        )
        return 2

    reports = []
    parse_errors = 0
    for path in report_files:
        report = parse_report(path)
        reports.append(report)
        if report.get("parse_error"):
            parse_errors += 1

    # Parse deviations
    deviations = parse_deviations(args.deviations_file)

    # Cumulative file list
    cumulative_files = collect_cumulative_files(reports)

    # Total tasks estimate
    if args.total_tasks is not None:
        total_tasks = args.total_tasks
    else:
        total_tasks = count_plan_tasks(args.reports_dir)
        # Fall back to completed count if no reports with parseable task numbers
        if total_tasks == 0:
            total_tasks = len(reports)

    # Generate summary markdown
    summary_md = generate_summary(reports, deviations, cumulative_files, total_tasks)

    # Write output
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print(
                json.dumps({"error": f"Cannot create output directory: {e}"}),
                file=sys.stderr,
            )
            return 2

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(summary_md)
    except OSError as e:
        print(
            json.dumps({"error": f"Cannot write output file: {e}"}),
            file=sys.stderr,
        )
        return 2

    # Print a brief status to stdout
    status_msg = {
        "status": "PARTIAL" if parse_errors else "OK",
        "reports_processed": len(reports),
        "parse_errors": parse_errors,
        "deviations_found": len(deviations),
        "files_tracked": len(cumulative_files),
        "output": args.output,
    }
    print(json.dumps(status_msg, indent=2))

    return 1 if parse_errors else 0


if __name__ == "__main__":
    sys.exit(main())
