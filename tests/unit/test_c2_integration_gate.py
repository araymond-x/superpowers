"""C2: Integration-test gate — model, validate-plan WARNING, Check 10.
Run: .venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent / "skills/scripts/models")
)


class TestIntegrationTestModel:
    def test_valid_relative_path(self):
        from plan import IntegrationTest
        it = IntegrationTest(path="tests/integration/sdd-e2e-test.sh")
        assert it.path == "tests/integration/sdd-e2e-test.sh"

    def test_absolute_path_rejected(self):
        from plan import IntegrationTest
        with pytest.raises(ValueError, match="absolute"):
            IntegrationTest(path="/absolute/path/test.sh")

    def test_dotdot_path_rejected(self):
        from plan import IntegrationTest
        with pytest.raises(ValueError, match="\\.\\."):
            IntegrationTest(path="tests/../../../etc/passwd")

    def test_plan_integration_test_optional(self):
        from plan import Plan
        p = Plan(
            schema_version=1,
            feature_archetype="extension",
            tasks=[{"id": 1, "title": "T"}],
        )
        assert p.integration_test is None

    def test_plan_integration_test_present(self):
        from plan import Plan
        p = Plan(
            schema_version=1,
            feature_archetype="extension",
            tasks=[{"id": 1, "title": "T"}],
            integration_test={"path": "tests/e2e.sh"},
        )
        assert p.integration_test.path == "tests/e2e.sh"
