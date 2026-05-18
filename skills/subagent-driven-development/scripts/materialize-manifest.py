#!/usr/bin/env python3
"""
materialize-manifest.py

Reads plan frontmatter, computes enforcement profile from tier,
writes .sdd-session.json to the feature directory.

Exit codes:
  0 - Success (manifest written or already up-to-date)
  1 - Validation failure (bad frontmatter, missing fields)
  2 - Script error (bad arguments, file not found)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Add models to path (same pattern as controller-checkpoint.py)
sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))

try:
    import yaml
except ImportError:
    print("PyYAML required. Install: .venv/bin/pip install pyyaml", file=sys.stderr)
    sys.exit(2)

from pydantic import ValidationError

from _base import CURRENT_SCHEMA_VERSION
from sdd_session import (
    SddSession,
    TIER_PROFILES,
    ArtifactPaths,
    Enforcement,
    ModuleState,
    ProcessRequirements,
)


def extract_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter between --- delimiters. Returns None if absent."""
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    raw = text[3:end]
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        print(f"YAML parse error in frontmatter: {exc}", file=sys.stderr)
        return None


def compute_midpoint(start: int, end: int) -> int:
    """Compute the midpoint of a task range.

    Formula: start + (range_size + 1) // 2, where range_size = end - start.
    This gives a ceiling-biased midpoint within the range.
    """
    range_size = end - start
    return start + (range_size + 1) // 2


def git_root_relative(path: str) -> str:
    """Normalize an absolute path to git-root-relative.

    If the path is already relative, returns it unchanged.
    If git root cannot be determined, returns the path unchanged with a warning.
    """
    if not os.path.isabs(path):
        return path

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    git_root = result.stdout.strip()
    if git_root and path.startswith(git_root):
        return os.path.relpath(path, git_root)

    print(
        f"WARNING: '{path}' is absolute but not under git root '{git_root}'",
        file=sys.stderr,
    )
    return path


def materialize(plan_file: str, feature_dir: str) -> int:
    """Read plan frontmatter, build SddSession, write manifest."""
    plan_path = Path(plan_file)
    if not plan_path.is_file():
        print(f"Plan file not found: {plan_file}", file=sys.stderr)
        return 2

    text = plan_path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(text)
    if frontmatter is None:
        print(f"No valid YAML frontmatter in {plan_file}", file=sys.stderr)
        return 1

    # --- Tier ---
    tier = frontmatter.get("enforcement_tier") or "standard"
    if tier not in TIER_PROFILES:
        print(f"Invalid enforcement_tier: '{tier}'. Must be one of: {list(TIER_PROFILES)}", file=sys.stderr)
        return 1

    # --- Tasks ---
    tasks = frontmatter.get("tasks", [])
    total_tasks = len(tasks)
    if total_tasks == 0:
        print("No tasks found in plan frontmatter", file=sys.stderr)
        return 1

    # --- Modules (optional) ---
    modules_raw = frontmatter.get("modules")
    modules: list[ModuleState] | None = None
    active_module_id: int | None = None
    active_module_file: str | None = None

    if modules_raw:
        modules = []
        for m in modules_raw:
            file_val = m.get("file")
            if not file_val:
                print(
                    f"Module {m.get('id', '?')} is missing 'file' field. "
                    "Modules must declare their plan file path.",
                    file=sys.stderr,
                )
                return 1
            modules.append(ModuleState(
                id=m["id"],
                title=m["title"],
                file=file_val,
                task_ids=m["task_ids"],
            ))
        first = modules[0]
        task_range = (first.task_ids[0], first.task_ids[-1])
        active_module_id = first.id
        active_module_file = first.file
    else:
        all_ids = sorted(t["id"] for t in tasks)
        task_range = (all_ids[0], all_ids[-1])

    # --- Midpoint ---
    midpoint = compute_midpoint(task_range[0], task_range[1])

    # --- Enforcement profile ---
    profile = TIER_PROFILES[tier]
    enforcement_data = dict(profile["enforcement"])
    if tier == "standard":
        enforcement_data["context_summary_at"] = midpoint
    # micro tier leaves context_summary_at as None (from profile)

    # --- Normalize paths to git-root-relative ---
    feature_dir = git_root_relative(feature_dir)
    plan_file_rel = git_root_relative(plan_file)

    paths = ArtifactPaths(
        feature_dir=feature_dir,
        reports_dir=os.path.join(feature_dir, "reports"),
        dispatch_log=os.path.join(feature_dir, "reports", ".dispatch-log"),
        deviations_file=os.path.join(feature_dir, "deviations.md"),
    )

    # --- Build session model ---
    try:
        session = SddSession(
            schema_version=CURRENT_SCHEMA_VERSION,
            tier=tier,
            paths=paths,
            plan_file=plan_file_rel,
            active_module_id=active_module_id,
            active_module_file=active_module_file,
            task_range=task_range,
            total_tasks=total_tasks,
            midpoint=midpoint,
            enforcement=Enforcement.model_validate(enforcement_data),
            process_requirements=ProcessRequirements.model_validate(
                profile["process_requirements"]
            ),
            modules=modules,
        )
    except ValidationError as exc:
        print(f"Manifest validation failed:\n{exc}", file=sys.stderr)
        return 1

    # --- Idempotency: skip write if manifest matches ---
    manifest_path = Path(feature_dir) / ".sdd-session.json"
    new_data = json.loads(session.model_dump_json())

    if manifest_path.is_file():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = None

        if existing == new_data:
            print(f"Manifest up-to-date: {manifest_path}")
            return 0

        print(
            f"Manifest exists but differs from plan. Re-materializing: {manifest_path}",
            file=sys.stderr,
        )

    # --- Write ---
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        session.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    print(f"Manifest written: {manifest_path}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize SDD session manifest from plan frontmatter"
    )
    parser.add_argument(
        "--plan-file", required=True, help="Path to plan.md with YAML frontmatter"
    )
    parser.add_argument(
        "--feature-dir",
        required=True,
        help="Feature directory path (will be normalized to git-root-relative)",
    )
    args = parser.parse_args()
    sys.exit(materialize(args.plan_file, args.feature_dir))


if __name__ == "__main__":
    main()
