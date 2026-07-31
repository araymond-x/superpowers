---
schema_version: 1
task_id: 2
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md"
    description: "SP1 root cause: multi-iteration double-count in message.usage. Evidence, five-hypothesis disposition, the no-op proof, why no exclusion rule is adopted, and the verbatim N76 merge replacement text as the final section."
  - path: "skills/subagent-driven-development/scripts/context-probe.py"
    description: "usage_total now reads the last type:'message' iteration from message.usage.iterations, falling back to the top-level fields when no iterations key is present. Stdlib-only and py39-clean preserved."
  - path: "tests/unit/test_context_probe_iterations.py"
    description: "Differential tests (buggy vs corrected value) over the iterations-*.jsonl fixtures, one carrying the real archived usage block verbatim. [CORRECTED 2026-07-31: originally said '8 tests over 7 fixtures'; the [task 2 fix] round added the fail-open, 3-iteration, non-dict-entry and non-iterable regression cases.]"
  - path: "tests/unit/fixtures/context-probe/iterations-advisor-triple.jsonl"
    description: "The real archived block (373139 -> 189929) verbatim. [ADDED to files_changed 2026-07-31: omitted from the controller-authored original.]"
  - path: "tests/unit/fixtures/context-probe/iterations-message-pair.jsonl"
    description: "('message','message') multi-iteration, no advisor. [ADDED to files_changed 2026-07-31.]"
  - path: "tests/unit/fixtures/context-probe/iterations-single.jsonl"
    description: "Single-iteration no-op pin. [ADDED to files_changed 2026-07-31.]"
  - path: "tests/unit/fixtures/context-probe/iterations-empty.jsonl"
    description: "iterations == [] fallback. [ADDED to files_changed 2026-07-31.]"
  - path: "tests/unit/fixtures/context-probe/iterations-not-a-list.jsonl"
    description: "Non-iterable scalar iterations (5) fallback. [ADDED to files_changed 2026-07-31; value changed from the string 'nope' to 5 in the [task 2 fix] round, because a string IS iterable and so did not pin the isinstance-list check.]"
  - path: "tests/unit/fixtures/context-probe/iterations-no-message-type.jsonl"
    description: "No `message` iteration present, fallback. [ADDED to files_changed 2026-07-31.]"
  - path: "tests/unit/fixtures/context-probe/iterations-advisor-last.jsonl"
    description: "Unobserved advisor-last shape, pins the chosen branch. [ADDED to files_changed 2026-07-31.]"
  - path: "tests/unit/fixtures/context-probe/iterations-message-no-fields.jsonl"
    description: "New in the [task 2 fix] round — a `message` iteration carrying no token fields; pins the fallback-on-zero that closes the gate fail-open."
  - path: "tests/unit/fixtures/context-probe/iterations-message-triple.jsonl"
    description: "New in the [task 2 fix] round — three `message` iterations (315406/107802 = 2.9258x inflation); pins that the ratio is not structurally 2.0."
  - path: "tests/unit/fixtures/context-probe/iterations-non-dict-entries.jsonl"
    description: "New in the [task 2 fix] round — non-dict entries surrounding the valid iteration; pins the isinstance-dict guard."
  - path: "tests/unit/fixtures/context-probe/iterations-string.jsonl"
    description: "New in the [task 2 fix] round — preserves the iterable-but-not-a-list shape the old iterations-not-a-list fixture held."
tests:
  written: 12
  passing: 12
  command: ".venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py -v"
  result: PASS
contract_compliance:
  - constraint: "context-probe.py stays stdlib-only (the hook invokes it without the venv)"
    status: compliant
    detail: "Verified by executing the probe under bare /usr/bin/python3; imports unchanged (argparse, json, os, sys, pathlib.Path, typing.Optional)."
  - constraint: "Python 3.9 compatibility for skills/subagent-driven-development/scripts/"
    status: compliant
    detail: "No PEP-604 unions, no builtin generics in annotations. check_python39_compat passes in the regression suite."
  - constraint: "Cross-repo read-only"
    status: compliant
    detail: "claude-codex-handoff and ~/.claude/projects/ were read only. No edits, commits, or git state changes outside this worktree."
  - constraint: "Do not touch BACKLOG.md"
    status: compliant
    detail: "No BACKLOG edit. The verbatim N76 replacement text is the doc's final section, for the merge step to apply."
  - constraint: "Modify code only if the root cause is a probe bug"
    status: compliant
    detail: "The root cause IS a probe bug, so the code change is authorized by the plan's own conditional."
---

## Implementation Summary

**Root cause: a multi-iteration double-count, not a misattribution.**

A single assistant turn can contain several sequential model calls. Claude Code records them in `message.usage.iterations`, and the top-level `usage` fields **aggregate across the `type: "message"` iterations only** — a non-`message` iteration such as `advisor_message` is excluded — so the same cached prompt is counted once per `message` call. `context-probe.py` summed the top level and reported roughly 2× the real context. *[CORRECTED 2026-07-31, `[task 2 fix]`: originally "aggregate across those iterations", which over-generalizes in the same way the section below corrects.]*

The archived turn (cmux-transport session `d8a9d842`, `2026-07-30T00:55:22Z`, `isSidechain: false`, ending in the `[task 5 fix]` `Agent` tool-use) has iterations `['message','advisor_message','message']` with `cache_read = 180524 + 181567 = 362091`. **True context: 189,929** — corroborated independently by the next turn reading `cache_read = 181567` exactly.

### Controller correction to the stated mechanism

The report originally said the top-level fields are "their sum" over iterations. **Verified by the controller against its own peak block, that is imprecise.** For a `['message','advisor_message','message']` turn:

```
[0] type=message           subtotal=268840
[1] type=advisor_message   subtotal=271751
[2] type=message           subtotal=270851
SUM(all iterations) = 811442   top-level = 539691   -> NOT equal
268840 + 270851      = 539691   top-level = 539691   -> EXACT
```

The top level is the sum of the **`type: "message"`** iterations; the `advisor_message` iteration is excluded. This does not change the fix or any number — the last `message` iteration is 270,851 either way — but the mechanism sentence in the durable doc must say "sum of the message-type iterations", not "sum of the iterations". Flagged for the quality review to confirm the doc's wording.

## Hypothesis disposition

- **(d) wrong transcript — FALSE.** This was the leading hypothesis in the durable record (N76 / run-analysis F7). `373139` is byte-exact present in the *correct* transcript at the *correct* time.
- **(a) sidechain — FALSE.** Re-tested against the archived corpus' own evidence rather than inherited from the controller's instance, as the dispatch required.
- **(c) genuine spike — FALSE.**
- **(b)** is closest, but its stated mechanism is wrong: the inflation is entirely `cache_read`, and the trigger is an extra in-turn model call, not a retry.
- **(e) pre-compaction peak — FALSE, including for the controller's own case.**

## Two premises falsified — controller action needed

1. **The controller's own 539,691 reading is this same bug** (true: 270,851). `reports/task-002-controller-observation.md` and `reports/context-summary.md` both assert "the probe total is not monotonic" with auto-compaction as the residual hypothesis. With the fix, **every >15% drop across 209 turns in both sessions disappears (4 → 0)**. Those artifacts were not edited — outside the authorized file list, and they are the controller's flight recorder — but `transition-module.py` archives them at the boundary, so this needs a decision before Module 1→2.

2. **N76's severity is understated.** "Harmless at runtime (`action=allow`)" is false: the controller **handed off on a 2× inflated number**, spending a hop and a session. Separately, and *not* observed: an inflated read on the gated implementer path could produce a spurious non-retryable HARD block.

Also: N76's "on the fix-marked path" is a **correlation, not a mechanism** — `ctx_observe_and_log` is identical on both paths. Fix dispatches simply tend to share a turn with an advisor consult.

## The fix

`usage_total` reads the last `type:"message"` iteration, falling back to the top-level fields when no `iterations` key is present.

**Provably a no-op on the majority path** — all 32,160 single-iteration turns in the corpus have top-level == `iterations[0]`, zero mismatches. The detector was positive-controlled with a planted mismatch before being trusted. Multi-iteration turns are ~4.5% of rows, inflate by **~2× (measured range 1.94×–2.00× across 822 turns; exactly 2.0 in none of them), scaling with the `message` iteration count** — a three-`message` turn measures ~2.9×, so the ratio is not a structural constant — and are **not advisor-specific** (`('message','message')` also occurs). *[CORRECTED 2026-07-31, `[task 2 fix]`: originally "inflate by **exactly 2.0×**", falsified by the report's own headline numbers (373139/189929 = 1.9646, 539691/270851 = 1.9926).]*

Stdlib-only verified by executing under bare `/usr/bin/python3`; py39 preserved.

**Tests:** 8 new differential tests + 7 fixtures (one carrying the real block verbatim). A mutation test turns exactly the 3 differential tests RED. Live replay of both real transcripts: `373139 → 189929`, `539691 → 270851`. Suites: 52 probe/gate, **649 unit** (641 + 8), regression 159/0/2 advisory, **e2e 15/15 including Step 13's live context gate**.

`context-probe.py` is **not** baselined — `grep -c 'context-probe' baseline.txt` → 0. No `check-hooks.sh --capture` needed.

### Controller-side independent verification

Re-run against the committed tree rather than accepted from the report: the peak block's iteration breakdown and the `268840 + 270851 = 539691` identity; the probe returning a corrected total on the controller's live transcript; execution under bare `/usr/bin/python3` (the hook path); and 52/52 probe+gate tests passing.

## Exclusion rule

**Not adopted.** The plan's ">50% against both neighbors" treats a code defect as data noise and cannot distinguish poison from a real peak. Post-fix rows need no rule; pre-fix rows should be **recomputed from the retained transcript** — exactly 1 of 80 rows was poisoned, and all 80 were matched, so a second would have been found. Fallback if transcripts rotate: ≈2.0× *and* returning to the prior level — with the stated residual that **zero compaction events were observed**, so that discriminator is untested against a real peak.

This is the controller-pre-authorized "explicitly state it cannot discriminate" branch, recorded in `deviations.md`.

## Source Files Read

- `~/projects/claude-custom/claude-codex-handoff/.worktrees/cmux-transport/docs/imp-plans/2026-07-29-cmux-transport/reports/context-observations.log` (read-only, cross-repo)
- `~/.claude/projects/-Users-araymond-projects-claude-custom-claude-codex-handoff--worktrees-cmux-transport/*.jsonl` (read-only)
- `skills/subagent-driven-development/scripts/context-probe.py`, `sdd-pre-dispatch-hook.sh` (`ctx_observe_and_log`, `ctx_probe_tokens`)
- `git show main:docs/process-improvement-findings/BACKLOG.md` and `git show main:docs/process-improvement-findings/2026-07-30-first-live-sdd-auto-spawn-run-analysis.md` (F7)
- `reports/context-summary.md`, `reports/task-002-controller-observation.md`
- `tests/ARaymond-hook-baseline/baseline.txt`

## CLAUDE.md Files Read

- Repo-root `CLAUDE.md` — no line-number citations in durable artifacts (constructs cited throughout); no hardcoded counts where a command computes them (each count is printed with its command).

## Deviations from Plan

1. **No exclusion rule adopted.** The plan's Step 3 branch (c) anticipated one; the root cause turned out to be a code defect, so the plan's own "if a probe bug, patch it" branch applies instead. The pre-authorized "cannot discriminate" statement is included rather than a rule.
2. **Five hypotheses tested where the plan listed three** — (d) and (e) were injected by the dispatch from the durable record and the controller's live observation.

## Self-Review Findings

- The no-op claim was positive-controlled before being trusted: a planted mismatch was verified to make the detector fire, so "zero mismatches across 32,160 turns" is a measurement rather than an absence.
- Hypothesis (a) was re-tested on the archived corpus rather than inheriting the controller's exclusion, as the dispatch explicitly required.
- The mechanism sentence's imprecision (sum over *message-type* iterations, not all iterations) was caught by the controller during verification, not by self-review. Recorded above.

### `[task 2 fix]` round, 2026-07-31 — closing both reviews

**Code.** `usage_total` now falls back to the top-level reading when the preferred `message` iteration sums to 0, closing the fail-open the quality review found: `_coerce_int` maps every non-int (floats included) to 0, so a malformed iteration made the probe return **0 while exiting 0** — a *successful measurement* of an empty context, read by the blocking gate as `tier=below action=allow`, which additionally resets an in-progress fallback streak.

**Every new test was mutation-verified — applied, confirmed RED, reverted, confirmed GREEN.** Baseline and restored state both 12 passed:

| Mutation | Target test | Result |
|---|---|---|
| revert the fallback-on-zero | `test_zero_summing_message_iteration_falls_back_to_top_level` | **RED** (1 failed) |
| `reversed(iterations)` → `iterations` | `test_three_message_iterations_scale_beyond_2x` | **RED** (3 failed — also the two pre-existing multi-iteration tests) |
| drop the `isinstance(iteration, dict)` guard | `test_non_dict_iteration_entries_are_skipped` | **RED** (1 failed) |
| `not isinstance(iterations, list)` → `iterations is None` | `test_falls_back_to_top_level[iterations-not-a-list.jsonl]` | **RED** (1 failed) |

**`null` was rejected for the non-a-list fixture; `5` was used.** The reviews offered them as equivalent. They are not: under the mutation, `iterations: null` makes `usage.get("iterations")` return `None`, the mutated guard fires, the function returns `None`, the probe falls back and still reads 250000 — **measured, the mutation SURVIVES at 12 passed.** Only a non-`None` non-iterable makes `reversed(5)` raise `TypeError` and the probe exit non-zero. The old string `"nope"` is preserved as a sibling fixture (`iterations-string.jsonl`), since iterable-but-not-a-list is a genuinely distinct shape.

**Restore discipline — and a near-miss worth recording.** The first mutation pass used `git checkout --` on the explicit path, per the standing "never `git stash`" rule. That silently reverted the *uncommitted fix itself*, because the file is tracked and the fix was not yet committed, contaminating the three subsequent mutation runs. Detected from the restored-state run showing `1 failed` instead of `12 passed`. The fix was re-applied and every mutation re-run against a **pristine copy saved outside the repo**. `git checkout --` is the right restore for committed baselines and the wrong one for in-flight work.

## Concerns

1. **An un-owned defect was surfaced and cannot be filed from here.** `~/.claude/bin/claude-ctx-check` carries the bug. **CONTROLLER CORRECTION 2026-07-31: this report also named the statusline, and that is FALSE — see the experiment recorded in `context-summary.md`; the statusline is harness-computed and measured correct.** For `claude-ctx-check` it is the same measurement, computed the same way. Both are outside this worktree (read-only), so no fix and no BACKLOG id could be allocated. This needs its own row at merge.
2. **Two committed controller artifacts now assert a falsified claim** (`task-002-controller-observation.md`, `context-summary.md`). They are the controller's to correct, and `transition-module.py` archives them at the Module 1→2 boundary.
3. **Zero compaction events were observed in either corpus**, so the "real peak" case the fallback discriminator is meant to handle remains hypothetical and untested.

### Added by the `[task 2 fix]` round, 2026-07-31

4. **Two fail-open residuals survive the fallback-on-zero, and were deliberately not coded around.** (a) If the `message` iteration *and* the top-level fields both sum to 0, the probe still returns 0 with exit 0. (b) A partially-float iteration such as `{"input_tokens": 180000.0, "output_tokens": 5}` sums to a truthy `5`, so no fallback fires and the gate reads a 5-token context. Neither is reachable without the stricter "fall back if any field is not an int" variant, which the quality review explicitly rejected and measured against 273 transcripts — `missing-fields.jsonl` shows legitimately omitted fields are a real shape. Both are unobserved in the corpus (0 of 34,139 `message` iterations malformed). Recorded rather than fixed; a version canary is the proper instrument.

5. **The differential parity test now certifies less than its name suggests.** Post-fix the probe and `claude-ctx-check` genuinely diverge on multi-iteration transcripts, and `test_differential_parity_with_ctx_check` uses a fixture with no `iterations` key — so it pins only the fallback path. Nothing pins the two implementations against each other on multi-iteration input, and nothing should until `claude-ctx-check` is fixed. Scoped explicitly in the SP1 doc's Parity paragraph.

6. **`deviations.md` row 79 still reads `Pending — [task 2 fix]`.** Its three prescribed corrections (drop the statusline from divergence 2; correct the SUM wording; label `iterations` version-unstable) are all now applied in `context-probe.py`. The register is the controller's to close — this round did not edit it.

7. **The occurrence sweep found a sixth SUM site the reviews did not name.** Both reviews' regexes keyed on the literal word "sum"; this report's own Implementation Summary said *"aggregate across those iterations"* — the same false generalization in different words. Corrected. The pattern now stands at **three sweeps, each finding more sites than the review that prompted it** (1/5, 3/5, 5/6). A lexical sweep is a floor, not a census.
