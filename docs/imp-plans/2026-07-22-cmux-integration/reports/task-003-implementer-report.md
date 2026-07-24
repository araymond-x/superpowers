---
schema_version: 1
task_id: 3
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Replaced the Task-3 marker (line 130) with Precondition 5: quota tool resolution, a timeout-bounded `check_quota()` emitting ok/low/unchecked, and the case dispatch (low → cmux notify + manual instructions + exit 3)."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "Appended the 5 quota test functions (7 collected cases) covering low, the four fail-open classes, tool-absent, and ok."
tests:
  written: 7
  passing: 7
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -k quota -v"
  result: PASS
contract_compliance:
  - constraint: "Quota is fail-open: tool absent / non-zero / 60s timeout / unparseable / window-or-field missing / non-numeric ⇒ proceed with quota=unchecked. Only a parsed numeric < SUPERPOWERS_CMUX_QUOTA_MIN_PCT refuses (exit 3)."
    status: compliant
    detail: "All seven classes verified. Six by the unit tests; the timeout class by an out-of-band smoke run (hanging stub + SUPERPOWERS_CMUX_QUOTA_TIMEOUT=3 → rc 0, quota=unchecked, 3.6s wall clock). Non-numeric `remaining_pct` also verified → unchecked. Boundary confirmed strict: pct == MIN classifies ok, not low."
  - constraint: "Shared constant: use $QUOTA_MIN_PCT, do not hardcode 15 anywhere."
    status: compliant
    detail: "Both the awk comparison and the notify body interpolate $QUOTA_MIN_PCT. No literal 15 in script or tests. Verified live: overriding SUPERPOWERS_CMUX_QUOTA_MIN_PCT=70 flips a 63.0% reading to low/exit 3; =20 keeps 20.0% at ok."
  - constraint: "House bash style: no `set -u`, never pipe a producer into `grep -q` under pipefail, use $PYTHON."
    status: compliant
    detail: "No set -u, no grep pipelines added. Tool output is parsed by `$PYTHON` (line 17) with the JSON passed as sys.argv[1], never interpolated into program text. `bash -n` clean; shellcheck --severity=warning reports only pre-existing-pattern SC2034s."
---

**Commit:** `7131698`

**Implementation Summary:**
Added Precondition 5 (quota) to `spawn-handoff-session.sh`. `check_quota()` runs `claude-usage-pace --json --no-log` under a background-watcher timeout (macOS has no `timeout`), extracts `windows[key=="session"].remaining_pct` via `$PYTHON`, and classifies `ok:<pct>` / `low:<pct>` / `unchecked`. Every failure mode collapses to `unchecked` and proceeds; only a parsed numeric below `$QUOTA_MIN_PCT` notifies, prints manual instructions, and exits 3.

**Source Files Read:**
- `spawn-handoff-session.sh` — confirmed `PYTHON`, `QUOTA_MIN_PCT` (L21), `QUOTA_TOOL_DEFAULT` (L23), `print_manual_instructions()` (L57); marker at L130. Left the Tasks 4-5 / Task 6 markers untouched (now L181-182).
- `spawn_handoff_helpers.py` — the six `PACE_*` literals and `run_spawn(pace_body=, env_extra=)`. Critically: it remaps `HOME` to `tmp_path/home` and installs the `claude-usage-pace` stub on `PATH`.
- `test_spawn_handoff.py` — 14 existing tests; matched their mid-file-import, append-only style.
- `spec.md` §5.2/§5.3 — pinned invocation, field, threshold, and the exact fail-open class list.
- `test_context_gate_tier.py` — subprocess-with-env-stub harness pattern.

**CLAUDE.md Files Read:**
- `CLAUDE.md` (repo root; the only CLAUDE.md in the tree — no subdirectory ones exist) — Hook Development Gotchas (`$PYTHON` for PyYAML/Pydantic, no `set -u`, the `grep -q`/SIGPIPE fail-open trap), Testing (pytest via `.venv/bin/python3`), and the macOS "no `timeout`, use background-process-kill" note.

**Deviations from Plan:**

Two, both because the plan's verbatim Step 2 snippet is broken as written. **The plan doc still contains the broken original — please propagate these into `plan.md` before any re-run.**

1. **Timeout capture rewritten (temp file, not a pipe).** The plan's snippet hangs for the *entire* timeout on the **success** path, not just on timeout. The watcher's `sleep` grandchild inherits the command-substitution pipe's write end; `kill $watcher` reaps the subshell but orphans `sleep`, which holds the pipe open. Measured: a tool returning instantly took **30.0s** with `QUOTA_TIMEOUT=30` — so in production every spawn would stall 60s, and the 7 quota tests would take ~7 minutes. I capture into a `mktemp` file instead and `wait` on the tool PID, which is immune to fd inheritance. Verified: fast path 0-1s; both hang shapes (single-process `exec sleep` **and** a tool that forks a child) time out exactly at the limit and fail open. The minimal alternative (just `>/dev/null` on the watcher) fixes the success path but still hangs for any tool that forks — the temp file is what actually delivers the spec's 60s guarantee.
2. **Default-only PATH fallback for tool resolution.** The plan's snippet and its tests are mutually inconsistent: `run_spawn` sets `HOME=tmp_path/home`, so `QUOTA_TOOL_DEFAULT` (`$HOME/.claude/bin/claude-usage-pace`) never exists under test, and the harness's `PATH` stub is unreachable — `test_quota_ok_proceeds` and `test_quota_low_exits_3` could never pass, and `test_quota_tool_absent_proceeds` would be vacuous. I kept the plan's tests verbatim (ground truth) and fixed the script: when **no** `SUPERPOWERS_CMUX_QUOTA_TOOL` override is given and the pinned default is absent, fall back to `command -v claude-usage-pace`. An explicit override stays authoritative (a bad override ⇒ `unchecked`, never a silent fallback), which is what keeps the absent-test meaningful. Production is spec-exact: `~/.claude/bin/claude-usage-pace` exists there (verified), so the fallback never fires. Note `~/.claude/bin` is **not** on `PATH` — the absolute default remains the real resolution path.

Also: `SUPERPOWERS_CMUX_QUOTA_TIMEOUT` (default 60) is live and needs adding to the Task 9 docs list, as the plan's timeout note anticipated.

**Self-Review Findings:**
- Ran the 14 pre-existing tests before and after; all still pass — none reach the quota block (they exit at preconditions 1-4). Full file **21/21**; full unit suite **574 passed**, no regressions.
- Confirmed the `QCLASS="$(check_quota)"` call site did not reintroduce the pipe stall — 7 quota tests in **5.3s** wall clock.
- Verified the low path end-to-end: `cmux notify --title "SDD handoff" --body "Session quota 8.0% < 15% — manual resume"` reaches the stub, `/pickup b1` instructions print, exit 3.
- shellcheck flags `QUOTA_STATUS` as SC2034 (unused). Left as-is deliberately: it is forward-scaffolding for the Task-6 spawn log, exactly mirroring `SP_HOP` (set by Task 2 for Task 5). No severe (fail-open) classes.
- Cleaned all scratch files and stray experiment processes. Committed exactly the two in-scope files; controller artifacts (`deviations.md`, `.dispatch-log`, `context-observations.log`, checkpoints) were left unstaged and untouched.

**Concerns:**
- **The plan doc needs both corrections above.** My code is right, but a future reader copying the Step 2 snippet verbatim gets a 60s stall on every spawn plus tests that cannot pass.
- A timeout leaves one orphaned `sleep` (reparented to init, stdout/stderr `/dev/null`) and prints a `Killed: 9` job notice to stderr. Both are cosmetic and unreached by any test; suppressing them needs process-group handling, which I judged overbuild.
- A non-numeric `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` makes the `awk` program error out, classifying `ok` (proceed). Outside the spec's fail-open matrix, which only covers tool-side faults; flagging rather than adding unrequested validation.
- Scoped verification to the unit file per the task. The e2e, regression, and install suites were not run — those are the controller's pre-completion gates.
