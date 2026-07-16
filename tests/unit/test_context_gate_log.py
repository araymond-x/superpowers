"""Observation-log threading for non-implementer dispatches + append safety."""
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


def test_reviewer_dispatch_logs_one_line(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), total_tasks=4, completed_tasks=1)
    payload = make_hook_input("Spec compliance review for task 1",
                              transcript_path=str(FIX / "below.jsonl"), cwd=str(tmp_path))
    r = run_hook(payload, str(tmp_path))
    assert r.returncode == 0
    lines = _obs(tmp_path)
    assert len(lines) == 1
    assert "source=probe" in lines[0] and "tokens=250000" in lines[0]
    assert "type=spec-review" in lines[0] and "tier=below" in lines[0]


def test_append_failure_never_breaks_dispatch(tmp_path):
    """Unwritable reports/ (pre-created as a dir) -> stderr note, dispatch proceeds."""
    setup_full_sdd_workspace(str(tmp_path), total_tasks=4, completed_tasks=1)
    (Path(tmp_path) / "reports" / "context-observations.log").mkdir()
    payload = make_hook_input("Spec compliance review for task 1",
                              transcript_path=str(FIX / "below.jsonl"), cwd=str(tmp_path))
    assert run_hook(payload, str(tmp_path)).returncode == 0
