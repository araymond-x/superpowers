# Module 3 — Discoverability sweep + kill switch

**Goal:** Make cmux auto-spawn discoverable proactively (in the auto-loaded SDD skill body and both context-gate hook messages, not only by reading the runtime protocol doc when blocked), add the clean plan-less `SUPERPOWERS_CMUX_AUTOSPAWN` kill switch as a script precondition, document it in both env registries, and record a skill-awareness audit.

**Source Contracts:** None

(See the parent plan; `spec-distilled.md` §C3, §C4; the hook messages and script preconditions are read-only contracts verified during orientation.)

**Contract Constraints:**
- Hook message rewrites must name `spawn-handoff-session.sh <bundle>` as the **default** block-response and manual `/pickup` as the alternative. The HARD block stays a stop-and-hand-off (NOT fix-and-retry).
- `SUPERPOWERS_CMUX_AUTOSPAWN=0`/`false` → exit 3, `reason=autospawn-disabled`, **before** the cmux-reachability check (Precondition 3, line ~219). Invalid values warn and leave auto-spawn enabled (fail-safe/default). Does **not** call `cmux notify` (nothing reserved; parallels the 2b consent refusals).
- `sdd-pre-dispatch-hook.sh` is **baselined** — Task 7 re-captures `baseline.txt` in the same commit.
- `spawn-handoff-session.sh` is **not** baselined.
- Word ceiling: `subagent-driven-development/SKILL.md` is 4993/5000 — Task 6 must extract before adding; verify an explicit `wc -w` number under 5000.
- Consent value set stays `auto`/`ask`/`off`.

**Pattern References:**
- `spawn-handoff-session.sh` Layer-0 knobs (QUOTA_MIN_PCT lines ~29-33) — the validate-warn-revert idiom (Task 8).
- `tests/unit/spawn_handoff_helpers.py`, `tests/unit/test_spawn_handoff.py` — the pytest bash-stub harness (Task 8).

## File Map

| File | Responsibility |
|------|----------------|
| `skills/subagent-driven-development/SKILL.md` (Context Health Protocol) | Name cmux auto-spawn as default block-response (Task 6) |
| `skills/subagent-driven-development/references/context-health-protocol.md` | Receive the extracted Context-Budget detail (Task 6) |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (SOFT/HARD messages) | Name spawn-handoff-session.sh as default (Task 7, baselined) |
| `tests/ARaymond-hook-baseline/baseline.txt` | Re-captured after Task 7 (and again after Task 11 in Module 4) |
| `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (Precondition 0) | `SUPERPOWERS_CMUX_AUTOSPAWN` kill switch (Task 8) |
| `skills/subagent-driven-development/references/context-handoff-protocol.md` (Env knobs), `CLAUDE.md` (env registry) | Document the kill switch (Task 9) |
| `docs/process-improvement-findings/2026-08-04-cmux-autospawn-skill-awareness-audit.md` (new) | Durable skill-awareness audit result (Task 10) |
| Tests: `test_context_gate_*.py`, `test_spawn_handoff*.py` | Message + precondition coverage (Tasks 7, 8) |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| Task 6 | `skills/subagent-driven-development/SKILL.md`, `skills/subagent-driven-development/references/context-health-protocol.md` | — | Task 5 |
| Task 7 | `sdd-pre-dispatch-hook.sh`, `tests/ARaymond-hook-baseline/baseline.txt`, `tests/unit/test_context_gate_*.py` | context-handoff-protocol.md | Task 6 |
| Task 8 | `spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff*.py` | Layer-0 knobs, bash-stub harness | Task 7 |
| Task 9 | `skills/subagent-driven-development/references/context-handoff-protocol.md`, `CLAUDE.md` | spawn-handoff-session.sh | Task 8 |
| Task 10 | `docs/process-improvement-findings/2026-08-04-cmux-autospawn-skill-awareness-audit.md` | all skill bodies | Task 9 |

> **Serialization note:** `tests/ARaymond-hook-baseline/baseline.txt` is owned by Task 7 here AND by Task 11 in Module 4. Sequential module order (M3 before M4) guarantees no parallel write. Never run Task 7 and Task 11 concurrently.

---

### Task 6: SDD SKILL.md Context Health Protocol — name cmux auto-spawn as default block-response (ceiling-safe)

**Files:**
- Modify: `skills/subagent-driven-development/SKILL.md` (extract Context Budget detail, rewrite Context Health Protocol)
- Modify: `skills/subagent-driven-development/references/context-health-protocol.md` (receive extracted detail)

- [x] **Step 1: Measure the baseline**

Run: `wc -w skills/subagent-driven-development/SKILL.md` (expect 4993).

- [x] **Step 2: Extract the Context Budget Management detail FIRST (ceiling offset)**

Move the verdict bullets + subagent-budget detail from `## Context Budget Management` (SKILL.md ~lines 259-270) into `references/context-health-protocol.md` (append a `## Context Budget (task-token estimation)` subsection with that content). In SKILL.md, replace with a short pointer:

```markdown
## Context Budget Management

The pre-dispatch hook runs `estimate-task-tokens.py` automatically for every implementer dispatch and acts on the verdict (`OK` proceeds, `WARNING`/≥25% injects a focus note, `TOO_LARGE`/≥50% BLOCKS — split the task). This is deterministic and hook-enforced; there is no manual step and no override. See `references/context-health-protocol.md` for the verdict thresholds and subagent budget allocations.
```

- [x] **Step 3: Rewrite the Context Health Protocol section**

Replace the `## Context Health Protocol` block (SKILL.md ~lines 276-280) with:

```markdown
## Context Health Protocol

See `references/context-health-protocol.md` for managing controller context accumulation, signs of context pressure, and when to generate context summaries.

When the pre-dispatch hook BLOCKS a dispatch for context pressure (hard threshold), the block is not a fix-and-retry — it is a clean handoff boundary. The **default block-response is the cmux auto-spawn**: commit pending state, build a fresh-session handoff bundle (invoke the handoff skill, entry skill `superpowers:subagent-driven-development`), then run `spawn-handoff-session.sh <bundle>` to launch the successor session automatically. It **degrades to a manual `/pickup` handoff** when cmux is unreachable or when the plan's `handoff_spawn` / `SUPERPOWERS_CMUX_AUTOSPAWN` opts out. Either way: commit, hand off, and STOP — do not retry. Full runtime protocol: `references/context-handoff-protocol.md`.
```

- [x] **Step 4: Verify the word ceiling (explicit number) + regression**

Run: `wc -w skills/subagent-driven-development/SKILL.md`
Expected: **under 5000** (the Context Budget extraction frees ~140 words; the rewrite adds ~55; expect ~4900).

Run: `.venv/bin/python3 tests/ARaymond-skill-regression/validate-all-skills.py 2>&1 | tail -8`
Expected: no new FAIL; SDD SKILL.md not over the hard word limit; the `references/context-health-protocol.md` cross-reference resolves.

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/SKILL.md skills/subagent-driven-development/references/context-health-protocol.md
git commit -m "docs(discoverability): SDD SKILL.md names cmux auto-spawn as default block-response (extract context-budget detail)"
```

---

### Task 7: sdd-pre-dispatch-hook.sh — name spawn-handoff-session.sh in SOFT nudge + HARD block (baselined, recapture)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (HARD block ~line 842, SOFT nudge ~line 846)
- Modify: `tests/ARaymond-hook-baseline/baseline.txt` (recapture — same commit)
- Test: `tests/unit/test_context_gate_*.py` (update the message-content assertions)

**Pattern References:** `regen-check-hooks-baseline`.

- [x] **Step 1: Update the HARD block message**

Replace the HARD-block `echo` (currently: "…build a fresh-session handoff (invoke the handoff skill…), tell the user to start a fresh session from the worktree and run /pickup, then STOP. See …context-handoff-protocol.md.") with wording that names the auto-spawn as the default and manual as the fallback, still stop-and-hand-off:

```bash
        echo "BLOCKED (context): controller context is ~$CTX_T tokens (>= HARD $CTX_HARD). Do NOT retry this dispatch — retrying is wrong. This is a clean handoff boundary: commit pending state, then hand off. DEFAULT (cmux auto-spawn): build the fresh-session handoff bundle (invoke the handoff skill, entry skill superpowers:subagent-driven-development), then run spawn-handoff-session.sh <bundle> to launch the successor automatically. FALLBACK (cmux unreachable, or handoff_spawn/SUPERPOWERS_CMUX_AUTOSPAWN opted out): tell the user to start a fresh session from the worktree and run /pickup. Either way STOP after handing off. See skills/subagent-driven-development/references/context-handoff-protocol.md." >&2
```

- [x] **Step 2: Update the SOFT nudge message**

Replace the SOFT `CTX_NUDGE=` assignment with:

```bash
        CTX_NUDGE="CONTEXT NUDGE: controller context is ~$CTX_T tokens — this is a clean task boundary. Consider handing off to a fresh session now rather than starting task ${TASK_NUMBER}: the default is the cmux auto-spawn (build a handoff bundle, then spawn-handoff-session.sh <bundle>); manual /pickup is the fallback. See references/context-handoff-protocol.md."
```

- [x] **Step 3: Update the message-content tests**

Find the context-gate tests that assert the message strings:

Run: `/usr/bin/grep -rln "CONTEXT NUDGE\|BLOCKED (context)\|context-handoff-protocol" tests/unit/`
The true positive is `tests/unit/test_context_gate_tier.py` (its existing assertions — `CONTEXT NUDGE`, `do not retry`/`Do NOT retry`, `context-handoff-protocol` — remain valid substrings after the rewrite, so they stay green). **Add** an assertion there that both the HARD block and the SOFT nudge now contain `spawn-handoff-session.sh` (the new default-response naming). Keep all existing assertions intact. If `test_spawn_handoff.py` appears in the grep, it is a **false positive** (unrelated `/pickup <bundle>` CLI-arg tests) — do NOT edit it.

- [x] **Step 4: Run the context-gate tests**

Run: `.venv/bin/python3 -m pytest tests/unit/ -k "context_gate or context_probe" -q`
Expected: all PASS.

- [x] **Step 5: Re-capture the hook baseline (SAME commit)**

Run: `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture`
Run: `bash tests/ARaymond-hook-baseline/check-hooks.sh` (verify — expect in-sync).

- [x] **Step 6: Commit (hook + baseline together)**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/ARaymond-hook-baseline/baseline.txt tests/unit/
git commit -m "docs(discoverability): context-gate hook names spawn-handoff-session.sh as default response (baseline recaptured)"
```

---

### Task 8: spawn-handoff-session.sh — SUPERPOWERS_CMUX_AUTOSPAWN precondition 0 (reason=autospawn-disabled)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (new Precondition 0, before Precondition 1 at ~line 150)
- Test: `tests/unit/test_spawn_handoff.py` (or `test_spawn_handoff_v2.py` — extend the existing harness)

**Pattern References:** `env-knob-validate-warn-revert`, `pytest-bash-stub-harness`.

- [ ] **Step 1: Write the failing tests (extend the bash-stub harness)**

Using the existing `run_spawn()` driver / PATH stubs (see `tests/unit/spawn_handoff_helpers.py`), add tests asserting the below. NOTE the real `run_spawn` signature uses **`env_extra=`** (NOT `env=`) to inject env vars — match the existing call sites in `test_spawn_handoff.py`:

```python
def test_autospawn_disabled_zero_refuses_before_cmux(...):
    # SUPERPOWERS_CMUX_AUTOSPAWN=0 -> exit 3, reason=autospawn-disabled,
    # and it fires BEFORE the cmux-reachability probe (so a reachable-cmux stub
    # is irrelevant; the refusal is autospawn-disabled, NOT cmux-unreachable).
    res = run_spawn(..., env_extra={"SUPERPOWERS_CMUX_AUTOSPAWN": "0"})
    assert res.returncode == 3
    assert "reason=autospawn-disabled" in res.stderr
    assert "not in a reachable cmux" not in res.stderr  # did not reach Precondition 3

def test_autospawn_disabled_false_refuses(...):
    res = run_spawn(..., env_extra={"SUPERPOWERS_CMUX_AUTOSPAWN": "false"})
    assert res.returncode == 3 and "reason=autospawn-disabled" in res.stderr

def test_autospawn_invalid_warns_and_proceeds(...):
    # Invalid value -> WARNING, auto-spawn stays enabled (reaches later preconditions)
    res = run_spawn(..., env_extra={"SUPERPOWERS_CMUX_AUTOSPAWN": "banana"})
    assert "invalid SUPERPOWERS_CMUX_AUTOSPAWN" in res.stderr
    assert "reason=autospawn-disabled" not in res.stderr

def test_autospawn_unset_proceeds(...):
    res = run_spawn(...)  # no AUTOSPAWN in env_extra
    assert "reason=autospawn-disabled" not in res.stderr
```

Match the harness's fixture setup (clean tree, valid bundle, manifest with `spawn_policy=auto`) so the disabled tests exercise a case that would otherwise proceed. Confirm the exact `run_spawn` keyword by reading `tests/unit/spawn_handoff_helpers.py` first.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/ -k autospawn -v`
Expected: the new tests FAIL (no such precondition yet).

- [ ] **Step 3: Add Precondition 0**

In `spawn-handoff-session.sh`, insert immediately before `# --- Precondition 1: clean tree ---` (line ~150; `print_manual_instructions` is defined at ~line 140, so it is in scope):

```bash
# --- Precondition 0: auto-spawn enable switch (nothing reserved yet) ---------
# Plan-less, per-run kill switch, complementary to the plan-level handoff_spawn:off.
# 0/false disables auto-spawn entirely and exits 3 (manual fallback) with an honest
# reason, BEFORE the cmux-reachability probe. Invalid values warn and leave auto-spawn
# ENABLED (the default) — fail-safe like the other knobs. No cmux notify: nothing is
# reserved and the user chose this; the printed manual instructions carry it.
AUTOSPAWN="${SUPERPOWERS_CMUX_AUTOSPAWN:-1}"
case "$AUTOSPAWN" in
  0|false|FALSE|no|NO|off|OFF)
    echo "[spawn-handoff] refused: auto-spawn disabled by config (SUPERPOWERS_CMUX_AUTOSPAWN=$AUTOSPAWN, reason=autospawn-disabled). Resume manually." >&2
    print_manual_instructions
    exit 3
    ;;
  1|true|TRUE|yes|YES|on|ON|"")
    : ;;  # enabled (default)
  *)
    echo "WARNING: invalid SUPERPOWERS_CMUX_AUTOSPAWN ($AUTOSPAWN) — auto-spawn stays enabled (default)." >&2
    ;;
esac
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/ -k "autospawn or spawn_handoff" -q`
Expected: all PASS. Also run `bash scripts/lint-shell.sh` if available (no new ShellCheck warnings).

- [ ] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/spawn-handoff-session.sh tests/unit/
git commit -m "feat(n55): SUPERPOWERS_CMUX_AUTOSPAWN kill switch as precondition 0 (reason=autospawn-disabled)"
```

---

### Task 9: Env-registry docs — context-handoff-protocol.md + CLAUDE.md add SUPERPOWERS_CMUX_AUTOSPAWN

**Files:**
- Modify: `skills/subagent-driven-development/references/context-handoff-protocol.md` (the `## Env knobs (defaults)` list, ~line 186)
- Modify: `CLAUDE.md` (the "cmux auto-spawn env vars" bullet in Hook Development Gotchas)

- [ ] **Step 1: Add the knob to the protocol's Env knobs list**

In `context-handoff-protocol.md`, in the `## Env knobs (defaults)` list, add:

```markdown
- **`SUPERPOWERS_CMUX_AUTOSPAWN`** — the plan-less, per-run kill switch. Default enabled. Set to `0`/`false` to disable auto-spawn entirely: the script exits 3 with `reason=autospawn-disabled` at **Precondition 0** (before the cmux-reachability probe), and you resume manually. Invalid values warn and leave it enabled. Complementary to the plan-level `handoff_spawn: off` (durable) — this is the per-run opt-out.
```

- [ ] **Step 2: Add the knob to CLAUDE.md's env-var registry**

In `CLAUDE.md`, in the "**cmux auto-spawn env vars**" bullet (Hook Development Gotchas → the de-facto env-var registry), add `SUPERPOWERS_CMUX_AUTOSPAWN` with a one-line description matching the script's contract (0/false → exit 3 reason=autospawn-disabled at Precondition 0, before cmux reachability; invalid warns-and-stays-enabled; complementary to plan-level `handoff_spawn: off`).

- [ ] **Step 3: Verify**

Run: `/usr/bin/grep -rn "SUPERPOWERS_CMUX_AUTOSPAWN" skills/ CLAUDE.md` → appears in the script (Task 8), the protocol doc, and CLAUDE.md.

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/references/context-handoff-protocol.md CLAUDE.md
git commit -m "docs(n55): document SUPERPOWERS_CMUX_AUTOSPAWN in both env registries"
```

---

### Task 10: Skill-awareness audit — which skills know about auto-spawn

**Files:**
- Create: `docs/process-improvement-findings/2026-08-04-cmux-autospawn-skill-awareness-audit.md`

Records a durable answer to "which skills need to know about auto-spawn, and does each carry the awareness."

- [ ] **Step 1: Assess each skill**

For each of SDD, writing-plans, brainstorming, `executing-plans`, `using-superpowers`: determine whether its flow reaches the context-pressure gate / auto-spawn, and whether it now carries the awareness. Specifically verify:
- SDD, writing-plans, brainstorming — edited in this feature (confirm the awareness landed).
- `executing-plans` — read `skills/executing-plans/SKILL.md`: does its inline/batch execution path reach the pre-dispatch context gate (which fires on implementer Agent dispatches)? Record whether it dispatches implementers via the Agent tool (gate applies) or executes inline (gate may not fire), and whether a pointer is warranted.
- `using-superpowers` — the bootstrap; confirm no change is needed (it does not orchestrate dispatches).

- [ ] **Step 2: Write the findings doc**

Create `docs/process-improvement-findings/2026-08-04-cmux-autospawn-skill-awareness-audit.md` with a per-skill table (skill | reaches gate? | awareness present? | action taken / none needed) and a one-paragraph conclusion. If `executing-plans` warrants a pointer, note it as a follow-up (do NOT edit executing-plans here unless the assessment shows a clear gap — flag it for the plan/BACKLOG instead to keep scope tight).

- [ ] **Step 3: Commit**

```bash
git add docs/process-improvement-findings/2026-08-04-cmux-autospawn-skill-awareness-audit.md
git commit -m "docs(discoverability): skill-awareness audit for cmux auto-spawn"
```

## Acceptance Criteria (Module 3)

- [ ] SDD `SKILL.md` Context Health Protocol names the cmux auto-spawn as the default block-response (manual as fallback); `wc -w` under 5000; regression no new FAIL.
- [ ] Both the SOFT nudge and HARD block hook messages name `spawn-handoff-session.sh` as the default response; existing assertions (Do NOT retry / STOP) preserved; hook baseline re-captured in the same commit.
- [ ] `SUPERPOWERS_CMUX_AUTOSPAWN=0`/`false` → exit 3 `reason=autospawn-disabled` before the cmux-reachability check; invalid warns-and-proceeds; unset proceeds.
- [ ] `SUPERPOWERS_CMUX_AUTOSPAWN` documented in `context-handoff-protocol.md` and `CLAUDE.md`.
- [ ] Skill-awareness audit result recorded for SDD, writing-plans, brainstorming, executing-plans, using-superpowers.
