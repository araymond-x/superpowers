# Task 7 — Spec Compliance Review (Sweep A)

**Reviewer:** general-purpose spec compliance auditor
**Scope:** `git diff 518875c..8ea8509` — `tests/unit/spawn_handoff_helpers.py`, `tests/unit/test_spawn_handoff.py`

## Verdict: **PASS** — spec compliant AND contract compliant

All seven steps implemented and independently verified. The reviewer re-ran **five** mutations itself (four beyond the controller's M3); every claim it tested held.

## Mutations the reviewer re-ran

All applied via in-place edit, restored with `git checkout --` (never `git stash`).

| # | Mutation | Observed |
|---|---|---|
| **M2** | `:298` reduced to bare `[ -f "$VERSIONS_DIR/…" ] \|\| return 1` | **RED** — `test_non_executable_version_degrades_to_picker_manual` failed on `launch=auto`; both pre-existing `metadata_degraded` params stayed GREEN (1 failed, 2 passed) |
| **M4b** | deleted **only** `:29` `QUOTA_MIN_PCT="$QUOTA_MIN_PCT_DEFAULT"`, WARNING echo kept | **RED** — `assert 0 == 3` |
| **M5b** | deleted **only** `:156` `QUOTA_TIMEOUT="$QUOTA_TIMEOUT_DEFAULT"`, WARNING echo kept | **RED** — `assert 0 == 3`; M4b+M5b together: 2 failed, 10 pre-existing quota tests passed |
| **M1b** | deleted `:299` (`command -v claude-picker … \|\| return 1`) alone | **GREEN** (8 passed) — the plan's prescribed mutation is genuinely inert |
| **M1** | replaced `:299-:301` with the contract probe wrapped in `if command -v claude-picker; then … fi` | **RED** — `test_picker_absent_degrades_to_picker_manual` failed on `launch=auto`; `test_picker_manual_when_contract_wrong` GREEN |

**Restore confirmed** after every mutation and finally: `git diff --name-only`, `git status --porcelain`, and `git diff HEAD --stat` on the script all empty; lines 298-301 visually match HEAD. Controller re-verified independently after the review returned.

## Verdict on the claimed plan defect (BLOCKING if wrong)

**The diagnosis is correct.** M1b came out GREEN under the reviewer's own run. Reading `:294-302`: with the picker absent, `$(claude-picker --handoff-contract 2>/dev/null)` swallows the shell's "command not found" via the redirection inside the substitution, yields empty, `"" != "1"`, and `:301` returns 1 — the same classification `:299` would have produced. `:299` is redundant with `:301` and unobservable by any black-box test.

Step 2 is nevertheless **satisfied**: M1 proves the delivered test discriminates the spec contract (spec.md:196, picker missing → picker-manual), which is the real deliverable. Reviewer's assessment: "Running the prescribed mutation and recording its GREEN rather than inferring it, then substituting an isolating one and disclosing the swap, is exemplary practice."

## Test-echo collision audit (the highest-risk class) — CLEAN

Every asserted string grepped against the script:
- `launch=picker-manual` / `launch=auto` — produced **only** by `$LAUNCH_MODE` interpolation at `:354` and `:413`. No independent literal echo anywhere. The combined-stream assertion is acceptable *because the only producer is the variable under test* — and M1/M2 empirically proved it reddens.
- `quota=low` — only from `quota=$QCLASS` at `:193`/`:196`, both classifier-driven.
- `--telemetry off` — anchored on `_successor_cmd(r)`, which prefix-filters on `MARKER = "[spawn-handoff] successor command: "` (`:355`). Correctly dodges the Task-4 `telemetry=off` diagnostic echo at `:285`.
- `_warning_lines` reads `r.stderr` only and prefix-anchors on `WARNING: invalid SUPERPOWERS_CMUX_QUOTA_`. No stdout contamination path.

**The Task-5/Task-6 recurrence did NOT happen here.**

## Contract constraints — all verified

- **Script read-only:** `git diff cfe8c27..HEAD --name-only` lists only the controller's own three docs files from `518875c`. Commit `518875c..8ea8509` is **exactly** the two test files.
- **Hook + baseline:** absent from `cfe8c27..HEAD`.
- **Exit-code ladder:** untouched; new tests assert existing codes 0 and 3 only.
- **Knobs default to today's behavior:** `install_version(executable=True)` → `0o755`; `run_spawn(picker_stub=True)` → stub installed, PATH unfiltered. Test-file diff is a pure append (`@@ -970,3 +970,130 @@`); **zero existing tests edited**.
- **SSOT:** no frozen constant restated. The `"claude-picker '/pickup b1'"` expected-value literal at `:1003`/`:1017` mirrors the pre-existing idiom at `:476` — file-consistent test style, not a constants violation.
- **MIN_PCT / MAX_HOPS not hardcoded:** confirmed. The reviewer judged the "numeric default above 8.0" trade **correct, not hollowed out** — parsing the default out of the WARNING text would be tautological (change `QUOTA_MIN_PCT_DEFAULT` and the warning changes with it), so no black-box test can pin the literal 15 without hardcoding it. The plan's "default-15 behavior" wording and the shared-constants constraint genuinely conflict; the implementer chose the constraint and disclosed the cost.
- **`_hermetic_picker_env`:** untouched.

## Counts

`tests/unit/test_spawn_handoff.py` → **63 passed** (58 + 5). `tests/unit/` → **616 passed**, 1 warning. Both match the report.

## Findings

**`[ADVISORY] [MISUNDERSTANDING]` `tests/unit/test_spawn_handoff.py:981`** — `_only_failing_predicate_is` is named broader than it can guarantee. For the `-x` test it is exact (M2 → `launch=auto` proves every other predicate held). For the picker-absent test, picker absence *necessarily* fails two predicates (`:299` and `:301`), so "only one failing predicate" is inexpressible there. Same redundancy the implementer documented in Concerns 1 — a naming nit, not a defect; the fixture still does its real job of preventing over-determination by *unrelated* predicates.

No blocking findings.

## Report completeness

All required sections present. Status / Files Changed / Tests / Contract Compliance in YAML frontmatter (correct shape for this repo's `validate-report.py`); Implementation Summary, Mutation Proofs, Source Files Read, CLAUDE.md Files Read, Deviations, Self-Review Findings, Concerns in the body. Nothing suspiciously empty — Concerns and Self-Review are substantive and self-critical. No `CLAUDE.md` exists under `tests/`, so the root-only read is complete. **Not** REPORT_INCOMPLETE.
