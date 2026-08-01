# Task 6 — Code Quality Review (round 2, adversarial)

**Verdict: CHANGES_REQUESTED**

**All eight round-1 findings are genuinely CLOSED, each proven by mutation.** But round 2 found **one
substantive over-permissive survivor in the same class as round 1's Major 1 — on the OTHER call site** —
plus one unpinned guard from the family round 1 enumerated but did not finish.

## Harness
Anchor uniqueness enforced (`MUTATION-ANCHOR-ERROR count=3` aborted one attempt rather than silently
no-op'ing). `__pycache__` cleared between runs; `-p no:cacheprovider`. **Scope proven complete:**
`/usr/bin/grep -rn "_handoff_support" tests/ skills/` shows only the two test files plus
`materialize-manifest.py:60` — nothing else imports the module, so a scoped "survived" is not understated.
**Baseline `28 passed`. Positive control** `HOP_DIVISOR 2.5 → 2` → **`4 failed, 24 passed`** — harness live.

**Gates:** full unit **694 passed**; `validate-all-skills.py` **PASS: 160 / FAIL: 0 / WARNING: 2**.
**+7 accounting verified, not inherited:** `grep -c 'def test_'` → `test_handoff_support.py` 9 → 16;
`test_materialize_manifest.py` 12 → 12. Net **+7** = 5 net-new + the 1→3 split (+2). Matches 687 → 694.

## Closure table — all 8 CLOSED, every one the SOLE failure

| # | Mutation applied | Result | Caught by |
|---|---|---|---|
| F1 (M17) | materialize: `expected_hops(total_tasks, tier)` → `..., "standard")` | `1 failed, 27 passed` | `test_micro_tier_expected_hops_is_one` |
| F2 (M12) | materialize: `if spawn_policy is None:` → `if not spawn_policy:` | `1 failed, 27 passed` | `test_off_survives_...` |
| F3 (M14) | `math.ceil(t/HOP_DIVISOR)` → `max(1, round(...))` | `1 failed, 27 passed` | `test_formula_standard` |
| F4 (M19) | swap module-union and `task_range` blocks | `1 failed, 27 passed` | `test_module_union_beats_task_range` |
| F5a (M2) | drop `not isinstance(t, bool)` (step 1) | `1 failed, 27 passed` | `test_bool_never_counts_...` |
| F5b (M3) | drop `not isinstance(tid, bool)` (task_ids) | `1 failed, 27 passed` | same |
| F5c (M5) | drop `not isinstance(eh, bool)` | `1 failed, 27 passed` | `test_invalid_block_values_are_rederived_not_trusted` |
| F5d (M4) | `eh >= 1` → `eh >= 0` | `1 failed, 27 passed` | same |
| F5e (M7) | `len(tr) == 2` → `>= 2` | `1 failed, 27 passed` | `test_wrong_length_task_range_is_not_derivable` |
| F6 (M8) | `tr[0] <= tr[1]` → `<` | `1 failed, 27 passed` | `test_single_task_range_is_inclusive` |
| F8 | split verified by reading the diff | — | three split tests carry all three original assertions verbatim |

**F1 — the replacement genuinely discriminates** (measured, not inferred): on the default 5-task plan,
`micro → expected_hops 1` and `standard → 2`, **both exit 0**. The answers differ, so the assertion CAN
fail; M17 confirms it does. The original `tasks=[{"id":0},{"id":1}]` gave `ceil(2/2.5)==1 == micro` —
exactly why it was vacuous.

**F2 — the stderr half is independently load-bearing.** Two measurements in order: (a) the plain M12
mutation fails on `_mf`'s INTERNAL `assert (r["exit_code"] == 0) is ok` — the exit-code half, not the
new clause. (b) So the reviewer built the composite regression round 1 predicted: consent bypass PLUS an
unrelated later gate that also returns 1. The **old** assertion form PASSES
(`exit_code: 1 | OLD assert (exit!=0): True`) while the **new** form FAILS
(`'spawn_policy' in 'Unrelated later gate rejected the plan'` → False).
**The vacuous-green scenario reproduced, and the stderr clause is what catches it.**

## F7 — verified independently
Round-tripped the literal body `_write_report` now emits through `ImplementerReport.model_validate`:
populated default → all four cases **VALID** (was: `(2,'DONE_WITH_CONCERNS')` and `(4,'DONE')` INVALID).
**Exemption still reachable AND still discriminating:** `files_changed="[]"` + `task_type="verification"`
+ `DONE` → VALID; same empty list with `task_type="implementation"` → **INVALID**. So the variant Task 7
must honor is exercisable and the guard behind it is not neutered. Signature-compatible with all seven
of Task 7's planned call sites (the new keyword is appended last with a default). `_write_report` has
zero live callers, so no existing test changed behavior.

## Fix is genuinely test-only
`git diff --stat 9b32c25 HEAD -- skills/` → **empty**. sha256 vs `git show 9b32c25:<path>`:
`_handoff_support.py` `ccffc2b2…cf7410cd` MATCH; `materialize-manifest.py` `2de5dfa6…637b9335` MATCH.

## NEW findings

### Major 1 — `tier` propagation is unpinned INSIDE `_handoff_support.py`; two over-permissive mutations survive all 28 tests (SUBSTANTIVE)

Round 1's Major 1 closed tier propagation at the **materialize** call site. The identical propagation
inside the support module — **the one Module 3's planned `expected-hops --manifest` CLI actually goes
through** — was never mutated by round 1 and is still unpinned. Two survivors, one root cause:

| Mutation | Result | Measured consequence |
|---|---|---|
| `derive_expected_hops`: `manifest.get("tier") or "standard"` → `"standard"` | **`28 passed`** | `derive_expected_hops({"total_tasks": 19, "tier": "micro"})` = **1** guarded, **8** mutated |
| `expected_hops`: `if tier == "micro":` → `if tier != "standard":` (**round 1's M16, listed OVER-PERM/not-caught and NEVER DISPOSITIONED in either the findings or the explicitly-not-filed paragraph**) | **`28 passed`** | `expected_hops(19, "Micro")` = **8** guarded, **1** mutated |

`test_micro_is_one` pins `expected_hops(19,"micro")` only, and **no test calls `derive_expected_hops`
with a `tier` key at all** — so neither mutant is observable.

**Reachability measured, not assumed:** the second mutant is NOT reachable from `materialize-manifest.py`
(it validates `tier not in TIER_PROFILES → return 1` before the call). Both ARE reachable through
`derive_expected_hops`'s raw-JSON path against a hand-edited, legacy or pre-v2 manifest — the exact
tolerate-what-we-didn't-write role the plan's B4 note assigns this function.

**Fix — two assertions, both verified to discriminate:**
```python
assert derive_expected_hops({"total_tasks": 19, "tier": "micro"}) == 1
assert expected_hops(19, "weird") == 8      # unknown tier behaves as standard
```

### Minor 1 — the FOURTH bool guard in `derive_total_tasks` is unpinned (SUBSTANTIVE)
Round 1's Major 3 enumerated three bool guards (M2/M3/M5) and the fix closed all three. There is a
fourth, inside the `task_range` element check, never mutated by anyone. Mutation
`all(isinstance(x, int) and not isinstance(x, bool) for x in tr)` → `all(isinstance(x, int) for x in tr)`
→ **`28 passed`**. Measured: `derive_total_tasks({"total_tasks": 0, "modules": [], "task_range": [True, 4]})`
= `None` guarded, **`4` mutated** (`4 - True + 1`). Same raw-JSON reachability as Major 3.
**Fix:** `assert derive_total_tasks({"total_tasks": 0, "modules": [], "task_range": [True, 4]}) is None`.

### Minor 2 — Task 7's planned fixture no longer exercises the verification exemption (COSMETIC)
`module-2-models-budget.md:464` still reads `_write_report(r, 1, "DONE", task_type="verification")
# empty files_changed OK`. With the new populated default that call emits a NON-empty `files_changed`,
so as written it no longer exercises the exemption round 1 asked to preserve. **Cosmetic by the
reviewer's own measurement:** `count_tasks_done` keys on status and never model-validates, so no Task 7
assertion moves, and the exemption is reachable via `files_changed="[]"`. What is stale is a plan
comment. Update that plan line to `..., files_changed="[]")` when Task 7 is dispatched.

### Not filed (measured, deliberately)
**M6** (`isinstance(m, dict)` → `if True`) → `28 passed`, as expected — round 1 dispositioned it as
crash-directional. **M1**/**M15** are on the do-not-refile list. `TestHopCeiling.test_floor_factor_and_none`
is still packed (Nit 1's shape, split only for `TestDeriveExpectedHops`) — but **not vacuous**:
`max`→`min`, `CEILING_FLOOR 6→5` and `CEILING_FACTOR 2→3` each produce `1 failed, 27 passed` against it.
No coverage loss, so not filed.

## Verified correct
- **No coverage lost in the split** — the three split tests carry the packed original's three assertions
  verbatim, and F5c/F5d prove that class discriminates.
- **None of the seven new tests is vacuous** — each proven to fail under a mutation of the property it
  names, each as the SOLE failure.
- **Nine additional mutations run beyond the eight findings**, all caught: `total_tasks <= 0` → `< 0`;
  `derive_total_tasks(...) or 1`; materialize default `"auto"` → `"ask"`; materialize `ask` → `auto`
  coercion; the three `hop_ceiling` mutants; plus the positive control.

## Final restore verification
sha256 MATCH vs HEAD for all four files; MATCH vs `9b32c25` for both production files.
`git status --porcelain -- skills tests` → **empty**. Post-restore scoped run → **28 passed**.
Nothing committed; no `git stash` used.
