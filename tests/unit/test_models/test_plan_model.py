"""Tests for Plan Pydantic model and its cross-field validators."""

import os
import subprocess
import sys
import textwrap
from typing import get_args

import pytest
from pydantic import ValidationError

from plan import (
    Plan,
    Task,
)
from _base import CURRENT_SCHEMA_VERSION

VALIDATORS = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "skills",
    "scripts",
    "models",
    "validators.py",
)


MINIMAL_PLAN = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "feature_archetype": "greenfield",
    "tasks": [{"id": 0, "title": "Setup"}, {"id": 1, "title": "Build"}],
}


class TestPlanGoldenInput:
    def test_minimal_plan_parses(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        assert plan.feature_archetype == "greenfield"
        assert len(plan.tasks) == 2

    def test_roundtrip_through_json(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        dumped = plan.model_dump()
        reparsed = Plan.model_validate(dumped)
        assert reparsed == plan


class TestPlanFieldValidation:
    def test_missing_tasks_fails(self):
        data = {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "feature_archetype": "greenfield",
        }
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["loc"] == ("tasks",)

    def test_missing_feature_archetype_fails(self):
        data = {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "tasks": [{"id": 0, "title": "x"}],
        }
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["loc"] == ("feature_archetype",)

    def test_invalid_archetype_fails(self):
        data = {**MINIMAL_PLAN, "feature_archetype": "expansion"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"

    def test_extra_field_rejected(self):
        data = {**MINIMAL_PLAN, "bogus_field": "nope"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["type"] == "extra_forbidden"

    @pytest.mark.parametrize(
        "archetype", ["greenfield", "replacement", "extension", "refactor", "migration"]
    )
    def test_all_valid_archetypes_accepted(self, archetype):
        data = {**MINIMAL_PLAN, "feature_archetype": archetype}
        plan = Plan.model_validate(data)
        assert plan.feature_archetype == archetype

    def test_literal_error_ctx_expected_shape(self):
        """Pin the shape of Pydantic v2 ctx.expected for literal_error."""
        data = {**MINIMAL_PLAN, "feature_archetype": "bogus"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        err = exc.value.errors()[0]
        assert err["type"] == "literal_error"
        assert "expected" in err.get("ctx", {}), (
            f"Pydantic literal_error ctx must contain 'expected' key; got {err.get('ctx')}"
        )


class TestTaskUniqueSequentialIds:
    def test_non_sequential_fails(self):
        # Gap at 1 — catches accidentally skipped or omitted tasks
        data = {
            **MINIMAL_PLAN,
            "tasks": [{"id": 0, "title": "a"}, {"id": 5, "title": "b"}],
        }
        with pytest.raises(ValidationError, match="sequential ascending"):
            Plan.model_validate(data)

    def test_duplicate_ids_fail(self):
        data = {
            **MINIMAL_PLAN,
            "tasks": [{"id": 0, "title": "a"}, {"id": 0, "title": "b"}],
        }
        with pytest.raises(ValidationError, match="Duplicate"):
            Plan.model_validate(data)

    def test_sequential_ids_pass(self):
        data = {
            **MINIMAL_PLAN,
            "tasks": [
                {"id": 0, "title": "a"},
                {"id": 1, "title": "b"},
                {"id": 2, "title": "c"},
            ],
        }
        plan = Plan.model_validate(data)
        assert len(plan.tasks) == 3

    def test_sequential_from_nonzero_start_passes(self):
        # Module 2 renumbered globally (M1 was 0–5): [6,7,8] is sequential from 6
        data = {
            **MINIMAL_PLAN,
            "tasks": [
                {"id": 6, "title": "a"},
                {"id": 7, "title": "b"},
                {"id": 8, "title": "c"},
            ],
        }
        plan = Plan.model_validate(data)
        assert len(plan.tasks) == 3


class TestDependsOnValidation:
    def test_invalid_dependency_fails(self):
        data = {
            **MINIMAL_PLAN,
            "tasks": [
                {"id": 0, "title": "a"},
                {"id": 1, "title": "b", "depends_on": [99]},
            ],
        }
        with pytest.raises(ValidationError, match="don't exist"):
            Plan.model_validate(data)

    def test_forward_dependency_fails(self):
        data = {
            **MINIMAL_PLAN,
            "tasks": [
                {"id": 0, "title": "a", "depends_on": [1]},
                {"id": 1, "title": "b"},
            ],
        }
        with pytest.raises(ValidationError, match="cannot depend on"):
            Plan.model_validate(data)

    def test_valid_backward_dependency_passes(self):
        data = {
            **MINIMAL_PLAN,
            "tasks": [
                {"id": 0, "title": "a"},
                {"id": 1, "title": "b", "depends_on": [0]},
            ],
        }
        plan = Plan.model_validate(data)
        assert plan.tasks[1].depends_on == [0]


class TestSharedConstantsValidation:
    def test_undeclared_constant_fails(self):
        data = {
            **MINIMAL_PLAN,
            "tasks": [
                {"id": 0, "title": "a", "shared_constants_used": ["app.config.X"]}
            ],
        }
        with pytest.raises(ValidationError, match="not in plan.shared_constants"):
            Plan.model_validate(data)

    def test_declared_constant_passes(self):
        data = {
            **MINIMAL_PLAN,
            "shared_constants": [
                {"path": "app.config.X", "value": "1", "reason": "test"}
            ],
            "tasks": [
                {"id": 0, "title": "a", "shared_constants_used": ["app.config.X"]}
            ],
        }
        plan = Plan.model_validate(data)
        assert len(plan.shared_constants) == 1


class TestPatternReferencesValidation:
    def test_undeclared_pattern_fails(self):
        data = {
            **MINIMAL_PLAN,
            "tasks": [{"id": 0, "title": "a", "pattern_references": ["nonexistent"]}],
        }
        with pytest.raises(ValidationError, match="not in plan.pattern_references"):
            Plan.model_validate(data)

    def test_declared_pattern_passes(self):
        data = {
            **MINIMAL_PLAN,
            "pattern_references": [
                {"name": "p1", "source_files": ["f.py"], "reason": "test"}
            ],
            "tasks": [{"id": 0, "title": "a", "pattern_references": ["p1"]}],
        }
        plan = Plan.model_validate(data)
        assert plan.tasks[0].pattern_references == ["p1"]


class TestModuleValidation:
    def test_task_claimed_by_two_modules_fails(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [
                {"id": 1, "title": "A", "task_ids": [0]},
                {"id": 2, "title": "B", "task_ids": [0]},
            ],
        }
        with pytest.raises(ValidationError, match="claimed by Module"):
            Plan.model_validate(data)

    def test_orphan_task_fails(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [{"id": 1, "title": "A", "task_ids": [0]}],
        }
        with pytest.raises(ValidationError, match="not claimed"):
            Plan.model_validate(data)

    def test_valid_modules_pass(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [{"id": 1, "title": "All", "task_ids": [0, 1]}],
        }
        plan = Plan.model_validate(data)
        assert len(plan.modules) == 1

    def test_no_modules_is_valid(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        assert plan.modules is None


class TestEnforcementTierField:
    def test_accepts_standard_tier(self):
        data = {**MINIMAL_PLAN, "enforcement_tier": "standard"}
        plan = Plan.model_validate(data)
        assert plan.enforcement_tier == "standard"

    def test_accepts_micro_tier(self):
        data = {**MINIMAL_PLAN, "enforcement_tier": "micro"}
        plan = Plan.model_validate(data)
        assert plan.enforcement_tier == "micro"

    def test_defaults_to_none(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        assert plan.enforcement_tier is None

    def test_rejects_comprehensive(self):
        data = {**MINIMAL_PLAN, "enforcement_tier": "comprehensive"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"


class TestModuleFileField:
    def test_accepts_file_path(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [
                {
                    "id": 1,
                    "title": "All",
                    "task_ids": [0, 1],
                    "file": "docs/module-1.md",
                }
            ],
        }
        plan = Plan.model_validate(data)
        assert plan.modules[0].file == "docs/module-1.md"

    def test_defaults_to_none(self):
        data = {
            **MINIMAL_PLAN,
            "modules": [{"id": 1, "title": "All", "task_ids": [0, 1]}],
        }
        plan = Plan.model_validate(data)
        assert plan.modules[0].file is None


class TestReviewTier:
    def test_review_tier_defaults_to_full(self):
        task = Task(id=1, title="x")
        assert task.review_tier == "full"

    def test_review_tier_accepts_minimum(self):
        task = Task(id=1, title="x", review_tier="minimum")
        assert task.review_tier == "minimum"

    def test_review_tier_rejects_other_values(self):
        with pytest.raises(ValidationError) as exc:
            Task(id=1, title="x", review_tier="medium")
        assert exc.value.errors()[0]["type"] == "literal_error"

    def test_plan_with_review_tier_parses(self):
        data = {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "feature_archetype": "extension",
            "tasks": [
                {"id": 0, "title": "Setup"},
                {"id": 1, "title": "DDL", "review_tier": "minimum"},
            ],
        }
        plan = Plan.model_validate(data)
        assert plan.tasks[0].review_tier == "full"  # default
        assert plan.tasks[1].review_tier == "minimum"

    def test_schema_version_unchanged(self):
        """Adding review_tier is non-breaking — schema version must NOT change."""
        assert CURRENT_SCHEMA_VERSION == 1


class TestEntryMode:
    def test_entry_mode_defaults_to_brainstorming(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        assert plan.entry_mode == "brainstorming"

    def test_entry_mode_accepts_direct(self):
        data = {**MINIMAL_PLAN, "entry_mode": "direct"}
        plan = Plan.model_validate(data)
        assert plan.entry_mode == "direct"

    def test_entry_mode_rejects_invalid(self):
        data = {**MINIMAL_PLAN, "entry_mode": "handoff"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"


class TestTaskType:
    def test_task_type_defaults_to_implementation(self):
        task = Task(id=1, title="x")
        assert task.task_type == "implementation"

    def test_task_type_accepts_verification(self):
        task = Task(id=1, title="x", task_type="verification")
        assert task.task_type == "verification"

    def test_task_type_rejects_invalid(self):
        with pytest.raises(ValidationError) as exc:
            Task(id=1, title="x", task_type="audit")
        assert exc.value.errors()[0]["type"] == "literal_error"

    def test_plan_with_task_type_parses(self):
        data = {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "feature_archetype": "extension",
            "tasks": [
                {"id": 0, "title": "Setup"},
                {"id": 1, "title": "Audit orphans", "task_type": "verification"},
            ],
        }
        plan = Plan.model_validate(data)
        assert plan.tasks[0].task_type == "implementation"  # default
        assert plan.tasks[1].task_type == "verification"

    def test_task_type_orthogonal_to_review_tier(self):
        task = Task(id=1, title="x", task_type="verification", review_tier="minimum")
        assert task.task_type == "verification"
        assert task.review_tier == "minimum"

    def test_schema_version_unchanged(self):
        """Adding task_type is non-breaking — schema version must NOT change."""
        assert CURRENT_SCHEMA_VERSION == 1


class TestHandoffSpawn:
    def test_defaults_to_auto(self):
        plan = Plan.model_validate(MINIMAL_PLAN)
        assert plan.handoff_spawn == "auto"

    def test_accepts_ask_and_off(self):
        for v in ("ask", "off"):
            data = {**MINIMAL_PLAN, "handoff_spawn": v}
            plan = Plan.model_validate(data)
            assert plan.handoff_spawn == v

    def test_rejects_invalid_value(self):
        data = {**MINIMAL_PLAN, "handoff_spawn": "prompt"}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"

    def test_literal_is_closed_set(self):
        """Pins the Literal itself, not just accept/reject cases -- a widened
        Literal (e.g. a fourth authorized value) would leave the other tests
        in this class green."""
        assert get_args(Plan.model_fields["handoff_spawn"].annotation) == (
            "auto",
            "ask",
            "off",
        )

    def test_schema_version_not_bumped(self):
        """Adding handoff_spawn is non-breaking — schema version must NOT change."""
        assert CURRENT_SCHEMA_VERSION == 1

    def test_unquoted_off_coerces_to_off(self):
        # yaml.safe_load("handoff_spawn: off") -> False (YAML 1.1); model coerces to "off"
        data = {**MINIMAL_PLAN, "handoff_spawn": False}
        assert Plan.model_validate(data).handoff_spawn == "off"

    def test_bare_on_rejected_with_actionable_message(self):
        data = {**MINIMAL_PLAN, "handoff_spawn": True}
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        assert "on" in str(exc.value).lower()


def _write_plan(tmp_path, handoff_line):
    body = textwrap.dedent(f"""\
        ---
        schema_version: 1
        feature_archetype: extension
        {handoff_line}
        tasks:
          - id: 0
            title: t
        ---
        # Plan
        ### Task 0: t
        - [ ] do it
        """)
    p = os.path.join(tmp_path, "plan.md")
    open(p, "w").write(body)
    return p


def test_validators_cli_accepts_unquoted_off(tmp_path):
    p = _write_plan(tmp_path, "handoff_spawn: off")  # unquoted -> False in YAML
    r = subprocess.run(
        [sys.executable, VALIDATORS, "plan", p], capture_output=True, text=True
    )
    assert r.returncode == 0, r.stderr


def test_validators_cli_rejects_bare_on(tmp_path):
    p = _write_plan(tmp_path, "handoff_spawn: on")
    r = subprocess.run(
        [sys.executable, VALIDATORS, "plan", p], capture_output=True, text=True
    )
    assert r.returncode == 1, r.stdout + r.stderr
