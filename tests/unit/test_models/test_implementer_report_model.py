"""Unit tests for ImplementerReport Pydantic model."""
import pytest
from pydantic import ValidationError

from implementer_report import (
    ImplementerReport, FileChange, TestSummary, ContractComplianceItem,
    Status, TestResult, ComplianceStatus,
)
from _base import CURRENT_SCHEMA_VERSION


def _minimal_data(**overrides):
    """Golden-path minimal data dict."""
    data = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "task_id": 1,
        "status": "DONE",
        "files_changed": [{"path": "src/foo.py", "description": "added feature"}],
        "tests": {"written": 2, "passing": 2, "command": "pytest -v", "result": "PASS"},
    }
    data.update(overrides)
    return data


class TestGoldenPath:
    def test_minimal_valid(self):
        report = ImplementerReport(**_minimal_data())
        assert report.task_id == 1
        assert report.status == "DONE"
        assert report.contract_compliance == []

    def test_full_featured(self):
        data = _minimal_data(
            status="DONE_WITH_CONCERNS",
            contract_compliance=[{
                "constraint": "Must use async",
                "status": "compliant",
                "detail": "All endpoints async",
            }],
        )
        report = ImplementerReport(**data)
        assert len(report.contract_compliance) == 1
        assert report.contract_compliance[0].status == "compliant"


class TestStatusEnum:
    @pytest.mark.parametrize("status", ["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"])
    def test_valid_statuses(self, status):
        report = ImplementerReport(**_minimal_data(
            status=status,
            files_changed=[] if status in ("BLOCKED", "NEEDS_CONTEXT") else [{"path": "x.py", "description": "y"}],
        ))
        assert report.status == status

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError, match="status"):
            ImplementerReport(**_minimal_data(status="INVALID"))


class TestTestResultEnum:
    @pytest.mark.parametrize("result", ["PASS", "FAIL"])
    def test_valid_results(self, result):
        report = ImplementerReport(**_minimal_data(
            tests={"written": 1, "passing": 1 if result == "PASS" else 0, "command": "pytest", "result": result},
        ))
        assert report.tests.result == result

    def test_invalid_result_rejected(self):
        with pytest.raises(ValidationError, match="result"):
            ImplementerReport(**_minimal_data(
                tests={"written": 1, "passing": 1, "command": "pytest", "result": "SKIP"},
            ))


class TestComplianceStatusEnum:
    @pytest.mark.parametrize("cs", ["compliant", "non_compliant", "partial", "not_applicable"])
    def test_valid_compliance_statuses(self, cs):
        data = _minimal_data(contract_compliance=[{
            "constraint": "test", "status": cs, "detail": "detail",
        }])
        report = ImplementerReport(**data)
        assert report.contract_compliance[0].status == cs

    def test_invalid_compliance_status_rejected(self):
        with pytest.raises(ValidationError, match="status"):
            ImplementerReport(**_minimal_data(contract_compliance=[{
                "constraint": "test", "status": "invalid", "detail": "detail",
            }]))


class TestRequiredFields:
    @pytest.mark.parametrize("field", ["schema_version", "task_id", "status", "files_changed", "tests"])
    def test_missing_required_field(self, field):
        data = _minimal_data()
        del data[field]
        with pytest.raises(ValidationError):
            ImplementerReport(**data)


class TestExtraFieldsForbidden:
    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError, match="extra"):
            ImplementerReport(**_minimal_data(surprise_field="oops"))


class TestSchemaVersion:
    def test_wrong_version_rejected(self):
        with pytest.raises(ValidationError, match="schema_version"):
            ImplementerReport(**_minimal_data(schema_version=99))


class TestTestCountsConsistentValidator:
    def test_passing_exceeds_written_fails(self):
        with pytest.raises(ValidationError, match="cannot exceed"):
            ImplementerReport(**_minimal_data(
                tests={"written": 2, "passing": 5, "command": "pytest", "result": "PASS"},
            ))

    def test_passing_equals_written_passes(self):
        report = ImplementerReport(**_minimal_data(
            tests={"written": 3, "passing": 3, "command": "pytest", "result": "PASS"},
        ))
        assert report.tests.passing == 3

    def test_zero_tests_passes(self):
        report = ImplementerReport(**_minimal_data(
            status="BLOCKED",
            files_changed=[],
            tests={"written": 0, "passing": 0, "command": "pytest", "result": "FAIL"},
        ))
        assert report.tests.written == 0


class TestFilesChangedNonEmptyForDoneValidator:
    def test_done_with_empty_files_fails(self):
        with pytest.raises(ValidationError, match="files_changed is empty"):
            ImplementerReport(**_minimal_data(files_changed=[]))

    def test_done_with_concerns_with_empty_files_fails(self):
        with pytest.raises(ValidationError, match="files_changed is empty"):
            ImplementerReport(**_minimal_data(status="DONE_WITH_CONCERNS", files_changed=[]))

    def test_blocked_with_empty_files_passes(self):
        report = ImplementerReport(**_minimal_data(status="BLOCKED", files_changed=[]))
        assert report.files_changed == []

    def test_needs_context_with_empty_files_passes(self):
        report = ImplementerReport(**_minimal_data(status="NEEDS_CONTEXT", files_changed=[]))
        assert report.files_changed == []
