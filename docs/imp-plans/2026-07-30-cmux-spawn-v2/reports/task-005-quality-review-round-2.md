# Task 5 — Code Quality Review (round 2, adversarial)

**Verdict: APPROVED**

All three round-1 findings closed, verified by mutation rather than by reading. Four additional
over-permissive mutations round 1 did not run were all caught. The escalated coupling question is
ruled **cosmetic** — with the "can it hide a survival?" question answered empirically, not by argument.

Reviewer: general-purpose subagent (opus). Worktree restored and verified (both source files
byte-identical to their commits, `git stash list` empty, no commit made).

## Harness integrity

Every mutation run cleared `__pycache__` before and after and used `-p no:cacheprovider` — round 1's
corruption mode. Recursive sweeps used `/usr/bin/grep`, never the shell `ugrep` wrapper.

**Positive controls carried:** the scope grep was run unfiltered first (`/usr/bin/grep -rl
"expected_hops" tests/` → the test file PLUS its `.pyc`), so the `--include='*.py'` narrowing is a
measurement, not a silent miss. Under mutation the fast harness DID report failures every time it
should have, and the one surviving mutation (J) ran in the same harness that killed the four beside it.

**Confinement premise bought, not inherited.** The fix report's "sole new failure" claims rest on the
full 674-test suite. Round 2 re-ran the FULL `tests/unit/` under the `ge=2` mutation itself:
`2 failed, 672 passed`, both failures inside `TestHandoffBlock`. Since all three closure mutations
touch the same two lines of the same class, that one run closes confinement for the whole battery.
(`sdd_session.py` is imported by `materialize-manifest.py`, `controller-checkpoint.py`,
`transition-module.py`, `validators.py`, and `plan.py`, so this was not free.)

## Closure table

| # | Round-1 finding | Mutation applied | Closed? | Evidence |
|---|---|---|---|---|
| MAJOR 1 | valid `ge=1` boundary unpinned | `Field(ge=1)` → `Field(ge=2)` | **YES** | `2 failed, 176 passed` (model dir) and **`2 failed, 672 passed` (full suite)**. Failures: `test_expected_hops_accepts_one` (intended) + `test_rejects_invalid_spawn_policy` (the coupling, ruled below). Round 1 had this at 175/671 — SURVIVED. |
| MINOR 3 | int-ness unpinned | `expected_hops: int` → `float` | **YES** | `1 failed, 177 passed`; sole failure `test_expected_hops_must_be_an_integer`. Note: `test_expected_hops_accepts_one` PASSED under this mutation (`1.0 == 1`), so the two new tests are not redundant with each other. |
| MAJOR 2 | invalid `spawn_policy` behaviorally unpinned | `@field_validator("spawn_policy", mode="before")` returning `v if v in (...) else "auto"` | **YES, and the annotation guard stayed green** | `1 failed, 177 passed`. Per-test `-v`: `test_rejects_invalid_spawn_policy FAILED` while **`test_spawn_policy_literal_is_closed_set PASSED`** (named, not inferred from a count). Direct probe: `Handoff.model_validate({'expected_hops':1,'spawn_policy':'prompt'}).spawn_policy` → `auto`; `get_args(...)` → unchanged. |

**All three new tests proven non-vacuous** — each killed by a mutation of exactly the property it
claims to pin, and by no other mutation in the battery.

## Ruling on the escalated coupling question

**Cosmetic. Ship as-is. No change required.**

Two measurements decide it, both taken this round rather than inherited:

1. **The fix report's mechanism is correct.** Under `ge=2` the validate call raises with
   `[('expected_hops','greater_than_equal'), ('spawn_policy','literal_error')]`. `errors()[0]` is
   `greater_than_equal`, exactly as reported, and the failing pair is exactly the pair reported.
   **One premise in this feature that did NOT have to be overturned.**
2. **The coupling cannot produce a false SURVIVED — verified two ways.**
   - *Structurally:* for `errors()[0]["type"] == "literal_error"` to hold while `spawn_policy`
     validation is broken, some other field would have to emit `literal_error` FIRST. `MINIMAL_SESSION`
     supplies `"tier": "standard"` and the `TIER_PROFILES["standard"]` blocks — every literal-typed
     field is valid, so no `ValidationError` would be raised at all and `pytest.raises` would fail.
   - *Empirically:* mutation C broke `spawn_policy` validation outright, and the test **FAILED**. It
     did not silently pass.

So the coupling is **one-directional**: it can only add one *explainable* extra failure to an
unrelated mutation's diagnosis. That is the OPPOSITE direction of harm from the `__pycache__`
aliasing that corrupted round 1 — that produced a **wrong attribution**; this produces a **noisy
correct** one. Mutation diagnosis is degraded by a footnote, never by a miss.

**Process ruling:** the fix subagent was RIGHT. Declining to unilaterally deviate from
reviewer-prescribed code and escalating instead is correct behavior for a fix round, and round 2 is
the right authority to decide it. Do not treat the escalation as a defect.

**Recommended form if ever touched (optional Nit, not required):** prefer the located-error assertion
over changing the literal —
```python
assert [e["type"] for e in exc.value.errors() if e["loc"][-1] == "spawn_policy"] == ["literal_error"]
```
`expected_hops: 3` decouples from THIS mutation only; the located-error form decouples from ANY
co-occurring error while keeping the assertion strictly exact. Do not require a round for it.

## New findings

**None at Blocker, Major, or Minor.** Four mutations round 1's battery did not run were applied; all
four were caught.

### Nit 7 — a tier-conditional nulling validator survives all eleven tests. COSMETIC, no action.

Reported for completeness, deliberately NOT filed. Mutation J added a `@model_validator(mode="after")`
on `SddSession` setting `self.handoff = None` when `self.tier == "micro"` — silent data loss for
exactly the tier whose `expected_hops` is `1`. Result: `178 passed`, survived. Why not actionable: no
plausible edit produces that validator (a fabricated conditional with no basis in the plan, the spec,
or the model's design); `test_expected_hops_accepts_one` now pins the micro value at the model layer;
and micro-tier materialization is Task 6's `test_micro_tier_expected_hops_is_one`. **Manufacturing a
finding out of a contrived mutation would be the tenth wrong premise in this feature, not the first
real one.**

## Verified-correct

- **The alias / serialized-key surface is structurally closed** — the one surface round 1's battery
  never probed (nothing asserts the JSON keys are `expected_hops`/`spawn_policy`, and
  `_handoff_support` will read raw JSON keys). Measured, not reasoned:
  - *Wire-key drift* — renaming the field to `policy` with `alias="spawn_policy"` +
    `populate_by_name=True` → `3 failed` (`test_handoff_block_validates`,
    `test_spawn_policy_defaults_auto`, `test_spawn_policy_literal_is_closed_set`). Caught.
  - *Why no silent path exists:* `StrictModel` sets ONLY `extra="forbid"` — no `populate_by_name`
    (`_base.py`) — and `materialize-manifest.py` serializes with plain `model_dump_json()` /
    `model_dump_json(indent=2)` with **no `by_alias`** (lines 194, 213). So the written key is always
    the field name, and the field name is pinned by `extra="forbid"` on read.
  - *Serialization drops* are covered by `test_round_trips_through_json` precisely because it uses
    non-default values (`4`, `"off"`): an `exclude=True` on either field breaks equality or raises.
- **`mode="before"` coercer `int(v)` on `expected_hops`** (a strictly different over-permissive shape
  from the `float` annotation change) → `1 failed`, sole failure `test_expected_hops_must_be_an_integer`.
- **Subclass-level `model_config = ConfigDict(extra="allow")` on `Handoff`** — distinct from round 1's
  PC1 base-class swap, and the more likely real-world edit → `1 failed`, sole failure
  `test_extra_key_rejected`. The `StrictModel` guard holds against BOTH routes.
- **The fix is genuinely test-only.** `git show --stat --name-only d1741e0` lists exactly the one test
  file. `sdd_session.py` sha256 equals `git show f91b94f:...` — the production model is byte-for-byte
  what round 1 reviewed, so the fix carries zero behavioral risk, as claimed.
- **Suite counts confirmed, not inherited:** `tests/unit/test_models/ -q` → **178 passed**;
  `tests/unit/ -q` → **674 passed** (154-158s). Both match the fix report exactly (+3 from 175/671).
- **`materialize-manifest.py` does not yet import `Handoff`** — Task 5's write scope is clean and the
  `"handoff": null` side effect remains Task 6's, as dispositioned.
- Already-dispositioned items re-checked but not re-filed: the three plan-verbatim style choices,
  `"handoff": null`, the pre-commit hook not firing (that prediction has now failed twice),
  `expected_hops` required per B4, and round-1 Nits 4-6.

## Restore verification

`git status --porcelain` lists no source file (only pre-existing SDD artifacts). sha256 both ways:
```
3d1341799a0cb95f2b10d2e3b2b9417eba5e530cc427cce31c08e7ce525282fe  git show f91b94f:skills/scripts/models/sdd_session.py
3d1341799a0cb95f2b10d2e3b2b9417eba5e530cc427cce31c08e7ce525282fe  skills/scripts/models/sdd_session.py
3e4f8947b217af2616a88b96360422a8ea233c55a868fed79939c83f102c2c8c  git show d1741e0:tests/unit/test_models/test_sdd_session_model.py
3e4f8947b217af2616a88b96360422a8ea233c55a868fed79939c83f102c2c8c  tests/unit/test_models/test_sdd_session_model.py
```
`git stash list | wc -l` → `0`. `__pycache__` cleared after the final restore; the post-restore clean
run is the 178-passed result above. Nothing committed.
