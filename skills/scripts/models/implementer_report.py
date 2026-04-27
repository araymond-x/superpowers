"""Pydantic model for ImplementerReport artifacts (YAML frontmatter)."""
from typing import Literal

from pydantic import Field, model_validator

from _base import StrictModel, SchemaVersionedModel

Status = Literal["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"]
TestResult = Literal["PASS", "FAIL"]
ComplianceStatus = Literal["compliant", "non_compliant", "partial", "not_applicable"]


class FileChange(StrictModel):
    path: str
    description: str


class TestSummary(StrictModel):
    written: int
    passing: int
    command: str
    result: TestResult


class ContractComplianceItem(StrictModel):
    constraint: str
    status: ComplianceStatus
    detail: str


class ImplementerReport(SchemaVersionedModel):
    task_id: int
    status: Status
    files_changed: list[FileChange]
    tests: TestSummary
    contract_compliance: list[ContractComplianceItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def test_counts_consistent(self) -> "ImplementerReport":
        if self.tests.passing > self.tests.written:
            raise ValueError(
                f"tests.passing ({self.tests.passing}) cannot exceed "
                f"tests.written ({self.tests.written})"
            )
        return self

    @model_validator(mode="after")
    def files_changed_non_empty_for_done(self) -> "ImplementerReport":
        if self.status in ("DONE", "DONE_WITH_CONCERNS") and not self.files_changed:
            raise ValueError(
                f"status is {self.status} but files_changed is empty — "
                f"completed tasks must list at least one file"
            )
        return self
