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


def _large_transcript(tmp_path, imperative, pad_lines=3000):
    """Write a LARGE JSONL transcript: imperative on line 1, then many padding
    `"role":"user"` lines so the *filtered* grep output exceeds the 64KB pipe
    buffer.

    The C1 SIGPIPE bug only reproduces when (a) the SDD imperative matches EARLY
    (line 1) so the downstream `grep -q` exits while the upstream grep is still
    streaming, and (b) the upstream grep's OUTPUT — not just raw file size —
    exceeds the ~64KB pipe buffer, forcing the upstream to block on write and
    then take SIGPIPE (exit 141 → pipefail → if-false → fails to block).

    Each padding line contains the literal `"role":"user"` so it survives the
    upstream filter. ~3000 lines at ~70 bytes each yields ~200KB of filtered
    output, comfortably over the 64KB buffer (matches the smallest size the
    controller independently re-tests).
    """
    sep = (",", ":")
    lines = [json.dumps({"role": "user", "content": imperative}, separators=sep)]
    pad = json.dumps({"role": "user", "content": "padding line for buffer overflow xxxxx"},
                     separators=sep)
    lines.extend([pad] * pad_lines)
    p = tmp_path / "transcript-large.jsonl"
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


# ─── C1 regression: large transcript must still BLOCK ──────────────────────
# Defect C1: the piped `grep ... | grep -q` SDD detection takes SIGPIPE (141)
# under `set -o pipefail` once the upstream grep's output exceeds the ~64KB
# pipe buffer, so the hook fails to block on every real (large) transcript.
def test_blocks_on_large_transcript(tmp_path):
    t = _large_transcript(tmp_path, "please invoke subagent-driven-development")
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 2, f"large transcript must block; stdout={r.stdout} stderr={r.stderr}"
    assert "subagent-driven-development" in r.stderr


# ─── I1 regression: regex word-boundary false positives must NOT block ─────
# Defect I1: missing `\b` before the verb group and after the `sdd` group let
# `use` match inside `reuse`/`misuse` and `sdd` match inside `assddata`.
def test_reuse_does_not_block(tmp_path):
    t = _transcript(tmp_path, "please reuse the sdd module here", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0, f"'reuse' must not match 'use'; stderr={r.stderr}"


def test_misuse_does_not_block(tmp_path):
    t = _transcript(tmp_path, "misuse sdd here", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0, f"'misuse' must not match 'use'; stderr={r.stderr}"


def test_embedded_sdd_does_not_block(tmp_path):
    t = _transcript(tmp_path, "use the assddata module", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0, f"'assddata' must not match 'sdd'; stderr={r.stderr}"
