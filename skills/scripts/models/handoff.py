"""Pydantic model for HandoffPackage artifacts (YAML frontmatter)."""
from typing import Literal

from pydantic import Field, model_validator

from _base import StrictModel, SchemaVersionedModel

FieldTypeKind = Literal["string", "integer", "float", "boolean", "date", "enum"]


class FieldType(StrictModel):
    """A single field constraint in a handoff contract."""

    name: str
    kind: FieldTypeKind
    format_hint: str | None = None
    nullable: bool = False


class FormatRule(StrictModel):
    """A formatting rule that applies to one or more declared fields."""

    applies_to: list[str]
    rule: str


class Sample(StrictModel):
    """A sample file reference included in the handoff package."""

    path: str
    description: str


class HandoffPackage(SchemaVersionedModel):
    """Top-level model for handoff package README.md frontmatter."""

    package_name: str
    feeds_into: str
    one_sentence_purpose: str
    contract_constraints: list[FieldType]
    format_rules: list[FormatRule] = Field(default_factory=list)
    samples: list[Sample]

    @model_validator(mode="after")
    def format_rules_reference_declared_fields(self) -> "HandoffPackage":
        declared = {f.name for f in self.contract_constraints}
        for rule in self.format_rules:
            undeclared = [f for f in rule.applies_to if f not in declared]
            if undeclared:
                raise ValueError(
                    f"FormatRule applies_to={undeclared} but those fields aren't declared in contract_constraints"
                )
        return self

    @model_validator(mode="after")
    def at_least_one_sample(self) -> "HandoffPackage":
        if not self.samples:
            raise ValueError("HandoffPackage must include at least one sample")
        return self
