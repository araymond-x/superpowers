# cmux Integration — Module 2: protocol rewrite + e2e Step 14 + docs

> **Parent plan:** `docs/imp-plans/2026-07-22-cmux-integration/plan.md`
> **Module:** 2 of 2
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Close the Module-1 test debt (Tasks 7–8), then wire the finished `spawn-handoff-session.sh` into the live pipeline: rewrite `context-handoff-protocol.md` steps 3–5 to capture the bundle id and drive the script (Task 9), add e2e Step 14 (spawn end-to-end with stubs, banner `14`→`15`, Task 10), and update the three docs (CLAUDE.md, customization manifest, BACKLOG — Task 11).

**Source Contracts:** None

_This module consumes Module 1's internal output (the completed `spawn-handoff-session.sh` interface + exit codes) — a module dependency, not an external contract. No new external schema/API/handoff is introduced, so no Task 0 is required here (its contracts were verified in Module 1 Task 0)._

**Contract Constraints:** Exit-code contract (0 spawned / 3 manual fallback / 1 refused); the script path is `~/.claude/skills/superpowers/subagent-driven-development/scripts/spawn-handoff-session.sh` for the installed protocol doc, and `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` in-repo. Do not change `sdd-pre-dispatch-hook.sh` or the hook baseline.

**Feature Archetype:** Extension (rewrite of protocol steps 3–5 is the only replaced content; e2e + docs are additive).

## File Map

| File | Responsibility |
|------|----------------|
| `tests/unit/test_spawn_handoff.py` | Module-1 test-debt sweep: new regression + mutation-proven tests (Tasks 7, 8) |
| `tests/unit/spawn_handoff_helpers.py` | Sweep harness knobs — picker-absent, non-executable version (Task 7) |
| `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` | Sweep hardening: reservation-write rc checks + Task-4 cleanup trio (Task 8) |
| `docs/imp-plans/2026-07-22-cmux-integration/module-1-spawn-script.md` | Owed plan-doc corrections (Task 8) |
| `skills/subagent-driven-development/references/context-handoff-protocol.md` | Steps 3–5 rewrite (steps 1–2 byte-identical) |
| `tests/integration/sdd-e2e-test.sh` | New Step 14 (spawn end-to-end) + banner `14`→`15` |
| `CLAUDE.md` | New "cmux Integration" section; env vars into Hook Dev Gotchas list |
| `docs/ARaymond-customization-manifest.md` | Inventory entries |
| `docs/process-improvement-findings/BACKLOG.md` | Close N43(D) with a new row |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 7 (sweep A) | `tests/unit/test_spawn_handoff.py`, `tests/unit/spawn_handoff_helpers.py` | `spawn-handoff-session.sh` | Task 6 |
| Task 8 (sweep B) | `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff.py`, `docs/imp-plans/2026-07-22-cmux-integration/module-1-spawn-script.md` | `tests/unit/spawn_handoff_helpers.py` | Task 7 |
| Task 9 | `context-handoff-protocol.md` | `spawn-handoff-session.sh` | Task 8 |
| Task 10 | `tests/integration/sdd-e2e-test.sh` | `spawn-handoff-session.sh` | Task 9 |
| Task 11 | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | all above | Task 10 |

> **Write-scope note for the sweep (Tasks 7–8):** `spawn_handoff_helpers.py` was READ-ONLY
> throughout Module 1, but three of the knob-needing gaps genuinely require a new harness knob in
> it. Editing it in Task 7 is expected — **it is logged as a write-scope deviation** rather than
> rediscovered cold. There is no concurrency risk: only Task 7 writes it, and Task 8 reads it.
>
> **Task 7 does NOT write `spawn-handoff-session.sh`** — sweep A is coverage-only, so its new tests
> pin today's behavior. All script changes are Task 8's, and they must not invalidate Task 7's
> assertions.

## Module-1 test-debt sweep — now Tasks 7 and 8

Module 1 closed with every debt item formally *dispositioned* but the sweep itself **not done**.
Disposition removes an item from every enforcement gate, so plan checkboxes are its only home —
the pre-completion all-checkboxes gate is what makes this survive. Full context and rationale per
item live in `deviations.md` → "Deferred Work" → "Task 6 test-debt sweep".

The sweep was carried here as an unnumbered "bounded round". That framing could not be dispatched:
the pre-dispatch hook rejects any task number outside the manifest `task_range`, and a *numberless*
dispatch falls through to passthrough with **no** checkpoint, partner review, or provenance — the
exact evaporation risk the checkboxes exist to prevent. It is therefore promoted to two real,
gated tasks (**7** = coverage-only, **8** = script hardening + residual + doc corrections), and the
original module tasks are renumbered 7→9, 8→10, 9→11. Item checkboxes moved into those tasks
verbatim; none were dropped.

**Most of these are spec-behavior regressions with ZERO test protection.** Each behavior was
verified working by execution during review, but deleting it today is undetected, so a future edit
breaks it silently. Mutation-prove each new test (break the behavior, watch it go RED).

Explicitly **accepted, no action** (do not re-open as findings): NM5 (`rm -f "$out_f"` unasserted),
`shq` rc-propagation (no reachable trigger), contract-probe timeout, `_successor_cmd` newline
truncation (test-helper only), and the hardcoded notify `--title` (relevant only to the eventual
Decision-15 extraction).

## Acceptance Criteria

- [ ] The Module-1 test-debt sweep (Tasks 7–8) is complete, with each new test mutation-proven — the implementer showing the assertion RED when its behavior is broken, not merely green when it is not.
- [x] The exit-code ladder is still exactly **0 spawned / 3 manual fallback / 1 refused** — Task 8 added no new exit code.
- [x] `context-handoff-protocol.md` steps 1–2 are byte-identical to the original; steps 3–5 drive the script per the exit-code ladder; a closing note documents the soft-nudge use.
- [x] `sdd-e2e-test.sh` reaches Step 14, asserts composed spawn command + notify + reservation-then-outcome log records, and passes; the final banner reads `15 steps`.
- [x] `git diff` shows `sdd-pre-dispatch-hook.sh` and `tests/ARaymond-hook-baseline/baseline.txt` unchanged.
- [ ] CLAUDE.md has a "cmux Integration" section; the two env vars are in the Hook Development Gotchas env-var list; the customization manifest and BACKLOG are updated; N43(D) is closed.

---

## Tasks

### Task 7: Sweep A — zero-protection regression coverage + harness knobs

**Files:**
- Modify: `tests/unit/spawn_handoff_helpers.py` (new knobs — see write-scope note above)
- Modify: `tests/unit/test_spawn_handoff.py`

**Coverage-only. Do NOT modify `spawn-handoff-session.sh` in this task** — it is read-only here.
Every test below must pin *today's* behavior. If a test cannot be made to pass without changing the
script, report **BLOCKED** rather than editing the script; that change belongs to Task 8.

**Pattern References:**
- `tests/unit/test_spawn_handoff.py` (existing 58 tests) — harness idiom, `run_spawn` usage, `_notify_line`/`_successor_cmd` extractors.

**Mutation proof is required, not optional.** For each new test, break the behavior it claims to
cover, run the test, and record the observed RED (test name + how it was broken + the failure) in
your report. Task 6 shipped seven assertions that looked like coverage and caught nothing.

**The test-echo collision is a recurring class in this script.** `spawn-handoff-session.sh` is
chatty on stderr, so an assertion against combined `stdout + stderr` can be satisfied by an
unrelated diagnostic echo. Treat any such assertion as contaminated until the mutation proof shows
it discriminates. Anchor on a distinctive line.

- [x] **Step 1: Add the two harness knobs to `spawn_handoff_helpers.py`.**

Both are needed because the current helper makes the failing case inexpressible. Keep the existing
call signatures working (default the new parameters to today's behavior) so no existing test changes.

  - `install_version(...)` always `chmod 0o755`. Add a knob (e.g. `executable=True`) so a
    **non-executable** version file can be installed.
  - `run_spawn(...)` always installs a `claude-picker` stub with no removal knob. Add a knob
    (e.g. `picker_stub=True`) so the **picker-absent** case can be exercised.

Do NOT remove or narrow the autouse `_hermetic_picker_env` fixture — this machine's session is
picker-launched and `run_spawn` copies `os.environ`, so that fixture is what makes "metadata absent"
cases actually mean absent.

- [x] **Step 2: `command -v claude-picker` preflight guard (`:293`).** spec.md:196 pins "picker missing → picker-manual"; deleting the check is currently undetected. Uses the picker-absent knob.

- [x] **Step 3: `-x` half of the version predicate (`:292`).** Reducing it to a bare `[ -f … ]` is undetected. Uses the non-executable-version knob.

- [x] **Step 4: `--telemetry off` value on the composed line.** The flag *pair's* presence is already pinned; only the `off` value is unasserted (all auto-path tests use `telem="1"`). Assert the value on the composed successor command line.

- [x] **Step 5: Two env-validation regression tests owed since the Task-3 fix round.** Invalid `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` → stderr WARNING + default-15 behavior; invalid `SUPERPOWERS_CMUX_QUOTA_TIMEOUT` → stderr WARNING + gate stays live. Deleting either regex block currently leaves the suite green.

- [x] **Step 6: Run the suites and confirm no regression.**

```bash
.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q
.venv/bin/python3 -m pytest tests/unit/ -q
```
Expected: all green; the `test_spawn_handoff.py` count rises from 58 by the number of tests you added.
Verify any `-k` filter with `--collect-only -q` before deriving counts from it.

- [x] **Step 7: Confirm the script is untouched, then commit.**

```bash
git diff --name-only skills/subagent-driven-development/scripts/spawn-handoff-session.sh   # must be EMPTY
git add tests/unit/test_spawn_handoff.py tests/unit/spawn_handoff_helpers.py
git commit -m "test(cmux-int): sweep A — picker-absent, -x predicate, telemetry off, env validation (Task 7)"
```

---

### Task 8: Sweep B — reservation-write hardening, residual coverage, plan-doc corrections

**Files:**
- Modify: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`
- Modify: `tests/unit/test_spawn_handoff.py`
- Modify: `docs/imp-plans/2026-07-22-cmux-integration/module-1-spawn-script.md`

**Contract constraint — the exit-code ladder is frozen at 0 / 3 / 1.** A failed reservation write
routes to the **existing exit 3** (manual fallback: no spawn happened, the hop is consumed, manual
recovery is correct) — print the manual instructions first. **Do not mint a new exit code.** Task 10
asserts this ladder in e2e and Task 11 documents it; a fourth code silently invalidates both. If you
believe exit 3 is wrong here, report **BLOCKED** with your reasoning rather than deciding unilaterally.

Same mutation-proof and test-echo-collision requirements as Task 7 — see that task's preamble.

Do **NOT** add `set -u` to the script: `${FORWARDED[*]}` on an empty array raises `unbound variable`
on bash 3.2 (the verified floor, 3.2.57) while passing on 4.4+.

- [x] **Step 1: Unchecked reservation writes (`:422-423`).** A failed `.handoff-hops` / `intent` write still proceeds to spawn, weakening Decision 21's durability guarantee. Check both writes; on failure warn, print manual instructions, exit 3. Add a test driving it (unwritable reports dir).

- [x] **Step 2: NM4 — failure-branch `cmux notify` unasserted (`:445`).** Deleting it leaves 58/58 green. One-line fix: assert the notify body inside `test_spawn_failure_keeps_hop_exits_3`.

- [x] **Step 3: mktemp-failure branch untested (`:393-397`).** Safe as written, but a future edit could break rc propagation there undetected. Stub `mktemp` on PATH to force the failure.

- [x] **Step 4: Task-4 cleanup trio.** `max(0, …)` on the label slice, lone-surrogate `try`-wrap, and confirm the `mkdir` gating fix (already landed in Task 6) needs nothing further. If a cleanup has no observable behavior change, say so explicitly rather than inventing a test.

- [x] **Step 4b: Two coverage residuals found by the Task-7 quality review (both mutation-proven to survive a green 63-test suite).** These are the `-f`/regex halves that Task 7's Step 3/Step 5 wording under-specified. The script is correct as written — these pin behavior that is currently undetectable.

  - **The `-f` half of the version predicate (`:298`).** Reducing the conjunction to a bare `[ -x … ]` leaves 63/63 green (verified independently by the controller). The pre-existing degraded-metadata param fails BOTH halves, so it pins only the conjunction; Task 7 pinned `-x`; `-f` remains unpinned. Test it by installing a **directory** named `2.1.218` under `versions/` — dirs are 0755 so `-x` passes and `-f` fails, and the picker's own `find -type f -perm -u+x` would never discover it. Expect `launch=picker-manual`.
  - **The fractional half of the `QUOTA_MIN_PCT` regex (`:27`).** `^[0-9]+(\.[0-9]+)?$` blesses `12.5`, but every MIN_PCT value in the suite is an integer, so tightening it to `^[0-9]+$` — silently reverting a legitimate fractional threshold to the default — leaves 63/63 green. Test with `SUPERPOWERS_CMUX_QUOTA_MIN_PCT="12.5"` asserting **no** WARNING and `quota=ok` at a 63.0% reading.

- [x] **Step 4c: Decide the `:299` redundancy explicitly (do not default).** Task 7 proved `command -v claude-picker` at `:299` is redundant with the contract probe at `:301` and unobservable by any black-box test: with the picker absent, `$(claude-picker --handoff-contract 2>/dev/null)` swallows "command not found", the substitution is empty, `"" != "1"`, and `:301` returns 1 anyway. Either keep it (defensible — it documents intent and stays robust if `:301` ever changes) or remove it, but **state the decision and the reason**. Do not leave it decided-by-default.

- [x] **Step 4d: Move `_hermetic_picker_env` from `test_spawn_handoff.py` to `tests/unit/conftest.py`.** The fixture is currently **module-scoped**, so any future spawn-handoff test placed in a *different* file silently inherits the developer's ambient picker env and "metadata absent" stops meaning absent. This is not hypothetical — the Task-7 quality re-reviewer wrote a throwaway probe in a scratchpad file, did not get the fixture, observed an ambient leak, and filed a finding that was wrong *because of it*. Moving it to `conftest.py` closes the class. **Keep `PICKER_ENV_VARS` as the single source of the list** (import it, do not restate it).

  **Blast radius:** moving it into `conftest.py` makes the fixture autouse for **all of `tests/unit/` (616 tests)**, not just this file's 63. So the verification is `.venv/bin/python3 -m pytest tests/unit/ -q` — **not** just the one file. The deletions use `raising=False` and *should* be inert for unrelated tests, but "should be inert" is precisely the claim this run has repeatedly disproven; run the full suite and report the count.

- [x] **Step 5: Owed plan-doc corrections in `module-1-spawn-script.md`.** Task 3 Step 2 (both snippet defects — the command-substitution + background-watcher timeout that stalls the full timeout on the success path, and the fallback-less `QUOTA_TOOL=` line whose own Step 1 tests cannot pass; replace with the shipped implementation from commit `7131698`); Task 4's wrong bash caveat (≥4.x → **≥3.2**); and Task 6 Step 2's spawn-id ordering defect (the id must be generated *before* the compose block so the composed fallback tail carries the uuid, per spec §5.4d). Scope is this file only — `plan.md` and `spec.md` do not mirror the snippet.

- [x] **Step 6: Run the suites.**

```bash
.venv/bin/python3 -m pytest tests/unit/ -q
bash scripts/lint-shell.sh
```
Expected: all green; lint-shell clean for this script.

- [x] **Step 7: Confirm no hook/baseline drift, then commit.**

```bash
git diff --name-only skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/ARaymond-hook-baseline/baseline.txt   # must be EMPTY
git add skills/subagent-driven-development/scripts/spawn-handoff-session.sh tests/unit/test_spawn_handoff.py docs/imp-plans/2026-07-22-cmux-integration/module-1-spawn-script.md
git commit -m "fix(cmux-int): sweep B — reservation-write durability, residual coverage, plan-doc corrections (Task 8)"
```

---

### Task 9: Rewrite context-handoff-protocol.md steps 3–5

**Files:**
- Modify: `skills/subagent-driven-development/references/context-handoff-protocol.md`

- [x] **Step 1: Confirm the anchor (no hook change).**

Verify the HARD-block message already points to this doc — this is why the hook needs no edit:

Run: `grep -n "context-handoff-protocol" skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
Expected: a match (spec cites line 840). If absent, STOP and report — the no-hook-change assumption is void.

- [x] **Step 2: Rewrite steps 3–5.**

Steps 1–2 stay byte-identical. Replace the current step 3 (from `**3. Build the fresh-session handoff.**`) through step 5 (`**5. STOP.**`) with the text below. Keep the "Why a block" and "A soft nudge" paragraphs, and append the closing note.

Replace this exact block:

```
**3. Build the fresh-session handoff.** Invoke the `handoff` skill to create a
bundle whose entry skill is `superpowers:subagent-driven-development` (the N39
flow). The bundle captures the goal, the plan/manifest, and next-action context.

**4. Tell the user how to resume.** Instruct them to start a FRESH session FROM
the worktree (so the enforcement hooks bind to the worktree CWD) and run
`/pickup`. The new session invokes SDD via the entry skill and resumes mid-plan
per `references/session-recovery.md` (plan checkboxes + `deviations.md` +
`reports/` → first unchecked task).

**5. STOP.** Do not dispatch the next task in this session.
```

with:

```
**3. Build the fresh-session handoff and capture its id.** Invoke the `handoff`
skill to create a bundle whose entry skill is
`superpowers:subagent-driven-development` (the N39 flow). The bundle captures the
goal, the plan/manifest, and next-action context. **Capture the bundle id** the
`/handoff` output prints (e.g. `2026-07-23T01-19-43Z-<repo>`) — step 4 needs it.

**4. Spawn the successor (or fall back).** Run:

    ~/.claude/skills/superpowers/subagent-driven-development/scripts/spawn-handoff-session.sh <bundle-id>

The script verifies the clean tree, validates the bundle, checks cmux reachability,
the hop limit, and session quota, then spawns the successor in a new cmux workspace
through the extended claude-picker. Act on its exit code:

- **Exit 0** — spawned. Report the workspace ref and launch mode (`auto` =
  unattended non-interactive pickup; `picker-manual` = the workspace opened the
  interactive picker and a notification asks the user to complete it). Nothing
  more to do here.
- **Exit 3** — manual fallback (not in a cmux workspace, hop limit reached, quota
  low, or spawn failed after reservation). Relay the manual resume instructions
  the script printed (start a fresh session from the worktree, run
  `/pickup <bundle-id>`).
- **Exit 1** — refused (dirty tree, bundle validation failed, or missing
  `.active-feature`). Fix the printed precondition and re-run the script.

**5. STOP.** Do not dispatch the next task in this session.
```

Then append this closing note after the existing "A soft nudge" paragraph:

```
**Soft-nudge use:** handing off at the soft nudge (context ≥ soft, < hard) is
preferred to waiting for the hard block, and the **same** `spawn-handoff-session.sh`
serves it — build the bundle early (step 3) and run the script (step 4) at the
nudge rather than pushing to the block.
```

- [x] **Step 3: Verify steps 1–2 are untouched.**

Run: `git diff skills/subagent-driven-development/references/context-handoff-protocol.md`
Confirm the diff touches only step 3 onward — the step 1 and step 2 paragraphs must be unchanged.

- [x] **Step 4: Run the regression suite (protocol doc is cross-referenced by validate-all-skills).**

Run: `python3 tests/ARaymond-skill-regression/validate-all-skills.py`
Expected: PASS (with the known advisory WARNINGs; no new FAIL).

- [x] **Step 5: Commit.**

```bash
git add skills/subagent-driven-development/references/context-handoff-protocol.md
git commit -m "docs(cmux-int): protocol steps 3-5 drive spawn-handoff-session.sh (Task 9)"
```

---

### Task 10: e2e Step 14 (spawn end-to-end) + banner 14→15

**Files:**
- Modify: `tests/integration/sdd-e2e-test.sh`

**Pattern References:**
- `tests/integration/sdd-e2e-test.sh` Step 13 (lines ~571–607) — stub-on-PATH, `|| RC=$?` around expected-nonzero calls, PASS echo, temp workspace cleanup.

- [x] **Step 1: Add Step 14 before the final banner.**

Insert this block after the Step 13 `echo "PASS: Step 13 ..."` line and before `echo "E2E PIPELINE PASS ..."`. It builds a fixture worktree + valid bundle, puts stub `cmux`/`claude-picker`/`claude-usage-pace` on PATH, drives `spawn-handoff-session.sh` end-to-end (real spawn path), and asserts the composed command, notify, and reservation-then-outcome ordering.

```bash
echo ""
echo "=== Step 14: spawn-handoff-session.sh end-to-end (stubbed cmux + picker) ==="
# NOTE: exercises THIS checkout's script. The installed live path resolves to the
# main checkout — a post-merge live smoke is required separately (spec §7).
SPAWN_WORK=$(mktemp -d -t sdd-spawn-XXXXXX)
SPAWN_HOME="$SPAWN_WORK/home"
SPAWN_STUBS="$SPAWN_WORK/stubs"
mkdir -p "$SPAWN_HOME/.claude-codex-handoff/bundles/b14" \
         "$SPAWN_HOME/.local/share/claude/versions/2.1.218" "$SPAWN_STUBS"

# Fixture worktree with .active-feature + reports
SPAWN_WT="$SPAWN_WORK/wt"; mkdir -p "$SPAWN_WT/docs/imp-plans/feat/reports"
( cd "$SPAWN_WT" && git init -q && git config user.email t@t && git config user.name t \
  && echo docs/imp-plans/feat > .active-feature && echo seed > seed \
  && git add -A && git commit -qm seed )
SPAWN_REPO_ID=$(cd "$SPAWN_WT" && $PYTHON - <<'PY'
import os,subprocess
c=subprocess.run(["git","rev-parse","--git-common-dir"],capture_output=True,text=True).stdout.strip()
print(os.path.realpath(c if os.path.isabs(c) else os.path.join(os.getcwd(),c)))
PY
)

# Valid work/SDD bundle manifest with the matching repo_id
cat > "$SPAWN_HOME/.claude-codex-handoff/bundles/b14/manifest.json" <<JSON
{"session":{"bundle_type":"work","entry_skill":"superpowers:subagent-driven-development"},
 "project":{"repo_id":"$SPAWN_REPO_ID","repo_name":"feat"}}
JSON

# Stubs
cat > "$SPAWN_STUBS/cmux" <<'SH'
#!/usr/bin/env bash
if [ "$1" = "ping" ]; then echo PONG; exit 0; fi
echo "$@" >> "$CMUX_LOG"; exit 0
SH
cat > "$SPAWN_STUBS/claude-picker" <<'SH'
#!/usr/bin/env bash
if [ "$1" = "--handoff-contract" ]; then echo 1; exit 0; fi
exit 0
SH
cat > "$SPAWN_STUBS/claude-usage-pace" <<'SH'
#!/usr/bin/env bash
echo '{"windows":[{"key":"session","remaining_pct":63.0}]}'
SH
chmod +x "$SPAWN_STUBS"/*

SPAWN_ARGS=$($PYTHON - <<'PY'
import base64,json
print("v1:"+base64.b64encode(json.dumps(["--append-system-prompt-file","/tmp/a b.md"]).encode()).decode())
PY
)
SPAWN_RC=0
CMUX_LOG="$SPAWN_WORK/cmux.log" \
PATH="$SPAWN_STUBS:$PATH" HOME="$SPAWN_HOME" \
CMUX_WORKSPACE_ID=TEST-WS \
CLAUDE_CODE_PICKER_VERSION=2.1.218 \
CLAUDE_CODE_PICKER_ARGS="$SPAWN_ARGS" \
CLAUDE_CODE_PICKER_LABEL="Proj-Session-2" \
CLAUDE_CODE_ENABLE_TELEMETRY=1 \
SUPERPOWERS_ROOT="$PROJECT" \
bash "$PROJECT/skills/subagent-driven-development/scripts/spawn-handoff-session.sh" b14 \
  > "$SPAWN_WORK/out" 2>&1 || SPAWN_RC=$?

[ "$SPAWN_RC" -eq 0 ] || { echo "FAIL: spawn exit $SPAWN_RC"; cat "$SPAWN_WORK/out"; exit 1; }
grep -q "new-workspace" "$SPAWN_WORK/cmux.log" || { echo "FAIL: no new-workspace"; exit 1; }
grep -q -- "--focus false" "$SPAWN_WORK/cmux.log" || { echo "FAIL: missing --focus false"; exit 1; }
grep -q "notify" "$SPAWN_WORK/cmux.log" || { echo "FAIL: no notify"; exit 1; }
# reservation ordering: intent line precedes outcome line
SPAWN_LOG="$SPAWN_WT/docs/imp-plans/feat/reports/handoff-spawn.log"
INTENT_LN=$(grep -n " intent " "$SPAWN_LOG" | head -1 | cut -d: -f1)
OUTCOME_LN=$(grep -n " outcome " "$SPAWN_LOG" | head -1 | cut -d: -f1)
[ -n "$INTENT_LN" ] && [ -n "$OUTCOME_LN" ] && [ "$INTENT_LN" -lt "$OUTCOME_LN" ] \
  || { echo "FAIL: reservation ordering (intent before outcome)"; cat "$SPAWN_LOG"; exit 1; }
# hop incremented
[ "$(cat "$SPAWN_WT/docs/imp-plans/feat/reports/.handoff-hops")" = "1" ] \
  || { echo "FAIL: hop not incremented to 1"; exit 1; }
rm -rf "$SPAWN_WORK"
echo "PASS: Step 14 — spawn end-to-end: composed command, notify, reservation-then-outcome"
```

- [x] **Step 2: Bump the banner.**

Change the final banner line from:

    echo "E2E PIPELINE PASS - 14 steps composed correctly"

to:

    echo "E2E PIPELINE PASS - 15 steps composed correctly"

- [x] **Step 3: Run the e2e suite.**

Run: `bash tests/integration/sdd-e2e-test.sh`
Expected: reaches `PASS: Step 14 ...` then `E2E PIPELINE PASS - 15 steps composed correctly`.

- [x] **Step 4: Confirm no hook / baseline drift.**

Run: `git diff --name-only skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/ARaymond-hook-baseline/baseline.txt`
Expected: **empty** (neither file changed). If either appears, revert it — this feature changes no hook.

- [x] **Step 5: Commit.**

```bash
git add tests/integration/sdd-e2e-test.sh
git commit -m "test(cmux-int): e2e Step 14 spawn end-to-end + banner 15 (Task 10)"
```

---

### Task 11: Docs — CLAUDE.md section, manifest, BACKLOG N43(D)

**review_tier: minimum** (pure documentation — no logic).

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/ARaymond-customization-manifest.md`
- Modify: `docs/process-improvement-findings/BACKLOG.md`

- [ ] **Step 1: Add the CLAUDE.md "cmux Integration" section (read-merge).**

Read `CLAUDE.md` first. Add a new top-level section (near the other feature sections). Content:
- What `spawn-handoff-session.sh` does, its interface (`BUNDLE_ID [--dry-run]`), and the exit-code ladder (0 spawned auto/picker-manual · 3 manual fallback · 1 refused).
- The cross-repo split (Decision 19): telemetry-exp picker (repo-1) → cmux-custom-skills (repo-2, `~/projects/claude-custom/cmux-custom-skills`, symlinked, pristine-vendored) → superpowers (repo-3). Note repo-2 is a separate repo with its own `verify-install.sh`; the fork's `verify-symlink-install.sh` is unchanged.
- The `handoff-spawn.log` format (ISO-8601, spawn id, record type `intent|outcome|runtime-picker-failure`, hop; outcomes add workspace ref/launch mode/bundle id/quota status) and that it is **separate** from `context-observations.log` — do not conflate the formats. Both `.handoff-hops` and `handoff-spawn.log` are **tracked** (reports/ convention).
- That the spawn script is NOT a hook (no baseline entry), but live sessions resolve `~/.claude/skills/superpowers/...` to the main checkout → develop in a worktree, live-smoke after merge.
- A pointer to the cmux fork-usage guidance ("prefer `--focus false`"; vendored cmux skills are pristine — fork-specific cmux guidance lives here, not in the vendored files).

Add the two env vars to the **Hook Development Gotchas** env-var list (alongside `SUPERPOWERS_CMUX_*`... i.e. next to the context-gate env vars): `SUPERPOWERS_CMUX_MAX_HOPS` (default 3 — hop limit) and `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` (default 15 — session-quota refusal threshold). Also mention `SUPERPOWERS_CMUX_QUOTA_TIMEOUT` (default 60) and `SUPERPOWERS_CMUX_QUOTA_TOOL` if the implementer kept them (test seams).

- [ ] **Step 1b: Document the deliberate `cmux notify` asymmetry across the exit-3 branches.** (Added by the Task-8 quality review, finding 4 — controller ratified the omission rather than adding the notify.) Three exit-3 branches DO notify — hop-limit, quota-low, and spawn-failed-after-reservation — but the two **reservation-write-failure** branches deliberately do **not**: the plan prescribed exactly "warn, print manual instructions, exit 3", and a broken/unwritable reports dir is relayed via exit 3 plus printed instructions, not a push notification. State this as an intentional rule so a future reader does not "fix" the inconsistency by reflex. Without this line the omission is invisible and indistinguishable from an oversight.

- [ ] **Step 1c: Land the accumulated doc obligations from `deviations.md`.** They are filed under the **Deferred Work** heading literally titled *"Task 9 doc obligations"* — that heading predates the Task 7/8 plan surgery and uses the **OLD** numbering, where old-Task-9 = **this task (11)**. It does NOT mean new-Task-9 (the protocol-doc rewrite). Read that list and land each item in the CLAUDE.md section: (a) the bash floor is **≥ 3.2**, NOT the plan's "≥ 4.x" — construct floor 3.1, verified floor 3.2.57; (b) the `set -u` ↔ `${FORWARDED[*]}`-on-empty-array coupling, documented **at the `FORWARDED` site**, not only generically — a future `set -u` breaks bash 3.2 silently while passing on 4.4+; (c) `SUPERPOWERS_CMUX_QUOTA_TIMEOUT` (60) + `SUPERPOWERS_CMUX_QUOTA_TOOL`; (d) rematerialized append-prompt files accumulate at `~/.claude-codex-handoff/append-prompts/<bundle>-hop<N>.md` with **no reaper** (spec §5.4d defines none). These were dispositioned in `deviations.md`, and disposition removes an item from every enforcement gate — this checkbox is their only remaining enforcement, exactly as with the Task 6 test-debt sweep.

- [ ] **Step 2: Update the customization manifest (read-merge).**

Read `docs/ARaymond-customization-manifest.md`. Add inventory entries under the relevant sections:
- New script: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`.
- New test: `tests/unit/test_spawn_handoff.py` + fixtures `tests/unit/fixtures/spawn-handoff/`.
- e2e Step 14 added (banner 14→15).
- Protocol doc steps 3–5 rewritten.
- Cross-repo pointer: repo-1 (telemetry-exp), repo-2 (`~/projects/claude-custom/cmux-custom-skills`).

- [ ] **Step 3: Close N43(D) in BACKLOG (read-merge).**

Read `docs/process-improvement-findings/BACKLOG.md`. Add a row/entry closing **N43 component (D)** (cmux auto-spawn of the next session) — reference this feature dir `docs/imp-plans/2026-07-22-cmux-integration/` and note component A (vendored cmux skills) shipped alongside. Preserve every existing row.

- [ ] **Step 4: Run all static + integration suites.**

```bash
bash tests/ARaymond-installation/verify-symlink-install.sh \
 && python3 tests/ARaymond-skill-regression/validate-all-skills.py \
 && .venv/bin/python3 -m pytest tests/unit/ -q \
 && bash tests/integration/sdd-e2e-test.sh
```
Expected: all green (regression with known advisory WARNINGs only). Confirm the hook baseline check too: `bash tests/ARaymond-hook-baseline/check-hooks.sh` (must PASS with no re-capture — no hook changed).

- [ ] **Step 5: Commit.**

```bash
git add CLAUDE.md docs/ARaymond-customization-manifest.md docs/process-improvement-findings/BACKLOG.md
git commit -m "docs(cmux-int): CLAUDE.md cmux section, manifest, close N43(D) (Task 11)"
```
