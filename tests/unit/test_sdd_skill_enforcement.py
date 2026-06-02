"""C5: sdd-skill-enforcement-hook.sh promoted to blocking.
Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_skill_enforcement.py -v
"""
import json
import os
import subprocess

HOOK_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "sdd-skill-enforcement-hook.sh",
))


def _transcript(tmp_path, user_text, skill_loaded=False):
    """Write a JSONL transcript with one user line (+ optional Skill tool line).

    IMPORTANT: emit COMPACT JSON (separators=(",", ":")). The hook greps the
    transcript for the literal `"role":"user"` and `"name":"Skill"` (no spaces) —
    matching real Claude Code transcripts. json.dumps' default spacing
    (`"role": "user"`) would NOT match the hook's grep, so the hook would
    short-circuit at its early `exit 0` and the block tests could never go GREEN.
    """
    sep = (",", ":")
    lines = [json.dumps({"role": "user", "content": user_text}, separators=sep)]
    if skill_loaded:
        lines.append(json.dumps({"role": "assistant",
                                 "content": [{"type": "tool_use", "name": "Skill",
                                              "input": {"skill": "superpowers:subagent-driven-development"}}]},
                                separators=sep))
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(lines) + "\n")
    return str(p)


def run_hook(file_path, transcript_path, env_extra=None):
    payload = json.dumps({"tool_input": {"file_path": file_path},
                          "transcript_path": transcript_path})
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", HOOK_PATH], input=payload,
                          capture_output=True, text=True, timeout=10, env=env)


def test_blocks_when_sdd_requested_skill_not_loaded(tmp_path):
    t = _transcript(tmp_path, "please invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 2, f"stdout={r.stdout} stderr={r.stderr}"
    assert "subagent-driven-development" in r.stderr


def test_allows_when_skill_loaded(tmp_path):
    t = _transcript(tmp_path, "let's use SDD", skill_loaded=True)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0


def test_casual_mention_does_not_block(tmp_path):
    t = _transcript(tmp_path, "I was reading about subagent-driven-development in the docs", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0


def test_non_impl_file_does_not_block(tmp_path):
    t = _transcript(tmp_path, "invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("docs/notes.md", t)
    assert r.returncode == 0


def test_bypass_env_var_recovers(tmp_path):
    t = _transcript(tmp_path, "invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("src/app/feature.py", t, env_extra={"SUPERPOWERS_SDD_BYPASS": "1"})
    assert r.returncode == 0
    assert "SUPERPOWERS_SDD_BYPASS" in r.stderr


def test_no_sdd_request_allows(tmp_path):
    t = _transcript(tmp_path, "fix the login bug", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0
