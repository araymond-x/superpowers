"""Contract verification for Phase 2 models.

Anchors implementation to ground-truth spec facts.
Must pass before any model code is written.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "skills" / "scripts" / "models"))

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "reports" / "contracts"


def test_schema_facts_file_exists():
    assert (FIXTURES_DIR / "schema_facts.json").is_file()


def test_schema_facts_has_required_structure():
    with open(FIXTURES_DIR / "schema_facts.json") as f:
        facts = json.load(f)
    assert "implementer_report" in facts
    assert "checkpoint_result" in facts
    assert "current_schema_version" in facts


def test_base_classes_importable():
    from _base import CURRENT_SCHEMA_VERSION, StrictModel, SchemaVersionedModel
    assert CURRENT_SCHEMA_VERSION == 1
    assert hasattr(StrictModel, "model_config")
    assert hasattr(SchemaVersionedModel, "model_fields")


def test_schema_version_matches_base():
    from _base import CURRENT_SCHEMA_VERSION
    with open(FIXTURES_DIR / "schema_facts.json") as f:
        facts = json.load(f)
    assert facts["current_schema_version"] == CURRENT_SCHEMA_VERSION


def test_implementer_report_status_values_complete():
    with open(FIXTURES_DIR / "schema_facts.json") as f:
        facts = json.load(f)
    expected = {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"}
    assert set(facts["implementer_report"]["status_values"]) == expected


def test_checkpoint_result_check_status_values_complete():
    with open(FIXTURES_DIR / "schema_facts.json") as f:
        facts = json.load(f)
    expected = {"PASS", "FAIL", "SKIP", "OK", "WARNING"}
    assert set(facts["checkpoint_result"]["check_status_values"]) == expected
