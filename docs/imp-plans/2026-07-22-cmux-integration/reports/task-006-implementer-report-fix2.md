---
schema_version: 1
task_id: 6
task_type: implementation
status: DONE
files_changed:
  - path: "tests/unit/test_spawn_handoff.py"
    description: "Added exact-argv + log-record-field tests; extended _spawn_log_records/_outcome_workspace; replaced the colliding manual-instructions guard; consumed the frozen CMUX_* constants"
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Comment only - softened the overclaiming 'Pure mechanics (no SDD policy)' header on the extraction-ready spawn core"
tests:
  written: 4
  passing: 4
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v"
  result: PASS
contract_compliance:
  - constraint: "spec 5.5 - every non-spawn path prints the manual instructions"
    status: compliant
    detail: "test_spawn_failure_keeps_hop_exits_3 now asserts 'Manual resume required' and 'Then STOP the current session' on r.stdout ALONE (text unique to print_manual_instructions). MX2 goes RED."
  - constraint: "spec 5.4d step 2 - cmux new-workspace --name 'SDD resume: <feature>' --cwd <worktree-root> --focus false"
    status: compliant
    detail: "New argv-recording cmux stub (via the existing cmux_body= knob) records one element per line per subcommand; values asserted exactly. --cwd expected value computed with `git rev-parse --show-toplevel` in ctx['wt'], matching how the script derives it (realpath would drift on macOS /var -> /private/var)."
  - constraint: "spec 5.4d step 3 - notify --title 'SDD handoff'"
    status: compliant
    detail: "--title value == 'SDD handoff'; --body asserted to start with 'Hop 1/3 '."
  - constraint: "spec 5.4d Log format - hop on every record; workspace/launch/bundle/quota on outcomes"
    status: compliant
    detail: "_spawn_log_records now returns (kind, id, fields); new test pins intent {hop:1} and outcome hop/workspace/launch/bundle/quota."
  - constraint: "SSOT - consume Task-0 frozen CMUX_NEW_WORKSPACE_FLAGS / CMUX_NOTIFY_FLAGS"
    status: compliant
    detail: "The literal ['--name','--cwd','--command','--focus false'] duplicate is gone; both tests iterate the constants. Constant VALUES unchanged - verified they match the script's emitted argv."
  - constraint: "tests/unit/spawn_handoff_helpers.py read-only"
    status: compliant
    detail: "Untouched; all new stub behavior expressed through cmux_body=."
---

> `[task 6 fix] round 2` — closes the five surviving mutations from
> `task-006-quality-review.md` (PASS with fixes). Commit `ec0df92`.
>
> **Controller correction to the returned frontmatter:** the subagent returned `tests.written` as a
> LIST of four test names, which the strict `ImplementerReport` model rejects (it requires an
> integer). Normalized to `written: 4 / passing: 4` — the honest count of tests added-or-modified
> in this round: **2 new** (`test_new_workspace_and_notify_argv_values_match_spec`,
> `test_spawn_log_record_fields_match_spec_log_format`) and **2 modified**
> (`test_auto_spawn_success_exit_0`, `test_spawn_failure_keeps_hop_exits_3`). No count was
> inflated; the file total (58) is in the prose, not the field.

**Implementation Summary:**
Five surviving mutations closed, all test-side except one comment. (1) The spawn-failure guard now
asserts stdout-only text unique to `print_manual_instructions` instead of `/pickup b1` against
stdout+stderr (which the Task-5 `successor command:` echo already satisfied). (2) New
`_cmux_stub_recording_argv()` records argv one element per line per subcommand
(`$CMUX_LOG.$1.argv`) — the default stub's `echo "$@"` flattens argv and cannot separate a flag
from its value when values contain spaces (`SDD resume: feat`). `_flag_value()` + `_recorded_argv()`
drive exact-value assertions for `--name`, `--cwd`, `--command`, `--focus`, `--title`, `--body`.
(3) `_spawn_log_records` extended to `(kind, spawn_id, fields)` with a `_spawn_log_fields(ctx, kind)`
accessor; `_outcome_workspace` reimplemented on top of it (its 4 call sites unchanged). All four
unpack sites updated. (4) The presence loops in `test_auto_spawn_success_exit_0` now consume
`CMUX_NEW_WORKSPACE_FLAGS` / `CMUX_NOTIFY_FLAGS`.

**Source Files Read:**
- `docs/imp-plans/2026-07-22-cmux-integration/reports/task-006-quality-review.md`
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (`:1-66`, `:300-446`)
- `tests/unit/test_spawn_handoff.py`
- `tests/unit/spawn_handoff_helpers.py` (read-only)
- `docs/imp-plans/2026-07-22-cmux-integration/spec.md` §5.4d / §5.5

**CLAUDE.md Files Read:**
- repo root `CLAUDE.md` — bash conventions, "Worktree Sessions", no `set -u`.

**Deviations from Plan:**
FIX 2/4 landed as two new dedicated tests rather than expanding `test_auto_spawn_success_exit_0` in
place — that test uses the default stub, and the value assertions need the argv-recording stub.
`test_auto_spawn_success_exit_0` keeps its flag-presence role, now via the constants.

**Self-Review Findings:**
- `_worktree_root()` runs `git rev-parse --show-toplevel` rather than `realpath(ctx['wt'])` — git
  canonicalizes `/var`→`/private/var` on macOS, so a realpath expectation could false-red.
- `_flag_value(nw, "--command") == _successor_cmd(r)` is exact-string equality on a non-targeted
  field; it passes and adds real `--command`-value coverage, but if a future compose change makes
  it brittle, downgrade to containment rather than debug it.

**Concerns:**
None blocking. Nothing from the deferred sweep list was touched; no `trap` added; helpers file
untouched; no `set -u`.

**Mutation Results:**
(each applied to a pristine script, target test run, then reverted; final `orig == current` check
`True`; `git diff` of the script = the comment hunk only)

| ID | Mutation | Target test | Observed |
|---|---|---|---|
| MX1 | `--cwd "$cwd"` → `--cwd /tmp` | `test_new_workspace_and_notify_argv_values_match_spec` | **RED** |
| MX2 | delete `print_manual_instructions` on the spawn-failure branch | `test_spawn_failure_keeps_hop_exits_3` | **RED** |
| MX3 | `--name "$ws_name"` → `--name BOGUS` | `test_new_workspace_and_notify_argv_values_match_spec` | **RED** |
| MX4 | intent record `"$SP_HOP"` → `"Z1"` | `test_spawn_log_record_fields_match_spec_log_format` | **RED** |
| MX5 | notify `--title "SDD handoff"` → `"BOGUS TITLE"` | `test_new_workspace_and_notify_argv_values_match_spec` | **RED** |

All five previously SURVIVED a fully green 56-test suite.

**Whole-suite numbers (prose only):** `test_spawn_handoff.py` **58 passed** (was 56); `tests/unit/`
**611 passed**, 1 warning; skill regression **PASS 159 / FAIL 0 / WARNING 2** (the 2 known
advisories); spawn file re-run green under a `/bin/bash` 3.2.57 PATH shim (58 passed).

---

## Controller independent verification

- Commit `ec0df92` scope is exactly the 2 in-scope files. The **script diff is comment-only**
  (`@@ -356`, 6 lines) — and the replacement comment is accurate: it names the notify `--title` as
  the single caller-specific string an extractor must parameterize.
- SSOT closed: `CMUX_NEW_WORKSPACE_FLAGS` / `CMUX_NOTIFY_FLAGS` are now consumed at three sites
  (`:656`, `:659`, `:694`, `:702`); the hardcoded literal list is gone. Constant values unchanged.
- **Controller independently re-ran MX2** (the highest-consequence gap — the dead-ended
  post-reservation failure path): replacing the `print_manual_instructions` call at `:447` with a
  no-op turns `test_spawn_failure_keeps_hop_exits_3` **RED** (1 failed). It previously survived
  with 56 green. Gap confirmed closed.
- Script restored byte-clean after mutation; `test_spawn_handoff.py` **58 passed**.
