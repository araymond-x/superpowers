# Task 2 Code Quality Re-Review (Round 2) — SP1 context-probe iteration fix

**Verdict: CHANGES_REQUESTED** — one BLOCKING finding is **partially, not fully, closed**; the MINOR mutation finding is fully closed. Four advisories.

The fix round did good work: every shape round 1 tabulated is now closed, every mutation round 1 named is now RED, the positive control survives, and the corpus is unmoved. What remains open is the **adjacent half of the same defect class** — round 1's fail-open was closed for iteration totals of *exactly* zero and left open for iteration totals that are small-but-truthy. I proved it end-to-end against a **real archived 493,759-token usage block**, and I proved a variant that closes it with **zero** measured behavior change.

Everything below was verified by execution unless explicitly labeled *reasoned*. Attacks that found nothing are listed at the end.

---

## Execution scope

Run: the 8-file probe+gate subset (`56 passed`, verified at baseline and after every single mutation revert); an **8-mutation** battery against `context-probe.py`; live `sdd-pre-dispatch-hook.sh` drives on the implementer new-task path via `sdd_test_helpers.setup_full_sdd_workspace` (18 hook invocations across 4 harnesses); a 13-shape probe-level harness under bare `/usr/bin/python3` (the hook's interpreter); three full sweeps over **1,319** transcripts under `~/.claude/projects`; the full unit suite; and the skill regression gate.

Counts with their commands:

| figure | command |
|---|---|
| `56 passed` | `.venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py -q` |
| `653 passed` | `.venv/bin/python3 -m pytest tests/unit/ -q` |
| `PASS 159 / FAIL 0 / WARNING 2` | `python3 tests/ARaymond-skill-regression/validate-all-skills.py` |
| corpus figures below | a stdlib script walking `sorted((Path.home()/".claude"/"projects").rglob("*.jsonl"))`, loading the pre-fix module via `git show e7034bc:…` and the shipped module side by side with `importlib.util.spec_from_file_location`, comparing `find_latest_total` |

Tree state: `git status --porcelain` is byte-identical to what it was when I started — three modified controller/hook-written files (`deviations.md`, `.dispatch-log`, `context-observations.log`) and four untracked review reports. No `git stash`. Every mutation reverted with `git checkout -- <explicit path>` **and** re-verified at exactly `56 passed` before the next mutation was applied; the restore check printed `OK` 8/8 times.

---

## FINDING 1 [BLOCKING] — the fail-open is closed for an *exactly-zero* iteration and still open for a *small-but-truthy* one

**Construct:** `usage_total` in `skills/subagent-driven-development/scripts/context-probe.py`, specifically the `if total:` truthiness test.

### First: what the fix genuinely closed — verified

All six shapes round 1 tabulated now return the top-level reading. Probe level, bare `/usr/bin/python3`, top-level summing to 250,000:

| shape (`iterations` value) | round 1 (shipped then) | now |
|---|---|---|
| `[{"type":"message"}]` — no token fields | 0 | **250000** |
| all four fields `0` | 0 | **250000** |
| string / `null` fields | 0 | **250000** |
| booleans | 0 | **250000** |
| floats | 0 | **250000** |
| `[{good}, {"type":"message"}]` — last-wins picks the bad one | 0 | **250000** |

**The positive control holds — the fallback did not swallow the feature.** A `good_message` iteration still returns the *iteration* value, not the top-level value: probe level `182001` (not 250000); live hook `tokens=182001 source=probe tier=below action=allow`. The suite's own assertions corroborate independently — `test_message_pair_is_not_double_counted` asserts `204202`, `test_three_message_iterations_scale_beyond_2x` asserts `107802`, both against `legacy_total` values of 373139 / 315406.

**Live hook, over-HARD transcript (top-level 451,000, `HARD=400000` default), implementer new-task path:**

| case | rc | observation row |
|---|---|---|
| control: no `iterations` key | **2** | `tokens=451000 source=probe tier=hard action=block` |
| round-1 defect A (`[{"type":"message"}]`) | **2** | `tokens=451000 source=probe tier=hard action=block` |
| round-1 defect D (booleans) | **2** | `tokens=451000 source=probe tier=hard action=block` |
| round-1 defect E (all floats) | **2** | `tokens=451000 source=probe tier=hard action=block` |
| round-1 defect F (good-then-bad) | **2** | `tokens=451000 source=probe tier=hard action=block` |

**Fallback-streak escalation is no longer disarmed by the poisoned shape:** with two `action=fallback` rows seeded, defect A now writes `action=block` (rc=2) instead of resetting the streak with `action=allow`.

That half of round 1's finding is **closed**, verified in both directions.

### Second: the half that is still open

`if total:` is a truthiness test, so it rescues **only** a total of exactly `0`. Any surviving int field makes the corrupted iteration truthy and it is returned as a measurement. Probe level, same 451,000 top-level:

| shape | shipped result |
|---|---|
| `[{"type":"message","input_tokens":1}]` | **1** |
| three floats + one int survivor (`output_tokens:7`) | **7** |
| iteration's `cache_read_input_tokens` renamed, others intact | **1902** |

Driven through the **live hook**, all three exit `0` and write `source=probe tier=below action=allow`:

```
ATK I: iteration {input_tokens:1}       rc=0  tokens=1    source=probe tier=below action=allow
ATK J: 3 floats + 1 int survivor        rc=0  tokens=7    source=probe tier=below action=allow
ATK M: partial field rename             rc=0  tokens=1000 source=probe tier=below action=allow
```

And it still disarms the streak: with two seeded `action=fallback` rows, `ATK I` writes `action=allow` and resets the counter — the exact escalation-disarm round 1 described, surviving intact for this shape.

### Third: this is not a synthetic-only concern — measured on real data

Across **1,319** real transcripts / **49,052** `type:"message"` iterations, `cache_read_input_tokens` is a **median 98.2%** (mean 92.1%) of a message iteration's four-field total. So losing that one field inside the iteration collapses the reading to a small truthy number rather than to zero.

Quantified against real over-HARD sessions — of the **47** newest-block readings at or above `HARD=400000`, how many would drop below HARD (and be **allowed**) if exactly one iteration field became unreadable:

```
drop input_tokens                -> 0/47
drop cache_creation_input_tokens -> 1/47
drop cache_read_input_tokens     -> 46/47
drop output_tokens               -> 0/47
```

**End-to-end proof on a real archived block** (top-level 493,759; chosen iteration 493,759), driven through the live hook:

| mutation of the real block | rc | observation row |
|---|---|---|
| unmodified (control) | **2** | `tokens=493759 source=probe tier=hard action=block` |
| **iteration's `cache_read_input_tokens` renamed** | **0** | `tokens=24234 source=probe tier=below action=allow` |
| iteration's **all four** renamed (control — the shape the fix closes) | **2** | `tokens=493759 source=probe tier=hard action=block` |
| top-level only renamed (control) | **2** | `tokens=493759 source=probe tier=hard action=block` |

A real 493,759-token controller session reads as **24,234 tokens**, `source=probe`, and is allowed to dispatch. The all-or-nothing corruption blocks; the one-field corruption does not. That asymmetry is arbitrary, and round 1's severity reasoning applies unchanged: it is a fail-open in a blocking safety gate, it presents as a *successful* measurement rather than a probe failure, it resets the escalation counter, and the poisoned row carries `source=probe` — the exact rows N43 threshold tuning consumes.

**Scope bound I owe you, verified not reasoned.** If the same rename hit the top-level fields *as well*, the fallback collapses identically (`tokens=24234`, allow) and no guard inside `usage_total` helps. So this finding is precisely scoped: **the iteration-specific degradation path — the one this fix exists to create — is protected only against total corruption, not partial.** The top-level four field names are the stable, API-level names `claude-ctx-check` has always read; `iterations` is the shape this feature's own docstring labels *"an UNDOCUMENTED internal shape … NOT version-stable."* A partial change to the unstable shape alone is the realistic case, and it is the case still open. *(The plausibility of a partial rename is reasoned; everything else in this finding is measured.)*

### Fourth: the fix report's characterization of the residual does not survive measurement

The fix report's Self-Review says the residuals are *"not closable without the stricter 'fall back if any field is not an int' variant, which the quality review explicitly examined and rejected because it would spuriously fall back on iterations that legitimately omit a field."*

**That rejection was mine, in round 1, and it does not hold.** I reasoned it from `missing-fields.jsonl`, a **top-level** fixture, and generalized to iteration behavior. At the iteration level the data contradicts it. Independently re-measured across all 1,319 transcripts / **49,052** `message` iterations:

```
with a MISSING token field:      0
with a NON-INT present field:    0
summing to ZERO:                 0
non-dict entries:                0
```

I then built and measured the stricter variant — treat the chosen iteration as unusable unless all four fields are present ints:

```python
iteration = _last_message_iteration(usage)
if iteration is not None and not all(
    isinstance(iteration.get(f), int) and not isinstance(iteration.get(f), bool)
    for f in FIELDS
):
    iteration = None
if iteration is not None:
    total = _sum_fields(iteration)
    if total:
        return total
return _sum_fields(usage)
```

Measured, all by execution:

- **Zero differences** from the shipped version across all **1,319** transcripts (`identical=1246 no-usage=73 DIFFER=0`). There is no spurious fallback to be found in the real corpus.
- Existing suite unchanged: **`56 passed`** with the variant applied (then reverted, re-verified `56 passed`).
- Closes all three residual shapes: `1 → 451000`, `7 → 451000`, `1902 → 451000`.
- **Preserves the positive control:** `good_message` still returns `182001`, not the top-level value.

So the residual **is** closable, with the same zero-behavior-change property the shipped fix has. The actionable defect is that the fix report presents an inherited *reasoned* rejection as a *measured* one and stops there. The fix round did exactly what round 1 told it to; the instruction was wrong.

**Fix:** apply the completeness guard above, ship the two fixtures that pin it (a `message` iteration with one surviving int field, and one with a renamed `cache_read_input_tokens`), and correct the fix report's Self-Review item and Concern 1 to state the measured basis. Keep `if total:` — it still covers the all-zero-values case the completeness guard admits.

**Attribution:** the surviving fail-open is the fix round's (`2dbba48`), narrowed from the implementer's (`529f283`); the mis-scoped guidance that produced it is round 1's (mine).

---

## FINDING 4 [round 1, MINOR] — **CLOSED**. Full mutation battery, 8/8 RED

Mutation harness: single-construct edits to `context-probe.py`, each run against the 8-file probe+gate subset, each reverted with `git checkout --` and the restore re-verified at exactly `56 passed` before the next.

| # | mutation | round 1 | now |
|---|---|---|---|
| M1 | `reversed(iterations)` → `iterations` | RED | **RED** (3 failed) |
| M2 | drop the `type == "message"` filter | RED | **RED** (2 failed) |
| M3 | revert the fallback-on-zero (`return _sum_fields(iteration)`) | RED | **RED** (1 failed — `test_zero_summing_message_iteration_falls_back_to_top_level`) |
| M4 | fallback returns `0` | RED | **RED** (24 failed) |
| M5 | `not isinstance(iterations, list)` → `iterations is None` | **SURVIVED** | **RED** (1 failed — `test_falls_back_to_top_level[iterations-not-a-list.jsonl]`) |
| M6 | drop the `isinstance(iteration, dict)` guard | **SURVIVED** | **RED** (1 failed — `test_non_dict_iteration_entries_are_skipped`) |
| M7 | `if total:` → `if total is not None:` | new | **RED** (1 failed — the same zero-fallback test) |
| M8 | list guard → `if not iterations:` (truthiness) | new | **RED** (1 failed) |

**Harness positive control:** 8/8 RED with distinct, plausible failure sets, and the restore returned to the baseline count every time — a "survived" verdict would have been a measurement. **M3 is the dispatch's central question — the new tests do NOT pass if the fix is reverted.** Answered: 1 targeted failure, by name.

**M7 answers the dispatch's fix-targeting question directly:** `if total is not None:` goes RED, so `test_zero_summing_message_iteration_falls_back_to_top_level` pins truthiness, not merely not-None — it asserts what its name says.

### Fixture verification — decoded, not read

Round 1's central minor finding was a fixture whose name asserted a property it did not have. I decoded all five changed/new fixtures and checked shape against name and against the test's assertion:

| fixture | decoded shape | name accurate? |
|---|---|---|
| `iterations-message-no-fields.jsonl` | `[{"type":"message"}]`, iteration sum **0**, top-level **250000** | yes |
| `iterations-message-triple.jsonl` | three `message` iterations summing 102502 / 105102 / 107802; top-level **315406** | yes |
| `iterations-non-dict-entries.jsonl` | `[7, {message sum 182001}, "x", null]` — genuinely non-dict entries | yes |
| `iterations-not-a-list.jsonl` | scalar `5`; `list(reversed(5))` raises `TypeError: 'int' object is not reversible` | yes — genuinely pins the list check |
| `iterations-string.jsonl` | `"nope"`; reversible — preserves the iterable-but-not-list shape | yes |

**The `iterations-message-triple.jsonl` arithmetic verifies from the fixture itself:** top-level `6 + 6000 + 304600 + 4800 = 315406`; last `message` iteration `2 + 3000 + 103100 + 1700 = 107802`; ratio `315406 / 107802 = 2.9258`. The claim checks out. It is also internally consistent with the *corrected* mechanism — `102502 + 105102 + 107802 = 315406` exactly, so the fixture itself demonstrates "top-level = sum of the `message` iterations."

**The fix report's Deviation 1 verifies.** I reimplemented the M5 mutant and measured all three candidate values: `iterations: null` → shipped 250000, mutant 250000, **mutation survives**; `iterations: 5` → shipped 250000, mutant raises `TypeError`, **mutation killed**; `"nope"` → survives. The report's claim that `null` would not have killed M5, and that only a non-iterable scalar works, is correct.

---

## Advisories

**[MINOR] `test_non_dict_iteration_entries_are_skipped` bites via the crash path, not the skip path.** I inspected the M6 failure: it fails on `run_probe`'s `assert result.returncode == 0` (an `AttributeError` escaping the probe), not on the `== 182001` value comparison. The test's *docstring* states this mechanism accurately, and on shipped code the `182001` assertion does pin the skip semantics; no meaningful non-crashing mutant of that guard exists. This is a naming nit, not a repeat of round 1's fixture-naming finding.

**[MINOR] `iterations-string.jsonl` kills no mutation.** Under both M5 and M8 the string still falls through to `return None` and reads 250000, so only the `iterations-not-a-list` parameter goes RED. It was added deliberately to preserve prior coverage, and redundant coverage is not a defect — recorded so a future round does not re-derive it.

**[MINOR] Two undeclared content changes in the diff.** `tests/unit/test_context_probe_iterations.py` was black-reformatted (tuple wrapping, parenthesized asserts, added blank lines) and `main()`'s stderr message was re-joined from two implicit-concatenation fragments into one line — neither declared in the fix report's `files_changed` descriptions. I verified the stderr string is **byte-identical** by execution: both the pre-fix and shipped probes emit `context-probe: no usage block found in transcript (no completed turn)` with rc=1, and `cmp` on the captured stderr reports no difference. Harmless; declare it.

**[MINOR, scope observation not a finding] The fallback source is exempt from the fix's own stated principle.** The new docstring asserts *"A `0` from a preferred-but-unusable source must never be mistaken for a measurement."* But a top-level `usage` block carrying no recognized token fields still yields `_sum_fields(usage) == 0`, the probe exits 0, and the live hook writes `tokens=0 source=probe tier=below action=allow` (measured). This is **pre-existing legacy behavior**, unchanged by SP1 or by this fix, and out of scope — noted only because the docstring now states a general principle the code applies to one source and not the other. A real controller session can never have 0 accumulated tokens, so a probe total of `0` is arguably never a measurement.

---

## Attacks that found nothing — negative results I actually ran

- **The fix did not silently revert the original fix.** Probe level `182001` on a `good_message` iteration; live hook `tokens=182001`; suite assertions `204202` / `107802` against legacy values of 373139 / 315406. Verified three independent ways.
- **Zero behavior change on the real corpus — the fix report's claim verifies, and on a broader corpus than it used.** Pre-fix (`git show e7034bc:`) vs shipped `find_latest_total` over all **1,319** transcripts under `~/.claude/projects`: `identical=1246 no-usage=73 DIFFER=0 errors=0`. (The fix report cited 273 transcripts; my sweep is 4.8× larger and agrees.)
- **Round-1's corpus integrity figures reproduce and strengthen.** 49,052 `message` iterations (vs round 1's 34,139 over 120 files): 0 missing fields, 0 non-int fields, 0 zero-summing, 0 non-dict entries. Malformed iteration data remains unobserved in the wild.
- **No new test passes for the wrong reason.** Each of the four new tests has a mutation that targets it specifically and goes RED (M3/M7 → zero-fallback; M1 → triple; M6 → non-dict; M5/M8 → not-a-list).
- **Negative iteration totals fail safe.** An iteration summing to `-100` is truthy and returned, but the hook's `[[ "$out" =~ ^[0-9]+$ ]]` guard rejects it and routes to the byte-proxy (`source=byte-proxy action=fallback`) rather than allowing on a garbage reading.
- **Reformatting caused no collateral.** Full unit suite `653 passed`; regression gate `PASS 159 / FAIL 0 / WARNING 2` (the two pre-existing soft word-count advisories). Both independently corroborate the fix report's figures rather than inheriting them.
- **Documentation findings 2, 3, 5, 6 not re-swept** — owned by the round-2 spec re-review per the dispatch. Nothing in the code diff contradicts it; I confirmed the `context-probe.py` docstring's statusline claim is corrected and its `usage.iterations` version-instability note is present.

---

## Bottom line

The fix is correct as far as it goes and is proven not to have swallowed the feature it was fixing: six shapes closed, eight mutations RED, five fixtures decoded and honest, zero corpus movement across 1,319 transcripts, and the escalation streak no longer disarmed by the zero shape. What blocks is that `if total:` closes the defect for a corrupted iteration that sums to *exactly* zero and leaves it open for one that sums to *anything else* — demonstrated end-to-end on a real 493,759-token block that the live hook allows at `tokens=24234 source=probe`, with 46 of 47 real over-HARD sessions in the same position under a single-field loss. My own round-1 guidance is what scoped the fix that narrowly; the completeness guard I rejected then produces zero differences across the whole corpus, passes the 56-test suite unchanged, closes all three residual shapes, and preserves the positive control. It should ship.
