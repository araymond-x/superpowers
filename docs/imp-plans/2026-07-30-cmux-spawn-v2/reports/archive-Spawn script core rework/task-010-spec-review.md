# Task 10 Spec Compliance Review — cmux-spawn-v2

**Overall: PASS** (spec-compliant and contract-compliant) — with one ADVISORY finding (undeclared minor departure, non-blocking).

## Full suite re-run (load-bearing evidence)
```
.venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider
796 passed, 1 warning in 259.43s
```
Matches the implementer's claimed 777→796, 0 failed exactly. (The 1 warning is a pre-existing, unrelated `PytestCollectionWarning` about `TestSummary` having an `__init__`.)

## Verified claims (all held up against code, not the report's prose)

- **Handshake/diagnosis separation** (`skills/subagent-driven-development/scripts/spawn-handoff-session.sh`): `diagnose_target()` is called exactly once, only inside the second `if ! wait_for_token` failure branch — after `exit 3` is already the only remaining outcome. No path from `DIAG`/`diagnose_target` reaches the `exit 0` stanza. Confirmed by reading the whole control-flow block, not just the diff.
- **Exactly one re-wait, same `$SPAWN_WAIT_TIMEOUT`**: confirmed in code and by `test_timeout_rewaits_once_same_duration`, which parses *both* logged `wait-for` lines (not `_flag`/`_argv`, which the plan warned would leave the re-wait half vacuous).
- **Fixture provenance**: `trust-dialog.txt`, `banner.txt`, `noise.txt` are byte-exact matches to `cmux-verb-shapes.json`'s `trust_dialog_screen.screen`, `rc_confirmation_screen.rc_screen`, and `read_screen_warm.stdout` respectively (verified independently with a Python byte comparison, not the implementer's own equality tests). `cmux-verb-shapes.json` itself is unmodified (`git diff` empty). `picker-error.txt`/`both-anchors.txt` are labelled `SYNTHETIC FIXTURE (not a capture)` in-file.
- **Anchor pattern counts**: independently re-derived (regex counts against `trust`, `rc_screen`, `rename_screen`, `warm`, whole fixture) and match the report's table exactly, including the `claude code` removal rationale and `esc to interrupt` scoring 0 everywhere.
- **`noise.txt` reclassification**: confirmed correct — it is `read_screen_warm.stdout`, a live capture, contradicting the plan's stale "three synthetic" inventory line; only `picker-error.txt`/`both-anchors.txt` remain genuinely synthetic.
- **Contract constraints**: no live `set -u`/`set -e`/pipefail (`grep -nE` hits are comments only); all four new `diagnose_target` greps use here-strings (`<<< "$screen"`), no pipe into `grep -q`; exit codes stay 0/3/1 across the whole file.
- **Write scope**: `git diff --stat a963186..1a75a16` touches exactly the six declared paths + `deviations.md` + the implementer report; `_handoff_support.py`, `test_handoff_support.py`, and `tests/integration/sdd-e2e-test.sh` all show empty diffs. `CMUX_READ_SCREEN_RC` is scoped only to `spawn_handoff_helpers.py`.
- **Step 4 sub-obligations**: (a) suite re-measured (796, matches); (b) row 18 flipped with a fully reasoned, falsifiable decline; (c) row 271 flipped with the 5-site count re-verified at lines 686/840/867/957/996 in `test_spawn_handoff.py`; (d) row 165 resolved to single ownership (Task 13); (e) commit message is byte-exact.
- **Row 266** (separate controller-flipped row): plan text at `module-3-spawn-script.md:728` and `:821` both read the corrected "not 'both unit files'" wording — verified directly, disposition is accurate.
- **Import assertion**: `test_wait_timeout_default_matches_the_frozen_fixture` already existed (landed by Task 9), not duplicated; confirmed present and column-0 `SPAWN_WAIT_TIMEOUT_DEFAULT=60` at line 54 of the script.
- **Report completeness**: `validate-report.py` → `status: COMPLETE`, all 5 required sections found, exit 0.
- **Concerns section claims** all checked against code: `esc to interrupt` genuinely appears in zero tests/fixtures; `picker-error.txt` is fully synthetic and says so in-file; n=1 banner scoping is stated honestly in the code comment.

## Finding

- **[ADVISORY] [MISUNDERSTANDING]**: `skills/subagent-driven-development/scripts/spawn-handoff-session.sh:847,849` — the `trust-dialog` and `banner` case arms in the timeout tail each insert `"(hop $SP_HOP consumed)"` into the operator-facing `echo` message. The plan's Step 3 fence text (`module-3-spawn-script.md:709-712`) does not include that phrase in those two arms — only the `picker-error` and default (`*`) arms carry it there. A real, undeclared departure from the literal fence (a fourth one, beyond the three declared in "Deviations from Plan"). Very likely intentional and arguably an improvement (makes all four diagnosis arms consistently state the hop was spent; `test_timeout_notifies_and_keeps_hop` relies on "hop 1 consumed" appearing for the `banner` diagnosis) — but it was never declared, and this feature's own history shows a prior task FAILED spec review over exactly this shape of undeclared fence departure. Does not violate any contract constraint, does not change exit-code behavior, is covered by a passing test — not blocking. **Controller resolution: independently verified (matches exactly), logged as a fourth row in `deviations.md`, disposition `Accepted`.**

No BLOCKING findings (no CONTRACT or MISSING violations found). No REPORT_INCOMPLETE — the report has all required sections and `validate-report.py` confirms it.
