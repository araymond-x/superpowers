# Task 9 — Adversarial Code Quality Review

**ASSESSMENT: CHANGES_REQUESTED** (17th consecutive adversarial quality review to find a real defect on a green upstream.)

## Method

Baseline full suite 773; the three spawn files 139 passed in 143s. Nine mutations, each with the anchor asserted to match exactly once, the diff printed and READ (this caught a perl `$`-interpolation accident that ate `$CAPTURED_REF` — the class that manufactures meaningless REDs), `__pycache__` cleared, `-p no:cacheprovider`, explicit paths, restore by file copy + `diff -q`. Harness positive control **M-I** (disable the ref-shape check) went RED, proving the harness can kill.

| # | Mutation | Result |
|---|---|---|
| M-I | ref-shape check always passes | **RED** x1 (positive control) |
| M-C | drop `${SPAWN_SURFACE_REF:--}` sentinel | **RED** x2 |
| M-M | `rename-tab --workspace` → caller's workspace both paths | **RED** x1 |
| M-A | `if(index($0,"[selected]"))` → `if(0)` | **SURVIVED** |
| M-L | fallback surface ref-shape gate always passes | **SURVIVED** |
| M-B | drop `BUDGET_FLAG` from the `handshake=timeout` record | **SURVIVED** |
| M-N | drop `shq` from forwarded knob values | **SURVIVED** |
| H-1 | `_did_not_spawn` re-spells `SPAWN_VERBS` locally | **SURVIVED** (13/13 green) |
| V-1 | remove `run_spawn`'s `kw.setdefault("cmux_body", …)` | 33 failed / 20 passed |

## Strengths

- The ref made load-bearing is real hardening with the right failure direction: a fabricated ref would address a target nobody can drive while the run reported success. `capture_cmux_ref` is a genuine SSOT for every ref-returning verb.
- Capturing to a temp file so `$?` stays the verb's own rc, and awk rather than `read` (which drops a final unterminated line — green stub, 100% production failure), are both correctly reasoned in-code.
- `TOPOLOGY_FIELD` computed once above three outcome records, instead of the fence's per-branch recompute, improves on the plan.
- The register is unusually honest: the inferred `--workspace TEST-WS` shape, the orphan concern widened to its exit-0 half, and the OP-1 pre-emption are all declared rather than smuggled.

## Answers to the three named targets

### Target 1 — `assert _did_not_spawn.__module__` is vacuous. CONFIRMED, and worse than stated.

Not stopped at the analytic argument: **ran the exact drift the adjacent comment claims to catch** — replaced `_did_not_spawn`'s body with a locally re-spelled verb tuple. **All 13 tests passed.** The comment "helper is imported, not re-spelled here" describes a check that does not exist, in the file whose entire subject is a fail-open.

Non-vacuous replacement, positive-controlled BOTH directions (RED against the mutant, GREEN against landed code):

```python
def test_did_not_spawn_delegates_to_the_shared_helper(monkeypatch, tmp_path):
    import sys as _sys
    sentinel = object()
    monkeypatch.setattr(_sys.modules[__name__], "did_not_spawn", lambda log_text: sentinel)
    assert _did_not_spawn(tmp_path) is sentinel
```

Note `assert did_not_spawn.__module__ == "spawn_handoff_helpers"` would ALSO survive the mutant (the import stays; only the call site is replaced) — **delegation must be pinned, not provenance.**

### Target 2 — substance complete, name wrong.

Measured (**M-M**): scoping `rename-tab` to `$CMUX_WORKSPACE_ID` instead of `$SPAWN_WORKSPACE_REF` — indistinguishable on the surface path, wrong on the fallback — killed **exactly one test: `..._on_the_fallback`**. The "both topologies" test **survived its own subject.** Coverage across both paths IS complete and mutation-proven; the defect is naming plus the undeclared fence departure (the fence specified one test; two shipped). This is the shape where a reader deletes the sibling believing the survivor covers it.

### Target 3 — the shadowing, measured rather than argued.

Removing `kw.setdefault(...)`: **33 failed / 20 passed.** Of the 33, **16 are pre-existing** non-`TestSurfaceTopology` tests — the shadow is doing real work, restoring premises Step 3 would otherwise have broken. The spec review's analytic acceptance is **empirically correct for the tests it named**: the 20 survivors are refusal-path and pure-fixture tests, passing identically either way. Residual risk is structural, not present-tense: a future test silently inherits v2, and a refusal test asserting bare `returncode == 3` could be satisfied by a *spawn* failure rather than the refusal it names. Recommend the shadow assert its own premise, or refusal tests pin the message rather than the rc alone. Not blocking.

## Issues

### Important

**I1 — Vacuous claimed pin in the fail-open file** (`test_spawn_handoff_hardening.py:120`). See Target 1. Replacement supplied and positive-controlled. `test-vacuity`

**I2 — `shq` on forwarded knob values has ZERO coverage (a guard nobody claimed).** **M-N** — `$knob=$(shq "$v")` → `$knob=$v` — **survived all 139 spawn tests.** This is the only thing between operator-controlled env values and a shell line delivered into a live terminal by `cmux send`:

```
QUOTED:   KNOB='a b; touch /tmp/PWNED'
UNQUOTED: KNOB=a b; touch /tmp/PWNED
```

`SUPERPOWERS_CMUX_QUOTA_TOOL` (a path) and `SUPERPOWERS_CMUX_TITLE_FORMAT` (free text) are both forwarded. Every existing assertion uses a single-token value (`"2"`), so the quoting is unexercised **by construction**. Add one test forwarding a value with a space and a `;`. Note the register DOES reason about `$SPAWN_ID` being interpolated unquoted (uuid4, shell-safe) — the knob values got the correct treatment in code and no pin. `test-coverage`

**I3 — The fallback's "refuse on an unresolvable surface" contract is untestable by construction.** **M-L** — making the `case "$SPAWN_SURFACE_REF" in surface:*)` gate always pass — **survived all 139.** Precise framing, so nobody fixes the wrong thing: the gate is *redundant with the parser* under every shape `cmux_v2_stub()` can emit, since the awk only yields `^surface:[0-9]+$` or empty. It fires only when the parser finds nothing, and **there is no stub knob that makes `list-pane-surfaces` return zero surface tokens.** Consistent with (not contradicting) the register's claim that reverting the parser to `$1` reds 5 tests. **The fix is a knob, not another assertion** — and it matters because this guards the exact production failure Task 0 measured. `test-coverage`

**I4 [NEEDS_CONTEXT] — the double-spawn guard rests on an unmeasured premise, and the tautology is the lesser half.** The structural guard is dead (see M2), but that is not the answer to "can a path create two targets?" **It can, by design:** `launch_into_target` runs `rename-tab` BEFORE `send`, so on the send-failure path (`test_send_failure_on_surface_falls_back`, **exit 0**) surface:7 is created AND titled, then the fallback creates a second target with the same title. The register's orphan row treats this as cleanup/visibility. The sharper premise it does not state: **the entire runaway-chain bound rests on `cmux send`'s rc being a reliable accept/reject signal, and nothing measures that.** If a transient non-zero rc can ever accompany a DELIVERED command, one hop yields two live successors — the failure this script exists to prevent. **Note the asymmetry with the register's own discipline:** it records `--workspace TEST-WS` as "INFERRED, not measured" for a cosmetic risk, while the higher-stakes send-rc inference is unrecorded. Unverifiable without live cmux. `correctness`

### Minor

**M1 — The `[selected]` branch and `END{print first}` mutually mask on a one-row stub.** **M-A** survived all 139: with a single always-selected row, `first == selected`, so neither branch is distinguishable. Production impact bounded (a fresh workspace has exactly one always-selected surface) — coverage, not a live bug — but it is **the same shape Task 0's review already flagged at the FIXTURE level (5 inversion mutations surviving), now recurring at the SCRIPT level.** A two-row stub with the marker on the second row closes both.

**M2 — Dead tautological guard.** `[ "$LAUNCH_ACCEPTED" = "0" ] && [ "$SPAWN_TOPOLOGY" = "surface" ]` sits in the `else` of `if create_surface_target && launch_into_target`. `LAUNCH_ACCEPTED` is set to 1 only in the `then`; `SPAWN_TOPOLOGY` becomes `workspace-fallback` only inside `create_workspace_target`, which has not run. Both conjuncts tautologies — harmless, but it READS as a live containment check and no test can distinguish it from `if true`.

**M3 — The `handshake=timeout` record's suffix fields are unpinned.** Measured: dropping `BUDGET_FLAG` from that printf **survived all 139** (**M-B**) — the `budget=over-expected` pin covers only the `handshake=ok` record. `TOPOLOGY_FIELD` on the same printf is **inferred** unpinned, not measured: no test reaches fallback + timeout. A timeout on an over-budget fallback run would silently lose both fields. *Stated separately because measured and inferred are not the same evidence.*

**M4 — Name overclaim + undeclared fence departure.** See Target 2.

**M5 — `test_spawn_verb_vocabulary_retains_the_legacy_verb` restates the verb tuple.** Defensible as a change-detector, but it is the one place a reader could mistake for a second SSOT — and it sits two lines from the vacuous `__module__` assertion, which is what a reader would otherwise trust to enforce single-source. **Fixing I1 makes this benign; leaving both is the risk.**

## Assessment

What everyone else's method structurally failed to see is consistent in shape: **the guards nobody claimed** (`shq`, the fallback's own ref-shape gate) and **the branches a single-shape stub cannot separate** (`[selected]` vs `first`, the timeout record's suffix). Per-guard review cannot see a guard that was never claimed, and a green suite cannot distinguish two branches that agree on every input the stub can produce.

I1 alone warrants the verdict: a claimed pin that pins nothing, in the file whose entire subject is a fail-open, with a positive-controlled replacement already in hand.

**ASSESSMENT: CHANGES_REQUESTED**
