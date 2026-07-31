---
schema_version: 1
task_id: 2
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md
    description: SP1 deliverable — root cause, evidence, five-hypothesis disposition, prevalence, severity, tuning guidance, verbatim N76 merge text
  - path: skills/subagent-driven-development/scripts/context-probe.py
    description: usage_total reads the last `type:"message"` iteration instead of the double-counting top-level sum; docstring records parity divergence 2
  - path: tests/unit/test_context_probe_iterations.py
    description: new — 8 differential regression tests for multi-iteration turns and the fallback branches
  - path: tests/unit/fixtures/context-probe/iterations-advisor-triple.jsonl
    description: new — the real archived block (373139 -> 189929) verbatim
  - path: tests/unit/fixtures/context-probe/iterations-message-pair.jsonl
    description: new — ('message','message') multi-iteration, no advisor
  - path: tests/unit/fixtures/context-probe/iterations-single.jsonl
    description: new — single-iteration no-op pin
  - path: tests/unit/fixtures/context-probe/iterations-empty.jsonl
    description: new — iterations == [] fallback
  - path: tests/unit/fixtures/context-probe/iterations-not-a-list.jsonl
    description: new — non-list iterations fallback
  - path: tests/unit/fixtures/context-probe/iterations-no-message-type.jsonl
    description: new — no `message` iteration fallback
  - path: tests/unit/fixtures/context-probe/iterations-advisor-last.jsonl
    description: new — unobserved advisor-last shape, pins the chosen branch
tests: {written: 8, passing: 8, command: ".venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py -v", result: PASS}
contract_compliance:
  - constraint: context-probe.py stays stdlib-only
    status: compliant
    detail: No new imports. Verified by running the probe under bare /usr/bin/python3 (not the venv) against a real transcript — exit 0, correct JSON.
  - constraint: Python 3.9 compatibility under skills/subagent-driven-development/scripts/
    status: compliant
    detail: Optional[int] retained, no PEP-604 unions, no builtin generics. validate-all-skills.py (which runs check_python39_compat) 159 PASS / 0 FAIL / 2 pre-existing advisory warnings.
  - constraint: Do NOT invoke cmux
    status: compliant
    detail: No cmux invocation.
  - constraint: Cross-repo read-only escalation
    status: compliant
    detail: claude-codex-handoff and ~/.claude/projects were read only. ~/.claude/bin/claude-ctx-check read only. Transcript slices for replay were written to the session scratchpad, never into another repo. No git state changed outside this worktree.
  - constraint: Never git add -A, never git stash, stage explicit paths
    status: compliant
    detail: Explicit paths only; no stash.
  - constraint: Do NOT touch BACKLOG.md
    status: compliant
    detail: Untouched. The verbatim N76 replacement text is the findings doc's final section.
  - constraint: Modify code only if the root cause is a probe bug
    status: compliant
    detail: It is a probe bug. Code change is confined to context-probe.py plus new tests and fixtures.
  - constraint: Files in reports/ named task-NNN-{type}.md
    status: compliant
    detail: This report is task-002-implementation.md.
  - constraint: Parent plan Shared Contract (per-verb OK shapes, cold-start measurement method, screen polling as instrument only)
    status: not_applicable
    detail: A probe-attribution spike touches none of these surfaces.
---

## Implementation Summary

SP1's anomaly is a **multi-iteration double-count**, not a misattribution. A single assistant
turn can contain several sequential model calls; Claude Code records them in
`message.usage.iterations` and the **top-level** `usage` fields are their **sum**. Each call
re-reads the same cached prompt, so `cache_read_input_tokens` is counted once per iteration and
the naive top-level sum — which `context-probe.py` used — reports ~2x the real context.

The archived row's turn (cmux-transport session `d8a9d842`, `2026-07-30T00:55:22Z`,
`isSidechain: false`, ending in the `[task 5 fix]` `Agent` tool-use) has iterations
`['message', 'advisor_message', 'message']` with `cache_read` of `180524 + 181567 = 362091`.
True context: **189,929**, corroborated by the next turn reading `cache_read = 181567` exactly.

All five hypotheses are dispositioned in the deliverable. (d) — the leading hypothesis in the
durable record — is **false**: the value is byte-exact present in the *correct* transcript at
the *correct* time. (e) is **false including for the controller's own 539,691 observation**,
which is the same bug (corrected: 270,851).

**Fix:** `usage_total` reads the last `type: "message"` iteration and falls back to the
top-level fields when none exists. Provably a no-op on the majority path — across all 32,160
single-iteration turns in the retained corpus the top-level fields equal `iterations[0]`, zero
mismatches (detector positive-controlled with a planted mismatch first).

**Verification beyond the unit tests:** replayed both real transcripts truncated at exactly the
entry the hook saw — `373139 -> 189929` and `539691 -> 270851`; mutation test (revert
`usage_total` to the legacy sum) turns all three differential tests RED and nothing else, then
green on revert; full unit suite 649 passed (641 baseline + 8 new).

## Source Files Read

- `skills/subagent-driven-development/scripts/context-probe.py`
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (probe call sites; confirmed both fix and gated paths use `ctx_observe_and_log` identically)
- `tests/unit/test_context_probe.py`, `test_context_probe_fixtures.py`, existing fixtures
- `tests/ARaymond-hook-baseline/baseline.txt` (grep only)
- `~/.claude/bin/claude-ctx-check` (read-only parity source)
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/context-summary.md`, `task-002-controller-observation.md`
- `git show main:` — `BACKLOG.md` (N76), `2026-07-30-first-live-sdd-auto-spawn-run-analysis.md` (F7)
- Read-only cross-repo: the cmux-transport `context-observations.log`; 15 transcripts under `~/.claude/projects/-Users-...-cmux-transport/`; the controller's own transcript; a 120-file corpus sweep across `~/.claude/projects`

## CLAUDE.md Files Read

- `/Users/araymond/projects/claude-custom/superpowers/.worktrees/cmux-spawn-v2/CLAUDE.md` (the only CLAUDE.md in the repo; `find` confirms no subdirectory files). Applied: cite constructs not line numbers; pair counts with the command that computes them; `context-probe.py` is not a baselined hook so no re-capture; stdlib-only constraint on hook-invoked scripts.
- Global `~/.claude/CLAUDE.md` and rules (coding-style, error-handling, git-workflow) via session context.

## Deviations from Plan

1. **The plan's suggested exclusion rule was examined and NOT adopted.** *"Exclude rows where
   tokens jumps >50% against both neighbors"* treats a code defect as data noise and cannot
   distinguish a poisoned reading from a real peak. Because the root cause is a fixable probe
   bug, post-fix rows need no exclusion rule at all; the doc gives a three-tier procedure for
   pre-fix rows, preferring exact recomputation from the retained transcript. This is the
   pre-authorized second branch (controller decision recorded in `deviations.md`).

2. **A sixth mechanism was found that the plan's five hypotheses do not name.** (b) is the
   closest but its stated mechanism (inflated `cache_creation`) is wrong — the inflation is
   entirely `cache_read`, and the trigger is an extra in-turn model call, not a retry. Reported
   as a distinct finding rather than forced into (b).

3. **One prompt premise is partly wrong, as the prompt anticipated.** N76's "on the fix-marked
   path" is a correlation, not a mechanism — confirmed at the source: `ctx_observe_and_log` is
   invoked identically on both paths. The causal explanation is behavioral (advisor consult and
   fix dispatch share a turn), and it is stated in the doc.

## Self-Review Findings

- **Positive control for every absence claim.** The row-matching method resolved all 80
  observation rows with no unmatched and no ambiguous values, so a second poisoned row would
  have been found. The no-op detector was validated against a planted mismatch before its zero
  count was trusted. The mutation test proves the new tests fail on a revert.
- **Discriminated positively rather than by spike shape**, per the standing caution: the
  disposition rests on the `iterations` arithmetic and on the following turn's `cache_read`
  matching iteration [2] exactly — not on the row sitting between lower neighbors.
- **Fallback branch choice.** "Last `message` iteration, else top-level" is two branches with
  one fallback; the fallback is the legacy behavior, so unknown shapes degrade to today's
  reading rather than to an error.
- **`advisor_message`-last is unobserved** (0 of 793). Pinned by test with a sentinel top-level
  value so the branch is chosen, not accidental.
- **Live-hook path checked, not assumed.** `usage_total` is what the pre-dispatch context gate
  reads, so `bash tests/integration/sdd-e2e-test.sh` was run: **15/15 steps PASS**, including
  Step 13, which drives the hook against an over-HARD transcript and asserts `exit 2` +
  `source=probe` + `action=block`. Its fixture (`hard.jsonl`) carries no `iterations` key —
  `grep -rl iterations tests/integration/` returns nothing — so it takes the fallback path and
  its 450,000 reading is unchanged.
- **Test scope check:** `test_context_probe_fixtures.py` (the hand-written parity mirror) was
  deliberately left unmodified — its fixtures carry no `iterations` key, so it still agrees
  with the probe and remains a valid pin of the legacy sum on well-formed single-iteration
  input.

## Concerns

1. **Two committed artifacts on this branch now carry a falsified claim, and I did not edit
   them** (outside this task's authorized file list). `reports/task-002-controller-observation.md`
   ("the probe total is not monotonic"; "auto-compaction is the residual hypothesis") and
   `reports/context-summary.md` (which propagates it) are both wrong: the 539,691 reading is
   this same bug, and with the fix both sessions show **zero** >15% drops across 209 turns.
   `transition-module.py` archives `reports/` at the module boundary, so the controller should
   decide whether to correct them in place before Module 1→2 rather than rely on this note.

2. **Severity is higher than N76 records, and the merge text must carry that.** "Harmless at
   runtime (`action=allow`)" is falsified — the controller's own session handed off on a 2x
   inflated number, spending a hop and a session. A spurious non-retryable HARD block on the
   gated implementer path is a live consequence of the same defect, though not observed.

3. **`~/.claude/bin/claude-ctx-check` has the identical bug and is un-owned.** It is outside
   this worktree (read-only escalation), so it was not fixed. It and the statusline `ctx:`
   field over-report multi-iteration turns by ~2x. It belongs to the telemetry-exp/global-bin
   surface and needs its own BACKLOG row, which this task is forbidden to allocate.

4. **Pre-fix observation rows are still poisoned on disk.** The fix changes future readings
   only. The one known bad row lives in another repo's committed log; recomputation there is a
   separate, cross-repo change this task did not make.

5. **Threshold implication, not acted on.** `SOFT=300000` / `HARD=400000` were tuned against
   inflated readings. Any tuning pass should re-derive them from corrected data.
