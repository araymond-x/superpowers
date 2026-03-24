#!/usr/bin/env python3
"""
validate-report.py

Validates that an implementer's report contains all required sections.
Required sections are defined by the implementer-prompt-v0.1.md contract.

Exit codes:
  0 - COMPLETE (all required sections present)
  1 - INCOMPLETE (one or more sections missing)
  2 - Script error (bad arguments, file not found, etc.)

Usage:
  python validate-report.py --report-file /path/to/report.md
"""

import argparse
import json
import os
import sys

# Add the script directory to the path so _report_utils can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_utils import validate_report_sections


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validate that an implementer report contains all required sections. "
            "Outputs JSON to stdout. "
            "Exit code 1 if any section is missing, 0 if complete."
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

    try:
        with open(args.report_file, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        print(
            json.dumps({"error": "Could not read report file: {}".format(e)}),
            file=sys.stderr,
        )
        return 2

    if not content.strip():
        print(
            json.dumps({"error": "Report file is empty."}),
            file=sys.stderr,
        )
        return 2

    result = validate_report_sections(content)
    print(json.dumps(result, indent=2))

    return 1 if result["status"] == "INCOMPLETE" else 0


if __name__ == "__main__":
    sys.exit(main())
