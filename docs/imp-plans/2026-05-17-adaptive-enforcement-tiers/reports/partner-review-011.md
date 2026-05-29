# Partner Review — Task 11: Hook Rewrite Tests

**Tier:** Full (final Module 2 task; sets test coverage baseline for all manifest-mode logic from Tasks 6-9)
**Model:** haiku
**Final Status:** APPROVED (first round)

## Checks (all PASS)

1. **Midpoint formula correction:** Prompt explicitly identifies the bug in the plan's reference code (`end - start + 1`) and instructs the Module 1 formula (`end - start`). Cross-referenced against `materialize-manifest.py:64`.
2. **Helper availability:** Confirms `make_hook_input` and `run_hook` exist in `sdd_test_helpers.py`. Notes that `create_reports_for_task` and `create_full_task_prerequisites` may not exist — instructs implementer to create stubs if needed.
3. **Required tests:** 5 listed (micro skip partner; standard block partner; out-of-range; Explore passthrough; process requirements injected) + 1 optional sentinel-edge case from Task 9 carry-forward.
4. **Test class organization:** New `TestManifestModeDispatchDetection` class appended to existing test file.
5. **Pydantic schema:** Prompt specifies "all required fields" of SddSession; cross-referenced.
6. **Test-only scope:** Hook is NOT modified by Task 11.
7. **Test result expectation:** All tests (existing 16 + new 5+) must PASS.

## Authorization

Proceed with implementer dispatch using `/tmp/task-011-implementer-prompt.md`.

## Expected Deviations

- Required Modification #1: midpoint formula uses Module 1's `end - start` (vs plan's `end - start + 1`). This is the planned-and-disclosed correction.
- Possible additional deviations: new helper stubs if `create_reports_for_task` / `create_full_task_prerequisites` don't exist.
