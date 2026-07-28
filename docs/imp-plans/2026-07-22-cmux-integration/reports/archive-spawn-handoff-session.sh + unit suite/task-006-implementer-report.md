---
schema_version: 1
task_id: 6
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Added the generic spawn_claude_workspace() core, the --dry-run short-circuit, and the reserve-before-spawn sequence with exit-code ladder (0 auto / 0 picker-manual / 3 spawn-failed-after-reservation). Moved SPAWN_ID generation to before the compose block and interpolated it into the composed runtime-picker-failure tail (was the literal word `spawn`); regenerated the worked-example comment from a real run. Moved the append-prompt directory creation out of the shell into the Python write path via os.makedirs(exist_ok=True)."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "9 new tests covering dry-run, auto-spawn success, spawn-failure exit 3 with hop consumed, notify-failure exit 0, picker-manual real spawn, append-prompt real write path, spawn-id shape, spawn-id correlation, and reservation timing at new-workspace. Added UUID_RE and the _reach_spawn / _fallback_spawn_id / _spawn_log_records helpers."
tests:
  written: 9
  passing: 9
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q"
  result: PASS
contract_compliance:
  - constraint: "Reservation (hop increment + `intent` log line) happens before `cmux new-workspace`. Post-spawn failures are non-retryable (warn, still exit 0). A spawn failure after reservation keeps the hop consumed and exits 3."
    status: compliant
    detail: "Hop write + intent record precede spawn_claude_workspace(). Proven at the moment that matters by test_reservation_lands_before_cmux_new_workspace_runs (the cmux stub snapshots handoff-spawn.log and .handoff-hops at new-workspace time; kinds == ['intent'], hops == '1'). test_spawn_failure_keeps_hop_exits_3 asserts hop stays 1 + outcome=spawn-failed + exit 3; test_notify_failure_still_exit_0 asserts notify failure warns and still exits 0."
  - constraint: "spec 5.4d log format - spawn id (uuid) in every record type (intent | outcome | runtime-picker-failure)"
    status: compliant
    detail: "One uuid generated before composition, used in all four records. Success outcome + composed fallback tail correlation asserted in test_auto_spawn_success_exit_0 (len(ids)==1 across log records AND _fallback_spawn_id(cmd) == that id) and test_fallback_tail_spawn_id_correlates_with_intent_record; the spawn-failed outcome record's correlation with intent is asserted by the len(ids)==1 check in test_spawn_failure_keeps_hop_exits_3; shape alone by test_fallback_tail_spawn_id_is_a_uuid."
  - constraint: "Exit-code ladder per spec 5.5 (0 auto / 0 picker-manual / 3 spawn-failed-after-reservation / 1 refused)"
    status: compliant
    detail: "Verified by execution on all three Task-6 paths; the exit-1 refusal paths are unchanged from Tasks 1-2 and remain green."
  - constraint: "SUPERPOWERS_CMUX_MAX_HOPS consumed via $MAX_HOPS - do not hardcode 3"
    status: compliant
    detail: "The notify body uses \"Hop $SP_HOP/$MAX_HOPS\"; no literal 3 added."
  - constraint: "Compose-side quoting: every interpolated element is shlex-style re-quoted"
    status: compliant
    detail: "Unchanged from Task 5. $SPAWN_ID is interpolated double-quoted rather than via shq(), matching the existing $SP_HOP treatment - uuid4 and an integer are both within the shell-safe charset by construction. test_composed_command_reparses_with_correct_arity still green."
  - constraint: "CLAUDE_CODE_PICKER_APPEND_PROMPT must be consumed (decode -> rematerialize -> substitute)"
    status: compliant
    detail: "test_append_prompt_file_written_on_real_spawn is the first non-dry-run exercise of the write path: the target file's bytes match the decoded content and the forwarded path points at it."
  - constraint: "Bash support floor is 3.2.57"
    status: compliant
    detail: "`/bin/bash -n` clean; the full 51-test file re-run with /bin (3.2.57) ahead of Homebrew bash on PATH - 51 passed, covering both the success and forced-failure spawn paths. The default pytest run uses Homebrew bash 5.3.9, so this was a required separate check."
  - constraint: "tests/unit/spawn_handoff_helpers.py is READ-ONLY for Task 6"
    status: compliant
    detail: "Untouched - git status shows only the script and test_spawn_handoff.py modified. The reservation-timing test needed no new harness knob; it uses the existing cmux_body and env_extra parameters."
---

**Implementation Summary:**
Completed Module 1 by inserting the reserve-before-spawn sequence into `spawn-handoff-session.sh`: a generic `spawn_claude_workspace()` mechanics core, a `--dry-run` short-circuit that evaluates preconditions and preflight but writes nothing, and the hop-reservation → spawn → outcome ladder with exit codes 0/0/3. Fixed the §5.4d contract violation the plan text would have shipped (literal `spawn` in the composed runtime-picker-failure record) by generating the spawn uuid once before composition and threading it through all four records. Also moved the append-prompt directory creation from the shell into the Python write path.

**Source Files Read:**
- `docs/imp-plans/2026-07-22-cmux-integration/spec.md` — §5.4d spawn sequence (reserve before spawn, log format with spawn id in every record, "workspace ref" in outcomes) and §5.5 exit-code ladder.
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — full script; especially the Task-5 composition block at 300–339 and the append-prompt heredoc at 217–259.
- `tests/unit/spawn_handoff_helpers.py` — `run_spawn`'s PATH/HOME remapping, the default cmux stub (`echo "$@" >> "$CMUX_LOG"`, nothing on stdout), and the `cmux_body`/`env_extra` knobs.
- `tests/unit/test_spawn_handoff.py` — existing `_spawnable` / `_meta` / `_successor_cmd` helpers and the autouse `_hermetic_picker_env` fixture.
- `docs/imp-plans/2026-07-22-cmux-integration/reports/task-000-implementer-report.md` — frozen cmux/picker contract facts.
- Live: `cmux new-workspace --help`, `cmux --help`, and the upstream cmux CLI contract doc — for REQUIRED DECISION #2.

**CLAUDE.md Files Read:**
- `CLAUDE.md` (repo root) — pytest via `.venv/bin/python3`; hook-development gotchas (no `set -u`, no producer-into-`grep -q` under pipefail); the mandate to run all static + integration suites for significant changes. No `CLAUDE.md` exists under `tests/`, `tests/unit/`, or `skills/subagent-driven-development/`.

**Deviations from Plan:**
- **REQUIRED DEVIATION #1 (spawn id).** Generated `SPAWN_ID` once immediately before the compose block and interpolated it (as `\"$SPAWN_ID\"`) into the composed fallback tail in place of the literal `spawn`; deleted the plan's duplicate `SPAWN_ID=` line from the Step-2 spawn-sequence block. The same id now appears in the intent record, the success outcome, the spawn-failed outcome, and the composed runtime-picker-failure tail. Regenerated the worked-example comment (lines ~341–347) from a real dry-run with the same inputs the comment documents, noting the uuid varies per invocation. `--dry-run` computes a uuid but writes nothing — `test_dry_run_spawns_nothing` passes unchanged.
- **REQUIRED DECISION #2 (workspace ref) — ONE deviation covering BOTH sites.** No workspace ref is obtainable, so §5.4d's outcome "workspace ref" is degraded to the constant `(spawned)` **and** the notify body is kept as the plan's `"Hop N/MAX — successor spawned"` (no `in <workspace-ref>` suffix). Evidence: `cmux new-workspace --help` documents no `--json` and no return value, unlike `identify`/`list-workspaces`/`ssh-session-list` which all expose `--json`; the upstream CLI contract doc describes it only as "Create a workspace, optionally with cwd, command, description, layout…" with no documented output. Even a positive result would be unusable here — capturing it needs a command substitution (which would swallow cmux's own diagnostics) or a parse layer (explicitly out of scope), and the test harness stub emits nothing on stdout so no test could verify it. Recorded in a code comment on the outcome line. I deliberately did **not** create-and-close a live workspace to probe: it would not change the outcome.
- **`mkdir -p "$APPEND_TARGET_DIR"` gating (in scope).** Deleted the shell `mkdir` gated on ARGS-presence; added `os.makedirs(os.path.dirname(target), exist_ok=True)` inside the existing `if SPAWN_DRY_RUN != "1":` try, immediately before `open()`. Dry-run stays write-free (`test_append_prompt_substituted_in_forwarded` still green) and failure routes to the existing `sys.exit(4)` → `ARGS_OK=0` → picker-manual.
- **One test beyond the plan's six, plus the two mandated spawn-id tests.** Added `test_reservation_lands_before_cmux_new_workspace_runs` after mutation testing proved the plan's log-order assertion could not detect a real reservation-ordering break (see Mutation Results).
- Nothing from the deferred-work list was touched. `spawn_handoff_helpers.py` untouched. No e2e step added. No `set -u`. The `_hermetic_picker_env` fixture untouched.

**Self-Review Findings:**
- The plan's `kinds.index("intent") < kinds.index("outcome")` assertion is not a reservation-ordering check — it only sees file order. Mutation M2a proved it. Resolved by adding a test that snapshots both reservation artifacts from inside the cmux stub at `new-workspace` time, which is the only moment that proves the hop was consumed before the workspace existed.
- Initial worry that `_fallback_spawn_id` might match a uuid elsewhere in the composed string (the log path, the `/pickup` id). Anchored the regex on the runtime-deferred `$(date …)` substitution so it reads the actual positional field; confirmed it returns `spawn` under mutation M1 rather than silently finding a uuid.
- Confirmed `local rc=$?` immediately after the cmux call behaves correctly on bash 3.2 by executing the forced-failure path (exit 5 → script exit 3), not by inspection.
- Verified the `-k` filter with `--collect-only -q` before deriving the count (8 at the time; 9th added later).
- Verified the committed content passes (51/51 re-run post-commit), and that only my two files were staged.

**Concerns:**
- `(spawned)` is a degraded value for spec §5.4d's outcome "workspace ref", and spec step 4 ("Print the workspace ref and exit 0") is likewise satisfied only by `[spawn-handoff] spawned successor (launch=…)`. If a future cmux adds `--json` to `new-workspace`, this is the one place to revisit. The spec text should probably be amended rather than left as an unmet clause.
- The mutation battery ran under Homebrew bash 5.3.9 (fast path); the bash-3.2 verification was a separate full-file run. Mutation results are about assertion strength, not bash-version behavior, so this split is intentional — but no mutation was individually re-run under 3.2.
- `APPEND_TARGET_DIR` now exists only to build `APPEND_TARGET`. Harmless and still readable; left as-is to avoid churn outside scope.
- The environment's `.py` file-watcher reformatted parts of the appended test code (cosmetic line-wrapping only). Verified the committed content passes 51/51.

**Mutation Results:**
- **M1 — revert the composed fallback tail's spawn-id field to the literal `spawn`** → RED: `test_fallback_tail_spawn_id_is_a_uuid`, `test_fallback_tail_spawn_id_correlates_with_intent_record`, `test_auto_spawn_success_exit_0` (3 failed / 47 passed). The pre-existing `runtime-picker-failure` token assertion stayed green, confirming it was never coverage for this.
- **M6 — regenerate a second uuid inside the spawn sequence** (the exact failure mode of following the plan verbatim) → RED: `test_fallback_tail_spawn_id_correlates_with_intent_record`, `test_auto_spawn_success_exit_0`. The shape-only test `test_fallback_tail_spawn_id_is_a_uuid` **stayed GREEN** — proving the correlation assertion is load-bearing and distinct from "is a uuid."
- **M2a — write the `intent` record AFTER the spawn but BEFORE the outcome** → **SURVIVED** initially: all 50 tests green, because the file order is still `[intent, outcome]`. This is a genuine gap in the plan's ordering assertion. Closed by adding `test_reservation_lands_before_cmux_new_workspace_runs`; M2a re-run then went **RED** on exactly that test (1 failed / 50 passed).
- **M2b — write the `intent` record AFTER the outcome record** → RED: `test_auto_spawn_success_exit_0` (the plan's ordering assertion) and `test_reservation_lands_before_cmux_new_workspace_runs`.
- **M3 — delete the `$HOPS_FILE` reservation write** → RED: `test_spawn_failure_keeps_hop_exits_3`, `test_auto_spawn_success_exit_0`, `test_reservation_lands_before_cmux_new_workspace_runs`.
- **M4 — delete the `--dry-run` short-circuit** → RED: `test_dry_run_spawns_nothing` (plus collateral `test_telemetry_on_and_off`).
- **M5 — remove `os.makedirs` beside the append-prompt write** → RED: `test_append_prompt_file_written_on_real_spawn` (target file absent — the write fails, `exit 4` degrades to picker-manual). This is the first coverage that path has ever had.

**Whole-suite numbers (prose, not the per-task fields above):** `tests/unit/test_spawn_handoff.py` 51 passed (42 pre-existing + 9 new); full `tests/unit/` 604 passed (was 595); `validate-all-skills.py` PASS 159 / FAIL 0 / WARNING 2 (the known advisory soft-threshold warnings); `scripts/lint-shell.sh` exit 0, no findings.

**Commit:** `5c6e4d9`
