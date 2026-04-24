"""Pydantic model for Plan artifacts (YAML frontmatter)."""
from typing import Literal

from pydantic import Field, model_validator

from _base import StrictModel, SchemaVersionedModel

FeatureArchetype = Literal["greenfield", "replacement", "extension", "refactor", "migration"]


class SharedConstant(StrictModel):
    path: str
    value: str
    reason: str


class PatternReference(StrictModel):
    name: str
    source_files: list[str]
    reason: str


class Task(StrictModel):
    id: int
    title: str
    module_id: int | None = None
    depends_on: list[int] = Field(default_factory=list)
    pattern_references: list[str] = Field(default_factory=list)
    shared_constants_used: list[str] = Field(default_factory=list)


class Module(StrictModel):
    id: int
    title: str
    task_ids: list[int]


class Plan(SchemaVersionedModel):
    feature_archetype: FeatureArchetype
    source_contracts: str | None = None
    shared_constants: list[SharedConstant] = Field(default_factory=list)
    pattern_references: list[PatternReference] = Field(default_factory=list)
    modules: list[Module] | None = None
    tasks: list[Task]

    @model_validator(mode="after")
    def tasks_have_unique_sequential_ids(self) -> "Plan":
        ids = [t.id for t in self.tasks]
        if len(ids) != len(set(ids)):
            dupes = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate task IDs: {sorted(set(dupes))}")
        expected = list(range(ids[0], ids[0] + len(ids)))
        if ids != expected:
            raise ValueError(f"Task IDs must be sequential ascending; got {ids}")
        return self

    @model_validator(mode="after")
    def depends_on_references_valid_ids(self) -> "Plan":
        valid_ids = {t.id for t in self.tasks}
        for task in self.tasks:
            invalid = [d for d in task.depends_on if d not in valid_ids]
            if invalid:
                raise ValueError(
                    f"Task {task.id} depends_on={invalid} but those task IDs don't exist in plan"
                )
            forward = [d for d in task.depends_on if d >= task.id]
            if forward:
                raise ValueError(
                    f"Task {task.id} cannot depend on task(s) {forward} — dependencies must have lower IDs"
                )
        return self

    @model_validator(mode="after")
    def shared_constants_used_are_declared(self) -> "Plan":
        declared_paths = {c.path for c in self.shared_constants}
        for task in self.tasks:
            undeclared = [p for p in task.shared_constants_used if p not in declared_paths]
            if undeclared:
                raise ValueError(
                    f"Task {task.id} uses shared_constants {undeclared} but they're not in plan.shared_constants"
                )
        return self

    @model_validator(mode="after")
    def pattern_references_are_declared(self) -> "Plan":
        declared = {p.name for p in self.pattern_references}
        for task in self.tasks:
            undeclared = [p for p in task.pattern_references if p not in declared]
            if undeclared:
                raise ValueError(
                    f"Task {task.id} references patterns {undeclared} but they're not in plan.pattern_references"
                )
        return self

    @model_validator(mode="after")
    def module_task_ids_are_consistent(self) -> "Plan":
        if self.modules is None:
            return self
        seen: dict[int, int] = {}
        for mod in self.modules:
            for tid in mod.task_ids:
                if tid in seen:
                    raise ValueError(
                        f"Task {tid} claimed by Module {seen[tid]} AND Module {mod.id}"
                    )
                seen[tid] = mod.id
        all_task_ids = {t.id for t in self.tasks}
        claimed = set(seen.keys())
        orphans = all_task_ids - claimed
        if orphans:
            raise ValueError(f"Tasks {sorted(orphans)} are not claimed by any module")
        return self
