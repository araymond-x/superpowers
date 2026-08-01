---
schema_version: 1
task_id: 2
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/context-probe.py"
    description: "usage_total falls back to the top-level reading when the preferred type:'message' iteration sums to 0 — closes the gate fail-open. Docstring records the safety rationale, scopes the parity claim to claude-ctx-check alone (statusline falsified), and labels iterations an undocumented version-unstable shape. [ADDED to description 2026-07-31, round 2: also re-joined main()'s 'no usage block found' stderr message from two implicit-concatenation fragments into one line — undeclared at the time; verified byte-identical by execution, pre-fix and post-fix stderr compare equal.]"
  - path: "tests/unit/test_context_probe_iterations.py"
    description: "Four new mutation-verified test cases: fallback-on-zero, three-message-iteration ratio, non-dict entry skip, non-iterable iterations. Module docstring SUM claim corrected. [ADDED to description 2026-07-31, round 2: the whole file was also black-reformatted (tuple wrapping, parenthesized asserts, added blank lines) — undeclared at the time; semantically inert.]"
  - path: "tests/unit/fixtures/context-probe/iterations-message-no-fields.jsonl"
    description: "New — a message iteration with no token fields; the direct regression guard for the fail-open."
  - path: "tests/unit/fixtures/context-probe/iterations-message-triple.jsonl"
    description: "New — three message iterations (315406/107802 = 2.9258x); pins that the inflation ratio is not structurally 2.0."
  - path: "tests/unit/fixtures/context-probe/iterations-non-dict-entries.jsonl"
    description: "New — non-dict entries around a valid iteration; pins the isinstance-dict guard (mutation M6)."
  - path: "tests/unit/fixtures/context-probe/iterations-string.jsonl"
    description: "New — preserves the iterable-but-not-a-list shape the old not-a-list fixture held."
  - path: "tests/unit/fixtures/context-probe/iterations-not-a-list.jsonl"
    description: "Value changed from the string 'nope' to the non-iterable scalar 5, so it actually pins the isinstance-list check (mutation M5)."
  - path: "docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md"
    description: "Mechanism corrected to 'sum of the type:message iterations' at the opening summary and the N76 merge blockquote; 'exactly 2.0' replaced with the measured range at all sites incl. Guidance rule 2's discriminator; parity-test citation corrected to test_context_probe_sessionid.py."
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-002-implementer-report.md"
    description: "files_changed widened from 3 to 14 paths; 'exactly 2.0x' corrected; a sixth SUM site ('aggregate across those iterations') corrected. All edits marked [CORRECTED]/[ADDED] in place."
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-002-implementation.md"
    description: "SUM site corrected; the sentence garbled by the controller's d6678ad statusline edit repaired; canonical-report pointer added at top."
tests:
  written: 4
  passing: 4
  command: ".venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py -v"
  result: PASS
contract_compliance:
  - constraint: "context-probe.py stays stdlib-only (the hook invokes it without the venv)"
    status: compliant
    detail: "Executed under bare /usr/bin/python3 3.9.6 against a real transcript; exit 0. Imports unchanged."
  - constraint: "Python 3.9 compatibility for skills/subagent-driven-development/scripts/"
    status: compliant
    detail: "validate-all-skills.py PASS 159 / FAIL 0 / WARNING 2 (pre-existing soft word-count advisories)."
  - constraint: "Cross-repo read-only"
    status: compliant
    detail: "No writes outside this worktree."
  - constraint: "Do not touch BACKLOG.md"
    status: compliant
    detail: "The N76 replacement text was corrected inside the SP1 doc; BACKLOG.md is not in the changeset."
---

## Implementation Summary

Closes every finding from the Task 2 spec compliance review (FAIL) and adversarial code quality review (CHANGES_REQUESTED) in one consolidated round. Two commits: `2dbba48` (the fix round) and `48b409d` (a self-caught ratio reconciliation).

**The blocking code fix.** `usage_total` now falls back to the top-level reading when the preferred `type:"message"` iteration sums to 0. Previously it returned `_sum_fields(iteration)` unconditionally once any `message` entry was found, so a malformed or zero-summing iteration made the probe return 0 *while exiting 0* — presenting as a successful measurement of an empty context, which the gate reads as `tier=below action=allow`. Four new fixtures and four new test cases ship with it.

**Documentation corrections.** The falsified "top-level fields are their SUM" mechanism was corrected at six sites (five named by the reviews, one found by the round's own sweep). The falsified "exactly 2.0" inflation ratio was corrected at four sites, including Guidance rule 2, where it was offered as a discriminator *tighter than* the plan's ">50%" — and, being exact, matched none of the 822 real poisoned turns. The falsified statusline claim was dropped from `context-probe.py`'s docstring, its last surviving instance in committed code. `iterations` is now labeled an undocumented, version-unstable internal shape.

## Mutation verification

Each new test was verified to bite: mutation applied → RED → reverted → GREEN. Baseline and restored state both 12 passed.

| Mutation | Target test | Result |
|---|---|---|
| revert fallback-on-zero | `test_zero_summing_message_iteration_falls_back_to_top_level` | RED (1 failed) |
| `reversed(iterations)` → `iterations` | `test_three_message_iterations_scale_beyond_2x` | RED (3 failed) |
| drop `isinstance(iteration, dict)` | `test_non_dict_iteration_entries_are_skipped` | RED (1 failed) |
| `not isinstance(…, list)` → `is None` | `test_falls_back_to_top_level[iterations-not-a-list]` | RED (1 failed) |

## Deviations from Plan — three divergences from the dispatch, each with evidence

1. **`null` would NOT have killed the M5 mutation.** The dispatch offered `5` or `null` as equivalent replacements for the string fixture. Measured: with `iterations: null` the mutated guard still fires, the probe falls back, and the mutation **survives at 12 passed**. Only a non-iterable scalar makes `reversed(...)` raise. Used `5`; preserved the old string shape as a new sibling fixture `iterations-string.jsonl` rather than losing that coverage.

2. **The occurrence sweep found a SIXTH SUM site** that neither review caught — `task-002-implementer-report.md`'s Implementation Summary said *"aggregate across those iterations"*. Same falsehood, different words, invisible to both reviews' `sum`-keyed regexes. The sweep pattern was widened accordingly.

3. **Self-caught measurement error.** The round initially cited the quality reviewer's 2.97x as pinned by its own fixture, which actually measures 2.9258x — two independent measurements of the same phenomenon, not one. Reconciled in `48b409d`: the doc now says ~2.9x, names both measurements separately, and gives the recompute command.

## Self-Review Findings

- **Propagation-sweep pattern now three-for-three.** Each sweep has found more sites than the review that prompted it: 1 named / 5 found, 3 named / 5 found, 5 named / 6 found. The sweep is earning its place as a deliverable rather than a suggestion.
- **[CORRECTED 2026-07-31, round 2 — this item was wrong on its central point.]** It originally read: *"Two fail-open residuals survive and were deliberately not coded around: (a) iteration and top level both sum to 0; (b) a partial-float iteration summing to a truthy small value. Neither is closable without the stricter 'fall back if any field is not an int' variant, **which the quality review explicitly examined and rejected because it would spuriously fall back on iterations that legitimately omit a field.** Both are unobserved (0 of 34,139 `message` iterations). A version canary is the right instrument for this class."*

  Two corrections. **First, the basis was misstated:** round 1 of the quality review *reasoned* that rejection from `missing-fields.jsonl` — a **top-level** fixture — and generalized it to iteration behavior; it did not measure it. This report presented an inherited reasoned rejection as a measured one. **Second, the rejection does not hold.** Round 2 of the quality review retracted it against measurement: of 49,052 `message` iterations across 1,319 transcripts, **0 have a missing field, 0 a non-int field, 0 sum to zero, 0 are non-dict** — there is no population of legitimately-incomplete iterations to spuriously fall back on. Residual (b) was therefore closable and was a live fail-open: with `cache_read_input_tokens` renamed inside the iteration, a real archived 493,759-token block read `tokens=24234 source=probe tier=below action=allow` through the live hook. It is closed by the completeness guard shipped in the round-2 fix (`task-002-fix-round-2-implementer-report.md`). Residual (a) — iteration and top level both zero — is genuinely out of `usage_total`'s reach and remains open by design.
- **Process lesson.** The first mutation pass used `git checkout --` per the standing "never `git stash`" rule — which silently reverted the *uncommitted fix itself* and contaminated three runs. Caught because the restored-state run showed `1 failed` rather than the baseline. `git checkout --` is correct for restoring against a committed baseline and wrong for in-flight work; restore from a copy held outside the repo instead.

## Source Files Read

- `reports/task-002-spec-review.md`, `reports/task-002-quality-review.md`, `reports/task-002-implementer-report.md`, `reports/task-002-implementation.md`
- `docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md`
- `skills/subagent-driven-development/scripts/context-probe.py`, `sdd-pre-dispatch-hook.sh`
- `tests/unit/test_context_probe_iterations.py`, `test_context_probe_fixtures.py`, `test_context_probe_sessionid.py`, `test_context_gate*.py`

## CLAUDE.md Files Read

- Repo-root `CLAUDE.md` — no line-number citations in durable artifacts (constructs cited throughout); counts paired with the command that computes them; explicit-path staging, never `git add -A`; never `git stash` in this tree.

## Verification

- Probe + gate subset: **56 passed**
- Full unit suite: **653 passed**
- Regression / py39 gate: **PASS 159 / FAIL 0 / WARNING 2** (pre-existing advisories)
- Stdlib-only: `/usr/bin/python3` 3.9.6 → exit 0 against a real transcript
- Integration: **`E2E PIPELINE PASS - 15 steps`** — run after the code fix and before `48b409d`, which touched only two markdown files (verified: `git show 48b409d -- '*.py'` is empty), so it cannot have regressed the run
- `validate-report.py`: `COMPLETE`, `sections_missing: []`
- `git status --porcelain`: clean apart from hook-written logs and controller-owned review reports — every mutation reverted

## Concerns

1. **[CORRECTED 2026-07-31, round 2.]** Originally: *"Two fail-open residuals remain by design (above). Unobserved today, not closable without a variant the quality review **rejected on measured grounds**. The right instrument is the `iterations`-shape version canary, already recorded as a merge-time BACKLOG row."* The phrase "rejected on measured grounds" is false — round 1's rejection was **reasoned**, from a top-level fixture, and round 2 retracted it against 49,052 measured `message` iterations. One of the two residuals (a partially readable iteration summing to a small truthy value) was a live fail-open, not a by-design residual, and is now closed by the completeness guard. Only the both-sources-zero residual remains by design. The `iterations`-shape version canary is still the right instrument for the shape-drift class generally.
2. **`deviations.md` row 79 still reads `Pending — [task 2 fix]`.** All three of its prescribed corrections are applied. The register is the controller's to close; this round did not edit it, to avoid two writers on one artifact.
3. **The e2e suite was run before the final markdown-only commit.** Verified non-regressing by inspection (`git show 48b409d -- '*.py'` returns empty), not by a second run.
