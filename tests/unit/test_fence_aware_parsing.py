"""N5: Fence-aware task-header parsing at all 7+1 sites.
Run: .venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py -v
"""
import importlib.util
import os
import re

import pytest

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_script(name, filename):
    path = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_vp = _load_script("validate_plan", "validate-plan.py")
_ckpt = _load_script("controller_checkpoint", "controller-checkpoint.py")


# SELF-HOSTING GUARD: _H avoids plan-validator false match.
_H = "##" + "# Task"

FENCED_PLAN = f"""---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 1
    title: "Real task"
  - id: 2
    title: "Another real task"
---

# Plan

{_H} 1: Real task

Do something.

```markdown
{_H} 99: This is inside a fence and must be ignored
```

{_H} 2: Another real task

Do something else.
"""


class TestValidatePlanFenceAware:
    def test_extract_task_numbers_ignores_fenced(self):
        extract_task_numbers = _vp.extract_task_numbers
        nums = extract_task_numbers(FENCED_PLAN)
        assert 99 not in nums
        assert sorted(nums) == [1, 2]

    def test_analyse_tasks_ignores_fenced(self):
        analyse_tasks = _vp.analyse_tasks
        tasks, warnings, blockers = analyse_tasks(FENCED_PLAN.splitlines())
        task_nums = [t["number"] for t in tasks]
        assert 99 not in task_nums
        assert sorted(task_nums) == [1, 2]

    def test_task_zero_check_ignores_fenced(self):
        fenced_zero = f"\n```\n{_H} 0: Fake task zero inside fence\n```\n\n{_H} 1: Real first task\n"
        check_sections = _vp.check_sections
        lines = fenced_zero.splitlines()
        sections = check_sections(lines, fenced_zero)
        assert sections["task_0"]["present"] is False


class TestCheckpointFenceAware:
    def test_count_tasks_ignores_fenced(self):
        count_tasks = _ckpt.count_tasks
        assert count_tasks(FENCED_PLAN) == 2

    def test_has_task_zero_ignores_fenced(self):
        fenced_zero = f"\n```\n{_H} 0: Fake zero\n```\n{_H} 1: Real\n"
        has_task_zero = _ckpt.has_task_zero
        assert has_task_zero(fenced_zero) is False

    def test_checkbox_range_ignores_fenced_headers(self):
        plan = f"{_H} 1: Real\n\n- [ ] Step A\n\n```\n{_H} 2: Fake boundary\n- [ ] Fake checkbox\n```\n\n- [ ] Step B\n\n{_H} 2: Real next\n- [ ] Step C\n"
        get_task_checkbox_range = _ckpt.get_task_checkbox_range
        cbs = get_task_checkbox_range(plan, 1)
        assert cbs["unchecked"] == 2  # Step A + Step B, not the fenced one
