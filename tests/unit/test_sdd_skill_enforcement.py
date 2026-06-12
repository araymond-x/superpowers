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


# ─── tool_result contamination: SDD phrase in tool results must NOT block ──
# Root cause of the Plane PM false positive (2026-06-12):
# - hook's own error message ("invoke superpowers:subagent-driven-development")
#   is stored as an is_error=True tool_result in a user-role JSONL entry
# - pickup bundle content is stored as a tool_result in a user-role entry
# Both are user-role entries, so the SDD detection grep matches them as if
# the user had requested SDD. Filtering out "type":"tool_result" lines fixes this.

def _transcript_with_tool_result(tmp_path, tool_result_text, is_error=False,
                                  user_text="fix the login bug"):
    """Write a JSONL transcript where the SDD phrase appears ONLY in a tool_result
    block (not in a direct user text message). Simulates the hook's own error
    message or a pickup bundle being stored in the transcript."""
    sep = (",", ":")
    # Real user message (no SDD mention)
    user_line = json.dumps({"role": "user", "content": user_text}, separators=sep)
    # Tool result stored as user-role entry (how Claude Code stores tool results)
    tool_result_line = json.dumps({
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": "toolu_test123",
            "content": tool_result_text,
            "is_error": is_error,
        }],
    }, separators=sep)
    p = tmp_path / "transcript.jsonl"
    p.write_text(user_line + "\n" + tool_result_line + "\n")
    return str(p)


def test_hook_error_message_does_not_poison_subsequent_edits(tmp_path):
    """The hook's own error message stored as is_error tool_result must not cause
    all subsequent edits to be blocked (self-reinforcing loop)."""
    hook_error = ("BLOCKED: The user requested subagent-driven-development but you have "
                  "not loaded the skill via the Skill tool. Load the skill now: "
                  "invoke superpowers:subagent-driven-development.")
    t = _transcript_with_tool_result(tmp_path, hook_error, is_error=True)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0, (
        "hook error message stored as tool_result must NOT trigger SDD detection; "
        f"stderr={r.stderr}"
    )


def test_pickup_bundle_sdd_mention_does_not_block(tmp_path):
    """Pickup bundle continuation text stored as tool_result must not trigger
    SDD detection in an unrelated project session."""
    pickup_content = ("From this worktree, invoke superpowers:subagent-driven-development "
                      "via the Skill tool. During SDD ingestion...")
    t = _transcript_with_tool_result(tmp_path, pickup_content, is_error=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0, (
        "pickup bundle tool_result must NOT trigger SDD detection; "
        f"stderr={r.stderr}"
    )


def test_user_text_sdd_still_blocks_despite_tool_result_filter(tmp_path):
    """Regression: real user text requesting SDD must still block even when
    a tool_result is also in the transcript."""
    sep = (",", ":")
    # Real user SDD request
    user_line = json.dumps({"role": "user", "content": "invoke subagent-driven-development"},
                           separators=sep)
    # Tool result also present (should not affect detection of user request)
    tool_result_line = json.dumps({
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "some output"}],
    }, separators=sep)
    p = tmp_path / "transcript.jsonl"
    p.write_text(user_line + "\n" + tool_result_line + "\n")
    r = run_hook("src/app/feature.py", str(p))
    assert r.returncode == 2, (
        "real user SDD request must still block even with tool_result in transcript; "
        f"stderr={r.stderr}"
    )


# ─── Path exclusion: .env files in api/ dirs must not trigger hook ──────────
# Root cause: apps/api/.env matched (^|/)api/ because /api/ appears as a
# path segment. A .env file is a config file, not implementation code.

def test_env_file_in_api_dir_does_not_trigger_impl_check(tmp_path):
    """apps/api/.env should be excluded as a config file before SDD detection,
    even though the path contains the /api/ segment."""
    t = _transcript(tmp_path, "invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("apps/api/.env", t)
    assert r.returncode == 0, (
        "apps/api/.env is a config file and must not trigger the implementation "
        f"file check; stderr={r.stderr}"
    )
