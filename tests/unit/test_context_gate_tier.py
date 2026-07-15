"""Two-tier nudge/block tests for the context gate (implementer path only)."""
import json
import os
import subprocess
from pathlib import Path

from sdd_test_helpers import make_hook_input, setup_full_sdd_workspace

ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = ROOT / "skills" / "subagent-driven-development" / "scripts" / "sdd-pre-dispatch-hook.sh"
FIX = Path(__file__).parent / "fixtures" / "context-probe"


def run_hook(payload, cwd, env_extra=None):
    env = dict(os.environ)
    env.setdefault("SUPERPOWERS_ROOT", str(ROOT))
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", str(HOOK)], input=payload, capture_output=True,
                          text=True, cwd=cwd, env=env)


def _impl(tmp_path, fixture, task=1):
    return make_hook_input(f"Implement task {task}", prompt=f"You are implementing task {task}",
                           transcript_path=str(FIX / fixture), cwd=str(tmp_path))


def test_below_allows(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(_impl(tmp_path, "below.jsonl"), str(tmp_path))
    assert r.returncode == 0 and "CONTEXT NUDGE" not in r.stdout


def test_soft_nudges(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(_impl(tmp_path, "soft.jsonl"), str(tmp_path))
    assert r.returncode == 0
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CONTEXT NUDGE" in ctx and "350000" in ctx


def test_hard_blocks(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(_impl(tmp_path, "hard.jsonl"), str(tmp_path))
    assert r.returncode == 2
    assert "do not retry" in r.stderr.lower()
    assert "context-handoff-protocol" in r.stderr


def test_reviewer_never_blocks_even_over_hard(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    payload = make_hook_input("Spec compliance review for task 1",
                              transcript_path=str(FIX / "hard.jsonl"), cwd=str(tmp_path))
    assert run_hook(payload, str(tmp_path)).returncode == 0


def test_marked_fix_never_blocks_even_over_hard(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    payload = make_hook_input("[task 1 fix] address review", prompt="You are implementing task 1",
                              transcript_path=str(FIX / "hard.jsonl"), cwd=str(tmp_path))
    assert run_hook(payload, str(tmp_path)).returncode == 0


def test_verification_task_is_eligible_for_block(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    plan = Path(tmp_path) / "docs" / "imp-plans" / "plan.md"
    plan.write_text(
        "---\nschema_version: 1\ntasks:\n  - id: 0\n    title: t0\n"
        "  - id: 1\n    title: t1\n    task_type: verification\n---\n\n"
        "**Source Contracts:** None\n\n### Task 1 -- verify\n- [ ] check\n")
    assert run_hook(_impl(tmp_path, "hard.jsonl"), str(tmp_path)).returncode == 2


def test_bypass_skips_gate(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(_impl(tmp_path, "hard.jsonl"), str(tmp_path),
                 env_extra={"SUPERPOWERS_CTX_HANDOFF_BYPASS": "1"})
    assert r.returncode == 0 and "BYPASS" in r.stderr.upper()
    assert "source=bypass" in (Path(tmp_path) / "reports" / "context-observations.log").read_text()


def test_env_override_lowers_threshold(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(_impl(tmp_path, "below.jsonl"), str(tmp_path),
                 env_extra={"SUPERPOWERS_CTX_SOFT_TOKENS": "100000", "SUPERPOWERS_CTX_HARD_TOKENS": "130000"})
    assert r.returncode == 2


def test_invalid_env_reverts_to_defaults(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(_impl(tmp_path, "below.jsonl"), str(tmp_path),
                 env_extra={"SUPERPOWERS_CTX_SOFT_TOKENS": "400000", "SUPERPOWERS_CTX_HARD_TOKENS": "300000"})
    assert r.returncode == 0 and "reverting to defaults" in r.stderr
