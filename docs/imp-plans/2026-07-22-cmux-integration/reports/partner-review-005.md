# Partner Review — Task 5 Dispatch (Launch composition B: auto preflight + compose-side quoting)

**Reviewer:** SDD Controller Partner (general-purpose, haiku)
**Date:** 2026-07-24
**Review tier:** full (task consumes external picker contract + shell re-parse semantics)

## Sources Read

1. Proposed implementer prompt (full file)
2. Plan header (plan.md frontmatter + lines 103-124)
3. Task 5 spec (module-1-spawn-script.md lines 855-967)
4. Deviations register (all 21 rows + Deferred Work)
5. Task 4's implementer report (DONE_WITH_CONCERNS status)
6. Task 4's spec review (PASS)
7. Task 4's quality review (PASS with advisories)

---

**Status:** APPROVED

**Context Completeness:** PASS
- Contract Constraints (prompt lines 180-199): all 11 bullets present
- Shared Constants (lines 201-208): both env vars with correct defaults and reasoning
- Pattern References (lines 214-228): task-level `pytest-bash-stub-harness` + module-level `sdd-bash-hook-style` correctly attributed
- Source Files (lines 155-174): 4 files listed with guidance
- Subdirectory CLAUDE.md reminder (lines 230-235): present

**Context Accuracy:** PASS
- Contract Constraints match plan.md lines 103-114 verbatim (all 11 bullets confirmed)
- Shared Constants match plan header lines 117-118 with correct defaults (3 and 15)
- Pattern References: task frontmatter declares only `pytest-bash-stub-harness`; module-level `sdd-bash-hook-style` correctly labeled as house style applicable to this task
- Task 5 description (prompt lines 12-125) matches module-1-spawn-script.md lines 855-967 verbatim including both test code fences and both Notes
- Code fences spot-checked: test function signatures, bash variable assignments, contract checks all match exactly

**Prior Task Awareness:** PASS
- Task 4 reported DONE_WITH_CONCERNS with 4 concerns; all logged in deviations.md rows 10-13 and 21
- Autouse fixture carry-forward (deviations row 8) explicitly called out at prompt lines 277-282: "Do NOT remove or narrow the autouse `_hermetic_picker_env` fixture"
- CRITICAL TEST-ECHO COLLISION carry-forward (deviations line 34) extensively addressed at prompt lines 264-269 and the entire CRITICAL CARRY-FORWARDS section
- Deferred Task-9 doc obligations correctly noted (bash floor, `set -u` coupling); Task 5 is not asked to fix them

**Escalation Check:** PASS
- Task 4 was DONE_WITH_CONCERNS, not BLOCKED — no unresolved gate to clear
- All four Task-4 concerns (autouse fixture, mkdir side-effect, append-prompt accumulation, report field convention) are logged in deviations.md
- Task 5 is explicitly made aware of the fixture (must not remove) and the test-echo collision (must anchor on discriminating tokens)

**Architectural Alignment:** PASS
- Single source of truth: prompt explicitly forbids literal `1` (line 208) — "use the variable, never a literal `1`"; `PICKER_CONTRACT` at script line 35 is the canonical constant
- No re-derivation allowed: prompt lines 147-149 require verification of pre-existing variables (`VERSIONS_DIR`, `ARGS_OK`, `FORWARDED`, `LABEL`, `TELEMETRY`) by reading the script, not re-deriving
- No new constants created by Task 5 (composition only)
- Consumer updates: N/A (no new types/enums/constants exported)

**Pattern Completeness:** PASS
- Pattern References cover the right aspects: `pytest-bash-stub-harness` for test harness structure (subprocess, PATH stubs, tmp_path, assertions); `sdd-bash-hook-style` for bash conventions (SUPERPOWERS_ROOT self-resolution, `$PYTHON` usage, no `set -u`, here-strings not piped `grep -q`)
- Both references point to real, readable files in the codebase
- CLAUDE.md reminder ensures implementer checks repo conventions

**Non-Vacuous Test Guidance:** PASS

The prompt provides exceptional guidance on the critical test-echo collision:

**(a) Names the trap explicitly** (lines 264-269):
> "Task 4's diagnostic echo at `spawn-handoff-session.sh:281` ALREADY emits `--append-system-prompt-file` and `a b.md` to stderr... that assertion can pass without your compose line ever being exercised."

**(b) Tells implementer which observable to anchor on** (line 267):
> "You must anchor the compose assertions on the specific `[spawn-handoff] successor command:` line (extract that line from the output and assert against it), not against bare `out`."

**(c) Lists discriminating tokens** (line 268):
> "Tokens with no Task-4 emitter and therefore genuinely discriminating: `--non-interactive`, `--pick-version 2.1.218`, `--telemetry on`, `--session-label`, `/pickup b1`."

**(d) Requires proof test is non-vacuous** (lines 268-269):
> "Do not ship a self-satisfying assertion. Prove your test is non-vacuous — e.g. confirm it fails when the compose block is disabled."

**BONUS: `-k` filter contamination** (lines 292-301) — the prompt warns that the Step 3 filter `-k "auto or picker_manual or contract or codec"` will match the pre-existing `test_fixtures_shape_matches_contract` (substring match on "contract"), and explicitly instructs the implementer to ignore that extra pass when deriving `tests.passing`. This directly prevents the report-field error that has blocked a dispatch in this run.

The REPORT FIELD RULE itself reinforces the point:
> "Task 5 adds 5 test functions, one of which is parametrized ×2 — state whichever convention you use (functions or collected cases) consistently across both fields. See carry-forward #7: the plan's `-k` filter also matches one pre-existing test, so its pass count is NOT your `tests.passing`."

---

## Findings

No blocking issues found. The dispatch is complete, contextually accurate, and exceptionally well-briefed on the known traps.

---

## Controller note (added post-review)

The `-k` contamination claim was independently verified by the controller before dispatch, not merely asserted:
`.venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -k "auto or picker_manual or contract or codec" --collect-only -q`
→ `tests/unit/test_spawn_handoff.py::test_fixtures_shape_matches_contract` / `1/34 tests collected (33 deselected)`.
Confirms the filter selects exactly one pre-existing test today, and will report 7 collected cases (6 new + 1 pre-existing) after Task 5 lands.
