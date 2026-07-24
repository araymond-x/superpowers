"""Unit matrix for spawn-handoff-session.sh (SDD auto-spawn tool).

The bash script is driven via subprocess with stub `cmux`, `claude-picker`, and
`claude-usage-pace` on a per-test PATH (harness in spawn_handoff_helpers.py).
Pattern mirrors test_context_gate_tier.py.
"""

import json
from pathlib import Path

FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"

# Contract facts frozen from live `cmux --help` (2026-07-22). If cmux renames a
# flag, the exact-argv assertions in later tasks must be updated too.
CMUX_NEW_WORKSPACE_FLAGS = ["--name", "--cwd", "--command", "--focus"]
CMUX_NOTIFY_FLAGS = ["--title", "--body"]
PICKER_CONTRACT_VERSION = "1"

# claude-picker exports FOUR forwarding vars on EVERY launch path (verified vs
# telemetry-exp launchers/claude-picker v1). The 4th (APPEND_PROMPT = base64 of
# the --append-system-prompt-file CONTENTS) is the designed remedy for a dead/temp
# append path and MUST be consumed (decode->rematerialize->substitute; Task 4).
# Telemetry-on = inherited CLAUDE_CODE_ENABLE_TELEMETRY=1 (via telemetry-vars.sh).
PICKER_EXPORTS = [
    "CLAUDE_CODE_PICKER_VERSION",
    "CLAUDE_CODE_PICKER_LABEL",
    "CLAUDE_CODE_PICKER_ARGS",
    "CLAUDE_CODE_PICKER_APPEND_PROMPT",
]


def test_fixtures_shape_matches_contract():
    valid = json.loads((FIX / "valid-manifest.json").read_text())
    assert valid["session"]["bundle_type"] == "work"
    assert valid["session"]["entry_skill"] == "superpowers:subagent-driven-development"
    assert "repo_id" in valid["project"]
    assert (
        json.loads((FIX / "wrong-type-manifest.json").read_text())["session"][
            "bundle_type"
        ]
        == "review"
    )
    assert (
        json.loads((FIX / "wrong-skill-manifest.json").read_text())["session"][
            "entry_skill"
        ]
        != "superpowers:subagent-driven-development"
    )
    assert (
        json.loads((FIX / "foreign-repo-manifest.json").read_text())["project"][
            "repo_id"
        ]
        == "/some/other/repo/.git"
    )
    assert (
        "CLAUDE_CODE_PICKER_APPEND_PROMPT" in PICKER_EXPORTS
    )  # 4th export is consumed (Task 4)
