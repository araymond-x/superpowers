"""Implementer-path observation logging + session_id hoist proof."""
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


def _obs(tmp_path):
    log = Path(tmp_path) / "reports" / "context-observations.log"
    return log.read_text().splitlines() if log.is_file() else []


def test_implementer_logs_via_session_id_fallback(tmp_path):
    """No transcript_path -> the hoisted session_id drives probe resolution for
    an IMPLEMENTER dispatch. Pre-hoist this would be source=byte-proxy."""
    setup_full_sdd_workspace(str(tmp_path), total_tasks=4, completed_tasks=1)
    home = tmp_path / "home"
    proj = home / ".claude" / "projects" / "p"
    proj.mkdir(parents=True)
    (proj / "sess-1.jsonl").write_text((FIX / "below.jsonl").read_text())
    payload = make_hook_input("Implement task 1", prompt="You are implementing task 1",
                              session_id="sess-1", cwd=str(tmp_path))
    r = run_hook(payload, str(tmp_path), env_extra={"HOME": str(home)})
    assert r.returncode == 0
    lines = [ln for ln in _obs(tmp_path) if "type=implementer" in ln]
    assert lines and "source=probe" in lines[-1]


def test_fix_dispatch_logs_type_other(tmp_path):
    """A [task N fix] dispatch reaches the implementer tail but logs type=other."""
    setup_full_sdd_workspace(str(tmp_path), total_tasks=4, completed_tasks=1)
    payload = make_hook_input("[task 1 fix] address review", prompt="You are implementing task 1",
                              transcript_path=str(FIX / "below.jsonl"), cwd=str(tmp_path))
    r = run_hook(payload, str(tmp_path))
    assert r.returncode == 0
    assert any("type=other" in ln for ln in _obs(tmp_path))
