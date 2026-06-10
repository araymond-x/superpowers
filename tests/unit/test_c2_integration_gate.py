"""C2: Integration-test gate — model, validate-plan WARNING, Check 10.
Run: .venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py -v
"""
import pytest

from plan import IntegrationTest, Plan


class TestIntegrationTestModel:
    def test_valid_relative_path(self):
        it = IntegrationTest(path="tests/integration/sdd-e2e-test.sh")
        assert it.path == "tests/integration/sdd-e2e-test.sh"

    def test_absolute_path_rejected(self):
        with pytest.raises(ValueError, match="absolute"):
            IntegrationTest(path="/absolute/path/test.sh")

    def test_dotdot_path_rejected(self):
        with pytest.raises(ValueError, match="\\.\\."):
            IntegrationTest(path="tests/../../../etc/passwd")

    def test_empty_path_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            IntegrationTest(path="")

    def test_bare_dotdot_rejected(self):
        with pytest.raises(ValueError, match="\\.\\."):
            IntegrationTest(path="..")

    def test_plan_integration_test_optional(self):
        p = Plan(
            schema_version=1,
            feature_archetype="extension",
            tasks=[{"id": 1, "title": "T"}],
        )
        assert p.integration_test is None

    def test_plan_integration_test_present(self):
        p = Plan(
            schema_version=1,
            feature_archetype="extension",
            tasks=[{"id": 1, "title": "T"}],
            integration_test={"path": "tests/e2e.sh"},
        )
        assert p.integration_test.path == "tests/e2e.sh"
