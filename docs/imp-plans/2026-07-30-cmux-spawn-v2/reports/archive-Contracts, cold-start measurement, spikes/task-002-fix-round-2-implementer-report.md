---
schema_version: 1
task_id: 2
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/context-probe.py"
    description: "usage_total gains the completeness guard — the preferred type:'message' iteration is discarded whole unless all four FIELDS are present on it as genuine ints (bool excluded). Closes the small-but-truthy partial-corruption fail-open that `if total:` left open. Docstring records what the guard trades (degradation to the known-wrong-HIGH legacy reading, deliberate), why `if total:` survives it, and scopes the never-mistake-a-0 principle to the preferred-iteration source. Module docstring's ~3x corrected to ~2.9x with the always-strictly-below-N property and its mechanism."
  - path: "tests/unit/test_context_probe_iterations.py"
    description: "Five new tests: one-surviving-int-field, renamed field, bool in an int slot, the over-rejection control (a legitimate 0 must be ACCEPTED), and the all-zero iteration that keeps `if total:` alive. Module docstring records the completeness requirement; the existing zero-summing test's docstring corrected — it is now caught by the guard, not by `if total:`."
  - path: "tests/unit/fixtures/context-probe/iterations-message-one-int-field.jsonl"
    description: "New — a message iteration with ONE surviving int field. Pre-guard this returned 1 and the gate allowed."
  - path: "tests/unit/fixtures/context-probe/iterations-message-renamed-field.jsonl"
    description: "New — cache_read_input_tokens renamed inside the iteration, other three intact. The realistic partial-shape-drift case; pre-guard this returned 1902."
  - path: "tests/unit/fixtures/context-probe/iterations-message-bool-field.jsonl"
    description: "New — a bool in an int slot. Pins the `not isinstance(..., bool)` clause, which no other fixture kills."
  - path: "tests/unit/fixtures/context-probe/iterations-message-legit-zero-field.jsonl"
    description: "New — OVER-REJECTION CONTROL. cache_creation_input_tokens is a legitimate int 0; the guard must accept the iteration and the probe must return 182001, not the 250000 top-level value."
  - path: "tests/unit/fixtures/context-probe/iterations-message-all-zero-fields.jsonl"
    description: "New — all four fields present as int 0. The one shape the guard admits but cannot use; the only remaining fixture that keeps `if total:` from looking like dead code."
  - path: "docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md"
    description: "793/822 reconciled as one population measured twice, with a provenance table and a verified recount command; the same reconciliation carried into the N76 merge blockquote. New 'Completeness, not truthiness' subsection documents the guard, what it trades and its over-rejection control, with a verified corpus-differential command and a live-hook before/after table (pre-guard rc=0 tokens=24234 allow vs guarded rc=2 tokens=493759 block) plus the note that the block is single-iteration, so the fail-open reached the majority path. Opening 'each is paired with the command that recomputes it' promise replaced with an accurate two-group classification. Guidance rule 2 and the Files-changed table updated."
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-002-fix-implementer-report.md"
    description: "Self-Review item and Concern 1 corrected with [CORRECTED 2026-07-31] markers preserving the original wording — round 1's rejection of the completeness variant was REASONED (from a top-level fixture), not measured, and round 2 retracted it against 49,052 measured iterations. Two undeclared round-1 content changes (black reformat of the test file; the re-joined main() stderr string) added to their files_changed descriptions."
tests:
  written: 5
  passing: 5
  command: ".venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py -q"
  result: PASS
contract_compliance:
  - constraint: "context-probe.py stays stdlib-only (the hook invokes it without the venv)"
    status: compliant
    detail: "Every new fixture executed under bare /usr/bin/python3 3.9.6, plus a 320,670-token real transcript with --json, all exit 0. Imports unchanged (argparse/json/os/sys/pathlib/typing)."
  - constraint: "Python 3.9 compatibility"
    status: compliant
    detail: "Parses and runs under 3.9.6; no PEP-604 unions or builtin generics added. Regression gate PASS 159 / FAIL 0 / WARNING 2."
  - constraint: "Cross-repo read-only"
    status: compliant
    detail: "~/.claude/projects and ~/.claude/bin were read only. All writes are inside this worktree."
  - constraint: "Do not touch BACKLOG.md"
    status: compliant
    detail: "The N76 replacement text was corrected inside the SP1 doc; BACKLOG.md is not in the changeset (git diff --name-only b517fe8..HEAD carries no BACKLOG.md)."
---

## Implementation Summary

Closes the round-2 quality review's single BLOCKING finding plus its four documentation items. Three commits: `fdd6b58` (the guard, its tests, and all four doc items), `caac3ce` (a self-caught misclassification in the item-4 rewrite), and `2779918` (the live-hook before/after table, added after re-measuring the review's inherited 24,234 figure myself).

**The blocking fix.** `usage_total` now requires the preferred `type:"message"` iteration to be **complete** — all four `FIELDS` present as genuine ints, `bool` excluded — before trusting it. The reviewer's measured form shipped verbatim. Previously `if total:` was a truthiness test, so it rescued only an iteration summing to exactly zero; an iteration with any surviving int field was returned as a measurement. The review proved that end-to-end on a real archived 493,759-token block that read `tokens=24234 source=probe tier=below action=allow` through the live hook with `cache_read_input_tokens` renamed. `if total:` is retained and still load-bearing — it covers the all-fields-present-all-zero shape the guard admits.

**One addition beyond the dispatch's three required tests, and it was required.** See Deviation 1: the guard *subsumes* the existing `iterations-message-no-fields` fixture, so shipping the dispatch's three tests alone would have silently regressed two mutations (the review's M3 and M7) that the previous round paid for. Measured, not assumed — see Self-Review.

**Documentation.** 793/822 reconciled as one population measured twice, with a provenance table and a verified recount command, at both the prose site and the N76 blockquote that lands in `main`. `~3x` corrected to `~2.9x` with the always-strictly-below-N property. The SP1 doc's "each is paired with the command that recomputes it" promise softened to an accurate classification. The prior fix report's misstated rejection basis corrected in place.

## Source Files Read

- `reports/task-002-quality-review-round-2.md`, `reports/task-002-spec-review-round-2.md`, `reports/task-002-fix-implementer-report.md`
- `skills/subagent-driven-development/scripts/context-probe.py`
- `tests/unit/test_context_probe_iterations.py`; all 20 fixtures under `tests/unit/fixtures/context-probe/` decoded programmatically
- `docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md`

## CLAUDE.md Files Read

- Repo-root `CLAUDE.md` — no line-number citations in durable artifacts (constructs cited throughout: `usage_total`, `_last_message_iteration`, `_coerce_int`, `if total:`, named tests and fixtures); counts paired with the command that computes them, and where a figure has no command the doc now says so rather than implying one; explicit-path staging, never `git add -A`; never `git stash` in this tree.

## Deviations from Plan

1. **Two fixtures added beyond the dispatch's three, one of them mandatory.** The dispatch named three tests: one-surviving-int-field, renamed field, and the over-rejection control.

   **`iterations-message-all-zero-fields.jsonl` is not optional.** The dispatch says to keep `if total:` for the all-fields-present-all-zero case, but after the guard **no committed test reached that branch**. The existing `iterations-message-no-fields` fixture carries *zero* of four fields, so the guard nulls the iteration before `if total:` is evaluated. Measured rather than reasoned: applying mutation D (`return _sum_fields(iteration)` unconditional — the review's M3) and mutation E (`if total is not None:` — the review's M7) each fails **only** `test_all_zero_iteration_falls_back_to_top_level`, and `test_zero_summing_message_iteration_falls_back_to_top_level` **passes under both**. Without the new fixture, M3 and M7 would have gone from RED to SURVIVED — a silent regression of coverage the previous round paid for, in exactly the "clause with no killing test" class round 1's Finding 4 raised.

   **`iterations-message-bool-field.jsonl` closes the third clause.** The guard has three clauses; the dispatch's fixtures kill two. Dropping `not isinstance(..., bool)` admits an iteration with `True` in an int slot, `_coerce_int` maps it to 0, the total is still truthy, and the probe returns an *undercount* — 181,900 against a 250,000 top level. Mutation B confirms this is caught by nothing else in the suite.

2. **The reviewer's guard shipped verbatim, including the double-negative `not all(...)` shape.** A named helper would read better, but the form was measured end-to-end by the reviewer (zero corpus differences, suite unchanged, three residual shapes closed, positive control preserved) and transcribing it exactly keeps the next round's verification cheap. Recorded as a deliberate style concession, not an oversight.

3. **A second commit for a self-caught error.** My first rewrite of the SP1 doc's opening classified the 1.9427/1.9979 ratio band as "session-specific". It is not — it is a corpus measurement that simply has no paired command. Fixing item 4 by writing a *different* inaccurate sentence would have reproduced the class the item exists to close. Corrected in `caac3ce`, with each imported figure attributed to the round that measured it.

## Self-Review Findings

### Mutation battery — 5/5 RED, restore verified at 61 every time

Run **after** committing the fix (`fdd6b58`), so `git checkout -- <path>` restores the guard rather than reverting in-flight work — the exact contamination the previous round documented in its own Self-Review. Baseline and every restore re-verified at exactly `61 passed` before the next mutation was applied.

| # | Mutation on `context-probe.py` | Result | Failing tests |
|---|---|---|---|
| A | drop the completeness guard entirely | **RED** | 3 failed: one-surviving-field, renamed-field, bool-in-int-slot |
| B | drop the `not isinstance(..., bool)` clause | **RED** | 1 failed: `test_bool_in_an_int_slot_falls_back` |
| C | treat a field as absent unless truthy (`and bool(...)`) — the over-rejection mutant | **RED** | 2 failed: `test_legitimate_zero_field_is_not_over_rejected`, bool-in-int-slot |
| D | revert fallback-on-zero (`return _sum_fields(iteration)`) — the review's M3 | **RED** | 1 failed: `test_all_zero_iteration_falls_back_to_top_level` |
| E | `if total:` → `if total is not None:` — the review's M7 | **RED** | 1 failed: `test_all_zero_iteration_falls_back_to_top_level` |

**The over-rejection control's result, called out because the dispatch asked for it specifically.** `test_legitimate_zero_field_is_not_over_rejected` passes on the shipped guard — the probe returns the **iteration** value `182001`, not the `250000` top-level fallback — and goes **RED** under mutation C, the only mutation that makes the guard treat a legitimate `0` as absent. The assertion is differential (top level 250,000 ≠ iteration 182,001), so it cannot pass by way of the fallback path. The guard's own failure mode is therefore pinned in both directions: A/B catch under-rejection, C catches over-rejection.

**The M3/M7 measurement behind Deviation 1.** Mutations D and E fail `test_all_zero_iteration_falls_back_to_top_level` and **do not** fail `test_zero_summing_message_iteration_falls_back_to_top_level`. That is the empirical proof that the guard subsumes the old fixture's branch, and the justification for the fourth fixture being required rather than scope creep.

### Live-hook proof — the review's 24,234 reading re-measured, and closed

The round-2 review's blocking evidence was a **live-hook** measurement, and this fix cites its 24,234 figure in three durable artifacts (the `usage_total` docstring, the SP1 doc, and the N76 text that lands in `main`). Carrying an inherited figure as the justification for a gate change without re-measuring it is the same class this whole round exists to close, so I drove both sides myself.

Located the exact block by value across the corpus: `~/.claude/projects/-Users-araymond-projects-big-contingent-talent/56b483bc-39c6-4eff-820b-1e3fb105d522.jsonl`, top-level total **493,759**. Truncated the transcript at that entry, produced a second copy with `cache_read_input_tokens` renamed **inside the iteration only**, and drove both through the live `sdd-pre-dispatch-hook.sh` on the implementer new-task path via `sdd_test_helpers.setup_full_sdd_workspace`:

| probe | input | rc | observation row |
|---|---|---|---|
| pre-guard (`b517fe8`) | control, unmodified | **2** | `tokens=493759 source=probe tier=hard action=block` |
| pre-guard (`b517fe8`) | iteration `cache_read` renamed | **0** | `tokens=24234 source=probe tier=below action=allow` |
| **shipped (guarded)** | control, unmodified | **2** | `tokens=493759 source=probe tier=hard action=block` |
| **shipped (guarded)** | iteration `cache_read` renamed | **2** | `tokens=493759 source=probe tier=hard action=block` |

The review's figure reproduces exactly — `rc=0 tokens=24234 … action=allow` — and the guard closes it to `rc=2 … action=block` while leaving the control unchanged. The pre-guard probe was swapped in with `git show b517fe8:… >` and restored with `git checkout --` against the committed baseline; the restore was re-verified at `61 passed`.

**One thing this measurement adds that the review did not state.** That block's `iterations` carries a **single** `message` iteration — the majority path. So the partial-corruption fail-open was never confined to the multi-iteration turns SP1 was about: it reached every turn the probe reads, which is the whole corpus. The guard's scope is correspondingly wider than the divergence that motivated it.

### Corpus differential — 0 differences

```
transcripts=1320 identical=1247 no-usage=73 DIFFER=0 errors=0
```

Baseline is `b517fe8` (shipped-vs-guarded), **not** `e7034bc` (which is the pre-SP1 comparison the reviewer used for a different question). Loaded both modules side by side with `importlib.util.spec_from_file_location` and compared `find_latest_total` over `sorted((Path.home()/".claude"/"projects").rglob("*.jsonl"))`. The command is committed into the SP1 doc under "Completeness, not truthiness" and was executed verbatim from that text, printing `identical: 1247 no-usage: 73 DIFFER: 0`. This independently confirms the reviewer's zero-difference measurement on a corpus one transcript larger than theirs (1,320 vs 1,319).

### No-collateral proof, stronger than "the suite still passes"

Decoded every fixture's *chosen* `message` iteration and tested it against the guard before writing any test. **Exactly one** existing fixture has an incomplete chosen iteration — `iterations-message-no-fields.jsonl`, which already asserts the top-level fallback, so the guard cannot change its outcome. Every other fixture with a chosen iteration (`advisor-last`, `advisor-triple`, `message-pair`, `message-triple`, `non-dict-entries`, `single`) is complete and unaffected. That is why 56 became 61 with no test rewritten.

### Empirical backing for the over-rejection control

Across the same 1,320 transcripts, **49,222** `type:"message"` iterations: **0** incomplete (no missing field, no non-int field) and **1,010** carrying a legitimate `0` in at least one field. So the population the guard could wrongly reject is real and four figures large, while the population round 1 feared it would wrongly reject — legitimately-incomplete iterations — is empirically empty. This is the measurement that retires round 1's reasoning, and it reproduces the round-2 review's finding independently.

### Docstring exposure closed

The round-2 review noted (as an out-of-scope observation) that the docstring asserted a general principle — *"A `0` from a preferred-but-unusable source must never be mistaken for a measurement"* — that the code applies to the iteration source and not the top-level one. Since I rewrote that docstring, an unqualified survival would have become mine. It is now explicitly scoped to the **preferred-iteration** source, with the top-level exemption named as pre-existing legacy behavior left unchanged. The top-level behavior itself is untouched — still out of scope.

## Concerns

1. **The guard's degradation target is the bug this feature exists to fix, and that is the intended design.** An unrecognized `iterations` shape now falls to the legacy double-counting reading. Documented in three places (the `usage_total` docstring, the SP1 doc's "What the guard trades", and the N76 merge text) because a future reader who finds the probe over-reporting after a Claude Code upgrade needs to recognize this as the designed failure direction, not a new bug. The right long-term instrument is still an `iterations`-shape version canary that surfaces the drift instead of silently absorbing it — unchanged from the previous round's recommendation.

2. **One fail-open residual remains, and it is genuinely outside `usage_total`'s reach.** If the iteration *and* the top-level fields are both unreadable, `_sum_fields(usage)` returns 0, the probe exits 0, and the hook logs `tokens=0 source=probe tier=below action=allow`. This is **pre-existing legacy behavior** on the top-level path, unchanged by SP1 or by either fix round, and the round-2 review scoped it out explicitly. I confirmed it still holds: the newest transcript in `~/.claude/projects` currently reads `total_tokens: 0` with exit 0. A real controller session cannot have 0 accumulated tokens, so `0` is arguably never a measurement — but fixing that is a change to the legacy fallback contract, not to this task.

3. **`deviations.md` row 79 still reads `Pending — [task 2 fix]`** (carried from the previous round, and re-raised by the round-2 spec review as its Advisory 5). All three of its prescribed corrections remain verifiably applied. Not edited here, same reason as last round: it is the controller's register and two writers on one artifact is worse than a stale cell.

4. **The e2e run predates the two documentation commits.** `bash tests/integration/sdd-e2e-test.sh` printed `E2E PIPELINE PASS - 15 steps composed correctly` after `fdd6b58`, the only commit carrying code. `caac3ce` and `2779918` each touch one markdown file (`git show <sha> --stat` → 1 file, `.md`), so neither can regress the pipeline. Stated rather than glossed; not re-run.

5. **This report is left untracked**, matching the previous round's convention — the controller commits `reports/` (that is what `b517fe8` did). The three code/doc commits are `fdd6b58`, `caac3ce` and `2779918`.

## Verification

Every figure below is output I read, not a claim.

| Check | Command | Result |
|---|---|---|
| Probe + gate subset | `.venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py -q` | **61 passed** (56 baseline + 5 new) |
| Full unit suite | `.venv/bin/python3 -m pytest tests/unit/ -q` | **658 passed, 1 warning** in 149.34s |
| Regression / py39 gate | `python3 tests/ARaymond-skill-regression/validate-all-skills.py` | **PASS: 159  FAIL: 0  WARNING: 2** — `Result: PASS (with warnings)` (the two pre-existing soft word-count advisories) |
| Integration | `bash tests/integration/sdd-e2e-test.sh` | **`E2E PIPELINE PASS - 15 steps composed correctly`** |
| Stdlib-only | `/usr/bin/python3 skills/.../context-probe.py --transcript …` (no venv) | 3.9.6; all five new fixtures + `advisor-triple` (189929) and `message-triple` (107802) exit 0; a 320,670-token real transcript returns valid `--json` |
| Corpus differential | pre/post `find_latest_total` over 1,320 transcripts, baseline `b517fe8` | **`identical=1247 no-usage=73 DIFFER=0 errors=0`** |
| Mutation battery | 5 mutations, each reverted with `git checkout --` against the **committed** baseline | **5/5 RED**, restore `61 passed` 5/5 |
| Live hook, real 493,759 block | `sdd-pre-dispatch-hook.sh` on the implementer new-task path, pre-guard vs shipped | pre-guard renamed-field: **`rc=0 tokens=24234 … action=allow`** (the review's figure, reproduced); shipped: **`rc=2 tokens=493759 tier=hard action=block`**; controls block on both |
| Doc commands run verbatim | the SP1 doc's new recount block and corpus-differential block | `multi-iteration: 825 multi-message: 825`; `identical: 1247 no-usage: 73 DIFFER: 0` |
| Prior report still validates | `validate-report.py --report-file …/task-002-fix-implementer-report.md` | `COMPLETE`, `sections_missing: []` |
| Tree state | `git status --porcelain` | only `reports/.dispatch-log` and `reports/context-observations.log` modified — both hook-written. Every mutation reverted; no source or fixture file dirty. |
