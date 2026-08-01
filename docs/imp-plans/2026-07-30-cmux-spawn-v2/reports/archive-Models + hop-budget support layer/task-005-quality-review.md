# Task 5 — Code Quality Review (round 1, adversarial)

**Verdict: CHANGES_REQUESTED**

Three mutations survive the full 671-test suite — **two of them over-permissive**. All three fixes
are *test-only additions*, verified green against unmutated code; no production-code change required.

Reviewer: general-purpose subagent (opus). Worktree restored and verified (`sdd_session.py` sha
identical to the committed blob, `git stash list` empty, no stray temp files, no commit made).

## Harness integrity (read before the table)

The reviewer's FIRST battery run reported M9 and M10 as failing 13 tests each with byte-identical
failure lists. **That was wrong** — a stale `__pycache__` artifact (mutation N's `.pyc` surviving
into run N+1; mtime+size aliasing at sub-second write cadence). Re-running M10 in isolation after
clearing `__pycache__` gave 2 failures, not 13. Every number below is from the re-run with cache
clearing between every mutation. Self-reported because *a harness that mis-attributes failures can
equally mis-attribute survivals*.

Controls, both confirmed before any result was trusted:
- **Positive control** (the plan's own stated discriminating control): `Handoff(StrictModel)` →
  `BaseModel` → CAUGHT by `test_extra_key_rejected` alone, no other test moved.
- **Negative control**: a no-op docstring edit → SURVIVED, 175 passed — i.e. "SURVIVED" means the
  suite ran and passed, not that nothing executed.

Scope justified by measurement: `/usr/bin/grep -rn "Handoff" tests/` and `'"handoff"' tests/` show
`TestHandoffBlock` is the ONLY coverage of the new block anywhere in the repo. The full `tests/unit/`
suite was nonetheless re-run for each survivor.

## Mutation battery

| # | Mutation | Direction | Caught? | Which test |
|---|---|---|---|---|
| PC1 | `Handoff(StrictModel)` → `BaseModel` | **OVER-PERMISSIVE** | yes | `test_extra_key_rejected` (only) |
| M1 | drop `ge=1` | **OVER-PERMISSIVE** | yes | `test_expected_hops_must_be_positive` |
| M2 | `expected_hops` gains `default=1` | **OVER-PERMISSIVE** | yes | `test_partial_block_rejected` |
| M3 | `SpawnPolicy` widened to 4th member `"always"` | **OVER-PERMISSIVE** | yes | `test_spawn_policy_literal_is_closed_set` |
| M4 | `SpawnPolicy` → `str` | **OVER-PERMISSIVE** | yes | `test_spawn_policy_literal_is_closed_set` |
| M5 | `handoff: Handoff\|None` → `dict\|None` | **OVER-PERMISSIVE** | yes | 5 tests incl. `test_handoff_block_validates` |
| M6 | `spawn_policy: SpawnPolicy\|None = None` | **OVER-PERMISSIVE** | yes | `test_spawn_policy_defaults_auto`, `..._closed_set` |
| M8 | `ge=1` → `ge=0` | **OVER-PERMISSIVE** | yes | `test_expected_hops_must_be_positive` |
| **M7** | **`expected_hops: int` → `float`** | **OVER-PERMISSIVE** | **NO** | — 175 passed; full suite **671 passed** |
| **M14** | **`mode="before"` validator coercing any unrecognized `spawn_policy` to `"auto"`** | **OVER-PERMISSIVE** | **NO** | — 175 passed |
| M9 | `handoff` loses its default (becomes required) | RESTRICTIVE | yes | 13 tests (genuine) |
| M10 | `SpawnPolicy` narrowed to 2 members | RESTRICTIVE | yes | `test_handoff_block_validates`, `..._closed_set` |
| M11 | `spawn_policy` default → `"off"` | RESTRICTIVE | yes | `test_spawn_policy_defaults_auto` |
| **M12** | **`ge=1` → `ge=2`** | RESTRICTIVE | **NO** | — 175 passed; full suite **671 passed** |
| M13 | `expected_hops: int` → `str` | RESTRICTIVE | yes | 3 tests |

Restored sha after the battery equals `git show f91b94f:skills/scripts/models/sdd_session.py | shasum -a 256`.

**Both existing guards genuinely discriminate** — verified by mutation, not assumption:
`test_spawn_policy_literal_is_closed_set` kills M3 and M4; `test_extra_key_rejected` kills PC1 and
nothing else, exactly as the plan predicted. The findings are the gap NEITHER covers.

## Findings

### MAJOR 1 — The valid boundary of `expected_hops` is unpinned, and that boundary is micro tier's production value. SUBSTANTIVE.

`test_expected_hops_must_be_positive` tests only the invalid half of the conjunction (`0`, `-1`).
Nothing asserts `1` is ACCEPTED, so tightening the bound is invisible: M12 (`ge=1` → `ge=2`) survives
at 175 and at the full 671. Not hypothetical — the module Contract Constraints pin
`expected_hops = ceil(total_tasks / 2.5)` standard, **`1` micro**, so `ge=2` would reject every
micro-tier manifest `materialize-manifest.py` will emit. The only planned coverage of that value,
`test_micro_tier_expected_hops_is_one`, lives in a DIFFERENT task's file (Task 6's
`test_materialize_manifest.py`) — so the constraint Task 5 owns is not pinned by Task 5.

Fix (test-only, verified passing on current code):
```python
def test_expected_hops_accepts_one(self):   # micro-tier value; pins the valid boundary
    s = SddSession.model_validate({**MINIMAL_SESSION, "handoff": {"expected_hops": 1}})
    assert s.handoff.expected_hops == 1
```

### MAJOR 2 — The drift risk is guarded on only ONE side, because the closed-set guard pins the ANNOTATION, not the BEHAVIOR. SUBSTANTIVE.

Task 4's `TestHandoffSpawn` guards its copy with TWO mechanisms — `test_rejects_invalid_value`
(feeds `"prompt"`, asserts `errors()[0]["type"] == "literal_error"`) AND `test_literal_is_closed_set`
(introspects `get_args`). Task 5's `TestHandoffBlock` has only the introspection guard;
`/usr/bin/grep -n "spawn_policy"` on the test file returns 8 lines, none feeding an invalid value.

M14 demonstrates the hole: a lenient `mode="before"` validator leaves the annotation — and therefore
`get_args` — untouched, so the guard passes while
`Handoff.model_validate({'expected_hops':1,'spawn_policy':'prompt'}).spawn_policy` returns `'auto'`.

**Why consequential rather than contrived** (the reviewer checked the consumer side): the
`_handoff_support` CLI reads `print(pol if pol in ("auto","ask","off") else "auto")` and
`spawn-handoff-session.sh` re-defaults with `case ... *) SPAWN_POLICY="auto" ;;`. Both raw layers
**silently map an unrecognized consent value to `"auto"` — the spawn-without-asking value.** The
Pydantic model is the ONLY layer in the stack that would reject a typo'd consent policy loudly, and
that behavior is currently untested.

Fix (test-only, verified passing — raises with `type == "literal_error"`):
```python
def test_rejects_invalid_spawn_policy(self):   # symmetric to Task 4's test_rejects_invalid_value
    with pytest.raises(ValidationError) as exc:
        SddSession.model_validate({**MINIMAL_SESSION,
                                   "handoff": {"expected_hops": 1, "spawn_policy": "prompt"}})
    assert exc.value.errors()[0]["type"] == "literal_error"
```

### MINOR 3 — Nothing pins `expected_hops` as an integer. SUBSTANTIVE.

M7 (`int` → `float`) survives at 175 and at the full 671. The tests feed only `5`, `3`, `4`, `0`,
`-1`: `ge` still rejects 0/-1, and `5.0 == 5` is `True`, so even the equality assertions and the JSON
round-trip pass. A hop budget of `2.5` would validate.

Fix (test-only; verified — `2.5` raises `int_from_float`, `type(...) is int` is `True`):
```python
def test_expected_hops_must_be_an_integer(self):
    with pytest.raises(ValidationError):
        SddSession.model_validate({**MINIMAL_SESSION, "handoff": {"expected_hops": 2.5}})
    s = SddSession.model_validate({**MINIMAL_SESSION, "handoff": {"expected_hops": 3}})
    assert type(s.handoff.expected_hops) is int
```

### NIT 4 — Model/consumer laxness asymmetry on `expected_hops` (bool/str). COSMETIC.

Measured: `True` → ACCEPTED as `1`; `3.0` → ACCEPTED as `3`; `'5'` → ACCEPTED as `5`; `False`/`2.5`/
`'abc'` → REJECTED. So `validators.py session` blesses `{"expected_hops": true}`. The spawn-time
reader is STRICTER (`isinstance(eh, int) and not isinstance(eh, bool) and eh >= 1`), so it ignores
such a value and silently re-derives — the divergence is fail-safe, and the only writer emits a
computed `int`. Optional hardening `Field(ge=1, strict=True)`. Reviewer: "not worth a round-trip on
its own."

### NIT 5 — No upper bound on `expected_hops`; `10**18` validates. COSMETIC.

Module 3 derives the runaway ceiling as `max(6, 2 x expected_hops)`, so an absurd hand-edited value
effectively disables the hop guard. The only writer computes `ceil(total_tasks/2.5)`. Raised as a
plan observation, not a request.

### NIT 6 — `SpawnPolicy` placement splits the type-alias block. COSMETIC.

The four pre-existing aliases are contiguous; `SpawnPolicy` sits after a blank line with
`class Handoff` then inserted between the alias region and `class ArtifactPaths`. NAMING is right —
`sdd_session.py`'s convention is named aliases (`Tier`, `ReviewMode`, `DispatchMode`,
`RequirementLevel`), unlike `plan.py` which inlines field-level literals. Purely placement.

## Verified-correct

- **Backward compatibility, with a WORKING negative control.** A genuine pre-v2 manifest exists in
  this worktree: this feature's own `.sdd-session.json`, whose 15 keys do not include `handoff`
  (`json.load` + `'handoff' in d` → `False`). `validators.py session <it>` → rc=0. Negative control:
  same file with `bogus_key` injected → rc=1, "Extra inputs are not permitted". Positive control:
  same file with a valid handoff block added → rc=0. The check can fail, and does not.
  - Side note, not a finding: the implementer reported the backward-compat CLI "had no target"
    because the *2026-07-22* manifest is absent — but this feature's OWN pre-v2 manifest was
    available. The spec reviewer ran it and this reviewer re-ran it independently; both rc=0.
    Nothing is unverified, only unverified *by the implementer*.
- **`spawn_policy` absent-key parity across all three layers — clean.** Model absent → `"auto"`
  (measured); `_handoff_support` CLI absent/unrecognized → `"auto"`; `spawn-handoff-session.sh`
  re-defaults → `"auto"`. Under B4's all-or-nothing reading `{"expected_hops": N}` is a legal shape,
  so this parity is load-bearing, and it holds. (The INVALID-value handling diverges — Finding 2.)
- **Round-trip, both dump modes.** JSON mode is the committed test. Python mode additionally
  confirmed: `SddSession.model_validate(s.model_dump()).handoff == s.handoff` → `True`. Coverage
  note only: no committed test round-trips a POPULATED handoff through `model_dump()` (MINIMAL_SESSION
  carries none, so the golden test exercises the `None` path). Low risk; Task 6 materializes via
  `model_dump_json()`.
- **B4's pinned reading implemented faithfully** (verified, not re-litigated): `{}` and
  `{"spawn_policy":"ask"}` both raise; absent-entirely validates; `model_fields["handoff"].default is None`.
- **Sibling-pattern consistency.** `Handoff` matches `plan.py`'s `IntegrationTest` /
  `Plan.integration_test` shape — nested `StrictModel`, optional parent field defaulting to `None`,
  no schema bump (`CURRENT_SCHEMA_VERSION = 1` untouched, absent from the diff).

**Recommendation:** one remediation round adding the three tests. No production-code change needed
for Findings 1-3; all three assertions pass against the code exactly as committed, so the fix carries
zero behavioral risk and the cycle can close on the next review.
