"""Unit tests for CheckpointResult Pydantic model."""
import pytest
from pydantic import ValidationError

from checkpoint_result import (
    CheckpointResult, CheckResult, Progress,
    Phase, CheckStatus,
)
from _base import CURRENT_SCHEMA_VERSION


def _minimal_data(**overrides):
    """Golden-path minimal data dict for a passing pre-execution checkpoint."""
    data = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "phase": "pre-execution",
        "status": "PASS",
        "checks": {
            "plan_exists": {"status": "PASS", "detail": "Plan file found"},
        },
        "warnings": [],
        "blockers": [],
    }
    data.update(overrides)
    return data


def _pre_dispatch_data(**overrides):
    """Pre-dispatch checkpoint with required task_number."""
    data = _minimal_data(phase="pre-dispatch", task_number=3)
    data.update(overrides)
    return data


class TestGoldenPath:
    def test_pre_execution_pass(self):
        result = CheckpointResult(**_minimal_data())
        assert result.phase == "pre-execution"
        assert result.status == "PASS"
        assert result.task_number is None
        assert result.progress is None

    def test_pre_dispatch_pass(self):
        result = CheckpointResult(**_pre_dispatch_data())
        assert result.task_number == 3

    def test_pre_completion_pass(self):
        result = CheckpointResult(**_minimal_data(phase="pre-completion"))
        assert result.phase == "pre-completion"

    def test_with_progress(self):
        result = CheckpointResult(**_pre_dispatch_data(
            progress={"tasks_total": 10, "checkboxes_total": 50, "checkboxes_checked": 25, "tasks_completed": 3, "percentage": 50},
        ))
        assert result.progress.tasks_total == 10
        assert result.progress.percentage == 50


class TestPhaseEnum:
    @pytest.mark.parametrize("phase", ["pre-execution", "pre-dispatch", "pre-completion"])
    def test_valid_phases(self, phase):
        data = _minimal_data(phase=phase)
        if phase == "pre-dispatch":
            data["task_number"] = 1
        result = CheckpointResult(**data)
        assert result.phase == phase

    def test_invalid_phase_rejected(self):
        with pytest.raises(ValidationError, match="phase"):
            CheckpointResult(**_minimal_data(phase="post-mortem"))


class TestCheckStatusEnum:
    @pytest.mark.parametrize("cs", ["PASS", "FAIL", "SKIP", "OK", "WARNING"])
    def test_valid_check_statuses(self, cs):
        result = CheckpointResult(**_minimal_data(
            checks={"test_check": {"status": cs, "detail": "test"}},
        ))
        assert result.checks["test_check"].status == cs

    def test_invalid_check_status_rejected(self):
        with pytest.raises(ValidationError, match="status"):
            CheckpointResult(**_minimal_data(
                checks={"test_check": {"status": "WARN", "detail": "test"}},
            ))


class TestFailRequiresBlockers:
    def test_fail_without_blockers_rejected(self):
        with pytest.raises(ValidationError, match="blockers is empty"):
            CheckpointResult(**_minimal_data(
                status="FAIL",
                checks={"bad_check": {"status": "FAIL", "detail": "broken"}},
            ))

    def test_fail_with_blockers_passes(self):
        result = CheckpointResult(**_minimal_data(
            status="FAIL",
            checks={"bad_check": {"status": "FAIL", "detail": "broken"}},
            blockers=["bad_check"],
        ))
        assert result.status == "FAIL"


class TestBlockersReferenceCheckNames:
    def test_blocker_not_in_checks_rejected(self):
        with pytest.raises(ValidationError, match="not a key in checks"):
            CheckpointResult(**_minimal_data(
                status="FAIL",
                checks={"real_check": {"status": "FAIL", "detail": "broken"}},
                blockers=["typo_check"],
            ))

    def test_blocker_matching_check_passes(self):
        result = CheckpointResult(**_minimal_data(
            status="FAIL",
            checks={"real_check": {"status": "FAIL", "detail": "broken"}},
            blockers=["real_check"],
        ))
        assert result.blockers == ["real_check"]


class TestTaskNumberRequiredForPreDispatch:
    def test_pre_dispatch_without_task_number_rejected(self):
        with pytest.raises(ValidationError, match="task_number is required"):
            CheckpointResult(**_minimal_data(phase="pre-dispatch"))

    def test_pre_execution_without_task_number_passes(self):
        result = CheckpointResult(**_minimal_data(phase="pre-execution"))
        assert result.task_number is None

    def test_pre_completion_without_task_number_passes(self):
        result = CheckpointResult(**_minimal_data(phase="pre-completion"))
        assert result.task_number is None


class TestSchemaVersion:
    def test_wrong_version_rejected(self):
        with pytest.raises(ValidationError, match="schema_version"):
            CheckpointResult(**_minimal_data(schema_version=99))


class TestExtraFieldsForbidden:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError, match="extra"):
            CheckpointResult(**_minimal_data(surprise="oops"))


class TestModelDump:
    def test_exclude_none_omits_absent_optionals(self):
        result = CheckpointResult(**_minimal_data())
        dumped = result.model_dump(exclude_none=True)
        assert "task_number" not in dumped
        assert "progress" not in dumped
        assert "schema_version" in dumped
