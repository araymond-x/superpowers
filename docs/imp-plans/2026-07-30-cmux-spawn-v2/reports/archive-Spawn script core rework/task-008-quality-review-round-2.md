# Task 8 — Adversarial Code-Quality Re-Review (round 2, post-fix)

**Status:** CHANGES_REQUESTED — narrowly.

Reviewed at HEAD `e0960ac`. Model: opus. **All four round-1 survivals are genuinely closed, and there is NO production-code defect this round.** Every finding is test- or comment-side. One (F1) is real rather than cosmetic — a working escape from the SSOT test that falsifies an unqualified claim made in the code comment, the fix report, AND the deviations register.

Harness: file-copy baselines from `git show HEAD:`, an exact-string mutator that **refuses unless the anchor matches exactly once**, diff printed every run, `__pycache__` cleared, `-p no:cacheprovider`, explicit test paths (zsh), byte-verified restore after each. Positive controls: 158 green before and after; `diff -q` shown to report differences when fed a changed file.

## 1. The four round-1 survivals — all now RED

| r1 id | Mutation | Result | Killed by |
|---|---|---|---|
| **M15** | `DERIVED=$((EXPECTED_HOPS * 2))` → `* 99` | **RED** | `test_ceiling_derived_from_expected_hops_refuses_at_the_ceiling` **and** `TestCeilingDerivationIsSingle` — a **behavioral** catch on two paths, not merely the SSOT text test |
| **M11** | deleted the `MAX_STALL_HOPS` validate-warn-revert block | **RED** | `test_invalid_knob_warns_and_the_stall_gate_still_refuses`. Mutant stderr reproduces the fail-open verbatim: `[: abc: integer expected` … `launch=auto` |
| **M13** | `MAX_STALL_HOPS` env read made inert | **RED ×2** | both halves incl. `test_raised_knob_is_honoured_and_the_same_chain_proceeds` |
| **M12** | `off` gate made bypassable by `--user-approved` | **RED** | `test_off_refuses_even_with_user_approved` (mutant spawns, exit 0) |
| **M14** | deleted the `TASKS_DONE` numeric fallback | **RED** | `test_failed_tasks_done_cli_degrades_to_unknown_with_a_diagnostic` — bites on the message, not the exit code, which is correct |

**The derivation is genuinely single, measured not assumed:** one arithmetic site (`:247`); `-lt` appears **once in the whole file** (`:248`); `DERIVED` is read at exactly two sites (`:250`, `:255`) — confirming `e0960ac`'s "assigned on every path" note is inert. `hop_ceiling()` is a third instance of the formula but is the **sanctioned Python SSOT**, not a duplication — noted so the next reader does not re-file it.

## 2. Ten new mutations against the restructured block

Deleted `MAX_HOPS="$DERIVED"` pre-assignment → **RED ×3**; inverted inner test → **RED ×6**; regex → `^.*$` → **RED ×3**; `!= "unknown"` → `=` → **RED ×4**; `DERIVED=6` → `99` → **RED**; reordering so the env value is clobbered → **RED ×3**; unconditional `TOTAL_DISP` → **RED**. Two survived (F2, F3 below), **both fail-SAFE in direction**.

## 3. The SSOT test — an escape WAS found

Three assertions gate re-duplication and each has a different blind spot: `factor` is **whitespace-exact**, `floor_cmp` requires the `-lt N ]` bracket form, `seeds` knows only the names `DERIVED`/`MAX_HOPS`. A copy escapes only by clearing all three at once — and two idiomatic shapes do.

| Probe | Second derivation inserted | Verdict |
|---|---|---|
| D3 | the **real historical** indented, semicolon-joined form | **RED** — the rewrite's central claim holds for the shape it was written for |
| D2 | third name `CEIL`, canonical spacing, `-lt` clamp | **RED** |
| **D1** | `CEIL=$(( EXPECTED_HOPS*2 ))` + `(( CEIL < 6 )) && CEIL=6` | **SURVIVED** |
| **D5** | `CEIL=$(( EXPECTED_HOPS * 2 ))` + `[ "$CEIL" -gt 6 ] \|\| CEIL=6` | **SURVIVED** |
| D4 | pure padded reflow, no duplication | **RED** — fail-closed, a point in the test's favour |

D5 is the plausible one: padded arithmetic and a `-gt`-form "clamp up to the floor" are both ordinary bash. Checked whether a formatter could introduce the padding — **`shfmt 3.13.1` preserves `$((EXPECTED_HOPS * 2))`**, so D4's tripwire is manual-reflow-only.

## 4. Over-permissive sweep — NO production finding

Consent gate (`off` now pinned, `ask` both ways, fail-closed `*)`, the deliberate `[ -f ]` short-circuit), ceiling (valid override, invalid revert, `MAX_HOPS=0` kill switch, empty-string neutralizer channel, `-ge` boundary), stall gate — all pinned. Chased the one silent-skip shape round 1's Minor 2 did not cover (an **empty `STREAK`** matching neither arm): traced `stall_streak`'s exception ladder, confirmed it is yaml-free and always prints, and that a `$PYTHON` broken enough to yield empty stdout would already have routed through `TASKS_DONE="unknown"` **with** a diagnostic. **Not a finding.**

## 5. Is the code better? Yes, unambiguously

One derivation instead of two; the shape now reads *derived is the default, a valid env value overrides* rather than two branches that each recompute; the invalid-knob path no longer carries a private copy free to drift. **The proof is §1: `* 99` is now caught by TWO behavioral tests on TWO paths, where before it was caught by neither.** Task 9 inherits something genuinely better, not merely different. The comment block is ~4× the construct it explains — heavy, but it matches this file's convention and each paragraph earns its place.

## Findings

**F1 — Minor (top). The SSOT test's re-duplication guard is shape-sensitive, and the claim attached to it is unqualified.** `test_handoff_support.py:252-262`. `factor` demands byte-exact spacing, `floor_cmp` the bracket form, `seeds` only two names. Evidence: **D5 — a second, fully functional ceiling derivation in ordinary bash passes the test.** Meanwhile the code comment says "Change both or neither", the fix report says re-duplication "FAILs", and `deviations.md` says "re-duplicating it also fails" — **all unqualified, all falsified by D5.** Same species as round 1's Major 2: a claim true of the shape tested and false of the shape shipped-adjacent. *Fix:* make `factor` whitespace-tolerant (`r"\$\(\(\s*EXPECTED_HOPS\s*\*\s*(\d+)\s*\)\)"`) and add a shape-independent backstop counting `EXPECTED_HOPS *` + `EXPECTED_HOPS*` == 1. Prove it with D5 re-applied.

**F2 — Minor. The shell's floor clamp has no behavioural pin, and a comment claims otherwise.** `spawn-handoff-session.sh:248`. Deleting it survives all 107+ spawn tests. `test_spawn_handoff_v2.py:472` reads `write_manifest(ctx, expected_hops=1, total_tasks=1)  # ceiling floors to 6` — but the test only sets `_hops(ctx, 1)` and asserts `returncode == 0`, which passes at a ceiling of 2 just as well. **A comment asserting a property the test does not check** — the Minor-1 defect class recurring one file over. Fail-safe in direction, and the SSOT text test does catch the deletion. *Fix:* `expected_hops=1`, `_hops(ctx, 5)`, assert proceeds (only true because the floor lifts the ceiling to 6).

**F3 — Minor. The outer `[ -n "$SUPERPOWERS_CMUX_MAX_HOPS" ]` guard is unpinned.** `:251`. Replaced with `if true; then` → **158/158 pass**. Isolated repro: with the knob unset the mutant prints `WARNING: invalid SUPERPOWERS_CMUX_MAX_HOPS () — reverting to derived default 10.` on **every** run while `MAX_HOPS` stays correct. Not fail-open — but it is noise in exactly the diagnostic channel the fix round treated as load-bearing when it argued Minor 2's assertion had to be on the message rather than the exit code. *Fix:* assert no `WARNING:` line in one existing no-knob ceiling test.

**F4 — Nit (Task 9 tripwire). Two SSOT regexes scan the whole file, not the derivation block.** Inserting an unrelated `[ "${#BUNDLE_ID}" -lt 3 ]` anywhere fails the seam test with `one floor comparison, got ['6','3']` — a message that misattributes the cause. Fail-closed and loud, so acceptable, but Task 9 edits this file and will read it as a ceiling regression. *Fix:* slice to the derivation block, or widen the message to name the whole-file scan.

## Premises verified first-hand vs. accepted

**Measured:** every row of both mutation tables (anchor count asserted, diff printed, named tests run, restore byte-verified); the 158 baseline before and after; the single-derivation / single-`-lt` / two-`DERIVED`-reader greps via `/usr/bin/grep`; the D1–D5 escape probes; the F4 tripwire; the F3 isolated repro; `shfmt`'s treatment of the derivation; `stall_streak`'s exception ladder; that the amended step-(e) fence now matches the landed block character-for-character.

**Accepted on trust:** the `748 passed` full suite and e2e 15-step PASS (ran only the four spawn/support files, 158 tests); shellcheck's single `BUDGET_FLAG`; `bash -n` on 3.2.57; the spec re-review's PASS.

**Where I was wrong mid-review:** I expected the SSOT test to be the ONLY thing catching `* 99` after the collapse, and **pre-drafted that as a "half-closed Major 1."** Running the mutation against the spawn files refuted me — two behavioral tests kill it. **Major 1 is closed on behaviour, and I say so rather than keeping the finding I came in expecting.** I also expected `floor_cmp` to catch D5; it did not, because a `-gt` clamp is not a `-lt` clamp — which is why F1 is stated from the probe and not from reading the regex.

## What did NOT find anything (judge depth, not verdict)

Ten new mutations against the restructured code went RED; the whole consent gate resisted every re-probe; the empty-`STREAK` silent-skip path traced to unreachable; `shfmt` cleared as a source of F1's escape shape; the `--user-approved` parser and the `ask`/`auto` matrix already pinned. **No production-code defect found.**

---

## Controller disposition

**All four findings ACCEPTED. Fifteenth consecutive round in which an adversarial quality review found something real on an all-green upstream — but the honest summary is that the code is now clean and the remaining work is test-side.**

**Two things distinguish this round.** First, the reviewer **refuted its own pre-drafted finding**: it came in expecting Major 1 to be only half-closed and reported the opposite once it measured. A reviewer that discards the finding it arrived with is doing the job. Second, **F1 is a claim-falsification, not just a coverage gap** — the unqualified assertion "re-duplicating it also fails" appears in three places including a `deviations.md` row the controller wrote, and D5 disproves all three. **A false claim in the durable register is worse than an untested guard, because it stops the next person from checking.**

F1 must be fixed before Task 9 touches this region — that test is the only thing standing between Task 9 and a silently reintroduced split guard, which is the exact defect this whole fix round existed to eliminate.
