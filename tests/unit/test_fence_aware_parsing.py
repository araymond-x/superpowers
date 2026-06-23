"""N5: Fence-aware task-header parsing at all 7+1 sites.
Run: .venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py -v
"""
import argparse

import pytest

from sdd_test_helpers import _load_script

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


class TestSourceContractsNonePass:
    def test_source_contracts_none_is_valid_absent(self, tmp_path):
        """N7: Source Contracts: None should yield PASS, not FAIL."""
        plan = tmp_path / "plan.md"
        plan.write_text(
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            "source_contracts: null\ntasks:\n  - id: 1\n    title: T\n---\n"
            "# Plan\n\n**Source Contracts:** None\n\n**Contract Constraints:** None\n\n"
            "**Feature Archetype:** Extension\n\n**Code Footprint:**\n\n"
            "| Cat | Files | Action | Deps |\n|--|--|--|--|\n| New | f.py | Create | - |\n\n"
            f"{_H} 1: Do thing\n- [ ] Step 1\n"
        )
        run_pre_execution = _ckpt.run_pre_execution
        args = argparse.Namespace(
            plan_file=str(plan),
            deviations_file=None,
            reports_dir=None,
            manifest=None,
        )
        result = run_pre_execution(args)
        sc = result["checks"].get("source_contracts", {})
        assert sc["status"] != "FAIL", f"Source Contracts: None should PASS, got {sc}"


class TestFenceHelperEdges:
    """N20: tilde fences, own-marker-type closing, unclosed-at-EOF, open-fence detector."""

    def test_tilde_fence_blanked(self):
        from _report_utils import _unfenced_content
        text = "before\n~~~\nfenced line\n~~~\nafter\n"
        out = _unfenced_content(text)
        assert "fenced line" not in out
        assert "before" in out and "after" in out

    def test_backtick_not_closed_by_tilde(self):
        from _report_utils import _unfenced_content
        # A ~~~ line inside a ``` fence is content, not a close.
        text = "```\nstill fenced\n~~~\nstill fenced too\n```\nout\n"
        out = _unfenced_content(text)
        assert "still fenced" not in out
        assert "still fenced too" not in out
        assert "out" in out

    def test_unclosed_fence_blanks_to_eof(self):
        from _report_utils import _unfenced_content
        text = "head\n```\nshadowed 1\nshadowed 2\n"  # no closing fence
        out = _unfenced_content(text)
        assert "head" in out
        assert "shadowed 1" not in out and "shadowed 2" not in out

    def test_ends_in_open_fence_true(self):
        from _report_utils import ends_in_open_fence
        assert ends_in_open_fence("x\n```\nunclosed\n") is True
        assert ends_in_open_fence("x\n~~~\nunclosed\n") is True

    def test_ends_in_open_fence_false(self):
        from _report_utils import ends_in_open_fence
        assert ends_in_open_fence("x\n```\nclosed\n```\n") is False
        assert ends_in_open_fence("no fences here\n") is False
