---
schema_version: 1
task_id: 5
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Appended launch composition B (40 lines) after the Task-4 diagnostic echo: `preflight_ok()` (5-condition auto-mode gate), `shq()` shlex re-quoter, `build_successor_cmd()`, and the auto/picker-manual `SUCCESSOR_CMD` branch. Leaves `LAUNCH_MODE` + `SUCCESSOR_CMD` set for Task 6; Task-6 placeholder comment untouched."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "Appended the Task-5 section (108 lines): `_successor_cmd()` extractor plus 6 test functions / 7 collected cases covering auto composition, re-parse arity, and the four picker-manual degradation paths."
tests:
  written: 6
  passing: 6
  command: ".venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -v"
  result: PASS
contract_compliance:
  - constraint: "`--handoff-contract` must print the string `1` exactly — compare with string equality after trimming, not `-ge`"
    status: compliant
    detail: "`[ \"$(claude-picker --handoff-contract 2>/dev/null)\" = \"$PICKER_CONTRACT\" ]`. Command substitution strips the trailing newline only (not arbitrary whitespace) — correct for an echo-based probe, and it fails safe: any unexpected probe output degrades to picker-manual, never false-auto. Uses the `PICKER_CONTRACT` variable (script line 35), never a literal `1`. Proven by `test_picker_manual_when_contract_wrong` (stub echoes `2`)."
  - constraint: "Picker version discovery uses `find -type f -perm -u+x` — the auto preflight asserts `-f` AND `-x` (not a lenient `-e`)"
    status: compliant
    detail: "`{ [ -f \"$VERSIONS_DIR/$V\" ] && [ -x \"$VERSIONS_DIR/$V\" ]; } || return 1`. Proven by `test_picker_manual_when_metadata_degraded[9.9.9]` (version declared, file absent)."
  - constraint: "Compose-side quoting: every interpolated element (each decoded arg, version, label) is shlex-style re-quoted"
    status: compliant
    detail: "`shq()` wraps Python `shlex.quote`. Applied to the version, the label, EVERY forwarded element, the `/pickup <id>` prompt, and the `$SPAWN_LOG` path in the fallback chain. Verified by execution, not inspection: a composed command carrying `/tmp/a b.md` and `he said \"hi\"; rm -rf /` re-parsed under /bin/bash 3.2 into 12 argv elements with both hostile values intact as single literals and no injection. `--telemetry`'s value is not shq'd — it is internally derived (`on`/`off` from a strict `= \"1\"` test), and spec §5.4c enumerates exactly the three external elements above."
  - constraint: "`CLAUDE_CODE_PICKER_ARGS` corrupt v1 body ⇒ degrade to picker-manual, never a silent arg-drop"
    status: compliant
    detail: "Preflight requires `ARGS_OK = 1` (set by Task 4). Both the non-v1 prefix and the valid-prefix/garbage-body cases are covered by dedicated tests."
  - constraint: "`CLAUDE_CODE_ENABLE_TELEMETRY==1` ⇒ `--telemetry on`; absent ⇒ off (never blocks auto)"
    status: compliant
    detail: "Preflight does not consult telemetry at all; `$TELEMETRY` (Task 4) flows straight into the composed flags. `--telemetry on` asserted on the composed line."
  - constraint: "Do NOT add `set -u`; bash 3.2 floor"
    status: compliant
    detail: "No `set -u` added (the only match in the file is the line-6 header comment). Full 41-test file re-run with `bash` resolving to /bin/bash 3.2.57 — all pass. `bash -n` clean under both 3.2.57 and 5.3.9."
  - constraint: "Shared constants: use PICKER_CONTRACT; do not re-read/re-default MAX_HOPS or QUOTA_MIN_PCT"
    status: compliant
    detail: "Neither hop nor quota constant is referenced in this block. `$SP_HOP`, `$SPAWN_LOG`, `$VERSIONS_DIR`, `$ARGS_OK`, `$FORWARDED`, `$LABEL`, `$TELEMETRY`, `$PYTHON` are all consumed from earlier tasks' scope; nothing re-derived."
  - constraint: "Reservation ordering / spawn sequence / dry-run short-circuit (Task 6)"
    status: not_applicable
    detail: "Out of scope. This block only composes strings and echoes them; it behaves identically in dry-run and live mode, and adds no dry-run branching."
---

**Implementation Summary:**
Appended launch composition B to `spawn-handoff-session.sh`: a five-condition `preflight_ok()` gate that admits `launch=auto` only when the forwarding metadata is usable, the version binary is an executable regular file, `claude-picker` resolves, and its `--handoff-contract` probe prints exactly `$PICKER_CONTRACT`; otherwise the script degrades to `picker-manual`. The successor `--command` is composed with a `shlex.quote`-backed `shq()` applied to every interpolated element, and the auto branch embeds the residual `|| { <log runtime-picker-failure>; claude-picker '/pickup <id>'; }` fallback chain. `LAUNCH_MODE` and `SUCCESSOR_CMD` are left set for Task 6.

**Source Files Read:**
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — confirmed every variable my block reads is already in scope (`VERSIONS_DIR:200`, `ARGS_OK:203`, `FORWARDED:217`, `LABEL:262`, `TELEMETRY:279`, `SP_HOP:132`, `SPAWN_LOG:62`, `PICKER_CONTRACT:35`, `PYTHON:17`). Confirmed no `set -e` (so the `[ -n "$LABEL" ] && parts+=(…)` guard is safe mid-function) and no `set -u`.
- `tests/unit/test_spawn_handoff.py` — the autouse `_hermetic_picker_env` fixture and `_meta()` helper; confirmed line 281's `forwarded=` echo already emits `--append-system-prompt-file` and `a b.md`, which is the exact test-echo collision carry-forward #2 warned about.
- `tests/unit/spawn_handoff_helpers.py` — `install_version()` already writes an executable regular file (matching the `-f`/`-x` predicate); `run_spawn()` invokes `["bash", …]` from PATH; the default `picker_body` answers `--handoff-contract` with `1`.
- `docs/imp-plans/2026-07-22-cmux-integration/spec.md` §5.4a–d, §5.5, §7 — flag ordering, the preflight condition list, the fallback-chain shape, and the repo-3 test matrix.
- `tests/unit/test_context_gate_tier.py` — the pytest/bash subprocess harness pattern this file already follows.

**CLAUDE.md Files Read:**
- `CLAUDE.md` (repo root; no subdirectory CLAUDE.md exists in either directory I modified — verified by `find`) — "Hook Development Gotchas": no `set -u`, no producer piped into `grep -q` under pipefail (my block does neither), `$PYTHON` for Python calls (used by `shq`), and the `scripts/lint-shell.sh` harness which I ran.

**Deviations from Plan:**
- **No fence defect this time.** Unlike Tasks 3 and 4, I found the Step-2 fence correct as written and adopted it essentially verbatim (I added three explanatory comments). I verified rather than assumed: I extracted a real composed command and *executed* it under /bin/bash 3.2 with a stub picker on both the success and forced-failure paths. Success → 12 argv elements, `/tmp/a b.md`, `he said "hi"; rm -rf /`, and `/pickup b1` each arriving as one literal element. Failure → the log line `2026-07-24T13:49:08Z spawn runtime-picker-failure hop=1` written, then `claude-picker` re-invoked with the single argv `/pickup b1`. The nested quoting, the `{ …; }` group, the deferred `$(date …)`, and the `>>` redirect all round-trip.
- **Compose assertions anchored on the extracted `successor command:` line, not raw `out`** (carry-forward #2). I added a `_successor_cmd(r)` helper that asserts the line exists before slicing, so a TDD-red failure is legible rather than an IndexError. The plan's token list is preserved unchanged; only the haystack is narrowed. Proven necessary and sufficient by the disable test below.
- **Added a 6th test, `test_composed_command_reparses_with_correct_arity`.** This is not gold-plating: spec §7's repo-3 matrix explicitly requires "a space/quote-bearing decoded argv driven through composition → survives intact in the `--command` string (compose-side quoting, §5.4c)". The plan's `assert "a b.md" in cmd` under-covers that — a naive space-join satisfies it. The new test `shlex.split`s the composed picker command and asserts `/tmp/a b.md` is one element and `argv[-1] == "/pickup b1"`, which is the actual proof of a spec-listed item and of carry-forward #1's arity concern.
- **Carry-forward #7 confirmed empirically.** The plan's `-k` filter selects the pre-existing `test_fixtures_shape_matches_contract`; the subset run reports 8 passed, of which 1 is not mine. Reported counts are my own tests only, and `tests.command` is the full-file run.

**Self-Review Findings:**
- *Non-vacuousness (the highest-risk item).* I disabled only the compose emission line — leaving Task 4's `a b.md` emitter running — and confirmed both `test_auto_mode_composes_exact_command` and `test_composed_command_reparses_with_correct_arity` FAIL with "no `successor command:` line emitted", then restored and re-verified green. The assertions cannot be satisfied by Task 4's output.
- *Bash-version blind spot.* The harness resolves `bash` to Homebrew 5.3.9, so the suite alone cannot verify the 3.2 floor. I re-ran the entire 41-test file with `bash` shimmed to /bin/bash 3.2.57 — all pass. The 3.2-sensitive constructs (multiline `local parts=(…)`, `parts+=(…)`, `"${FORWARDED[@]}"` on an empty array) are confirmed safe in practice, not just in theory.
- *Lint.* `shellcheck --severity=warning` reports only two pre-existing SC2034s (`FEATURE_NAME`, `QUOTA_STATUS` — both Task-6 consumers). My block introduces zero new findings.
- *Scope hygiene.* I did not take the three deferred Task-4 cleanups. Scratch files live in the session scratchpad, outside the repo; `git status` showed no stray files and the commit contains exactly the two in-scope files (148 insertions).
- *Regression.* Full `tests/unit/` suite: 594 passed.

**Concerns:**
1. **Task 5/6 coupling — the fallback chain's spawn-id is a placeholder.** The composed runtime-failure line logs the literal word `spawn` in the spawn-id field, whereas spec §5.4d's log format specifies the uuid Task 6 generates. The string is baked at compose time, before that uuid exists, so the runtime fallback can never carry the real id. This is the plan's own fence text and only the `runtime-picker-failure` token is asserted, so it is non-blocking — but Task 6's author should not assume it is wired. Resolving it means either generating the spawn id before composition (moving it into Task 5's territory) or having Task 6 re-compose the fallback tail.
2. **`--telemetry`'s value is not `shq`'d.** It is internally derived (`on`/`off` only) and spec §5.4c enumerates only the version, label, and forwarded args as requiring re-quoting, so this is compliant — flagging it so a future reviewer doesn't read it as an oversight.
3. **`shq` spawns one Python process per forwarded element.** Deliberate and acceptable at this scale (a handful of args on a once-per-handoff path); calling it out rather than leaving it silent. If the forwarded argv ever grows large, batch the quoting into a single Python call.
4. **The `picker-manual` branch's append-path caveat is real but accepted** (per the plan's own precision note): the picker validates `--append-system-prompt-file` readability only under `--non-interactive`, so the interactive fallback does not catch a dead path. Task 4's rematerialization already covers the auto path, and picker-manual is attended.

---

## Controller independent verification (added post-report, before spec review)

The controller re-verified the load-bearing claims rather than accepting them:

- **Commit scope**: `e7d5fe1`, exactly 2 files, 148 insertions (+40 script / +108 tests). No out-of-scope file touched.
- **Full file suite**: 41 passed in 30.04s.
- **Mutation 1 — emission disabled** (`echo "…successor command: …"` → `:`), leaving Task 4's `a b.md` emitter running: `test_auto_mode_composes_exact_command` and `test_composed_command_reparses_with_correct_arity` both FAIL. Confirms the implementer's non-vacuousness claim; the test-echo collision is closed.
- **Mutation 2 — `shq()` replaced with an identity `echo "$1"`**: `test_auto_mode_composes_exact_command` **PASSES**, `test_composed_command_reparses_with_correct_arity` **FAILS**. This independently justifies the added 6th test: the plan's own substring assertion survives a completely broken quoter, so without the arity test the compose-quoting contract constraint would have had zero real coverage.
- Script restored byte-identical after both mutations (`git diff --stat` empty); suite re-verified green.
