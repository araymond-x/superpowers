"""Tests for the validation error and YAML error formatters."""
import pytest
from pydantic import ValidationError

from errors import format_validation_error, format_yaml_error
from plan import Plan
from _base import CURRENT_SCHEMA_VERSION


class TestFormatValidationError:
    def _get_validation_error(self, data: dict) -> ValidationError:
        with pytest.raises(ValidationError) as exc:
            Plan.model_validate(data)
        return exc.value

    def test_header_contains_validation_failed(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test-plan.md")
        assert "VALIDATION FAILED" in output
        assert "test-plan.md" in output

    def test_shows_field_path(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test.md")
        assert "feature_archetype" in output

    def test_shows_issue_count(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test.md")
        assert "issue(s) found" in output

    def test_literal_error_shows_expected(self):
        err = self._get_validation_error({
            "schema_version": CURRENT_SCHEMA_VERSION,
            "feature_archetype": "bogus",
            "tasks": [{"id": 0, "title": "x"}],
        })
        output = format_validation_error(err, "test.md")
        assert "Expected:" in output

    def test_missing_field_shows_required(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test.md")
        assert "required" in output

    def test_missing_schema_version_shows_hint(self):
        err = self._get_validation_error({"feature_archetype": "greenfield", "tasks": []})
        output = format_validation_error(err, "test.md")
        assert "schema_version: 1" in output
        assert "Hint:" in output

    def test_box_drawing_borders_present(self):
        err = self._get_validation_error({"schema_version": CURRENT_SCHEMA_VERSION})
        output = format_validation_error(err, "test.md")
        assert "═" in output


class TestFormatYamlError:
    def test_header_contains_yaml_parse_failed(self):
        output = format_yaml_error(ValueError("bad yaml"), "test.md")
        assert "YAML PARSE FAILED" in output
        assert "test.md" in output

    def test_shows_exception_details(self):
        output = format_yaml_error(ValueError("unexpected ':'"), "test.md")
        assert "unexpected ':'" in output

    def test_notes_pydantic_not_attempted(self):
        output = format_yaml_error(ValueError("x"), "test.md")
        assert "Pydantic validation was not attempted" in output

    def test_distinct_from_validation_header(self):
        yaml_output = format_yaml_error(ValueError("x"), "test.md")
        assert "YAML PARSE FAILED" in yaml_output
        assert "VALIDATION FAILED" not in yaml_output
