# Task 6 — Code Quality Review (round 1, adversarial)

**Verdict: CHANGES_REQUESTED**

**All findings are test-strength, not code defects — the implementation is correct as written.** But
guards that no test can falsify get deleted green by the next refactor, which is the exact shape that
produced Task 5's `StrictModel`/`BaseModel` gap. **Twelve mutations survived, ten of them
over-permissive.** Reviewer: general-purpose subagent (opus).

## Harness

Mutate one anchored string → `rm -rf` all `__pycache__` → scoped pytest with `-p no:cacheprovider` →
restore. **Anchor uniqueness enforced** — M9 initially aborted with `MUTATION-ANCHOR-ERROR count=0`
rather than silently no-op'ing (a no-op mutation reads as "survived").
**Baseline** `21 passed` scoped / `687 passed` full. **Positive control:** `HOP_DIVISOR 2.5→2` →
`3 failed, 18 passed` — harness proven live, no `.pyc` shadowing.

## Mutation battery

| # | Mutation | Direction | Caught? | By |
|---|---|---|---|---|
| PC | `HOP_DIVISOR 2.5→2` | — | **YES** (3 failed) | control |
| M1 | `expected_hops`: drop `isinstance(total_tasks, bool)` | **OVER-PERM** | **NO** | — |
| M2 | `derive_total_tasks` step 1: drop bool guard | **OVER-PERM** | **NO** | — |
| M3 | `task_ids` loop: drop bool guard | **OVER-PERM** | **NO** | — |
| M4 | `derive_expected_hops`: `eh >= 1` → `eh >= 0` | **OVER-PERM** | **NO** | — |
| M5 | `derive_expected_hops`: drop `eh` bool guard | **OVER-PERM** | **NO** | — |
| M6 | drop `isinstance(m, dict)` on module entry | crash-dir | **NO** | — |
| M7 | `len(tr) == 2` → `len(tr) >= 2` | **OVER-PERM** | **NO** | — |
| M8 | `tr[0] <= tr[1]` → `<` | RESTRICTIVE | **NO** | — |
| M9 | `isinstance(h, dict)` → `hasattr(h,'get')` | equivalent | **NO** | — |
| M10 | `CEILING_FACTOR*exp` → `-1` | RESTRICTIVE | YES | `test_floor_factor_and_none` |
| M11 | `if exp is None` → `if not exp` | equivalent | **NO** | — |
| M12 | materialize `is None` → `or "auto"` | **OVER-PERM (consent bypass)** | YES | `test_off_survives...` |
| M13 | delete precedence step 2 entirely | RESTRICTIVE | YES | `test_precedence_2` |
| M14 | `math.ceil(...)` → `max(1, round(...))` | RESTRICTIVE | **NO** | — |
| M15 | materialize reimplements formula (drops import) | SSOT breach | **NO** | — |
| M16 | `tier == "micro"` → `tier != "standard"` | **OVER-PERM** | **NO** | — |
| M17 | materialize: `expected_hops(total_tasks, tier)` → `..., "standard")` | **OVER-PERM** | **NO** | — |
| M18 | materialize special-cases `False → "auto"` | **OVER-PERM (consent bypass)** | YES | `test_off_survives...` |
| M19 | swap precedence steps 2 ↔ 3 | contract-order | **NO** | — |

**Ran and explicitly NOT filed** (survival is not a defect): **M11** (`max(6,0)==6`, behaviorally
identical — equivalent mutant); **M9** (a non-dict has no `.get`, both forms take the same branch);
**M6** (produces `AttributeError` — a crash, not silent wrong acceptance); **M8** folded into Minor 3.
**Restore verified:** sha256 MATCH vs `git show 9b32c25:<path>` for all four files;
`git status --porcelain -- skills tests` empty; post-restore `21 passed`.

## Ruling on the escalated `exit_code != 0` question

**SUBSTANTIVE. The implementer should not have declined it.**

The test is named `test_off_survives_and_bare_off_is_never_coerced_to_auto` — it asserts a REASON in
its name while its body asserts only *a* failure. M12/M18 are caught solely because the mutant
**succeeds**; the instant anything else makes materialization fail earlier (a new required frontmatter
key, a stricter plan gate, a path change), the test goes **vacuously green with the consent bypass free
to regress**. That is the identical "these tests cannot distinguish it" argument the plan itself used
three tasks upstream to justify `test_extra_key_rejected`. Declining it is inconsistent with the plan's
own precedent.

Failure identity is precise and available — measured: `Manifest validation failed: 1 validation error
for SddSession / handoff.spawn_policy / Input should be 'auto', 'ask' or 'off'
[type=literal_error, input_value=False, input_type=bool]`, exit 1.

**Recommended form** — `_mf(ok=False)` already returns the full `r`, so **no helper change is needed**,
which removes the "plan text is deliberate" objection entirely:
```python
r = self._mf(extra_frontmatter="handoff_spawn: off", ok=False)
assert "spawn_policy" in r["stderr"]
```

## Findings

### Major 1 — `test_micro_tier_expected_hops_is_one` is VACUOUS; materialize's tier propagation is entirely unpinned (substantive)
It passes `tasks=[{"id":0},{"id":1}]`, but **`ceil(2/2.5) == 1`, which is also the micro answer** — the
test passes identically whether tier is honored or ignored. Measured: **M17** (hardcode `"standard"` at
the call site) → `21 passed`. **Fix, verified to discriminate before prescribing** — drop the `tasks=`
override and use the default 5-task plan:
```python
def test_micro_tier_expected_hops_is_one(self):
    assert self._mf(tier="micro")["handoff"]["expected_hops"] == 1
```
Probe: `micro → expected_hops 1`, `standard → 2`, both exit 0 (materialize only checks
`tier in TIER_PROFILES`; `validate-plan.py`'s micro+>3-tasks WARNING is a different script
`run_materialize` never invokes).

### Major 2 — the Decision 9 formula, the one thing this file exists to be SSOT for, is not pinned to `ceil` (substantive)
Tested at total = 1, 5, 19 — **every one a point where `ceil` and `round` agree.** Measured: **M14**
(`math.ceil(t/2.5)` → `max(1, round(t/2.5))`) → `21 passed`. First divergence is total = 6:
`ceil(2.4) = 3` vs `2`. **Fix:** one assertion — `assert expected_hops(6, "standard") == 3`.

### Major 3 — the reachable bool/range guards in the two `derive_*` functions are unpinned (substantive)
These read **raw manifest JSON**, which carries `true`, and `derive_expected_hops` is what Module 3's
planned `expected-hops --manifest` calls against a file on disk. Reachability is real.

| Mutation | Consequence if the guard is later deleted |
|---|---|
| M2 `total_tasks: true` | returns `True` (== 1) as the task total |
| M3 `task_ids: [true, 2]` | `{True, 2}` collapses to `{1, 2}` — silent undercount |
| M5 `expected_hops: true` | returned verbatim as the hop budget |
| M4 `eh >= 0` | `expected_hops: 0` accepted verbatim instead of re-derived |
| M7 `len(tr) >= 2` | a 3-element `task_range` silently computes from `tr[0]`/`tr[1]` |

**On M4 the reviewer traced downstream impact rather than asserting severity:** `expected_hops: 0`
reaching Module 3 gives `MAX_HOPS=$((0*2))=0` → `[ 0 -lt 6 ]` → 6; Module 4's `hop_ceiling(0)` →
`max(6,0)` → 6. **The floor rescues it, so this is a test-strength gap, not a live bug** — but it is the
degradation contract failing open, and the `Handoff` model's `ge=1` only covers what WE write, which is
precisely why `derive_expected_hops` exists. **Fix:** one negative test per function.

### Major 4 — the contract's precedence ORDERING between steps 2 and 3 is unpinned (substantive)
Contract Constraints name it: "union of module task IDs → inclusive `task_range`". **No test supplies
both** — `test_precedence_2` has modules and no `task_range`; `test_precedence_3` has `modules: []` and
a `task_range`. Measured: **M19** (move the `task_range` block above the module-union block) →
`21 passed`. **Fix:** `derive_total_tasks({"total_tasks": 0, "modules": [{"task_ids": [0,1,2]}], "task_range": [0, 20]}) == 3`.

### Minor 1 — Task 7's `_write_report` fixtures are MODEL-INVALID for two of four calls (substantive; bites Task 7)
Measured by round-tripping the exact body `_write_report` writes through `ImplementerReport.model_validate`:
`(1,'DONE','verification') → OK`; `(2,'DONE_WITH_CONCERNS') → FAIL`; `(3,'BLOCKED') → OK`;
`(4,'DONE') → FAIL`. `files_changed_non_empty_for_done` exempts `task_type == "verification"` but rejects
`DONE`/`DONE_WITH_CONCERNS` with empty `files_changed`. Task 7's planned assertions
(`count_tasks_done(...) == 2` twice) hold only if it raw-YAML-parses; Contract Constraints' wording
("frontmatter **parses** AND has status") suggests it does, but `validate-report.py` model-validates,
so that is the obvious idiom an implementer reaches for — silently yielding 0 and 1 instead of 2 and 2.
**Fix (better than documenting the ambiguity, which leaves the trap):** make the fixtures model-valid by
giving `_write_report` a non-empty `files_changed`. `count_tasks_done` keys on status, so content is
irrelevant to Task 7's assertions, and the helper then works under BOTH readings. Keep the
`task_type="verification"` + empty-`files_changed` case as a deliberate variant — it is the exemption
Task 7 must honor.

### Minor 2 — `hop_ceiling` has no CLI seam; Module 3 will duplicate its literals in bash (substantive; actionable in Task 7)
`module-4` imports and calls `hop_ceiling`. `module-3` instead hardcodes
`DERIVED=$((EXPECTED_HOPS * 2)); [ "$DERIVED" -lt 6 ] && DERIVED=6` — **twice**. Task 7's planned CLI
exposes `tasks-done`, `expected-hops` and the stall subcommand but **no `hop-ceiling`**, so Module 3's
bash *cannot* call the SSOT. One consumer importing and one re-deriving the same `2` and `6` is exactly
the `_midpoint.py` anti-pattern this file's own docstring cites as its rationale. **Fix:** add
`hop-ceiling --expected <n|unknown>` in Task 7 and have Module 3 call it.

### Minor 3 — `tr[0] <= tr[1]` boundary tested only from the invalid side (substantive)
**M8** (`<=` → `<`) → `21 passed`. A single-task module (`task_range: [5,5]`) would silently derive
`None` instead of `1`. Same class as Task 5 round 1's boundary finding, and single-task ranges are real
here. **Fix:** `derive_total_tasks({"task_range": [5, 5]}) == 1`.

### Minor 4 — "absent-with-WARNING" is asserted in a docstring but nothing warns (substantive)
`/usr/bin/grep -niE "warn|stderr|logg"` over the file returns that docstring line and nothing else. The
plan routes the degradation to the spawn-time reader, so the placement is defensible — but the
parenthetical reads as ALREADY SATISFIED, and a Task 7 implementer has no cue the warning is still owed.
**Fix:** one docstring word — "(caller warns; see Task 7 CLI)".

### Nit 1 — `test_block_wins_else_derive_else_none` packs three branches into one test (cosmetic)
First failing assert masks the other two; sibling classes split. Split or parametrize.

### Nit 2 — SSOT import not pinned, but CONSISTENT with the named precedent (cosmetic)
**M15** (materialize drops the import and reimplements locally) → `21 passed`. **The reviewer checked
whether the cited precedent does better:** `/usr/bin/grep -rn "_midpoint" tests/` returns only midpoint
*behavior* tests — **no test pins `_midpoint`'s import either.** So this is consistent with the
established pattern, not a regression against it. **"Filing it higher would have been the over-claim."**

## Verified correct

- **Consent bypass genuinely gated** — M12 and M18 both caught; the `is None` form is load-bearing. The
  reviewer confirmed the implementer's control independently rather than accepting the report's claim.
- **`expected_hops`'s `isinstance(int)` guard is load-bearing** — `test_invalid_total_raises` passes
  `"7"`/`None`; without it those raise `TypeError`, not `ValueError`. Only the bool half is unpinned
  (M1), and M1 is defense-in-depth: the only callers pass `len(tasks)` or already-bool-filtered values.
- **Materialize wiring is at the right point** — `tier` is validated against `TIER_PROFILES` (returns 1
  on invalid) and `total_tasks == 0` returns 1, both BEFORE the handoff block, so `expected_hops` can
  never raise from this call site. No ordering hazard.
- **Idempotency preserved** — the write path compares `json.loads(model_dump_json())` against the
  existing file; the handoff block is a pure function of parsed frontmatter, so repeat runs still hit
  "Manifest up-to-date". A pre-v2 manifest re-materializes once — expected and benign.
- **Backward compat / B4** — `handoff: Handoff | None = None`, all-or-nothing, `CURRENT_SCHEMA_VERSION`
  still 1. **B7** — the file is genuinely in scan scope (`os.listdir` lists it) and carries no
  annotations; gate `PASS: 160 / FAIL: 0 / WARNING: 2`.
- **`_handoff_support.py` is well-shaped as an SSOT** — naming, `_`-prefix and the mid-file
  `# noqa: E402  (single source of truth)` comment all mirror `_midpoint.py`; stdlib-only at import as
  documented. Two cosmetic docstring gaps vs the precedent (no Args/Returns; advertises tasks_done +
  lazy PyYAML, neither present until Task 7) — forward-looking by plan design, not filed.
- **Shared test helpers correctly aimed at Task 7** except Minor 1: `VENV_PY`/`SUPPORT` resolve
  correctly, `_log`'s newline-join matches the `handoff-spawn.log` one-record-per-line format.

**Stopping rule:** every finding above Nit is **substantive**, so this does not meet "cosmetic AND approved."
