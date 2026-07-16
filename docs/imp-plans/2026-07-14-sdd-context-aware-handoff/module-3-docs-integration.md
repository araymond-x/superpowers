# Module 3 — Docs, Integration, Verification

**Goal:** Add the controller's block-response protocol reference and a short SKILL.md pointer (offset under the word ceiling by extracting existing prose), write the operational/troubleshooting docs, add the e2e over-threshold-block step, and run the full verification sweep.

**Source Contracts:** None

_This module documents and tests the hook behavior built in Module 2 (nudge/block, observation log, fallback) and the `context-probe.py` CLI (Module 1). No new external schema — internal dependencies only, so no Task 0._

**Contract Constraints:**
- SDD SKILL.md must stay **< 5000 words** (`validate-all-skills.py` WORD_LIMIT). The new pointer MUST be offset by extracting existing prose to a **separate** reference file (not the protocol doc).
- The e2e step is **checkout-path proof only** — the live hook resolves to the main checkout via settings.json; label it so and note the post-merge live-hook smoke check.
- Task 10 is `task_type: verification` — it runs suites and reads state; it modifies NO files (baseline was already captured in Module 2).

## File Map
- Create: `skills/subagent-driven-development/references/context-handoff-protocol.md`
- Create: `skills/subagent-driven-development/references/controller-health-checkpoints.md`
- Modify: `skills/subagent-driven-development/SKILL.md`
- Modify: `CLAUDE.md`, `docs/ARaymond-skills-best-practices.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md`
- Modify: `tests/integration/sdd-e2e-test.sh`

**Write-Scope Partitioning:**

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| 7 | `references/context-handoff-protocol.md`, `references/controller-health-checkpoints.md`, `SKILL.md` | `validate-all-skills.py` | 6 |
| 8 | `CLAUDE.md`, `docs/ARaymond-skills-best-practices.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | the hook, the probe | 7 |
| 9 | `tests/integration/sdd-e2e-test.sh` | the hook, fixtures | 8 |
| 10 | (none) | all suites | 9 |

---

### Task 7: Handoff-protocol reference + SKILL.md pointer (word-offset)

**Files:**
- Create: `skills/subagent-driven-development/references/context-handoff-protocol.md`
- Create: `skills/subagent-driven-development/references/controller-health-checkpoints.md`
- Modify: `skills/subagent-driven-development/SKILL.md`
- Report: `.../reports/task-007-implementer-report.md`

**Pattern References:** `references/context-health-protocol.md` — same shape (short SKILL pointer → a `references/` doc).

- [x] **Step 1: Create the block-response protocol reference**

`skills/subagent-driven-development/references/context-handoff-protocol.md`:

```markdown
# Context Handoff Protocol (controller block-response)

The pre-dispatch hook has BLOCKED the next new-task implementer dispatch because
the controller's context reached the hard threshold (default 400k tokens). This
is a deterministic stop at a clean task boundary — the previous task is fully
committed and reviewed. Follow this protocol. Do NOT improvise.

**1. This is NOT a fix-and-retry.** Retrying the dispatch is wrong — the block
is not caused by a missing report or a failed review. Do not edit files to "get
past" it, and do not set `SUPERPOWERS_CTX_HANDOFF_BYPASS` unless you have a
specific reason to run without the gate (a diagnosed probe fault). The correct
response is to hand off, not to push through.

**2. Commit pending state.** Ensure the completed task's code, its reports under
`reports/`, updated plan checkboxes, and `deviations.md` are all committed. The
fresh session resumes from committed state only.

**3. Build the fresh-session handoff.** Invoke the `handoff` skill to create a
bundle whose entry skill is `superpowers:subagent-driven-development` (the N39
flow). The bundle captures the goal, the plan/manifest, and next-action context.

**4. Tell the user how to resume.** Instruct them to start a FRESH session FROM
the worktree (so the enforcement hooks bind to the worktree CWD) and run
`/pickup`. The new session invokes SDD via the entry skill and resumes mid-plan
per `references/session-recovery.md` (plan checkboxes + `deviations.md` +
`reports/` → first unchecked task).

**5. STOP.** Do not dispatch the next task in this session.

**Why a block, not just advice:** a context-heavy controller is exactly the one
that rationalizes "just one more task." The hook removes the choice at the
boundary. The block guarantees the next task will not dispatch here; the *clean*
handoff still depends on you following steps 2–5.

**A soft nudge** (context ≥ soft, < hard) is the same guidance offered earlier,
without the stop — handing off at the nudge is preferred to waiting for the block.
```

- [x] **Step 2: Extract "Controller Health Checkpoints" to a reference (the word offset)**

Create `skills/subagent-driven-development/references/controller-health-checkpoints.md` containing the CURRENT SKILL.md §272–292 content verbatim (the three `controller-checkpoint.py` invocations for pre-execution / pre-dispatch / pre-completion, with their Verify lines). Header:

```markdown
# Controller Health Checkpoints

The controller runs a deterministic checkpoint script at three critical moments. These are not optional — they replace self-assessment with mechanical verification.
```
…followed by the three fenced `bash` command blocks and their `Verify:` lines exactly as they appear in SKILL.md §276–292 today (they already use the reconciled `--manifest … --deviations-file … --reports-dir` form — copy them without alteration).

- [x] **Step 3: Replace §272–292 in SKILL.md with a short pointer**

Replace the entire `## Controller Health Checkpoints` section body (lines 272–292) with:

```markdown
## Controller Health Checkpoints

See `references/controller-health-checkpoints.md` for the three deterministic `controller-checkpoint.py` invocations (pre-execution, pre-dispatch, pre-completion) and what each verifies. The pre-dispatch hook enforces the pre-dispatch checkpoint (Check 5c) and the pre-completion gate automatically.
```

- [x] **Step 4: Add the handoff-protocol pointer in the Context Health Protocol section**

In the `## Context Health Protocol` section (SKILL.md ~L294), append a sentence after the existing pointer:

```markdown
When the pre-dispatch hook BLOCKS a dispatch for context pressure (hard threshold), follow `references/context-handoff-protocol.md` — the block is not a fix-and-retry; commit, build a fresh-session handoff, and stop.
```

- [x] **Step 5: Verify the word count stays under the limit**

Run: `python3 tests/ARaymond-skill-regression/validate-all-skills.py 2>&1 | grep -iE 'subagent-driven|word|PASS|FAIL'`
Expected: SDD SKILL.md under the 5000 WORD_LIMIT (the ~169-word extraction more than offsets the two short pointers). Confirm no new FAIL. Also confirm the two new reference files are present (the regression test cross-checks `references/` links).

Run: `wc -w skills/subagent-driven-development/SKILL.md`
Expected: below 5000 (was 4918; net change should be negative).

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/references/context-handoff-protocol.md \
  skills/subagent-driven-development/references/controller-health-checkpoints.md \
  skills/subagent-driven-development/SKILL.md
git commit -m "docs(sdd-ctx): add context-handoff-protocol reference + SKILL pointer (word-offset)"
```

---

### Task 8: Operational + troubleshooting documentation

**review_tier: minimum** (documentation). No dispatched review required.

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/ARaymond-skills-best-practices.md`
- Modify: `docs/ARaymond-customization-manifest.md`
- Modify: `docs/process-improvement-findings/BACKLOG.md`
- Report: `.../reports/task-008-implementer-report.md`

- [x] **Step 1: CLAUDE.md — Hooks-Based Enforcement entry**

Under the "Hooks-Based Enforcement" section, add a bullet describing the context gate: what it does (reads the controller's actual token count via `context-probe.py`, nudges at SOFT, blocks at HARD on the implementer new-task path only, manifest-gated to SDD sessions), where it lives (`sdd-pre-dispatch-hook.sh` + `context-probe.py` + `references/context-handoff-protocol.md`), that the observation log is `reports/context-observations.log` (separate from `.dispatch-log`), and that the byte-proxy fallback is advisory with a K-consecutive-fallback escalation.

- [x] **Step 2: CLAUDE.md — env-var list + Hook Development Gotchas**

Add the three env vars to the Hook Development Gotchas env-var list (alongside `SUPERPOWERS_VALIDATOR_BYPASS` / `SUPERPOWERS_SDD_BYPASS`):
- `SUPERPOWERS_CTX_SOFT_TOKENS` (default 300000), `SUPERPOWERS_CTX_HARD_TOKENS` (default 400000), `SUPERPOWERS_CTX_FALLBACK_STREAK` (default 3), `SUPERPOWERS_CTX_HANDOFF_BYPASS` (escape hatch — skips the gate with a stderr warning). Note the window policy: defaults are 1M-tuned; on a 200k session lower BOTH (setting only HARD below SOFT trips the `HARD ≤ SOFT` guard → reverts to defaults). Note the transcript-from-payload design (why not `CLAUDE_CODE_SESSION_ID`), so it isn't "fixed" back to the fragile env-var path.

- [x] **Step 3: CLAUDE.md — test counts**

Update the unit-test inventory line to include the new suites: `test_context_probe.py`, `test_context_probe_fixtures.py`, `test_context_gate_log.py`, `test_context_gate_tier.py`, `test_context_gate_fallback.py`; note the e2e step count increases; note the new baseline hash for `sdd-pre-dispatch-hook.sh`.

- [x] **Step 4: docs/ARaymond-skills-best-practices.md — troubleshooting runbook**

Add a "Context Gate Troubleshooting" subsection:
- **Gate never fires** → check `.transcript_path` resolution and grep the observation log for `action=fallback` (probe is failing → gate degraded to advisory byte-proxy). Confirm the session actually reaches HARD before auto-compaction.
- **Falling back every dispatch** → run `context-probe.py --transcript <path>` manually; check its exit code and that it is stdlib-only (no venv-only imports); confirm the payload carries `.transcript_path`.
- **Fires too early / too late** → tune `SUPERPOWERS_CTX_SOFT_TOKENS` / `_HARD_TOKENS` from real `source=probe` rows in `reports/context-observations.log` (exclude `byte-proxy`/`bypass` rows from the analysis).
- **How to disable** → `SUPERPOWERS_CTX_HANDOFF_BYPASS=1`.
- **Design note (transcript source)** — transcript comes from the PreToolUse stdin payload (`.transcript_path`), NOT `CLAUDE_CODE_SESSION_ID` (a hook is a different spawn path; the env var is not guaranteed there). Do not "simplify" it back to the env var.
- **Design note (per-dispatch cost)** — the probe `read_text()`s the whole transcript on **every** dispatch (strict parity with `claude-ctx-check` was chosen over a bounded tail-read, which would break the differential test). On a large (1M-token) session the transcript can be tens of MB, so each dispatch pays that read; this is an accepted trade-off for parity. If it ever becomes a latency problem, a bounded reverse-read is the optimization — but it must be re-pinned against `claude-ctx-check` to preserve parity.
- **Design note (observation-log scope)** — an implementer dispatch blocked by a *prior* enforcement check (`ERRORS` → `exit 2`) does NOT log a context observation (the gate sits after the ERRORS report by design). This mirrors the pre-parse early-exit carve-out; the clean re-dispatch logs. Do not "fix" it by moving the gate before the ERRORS report — that would let a context block strand a half-reviewed prior task.

- [x] **Step 5: docs/ARaymond-customization-manifest.md — inventory**

Add inventory entries for `context-probe.py`, the `sdd-pre-dispatch-hook.sh` context-gate change, `references/context-handoff-protocol.md`, `references/controller-health-checkpoints.md`, and the `reports/context-observations.log` runtime artifact.

- [x] **Step 6: BACKLOG.md — N43 status**

Flip BACKLOG N43 to done-pending-merge (the actual merge-commit annotation happens during `finishing-a-development-branch`). Note that B10 (pressure-conditional context-summary) is now unblocked as the fast-follow.

- [x] **Step 7: Commit**

```bash
git add CLAUDE.md docs/ARaymond-skills-best-practices.md docs/ARaymond-customization-manifest.md docs/process-improvement-findings/BACKLOG.md
git commit -m "docs(sdd-ctx): operational + troubleshooting docs for the context gate"
```

---

### Task 9: e2e integration step (over-threshold block)

**Files:**
- Modify: `tests/integration/sdd-e2e-test.sh`
- Report: `.../reports/task-009-implementer-report.md`

- [x] **Step 1: Add the context-gate block step**

Append a new step (after the current final Step 12) to `tests/integration/sdd-e2e-test.sh`. It drives the live-checkout hook with an implementer dispatch whose `.transcript_path` points at the `hard.jsonl` fixture, in a manifest workspace with a completed prior task, and asserts `exit 2` + the non-retryable message + a `source=probe` observation line. Label it checkout-path proof.

```bash
echo ""
echo "=== Step 13: context gate blocks over-HARD implementer dispatch (checkout-path proof) ==="
# NOTE: this exercises THIS checkout's hook, not the installed live hook
# (settings.json resolves the live hook to the main checkout). A post-merge
# live-hook smoke check is required separately (see spec §9 constraint 2).
CTX_WORK=$(mktemp -d)
# Minimal manifest workspace with task 0 complete, dispatching task 1.
# setup_full_sdd_workspace does its own git init + checkout + initial commit,
# so no manual git setup is needed here.
PYTHONPATH="$PROJECT/tests/unit" $PYTHON - "$CTX_WORK" "$PROJECT" << 'PYEOF'
import sys
sys.path.insert(0, sys.argv[2] + "/tests/unit")
from sdd_test_helpers import setup_full_sdd_workspace
setup_full_sdd_workspace(sys.argv[1], total_tasks=4, completed_tasks=1)
PYEOF
CTX_FIX="$PROJECT/tests/unit/fixtures/context-probe/hard.jsonl"
CTX_PAYLOAD=$($PYTHON - "$CTX_WORK" "$CTX_FIX" << 'PYEOF'
import json, sys
print(json.dumps({
  "tool_input": {"description": "Implement task 1", "prompt": "You are implementing task 1"},
  "cwd": sys.argv[1],
  "transcript_path": sys.argv[2],
}))
PYEOF
)
CTX_OUT=$(mktemp)
SUPERPOWERS_ROOT="$PROJECT" bash "$PROJECT/skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh" \
  <<< "$CTX_PAYLOAD" > "$CTX_OUT" 2>"$CTX_OUT.err"
CTX_RC=$?
grep -qi "do not retry" "$CTX_OUT.err" || { echo "FAIL: block message missing non-retryable text"; exit 1; }
[ "$CTX_RC" -eq 2 ] || { echo "FAIL: expected exit 2, got $CTX_RC"; exit 1; }
grep -q "source=probe" "$CTX_WORK/reports/context-observations.log" || { echo "FAIL: no source=probe observation line"; exit 1; }
grep -q "action=block" "$CTX_WORK/reports/context-observations.log" || { echo "FAIL: no action=block observation line"; exit 1; }
rm -rf "$CTX_WORK" "$CTX_OUT" "$CTX_OUT.err"
echo "PASS: Step 13 — context gate blocks over-HARD implementer dispatch + logs source=probe"
```

Update the closing banner (`E2E PIPELINE PASS - N steps ...`) to reflect the new step count (13 → 14).

- [x] **Step 2: Run the e2e suite**

Run: `bash tests/integration/sdd-e2e-test.sh`
Expected: all steps PASS including the new Step 13; final banner shows the incremented count.

- [x] **Step 3: Commit**

```bash
git add tests/integration/sdd-e2e-test.sh
git commit -m "test(sdd-ctx): e2e step — context gate blocks over-HARD dispatch"
```

---

### Task 10: Final verification (all suites + baseline verify)

**task_type: verification** · **review_tier: minimum** — read-only; runs suites, writes no files.

**Files:**
- Report: `.../reports/task-010-implementer-report.md` (verification report — empty `files_changed`)

- [x] **Step 1: Run the full static + unit + integration sweep**

```bash
.venv/bin/python3 -m pytest tests/unit/ -q
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/ARaymond-installation/verify-symlink-install.sh
bash tests/integration/sdd-e2e-test.sh
```
Expected: unit green (including the 5 new context suites); regression PASS-with-advisory (SDD SKILL.md < 5000 words); install PASS; e2e PASS.

- [x] **Step 2: Verify the hook baseline is in sync (verify mode, no capture)**

Run: `bash tests/ARaymond-hook-baseline/check-hooks.sh`
Expected: exit 0 — baseline matches (it was re-captured in Module 2's tasks).

- [x] **Step 3: Confirm the Check-7 removal left no orphans**

Run: `grep -rn 'CONTEXT_LOAD_WARNING' skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
Expected: no matches.

- [x] **Step 4: Confirm SKILL.md word ceiling + probe stdlib-only**

Run: `wc -w skills/subagent-driven-development/SKILL.md` (expect < 5000).
Run: `python3 skills/subagent-driven-development/scripts/context-probe.py --transcript tests/unit/fixtures/context-probe/hard.jsonl` (expect `450000` under system `python3`).

- [x] **Step 5: Write the verification report**

Write `reports/task-010-implementer-report.md` as a `task_type: verification` report (frontmatter `task_type: verification`, empty `files_changed`) summarizing every command's result. Do NOT modify any repo file in this task.

**Note on the live-hook smoke check (post-merge, out of SDD scope):** after merge, confirm the INSTALLED hook (main checkout, resolved by settings.json) fires — e.g. temporarily set `SUPERPOWERS_CTX_HARD_TOKENS` low and observe a block, or inspect a real `reports/context-observations.log` for `source=probe` rows. The e2e proves the checkout code path only.

- [x] `context-handoff-protocol.md` created; SKILL.md points to it and stays < 5000 words (offset via the checkpoints extraction).
- [x] Operational docs written (CLAUDE.md hook entry + env vars + test counts; skills-best-practices runbook; manifest inventory); BACKLOG N43 → done-pending-merge.
- [x] e2e Step 13 proves an over-HARD implementer dispatch is blocked with the non-retryable message + a `source=probe` observation line (labeled checkout-path proof).
- [x] Full sweep green; baseline verifies; no `CONTEXT_LOAD_WARNING` orphans.
