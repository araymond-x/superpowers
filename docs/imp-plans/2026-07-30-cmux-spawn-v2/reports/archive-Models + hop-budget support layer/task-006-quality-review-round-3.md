# Task 6 — Code Quality Review (round 3, adversarial)

**Verdict: APPROVED**

Both round-2 findings are **CLOSED, each proven by mutation as the SOLE failure**, each new assertion
proven **non-vacuous by measurement** (guarded and mutated answers differ at the chosen input). The fix
is **genuinely test-only** (verified independently). Anchor integrity holds.

Round 3 ran **20 mutation runs — 13 hunt mutations no prior round attempted, plus the 3 round-2 closures,
the 2 anchor-integrity re-mutations, the positive control, and 1 fix-verification composite** — driven by
the question the prompt demands: *which of these makes the code ACCEPT something it should not?*
**Every over-permissive mutation
reachable through any shipped or planned consumer is now caught.** What survives is either unreachable
from every consumer (Minor 1), forward-looking plan text for Task 7 (Minor 2), or crash-directional /
contrived (Nits). **No Blocker, no Major. The substantive surface is closed.**

---

## Harness

- **Positive control:** `HOP_DIVISOR 2.5 → 2` → **`5 failed, 26 passed`**. Harness live. (Round 2 measured
  `4 failed` at baseline 28; the 5th is the new `test_unknown_tier_behaves_as_standard`, which also
  consumes the divisor — expected, not a discrepancy.)
- **Anchor uniqueness enforced** on every mutation by a Python-counting wrapper that aborts with
  `MUTATION-ANCHOR-ERROR count=N` unless the literal occurs **exactly once**. Two attempts were rewritten
  after the counter reported `count=2` on an over-short anchor rather than silently no-op'ing (a no-op
  reads as SURVIVED).
- **`__pycache__` cleared before AND after every mutation run** (`find … -print0 | xargs -0 rm -rf`,
  excluding `.venv`); every run passed `-p no:cacheprovider`.
- **All recursive sweeps used `/usr/bin/grep`**, never the shell's ugrep wrapper.
- **Restore proven after every single mutation**: `git checkout --` then sha256 re-compare → `RESTORE-OK`
  printed on all 20. **No `git stash`. Nothing committed.**
- **Scope proven complete, not inherited:** `/usr/bin/grep -rn "_handoff_support" tests/ skills/ docs/…`
  → the only code importer is `materialize-manifest.py:60`; `skills/scripts/models/sdd_session.py:19` is a
  docstring mention, not an import. So a scoped "survived" is not understated.

### Baselines — all three CHECKED, all three MATCH the controller's numbers

| Scope | Measured | Controller's claim |
|---|---|---|
| `test_handoff_support.py` alone | **19 passed** | 19 ✓ |
| `+ test_materialize_manifest.py` (round 2's scope) | **31 passed** | 31 ✓ |
| Full `tests/unit/` | **697 passed**, 1 warning, 156.96s | 697 ✓ |

---

## 1. Closure by mutation — both round-2 findings CLOSED, each the SOLE failure

| Finding | Mutation applied (exact) | Round 2 | Round 3 | Sole failure named |
|---|---|---|---|---|
| Major 1a | `derive_expected_hops`: `expected_hops(total, manifest.get("tier") or "standard")` → `expected_hops(total, "standard")` | 28 passed | **`1 failed, 30 passed`** | `TestDeriveExpectedHops::test_tier_propagates_from_manifest` |
| Major 1b (M16) | `expected_hops`: `if tier == "micro":` → `if tier != "standard":` | 28 passed | **`1 failed, 30 passed`** | `TestExpectedHops::test_unknown_tier_behaves_as_standard` |
| Minor 1 | `derive_total_tasks`: `all(isinstance(x, int) and not isinstance(x, bool) for x in tr)` → `all(isinstance(x, int) for x in tr)` | 28 passed | **`1 failed, 30 passed`** | `TestDeriveTotalTasks::test_bool_in_task_range_is_not_derivable` |

Each mutant is caught by **exactly one** test, and that test is the one whose name claims the property.
Round 1's M16 — *listed as over-permissive-and-uncaught and then never dispositioned* — is now closed.

## 2. Non-vacuousness — measured, not argued

Each new assertion was checked against the question *could this pass whether or not the property holds?*
The guarded and mutated answers **differ at the chosen input** in all three cases:

| Assertion | Guarded | Mutated | Differ? |
|---|---|---|---|
| `expected_hops(19, "weird") == 8` | **8** | **1** (`tier != "standard"` → micro short-circuit) | ✓ |
| `derive_expected_hops({"total_tasks": 19, "tier": "micro"}) == 1` | **1** | **8** (hardcoded `"standard"`) | ✓ |
| `derive_total_tasks({… "task_range": [True, 4]}) is None` | **None** | **4** (`4 - True + 1`) | ✓ |

None repeats this feature's vacuousness pattern: `19` is not a point where the tier branches agree
(`ceil(19/2.5)=8 ≠ 1`), unlike the `total=2` micro test round 1 had to replace; and `[True, 4]` is not a
point where the bool guard is a no-op.

**Adversarial cross-check on the first row:** `test_unknown_tier_behaves_as_standard` also fails under the
positive control (`HOP_DIVISOR`). That is *shared* coverage with `test_formula_standard`, not vacuousness —
M16 kills it **uniquely**, which is the discriminating measurement.

### Do the new assertions pin the RIGHT answer, not merely a discriminating one?

Discrimination is necessary but not sufficient: a test can uniquely kill a mutant and still cement wrong
behavior. Two assertions are the spec verbatim — `derive_expected_hops({19,"micro"}) == 1` is Decision 9,
and `task_range:[True,4] → None` is the bool-guard family's semantics. The third,
`expected_hops(19, "weird") == 8`, was **inherited from round 2's recommended fix**, so I checked it against
the spec rather than only against M16:

> `spec-distilled.md:32` — *"**`expected_hops` formula:** `ceil(total_tasks / 2.5)` standard tier; `1` micro."*

**The spec is silent on an unrecognized tier** — it defines the two known tiers and no fallback; the plan
files add nothing. **So the assertion pins current behavior deliberately, and I am not manufacturing a
finding from silence.** Recording the direction so a future round need not re-derive it: unknown-as-standard
is the *looser* choice (a typo'd `"mikro"` yields 8 hops / ceiling 16 rather than 1 / ceiling 6). Three
things bound that: `materialize-manifest.py` rejects any tier outside `TIER_PROFILES` before the call, so
only raw hand-edited or legacy JSON reaches it; the derived ceiling is a *default* that
`SUPERPOWERS_CMUX_MAX_HOPS` overrides absolutely, and `.handoff-hops` remains the fail-closed runaway guard;
and unknown-as-standard is **consistent with the absent-tier default** the same expression already encodes
(`manifest.get("tier") or "standard"`), whereas unknown-as-micro would under-budget a long plan into a
premature refusal. Defensible and consistent — **not a finding.**

## 3. The fix is genuinely test-only — verified independently, not inherited

- `git diff --stat 9b32c25 HEAD -- skills/` → **empty output**.
- `git diff --name-only 65ac0ac bf4343a` → **`tests/unit/test_handoff_support.py`** only.
- sha256 vs `git show 9b32c25:<path>`:
  - `_handoff_support.py` → `ccffc2b24cfbd948ba7d8539249f1591ac799ca10dcb46fb121c971ecf7410cd` **MATCH**
  - `materialize-manifest.py` → `2de5dfa6690af63ad15dbc2864316c4b7cd15241e792f740b2093d91637b9335` **MATCH**

## 4. Anchor integrity — intact

The two guards for which `test_bool_never_counts_as_a_total_or_a_task_id` is the sole-failure anchor
(round 2's F5a/F5b) were re-mutated **after** the fix:

| Mutation | Result | Named |
|---|---|---|
| drop `not isinstance(t, bool)` (step-1 total) | `1 failed, 30 passed` | `test_bool_never_counts_as_a_total_or_a_task_id` |
| drop `not isinstance(tid, bool)` (task_ids) | `1 failed, 30 passed` | same |

The decision to give the 4th bool guard its own test name rather than a third assertion on the packed
anchor is **vindicated by measurement**: the anchor still uniquely identifies which of its two guards died,
and the new test uniquely identifies the third. Had the assertion been appended, all three guards would
have collapsed onto one name.

---

## NEW findings

### Minor 1 — the FIFTH bool guard, in `expected_hops`, is unpinned; the over-permissive mutant survives all 31 tests

Rounds 1 and 2 worked through this module's bool-guard family: round 1 found three (`total_tasks`,
`task_ids`, `expected_hops` block), round 2 found the fourth (`task_range`). **There is a fifth**, inside
`expected_hops`'s own validator, and nobody has mutated it.

```
if not isinstance(total_tasks, int) or isinstance(total_tasks, bool) or total_tasks <= 0:
                                    → if not isinstance(total_tasks, int) or total_tasks <= 0:
```
**Result: `31 passed` — survives.**

**Measured consequence (over-permissive, and silent):**

| | guarded | mutated |
|---|---|---|
| `expected_hops(True, "standard")` | **raises `ValueError`** | **returns `1`** (`ceil(True/2.5)`) |

The function's own docstring states the contract this breaks — *"Raises on garbage — callers that must
degrade catch ValueError (never divide by garbage)."* `True` is garbage; under the mutant the caller gets a
bogus hop budget of `1` with **no signal at all**, which is precisely the accept-what-it-should-not
direction. `test_invalid_total_raises` iterates `(0, -3, "7", None)` — every kind of garbage **except** a
bool, while all four sibling bool guards now have tests.

**Reachability — measured, and honestly weak.** I traced every consumer:
- `materialize-manifest.py:121` passes `total_tasks = len(tasks)` — always a real int. Not reachable.
- `derive_expected_hops` passes `derive_total_tasks(...)`, whose four bool guards (all now pinned) mean no
  bool can escape. Not reachable.
- **Task 7's planned CLI** (`module-2-models-budget.md`, `_cli`) routes `expected-hops --manifest` through
  `derive_expected_hops`, **not** a direct call — so it is not reachable there either.

So this is a deliberate, working guard that no current or planned path can reach. That caps it well below
Major and is why I am **not** filing it as one. It is still worth one token: the enumeration is otherwise
complete, and the guard is the only member of its family a refactor could delete unnoticed.

**Fix (verified to discriminate, as the sole failure):** add `True` to the existing tuple.
```python
for bad in (0, -3, "7", None, True):
```
Measured with fix + mutation applied together → **`1 failed, 30 passed`**, named
`TestExpectedHops::test_invalid_total_raises`. Zero new test functions.

### Minor 2 — forward-looking, for the Task 7 dispatch: the planned CLI tracebacks on a non-object manifest, violating its own stated contract

Task 7's planned `_cli` (`module-2-models-budget.md`) declares *"prints ONE value on stdout. Exit 0 with a
value … exit 2 = usage error"* and the Task 7 checkbox says *"degradation is observable, never an
exception."* Its guard is:

```python
try:    manifest = json.load(open(a.manifest, encoding="utf-8"))
except Exception:  manifest = {}
```
That catches a **corrupt** file. It does **not** catch a file containing *valid JSON that is not an object*
— `json.loads` accepts `null`, `5`, `"abc"`, `[1,2]` and returns a non-dict, which then reaches
`derive_expected_hops` unprotected.

**Measured against the delivered Task 6 module:**
```
derive_expected_hops([1, 2])  RAISES AttributeError: 'list' object has no attribute 'get'
derive_expected_hops(5)       RAISES AttributeError: 'int'  object has no attribute 'get'
derive_expected_hops('abc')   RAISES AttributeError: 'str'  object has no attribute 'get'
derive_expected_hops(None)    RAISES AttributeError: 'NoneType' object has no attribute 'get'
```
An uncaught traceback and a non-0/2 exit — exactly what the contract forbids. Reachable via a manifest
truncated or overwritten to `null` / `[]`, which parses fine.

**This is NOT a defect in Task 6's delivered code**, whose signature is a manifest *dict*, and I verified
that invariant holds: for an arbitrarily hostile **dict**, nothing raises —
`derive_expected_hops({"handoff":"x","modules":{"a":1},"task_range":"zz","total_tasks":"9","tier":[1]})`
→ `None`. It is a **plan-text item for the Task 7 dispatch**, the same disposition round 2 gave its Minor 2.
**Fix at dispatch:** one line after the `try/except` —
```python
if not isinstance(manifest, dict): manifest = {}
```

---

## Nits (contrived or crash-directional — recorded so round 4 need not re-run them)

- **Nit 1 — float tolerance on the handoff block is the only *silent* survivor.**
  `isinstance(eh, int)` → `isinstance(eh, (int, float))` → **`31 passed`**. Measured:
  `derive_expected_hops({"handoff": {"expected_hops": 9.5}, "total_tasks": 5})` = **2** guarded, **9.5**
  mutated → `hop_ceiling(9.5)` = **19.0**, a float hop budget propagating silently.
  **Held to a Nit deliberately, per the standing obligation:** the *plausible* minimal edit (simply dropping
  `isinstance(eh, int)`) is **caught** — `3 failed, 28 passed` (TypeError comparing `None >= 1`). Only my
  contrived `(int, float)` rewrite survives. Optional one-liner if ever wanted:
  `assert derive_expected_hops({"handoff": {"expected_hops": 9.5}, "total_tasks": 5}) == 2`.
- **Nit 2 — the same float tolerance on `total_tasks` and on `task_range` elements** also survives
  (`31 passed` each) but is **crash-directional**, not over-permissive: a float total reaches
  `expected_hops`, which rejects non-ints and raises. Lower priority than Nit 1 by the M6 precedent.
- **Nit 3 — `X or []` / `or {}` → `.get(X, default)`** survives at all three sites (`modules`, `task_ids`,
  `handoff`; `31 passed` each). Purely **crash-directional** — only an explicit `null` in the manifest
  differs, and it crashes rather than being accepted. Round 1 dispositioned M6 on exactly this reasoning.

## Mutations run and CAUGHT (beyond the three closures) — no finding

`HOP_DIVISOR` (control) · `math.ceil → int(...) or 1` (`2 failed`) · `if ids:` → `if ids is not None:`
(`7 failed`) · `t > 0` → `t >= 0` (`8 failed`) · drop `isinstance(eh, int)` minimally (`3 failed`) ·
F5a step-1 bool · F5b task_ids bool.

## Equivalent mutants (measured — NOT defects, do not re-file)

- `manifest.get("tier") or "standard"` → `manifest.get("tier", "standard")` → `31 passed`. **Verified
  equivalent**, not a coverage gap: a `None`/empty tier yields a non-`"micro"` value either way, so the
  formula's answer is identical. Nothing to pin.
- `hop_ceiling`: `if exp is None:` → `if not exp:` — `exp == 0` is unreachable (`derive_expected_hops`
  returns `>= 1` or `None`), and `hop_ceiling(0)` = `max(6, 0)` = 6 = the `None` answer regardless.
  Indistinguishable by construction.

## Do-not-refile list — honored

M6, M1, M15 not re-filed. `TestHopCeiling.test_floor_factor_and_none` not re-filed (round 2 measured it
non-vacuous). Round 2's Minor 2 (`module-2-models-budget.md`, the `_write_report(...)  # empty
files_changed OK` comment) is out of scope here and remains its **own** deferred Task 7 row — my Minor 2 is
a **different line in the same file** (the `_cli` `try/except`) and does **not** supersede or satisfy it.

## Deferred rows requested — "disposition ≠ done"

APPROVED is a stopping point, so a recommendation with no checkbox evaporates. **Two NEW rows for the Task 7
dispatch** (in addition to round 2's existing Minor-2 row, which stands):

| # | Row | File | Change |
|---|---|---|---|
| R3-1 | Pin the 5th bool guard (Minor 1) | `tests/unit/test_handoff_support.py` | `for bad in (0, -3, "7", None)` → `for bad in (0, -3, "7", None, True)` — one token, no new test function |
| R3-2 | Harden the planned CLI against a non-object manifest (Minor 2) | `docs/imp-plans/.../module-2-models-budget.md` (`_cli` body) | add `if not isinstance(manifest, dict): manifest = {}` after the `try/except` |

## Gates

Full `tests/unit/` **697 passed**. `validate-all-skills.py` **not re-run — N/A**: `skills/` is byte-identical
to `9b32c25` by sha256 (verified above), so round 2's `PASS: 160 / FAIL: 0 / WARNING: 2` still holds by
construction. Recorded rather than left silent, since round 2 listed it.

---

## Final restore verification

- sha256 vs `HEAD` → **MATCH** for `_handoff_support.py`, `materialize-manifest.py`,
  `test_handoff_support.py`, `test_materialize_manifest.py`.
- `git status --porcelain -- skills tests` → **empty**.
- Post-restore full suite → **697 passed**. `__pycache__` cleared.
- No `git stash` used. Nothing committed. `.venv` symlink untouched.

---

## Verdict: **APPROVED**

Round 2's Major 1 and Minor 1 are closed, proven by the exact mutations round 2 measured as surviving, each
now the sole failure, each new assertion non-vacuous by measurement. The fix is test-only. Anchor integrity
is intact. All three baselines match.

**The substantive surface is closed.** I ran the over-permissive sweep this feature's defects have always
lived in, including 13 hunt mutations no prior round attempted, and **every over-permissive mutant reachable
from any shipped or planned consumer is caught**. The two Minors are (1) a guard no consumer can reach,
fixable with one token in an existing tuple, and (2) plan text for a task not yet dispatched. Neither
indicates the delivered code is wrong. By the stopping rule — findings cosmetic **and** reviewer approves —
both conjuncts hold.

The third new assertion was additionally checked **against the spec, not only against its mutant**: the spec
is silent on an unrecognized tier, so it pins current behavior deliberately and consistently with the
absent-tier default — verified, not assumed, since it was inherited from round 2.

**Non-blocking, but carried as rows R3-1 and R3-2 above** so they survive this stopping point: fold Minor 1's
single token into the existing tuple, and add the `isinstance(manifest, dict)` line to the planned CLI.
