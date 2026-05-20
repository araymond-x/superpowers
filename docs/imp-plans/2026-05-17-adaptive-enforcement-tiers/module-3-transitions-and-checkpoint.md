---
schema_version: 1
feature_archetype: refactor
# enforcement_tier: standard — added by this plan's own Task 3
source_contracts: null
shared_constants:
  - path: "skills.scripts.models.sdd_session.TIER_PROFILES"
    value: "dict mapping tier name to enforcement + process_requirements"
    reason: "Transition script validates report requirements against tier profile"
pattern_references:
  - name: "checkpoint-result-model"
    source_files: ["skills/scripts/models/checkpoint_result.py"]
    reason: "CheckpointResult model pattern for --manifest argument handling"
tasks:
  - id: 12
    title: "Transition-module script"
  - id: 13
    title: "Transition-module tests"
    depends_on: [12]
  - id: 14
    title: "Controller checkpoint --manifest support"
    pattern_references: ["checkpoint-result-model"]
  - id: 15
    title: "Controller checkpoint tests"
    depends_on: [14]
---

# Module 3: Module Transitions and Controller Checkpoint

**Goal:** Create `transition-module.py` for module boundary lifecycle and add `--manifest` argument to `controller-checkpoint.py`.

**Source Contracts:** None

**Reference spec:** `spec-distilled.md` §Module Transition Script, §Controller Checkpoint (contract verification in Module 1 Task 0)

**Contract Constraints:**
- `transition-module.py`: validates completion, archives reports, updates manifest, archives dispatch log, logs to deviations
- Exit codes: 0 (complete), 1 (validation failure), 2 (script error)
- `controller-checkpoint.py --manifest`: reads plan_file, enforcement, task_range, midpoint from manifest
- When manifest absent, falls back to `--plan-file` (backward compatible)
- Micro tier: skip honesty check and trace audit in pre-completion phase

**Pattern References:**
- `skills/scripts/models/checkpoint_result.py` — `CheckpointResult` model, argparse pattern

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `skills/subagent-driven-development/scripts/transition-module.py` | Create | Module boundary lifecycle |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Modify | Add `--manifest` argument, read from manifest |
| `tests/unit/test_transition_module.py` | Create | Transition script tests |
| `tests/unit/test_controller_checkpoint_stale.py` | Extend | Manifest-mode checkpoint tests |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 12 | `skills/subagent-driven-development/scripts/transition-module.py` | `skills/scripts/models/sdd_session.py` | Module 1 |
| Task 13 | `tests/unit/test_transition_module.py` | `transition-module.py` | Task 12 |
| Task 14 | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | `skills/scripts/models/sdd_session.py` | Module 1 |
| Task 15 | `tests/unit/test_controller_checkpoint_stale.py` | `controller-checkpoint.py` | Task 14 |

## Acceptance Criteria

- [ ] `transition-module.py` validates module completion before allowing transition
- [ ] Reports archived to `reports/archive-{module-name}/`
- [ ] Manifest updated with new active module, task range, midpoint
- [ ] Dispatch log archived and truncated
- [ ] Module transition logged to deviations.md
- [ ] `controller-checkpoint.py --manifest` reads from manifest
- [ ] Micro tier skips honesty check and trace audit in pre-completion
- [ ] Backward compatible: `--plan-file` without `--manifest` works unchanged

---

### Task 12: Transition-Module Script

**Files:**
- Create: `skills/subagent-driven-development/scripts/transition-module.py`

- [x] **Step 1: Write the script**

```python
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

sys.path.insert(0, str(Path(__file__).resolve().parent / "../../scripts/models"))

from sdd_session import SddSession


def validate_module_completion(manifest: SddSession, module_name: str, git_root: str) -> list[str]:
    """Check all tasks in the completed module have required reports."""
    errors = []
    module = None
    for m in (manifest.modules or []):
        if m.title == module_name or str(m.id) == module_name:
            module = m
            break

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
            quality_min = os.path.join(reports_dir, f"task-{padded}-quality-review-minimum-tier.md")
            has_quality = (
                (os.path.isfile(quality_report) and os.path.getsize(quality_report) >= 50)
                or (os.path.isfile(quality_min) and os.path.getsize(quality_min) >= 50)
            )
            if not has_quality:
                errors.append(f"Task {task_id}: missing or empty quality review")

    return errors


def transition(manifest_path: str, completed_module: str, next_module: str) -> int:
    manifest_file = Path(manifest_path)
    if not manifest_file.is_file():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest = SddSession.model_validate(data)

    if manifest.modules is None:
        print("Not a multi-module plan — no modules in manifest", file=sys.stderr)
        return 1

    # Determine git root robustly
    git_result = subprocess.run(
        ["git", "-C", str(manifest_file.parent), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if git_result.returncode != 0:
        print(f"Cannot determine git root from {manifest_path}", file=sys.stderr)
        return 2
    git_root = git_result.stdout.strip()

    # Step 1: Validate completion
    errors = validate_module_completion(manifest, completed_module, git_root)
    if errors:
        for e in errors:
            print(f"INCOMPLETE: {e}", file=sys.stderr)
        return 1

    # Step 2: Find next module
    next_mod = None
    for m in manifest.modules:
        if m.title == next_module or str(m.id) == next_module:
            next_mod = m
            break
    if next_mod is None:
        print(f"Next module '{next_module}' not found in manifest", file=sys.stderr)
        return 1

    reports_dir = os.path.join(git_root, manifest.paths.reports_dir)
    archive_dir = os.path.join(reports_dir, f"archive-{completed_module}")

    # Step 3: Archive reports
    os.makedirs(archive_dir, exist_ok=True)
    completed_mod = None
    for m in manifest.modules:
        if m.title == completed_module or str(m.id) == completed_module:
            completed_mod = m
            break

    for task_id in completed_mod.task_ids:
        padded = f"{task_id:03d}"
        for f in Path(reports_dir).glob(f"task-{padded}-*"):
            shutil.move(str(f), os.path.join(archive_dir, f.name))

    # Step 4: Update manifest
    data["active_module_id"] = next_mod.id
    data["active_module_file"] = next_mod.file
    data["task_range"] = [next_mod.task_ids[0], next_mod.task_ids[-1]]
    range_size = next_mod.task_ids[-1] - next_mod.task_ids[0] + 1
    data["midpoint"] = next_mod.task_ids[0] + (range_size + 1) // 2
    if completed_module not in data.get("completed_modules", []):
        data.setdefault("completed_modules", []).append(completed_module)
    data["module_reports_archived"] = True

    manifest_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # Step 5: Archive dispatch log
    dispatch_log = os.path.join(git_root, manifest.paths.dispatch_log)
    if os.path.isfile(dispatch_log):
        shutil.copy2(dispatch_log, os.path.join(archive_dir, ".dispatch-log"))
        open(dispatch_log, "w").close()  # truncate to empty

    # Step 6: Log transition to deviations
    deviations_file = os.path.join(git_root, manifest.paths.deviations_file)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(deviations_file, "a", encoding="utf-8") as f:
        f.write(f"\n| {timestamp} | Module transition: {completed_module} → {next_module} | FYI | Accepted |\n")

    print(f"Transition complete: {completed_module} → {next_module}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Manage SDD module transitions")
    parser.add_argument("--manifest", required=True, help="Path to .sdd-session.json")
    parser.add_argument("--completed-module", required=True, help="Name or ID of completed module")
    parser.add_argument("--next-module", required=True, help="Name or ID of next module")
    args = parser.parse_args()
    sys.exit(transition(args.manifest, args.completed_module, args.next_module))


if __name__ == "__main__":
    main()
```

- [x] **Step 2: Make executable**

```bash
chmod +x skills/subagent-driven-development/scripts/transition-module.py
```

- [x] **Step 3: Commit**

```bash
git add skills/subagent-driven-development/scripts/transition-module.py
git commit -m "feat: add transition-module.py for multi-module SDD lifecycle"
```

---

### Task 13: Transition-Module Tests

**Files:**
- Create: `tests/unit/test_transition_module.py`

- [x] **Step 1: Write tests**

```python
"""Tests for transition-module.py."""
import json
import os
import subprocess
import sys
import tempfile

import pytest

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "skills",
    "subagent-driven-development",
    "scripts",
    "transition-module.py",
)

PYTHON = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    ".venv",
    "bin",
    "python3",
)

# Import helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "skills", "scripts", "models"))
from sdd_session import TIER_PROFILES


def create_manifest(tmp_path, tier="standard"):
    feat_dir = tmp_path / "docs" / "imp-plans" / "test-feature"
    feat_dir.mkdir(parents=True)
    reports_dir = feat_dir / "reports"
    reports_dir.mkdir()
    (feat_dir / "deviations.md").write_text("# Deviations\n")

    profile = TIER_PROFILES[tier]
    manifest = {
        "schema_version": 1,
        "tier": tier,
        "paths": {
            "feature_dir": str(feat_dir.relative_to(tmp_path)),
            "reports_dir": str(reports_dir.relative_to(tmp_path)),
            "dispatch_log": str((reports_dir / ".dispatch-log").relative_to(tmp_path)),
            "deviations_file": str((feat_dir / "deviations.md").relative_to(tmp_path)),
        },
        "plan_file": str((feat_dir / "plan.md").relative_to(tmp_path)),
        "active_module_id": 1,
        "active_module_file": "m1.md",
        "task_range": [0, 3],
        "total_tasks": 8,
        "midpoint": 2,
        "enforcement": profile["enforcement"],
        "process_requirements": profile["process_requirements"],
        "completed_modules": [],
        "module_reports_archived": False,
        "modules": [
            {"id": 1, "title": "Core", "file": "m1.md", "task_ids": [0, 1, 2, 3]},
            {"id": 2, "title": "API", "file": "m2.md", "task_ids": [4, 5, 6, 7]},
        ],
        "dispatch_log_sentinel": False,
    }

    manifest_path = feat_dir / ".sdd-session.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Create dispatch log
    (reports_dir / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")

    return manifest_path, reports_dir, feat_dir


def create_task_reports(reports_dir, task_ids):
    """Create implementer, spec-review, and quality-review reports for given tasks."""
    for tid in task_ids:
        padded = f"{tid:03d}"
        for report_type in ["implementer-report", "spec-review", "quality-review"]:
            path = reports_dir / f"task-{padded}-{report_type}.md"
            path.write_text(f"# {report_type} for task {tid}\n" + "x" * 100)


def run_transition(manifest_path, completed, next_mod):
    result = subprocess.run(
        [PYTHON, SCRIPT_PATH, "--manifest", str(manifest_path),
         "--completed-module", completed, "--next-module", next_mod],
        capture_output=True, text=True, timeout=10,
    )
    return result


class TestTransitionModule:
    def test_successful_transition(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        result = run_transition(manifest_path, "Core", "API")
        assert result.returncode == 0
        assert "Transition complete" in result.stdout

    def test_manifest_updated_after_transition(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        run_transition(manifest_path, "Core", "API")
        updated = json.loads(manifest_path.read_text())
        assert updated["active_module_id"] == 2
        assert updated["task_range"] == [4, 7]
        assert "Core" in updated["completed_modules"]

    def test_reports_archived(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        run_transition(manifest_path, "Core", "API")
        archive = reports_dir / "archive-Core"
        assert archive.is_dir()
        assert (archive / "task-000-implementer-report.md").is_file()

    def test_dispatch_log_archived_and_truncated(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        run_transition(manifest_path, "Core", "API")
        archive = reports_dir / "archive-Core"
        assert (archive / ".dispatch-log").is_file()
        assert (reports_dir / ".dispatch-log").read_text() == ""

    def test_blocks_when_reports_missing(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        # Don't create reports
        result = run_transition(manifest_path, "Core", "API")
        assert result.returncode == 1
        assert "INCOMPLETE" in result.stderr

    def test_rejects_single_module_plan(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        # Remove modules from manifest
        data = json.loads(manifest_path.read_text())
        data["modules"] = None
        manifest_path.write_text(json.dumps(data))
        result = run_transition(manifest_path, "Core", "API")
        assert result.returncode == 1

    def test_deviations_log_updated(self, tmp_path):
        manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
        create_task_reports(reports_dir, [0, 1, 2, 3])
        run_transition(manifest_path, "Core", "API")
        devs = (feat_dir / "deviations.md").read_text()
        assert "Module transition" in devs
```

- [x] **Step 2: Run tests**

```bash
.venv/bin/python3 -m pytest tests/unit/test_transition_module.py -v
```

Expected: All tests PASS

- [x] **Step 3: Commit**

```bash
git add tests/unit/test_transition_module.py
git commit -m "test: add transition-module.py unit tests"
```

---

### Task 14: Controller Checkpoint --manifest Support

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py`

- [x] **Step 1: Add --manifest argument to argparse**

In the `main()` function's argument parser, add:

```python
parser.add_argument(
    "--manifest",
    type=str,
    default=None,
    help="Path to .sdd-session.json. When provided, reads plan_file, enforcement, "
         "task_range, and midpoint from manifest instead of command-line arguments.",
)
```

- [x] **Step 2: Add manifest reading at the top of each phase function**

In the pre-execution, pre-dispatch, and pre-completion phase handlers, add manifest override logic:

```python
# At the top of run_pre_dispatch (and similar for other phases):
if args.manifest:
    manifest_data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    # Override plan_file from manifest
    git_root = str(Path(args.manifest).resolve().parent.parent.parent)
    args.plan_file = os.path.join(git_root, manifest_data["plan_file"])
    if manifest_data.get("active_module_file"):
        args.plan_file = os.path.join(git_root, manifest_data["active_module_file"])
    # Read enforcement flags
    enforcement = manifest_data.get("enforcement", {})
    tier = manifest_data.get("tier", "standard")
```

- [x] **Step 3: Gate pre-completion checks by tier**

In the pre-completion phase, add tier-based gating:

```python
if tier == "micro":
    # Skip honesty check and trace audit for micro tier
    checks["honesty_check"] = CheckResult(status="SKIP", detail="Micro tier — honesty check skipped")
    checks["trace_audit"] = CheckResult(status="SKIP", detail="Micro tier — trace audit skipped")
else:
    # (existing honesty check and trace audit code)
```

- [x] **Step 4: Run existing checkpoint tests**

```bash
.venv/bin/python3 -m pytest tests/unit/test_controller_checkpoint_stale.py tests/unit/test_pre_completion_gates.py -v
```

Expected: All existing tests PASS

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py
git commit -m "feat: add --manifest support to controller-checkpoint.py"
```

---

### Task 15: Controller Checkpoint Tests

**Files:**
- Extend: `tests/unit/test_controller_checkpoint_stale.py`

- [ ] **Step 1: Add manifest-mode tests**

```python
import json
import os
import subprocess
import sys

import pytest

CHECKPOINT_SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "controller-checkpoint.py",
)
PYTHON = os.path.join(os.path.dirname(__file__), "..", "..", ".venv", "bin", "python3")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "skills", "scripts", "models"))
from sdd_session import TIER_PROFILES


def setup_checkpoint_workspace(tmp_path, tier="standard"):
    """Create a workspace with manifest, plan, deviations, and reports for checkpoint testing."""
    feat_dir = tmp_path / "docs" / "imp-plans" / "test-feature"
    feat_dir.mkdir(parents=True)
    reports_dir = feat_dir / "reports"
    reports_dir.mkdir()

    plan_content = "# Plan\n\n### Task 0: Setup\n- [x] Done\n\n### Task 1: Build\n- [x] Done\n"
    (feat_dir / "plan.md").write_text(plan_content)
    (feat_dir / "deviations.md").write_text("# Deviations\n")

    profile = TIER_PROFILES[tier]
    manifest = {
        "schema_version": 1,
        "tier": tier,
        "paths": {
            "feature_dir": str(feat_dir.relative_to(tmp_path)),
            "reports_dir": str(reports_dir.relative_to(tmp_path)),
            "dispatch_log": str((reports_dir / ".dispatch-log").relative_to(tmp_path)),
            "deviations_file": str((feat_dir / "deviations.md").relative_to(tmp_path)),
        },
        "plan_file": str((feat_dir / "plan.md").relative_to(tmp_path)),
        "active_module_id": None,
        "active_module_file": None,
        "task_range": [0, 1],
        "total_tasks": 2,
        "midpoint": 1,
        "enforcement": profile["enforcement"],
        "process_requirements": profile["process_requirements"],
        "completed_modules": [],
        "module_reports_archived": False,
        "modules": None,
        "dispatch_log_sentinel": False,
    }
    manifest_path = feat_dir / ".sdd-session.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return {"manifest_path": manifest_path, "feat_dir": feat_dir, "reports_dir": reports_dir}


def run_checkpoint(phase, manifest_path=None, plan_file=None, task_number=None,
                   deviations_file=None, reports_dir=None):
    cmd = [PYTHON, CHECKPOINT_SCRIPT, "--phase", phase]
    if manifest_path:
        cmd.extend(["--manifest", str(manifest_path)])
    if plan_file:
        cmd.extend(["--plan-file", str(plan_file)])
    if task_number is not None:
        cmd.extend(["--task-number", str(task_number)])
    if deviations_file:
        cmd.extend(["--deviations-file", str(deviations_file)])
    if reports_dir:
        cmd.extend(["--reports-dir", str(reports_dir)])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    output = json.loads(result.stdout) if result.stdout.strip() else {}
    return {"exit_code": result.returncode, "output": output, "stderr": result.stderr}


class TestManifestMode:
    """Tests for --manifest argument."""

    def test_manifest_overrides_plan_file(self, tmp_path):
        """When --manifest is provided, plan_file comes from manifest."""
        ws = setup_checkpoint_workspace(tmp_path)
        result = run_checkpoint(
            "pre-execution",
            manifest_path=ws["manifest_path"],
            deviations_file=str(ws["feat_dir"] / "deviations.md"),
            reports_dir=str(ws["reports_dir"]),
        )
        # Should not error about missing plan file — manifest provides it
        assert result["exit_code"] != 3, f"Script error: {result['stderr']}"

    def test_micro_tier_skips_honesty_check(self, tmp_path):
        """Pre-completion with micro tier should SKIP honesty check."""
        ws = setup_checkpoint_workspace(tmp_path, tier="micro")
        result = run_checkpoint(
            "pre-completion",
            manifest_path=ws["manifest_path"],
            deviations_file=str(ws["feat_dir"] / "deviations.md"),
            reports_dir=str(ws["reports_dir"]),
        )
        checks = result["output"].get("checks", {})
        honesty = checks.get("honesty_check", {})
        assert honesty.get("status") == "SKIP", f"Expected SKIP, got {honesty}"

    def test_backward_compat_without_manifest(self, tmp_path):
        """When --manifest absent, --plan-file works as before."""
        ws = setup_checkpoint_workspace(tmp_path)
        result = run_checkpoint(
            "pre-execution",
            plan_file=str(ws["feat_dir"] / "plan.md"),
            deviations_file=str(ws["feat_dir"] / "deviations.md"),
            reports_dir=str(ws["reports_dir"]),
        )
        assert result["exit_code"] != 3, f"Script error: {result['stderr']}"
```

- [ ] **Step 2: Run tests**

```bash
.venv/bin/python3 -m pytest tests/unit/test_controller_checkpoint_stale.py -v
```

Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_controller_checkpoint_stale.py
git commit -m "test: add controller-checkpoint manifest-mode tests"
```
