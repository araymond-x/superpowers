---
schema_version: 1
task_id: 11
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Added POST_SPAWN_DEFAULT/POST_SPAWN knob (validate-warn-revert, ${var-def} so empty-string is a valid disabling value distinct from unset) beside the other Layer-0 knobs. Added post_spawn_send_verified() (3-arg, both anchors fixed-string grep -F per the AMENDED fence — no regex/alternation branch, no dead code) and run_post_spawn() (ordering canonicalization: rc,rename reorders to rename,rc with a warning citing operator addendum #3; iterates POST_SPAWN, stops at first verify failure, sets POST_SPAWN_FIELD). Wired `[ -n \"$POST_SPAWN\" ] && run_post_spawn` between the handshake-success point (\"Token received\") and the outcome-record printf; POST_SPAWN_FIELD appended as a third %s alongside TOPOLOGY_FIELD/BUDGET_FLAG."
  - path: "tests/unit/test_spawn_handoff_v2.py"
    description: "Added TestPostSpawn (7 tests: default sequence order, verify-failure-warns-partial, knob-disables-all, knob-subset-and-invalid-token [2 legs], title-format-override, echo-only negative fixture [AMENDED], ordering-reorder [AMENDED]) plus helpers (_post_spawn_screen, _echo_only_screen, _success_ctx, _run_post_spawn, _send_lines, _post_spawn_verbs, _rc_anchor/_rename_anchor pulling MEASURED values from cmux-verb-shapes.json). Fixed 6 pre-existing TestSurfaceTopology tests broken by post-spawn's default-on behavior (5 outright failures on exact send-count/content assertions; 1 — test_unset_knobs_are_not_forwarded_as_empty — had gone silently vacuous, confirmed by mutation) by adding SUPERPOWERS_CMUX_POST_SPAWN=\"\" to each test's own env."
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md"
    description: "Added one row documenting the implementation-time blast-radius fix (6 pre-existing tests) and the vacuity catch, with mutation evidence."
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/.dispatch-log"
    description: "Auto-appended by the SDD pre-dispatch hook on my own implementer dispatch (task=11)."
  - path: "docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/context-observations.log"
    description: "Auto-appended by the context-pressure gate on my own dispatch (tier=soft action=nudge)."
tests:
  written: 7
  passing: 7
  command: ".venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider (FULL SUITE: 796 before -> 803 after, 0 failed; the 7 here are this task's new tests; 6 pre-existing tests were also modified, not counted as written)"
  result: PASS
contract_compliance:
  - constraint: "Bash >= 3.2; NO set -u/set -e/pipefail"
    status: compliant
    detail: "None introduced — grep -nE '^\\s*set -[ue]|pipefail' matches only pre-existing explanatory comments. shellcheck --severity=warning --external-sources exits 0. bash -n clean."
  - constraint: "printf not echo for composed strings"
    status: compliant
    detail: "The outcome record uses printf (POST_SPAWN_FIELD appended as a new %s). My two new echo calls are stderr diagnostics, matching every other WARNING/[spawn-handoff] line in this file's own established convention — not composed strings sent anywhere."
  - constraint: "Never pipe a producer into grep -q — use here-strings"
    status: compliant
    detail: "grep -qiF \"$2\" <<< \"$screen\" uses a here-string. No new pipe-into-grep-q introduced (grep -n '| grep -q' matches nothing new)."
  - constraint: "Env knobs validate-warn-revert"
    status: compliant
    detail: "SUPERPOWERS_CMUX_POST_SPAWN validates against ^(rename|rc)(,(rename|rc))*$, warns, and reverts to POST_SPAWN_DEFAULT on an invalid value — proven by test_knob_subset_and_invalid_token's second leg (rename,bogus)."
  - constraint: "A received token is the ONLY exit-0 path; post-spawn failures are WARNINGs, never a spawn failure"
    status: compliant
    detail: "run_post_spawn only ever returns 0; post_spawn_send_verified's failure path sets POST_SPAWN_FIELD and returns 1, which run_post_spawn converts back to a 0 return via the || { ...; return 0; } pattern. test_verify_failure_warns_partial_never_fails_spawn and the echo-only negative-fixture test both assert exit 0 with post_spawn=partial:<step>."
  - constraint: "Fallback fires ONLY before launch accepted; after cmux send rc 0, NEVER spawn again"
    status: not_applicable
    detail: "Task 11's code runs entirely after handshake=ok, downstream of the launch-accepted point; it creates no new spawn target and calls no spawn verb (new-surface/workspace create)."
  - constraint: "Exit codes stay 0/3/1"
    status: compliant
    detail: "No new exit path introduced; the success stanza's existing `exit 0` is unconditional and unchanged in position — post-spawn only affects the outcome record's post_spawn= field and stderr diagnostics."
  - constraint: "Task 11's own work does not touch exit codes"
    status: compliant
    detail: "Verified directly: the wiring call site and both new functions contain no `exit` statement."
---

**Implementation Summary:**

Task 11 adds the last piece of the spawn script's success path: after `wait_for_token` confirms `handshake=ok`, `run_post_spawn` script-drives `/rename` and `/rc` inside the successor's terminal and verifies each landed by reading the screen back against the AMENDED fence's MEASURED, echo-proof anchors (`Session renamed to:`, `/remote-control is active`). A verify failure records `post_spawn=partial:<step>` and stops the sequence, but never changes the exit code — the whole feature is cosmetic per the module's Contract Constraints. `SUPERPOWERS_CMUX_POST_SPAWN` (default `rename,rc`) selects/disables steps with validate-warn-revert; `rc,rename` is canonicalized to `rename,rc` with a warning citing operator addendum #3 (`/rc` must be sent last), never rejected.

**Source Files Read:**
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-3-spawn-script.md` lines 1–56 (Contract Constraints, File Map, Write-Scope Partitioning) and 738–847 (Task 11's full text including the AMENDED note, both fence blocks, and the Module 3 Acceptance Criteria) — read verbatim, not summarized.
- `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json` (`rc_confirmation_screen` key, READ-ONLY) — the measured anchors, sent lines, and rationale fields the fence and my tests are built against.
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — the whole file, in particular Task 10's landed `wait_for_token`/`diagnose_target`/timeout-tail/success-stanza block, `TOPOLOGY_FIELD`'s pattern, and Task 9's `rename-tab`/`TAB_TITLE` composition.
- `tests/unit/spawn_handoff_helpers.py` — `cmux_v2_stub()` and its knob table (`CMUX_SCREEN_FILE`, `CMUX_WAITFOR_RC`), `run_spawn`'s env-construction order.
- `tests/unit/test_spawn_handoff_v2.py` — the whole file, especially `TestHandshake`'s `_timeout_ctx`/`_diagnose`/`_wait_for_lines` helpers (the interleaved-argv-sidecar gotcha they document, which is why `_send_lines` filters the flat log by line rather than using `_argv`), `TestSurfaceTopology`'s existing tab-title tests (confirming default `TAB_TITLE="hop1 SDD feat"` for a fresh worktree).
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-010-implementer-report.md` and `task-010-quality-review.md` — Task 10's wiring point, its mutation-testing discipline, and its report-section-naming correction.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md` rows 172 and 295 — confirmed the AMENDED fence's anchors/ordering/dead-code-collapse were already resolved at the pre-dispatch obligation audit, so I built directly against the current plan text rather than re-litigating it.
- `CLAUDE.md` (worktree root). No subdirectory `CLAUDE.md` exists — verified with `find . -name CLAUDE.md -not -path "./.git/*"`, which returned exactly one path (the root).

**Self-Review Findings:**

1. **A real, non-obvious regression found and fixed: `POST_SPAWN_DEFAULT="rename,rc"` is default-on and fires on every genuine `handshake=ok`, which broke 5 pre-existing `TestSurfaceTopology` tests outright** (`test_surface_happy_path`, `test_sent_command_ends_with_the_successor_command`, `test_sent_command_carries_inline_env`, `test_forwarded_knob_values_are_shell_quoted`, `test_send_failure_on_surface_falls_back`) because they assert exact `send`-call counts or exact sent-payload content and post-spawn's own `/rename`/`/rc` sends add noise after `wait-for`. Measured the full suite before touching anything (796 passed per Task 10's baseline, re-confirmed independently) and after my first pass (5 failed). Fixed by adding `SUPERPOWERS_CMUX_POST_SPAWN=""` to each test's own `_reach_gate(...)` call — surgical, not a shared-harness change, since only 6 of the file's 82 tests actually assert on exact `send` content/count.
2. **A sixth test had gone silently VACUOUS, not merely broken — the more dangerous failure mode.** `test_unset_knobs_are_not_forwarded_as_empty` stayed green because `_sent_text` (last logged `send` call's payload) now returns post-spawn's own `/rename` line instead of the launch's, so its negative assertion (`"KNOB" not in sent`) trivially passed regardless of what the launch actually forwarded. Confirmed by mutation: removed the `[ -n "$v" ] && ` forwarding guard from `INLINE_ENV`'s composition — the test stayed green. Fixed the same way (disable post-spawn), then re-ran the identical mutation and confirmed the test now goes RED, then restored the script via file copy + `diff -q` (never `git checkout --`/`git stash`).
3. **Positive-controlled my two highest-risk new pins per the self-review instructions.** (a) The ordering-reorder logic: removed the `if [ "$POST_SPAWN" = "rc,rename" ]` guard entirely — `test_knob_order_rc_before_rename_is_reordered_with_warning` went RED (sent `/rc` before `/rename`). (b) The anchor-safety fix itself: reverted `post_spawn_send_verified`'s call-site anchors to the pre-amendment bare forms (`$TAB_TITLE` alone, `/remote-control` alone) — `test_echo_only_screen_does_not_false_positive_either_anchor` went RED (`KeyError: 'post_spawn'`, i.e. false success), proving the negative fixture genuinely exercises the hazard the AMENDED fence closed. Both mutations restored by file copy + `diff -q` verified identical; the full `TestPostSpawn` class re-confirmed green (7 passed) after each restore.
4. **Deliberately did not check in new screen fixture files under `tests/unit/fixtures/spawn-handoff/screens/`.** Unlike Task 10's static diagnosis screens, post-spawn's confirmation text embeds the dynamically-computed `TAB_TITLE` (default `"hop1 SDD feat"`, or a knob override), so a checked-in fixture would either hardcode a title unrelated to the test's own knob configuration or require per-test parameterized fixtures. Built via a `_post_spawn_screen()`/`_echo_only_screen()` helper writing to `tmp_path` instead, pulling the anchor strings from `cmux-verb-shapes.json` at test time (never hardcoded duplicates) so the fixture's measured provenance is preserved.
5. **Fence's collapsed 3-arg `post_spawn_send_verified`** — confirmed no `$4`/regex-vs-fixed branch exists anywhere in the function; both anchors are `grep -qiF` fixed-string, matching the plan's "collapsed to a 3-arg function, one match mode, no unused branch" requirement.

**Deviations from Plan:**

1. Fixed 6 pre-existing tests in `TestSurfaceTopology` (5 outright failures + 1 vacuity) that Task 11's own fence did not enumerate — necessary to satisfy "run the FULL unit suite" and this module's own Acceptance Criteria bullet ("the FULL unit suite green after every task"). Recorded as a `deviations.md` row (same shape as Task 9's "migration blast radius" row). All 6 are within `test_spawn_handoff_v2.py`, squarely inside Task 11's write scope.
2. No new checked-in screen fixtures (see Self-Review Finding 4) — a deliberate design choice given `TAB_TITLE` is dynamic, not a scope reduction.

**Concerns:**

1. **Post-spawn has never run against a live cmux surface**, same evidence-gap class Task 10 already disclosed for `diagnose_target` — coverage here is unit-level against a stub, not a live capture of a spawned successor typing `/rename`/`/rc` and reading its own screen back. The anchors themselves ARE measured from a live capture (Task 0's `rc_confirmation_screen`), but the *sequencing* (send → send-key → sleep 2 → read-screen, twice) has not been exercised live.
2. **The `sleep 2` between send and read-screen is untimed/unmeasured** — Task 0's fixture captures the confirmation screens' *content* but not how long a real cmux surface takes to render a slash-command's response after the Enter key. If 2s proves insufficient in production, `post_spawn_send_verified` degrades to `partial:<step>` (a WARNING, never a failure) — bounded but unverified against real timing.
3. Full unit suite re-measured fresh (not inherited): **796 → 803 passed, 0 failed**, 379.55s. `tests/integration/sdd-e2e-test.sh` was not touched and not run (RED by design until Task 17).
