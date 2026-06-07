"""N9: _task_ids_where + _load_all_plan_contents helpers.
Run: .venv/bin/python3 -m pytest tests/unit/test_n9_plan_loading_helpers.py -v
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT_PATH = os.path.join(
    ROOT, "skills", "subagent-driven-development", "scripts", "controller-checkpoint.py"
)


def _load_checkpoint():
    spec = importlib.util.spec_from_file_location("controller_checkpoint", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ckpt = _load_checkpoint()


PLAN_WITH_MIN = """---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 1
    title: "Task one"
    review_tier: minimum
  - id: 2
    title: "Task two"
  - id: 3
    title: "Task three"
    task_type: verification
---
# Plan
"""

PLAN_NO_FM = "# Plan with no frontmatter\n"


class TestTaskIdsWhere:
    def test_review_tier_minimum(self):
        ids, parsed = _ckpt._task_ids_where([PLAN_WITH_MIN], "review_tier", "minimum")
        assert ids == {1}
        assert parsed is True

    def test_task_type_verification(self):
        ids, parsed = _ckpt._task_ids_where([PLAN_WITH_MIN], "task_type", "verification")
        assert ids == {3}
        assert parsed is True

    def test_no_frontmatter(self):
        ids, parsed = _ckpt._task_ids_where([PLAN_NO_FM], "review_tier", "minimum")
        assert ids == set()
        assert parsed is False

    def test_multi_file_aggregation(self):
        plan2 = """---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 4
    title: "Task four"
    review_tier: minimum
---
"""
        ids, parsed = _ckpt._task_ids_where(
            [PLAN_WITH_MIN, plan2], "review_tier", "minimum"
        )
        assert ids == {1, 4}


class TestLoadAllPlanContents:
    def test_parent_plus_modules(self, tmp_path):
        feat = tmp_path / "feat"
        feat.mkdir()
        parent = feat / "plan.md"
        parent.write_text("# Parent plan\n")
        mod1 = feat / "module-1.md"
        mod1.write_text("# Module 1\n")
        manifest = {
            "plan_file": "feat/plan.md",
            "paths": {"feature_dir": "feat"},
            "modules": [
                {"id": 1, "title": "M1", "task_ids": [1], "file": "module-1.md"}
            ],
        }
        result = _ckpt._load_all_plan_contents(manifest, str(tmp_path))
        assert len(result) == 2
        assert "# Parent plan" in result[0]
        assert "# Module 1" in result[1]

    def test_deduplicates(self, tmp_path):
        feat = tmp_path / "feat"
        feat.mkdir()
        plan = feat / "plan.md"
        plan.write_text("# Plan\n")
        manifest = {
            "plan_file": "feat/plan.md",
            "paths": {"feature_dir": "feat"},
            "modules": [
                {"id": 1, "title": "M1", "task_ids": [1], "file": "plan.md"}
            ],
        }
        result = _ckpt._load_all_plan_contents(manifest, str(tmp_path))
        assert len(result) == 1

    def test_missing_module_file_skipped(self, tmp_path):
        feat = tmp_path / "feat"
        feat.mkdir()
        plan = feat / "plan.md"
        plan.write_text("# Plan\n")
        manifest = {
            "plan_file": "feat/plan.md",
            "paths": {"feature_dir": "feat"},
            "modules": [
                {"id": 1, "title": "M1", "task_ids": [1], "file": "gone.md"}
            ],
        }
        result = _ckpt._load_all_plan_contents(manifest, str(tmp_path))
        assert len(result) == 1
