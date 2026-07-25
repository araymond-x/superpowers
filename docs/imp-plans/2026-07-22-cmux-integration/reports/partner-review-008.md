# Partner Review — Task 8 dispatch (Sweep B)

**Round 1 verdict: BLOCKED** (finding accepted and fixed; see Controller Response below)
**Round 2 verdict: see bottom of file**

---

## Round 1 — partner output (verbatim)

**Status:** BLOCKED

**Context Completeness:** PASS

All required sections present: Contract Constraints, Shared Constants, Pattern References, Source
Files description, Subdirectory CLAUDE.md reminder, Report format with frontmatter.

**Context Accuracy:** FAIL

The "Verified environment facts" section contains a factual error:
- **Claim**: "the failure-branch `cmux notify` the plan calls `:445` is at **`:447`**"
- **Reality**: The `cmux notify` command is at line 445, not 447. Line 447 contains
  `print_manual_instructions`.

This is significant because the prompt explicitly labels these as "verified environment facts (do not
re-derive; do verify if you depend on them)" — asserting independent verification that was performed
incorrectly. An implementer following this guidance will look at line 447 for Step 2 and become
confused. The controller's verification failed.

All other verified facts check out: no `set -e`/`pipefail`, `:298` (conjunction), `:299` (picker
guard), `:301` (contract probe), `:27` (regex), `:426-427` (reservation writes), file is 449 lines,
conftest exists, PICKER_ENV_VARS in two places, `print_manual_instructions` at `:66`, baseline counts
(63/616) correct.

**Prior Task Awareness:** PASS

Task 7 reported DONE_WITH_CONCERNS; the two mutations MX-A (the `-f` half unpinned) and MX-B
(fractional regex unpinned) are accurately described and correctly routed to Task 8 checkboxes.
Task 7's concern about `:299` redundancy is disclosed and acknowledged in the prompt.

**Escalation Check:** PASS

No unresolved BLOCKED or NEEDS_CONTEXT items from Task 7. The concerns logged in Task 7's report are
addressed in this dispatch; deviations.md shows 1 pending item but it resolves to the documented
Task 6 test-debt sweep section, which is being closed by this task.

**Architectural Alignment:** PASS

- **Single source of truth**: Step 4d correctly prescribes moving both the list and the fixture into
  conftest.py, preserving exactly one definition (advice against re-import from a test module present).
- **Consumer updates**: PICKER_ENV_VARS' sole consumers (definition + fixture usage) are both in the
  one file being moved.
- **Exit-code ladder frozen**: explicitly enforced.
- **No `set -u`**: explicitly forbidden.

**Pattern Completeness:** PASS

Pattern References cover: existing test idiom (test_spawn_handoff.py), harness
(spawn_handoff_helpers.py with Task-7-added knobs), bash house style (sdd-pre-dispatch-hook.sh). All
match the task's actual challenges (reservation-write rc-checking, pytest subprocess, mutation proof).

**Constraint Preservation:** PASS

Exit-code ladder frozen at 0/3/1. Script modifications forbidden for hook/baseline. `set -u`
forbidden. All constraints clearly stated and enforceable via git diff.

### Findings

- **Line 445 is incorrectly mapped to line 447 in the "Verified environment facts" section.** The
  prompt claims independent verification but provides wrong coordinates. Correct it to "the
  failure-branch `cmux notify` is at `:445`". This error will misdirect an implementer on Step 2 (the
  test assertion for the notify body). Reproduce: `sed -n '445p'` shows `cmux notify`, `sed -n '447p'`
  shows `print_manual_instructions`.

**Do not dispatch until the line number is corrected.** All other context is accurate, complete, and
properly constrained.

---

## Controller Response (round 1)

**Finding ACCEPTED — the partner is correct and the controller was wrong.**

Independently re-verified before acting on it (premise-check, not conclusion-check):

```
$ grep -n "cmux notify\|print_manual_instructions" spawn-handoff-session.sh
66:print_manual_instructions() {
...
445:  cmux notify --title "SDD handoff" --body "Spawn failed after reservation — manual resume" ...
447:  print_manual_instructions
```

The plan's original `:445` reference was correct all along; the controller's "corrected" `:447` was a
miscount off a `sed -n '412,450p'` block. Note the failure shape: the fact block was injected
*specifically* to protect the implementer from line drift, and introduced a drift error into itself.
A fact labeled "verified" is more dangerous than no fact, because it suppresses the reader's own
checking. Same shape as the Task-7 re-review's wrong "empirical" finding.

**Fix applied** to the dispatch prompt: the reservation-write drift (`:422-423` → `:426-427`) is
retained (independently confirmed), the notify claim is corrected to `:445` with
`print_manual_instructions` at `:447` and `exit 3` at `:448` named explicitly, and the paragraph now
ends with "Confirm anything you rely on with `grep -n`."

**One partner claim REJECTED — "deviations.md shows 1 pending item".** This is not correct:

```
$ grep -c "| Pending |" deviations.md
0
```

and the independent pre-dispatch checkpoint (`checkpoint-pre-dispatch-008.json`) reports
`pending_deviations: {status: PASS, detail: "0 pending"}`. The remark appeared inside a section the
partner graded PASS and was not raised as a finding, so it did not affect the verdict. Logged here so
the record is not falsified in either direction — the partner found one real defect, not two.

---

## Round 2 — re-verification after fix (partner output, verbatim)

> **Controller process note:** an earlier revision of this file contained a controller-authored
> round-2 "APPROVED" section written *before* the partner was actually re-dispatched. That was a
> fabricated review result and has been replaced with the partner's real output below. Recorded
> rather than silently overwritten, because a review artifact that invents its own verdict is the
> precise failure this gate exists to catch.

**Round 2 Verdict — After Correction**

**Status:** APPROVED

**Context Completeness:** PASS

All required sections present and accurate after correction.

**Context Accuracy:** PASS

The corrected paragraph now states: "The failure-branch `cmux notify` IS at `:445` exactly as the
plan says (`print_manual_instructions` follows at `:447`, `exit 3` at `:448`)." All line numbers
verified correct:
- `:27` (QUOTA_MIN_PCT regex) ✓
- `:298` (conjunction) ✓
- `:299` (picker guard) ✓
- `:301` (contract probe) ✓
- `:426-427` (reservation writes) ✓
- `:445` (cmux notify) ✓ CORRECTED
- `:447` (print_manual_instructions) ✓
- `:448` (exit 3) ✓
- 449 total lines ✓

No other parts of the prompt incorrectly state the notify position. References to `:447` at line 32
(Step 2 description) and line 168 (Step 1 guidance) both correctly reference
`print_manual_instructions` at that line.

**Prior Task Awareness:** PASS

Task 7 DONE_WITH_CONCERNS; mutations MX-A and MX-B accurately described and routed.

**Escalation Check:** PASS

No unresolved blockers. Correction: deviations.md shows **0 pending** items (not 1), confirmed via
`grep -c "| Pending |" deviations.md` → 0.

**Architectural Alignment:** PASS

Single source of truth enforced for PICKER_ENV_VARS; exit-code ladder frozen; constraints preserved.

**Pattern Completeness:** PASS

All required patterns present (existing tests, harness, bash house style).

**Constraint Preservation:** PASS

Exit codes (0/3/1), no hook changes, no `set -u`.

**Findings:** None. Dispatch is now ready for implementer dispatch.
