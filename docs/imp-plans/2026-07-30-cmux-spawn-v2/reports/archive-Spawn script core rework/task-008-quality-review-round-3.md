# Task 8 — Quality Re-Review Round 3 (fix round `503bdcf` + `d9ad382`)

## Method (so the evidence can be re-run)

- **Comment-only claim verified from the raw diff, not from a stripper.** `diff /tmp/old.sh /tmp/new.sh` shows every changed line begins with `#` (12 lines, all inside the SSOT comment block). A comment-stripped comparison also came back `STRIPPED-IDENTICAL`. The raw diff is the stronger proof and it holds. **Claim CONFIRMED.**
- **Per-assertion attribution done on COPIES.** I rebuilt the eight assertions of `test_shared_constants_are_the_ssot_the_shell_mirrors` as a standalone harness that evaluates each independently against an arbitrary file path, so the tracked script was never mutated for the F1 work. Harness fidelity was cross-validated once against real pytest: `M_indirect_bracket` → harness says `C_floor_cmp_count` only; pytest fails at `assert len(floor_cmp) == 1 … got ['6','6']`. Same assertion, same values.
- **Mutator refuses unless the anchor matches exactly once** (count printed), full unified diff printed and read on every run, restore by file copy + `diff -q`, `__pycache__` cleared, `-p no:cacheprovider`, explicit node ids. No `git checkout --`, no `git stash`.
- **Positive controls:** harness returns all-PASS on the unmutated file with `arith_sites=['$((EXPECTED_HOPS * 2))', '$((HOPS + 1))']`; `/usr/bin/grep -n '(('` over the script confirms exactly five `((` sites and that the three Python-one-liner lines (141–143) produce no false positives. Every SURVIVED verdict below sits next to a KILLED verdict from the same harness run.
- Targeted baseline 76 passed. Full unit suite **748 passed in 202s** — matches the report's claim exactly. Tree left clean (only the two hook-written logs that were already dirty at dispatch).

## Strengths

1. **The F1 backstop is genuinely shape-independent within its stated scope, and I could not find a counterexample inside that scope.** Measured kills, each attributed to a single assertion: reversed operands `$(( 2 * EXPECTED_HOPS ))`, `${EXPECTED_HOPS}` brace form, self-addition, bare `(( CEIL = EXPECTED_HOPS * 2 ))`, and double-nested `$(( ((EXPECTED_HOPS)) * 2 ))` — **all killed by `A_derivations_count` alone**, with `factor`, `floor_cmp` and `seeds` all passing. The nested case is the interesting one: the outer `$((` fails the one-level-nesting regex, but the inner `((EXPECTED_HOPS))` is rescued by the second alternative, so the count still reaches 2. D1 and D5 (round 2's working escape) are killed by the backstop **and** the newly whitespace-tolerant `factor`.
2. **The per-assertion attribution in the report and in the source comments is accurate at the assertion level** — the thing round 2's standing rule demands. `E="$EXPECTED_HOPS"; CEIL=$((E * 2))` + `-lt` clamp dies to `floor_cmp` **and nothing else** (confirmed by real pytest, not only the harness). The report's own table says exactly that, and says its first draft got it wrong.
3. **F2 is a real pin, proven in both directions.** Deleting `[ "$DERIVED" -lt 6 ] && DERIVED=6` makes the new test RED with the mechanism visible: `hop ceiling reached (5/2)`. The **pre-fix test (hop 1) PASSES the identical mutation** — I ran `git show 503bdcf^:tests/unit/test_spawn_handoff_v2.py` against the clamp-deleted script: `1 passed`. The old assertion was vacuous; the new one is not.
4. **F2's fixture change does not release what the test already pinned** (the failure mode this sprint has hit four times, and the one my harness method would have missed). I neutered the over-expected branch to `if false; then`: the test still REDs at **line 492, `assert "budget=over-expected" in r.stderr`** — not at the returncode. Both halves of the test are live at hop 5.
5. **F3 is a real pin and the report's justification for it is true.** `if [ -n "$SUPERPOWERS_CMUX_MAX_HOPS" ]; then` → `if true; then` REDs the new assertion at line 451; the same mutant against the **pre-fix** versions of both test files gives **76 passed** — the guard was genuinely unpinned across the whole targeted surface.
6. **Closes a real formula gap nobody framed as one.** The SSOT test compares *literals*, so `min(6, 2·e)` would satisfy it. F2 is now the only behavioural pin on the `max()` floor branch, and `test_ceiling_derived_from_expected_hops` pins the factor branch. Together they pin the formula shape the literal test cannot see.
7. The `assert arith_sites` positive control is **honestly described** — its comment says a broken pattern would make the count below "fail loudly rather than pass vacuously", i.e. it is a diagnostic, not extra coverage. That is exactly what it is. No overclaim.

## Issues

### Critical
None.

### Important
None.

### Minor

**M1 — One sentence in the KNOWN RESIDUAL ESCAPES block generalizes past the guard's actual scope, and there is a witness.** `test_handoff_support.py` states the escape rule as: *"A second derivation still passes if it BOTH avoids an arithmetic context naming EXPECTED_HOPS **and** clamps without the `-lt N ]` bracket form."* By that rule, a shape that **does** name `EXPECTED_HOPS` in an arithmetic context is closed. Measured counterexamples that name it in arithmetic and still SURVIVE:

- `CEIL=$[EXPECTED_HOPS * 2]` + `(( CEIL < 6 ))` — legacy bash `$[ ]` arithmetic → **SURVIVED**
- `declare -i CEIL; CEIL=EXPECTED_HOPS*2` + `(( CEIL < 6 ))` (and the `typeset -i` twin) — integer-attribute assignment is an arithmetic context → **SURVIVED**

This is *one loose sentence*, not a scope error: the other two documentation sites are precise — the assertion comment says *"every arithmetic context — `$(( ))` or bare `(( ))`"* and the script comment says *"any `$(( ))` or `(( ))` shape"*. Fix is a qualifier: ``…avoids a `$(( ))`/`(( ))` arithmetic context naming EXPECTED_HOPS…``. **Does not block**, and it does not change the *decision*: `$[ ]` and `declare -i` are no more "ordinary bash in a file that uses `$(( ))` and `[ ]` throughout" than the `let` escape the delta already accepts as open. (For completeness and explicitly **not** as findings: `expr`, `bc`, `awk`, and `$("$PYTHON" -c …)` all survived too — the stated rule correctly implies all of those are open.)

**M2 — The escape count is internally inconsistent across the paperwork.** `deviations.md` says *"tried SIX shapes against its own fix: four RED (…); three could NOT be closed"* — 4 + 3 = 7. The report's attribution table has six rows and **omits `let` entirely** (it appears only in the survivors list, never in the killed-by table). The individual shape claims are all accurate as measured; only the tally is wrong.

**M3 — F3's new assertion is broader than the guard it pins, which is the same misattribution class F4 just fixed twelve lines away.** `assert "WARNING:" not in r.stderr` with the message *"no knob is set — nothing may warn about one"* will trip on **any** future warning emitted on the no-knob path and will blame the knob for it. F3 and F4 were reviewed as separate findings, so nobody looked at them together. A tighter pin keys on the substring `invalid SUPERPOWERS_CMUX_MAX_HOPS`. Fail-closed, non-blocking.

**M4 — Two sentences in the script comment sit in tension until the reader reaches the third.** *"a second copy in any `$(( ))` or `(( ))` shape fails too"* is false for `$((E * 2))` — literally a second copy in a `$(( ))` shape that passes. The very next sentence corrects it (*"or derives from an intermediate variable … still passes"*), so a reader who finishes the paragraph is not misled. Cosmetic; flagging only because this delta's subject matter is comment precision.

**[NEEDS_CONTEXT]** — none. Every claim in this review is backed by a run I performed in this session.

---

## Q1 — Is the new F1 backstop itself shape-sensitive, and is the documented escape set correctly scoped?

**The backstop is not shape-sensitive within the scope it declares, and I attacked it.** Nine constructed mutant shapes that name `EXPECTED_HOPS` inside `$(( ))` or `(( ))` were all killed, five of them **by `A_derivations_count` alone** with all three legacy patterns passing — including operand reversal, `${…}` bracing, a different operator (`+` instead of `*`), a bare arithmetic command with a different target name, and two-level paren nesting. I also probed the two structural ways to evade a *counting* guard: merging both derivations into one arithmetic site via the comma operator (killed by `factor`, which drops to 0), and hiding a site inside a larger match (impossible — the body class excludes `)`, so sites cannot merge). The regex's one-level nesting limit is the only theoretical weakness and it self-heals through the bare-`((` alternative.

**The documented escape set is correctly scoped in two of its three statements and loosely scoped in the third** (M1). The three named open escapes — indirection, `expr`, `let` — are real: I reproduced all three as SURVIVED. The general rule stated above them is what over-reaches, and `$[EXPECTED_HOPS * 2]` / `declare -i CEIL; CEIL=EXPECTED_HOPS*2` are the witnesses: arithmetic contexts naming `EXPECTED_HOPS` that the rule implies are closed and that survive. By the brief's own criterion — *"an under-documented escape is a finding; a documented one is not"* — that is a finding, and it is the only one I found. It is a one-token documentation fix, not a guard defect.

## Q2 — Is a whole-test RED being attributed to the right assertion?

**Yes. Every attribution claim in the fix report and in the source comments checks out at the assertion level.** I did not accept a whole-test RED anywhere. Measured, per assertion, in isolation:

| Mutant shape | Killed by (measured) | Report/comment claim | Match |
|---|---|---|---|
| D1 `$(( EXPECTED_HOPS*2 ))` + `(( ))` clamp | `derivations` + `factor` | "new backstop + widened factor" | ✅ |
| D5 `$(( EXPECTED_HOPS * 2 ))` + `-gt` clamp | `derivations` + `factor` | same | ✅ |
| reversed `$(( 2 * EXPECTED_HOPS ))` | `derivations` **alone** | "new backstop" | ✅ |
| self-addition, bare `(( CEIL = … ))` | `derivations` **alone** | "new backstop alone" | ✅ |
| indirection + `-lt` clamp | `floor_cmp` **alone** (pytest-confirmed) | "`floor_cmp` only" | ✅ |
| indirection / `expr` / `let` + `(( ))` clamp | **nothing — SURVIVED** | "SURVIVED, left open" | ✅ |
| factor 2→3 / floor 6→8 / seed 6→8 | `E` / `F` / `G` respectively | "change both or neither" | ✅ |

The corrected claim — *"the backstop closes shapes that name `EXPECTED_HOPS` inside `$(( ))` or `(( ))`; indirection is caught only by the bracket-clamp pattern, and not at all when both are evaded"* — is **exactly right**, verified assertion-by-assertion rather than inferred. The implementer's self-correction of its own first draft is accurate, and its record of that correction in `deviations.md` as a standing rule is the right disposition.

**F2/F3/F4 vacuousness:** F2 and F3 are non-vacuous, proven the only way that counts — mutant RED against the new test **and** the same mutant PASSING against the pre-fix test (F2: `1 passed`; F3: `76 passed`). F4 is message text; the report says plainly it is "not mutation-proven, and it is not mutation-provable", which is honest and correct — there is no vacuousness claim to falsify, and the four widened messages do accurately describe the whole-file scans I measured.

---

## Assessment: **APPROVED**

Round 2 blocked on an *unqualified* claim. This round's claims are qualified, and — with the single residual-rule sentence in M1 — they are accurate. The comment-only assertion is confirmed from the raw diff; the F1 backstop survives nine adversarial shapes it declares in scope; F2 and F3 are proven non-vacuous in both directions; F2 does not release what it previously pinned; the paperwork matches what landed apart from one arithmetic slip. Full suite 748, tree clean.

The four Minor findings are all documentation-precision items on a delta whose entire purpose was documentation precision, and **none of them blocks**. M1 is worth folding into Task 9's edit of this region (it edits this block by hand, which is the reason the residual escapes were written down at all); M2 and M3 are cheap to fix whenever this file is next touched.
