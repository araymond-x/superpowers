# Task 2 Code Quality Review — SP1 context-probe iteration fix

**Verdict: CHANGES_REQUESTED** — one BLOCKING finding, two IMPORTANT, three MINOR. The root-cause work is correct and the fix's central mechanism is right; what fails is a fail-open path the fix newly creates in a blocking gate, and two documented claims that are false as measured.

Everything below was verified by execution unless labeled otherwise. Attacks that found nothing are listed at the end so the next round need not re-run them.

---

## Execution scope, stated up front

I ran: the 8-file context subset (`test_context_probe*.py` + `test_context_gate*.py`, **52 passed** at restored HEAD), six mutations of `context-probe.py` against that subset, live `sdd-pre-dispatch-hook.sh` invocations through `sdd_test_helpers.setup_full_sdd_workspace`, 18 synthetic edge fixtures under `/usr/bin/python3` (the hook's bare interpreter), and two corpus sweeps over `~/.claude/projects` (120-largest for shape statistics, all 273 transcripts for the differential).

I did **not** re-run the full unit suite or `tests/integration/sdd-e2e-test.sh`. That evidence (`E2E PIPELINE PASS - 15 steps`, `validate-all-skills.py` PASS 159/0/2) is **inherited from the spec review** and is labeled as inherited, not corroborated.

Tree state: `git status --porcelain` is byte-identical to the baseline I captured before the first mutation — the two modified logs (`.dispatch-log`, `context-observations.log`) carry the controller's own 22:10 spec-review and 22:19 quality-review dispatch rows, written by the live hook before my work began. No `git stash` was used; every mutation was reverted with `git checkout --` on the explicit path.

---

## FINDING 1 — [BLOCKING] `usage_total` returns a silent `0` when the chosen `message` iteration is malformed, disabling the gate

**Construct:** `usage_total` in `skills/subagent-driven-development/scripts/context-probe.py`, specifically `return _sum_fields(iteration if iteration is not None else usage)`.

Once `_last_message_iteration` finds *any* `type: "message"` entry, `usage_total` returns `_sum_fields` of that entry **unconditionally**. `_coerce_int` maps every non-int (string, `null`, list, dict, **float**) and every bool to `0`. So a `message` iteration whose four token fields are absent or non-int makes `usage_total` return `0` — **discarding a well-formed top-level reading that the pre-fix code would have used.**

### Evidence — probe level

Pre-fix (`git show a4dc986:…`) vs. shipped HEAD, both under `/usr/bin/python3`, on a block whose top-level fields sum to 250,000:

| fixture (`iterations` value) | pre-fix | shipped |
|---|---|---|
| `[{"type":"message"}]` — no token fields | 250000 | **0** |
| `[{...all four = 0}]` | 250000 | **0** |
| `[{"input_tokens":"12345", "output_tokens":null, …}]` | 250000 | **0** |
| `[{...all four = true}]` (booleans) | 250000 | **0** |
| `[{"input_tokens":180000.0, …}]` — **floats, valid JSON numbers** | 250000 | **0** |
| `[{good message}, {"type":"message"}]` — last-wins picks the bad one | 250000 | **0** |

### Evidence — live hook, positive-controlled in both directions

A transcript whose top-level usage sums to **451,000** (over `HARD=400000`), driven through the real `sdd-pre-dispatch-hook.sh` on the implementer new-task path:

| case | rc | observation row |
|---|---|---|
| control: `hard.jsonl` (existing fixture) | **2** (blocks) | — |
| control: same 451k block, **no** `iterations` key | **2** (blocks) | — |
| defect: same 451k block, `iterations: [{"type":"message"}]` | **0** | `tokens=0 source=probe tier=below action=allow` |
| defect: same 451k block, float token fields | **0** | `tokens=0 source=probe tier=below action=allow` |

The probe **exits 0** and prints `0`, so `ctx_probe_tokens`'s `[ "$rc" -eq 0 ] && [[ "$out" =~ ^[0-9]+$ ]]` succeeds: `CTX_T=0`, `CTX_SOURCE=probe`, `ctx_tier 0` → `below`, `action=allow`. **This presents as a successful measurement, which is strictly worse than a probe failure** — a failure routes to the byte-proxy and eventually to the K-streak block; a "successful" `0` routes to `allow` indefinitely.

### It also disarms the fallback-streak escalation — verified, not reasoned

`ctx_fallback_streak` counts *trailing consecutive* `action=fallback` rows, so a poisoned `action=allow` row **resets an in-progress streak to zero**. With two prior `action=fallback` rows seeded in `context-observations.log`:

- control (unreadable transcript → 3rd consecutive fallback): **rc=2**, escalation block fires.
- poisoned transcript: **rc=0**, log ends `tokens=0 source=probe tier=below action=allow`. Streak disarmed.

A session that is genuinely degrading and then hits one malformed-iteration transcript loses its escalation counter.

### Why this is BLOCKING despite zero sightings

Corpus sweep over the 120 largest transcripts (33,368 usage rows, **34,139** `message` iterations): **0** with a missing/non-int field, **0** summing to zero, **0** non-dict iteration entries. So this is unobserved today.

It is blocking anyway because this change **creates a fail-open path that did not exist pre-fix**, in a blocking safety gate, keyed on a shape this feature's own `deviations.md` row 2 calls *"an undocumented, version-unstable internal shape,"* citing Claude Code's own *"the transcript entry format is internal to Claude Code and changes between versions, so it's not a stable contract."* **Zero occurrences today is precisely the reassurance a version-unstable shape cannot give.** The corrupted row is also written with `source=probe` — the exact rows the N43 threshold tuning consumes.

### Fix — verified in both directions

```python
iteration = _last_message_iteration(usage)
if iteration is not None:
    total = _sum_fields(iteration)
    if total:
        return total
return _sum_fields(usage)
```

I applied this and measured:

- All six zero-shapes above → **250000** (falls back to the top-level reading).
- Existing suite: **40 passed** (probe + gate subset).
- Across **all 273** transcripts under `~/.claude/projects`: **0 differences** from the shipped version. The fallback-on-zero is a pure safety net, not a behavior change.

Do **not** use the stricter "fall back if any of the four fields is not an int" variant — it would spuriously fall back on a `message` iteration that legitimately omits a field, and `missing-fields.jsonl` shows omitted fields are a real shape at top level.

Ship a fixture + test with it (a `message` iteration with no token fields, asserting the top-level value), or the next mutation round finds this again.

Note, without reopening it: the spec review correctly ruled the `iterations`-shape **version canary** out of scope. This fix is the cheap partial substitute — with the zero-fallback in place, a future shape change degrades to the legacy top-level reading instead of silently returning `0`.

**Attribution:** implementer (`529f283`).

---

## FINDING 2 — [IMPORTANT] Attack (iv): the false "SUM" mechanism survives at **two** sites the spec review did not name — one of them committed code

The spec review named three sites (SP1 doc opening summary, SP1 doc N76 blockquote, `context-probe.py` module docstring) and I did not re-litigate them. Sweeping every file in `git diff --name-only a4dc986..HEAD` for `their \*?sum|are their sum|SUM, so|sum of the iterations|fields are their` returns two more:

1. **`tests/unit/test_context_probe_iterations.py`, module docstring** — *"Claude Code records them in `message.usage.iterations` and the TOP-LEVEL `usage` fields are their SUM."* This is **committed code**, implementer-owned, and it is not in the deferred-fix row's scope.
2. **`docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-002-implementation.md`** — *"`message.usage.iterations` and the **top-level** `usage` fields are their **sum**."*

Both introduced by `529f283` (implementer), confirmed with `git log -S`.

The claim is false, re-measured independently across the corpus: over **822** multi-`message` turns, top-level `== sum(message iterations)` in **822/822**, and `== sum(ALL iterations)` in only **18/822** (exactly the `('message','message')` turns, where the two are trivially the same set). The 804 `('message','advisor_message','message')` turns are counterexamples.

Pattern check: **3 sites named / 5 found** — the same one-named/five-found and three-named/five-found shape this feature has hit twice before. Add both to the `[task 2 fix]` round.

**Fix:** in both sites, "the top-level fields are the sum of the **`type: "message"`** iterations."

---

## FINDING 3 — [IMPORTANT] Attack (v): "the inflation ratio is exactly 2.0" is false in **every** observed turn, and a documented tuning rule is built on it

**Measured**, over the 822 multi-`message` turns (ratio = top-level ÷ last-`message`-iteration): **min 1.9427, max 1.9979, exactly 2.0 in 0 of 822.** The document's own two headline numbers contradict it: `373139 / 189929 = 1.9646` and `539691 / 270851 = 1.9926`.

Sites, from the sweep:

| site | text | status |
|---|---|---|
| SP1 doc, Prevalence | *"the inflation ratio is **exactly 2.0 in every one**"* | wrong — but see charitable reading below |
| SP1 doc, Guidance rule 2 | *"The observed ratio was **exactly 2.0** in all 793 multi-iteration turns, which is far tighter than '>50%'"* | **inoperable as written** |
| SP1 doc, **N76 blockquote** | *"inflate by **exactly 2.0x**"* | wrong, **and scheduled for paste into `main`'s BACKLOG** |
| `task-002-implementer-report.md` | *"inflate by **exactly 2.0×**"* | wrong |
| `task-002-implementer-report.md` | *"≈2.0× *and* returning to the prior level"* | **defensible** — carries the approximation sign |

**Pre-empting the charitable reading:** the Prevalence line's em-dash gloss — *"— two `message` iterations, one prompt counted twice"* — can be read as "exactly two iterations," not "ratio exactly 2.0." Grant that for the Prevalence line. It does not rescue **Guidance rule 2**, where the figure is unambiguously numeric and used as a threshold against the ">50%" alternative. A discriminator keyed on "exactly 2.0" matches **none** of the 822 real poisoned turns. The rule is not imprecise; it is inoperable.

**Second half of attack (v) — 2.0x as a structural constant.** Nothing observed rules out three `message` iterations. I built a three-`message`-iteration fixture and measured the shipped probe: top-level 304,806, corrected 102,702 — **2.97x**. The probe handles it correctly; rule 2 would not detect it. The doc caveats only the compaction residual, not this one, and no fixture covers the shape.

**Fix:** replace "exactly 2.0" with the measured range (`1.94–2.00`, ~2x, mode 1.99) at all four wrong sites including the N76 blockquote; restate rule 2's discriminator as a range rather than a point; and add one sentence noting that the ratio scales with the number of `message` iterations, so a 3-iteration turn would inflate ~3x and rule 2 would miss it.

**Attribution:** implementer (`529f283`); echoed by the controller in `task-002-implementer-report.md` (`890eacc`).

---

## FINDING 4 — [MINOR] Two surviving mutations: `iterations-not-a-list.jsonl` does not pin the list check, and no fixture pins the dict guard

Mutation harness: six single-construct mutations of `context-probe.py`, each run against the probe + gate subset, each reverted with `git checkout --`. Baseline **52 passed**.

| # | mutation | result |
|---|---|---|
| M1 | `reversed(iterations)` → `iterations` (first instead of last `message`) | **RED** (2 failed) |
| M2 | drop the `type == "message"` filter | **RED** (2 failed) |
| M3 | `return _sum_fields(usage)` — i.e. **revert the fix** | **RED** (3 failed) |
| M4 | fallback returns `0` instead of the top-level sum | **RED** (22 failed) |
| M5 | `not isinstance(iterations, list)` → `iterations is None` | **SURVIVED** |
| M6 | drop the `isinstance(iteration, dict)` guard | **SURVIVED** |

Harness positive control: M1–M4 all produced RED, so a "survived" verdict is a measurement, not a broken harness. **M3 is the dispatch's explicit question — the new tests do NOT pass if the fix is reverted.** Answered: 3 failures.

**M5 root cause (the real finding):** `tests/unit/fixtures/context-probe/iterations-not-a-list.jsonl` holds the **string** `"nope"`. A string *is* iterable — `list(reversed("nope"))` returns `['e','p','o','n']` — so under M5 the loop still runs, every char fails the dict check, the function still returns `None`, and the fixture still reads 250000. **The fixture named "not-a-list" does not pin the list check.** Concrete consequence, measured with M5 applied: a transcript with `iterations: 5` raises `TypeError: 'int' object is not reversible`, the probe exits non-zero, and the gate degrades to the byte-proxy. The shipped code is correct here (I confirmed `iterations: 5`, `null`, and a bare dict all return 250000 unmutated) — this is purely a coverage gap.

**M6:** no fixture carries a non-dict iteration entry, so the dict guard is untested. The shipped code handles it correctly (mixed `["x", 7, null, {message}]` → 180001).

**Fix:** change `iterations-not-a-list.jsonl` to a non-iterable scalar (`5` or `null`), or add a sibling fixture; add one fixture with a non-dict entry among valid ones.

### Consolidated fixture-coverage gap

Missing shapes, as one statement: (a) three or more `message` iterations — pins that 2.0x is not structural, per Finding 3; (b) a malformed / zero-summing last `message` iteration — **required** by Finding 1's fix; (c) a non-dict iteration entry — M6; (d) a genuinely non-iterable `iterations` value — M5.

---

## FINDING 5 — [MINOR] The doc cites the wrong file as the differential parity test, and post-fix that test no longer certifies what the doc says

The SP1 doc's Parity paragraph: *"The existing differential parity test (`test_context_probe_fixtures.py`) still passes untouched: its fixtures carry no `iterations` key, so both implementations take the fallback path."*

`grep -nE 'claude-ctx-check|PROBE|subprocess|import' tests/unit/test_context_probe_fixtures.py` returns only `import json` and `from pathlib import Path`. **That file invokes neither `context-probe.py` nor `claude-ctx-check`** — it is a hand reimplementation asserting against itself, so "both implementations take the fallback path" is not a statement about it.

The real differential test is `test_differential_parity_with_ctx_check` in `tests/unit/test_context_probe_sessionid.py` (it surfaced in M4's failure list). It uses `hard.jsonl`, which carries no `iterations` key — so the doc's *reasoning* is right, applied to the wrong file. Post-fix the two implementations genuinely diverge on multi-iteration transcripts and **nothing pins where**; the parity test now certifies only the fallback path.

**Fix:** cite `test_context_probe_sessionid.py::test_differential_parity_with_ctx_check`, and add one sentence scoping what parity still means post-divergence.

---

## FINDING 6 — [MINOR] The duplicate report is a second divergent copy carrying defects the conventional report does not — strengthening the spec review's ADVISORY 2

`task-002-implementation.md` also carries a sentence garbled by the controller's `d6678ad` statusline correction:

> "It alone carries this — the statusline `ctx:` does NOT (see the 2026-07-31 experiment note in `context-summary.md`; harness-computed, measured correct). **Formerly-claimed statusline `ctx:` field over-report multi-iteration turns by ~2x.**"

The trailing fragment is a leftover from the edit and still reads as asserting the statusline over-reports — the exact claim the whole correction round exists to retract.

Combined with SUM site 5 (Finding 2) in the same file, the spec review's ADVISORY 2 ("consolidate the duplicate misnamed report") becomes a **correctness** argument rather than a tidiness one: the duplicate is a second divergent copy carrying two defects the conventional `task-002-implementer-report.md` does not. Consolidate before the module boundary archives both.

**Attribution:** garbled sentence — controller (`d6678ad`); SUM site — implementer (`529f283`).

---

## Attacks that found nothing — negative results I actually ran

- **Attack (i) — the positive control fires.** I re-ran the no-op detector myself. Over 2,483 harvested real single-iteration usage blocks: unplanted → `(2483, 0)`; with **one** planted `input_tokens += 1` → `(2483, 1)`; with **five** plants → `(2483, 5)`. The detector produces non-zero, so "zero mismatches" is a measurement. Independently reproduced across the 120-largest corpus: **32,498 single-iteration turns, 0 mismatches** (the doc's `32,160` is corpus drift, as the spec review noted).
- **Attack (iii) — the no-iterations fallback is behaviorally identical.** Loaded the pre-fix (`a4dc986`) and shipped modules side by side and compared `find_latest_total` over **all 273** transcripts under `~/.claude/projects`: 204 identical, 66 no-usage, **3 differ — all with a multi-`message` newest block. Zero regressions on any other shape.** Corroborated at the source level (the fallback expression `_sum_fields(usage)` is the old inline `sum(_coerce_int(usage.get(f)) for f in FIELDS)`; line scanning, `JSONDecodeError` skip, dict guards, and reverse order are untouched) and on synthetic fixtures A–G/O/R, all of which matched pre-fix output exactly.
- **The "last `message` iteration" selection rule is consistent with the monotonicity claim.** Across all 822 multi-`message` turns, the last `message` iteration is the **maximum** of the message iterations in **822/822** — it is never a smaller later call.
- **Attack (iv), statusline half — no new site.** Sweeping the changeset for `statusline` finds exactly one surviving wrong claim: `context-probe.py`'s divergence-2 paragraph, which the spec review already named and `deviations.md` row 2 already owns. The controller's "five sites corrected" claim verifies. (The `d6678ad` garble in Finding 6 is a broken sentence in a corrected site, not a sixth uncorrected one.)
- **Malformed iteration data is unobserved in the corpus.** 34,139 `message` iterations: 0 with a missing/non-int field, 0 summing to zero, 0 non-dict entries. This bounds Finding 1's severity register — it is a structural fail-open, not a sighting.
- **Shipped code handles the remaining edge shapes correctly.** `iterations` as a dict, string, `null`, or int; `type` as a non-string (a list); a list of only non-dicts; `[message, advisor_message]` ending on a non-message — all return the intended value with rc=0, no crash.
- **No tier-selection interaction beyond Finding 1.** The only way the fix turns a probe success into a different tier or a silent failure is the zero path.

---

## Bottom line

The mechanism the fix implements — read the last `type: "message"` iteration, fall back to top level — is correct, and I confirmed it against real archived data and 822 real multi-iteration turns. Four of six mutations go RED, including the revert. What blocks is that the fix introduces a new way for a blocking gate to read `0` and report it as a successful probe, against a shape the feature itself documents as version-unstable; the one-line fallback-on-zero closes it with zero measured behavior change across 273 transcripts. Alongside it, two documented claims are false as measured — the "SUM" mechanism at two further sites, and "exactly 2.0" at four, one of each queued for copy into `main`'s BACKLOG.
