# Code Quality Review — Task 13 (durable outcome writes N63 + bookkeeping commit + card)

**Model:** opus (adversarial + mutation) · **BASE** `8726d22` → **HEAD** `96c4d48` · **Verdict: Ready to merge — WITH FIXES** (0 Critical, 1 Important, 1 Minor plan-gap)

## Strengths
- N63 exit-code invariant genuinely pinned: M2 (success write-failure → `exit 1`) drives `test_unwritable_log_on_success_path_warns_still_exit_0` RED on the `returncode==0` assert — protected on both warn-text AND exit-code axes.
- `TestDurableOutcome` asserts the actual audit-trail gap (`intent` present, `outcome` ABSENT), not just warn text. M1/M3 (unchecking success/spawn-failed writes) → RED.
- `git add -A` discriminator claim verified TRUE and EXCLUSIVE: M5 (`<paths>`→`-A`) turns exactly ONE test RED (`test_commit_never_sweeps_unrelated_worktree_state`); the other 7 stay green. That test carries its own positive control (`assert stray.exists()`).
- Bash clean: no `set -u/-e/pipefail`; the three N63 `then`-bodies contain only `cmux notify … || true` + `echo >&2` (branch exits sit outside the wrapped blocks); `CMUX_SABOTAGE_ON_WAITFOR` chmod guarded by `[ -n … ]` at both stub sites — no leak. No dead code added.

## Issues
### Important
1. **`spawn-handoff-session.sh` bare `git commit` sweeps a concurrently-STAGED file into the `chore(sdd)` bookkeeping commit.** After `git add "$HOPS_FILE" "$SPAWN_LOG"` (explicit, correct), the commit carries no pathspec → commits the whole index. Demonstrated empirically (staged stray via the stub `extra` hook lands in the commit). CURRENTLY UNTESTED: `test_commit_never_sweeps_unrelated_worktree_state` uses an *untracked* stray (discriminates `-A`, not the bare-commit window); a *staged* stray rides straight through. → **[task 13 fix]** (see adjudication for the correct Form-C fix + required staged-stray test).

### Minor
2. **Timeout-leg N63 wrapping (`:854-860`) has zero fault-injection coverage** — M4 (uncheck the timeout write) is the ONLY outcome-path mutation that stays GREEN. **Plan gap, not an implementer defect** (Step 1 specified only success + spawn-failed `TestDurableOutcome` tests; implementer wrote exactly those). If closed, it's a near-copy of the spawn-failed test (`CMUX_WAITFOR_RC=1` + `CMUX_SABOTAGE_ON_WAITFOR=1` + `SABOTAGE_TARGET`). Controller's discretion — do NOT bounce as a Task 13 implementer deviation.

## Concern Adjudication — bare `git commit`
**Verdict: real risk, fix now as `[task 13 fix]` (Important), NOT a merge-blocker.**
- Real + demonstrated; matches plan Step-2b fence exactly.
- **The naive fix is a TRAP:** `git commit -- "$HOPS_FILE" "$SPAWN_LOG"` ERRORS on untracked files ("pathspec did not match") — the common first-hop case (all 3 files new) — breaking 4 tests (commit silently fails → warn → no commit → successor Precondition 1 refuses). Worse than the bug.
- **Correct fix (Form C, verified in isolation → rc 0, commits exactly 3 files, leaves staged stray uncommitted), bash-3.2-safe:**
  ```bash
  git add "$HOPS_FILE" "$SPAWN_LOG" 2>/dev/null
  BK_PATHS=("$HOPS_FILE" "$SPAWN_LOG")
  [ -f "$REPORTS_DIR/handoff-mechanics.md" ] && { git add "$REPORTS_DIR/handoff-mechanics.md" 2>/dev/null; BK_PATHS+=("$REPORTS_DIR/handoff-mechanics.md"); }
  if ! git commit -m "chore(sdd): record handoff hop $SP_HOP" -- "${BK_PATHS[@]}" >/dev/null 2>&1; then …
  ```
  Ship WITH a staged-stray test (the `extra`-hook harness exists) or the fix is unprotected.
- **Downstream interaction (decisive):** Task 15 (same module) makes Check 9 exclude by feature-dir path-set. A swept file OUTSIDE feature_dir (a real source file) becomes a Check-9 false-trip in a verification window — fails CLOSED (noisy block, not open), safer, but interacts with a gate this module builds.
- Not a blocker because Precondition 1 refuses a dirty tree at start, the design isolates spawns in their own worktree, post-commit the tree is clean either way, and the Check-9 interaction fails closed. But the fix is ~5 min, in-module, strictly tighter, and the feature's whole point is shared-worktree cleanliness → fix-now.

## Assessment
**Ready to merge? With fixes.** Route the Important finding as `[task 13 fix]` (Form C + staged-stray test) before the module transition; close the Minor timeout-leg gap (near-copy test) in the same round at controller discretion.

### Mutation log (restored via `cp` backup + `diff -q`; never `git checkout`/`stash`)
| # | Mutation | Result |
|---|----------|--------|
| M1 | success outcome write made unchecked | RED (warn absent) |
| M2 | success write-failure branch → `exit 1` | RED (exit-0 invariant) |
| M3 | spawn-failed outcome write made unchecked | RED (warn absent) |
| M4 | timeout outcome write made unchecked | **GREEN** (untested leg — finding #2) |
| M5 | `git add <paths>` → `git add -A` | RED, exactly 1 test (sole discriminator confirmed) |
| M6 | commit message changed | RED (3 tests) |
| M7 | `--no-commit` gate neutralized | RED (1 test) |
| M8 | card generation neutered | RED (3 tests: gen + ordering) |
| M9 | commit-failure `if !` unwrapped | RED (1 test) |
| M10 | commit injected into timeout branch | RED (`test_timeout_path_does_not_commit`) |

Baseline: TestDurableOutcome + TestBookkeepingCommit = 10 passed. Full regression after restores: v2 94 passed; test_spawn_handoff.py + hardening 87 passed. Script byte-identical to pre-review baseline.
