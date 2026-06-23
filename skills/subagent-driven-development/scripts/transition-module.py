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
from typing import List, Optional

# Add models to path (same pattern as materialize-manifest.py / controller-checkpoint.py)
sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))

from sdd_session import ModuleState, SddSession


def _find_module(modules: List[ModuleState], name_or_id: str) -> Optional[ModuleState]:
    """Locate a module by title or numeric id (string or int)."""
    for m in modules:
        if m.title == name_or_id or str(m.id) == name_or_id:
            return m
    return None


def _has_dispatch_provenance(dispatch_log_path: str, task_id: int, review_type: str) -> bool:
    """True if the live log has a `task=<id> type=<type>` line (mirrors hook Check 4c).

    Called at transition Step 1, before the Step 5 truncation — live log intact.
    """
    if not os.path.isfile(dispatch_log_path):
        return False
    needle = f"task={task_id} type={review_type}"
    try:
        with open(dispatch_log_path, encoding="utf-8") as fh:
            return any(needle in line for line in fh)
    except OSError:
        return False


def _verification_task_ids_from_file(plan_file: str) -> set:
    """task_type=='verification' IDs from a plan file's frontmatter.

    Mirrors controller-checkpoint.py:_verification_task_ids (single-file variant).
    """
    import yaml  # PyYAML available via the .venv python the hook/tests use

    if not os.path.isfile(plan_file):
        return set()
    try:
        content = Path(plan_file).read_text(encoding="utf-8")
    except OSError:
        return set()
    if not content.startswith("---"):
        return set()
    end = content.find("---", 3)
    if end == -1:
        return set()
    try:
        fm = yaml.safe_load(content[3:end])
    except Exception:
        return set()
    tasks = fm.get("tasks") if isinstance(fm, dict) else None
    if not isinstance(tasks, list):
        return set()
    return {
        t["id"]
        for t in tasks
        if isinstance(t, dict)
        and t.get("task_type") == "verification"
        and isinstance(t.get("id"), int)
    }


from _midpoint import compute_midpoint  # noqa: E402  (single source of truth)


def validate_module_completion(
    manifest: SddSession, module_name: str, git_root: str
) -> List[str]:
    """Check all tasks in the completed module have required reports."""
    errors: List[str] = []

    if manifest.modules is None:
        return [f"Module '{module_name}' not found in manifest"]

    module = _find_module(manifest.modules, module_name)
    if module is None:
        return [f"Module '{module_name}' not found in manifest"]

    reports_dir = os.path.join(git_root, manifest.paths.reports_dir)
    dispatch_log = os.path.join(git_root, manifest.paths.dispatch_log)
    pr = manifest.process_requirements

    # Per-task verification exemption (mirrors get_task_type's EFFECTIVE_PLAN_FILE
    # resolution in sdd-pre-dispatch-hook.sh): use the completing module's own
    # plan file only when module.file is set AND exists on disk (the hook's -n +
    # -f semantic); otherwise fall back to the main plan. N17/N19.
    module_plan = ""
    if module.file:
        module_plan = os.path.join(git_root, manifest.paths.feature_dir, module.file)
    if module_plan and os.path.isfile(module_plan):
        verif_ids = _verification_task_ids_from_file(module_plan)
    else:
        main_plan = os.path.join(git_root, manifest.plan_file)
        verif_ids = _verification_task_ids_from_file(main_plan)

    for task_id in module.task_ids:
        padded = f"{task_id:03d}"
        impl_report = os.path.join(reports_dir, f"task-{padded}-implementer-report.md")
        if not os.path.isfile(impl_report) or os.path.getsize(impl_report) < 50:
            errors.append(f"Task {task_id}: missing or empty implementer report")

        if task_id in verif_ids:
            continue  # verification task: implementer report only; no spec/quality/provenance

        if pr.spec_review_mode != "skip":
            spec_report = os.path.join(reports_dir, f"task-{padded}-spec-review.md")
            if not os.path.isfile(spec_report) or os.path.getsize(spec_report) < 50:
                errors.append(f"Task {task_id}: missing or empty spec review")
            elif manifest.enforcement.dispatch_provenance and not _has_dispatch_provenance(
                dispatch_log, task_id, "spec-review"
            ):
                errors.append(f"Task {task_id}: spec review not provenance-logged")

        if pr.quality_review_mode != "skip":
            quality_report = os.path.join(
                reports_dir, f"task-{padded}-quality-review.md"
            )
            quality_min = os.path.join(
                reports_dir, f"task-{padded}-quality-review-minimum-tier.md"
            )
            has_full = (
                os.path.isfile(quality_report) and os.path.getsize(quality_report) >= 50
            )
            has_min = (
                os.path.isfile(quality_min) and os.path.getsize(quality_min) >= 50
            )
            if not (has_full or has_min):
                errors.append(f"Task {task_id}: missing or empty quality review")
            elif has_min:
                pass  # file-based minimum signal waives quality-review provenance
            elif manifest.enforcement.dispatch_provenance and not _has_dispatch_provenance(
                dispatch_log, task_id, "quality-review"
            ):
                errors.append(f"Task {task_id}: quality review not provenance-logged")

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
    # N11: recompute context_summary_at for the new module's range. Without this
    # it stays pinned to the completed module's midpoint and Check 6b fires early
    # in later modules. Only when the tier uses it (non-null; micro leaves None).
    if data.get("enforcement", {}).get("context_summary_at") is not None:
        data["enforcement"]["context_summary_at"] = data["midpoint"]
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
