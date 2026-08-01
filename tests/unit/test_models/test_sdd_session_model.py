"""Tests for SddSession Pydantic model and its cross-field validators."""
import pytest
from pydantic import ValidationError

from sdd_session import (
    SddSession, ArtifactPaths, ModuleState, Enforcement,
    ProcessRequirements, TIER_PROFILES, Handoff,
)
from _base import CURRENT_SCHEMA_VERSION


MINIMAL_PATHS = {
    "feature_dir": "docs/imp-plans/x",
    "reports_dir": "docs/imp-plans/x/reports",
    "dispatch_log": "docs/imp-plans/x/reports/.dispatch-log",
    "deviations_file": "docs/imp-plans/x/deviations.md",
}

MINIMAL_SESSION = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "tier": "standard",
    "paths": MINIMAL_PATHS,
    "plan_file": "docs/imp-plans/x/plan.md",
    "task_range": (0, 4),
    "total_tasks": 5,
    "midpoint": 2,
    "enforcement": TIER_PROFILES["standard"]["enforcement"],
    "process_requirements": TIER_PROFILES["standard"]["process_requirements"],
}


class TestSddSessionGoldenInput:
    def test_minimal_session_parses(self):
        session = SddSession.model_validate(MINIMAL_SESSION)
        assert session.tier == "standard"
        assert session.task_range == (0, 4)
        assert session.total_tasks == 5
        assert session.midpoint == 2

    def test_roundtrip_through_json(self):
        session = SddSession.model_validate(MINIMAL_SESSION)
        dumped = session.model_dump()
        reparsed = SddSession.model_validate(dumped)
        assert reparsed == session

    def test_micro_tier_parses(self):
        data = {
            **MINIMAL_SESSION,
            "tier": "micro",
            "enforcement": TIER_PROFILES["micro"]["enforcement"],
            "process_requirements": TIER_PROFILES["micro"]["process_requirements"],
        }
        session = SddSession.model_validate(data)
        assert session.tier == "micro"
        assert session.enforcement.partner_review is False


class TestSddSessionValidation:
    def test_invalid_tier_rejected(self):
        data = {**MINIMAL_SESSION, "tier": "mega"}
        with pytest.raises(ValidationError) as exc:
            SddSession.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"

    def test_extra_field_rejected(self):
        data = {**MINIMAL_SESSION, "bogus_field": "nope"}
        with pytest.raises(ValidationError) as exc:
            SddSession.model_validate(data)
        assert exc.value.errors()[0]["type"] == "extra_forbidden"

    def test_task_range_start_greater_than_end(self):
        data = {**MINIMAL_SESSION, "task_range": (5, 2), "midpoint": 3}
        with pytest.raises(ValidationError, match=r"start \(5\) > end \(2\)"):
            SddSession.model_validate(data)

    def test_task_range_exceeds_total(self):
        data = {**MINIMAL_SESSION, "task_range": (0, 9), "total_tasks": 5, "midpoint": 4}
        with pytest.raises(ValidationError, match="total_tasks is 5"):
            SddSession.model_validate(data)

    def test_midpoint_outside_range(self):
        data = {**MINIMAL_SESSION, "task_range": (0, 4), "total_tasks": 5, "midpoint": 99}
        with pytest.raises(ValidationError, match=r"midpoint \(99\) outside task_range"):
            SddSession.model_validate(data)

    def test_midpoint_below_range(self):
        data = {
            **MINIMAL_SESSION,
            "task_range": (3, 7),
            "total_tasks": 10,
            "midpoint": 1,
        }
        with pytest.raises(ValidationError, match=r"midpoint \(1\) outside task_range"):
            SddSession.model_validate(data)


class TestSddSessionModuleConsistency:
    def test_modules_require_active_module_id(self):
        data = {
            **MINIMAL_SESSION,
            "modules": [
                {"id": 1, "title": "Module 1", "file": "m1.md", "task_ids": [0, 1, 2, 3, 4]},
            ],
            "active_module_id": None,
        }
        with pytest.raises(ValidationError, match="active_module_id is None"):
            SddSession.model_validate(data)

    def test_active_module_id_must_exist_in_modules(self):
        data = {
            **MINIMAL_SESSION,
            "modules": [
                {"id": 1, "title": "Module 1", "file": "m1.md", "task_ids": [0, 1, 2, 3, 4]},
            ],
            "active_module_id": 99,
        }
        with pytest.raises(ValidationError, match=r"active_module_id \(99\) not in modules"):
            SddSession.model_validate(data)

    def test_valid_multi_module_session(self):
        data = {
            **MINIMAL_SESSION,
            "modules": [
                {"id": 1, "title": "Module 1", "file": "m1.md", "task_ids": [0, 1]},
                {"id": 2, "title": "Module 2", "file": "m2.md", "task_ids": [2, 3, 4]},
            ],
            "active_module_id": 2,
            "active_module_file": "m2.md",
            "completed_modules": ["m1.md"],
        }
        session = SddSession.model_validate(data)
        assert len(session.modules) == 2
        assert session.active_module_id == 2
        assert session.completed_modules == ["m1.md"]

    def test_no_modules_allows_none_active_module_id(self):
        session = SddSession.model_validate(MINIMAL_SESSION)
        assert session.modules is None
        assert session.active_module_id is None


class TestTierProfiles:
    @pytest.mark.parametrize("tier_name", ["micro", "standard"])
    def test_enforcement_profile_validates(self, tier_name):
        enforcement = Enforcement.model_validate(TIER_PROFILES[tier_name]["enforcement"])
        assert isinstance(enforcement, Enforcement)

    @pytest.mark.parametrize("tier_name", ["micro", "standard"])
    def test_process_requirements_profile_validates(self, tier_name):
        reqs = ProcessRequirements.model_validate(
            TIER_PROFILES[tier_name]["process_requirements"]
        )
        assert isinstance(reqs, ProcessRequirements)

    def test_micro_skips_partner_review(self):
        reqs = ProcessRequirements.model_validate(
            TIER_PROFILES["micro"]["process_requirements"]
        )
        assert reqs.partner_review_mode == "skip"

    def test_standard_requires_dispatched_reviews(self):
        reqs = ProcessRequirements.model_validate(
            TIER_PROFILES["standard"]["process_requirements"]
        )
        assert reqs.spec_review_mode == "dispatched"
        assert reqs.quality_review_mode == "dispatched"
        assert reqs.partner_review_mode == "dispatched"

    def test_micro_enforcement_all_off(self):
        enforcement = Enforcement.model_validate(
            TIER_PROFILES["micro"]["enforcement"]
        )
        assert enforcement.pre_execution_audit is False
        assert enforcement.partner_review is False
        assert enforcement.dispatch_provenance is False
        assert enforcement.checkpoint_files is False
        assert enforcement.context_summary_at is None

    def test_standard_enforcement_all_on(self):
        enforcement = Enforcement.model_validate(
            TIER_PROFILES["standard"]["enforcement"]
        )
        assert enforcement.pre_execution_audit is True
        assert enforcement.partner_review is True
        assert enforcement.dispatch_provenance is True
        assert enforcement.checkpoint_files is True


class TestHandoffBlock:
    def test_absent_handoff_still_validates(self):
        s = SddSession.model_validate(MINIMAL_SESSION)
        assert s.handoff is None

    def test_handoff_block_validates(self):
        s = SddSession.model_validate({**MINIMAL_SESSION,
                                       "handoff": {"expected_hops": 5, "spawn_policy": "ask"}})
        assert s.handoff.expected_hops == 5
        assert s.handoff.spawn_policy == "ask"

    def test_spawn_policy_defaults_auto(self):
        s = SddSession.model_validate({**MINIMAL_SESSION, "handoff": {"expected_hops": 3}})
        assert s.handoff.spawn_policy == "auto"

    def test_expected_hops_must_be_positive(self):
        for bad in (0, -1):
            with pytest.raises(ValidationError):
                SddSession.model_validate({**MINIMAL_SESSION, "handoff": {"expected_hops": bad}})

    def test_round_trips_through_json(self):
        s = SddSession.model_validate({**MINIMAL_SESSION,
                                       "handoff": {"expected_hops": 4, "spawn_policy": "off"}})
        import json
        s2 = SddSession.model_validate(json.loads(s.model_dump_json()))
        assert s2.handoff == s.handoff

    def test_partial_block_rejected(self):        # deferred order B4 — see note below
        for partial in ({}, {"spawn_policy": "ask"}):
            with pytest.raises(ValidationError):
                SddSession.model_validate({**MINIMAL_SESSION, "handoff": partial})

    def test_spawn_policy_literal_is_closed_set(self):   # carry-forward from Task 4 quality r2
        from typing import get_args
        assert get_args(Handoff.model_fields["spawn_policy"].annotation) == ("auto", "ask", "off")

    def test_extra_key_rejected(self):    # pins StrictModel base — see note below
        with pytest.raises(ValidationError):
            SddSession.model_validate({**MINIMAL_SESSION,
                                       "handoff": {"expected_hops": 5, "typo": 1}})
