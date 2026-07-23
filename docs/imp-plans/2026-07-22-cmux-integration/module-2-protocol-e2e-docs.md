# cmux Integration — Module 2: protocol rewrite + e2e Step 14 + docs

> **Parent plan:** `docs/imp-plans/2026-07-22-cmux-integration/plan.md`
> **Module:** 2 of 2
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Wire the finished `spawn-handoff-session.sh` into the live pipeline: rewrite `context-handoff-protocol.md` steps 3–5 to capture the bundle id and drive the script, add e2e Step 14 (spawn end-to-end with stubs, banner `14`→`15`), and update the three docs (CLAUDE.md, customization manifest, BACKLOG).

**Source Contracts:** None

_This module consumes Module 1's internal output (the completed `spawn-handoff-session.sh` interface + exit codes) — a module dependency, not an external contract. No new external schema/API/handoff is introduced, so no Task 0 is required here (its contracts were verified in Module 1 Task 0)._

**Contract Constraints:** Exit-code contract (0 spawned / 3 manual fallback / 1 refused); the script path is `~/.claude/skills/superpowers/subagent-driven-development/scripts/spawn-handoff-session.sh` for the installed protocol doc, and `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` in-repo. Do not change `sdd-pre-dispatch-hook.sh` or the hook baseline.

**Feature Archetype:** Extension (rewrite of protocol steps 3–5 is the only replaced content; e2e + docs are additive).

## File Map

| File | Responsibility |
|------|----------------|
| `skills/subagent-driven-development/references/context-handoff-protocol.md` | Steps 3–5 rewrite (steps 1–2 byte-identical) |
| `tests/integration/sdd-e2e-test.sh` | New Step 14 (spawn end-to-end) + banner `14`→`15` |
| `CLAUDE.md` | New "cmux Integration" section; env vars into Hook Dev Gotchas list |
| `docs/ARaymond-customization-manifest.md` | Inventory entries |
| `docs/process-improvement-findings/BACKLOG.md` | Close N43(D) with a new row |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 7 | `context-handoff-protocol.md` | `spawn-handoff-session.sh` | Task 6 |
| Task 8 | `tests/integration/sdd-e2e-test.sh` | `spawn-handoff-session.sh` | Task 7 |
| Task 9 | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | all above | Task 8 |

## Acceptance Criteria

- [ ] `context-handoff-protocol.md` steps 1–2 are byte-identical to the original; steps 3–5 drive the script per the exit-code ladder; a closing note documents the soft-nudge use.
- [ ] `sdd-e2e-test.sh` reaches Step 14, asserts composed spawn command + notify + reservation-then-outcome log records, and passes; the final banner reads `15 steps`.
- [ ] `git diff` shows `sdd-pre-dispatch-hook.sh` and `tests/ARaymond-hook-baseline/baseline.txt` unchanged.
- [ ] CLAUDE.md has a "cmux Integration" section; the two env vars are in the Hook Development Gotchas env-var list; the customization manifest and BACKLOG are updated; N43(D) is closed.

---

## Tasks

### Task 7: Rewrite context-handoff-protocol.md steps 3–5

**Files:**
- Modify: `skills/subagent-driven-development/references/context-handoff-protocol.md`

- [ ] **Step 1: Confirm the anchor (no hook change).**

Verify the HARD-block message already points to this doc — this is why the hook needs no edit:

Run: `grep -n "context-handoff-protocol" skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
Expected: a match (spec cites line 840). If absent, STOP and report — the no-hook-change assumption is void.

- [ ] **Step 2: Rewrite steps 3–5.**

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

- [ ] **Step 3: Verify steps 1–2 are untouched.**

Run: `git diff skills/subagent-driven-development/references/context-handoff-protocol.md`
Confirm the diff touches only step 3 onward — the step 1 and step 2 paragraphs must be unchanged.

- [ ] **Step 4: Run the regression suite (protocol doc is cross-referenced by validate-all-skills).**

Run: `python3 tests/ARaymond-skill-regression/validate-all-skills.py`
Expected: PASS (with the known advisory WARNINGs; no new FAIL).

- [ ] **Step 5: Commit.**

```bash
git add skills/subagent-driven-development/references/context-handoff-protocol.md
git commit -m "docs(cmux-int): protocol steps 3-5 drive spawn-handoff-session.sh (Task 5)"
```

---

### Task 8: e2e Step 14 (spawn end-to-end) + banner 14→15

**Files:**
- Modify: `tests/integration/sdd-e2e-test.sh`

**Pattern References:**
- `tests/integration/sdd-e2e-test.sh` Step 13 (lines ~571–607) — stub-on-PATH, `|| RC=$?` around expected-nonzero calls, PASS echo, temp workspace cleanup.

- [ ] **Step 1: Add Step 14 before the final banner.**

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

- [ ] **Step 2: Bump the banner.**

Change the final banner line from:

    echo "E2E PIPELINE PASS - 14 steps composed correctly"

to:

    echo "E2E PIPELINE PASS - 15 steps composed correctly"

- [ ] **Step 3: Run the e2e suite.**

Run: `bash tests/integration/sdd-e2e-test.sh`
Expected: reaches `PASS: Step 14 ...` then `E2E PIPELINE PASS - 15 steps composed correctly`.

- [ ] **Step 4: Confirm no hook / baseline drift.**

Run: `git diff --name-only skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/ARaymond-hook-baseline/baseline.txt`
Expected: **empty** (neither file changed). If either appears, revert it — this feature changes no hook.

- [ ] **Step 5: Commit.**

```bash
git add tests/integration/sdd-e2e-test.sh
git commit -m "test(cmux-int): e2e Step 14 spawn end-to-end + banner 15 (Task 6)"
```

---

### Task 9: Docs — CLAUDE.md section, manifest, BACKLOG N43(D)

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
git commit -m "docs(cmux-int): CLAUDE.md cmux section, manifest, close N43(D) (Task 7)"
```
