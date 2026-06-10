"""
_report_utils.py

Shared utilities for report parsing, section detection, and content heuristics.
Used by validate-report.py, controller-checkpoint.py, context-summary.py, and
validate-plan.py.

VALID_STATUSES is re-exported from the Pydantic model (single source of truth).
Prose section validation covers the 5 sections that remain in the markdown body
after Phase 2 moved Status, Files Changed, Tests, and Contract Compliance to
YAML frontmatter.
"""

import re
import sys
from pathlib import Path

# Re-export VALID_STATUSES from the Pydantic model (single source of truth)
sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))
from implementer_report import Status
VALID_STATUSES = set(Status.__args__)

# Required prose sections — 5 remain after Phase 2 moved 4 to frontmatter
REQUIRED_SECTIONS = [
    ("Implementation Summary", [r"implementation\s+summary"]),
    ("Source Files Read", [r"source\s+files?\s+read"]),
    ("Deviations from Plan", [r"deviations?\s+from\s+plan"]),
    ("Self-Review Findings", [r"self[\-\s]review\s+findings?"]),
    ("Concerns", [r"\bconcerns?\b"]),
]

# Matches bold (**Section**) or ATX (## Section) headers
SECTION_HEADER_PATTERN = re.compile(r"(?:\*\*([^*]+)\*\*|^#{1,4}\s+(.+))", re.MULTILINE)

# Placeholder values that indicate "no content"
PLACEHOLDER_VALUES = {"none", "n/a", "na", "-", "\u2014", ""}

PROMPT_PLACEHOLDER_PHRASES = [
    "none \u2014 implemented exactly as specified",
    "no issues found",
    "no concerns",
    "none \u2014 no source files listed for this task",
    "none found in modified directories",
    "no contract constraints for this task",
]


def _unfenced_content(text: str) -> str:
    """Return text with lines inside ``` fence blocks replaced by blank lines.

    Preserves line count so that line-index-based logic (span measurement,
    header positions) remains valid after filtering.

    Single source of truth — imported by validate-plan.py and
    controller-checkpoint.py for fence-aware task-header parsing (N5).
    """
    lines = text.splitlines(keepends=True)
    result = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            result.append("\n")
        elif in_fence:
            result.append("\n")
        else:
            result.append(line)
    return "".join(result)


def find_sections(content):
    """
    Return a list of all candidate section header strings found in the report.
    Headers are returned in their original case (matching is done case-insensitively
    by callers).
    """
    found = []
    for match in SECTION_HEADER_PATTERN.finditer(content):
        header_text = match.group(1) or match.group(2)
        if header_text:
            found.append(header_text.strip())
    return found


def section_is_present(canonical_name, patterns, headers):
    """
    Return True if any of the accepted patterns matches any found header.
    Matching is case-insensitive.
    """
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    for header in headers:
        for pattern in compiled:
            if pattern.search(header):
                return True
    return False


def section_contains_content(section_name, content):
    """
    Heuristic check: returns True if a section likely has non-trivial content.
    Handles both **bold** and ## ATX header styles.
    Used for "Deviations from Plan" and "Concerns" flags.
    """
    # Try bold header first
    bold_pattern = re.compile(
        r"\*\*" + re.escape(section_name) + r"\*\*[:\s]*(.*?)(?=\*\*[A-Z]|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    match = bold_pattern.search(content)

    # Fall back to ATX header
    if not match:
        atx_pattern = re.compile(
            r"^#{1,4}\s+" + re.escape(section_name) + r"\s*\n(.*?)(?=^#{1,4}\s|\Z)",
            re.DOTALL | re.IGNORECASE | re.MULTILINE,
        )
        match = atx_pattern.search(content)

    if not match:
        return False

    body = match.group(1).strip()
    if not body or body.lower() in PLACEHOLDER_VALUES:
        return False
    # Check against prompt template placeholder phrases
    body_lower = body.lower()
    for phrase in PROMPT_PLACEHOLDER_PHRASES:
        if body_lower.startswith(phrase):
            return False
    if len(body) <= 10:
        return False
    return True


def is_placeholder_text(text):
    """Return True if text is a placeholder value indicating 'no content'."""
    if not text:
        return True
    return text.strip().lower() in PLACEHOLDER_VALUES


def validate_report_sections(content):
    """
    Validate a report's sections and return a result dict.
    This is the canonical validation logic — do not reimplement elsewhere.

    Returns dict with keys:
        status: "COMPLETE" or "INCOMPLETE"
        sections_found: list of canonical names found
        sections_missing: list of canonical names missing
        has_deviations: bool
        has_concerns: bool
    """
    headers = find_sections(content)

    sections_found = []
    sections_missing = []

    for canonical_name, patterns in REQUIRED_SECTIONS:
        if section_is_present(canonical_name, patterns, headers):
            sections_found.append(canonical_name)
        else:
            sections_missing.append(canonical_name)

    return {
        "status": "COMPLETE" if not sections_missing else "INCOMPLETE",
        "sections_found": sections_found,
        "sections_missing": sections_missing,
        "has_deviations": section_contains_content("Deviations from Plan", content),
        "has_concerns": section_contains_content("Concerns", content),
    }
