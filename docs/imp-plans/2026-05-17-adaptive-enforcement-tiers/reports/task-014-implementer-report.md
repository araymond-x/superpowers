---
schema_version: 1
task_id: 14
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "modified"
  - path: "docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/deviations.md"
    description: "modified"
tests:
  written: 0
  passing: 0
  command: ".venv/bin/python3 -m pytest tests/unit/test_controller_checkpoint_stale.py tests/unit/test_pre_completion_gates.py -v (regression: 24/24 PASS; new tests are Task 15)"
  result: PASS
---

**Implementation Summary:**

Added `--manifest` support to `controller-checkpoint.py`. The new
`_load_manifest_config(args)` helper is called at the top of all three phase
functions (`run_pre_execution`, `run_pre_dispatch`, `run_pre_completion`); when
`args.manifest` is set, it loads and validates the `.sdd-session.json` file via
`SddSession.model_validate`, resolves git root via
`git -C <manifest_parent> rev-parse --show-toplevel` (with `parent.parent.parent`
fallback), and mutates `args.plan_file` in place — preferring
`active_module_file` over `plan_file` when both are set. The helper returns
`(tier, enforcement_dict)`. In `run_pre_completion`, the returned `tier` gates
Checks 5 (honesty check) and 6 (trace audit): when `tier == "micro"`, both
checks emit `{"status": "SKIP", "detail": "Micro tier — ... skipped per manifest"}`
without appending to `blockers`. Standard tier preserves the existing FAIL
behavior. Check 7 (minimum-tier ratio cap) is independent of tier and left
intact.

`--plan-file` was relaxed from `required=True` to `required=False`, with an
explicit guard in `main()` that prints a JSON error and returns exit 3 when
both `--plan-file` and `--manifest` are absent. This preserves the script's
JSON-on-stderr + exit-3 contract for script errors.

Backward compatibility verified end-to-end: existing 24 tests in
`test_controller_checkpoint_stale.py` and `test_pre_completion_gates.py` all pass
without modification. Full unit suite (321 tests) passes. Manual spot-test
confirmed `--manifest` mode skips honesty/trace checks under micro tier and
enforces them under standard tier, and that backward-compat `--plan-file`
invocations work unchanged.

**Source Files Read:**
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` (full file, lines 1-1149)
- `skills/scripts/models/sdd_session.py` (`SddSession`, `Enforcement`, `TIER_PROFILES`)
- `skills/subagent-driven-development/scripts/transition-module.py` (git-root resolution pattern, lines 115-123)
- `skills/scripts/models/checkpoint_result.py` (existing CheckpointResult model — verified the existing `run_pre_completion` uses raw dict literals, not `CheckResult` constructors)
- `tests/unit/test_pre_completion_gates.py` (existing pre-completion test patterns)
- `tests/unit/test_controller_checkpoint_stale.py` (stale artifact test patterns)
- `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/module-3-transitions-and-checkpoint.md` (Task 14 spec lines 439-502, Task 15 reference lines 503-642 for forward-concern check)
- `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/deviations.md` (existing deviation row format)
- `tests/ARaymond-skill-regression/validate-all-skills.py` (Python 3.9 regression policy, lines 1145-1242)

**Deviations from Plan:**

Six rows added to `deviations.md` under Task 14:

1. **Bug fix — git-root resolution.** Replaced plan's brittle
   `Path(args.manifest).resolve().parent.parent.parent` with `git rev-parse
   --show-toplevel` (matches `transition-module.py` precedent from Task 12).
   `parent.parent.parent` retained as a fallback only when `git rev-parse`
   exits non-zero, with a stderr warning emitted.

2. **IndependentDecision — `_load_manifest_config` helper extraction.** Plan
   reference text shows a 5-line block at the top of `run_pre_dispatch`
   ("and similar for other phases"). Triplicating would violate the SSOT
   architectural principle. Helper extracted per task contract; signature
   `(args) -> Tuple[Optional[str], Optional[dict]]` returns
   `(tier, enforcement_dict)` or `(None, None)`; mutates `args.plan_file`
   in place. Each phase calls it at the top.

3. **IndependentDecision — `--plan-file` relaxed to `required=False`.** With
   explicit guard in `main()` that returns exit 3 with a JSON error if both
   `--plan-file` and `--manifest` are absent. Preserves the script's JSON
   error contract.

4. **IndependentDecision — Legacy `typing.Optional`/`Tuple` annotations.** The
   regression test (`validate-all-skills.py` category 8) enforces Python 3.9
   compatibility for SDD scripts. Used `Tuple[Optional[str], Optional[dict]]`
   instead of `tuple[str | None, dict | None]` to keep the new helper at zero
   regression FAILs. Pre-existing PEP 604 violations in `materialize-manifest.py`
   and `transition-module.py` are out of scope.

5. **ForwardConcern — Task 15 reference test code uses wrong check keys.** Plan
   reference for Task 15 (module-3 Step 1, around line 613) reads
   `checks.get("honesty_check", {})`. The implemented keys are
   `honesty_check_missing` / `trace_audit_missing` (matches the existing
   pre-completion code). The Task 15 implementer must update the assertion
   key names or the test will dereference an empty dict.

**Self-Review Findings:**

- `--manifest` is optional (`default=None`) — confirmed via argparse signature.
- Backward compat: existing `--plan-file` tests pass without `--manifest` (24/24
  passed; full unit suite 321/321 passed).
- `_load_manifest_config` is extracted as a single helper called from three
  phase functions — not triplicated.
- `SddSession.model_validate` is used for safety; raises `pydantic.ValidationError`
  → caught and rendered as exit-3 JSON error.
- Git-root via `git rev-parse`, with `parent.parent.parent` as documented fallback
  + stderr warning when git is unavailable.
- Micro tier sets `honesty_check_missing` / `trace_audit_missing` to status
  `"SKIP"` and does NOT append them to `blockers`. Verified via end-to-end
  spot-test with synthetic micro and standard manifests.
- No unused imports: `subprocess` and `SddSession` are new; `Optional` and `Tuple`
  from `typing` are used in the helper signature; existing imports unchanged.
- Tests `result: PASS` (not `N/A`) — frontmatter accurate.

Regression test PASS count rose from 142 to 143 (added file now passes Python 3.9
check). FAIL dropped from 11 to 9 (the 2 pre-existing controller-checkpoint
violations were on different lines and resolved by my legacy-annotation choice;
the 9 remaining FAILs are all pre-existing in `materialize-manifest.py` and
`transition-module.py`).

**Concerns:**

1. **Task 15 will need a small fix** (FORWARD-CONCERN, logged in deviations row
   above). The reference test code in module-3 Step 1 uses key names
   `honesty_check` / `trace_audit` rather than the implemented
   `honesty_check_missing` / `trace_audit_missing`. The implementer should
   either rename the asserted keys or rename the implementation keys — I
   preserved the existing names per Task 14 instructions ("Use the actual check
   keys ... when implementing the SKIP override, not the plan's truncated key
   names").

2. **Pre-existing Python 3.9 violations in sibling SDD scripts** (Module 1
   `materialize-manifest.py`, Module 3 `transition-module.py`). Not introduced
   by Task 14, but flagged here for visibility — these are committed code that
   would FAIL the regression's category 8 check. Out of scope for Task 14;
   recommend a separate cleanup task to either remediate them or formally waive
   them in the regression test.

3. **`enforcement` return value is currently unused.** `_load_manifest_config`
   returns `(tier, enforcement_dict)` but only `tier` is consumed (by the
   pre-completion micro-tier branch). The `enforcement` dict is preserved in
   the signature for future tasks (Module 4 may use it to gate additional
   checks). Captured as `_enforcement` (underscore prefix) at the call site to
   signal intentional non-use. If a reviewer prefers it removed, the signature
   can be simplified to return only `tier`.
