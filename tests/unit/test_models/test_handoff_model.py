"""Tests for HandoffPackage Pydantic model."""
import pytest
from pydantic import ValidationError

from handoff import HandoffPackage, FieldType, FormatRule, Sample
from _base import CURRENT_SCHEMA_VERSION


MINIMAL_HANDOFF = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "package_name": "test-package",
    "feeds_into": "brainstorming",
    "one_sentence_purpose": "Test handoff for unit tests.",
    "contract_constraints": [
        {"name": "amount", "kind": "float"},
    ],
    "samples": [
        {"path": "samples/example.csv", "description": "Example data"},
    ],
}


class TestHandoffGoldenInput:
    def test_minimal_handoff_parses(self):
        pkg = HandoffPackage.model_validate(MINIMAL_HANDOFF)
        assert pkg.package_name == "test-package"
        assert len(pkg.samples) == 1

    def test_roundtrip_through_json(self):
        pkg = HandoffPackage.model_validate(MINIMAL_HANDOFF)
        reparsed = HandoffPackage.model_validate(pkg.model_dump())
        assert reparsed == pkg


class TestHandoffFieldValidation:
    def test_missing_package_name_fails(self):
        data = {k: v for k, v in MINIMAL_HANDOFF.items() if k != "package_name"}
        with pytest.raises(ValidationError) as exc:
            HandoffPackage.model_validate(data)
        assert exc.value.errors()[0]["loc"] == ("package_name",)

    def test_invalid_field_type_kind_fails(self):
        data = {**MINIMAL_HANDOFF, "contract_constraints": [{"name": "x", "kind": "complex"}]}
        with pytest.raises(ValidationError) as exc:
            HandoffPackage.model_validate(data)
        assert exc.value.errors()[0]["type"] == "literal_error"

    @pytest.mark.parametrize("kind", ["string", "integer", "float", "boolean", "date", "enum"])
    def test_all_valid_field_type_kinds(self, kind):
        data = {**MINIMAL_HANDOFF, "contract_constraints": [{"name": "x", "kind": kind}]}
        pkg = HandoffPackage.model_validate(data)
        assert pkg.contract_constraints[0].kind == kind

    def test_extra_field_rejected(self):
        data = {**MINIMAL_HANDOFF, "bogus": "nope"}
        with pytest.raises(ValidationError) as exc:
            HandoffPackage.model_validate(data)
        assert exc.value.errors()[0]["type"] == "extra_forbidden"

    def test_field_type_nullable_default_false(self):
        data = {**MINIMAL_HANDOFF}
        pkg = HandoffPackage.model_validate(data)
        assert pkg.contract_constraints[0].nullable is False

    def test_field_type_format_hint_optional(self):
        data = {**MINIMAL_HANDOFF, "contract_constraints": [
            {"name": "date", "kind": "date", "format_hint": "YYYY-MM-DD"},
        ]}
        pkg = HandoffPackage.model_validate(data)
        assert pkg.contract_constraints[0].format_hint == "YYYY-MM-DD"


class TestFormatRulesValidation:
    def test_undeclared_field_in_applies_to_fails(self):
        data = {**MINIMAL_HANDOFF, "format_rules": [
            {"applies_to": ["nonexistent"], "rule": "must be positive"},
        ]}
        with pytest.raises(ValidationError, match="aren't declared"):
            HandoffPackage.model_validate(data)

    def test_declared_field_in_applies_to_passes(self):
        data = {**MINIMAL_HANDOFF, "format_rules": [
            {"applies_to": ["amount"], "rule": "must be positive"},
        ]}
        pkg = HandoffPackage.model_validate(data)
        assert len(pkg.format_rules) == 1


class TestAtLeastOneSample:
    def test_empty_samples_fails(self):
        data = {**MINIMAL_HANDOFF, "samples": []}
        with pytest.raises(ValidationError, match="at least one sample"):
            HandoffPackage.model_validate(data)

    def test_one_sample_passes(self):
        pkg = HandoffPackage.model_validate(MINIMAL_HANDOFF)
        assert len(pkg.samples) == 1
