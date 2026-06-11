# Task 4 Spec Compliance Review (N7 + Step 3b SSOT consolidation)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=4 type=spec-review).
> Reviewed: commits 1179654 + 9799438 against module-1-cleanup.md Task 4 (base 1584112).

**PASS** — Spec compliant AND contract compliant

**Verification evidence (independently confirmed by reading code and running tests):**

1. **Step 1 (TDD red test)** — `TestSourceContractsNonePass` exists at `tests/unit/test_fence_aware_parsing.py:94-115`, uses the file's `_H` self-hosting guard (line 27) and `_ckpt` importlib loader (line 23), matches the plan's prescribed test almost verbatim. **Genuine red test verified**: I extracted the BASE_SHA (1584112) scripts tree to /tmp and ran the exact test scenario against the pre-fix `run_pre_execution` — old code returned `{'status': 'FAIL', ...}` with `blockers: ['source_contracts']`. New code passes.

2. **Step 3 (N7 fix)** — `controller-checkpoint.py:699-714` implements the exact three-way semantics from the plan: present+non-empty → PASS; present+None/empty → OK "valid-absent" with **no blocker appended**; absent → OK "Task 0 not required". Grep confirms no other `source_contracts` blocker append anywhere in the file. **No Task-0 regression for real-contract plans**: the old FAIL only validated section non-emptiness — Task-0-required enforcement for non-empty contracts lives in (a) `validate-plan.py:532-537` (plan-time BLOCKER via `source_contracts_non_none`, untouched) and (b) the hook's Check 5 (`sdd-pre-dispatch-hook.sh:546-572`, dispatch-time block, untouched, with the pre-existing `None` exemption at line 554 the implementer cited). `source_contracts_non_empty` has no other callers (grep-confirmed).

3. **Step 3b (SSOT consolidation)** — `_unfenced_content` is now defined exactly once (`_report_utils.py:48`); both scripts import it (`validate-plan.py:31`, `controller-checkpoint.py:52`) and all 11 remaining call sites resolve to the import. I diffed the two BASE_SHA local copies against each other (byte-identical) and against the consolidated version (identical except 3 added docstring lines — documentation only, no behavior change). The `sys.path.insert` deviation is justified and works: importlib-loaded tests pass, and both scripts CLI-smoke-tested OK from `/tmp` (foreign cwd).

4. **Step 4 (tests)** — Observed counts: targeted suites (`test_fence_aware_parsing.py` + `test_validate_plan.py` + `test_pre_completion_gates.py`) = **67 passed**; new N7 test alone = **1 passed**; full suite `tests/unit/ -q` = **427 passed, 1 warning** (matches the report's command-string claim).

5. **Step 5 (commits)** — Both subjects match the prescription exactly: `1179654` "fix(N7): Source Contracts None/empty treated as valid-absent, not FAIL" (touches only the check block + test) and `9799438` "refactor(SSOT): consolidate _unfenced_content into _report_utils.py" (touches only the consolidation). Split is clean — verified via `git show` on each.

6. **Pydantic concern accuracy** — Confirmed real: `_report_utils.py:19-21` imports `implementer_report`, which imports `pydantic` (`implementer_report.py:5`), so `validate-plan.py` is no longer stdlib-only. Live install unaffected (both system and PATH python3 on this machine have pydantic; bare-python3 run of validate-plan.py on the live module plan returns PASS).

7. **Report completeness** — `reports/task-004-implementer-report.md` has valid frontmatter (status, files_changed, tests, contract_compliance) and all 5+1 prose sections, all substantive. The `tests.passing` post-hoc correction is pre-disclosed; not flagged.

**Advisory observations (non-blocking, for the controller's awareness):**

- [ADVISORY] [MISUNDERSTANDING]: The implementer's Concerns section slightly mischaracterizes the pydantic exposure mechanism. `plan-validation-gate-hook.sh:165` invokes `validate-plan.py` with bare `python3` **unconditionally** (not via `$PYTHON`, and not only in a "fallback branch" — only Gate 1b's `validators.py` call at line 193 uses `$PYTHON`). And the failure mode on a pydantic-less machine is not a visible crash: line 165's `|| echo ""` plus the `[ -z "$OUTPUT" ] && continue` at 166-168 means Gate 1 would **silently fail open** (structural validation skipped, no error surfaced). Risk-neutral on this machine (both pythons have pydantic) and the plan explicitly named `_report_utils.py` as the target, so the implementation is per-spec — but the follow-up note should record "Gate 1 bare-python3 silent fail-open" rather than "fallback crash" as the actual exposure.
- [ADVISORY] [EXTRA]: The consolidated docstring gained 3 lines vs. the byte-identical originals ("Single source of truth — imported by..."). Harmless and arguably useful; noted only because Step 3b said "byte-identical" — the code body is identical, only documentation was added.
