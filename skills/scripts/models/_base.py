"""Base classes for Pydantic validation models."""
from pydantic import BaseModel, field_validator, ConfigDict

CURRENT_SCHEMA_VERSION = 1


class StrictModel(BaseModel):
    """Base for nested models. Forbids unknown fields."""

    model_config = ConfigDict(extra="forbid")


class SchemaVersionedModel(StrictModel):
    """Base for top-level artifact models. Requires schema_version."""

    schema_version: int

    @field_validator("schema_version")
    @classmethod
    def must_match_current(cls, v: int) -> int:
        if v != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version={v} but validator is pinned to v{CURRENT_SCHEMA_VERSION}. "
                f"Update the frontmatter to schema_version: {CURRENT_SCHEMA_VERSION}, "
                f"or invoke the validator with --schema-version {v} for forensic review."
            )
        return v
