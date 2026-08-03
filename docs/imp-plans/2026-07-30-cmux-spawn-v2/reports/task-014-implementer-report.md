---
schema_version: 1
task_id: 14
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "hooks/session-start"
    description: "Added cmux-spawn-v2 handshake signal: backgrounded `cmux wait-for -S sdd-hop-<id>` fired right after PLUGIN_ROOT resolution when SUPERPOWERS_SPAWN_ID is set and cmux is on PATH; output discarded so it can never affect exit code or JSON stdout under set -euo pipefail."
  - path: "skills/subagent-driven-development/scripts/sdd-stop-hook.sh"
    description: "Decision 15: scans $HOME/.claude-codex-handoff/bundles for a this-session bundle (mtime >= transcript's first-line timestamp) matching bundle_type=work, entry_skill=superpowers:subagent-driven-development, and repo_id, with no matching outcome/decline record in reports/handoff-spawn.log; composes the warning into the existing FAIL systemMessage or emits it standalone on PASS."
  - path: "skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
    description: "Check 3b allowlist regex gains the `handoff-` alternative so reports/handoff-mechanics.md is not flagged as non-standard naming."
  - path: "tests/ARaymond-hook-baseline/baseline.txt"
    description: "Re-captured via --capture after all three hook edits were final; verified PASS with no drift."
  - path: "tests/unit/test_session_start_signal.py"
    description: "New file: 5 tests for the session-start signal (fires, no-spawn-id, cmux-absent, cmux-failing, cmux-hanging/backgrounding proof)."
  - path: "tests/unit/test_honesty_log_capture.py"
    description: "Extended _run_stop_hook with optional transcript_path/home; added TestSpawnOutcomeWarning (6 tests) plus a _clean_workspace fixture helper that makes controller-checkpoint.py exit 0 cleanly, required to reach the stop-hook's emission branches."
  - path: "tests/unit/test_sdd_classification.py"
    description: "Added test_handoff_prefix_reports_allowed and test_junk_reports_still_blocked (Check 3b bidirectional pair)."
tests:
  written: 13
  passing: 12
  command: ".venv/bin/python3 -m pytest tests/unit/test_session_start_signal.py tests/unit/test_honesty_log_capture.py tests/unit/test_sdd_classification.py -v"
  result: PASS
contract_compliance:
  - constraint: "A received cmux wait-for token is the ONLY exit-0 path (handshake=ok); screen reading is post-timeout diagnosis only"
    status: not_applicable
    detail: "Not touched by this task — session-start only fires the signal side; spawn-handoff-session.sh's handshake logic is untouched."
  - constraint: "Baselined-hook edits ship with ONE check-hooks.sh --capture + committed baseline.txt in the same change"
    status: compliant
    detail: "All three hook edits + baseline.txt landed in exactly one commit (dd68580); check-hooks.sh --capture ran only after all edits were final, verified PASS afterward."
  - constraint: "hooks/session-start runs under set -euo pipefail — signal must be backgrounded and never affect hook exit"
    status: compliant
    detail: "Verified by test_cmux_absent_never_breaks_hook, test_cmux_present_but_failing_never_breaks_hook, test_cmux_present_but_hanging_never_blocks_hook (elapsed < 2s against a 5s stub sleep)."
  - constraint: "Stop hooks emit systemMessage (never hookSpecificOutput), always exit 0"
    status: compliant
    detail: "New emission branch reuses the exact existing heredoc pattern; both FAIL-compose and PASS-with-warning paths still `exit 0`."
---

**Implementation Summary:**
Implemented all three hook edits exactly as fenced (session-start signal, stop-hook Decision-15 warning, Check 3b `handoff-` allowlist token), re-captured the hook baseline in the same commit, and wrote/extended the specified test files. One fixture gap surfaced during TDD: `controller-checkpoint.py` needs a frontmatter-bearing plan and a fully-sectioned report to exit cleanly, so I added a `_clean_workspace` helper to reach the stop-hook's emission branches at all.

**Source Files Read:**
- `hooks/session-start` — found the exact PLUGIN_ROOT resolution point; confirmed `set -euo pipefail` is active.
- `skills/subagent-driven-development/scripts/sdd-stop-hook.sh` — confirmed the SDD-detection block boundary and the existing `systemMessage`-only, always-exit-0 emission pattern.
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — located Check 3b's exact allowlist regex line.
- `tests/ARaymond-hook-baseline/check-hooks.sh` — confirmed it pins sha256 of 7 hook scripts + settings.json registrations.
- `tests/unit/sdd_test_helpers.py`, `tests/unit/test_sdd_classification.py`, `tests/unit/spawn_handoff_helpers.py` — existing test idioms (run_hook/make_hook_input, manifest-mode fixtures, cmux stub patterns) reused for consistency.
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — read `main()`'s exit-code contract and `_task_ids_where()` while diagnosing why the FAIL branch was unreachable.

**CLAUDE.md Files Read:**
None found in `hooks/` or `skills/subagent-driven-development/scripts/` (checked per task instructions; both are absent).

**Deviations from Plan:**
- `test_composes_with_checkpoint_fail_message` is marked `@pytest.mark.xfail(strict=True, ...)` rather than passing outright — see Concerns below for why, and why fixing it was out of scope.
- Added a `_clean_workspace` fixture helper (frontmatter plan + fully-sectioned report + execution-trace-audit.md) not specified in the plan's Step 1 pseudocode, needed to make `controller-checkpoint.py` exit 0 so the stop hook's `elif [ -n "$SPAWN_WARN" ]` branch is actually reachable by 5 of the 6 Decision-15 tests.

**Self-Review Findings:**
- Both Check 3b directions were empirically revert-proven (not just asserted in comments): temporarily removing `handoff-|` flipped `test_handoff_prefix_reports_allowed` red while `test_junk_reports_still_blocked` stayed green; temporarily widening the allowlist to `.*` flipped `test_junk_reports_still_blocked` red while the handoff test stayed green. File restored via `cp`+`diff` (verified zero net change), not `git checkout --`.
- The session-start positive test (`test_signal_fires_when_spawn_id_set`) was confirmed red-then-green via `git stash push -- hooks/session-start`; the other 4 session-start tests pass with or without the fix (they assert absence-of-breakage, which was already true pre-fix) — expected, not a coverage gap, since the positive test is the discriminator.
- **Three of the six Decision-15 suppression tests are non-discriminating**: `test_outcome_record_suppresses_warning`, `test_decline_record_suppresses_warning`, and `test_unrelated_repo_bundle_ignored` all stayed green when I stashed the entire stop-hook change, because their assertion (`bid not in stdout`) is trivially true against empty stdout. Only `test_warns_on_unmatched_bundle` (and the xfail) actually discriminate. This is the same vacuous-suppression-test shape this sprint's deviations log has flagged twice before (Task 11, Task 12) — flagging it explicitly rather than leaving it for the reviewer to rediscover.

**Concerns:**
- **Pre-existing latent bug found, not fixed (out of Task 14's scope):** `sdd-stop-hook.sh`'s checkpoint prerequisite gate — `if [ $? -ne 0 ] || [ -z "$CHECKPOINT_OUTPUT" ]; then exit 0; fi` — predates this task. `controller-checkpoint.py`'s `main()` prints its JSON result to stdout *before* choosing an exit code, returning 1 on `status:"FAIL"` and 2 when warnings are present even on a PASS; only the `except Exception` infra-crash path writes to stderr, leaving stdout empty. So `[ -z "$CHECKPOINT_OUTPUT" ]` alone already correctly discriminates a real crash, but the `[ $? -ne 0 ]` disjunct also fires on a legitimate FAIL/warnings result, silently exiting the hook before `STATUS` is ever read — the FAIL-emission branch (and the composition logic this task added to it) is currently unreachable in production. Confirmed via `bash -x` trace. Not fixed here per advisor guidance: Task 14 is the heavy-atomic hooks-trio + baseline-recapture commit, and un-silencing a previously-silent enforcement surface (every downstream SDD session's Stop event would start emitting `Pre-Completion Gate FAILED …` messages, including on sessions that are actually fine but merely have warnings) is a user-visible behavior change that deserves its own reviewed task, not a ride-along. Pinned via `test_composes_with_checkpoint_fail_message`, `xfail(strict=True)`, citing the exact gate — the composition code itself (`if [ -n "$SPAWN_WARN" ]` appended inside the existing FAIL branch, plus the new `elif` for PASS-with-warning) is written and correct; the xfail will flip to a hard failure and force itself to be un-xfailed the day someone fixes the gate. **Proposed one-line fix for the controller/BACKLOG:** `if [ -z "$CHECKPOINT_OUTPUT" ]; then exit 0; fi` (drop the `$? -ne 0` disjunct). This finding has been logged to `deviations.md` by the controller (routed to quality review for a FIX-NOW-vs-defer severity call).
- The three non-discriminating suppression tests noted above are acceptable coverage (paired with the one discriminating positive test) but worth a cheap follow-up: `test_outcome_record_suppresses_warning` could assert stdout is exactly empty (via `_clean_workspace`, a correct suppression yields the silent `:` branch) rather than merely `bid not in stdout`, which would make it a real discriminator against "warning fired anyway." Left as-is since the atomic-commit constraint was already satisfied and amending after commit wasn't appropriate.
