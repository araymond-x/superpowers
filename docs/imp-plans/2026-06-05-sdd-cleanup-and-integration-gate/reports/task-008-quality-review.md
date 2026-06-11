# Task 8 Code Quality Review (C2 model)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=8 type=quality-review).
> Reviewed: commit 0f26fb4 against module-2-integration-gate.md Task 8 (base 9d0e9c8).
> Resolution of Important Issue 1: folded into Task 9 (see deviations.md) — Check 10's
> planned `is_file()` requirement already prevents the vacuous-pass scenario.

### Strengths
- Implementation matches the plan exactly and **fixed a real bug in the plan's snippet** (sys.path resolving to nonexistent tests/skills/scripts/models).
- Model placement consistent (`IntegrationTest` with the other nested StrictModels above Task/Module/Plan); inherits extra="forbid" correctly.
- Docstring omission matches the file's per-validator convention (no other plan.py validator carries one).
- `v.split("/")` is the right segmentation — probed: bare `..` rejected, `a/../b` rejected; crucially MORE conservative than os.path.normpath (which would collapse `a/../b` → `b` and accept). POSIX-only fine for this repo.
- Defense-in-depth layering appropriate: plan-time rejection (via validators.py, the only Plan importer) before Task 10's execution-time lookup. No consumer surprises (model_dump roundtrip passes; Plan consumed only by validators.py). No schema bump — consistent with precedent.
- Test file appendable as claimed.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
1. **Empty-string path is accepted** (plan.py:30-35). Probed: `IntegrationTest(path="")` validates (`isabs("")` False; `"".split("/") == [""]`). If Check 10 tested existence rather than `is_file()`, `git_root/""` (the git root, exists) would pass vacuously. [NEEDS_CONTEXT → RESOLVED by controller: Task 10's plan Step 4 explicitly requires `is_file()`, so empty path FAILS the gate; the one-line model guard + test is folded into Task 9 (C2-model refinement batch).]

#### Minor (Nice to Have)
2. Redundant `sys.path.insert` in the test file (conftest.py already inserts the models dir); function-local imports diverge from test_models/ convention — clean when Task 9 touches the file. (Plan-prescribed, not implementer sloppiness.)
3. `~/x.sh` accepted (isabs doesn't catch tilde) — harmless iff downstream never calls expanduser; Task 10 must join to git root without expansion.
4. No test pins bare `..` or empty string — close alongside the Important fix.

### Recommendations
- Fold empty-string guard + pin tests into Task 9; record in deviations (done).
- Task 9: drop redundant sys.path block, hoist imports to module level.
- Task 10: join path without expanduser/resolve-then-trust; require is_file().

### Assessment
**Ready to merge?** With fixes (→ fixes assigned to Task 9; Check 10 is_file() requirement confirmed in plan)
**Reasoning:** Faithful to the plan (and improves it), correctly layered, fully green — targeted 167 passed; full suite 441 passed, 1 warning. The single substantive gap (empty-string path) is mitigated by Check 10's planned is_file() and assigned to Task 9.
