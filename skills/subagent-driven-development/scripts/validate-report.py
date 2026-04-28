#!/usr/bin/env python3
"""
validate-report.py

Two-layer report validation:
1. Pydantic frontmatter validation (via validators.py)
2. Prose section-presence check (via _report_utils.py)

Reports without frontmatter hard FAIL at layer 1 and never reach layer 2.

Exit codes:
  0 - COMPLETE (Pydantic valid + all required prose sections present)
  1 - INCOMPLETE (Pydantic invalid or prose sections missing)
  2 - Script error (bad arguments, file not found, etc.)

Usage:
  python validate-report.py --report-file /path/to/report.md
"""

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

# Add the script directory to the path so _report_utils can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_utils import validate_report_sections

# Add models directory for Pydantic validation
MODELS_DIR = str(Path(__file__).resolve().parent / "../../scripts/models")
sys.path.insert(0, MODELS_DIR)
from validators import validate_report


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validate that an implementer report has valid Pydantic frontmatter "
            "and contains all required prose sections. "
            "Outputs JSON to stdout. "
            "Exit code 1 if validation fails, 0 if complete."
        )
    )
    parser.add_argument(
        "--report-file",
        required=True,
        metavar="PATH",
        help="Path to the implementer report markdown file to validate.",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.report_file):
        print(
            json.dumps({"error": "Report file not found: {}".format(args.report_file)}),
            file=sys.stderr,
        )
        return 2

    # Layer 1: Pydantic frontmatter validation
    pydantic_exit = validate_report(args.report_file)
    if pydantic_exit != 0:
        # Pydantic validation failed — report as INCOMPLETE
        # Error details already printed to stderr by validate_report()
        print(json.dumps({
            "status": "INCOMPLETE",
            "sections_found": [],
            "sections_missing": ["YAML frontmatter validation failed"],
        }))
        return 1

    # Layer 2: Prose section-presence check
    try:
        with open(args.report_file, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        print(
            json.dumps({"error": "Could not read report file: {}".format(e)}),
            file=sys.stderr,
        )
        return 2

    result = validate_report_sections(content)

    # Layer 3: done_with_concerns_check (CLI-level warning, not blocking)
    # If status is DONE but markdown body has non-empty Deviations or Concerns,
    # emit a warning to stderr. Per spec: informational only, exit code unchanged.
    if pydantic_exit == 0:
        try:
            fm_end = content.find("---", 3)
            if fm_end != -1:
                fm_data = yaml.safe_load(content[3:fm_end])
                if isinstance(fm_data, dict) and fm_data.get("status") == "DONE":
                    if result.get("has_deviations") or result.get("has_concerns"):
                        print(
                            "WARNING: status is DONE but report has non-empty "
                            "Deviations or Concerns. Consider DONE_WITH_CONCERNS.",
                            file=sys.stderr,
                        )
        except Exception:
            pass  # Warning check should never block validation

    print(json.dumps(result, indent=2))

    return 1 if result["status"] == "INCOMPLETE" else 0


if __name__ == "__main__":
    sys.exit(main())
