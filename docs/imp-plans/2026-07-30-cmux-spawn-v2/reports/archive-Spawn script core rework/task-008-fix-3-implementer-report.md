---
schema_version: 1
task_id: 8
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/unit/test_handoff_support.py"
    description: "M1 (COMMENT ONLY — no executable text changed, verified by the controller with an independent positive-controlled diff filter): the KNOWN RESIDUAL ESCAPES block's rule said escape required avoiding an arithmetic context naming EXPECTED_HOPS, implying every arithmetic shape was closed. Rewritten to scope the rule to the TWO syntaxes the scanner's regex actually enumerates ($(( )) and bare (( ))), and to enumerate all FIVE measured open escapes — adding CEIL=$[EXPECTED_HOPS * 2] (legacy $[ ] arithmetic) and declare -i CEIL; CEIL=EXPECTED_HOPS*2 (integer attribute makes a plain assignment an arithmetic context; typeset -i is the same) to the pre-existing indirection / expr / let. States no bare count, so a future sixth escape cannot desync a total."
tests:
  written: 0
  passing: 0
  command: ".venv/bin/python3 -m pytest tests/unit/ -p no:cacheprovider -q"
  result: PASS
contract_compliance:
  - constraint: "test_handoff_support.py is writable for Task 8 only; it reverts to read-only for Tasks 9-11"
    status: compliant
    detail: "Fixed inside Task 8's window precisely because of this constraint — deferring M1 to Task 9 would have required a write-scope amendment to module-3-spawn-script.md, a heavier change than the one-sentence fix."
  - constraint: "B7 inverts by directory — _handoff_support.py is scanned by check_python39_compat"
    status: not_applicable
    detail: "Comment-only change to a test file; no type annotations added or altered."
---

## Implementation Summary

Closed finding M1 from Task 8's quality re-review round 3. The `KNOWN RESIDUAL ESCAPES` comment block in `test_shared_constants_are_the_ssot_the_shell_mirrors` stated a false rule: that a second ceiling derivation escapes only if it avoids *any* arithmetic context naming `EXPECTED_HOPS`. That implied every arithmetic-context shape was caught. It isn't — the scanner's regex enumerates exactly two syntaxes, and two further shapes that do name `EXPECTED_HOPS` in arithmetic survive. The rule is now qualified to those two syntaxes and the escape list enumerates all five measured survivors.

**Why this was fixed now rather than deferred:** `test_handoff_support.py` reverts to read-only for Tasks 9–11 (module-3 write-scope table, Task 9 row). "Fold it into Task 9" — the reviewer's suggestion — was not available without a plan amendment, which is heavier than the edit itself. Write scope, not urgency, forced the timing.

## Changes Made

One file, comment-only. Final block:

```python
    # KNOWN RESIDUAL ESCAPES — constructed and MEASURED to survive, not assumed
    # absent. The scan below enumerates exactly TWO syntaxes, `$(( ))` and bare
    # `(( ))`, so its shape-independence holds only WITHIN them: naming
    # EXPECTED_HOPS in an arithmetic context is NOT by itself enough to be
    # caught, because bash has arithmetic contexts outside those two spellings.
    # Each shape below was inserted as a second ceiling derivation and survived
    # a real pytest run. They clear this count by using a syntax or an operand
    # it cannot see, clear `floor_cmp` by clamping with `(( CEIL < 6 ))` instead
    # of the `-lt N ]` bracket form, and clear `seeds` by deriving into a fresh
    # target name:
    #   - `E="$EXPECTED_HOPS"; CEIL=$((E * 2))` — indirection; the parens name
    #     no EXPECTED_HOPS
    #   - `CEIL=$(expr "$EXPECTED_HOPS" \* 2)` — a command, not arithmetic
    #   - `let "CEIL = EXPECTED_HOPS * 2"` — arithmetic, but not `(( ))`
    #   - `CEIL=$[EXPECTED_HOPS * 2]` — legacy `$[ ]` arithmetic
    #   - `declare -i CEIL` then `CEIL=EXPECTED_HOPS*2` — the integer attribute
    #     makes a plain assignment an arithmetic context; `typeset -i` is the
    #     same
    # Left open deliberately: none is ordinary bash in a file that uses `$(( ))`
    # and `[ ]` throughout — `$[ ]` is deprecated legacy syntax, and neither
    # `declare -i` nor `typeset -i` appears anywhere in this script — so each is
    # a deliberate act rather than a drift, and closing them costs more
    # brittleness than the escape is worth. Stated so the next reader can weigh
    # it — an unqualified "re-duplication fails" is what this test got wrong
    # twice already.
```

Design notes carried from the dispatch: the rule now describes what the measured shapes *clear* (naming all three live patterns, including `seeds`) rather than asserting a general pass condition, so no new false sufficiency claim replaces the old one. No count of escapes is stated. The one number in the text — "exactly TWO syntaxes" — is verifiable by reading the regex it describes: `r"\$\(\((?:[^()]|\([^()]*\))*\)\)|(?<!\$)\(\((?:[^()]|\([^()]*\))*\)\)"` has exactly two top-level alternation branches.

The two "absent from this script" claims entering durable text were verified against the script with a positive control in the same invocation (`/usr/bin/grep -cE 'declare -i|typeset -i|EXPECTED_HOPS'` → 9, proving the instrument works; the narrowed `declare -i|typeset -i` and `$[` greps both exited 1 — genuinely absent).

## Source Files Read

- `tests/unit/test_handoff_support.py` — the `KNOWN RESIDUAL ESCAPES` block and the three live assertions it describes (`derivations` count, `factor`, `floor_cmp`, `seeds`).
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — read only, to verify the two "absent from this script" claims (`declare -i` / `typeset -i` / `$[`) and to site the mutation anchor.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-008-quality-review-round-3.md` — finding M1 and its two witnesses.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-3-spawn-script.md` — the write-scope table, to establish that `test_handoff_support.py` is read-only from Task 9 onward.

## Deviations from Plan

None. This is a review-driven fix inside Task 8's declared write scope, not a plan deviation. The only judgment call — fixing now rather than deferring to Task 9 as the reviewer suggested — is forced by that same write-scope table and is recorded in `deviations.md`.

## Self-Review Findings

**Controller re-measured the witnesses under real pytest BEFORE authorizing the edit**, rather than trusting the reviewer's standalone harness (which was cross-validated against pytest at n=1). Each shape inserted as a second ceiling derivation above `MAX_HOPS="$DERIVED"`:

| Case | Shape | Verdict |
|---|---|---|
| PC | `CEIL2=$((EXPECTED_HOPS * 2))` + `(( CEIL2 < 6 ))` | **KILLED** — `assert len(derivations) == 1 ... got ['$((EXPECTED_HOPS * 2))', '$((EXPECTED_HOPS * 2))']` |
| W1 | `CEIL2=$[EXPECTED_HOPS * 2]` + `(( CEIL2 < 6 ))` | **SURVIVED** |
| W2 | `declare -i CEIL2` / `CEIL2=EXPECTED_HOPS*2` + `(( CEIL2 < 6 ))` | **SURVIVED** |

The implementer independently reproduced the same three verdicts. Anchor asserted to match exactly once before every mutation; full diff printed and read each run; restore by file copy verified with `diff -q`; `__pycache__` cleared; `-p no:cacheprovider`; no `git checkout --`, no `git stash`.

**Comment-only proof, run independently by the controller** (the load-bearing claim, so not taken on the implementer's word):

```
git diff -U0 -- tests/unit/test_handoff_support.py | /usr/bin/grep -E '^[+-]' \
  | /usr/bin/grep -vE '^(\+\+\+|---)' | /usr/bin/grep -vE '^[+-][[:space:]]*#'
→ no output, exit 1
```

Positive control on that filter: fed `+    assert True`, it printed the line and exited 0. The filter can match; it found nothing because there is nothing.

**Suites:** targeted `test_handoff_support.py` + `test_spawn_handoff_v2.py` → 76 passed (baseline 76). Full unit suite → **748 passed in 199.20s** (baseline 748).

**Path resolution confirmed:** the test reads the *worktree* script, printed and checked — had it resolved to the main checkout, every mutation would have been a no-op and both witnesses would have read SURVIVED for the wrong reason.

## Concerns

None blocking. One process observation, logged to `deviations.md` as instrument failure #18:

The implementer's first harness captured `RC=${PIPESTATUS[0]}` after an intervening command had already clobbered it, so `RC` was empty and all three cases — **including the positive control** — printed KILLED. The raw pytest output in the same run said `1 passed` / `1 passed` / `1 failed`, contradicting the labels. It was caught only because the standing discipline is to read the raw output rather than the verdict line, and the run was repeated with a correct `RC=$?` capture.

This is the mirror image of the sprint's other instrument failures, which all manufactured false *negatives*. This one manufactured a false *positive-of-closure* — a broken verdict variable would have reported the finding already closed and produced no change at all. Both are caught by the same rule: a positive control that does not behave as required invalidates the entire run.

Honesty scope on the word "MEASURED" in the comment block: the two new escapes (`$[ ]`, `declare -i`) and the positive control were measured this session, twice independently. The three pre-existing entries (indirection, `expr`, `let`) carry forward from the round-2 fix and were not re-run; the collective label is accurate because all five have been measured at some point.

## Status

DONE
