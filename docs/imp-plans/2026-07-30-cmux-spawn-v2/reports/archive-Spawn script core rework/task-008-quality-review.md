# Task 8 — Adversarial Code-Quality Review

**Status:** CHANGES_REQUESTED

Reviewed at HEAD `a85d347`. Model: opus. **Four mutations survived the entire shipped suite. Three are fail-open on guards the file's own comments call load-bearing. All twelve CLAIMED pins went RED — the implementer's mutation-RED claims are accurate; the gaps are in guards nobody claimed.**

## Mutation results

Harness: file-copy restore (never `git checkout --`), explicit test paths, `-p no:cacheprovider`, `__pycache__` cleared per run, `git status` verified after each, diff printed per run. Positive control first (`CEILING_FLOOR 6→7` → RED). Anchor counts checked before each mutation; every one applied exactly one site; no no-ops.

| # | Guard | Mutation | Result |
|---|---|---|---|
| M1 | P7-1(i) shell `*)` arm | `"ask"` → `"auto"` | **RED** |
| M2a/b | P7-1(ii) key-presence / fail-closed | `.get() is None` / `else "auto"` | **RED** ×2 |
| M3 | P7-3 probe before glob | `_require_yaml()` → `None` | **RED** |
| M4 | P7-6 | narrow back to `except OSError` | **RED** (2 tests) |
| M5a/b | P7-8 blanket / order | FNFE arm deleted / handlers reversed | **RED** ×2 |
| M6 | P7-9(B) | **real** module-scope `import yaml` | **RED** (3 tests) |
| M7/M7b | P7-9(D) + `_cli` twin | `isinstance(h, dict)` dropped | **RED** ×2 |
| M8 | P7-4 shell `unknown` branch | neutralized | **RED** |
| M9a/b/c | ceiling `* 2` (main path) | `* 1` / `* 3` / deleted | **RED** ×3 |
| M10 | SSOT shell↔Python floor | shell `6` → `9` | **RED** — but by the rendered `Hop 1/6` assertion, **not** by the test named for the seam |
| M16 | stall boundary | `-gt` → `-ge` | **RED** |
| **M15** | **ceiling `* 2` (invalid-knob copy)** | **`* 2` → `* 99`** | **SURVIVED** — 107/107 pass |
| **M11** | **`MAX_STALL_HOPS` validate-warn-revert** | **block deleted** | **SURVIVED** |
| **M13** | **`MAX_STALL_HOPS` env read** | **made inert** | **SURVIVED** |
| **M12** | **`off` gate** | **made bypassable by `--user-approved`** | **SURVIVED** |
| M14 | `TASKS_DONE` numeric fallback | line deleted | **SURVIVED** |

## Major 1 — the ceiling derivation is DUPLICATED, and the copy nobody tests is the one that fails open

`spawn-handoff-session.sh:235` and `:240-241`. The derived ceiling is computed **twice** — once in the invalid-knob branch, once in the else branch. Only the second is pinned. **M15 changed `* 2` to `* 99` in the first copy and all 107 spawn tests passed.** The reachable path is ordinary: a typo'd `SUPERPOWERS_CMUX_MAX_HOPS` on a v2 plan that ships a manifest. The only existing invalid-knob test uses a fixture with **no** `.sdd-session.json`, so `EXPECTED_HOPS` is `unknown` and the derivation sub-branch never executes. The code six lines above calls this *"the ONLY guard against an unbounded spawn chain."*

**Fix is structural, not a test** — derive once, then let a valid env value override, deleting the second copy. A test-only fix leaves the duplication for Task 9, which edits this same region.

## Major 2 — the new `MAX_STALL_HOPS` knob is unpinned in BOTH directions while its siblings are not

`spawn-handoff-session.sh:35-40, 259`. **M11** deleted the validate-warn-revert block → suite green; probed the behavior: with the block gone and the knob set to `abc`, a two-stall chain that must refuse **exits 0 and spawns** (`[ 2 -gt abc ]` errors, branch not taken) — a genuine fail-OPEN. **M13** made the env read inert → green, so the variable the refusal message tells the user to raise could stop working with nothing noticing.

**This is a contract-compliance discrepancy, not just coverage.** The report claims *"MAX_STALL_HOPS follows the existing pattern verbatim."* The **code** pattern landed; the **test** pattern did not. Both sibling knobs have both halves (`test_spawn_handoff.py:1082`, `:1101`) under a comment block spelling out why.

## Major 3 — `spawn_policy=off` is not pinned against a `--user-approved` bypass

`spawn-handoff-session.sh:179-186`. **M12** rewrote the `off` gate to `[ "$SPAWN_POLICY" = "off" ] && [ "$USER_APPROVED" != "1" ]` — making the plan author's hard refusal overridable — and all 25 policy/stall tests passed. `test_off_refuses_pre_reservation` never passes the flag, so both branches are only ever tested with `USER_APPROVED=0`. The code is correct today; the exposure is that the two policy branches are adjacent, both consult `SPAWN_POLICY`, and **folding them is the most natural simplification anyone will reach for** — converting a hard refusal into a soft one with a green suite.

## Minor 1 — `test_shared_constants_are_the_ssot_the_shell_mirrors` does not read the shell

`test_handoff_support.py:200-215`. Its docstring claims it makes a divergence fail. It asserts three Python constants and never opens `spawn-handoff-session.sh`. The shell side *is* caught (M10, M9a/b) but by two unrelated tests in another file, neither of which names the seam. **A reader trusting this docstring will believe the seam is guarded here and delete the tests that actually guard it.** Also `HOP_DIVISOR` has no shell mirror at all.

## Minor 2 — `TASKS_DONE` numeric fallback is load-bearing and unpinned

`:222`. **M14** deleted it → green. Measured: with a `python3` stub failing only on `*tasks-done*`, `TASKS_DONE` is **empty**, not `unknown`; with the fallback deleted the run reaches `stall-streak --tasks-done ""` → argparse exit 2 → empty `STREAK` → matches neither arm → **spawns a two-stall chain with no diagnostic at all.** The same silent-skip defect the implementer found for the `unknown` case, still open for the empty case.

## Minor 3 — the derived ceiling has no upper clamp

`:241`. `MAX_HOPS = 2 × expected_hops` from the manifest; `expected_hops: 500` yields a ceiling of 1000. Before Task 8 the bound was a fixed 3; it is now manifest-controlled and unbounded on the guard called "the ONLY guard against an unbounded spawn chain." The stall gate backstops only *zero-progress* hops.

## Minor 4 — usage string and header omit `--user-approved`

`:2` and `:60` still read `BUNDLE_ID [--dry-run]`, while the `reason=policy-ask` message tells the user to re-run with the flag.

## Minor 5 — doc lag with a live window (scheduled; flagging the window, not the omission)

`references/context-handoff-protocol.md:55,74` still says "Default limit 3" and its exit-3 list omits `policy-off`/`policy-ask`/`stall`. **Scheduled** at Task 16 (`module-4:591`), so not an oversight. The concern is the window: Tasks 9–15 sit between, and `policy-ask` is the **retryable** exit-3 cause — a controller hitting it and reading the current doc relays "manual resume" instead of asking the user and re-running with the flag.

## Nit

`:260` — `TOTAL_DISP="?"` is immediately overwritten by a command substitution that yields empty on a malformed manifest, rendering `tasks 3/`.

## Over-permissive sweep

Three answers, all above (M12, M11, M15) — all **test gaps against currently-correct code**, not live defects. The `*)` arm, the `-ge` ceiling boundary (9/10), the `-gt` stall boundary (both directions), and pre-reservation ordering are genuinely pinned.

## Bool-guard rule — claim VERIFIED, by method

Swept every added test line for bool literals and classified each. The `True`s at diff lines 268/273/282/333 are **pre-existing**, carried through the reflow, none feeding a count set. The new `false`/`"true"` entries reach `ask` via the non-dict / not-in-tuple guards exactly as claimed — `"true"` → `True` → `isinstance(True, dict)` False → `ask`, no set membership, so `True == 1` is unreachable. **No new count-based fixture contains a bool anywhere.** Accurate and non-vacuous (the two entries are *redundant* with `"OFF"`/`5`, but redundant is not vacuous).

## Integration risk — checked, none found

Full `sdd-e2e-test.sh` run: **PASS, 15 steps**, incl. Step 14 which drives this script (its fixture ships no manifest, so the `[ -f ]` short-circuit keeps it `auto` and the gate is transparent). No other shell or script reads `SUPERPOWERS_CMUX_MAX_HOPS`. **The newly fail-closed `ask` path cannot strand real manifests:** `materialize-manifest.py:118-122` always writes a complete `handoff` block with `spawn_policy` defaulting to `"auto"`, and `sdd_session.py:21` types it as a literal — no v2 manifest can land in the present-but-invalid bucket; pre-v2 manifests have no `handoff` key and keep consenting.

## What Task 9 inherits

1. `BUDGET_FLAG` SC2034 — verified exactly one shellcheck finding on this file; Task 9's fence (d) consumes it.
2. B1's second clause — correctly deferred.
3. **New: the duplicated ceiling derivation.** Task 9 edits this same region; whichever copy it touches, the other is free to drift and only one is tested.
4. **New: the three unpinned guards are in code Task 9 will read as "already reviewed and green" — the exact state in which a natural simplification becomes a silent fail-open.**

## Premises verified first-hand vs. accepted

**Measured:** every row of the mutation table (mutation applied, diff printed, specific tests run, file restored and byte-compared); the four survivals re-probed with purpose-built tests then positive-controlled by re-applying the mutation; the full e2e; shellcheck's single SC2034; the sibling-knob precedent; `materialize-manifest.py`'s always-complete handoff block; Task 16's scheduled coverage; the bool sweep; the protocol doc's stale text.

**One instrument failure, disclosed:** the first M9a run passed the replacement unescaped and perl interpolated `$(` as a special variable, producing garbage that "went RED" across 16 tests. **That RED was meaningless.** Caught by reading the printed diff rather than the pass/fail line. **This is why the harness prints the diff every run — a mutation that reads as a dramatic RED is exactly the shape a broken instrument produces.**

**Accepted on trust:** the 741 count, fence fidelity, the reflow's AST-inertness, the 19-line non-fence inventory, `bash -n` (all measured by spec review).

**Where I was wrong mid-review:** I initially wrote the shell↔Python SSOT divergence as an unguarded gap, on the strength of reading the test's docstring and seeing it never touch the shell. **M10 refuted me** — the shell floor IS caught, by a rendered-string assertion in another file that no comment connects to the seam. The finding survives, **demoted from Major to Minor** and restated as a documentation defect rather than a coverage one. **Reading a test's docstring is not measuring what it catches.**

---

## Controller disposition

**CHANGES_REQUESTED accepted in full. This is the fourteenth consecutive time an adversarial quality review dispatched onto an all-green upstream has found a real defect** — here, four surviving mutations after a clean implementer self-review, five partner rounds, and a PASS spec review.

**The shape of the finding is the lesson.** All twelve *claimed* pins went RED — the implementer's mutation discipline was sound. **Every gap was in a guard nobody thought to claim.** Major 1 is the sharpest case: the ceiling derivation exists twice, the tested copy is fine, and the untested copy is reachable by an ordinary typo. A reviewer checking "is the ceiling pinned?" gets yes. Only mutating *each copy separately* finds it. **Duplication does not merely risk drift — it splits a guard's test coverage in a way that per-guard review cannot see.**

**Major 2 is a contract discrepancy, not a coverage gap**, and that distinction is why it is Major: the report certified "follows the existing pattern verbatim" and the *code* does — but the pattern's sibling knobs each carry two tests, and this one carries none. A compliance claim that is true of the code and false of the tests is the kind that passes every review that reads the code.

**Accepting Minor 5 as a record-only item.** The doc lag is genuinely scheduled to Task 16 and `references/context-handoff-protocol.md` is Module 4's write scope — editing it now would be the scope violation this sprint has repeatedly refused. The window risk is also theoretical *for this worktree*, since the live hooks resolve to the main checkout and this branch is unmerged. Recorded as Pending, owned by Module 4.

Dispatching a fix subagent rather than fixing inline, per the skill: controller edits accumulate implementation context that bleeds into later dispatches and reviews.
