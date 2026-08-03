"""Pydantic model for SDD session manifest (.sdd-session.json)."""
from typing import Literal

from pydantic import Field, model_validator

from _base import StrictModel, SchemaVersionedModel

Tier = Literal["micro", "standard"]
ReviewMode = Literal["dispatched", "self_review", "skip"]
DispatchMode = Literal["required", "controller_direct"]
RequirementLevel = Literal["required", "skip"]

SpawnPolicy = Literal["auto", "ask", "off"]


class Handoff(StrictModel):
    """Auto-spawn consent + advisory hop budget (cmux-spawn-v2). Optional —
    absent on pre-v2 manifests; spawn-time consumers re-derive (see
    _handoff_support.derive_expected_hops)."""
    expected_hops: int = Field(ge=1)
    spawn_policy: SpawnPolicy = "auto"


class ArtifactPaths(StrictModel):
    """All paths are git-root-relative."""
    feature_dir: str
    reports_dir: str
    dispatch_log: str
    deviations_file: str


class ModuleState(StrictModel):
    id: int
    title: str
    file: str
    task_ids: list[int]


class Enforcement(StrictModel):
    pre_execution_audit: bool
    partner_review: bool
    dispatch_provenance: bool
    context_summary_at: int | None
    checkpoint_files: bool


class ProcessRequirements(StrictModel):
    subagent_dispatch: DispatchMode
    spec_review_mode: ReviewMode
    quality_review_mode: ReviewMode
    partner_review_mode: ReviewMode
    deviations_log: RequirementLevel
    checkpoint_script: RequirementLevel


TIER_PROFILES: dict[str, dict] = {
    "micro": {
        "enforcement": {
            "pre_execution_audit": False,
            "partner_review": False,
            "dispatch_provenance": False,
            "context_summary_at": None,
            "checkpoint_files": False,
        },
        "process_requirements": {
            "subagent_dispatch": "controller_direct",
            "spec_review_mode": "self_review",
            "quality_review_mode": "self_review",
            "partner_review_mode": "skip",
            "deviations_log": "required",
            "checkpoint_script": "skip",
        },
    },
    "standard": {
        "enforcement": {
            "pre_execution_audit": True,
            "partner_review": True,
            "dispatch_provenance": True,
            "context_summary_at": None,  # computed at materialization time
            "checkpoint_files": True,
        },
        "process_requirements": {
            "subagent_dispatch": "required",
            "spec_review_mode": "dispatched",
            "quality_review_mode": "dispatched",
            "partner_review_mode": "dispatched",
            "deviations_log": "required",
            "checkpoint_script": "required",
        },
    },
}


class SddSession(SchemaVersionedModel):
    tier: Tier
    paths: ArtifactPaths
    plan_file: str
    active_module_id: int | None = None
    active_module_file: str | None = None
    task_range: tuple[int, int]
    total_tasks: int
    midpoint: int
    enforcement: Enforcement
    process_requirements: ProcessRequirements
    completed_modules: list[str] = Field(default_factory=list)
    module_reports_archived: bool = False
    modules: list[ModuleState] | None = None
    dispatch_log_sentinel: bool = False
    handoff: Handoff | None = None

    @model_validator(mode="after")
    def task_range_valid(self) -> "SddSession":
        start, end = self.task_range
        if start > end:
            raise ValueError(
                f"task_range start ({start}) > end ({end})"
            )
        if end - start + 1 > self.total_tasks:
            raise ValueError(
                f"task_range covers {end - start + 1} tasks but total_tasks is {self.total_tasks}"
            )
        return self

    @model_validator(mode="after")
    def midpoint_in_range(self) -> "SddSession":
        start, end = self.task_range
        if not (start <= self.midpoint <= end):
            raise ValueError(
                f"midpoint ({self.midpoint}) outside task_range [{start}, {end}]"
            )
        return self

    @model_validator(mode="after")
    def module_fields_consistent(self) -> "SddSession":
        if self.modules is not None:
            if self.active_module_id is None:
                raise ValueError(
                    "modules is set but active_module_id is None"
                )
            valid_ids = {m.id for m in self.modules}
            if self.active_module_id not in valid_ids:
                raise ValueError(
                    f"active_module_id ({self.active_module_id}) not in modules: {valid_ids}"
                )
        return self
