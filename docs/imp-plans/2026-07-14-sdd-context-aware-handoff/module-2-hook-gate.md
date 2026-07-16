# Module 2 — Hook Context Gate

**Goal:** Wire `context-probe.py` into `sdd-pre-dispatch-hook.sh`: hoist `.session_id`, add shared probe/observation helpers threaded into every dispatch exit path, apply a two-tier nudge/block on the implementer new-task path only, and escalate to a block after K consecutive probe fallbacks. Retire Check 7's standalone warning by moving its byte-sum into the probe-failure fallback. Re-capture the hook baseline in the same commit as each hook edit.

**Source Contracts:** None

_This module consumes the internal `context-probe.py` CLI produced by Module 1 (`--transcript <path>` / `--session-id <id>` / `--json`; prints bare integer `total_tokens`; non-zero exit = unavailable) and the PreToolUse stdin payload fields `.transcript_path` / `.session_id` (mirror the sibling hook `sdd-skill-enforcement-hook.sh:~35`). These are internal/established interfaces — not new external contracts — so this module has no Task 0. The parent's "Shared Contract" section is the authoritative probe-CLI definition._

**Contract Constraints:**
- Nudge/block predicate: `IS_IMPLEMENTER && ! MARKED_FIX`. Verification tasks ARE eligible.
- Observation log at `reports/context-observations.log`; append best-effort (never breaks a dispatch).
- **Observation-log scope carve-out:** reviewer / re-review / passthrough / fix and every non-blocked implementer dispatch log exactly one line. An implementer dispatch that a **prior** enforcement check blocks (populates `ERRORS` → `exit 2` *before* the post-ERRORS context gate) does **not** log — this deliberately mirrors the spec's pre-parse early-exit exclusion (spec §5.3). Rationale: it keeps the context gate a single clean block placed *after* the ERRORS report (so a context block fires only at a clean boundary, never stranding a half-reviewed prior task) rather than splitting probe/log/gate across that boundary. A blocked dispatch is transient — the eventual clean re-dispatch logs at ~the same reading, so context-tuning (which consumes only `source=probe` rows) is unaffected.
- HARD block is its own `exit 2` with only the handoff message — NOT folded into `ERRORS[]`. Placed after the ERRORS report so it fires only at a clean boundary. The SOFT nudge appends to the existing `additionalContext` assembly.
- Probe invoked with system `python3` (stdlib-only); the hook holds no path-resolution logic.
- `SUPERPOWERS_CTX_HANDOFF_BYPASS` set → skip gate (stderr warning), log `source=bypass action=allow`.
- Thresholds parsed from env with defaults `SOFT=300000 HARD=400000 FALLBACK_STREAK=3`; non-numeric OR `HARD ≤ SOFT` → reset both to defaults with a stderr warning.

## File Map
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (Tasks 3, 4, 5, 6)
- Modify: `tests/unit/sdd_test_helpers.py` (Task 3 — extend `make_hook_input`)
- Create: `tests/unit/test_context_gate_log.py` (Task 3), `test_context_gate_impl_log.py` (Task 4), `test_context_gate_tier.py` (Task 5), `test_context_gate_fallback.py` (Task 6)
- Modify: `tests/ARaymond-hook-baseline/baseline.txt` (Tasks 3, 4, 5, 6 — re-capture each)

**Write-Scope Partitioning:**

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| 3 | hook, `sdd_test_helpers.py`, `test_context_gate_log.py`, `baseline.txt` | `context-probe.py`, sibling hook | 2 |
| 4 | hook, `test_context_gate_impl_log.py`, `baseline.txt` | `sdd_test_helpers.py` | 3 |
| 5 | hook, `test_context_gate_tier.py`, `baseline.txt` | `sdd_test_helpers.py` | 4 |
| 6 | hook, `test_context_gate_fallback.py`, `baseline.txt` | `sdd_test_helpers.py` | 5 |

**Baseline discipline (all four tasks):** editing the hook turns `check-hooks.sh` RED. Each task re-captures the baseline in its OWN commit (`bash tests/ARaymond-hook-baseline/check-hooks.sh --capture`) so every commit boundary is self-consistent. Do NOT assert a green `check-hooks.sh` before the re-capture step within a task.

---

### Task 3: Hoist session_id + helpers + thread into non-implementer exit paths

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
- Modify: `tests/unit/sdd_test_helpers.py`
- Create: `tests/unit/test_context_gate_log.py`
- Modify: `tests/ARaymond-hook-baseline/baseline.txt`
- Report: `.../reports/task-003-implementer-report.md`

**Pattern References:** `sdd-skill-enforcement-hook.sh:~35` (`.transcript_path` read); `estimate-task-tokens.py` call site (~hook L704, `python3` shellout); `tests/unit/test_sdd_classification.py` (subprocess hook run).

- [x] **Step 1: Extend the test seam — `make_hook_input`**

In `tests/unit/sdd_test_helpers.py`, add `transcript_path` + `session_id` (top-level payload fields — where the hook reads them):

```python
def make_hook_input(
    description: str,
    prompt: str = "",
    cwd: str = "",
    subagent_type: str = "",
    transcript_path: str = "",
    session_id: str = "",
) -> str:
    """PreToolUse payload. transcript_path / session_id are top-level fields."""
    tool_input: dict = {"description": description, "prompt": prompt}
    if subagent_type:
        tool_input["subagent_type"] = subagent_type
    payload = {"tool_input": tool_input, "cwd": cwd}
    if transcript_path:
        payload["transcript_path"] = transcript_path
    if session_id:
        payload["session_id"] = session_id
    return json.dumps(payload)
```

- [x] **Step 2: Write the failing non-implementer observation tests**

`tests/unit/test_context_gate_log.py`:

```python
"""Observation-log threading for non-implementer dispatches + append safety."""
import os, subprocess
from pathlib import Path
from sdd_test_helpers import make_hook_input, setup_full_sdd_workspace

ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = ROOT / "skills" / "subagent-driven-development" / "scripts" / "sdd-pre-dispatch-hook.sh"
FIX = Path(__file__).parent / "fixtures" / "context-probe"

def run_hook(payload, cwd, env_extra=None):
    env = dict(os.environ); env.setdefault("SUPERPOWERS_ROOT", str(ROOT))
    if env_extra: env.update(env_extra)
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
```

- [x] **Step 3: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_gate_log.py -v`
Expected: FAIL — no observation log written yet.

- [x] **Step 4: Threshold parsing + probe path constant**

Add this **after the `VALIDATE_REPORT_SCRIPT` line (~L41)** — it must come *after* `SUPERPOWERS_ROOT` is defined (L31), because `CONTEXT_PROBE_SCRIPT` references it and the hook runs under `set -u` (placing it before L31 aborts with `SUPERPOWERS_ROOT: unbound variable`):

```bash
CONTEXT_PROBE_SCRIPT="$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/context-probe.py"
CTX_SOFT="${SUPERPOWERS_CTX_SOFT_TOKENS:-300000}"
CTX_HARD="${SUPERPOWERS_CTX_HARD_TOKENS:-400000}"
CTX_STREAK="${SUPERPOWERS_CTX_FALLBACK_STREAK:-3}"
if ! [[ "$CTX_SOFT" =~ ^[0-9]+$ ]] || ! [[ "$CTX_HARD" =~ ^[0-9]+$ ]] || [ "$CTX_HARD" -le "$CTX_SOFT" ]; then
  echo "WARNING: invalid SUPERPOWERS_CTX thresholds (SOFT=$CTX_SOFT HARD=$CTX_HARD) — reverting to defaults 300000/400000." >&2
  CTX_SOFT=300000; CTX_HARD=400000
fi
[[ "$CTX_STREAK" =~ ^[0-9]+$ ]] || CTX_STREAK=3
CTX_T=0; CTX_SOURCE="probe"   # globals, set by ctx_probe_tokens before use
```

- [x] **Step 5: Hoist `.session_id` before classification**

The hook already declares `SESSION_ID=""` in the variable-init block (~L95). **REPLACE that initializer line** with the actual extraction (`INPUT` is parsed at L44, well before L95), so the value survives into classification:

```bash
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // ""' 2>/dev/null)
```

**Do NOT insert the extraction earlier** (e.g. right after `INPUT=$(cat)` at ~L44) — the `SESSION_ID=""` initializer at ~L95 would clobber it back to empty (the probe's `--session-id` fallback would then always receive `""`, always drop to byte-proxy, and Task 4's `test_implementer_logs_via_session_id_fallback` would fail). Replacing the L95 line is the single-edit, clobber-proof fix.

While in the var-init block, also add `OBS_LOG=""` and `CTX_NUDGE=""` alongside the other `""` initializers (~L82-98) for `set -u` hygiene (both are assigned real values only in manifest mode / the tier logic).

In the reviewer sentinel branch (~L200), delete the local `SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' ...)` reassignment and guard the sentinel hash with `${SESSION_ID:-unknown}` (uses the hoisted value).

- [x] **Step 6: Set `OBS_LOG` and define the helpers**

Inside the manifest block, right after `REPORTS_DIR=...` (~L108), add `    OBS_LOG="$REPORTS_DIR/context-observations.log"`. Then, after the manifest guard (~L142), before Stage 0, add the helpers:

```bash
ctx_byte_estimate() {  # repurposed Check-7 byte-sum (bytes/4 ~= tokens), advisory
  local total=0 sz
  for pf in "$MANIFEST_PLAN_FILE" "$MANIFEST_MODULE_FILE" "$DEVIATIONS_FILE"; do
    [ -n "$pf" ] && [ -f "$pf" ] && { sz=$(wc -c < "$pf" 2>/dev/null | tr -d ' '); total=$((total + sz)); }
  done
  if [ -d "$REPORTS_DIR" ]; then
    for rf in "$REPORTS_DIR"/*.md; do
      [ -f "$rf" ] && { sz=$(wc -c < "$rf" 2>/dev/null | tr -d ' '); total=$((total + sz)); }
    done
  fi
  echo $((total / 4))
}
ctx_tier() {  # $1=T -> below|soft|hard
  if [ "$1" -ge "$CTX_HARD" ] 2>/dev/null; then echo hard
  elif [ "$1" -ge "$CTX_SOFT" ] 2>/dev/null; then echo soft
  else echo below; fi
}
ctx_probe_tokens() {  # $1=transcript_path. Sets CTX_T + CTX_SOURCE. 0=probe, 1=fallback.
  local tpath="$1" out rc=1
  if [ -n "$tpath" ]; then
    out=$(python3 "$CONTEXT_PROBE_SCRIPT" --transcript "$tpath" 2>/dev/null); rc=$?
  elif [ -n "$SESSION_ID" ]; then
    out=$(python3 "$CONTEXT_PROBE_SCRIPT" --session-id "$SESSION_ID" 2>/dev/null); rc=$?
  fi
  if [ "$rc" -eq 0 ] && [[ "$out" =~ ^[0-9]+$ ]]; then
    CTX_T="$out"; CTX_SOURCE="probe"; return 0
  fi
  CTX_T=$(ctx_byte_estimate); CTX_SOURCE="byte-proxy"; return 1
}
ctx_log() {  # $1=type $2=source $3=tier $4=action $5=tokens
  local line
  line="$(date -u +%Y-%m-%dT%H:%M:%SZ) task=${TASK_NUMBER:-} type=$1 tokens=$5 source=$2 tier=$3 action=$4"
  { mkdir -p "$REPORTS_DIR" && printf '%s\n' "$line" >> "$OBS_LOG"; } 2>/dev/null \
    || echo "WARNING: context-observations append failed ($OBS_LOG)" >&2
}
ctx_observe_and_log() {  # $1=dispatch type. Probe + log only (no nudge/block).
  local dtype="$1" tpath
  if [ -n "${SUPERPOWERS_CTX_HANDOFF_BYPASS:-}" ]; then ctx_log "$dtype" bypass below allow 0; return; fi
  tpath=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null)
  if ctx_probe_tokens "$tpath"; then
    ctx_log "$dtype" probe "$(ctx_tier "$CTX_T")" allow "$CTX_T"
  else
    ctx_log "$dtype" byte-proxy "$(ctx_tier "$CTX_T")" fallback "$CTX_T"
  fi
}
```

- [x] **Step 7: Thread into the non-implementer exit paths + remove Check 7**

Add just before each non-implementer `exit 0`:
- Re-review branch (~L165): `ctx_observe_and_log other`
- Reviewer branch (~L208): `REVIEW_TYPE_LOG="${REVIEW_TYPE}"; [ "$REVIEW_TYPE_LOG" = "unknown" ] && REVIEW_TYPE_LOG=other; ctx_observe_and_log "$REVIEW_TYPE_LOG"`
- Passthrough Stage-3 branch (~L242): `ctx_observe_and_log other`

Then DELETE Check 7's standalone block (~L754–789) and its injection (~L814–816). Verify no orphans:

Run: `grep -n 'CONTEXT_LOAD_WARNING' skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
Expected: no matches (remove the now-unused `CONTEXT_LOAD_WARNING_BYTES` constant too if orphaned).

- [x] **Step 8: Run the non-implementer tests + regression — expect PASS**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_gate_log.py tests/unit/test_sdd_classification.py tests/unit/test_sdd_hook_hardening.py -q`
Expected: PASS (reviewer/passthrough log; existing hook behavior unbroken).

- [x] **Step 9: Re-capture baseline and commit**

```bash
bash tests/ARaymond-hook-baseline/check-hooks.sh --capture
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh \
  tests/unit/sdd_test_helpers.py tests/unit/test_context_gate_log.py \
  tests/ARaymond-hook-baseline/baseline.txt
git commit -m "feat(sdd-ctx): hoist session_id + context helpers threaded into non-implementer exits"
```

---

### Task 4: Implementer-path observation logging + hoist proof

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
- Create: `tests/unit/test_context_gate_impl_log.py`
- Modify: `tests/ARaymond-hook-baseline/baseline.txt`
- Report: `.../reports/task-004-implementer-report.md`

- [x] **Step 1: Write the failing implementer-log tests**

`tests/unit/test_context_gate_impl_log.py`:

```python
"""Implementer-path observation logging + session_id hoist proof."""
import os
import subprocess
from pathlib import Path

from sdd_test_helpers import make_hook_input, setup_full_sdd_workspace

ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = ROOT / "skills" / "subagent-driven-development" / "scripts" / "sdd-pre-dispatch-hook.sh"
FIX = Path(__file__).parent / "fixtures" / "context-probe"


def run_hook(payload, cwd, env_extra=None):
    env = dict(os.environ); env.setdefault("SUPERPOWERS_ROOT", str(ROOT))
    if env_extra: env.update(env_extra)
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
```

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_gate_impl_log.py -v`
Expected: FAIL — implementer path not wired yet.

- [x] **Step 3: Thread the implementer-tail log stub**

After the `ERRORS[@]` report block (~L752, where the implementer path is guaranteed and ERRORS is empty), add:

```bash
# Context observation for the implementer/fix dispatch (logged once).
# Task 5 replaces this stub with the full nudge/block tier logic.
if [ "$IS_IMPLEMENTER" = true ]; then
  if [ "$MARKED_FIX" = true ]; then
    ctx_observe_and_log other        # fix dispatch: log only, never gated
  else
    ctx_observe_and_log implementer
  fi
fi
```

- [x] **Step 4: Run the implementer-log tests + regression — expect PASS**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_gate_impl_log.py tests/unit/test_context_gate_log.py tests/unit/test_sdd_hard_gates.py -q`
Expected: PASS.

- [x] **Step 5: Re-capture baseline and commit**

```bash
bash tests/ARaymond-hook-baseline/check-hooks.sh --capture
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh \
  tests/unit/test_context_gate_impl_log.py tests/ARaymond-hook-baseline/baseline.txt
git commit -m "feat(sdd-ctx): observation logging on the implementer dispatch path"
```

---

### Task 5: Nudge/block tier in the implementer new-task path

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
- Create: `tests/unit/test_context_gate_tier.py`
- Modify: `tests/ARaymond-hook-baseline/baseline.txt`
- Report: `.../reports/task-005-implementer-report.md`

- [x] **Step 1: Write the failing tier tests**

`tests/unit/test_context_gate_tier.py`:

```python
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
    env = dict(os.environ); env.setdefault("SUPERPOWERS_ROOT", str(ROOT))
    if env_extra: env.update(env_extra)
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
```

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_gate_tier.py -v`
Expected: FAIL — the Task-4 stub logs but never nudges/blocks.

- [x] **Step 3: Replace the Task-4 stub with the full tier logic**

Replace the Task-4 implementer-tail block (after the ERRORS report) with:

```bash
# ─── Context-pressure gate (implementer new-task path only) ───────────────
if [ "$IS_IMPLEMENTER" = true ]; then
  if [ "$MARKED_FIX" = true ]; then
    ctx_observe_and_log other            # fix dispatch: log only, never gated
  elif [ -n "${SUPERPOWERS_CTX_HANDOFF_BYPASS:-}" ]; then
    echo "WARNING: SUPERPOWERS_CTX_HANDOFF_BYPASS set — context gate skipped." >&2
    ctx_log implementer bypass below allow 0
  else
    TPATH=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null)
    if ctx_probe_tokens "$TPATH"; then
      CTX_TIER=$(ctx_tier "$CTX_T")
      if [ "$CTX_TIER" = hard ]; then
        ctx_log implementer probe hard block "$CTX_T"
        echo "BLOCKED (context): controller context is ~$CTX_T tokens (>= HARD $CTX_HARD). Do NOT retry this dispatch — retrying is wrong. This is a clean task boundary: commit pending state, build a fresh-session handoff (invoke the handoff skill, entry skill superpowers:subagent-driven-development), tell the user to start a fresh session from the worktree and run /pickup, then STOP. See skills/subagent-driven-development/references/context-handoff-protocol.md." >&2
        exit 2
      elif [ "$CTX_TIER" = soft ]; then
        ctx_log implementer probe soft nudge "$CTX_T"
        CTX_NUDGE="CONTEXT NUDGE: controller context is ~$CTX_T tokens — this is a clean task boundary. Consider handing off to a fresh session now (see references/context-handoff-protocol.md) rather than starting task ${TASK_NUMBER}."
      else
        ctx_log implementer probe below allow "$CTX_T"
      fi
    else
      ctx_log implementer byte-proxy "$(ctx_tier "$CTX_T")" fallback "$CTX_T"
    fi
  fi
fi
```

- [x] **Step 4: Append the soft nudge into `additionalContext`**

In the final `CONTEXT` assembly (~L810, alongside `TOKEN_WARNING`), add:

```bash
if [ -n "${CTX_NUDGE:-}" ]; then
  CONTEXT="$CONTEXT | $CTX_NUDGE"
fi
```

- [x] **Step 5: Run the tier tests + regression — expect PASS**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_gate_tier.py tests/unit/test_context_gate_impl_log.py tests/unit/test_context_gate_log.py tests/unit/test_sdd_hard_gates.py -q`
Expected: PASS.

- [x] **Step 6: Re-capture baseline and commit**

```bash
bash tests/ARaymond-hook-baseline/check-hooks.sh --capture
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh \
  tests/unit/test_context_gate_tier.py tests/ARaymond-hook-baseline/baseline.txt
git commit -m "feat(sdd-ctx): two-tier context nudge/block on implementer new-task path"
```

---

### Task 6: K-consecutive-fallback escalation

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
- Create: `tests/unit/test_context_gate_fallback.py`
- Modify: `tests/ARaymond-hook-baseline/baseline.txt`
- Report: `.../reports/task-006-implementer-report.md`

- [x] **Step 1: Write the failing fallback/escalation tests**

`tests/unit/test_context_gate_fallback.py`:

```python
"""Byte-proxy fallback escalation + compaction/retry tests."""
import os
import subprocess
from pathlib import Path

from sdd_test_helpers import make_hook_input, setup_full_sdd_workspace

ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = ROOT / "skills" / "subagent-driven-development" / "scripts" / "sdd-pre-dispatch-hook.sh"
FIX = Path(__file__).parent / "fixtures" / "context-probe"


def run_hook(payload, cwd, env_extra=None):
    env = dict(os.environ); env.setdefault("SUPERPOWERS_ROOT", str(ROOT))
    if env_extra: env.update(env_extra)
    return subprocess.run(["bash", str(HOOK)], input=payload, capture_output=True,
                          text=True, cwd=cwd, env=env)


def _bad_probe(tmp_path):
    # missing transcript file AND no session_id -> probe fails -> byte-proxy.
    return make_hook_input("Implement task 1", prompt="You are implementing task 1",
                           transcript_path=str(FIX / "does-not-exist.jsonl"), cwd=str(tmp_path))


def _seed(tmp_path, n):
    log = Path(tmp_path) / "reports" / "context-observations.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as f:
        for _ in range(n):
            f.write("2026-01-01T00:00:00Z task=1 type=implementer tokens=1 source=byte-proxy tier=below action=fallback\n")


def test_single_fallback_allows(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(_bad_probe(tmp_path), str(tmp_path), env_extra={"SUPERPOWERS_CTX_FALLBACK_STREAK": "3"})
    assert r.returncode == 0
    assert "source=byte-proxy" in (Path(tmp_path) / "reports" / "context-observations.log").read_text()


def test_k_consecutive_fallbacks_block(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    _seed(tmp_path, 2)  # 2 prior + this = 3 = streak
    r = run_hook(_bad_probe(tmp_path), str(tmp_path), env_extra={"SUPERPOWERS_CTX_FALLBACK_STREAK": "3"})
    assert r.returncode == 2 and "blind" in r.stderr.lower()


def test_probe_success_resets_streak(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    _seed(tmp_path, 5)
    with (Path(tmp_path) / "reports" / "context-observations.log").open("a") as f:
        f.write("2026-01-01T00:01:00Z task=1 type=implementer tokens=250000 source=probe tier=below action=allow\n")
    r = run_hook(_bad_probe(tmp_path), str(tmp_path), env_extra={"SUPERPOWERS_CTX_FALLBACK_STREAK": "3"})
    assert r.returncode == 0  # this dispatch is only the 1st trailing fallback


def test_reading_across_compaction_resets_tier(tmp_path):
    """Post-compaction the reading DROPS (below fixture) -> tier=below -> allow."""
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    r = run_hook(make_hook_input("Implement task 1", prompt="You are implementing task 1",
                                 transcript_path=str(FIX / "below.jsonl"), cwd=str(tmp_path)), str(tmp_path))
    assert r.returncode == 0


def test_retry_after_block_still_blocks(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    p = make_hook_input("Implement task 1", prompt="You are implementing task 1",
                        transcript_path=str(FIX / "hard.jsonl"), cwd=str(tmp_path))
    assert run_hook(p, str(tmp_path)).returncode == 2
    assert run_hook(p, str(tmp_path)).returncode == 2


def test_bypass_after_block_allows(tmp_path):
    setup_full_sdd_workspace(str(tmp_path), 4, 1)
    p = make_hook_input("Implement task 1", prompt="You are implementing task 1",
                        transcript_path=str(FIX / "hard.jsonl"), cwd=str(tmp_path))
    assert run_hook(p, str(tmp_path)).returncode == 2
    assert run_hook(p, str(tmp_path), env_extra={"SUPERPOWERS_CTX_HANDOFF_BYPASS": "1"}).returncode == 0
```

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_gate_fallback.py -v`
Expected: `test_k_consecutive_fallbacks_block` FAILs (returns 0) — no escalation yet. The compaction/retry/reset tests pass from Task 5 (assert existing behavior).

- [x] **Step 3: Add the streak counter helper**

After `ctx_log` in the helpers block (Task 3 Step 6), add:

```bash
ctx_fallback_streak() {
  # Trailing consecutive action=fallback rows (a non-fallback row breaks the
  # streak). Includes the row just written. tac is absent on macOS -> awk.
  awk '{a[NR]=$0} END{c=0; for(i=NR;i>=1;i--){ if(a[i] ~ /action=fallback/) c++; else break } print c}' "$OBS_LOG" 2>/dev/null || echo 0
}
```

- [x] **Step 4: Escalate in the implementer fallback branch**

In the implementer-tail fallback branch (Task 5 Step 3, the `else` arm), after `ctx_log implementer byte-proxy ... fallback`, add:

```bash
      STREAK_N=$(ctx_fallback_streak)
      if [ "${STREAK_N:-0}" -ge "$CTX_STREAK" ] 2>/dev/null; then
        echo "BLOCKED (context): the context gate has run blind for $STREAK_N consecutive dispatches — context-probe.py is failing (check .transcript_path resolution and that the probe is stdlib-only). A silently-inert gate is not allowed. Fix the probe, or set SUPERPOWERS_CTX_HANDOFF_BYPASS=1 to proceed without the gate. See references/context-handoff-protocol.md." >&2
        exit 2
      fi
```

- [x] **Step 5: Run the fallback tests + full context suite — expect PASS**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_gate_fallback.py tests/unit/test_context_gate_tier.py tests/unit/test_context_gate_impl_log.py tests/unit/test_context_gate_log.py -q`
Expected: PASS. Re-run the existing hook suites — still green.

- [x] **Step 6: Re-capture baseline and commit**

```bash
bash tests/ARaymond-hook-baseline/check-hooks.sh --capture
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh \
  tests/unit/test_context_gate_fallback.py tests/ARaymond-hook-baseline/baseline.txt
git commit -m "feat(sdd-ctx): K-consecutive-fallback escalation for a blind context gate"
```

- [x] Every dispatch that reaches the gate appends exactly one observation line (reviewer/re-review/passthrough/fix + non-blocked implementer); blocked-by-prior-check implementer dispatches are excepted per the carve-out; append failure never breaks a dispatch.
- [x] `--session-id` fallback resolves the transcript for an implementer dispatch (hoist proven).
- [x] below→allow, soft→nudge (in `additionalContext`), hard→`exit 2` non-retryable.
- [x] Reviewer / partner / fix / re-review never blocked; verification task IS eligible.
- [x] Env overrides apply; invalid (`HARD ≤ SOFT` / non-numeric) reverts to defaults with a warning; bypass logs `source=bypass`.
- [x] K consecutive fallbacks escalate to a block; a probe success resets the streak.
- [x] Reading-across-compaction resets the tier (no fire); retry blocks again; bypass-after-block allows.
- [x] Check 7's standalone warning removed (no `CONTEXT_LOAD_WARNING` references); byte-sum lives only in `ctx_byte_estimate`.
- [x] `check-hooks.sh` green at each commit boundary (baseline re-captured per task).
