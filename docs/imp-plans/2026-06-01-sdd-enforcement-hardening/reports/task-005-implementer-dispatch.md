You are a focused implementation engineer. You are implementing Task 5 of the SDD Enforcement Hardening plan — modifying the integration e2e test.

Work from: `/Users/araymond/projects/claude-custom/superpowers/.worktrees/sdd-enforcement-hardening` (git worktree, branch `sdd-enforcement-hardening`).

## Task Description (VERBATIM from plan.md, Task 5)

### Task 5: E2E — provenance in transition + module-2-first-task post-transition

**Files:**
- Modify: `tests/integration/sdd-e2e-test.sh`

**Context:** Two changes. (a) Step 4 must append dispatch-log provenance for the Module 1 tasks, or the Step 5 transition now FAILs under N3b. (b) A new step dispatches the **module-2 first task (task 2) through the live hook after the transition** and asserts it is allowed — the live proof of BOTH the N3a skip-guard (pre-fix, Check 4c looks for `task=1` provenance in the truncated/empty log and blocks) AND the N11 recompute (pre-fix, `context_summary_at` stays 1 and Check 6b blocks task 2; the step also asserts the manifest recomputed it to 3). N10's archived-Task-0 path is covered by Task 2's unit test (`test_check5_finds_archived_task0`).

- [ ] **Step 1: Add provenance to Step 4.** In the Module-1 report-creation loop (the `for tid in 0 1; do ... done` block around the existing Step 4), append provenance lines to the dispatch log so the transition validator passes:

```bash
for tid in 0 1; do
  padded=$(printf "%03d" $tid)
  for kind in implementer-report spec-review quality-review; do
    { echo "# ${kind} for task ${tid}"; echo ""; printf 'x%.0s' {1..100}; } > "$FEAT/reports/task-${padded}-${kind}.md"
  done
  # N3b: transition now verifies dispatch-log provenance before truncating.
  echo "2026-06-01T00:00:00Z DISPATCH reviewer task=${tid} type=spec-review" >> "$FEAT/reports/.dispatch-log"
  echo "2026-06-01T00:00:00Z DISPATCH reviewer task=${tid} type=quality-review" >> "$FEAT/reports/.dispatch-log"
done
```

- [ ] **Step 2: Add the post-transition module-2-first-task step.** After the existing Step 7 (post-transition checkpoint) — before the rt-feature Step 8 block — insert a new step that drives the live hook. Keep the existing `=== STEP N ===` numbering style; renumber subsequent steps' echo labels if you prefer, or label this `STEP 7b`:

```bash
echo ""
echo "=== STEP 7b: module-2 first task dispatches post-transition (N3a skip-guard + N11) ==="
# After the Core->API transition the live log is empty (truncated), task_range is
# [2,3], and (N11) context_summary_at has been recomputed to module-2's midpoint
# (3). Dispatching task 2 (module-first) must be ALLOWED: PREV=1 < START=2 ->
# Check 4c skip-guard. Non-vacuous on TWO axes: pre-N3a the hook greps the empty
# log for `task=1 type=spec-review` and BLOCKS; pre-N11 context_summary_at stays 1,
# so Check 6b (2 >= 1) BLOCKS task 2 for a missing context summary. Live proof of both.
CS=$(python3 -c "import json; print(json.load(open('$FEAT/.sdd-session.json'))['enforcement']['context_summary_at'])")
test "$CS" = "3" || { echo "FAIL: N11 — context_summary_at not recomputed for module 2 (got $CS, want 3)"; exit 1; }
HOOK="$PROJECT/skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
echo "$FEAT" > "$WORK/.active-feature"          # hook resolves manifest via .active-feature
touch "$WORK/.allow-main"                         # git init default branch is main; allow SDD here
# Support files so the only gate that could fire for task 2 is Check 4c (NO
# context-summary stub needed — N11's recompute means 2 < context_summary_at=3):
{ echo "# audit"; printf 'x%.0s' {1..60}; } > "$FEAT/reports/pre-execution-audit.md"
echo '{"status":"PASS","detail":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}' > "$FEAT/reports/checkpoint-pre-dispatch-002.json"
{ echo "# partner"; printf 'x%.0s' {1..60}; } > "$FEAT/reports/partner-review-002.md"
echo "2026-06-01T00:00:00Z DISPATCH reviewer task=2 type=partner-review" >> "$FEAT/reports/.dispatch-log"
HOOK_INPUT='{"tool_input":{"description":"Implement task 2","prompt":"You are implementing task 2"},"cwd":"'"$WORK"'"}'
set +e
echo "$HOOK_INPUT" | bash "$HOOK"; HOOK_RC=$?
set -e
test "$HOOK_RC" -eq 0 || { echo "FAIL: hook blocked module-2 first task post-transition (rc=$HOOK_RC)"; exit 1; }
echo "  PASS: task 2 dispatched post-transition — skip-guard (N3a) + recomputed context_summary_at (N11)"
```

> Note: the hook no-ops (exit 0) if `jq` is missing — this step assumes `jq` is installed (it is on the dev machine; the hook depends on it). The `set +e/-e` dance is required because the harness runs under `set -e` + an ERR trap.

- [ ] **Step 3: Update the final banner.** Change the closing `echo "E2E PIPELINE PASS - 10 steps composed correctly"` to reflect the new count (11 steps).

- [ ] **Step 4: Run the e2e**

Run: `bash tests/integration/sdd-e2e-test.sh`
Expected: `E2E PIPELINE PASS - 11 steps composed correctly`.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/sdd-e2e-test.sh
git commit -m "test(sdd): e2e provenance in transition + module-2-first-task post-transition"
```

## CRITICAL GUARDRAILS
1. **Step 1 modifies the EXISTING Step 4 loop** (currently lines ~113-124: `for tid in 0 1; do ... done`). Add ONLY the two `echo "... DISPATCH reviewer task=${tid} type=..." >> "$FEAT/reports/.dispatch-log"` lines inside the loop (after the report-creation inner loop). The existing report creation must be preserved. (The current loop uses a multi-line `{ echo...; echo ""; printf...; }` block — you may keep that exact form and just add the 2 provenance lines, or use the plan's compact one-line form; either works as long as the reports + provenance are both created.)
2. **Step 2 inserts a NEW step (STEP 7b) between the existing Step 7 (ends ~line 159, "PASS: Post-transition checkpoint resolves module-2.md") and the existing Step 8 (starts ~line 162, "=== STEP 8: review_tier:minimum exclusion...").** Paste the Step 7b block verbatim. Do NOT renumber Step 8+ (labeling the new one "7b" avoids renumbering — simplest).
3. **The hook under test is `$PROJECT/skills/.../sdd-pre-dispatch-hook.sh`** — i.e. the WORKTREE hook (hardened by Task 2's N3a). PROJECT resolves to the repo root (worktree). This is correct: Step 7b proves the hardened hook allows the module-2 first task. Do NOT point it elsewhere.
4. **Step 3: banner 10 → 11** — only the count changes.
5. **Variables** (confirm by reading the e2e top): `PROJECT` = repo root; `WORK` = temp dir (script `cd`s into it at line 14); `FEAT=docs/imp-plans/test-feature` (relative to WORK); `DEVIATIONS=$FEAT/deviations.md`. The Step 7b snippet uses `$FEAT`, `$WORK`, `$PROJECT` — all already defined.
6. **The `set +e/-e` dance in Step 7b is load-bearing** — the e2e runs under `set -e` (+ likely an ERR trap); without it, a non-zero hook rc would abort the script before the `test` assertion. Keep it exactly.
7. Read the e2e fully before editing. If the Step 4 loop or the Step 7/Step 8 boundary differs from this description, STOP and report BLOCKED.

## Context (scene-setting)
`tests/integration/sdd-e2e-test.sh` is the composed-pipeline smoke test (materialize → validators → checkpoint → transition → post-transition). It runs in an isolated `$WORK` temp dir (git-init'd, `cd`'d into). After Task 3 landed N3b (transition-time provenance), the existing Step 4 creates reports but NO dispatch-log provenance, so Step 5's transition now FAILs (`INCOMPLETE: Task 0: spec review not provenance-logged`) — the e2e is currently RED by design. Step 1 of THIS task fixes that. Step 2 adds the live proof that a module-2 first task dispatches post-transition (N3a skip-guard + N11 recompute), driving the actual (worktree, hardened) hook via subprocess.

## Contract Constraints (verbatim — non-negotiable)
- Dispatch-log provenance line format: `<ts> DISPATCH reviewer task=<N> type=<spec-review|quality-review|partner-review>`. Step 1 + Step 7b write these.
- Manifest is git-root-relative; the hook resolves the manifest via `$WORK/.active-feature` (Step 7b writes it). `MANIFEST_TASK_START = task_range[0]` ([2,3] post-transition → START=2).
- Module boundary lifecycle: after the Core→API transition (Step 5), the live `.dispatch-log` is truncated (empty) and `task_range` is [2,3]; (N11) `context_summary_at` recomputed to module-2 midpoint (3). Step 7b asserts CS==3 and that the hook ALLOWS task 2 (PREV=1 < START=2 → Check 4c skip).
- Block convention: hook exit 2 = block, exit 0 = allow. Step 7b asserts exit 0.

## Source Files (read-only except the e2e you own)
- `tests/integration/sdd-e2e-test.sh` (the file you modify — read fully; confirm Step 4 loop, Step 7 end, Step 8 start, banner).
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (the hook Step 7b drives — already hardened by Task 2; do NOT modify).
- `skills/subagent-driven-development/scripts/transition-module.py` (Step 5 calls it — already has N3b+N11 from Task 3; do NOT modify).

## Shared Constants
None.

## Pattern References
None specific. Match the e2e's existing step style (`echo "=== STEP N: ... ==="`, `test ...`, `echo "  PASS: ..."`).

## Subdirectory CLAUDE.md Files
None in `tests/integration/`. Governing conventions: root CLAUDE.md ("Behavioral Test Gotchas": grep -E for ERE; macOS has no `timeout`; the `!`...`` preprocessor note is N/A here). The e2e is a bash script run directly (not via the command-stub preprocessor).

## Before You Begin
If the Step 4 loop or the Step 7→Step 8 boundary differs from the description, or if running the UN-modified e2e does NOT fail at Step 5 (it should, post-N3b), STOP and report — the premise would be off.

## Your Job
1. Read the e2e fully (confirm Step 4 loop ~113-124, Step 7 end ~159, Step 8 start ~162, banner ~361).
2. (Optional but recommended) run the un-modified e2e to confirm it currently FAILs at Step 5 (RED baseline for this task).
3. Step 1: add the 2 provenance lines inside the Step 4 loop.
4. Step 2: insert STEP 7b verbatim between Step 7 and Step 8.
5. Step 3: banner 10 → 11.
6. Step 4: run `bash tests/integration/sdd-e2e-test.sh` → `E2E PIPELINE PASS - 11 steps composed correctly`.
7. Step 5: commit the one file with the exact message.
8. Clean up scratch files. Self-review (Step 4 reports+provenance both present; Step 7b inserted at the right boundary; banner updated; e2e green at 11 steps). Report.

## Report Format
Standard YAML frontmatter (schema_version, task_id: 5, status, files_changed, tests {written: [describe — e2e step count], passing, command: "bash tests/integration/sdd-e2e-test.sh", result}, contract_compliance) then prose sections: Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations from Plan, Self-Review Findings, Concerns. Your final message IS the report. DONE_WITH_CONCERNS if any deviations/concerns; BLOCKED if you cannot complete.
