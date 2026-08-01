---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: "docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md"
integration_test:
  path: tests/integration/sdd-e2e-test.sh
tasks:
  - id: 0
    title: "Contract verification + cold-start handshake measurement (BLOCKING)"
  - id: 1
    title: "SP2: workspace --env / --env-file probe + disposition"
    depends_on: [0]
    review_tier: minimum
  - id: 2
    title: "SP1: context-probe.py [task N fix] attribution root cause"
    depends_on: [0]
  - id: 3
    title: "SP3 + SP4 design docs + BACKLOG rows"
    depends_on: [0, 1, 2]
    review_tier: minimum
---

# cmux-spawn-v2 — Module 1: Contracts, cold-start measurement, spikes

> **Parent plan:** `docs/imp-plans/2026-07-30-cmux-spawn-v2/plan.md`
> **Module:** 1 of 4
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Anchor the sprint to ground truth. Capture the installed cmux binary's per-verb output shapes as fixtures, measure the true-cold-start handshake time and pin the `SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT` shipped default, run the SP1/SP2 probes, and commit the SP3/SP4 design docs. No production code changes in this module except an optional SP1 `context-probe.py` fix.

**Source Contracts:** The installed cmux binary (`cmux 0.64.20 (100) [14e3400b9]` — re-pin with `cmux --version` at execution time), `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md` Contract Facts, capability matrix `docs/process-improvement-findings/2026-07-28-cmux-capability-usage-matrix.md` §4.2.

**Contract Constraints:** Per-verb `OK` shapes (parent plan Shared Contract Section item 1); measurement method is pinned (true cold start: fresh surface, no warm claude process, picker version download excluded; shipped default = measured p95 × 2); screen polling is allowed HERE as a measurement instrument only — it is never the production readiness signal.

## File Map

| File | Responsibility |
|------|----------------|
| `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json` | Verbatim captured stdout/exit codes for every state-changing verb + negative shapes |
| `tests/unit/fixtures/spawn-handoff/cold-start-timing.json` | The 5 measured cold-start durations + the derived shipped default |
| `tests/unit/test_spawn_handoff_v2.py` | New test file; Task 0 seeds only its fixture-contract section |
| `docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md` | SP2 probe transcript + disposition |
| `docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md` | SP1 root cause (always written, even if a code fix also lands) |
| `skills/subagent-driven-development/scripts/context-probe.py` + `tests/unit/test_context_probe*.py` | SP1 fix, ONLY if root cause is a probe bug |
| `docs/process-improvement-findings/2026-07-30-sp3-non-sdd-context-guard-design.md` | SP3 design doc |
| `docs/process-improvement-findings/2026-07-30-sp4-carry-forward-fix-lane-design.md` | SP4 design doc |
| `docs/process-improvement-findings/BACKLOG.md` | New rows: SP2 disposition, SP3, SP4 (and SP1 if exclusion-rule outcome) |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 0 | `tests/unit/fixtures/spawn-handoff/{cmux-verb-shapes,cold-start-timing}.json`, `tests/unit/test_spawn_handoff_v2.py` | installed cmux, spec | — |
| Task 1 | `docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md`, `BACKLOG.md` | installed cmux | Task 0 |
| Task 2 | `docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md`, `context-probe.py`, `tests/unit/test_context_probe*.py` | archived transcripts, observation logs | Task 0 |
| Task 3 | `docs/process-improvement-findings/2026-07-30-sp3-*.md`, `2026-07-30-sp4-*.md`, `BACKLOG.md` | — | Task 0 |

`BACKLOG.md` has **three** potential writers in this module, not two: Task 1 (SP2 disposition row),
Task 2 (conditionally — an SP1 row only if the outcome is an exclusion rule), and Task 3 (SP3 + SP4
rows). Strict execution order is **0 → 1 → 2 → 3**, and this is now encoded in `depends_on`
(Task 3 declares `[0, 1, 2]`) rather than living only in this prose — frontmatter is what the tooling
reads. Each writer APPENDS; none rewrites the file. Task 3 picks the next free N-ids after whatever
Tasks 1 and 2 actually added, so it must read `BACKLOG.md` at execution time rather than assuming
ids reserved at plan time.

### Task 0: Contract verification + cold-start handshake measurement (BLOCKING)

**Files:**
- Create: `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json`
- Create: `tests/unit/fixtures/spawn-handoff/cold-start-timing.json`
- Create: `tests/unit/test_spawn_handoff_v2.py` (fixture-contract section only)

No other task may start until this one completes. All work happens inside a **throwaway cmux workspace** so the user's sidebar is disturbed only by clearly-named `task0-*` entries that this task deletes on exit. — **COMPLETE:** quality review round 1 CHANGES_REQUESTED → `[task 0 fix]` round (live re-capture, same binary) → round 2 **APPROVED** (71 mutations, 0 survivors, 4 negative controls held). Finding 4's consumer half landed as a Module 3 Task 9 plan amendment (`949d310`); see `deviations.md`.

- [x] **Step 1: Verify environment or take the blocked path**

```bash
cmux --version           # expect: cmux 0.64.20 (100) [14e3400b9] — record verbatim if different
[ -n "$CMUX_WORKSPACE_ID" ] && [ "$(cmux ping 2>/dev/null)" = "PONG" ] && echo REACHABLE
```

**The controller verified live reachability at ingestion** (version exactly `cmux 0.64.20 (100) [14e3400b9]`, `cmux ping` → `PONG`, `CMUX_WORKSPACE_ID` exported and inherited by nested subshells), **so the blocked path below is NOT licensed for this run.** If your check fails, something changed mid-flight: report **NEEDS_CONTEXT** and stop — `default_seconds` feeds an import assertion (Task 9 Step 4), so a provisional value silently ships a wrong production timeout. If a *different* cmux version is installed, capture against it and record the version in both fixtures; the installed binary outranks the spec's pin.

Blocked path (only on explicit controller instruction): do not fabricate fixtures. Write `cold-start-timing.json` with `"measured": false, "default_seconds": 120`; copy capability-matrix §4.2 shapes into `cmux-verb-shapes.json` with `"captured": "matrix-fallback"` and every Step-2b/2c/4b key `"unavailable"`; log a `deviations.md` row (post-merge live smoke must re-measure); then skip to **Step 7**. (Not Step 5 — Step 5 *rewrites* `cold-start-timing.json` with the `measured: true` shape and a `runs_seconds` array the blocked path never produced.)

- [x] **Step 2: Capture per-verb shapes into a scratch log**

```bash
WS_OUT=$(CMUX_QUIET=1 cmux workspace create --name "task0-shapes" --cwd "$HOME" --focus false)
echo "workspace_create: $WS_OUT"          # expect: OK workspace:<N>
WS_REF=$(echo "$WS_OUT" | awk '{print $2}')
SURF_LIST=$(cmux list-pane-surfaces --workspace "$WS_REF")
echo "list_pane_surfaces: $SURF_LIST"     # capture verbatim; note which line carries [selected]
NS_OUT=$(cmux new-surface --workspace "$WS_REF" --type terminal --working-directory "$HOME" --focus false)
echo "new_surface: $NS_OUT"               # expect: OK surface:<N> pane:<M> workspace:<K>
SURF_REF=$(echo "$NS_OUT" | awk '{print $2}')
RT_OUT=$(cmux rename-tab --surface "$SURF_REF" "task0 title probe"); echo "rename_tab: $RT_OUT"
# expect field 2 = action=rename, NOT a ref — this is the wrong-ref trap fixture
COLD_RS=$(cmux read-screen --surface "$SURF_REF" --scrollback 2>&1); RS_RC=$?
echo "read_screen_cold rc=$RS_RC: $COLD_RS"   # expect internal_error on a never-driven surface
SEND_OUT=$(cmux send --surface "$SURF_REF" "echo task0-alive\n"); echo "send: $SEND_OUT"
SK_OUT=$(cmux send-key --surface "$SURF_REF" enter); echo "send_key: $SK_OUT"
sleep 2; WARM_RS=$(cmux read-screen --surface "$SURF_REF" --scrollback 2>&1); RS2_RC=$?
echo "read_screen_warm rc=$RS2_RC (should contain task0-alive)"
( sleep 1; cmux wait-for -S task0-token ) & WF_OUT=$(cmux wait-for task0-token --timeout 10); WF_RC=$?
echo "wait_for rc=$WF_RC out=$WF_OUT"     # round-trip proof: signal received within timeout
CS_OUT=$(cmux close-surface --surface "$SURF_REF" 2>&1); echo "close_surface: $CS_OUT"
# capture verbatim — the spec pins that this returns a plausible WRONG ref; it is a negative fixture
```

- [x] **Step 2b: Probe for a durable surface UUID (audit order A1)** — **run BEFORE the `close-surface` line above**; it needs a live surface. Short refs (`surface:73`) renumber across cmux app restarts, so the outcome record needs permanent identity. Nothing in the plan establishes such a UUID is obtainable; the parent writes the log, so the question is whether the PARENT can learn the CHILD's UUID from a verb. (A surface does export its own `CMUX_SURFACE_ID`, UUID-shaped.)

```bash
cmux identify --json 2>&1; cmux identify --json --id-format both 2>&1
cmux list-pane-surfaces --workspace "$WS_REF" --id-format both 2>&1
cmux new-surface --help 2>&1 | grep -i "id-format\|uuid"
```

Record `surface_uuid_source` as `{"available": true, "verb": …, "key_path": …, "example": …}` or `{"available": false, "transcript": …}`. **Unavailable is a legitimate documented outcome, not a failure** — say so plainly and the controller converts operator addendum #1 into a recorded refusal. Do NOT invent a substitute identity scheme.

- [x] **Step 2c: Probe `wait-for` latching (audit order A2 — possible ESCALATION)** — Step 2 proves only wait-then-signal. Task 10 calls `wait_for_token` **twice** (bounded re-wait). If a token signaled between the first wait's return and the second wait's start is LOST, a healthy successor yields `handshake=timeout` + a consumed hop — a false negative on "token is the ONLY exit-0 path".

```bash
cmux wait-for -S task0-latch; sleep 3
cmux wait-for task0-latch --timeout 10; echo "latch_rc=$?"      # 0 => latching
( sleep 2; cmux wait-for -S task0-gap ) &                        # models the re-wait gap
cmux wait-for task0-gap --timeout 1; echo "first_rc=$?"          # expect timeout
cmux wait-for task0-gap --timeout 10; echo "second_rc=$?"        # 0 => survived the gap
```

Record `wait_for_latching: {"latching": true|false, "transcript": …}`. **If false: STOP and report to the controller** — Task 10's two-call re-wait is unsound as designed and needs a plan amendment (single longer wait, or a continuously-held waiter). Do not redesign it or work around it.

- [x] **Step 3: Write `cmux-verb-shapes.json`** — one key per verb: `{"verb", "argv", "stdout", "exit"}` from the captures above, plus `"cmux_version"` and `"captured": "live"`. Every value verbatim — no hand-editing.

Beyond the per-verb keys, this fixture also carries the three audit-ordered probe results:
`surface_uuid_source` (Step 2b), `wait_for_latching` (Step 2c), and `rc_confirmation_screen`
(Step 4b, written after the timing runs). Write the first two now; add the third in Step 4b.

- [x] **Step 4: Measure true cold start (5 runs)**

Pinned method. Each run: fresh workspace + fresh surface (no warm claude process anywhere in the run), picker version already on disk (excluded from timing), poll `read-screen` every 2s as the measurement instrument.

```bash
# Measurement shell only — the production no-pipe/no-poll rules bind the spawn
# script, not this probe; read-screen polling here is the instrument, never the
# shipped readiness signal.
VER="${CLAUDE_CODE_PICKER_VERSION:-$(ls -t "$HOME/.local/share/claude/versions" | head -1)}"
if [ ! -f "$HOME/.local/share/claude/versions/$VER" ]; then
  echo "ABORT: version not on disk — downloading would pollute the measurement"; exit 1
fi
for i in 1 2 3 4 5; do
  W=$(CMUX_QUIET=1 cmux workspace create --name "task0-cold-$i" --cwd "$HOME" --focus false | awk '{print $2}')
  S=$(cmux new-surface --workspace "$W" --type terminal --working-directory "$HOME" --focus false | awk '{print $2}')
  T0=$(date +%s)
  cmux send --surface "$S" "claude-picker --non-interactive --pick-version $VER -p 'Reply with exactly READY'\n"
  ELAPSED=timeout
  for t in $(seq 2 2 300); do
    sleep 2
    if cmux read-screen --surface "$S" --scrollback 2>/dev/null | grep -q "READY"; then
      ELAPSED=$(( $(date +%s) - T0 )); break
    fi
  done
  echo "run $i: ${ELAPSED}s"
done
```

Note: `-p` completes a full headless turn, so each sample slightly OVERestimates boot→SessionStart — the safe direction for a timeout. If a run reports `timeout`, investigate before proceeding (a dead picker invalidates the sample set).

- [x] **Step 4b: Capture the real `/rc` confirmation string (audit order A3a)**

**Ordering is load-bearing: run ONLY after all five Step-4 timing runs finish, in its OWN workspace (`task0-rc`).** Step 4 requires "no warm claude process anywhere in the run"; booting Claude here first, or in a shared workspace, contaminates the measurement.

Why: Task 11 verifies `/rename` by searching the screen for the very title text it just sent, so the **shell echo satisfies the check whether or not `/rename` ran** — the exact defeat `spec-distilled.md` already records ("shell echo defeating composer verify"). We need the real confirmation text so Task 11 can anchor on a string its own sent line cannot contain.

```bash
W=$(CMUX_QUIET=1 cmux workspace create --name "task0-rc" --cwd "$HOME" --focus false | awk '{print $2}')
S=$(cmux new-surface --workspace "$W" --type terminal --working-directory "$HOME" --focus false | awk '{print $2}')
cmux send --surface "$S" "claude-picker --non-interactive --pick-version $VER\n"
for t in $(seq 2 2 180); do sleep 2; cmux read-screen --surface "$S" --scrollback >/dev/null 2>&1 && break; done
sleep 10
cmux send --surface "$S" "/rc"; cmux send-key --surface "$S" enter; sleep 5
cmux read-screen --surface "$S" --scrollback 2>&1                     # CAPTURE VERBATIM
cmux send --surface "$S" "/rename task0-rename-probe"; cmux send-key --surface "$S" enter; sleep 5
cmux read-screen --surface "$S" --scrollback 2>&1                     # CAPTURE VERBATIM
```

`/rename` is probed AFTER `/rc` **deliberately**: operator addendum #3 reports (N=1, unproven) that `send` stops landing once `/remote-control` is active, so a second send that does not land cheaply reproduces the hazard. Record either result — a negative is data.

Record `rc_confirmation_screen: {"rc_screen": …, "rename_screen": …, "send_after_rc_landed": true|false}`. In your report, name the exact substring that proves `/rc` is active **and cannot appear in the sent line itself** — that becomes Task 11's anchor.

- [x] **Step 5: Derive and record the default**

p95 of 5 samples = max sample. `default = max(60, 2 × max_sample)` rounded UP to the nearest 10 seconds. Write `cold-start-timing.json`:

```json
{"measured": true, "cmux_version": "<verbatim>", "picker_version": "<VER>",
 "method": "read-screen poll 2s for headless READY; fresh workspace+surface per run",
 "runs_seconds": [<r1>, <r2>, <r3>, <r4>, <r5>],
 "p95_seconds": <max>, "default_seconds": <derived>}
```

- [x] **Step 6: Clean up** — delete every `task0-*` workspace (probe the canonical close verb first: `cmux workspace --help` lists subcommands; legacy `close-workspace` also works). This now includes `task0-shapes`, the five `task0-cold-*`, and `task0-rc`. Verify with `cmux list-workspaces` that no `task0-*` entries remain. These are the user's real sidebar entries — a leaked workspace is a visible defect, not a cosmetic one.

- [x] **Step 7: Write the fixture-contract test section**

```python
# tests/unit/test_spawn_handoff_v2.py
"""Unit matrix for the cmux-spawn-v2 rework. Task 0 seeds the fixture contracts;
Modules 3-4 append behavior tests."""
import json
from pathlib import Path

FIX = Path(__file__).parent / "fixtures" / "spawn-handoff"


def test_verb_shapes_fixture_contract():
    d = json.loads((FIX / "cmux-verb-shapes.json").read_text())
    ns = d["new_surface"]["stdout"].split()
    assert ns[0] == "OK" and ns[1].startswith("surface:")
    ws = d["workspace_create"]["stdout"].split()
    assert ws[0] == "OK" and ws[1].startswith("workspace:")
    rt = d["rename_tab"]["stdout"].split()
    assert rt[1] == "action=rename", "rename-tab field 2 must never be treated as a ref"
    assert "internal_error" in d["read_screen_cold"]["stdout"] or d["read_screen_cold"]["exit"] != 0


def test_cold_start_default_derivation():
    d = json.loads((FIX / "cold-start-timing.json").read_text())
    assert isinstance(d["default_seconds"], int) and d["default_seconds"] >= 60
    if d["measured"]:
        assert d["default_seconds"] >= 2 * max(d["runs_seconds"])


def test_audit_ordered_probe_keys_present():
    """A1/A2/A3a probes must be recorded — including negative results.

    These three keys are the only record of facts that can be established
    solely inside Task 0's live-cmux window. An absent key is indistinguishable
    from an unrun probe, so presence is asserted even when the answer is "no".
    """
    d = json.loads((FIX / "cmux-verb-shapes.json").read_text())

    assert "surface_uuid_source" in d
    assert isinstance(d["surface_uuid_source"].get("available"), bool)

    assert "wait_for_latching" in d
    assert isinstance(d["wait_for_latching"].get("latching"), bool)

    assert "rc_confirmation_screen" in d
    rc = d["rc_confirmation_screen"]
    assert rc.get("rc_screen"), "the /rc confirmation text is Task 11's verification anchor"
```

- [x] **Step 8: Run and commit**

Run: `.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff_v2.py -v` — expect 3 PASS.

```bash
git add tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json \
        tests/unit/fixtures/spawn-handoff/cold-start-timing.json \
        tests/unit/test_spawn_handoff_v2.py
git commit -m "test(cmux-spawn-v2): Task 0 — live verb-shape fixtures + cold-start timeout measurement"
```

### Task 1: SP2 — workspace --env / --env-file probe + disposition

**Files:**
- Create: `docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md`
- Modify: `docs/process-improvement-findings/BACKLOG.md` (one disposition row)

- [x] **Step 1: Probe the help surfaces** — capture verbatim: `cmux workspace create --help` (does it list `--env`/`--env-file`? precedence notes? `export ` stripping? `--mask`?) and `cmux new-surface --help` (any surface-scoped env equivalent? Per the 2026-07-30 planning check there is none in the flag list — confirm and record).

- [x] **Step 2: Exercise `--env` live** (throwaway workspace, deleted after):

```bash
W=$(CMUX_QUIET=1 cmux workspace create --name "sp2-env" --cwd "$HOME" --focus false \
     --env SP2_PROBE=alpha --env-file /dev/null 2>&1)
# If create rejects the flags, capture the error verbatim — that IS the probe result.
# Otherwise: send `echo $SP2_PROBE` to its surface, read-screen, verify `alpha` appears.
cmux workspace env "$(echo "$W" | awk '{print $2}')"   # capture the configured-env view
```

- [x] **Step 3: Write the disposition doc** — transcript + answer to: can `--env` replace the inline-env command-string prefix on the FALLBACK path (scalars only; the append-prompt is content and stays on the rematerialization path)? Disposition options: (a) viable → BACKLOG row proposing the swap (this sprint still ships command-string per Decision 2's shared wrapper); (b) not viable → record why, close N67's premise accordingly.

- [x] **Step 4: Append the BACKLOG row** (cite the doc), delete the `sp2-env` workspace, run `bash tests/ARaymond-installation/verify-symlink-install.sh` (docs-only change — expect PASS), commit:

```bash
git add docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md docs/process-improvement-findings/BACKLOG.md
git commit -m "docs(cmux-spawn-v2): SP2 — workspace --env probe transcript + disposition"
```

### Task 2: SP1 — context-probe.py [task N fix] attribution root cause

**Files:**
- Create: `docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md`
- Modify (ONLY if root cause is a probe bug): `skills/subagent-driven-development/scripts/context-probe.py`, `tests/unit/test_context_probe.py` (or a new sibling test file)

Gate note: this spike blocks threshold tuning only, NOT the sprint. If the root cause cannot be reproduced from retained artifacts, the deliverable degrades to a documented exclusion rule — never to silence.

- [x] **Step 1: Locate the poisoned row and its transcript**

```bash
grep -rn "tokens=373139" ~/projects/claude-custom/*/docs/imp-plans/*/reports/context-observations.log ~/projects/claude-custom/*/.worktrees/*/docs/imp-plans/*/reports/context-observations.log
# CORRECTED: the row is in ANOTHER REPO — claude-codex-handoff/.worktrees/cmux-transport, feature 2026-07-29-cmux-transport. Neighbors 171666/210693. READ-ONLY across repos.
```

Identify the session transcript that dispatch ran against — retained under `~/.claude/projects/-Users-araymond-projects-claude-custom-claude-codex-handoff--worktrees-cmux-transport/` (12 `.jsonl`, Jul 29–31; do NOT filter by mtime). The ORIGINAL pointer here named the cmux-integration feature dir — wrong feature AND wrong repo; superseded.

- [x] **Step 2: Reproduce the probe's answer against the retained transcript** — run `context-probe.py --transcript <file>` and bisect: which assistant `usage` block yields 373139? Compare `input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens` across the final assistant entries. Candidate hypotheses to test explicitly: (a) a sidechain/subagent entry's usage was the "most recent assistant block" at dispatch time; (b) a retry/error turn carried inflated `cache_creation`; (c) the row is genuine (a real transient spike) and the probe is correct.

- [x] **Step 3: Fix or document.** If (a)/(b): patch `context-probe.py` (e.g. skip entries marked as sidechain when scanning from the end), keep the stdlib-only constraint, and add a regression test with a minimal transcript fixture reproducing the misattribution (differential: buggy value vs corrected value). Run the FULL probe test set: `.venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py -v` — all PASS. If (c): no code change; the doc pins the exclusion rule for tuning consumers (e.g. "exclude rows where tokens jumps >50% against both neighbors").

- [x] **Step 4: Write the doc + commit** — root cause, evidence (the exact usage block), what changed (code or rule). If code changed, note that `context-probe.py` is NOT a baselined hook (no `check-hooks.sh --capture` needed — the baseline pins hook scripts; verify by grepping `tests/ARaymond-hook-baseline/baseline.txt` for `context-probe` and record the result in the doc).

```bash
git add docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md  # + code/tests if any
git commit -m "docs(cmux-spawn-v2): SP1 — probe-row attribution root cause"
```

### Task 3: SP3 + SP4 design docs + BACKLOG rows

**Files:**
- Create: `docs/process-improvement-findings/2026-07-30-sp3-non-sdd-context-guard-design.md`
- Create: `docs/process-improvement-findings/2026-07-30-sp4-carry-forward-fix-lane-design.md`
- Modify: `docs/process-improvement-findings/BACKLOG.md` (two rows)

NO implementation in either — design docs only.

- [ ] **Step 1: SP3 doc** — where a context guard for non-SDD sessions should live. Must cover: the evidence ($127 / 569k-token unguarded planning session, spec §6), why the SDD gate cannot simply extend (it is manifest-gated and fires on the implementer dispatch path only), candidate homes (a UserPromptSubmit/PreToolUse hook independent of SDD artifacts; a stop-hook advisory; a `claude-usage-pace`-based session monitor), the probe reuse story (`context-probe.py` is already transcript-driven and SDD-agnostic), and a recommendation with rollout risk. End with the BACKLOG row text.

- [ ] **Step 2: SP4 doc** — a sanctioned carry-forward fix lane across module transitions. Must cover: today's rule (fixes belong to the module that owns the file; `transition-module.py` archives reports and truncates the dispatch log at the boundary), the observed friction (a defect found in module N+1 whose fix belongs to module N's files has no clean dispatch lane), candidate designs (a `type=fix` cross-module dispatch class the hook already logs; a deviations-ledger lane; re-opening the archived module), enforcement interactions (Checks 4c/5c/9 and the N26 fix-attribution rows), and a recommendation. End with the BACKLOG row text.

- [ ] **Step 3: Append both BACKLOG rows** (next free N-ids; cite both docs), then commit:

```bash
git add docs/process-improvement-findings/2026-07-30-sp3-non-sdd-context-guard-design.md \
        docs/process-improvement-findings/2026-07-30-sp4-carry-forward-fix-lane-design.md \
        docs/process-improvement-findings/BACKLOG.md
git commit -m "docs(cmux-spawn-v2): SP3 + SP4 design docs + BACKLOG rows"
```

## Module 1 Acceptance Criteria

- [ ] `cmux-verb-shapes.json` + `cold-start-timing.json` exist with `captured: live` / `measured: true` (or the documented blocked-path values + a deviation row).
- [ ] `test_spawn_handoff_v2.py` fixture-contract section passes (3 tests).
- [ ] The three audit-ordered probes are recorded, negative answers included: `surface_uuid_source` (A1), `wait_for_latching` (A2), `rc_confirmation_screen` (A3a).
- [ ] Any escalation trigger fired to the controller rather than worked around: `wait_for_latching.latching == false` (Task 10's re-wait is unsound as designed), `surface_uuid_source.available == false` (operator addendum #1 becomes a recorded refusal), or a captured verb shape contradicting a pinned Contract Constraint.
- [ ] The derived `default_seconds` is pinned and ≥ 2 × the worst measured run.
- [ ] SP1 doc committed (with probe fix + green probe/gate test set, or a pinned exclusion rule).
- [ ] SP2 disposition + SP3/SP4 design docs committed with BACKLOG rows.
- [ ] No `task0-*` or `sp2-*` workspaces remain in `cmux list-workspaces`.
