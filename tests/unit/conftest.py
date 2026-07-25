"""Pytest configuration — Pydantic model import path + hermetic picker env."""

import sys
from pathlib import Path

import pytest

MODELS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "skills" / "scripts" / "models"
)
sys.path.insert(0, str(MODELS_DIR))

# The forwarding metadata the spawn-handoff tests exercise is REAL ambient env on
# any machine whose own session was launched through claude-picker (the
# developer's is). Since run_spawn snapshots os.environ, an "absent var" case
# would silently inherit that live value — telemetry-off and append-prompt-empty
# would both test the opposite of what they claim.
#
# Lives in conftest.py, not in test_spawn_handoff.py, so the scrub is not
# module-scoped: a spawn-handoff test written in ANY other file inherits it too.
# That is not hypothetical — a throwaway probe in a separate file once picked up
# the ambient leak and produced a wrong review finding.
PICKER_ENV_VARS = [
    "CLAUDE_CODE_PICKER_VERSION",
    "CLAUDE_CODE_PICKER_LABEL",
    "CLAUDE_CODE_PICKER_ARGS",
    "CLAUDE_CODE_PICKER_APPEND_PROMPT",
    "CLAUDE_CODE_ENABLE_TELEMETRY",
]


@pytest.fixture(autouse=True)
def _hermetic_picker_env(monkeypatch):
    for var in PICKER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
