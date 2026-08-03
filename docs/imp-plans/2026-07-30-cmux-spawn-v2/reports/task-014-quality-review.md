# Code Review — Task 14 (Hooks trio + baseline re-capture), `dc642f6..dd68580`

### Strengths

- The three hook edits match the plan fences character-for-character (session-start and Check 3b byte-identical; stop-hook fence has one `\\n` vs `\n` difference, proven semantically identical in a bash double-quoted string).
- The atomic-commit constraint genuinely holds: `dd68580` contains all three hooks + baseline.txt + tests; `check-hooks.sh` PASSes at HEAD with no drift.
- The Check 3b bidirectional claim is real, independently reproduced.
- `( cmd & )` backgrounding is properly tested — mutation D (remove `&`, keep subshell) reddens two tests, stronger than the implementer credited.
- Honest self-reporting: implementer proactively flagged the vacuous-suppression-test shape and the latent gate rather than leaving them for review.
- No new lint findings on the three edited hooks. Bash 3.2 constraints respected (no `set -u`/`set -e`/pipefail added; `grep -qE` runs against a file, not a pipe — no SIGPIPE hazard).

### Mutation Testing Log

Backups via `cp`, restores verified via `cp` + `diff -q` + `shasum -a256` against committed baseline hashes. No `git checkout --`, no `git stash`.

| # | Mutation | Expected RED | Actual | Verdict |
|---|---|---|---|---|
| A | Remove `handoff-\|` from Check 3b allowlist | `test_handoff_prefix_reports_allowed` | RED; junk test stayed green | discriminating |
| B | Widen allowlist with `.*` catch-all | `test_junk_reports_still_blocked` | RED; others stayed green | discriminating |
| C | Delete session-start `if` block | `test_signal_fires_when_spawn_id_set` | RED, only that one | as declared |
| D | Remove trailing `&` (keep subshell) | hanging test | RED — and also the failing-cmux test | better than claimed |
| E | Full revert of Decision-15 stop-hook change | ? | RED: `test_warns_on_unmatched_bundle` + xfail; 4 stayed green | see below |
| F | Break suppression regex -> `ZZZNEVERMATCH` | ? | RED: outcome + decline suppression tests | discriminating |
| G | Drop `$BREPO` = `$REPO_ID` filter | ? | RED: `test_unrelated_repo_bundle_ignored` | discriminating |
| H | Drop `SESSION_START` guard alone | ? | all green — only reddens if `START_EPOCH` guard also removed | weak |

**Overturns the implementer's and spec reviewer's "3 of 6"/"4 of 6" conclusion.** Mutations F and G prove `test_outcome_record_suppresses_warning`, `test_decline_record_suppresses_warning`, and `test_unrelated_repo_bundle_ignored` are genuine discriminators against bugs *inside* the block — whole-feature revert is a degenerate mutation for a suppression test by construction. Only `test_missing_transcript_silently_skips_check` is genuinely weak.

Post-review: `git diff HEAD` empty for all three hooks; `check-hooks.sh` PASS; full suite re-run 833 passed, 1 xfailed.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)

**1. [RESOLVED BY CONTROLLER] Stranded git index — a staged revert of the entire stop-hook edit.**
`git status` showed `MM skills/subagent-driven-development/scripts/sdd-stop-hook.sh` — the index held the pre-Task-14 blob while HEAD/worktree held the correct version. Invisible to `check-hooks.sh` (hashes the worktree) and to file-level `git show --stat`. Attribution undetermined (not `git stash`, not clearly either reviewer's mutation cleanup). **Fixed by the controller**: `git reset -- skills/subagent-driven-development/scripts/sdd-stop-hook.sh`, confirmed `git diff HEAD` empty and `check-hooks.sh` still PASS.

**2. [ACCEPTED, documented] Undeclared reformat inside the atomicity-justified commit.**
`test_sdd_classification.py` (193+/63-, only 32 lines are the two genuinely new tests) and `test_honesty_log_capture.py` carry ad hoc reformatting of pre-existing code — no formatter config exists in the repo. Undeclared in the implementer's Deviations section. Controller decision: accept with a deviations note (zero functional risk, not worth a fix round on its own) — logged.

#### Minor (Nice to Have)

**3. [FIX DISPATCHED] Dead code** — `tests/unit/test_session_start_signal.py:91-92`, an unused `env` dict. Classified Minor (zero behavioral surface, surrounding test correct per mutation C) rather than blocking. Routed to a `[task 14 fix]` round for deletion (trivial, test-file-only, no baseline recapture needed).

**4. [ACCEPTED, documented] `test_missing_transcript_silently_skips_check` is weak** (mutation H) — reddens only when both the `SESSION_START` and `START_EPOCH` guards are removed together. Defense-in-depth negative test; vacuity under single-guard mutation is inherent to the shape. Cheap future improvement: assert stdout is exactly empty.

**5. `$BID` charset safety verified at the source** — `build_bundle_id()` in `claude-codex-handoff` slugifies to `^[A-Za-z0-9_.-]+$`; all 156 real bundle ids on disk match. Caveat: `--bundle-id` override bypasses slugify, but worst case is fail-safe (false suppression or grep exit 2 -> treated as no-match -> warning fires). No injection risk — none of `$BID`/`$REPO_ID`/`$SESSION_START` reach a shell-evaluated context.

**6. One character-level fence divergence** (`\\n` vs `\n`) — proven semantically identical. No action.

### Latent-Bug Adjudication

**Verdict: DEFER.** Disposition: Accepted-with-BACKLOG-row (coupled two-part). No `[task 14 fix]` round for this.

**Correction that strengthens the finding:** the `elif [ -n "$SPAWN_WARN" ]` branch also sits behind the same gate, so Decision 15's warning can only fire when the checkpoint exits exactly 0 (PASS, zero warnings). Verified against this feature's own real pre-completion checkpoint: exit code 1, status FAIL, blockers present. **Decision 15 as shipped cannot fire in this repo today** — not a regression (nothing behind the gate was reachable before), but the AC should not be recorded as verified-live.

**Why DEFER is not merely "the one-liner is risky":** the proposed one-liner (`if [ -z "$CHECKPOINT_OUTPUT" ]; then exit 0; fi`) is verified sound — `STATUS` comes from `jq -r '.status'`, not `$?`, so a warnings-on-PASS result would NOT cause spurious FAIL messages, and the crash path writes to stderr leaving stdout empty (correctly discriminated). The real blocker is a **second, coupled defect**: this repo has 31 bundles matching Decision 15's filter (`bundle_type=work` + matching `entry_skill` + `repo_id`) and zero `handoff-spawn.log` — every one reads as "unmatched." The filter cannot distinguish a human-pickup `/handoff` bundle (this repo's dominant end-of-session workflow) from an abandoned auto-spawn bundle; both carry identical `bundle_type`/`entry_skill`. Fixing the gate alone would turn an inert check into a false positive on nearly every session.

**Requested BACKLOG row (both halves, coupled — file at merge, per this feature's established BACKLOG.md-owned-by-concurrent-session convention):**
1. `sdd-stop-hook.sh` gate: drop the `$? -ne 0` disjunct (verified safe).
2. Do NOT ship (1) without addressing (2): Decision 15's bundle filter needs a way to distinguish human-pickup from abandoned-auto-spawn bundles before the gate fix can go live without misfiring.

The `xfail(strict=True)` tripwire is correctly wired and will force this decision back into view the day someone fixes the gate alone.

### Recommendations

1. Fixed: `git reset` on the stranded index.
2. Dead code fix dispatched.
3. Deviations.md updated with the corrected disposition and the coupled BACKLOG note.
4. Record that Decision 15 ships inert in production, not verified-live.
5. Reformat accepted with a documented note.

### Assessment

**Ready to merge?** With fixes (all addressed: stranded index fixed by controller, dead-code fix dispatched below, deviations.md updated).

**Reasoning:** The shipped hook logic is correct — three fences reproduced character-for-character, atomic-commit and baseline constraints genuinely hold, eight mutations surfaced no defect in the implementation itself. The blockers were operational (a stranded git index, invisible to every upstream check) and bookkeeping (latent-bug disposition, dead-code cleanup) rather than functional defects in the shipped hooks.
