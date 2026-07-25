---
schema_version: 1
task_id: 10
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/integration/sdd-e2e-test.sh"
    description: "Added Step 14 (spawn-handoff-session.sh end-to-end with stubbed cmux/claude-picker, using the controller-corrected file-not-directory fixture) and bumped the final banner from 14 to 15 steps."
tests:
  written: 9
  passing: 9
  command: "bash tests/integration/sdd-e2e-test.sh"
  result: PASS
contract_compliance:
  - constraint: "Exit-code contract (0 spawned / 3 manual fallback / 1 refused)"
    status: compliant
    detail: "Step 14 exercises the exit-0 spawned path only (stubs are configured to succeed at every precondition); exit 3/1 paths are already covered by the unit suite (test_spawn_handoff.py), not re-tested here — that's within scope, the module's AC asks for the composed-command proof."
  - constraint: "Do not change sdd-pre-dispatch-hook.sh or the hook baseline"
    status: compliant
    detail: "git diff --name-only against both paths is empty, confirmed before and after commit."
  - constraint: "spawn-handoff-session.sh frozen — restored if mutated for proofs"
    status: compliant
    detail: "Mutated 3 times for mutation-proofs; each time restored via `git checkout --` and verified `git diff --name-only` returned 0 lines before proceeding to the next mutation."
---

**Implementation Summary:** Inserted Step 14 into `tests/integration/sdd-e2e-test.sh`, using the controller-corrected fixture (executable file, not directory, for the picker version) and replacing the plan's placeholder with two composed-command assertions derived from an actual run. Bumped the final banner to "15 steps composed correctly."

**Source Files Read:**
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (full file) — learned the full launch-composition path: `preflight_ok()`'s five-way AND, the label-increment regex at `:284-301`, `build_successor_cmd()`'s exact token order at `:334-348`, and that `WORKTREE_ROOT` is resolved via `git rev-parse --show-toplevel` against the **caller's cwd** (no path argument) — this is what exposed the missing-`cd` defect below.
- `tests/integration/sdd-e2e-test.sh` (Step 13 + top-of-file preamble) — confirmed the real idioms (`|| RC=$?`, PASS echo, `rm -rf` cleanup at the very end only, no `PATH` stubbing) and that the script `cd`s into `$WORK` once at line 14 and stays there for the rest of the file.
- Repo-root `CLAUDE.md` — "Testing" and "Behavioral Test Gotchas" sections; used the `shellcheck` direct-invocation guidance instead of the vacuous no-arg `lint-shell.sh`.

**CLAUDE.md Files Read:** repo-root `CLAUDE.md` — confirmed no subdirectory `CLAUDE.md` exists under `tests/`.

**Deviations from Plan:** Beyond the two controller-supplied fixture corrections (executable file + `launch=auto` assertion), I found and fixed a third defect in the given Step 14 block during implementation: **the block as handed to me never `cd`s into `$SPAWN_WT` before invoking the script.** `spawn-handoff-session.sh` resolves `WORKTREE_ROOT` via `git rev-parse --show-toplevel` against the *caller's* cwd — since the e2e harness stays `cd`'d into `$WORK` for its entire run (set once at line 14), invoking the script without an explicit `cd "$SPAWN_WT"` first makes it resolve `$WORK` as the worktree instead of the fixture, and `$WORK` is virtually never a clean git tree at that point in the pipeline. I verified this empirically before fixing it: running the given block's env-var-prefixed invocation without a `cd` reproduced `REFUSED: worktree not clean — commit pending state first (protocol step 2)` (RC=1); adding `( cd "$SPAWN_WT" && ... )` around the same invocation produced the expected `RC=0` and the full expected output. Fixed by wrapping the invocation in a subshell that `cd`s into `$SPAWN_WT` first (documented inline with the empirical finding). This is an "obvious, reversible" fix required to make the given block actually work, not a scope change — noted here rather than in `deviations.md` since that ledger is the controller's to maintain, but flagging for the controller to log if desired.

**Self-Review Findings:** Initially wrote unnecessary `rm -rf "$SPAWN_WORK"` calls into each of Step 14's `FAIL` branches. Checked Step 13 and the rest of the file for convention: **no step anywhere cleans up its temp workspace on a failure path** — cleanup happens only after all checks pass, by design (the top-of-file `echo "Workspace: $WORK"` shows the file's philosophy is to preserve state for debugging on failure, and the whole script runs under `set -e` + a bare ERR trap that just echoes and exits). Removed the extra `rm -rf` calls from all `FAIL` branches to match the file's established convention rather than inventing a new one. Re-ran the full suite and `shellcheck` after this fix; both still clean.

**Concerns:** None beyond the documented deviation above (the missing `cd`, now fixed and verified).

**Mutation proofs:**

| Assertion | Mutation | Observed FAIL | Restored? |
|---|---|---|---|
| `launch=auto` | `preflight_ok() { return 1; ...}` — forces picker-manual unconditionally | `FAIL: expected launch=auto — fixture degraded to picker-manual` + dump showing `launch=picker-manual` and `successor command: claude-picker '/pickup b14'` | Yes — `git checkout --`, `git diff --name-only` → 0 lines |
| Flag-order/telemetry/label assertion | Swapped `--telemetry`/`--pick-version` order in `build_successor_cmd`'s `parts=(...)` | `FAIL: composed command missing expected flag order/telemetry/incremented label` + dump showing `--telemetry on --pick-version 2.1.218` (swapped) | Yes — `git checkout --`, `git diff --name-only` → 0 lines |
| Forwarded-arg re-quoting + trailing `/pickup` assertion | Changed `parts+=("$(shq "$a")")` to `parts+=("$a")` in the `FORWARDED` loop (dropped re-quoting) | `FAIL: composed command missing forwarded arg (re-quoted) + trailing /pickup b14` + dump showing `--append-system-prompt-file /tmp/a b.md '/pickup b14'` (unquoted, so the path silently split on the space) | Yes — `git checkout --`, `git diff --name-only` → 0 lines |

Between each mutation and the next, I confirmed `git diff --name-only skills/subagent-driven-development/scripts/spawn-handoff-session.sh` returned 0 lines before proceeding. No `git stash` was used anywhere.

**Verbatim evidence:**

Actual `[spawn-handoff] successor command: …` line (from the cd-fixed, un-mutated run — this is what my two assertions were derived from):
```
[spawn-handoff] successor command: claude-picker --non-interactive --pick-version 2.1.218 --telemetry on --session-label Proj-Session-3 --append-system-prompt-file '/tmp/a b.md' '/pickup b14' || { printf '%s %s runtime-picker-failure hop=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "915a2d90-3f05-4c8a-aa00-2d9d0050c4f0" "1" >> /private/var/folders/5b/xvnzjr955fsfg2kr5c8vkqkm0000gn/T/sdd-spawn-probe-XXXXXX.PLG1CntroE/wt/docs/imp-plans/feat/reports/handoff-spawn.log; claude-picker '/pickup b14'; }
```

Actual `launch=` line from the same run (evidencing `auto`, not `picker-manual`):
```
[spawn-handoff] launch=auto
```

Real final line of `bash tests/integration/sdd-e2e-test.sh` (post-fix, post-mutation-proofs, post-commit):
```
E2E PIPELINE PASS - 15 steps composed correctly
```
(exit code 0; all 15 `PASS: Step N …` lines present in the run, Step 14's being `PASS: Step 14 — spawn end-to-end: composed command, notify, reservation-then-outcome`)

Real `shellcheck` result:
```
$ shellcheck --severity=warning --external-sources tests/integration/sdd-e2e-test.sh
$ echo $?
0
```
(no warnings printed, exit 0 — not the vacuous no-arg `lint-shell.sh` form)

`git diff --name-only` after committing (comparing the commit to its parent):
```
tests/integration/sdd-e2e-test.sh
```

`git status --short` (post-commit, proving no fixture residue from my work):
```
 M docs/imp-plans/2026-07-22-cmux-integration/deviations.md
 M docs/imp-plans/2026-07-22-cmux-integration/reports/.dispatch-log
 M docs/imp-plans/2026-07-22-cmux-integration/reports/context-observations.log
?? docs/imp-plans/2026-07-22-cmux-integration/reports/checkpoint-pre-dispatch-010.json
?? docs/imp-plans/2026-07-22-cmux-integration/reports/partner-review-010.md
```
These four entries pre-existed at dispatch time (controller's own SDD artifacts — dispatch log, deviations, checkpoint, partner review) and were never touched by me; `tests/integration/sdd-e2e-test.sh` itself shows clean (fully committed). I also confirmed no leaked `sdd-spawn-*` temp directories remain under `/var/folders/.../T/` after the final run.

---

## Controller verification (independent, before dispatching review)

**The implementer found a THIRD defect in the plan's Step 14 block, and it is REAL. Verified independently:**

| Claim | What the controller ran | Result |
|---|---|---|
| `WORKTREE_ROOT` resolves against the **caller's cwd**, with no path argument | `grep -n 'WORKTREE_ROOT=' spawn-handoff-session.sh` | **CONFIRMED** — `:53` is `WORKTREE_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"`, bare, no path |
| The e2e harness `cd`s into `$WORK` early and stays there | `grep -n '^cd \|^WORK=' tests/integration/sdd-e2e-test.sh` | **CONFIRMED** — `:12` `WORK=$(mktemp -d …)`, `:14` `cd "$WORK"` |
| The `cd` fix is present in the committed block | `grep -n 'cd "\$SPAWN_WT"'` | **CONFIRMED** — the invocation at `:676` is wrapped `( cd "$SPAWN_WT" && \`, with an explanatory comment at `:668` |
| Exactly one file in the commit | `git show --stat --format="" HEAD` | **CONFIRMED** — `tests/integration/sdd-e2e-test.sh`, 119 insertions / 1 deletion |
| Frozen artifacts intact across all of Task 10 | `git diff --name-only f95912c..HEAD` scoped to the 3 frozen paths | **CONFIRMED — empty** |

The implementer's own evidence for the defect carried a **positive control**, which is why it is credible rather than
merely plausible: it reproduced the failure first (`REFUSED: worktree not clean`, RC=1) and only then showed the fix
producing RC=0. It did not simply assert that a `cd` was needed.

**Note on the observed error message:** the implementer saw `REFUSED: worktree not clean` rather than
`REFUSED: not in a git repository`, which implies `$WORK` is itself a git repository by the time Step 14 runs — i.e. an
earlier e2e step `git init`s a fixture inside `$WORK`. That detail does not affect the finding (either message is an
exit-1 refusal and the fixture is never reached), but it is recorded rather than smoothed over, and it means the defect
would have manifested as a confusing "not clean" complaint about a directory the reader never intended to be the
worktree.

**Controller assessment of the report:** honest and unusually good. It (a) found a real defect the controller and the
partner both missed, (b) proved it before fixing it, (c) declined to invent a cleanup-on-failure convention after
checking that the file has none, and (d) explicitly declined to write to `deviations.md` itself, correctly identifying
that ledger as the controller's to maintain — and flagged it for logging instead. Status `DONE_WITH_CONCERNS` is the
correct routing signal. **All three mutation proofs pasted real FAIL output rather than eliding it**, which is the
standard the two Task 9 fix implementers did not meet.
