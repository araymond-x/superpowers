# Spec Review — Task 009: Write Hard Gate Tests
# Status: PASS
- All 3 test classes present with correct method counts (2 + 3 + 3 = 8 tests)
- Assertions match plan behaviors (exit 2 for blocks, exit 0 for allows)
- Uses shared helpers from sdd_test_helpers.py
- 3 fail for correct TDD reasons, 5 pass on existing behavior
- Deviation noted: test_blocks_when_task_header_not_in_plan doesn't isolate token gate
