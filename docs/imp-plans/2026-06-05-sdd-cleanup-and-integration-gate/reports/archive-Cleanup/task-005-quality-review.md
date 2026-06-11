# Task 5 Code Quality Review (N12)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=5 type=quality-review).
> Reviewed: commit edc5ff2 against module-1-cleanup.md Task 5 (base 9799438).

### Strengths

- **Surgical, plan-faithful diff.** The fix is exactly the two `elif` gates the plan specified (`transition-module.py:127-130, 149-152`) — file-existence stays under `pr.{spec,quality}_review_mode != "skip"`, only `_has_dispatch_provenance()` is gated on `manifest.enforcement.dispatch_provenance`. No drive-by changes, no dead code anywhere in the range.
- **SSOT confirmed.** The hook's Check 4c (`sdd-pre-dispatch-hook.sh:500`: `NEED_PROV=$(jq -r '.enforcement.dispatch_provenance' "$MANIFEST")`) and the transition validator now key the same decision off the same manifest field. This is the right dimension: micro tier's `process_requirements` review modes are `"self_review"` (not `"skip"`), so file-existence checks correctly remain active under micro — precisely the N12 semantics. Gating on `process_requirements` instead would have conflated review mode with provenance and diverged from the hook.
- **Test design is deliberate, not just green.** Test 1 pins the positive cell with both a return code AND an error-substring exclusion; test 2 is an explicit regression guard against over-correcting — its passed-pre-fix status is correct and by design for a "split" fix.
- **Fixture conventions followed exactly** — `create_manifest(tier="micro")` / `run_transition`, the `"x" * 100` >50-byte pattern, same per-`tid` loop shape as adjacent tests. No parallel machinery.
- **Wrap style clean** — conditions break at the call parenthesis, consistent with the file.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)

1. **"No dispatch log" cell tested as sentinel-only, not file-absent.** The truly-absent-file path was verified by code-read: `validate_module_completion` never touches the log when provenance is off, and `transition()` Step 5 guards `os.path.isfile(dispatch_log)` before archiving — a literally-missing log also passes. Acceptable as-is.
2. **DRY judgment:** extracting a helper for the twice-repeated two-line gate with an intervening `has_min` waiver would be premature abstraction; `_has_dispatch_provenance` already encapsulates the log parsing. Leave it.
3. **`create_manifest` `context_summary_at=2` override — implementer's out-of-scope judgment confirmed correct** (function under test never reads it). However, real micro manifests carry `context_summary_at: None` (materialize-manifest.py:157), so the helper's blanket `=2` makes micro-tier test manifests exercise the N11 recompute branch (transition-module.py:234-235) that real micro manifests skip — a fixture-fidelity gap vs. the "fixtures must match actual system output" rule. Worth a follow-up row: make the override tier-faithful. Not blocking.

### Recommendations

- Add a BACKLOG/follow-up row for Minor 3 (tier-faithful `context_summary_at` in `create_manifest`).
- Four-way matrix fully pinned across new + existing tests: provenance-on × entries-present (`test_successful_transition`), provenance-on × entries-absent (`test_blocks_when_provenance_missing`), provenance-off × files-present (new test 1), provenance-off × file-absent (new test 2), plus the min-tier waiver orthogonal.

### Assessment

**Tests observed:** transition + SSOT suites → **16 passed**; full suite → **429 passed, 1 warning**.

**Ready to merge?** Yes

**Reasoning:** The change is exactly what the plan specified, restores hook↔transition SSOT on `enforcement.dispatch_provenance`, and the new tests pin all four matrix cells with specific error-substring assertions using existing fixtures. Only non-blocking fixture-fidelity and follow-up-row suggestions.
