# Deviations Log — Adaptive Enforcement Tiers

| Task | Category | Description | Disposition |
|------|----------|-------------|-------------|
| 4 | Bug fix | **Midpoint formula `range_size` definition.** Plan reference code uses `range_size = end - start + 1`, but this produces midpoints outside the task range for single-task inputs (e.g., range (1,1) yields midpoint 2, failing `midpoint_in_range` validator). Changed to `range_size = end - start`, which is consistent with the test fixtures in Task 5 and passes all edge cases. The existing `sdd-pre-dispatch-hook.sh` uses `(TOTAL_TASKS + 1) / 2` (1-indexed); the manifest formula operates on 0-indexed task IDs and will replace the hook calculation. | Accepted — plan code is buggy; formula matches spec intent and test fixtures |
| 4 | Simplification | **`active_module_file` stores bare filename, not joined path.** Plan reference code uses `os.path.join(feature_dir, first.file)`, but the committed test fixture `test_valid_multi_module_session` uses `"active_module_file": "m2.md"` (bare filename). Used bare filename to match the established test contract. | Accepted — matches committed test fixture |
