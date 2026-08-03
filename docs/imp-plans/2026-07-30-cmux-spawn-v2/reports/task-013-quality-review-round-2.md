# Code Quality Re-Review (round 2) — Task 13 `[task 13 re-review:quality]`

**Model:** opus (adversarial) · **Fix commit** `07b27b0` (diff `96c4d48..07b27b0`) · **Verdict: Fix approved — YES** (0 issues)

Re-review of the `[task 13 fix]` that closed the prior round's Important finding (bare `git commit` sweeps a concurrently-staged stray into the bookkeeping commit) + Minor plan-gap (timeout-leg N63 write had no fault-injection test).

## Strengths
- **Both new tests non-vacuous** (mutation-proven, not trusted-green).
- **The two stray tests are genuinely distinct discriminators.** The pre-existing `test_commit_never_sweeps_unrelated_worktree_state` stages nothing (catches `git add -A` vs explicit paths). The new `test_staged_stray_does_not_ride_into_bookkeeping_commit` injects `git add "{stray}"` (confirmed in body: `cmux_v2_stub(extra=': > "{stray}"; git add "{stray}"')`), so only the commit's own `-- "${BK_PATHS[@]}"` scoping keeps it out. Under mutation the untracked sibling stayed GREEN while the staged test went RED — different layers.
- **Form C correct.** `git add` lines retained (files tracked first — needed on hop 1 when untracked), THEN the pathspec commit — did NOT regress into the naive `git commit -- <literal untracked paths>` that errors "pathspec did not match".
- **`${BK_PATHS[@]}` safe** — array unconditionally initialized to 2 elements, can never expand empty (which would make `git commit --` commit the whole index). `+=` is bash-3.1+; `bash -n` clean; no `set -u/-e/pipefail`; fix sits inside the `else` of the `--no-commit` gate.
- **Timeout-leg test asserts the right invariants**: exit 3 unchanged, warn text present, audit-trail gap (intent present / outcome absent), reservation hop counter still 1.

## Issues
None (Critical/Important/Minor all none).

## Assessment — **Fix approved? Yes.**
Both prior defects correctly closed and defended by biting tests. Positive controls green first; each mutation RED for the right reason; each restored clean. Full `test_spawn_handoff_v2.py` 96/96 post-restore; no regression; tree clean.

### Mutation log (`cp` backup, never `git checkout`/`stash`)
| # | Mutation | Test | Result | Restored |
|---|----------|------|--------|----------|
| 1 | drop `-- "${BK_PATHS[@]}"` → bare `git commit` | `test_staged_stray_does_not_ride_into_bookkeeping_commit` | **RED** (stray rode in) | clean, no diff vs HEAD |
| 1b | (same) | `test_commit_never_sweeps_unrelated_worktree_state` (untracked sibling) | **GREEN** (confirms distinct layers) | clean |
| 2 | timeout-leg `if ! printf; then warn fi` → unchecked `printf 2>/dev/null` | `test_unwritable_log_on_timeout_path_still_exit_3` | **RED** (warn absent; exit still 3 — bites on warn-wrapping) | clean, no diff vs HEAD |

Controller-run full suite (authoritative): **821 passed, 0 failed** (819 baseline + 2 new).
