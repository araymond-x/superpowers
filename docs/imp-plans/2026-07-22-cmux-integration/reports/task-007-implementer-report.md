---
schema_version: 1
task_id: 7
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "tests/unit/spawn_handoff_helpers.py"
    description: "Added two harness knobs, both defaulting to today's behavior so no existing test changed: install_version(..., executable=True) (installs 0o644 when False, the only way to exercise the -x half of the preflight predicate) and run_spawn(..., picker_stub=True) (when False, skips the picker stub AND filters PATH entries providing claude-picker via new _path_without helper — necessary because this machine has a real picker at ~/.local/bin and run_spawn copies os.environ)."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "New 'Task 7 (Sweep A)' section: 5 mutation-proven regression tests covering the four zero-protection behaviors plus the two owed env-validation regressions. Adds _only_failing_predicate_is (fixture ensuring picker-manual is not over-determined) and _warning_lines (stderr-only, prefix-anchored WARNING extractor)."
tests:
  written: 5
  passing: 5
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q && .venv/bin/python3 -m pytest tests/unit/ -q"
  result: PASS
contract_compliance:
  - constraint: "Coverage-only. Do NOT modify spawn-handoff-session.sh in this task — it is READ-ONLY here."
    status: compliant
    detail: "Mutations applied only transiently for proof, each restored with `git checkout --` (never `git stash`, which would have swept the controller's modified reports/.dispatch-log). `git diff --name-only` and `git status --porcelain` on the script path re-verified EMPTY after every mutation and again before commit. Controller independently confirmed the script is absent from `git diff cfe8c27..HEAD`."
  - constraint: "Mutation proof is required, not optional — record test name, mutation, observed failure."
    status: compliant
    detail: "Seven mutations across five tests (two tests got a second, narrower mutation isolating the behavioral half from the WARNING half). Every RED observed and recorded; one predicted-GREEN was RUN rather than inferred."
  - constraint: "Anchor on a distinctive line — combined stdout+stderr assertions are contaminated by this script's chatty stderr."
    status: compliant
    detail: "The telemetry test anchors on _successor_cmd(r), not stdout+stderr — the Task-4 `telemetry=off` diagnostic echo would otherwise satisfy it with the composition never running (proven: M3 leaves that echo correct and the new test still goes RED). The env-validation tests use _warning_lines, which reads r.stderr ONLY and prefix-anchors on `WARNING: invalid SUPERPOWERS_CMUX_QUOTA_`."
  - constraint: "New helper knobs must default to today's behavior so no existing test changes."
    status: compliant
    detail: "Landed the knobs alone and ran the file at 58 passed BEFORE adding any new test, isolating 'knob broke something' from 'new test fails'. Zero existing tests edited."
  - constraint: "Do NOT remove or narrow the autouse _hermetic_picker_env fixture."
    status: compliant
    detail: "Untouched. All five new tests rely on it; the two preflight tests build their env through the existing _meta() helper on top of it."
  - constraint: "Consume the frozen in-repo contract constants; do not duplicate them (SSOT)."
    status: compliant
    detail: "No new test needed CMUX_NEW_WORKSPACE_FLAGS / CMUX_NOTIFY_FLAGS / PICKER_CONTRACT_VERSION / PICKER_EXPORTS, so none were referenced or restated. SUPERPOWERS_CMUX_QUOTA_MIN_PCT's default 15 is NOT hardcoded in the new tests (see Concerns 2 for what that costs)."
  - constraint: "Verify any -k filter with --collect-only -q before deriving counts from it."
    status: compliant
    detail: "All five filters collect-only verified before use; each confirmed to include both the new test and the pre-existing tests it must NOT redden."
  - constraint: "Do not change sdd-pre-dispatch-hook.sh or the hook baseline."
    status: not_applicable
    detail: "No hook touched; commit contains exactly two test files."
---

**Implementation Summary:**
Added two default-preserving knobs to the spawn-handoff harness and five mutation-proven tests pinning behaviors that had zero protection: the `command -v claude-picker` preflight guard, the `-x` half of the version predicate, the `--telemetry off` value on the composed successor command, and the two env-validation regex blocks (`QUOTA_MIN_PCT`, `QUOTA_TIMEOUT`). The script was not modified. Suite: 58 → 63 in the file, 611 → 616 across `tests/unit/`. Committed as `8ea8509`.

**Mutation Proofs:**

| # | Test | Mutation applied | Observed |
|---|---|---|---|
| M1 | `test_picker_absent_degrades_to_picker_manual` | Wrapped the contract probe in `if command -v claude-picker …; then … fi` and dropped the standalone guard — preflight no longer requires the picker at all | **RED**: `assert 'launch=picker-manual' in …` — script emitted `launch=auto`. `test_picker_manual_when_contract_wrong` stayed GREEN, so this is coverage no existing test provides |
| M1b | same test | Deleted `:299` (`command -v claude-picker … \|\| return 1`) **alone** | **GREEN — run, not inferred.** See Concerns 1 |
| M2 | `test_non_executable_version_degrades_to_picker_manual` | Reduced `{ [ -f … ] && [ -x … ]; }` to bare `[ -f … ] \|\| return 1` | **RED**: emitted `launch=auto`. Both `test_picker_manual_when_metadata_degraded` params stayed GREEN (isolating: they cover only the `-f` half) |
| M3 | `test_telemetry_off_value_on_composed_command` | Hardcoded `"--telemetry" "on"` in `build_successor_cmd` (leaves the `TELEMETRY` resolution and its stderr echo correct) | **RED**: `assert '--telemetry off' in "claude-picker --non-interactive --pick-version 2.1.218 --telemetry on …"`. `test_telemetry_on_and_off` stayed GREEN — it asserts the diagnostic echo, which this mutation does not touch |
| M4a | `test_invalid_quota_min_pct_warns_and_reverts_to_default` | Deleted the entire MIN_PCT validation block | **RED**: `assert []` (no WARNING on stderr) |
| M4b | same test | Kept the WARNING echo, deleted **only** `QUOTA_MIN_PCT="$QUOTA_MIN_PCT_DEFAULT"` | **RED on the behavioral half**: `assert 0 == 3` — with `abc` reaching awk as an uninitialized variable (`0`), the 8.0% reading no longer classifies `low`, the refusal gate goes inert and the script proceeds to spawn |
| M5a | `test_invalid_quota_timeout_warns_and_quota_gate_stays_live` | Deleted the entire TIMEOUT validation block | **RED**: `assert []` (no WARNING on stderr) |
| M5b | same test | Kept the WARNING echo, deleted **only** `QUOTA_TIMEOUT="$QUOTA_TIMEOUT_DEFAULT"` | **RED on the behavioral half**: `assert 0 == 3` — `sleep abc` fails instantly (verified: rc 1, "invalid time interval"), the watchdog kills the tool at once, every reading becomes `unchecked` |

`test_quota_tool_timeout_proceeds`, `test_quota_threshold_reads_env_not_hardcoded_default` and `test_quota_threshold_boundary_is_strict_less_than` stayed GREEN under M4/M5 — the new tests catch what they cannot.

Two cheap experiments run rather than reasoned about (per hard constraint 3): `sleep abc` fails / `sleep 60s` **succeeds** on this box (so `abc`, not `60s`, is the valid invalid-value fixture); and the installed `claude-picker --handoff-contract` prints exactly `1`, which is what makes the picker-absent test's unmutated PASS proof of genuine absence rather than a leaked-but-wrong-contract picker.

**CONTROLLER INDEPENDENT VERIFICATION (not the implementer's claim):**
The controller re-ran M3 from scratch — `sed`-patched line 312 to `"--telemetry" "on"`, ran `-k telemetry`, and observed **1 failed, 1 passed**: `test_telemetry_off_value_on_composed_command` RED with the composed command showing `--telemetry on`, and the pre-existing `test_telemetry_on_and_off` GREEN. This confirms both that the new test discriminates and that the pre-existing test structurally cannot catch this class. Script restored and `git diff --name-only` re-verified empty.

**Source Files Read:**
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — preflight predicate order (`:294-302`); the layered picker checks; MIN_PCT (`:27`, before any git/bundle work) and TIMEOUT (`:154`) guards both revert-not-exit because the quota gate's contract is fail-open; `check_quota`'s watchdog captures through a temp file, and the watcher subshell is `>/dev/null 2>&1` so an orphaned `sleep` cannot hold pipes open.
- `tests/unit/spawn_handoff_helpers.py` — `install_version` always chmod 0o755; `run_spawn` copies `os.environ` and prepends the stub dir to the live PATH.
- `tests/unit/test_spawn_handoff.py` — `_successor_cmd` / `_notify_line` / `_meta` / `_spawnable` idioms and the Task-5 comment documenting the test-echo collision class.
- `docs/imp-plans/2026-07-22-cmux-integration/spec.md` §7 — "metadata absent / version binary missing / picker missing / contract probe failing → `launch=picker-manual`", the contract the two preflight tests encode.

**CLAUDE.md Files Read:**
- Repo root `CLAUDE.md` — pytest must run as `.venv/bin/python3 -m pytest` (system python3 lacks pydantic/PyYAML); test-layer inventory. No `CLAUDE.md` exists anywhere under `tests/` (checked with `find`).

**Deviations from Plan:**
- One, in the mutation used for Step 2 rather than in the delivered test. The plan says of the `command -v claude-picker` guard: "deleting the check is currently undetected." True, but the stronger fact is that deleting it is **undetectable by any black-box test** — so the new test could not be proven with that mutation. An isolating mutation was used instead (remove the picker requirement from preflight while keeping the contract-wrong path intact), and the plan's single-line deletion was separately run to record its GREEN. Test and step scope are otherwise exactly as specified.

**Self-Review Findings:**
1. Initially planned to prove Step 2 with a two-line delete (guard + probe). That also reddens `test_picker_manual_when_contract_wrong`, so it would have proven nothing new — replaced with the isolating mutation above.
2. Initially planned only whole-block mutations for the env-validation tests; those kill the WARNING and the revert together, so both assertions redden at once and neither is shown load-bearing. Added the narrower reassignment-only mutations (M4b/M5b) that isolate the behavioral half.
3. Considered parsing the default out of the WARNING text and re-running at default+1 to pin the threshold tightly. Dropped it: same discriminating power for double the runtime, and it would have put the script's em dash into a regex.
4. One new line ran 90 chars against the file's ~88-char style; reformatted and re-ran the file (63 passed). Verified the only three >88-char lines in both files are pre-existing.
5. The full-suite 616 predated that reformat, so confirmed `grep -rl spawn_handoff_helpers tests/` returns only `test_spawn_handoff.py` — 616 holds for the committed tree.
6. No scratch or temp files created; scratchpad empty and `git status` shows only the controller's own pre-existing report artifacts.

**Concerns:**
1. **`:299` is redundant with `:301` and unobservable by any black-box test** (M1b, verified by running it). With the picker absent, `$(claude-picker --handoff-contract 2>/dev/null)` applies the redirect before the failed execve, so "command not found" is swallowed, the substitution is empty, `"" != "1"`, and preflight returns 1 — the identical classification the deleted guard would have produced. The new test pins the spec-required composite behavior (picker missing → picker-manual), which is the real deliverable, but no test can pin that individual line. Flagged as a **Sweep B / simplification candidate deliberately not acted on** — the script is read-only for Task 7, and it is a judgment call whether an explicit-but-redundant guard is worth keeping.
2. **The MIN_PCT test pins "reverted to a numeric default above 8.0", not "15".** It cannot distinguish 15 from 50. That is the deliberate trade required by the shared-constants constraint (hardcoding 15 would restate the constant), and M4b proves the reassignment is exactly what the test catches — but nothing in the suite pins the literal default value, before or after this task.
3. **`_path_without` portability edge:** a PATH entry holding both `claude-picker` and something the script needs (e.g. `git`) would be dropped along with the picker. The failure mode is loud and immediate (`REFUSED: not in a git repository`), never a silent pass. No change wanted; noted for whoever runs this suite on a different machine.
