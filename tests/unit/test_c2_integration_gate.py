"""C2: Integration-test gate — model, validate-plan WARNING, Check 10.
Run: .venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py -v
"""
import importlib.util
import os

import pytest

from plan import IntegrationTest, Plan

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_script(name, filename):
    path = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_vp = _load_script("validate_plan_c2", "validate-plan.py")

# SELF-HOSTING GUARD: _H avoids plan-validator false match on task headers in fixtures.
_H = "##" + "# Task"

RISK_PLAN = (
    "---\nschema_version: 1\nfeature_archetype: extension\n"
    "tasks:\n  - id: 1\n    title: Add auth middleware\n---\n"
    f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
    f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
)

SAFE_PLAN_WITH_INTEGRATION = (
    "---\nschema_version: 1\nfeature_archetype: extension\n"
    "integration_test:\n  path: tests/e2e.sh\n"
    "tasks:\n  - id: 1\n    title: Add auth middleware\n---\n"
    f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
    f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
)


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


class TestC2RiskSurfaceWarning:
    def test_risk_pattern_no_integration_test_warns(self):
        result = _vp.validate_plan(RISK_PLAN)
        assert any("integration" in w.lower() or "risk" in w.lower()
                    for w in result["warnings"])

    def test_risk_pattern_with_integration_test_no_warn(self):
        result = _vp.validate_plan(SAFE_PLAN_WITH_INTEGRATION)
        risk_warns = [w for w in result["warnings"]
                      if "integration" in w.lower() and "risk" in w.lower()]
        assert len(risk_warns) == 0

    def test_no_risk_pattern_no_warn(self):
        no_risk = (
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            "tasks:\n  - id: 1\n    title: Add utility\n---\n"
            f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
            f"{_H} 1: Add utility\n- [ ] Do it\n"
        )
        result = _vp.validate_plan(no_risk)
        risk_warns = [w for w in result["warnings"]
                      if "integration" in w.lower() and "risk" in w.lower()]
        assert len(risk_warns) == 0

    def test_frontmatterless_plan_with_risk_warns(self):
        """No YAML frontmatter at all → frontmatter is None → still warns."""
        plan = (
            f"# Plan\n\n**Source Contracts:** None\n\n"
            f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
        )
        result = _vp.validate_plan(plan)
        assert any(w.startswith("integration_test_risk_surface")
                   for w in result["warnings"])
        section = result["sections"].get("integration_test_risk", {})
        assert section.get("status") == "WARNING"

    def test_explicit_null_integration_test_still_warns(self):
        """integration_test: null in frontmatter is not a declaration → still warns."""
        plan = (
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            "integration_test: null\n"
            "tasks:\n  - id: 1\n    title: Add auth middleware\n---\n"
            f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
            f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
        )
        result = _vp.validate_plan(plan)
        assert any(w.startswith("integration_test_risk_surface")
                   for w in result["warnings"])
        section = result["sections"].get("integration_test_risk", {})
        assert section.get("status") == "WARNING"
