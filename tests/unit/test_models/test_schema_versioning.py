"""Tests for StrictModel and SchemaVersionedModel base classes."""
import pytest
from pydantic import ValidationError

from _base import StrictModel, SchemaVersionedModel, CURRENT_SCHEMA_VERSION


class TestStrictModel:
    """StrictModel enforces extra='forbid'."""

    def test_rejects_unknown_fields(self):
        class Nested(StrictModel):
            name: str

        with pytest.raises(ValidationError) as exc:
            Nested(name="ok", bogus="nope")
        assert exc.value.errors()[0]["type"] == "extra_forbidden"

    def test_accepts_valid_fields(self):
        class Nested(StrictModel):
            name: str

        obj = Nested(name="ok")
        assert obj.name == "ok"


class TestSchemaVersionedModel:
    """SchemaVersionedModel requires schema_version == CURRENT_SCHEMA_VERSION."""

    def test_accepts_current_version(self):
        class Artifact(SchemaVersionedModel):
            title: str

        obj = Artifact(schema_version=CURRENT_SCHEMA_VERSION, title="test")
        assert obj.schema_version == CURRENT_SCHEMA_VERSION

    def test_rejects_wrong_version(self):
        class Artifact(SchemaVersionedModel):
            title: str

        with pytest.raises(ValidationError) as exc:
            Artifact(schema_version=999, title="test")
        errors = exc.value.errors()
        assert any("schema_version" in str(e["loc"]) for e in errors)
        assert "999" in str(exc.value)
        assert str(CURRENT_SCHEMA_VERSION) in str(exc.value)

    def test_missing_version_is_error(self):
        class Artifact(SchemaVersionedModel):
            title: str

        with pytest.raises(ValidationError) as exc:
            Artifact(title="test")
        assert exc.value.errors()[0]["loc"] == ("schema_version",)
        assert exc.value.errors()[0]["type"] == "missing"

    def test_rejects_unknown_fields(self):
        class Artifact(SchemaVersionedModel):
            title: str

        with pytest.raises(ValidationError) as exc:
            Artifact(schema_version=CURRENT_SCHEMA_VERSION, title="ok", extra="bad")
        assert exc.value.errors()[0]["type"] == "extra_forbidden"

    def test_current_schema_version_is_one(self):
        assert CURRENT_SCHEMA_VERSION == 1
