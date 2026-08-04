#!/usr/bin/env python3
"""
Unit tests for materialize-manifest.py — plan frontmatter to .sdd-session.json.

Tests cover:
  - Standard and micro tier manifest generation
  - Default tier fallback when enforcement_tier is absent
  - Invalid tier rejection
  - Midpoint computation
  - Git-root-relative path normalization
  - Idempotent re-runs
  - Multi-module active_module_id assignment

Run: .venv/bin/python3 -m pytest tests/unit/test_materialize_manifest.py -v
"""

import json
import os
import shutil
import subprocess
import tempfile

# Absolute path to script under test
SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "skills",
    "subagent-driven-development",
    "scripts",
    "materialize-manifest.py",
)

# Use venv python so PyYAML/Pydantic are available
PYTHON = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    ".venv",
    "bin",
    "python3",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_plan(
    tier: str = "standard",
    tasks: list[dict] | None = None,
    modules: list[dict] | None = None,
    omit_tier: bool = False,
    extra_frontmatter: str | None = None,
) -> str:
    """Generate plan text with YAML frontmatter.

    Args:
        tier: Enforcement tier value.
        tasks: List of task dicts with 'id' keys. Defaults to 5 tasks (0-4).
        modules: Optional list of module dicts for multi-module plans.
        omit_tier: If True, exclude enforcement_tier from frontmatter entirely.
        extra_frontmatter: Optional raw YAML line(s) injected into the
            frontmatter (e.g. ``handoff_spawn: ask``).

    Returns:
        Plan markdown with YAML frontmatter.
    """
    if tasks is None:
        tasks = [{"id": i} for i in range(5)]

    lines = ["---"]
    if not omit_tier:
        lines.append(f"enforcement_tier: {tier}")
    if extra_frontmatter:
        lines.append(extra_frontmatter)
    lines.append("tasks:")
    for t in tasks:
        lines.append(f"  - id: {t['id']}")
    if modules:
        lines.append("modules:")
        for m in modules:
            lines.append(f"  - id: {m['id']}")
            lines.append(f"    title: \"{m['title']}\"")
            lines.append(f"    file: \"{m['file']}\"")
            task_ids_str = ", ".join(str(tid) for tid in m["task_ids"])
            lines.append(f"    task_ids: [{task_ids_str}]")
    lines.append("---")
    lines.append("")
    lines.append("# Implementation Plan")
    lines.append("")
    for t in tasks:
        lines.append(f"### Task {t['id']} — Task {t['id']} work")
        lines.append(f"- [ ] Do task {t['id']}")
        lines.append("")

    return "\n".join(lines)


def run_materialize(
    plan_content: str,
    feature_dir: str = "feature",
    tmp_dir: str | None = None,
) -> dict:
    """Write plan to a temp dir, run materialize-manifest.py, return results.

    Args:
        plan_content: Full plan markdown text with frontmatter.
        feature_dir: Relative feature directory name.
        tmp_dir: If provided, reuse this directory (for idempotency tests).

    Returns:
        Dict with exit_code, manifest (parsed JSON or None), stdout, stderr,
        and tmp_dir (for reuse in subsequent calls).
    """
    cleanup = tmp_dir is None
    if tmp_dir is None:
        tmp_dir = tempfile.mkdtemp()

    plan_path = os.path.join(tmp_dir, "plan.md")
    with open(plan_path, "w") as f:
        f.write(plan_content)

    try:
        result = subprocess.run(
            [
                PYTHON,
                SCRIPT_PATH,
                "--plan-file",
                "plan.md",
                "--feature-dir",
                feature_dir,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=tmp_dir,
        )

        manifest = None
        manifest_path = os.path.join(tmp_dir, feature_dir, ".sdd-session.json")
        if os.path.isfile(manifest_path):
            with open(manifest_path) as mf:
                manifest = json.load(mf)

        return {
            "exit_code": result.returncode,
            "manifest": manifest,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "tmp_dir": tmp_dir,
        }
    finally:
        if cleanup:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Tests: Standard manifest generation
# ---------------------------------------------------------------------------


class TestManifestWriter:
    """Core manifest generation from plan frontmatter."""

    def test_standard_tier_produces_manifest(self):
        """Standard tier plan produces manifest with tier='standard' and enforcement flags."""
        plan = make_plan(tier="standard")
        tmp_dir = tempfile.mkdtemp()
        try:
            r = run_materialize(plan, tmp_dir=tmp_dir)
            assert r["exit_code"] == 0, f"Expected success, got {r['exit_code']}: {r['stderr']}"
            assert r["manifest"] is not None, "Manifest file was not written"
            assert r["manifest"]["tier"] == "standard"
            assert r["manifest"]["enforcement"]["pre_execution_audit"] is True
            assert r["manifest"]["enforcement"]["partner_review"] is True
            assert r["manifest"]["enforcement"]["dispatch_provenance"] is True
            assert r["manifest"]["enforcement"]["checkpoint_files"] is True
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_micro_tier_produces_manifest(self):
        """Micro tier disables pre_execution_audit and other enforcement flags."""
        plan = make_plan(tier="micro")
        tmp_dir = tempfile.mkdtemp()
        try:
            r = run_materialize(plan, tmp_dir=tmp_dir)
            assert r["exit_code"] == 0, f"Expected success, got {r['exit_code']}: {r['stderr']}"
            assert r["manifest"] is not None
            assert r["manifest"]["tier"] == "micro"
            assert r["manifest"]["enforcement"]["pre_execution_audit"] is False
            assert r["manifest"]["enforcement"]["partner_review"] is False
            assert r["manifest"]["enforcement"]["dispatch_provenance"] is False
            assert r["manifest"]["enforcement"]["context_summary_at"] is None
            assert r["manifest"]["enforcement"]["checkpoint_files"] is False
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_default_tier_is_standard(self):
        """Plan without enforcement_tier line defaults to standard."""
        plan = make_plan(omit_tier=True)
        tmp_dir = tempfile.mkdtemp()
        try:
            r = run_materialize(plan, tmp_dir=tmp_dir)
            assert r["exit_code"] == 0, f"Expected success, got {r['exit_code']}: {r['stderr']}"
            assert r["manifest"] is not None
            assert r["manifest"]["tier"] == "standard"
            assert r["manifest"]["enforcement"]["pre_execution_audit"] is True
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_invalid_tier_fails(self):
        """Unrecognized tier value ('comprehensive') is rejected with exit code 1."""
        plan = make_plan(tier="comprehensive")
        r = run_materialize(plan)
        assert r["exit_code"] == 1, f"Expected exit 1 for invalid tier, got {r['exit_code']}"
        assert "comprehensive" in r["stderr"]

    def test_midpoint_computation(self):
        """10 tasks (0-9) produce midpoint = 5 per ceiling-biased formula."""
        tasks = [{"id": i} for i in range(10)]
        plan = make_plan(tier="standard", tasks=tasks)
        tmp_dir = tempfile.mkdtemp()
        try:
            r = run_materialize(plan, tmp_dir=tmp_dir)
            assert r["exit_code"] == 0, f"Expected success: {r['stderr']}"
            assert r["manifest"] is not None
            # task_range = (0, 9), midpoint = 0 + (9 - 0 + 1) // 2 = 5
            assert r["manifest"]["midpoint"] == 5
            assert r["manifest"]["task_range"] == [0, 9]
            assert r["manifest"]["total_tasks"] == 10
            # Standard tier sets context_summary_at to midpoint
            assert r["manifest"]["enforcement"]["context_summary_at"] == 5
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_paths_are_git_root_relative(self):
        """Relative feature_dir passes through to manifest paths."""
        plan = make_plan(tier="standard")
        feature_dir = "docs/imp-plans/test"
        tmp_dir = tempfile.mkdtemp()
        try:
            r = run_materialize(plan, feature_dir=feature_dir, tmp_dir=tmp_dir)
            assert r["exit_code"] == 0, f"Expected success: {r['stderr']}"
            assert r["manifest"] is not None
            paths = r["manifest"]["paths"]
            assert paths["feature_dir"] == "docs/imp-plans/test"
            assert paths["reports_dir"] == "docs/imp-plans/test/reports"
            assert paths["dispatch_log"] == "docs/imp-plans/test/reports/.dispatch-log"
            assert paths["deviations_file"] == "docs/imp-plans/test/deviations.md"
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_idempotent_rerun(self):
        """Running twice with the same plan prints 'up-to-date' on second run."""
        plan = make_plan(tier="standard")
        tmp_dir = tempfile.mkdtemp()
        try:
            # First run: writes manifest
            r1 = run_materialize(plan, tmp_dir=tmp_dir)
            assert r1["exit_code"] == 0, f"First run failed: {r1['stderr']}"
            assert r1["manifest"] is not None
            assert "Manifest written" in r1["stdout"]

            # Second run: same plan, same dir — should detect up-to-date
            r2 = run_materialize(plan, tmp_dir=tmp_dir)
            assert r2["exit_code"] == 0, f"Second run failed: {r2['stderr']}"
            assert "up-to-date" in r2["stdout"]
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Tests: Multi-module plans
# ---------------------------------------------------------------------------


class TestMultiModuleManifest:
    """Plans with modules set active_module_id from the first module."""

    def test_multi_module_sets_active_module(self):
        """Plan with modules sets active_module_id to the first module's id."""
        modules = [
            {
                "id": 1,
                "title": "Core Service",
                "file": "module-1-core.md",
                "task_ids": [0, 1, 2, 3],
            },
            {
                "id": 2,
                "title": "API Layer",
                "file": "module-2-api.md",
                "task_ids": [4, 5, 6],
            },
        ]
        # tasks must include all task ids across modules
        tasks = [{"id": i} for i in range(7)]
        plan = make_plan(tier="standard", tasks=tasks, modules=modules)
        tmp_dir = tempfile.mkdtemp()
        try:
            r = run_materialize(plan, tmp_dir=tmp_dir)
            assert r["exit_code"] == 0, f"Expected success: {r['stderr']}"
            assert r["manifest"] is not None
            assert r["manifest"]["active_module_id"] == 1
            assert r["manifest"]["active_module_file"] == "module-1-core.md"
            # task_range should be from first module's tasks
            assert r["manifest"]["task_range"] == [0, 3]
            # modules list preserved
            assert len(r["manifest"]["modules"]) == 2
            assert r["manifest"]["modules"][0]["id"] == 1
            assert r["manifest"]["modules"][1]["id"] == 2
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Tests: handoff block materialization (cmux-spawn-v2)
# ---------------------------------------------------------------------------


class TestHandoffBlockMaterialization:
    def _mf(self, ok=True, **kw):            # make_plan + run_materialize + cleanup
        tmp = tempfile.mkdtemp()
        try:
            r = run_materialize(make_plan(**kw), tmp_dir=tmp)
            assert (r["exit_code"] == 0) is ok, r["stderr"]
            return r["manifest"] if ok else r
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_manifest_gains_handoff_block(self):      # default 5 tasks, standard
        assert self._mf()["handoff"] == {"expected_hops": 2, "spawn_policy": "auto"}

    def test_spawn_policy_copied_from_plan(self):
        assert self._mf(extra_frontmatter="handoff_spawn: ask")["handoff"]["spawn_policy"] == "ask"

    def test_micro_tier_expected_hops_is_one(self):   # default 5 tasks: micro=1 vs standard=2
        assert self._mf(tier="micro")["handoff"]["expected_hops"] == 1

    def test_bare_off_coerces_to_off_policy(self):   # N83: YAML 1.1 unquoted off (False) -> "off"
        # quoted "off" already worked
        assert self._mf(extra_frontmatter='handoff_spawn: "off"')["handoff"]["spawn_policy"] == "off"
        # unquoted off (parsed False) now normalizes to "off" instead of failing
        assert self._mf(extra_frontmatter="handoff_spawn: off")["handoff"]["spawn_policy"] == "off"
