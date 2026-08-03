"""write-mechanics-card.py — deterministic successor mechanics card."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "skills" / "subagent-driven-development" / "scripts"
CARD = SCRIPTS / "write-mechanics-card.py"
VENV_PY = str(ROOT / ".venv" / "bin" / "python3")


def _fixture_feature(tmp_path):
    """git repo + feature dir + manifest + hop state + observation log + spawn log.
    Manifest content comes from the REAL materializer (drift here is exactly what
    the golden test must catch), then `handoff` and `context_summary_at` are
    pinned for determinism."""
    wt = tmp_path / "wt"
    feat = wt / "docs" / "imp-plans" / "feat"
    reports = feat / "reports"
    reports.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=wt, check=True)
    _materialize_minimal_plan(wt, feat)
    (reports / ".handoff-hops").write_text("1\n")
    (reports / "handoff-spawn.log").write_text(
        "2026-07-30T01:00:00Z u1 intent hop=1 tasks_done=0\n"
        "2026-07-30T01:01:00Z u1 outcome hop=1 workspace=workspace:5 surface=surface:7 "
        "launch=auto bundle=b1 quota=ok tasks_done=0 handshake=ok\n")
    (reports / "context-observations.log").write_text(
        "2026-07-30T01:02:00Z task=3 type=implementer tokens=250000 source=probe tier=below action=allow\n")
    return wt, feat, reports


def _run_card(wt, feat):
    import os
    env = {k: v for k, v in os.environ.items() if not k.startswith("SUPERPOWERS_CMUX_")}
    # ambient knobs (e.g. MAX_HOPS) would skew the card's ceiling line
    return subprocess.run(
        [VENV_PY, str(CARD), "--manifest", str(feat / ".sdd-session.json")],
        cwd=wt, capture_output=True, text=True, env=env)


def _materialize_minimal_plan(wt, feat):
    feat.mkdir(parents=True, exist_ok=True)
    tasks = "\n".join(f"  - id: {i}\n    title: t{i}" for i in range(5))
    (feat / "plan.md").write_text(
        f"---\nschema_version: 1\nfeature_archetype: extension\ntasks:\n{tasks}\n---\n# p\n")
    subprocess.run([VENV_PY, str(SCRIPTS / "materialize-manifest.py"),
                    "--plan-file", str(feat / "plan.md"), "--feature-dir", str(feat)],
                   cwd=wt, check=True)
    mpath = feat / ".sdd-session.json"
    m = json.loads(mpath.read_text())
    m["handoff"] = {"expected_hops": 2, "spawn_policy": "auto"}
    m["enforcement"]["context_summary_at"] = 2
    mpath.write_text(json.dumps(m))


def test_card_deterministic_with_contents(tmp_path):
    wt, feat, reports = _fixture_feature(tmp_path)
    assert _run_card(wt, feat).returncode == 0
    card = (reports / "handoff-mechanics.md").read_text()
    assert _run_card(wt, feat).returncode == 0
    assert (reports / "handoff-mechanics.md").read_text() == card    # deterministic
    assert "controller-checkpoint.py" in card and "--phase pre-dispatch" in card \
        and "--phase pre-completion" in card and "--manifest" in card \
        and "--deviations-file" in card and "--reports-dir" in card   # N35: both hard-required even in manifest mode
    assert "docs/imp-plans/feat/plan.md" in card and "deviations.md" in card
    assert re.search(r"hops used:\s*1", card) and re.search(r"expected:\s*2", card) \
        and re.search(r"ceiling:\s*6", card)
    assert "tokens=250000" in card                       # last observation line
    assert "context summary due at task 2" in card       # Check 6b midpoint status
    assert "workspace:5" in card and "surface:7" in card
    assert "/rename" in card and "/rc" in card and "context-handoff-protocol.md" in card


def test_report_skeleton_passes_validate_report(tmp_path):
    wt, feat, reports = _fixture_feature(tmp_path)
    _run_card(wt, feat)
    card = (reports / "handoff-mechanics.md").read_text()
    fence = "`" * 3          # composed, so this test can live inside fenced plan docs
    m = re.search(fence + r"markdown\n(---\n.*?)\n" + fence, card, re.S)
    assert m, "card must fence the report skeleton"
    skel = tmp_path / "task-999-implementer-report.md"
    skel.write_text(m.group(1) + "\n")
    r = subprocess.run([VENV_PY, str(SCRIPTS / "validate-report.py"), "--report-file", str(skel)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_missing_inputs_degrade_not_crash(tmp_path):
    wt, feat, reports = _fixture_feature(tmp_path)
    (reports / "context-observations.log").unlink()
    (reports / "handoff-spawn.log").unlink()
    assert _run_card(wt, feat).returncode == 0
    assert "(none recorded)" in (reports / "handoff-mechanics.md").read_text()


def test_byte_proxy_interference_invariant():
    """Spec: card IS counted by the byte-proxy (ctx_byte_estimate sums
    reports/*.md — real context) but collides with NO task-report glob. Pinned
    against the ACTUAL hook text so a glob change is caught. (The prior fenced
    form asserted fnmatch facts about a string literal only — vacuous, could
    never fail; amended pre-dispatch per the Task 11 fence-vs-prose discipline.)"""
    import fnmatch
    hook = (ROOT / "skills" / "subagent-driven-development" / "scripts"
            / "sdd-pre-dispatch-hook.sh").read_text()
    name = "handoff-mechanics.md"
    # ctx_byte_estimate() globs "$REPORTS_DIR"/*.md — the card lands there, counted.
    assert '"$REPORTS_DIR"/*.md' in hook
    assert fnmatch.fnmatch(name, "*.md")
    # task_report_glob() is task-${padded}-${report_type}* — card must not masquerade.
    assert 'task-${padded}-${report_type}' in hook
    assert not fnmatch.fnmatch(name, "task-*")
    assert not any(fnmatch.fnmatch(name, p) for p in
                   ("pre-execution-audit*", "context-summary*", "checkpoint-pre-dispatch*"))
