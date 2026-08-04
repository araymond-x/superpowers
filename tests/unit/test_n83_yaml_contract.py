"""N83 contract: PyYAML coercion ground truth + current reader shapes.

These assertions are STABLE facts the N83 fix rests on. They do not assert the
pre-fix model rejection (Task 1 replaces that with the post-fix coercion).
"""
import os
import sys

import yaml

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")
sys.path.insert(0, os.path.abspath(FIXTURES))
from n83_yaml_cases import YAML_SCALAR_CASES  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_pyyaml_coerces_unquoted_off_to_false():
    for raw, expected in YAML_SCALAR_CASES:
        got = yaml.safe_load(f"handoff_spawn: {raw}")["handoff_spawn"]
        assert got == expected and type(got) is type(expected), (
            f"handoff_spawn: {raw} -> {got!r} (expected {expected!r})"
        )


def test_plan_model_has_handoff_spawn_literal():
    p = os.path.join(REPO, "skills", "scripts", "models", "plan.py")
    src = open(p, encoding="utf-8").read()
    assert 'handoff_spawn: Literal["auto", "ask", "off"] = "auto"' in src


def test_sdd_session_has_spawn_policy_literal():
    p = os.path.join(REPO, "skills", "scripts", "models", "sdd_session.py")
    src = open(p, encoding="utf-8").read()
    assert 'SpawnPolicy = Literal["auto", "ask", "off"]' in src
    assert "spawn_policy: SpawnPolicy" in src


def test_materialize_reads_handoff_spawn_from_frontmatter():
    p = os.path.join(REPO, "skills", "subagent-driven-development", "scripts",
                     "materialize-manifest.py")
    src = open(p, encoding="utf-8").read()
    assert 'frontmatter.get("handoff_spawn")' in src


def test_script_emits_policy_off_reason():
    p = os.path.join(REPO, "skills", "subagent-driven-development", "scripts",
                     "spawn-handoff-session.sh")
    src = open(p, encoding="utf-8").read()
    assert "reason=policy-off" in src
