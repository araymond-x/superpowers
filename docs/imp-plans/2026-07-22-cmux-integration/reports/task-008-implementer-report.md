---
schema_version: 1
task_id: 8
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Both reservation writes (.handoff-hops, intent record) now checked; failure warns with branch-accurate wording, prints manual instructions, exits 3 (existing ladder). Decoder's final write wrapped in try (lone-surrogate degrade without a raw traceback). max(0, …) on the label slice. Comment recording the deliberate keep of the :299 picker-PATH check."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "9 new mutation-proven tests (reservation legs A/B, mktemp-failure spawn + rc propagation, version-as-directory with positive control, two fractional-threshold legs, lone-surrogate, label-slice); notify-body assertion added to test_spawn_failure_keeps_hop_exits_3; fixture moved out to conftest.py."
  - path: "tests/unit/conftest.py"
    description: "Received PICKER_ENV_VARS + the autouse _hermetic_picker_env fixture (single definition, explanatory comment carried); preserved the existing MODELS_DIR sys.path insert; added the required import pytest."
  - path: "docs/imp-plans/2026-07-22-cmux-integration/module-1-spawn-script.md"
    description: "Task 3 Step 2 snippet replaced with the shipped implementation from 7131698; Task 4 bash caveat corrected 4.x->3.2; Task 6 Step 2 spawn-id generation removed from the spawn-sequence snippet with a §5.4d note. No checkbox state changed."
tests:
  written: 9
  passing: 9
  command: ".venv/bin/python3 -m pytest tests/unit/ -q"
  result: PASS
contract_compliance:
  - constraint: "Exit-code ladder frozen at 0 / 3 / 1; failed reservation write routes to existing exit 3, manual instructions printed first"
    status: compliant
    detail: "Both new branches call print_manual_instructions then exit 3. No new exit code. grep confirms the script's only exits remain 0/1/3."
  - constraint: "Do NOT add set -u (bash 3.2 floor)"
    status: compliant
    detail: "No set -u/-e/pipefail added. Verified /bin/bash -n (3.2.57) OK."
  - constraint: "Do not change sdd-pre-dispatch-hook.sh or tests/ARaymond-hook-baseline/baseline.txt"
    status: compliant
    detail: "git diff --name-only on both paths is EMPTY after commit."
  - constraint: "Shared constants referenced, not re-literalled"
    status: compliant
    detail: "No new literals. Tests drive SUPERPOWERS_CMUX_QUOTA_MIN_PCT via env; QUOTA_MIN_PCT_DEFAULT untouched."
  - constraint: "Picker version predicate asserts -f AND -x"
    status: compliant
    detail: "Unchanged in the script; the -f half is now pinned by the directory test plus a positive control."
  - constraint: "spawn_handoff_helpers.py is read-only for this task"
    status: compliant
    detail: "Untouched. The 13.0% pace stub is derived in the test file as PACE_OK.replace('63.0','13.0')."
---

**Implementation Summary:** Hardened the reservation writes so a failed `.handoff-hops` or `intent`
write can no longer spawn a workspace against a reservation that never landed (the script runs
without `set -e`, so the redirection failure was silent). Added 9 mutation-proven tests closing the
residual gaps — including the `-f` half of the version predicate and the fractional half of the
`QUOTA_MIN_PCT` regex, both previously survivable on a green 63-test suite — moved the hermetic
picker-env fixture to `conftest.py`, and corrected the three owed plan-doc defects.

**Source Files Read:** `spawn-handoff-session.sh` (no `set -e`/pipefail; `print_manual_instructions`
reused); `spawn_handoff_helpers.py` (`executable=`/`picker_stub=` knobs, PACE_* constants);
`test_spawn_handoff.py` (harness idiom, `_notify_line`/`_successor_cmd`/`_warning_lines` extractors);
`conftest.py` (pre-existing `MODELS_DIR` insert — merged, not replaced); `spec.md` §5.4c/§5.4d/§5.5
(exit ladder, log format, PATH-resolution predicate); `module-1-spawn-script.md` Tasks 3/4/6;
`git show 7131698`.

**CLAUDE.md Files Read:** repo root — Hook Development Gotchas (no `set -u`, no
producer-into-`grep -q` under pipefail, `$PYTHON` for PyYAML/Pydantic), testing layers, hook-baseline
re-capture rule. No subdirectory CLAUDE.md exists under `skills/subagent-driven-development/` or
`tests/unit/` (checked).

**Mutation Proofs** — all 9 RED; script restored from a pre-mutation copy each time, final restore
verified byte-identical with `diff -q`:

| # | Test | Mutation | Observed RED |
|---|---|---|---|
| M1 | `test_hops_write_failure_exits_3_without_spawning` | hops-write `if !` reverted to bare `printf` | `no hops-write warning` — the *intent* branch caught it instead |
| M2 | `test_intent_write_failure_exits_3_without_spawning` | intent-write `if !` reverted to bare `printf` | `assert 0 == 3` (spawn proceeded) |
| M3 | `test_spawn_failure_keeps_hop_exits_3` | deleted failure-branch `cmux notify` | `cmux stub recorded no notify call` |
| M4 | `test_mktemp_failure_still_spawns_uncaptured` | deleted the uncaptured `else` branch | `assert 'new-workspace' in ''` |
| M5 | `test_mktemp_failure_preserves_spawn_failure_rc` | `rc=$?` → `rc=0` in that branch | `assert 0 == 3` |
| M6 | `test_version_installed_as_directory_degrades_to_picker_manual` | `-f && -x` → bare `-x` | `launch=auto` for a directory |
| M7 | both fractional tests | regex → `^[0-9]+$` | leg 1: warning appeared; leg 2 (13.0%): `assert 3 == 0` — behavioral flip |
| M8 | `test_lone_surrogate_arg_degrades_without_traceback` | unwrapped the `try` | `'Traceback' is contained here` |
| M9 | `test_label_slice_does_not_leak_base_...` | removed `max(0, …)` | label was `Proje-Session-1000…` — the leaked fragment |

**MX-A positive control (leg 2 of the same test):** identical fixture with a real executable regular
file at `versions/2.1.218` reaches `launch=auto`, proving the picker-manual leg is evidence about
`-f` and not an unrelated preflight failure. **MX-B 13.0 variant:** added as advised; the plan's 63.0
absence assertion is kept as the other leg.

**I caught one hollow assertion in my own work:** my first Step-1 fixture (`chmod 0555`) fails *both*
writes, so deleting the hops check left the test green (the intent check caught it). Fixed by
anchoring each leg on its branch-specific wording, and by giving leg B an isolating fixture —
`handoff-spawn.log` pre-created as an empty **directory** (`>>` is EISDIR, hops write succeeds first;
a read-only *file* would trip the clean-tree precondition and exit 1 for the wrong reason). Leg B
additionally asserts `.handoff-hops == "1"`, which is what discriminates it from leg A.

**Step 4c decision: KEEP** the `command -v claude-picker` check at `:299`. Spec §5.4c enumerates PATH
resolution as its own preflight predicate; removing it would make the script diverge from a
spec-enumerated condition to save one line, and the script freezes after this task. A comment now
records that the redundancy is intentional.

**Step 4 third sub-item:** confirmed the `mkdir` gating fix already landed in Task 6 —
`os.makedirs(os.path.dirname(target), exist_ok=True)` sits inside the write's `try`, so a failure
routes to the same `ARGS_OK=0` degrade. **Nothing further needed; no test invented.**

**Deviations from Plan:**
1. **4th file in the commit (`tests/unit/conftest.py`).** Step 4d mandates the edit but the plan's
   Files list and `git add` line both omit it — a plan defect. Left uncommitted, the fixture would
   exist in *neither* file and hermeticity would silently vanish. Committing it is entailed, not
   scope creep; noted in the commit body.
2. **MX-B 13.0 behavioral test added** alongside the plan's absence-only assertion (both legs kept),
   because at 63.0% both the correct and tightened regex yield `quota=ok`.
3. **Task 3 snippet restored from `7131698` verbatim as instructed;** the `QUOTA_TIMEOUT` validation
   landed later in `926ab60` and is already recorded in that task's Completed line, so the snippet
   intentionally lacks it.
4. **No `cmux notify` on the new exit-3 branches.** The plan prescribes exactly "warn, print manual
   instructions, exit 3"; adding a notify would be unrequested scope.
5. **Decoder exit code for the surrogate path is `5`, not `3`.** 3 and 4 are documented as specific
   diagnostics; the shell only tests `!= 0`, so behavior is identical.
6. Ran `validate-all-skills.py` (not in Step 6) because repo CLAUDE.md mandates it after any
   `skills/` edit: **PASS 159 / FAIL 0 / WARNING 2** (known advisory).

**Self-Review Findings:** (a) the leg-A hollow assertion above — fixed; (b) `git checkout --`
destroyed my *uncommitted* script edits during M2 restore — switched to copy-restore and re-verified;
(c) confirmed exactly one `PICKER_ENV_VARS` definition, with `conftest.py` importing no test module;
(d) `grep -rln` over `tests/unit/` shows only `conftest.py` and `test_spawn_handoff.py` reference the
picker vars, so the now-global fixture is provably inert for the other 553 tests, not merely
non-erroring; (e) plan validator on the edited doc: **0 blockers**, warnings byte-identical to the
pre-edit version; no checkbox state changed.

**Concerns:**
1. **`mkdir -p "$REPORTS_DIR"` immediately above the reservation is still unchecked** — same
   robustness class as Step 1, deliberately not expanded. Reported, not fixed.
2. **`DECODE_TMP="$(mktemp)"` is unchecked** — an empty path now degrades silently to `ARGS_OK=0`;
   previously it produced a traceback that pointed at the real cause. Correct behavior, slightly
   weaker diagnostic.
3. **The surrogate test's `launch=picker-manual` assertion is satisfied by any decode failure**, so
   `"Traceback" not in stderr` is its sole discriminator (exactly what M8 proved). The cleanup is
   diagnostic-only — no behavior change.
4. **`max(0, …)` does not bring a pathological label under 255** when the suffix alone exceeds it; it
   removes a negative-index footgun and makes truncation deterministic. Claiming it enforces the
   ceiling would be false.
5. Both reservation tests depend on `chmod`/EISDIR semantics — they would not discriminate if the
   suite ever ran as root.
