---
schema_version: 1
task_id: 11
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Replaced run_post_spawn's single-literal `if [ \"$POST_SPAWN\" = \"rc,rename\" ]` reorder with generalized canonicalization over the fixed {rename, rc} universe (rename first, rc last, duplicates collapsed); warns iff the effective sequence changed, naming actual input->result."
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "Added test_knob_multitoken_forces_rc_last and test_knob_duplicate_token_deduped; updated test_knob_order_rc_before_rename_is_reordered_with_warning's WARNING-text assertion to the generalized message; anchored the two 'canonicalized to rename,rc' stderr pins with a trailing '(' for prefix-safety."
tests:
  written: 2
  passing: 2
  command: ".venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider (this fix's 2 new tests pass; FULL SUITE: 803 before -> 805 after, 0 failed — controller independently re-measuring at HEAD 532c7b6)"
  result: PASS
contract_compliance:
  - constraint: "Bash >= 3.2; no set -u/-e/pipefail"
    status: compliant
    detail: "Canonicalization uses only [[ \",$POST_SPAWN,\" == *,glob,* ]] and ${canon:+$canon,} — both bash-3.2 constructs. No new set flags; no producer piped into grep -q."
  - constraint: "printf not echo for composed strings"
    status: compliant
    detail: "The new WARNING uses `echo \"...$POST_SPAWN...$canon...\" >&2`, matching the Step 2 fence verbatim and every sibling warning in the file (incl. the validate-warn-revert block above run_post_spawn). Interpolation cannot mangle: POST_SPAWN reaching this line has passed ^(rename|rc)(,(rename|rc))*$ or been reverted to the default, so both it and canon are tokens from {rename, rc} joined by commas — no backslashes, no leading '-'."
  - constraint: "All env knobs validate-warn-revert; canonicalization runs AFTER validation"
    status: compliant
    detail: "The ^(rename|rc)(,(rename|rc))*$ validate-warn-revert block above run_post_spawn is untouched; canonicalization runs inside run_post_spawn, after validation, and reorders+dedupes rather than reverting."
  - constraint: "Ordering always resolves to /rc LAST (Module 3 AC / addendum #3)"
    status: compliant
    detail: "canon appends rename first then rc, so /rc is always last when present, for every one of the 8 regex-valid inputs. Verified by test_knob_multitoken_forces_rc_last (send_lines[2] == /rc) and the reorder test."
---

## Implementation Summary

Closed round-2 quality review finding #1: `run_post_spawn`'s ordering guarantee held for only the exact literal `rc,rename`. Replaced the single-literal `if` block with the generalized canonicalization the amended Step 2 fence prescribes:

```bash
local canon=""
[[ ",$POST_SPAWN," == *,rename,* ]] && canon="rename"
[[ ",$POST_SPAWN," == *,rc,* ]] && canon="${canon:+$canon,}rc"
if [ "$canon" != "$POST_SPAWN" ]; then
  echo "WARNING: SUPERPOWERS_CMUX_POST_SPAWN=$POST_SPAWN canonicalized to $canon (operator addendum #3: /rc must be sent LAST; duplicate steps collapsed)." >&2
  POST_SPAWN="$canon"
fi
```

Over the fixed `{rename, rc}` token universe the canonical form is fully determined (rename first, rc last, duplicates collapsed), so this reorders AND dedupes every accepted token list and warns iff the effective sequence changed, naming the actual input and result. The validate-warn-revert regex block above the function is unchanged — canonicalization runs after validation. `canon` can never be empty at the warning: `run_post_spawn` is guarded by `[ -n "$POST_SPAWN" ]` and any regex-valid non-empty value contains at least one `{rename, rc}` token.

TDD sequence: wrote the two new tests + updated the third FIRST, confirmed RED against unfixed code (duplicate test measured `/rename` sent twice), implemented, confirmed GREEN.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-3-spawn-script.md` — Task 11 fence (both 2026-08-02 amendments, Step 1 test obligations, Step 2 implementation fence). Authoritative spec.
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — the config block (`POST_SPAWN_DEFAULT`/validation, lines ~65-69), `post_spawn_send_verified`, `run_post_spawn`, and the outcome printf wiring.
- `tests/unit/test_spawn_handoff_v2.py` — the `TestPostSpawn` class and its helpers (`_post_spawn_screen`, `_success_ctx`, `_run_post_spawn`, `_send_lines`, `_post_spawn_verbs`, `_rc_anchor`/`_rename_anchor`, `DEFAULT_TAB_TITLE`). New tests reuse these exactly; anchors resolve from `cmux-verb-shapes.json` at runtime via the existing helpers — no hardcoded anchor duplicates.

## Self-Review Findings

- **Positive control (per-pin, mandated):** Backed up the fixed script to scratchpad, reverted to the pre-fix single-literal block via Edit, ran the two NEW tests scoped -> both went RED (multitoken and duplicate). Restored the fix by file copy; `diff -q` reported IDENTICAL. Neither new test is vacuous.
- **All 8 regex-valid inputs traced:** `rename`, `rc`, `rename,rc` -> no warning (canon == input); `rc,rename`, `rename,rename`, `rc,rc`, `rename,rc,rename`, `rc,rename,rc` -> warn + canonicalize; all resolve to /rc last (when rc present). Confirmed with the advisor.
- **Assertion anchoring (advisor #3, noticed and addressed):** In `test_knob_multitoken_forces_rc_last` (input `rename,rc,rename`) and the updated reorder test, `rename,rc` is a prefix of a longer message substring. Traced that no reachable mutation of this algorithm actually slips through a loose match (a canon equal to the input emits no warning at all, so the assertion still fails; and `len(send_lines)==3` + positional pins are the real behavioral constraints), so it did not block. Tightened both to `"canonicalized to rename,rc ("` anyway for consistency with the duplicate test's already-anchored pin and to remove a match a reviewer would flag. Committed separately (532c7b6), not amended.

## Deviations from Plan

None. The implementation is the Step 2 fence verbatim; the two new tests and the third's updated assertion follow the Step 1 obligations. The only addition beyond the literal fence is the trailing-`(` anchoring of two stderr assertions (advisor-suggested, behavior-neutral, documented above) — a strengthening of the pins the fence describes, not a change to what they verify.

## Concerns

None material.

- **`echo` vs "printf not composed strings":** The new WARNING is an interpolated `echo`, which reads as a contradiction of the printf constraint on a diff. It is not one — the Step 2 fence prescribes `echo` verbatim, every sibling warning in the file uses `echo`, and the interpolated values are constrained to comma-joined `{rename, rc}` tokens (post-validation) so they cannot mangle. Recorded as `compliant` with that reasoning in `contract_compliance`, not silently.
- **Measurement provenance:** The 805-passing full-suite count was measured at commit `7a224ff` (the fix commit). Commit `532c7b6` only tightened two stderr substring matches (behavior-neutral); after it, the scoped `TestPostSpawn` class was re-confirmed 9 passed. The full 6.5-min suite was not re-run for a substring-anchor-only change. `tests.written: 2` (two written; the third was updated, not written); `tests.passing: 805` is the full-suite figure at 7a224ff. [CONTROLLER NOTE: independently re-measuring the full suite at HEAD (532c7b6) before trusting the count.]
