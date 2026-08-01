# Task 2 — Quality Review, Round 3 (closing round)

**Verdict: APPROVED.** The round-2 BLOCKING finding is closed by executed evidence. No new blocking defects. Two MINOR advisories, neither requiring action before merge.

Scope: the `usage_total` completeness guard in `skills/subagent-driven-development/scripts/context-probe.py` and the tests/fixtures shipped with it (`fdd6b58`). The documentation sites closed by prior rounds were not re-swept, per the round's scope.

## 1. Harness validity (stated first, because it invalidated a run)

My first mutation battery reported all eight mutations "RED" against a pytest invocation whose glob was quoted into a single argument — pytest collected nothing and emitted `ERROR: file or directory not found`. **The positive control caught it**: a mutation that sets `iteration = None` outright must fail many tests, and instead produced the same vacuous output as every other row. Every verdict below is from the corrected re-run. This is the harness-is-broken-not-the-tests case the round's instructions warned about, and it fired.

Positive control on the corrected harness: **6 failed, 55 passed** — harness demonstrably discriminates.

## 2. Mutation battery — 8/8 RED

Baseline pinned at **61 passed** before starting (`.venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py -q`). Each mutation applied by a unique-anchor patcher that exits non-zero on anchor miss, so an inert mutation cannot score as SURVIVED. Restore verified at **61 passed** after every single mutation, with `git diff --stat` on the probe confirming zero dirty lines each time.

| # | Mutation | Result | Failing test(s) |
|---|---|---|---|
| M1 | revert fallback-on-zero → `return _sum_fields(iteration)` | **RED** | `test_all_zero_iteration_falls_back_to_top_level` (only) |
| M2 | `if total:` → `if total is not None:` | **RED** | `test_all_zero_iteration_falls_back_to_top_level` (only) |
| M3 | remove the completeness guard entirely | **RED** | `test_partial_iteration_one_surviving_field_falls_back`, `test_partial_iteration_renamed_field_falls_back`, `test_bool_in_an_int_slot_falls_back` |
| M4 | drop `and not isinstance(..., bool)` | **RED** | `test_bool_in_an_int_slot_falls_back` (only) |
| M5 | `all(...)` → `any(...)` | **RED** | the same three as M3 |
| M6 | `reversed(iterations)` → `iterations` | **RED** | `test_advisor_triple_is_not_double_counted`, `test_message_pair_is_not_double_counted`, `test_three_message_iterations_scale_beyond_2x` |
| M7 | drop the `type == "message"` filter | **RED** | `test_last_message_iteration_wins_when_advisor_is_last`, `test_falls_back_to_top_level[iterations-no-message-type.jsonl]` |
| **M8** | **over-rejection mutant** — a field counts as present only if truthy (`and bool(...)`) | **RED** | `test_legitimate_zero_field_is_not_over_rejected` (only) |

**M8 is mine, and the required set did not cover the guard's own failure mode.** The prompt's seven mutations include `all(...)` → `any(...)`, but that is an *under*-rejection weakening — it admits more iterations. Nothing in the required set makes the guard reject a *legitimate* iteration. M8 is that mutant, and exactly one test kills it: the over-rejection control. Without that test the guard could tighten into re-introducing the SP1 double-count and the suite would stay green.

Scope note: RED verdicts were measured against the 61-test probe+gate subset; all failures landed in `test_context_probe_iterations.py`. Restored tree: full unit suite **658 passed, 1 warning**; regression gate **PASS 159 / FAIL 0 / WARNING 2**.

## 3. The subsumption claim (Deviation 1) — accurate, verified two independent ways

The fix report's most interesting claim is that the guard *subsumes* the pre-existing `iterations-message-no-fields` fixture, so without the new all-zero test, M1 and M2 would have silently regressed RED→SURVIVED. Both halves hold:

- **Mechanism (decode).** That fixture's chosen iteration decodes to exactly `{"type": "message"}` — zero of four fields — so the guard's `all(...)` is False, `iteration` is nulled, and `if total:` is never reached for it.
- **Mutants.** M1 and M2 each fail **only** `test_all_zero_iteration_falls_back_to_top_level`. `test_zero_summing_message_iteration_falls_back_to_top_level` is **absent from both failure lists** — it passes under both, exactly as claimed.

The fourth fixture was required, not scope creep. The claim is correct as written.

## 4. Over-rejection does not fire

- **Legit `0` accepted.** `iterations-message-legit-zero-field.jsonl` decodes to all four fields as genuine ints with `cache_creation_input_tokens: 0`; the guard admits it and the probe returns the **iteration** value `182001`, not the `250000` top level. Differential, so it cannot pass via the fallback.
- **Unambiguous healthy multi-iteration control, built fresh from the real corpus.** The prompt correctly noted the controller's control was ambiguous. I located a real transcript (`agent-af935363b5ed6f306.jsonl`) whose last usage block has two complete `message` iterations with sums `130450` and `135637`, top level `266087` — three distinct values. The probe returns **135637**, the last iteration. Correct value, chosen unambiguously. (The committed `iterations-message-pair` / `-triple` fixtures are also unambiguous — all iterations complete, last differs from every other and from top level.)
- **Corpus unmoved.** Loading `b517fe8` and `HEAD` side by side and comparing `find_latest_total` over `sorted((Path.home()/".claude"/"projects").rglob("*.jsonl"))`:
  `transcripts=1325 identical=1252 no-usage=73 DIFFER=0 errors=0`
  Reproduced independently. The count is 5 higher than the fix round's 1,320 because the corpus grows; DIFFER=0 is the load-bearing figure and it matches.
- **The over-rejection population is empirically empty.** Across the same corpus: **49,540** `type:"message"` iterations, **0** guard-incomplete, **1,015** carrying a legitimate `0` in at least one field, **0** carrying a negative. Independently reproduces the fix report's 49,222 / 0 / 1,010 on a slightly larger corpus.

## 5. Fixture honesty — all five clean

Every new fixture decoded programmatically; each matches its name *and* the assertion it feeds:

| Fixture | Decoded chosen iteration | Guard | Pre-guard return |
|---|---|---|---|
| `one-int-field` | `{type, input_tokens: 1}` | incomplete | `1` |
| `renamed-field` | three ints + `cache_read_tokens` (renamed) | incomplete | `1902` |
| `bool-field` | `input_tokens: true` + three ints | incomplete | `181900` |
| `legit-zero-field` | four genuine ints, one a real `0` | **complete** | `182001` (returned) |
| `all-zero-fields` | four genuine int `0` | **complete** | `0` → `if total:` rescues |

Round 1's `not-a-list`-holding-a-string pattern is absent. Round 2's crash-path pattern is absent: under M3 the three guard tests fail with **value assertions** exposing the exact pre-guard wrong number — `assert 1 == 250000`, `assert 1902 == 250000`, `assert 181900 == 250000` — not with an exception.

## 6. Attacks on the guard itself

Twelve hand-built shapes driven through the shipped probe (top-level legacy = 250000 in all):

**Found nothing (correct fallback to 250000):** all-float fields, string-numeric fields, explicit JSON nulls, a nested-dict in an int slot, `iterations` as a dict rather than a list, non-string `type`. **`iteration.get(f)` cannot raise** — `_last_message_iteration` returns only objects that passed its `isinstance(iteration, dict)` test; confirmed by construct and empirically by the nested-dict and dict-`iterations` cases both exiting 0. **`FIELDS` ordering** is irrelevant to `all()` and `sum()` — nothing. **Very large ints** — Python has no overflow; `10**30` round-trips exactly. **Iteration exceeding the top level** returns the larger iteration value, which is the fail-safe direction. **`cancels-to-zero`** (fields summing to 0 by cancellation) correctly falls back.

Two shapes produced findings, both MINOR:

### [MINOR] Advisory A — the docstring's safe-degradation claim doesn't cover additive field drift

`usage_total`'s docstring states that an `iterations` shape change the guard does not recognize "degrades to the LEGACY TOP-LEVEL READING," and that this fails safe because a wrong-HIGH reading can only over-block.

That is true for the shapes the guard *does* recognize — absent field, non-int, bool. It does not extend to **additive** drift: if a future Claude Code adds a new token field, all four `FIELDS` remain present as ints, the guard admits the iteration, and the probe returns a sum missing the new field — a wrong-LOW reading that never touches the top-level path. My `extra-unknown-field` probe returns `181902` while the iteration carries 700,000 further tokens in unrecognized keys.

**Stated precisely, because the obvious reading is wrong:** this is *not* the guard routing to somewhere worse. `_sum_fields(usage)` iterates the same `FIELDS`, so the top-level fallback is blind to a new field too. The real property is that **`FIELDS` is a closed list on both paths**, which the docstring's safe-degradation framing doesn't cover. A reader who checks the fallback path after reading a stronger claim will conclude the reviewer misread the code.

**Not live today.** The only extra key in real data is `cache_creation`, and it is a pure breakdown, not additive: across 20,027 sampled iterations, `sum(cache_creation.*) == cache_creation_input_tokens` with **0** mismatches (values are `ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens`). No additive field exists in 49,540 measured iterations.

**Fix (optional):** one clause scoping the claim — the safe-degradation property holds for fields that go absent or non-int, and neither path reads outside `FIELDS`, so an additive field is invisible to both.

### [MINOR] Advisory B — negatives are admitted by type but contained at the hook boundary

The guard tests `isinstance(..., int)`, which is a *type* check, not a domain check, so a negative value is admitted. The probe then emits a negative total with rc=0 (`-498098` on my `negative-cache-read` shape).

**The consumer rejects it.** `ctx_probe_tokens` in `sdd-pre-dispatch-hook.sh` gates on `[ "$rc" -eq 0 ] && [[ "$out" =~ ^[0-9]+$ ]]`, so a negative never reaches the tier comparison — it routes to the byte-proxy with `CTX_SOURCE="byte-proxy"`, which is the advisory path that escalates to a block on the fallback streak. **Fail-safe, and contained.** Zero negatives exist in the 49,540 measured iterations.

Optional one-token tightening if the probe's own output contract matters independently of its sole consumer: add `and iteration.get(f) >= 0`. **Not required** — the boundary check already holds.

## 7. Attacks that found nothing (explicit, as asked)

`iteration.get(f)` raising; `FIELDS` ordering; very large ints; floats; string-numerics; explicit nulls; nested-dict fields; non-list `iterations`; non-string `type`; iteration-exceeds-top-level; cancellation-to-zero; fixture-name dishonesty; crash-path test bites; corpus regression; suite regression.

## Tree state

`git status --porcelain` shows only `reports/.dispatch-log` and `reports/context-observations.log` — both hook-written, both already dirty when the round started. The probe and `tests/` are byte-identical to `016e027`. All mutation work ran in a fresh scratchpad subdirectory; nothing was committed, and `git stash` was never used.

## Bottom line

Closed, nothing new blocking. The three residual shapes from round 2 now fall back and BLOCK; the guard's own failure mode is pinned in both directions (M3/M4/M5 catch under-rejection, M8 catches over-rejection); the subsumption claim behind the fourth fixture is accurate on both halves; the corpus is unmoved at DIFFER=0 across 1,325 transcripts. The two advisories are documentation-scope and containment-verified respectively — neither blocks merge.
