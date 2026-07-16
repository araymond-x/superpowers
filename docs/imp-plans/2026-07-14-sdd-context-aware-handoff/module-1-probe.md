# Module 1 — Context Probe + Fixtures

**Goal:** Vendor a stdlib-only `context-probe.py` that mirrors `claude-ctx-check`'s transcript scan and 4-field token sum, plus fixture transcripts at known token totals that serve as the shared test seam for the whole feature. Freeze the external contract into fixtures first (Task 0), build the probe core against them (Task 1), then add session-id resolution + parity (Task 2).

**Source Contracts:**
- The Claude Code transcript JSONL `usage` block: an assistant `message` object carrying `usage.{input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens}`. Verified live: the real transcript also carries top-level `session_id`/`sessionId` and `type: "assistant"`; extra `usage` keys (`cache_creation`, `service_tier`, …) exist and are ignored.
- `~/.claude/bin/claude-ctx-check` — the parity source (external tool). Its `find_transcript` (glob `~/.claude/projects/*/<id>.jsonl`), `find_latest_usage` (scan lines in reverse for the first assistant `message.usage`), and the 4-field sum are the algorithm to mirror.

**Contract Constraints:**
- `T = input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens` from the **most recent** assistant `usage` block (scan from the end).
- Missing field → 0. Non-numeric field → 0 (probe hardening beyond `claude-ctx-check`, which would raise; documented divergence — the differential test compares only on well-formed fixtures where both agree).
- A malformed (non-JSON) trailing line is skipped, not fatal.
- Stdlib-only: no pydantic, no PyYAML, no third-party imports. Runs under bare `python3`.

## File Map
- Create: `tests/unit/fixtures/context-probe/{below,soft,hard,missing-fields,non-numeric,malformed-trailing,no-usage,empty}.jsonl`
- Create: `tests/unit/test_context_probe_fixtures.py` (Task 0)
- Create: `skills/subagent-driven-development/scripts/context-probe.py` (Task 1, extended in Task 2)
- Create: `tests/unit/test_context_probe.py` (Task 1)
- Create: `tests/unit/test_context_probe_sessionid.py` (Task 2)

**Write-Scope Partitioning:**

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| 0 | `tests/unit/fixtures/context-probe/*.jsonl`, `tests/unit/test_context_probe_fixtures.py` | `~/.claude/bin/claude-ctx-check`, a real transcript | — |
| 1 | `skills/subagent-driven-development/scripts/context-probe.py`, `tests/unit/test_context_probe.py` | the fixtures, `claude-ctx-check` | 0 |
| 2 | `skills/subagent-driven-development/scripts/context-probe.py`, `tests/unit/test_context_probe_sessionid.py` | the fixtures, `claude-ctx-check` | 1 |

**Note on the shared file:** Tasks 1 and 2 both write `context-probe.py` — they are serialized (Task 2 `depends_on` Task 1), never parallel. Task 1 builds the `--transcript` core; Task 2 adds the `--session-id` / env-var resolver.

---

### Task 0: Contract verification + fixture transcripts

**Files:**
- Read (contract source): `/Users/araymond/.claude/bin/claude-ctx-check`
- Create: the eight fixtures under `tests/unit/fixtures/context-probe/`
- Create: `tests/unit/test_context_probe_fixtures.py`
- Report: `docs/imp-plans/2026-07-14-sdd-context-aware-handoff/reports/task-000-implementer-report.md`

Blocking contract-verification task. No probe code yet — extract the ground truth from `claude-ctx-check`, freeze it into fixtures, pin them with a test that reproduces the documented 4-field sum by hand.

- [x] **Step 1: Read the parity source and record the vendored version**

Run: `cat ~/.claude/bin/claude-ctx-check` and note the algorithm (`find_transcript`, `find_latest_usage`, the 4-field sum). Compute a fingerprint for the probe to record:

```bash
shasum -a 256 ~/.claude/bin/claude-ctx-check | cut -c1-12
```
Record this 12-char fingerprint in the task report — Task 1 embeds it as `SOURCE_VERSION`.

- [x] **Step 2: Create the known-total fixtures**

Each fixture is JSONL: one assistant message per meaningful line; the four usage fields sum to the intended `T`.

`tests/unit/fixtures/context-probe/below.jsonl` (T = 250000):

```json
{"type":"user","message":{"role":"user","content":"hi"}}
{"type":"assistant","session_id":"fixture-below","message":{"role":"assistant","model":"claude-opus-4-8","usage":{"input_tokens":100000,"cache_creation_input_tokens":50000,"cache_read_input_tokens":90000,"output_tokens":10000}}}
```

`soft.jsonl` (T = 350000) — usage `{"input_tokens":150000,"cache_creation_input_tokens":50000,"cache_read_input_tokens":140000,"output_tokens":10000}`.
`hard.jsonl` (T = 450000) — usage `{"input_tokens":200000,"cache_creation_input_tokens":50000,"cache_read_input_tokens":190000,"output_tokens":10000}`.

- [x] **Step 3: Create the edge-case fixtures**

`malformed-trailing.jsonl` (valid T=250000 line, then a non-JSON trailing line — must be skipped):

```json
{"type":"assistant","message":{"role":"assistant","usage":{"input_tokens":100000,"cache_creation_input_tokens":50000,"cache_read_input_tokens":90000,"output_tokens":10000}}}
{ this is not valid json at all
```

`missing-fields.jsonl` (two fields absent → 0, T = 110000):

```json
{"type":"assistant","message":{"role":"assistant","usage":{"input_tokens":100000,"output_tokens":10000}}}
```

`non-numeric.jsonl` (a field is a string → 0, T = 100000):

```json
{"type":"assistant","message":{"role":"assistant","usage":{"input_tokens":100000,"cache_creation_input_tokens":"n/a","cache_read_input_tokens":0,"output_tokens":0}}}
```

`no-usage.jsonl` (assistant message, no usage block — probe must exit non-zero):

```json
{"type":"user","message":{"role":"user","content":"hi"}}
{"type":"assistant","message":{"role":"assistant","content":"reply, no usage yet"}}
```

`empty.jsonl` — empty file: `: > tests/unit/fixtures/context-probe/empty.jsonl`.

- [x] **Step 4: Write the fixture contract test**

`tests/unit/test_context_probe_fixtures.py` — reproduces the documented 4-field sum directly, freezing the fixtures independent of any probe code:

```python
"""Contract test: fixture transcripts encode their documented token totals.

Reproduces the claude-ctx-check 4-field sum by hand (missing/non-numeric -> 0,
malformed trailing line skipped) so the fixtures are pinned independently of
context-probe.py. Task 1's probe is then validated against these same fixtures.
"""
import json
from pathlib import Path

FIX = Path(__file__).parent / "fixtures" / "context-probe"
FIELDS = ("input_tokens", "cache_creation_input_tokens",
          "cache_read_input_tokens", "output_tokens")


def _coerce_int(value) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _sum_latest(path: Path):
    for line in reversed(path.read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if isinstance(usage, dict):
            return sum(_coerce_int(usage.get(f)) for f in FIELDS)
    return None


def test_below_total():
    assert _sum_latest(FIX / "below.jsonl") == 250000

def test_soft_total():
    assert _sum_latest(FIX / "soft.jsonl") == 350000

def test_hard_total():
    assert _sum_latest(FIX / "hard.jsonl") == 450000

def test_malformed_trailing_skipped():
    assert _sum_latest(FIX / "malformed-trailing.jsonl") == 250000

def test_missing_fields_count_zero():
    assert _sum_latest(FIX / "missing-fields.jsonl") == 110000

def test_non_numeric_counts_zero():
    assert _sum_latest(FIX / "non-numeric.jsonl") == 100000

def test_no_usage_returns_none():
    assert _sum_latest(FIX / "no-usage.jsonl") is None

def test_empty_returns_none():
    assert _sum_latest(FIX / "empty.jsonl") is None
```

- [x] **Step 5: Run — expect PASS**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_probe_fixtures.py -v`
Expected: all 8 PASS (validates the fixtures, not production code yet).

- [x] **Step 6: Commit**

```bash
git add tests/unit/fixtures/context-probe tests/unit/test_context_probe_fixtures.py
git commit -m "test(sdd-ctx): add fixture transcripts + contract test for context probe"
```

---

### Task 1: `context-probe.py` core (`--transcript` / `--json`)

**Files:**
- Create: `skills/subagent-driven-development/scripts/context-probe.py`
- Create: `tests/unit/test_context_probe.py`
- Report: `.../reports/task-001-implementer-report.md`

**Pattern References:** `~/.claude/bin/claude-ctx-check` — mirror `find_latest_usage` + the 4-field sum. This task builds ONLY the `--transcript`/`--json` path (session-id resolution is Task 2). Record the Task 0 fingerprint as `SOURCE_VERSION`.

- [x] **Step 1: Write the failing core tests**

`tests/unit/test_context_probe.py` — drive the probe as a subprocess under `sys.executable` (production runs it under bare `python3`):

```python
"""Core (--transcript / --json) tests for context-probe.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
PROBE = ROOT / "skills" / "subagent-driven-development" / "scripts" / "context-probe.py"
FIX = Path(__file__).parent / "fixtures" / "context-probe"


def run_probe(*args):
    return subprocess.run([sys.executable, str(PROBE), *args],
                          capture_output=True, text=True)


@pytest.mark.parametrize("fixture,expected", [
    ("below.jsonl", "250000"),
    ("soft.jsonl", "350000"),
    ("hard.jsonl", "450000"),
    ("malformed-trailing.jsonl", "250000"),
    ("missing-fields.jsonl", "110000"),
    ("non-numeric.jsonl", "100000"),
])
def test_transcript_totals(fixture, expected):
    r = run_probe("--transcript", str(FIX / fixture))
    assert r.returncode == 0
    assert r.stdout.strip() == expected


def test_json_output_shape():
    r = run_probe("--transcript", str(FIX / "below.jsonl"), "--json")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["total_tokens"] == 250000
    assert payload["transcript"].endswith("below.jsonl")
    assert payload["source_version"]  # non-empty fingerprint recorded


def test_no_usage_nonzero_exit():
    r = run_probe("--transcript", str(FIX / "no-usage.jsonl"))
    assert r.returncode != 0
    assert "usage" in r.stderr.lower()


def test_empty_nonzero_exit():
    r = run_probe("--transcript", str(FIX / "empty.jsonl"))
    assert r.returncode != 0


def test_missing_transcript_nonzero_exit():
    r = run_probe("--transcript", str(FIX / "does-not-exist.jsonl"))
    assert r.returncode != 0
```

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_probe.py -v`
Expected: FAIL/errors — the probe does not exist yet.

- [x] **Step 3: Implement `context-probe.py` (core)**

```python
#!/usr/bin/env python3
"""context-probe.py — vendored, stdlib-only controller context-token sensor.

Mirrors ~/.claude/bin/claude-ctx-check: scan a Claude Code transcript JSONL from
the end for the most recent assistant `usage` block and sum the four token
fields. Window-less and percentage-less — the SDD pre-dispatch hook owns the
thresholds. Stdlib-only so it runs under bare `python3` (no pydantic / PyYAML).

Parity note: this copy coerces missing OR non-numeric usage fields to 0 (the
source would raise on non-numeric). The differential test compares only on
well-formed fixtures, where both agree.

Resolution priority: --transcript -> --session-id -> $CLAUDE_CODE_SESSION_ID.
The hook only ever uses the first two; the env var path is for standalone use.

Vendored from claude-ctx-check source version: <SOURCE_VERSION from Task 0>.

Exit codes: 0 = printed total; 1 = unavailable (no id / no transcript / no usage).
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Recorded from Task 0: shasum -a 256 ~/.claude/bin/claude-ctx-check | cut -c1-12
SOURCE_VERSION = "REPLACE_WITH_TASK0_FINGERPRINT"

PROJECTS_DIR = Path.home() / ".claude" / "projects"
FIELDS = ("input_tokens", "cache_creation_input_tokens",
          "cache_read_input_tokens", "output_tokens")


def _coerce_int(value) -> int:
    """Non-numeric or missing -> 0 (bool is not counted as an int here)."""
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def find_latest_total(transcript_path: Path):
    """Most recent assistant usage block, 4-field sum. None if none found."""
    for line in reversed(transcript_path.read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if isinstance(usage, dict):
            return sum(_coerce_int(usage.get(f)) for f in FIELDS)
    return None


def resolve_transcript(args):
    # Task 2 extends this with --session-id / env-var resolution.
    if args.transcript:
        p = Path(args.transcript)
        return p if p.is_file() else None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Controller context-token sensor")
    parser.add_argument("--transcript", help="explicit transcript JSONL path")
    parser.add_argument("--session-id", help="resolve ~/.claude/projects/*/<id>.jsonl")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    transcript = resolve_transcript(args)
    if transcript is None:
        print("context-probe: no transcript resolvable (missing id or file)", file=sys.stderr)
        return 1

    total = find_latest_total(transcript)
    if total is None:
        print("context-probe: no usage block found in transcript (no completed turn)", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"total_tokens": total, "transcript": str(transcript),
                          "source_version": SOURCE_VERSION}))
    else:
        print(total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Replace `SOURCE_VERSION`'s placeholder with the Task 0 fingerprint.

- [x] **Step 4: Run the core tests — expect PASS**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_probe.py -v`
Expected: PASS.

- [x] **Step 5: Confirm stdlib-only under bare python3**

Run: `python3 skills/subagent-driven-development/scripts/context-probe.py --transcript tests/unit/fixtures/context-probe/hard.jsonl`
Expected: prints `450000` under the SYSTEM `python3`.

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/context-probe.py tests/unit/test_context_probe.py
git commit -m "feat(sdd-ctx): context-probe.py core (--transcript token sensor)"
```

---

### Task 2: `context-probe.py` `--session-id` resolution + parity

**Files:**
- Modify: `skills/subagent-driven-development/scripts/context-probe.py`
- Create: `tests/unit/test_context_probe_sessionid.py`
- Report: `.../reports/task-002-implementer-report.md`

**Pattern References:** `~/.claude/bin/claude-ctx-check` — mirror `find_transcript` (glob `~/.claude/projects/*/<id>.jsonl`). The differential test pins parity.

- [x] **Step 1: Write the failing session-id + parity tests**

`tests/unit/test_context_probe_sessionid.py`:

```python
"""--session-id resolution + claude-ctx-check parity tests for context-probe.py."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
PROBE = ROOT / "skills" / "subagent-driven-development" / "scripts" / "context-probe.py"
FIX = Path(__file__).parent / "fixtures" / "context-probe"


def test_session_id_resolution(tmp_path):
    """--session-id resolves ~/.claude/projects/*/<id>.jsonl via a temp HOME."""
    projects = tmp_path / ".claude" / "projects" / "proj"
    projects.mkdir(parents=True)
    sid = "test-session-xyz"
    shutil.copy(FIX / "below.jsonl", projects / f"{sid}.jsonl")
    env = dict(os.environ); env["HOME"] = str(tmp_path)
    r = subprocess.run([sys.executable, str(PROBE), "--session-id", sid],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0
    assert r.stdout.strip() == "250000"


def test_no_session_id_nonzero_exit():
    env = dict(os.environ); env.pop("CLAUDE_CODE_SESSION_ID", None)
    r = subprocess.run([sys.executable, str(PROBE)], capture_output=True, text=True, env=env)
    assert r.returncode != 0


def test_env_var_resolution(tmp_path):
    """$CLAUDE_CODE_SESSION_ID drives resolution when no args are given."""
    projects = tmp_path / ".claude" / "projects" / "p"
    projects.mkdir(parents=True)
    shutil.copy(FIX / "soft.jsonl", projects / "env-sess.jsonl")
    env = dict(os.environ); env["HOME"] = str(tmp_path)
    env["CLAUDE_CODE_SESSION_ID"] = "env-sess"
    r = subprocess.run([sys.executable, str(PROBE)], capture_output=True, text=True, env=env)
    assert r.returncode == 0 and r.stdout.strip() == "350000"


@pytest.mark.skipif(
    not (Path.home() / ".claude" / "bin" / "claude-ctx-check").is_file(),
    reason="claude-ctx-check not installed on this machine",
)
def test_differential_parity_with_ctx_check(tmp_path):
    """On a well-formed fixture, probe total == claude-ctx-check total."""
    ctx_check = Path.home() / ".claude" / "bin" / "claude-ctx-check"
    projects = tmp_path / ".claude" / "projects" / "proj"
    projects.mkdir(parents=True)
    shutil.copy(FIX / "hard.jsonl", projects / "diff-sess.jsonl")
    env = dict(os.environ); env["HOME"] = str(tmp_path)
    env["CLAUDE_CODE_SESSION_ID"] = "diff-sess"
    probe = subprocess.run([sys.executable, str(PROBE)], capture_output=True, text=True, env=env)
    ctx = subprocess.run([sys.executable, str(ctx_check), "--json"],
                         capture_output=True, text=True, env=env)
    assert probe.returncode == 0 and ctx.returncode == 0
    assert int(probe.stdout.strip()) == json.loads(ctx.stdout)["total_tokens"]
```

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_probe_sessionid.py -v`
Expected: FAIL — `resolve_transcript` returns None for `--session-id` (Task 1 stub).

- [x] **Step 3: Extend the probe's resolver**

Add `find_transcript` and extend `resolve_transcript` in `context-probe.py`:

```python
def find_transcript(session_id: str):
    """Search ~/.claude/projects/*/<session_id>.jsonl by filename (UUID is unique)."""
    if not PROJECTS_DIR.is_dir():
        return None
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        candidate = project_dir / f"{session_id}.jsonl"
        if candidate.is_file():
            return candidate
    return None


def resolve_transcript(args):
    if args.transcript:
        p = Path(args.transcript)
        return p if p.is_file() else None
    session_id = args.session_id or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        return None
    return find_transcript(session_id)
```

Note: `PROJECTS_DIR = Path.home() / ".claude" / "projects"` is a module constant evaluated at import — the tests set `HOME` in the subprocess env, so it resolves under the temp HOME. Keep it computed inside `find_transcript` ONLY if a test needs to override it after import; the subprocess-env approach makes the module-level constant correct.

- [x] **Step 4: Run the session-id tests — expect PASS**

Run: `.venv/bin/python3 -m pytest tests/unit/test_context_probe_sessionid.py tests/unit/test_context_probe.py -v`
Expected: PASS (the differential test PASSes where `claude-ctx-check` is installed, else SKIPS).

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/context-probe.py tests/unit/test_context_probe_sessionid.py
git commit -m "feat(sdd-ctx): context-probe.py --session-id resolution + ctx-check parity"
```

**Module 1 Acceptance Criteria:**
- [x] Fixtures encode their documented totals; the fixture contract test passes.
- [x] Probe returns correct `T` via `--transcript` and `--session-id` (and `$CLAUDE_CODE_SESSION_ID`); non-zero exit on the three unavailable cases.
- [x] Missing/non-numeric → 0; malformed trailing line skipped.
- [x] `--json` emits `total_tokens` + `transcript` + `source_version`.
- [x] Differential parity with `claude-ctx-check` passes (or skips when absent).
- [x] Probe runs under bare `python3` (stdlib-only).
