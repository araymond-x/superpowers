# Task 9 — Spec Compliance Review

**VERDICT: FAIL** — one Step 1c obligation unmet and undeclared. Everything
else met, several obligations exceeded, suite independently verified green
(773 passed, measured twice at 246s / 250s).

## The failure

**Step 1c, "do not add a fourth" log-reader — UNMET and UNDECLARED.**
`cmux_log_text` was added to `spawn_handoff_helpers.py:111` (confirmed absent
at `b3ca14f~1`) with none of the three test-file copies removed — giving
FOUR. The clause has content only under the additive reading: "zero copies in
helpers" is the antecedent, and a fourth *test-file* copy is impossible with
three test files.

Concrete symptom: `test_spawn_handoff.py` now BOTH imports `cmux_log_text`
(used at :671) AND defines `_cmux_log_text` (:1219, used at :1285/:1312/:1359)
— two readers of the same file in one module, the exact drift shape the step
names. It appears in neither the report's Deviations section nor
`deviations.md`.

Fix is mechanical: delete the three local definitions, route their call sites
to the helper.

## Per-step result

PASS: Step 1 (stub + all three Task-0 residuals — correlation pinned in BOTH
directions on every row of all three captures), 1b/M3, 1b/M4, 1c B1 rewrite,
1c SSOT (helpers:96-108 is the only verb list; all four consumers route
through it), 1c both positive controls (post-Step-3 by construction; control
(a)'s extra claim verified at hardening:88-90 — the old predicate is
permanently demonstrated fail-open on that same log), 1c the two breaking
tests, 1d (i)-(iv), Step 2, Step 3 (a)-(d) incl. F1 and the prescribed
provenance comment (`SPAWN_WAIT_TIMEOUT_DEFAULT=60`; `default_seconds: 60`),
the three demanded deletions, Step 4, Step 5.

FAIL: Step 1c "do not add a fourth".

## Declared deviations — all ACCEPTED

- **`run_spawn` shadowing.** Only sets a `cmux_body` default; explicit
  `cmux_body=` still wins (`kw.setdefault`). Cannot make a test pass for a
  real reason: refusal-path tests never reach a spawn verb, so the stub is
  irrelevant to them; spawning tests would otherwise have failed only on the
  new ref-shape check — precisely the unrelated reason. No masking.
- **17 no-op `_commit(ctx)` removals.** `_commit` uses `check=True` and fails
  on a clean tree; removing calls that could only have been no-ops changes no
  assertion.
- **`test_reservation_precedes_new_surface` migrated in place.** The name
  appears on both Step 2's fence and its migration paragraph; a literal
  reading duplicates one invariant. Probe injected via `cmux_v2_stub(extra)`
  so it cannot drift from the shared stub.
- **Step 1d (v) repointing (a third option beyond the spec's two).** Sound:
  both spec options presuppose the old invariant is gone, and it is
  (`capture_cmux_ref` returns 1 before `"$@"` runs). Repointing to
  rc-propagation would have duplicated `test_spawn_failure_rc_survives_stdout_capture`,
  which the implementer simultaneously strengthened. The repointed test pins
  something no sibling covers. Satisfies the spec's actual demand — "do not
  leave it green and unexamined".
- **OP-1 pre-emption.** Touches no contract Task 10 owns; the assertion is
  non-vacuous (column-0 regex vs `default_seconds`, with an explicit
  column-0-literal guard); it closes a gap the plan itself labelled a gap.
  Only live risk is Task 10 shipping it twice, and the register row states in
  bold that Task 10 must VERIFY rather than re-add. Declaring it is sufficient.
- **Two beyond-fence vacuousness closures.** The inline-env identity assertion
  correctly notes the fenced `startswith` passes on an empty value; the
  `TAB_TITLE` value pin is necessary because rename failure is
  warn-and-continue. Both strictly strengthen the fence.

## Scope — nothing landed outside

`git show --stat b3ca14f` = 5 code paths + `deviations.md`; `61ba1f4` =
`deviations.md` only. **`test_handoff_support.py` and `_handoff_support.py`
untouched** (read-only for Tasks 9-11). Fixtures dir legitimately untouched.

## Could not fully confirm (stated rather than omitted)

- The **748 baseline** — measured 773 myself twice, did not check out
  `b3ca14f~1` to re-measure 748. The +25 is consistent with the added tests.
- That the **M3 positive control was RUN** — confirmed *analytically* that the
  narrowed assertion must go RED under the `if true` mutation (script:282-286
  emits the exact substring; `NO_AMBIENT_HOP_KNOBS` empties the knob). Not
  re-executed: that requires modifying a tracked file during a read-only review.
- The **two self-review mutations**, for the same reason.

## Not spec failures — forwarded to quality review

1. `test_rename_tab_carries_workspace_on_both_topologies` covers ONE topology;
   its sibling `..._on_the_fallback` covers the other. Substance met and
   mutation-proven, but the NAME OVERCLAIMS, and this is an undeclared
   departure from the fence (the report describes it as a single test).
2. `assert _did_not_spawn.__module__` (hardening:120) is **vacuous** — a
   function's `__module__` is always a truthy string. The comment beside it
   describes a check the line does not perform.
3. `test_spawn_verb_vocabulary_retains_the_legacy_verb` restates the verb
   tuple (hardening:119). Defensible as a change-detecting pin, but it is the
   one place a reader could mistake for a second SSOT.
4. Report Concern 1 (`--workspace TEST-WS` inferred, not measured) correctly
   recorded and bounded; needs the post-merge live smoke check.
5. Report Concern 2 (orphaned surface on an exit-0 run) properly widened in
   `61ba1f4` and routed to Tasks 10/13.
