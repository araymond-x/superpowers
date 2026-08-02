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

`_handoff_support.py` was read-only for Module 3 as first written, but **EIGHT** scheduled rows are production/test edits to it and its test file — P7-1(ii), P7-2, P7-3, P7-5, P7-6, P7-7, P7-8, P7-9 (**executed by Step 2b, which is authoritative; this paragraph only justifies the scope. An earlier version said "seven" and omitted P7-2**), and the register routes them here — Task 8 consumes `spawn-policy`, `tasks-done` and `stall-streak`, so it owns their supply side. Scope widened for Task 8 ONLY; it reverts to read-only for Tasks 9–11. **B7 inverts by directory: `_handoff_support.py` is scanned by `check_python39_compat`, so use `Optional[X]`/`Dict[str,int]`, never `X | None`/`dict[str,int]`.**

- [x] **Step 1: Helper + fixtures.** In `spawn_handoff_helpers.py` add a manifest writer; in `fixtures/spawn-handoff/` nothing new is needed yet (manifests are written per-test):

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

- [x] **Step 2: Failing tests** (in `test_spawn_handoff_v2.py`; use `run_spawn` throughout):

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

- [x] **Step 2b: The EIGHT `_handoff_support.py` / `test_handoff_support.py` rows — these are STEPS, not background reading.** Every path Step 6 stages must have a step that writes it; these two had none. (The scope paragraph above said "seven" and omitted **P7-2**, which is explicitly a `test_handoff_support.py` edit — a count inherited and never enumerated, the same defect that BLOCKED an earlier round of this dispatch. Count them yourself.) Each bullet is a required edit with its row id. Production edits in `_handoff_support.py`, tests in `test_handoff_support.py`:
  - **P7-1(ii)** — a readable manifest with a present-but-INVALID `spawn_policy` (`"OFF"`, `"Off"`, JSON `false`, `null`, non-dict `handoff`) currently prints `auto`. **Fail closed to `ask`.** The shell's `*)` arm cannot cover this: `auto` is a recognized value matching its own case arm. **This is the ONLY bullet here that changes production behavior on the SOLE consent gate, so pin it explicitly: assert each of `"OFF"`, JSON `false`, `null` and a non-dict `handoff` prints `ask`. Required positive control — the existing no-`handoff`-block case (in `test_handoff_support.py::test_expected_hops_and_policy_cli_on_legacy_and_garbage`, `{"total_tasks":5,"tier":"standard"}` → `auto`) must STAY `auto`**, which is what forbids a blanket fail-closed. Without that pair the fix that creates new consent behavior ships unpinned while P7-5 pins an adjacent already-correct branch.
  - **P7-3** — `count_tasks_done` reaches its lazy `import yaml` only INSIDE the glob loop, so zero matches ⇒ the `ImportError` never fires ⇒ a fake `0`, which manufactures a stall. **Probe the import once before the glob**, keeping the stdlib-only-at-import property (P7-9(B)). **Pin it on an EMPTY (or absent) reports dir with yaml unimportable: it prints `0` today and must print `unknown`.** Measured: a POPULATED dir already prints `unknown` today, so a test built on one passes BEFORE and AFTER this fix — revert the probe and it stays green. That case is P7-7's positive control, not P7-3's pin. **Two fixtures, one battery.**
  - **P7-6** — `UnicodeDecodeError` subclasses `ValueError`, not the `OSError` `count_tasks_done` catches, so one non-UTF-8 byte in any report exits 1 with empty stdout (violates Module 2 AC-5). Use `errors="replace"` or widen the except. Fixture with invalid bytes; assert `returncode == 0`.
  - **P7-8** — `stall_streak` returns `0` for ANY `OSError`. **Split it:** `FileNotFoundError` → `0`, other `OSError` → `indeterminate`. **NOT a blanket `except OSError: return "indeterminate"`** — that breaks the legitimate first-hop `0` and passes any test pinning only "unreadable ⇒ indeterminate". **Required positive control: assert a MISSING log still returns `0` in the same battery.**
  - **P7-2** — `TestCli` has two tests and neither invokes `stall-streak`. Add CLI coverage, including P7-8's new degraded return.
  - **P7-5** — nothing pins `spawn-policy` on valid-JSON-but-non-object (`5`, `null`, `[1,2]`). They return `ask` correctly today; add the assertions.
  - **P7-7** — the `except ImportError: print("unknown")` mitigation (the designated mitigation for P7-3) has NO test; the mutation `print("unknown")` → `print(0)` SURVIVED. Technique: an `ImportError`-raising `yaml.py` on `PYTHONPATH`. **Positive-control it** — `/usr/bin/python3` on this machine DOES ship PyYAML, so the naive probe passes for the wrong reason. **Its fixture is the POPULATED reports dir — the already-correct case — which makes it the positive control paired with P7-3's empty-dir pin. Do NOT let one populated-dir test stand in for both rows: it cannot detect whether P7-3 was fixed.**
  - **P7-9** — (A) `expected-hops` on an unreadable manifest; (B) the lazy `import yaml` PLACEMENT invariant (hoisting it to module scope passes every existing test, and P7-3 edits that exact function); (D) `derive_expected_hops`'s `isinstance(h, dict)` guard, unpinned while its `_cli` twin is pinned.

- [x] **Step 3: Run to verify failures**, then **Step 4: Implement** in the script:

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
# AMENDED POST-QUALITY-REVIEW (this fence now matches the LANDED code — the
# original two-copy form is preserved in deviations.md's PlanDeviation row).
# Ceiling: derive max(6, 2 x expected) ONCE, then let an explicit VALID env value
# override it absolutely. The derivation used to exist TWICE — once as the
# invalid-knob revert target, once as the else-branch default — and only the
# second copy was reachable by any test, so `* 99` in the first survived the
# entire suite. Duplication does not merely risk drift: it SPLITS a guard's test
# coverage in a way per-guard review cannot see. Keep this single.
# SSOT: the floor and factor literals below MIRROR CEILING_FLOOR / CEILING_FACTOR
# in _handoff_support.py — shell cannot import them, so this is a deliberate,
# NAMED duplication. It is enforced: test_handoff_support.py::
# test_shared_constants_are_the_ssot_the_shell_mirrors READS THIS FILE and
# compares the literals. Change both or neither.
# Deliberately NOT clamped from above: expected_hops is plan-author-declared and
# schema-validated, so an author who writes expected_hops=500 has declared a
# 500-hop plan and the ceiling is elastic in it BY DESIGN. The backstop against a
# chain that spawns without PROGRESSING is the stall gate below, not this number.
# A CEILING_MAX was considered and rejected (deviations.md): it would add a fourth
# literal with no Python twin, in the region Task 9 edits.
DERIVED=6
if [ "$EXPECTED_HOPS" != "unknown" ]; then
  DERIVED=$((EXPECTED_HOPS * 2))
  [ "$DERIVED" -lt 6 ] && DERIVED=6
fi
MAX_HOPS="$DERIVED"
if [ -n "$SUPERPOWERS_CMUX_MAX_HOPS" ]; then
  if [[ "$SUPERPOWERS_CMUX_MAX_HOPS" =~ ^[0-9]+$ ]]; then
    MAX_HOPS="$SUPERPOWERS_CMUX_MAX_HOPS"
  else
    echo "WARNING: invalid SUPERPOWERS_CMUX_MAX_HOPS ($SUPERPOWERS_CMUX_MAX_HOPS) — reverting to derived default $DERIVED." >&2
  fi
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

- [x] **Step 5: Run the FULL suite + fix migrations** — `.venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider`. All PASS (707 green before this task; report the number you measure). A file-list run is dishonest here because this task moves a global default — narrow only while iterating.

- [x] **Step 6: Commit** — `git add` the EIGHT explicit paths (never `-A`): `spawn-handoff-session.sh`, `_handoff_support.py`, `test_spawn_handoff.py`, `test_spawn_handoff_v2.py`, `test_spawn_handoff_hardening.py`, `test_handoff_support.py`, `spawn_handoff_helpers.py`, `tests/unit/fixtures/spawn-handoff/`; `git commit -m "feat(cmux-spawn-v2): policy gate + progress-aware stall/ceiling + intent tasks_done"`.

### Task 9: Surface topology + shared launch wrapper + workspace fallback

**Files:** same set as Task 8.

- [x] **Step 1: Helper.** Add to `spawn_handoff_helpers.py` a v2 cmux stub whose behavior is env-driven (append `cmux_v2_stub()` returning the body string):

```python
CMUX_V2_STUB = r'''
if [ "$1" = "ping" ]; then echo PONG; exit 0; fi
echo "$@" >> "$CMUX_LOG"
case "$1" in
  new-surface)   [ -n "$CMUX_NEW_SURFACE_RC" ] && exit "$CMUX_NEW_SURFACE_RC"
                 echo "OK surface:7 pane:2 workspace:5"; exit 0 ;;
  rename-tab)    echo "OK action=rename tab=tab:77 workspace=workspace:29"; exit 0 ;;
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

- [x] **Step 1b: Close the TWO deferred residuals from Task 8's quality re-review round 3.** These are STEPS, not background reading — they are rows in `deviations.md` marked `Pending — TASK 9`, and a finding that no checkbox commands is a finding nobody does (this module already lost two `_handoff_support.py` paths to exactly that, which BLOCKED a partner round). Report on each by id.
  - **M3** (`test_spawn_handoff_v2.py`) — Task 8's F3 pin reads `assert "WARNING:" not in r.stderr` under the message "no knob is set — nothing may warn about one". It is fail-closed but misattributes: ANY future warning on the no-knob path trips it and blames the knob. Narrow it to the substring `invalid SUPERPOWERS_CMUX_MAX_HOPS`. **⚠ NARROWING CAN MAKE IT VACUOUS — the narrowed form is satisfied trivially if that substring never appears anywhere in the run. REQUIRED positive control: mutate `if [ -n "$SUPERPOWERS_CMUX_MAX_HOPS" ]; then` → `if true; then` and confirm the narrowed assertion still goes RED.** Without that control you have traded a live over-broad pin for a dead precise one, which is strictly worse than leaving it alone.
  - **M4** (`spawn-handoff-session.sh`, comment-only) — in the SSOT comment block, "a second copy in any `$(( ))` or `(( ))` shape fails too" is false for `$((E * 2))`; the next sentence corrects it, so it misleads only a reader who stops early. Qualify it to match the (now-accurate) `KNOWN RESIDUAL ESCAPES` block in `test_handoff_support.py`, which is the SSOT for what that guard does and does not catch. **`test_handoff_support.py` is READ-ONLY for this task — read it, do not edit it.**

- [x] **Step 1c: Discharge B1's SECOND clause — `test_spawn_handoff_hardening.py`.** `test_spawn_handoff_hardening.py` is in this task's write scope (Write-Scope table, Task 9 row) and `deviations.md` line 158 + the Task-8 row assign this clause to Task 9, but **no step commanded it until now** — the same producer-less-obligation defect that BLOCKED Task 8's partner round 3, recurring one task later. It is a **FAIL-OPEN, and this task is what opens it**: `_did_not_spawn()` currently returns `"new-workspace" not in _cmux_log(tmp_path)`. The moment Step 3 switches the script to `new-surface`, that expression is True **even when the script spawned**, silently voiding the seven refusal assertions that depend on it — a runaway-chain guard that passes because it can no longer see a spawn.
  - Rewrite `_did_not_spawn` to assert the absence of **EVERY** spawn verb — `new-surface`, `workspace create`, and the legacy `new-workspace` (keep it: an old stub or a partial revert must not read as "did not spawn").
  - **PUT THE VERB LIST IN EXACTLY ONE PLACE.** Add `SPAWN_VERBS = ("new-surface", "workspace create", "new-workspace")` and a `did_not_spawn(log_text)` helper to `spawn_handoff_helpers.py` — it is in this task's six-path write scope and is ALREADY imported by both `test_spawn_handoff.py` and `test_spawn_handoff_hardening.py`, so the seam exists. `_did_not_spawn` and all three `test_spawn_handoff.py` sites (Step 1d class (iv)) consume it; both positive controls below run against that single helper. **A second copy of this list in either test file is the drift shape `deviations.md:127` already caught once this sprint** (two `SpawnPolicy` Literals), where the remedy was written into the plan rather than left to the implementer. Note the log-reader is currently triplicated across the three test files with zero copies in helpers — do not add a fourth.
  - **REQUIRED: TWO positive controls, not one.** `_did_not_spawn` must return **False** on (a) a surface-path spawn log AND (b) a `CMUX_NEW_SURFACE_RC=1` **fallback** log containing `workspace create`. One control pins only the `new-surface` disjunct: a rewrite like `"new-surface" not in log and "workspace create" not in log.lower()` passes control (a) while leaving the fallback verb exactly as fail-open as the bug being fixed — and the fallback is the reachable path where a spawn happens with `new-surface` *absent from a successful create*. Both are constructible today: `test_absent_and_empty_hop_counter_remain_the_first_hop_case` already performs a real spawn, and `cmux_v2_stub()` + `CMUX_NEW_SURFACE_RC=1` gives the second. Without both, "asserts absence of every verb" is indistinguishable from "asserts absence of a verb no log contains" — the identical fail-open in a new spelling.
  - Note the predicate's meaning shifts from "did not spawn" to "did not ATTEMPT a spawn verb". That is the correct, conservative direction — do NOT "improve" it into checking success.
  - **⚠ SEQUENCING: re-run both controls AFTER Step 3 lands.** Run before it, a genuinely-spawning log still contains `new-workspace`, so the control passes against the OLD verb and proves nothing about the post-Step-3 world.
  - **TWO MORE TESTS IN THIS FILE BREAK OUTRIGHT UNDER STEP 3, and no step named them until now** — `test_absent_and_empty_hop_counter_remain_the_first_hop_case` (line ~154) and `test_feature_dir_name_containing_dots_is_still_accepted` (line ~242). Both assert `returncode == 0` on a real spawn driven by the DEFAULT stub, which emits no `OK surface:` stdout; after Step 3's ref-shape check `capture_cmux_ref` fails, both topologies fail before launch, and they exit 3. Switch both to `cmux_v2_stub()`. **Each is the precision fence on an M1/M2 fail-closed guard** — the test that stops the guard over-tightening into refuse-everything — so preserve its original invariant (a legitimate first hop / a legitimate dotted feature dir must SPAWN and reserve). Do not weaken either to `!= 1`.
  - Do NOT weaken Task 8's `SUPERPOWERS_CMUX_MAX_HOPS=3` pins in this file; B1's Task-8 clause is already discharged.

- [x] **Step 1d: Migrate `test_spawn_handoff.py` to the v2 topology.** *(Promoted from prose to a checkbox: this work targets a DIFFERENT file than Step 2's header names, and lived in an unnumbered paragraph that commanded nothing — the exact shape that BLOCKED Task 8's partner round 3. Enumerate the tests yourself from the paragraph below Step 2's fence; do not trust any count, including this sentence's.)* The paragraph immediately following Step 2's code fence is authoritative for WHICH tests and HOW. It has three classes, and the third is not a mechanical verb swap: **(i)** tests migrated to the v2 stub + surface expectations, or driven through the fallback path (`CMUX_NEW_SURFACE_RC=1`) where they pin pure workspace-core mechanics; **(ii)** four tests whose old default stub emits no `OK surface:` stdout and therefore fail the new ref-shape checks — switch them to the v2 stub; **(iii)** three tests whose **PREMISE must be rewritten**, because Task 9 deliberately makes the ref load-bearing and so converts two old *degradations* into *failures* — `test_workspace_ref_falls_back_when_cmux_emits_nothing`, the `(spawned)` assertion inside `test_spawn_log_record_fields_match_spec_log_format`, and `test_mktemp_failure_still_spawns_uncaptured` must pin the NEW contract (empty/garbled ref or mktemp failure → fallback attempt → spawn-failed exit 3, hop consumed, **never a fake ref and never a blind launch**). Every migrated test keeps its original invariant — ref propagation, rc survival, reservation ordering — only the verb/topology/degrade-contract changes. **A migrated test that no longer asserts its original invariant is a deleted test wearing its name.**
  - **(iv) THREE ASSERTIONS THAT GO SILENTLY VACUOUS — the identical B1 fail-open, in this file, and in NONE of the three classes above.** `test_spawn_handoff.py` contains `"new-workspace" not in …` three more times: line ~636 `test_dry_run_spawns_nothing`, line ~1179 `test_hops_write_failure_exits_3_without_spawning`, line ~1201 `test_intent_write_failure_exits_3_without_spawning`. **These are more dangerous than any test that breaks:** a broken test goes RED and gets fixed by whoever runs the suite, whereas these stay **green forever** — after Step 3 the script never emits `new-workspace`, so a `--dry-run` that actually spawned a surface, or a reservation-write failure that spawned anyway, satisfies all three. Rewrite all three to the shared helper from Step 1c, in the SAME pass. **Rank them with this discriminator, not by intuition: does the assertion become FALSE if a spawn occurred?** `not (reports/.handoff-hops).exists()` and `not handoff-spawn.log.exists()` (both in ~636) DO — reservation strictly precedes spawn, so they are *direct* anti-spawn legs. `"intent" not in log` (~1179) does, transitively — the reservation never completed. **`.handoff-hops == "1"` (~1201) does NOT** — the hop is consumed on the reservation path whether or not a spawn followed. So once the `new-workspace` leg goes vacuous, `test_intent_write_failure_exits_3_without_spawning`'s only remaining spawn evidence is `rc == 3`, making **~1201 the weakest of the three and ~636 the best-protected** — the inverse of the ranking an earlier draft of this step asserted. (That draft claimed ~636 "would assert nothing at all"; it was checked against the source and is false. Recorded because this step teaches distrust of vacuous assertions, and an implementer who positive-controls the claim — as this plan demands elsewhere — would find it wrong.)
  - **(v) `test_mktemp_failure_preserves_spawn_failure_rc` SURVIVES ITS OWN DELETION.** Step 2's paragraph says it "survives naturally" — it does, but vacuously and for a new reason. After Step 3, `capture_cmux_ref` returns 1 on `mktemp` failure **before running the verb at all**, so its custom stub's `exit 5` is unreachable and its stated invariant ("the uncaptured branch must propagate cmux's own exit code — the whole ladder hangs off that `rc=$?`") no longer exists in the code, while every assertion (rc 3, `spawn-failed`, hops `1`) still passes. Rewrite its premise alongside its class-(iii) sibling to pin the NEW contract (mktemp failure → both topologies fail before launch → spawn-failed exit 3, hop consumed), or delete it with a recorded reason. **Do not leave it green and unexamined** — this is the plan's own rule firing on a test the paragraph explicitly waved through.

- [x] **Step 2: Failing tests** (`test_spawn_handoff_v2.py`):

```python
class TestSurfaceTopology:
    def test_surface_happy_path(self, tmp_path):
        # v2 stub, spawnable ctx -> exit 0; cmux.log ORDER: new-surface (with
        # --workspace TEST-WS --type terminal --focus false) -> rename-tab
        # --workspace TEST-WS --surface surface:7 -> send --surface surface:7 (composed cmd + \n) -> wait-for
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
    def test_rename_tab_carries_workspace_on_both_topologies(self, tmp_path):
        # deviations.md:17 — rename-tab resolves refs only in the CALLER's workspace.
        # Recorded rename-tab argv carries --workspace on the surface path AND on the
        # CMUX_NEW_SURFACE_RC=1 fallback (where its absence is FATAL: the successor
        # surface is by definition not in the caller's workspace). Consume the frozen
        # fixture key `rename_tab`; do not restate the flag.
```

Migrate in `test_spawn_handoff.py` (same task, topology changed): `test_auto_spawn_success_exit_0`, `test_new_workspace_and_notify_argv_values_match_spec`, `test_spawn_log_record_fields_match_spec_log_format`, `test_spawn_failure_keeps_hop_exits_3`, `test_workspace_ref_*` (3 tests), `test_cmux_stdout_is_relayed_not_swallowed`, `test_spawn_failure_rc_survives_stdout_capture`, `test_mktemp_failure_*`, `test_reservation_lands_before_cmux_new_workspace_runs` — update them to the v2 stub + surface expectations, or where they pin the pure workspace-core mechanics, drive them through the fallback path (`CMUX_NEW_SURFACE_RC=1`) asserting `workspace create`. **Also migrate the four tests whose old default stub emits no `OK surface:` stdout and which therefore fail against the new ref-shape checks:** `test_picker_manual_spawn_uses_interactive_command` (also asserts the literal `new-workspace`), `test_append_prompt_file_written_on_real_spawn`, `test_fallback_tail_spawn_id_correlates_with_intent_record`, `test_notify_failure_still_exit_0` (custom stub) — switch them to the v2 stub. **Three tests need their PREMISE rewritten, not just the verb:** the old core degraded an empty `OK` capture to `workspace="(spawned)"` and spawned uncaptured when mktemp failed; the v2 ref-shape checks deliberately make the ref load-bearing (rename/send need it), so both degradations become failures. Rewrite `test_workspace_ref_falls_back_when_cmux_emits_nothing`, the `(spawned)` assertion in `test_spawn_log_record_fields_match_spec_log_format`, and `test_mktemp_failure_still_spawns_uncaptured` to pin the NEW contract (empty/garbled ref or mktemp failure → fallback attempt → spawn-failed exit 3, hop consumed, never a fake ref or a blind launch); `test_mktemp_failure_preserves_spawn_failure_rc` survives naturally. Every migrated test keeps its original invariant (ref propagation, rc survival, reservation ordering) — only the verb/topology/degrade-contract changes.

- [x] **Step 3: Implement.** In the script:

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
  rt_out="$(cmux rename-tab --workspace "$SPAWN_WORKSPACE_REF" --surface "$SPAWN_SURFACE_REF" "$TAB_TITLE" 2>&1)"
  case "$rt_out" in OK*) : ;; *) echo "[spawn-handoff] warn: rename-tab failed ($rt_out) — cosmetic, continuing." >&2 ;; esac
  cmux send --surface "$SPAWN_SURFACE_REF" "$SENT_CMD\n"
}
```

(`rename-tab` output is success-checked with a `case` on `OK*`, never ref-parsed — its field 2 is `action=rename`.)

**`--workspace` on `rename-tab` DISCHARGES `deviations.md:17`** (`Pending — Module 3 amendment`), whose basis Task 0 MEASURED: `rename-tab` resolves refs only within the CALLER's workspace unless `--workspace` is passed (`not_found: Tab not found`, exit 1; four data points plus a warm/cold control), and Task 0's frozen `cmux-verb-shapes.json` key `rename_tab` carries the flag in its argv. `deviations.md:39` narrows the *impact* to a tab title — it does NOT retire the amendment. `--workspace "$SPAWN_WORKSPACE_REF"` is correct for BOTH topologies and is populated by launch time: `create_surface_target` sets it after its rc guard (reached only on success, and `&&` sequences it before `launch_into_target`); `create_workspace_target` sets it from `CAPTURED_REF` before its rc guard. **Add a test asserting the recorded `rename-tab` argv carries `--workspace` on BOTH the surface path AND the `CMUX_NEW_SURFACE_RC=1` fallback path** — the fallback is where its absence is fatal (the successor surface is by definition not in the caller's workspace), and `test_rename_failure_still_launches` treats rename failure as cosmetic, so without this pin a permanently-failing rename stays green forever. `close-surface` needs NO change: it is called nowhere in Modules 3–4 (`deviations.md:39`, re-verified).

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

`SPAWN_WAIT_TIMEOUT` config (validate-warn-revert; default from Task 0's `cold-start-timing.json` — copy the literal `default_seconds` value into `SPAWN_WAIT_TIMEOUT_DEFAULT`). **The provenance comment's wording is PRESCRIBED by `deviations.md:22`, not free-form: it must say `spec floor; Task 0 measured 8–11s cold start`.** The reason is that the derivation was `max(60, 2 × 11) = 60` — the 60s FLOOR dominated, so 60 was **NOT measured**. A comment that merely "cites the fixture" is satisfiable by exactly the misleading phrasing ("measured default") that row exists to prevent. Do not paraphrase. (The *import assertion* pinning this constant to the fixture moved to Task 10 under OP-1; the constant and its comment remain Task 9's.)

```bash
SPAWN_WAIT_TIMEOUT_DEFAULT=<default_seconds from tests/unit/fixtures/spawn-handoff/cold-start-timing.json>
SPAWN_WAIT_TIMEOUT="${SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT:-$SPAWN_WAIT_TIMEOUT_DEFAULT}"
if ! [[ "$SPAWN_WAIT_TIMEOUT" =~ ^[0-9]+$ ]]; then
  echo "WARNING: invalid SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT ($SPAWN_WAIT_TIMEOUT) — reverting to default $SPAWN_WAIT_TIMEOUT_DEFAULT." >&2
  SPAWN_WAIT_TIMEOUT="$SPAWN_WAIT_TIMEOUT_DEFAULT"
fi
```

Also: delete the old `spawn_claude_workspace` success/failure call-site stanza it replaces; keep `spawn_claude_workspace()` DELETED (its mechanics live on in `create_workspace_target` + shared wrapper — remove the dead function, its argv/notify behavior is superseded) and update the dry-run echo: `--dry-run: would spawn surface in $CMUX_WORKSPACE_ID (workspace fallback armed) — quota=$QUOTA_STATUS launch=$LAUNCH_MODE policy=$SPAWN_POLICY tasks_done=$TASKS_DONE`.

**⚠ THIS TASK HAS NO SEPARATE "run to verify the tests fail" STEP (Task 8 had one).** Steps 1b–1d and Step 2's class-(iii) premise rewrites are **expected RED until Step 3 lands** — read that RED as the plan working, not as your own error. And **`tests/integration/sdd-e2e-test.sh` (its `new-workspace` grep) goes RED after this task and STAYS red until Task 17**, which owns that rewrite. It is outside this task's write scope: do not touch it and do not report it as a Task 9 failure. Step 4's acceptance is the **unit** suite.

- [x] **Step 4: Run the FULL unit suite** — not "both unit files": Steps 1b–1d touch `test_spawn_handoff_v2.py`, `test_spawn_handoff.py` **and** `test_spawn_handoff_hardening.py`, and Step 3 rewrites the spawn core that other suites exercise. All PASS, old file fully migrated (baseline before this task: **748**; re-measure, do not inherit that number). **Step 5: Commit** — never `git add -A`; stage explicit paths, enumerated against what you ACTUALLY changed rather than copied from any list. This task's write scope resolves to **SIX** paths ("first five above" in the Write-Scope row = Task 8's first five, in order): `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff_v2.py`, `tests/unit/test_spawn_handoff.py`, `tests/unit/spawn_handoff_helpers.py`, `tests/unit/fixtures/spawn-handoff/` — **plus** `tests/unit/test_spawn_handoff_hardening.py`. The fixtures dir is likely untouched (this task's stub lives in helpers, and `cmux-verb-shapes.json` is read-only source), but it IS writable — named explicitly so a fixture addition cannot be silently dropped. `tests/unit/test_handoff_support.py` and `_handoff_support.py` are **READ-ONLY** for this task. **Also flip `deviations.md:17` off `Pending — Module 3 amendment`** — this task discharges it (the `--workspace` fence + the both-topologies argv pin). A row that is satisfied but still reads `Pending` is indistinguishable from one that was forgotten. Commit message: `"feat(cmux-spawn-v2): surface topology + shared launch wrapper + workspace-create fallback"`.

(The import assertion pinning `SPAWN_WAIT_TIMEOUT_DEFAULT` to Task 0's measured fixture lives in **Task 10 Step 2** — it is wait-for work, and Task 10 owns the handshake. Task 9 still writes the constant, so it is unpinned for exactly one task; that gap is deliberate and recorded under OP-1.)

### Task 10: wait-for handshake, re-wait, read-screen diagnosis

**ROUTING (added 2026-08-02): `deviations.md:18` — the trust-preflight DECISION — is assigned to THIS task.** It sat at `Pending — Module 3 decision` with no step in ANY Module 3 task commanding it, which is how a decision becomes a silent omission. Task 10 owns `diagnosis=trust-dialog`, so it is the right home. **This is a DECISION to record, not necessarily a preflight to build.** Task 0 measured the modal live: an interactive `claude-picker` launch into an untrusted `--working-directory` raises the trust modal and sits there, never reaching SessionStart, therefore never signaling the token → `handshake=timeout` plus a consumed hop that one keystroke would have fixed — **and a fresh worktree is exactly the untrusted-path case this feature targets.** In Step 4, record an explicit decision in `deviations.md` — build a preflight, or decline with reasoning — and flip row 18 off `Pending`. **Do NOT decline on the unmeasured assumption that `$WORKTREE_ROOT` is already trusted because the parent runs there;** that argument is plausible and untested, and Task 0 measured the opposite case live. If you decline, say what would have to be true and what would falsify it.

**Files:** same set.

- [ ] **Step 1: Screen fixtures** — `tests/unit/fixtures/spawn-handoff/screens/`.

  **AMENDED 2026-08-02 (partner review, BLOCKER 1) — the original anchors were INVENTED and the frozen READ-ONLY Task 0 fixture CONTRADICTS them.** Measured, with a positive control (the string `trust` IS present in the fixture, so the instrument works): the phrase `Do you trust the files in this folder?` **appears nowhere** in `cmux-verb-shapes.json`. The real measured anchors under `trust_dialog_screen.candidate_anchors` are `Quick safety check: Is this a project you created or` and `1. Yes, I trust this folder`. Worse, run against the ONE live capture that carries a screen (`trust_dialog_screen`), the fence's **banner** regex `claude code|esc to interrupt` MATCHES while its **trust** regex does not — so a real trust modal would be classified `banner` and the operator told *"attach to that tab and continue there"* instead of *"answer the trust dialog"*, **the exact failure `deviations.md:18` exists to prevent.** It would have shipped GREEN, because Step 1 as originally written told you to author a fixture containing the invented phrase — code and fixture agreeing with each other and both disagreeing with reality.

  **`trust-dialog.txt` MUST BE DERIVED FROM THE FROZEN CAPTURE, NOT HAND-AUTHORED**: write it from `cmux-verb-shapes.json`'s `trust_dialog_screen.screen` value verbatim. Then add a test asserting the fixture still equals that frozen value, so the two cannot drift. **A fixture authored to match the code under test proves only that you can spell the same string twice.**

  **`banner.txt` IS ALSO DERIVED FROM A LIVE CAPTURE. AMENDED AGAIN 2026-08-02 (partner round 2, BLOCKER A) — the round-1 amendment asserted "Task 0 captured no live screen for them", and THAT CLAIM WAS FALSE.** `cmux-verb-shapes.json` is `captured: "live"` throughout, and `rc_confirmation_screen` holds **TWO live captures of a running Claude session** (`rc_screen`, `rename_screen`) — exactly the `banner` branch's semantic. **This is the controller writing a second false factual claim into the plan while fixing the first one**, the same shape partner round 2 caught on Task 9. Derive `banner.txt` from `rc_confirmation_screen.rc_screen` and pin BOTH live captures to `diagnosis=banner`.

  **Measured, with controls, against those two captures and the trust capture:** `shift+tab to cycle` is present in BOTH live sessions and ABSENT from the trust screen — it is the one usable MEASURED banner anchor. **Scope that measurement honestly (partner round 3, MEDIUM K): both captures carry the SAME session id and the same `bypass permissions` statusline, so n = ONE session captured twice**, and it was a long-running interactive session rather than a freshly-spawned successor — which is the population this feature actually cares about. The anchor IS measured; the generalization to "any running Claude session" is INFERRED and the fixture cannot settle it. Do not launder the one into the other. `esc to interrupt` occurs **zero times in the entire fixture** (both live captures are IDLE sessions; that string only appears while Claude is generating), so it is an INFERENCE covering the busy state. `claude code` matches **only the trust screen** and NEITHER running session — an anchor that fires on the wrong screen; it is REMOVED from the banner pattern.

  The remaining THREE are synthetic *(AMENDED — partner round 4, MEDIUM O: the count was two until MEDIUM L's remedy required a fifth fixture, and this inventory line was the twin that did not get updated)*: `picker-error.txt` (`claude-picker: error: no matching version`), `noise.txt` (shell prompt + scrollback junk), and **`both-anchors.txt`** — a screen carrying BOTH a trust anchor and a banner anchor, which no capture does, needed to pin the `diagnose_target` ordering now that the fixed banner pattern no longer overlaps the trust capture. Their synthetic status must be stated in each file or its loader comment. **For these three, an anchor you invent is a HYPOTHESIS, not a contract** — say so where it lives.

- [ ] **Step 2: Failing tests:**

```python
class TestHandshake:
    def test_token_is_only_success(self, tmp_path):
        # CMUX_WAITFOR_RC=1 + CMUX_SCREEN_FILE=banner.txt -> exit 3, NOT 0:
        # a full banner on screen never selects success (three live incidents)
        # outcome: handshake=timeout diagnosis=banner
    def test_timeout_rewaits_once_same_duration(self, tmp_path):
        # cmux.log contains exactly TWO wait-for lines, both --timeout <same value>
        # AMENDED 2026-08-02 (partner LOW 6; misattribution corrected round 2): do NOT
        # reach for _flag(_argv(tmp_path, "wait-for"), "--timeout") here. _argv returns
        # ALL matching lines; it is _flag that resolves only the FIRST occurrence — so
        # the blame sits on _flag alone. Either way "both" would silently assert one
        # value once and the re-wait half would be VACUOUS. Parse BOTH wait-for
        # lines out of cmux.log and compare them. Positive-control it: make the
        # re-wait use a different duration and confirm this test goes RED.
    def test_diagnosis_trust_dialog_names_dialog_and_steers_to_tab(self, tmp_path):
        # screen=trust-dialog.txt -> stderr names the trust dialog, contains the surface
        # ref, and does NOT contain the fresh-session manual instructions block
    # --- AMENDED 2026-08-02 (partner review) -------------------------------
    def test_trust_dialog_fixture_matches_the_frozen_capture(self):
        # BLOCKER 1: screens/trust-dialog.txt == cmux-verb-shapes.json
        # trust_dialog_screen.screen, verbatim. Stops fixture/contract drift.
    def test_banner_fixture_matches_the_frozen_capture(self):
        # MEDIUM M (partner round 3): banner.txt is ALSO derived from a live capture
        # (rc_confirmation_screen.rc_screen), so it needs the SAME anti-drift pin.
        # Round 1's remedy was written for trust-dialog.txt only and never mirrored
        # when banner.txt joined it — a derived fixture with no equality test can
        # drift from the capture it claims to derive from with every test green.
    def test_real_trust_capture_diagnoses_trust_not_banner(self, tmp_path):
        # BLOCKER 1: the real trust capture must diagnose trust-dialog.
        # AMENDED (partner round 3, MEDIUM L) — THE PRESCRIBED POSITIVE CONTROL NO
        # LONGER FIRES, and the reason is worth understanding rather than patching:
        # removing `claude code` from the banner pattern DISSOLVED the very overlap
        # that made ordering load-bearing. Measured: with the old pattern, reordering
        # banner above trust turned the trust capture into `banner`; with the fixed
        # pattern it stays `trust-dialog` either way. So "reorder and confirm RED"
        # now yields GREEN, and this test pins ordering for NO captured shape.
        # A correct fix can retire the subject of a companion test, leaving a test
        # that still READS as a guard while pinning nothing.
    def test_ordering_trust_beats_banner_on_a_both_anchors_screen(self, tmp_path):
        # MEDIUM L's actual remedy. Ordering remains correct defense-in-depth — a
        # screen CAN carry both anchors (a trust modal raised over a pane that has
        # already painted a statusline) — but no CAPTURED screen does. So pin it
        # with an explicitly SYNTHETIC fixture containing BOTH a trust anchor and a
        # banner anchor, labelled synthetic where it lives. THIS test is the one
        # whose positive control must go RED when the two greps are reordered.
    def test_diagnosis_banner_steers_to_tab_and_omits_manual_block(self, tmp_path):
        # MEDIUM 3: module AC names BOTH trust-dialog AND banner as steering to the
        # existing tab; only trust had a test. Assert the manual-instructions block
        # is ABSENT (the discriminator vs picker-error/none, which print it).
    def test_both_live_session_captures_diagnose_banner(self, tmp_path):
        # BLOCKER A (round 2): rc_confirmation_screen.rc_screen AND .rename_screen
        # are LIVE captures of a running Claude session. Before this amendment the
        # banner regex matched NEITHER -- both fell through to diagnosis=none,
        # breaking the module AC's "banner steers to the existing tab". Drive both
        # verbatim from the fixture. Positive-control by reverting the pattern to
        # `claude code|esc to interrupt` and confirming this test goes RED.
    def test_diagnosis_picker_error(self, tmp_path):        # diagnosis=picker-error
    def test_diagnosis_none_on_noise(self, tmp_path):       # diagnosis=none
    def test_diagnosis_unreadable_on_cold_surface(self, tmp_path):
        # no CMUX_SCREEN_FILE -> stub errors internal_error -> diagnosis=unreadable, no crash
        # AMENDED 2026-08-02 (partner LOW 5, strengthened round 2): `unreadable` has
        # TWO disjuncts — a non-zero read-screen rc, and the literal `internal_error`
        # in the output. THE SEPARATING KNOB ALREADY EXISTS: CMUX_SCREEN_FILE pointing
        # at a file whose CONTENT carries `internal_error` gives rc 0 + the literal,
        # isolating the second disjunct from the first. Round 1 established this with
        # evidence; do not re-open it as an open question. Write BOTH cases. The live
        # capture for this anchor is read_screen_cold (stderr `Error: internal_error:
        # Failed to read terminal text`, exit 1) — MEASURED, not invented.
    def test_timeout_notifies_and_keeps_hop(self, tmp_path):
        # notify line present; .handoff-hops still incremented; message NEVER claims
        # "nothing was spawned" (assert the string is absent)
    def test_token_success_exits_0_handshake_ok(self, tmp_path):
        # CMUX_WAITFOR_RC=0 -> exit 0, outcome handshake=ok
```

**VERIFY — DO NOT RE-ADD — the import assertion** tying the script's wait default to Task 0's measurement (relocated here from Task 9 by OP-1). **AMENDED 2026-08-02 at Task 10's obligation audit: Task 9 PRE-EMPTED it and it is ALREADY LANDED** in `test_spawn_handoff_v2.py` (the `cold-start-timing.json` load plus the anchored `^SPAWN_WAIT_TIMEOUT_DEFAULT=(\d+)$` search, asserting the script's literal equals `default_seconds`), and the script side is a column-0 `SPAWN_WAIT_TIMEOUT_DEFAULT=60`. **Following the original wording literally would ship a DUPLICATE assertion.** Your obligation is to CONFIRM it still exists, still resolves, and still passes — then say so in your report with the line numbers you actually read. If it is absent or broken, THEN add it in the shape below. Tasks 0/8/9 have all edited `test_spawn_handoff_v2.py` by now, so ADD `import re` and the `SCRIPT` constant **only if absent** (verify `parents[N]` actually resolves; a wrong path fails on `read_text()`, not on the assertion). `SPAWN_WAIT_TIMEOUT_DEFAULT=` must stay a **top-level, column-0** assignment in the script — the regex is anchored, so indenting it into a function or `if` block silently breaks the match.

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
  # AMENDED 2026-08-02 (partner BLOCKER 1): anchors come from the FROZEN capture
  # (cmux-verb-shapes.json trust_dialog_screen.candidate_anchors), NOT invented.
  # The trust test precedes the banner test as DEFENSE IN DEPTH. Be precise about
  # why (partner round 4, BLOCKER N -- the earlier wording here asserted the OLD
  # pattern's behaviour and became false the moment `claude code` was removed):
  # the pre-fix banner regex DID match the real trust screen, which is what made
  # ordering load-bearing. The fixed pattern scores ZERO on it (re-derived with a
  # control: the deleted `claude code` still scores 2), so ordering now changes no
  # CAPTURED screen's diagnosis. It is retained because a screen CAN carry both
  # anchors -- a trust modal raised over a pane that already painted a statusline --
  # and that case is pinned by a SYNTHETIC both-anchors fixture, not by any capture.
  if grep -qiE "quick safety check|yes, i trust this folder" <<< "$screen"; then printf 'trust-dialog'; return 0; fi
  if grep -qiE "claude-picker: (error|fatal)|no matching version" <<< "$screen"; then printf 'picker-error'; return 0; fi
  # AMENDED 2026-08-02 (partner round 2, BLOCKER A). `shift+tab to cycle` is
  # MEASURED: present in BOTH live running-session captures
  # (cmux-verb-shapes.json rc_confirmation_screen.rc_screen/.rename_screen) and
  # absent from trust_dialog_screen. `esc to interrupt` is INFERRED, covering the
  # BUSY state -- it occurs zero times in the whole fixture because both live
  # captures are IDLE. `claude code` was REMOVED: measured to match ONLY the trust
  # screen and NEITHER running session, i.e. it fired on the wrong screen.
  if grep -qiE "shift\+tab to cycle|esc to interrupt" <<< "$screen"; then printf 'banner'; return 0; fi
  printf 'none'
}
```

(pattern constants may be hoisted; every grep uses here-strings, never a pipe.)

- [ ] **Step 3b: Record anchor PROVENANCE for all four diagnoses.** *(AMENDED 2026-08-02 — partner review BLOCKER 2: this was prose inside Step 3 that commanded work no checkbox produced, the same producer-less shape that has now BLOCKED a partner round on two consecutive tasks. It is the ONLY place the plan requires anchor provenance at all, and BLOCKER 1 is what happens without it.)* Beside each pattern, state in a code comment whether the anchor is **MEASURED** (quote the `cmux-verb-shapes.json` key it came from) or **INVENTED** (say so plainly, and say what would falsify it). **AMENDED AGAIN 2026-08-02 (partner round 2, MEDIUM B) — the round-1 wording undercounted what Task 0 actually measured.** THREE are MEASURED: `trust-dialog` (`trust_dialog_screen.candidate_anchors`), `banner` (`rc_confirmation_screen`, two live running-session captures — see Step 1), and the `internal_error` disjunct of `unreadable`, whose live capture is `read_screen_cold` (`stderr: "Error: internal_error: Failed to read terminal text"`, exit 1) — that capture is the direct SOURCE of the anchor, not a guess. Only `picker-error` is genuinely un-captured. Label it INVENTED; do NOT mislabel the other three, and do not label as INFERRED anything the fixture measured. **LABEL PER ANCHOR, NOT PER BRANCH, and use THREE categories — MEASURED / INFERRED / INVENTED** *(partner round 3)*. The `banner` branch alone holds two anchors of DIFFERENT provenance: `shift+tab to cycle` is MEASURED, `esc to interrupt` is INFERRED (zero occurrences in the fixture; it covers the busy state that neither idle capture exercises). Labelled per-branch, `banner` reads MEASURED wholesale and the inference silently disappears — which is precisely the blurring this step exists to prevent. **Measured and inferred are not the same evidence, and a comment that blurs them is worse than no comment.**

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
        echo "[spawn-handoff] handshake=timeout: the successor in $SPAWN_SURFACE_REF is sitting on Claude's FOLDER-TRUST PROMPT ('Quick safety check: ... 1. Yes, I trust this folder'). Go to that tab and answer it — do NOT start a fresh session (a successor was spawned; a second one is a double-spawn)." >&2 ;;
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

- [ ] **Step 4: Run + commit + record TWO decisions.** **AMENDED 2026-08-02 at Task 10's obligation audit — the original one-line step carried a stale claim and silently omitted two obligations that were commanded elsewhere.**

  **(a) Run the FULL unit suite — NOT "both unit files".** That phrasing is STALE and contradicts this module's own Acceptance Criteria, whose last bullet reads *"the FULL unit suite green after every task (**not \"both unit files\"**)"*. Task 9's N6 corrected the AC and left this twin uncorrected — the same one-sided-edit shape as N1 (fix one site of a claim, leave its twin). Re-measure the baseline; **do not inherit a count** (the pre-task baseline is 777, itself re-measured, but verify it yourself).

  **(b) Record the TRUST-PREFLIGHT DECISION and flip `deviations.md:18` off `Pending`.** This is commanded by the ROUTING note at the head of this task but was never carried into a step, which is exactly how a decision becomes a silent omission. It is a **DECISION to record, not necessarily a preflight to build**. Task 0 MEASURED the failure live: an interactive `claude-picker` launch into an untrusted `--working-directory` raises the folder-trust modal and sits there, never reaching SessionStart, so the token never signals -> `handshake=timeout` plus a consumed hop that one keystroke would have fixed — **and a fresh worktree is exactly the untrusted-path case this feature targets.** Build it or decline it, with reasoning. **Explicitly forbidden: declining on the unmeasured assumption that `$WORKTREE_ROOT` is already trusted because the parent runs there** — that argument is plausible, untested, and Task 0 measured the opposite case. If you decline, state what would have to be true and what would falsify it.

  **(c) Record a DECISION on the five inline log-readers** (`deviations.md:271`, routed `Pending — TASK 10`). Five inline `(tmp_path / "cmux.log").read_text()` sites survive in `test_spawn_handoff.py` — count VERIFIED at 5 on 2026-08-02. They are a **DIFFERENT SHAPE, not a fourth copy** of the consolidated helper: they read unconditionally and RAISE on a missing file, whereas the helper returns `""`. **Swapping them would change failure semantics**, so this is a judgment call, not a mechanical cleanup. Evaluate and record — fix, or decline with reasoning and flip the row. Do NOT silently leave it.

  **(d) Resolve the ROUTING of `deviations.md:165`** (orphaned fallback workspace). *(AMENDED 2026-08-02 — partner MEDIUM 4.)* Its disposition names Task 10/13 but **no step in EITHER task produces it** — the identical shape as row 18, which is how a decision becomes a silent omission. **You are asked to resolve the ROUTING, not necessarily to build the fix:** read the row, decide whether it belongs to this task, a later one, or merge, and record that with reasoning. A row naming two tasks and owned by neither is owned by nobody.

  **(e) Commit** — never `git add -A`; stage explicit paths enumerated against what you ACTUALLY changed. Message: `"feat(cmux-spawn-v2): wait-for handshake + re-wait + read-screen diagnosis enrichment"`.

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
- [ ] `tests/unit/test_spawn_handoff.py` fully migrated in the same tasks that changed the behavior; the FULL unit suite green after every task (**not "both unit files"** — Task 9 writes three test files, and its Step 3 rewrites the spawn core other suites exercise).
