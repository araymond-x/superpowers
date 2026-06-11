# Task 6 Code Quality Review (N17)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=6 type=quality-review).
> Reviewed: commit 28b8f1a against module-1-cleanup.md Task 6 (base edc5ff2).

### Strengths

- **Exact plan conformance.** Implementation matches the Task 6 plan code block verbatim. Path semantics correct on both branches: `module.file` is a bare filename joined under `feature_dir`, while `plan_file` is git-root-relative both in the model and the hook (`MANIFEST_PLAN_FILE="$GIT_ROOT/$(jq -r '.plan_file' ...)"`). The join is consistent with the producer (materialize-manifest.py:161 `git_root_relative()`).
- **Test mirrors the established GREEN sibling.** `TestN17MainPlanFallback` is a precise RED-pair of `test_verification_task_exempt_from_reviews` — identical fixture shape; the only delta is the variable under test (which plan file carries the declaration).
- **Fixture approach follows file conventions.** Read-modify-write of the manifest JSON post-`create_manifest` is the established pattern (lines 129, 161, 240). Extending `create_manifest` with a param for a single consumer would be speculative generality.
- **Reuses `_verification_task_ids_from_file`** — SSOT within the Python layer respected.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)

1. **Dead initializer.** `verif_ids: set = set()` (transition-module.py:108) is now unconditionally reassigned by both branches — vestigial (it was load-bearing pre-fix; the empty fallthrough WAS the N17 bug). Collapsing to plain if/else assignment would make exhaustiveness explicit. Cosmetic.
2. **The fixed path has no canonical producer.** materialize-manifest.py:125-130 hard-fails on a module missing `file`, so empty `module.file` only arises from hand-edited/legacy manifests. The fix is hook-parity defense-in-depth (the hook's fallback exists for the same input). Not dead code — the model accepts `file: ""` and the plan mandated it.
3. **Set-but-missing divergence remains unpinned (per spec, acceptable).** Hook checks `-f`; Python checks truthiness — set-but-missing → fail-closed in Python. A one-line characterization test would prevent a future "harmonize with the hook" edit from silently flipping it; advisory note sufficient for now.
4. **Line-number comment will rot.** "hook lines ~294-299" — the durable cross-reference is the file/construct name (`EFFECTIVE_PLAN_FILE` fallback), not line numbers.

### Recommendations

- Bash/python duplication of the effective-plan-file *decision* is acceptable layer duplication (bash hook cannot share Python code; cross-reference comment is the right mitigation). Drift vector to watch: hook fallback chain growing a third tier without the transition mirroring it.
- Batch items 1/4 with any future touch of this function; neither justifies a standalone commit.

### Assessment

**Ready to merge?** Yes

**Reasoning:** Fix matches the plan verbatim, path resolution verified against model and materializer, test pairs with its GREEN sibling, all findings cosmetic or already-flagged advisories. Tests: transition suite **13 passed**; full suite **430 passed, 1 warning**.
