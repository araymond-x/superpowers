"""
_report_utils.py

Shared utilities for report parsing, section detection, and status extraction.
Used by validate-report.py, controller-checkpoint.py, and context-summary.py.

This is the single source of truth for report structure definitions.
Do NOT duplicate this logic in other scripts — import from here.
"""

import re

# ---------------------------------------------------------------------------
# Required sections as defined in implementer-prompt-v0.1.md.
# Each entry is (canonical_name, list_of_accepted_header_patterns).
# Patterns are matched case-insensitively against bold or ATX headers.
# ---------------------------------------------------------------------------
REQUIRED_SECTIONS = [
    ("Status", [r"\bstatus\b"]),
    ("Implementation Summary", [r"implementation\s+summary"]),
    ("Files Changed", [r"files?\s+changed"]),
    ("Source Files Read", [r"source\s+files?\s+read"]),
    (
        "Tests",
        [r"\btests?\b"],
    ),  # Word-boundary anchored to avoid "Contract" false positive
    ("Contract Compliance", [r"contract\s+compliance"]),
    ("Deviations from Plan", [r"deviations?\s+from\s+plan"]),
    ("Self-Review Findings", [r"self[\-\s]review\s+findings?"]),
    ("Concerns", [r"\bconcerns?\b"]),
]

# Valid implementer status values
VALID_STATUSES = {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"}

# Matches status value in report content
STATUS_VALUE_PATTERN = re.compile(
    r"\b(DONE_WITH_CONCERNS|DONE|BLOCKED|NEEDS_CONTEXT)\b"
)

# Matches bold (**Section**) or ATX (## Section) headers
SECTION_HEADER_PATTERN = re.compile(r"(?:\*\*([^*]+)\*\*|^#{1,4}\s+(.+))", re.MULTILINE)

# Placeholder values that indicate "no content"
PLACEHOLDER_VALUES = {"none", "n/a", "na", "-", "\u2014", ""}


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


def extract_implementer_status(content):
    """
    Find the implementer's status value in the report.
    Returns the status string or "UNKNOWN" if not found.
    """
    match = STATUS_VALUE_PATTERN.search(content)
    if match:
        return match.group(1)
    return "UNKNOWN"


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
    # Short text like "None — implemented exactly as specified" is a placeholder
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
        implementer_status: extracted status string
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
        "implementer_status": extract_implementer_status(content),
        "has_deviations": section_contains_content("Deviations from Plan", content),
        "has_concerns": section_contains_content("Concerns", content),
    }
