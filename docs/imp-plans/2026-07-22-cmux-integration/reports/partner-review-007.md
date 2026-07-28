# Partner Review — Task 7 dispatch (Sweep A)

**Dispatched:** controller partner (general-purpose, haiku), 2026-07-24
**Subject:** proposed implementer prompt for Task 7 — Sweep A, zero-protection regression coverage + harness knobs

**Status:** APPROVED

## Check Results

| Check | Result | Notes |
|-------|--------|-------|
| Context Completeness | PASS | Contract Constraints, Shared Constants, Pattern References, Source Files, subdirectory-CLAUDE.md reminder all present; pytest invocation detail (`.venv/bin/python3`) included. |
| Context Accuracy | PASS | Contract Constraints byte-identical to the module-2 header; Shared Constants match plan frontmatter; the `[VERBATIM Task 7 section …]` placeholder is the ONLY placeholder — everything else concrete. |
| Prior Task Awareness | PASS | Task 6's five surviving mutations (MX1–MX5) and the SSOT violation are carried into the prompt as hard constraints; the module transition + renumbering (`518875c`) is explained; the test-echo collision carry-forward and the `_hermetic_picker_env` preservation requirement are both explicit. |
| Escalation Check | PASS | No unresolved BLOCKED/NEEDS_CONTEXT from Task 6 being pushed through. Deferred items correctly routed — env-validation tests to Task 7, script changes to Task 8. |
| Architectural Alignment | PASS | SSOT enforced (frozen `CMUX_*` / `PICKER_*` constants must be consumed, not duplicated — directly addresses the Task-6 finding). Shared test infrastructure change framed correctly: add knobs, preserve existing call signatures, default to today's behavior. |
| Pattern Completeness | PASS | References target the task's actual challenge (harness idiom + assertion discriminating-power), not merely layout. |

## Judgment on the two controller decisions

**(a) Coverage-only (Task 7) vs script-changing (Task 8) seam — SOUND.**
All four zero-protection behaviors (picker-absent, non-executable version, `--telemetry off`, env-validation) can be pinned without changing the script. The two new helper knobs make the previously-inexpressible cases constructible; every test uses the existing output surface. Step 7's `git diff --name-only … spawn-handoff-session.sh` must-be-EMPTY check enforces the boundary mechanically.

**(b) Deferring the failed-reservation-write exit path to Task 8 — SOUND.**
The exit-code ladder is frozen at 0/3/1 by the module Contract Constraints. Routing a failed reservation write to the existing exit 3 is a script change (check write rc + conditional exit), which belongs in sweep B. Task 7 correctly stays out of it.

## Findings

None. The dispatch is ready.
