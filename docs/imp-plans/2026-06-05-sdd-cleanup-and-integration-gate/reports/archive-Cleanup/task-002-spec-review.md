# Spec Compliance Review — Task 2: N9 _task_ids_where + _load_all_plan_contents

**Verdict:** PASS

All requirements met:
1. `_task_ids_where` exists with correct signature, old functions removed ✓
2. `_load_all_plan_contents` with realpath dedup, missing file handling ✓
3. Retrofit: manifest = full replacement (NOT extend), non-manifest = single-file fallback ✓
4. All existing tests pass (420 total, 0 regressions) ✓
5. 7 new tests covering both helpers ✓

Tests verified: 38/38 passing (7 new + 31 pre-completion)
