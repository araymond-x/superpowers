"""Pydantic model for CheckpointResult artifacts (pure JSON)."""
from typing import Literal

from pydantic import model_validator

from _base import StrictModel, SchemaVersionedModel

Phase = Literal["pre-execution", "pre-dispatch", "pre-completion"]
CheckStatus = Literal["PASS", "FAIL", "SKIP", "OK", "WARNING"]


class CheckResult(StrictModel):
    status: CheckStatus
    detail: str


class Progress(StrictModel):
    tasks_total: int
    tasks_completed: int | None = None
    checkboxes_total: int
    checkboxes_checked: int
    checkboxes_unchecked: int | None = None
    percentage: int | None = None


class CheckpointResult(SchemaVersionedModel):
    phase: Phase
    status: Literal["PASS", "FAIL"]
    task_number: int | None = None
    checks: dict[str, CheckResult]
    warnings: list[str]
    blockers: list[str]
    progress: Progress | None = None

    @model_validator(mode="after")
    def fail_requires_blockers(self) -> "CheckpointResult":
        if self.status == "FAIL" and not self.blockers:
            raise ValueError(
                "status is FAIL but blockers is empty — "
                "a FAIL without named blockers is untraceable"
            )
        return self

    @model_validator(mode="after")
    def blockers_reference_check_names(self) -> "CheckpointResult":
        for blocker in self.blockers:
            if blocker not in self.checks:
                raise ValueError(
                    f"blocker '{blocker}' is not a key in checks — "
                    f"available check names: {list(self.checks.keys())}"
                )
        return self

    @model_validator(mode="after")
    def task_number_required_for_pre_dispatch(self) -> "CheckpointResult":
        if self.phase == "pre-dispatch" and self.task_number is None:
            raise ValueError(
                "task_number is required when phase is 'pre-dispatch'"
            )
        return self
