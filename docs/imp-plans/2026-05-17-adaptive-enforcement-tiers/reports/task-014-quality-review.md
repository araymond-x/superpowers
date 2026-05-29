# Task 14 Quality Review — Controller Checkpoint `--manifest` Support

**Reviewer:** Senior Code Reviewer (general-purpose)
**Reviewed range:** `f1cd891..46c909b`
**File reviewed:** `skills/subagent-driven-development/scripts/controller-checkpoint.py`
**Verified empirically:**
- `.venv/bin/python3 -m pytest tests/unit/ -v` -> 321/321 PASS
- `python3 tests/ARaymond-skill-regression/validate-all-skills.py` -> PASS: 143 / FAIL: 9 / WARNING: 2 (all 9 FAILs in `materialize-manifest.py` / `transition-module.py`, none in `controller-checkpoint.py`)
- Spot-tested four CLI error paths (missing args, missing file, malformed JSON, schema-invalid manifest) -> all exit 3 with `{"error": ...}` on stderr
- Spot-tested micro tier -> `honesty_check_missing` and `trace_audit_missing` emit `status: SKIP`, NOT in blockers
- Spot-tested standard tier -> both checks emit `status: FAIL`, ARE in blockers (regression intact)

---

## Strengths

- **Helper extraction is a genuine SSOT win.** `_load_manifest_config(args)` consolidates all manifest-loading logic into a single 50-line function called from each phase. No inline manifest reads exist anywhere else in the file (verified by grep for `args.manifest`, `manifest_data`, `json.loads(Path`). The partner review v2 mandate is satisfied with a clean interface.
- **Defense-in-depth on error paths.** Four distinct exit-3 error paths (missing args guard, file-not-found, JSON decode, Pydantic validation), each with a structured `{"error": ...}` payload on stderr. Matches the script's documented exit-code contract.
- **Git-root resolution upgrade.** Replacing `parent.parent.parent` with `git -C <manifest_parent> rev-parse --show-toplevel` is a meaningful robustness improvement that aligns with Task 12's `transition-module.py:115-123` precedent. The fallback path emits a clear stderr warning, so non-git environments degrade visibly rather than silently producing wrong paths.
- **Pydantic validation at the boundary.** `SddSession.model_validate(manifest_data)` is the right tool — extra fields are rejected, all schema constraints from `sdd_session.py` (task_range validity, midpoint in range, module consistency) run automatically. Cross-artifact correctness is enforced for free.
- **Tier gating implemented at the right level.** SKIP override lives directly inside the existing Check 5 / Check 6 conditional blocks in `run_pre_completion` (lines 994-1023, 1025-1047). The blockers list is gated by the same `if tier == "micro"` branch — there is no path where a check is SKIP yet still appended to blockers. Correct semantics.
- **Backward compatibility preserved.** All 24 pre-existing tests in `test_controller_checkpoint_stale.py` and `test_pre_completion_gates.py` pass unmodified. The full 321-test unit suite passes. The two callers of the script in production (`sdd-stop-hook.sh` and `sdd-pre-dispatch-hook.sh`) both supply `--plan-file` explicitly, so relaxing `required=True` -> `required=False` is invisible to them.
- **Six deviations dispositioned, all justified.** Each row in `deviations.md` (lines 25-29) names the architectural rule or precedent that motivates the choice, and the ForwardConcern for Task 15 is flagged exactly where the inheriting task will encounter it.

## Issues

### Critical

(none)

### Important

(none)

### Minor

- **Type-hint inconsistency vs. the rest of the file** — `controller-checkpoint.py:43,400`. The new helper signature uses `Tuple[Optional[str], Optional[dict]]`. Every other return annotation in the file uses bare built-ins (`-> dict`, `-> list`, `-> int`). The deviation log row 4 explains why PEP 604 was avoided (regression's Python 3.9 category), but the file's existing convention is unparameterized built-ins. Either accept the minor stylistic departure (chosen here for richer typing) or simplify to `-> tuple` and add a docstring note about the shape. Not worth holding the task on; record-only.
- **Generic `except Exception` on Pydantic validation** — `controller-checkpoint.py:433`. The handler is functionally correct (Pydantic's `ValidationError` derives from `Exception`), but `except Exception` could mask future unrelated bugs in `model_validate`. Tightening to `except (ValidationError, ValueError, TypeError)` would be cleaner. Low-priority; the existing `except Exception` in `main()` (line 1260) follows the same pattern, so consistency is preserved.
- **Side-effect mutation of `args.plan_file` could surprise maintainers** — `controller-checkpoint.py:443-446`. The docstring (lines 403-404) explicitly documents this side effect, which is the right mitigation. A future refactor could return the resolved path instead of mutating in place, but the current pattern is acceptable and contained.
- **`enforcement` return tuple element is unused** — `controller-checkpoint.py:848`. `_load_manifest_config` returns `(tier, enforcement_dict)`, but only `tier` is consumed (and only in `run_pre_completion`). The two other phase callers (`run_pre_execution:459`, `run_pre_dispatch:600`) ignore both return values. The implementer acknowledges this as deliberate forward planning for Module 4. Acceptable; alternative would be returning only `tier` and re-loading enforcement later when needed. Not worth changing now.

### Needs Context

- **Module 4 will likely consume `enforcement` via this helper.** The current "unused enforcement tuple element" minor finding is the right call only if Module 4 indeed uses it. If Module 4 takes a different route (e.g., a dedicated enforcement-loader), the dead-tuple element should be pruned. Resolution: defer to Module 4 plan once available.
- **PEP 604 cleanup of `materialize-manifest.py` / `transition-module.py` is logged but not scheduled.** The implementer's deviation row 4 notes 9 pre-existing FAILs in sibling Module 1/3 scripts and recommends a separate cleanup task or formal waiver. Either resolution is fine; raising visibility here so it doesn't go unscheduled indefinitely.

## Architectural Alignment

- **Single source of truth: PASS.** `_load_manifest_config` is the sole entry point for manifest reading. No inline duplication; all three phase handlers call it identically (`_load_manifest_config(args)` at the top of `run_pre_execution`, `run_pre_dispatch`, and `run_pre_completion`). Spot-grep for `args.manifest` shows only the helper and the main() guard reference it.
- **Dead code: PASS.** All four new imports (`subprocess`, `Optional`, `Tuple`, `SddSession`) are exercised by the new helper. Grep confirms each is used at runtime.
- **Caller audit (`--plan-file` relaxation): PASS.** Both production hooks that invoke the script (`sdd-stop-hook.sh:22`, `sdd-pre-dispatch-hook.sh:615`) supply `--plan-file` explicitly. SKILL.md documentation examples (lines 291, 297, 303) also supply `--plan-file`. The argparse relaxation is safe; the explicit guard in `main()` lines 1231-1238 catches the only failure mode (neither flag provided).
- **Migrations-and-code-together principle: PASS.** No schema changes; the manifest schema was already shipped in Module 1, and `controller-checkpoint.py` now consumes it via the same Pydantic model the producers use. Single contract end-to-end.

## Assessment

**APPROVE**

The implementation is faithful to the partner review v2 mandates (helper extraction, `git rev-parse`, `SddSession.model_validate`), correctly gates Checks 5 and 6 to SKIP under micro tier without polluting the blockers list, and preserves backward compatibility for every existing caller. All four error paths exit 3 with structured JSON, matching the script's contract. The six deviations are each justified by a stated architectural principle or in-tree precedent, and the lone ForwardConcern (Task 15 reference-test key names) is flagged in the right place for the inheriting task.

The Minor findings (type-hint convention, generic `except Exception`, side-effect mutation, unused enforcement tuple element) are all stylistic or forward-looking; none warrant changes to ship this task.

Task 15 must update its reference test code to use `honesty_check_missing` / `trace_audit_missing` (not `honesty_check` / `trace_audit`) — the ForwardConcern is correctly logged.
