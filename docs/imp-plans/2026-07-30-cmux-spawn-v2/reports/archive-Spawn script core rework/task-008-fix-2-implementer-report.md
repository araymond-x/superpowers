---
schema_version: 1
task_id: 8
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/unit/test_handoff_support.py"
    description: "F1: test_shared_constants_are_the_ssot_the_shell_mirrors made shape-independent — factor regex whitespace-tolerant, plus a new backstop counting every arithmetic context ($(( )) or bare (( ))) that mentions EXPECTED_HOPS and requiring exactly one, with its own positive control on the scanner. F4: all four count assertions' messages widened to name the scan as whole-file and to say an unrelated site elsewhere trips them. Docstring records the second shape-sensitivity failure and the three MEASURED residual escapes."
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "F2: test_over_expected_notifies_never_refuses now uses _hops(ctx, 5) against expected_hops=1, so it proceeds only because the floor clamp lifted the ceiling 2 -> 6; the comment that claimed 'ceiling floors to 6' is now true of the assertion. F3: test_ceiling_derived_from_expected_hops asserts no 'WARNING:' appears when no knob is set."
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "F1 (COMMENT ONLY — executable text byte-identical to HEAD, verified by comparing comment-stripped renderings): the SSOT block's unqualified 'It is enforced ... Change both or neither' replaced with what the test actually catches (literal divergence; a second derivation in any $(( ))/(( )) shape) and what it does not (expr / let / intermediate-variable copies clamped without the bracket form)."
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md"
    description: "One row: F1-F4 closed, the measured mutation evidence, the three residual escapes left open deliberately, and the generalized lesson about N shape-specific patterns being defeated by one shape that clears all N."
tests:
  written: 3
  passing: 3
  command: ".venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider"
  result: PASS
contract_compliance:
  - constraint: "Test/comment work only — do not change production behavior"
    status: compliant
    detail: "The only production file touched is spawn-handoff-session.sh and the change is comment-only. Verified two ways, not asserted: `git diff` shows nothing but comment lines, and a script comparing HEAD's and the working copy's comment-stripped text prints `executable text unchanged: True`. `bash -n` clean."
  - constraint: "Write scope: test_handoff_support.py, test_spawn_handoff_v2.py, spawn-handoff-session.sh (comments), deviations.md"
    status: compliant
    detail: "`git diff --stat` lists exactly those four plus the two hook-written logs (.dispatch-log, context-observations.log) that were already modified at dispatch. module-2-models-budget.md, BACKLOG.md and references/context-handoff-protocol.md untouched."
  - constraint: "Every pin mutation-proven: mutate, confirm RED, restore by file copy, diff-verify"
    status: compliant
    detail: "Twelve mutations run through an exact-string mutator that REFUSES unless the anchor matches exactly once (count printed every run); full diff printed every run; restore by `cp` from a file-copy baseline followed by `diff -q`. No `git checkout --` and no `git stash`. Script byte-identical to HEAD after the mutation rounds, before the comment edit."
  - constraint: "Bash >= 3.2; no set -u/-e/pipefail added"
    status: compliant
    detail: "No executable shell changed at all this round, so the floor is untouched by construction. `bash -n` re-run anyway; `scripts/lint-shell.sh` reports only the pre-existing SC2034 BUDGET_FLAG warning the previous round already accepted."
  - constraint: "Shared Constants: the shell's floor/factor remain the one sanctioned duplication, NAMED as mirroring _handoff_support.py"
    status: compliant
    detail: "CEILING_FLOOR / CEILING_FACTOR / HOP_DIVISOR imports still present and load-bearing (three assertions reference them); the naming comment is retained and now states its enforcement accurately rather than absolutely."
---

# Task 8 — Fix round 2: closing quality-review-round-2 findings F1–F4

## Implementation Summary

Four test-side findings, no production behavior changed. F1 was the one that mattered
and it is the only one that needed a design decision rather than an edit.

**F1 — the SSOT re-duplication guard.** The guard was three patterns, each
shape-sensitive in a *different* way: `factor` byte-exact on spacing, `floor_cmp` on
the `-lt N ]` bracket form, `seeds` on the two variable names it happened to know. A
second derivation escapes by clearing all three at once, and the review demonstrated
two ordinary-bash shapes that do.

The important realization is that **enumerating shapes loses this race** — widening
`factor` to tolerate whitespace kills D1 and D5 specifically, but says nothing about
the next shape nobody listed. So the fix adds the assertion to trust: count every
arithmetic context (`$(( … ))` or bare `(( … ))`) that mentions `EXPECTED_HOPS` and
require exactly one. That is blind to operator, operand order, spacing, and target
variable name. `factor` stays, whitespace-tolerant, because it is what pins the
*literal* against `CEILING_FACTOR`; the new count is what makes "exactly one
derivation" hold for shapes nobody enumerated. The comment says which to trust when
they disagree.

I rejected a total-`EXPECTED_HOPS`-token count as the backstop. It closes more
escapes, but it fails on every legitimate Task 9 edit that touches the variable, and
its repair ritual is "bump the number until it passes" — which silently re-admits D5,
since a bare count cannot tell the escape from the legitimate reference. A guard
whose maintenance procedure is "make the assertion match again" is the same defect
class F1 is.

**F4** took the message-widening branch rather than slicing. With a whole-file
arithmetic backstop the whole-file scan is now *intentional* — a re-duplicator is not
obliged to stay inside any block I could slice to — and the task warned that a slice
anchored on a fragile marker could silently match nothing and make the whole test
vacuous, which is strictly worse than the misattribution F4 describes. The four count
assertions now name the scan as whole-file and say an unrelated site elsewhere trips
them.

**F2 and F3** were straightforward missing pins; both were mutation-proven in both
directions (mutant RED against the fix, and — for F2 — the pre-fix test PASSING the
same mutation, so the pin is what changed and not the mutation's reach).

## Mutation evidence, per finding

Harness: an exact-string mutator that **refuses unless the anchor matches exactly
once** (match count printed every run — a no-op sed would otherwise read as
SURVIVED); full `diff -u` printed on every mutation; restore by `cp` from a file-copy
baseline then `diff -q`; `__pycache__` cleared and `-p no:cacheprovider` throughout;
explicit test paths.

### F1 — FIXED

Re-duplications inserted inside the `if [ "$EXPECTED_HOPS" != "unknown" ]` block, so
the copy is in scope and functional rather than trivially detectable:

| Shape | vs pre-fix test | vs fix |
|---|---|---|
| **D1** `CEIL=$(( EXPECTED_HOPS*2 ))` + `(( CEIL < 6 )) && CEIL=6` | **PASSED** (the escape, reproduced) | **RED** |
| **D5** `CEIL=$(( EXPECTED_HOPS * 2 ))` + `[ "$CEIL" -gt 6 ] \|\| CEIL=6` | **PASSED** (the escape, reproduced) | **RED** |
| **D3** historical indented, semicolon-joined, into `MAX_HOPS` | — | **RED** |

Reproducing D1 and D5 as *passing* against the baseline test file matters: it proves
the mutations are the demonstrated escapes and that my change is what killed them,
rather than a RED that a stray edit could have produced.

### F1 — what I tried in order to break my own fix

Six shapes, run against **each assertion in isolation** so the RED is attributed to
the assertion that actually produced it — a "RED" says nothing about which guard is
load-bearing unless you measure that separately, and measuring it corrected a claim I
had already written down:

| Shape | Killed by |
|---|---|
| reversed operands `$((2 * EXPECTED_HOPS))` + `-lt` clamp | **new backstop** + `floor_cmp` |
| self-addition `$((EXPECTED_HOPS + EXPECTED_HOPS))` + `(( ))` clamp | **new backstop** alone |
| bare arithmetic command `(( CEIL = EXPECTED_HOPS * 2 ))` + `(( ))` clamp | **new backstop** alone |
| indirection `E="$EXPECTED_HOPS"; CEIL=$((E * 2))` + `-lt` clamp | `floor_cmp` **only** |
| `expr` + `-lt` clamp | `floor_cmp` **only** |
| D1 / D5 (the review's escapes) | **new backstop** + widened `factor` |

**The correction that matters: the new backstop does NOT close indirection.**
`$((E * 2))` never names `EXPECTED_HOPS`, so the arithmetic count stays at 1; the
indirection and `expr` shapes die to `floor_cmp` — the pattern I describe elsewhere as
one of the weak, shape-sensitive ones. My first draft of this report listed those two
among "shapes designed to defeat the new backstop, all RED", which misattributes which
assertion is load-bearing. That is the same species of claim error F1 is about, caught
by re-running each mutant against the assertions individually instead of trusting a
whole-test RED. **Accurate statement: the backstop closes shapes that name
`EXPECTED_HOPS` inside `$(( ))` or `(( ))`. Indirection is caught only by the bracket
clamp pattern, and not at all when both are evaded.**

**Three escapes I could NOT close, and am reporting rather than claiming away.** A
copy survives if it evades the arithmetic scan **and** the bracket clamp *together*:

- `E="$EXPECTED_HOPS"; CEIL=$((E * 2)); (( CEIL < 6 )) && CEIL=6` — **SURVIVED**
- `CEIL=$(expr "$EXPECTED_HOPS" \* 2); (( CEIL < 6 )) && CEIL=6` — **SURVIVED**
- `let "CEIL = EXPECTED_HOPS * 2"; (( CEIL < 6 )) && CEIL=6` — **SURVIVED**

Note what these share with the two `-lt`-clamped shapes above: the derivation is
identical, only the clamp form differs. They survive because they evade the arithmetic
scan **and** the bracket pattern together — neither guard alone was ever seeing the
indirection.

These are **left open deliberately.** None is ordinary bash in a file that uses
`$(( ))` and `[ … ]` throughout — each is a deliberate act rather than the manual
reflow D5 modeled — and closing them requires either the token-count pin I rejected
above or a slice with the vacuousness risk F4 warns about. They are written down in
three places (the assertion's comment, the script's SSOT comment, and the deviations
row) so the next reader can re-weigh the trade rather than inherit a false sense of
coverage. **The claim is qualified on purpose: the guard is shape-independent across
arithmetic shapes, not against a determined rewrite.**

### F2 — FIXED

Mutation: delete `[ "$DERIVED" -lt 6 ] && DERIVED=6`.
- Against the fix: **RED**, with the mechanism visible in the failure —
  `[spawn-handoff] hop ceiling reached (5/2)`, i.e. the ceiling really was 2 without
  the clamp and hop 5 really does depend on the floor.
- Against the pre-fix test (hop 1): **PASSED** — confirming the review's finding that
  the old assertion could not see the clamp at all.

### F3 — FIXED

Mutation: `if [ -n "$SUPERPOWERS_CMUX_MAX_HOPS" ]; then` → `if true; then`.
Against the fix: **RED** on the new no-`WARNING:` assertion in
`test_ceiling_derived_from_expected_hops`.

### F4 — FIXED (message-widening branch)

Not mutation-proven, and it is not mutation-provable: the finding is that a
fail-closed message misattributes its cause, so the fix is the message text itself.
Verified by reading the rendered assertion strings. The whole-file property is now
*asserted as intentional* in the comment rather than being an unexamined accident.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-008-quality-review-round-2.md` — the four findings, the D1/D5 escape shapes, the suggested fixes.
- `CLAUDE.md` (repo root) — the cmux auto-spawn section's standing rules: no line numbers, bash 3.2 floor, no `set -u`, `spawn-handoff-session.sh` is not a baselined hook so no integrity re-capture is required for this change.
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — the ceiling derivation block, its SSOT comment, the knob validate-warn-revert, and every other `EXPECTED_HOPS` reference (needed to know what the whole-file scans would see).
- `tests/unit/test_handoff_support.py` — `test_shared_constants_are_the_ssot_the_shell_mirrors` and its docstring's two prior shape-sensitivity failures.
- `tests/unit/test_spawn_handoff_v2.py` — the `TestStallAndCeiling` ceiling tests, to find which is knob-free (F3) and which carried the false floor comment (F2).
- `skills/scripts/models/implementer_report.py` — the report frontmatter contract (`ComplianceStatus` enum; `PASS` is not a valid compliance status).
- `git show d22b5fa` — the controller's deviations.md correction, so this round's wording stays consistent with the register.

## Verification

- `.venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider` → **748 passed**
  in 188s. Matches the stated baseline of 748 exactly.
- `tests/unit/test_spawn_handoff_v2.py` + `tests/unit/test_handoff_support.py` → 76
  passed.
- `bash -n` clean; `scripts/lint-shell.sh` → only the pre-existing SC2034
  `BUDGET_FLAG` warning.
- Seam imports `HOP_DIVISOR` / `CEILING_FLOOR` / `CEILING_FACTOR` confirmed present
  after the edits (the formatter has stripped them four times historically).
- Script restored byte-identically to HEAD after every mutation round, `diff -q`
  verified, before the comment-only edit was applied.

## Deviations from Plan

None from the instruction. Two judgement calls, both recorded above and in
`deviations.md`: rejecting the total-token count in favour of the arithmetic-context
count, and taking F4's message-widening branch rather than slicing.

## Self-Review Findings

Things I checked on myself, several of which changed what I shipped:

1. **The arithmetic regex could have passed at HEAD for the wrong reason.** Before
   trusting any RED I printed what it matched on the unmutated file: it found
   `['$((EXPECTED_HOPS * 2))', '$((HOPS + 1))']` — two sites, one of them unrelated.
   That is the positive control: a pattern matching nothing would also have produced
   "exactly one derivation" failures I might have read as working. The scanner now
   carries that control as an in-test assertion.
2. **A wrong pytest node id printed `no tests ran in 0.05s`.** My first F2 mutation
   run used a guessed class name (`TestCeilingAndBudget`, which does not exist). The
   run reported an ERROR and zero tests — if I had been reading for "did it fail?"
   this would have counted as a RED. I collected the real node ids
   (`TestStallAndCeiling`) and re-ran. This is the instrument-failure class the task
   brief warned about, and it did occur.
3. **I verified my mutations were real escapes, not just failures.** For D1, D5 and
   F2 I ran the mutant against the *baseline* test file as well and confirmed it
   PASSED. Without that, a RED only proves something broke.
4. **I did not stop at the two escapes I was handed.** Four more shapes designed to
   defeat the new backstop went RED; three defeated it. Reporting the three is the
   substance of this round — the finding I was fixing was an unqualified claim, and
   answering it with another unqualified claim would have reproduced it.
5. **The production file's executable text is provably unchanged**, not merely
   "comments only by inspection": I compared comment-stripped renderings of HEAD and
   the working copy programmatically.

## Concerns

`status: DONE_WITH_CONCERNS` for one reason, and it is the honest one: **the F1 guard
has three known live escapes.** They are documented, judged not worth closing, and
narrower than the two the review found — but "shape-independent" is a qualified claim
here, not an absolute one, and Task 9 edits this region by hand. A reader who needs
the derivation to stay single should rely on the comment explaining *why* it must,
not on the test always catching them.

Secondary, on the counting: `tests: 3/3` counts the three test FUNCTIONS whose
assertions changed (`test_shared_constants_are_the_ssot_the_shell_mirrors`,
`test_over_expected_notifies_never_refuses`, `test_ceiling_derived_from_expected_hops`),
not three new test functions — this round added assertions to existing tests rather
than new ones. Stating the convention because the number is otherwise ambiguous, and
because a literal `0/0` on an implementation task that changed two test files is a
shape the git-reality and verification-ratio gates are built to flag.
