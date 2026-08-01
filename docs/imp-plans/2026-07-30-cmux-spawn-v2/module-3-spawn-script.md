---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: "docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md"
integration_test:
  path: tests/integration/sdd-e2e-test.sh
tasks:
  - id: 8
    title: "Spawn script: policy gate, stall/ceiling rework, intent tasks_done"
  - id: 9
    title: "Spawn script: surface topology + shared launch wrapper + workspace fallback"
    depends_on: [8]
  - id: 10
    title: "Spawn script: wait-for handshake, re-wait, read-screen diagnosis"
    depends_on: [9]
  - id: 11
    title: "Spawn script: post-spawn setup (/rename, /rc) + knobs"
    depends_on: [10]
---

# cmux-spawn-v2 — Module 3: Spawn script core rework

> **Parent plan:** `docs/imp-plans/2026-07-30-cmux-spawn-v2/plan.md`
> **Module:** 3 of 4
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Rework `spawn-handoff-session.sh` in place: consent policy gate, progress-aware stall/ceiling, surface-topology spawn through ONE shared launch-and-handshake wrapper (workspace path demoted to a one-shot fallback on the canonical `workspace create` verb), `wait-for` token handshake as the only success signal, read-screen diagnosis enrichment, and script-driven post-spawn setup. Every task keeps the script and BOTH unit files green.

**Source Contracts:** None

_External contracts were frozen into fixtures by Module 1's Task 0 (repo convention: the mechanical Task-0 gate resolves against the module that owns Task 0). The binding facts this module consumes — spec-distilled Decisions 2-8, 14, 19-20 + §5.1/§5.3, the Task 0 fixtures (`cmux-verb-shapes.json`, `cold-start-timing.json`), the `_handoff_support.py` CLI, and the parent plan's Shared Contract Section — are restated under Contract Constraints below._

**Contract Constraints:** Bash ≥ 3.2; NO `set -u`/`set -e`/pipefail; `printf` not `echo` for composed strings; never pipe a producer into `grep -q` (use here-strings); all env knobs validate-warn-revert (`.handoff-hops`'s fail-closed numeric guard is the ONE fail-closed guard and stays untouched; `SUPERPOWERS_CMUX_MAX_HOPS` keeps its validate-warn-revert contract but its validation MOVES into the ceiling derivation — Task 8(b)/(e)); reservation BEFORE spawn; a received token is the ONLY exit-0 path; fallback fires ONLY before the launch command is accepted (`cmux send` rc 0 = accepted — after that, NEVER spawn again); `policy-off`/`policy-ask` are pre-reservation (no hop consumed); exit codes stay 0/3/1.

## File Map

| File | Responsibility |
|------|----------------|
| `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` | The rework target — one function group per task |
| `tests/unit/spawn_handoff_helpers.py` | + `cmux_v2_stub()` builder (behavior via env: `CMUX_WAITFOR_RC`, `CMUX_SCREEN_FILE`, `CMUX_NEW_SURFACE_RC`, `CMUX_SEND_RC`, `CMUX_WS_CREATE_RC`) |
| `tests/unit/test_spawn_handoff_v2.py` | New behavior matrix (policy, stall, surface, handshake, post-spawn) |
| `tests/unit/test_spawn_handoff.py` | Existing matrix — topology-dependent tests MIGRATED in the task that changes the behavior, never later |
| `tests/unit/fixtures/spawn-handoff/*.json` | + manifests with `handoff` blocks; screen-text fixtures for diagnosis |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 8 | `spawn-handoff-session.sh`, `test_spawn_handoff_v2.py`, `test_spawn_handoff.py`, `spawn_handoff_helpers.py`, `tests/unit/fixtures/spawn-handoff/*`, **`_handoff_support.py`**, **`tests/unit/test_handoff_support.py`**, **`tests/unit/test_spawn_handoff_hardening.py`** (B1) | — | Task 7 |
| Task 9 | first five above + **`test_spawn_handoff_hardening.py`** (B1); `_handoff_support.py` returns to read-only after Task 8 | `_handoff_support.py`, Task 0 fixtures | Task 8 |
| Task 10 | same set | Task 0 fixtures | Task 9 |
| Task 11 | same set | — | Task 10 |

All four tasks write the same files — strictly serialized, never parallel.

### Task 8: Policy gate, stall/ceiling rework, intent tasks_done

**Files:**
- Modify: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`, and — **for the scheduled deferred rows only** — `skills/subagent-driven-development/scripts/_handoff_support.py`
- Test: `tests/unit/test_spawn_handoff_v2.py`, `tests/unit/test_spawn_handoff.py`, `tests/unit/spawn_handoff_helpers.py`, `tests/unit/fixtures/spawn-handoff/`, `tests/unit/test_handoff_support.py`, `tests/unit/test_spawn_handoff_hardening.py` (B1)

**B1 — `test_spawn_handoff_hardening.py` is a THIRD consumer of the moving default, and it is currently 10/10 green.** `test_nonnumeric_max_hops_reverts_to_default_and_still_refuses` seeds `.handoff-hops="3"` against today's `MAX_HOPS_DEFAULT=3` and asserts refusal; step (e) reverts an invalid knob to the DERIVED ceiling, which is `6` for that fixture (no `.sdd-session.json`, so `EXPECTED_HOPS="unknown"`), and 3 < 6 means **the gate stops refusing and the script spawns** — a fail-open regression. It fails only HALF-loudly (its `WARNING:` assertion still passes), so pin it deliberately: seed above the new derived ceiling or set `SUPERPOWERS_CMUX_MAX_HOPS` explicitly, whichever preserves each test's stated intent. **Because Task 8 moves a global default, the acceptance run for this task is the FULL suite, not a file list.** **The consumer sweep is FOUR unit tests, not two — and an identifier grep returns a clean FALSE closure.** `/usr/bin/grep -rlc 'MAX_HOPS' tests/unit/*.py` matches ONLY `test_spawn_handoff_hardening.py`; `test_spawn_handoff.py` scores **0** while containing two breaking consumers, because a dependency on a value is not a textual reference to its name. **Sweep the RENDERED form too.** All four breaking consumers are enumerated with their fixes in **Step 2's migration block** — work from that list, not from this paragraph. Also `tests/integration/sdd-e2e-test.sh:722` reads `.handoff-hops`, benign here (its fixture ships no manifest, so ceiling 6 vs hops 0) and owned by Module 4.

`_handoff_support.py` was read-only for Module 3 as first written, but seven scheduled rows are production/test edits to it and its test file (**executed by Step 2b — this paragraph only justifies the scope**), and the register routes them here — Task 8 consumes `spawn-policy`, `tasks-done` and `stall-streak`, so it owns their supply side. Scope widened for Task 8 ONLY; it reverts to read-only for Tasks 9–11. **B7 inverts by directory: `_handoff_support.py` is scanned by `check_python39_compat`, so use `Optional[X]`/`Dict[str,int]`, never `X | None`/`dict[str,int]`.**

- [ ] **Step 1: Helper + fixtures.** In `spawn_handoff_helpers.py` add a manifest writer; in `fixtures/spawn-handoff/` nothing new is needed yet (manifests are written per-test):

```python
def write_manifest(ctx, expected_hops=2, spawn_policy="auto", total_tasks=5,
                   tier="standard", task_range=(0, 4), omit_handoff=False):
    """Minimal .sdd-session.json in the feature dir. omit_handoff=True builds a
    pre-v2 manifest (no handoff block) for derivation-path tests. Defaults emit a
    COMPLETE block: deferred order B4 pins handoff as all-or-nothing, so a partial
    block is model-invalid — omit_handoff is the only sanctioned way to have none."""
    import json as _json
    m = {"tier": tier, "total_tasks": total_tasks, "task_range": list(task_range)}
    if not omit_handoff:
        m["handoff"] = {"expected_hops": expected_hops, "spawn_policy": spawn_policy}
    (ctx["wt"] / ctx["feat"] / ".sdd-session.json").write_text(_json.dumps(m))


def write_done_report(ctx, task_id, status="DONE"):
    body = (f"---\nschema_version: 1\ntask_id: {task_id}\nstatus: {status}\n"
            "files_changed: [{path: x, description: y}]\n"
            "tests: {written: 1, passing: 1, command: x, result: PASS}\n---\nbody\n")
    (ctx["reports"] / f"task-{task_id:03d}-implementer-report.md").write_text(body)


def append_outcome(ctx, hop, tasks_done, extra=""):
    line = (f"2026-07-30T00:00:0{hop}Z uuid-{hop} outcome hop={hop} workspace=w surface=s "
            f"launch=auto bundle=b quota=ok tasks_done={tasks_done} handshake=ok{extra}\n")
    with open(ctx["reports"] / "handoff-spawn.log", "a") as f:
        f.write(line)


def _commit(ctx, msg="fixture state"):
    subprocess.run(["git", "add", "-A"], cwd=ctx["wt"], check=True)   # fixture repo only
    subprocess.run(["git", "commit", "-qm", msg], cwd=ctx["wt"], check=True)


def _spawn_log_text_or_empty(ctx):
    p = ctx["reports"] / "handoff-spawn.log"
    return p.read_text() if p.exists() else ""
```

Ceiling/stall tests must pop ambient `SUPERPOWERS_CMUX_*` vars (run_spawn copies `os.environ`) — pass `env_extra` overrides explicitly and strip the rest in a small wrapper, or the developer's shell knobs skew derived-ceiling assertions.

Note: these reports/manifests must be **committed** inside the fixture worktree (the script's clean-tree precondition runs first) — add `git add -A && git commit` after writing, mirroring `setup_worktree`.

- [ ] **Step 2: Failing tests** (in `test_spawn_handoff_v2.py`; use `run_spawn` throughout):

```python
class TestPolicyDial:
    def test_off_refuses_pre_reservation(self, tmp_path):
        ctx = setup_worktree(tmp_path); install_bundle(...); write_manifest(ctx, expected_hops=3, spawn_policy="off"); _commit(ctx)
        r = run_spawn(ctx, tmp_path, "b1")
        assert r.returncode == 3 and "reason=policy-off" in r.stderr
        assert not (ctx["reports"] / ".handoff-hops").exists()      # no hop consumed
        assert "intent" not in _spawn_log_text_or_empty(ctx)

    def test_ask_without_flag_refuses_retryable(self, tmp_path):
        ... spawn_policy="ask" ...
        r = run_spawn(ctx, tmp_path, "b1")
        assert r.returncode == 3 and "reason=policy-ask" in r.stderr
        assert "--user-approved" in r.stderr                        # retry instruction printed

    def test_ask_with_flag_proceeds(self, tmp_path):
        r = run_spawn(ctx, tmp_path, "b1", "--user-approved", ...)
        assert "reason=policy-ask" not in r.stderr                  # gate passed (later gates may still act)

    # SPLIT deliberately: "absent file" and "present file, absent handoff block" are
    # two DIFFERENT code paths (shell `[ -f ]` short-circuit vs Python `auto` return).
    # One test named "or" pins only whichever the fixture happens to build.
    def test_absent_manifest_file_is_auto(self, tmp_path):
        # no .sdd-session.json at all -> shell never calls the CLI -> auto, proceeds
    def test_present_manifest_without_handoff_block_is_auto(self, tmp_path):
        # write_manifest(omit_handoff=True) -> CLI returns auto -> proceeds
    def test_cli_failure_is_non_consent(self, tmp_path):
        # THE ONLY test pinning the *) -> ask arm: both siblings above pass even if the
        # gate is deleted. Do not weaken or drop it. There is NO SUPPORT_CLI override —
        # it is derived from SCRIPT_DIR. Seam: set SUPERPOWERS_ROOT via env_extra so
        # $PYTHON falls back to bare `python3`, and put a python3 stub first on PATH that
        # DISPATCHES ON ARGV — fail only the `spawn-policy` call, `exec` the real
        # interpreter otherwise (validate_bundle makes four $PYTHON calls and runs BEFORE
        # this gate, so a blanket stub dies at bundle validation and never reaches it).
        # `exec` BY ABSOLUTE PATH (capture sys.executable when writing the stub): the stub
        # is first on PATH and is itself named python3, so bare `exec python3 "$@"` re-enters
        # it and, since exec does not fork, spins forever — a HANG inside the untimed
        # full-suite acceptance run, not a test failure. Measured: rc=137 under a watchdog.
        # Assert exit 3 + "reason=policy-ask".
```

```python
class TestStallAndCeiling:
    def test_progress_never_refused_below_ceiling(self, tmp_path):
        # 2 prior outcomes tasks_done=2,4; 5 DONE reports now; hops file "2" -> proceeds
    def test_one_stall_allowed(self, tmp_path):
        # prior outcome tasks_done=3; 3 DONE reports -> streak 1, proceeds
    def test_two_stalls_refused_with_progress_message(self, tmp_path):
        # two trailing outcomes tasks_done=3; 3 DONE reports -> exit 3, "reason=stall",
        # message contains "tasks 3/5" and "hops" and "SUPERPOWERS_CMUX_MAX_STALL_HOPS"
    def test_first_hop_baseline_not_stall(self, tmp_path):
        # empty log, 0 reports -> proceeds
    def test_malformed_prior_outcome_indeterminate_skips(self, tmp_path):
        # last outcome missing tasks_done= -> proceeds, stderr contains "stall=indeterminate"
    def test_ceiling_derived_from_expected_hops(self, tmp_path):
        # expected_hops=5 -> ceiling max(6, 2*5)=10; "9" proceeds, "10" -> exit 3 hop-limit.
        # MUST exceed the floor: at expected_hops=2 the max() picks 6 and the `* 2` branch
        # decides nothing, so `* 1`/`* 3`/deleting the derivation all SURVIVE. This is the
        # ONLY pin on the shell's CEILING_FACTOR literal (the Python twin is pinned by
        # test_handoff_support.py::test_floor_factor_and_none, in its `hop_ceiling(8) == 16`
        # assertion — NOT the `hop_ceiling(None)` line, which pins the FLOOR) — so this test
        # is the SSOT divergence guard the Shared Constants section exists to provide.
    def test_env_ceiling_wins_absolutely(self, tmp_path):
        # env MAX_HOPS=1, hops file "1" -> refused even though derived ceiling is 6
    def test_over_expected_notifies_never_refuses(self, tmp_path):
        # expected_hops=1, hops file "1", ceiling 6 -> proceeds; cmux.log contains notify
        # with "expected" in body; stderr notes budget=over-expected
    def test_intent_record_carries_tasks_done(self, tmp_path):
        # 2 DONE reports; reach the spawn -> intent line matches r" intent hop=\d+ tasks_done=2$"
```

**Migration block — FOUR breaking consumers, all mandatory** (an identifier grep finds only the first; see the B1 row for why):
- `test_spawn_handoff_hardening.py::test_nonnumeric_max_hops_reverts_to_default_and_still_refuses` — the fail-open regression: seeds `.handoff-hops="3"` against today's default 3, but the derived ceiling is 6, so it stops refusing and SPAWNS. Pin per the B1 row (seed above the derived ceiling, or set the knob explicitly).
- `test_spawn_handoff.py::test_hop_limit_exits_3` — relies on default `MAX_HOPS=3`; set `SUPERPOWERS_CMUX_MAX_HOPS=3` explicitly in its env (the default is now derived, floor 6).
- `test_spawn_handoff.py::test_new_workspace_and_notify_argv_values_match_spec` — asserts `startswith("Hop 1/3 ")`, rendered from `Hop $SP_HOP/$MAX_HOPS`; no manifest → ceiling 6 → must become `"Hop 1/6 "`.
- `test_spawn_handoff.py::test_spawn_log_record_fields_match_spec_log_format` — asserts `_spawn_log_fields(ctx, "intent") == {"hop": "1"}` by EXACT equality; step (f) adds `tasks_done=`. Before fixing it, sweep for OTHER exact-equality field-set assertions — step (f) and Tasks 9–10 also grow `outcome` records; do not assume this is the only one.

- [ ] **Step 2b: The EIGHT `_handoff_support.py` / `test_handoff_support.py` rows — these are STEPS, not background reading.** Every path Step 6 stages must have a step that writes it; these two had none. (The scope paragraph above said "seven" and omitted **P7-2**, which is explicitly a `test_handoff_support.py` edit — a count inherited and never enumerated, the same defect that BLOCKED an earlier round of this dispatch. Count them yourself.) Each bullet is a required edit with its row id. Production edits in `_handoff_support.py`, tests in `test_handoff_support.py`:
  - **P7-1(ii)** — a readable manifest with a present-but-INVALID `spawn_policy` (`"OFF"`, `"Off"`, JSON `false`, `null`, non-dict `handoff`) currently prints `auto`. **Fail closed to `ask`.** The shell's `*)` arm cannot cover this: `auto` is a recognized value matching its own case arm. **This is the ONLY bullet here that changes production behavior on the SOLE consent gate, so pin it explicitly: assert each of `"OFF"`, JSON `false`, `null` and a non-dict `handoff` prints `ask`. Required positive control — the existing no-`handoff`-block case (`test_handoff_support.py:198`, `{"total_tasks":5}` → `auto`) must STAY `auto`**, which is what forbids a blanket fail-closed. Without that pair the fix that creates new consent behavior ships unpinned while P7-5 pins an adjacent already-correct branch.
  - **P7-3** — `count_tasks_done` reaches its lazy `import yaml` only INSIDE the glob loop, so zero matches ⇒ the `ImportError` never fires ⇒ a fake `0`, which manufactures a stall. **Probe the import once before the glob**, keeping the stdlib-only-at-import property (P7-9(B)). **Pin it on an EMPTY (or absent) reports dir with yaml unimportable: it prints `0` today and must print `unknown`.** Measured: a POPULATED dir already prints `unknown` today, so a test built on one passes BEFORE and AFTER this fix — revert the probe and it stays green. That case is P7-7's positive control, not P7-3's pin. **Two fixtures, one battery.**
  - **P7-6** — `UnicodeDecodeError` subclasses `ValueError`, not the `OSError` `count_tasks_done` catches, so one non-UTF-8 byte in any report exits 1 with empty stdout (violates Module 2 AC-5). Use `errors="replace"` or widen the except. Fixture with invalid bytes; assert `returncode == 0`.
  - **P7-8** — `stall_streak` returns `0` for ANY `OSError`. **Split it:** `FileNotFoundError` → `0`, other `OSError` → `indeterminate`. **NOT a blanket `except OSError: return "indeterminate"`** — that breaks the legitimate first-hop `0` and passes any test pinning only "unreadable ⇒ indeterminate". **Required positive control: assert a MISSING log still returns `0` in the same battery.**
  - **P7-2** — `TestCli` has two tests and neither invokes `stall-streak`. Add CLI coverage, including P7-8's new degraded return.
  - **P7-5** — nothing pins `spawn-policy` on valid-JSON-but-non-object (`5`, `null`, `[1,2]`). They return `ask` correctly today; add the assertions.
  - **P7-7** — the `except ImportError: print("unknown")` mitigation (the designated mitigation for P7-3) has NO test; the mutation `print("unknown")` → `print(0)` SURVIVED. Technique: an `ImportError`-raising `yaml.py` on `PYTHONPATH`. **Positive-control it** — `/usr/bin/python3` on this machine DOES ship PyYAML, so the naive probe passes for the wrong reason. **Its fixture is the POPULATED reports dir — the already-correct case — which makes it the positive control paired with P7-3's empty-dir pin. Do NOT let one populated-dir test stand in for both rows: it cannot detect whether P7-3 was fixed.**
  - **P7-9** — (A) `expected-hops` on an unreadable manifest; (B) the lazy `import yaml` PLACEMENT invariant (hoisting it to module scope passes every existing test, and P7-3 edits that exact function); (D) `derive_expected_hops`'s `isinstance(h, dict)` guard, unpinned while its `_cli` twin is pinned.

- [ ] **Step 3: Run to verify failures**, then **Step 4: Implement** in the script:

(a) Arg parse gains the flag: add `--user-approved) USER_APPROVED=1 ;;` beside `--dry-run` (initialize `USER_APPROVED=0`).

(b) Config layer: DELETE the `MAX_HOPS` block from Layer 0 (its validation moves to (e)); add beside the quota knobs:

```bash
MAX_STALL_HOPS_DEFAULT=1
MAX_STALL_HOPS="${SUPERPOWERS_CMUX_MAX_STALL_HOPS:-$MAX_STALL_HOPS_DEFAULT}"
if ! [[ "$MAX_STALL_HOPS" =~ ^[0-9]+$ ]]; then
  echo "WARNING: invalid SUPERPOWERS_CMUX_MAX_STALL_HOPS ($MAX_STALL_HOPS) — reverting to default $MAX_STALL_HOPS_DEFAULT." >&2
  MAX_STALL_HOPS="$MAX_STALL_HOPS_DEFAULT"
fi
SUPPORT_CLI="$SCRIPT_DIR/_handoff_support.py"
```

(c) After the feature-dir block, resolve the manifest: `MANIFEST_FILE="$WORKTREE_ROOT/$FEATURE_DIR/.sdd-session.json"`.

(d) **Precondition 2b — policy** (immediately after `validate_bundle`, BEFORE the cmux-reachable check; nothing reserved yet):

```bash
# Absent manifest FILE stays `auto` DELIBERATELY: every pre-v2 handoff ships without
# .sdd-session.json and must still spawn. The CLI fails closed to `ask` on a nonexistent
# manifest PATH (omitting the flag is argparse exit 2 — different thing), but this
# `[ -f ]` short-circuit makes that branch unreachable from here.
# The two layers differ ON PURPOSE on this one input — do not "harmonize" them.
SPAWN_POLICY="auto"
if [ -f "$MANIFEST_FILE" ]; then
  # stderr NOT discarded: a CLI failure must be visible, not silently coerced.
  SPAWN_POLICY="$("$PYTHON" "$SUPPORT_CLI" spawn-policy --manifest "$MANIFEST_FILE")"
  # Fail CLOSED: empty stdout (CLI crashed) and every unrecognized value mean
  # NON-consent. `auto` here would make every failure mode of the SOLE consent
  # gate resolve to "spawn without asking"; `ask` is retryable and pre-reservation.
  case "$SPAWN_POLICY" in auto|ask|off) : ;; *) SPAWN_POLICY="ask" ;; esac
fi
if [ "$SPAWN_POLICY" = "off" ]; then
  echo "[spawn-handoff] refused: manifest spawn_policy=off (reason=policy-off). Auto-spawn is disabled for this plan — resume manually." >&2
  print_manual_instructions; exit 3
fi
if [ "$SPAWN_POLICY" = "ask" ] && [ "$USER_APPROVED" != "1" ]; then
  echo "[spawn-handoff] refused: manifest spawn_policy=ask without --user-approved (reason=policy-ask). ASK THE USER, then re-run with --user-approved. No hop was consumed — this refusal is retryable." >&2
  exit 3
fi
```

(e) **Precondition 4 rework** (replaces the flat hop-limit check; runs AFTER the cmux-reachable check so notify works; the malformed-`.handoff-hops` guard stays verbatim where it is):

```bash
# Progress accounting (Decision 8). tasks_done failure degrades to "unknown":
# the stall check SKIPs (stall=indeterminate) — never fake 0, which would
# manufacture stalls. The runaway fail-closed guard remains .handoff-hops's own.
TASKS_DONE="$("$PYTHON" "$SUPPORT_CLI" tasks-done --reports-dir "$REPORTS_DIR" 2>/dev/null)"
[[ "$TASKS_DONE" =~ ^[0-9]+$ ]] || TASKS_DONE="unknown"
EXPECTED_HOPS="unknown"
if [ -f "$MANIFEST_FILE" ]; then
  EXPECTED_HOPS="$("$PYTHON" "$SUPPORT_CLI" expected-hops --manifest "$MANIFEST_FILE" 2>/dev/null)"
  [[ "$EXPECTED_HOPS" =~ ^[0-9]+$ ]] || EXPECTED_HOPS="unknown"
fi
# Ceiling: explicit env wins absolutely; else derived max(6, 2 x expected).
# SSOT: the literals 6 and 2 below MIRROR CEILING_FLOOR / CEILING_FACTOR in
# _handoff_support.py — shell cannot import them, so this is a deliberate,
# NAMED duplication. Change both or neither; a silent divergence is invisible.
if [ -n "$SUPERPOWERS_CMUX_MAX_HOPS" ]; then
  MAX_HOPS="$SUPERPOWERS_CMUX_MAX_HOPS"
  if ! [[ "$MAX_HOPS" =~ ^[0-9]+$ ]]; then
    DERIVED=6; [ "$EXPECTED_HOPS" != "unknown" ] && { DERIVED=$((EXPECTED_HOPS * 2)); [ "$DERIVED" -lt 6 ] && DERIVED=6; }
    echo "WARNING: invalid SUPERPOWERS_CMUX_MAX_HOPS ($MAX_HOPS) — reverting to derived default $DERIVED." >&2
    MAX_HOPS="$DERIVED"
  fi
else
  MAX_HOPS=6
  [ "$EXPECTED_HOPS" != "unknown" ] && { MAX_HOPS=$((EXPECTED_HOPS * 2)); [ "$MAX_HOPS" -lt 6 ] && MAX_HOPS=6; }
fi
```

then, after the existing `SP_HOP=$((HOPS + 1))` / ceiling comparison block (message now says "ceiling"), the stall check:

```bash
BUDGET_FLAG=""
if [ "$TASKS_DONE" = "unknown" ]; then
  echo "[spawn-handoff] stall=indeterminate — tasks_done could not be counted; stall check skipped." >&2
else
  STREAK="$("$PYTHON" "$SUPPORT_CLI" stall-streak --spawn-log "$SPAWN_LOG" --tasks-done "$TASKS_DONE" 2>/dev/null)"
  if [ "$STREAK" = "indeterminate" ]; then
    echo "[spawn-handoff] stall=indeterminate — previous outcome record missing/malformed; stall check skipped." >&2
  elif [[ "$STREAK" =~ ^[0-9]+$ ]] && [ "$STREAK" -gt "$MAX_STALL_HOPS" ]; then
    TOTAL_DISP="?"; [ -f "$MANIFEST_FILE" ] && TOTAL_DISP="$("$PYTHON" -c 'import json,sys;print(json.load(open(sys.argv[1])).get("total_tasks","?"))' "$MANIFEST_FILE" 2>/dev/null)"
    cmux notify --title "SDD handoff" --body "Chain spawning without progress (tasks $TASKS_DONE/$TOTAL_DISP, hops $HOPS) — manual resume" 2>/dev/null || true
    echo "[spawn-handoff] refused: $STREAK consecutive zero-progress hops (> SUPERPOWERS_CMUX_MAX_STALL_HOPS=$MAX_STALL_HOPS) at tasks $TASKS_DONE/$TOTAL_DISP, hops $HOPS (reason=stall). If this chain is legitimately slow, raise SUPERPOWERS_CMUX_MAX_STALL_HOPS via inline env on the spawn invocation — settings.local.json is NOT read by a running session." >&2
    print_manual_instructions; exit 3
  fi
fi
if [ "$EXPECTED_HOPS" != "unknown" ] && [ "$SP_HOP" -gt "$EXPECTED_HOPS" ]; then
  BUDGET_FLAG=" budget=over-expected"
  cmux notify --title "SDD handoff" --body "Hop $SP_HOP exceeds expected_hops=$EXPECTED_HOPS (advisory — spawning anyway)" 2>/dev/null || true
  echo "[spawn-handoff] budget=over-expected (hop $SP_HOP > expected $EXPECTED_HOPS) — advisory only." >&2
fi
```

(f) The intent record gains the count: `printf '%s %s intent hop=%s tasks_done=%s\n' "$(now_iso)" "$SPAWN_ID" "$SP_HOP" "$TASKS_DONE" >> "$SPAWN_LOG"` (same checked-write `if !` wrapper as today).

- [ ] **Step 5: Run the FULL suite + fix migrations** — `.venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider`. All PASS (707 green before this task; report the number you measure). A file-list run is dishonest here because this task moves a global default — narrow only while iterating.

- [ ] **Step 6: Commit** — `git add` the EIGHT explicit paths (never `-A`): `spawn-handoff-session.sh`, `_handoff_support.py`, `test_spawn_handoff.py`, `test_spawn_handoff_v2.py`, `test_spawn_handoff_hardening.py`, `test_handoff_support.py`, `spawn_handoff_helpers.py`, `tests/unit/fixtures/spawn-handoff/`; `git commit -m "feat(cmux-spawn-v2): policy gate + progress-aware stall/ceiling + intent tasks_done"`.

### Task 9: Surface topology + shared launch wrapper + workspace fallback

**Files:** same set as Task 8.

- [ ] **Step 1: Helper.** Add to `spawn_handoff_helpers.py` a v2 cmux stub whose behavior is env-driven (append `cmux_v2_stub()` returning the body string):

```python
CMUX_V2_STUB = r'''
if [ "$1" = "ping" ]; then echo PONG; exit 0; fi
echo "$@" >> "$CMUX_LOG"
case "$1" in
  new-surface)   [ -n "$CMUX_NEW_SURFACE_RC" ] && exit "$CMUX_NEW_SURFACE_RC"
                 echo "OK surface:7 pane:2 workspace:5"; exit 0 ;;
  rename-tab)    echo "OK action=rename target=surface:7"; exit 0 ;;
  send)          [ -n "$CMUX_SEND_RC" ] && exit "$CMUX_SEND_RC"; echo OK; exit 0 ;;
  send-key)      echo OK; exit 0 ;;
  wait-for)      exit "${CMUX_WAITFOR_RC:-0}" ;;
  read-screen)   [ -n "$CMUX_SCREEN_FILE" ] && { cat "$CMUX_SCREEN_FILE"; exit 0; }
                 echo "internal_error: Failed to read terminal text" >&2; exit 1 ;;
  workspace)     [ "$2" = "create" ] || { echo OK; exit 0; }
                 [ -n "$CMUX_WS_CREATE_RC" ] && exit "$CMUX_WS_CREATE_RC"
                 echo "OK workspace:9"; exit 0 ;;
  list-pane-surfaces) printf '* surface:11  SDD resume: demo  [selected]\n'; exit 0 ;;
  *) echo OK; exit 0 ;;
esac
'''
```

(Exact `list-pane-surfaces` line format: copy from Task 0's `cmux-verb-shapes.json` — the stub MUST carry the `* ` selected-row marker and the two-space non-selected indent (key `selected_row_marker`). A marker-less stub is exactly what made the old `$1` parser look green while failing 100% in production. **Also close three MINOR residuals from Task 0's round-2 review while you are in `test_spawn_handoff_v2.py`:** pin the marker↔`[selected]` *correlation* (round 2 showed 5 inversion mutations survive — the marker and `[selected]` can be moved to different rows unnoticed, which is the semantic content of the whole finding); relax `assert len(rows) == 2` to `>= 2`, since 2 is an accidental capture value and a 3-surface re-capture would go RED for the wrong reason; and fix the comment that cites "Step 2c" for `surface_uuid_source.available`, a field Step 2b defines — and whose `false` outcome Step 2b calls *legitimate*, not an escalation.)

- [ ] **Step 2: Failing tests** (`test_spawn_handoff_v2.py`):

```python
class TestSurfaceTopology:
    def test_surface_happy_path(self, tmp_path):
        # v2 stub, spawnable ctx -> exit 0; cmux.log ORDER: new-surface (with
        # --workspace TEST-WS --type terminal --focus false) -> rename-tab
        # --surface surface:7 -> send --surface surface:7 (composed cmd + \n) -> wait-for
        # outcome record: workspace=TEST-WS surface=surface:7 handshake=ok, NO topology= field
    def test_sent_command_carries_inline_env(self, tmp_path):
        # env SUPERPOWERS_CMUX_MAX_STALL_HOPS=2 on the parent -> sent text starts with
        # "export SUPERPOWERS_SPAWN_ID=" and contains "SUPERPOWERS_CMUX_MAX_STALL_HOPS=2"
        # and ends with the successor command
    def test_rename_failure_still_launches(self, tmp_path):
        # rename-tab exit 1 (extend stub via CMUX_RENAME_RC) -> WARNING, send still happens on surface path
    def test_new_surface_failure_falls_back_to_workspace_once(self, tmp_path):
        # CMUX_NEW_SURFACE_RC=1 -> cmux.log shows `workspace create` (canonical verb, NOT
        # new-workspace) with --focus false; outcome: topology=workspace-fallback
        # workspace=workspace:9 surface=surface:11 handshake=ok; exit 0
    def test_send_failure_on_surface_falls_back(self, tmp_path):
        # CMUX_SEND_RC=1 ONLY for the first send (stub counts via a marker file) ->
        # fallback attempted; a SECOND send failure -> exit 3 spawn-failed, hop consumed
    def test_no_double_spawn_after_accepted_send(self, tmp_path):
        # send rc 0 then CMUX_WAITFOR_RC=1 (timeout) -> exit 3; cmux.log contains
        # EXACTLY ONE new-surface and ZERO `workspace create` lines
    def test_reservation_precedes_new_surface(self, tmp_path):
        # port of test_reservation_lands_before_cmux_new_workspace_runs to the surface verb
```

Migrate in `test_spawn_handoff.py` (same task, topology changed): `test_auto_spawn_success_exit_0`, `test_new_workspace_and_notify_argv_values_match_spec`, `test_spawn_log_record_fields_match_spec_log_format`, `test_spawn_failure_keeps_hop_exits_3`, `test_workspace_ref_*` (3 tests), `test_cmux_stdout_is_relayed_not_swallowed`, `test_spawn_failure_rc_survives_stdout_capture`, `test_mktemp_failure_*`, `test_reservation_lands_before_cmux_new_workspace_runs` — update them to the v2 stub + surface expectations, or where they pin the pure workspace-core mechanics, drive them through the fallback path (`CMUX_NEW_SURFACE_RC=1`) asserting `workspace create`. **Also migrate the four tests whose old default stub emits no `OK surface:` stdout and which therefore fail against the new ref-shape checks:** `test_picker_manual_spawn_uses_interactive_command` (also asserts the literal `new-workspace`), `test_append_prompt_file_written_on_real_spawn`, `test_fallback_tail_spawn_id_correlates_with_intent_record`, `test_notify_failure_still_exit_0` (custom stub) — switch them to the v2 stub. **Three tests need their PREMISE rewritten, not just the verb:** the old core degraded an empty `OK` capture to `workspace="(spawned)"` and spawned uncaptured when mktemp failed; the v2 ref-shape checks deliberately make the ref load-bearing (rename/send need it), so both degradations become failures. Rewrite `test_workspace_ref_falls_back_when_cmux_emits_nothing`, the `(spawned)` assertion in `test_spawn_log_record_fields_match_spec_log_format`, and `test_mktemp_failure_still_spawns_uncaptured` to pin the NEW contract (empty/garbled ref or mktemp failure → fallback attempt → spawn-failed exit 3, hop consumed, never a fake ref or a blind launch); `test_mktemp_failure_preserves_spawn_failure_rc` survives naturally. Every migrated test keeps its original invariant (ref propagation, rc survival, reservation ordering) — only the verb/topology/degrade-contract changes.

- [ ] **Step 3: Implement.** In the script:

(a) Title (used by rename-tab now, `/rename` in Task 11): in the config layer:

```bash
TITLE_FORMAT_DEFAULT='hop{hop} SDD {feature}'
TITLE_FORMAT="${SUPERPOWERS_CMUX_TITLE_FORMAT:-$TITLE_FORMAT_DEFAULT}"
[ -n "$TITLE_FORMAT" ] || TITLE_FORMAT="$TITLE_FORMAT_DEFAULT"
```

after `SP_HOP` is known: `TAB_TITLE="${TITLE_FORMAT//\{hop\}/$SP_HOP}"; TAB_TITLE="${TAB_TITLE//\{feature\}/$FEATURE_NAME}"`.

(b) Inline-env prefix (compose beside `SUCCESSOR_CMD`; values shq-quoted; the `export …;` prefix reaches BOTH the primary picker and the runtime-fallback tail):

```bash
INLINE_ENV="export SUPERPOWERS_SPAWN_ID=$SPAWN_ID"
for knob in SUPERPOWERS_CMUX_MAX_HOPS SUPERPOWERS_CMUX_QUOTA_MIN_PCT SUPERPOWERS_CMUX_QUOTA_TIMEOUT \
            SUPERPOWERS_CMUX_QUOTA_TOOL SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT \
            SUPERPOWERS_CMUX_MAX_STALL_HOPS SUPERPOWERS_CMUX_POST_SPAWN SUPERPOWERS_CMUX_TITLE_FORMAT; do
  eval "v=\${$knob}"
  [ -n "$v" ] && INLINE_ENV="$INLINE_ENV $knob=$(shq "$v")"
done
SENT_CMD="$INLINE_ENV; $SUCCESSOR_CMD"
```

(c) New spawn core functions (keep `spawn_claude_workspace` extraction-ready shape as the pattern; the workspace variant migrates its verb):

```bash
# All three publish refs via globals; return non-zero on failure BEFORE the
# launch command is accepted. After launch_into_target returns 0 the command
# is accepted: no caller may create another target (double-spawn guard).
SPAWN_SURFACE_REF=""; SPAWN_WORKSPACE_REF=""; SPAWN_TOPOLOGY="surface"; CAPTURED_REF=""
# ONE capture path for every ref-returning verb (SSOT). Publishes field 2 of the first
# `OK ` line as CAPTURED_REF ALWAYS — even on failure, so a spawn-failed record can name
# a partially-created target — relays stdout to stderr, then returns non-zero on mktemp
# failure, non-zero verb rc, or a ref failing the expected `<prefix>:` shape.
capture_cmux_ref() {
  local prefix="$1"; shift
  local out_f rc
  CAPTURED_REF=""
  out_f="$(mktemp 2>/dev/null)" || return 1
  CMUX_QUIET=1 "$@" >"$out_f"
  rc=$?
  CAPTURED_REF="$(awk '/^OK[ \t]/{print $2; exit}' "$out_f" 2>/dev/null)"
  cat "$out_f" >&2; rm -f "$out_f"
  [ $rc -eq 0 ] || return 1
  case "$CAPTURED_REF" in "$prefix":*) return 0 ;; *) return 1 ;; esac
}
create_surface_target() {
  capture_cmux_ref surface cmux new-surface --workspace "$CMUX_WORKSPACE_ID" \
    --type terminal --working-directory "$WORKTREE_ROOT" --focus false
  local rc=$?
  SPAWN_SURFACE_REF="$CAPTURED_REF"
  [ $rc -eq 0 ] || return 1
  SPAWN_WORKSPACE_REF="$CMUX_WORKSPACE_ID"
  return 0
}
create_workspace_target() {   # one-shot fallback — canonical verb (Decision 19)
  SPAWN_TOPOLOGY="workspace-fallback"
  capture_cmux_ref workspace cmux workspace create --name "SDD resume: $FEATURE_NAME" \
    --cwd "$WORKTREE_ROOT" --focus false
  local rc=$?
  SPAWN_WORKSPACE_REF="$CAPTURED_REF"
  [ $rc -eq 0 ] || return 1
  # Resolve the selected surface. Task 0 MEASURED `* ` prefixing the selected row, so awk's
  # $1 there is `*`, NOT the ref — and this fallback's fresh workspace has exactly ONE
  # always-selected surface: a $1 parser fails 100% in production yet passes a marker-less
  # stub. Match `surface:N` by PATTERN; print EXACTLY ONE line (a multi-line ref globs OK).
  SPAWN_SURFACE_REF="$(cmux list-pane-surfaces --workspace "$SPAWN_WORKSPACE_REF" 2>/dev/null \
    | awk '{ref="";for(i=1;i<=NF;i++)if($i~/^surface:[0-9]+$/){ref=$i;break};if(ref=="")next
            if(first=="")first=ref; if(index($0,"[selected]")){print ref;f=1;exit}} END{if(!f)print first}')"
  case "$SPAWN_SURFACE_REF" in surface:*) : ;; *) return 1 ;; esac
  return 0
}
launch_into_target() {   # shared for BOTH topologies (Decision 2)
  local rt_out
  rt_out="$(cmux rename-tab --surface "$SPAWN_SURFACE_REF" "$TAB_TITLE" 2>&1)"
  case "$rt_out" in OK*) : ;; *) echo "[spawn-handoff] warn: rename-tab failed ($rt_out) — cosmetic, continuing." >&2 ;; esac
  cmux send --surface "$SPAWN_SURFACE_REF" "$SENT_CMD\n"
}
```

(`rename-tab` output is success-checked with a `case` on `OK*`, never ref-parsed — its field 2 is `action=rename`.)

(d) Spawn sequence rewrite (reservation block unchanged above it):

```bash
LAUNCH_ACCEPTED=0
if create_surface_target && launch_into_target; then
  LAUNCH_ACCEPTED=1
else
  if [ "$LAUNCH_ACCEPTED" = "0" ] && [ "$SPAWN_TOPOLOGY" = "surface" ]; then
    echo "[spawn-handoff] surface path failed before launch accepted — one workspace-fallback attempt." >&2
    SPAWN_SURFACE_REF=""; SPAWN_WORKSPACE_REF=""
    if create_workspace_target && launch_into_target; then LAUNCH_ACCEPTED=1; fi
  fi
fi
if [ "$LAUNCH_ACCEPTED" != "1" ]; then
  printf '%s %s outcome hop=%s workspace=%s surface=%s launch=%s bundle=%s quota=%s tasks_done=%s handshake=none%s\n' \
    "$(now_iso)" "$SPAWN_ID" "$SP_HOP" "spawn-failed" "${SPAWN_SURFACE_REF:--}" "$LAUNCH_MODE" "$BUNDLE_ID" "$QUOTA_STATUS" "$TASKS_DONE" \
    "$([ "$SPAWN_TOPOLOGY" = "workspace-fallback" ] && printf ' topology=workspace-fallback')" >> "$SPAWN_LOG"
  cmux notify --title "SDD handoff" --body "Spawn failed after reservation — manual resume" 2>/dev/null || true
  echo "[spawn-handoff] spawn failed AFTER reservation (hop $SP_HOP consumed) — manual fallback." >&2
  print_manual_instructions; exit 3
fi
# Handshake (Task 10 expands this): token or nothing.
TOPOLOGY_FIELD=""; [ "$SPAWN_TOPOLOGY" = "workspace-fallback" ] && TOPOLOGY_FIELD=" topology=workspace-fallback"
if cmux wait-for "sdd-hop-$SPAWN_ID" --timeout "$SPAWN_WAIT_TIMEOUT"; then
  printf '%s %s outcome hop=%s workspace=%s surface=%s launch=%s bundle=%s quota=%s tasks_done=%s handshake=ok%s%s\n' \
    "$(now_iso)" "$SPAWN_ID" "$SP_HOP" "$SPAWN_WORKSPACE_REF" "$SPAWN_SURFACE_REF" "$LAUNCH_MODE" "$BUNDLE_ID" "$QUOTA_STATUS" "$TASKS_DONE" "$TOPOLOGY_FIELD" "$BUDGET_FLAG" >> "$SPAWN_LOG"
  cmux notify --title "SDD handoff" --body "Hop $SP_HOP/$MAX_HOPS — successor confirmed in $SPAWN_SURFACE_REF" 2>/dev/null || \
    echo "[spawn-handoff] warn: notify failed (successor already spawned)" >&2
  echo "[spawn-handoff] spawned successor in $SPAWN_SURFACE_REF of $SPAWN_WORKSPACE_REF (launch=$LAUNCH_MODE handshake=ok). STOP this session."
  exit 0
fi
# timeout: Task 10 replaces this stanza with re-wait + diagnosis
```

`SPAWN_WAIT_TIMEOUT` config (validate-warn-revert; default from Task 0's `cold-start-timing.json` — copy the literal `default_seconds` value into `SPAWN_WAIT_TIMEOUT_DEFAULT` with a comment citing the fixture):

```bash
SPAWN_WAIT_TIMEOUT_DEFAULT=<default_seconds from tests/unit/fixtures/spawn-handoff/cold-start-timing.json>
SPAWN_WAIT_TIMEOUT="${SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT:-$SPAWN_WAIT_TIMEOUT_DEFAULT}"
if ! [[ "$SPAWN_WAIT_TIMEOUT" =~ ^[0-9]+$ ]]; then
  echo "WARNING: invalid SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT ($SPAWN_WAIT_TIMEOUT) — reverting to default $SPAWN_WAIT_TIMEOUT_DEFAULT." >&2
  SPAWN_WAIT_TIMEOUT="$SPAWN_WAIT_TIMEOUT_DEFAULT"
fi
```

Also: delete the old `spawn_claude_workspace` success/failure call-site stanza it replaces; keep `spawn_claude_workspace()` DELETED (its mechanics live on in `create_workspace_target` + shared wrapper — remove the dead function, its argv/notify behavior is superseded) and update the dry-run echo: `--dry-run: would spawn surface in $CMUX_WORKSPACE_ID (workspace fallback armed) — quota=$QUOTA_STATUS launch=$LAUNCH_MODE policy=$SPAWN_POLICY tasks_done=$TASKS_DONE`.

- [ ] **Step 4: Run both unit files** — all PASS (old file fully migrated). **Step 5: Commit** — `"feat(cmux-spawn-v2): surface topology + shared launch wrapper + workspace-create fallback"`.

(The import assertion pinning `SPAWN_WAIT_TIMEOUT_DEFAULT` to Task 0's measured fixture lives in **Task 10 Step 2** — it is wait-for work, and Task 10 owns the handshake. Task 9 still writes the constant, so it is unpinned for exactly one task; that gap is deliberate and recorded under OP-1.)

### Task 10: wait-for handshake, re-wait, read-screen diagnosis

**Files:** same set.

- [ ] **Step 1: Screen fixtures** — `tests/unit/fixtures/spawn-handoff/screens/`: `trust-dialog.txt` (contains `Do you trust the files in this folder?`), `banner.txt` (a Claude session banner WITHOUT any token side-effect — e.g. `Claude Code v2` + composer chrome), `picker-error.txt` (`claude-picker: error: no matching version`), `noise.txt` (shell prompt + scrollback junk).

- [ ] **Step 2: Failing tests:**

```python
class TestHandshake:
    def test_token_is_only_success(self, tmp_path):
        # CMUX_WAITFOR_RC=1 + CMUX_SCREEN_FILE=banner.txt -> exit 3, NOT 0:
        # a full banner on screen never selects success (three live incidents)
        # outcome: handshake=timeout diagnosis=banner
    def test_timeout_rewaits_once_same_duration(self, tmp_path):
        # cmux.log contains exactly TWO wait-for lines, both --timeout <same value>
    def test_diagnosis_trust_dialog_names_dialog_and_steers_to_tab(self, tmp_path):
        # screen=trust-dialog.txt -> stderr names the trust dialog, contains the surface
        # ref, and does NOT contain the fresh-session manual instructions block
    def test_diagnosis_picker_error(self, tmp_path):        # diagnosis=picker-error
    def test_diagnosis_none_on_noise(self, tmp_path):       # diagnosis=none
    def test_diagnosis_unreadable_on_cold_surface(self, tmp_path):
        # no CMUX_SCREEN_FILE -> stub errors internal_error -> diagnosis=unreadable, no crash
    def test_timeout_notifies_and_keeps_hop(self, tmp_path):
        # notify line present; .handoff-hops still incremented; message NEVER claims
        # "nothing was spawned" (assert the string is absent)
    def test_token_success_exits_0_handshake_ok(self, tmp_path):
        # CMUX_WAITFOR_RC=0 -> exit 0, outcome handshake=ok
```

Also add the **import assertion** tying the script's wait default to Task 0's measurement (relocated here from Task 9 — it is wait-for work; see OP-1). Tasks 0/8/9 have all edited `test_spawn_handoff_v2.py` by now, so ADD `import re` and the `SCRIPT` constant **only if absent** (verify `parents[N]` actually resolves; a wrong path fails on `read_text()`, not on the assertion). `SPAWN_WAIT_TIMEOUT_DEFAULT=` must stay a **top-level, column-0** assignment in the script — the regex is anchored, so indenting it into a function or `if` block silently breaks the match.

```python
SCRIPT = (Path(__file__).resolve().parents[2] / "skills" / "subagent-driven-development"
          / "scripts" / "spawn-handoff-session.sh")

def test_wait_timeout_default_matches_measured_fixture():
    d = json.loads((FIX / "cold-start-timing.json").read_text())
    m = re.search(r"^SPAWN_WAIT_TIMEOUT_DEFAULT=(\d+)", SCRIPT.read_text(), re.M)
    assert m, "SPAWN_WAIT_TIMEOUT_DEFAULT= must be a top-level, column-0 assignment (anchored regex)"
    assert int(m.group(1)) == d["default_seconds"], (
        f"script default {m.group(1)} != measured {d['default_seconds']} (cold-start-timing.json)")
```

- [ ] **Step 3: Implement.** Replace Task 9's placeholder timeout tail:

```bash
wait_for_token() {   # one bounded wait; caller decides on re-wait
  cmux wait-for "sdd-hop-$SPAWN_ID" --timeout "$SPAWN_WAIT_TIMEOUT"
}
diagnose_target() {  # NEVER selects the exit code — enrichment only (Decision 5)
  local screen
  screen="$(cmux read-screen --surface "$SPAWN_SURFACE_REF" --scrollback 2>&1)"
  if [ $? -ne 0 ] || grep -qi "internal_error" <<< "$screen"; then
    printf 'unreadable'; return 0
  fi
  if grep -qi "do you trust the files" <<< "$screen"; then printf 'trust-dialog'; return 0; fi
  if grep -qiE "claude-picker: (error|fatal)|no matching version" <<< "$screen"; then printf 'picker-error'; return 0; fi
  if grep -qiE "claude code|esc to interrupt" <<< "$screen"; then printf 'banner'; return 0; fi
  printf 'none'
}
```

(pattern constants may be hoisted; every grep uses here-strings, never a pipe. The banner regex is finalized against Task 0's live captures if they contain a better anchor — record the choice in the code comment.)

Timeout tail:

```bash
if ! wait_for_token; then
  echo "[spawn-handoff] no readiness token after ${SPAWN_WAIT_TIMEOUT}s — one re-wait." >&2
  if ! wait_for_token; then
    DIAG="$(diagnose_target)"
    printf '%s %s outcome hop=%s workspace=%s surface=%s launch=%s bundle=%s quota=%s tasks_done=%s handshake=timeout diagnosis=%s%s%s\n' \
      "$(now_iso)" "$SPAWN_ID" "$SP_HOP" "$SPAWN_WORKSPACE_REF" "$SPAWN_SURFACE_REF" "$LAUNCH_MODE" "$BUNDLE_ID" "$QUOTA_STATUS" "$TASKS_DONE" "$DIAG" "$TOPOLOGY_FIELD" "$BUDGET_FLAG" >> "$SPAWN_LOG"
    cmux notify --title "SDD handoff" --body "Successor in $SPAWN_SURFACE_REF spawned but NOT confirmed (diagnosis=$DIAG) — check that tab" 2>/dev/null || true
    case "$DIAG" in
      trust-dialog)
        echo "[spawn-handoff] handshake=timeout: the successor in $SPAWN_SURFACE_REF is sitting on Claude's FOLDER-TRUST DIALOG ('Do you trust the files in this folder?'). Go to that tab and answer it — do NOT start a fresh session (a successor was spawned; a second one is a double-spawn)." >&2 ;;
      banner)
        echo "[spawn-handoff] handshake=timeout: a Claude session IS visible in $SPAWN_SURFACE_REF but no readiness token arrived. Attach to that tab and continue there — do NOT start a fresh session." >&2 ;;
      picker-error)
        echo "[spawn-handoff] handshake=timeout: the picker errored in $SPAWN_SURFACE_REF (hop $SP_HOP consumed). Inspect that tab; a spawn WAS attempted — check the tab before any manual resume." >&2
        print_manual_instructions ;;
      *)
        echo "[spawn-handoff] handshake=timeout (diagnosis=$DIAG, hop $SP_HOP consumed). A spawn WAS attempted in $SPAWN_SURFACE_REF — check that tab first; only then resume manually." >&2
        print_manual_instructions ;;
    esac
    exit 3
  fi
fi
# token received — handshake=ok success stanza (from Task 9) continues here
```

- [ ] **Step 4: Run + commit** — both unit files PASS; `"feat(cmux-spawn-v2): wait-for handshake + re-wait + read-screen diagnosis enrichment"`.

### Task 11: Post-spawn setup (/rename, /rc) + knobs

**Files:** same set.

- [ ] **Step 1: Failing tests:**

```python
class TestPostSpawn:
    def test_default_sequence_rename_then_rc(self, tmp_path):
        # screen file returns text containing the title after /rename and
        # "/remote-control is active" after /rc (stub: CMUX_SCREEN_FILE with both) ->
        # cmux.log order: send "/rename hop1 SDD feat" -> send-key enter -> read-screen
        # -> send "/rc" -> send-key enter -> read-screen; outcome has NO post_spawn= field
    def test_verify_failure_warns_partial_never_fails_spawn(self, tmp_path):
        # screen without "/remote-control is active" -> exit STILL 0;
        # outcome contains post_spawn=partial:rc
    def test_knob_disables_all(self, tmp_path):
        # SUPERPOWERS_CMUX_POST_SPAWN="" -> no /rename or /rc sends; exit 0
    def test_knob_subset_and_invalid_token(self, tmp_path):
        # "rc" -> only /rc; "rename,bogus" -> WARNING + revert to default both
    def test_title_format_override(self, tmp_path):
        # SUPERPOWERS_CMUX_TITLE_FORMAT='{feature} h{hop}' -> /rename feat h1 (and Task 9's rename-tab used it too)
```

- [ ] **Step 2: Implement.** Config (beside the other knobs):

```bash
POST_SPAWN_DEFAULT="rename,rc"
POST_SPAWN="${SUPERPOWERS_CMUX_POST_SPAWN-$POST_SPAWN_DEFAULT}"   # NOTE ${var-def}: empty string is a VALID value (disables)
if [ -n "$POST_SPAWN" ] && ! [[ "$POST_SPAWN" =~ ^(rename|rc)(,(rename|rc))*$ ]]; then
  echo "WARNING: invalid SUPERPOWERS_CMUX_POST_SPAWN ($POST_SPAWN) — reverting to default $POST_SPAWN_DEFAULT." >&2
  POST_SPAWN="$POST_SPAWN_DEFAULT"
fi
```

Functions + wiring (between handshake success and the outcome record; `POST_SPAWN_FIELD` joins the outcome printf like `TOPOLOGY_FIELD`):

```bash
post_spawn_send_verified() {
  # $1=text to send, $2=expected on screen, $3=step name, $4=match mode (fixed|regex).
  # rename verifies the TITLE (arbitrary user text -> fixed-string -F); rc
  # verifies a known phrase (regex alternation -E). Both here-strings, no pipes.
  local screen
  cmux send --surface "$SPAWN_SURFACE_REF" "$1" 2>/dev/null
  cmux send-key --surface "$SPAWN_SURFACE_REF" enter 2>/dev/null
  sleep 2
  screen="$(cmux read-screen --surface "$SPAWN_SURFACE_REF" --scrollback 2>/dev/null)"
  if [ "$4" = "fixed" ]; then
    grep -qiF "$2" <<< "$screen" && return 0
  else
    grep -qiE "$2" <<< "$screen" && return 0
  fi
  echo "[spawn-handoff] warn: post-spawn step '$3' unverified — cosmetic, successor is alive (post_spawn=partial:$3)." >&2
  return 1
}
POST_SPAWN_FIELD=""
run_post_spawn() {   # after handshake=ok ONLY; failures are WARNINGs by contract (§5.3)
  local step
  local IFS=','
  for step in $POST_SPAWN; do
    case "$step" in
      rename) post_spawn_send_verified "/rename $TAB_TITLE" "$TAB_TITLE" "rename" "fixed" || { POST_SPAWN_FIELD=" post_spawn=partial:rename"; return 0; } ;;
      rc)     post_spawn_send_verified "/rc" "/remote-control is active|remote.control" "rc" "regex" || { POST_SPAWN_FIELD=" post_spawn=partial:rc"; return 0; } ;;
    esac
  done
  return 0
}
[ -n "$POST_SPAWN" ] && run_post_spawn
```

(First failed step records `partial:<step>` and stops the sequence — the record names where it stopped.)

- [ ] **Step 3: Run + commit** — both files PASS; `"feat(cmux-spawn-v2): script-driven /rename + /rc post-spawn setup + knobs"`.

## Module 3 Acceptance Criteria

- [ ] `handoff_spawn: off` / un-approved `ask` refuse pre-reservation (no hop consumed, retryable message).
- [ ] Two consecutive zero-progress hops refuse with `tasks X/Y, hops N` + the inline-env raise instruction; progress chains are never refused below the ceiling; first hop and indeterminate history SKIP.
- [ ] Ceiling defaults to `max(6, 2×expected_hops)`; explicit env wins absolutely; `.handoff-hops` fail-closed guard untouched.
- [ ] Success path: `new-surface --focus false` in the caller's workspace → `rename-tab` → `send` (inline `export` env prefix) → token → `handshake=ok` → exit 0. Outcome carries `workspace=`, `surface=`, `tasks_done=`.
- [ ] Surface-path failure BEFORE an accepted send falls back ONCE through the SAME wrapper via `workspace create` (`topology=workspace-fallback`); an accepted send NEVER spawns twice.
- [ ] Timeout → one re-wait → exit 3 `handshake=timeout` with `diagnosis=` enrichment; a stubbed banner with no token is NOT success; trust-dialog/banner instructions steer to the existing tab; every timeout notifies; no message claims nothing was spawned.
- [ ] Post-spawn `/rename` + `/rc` verified by read-screen; failures are `post_spawn=partial:<step>` WARNINGs, never spawn failures; `SUPERPOWERS_CMUX_POST_SPAWN=""` disables.
- [ ] `tests/unit/test_spawn_handoff.py` fully migrated in the same tasks that changed the behavior; both unit files green after every task.
