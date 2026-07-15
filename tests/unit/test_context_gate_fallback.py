"""Byte-proxy fallback escalation + compaction/retry tests."""

import os
import subprocess
from pathlib import Path

from sdd_test_helpers import make_hook_input, setup_full_sdd_workspace

ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = (
    ROOT
    / "skills"
    / "subagent-driven-development"
    / "scripts"
    / "sdd-pre-dispatch-hook.sh"
)
FIX = Path(__file__).parent / "fixtures" / "context-probe"


def run_hook(payload, cwd, env_extra=None):
    env = dict(os.environ)
    env.setdefault("SUPERPOWERS_ROOT", str(ROOT))
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _bad_probe(tmp_path):
    # missing transcript file AND no session_id -> probe fails -> byte-proxy.
    return make_hook_input(
        "Implement task 1",
        prompt="You are implementing task 1",
        transcript_path=str(FIX / "does-not-exist.jsonl"),
        cwd=str(tmp_path),
    )


def _seed(tmp_path, n):
    log = Path(tmp_path) / "reports" / "context-observations.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as f:
        for _ in range(n):
            f.write(
                "2026-01-01T00:00:00Z task=1 type=implementer tokens=1 source=byte-proxy tier=below action=fallback\n"
            )


def test_single_fallback_allows(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(
        _bad_probe(tmp_path),
        str(tmp_path),
        env_extra={"SUPERPOWERS_CTX_FALLBACK_STREAK": "3"},
    )
    assert r.returncode == 0
    assert (
        "source=byte-proxy"
        in (Path(tmp_path) / "reports" / "context-observations.log").read_text()
    )


def test_k_consecutive_fallbacks_block(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    _seed(tmp_path, 2)  # 2 prior + this = 3 = streak
    r = run_hook(
        _bad_probe(tmp_path),
        str(tmp_path),
        env_extra={"SUPERPOWERS_CTX_FALLBACK_STREAK": "3"},
    )
    assert r.returncode == 2 and "blind" in r.stderr.lower()


def test_probe_success_resets_streak(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    _seed(tmp_path, 5)
    with (Path(tmp_path) / "reports" / "context-observations.log").open("a") as f:
        f.write(
            "2026-01-01T00:01:00Z task=1 type=implementer tokens=250000 source=probe tier=below action=allow\n"
        )
    r = run_hook(
        _bad_probe(tmp_path),
        str(tmp_path),
        env_extra={"SUPERPOWERS_CTX_FALLBACK_STREAK": "3"},
    )
    assert r.returncode == 0  # this dispatch is only the 1st trailing fallback


def test_reading_across_compaction_resets_tier(tmp_path):
    """Post-compaction the reading DROPS (below fixture) -> tier=below -> allow."""
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(
        make_hook_input(
            "Implement task 1",
            prompt="You are implementing task 1",
            transcript_path=str(FIX / "below.jsonl"),
            cwd=str(tmp_path),
        ),
        str(tmp_path),
    )
    assert r.returncode == 0


def test_retry_after_block_still_blocks(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    p = make_hook_input(
        "Implement task 1",
        prompt="You are implementing task 1",
        transcript_path=str(FIX / "hard.jsonl"),
        cwd=str(tmp_path),
    )
    assert run_hook(p, str(tmp_path)).returncode == 2
    assert run_hook(p, str(tmp_path)).returncode == 2


def test_bypass_after_block_allows(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    p = make_hook_input(
        "Implement task 1",
        prompt="You are implementing task 1",
        transcript_path=str(FIX / "hard.jsonl"),
        cwd=str(tmp_path),
    )
    assert run_hook(p, str(tmp_path)).returncode == 2
    assert (
        run_hook(
            p, str(tmp_path), env_extra={"SUPERPOWERS_CTX_HANDOFF_BYPASS": "1"}
        ).returncode
        == 0
    )


def test_nondefault_streak_threshold_blocks_earlier(tmp_path):
    """SUPERPOWERS_CTX_FALLBACK_STREAK=2 -> 1 seeded fallback + this bad-probe dispatch
    (streak 2) blocks, proving the env override lowers the escalation threshold below
    the default 3."""
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    _seed(tmp_path, 1)  # 1 prior + this = 2 = the overridden streak
    r = run_hook(
        _bad_probe(tmp_path),
        str(tmp_path),
        env_extra={"SUPERPOWERS_CTX_FALLBACK_STREAK": "2"},
    )
    assert r.returncode == 2 and "blind" in r.stderr.lower()


def test_nondefault_streak_threshold_allows_below(tmp_path):
    """SUPERPOWERS_CTX_FALLBACK_STREAK=5 -> 3 seeded fallbacks + this bad-probe dispatch
    (streak 4 < 5) still allows, proving a raised threshold defers the block."""
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    _seed(tmp_path, 3)  # 3 prior + this = 4 < 5
    r = run_hook(
        _bad_probe(tmp_path),
        str(tmp_path),
        env_extra={"SUPERPOWERS_CTX_FALLBACK_STREAK": "5"},
    )
    assert r.returncode == 0
