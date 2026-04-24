#!/usr/bin/env python3
"""CLI entry points for Pydantic validation of plan and handoff artifacts.

Usage:
    python3 validators.py plan <path/to/plan.md> [--schema-version N]
    python3 validators.py handoff <path/to/package-dir/> [--schema-version N]

Exit codes: 0 = pass, 1 = validation fail, 2 = infrastructure error.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install: .venv/bin/pip install pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    from pydantic import ValidationError
except ImportError:
    print(
        "Pydantic v2.7+ is required. Install: .venv/bin/pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(2)

from plan import Plan
from handoff import HandoffPackage
from errors import format_validation_error, format_yaml_error


def _check_bypass() -> bool:
    if os.environ.get("SUPERPOWERS_VALIDATOR_BYPASS") == "1":
        print(
            "WARNING: SUPERPOWERS_VALIDATOR_BYPASS is set — validation BYPASS active. "
            "This skips ALL Pydantic checks. Unset the env var when done.",
            file=sys.stderr,
        )
        return True
    return False


def _extract_frontmatter(text: str) -> str | None:
    """Extract YAML between first pair of --- delimiters. Returns None if no frontmatter."""
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    return text[3:end]


def validate_plan(path: str, schema_version: int | None = None) -> int:
    """Validate a plan file. Returns exit code."""
    plan_path = Path(path)
    if not plan_path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    if _check_bypass():
        return 0

    text = plan_path.read_text(encoding="utf-8")
    frontmatter_yaml = _extract_frontmatter(text)

    if frontmatter_yaml is None:
        print(
            f"No YAML frontmatter found in {path}. "
            "This plan predates the Phase 1 Pydantic cutover — "
            "add YAML frontmatter to validate it.",
            file=sys.stderr,
        )
        return 1

    try:
        data = yaml.safe_load(frontmatter_yaml)
    except yaml.YAMLError as e:
        print(format_yaml_error(e, path), file=sys.stderr)
        return 1

    if data is None:
        data = {}

    try:
        Plan.model_validate(data)
    except ValidationError as e:
        print(format_validation_error(e, path), file=sys.stderr)
        return 1
    except Exception as e:
        print(
            f"VALIDATOR CRASHED (this is a bug in the validator, not your artifact): "
            f"{type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return 2

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Pydantic artifact validator")
    parser.add_argument("command", choices=["plan", "handoff"])
    parser.add_argument("path", help="Path to plan file or handoff package directory")
    parser.add_argument(
        "--schema-version",
        type=int,
        default=None,
        help="Forensic: validate against older schema version (stub — not yet implemented)",
    )
    args = parser.parse_args()

    if args.command == "plan":
        sys.exit(validate_plan(args.path, args.schema_version))
    elif args.command == "handoff":
        print("Handoff validation not yet implemented", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
