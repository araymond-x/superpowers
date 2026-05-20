#!/usr/bin/env python3
"""
transition-module.py

Manages module boundary lifecycle in multi-module SDD sessions.
Archives completed module's reports, updates manifest, resets dispatch log.

Exit codes:
  0 - Transition complete
  1 - Validation failure (missing reports, module not found)
  2 - Script error (bad arguments, manifest not found)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add models to path (same pattern as materialize-manifest.py / controller-checkpoint.py)
sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))

from sdd_session import ModuleState, SddSession


def _find_module(modules: list[ModuleState], name_or_id: str) -> ModuleState | None:
    """Locate a module by title or numeric id (string or int)."""
    for m in modules:
        if m.title == name_or_id or str(m.id) == name_or_id:
            return m
    return None


def compute_midpoint(start: int, end: int) -> int:
    """Compute the midpoint of a task range.

    Matches Module 1's authoritative formula in materialize-manifest.py.
    Formula: start + (range_size + 1) // 2, where range_size = end - start.
    This gives a ceiling-biased midpoint that stays inside [start, end] for
    all range sizes (including single-task and two-task ranges).
    """
    range_size = end - start
    return start + (range_size + 1) // 2


def validate_module_completion(
    manifest: SddSession, module_name: str, git_root: str
) -> list[str]:
    """Check all tasks in the completed module have required reports."""
    errors: list[str] = []

    if manifest.modules is None:
        return [f"Module '{module_name}' not found in manifest"]

    module = _find_module(manifest.modules, module_name)
    if module is None:
        return [f"Module '{module_name}' not found in manifest"]

    reports_dir = os.path.join(git_root, manifest.paths.reports_dir)
    pr = manifest.process_requirements

    for task_id in module.task_ids:
        padded = f"{task_id:03d}"
        impl_report = os.path.join(reports_dir, f"task-{padded}-implementer-report.md")
        if not os.path.isfile(impl_report) or os.path.getsize(impl_report) < 50:
            errors.append(f"Task {task_id}: missing or empty implementer report")

        if pr.spec_review_mode != "skip":
            spec_report = os.path.join(reports_dir, f"task-{padded}-spec-review.md")
            if not os.path.isfile(spec_report) or os.path.getsize(spec_report) < 50:
                errors.append(f"Task {task_id}: missing or empty spec review")

        if pr.quality_review_mode != "skip":
            quality_report = os.path.join(reports_dir, f"task-{padded}-quality-review.md")
            quality_min = os.path.join(
                reports_dir, f"task-{padded}-quality-review-minimum-tier.md"
            )
            has_quality = (
                (os.path.isfile(quality_report) and os.path.getsize(quality_report) >= 50)
                or (os.path.isfile(quality_min) and os.path.getsize(quality_min) >= 50)
            )
            if not has_quality:
                errors.append(f"Task {task_id}: missing or empty quality review")

    return errors


def transition(manifest_path: str, completed_module: str, next_module: str) -> int:
    """Validate, archive, and update manifest for a module boundary transition."""
    manifest_file = Path(manifest_path)
    if not manifest_file.is_file():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Cannot parse manifest {manifest_path}: {exc}", file=sys.stderr)
        return 2

    try:
        manifest = SddSession.model_validate(data)
    except Exception as exc:  # ValidationError or otherwise
        print(f"Manifest failed validation: {exc}", file=sys.stderr)
        return 1

    if manifest.modules is None:
        print("Not a multi-module plan — no modules in manifest", file=sys.stderr)
        return 1

    # Determine git root from the manifest file's directory
    git_result = subprocess.run(
        ["git", "-C", str(manifest_file.parent), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if git_result.returncode != 0:
        print(f"Cannot determine git root from {manifest_path}", file=sys.stderr)
        return 2
    git_root = git_result.stdout.strip()

    # Step 1: Validate completion of the just-finished module
    errors = validate_module_completion(manifest, completed_module, git_root)
    if errors:
        for e in errors:
            print(f"INCOMPLETE: {e}", file=sys.stderr)
        return 1

    # Step 2: Find next module
    next_mod = _find_module(manifest.modules, next_module)
    if next_mod is None:
        print(f"Next module '{next_module}' not found in manifest", file=sys.stderr)
        return 1

    completed_mod = _find_module(manifest.modules, completed_module)
    if completed_mod is None:
        # Should not happen — validate_module_completion already checked, but be safe
        print(
            f"Completed module '{completed_module}' not found in manifest",
            file=sys.stderr,
        )
        return 1

    reports_dir = os.path.join(git_root, manifest.paths.reports_dir)
    archive_dir = os.path.join(reports_dir, f"archive-{completed_module}")

    # Step 3: Archive reports for the completed module
    os.makedirs(archive_dir, exist_ok=True)
    for task_id in completed_mod.task_ids:
        padded = f"{task_id:03d}"
        for f in Path(reports_dir).glob(f"task-{padded}-*"):
            shutil.move(str(f), os.path.join(archive_dir, f.name))

    # Step 4: Update manifest fields for the next module
    # NOTE: midpoint formula matches Module 1's authoritative compute_midpoint
    # (range_size = end - start, NOT end - start + 1). Plan reference code was
    # buggy — see deviations.md Tasks 4, 11, 12.
    data["active_module_id"] = next_mod.id
    data["active_module_file"] = next_mod.file
    data["task_range"] = [next_mod.task_ids[0], next_mod.task_ids[-1]]
    data["midpoint"] = compute_midpoint(next_mod.task_ids[0], next_mod.task_ids[-1])
    if completed_module not in data.get("completed_modules", []):
        data.setdefault("completed_modules", []).append(completed_module)
    data["module_reports_archived"] = True

    manifest_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # Step 5: Archive dispatch log and truncate live copy
    dispatch_log = os.path.join(git_root, manifest.paths.dispatch_log)
    if os.path.isfile(dispatch_log):
        shutil.copy2(dispatch_log, os.path.join(archive_dir, ".dispatch-log"))
        open(dispatch_log, "w").close()  # truncate to empty

    # Step 6: Log transition to deviations file
    deviations_file = os.path.join(git_root, manifest.paths.deviations_file)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(deviations_file, "a", encoding="utf-8") as f:
        f.write(
            f"\n| {timestamp} | Module transition: "
            f"{completed_module} → {next_module} | FYI | Accepted |\n"
        )

    print(f"Transition complete: {completed_module} → {next_module}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage SDD module transitions")
    parser.add_argument("--manifest", required=True, help="Path to .sdd-session.json")
    parser.add_argument(
        "--completed-module", required=True, help="Name or ID of completed module"
    )
    parser.add_argument(
        "--next-module", required=True, help="Name or ID of next module"
    )
    args = parser.parse_args()
    sys.exit(transition(args.manifest, args.completed_module, args.next_module))


if __name__ == "__main__":
    main()
