# Partner Review — Task 8 dispatch (round 3)

**Status:** BLOCKED

Reviewed at HEAD `b425aef`. Model: opus (the template's haiku default is wrong for this partner — rounds 1–3 all earned their findings by executing code, not by reading it).

## Round-2 findings — all four CLOSED, each verified first-hand

**F1a (plan Steps 5 and 6): CLOSED.** Step 5 (`:282`) is the full-suite run with the "a file-list run is dishonest here" rationale. Step 6 (`:284`) lists eight explicit paths, counted and matched against the widened write scope. Baseline re-measured independently: **full suite 707 passed** in 155s — the number the dispatch cites is correct.

**F2 (the false "closes at exactly two test files" claim): CLOSED, and the corrected list is accurate.** `:64` now says FOUR, states the identifier grep returns a false closure, and points at Step 2's migration block. Every leg re-measured:
- `/usr/bin/grep -rl 'MAX_HOPS' --include='*.py' --include='*.sh' .` → only the hardening file + the script. **The false closure reproduces exactly.**
- Rendered sweep `'Hop [0-9]*/'` → exactly one site, `test_spawn_handoff.py:692`, which is named.
- All four named tests exist at the cited names, with a bogus-name negative control returning rc=1.
- `sdd-e2e-test.sh` is a real `.handoff-hops` consumer, correctly flagged benign/Module 4.

Additionally swept for consumers the four-item list might still miss, since Task 8 inserts two new gates that run in every existing spawn test: no `tests/unit` spawn test writes a `.sdd-session.json` (policy gate stays `auto` everywhere), none seeds prior `outcome` records (stall streak 0 or indeterminate), and `test_max_hops_zero_is_honoured_as_a_deliberate_kill_switch` survives step (e) (`"0"` is numeric → env branch → `0 >= 0` refuses). **The four-item list is complete as far as measurable.**

**F3 (the stale `deviations.md` parenthetical): CLOSED.** The dispatch's Deviations section is the bare template bullet; the false-row parenthetical is gone and `:60` still says the shell fix is already in the plan.

**F4 (`test_cli_failure_is_non_consent` seam): CLOSED — both halves present, mechanism demonstrably works.** Plan `:140-148` prescribes the `SUPERPOWERS_ROOT` override AND the argv-dispatching stub, with the reason stated. Not accepted on a reading — driven against the real script:

```
override=True : rc=0  stub_invocations=14   (first three are validate_bundle's json probes,
                                             fourth is its heredoc call)
override=False: rc=0  stub_invocations=0    (positive control — venv python used, stub never hit)
```

The seam routes, the blanket-stub warning is correct, and the argv-dispatch requirement is necessary. This is the half round 2 could only reason about; it holds.

## New defects (round 3)

**Finding 1 — no Step writes `_handoff_support.py` or `test_handoff_support.py`. Seven of the eleven rows have no checkbox.** *(F1a's shape one level up.)*

Walking Steps 1–6 by the file each produces: Step 1 → `spawn_handoff_helpers.py`; Step 2 → `test_spawn_handoff_v2.py` plus the three migration files; Step 4(a–f) → `spawn-handoff-session.sh`; Steps 3/5 run things; Step 6 stages **eight**. Two of those eight — `_handoff_support.py` and `test_handoff_support.py`, precisely the pair `ca70612` widened scope for — are produced by **no step**.

The only plan text instructing edits to them is `:66`, which merely *names* the seven rows as scope justification and prescribes nothing. Dispatch `:19` says "Implement Steps 1–6 exactly as the plan specifies," and the spec reviewer mechanically diffs the fenced blocks — of which the P7 work has none. **An implementer can complete all six steps, tick all boxes, pass the fence diff, and have done zero P7 work.** The staging list is the tell: a plan that stages files no step produces.

**Finding 2 — the prescribed `python3` stub self-recurses and HANGS the acceptance run.** Plan `:145-146` says "`exec` the real interpreter otherwise." The stub is first on PATH and is *named* `python3`, so `exec python3 "$@"` re-invokes the stub. `exec` does not fork → unbounded loop in one process → not a failure but a **hang**, inside `subprocess.run` with no timeout, during the full-suite acceptance command. Measured both directions:

```
exec python3 "$@"          → killed by a 5s watchdog (rc=137)
exec /usr/bin/python3 "$@" → prints "hello", rc=0; argv dispatch still refuses spawn-policy
```

**Finding 3 — `test_ceiling_derived_from_expected_hops` cannot demonstrate the derivation it is named for.** Fixture is `expected_hops=2` and the plan's own comment concedes `max(6,4)=6` — the floor wins, so the `2 ×` branch never decides anything. Every other ceiling test is also a floor case (`test_env_ceiling_wins_absolutely` env 1; `test_over_expected_notifies_never_refuses` expected 1). **No prescribed test has `2 × expected > 6`.**

Ranked honestly: surviving mutations are `* 1`, `* 3`, and deleting the derivation — all **restrictive**-direction, not over-permissive; `* 100` *is* caught. So not a consent defect. It stands on two grounds: the test's name asserts a property its fixture cannot show (the generalized bool-guard rule — a fixture only discriminates if its value is not already in the expected set; here `4` collapses into the already-expected `6`); and the Python side of the SSOT pair **is** pinned (`test_handoff_support.py:113`) while the shell literal the dispatch devotes a whole Shared Constants section to has no test at all. **The exact divergence that section exists to prevent is the surviving mutation.**

## Standard checks

- **Context Completeness: PASS** — Contract Constraints, Shared Constants, Pattern References, Source Files, subdirectory-CLAUDE.md reminder all present.
- **Context Accuracy: PASS** — dispatch's Contract Constraints diffed programmatically against `module-3-spawn-script.md:35`: **byte-identical**. Every number re-measured: 707 baseline ✓; Task 8 = lines 58–285 = **228** ✓; `validate-plan.py` → `WARNING, blockers [], warnings ["Task 8 … 228 lines"]` ✓.
- **Prior Task Awareness: PASS** — Task 7's three concerns discharged or carried. P7-1(ii)'s live fail-open confirmed against the shipped CLI: `"OFF"` → `auto`, `{"handoff":false}` → `auto`, `spawn_policy:null` → `auto`, with positive controls (`off` → `off`; `5`/`null`/`[1,2]` → `ask`; nonexistent path → `ask`). P7-4's premise reproduces: `stall-streak --tasks-done unknown` → argparse exit 2.
- **Escalation Check: PASS**, with a non-finding note: the two Task-0 rows dispositioned "Pending — Module 3 amendment / decision" are still open; `rename-tab` at plan `:423` still has no `--workspace`. That is Task 9's, and Task 0's IMPORTANT row already corrected its impact to cosmetic.
- **Architectural Alignment: PASS** — the moving global default's consumer set is complete as measured (finding 3 is about test enforcement, not an un-updated consumer); shell/Python duplication named as a sanctioned exception with a truthful SSOT comment.
- **Pattern Completeness: PASS** — all three pattern references resolve to real files whose conventions the task extends.

## Register enumeration — measured, not inherited

**Eleven.** Rows whose gate names Task 8 or Module 3: **B1** (`:158`), **P7-1** (`:166`), **P7-2** (`:175`), **P7-3** (`:172`), **P7-4** (`:173`), **P7-5** (`:174`), **P7-6** (`:167`), **P7-7** (`:168`), **P7-8** (`:169`), **P7-9** (`:170`), **OP-1** (`:179`, dispositioned) = **11**. Excluded correctly: A3b/c+B2 (Task 11), B3/B8a (Task 13), B4/B7 (Module 2/4), M-1/M-2 (merge), R3-1/R3-2/B9 (Task 7). The **STANDING RULE** row (`:171`) is gated on "every future test touching this family" — it applies but is not one of the eleven.

*Nit:* the dispatch enumerates two different elevens — `:13` lists B1 + P7-1…P7-9 + STANDING RULE, `:51` lists B1 + P7-1…P7-9 + OP-1 — and `:150` demands a per-row report on "the ELEVEN rows above."

## Findings

1. **No Step writes `_handoff_support.py` / `test_handoff_support.py`** — seven of eleven rows sit in un-checkboxed preamble with no fence. Fix: a checkboxed Step 2b naming each P7 edit and its file.
2. **The prescribed `python3` stub recurses** on `exec python3` and hangs the acceptance run. Fix: require an absolute-path `exec` and say why.
3. **`test_ceiling_derived_from_expected_hops` never exercises the derivation** (floor dominates), leaving the shell `* 2` mirror unpinned. Fix: `expected_hops=5`, seed `"9"`/`"10"`.

## Premises verified first-hand vs. accepted

**First-hand:** all three commits since round 2 read in full. Plan Task 8 in full and its line span by `awk`. The dispatch in full. `deviations.md` Deferred Work table in full, eleven-row enumeration done by reading each gate cell. Contract Constraints compared programmatically for byte-equality. `validate-plan.py` run. **Full unit suite run: 707 passed.** Four named migration consumers confirmed with a negative control. All recursive sweeps via `/usr/bin/grep` with quoted `--include` (the first attempt died on zsh globbing — a wrong-shaped error, read rather than treated as an empty result). `_handoff_support.py` executed for seven consent inputs plus controls, and for the P7-4 argparse rejection. The recursion trap measured both directions with a watchdog. The `SUPERPOWERS_ROOT` seam driven against the real script with a positive control (14 stub invocations with the override, 0 without).

**Accepted on trust:** that the seven `_handoff_support.py` rows' prescribed fixes are individually correct — P7-1(ii), P7-3's mechanism, P7-4 and P7-8's `0`-conflation were verified live; P7-6, P7-7 and P7-9 were not re-derived from source. Also accepted: round 2's reading of Steps 5/6 as they stood *before* `f135c4f` (the post-fix state was verified, not the pre-fix state).

**Where I was initially wrong:** I first read Step 6's eight-path list as closing F1a completely and moved on. It closes the *staging* half only — the deeper problem is that two of those eight paths are produced by no step at all, which I had noticed and dismissed before re-examining it. Recording that plainly, because it is the same "guidance the implementer never reaches" failure the round-2 finding was about, and I nearly propagated it. **Round 2's lesson generalizes further than it stated: check that every staged path has a step that writes it.**

---

## Controller disposition (round 3)

**All three findings ACCEPTED, plus the enumeration nit.** Round 3 is the fourth block in the last five dispatches and the third consecutive round to find defects in the previous round's fixes.

**Finding 1 is the most serious defect of the entire Task 8 sequence.** Rounds 1 and 2 both scrutinized *what the seven P7 rows say* and neither asked *which step executes them*. The register rows, the widened write scope (`ca70612`), the eight-path staging list and the dispatch's per-row reporting demand all existed — and every one of them describes work that no checkbox commands. The gap was invisible precisely because so much apparatus pointed at it. The partner found it by walking Steps 1–6 and asking which file each produces, then noticing two staged paths with no producer. **Recorded as a standing rule: every path in a staging list must have a step that writes it — a staged path with no producer is scope that will not happen.**

**Finding 2 is a live hang, not a style note.** It would have fired inside the full-suite acceptance run with no timeout, presenting as an indefinitely hung acceptance rather than a test failure — the most expensive possible failure shape for an implementer to diagnose. Fixed with an absolute-path `exec` clause.

**Finding 3 is accepted on the reviewer's own reasoning, not upgraded beyond it.** The partner explicitly ranked it non-consent (surviving mutations are restrictive-direction; `* 100` is caught) and it still earns the fix on two grounds: a test whose name asserts what its fixture cannot show, and the shell half of an SSOT pair whose Python half *is* pinned. The one-token fix (`expected_hops=5`) is free.

Fixes landed in the plan and dispatch; round 4 dispatched to review the amendments, since rounds 1→2→3 have each found defects in the prior round's fixes and two of round 2's four were *introduced* by round 1's.
