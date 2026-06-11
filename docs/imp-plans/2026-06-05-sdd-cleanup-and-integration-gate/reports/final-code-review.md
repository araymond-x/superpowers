# Final Pre-Merge Review — sdd-cleanup-and-integration-gate (5767609..HEAD)

> Dispatched 2026-06-10 (Pre-Completion Gate final step; deviations.md read in full per gate requirement 4).
> Integration-level review of the whole 19-commit branch; per-task findings not re-litigated.
> Resolution of Important #1: fix commit follows (see deviations.md). Important #2: dispositioned Accepted + BACKLOG.

### Strengths

- **SSOT discipline held under mid-flight pressure.** Single `_unfenced_content` definition (no duplicates anywhere in skills/); `_task_ids_where` cleanly collapses the two walkers; `_load_all_plan_contents` quietly FIXES a latent pre-branch bug (old manifest-mode aggregation could double-count the active module and omit the parent plan).
- **The N18 lifecycle composes; its backstop comment is accurate** — every claim verified: boundary skip scoped correctly with the prior-modules discriminator; transition validates completion + provenance BEFORE truncating the log; pre-completion Checks 1/3/4 aggregate/archive-aware as claimed. Nothing skipped at the boundary escapes terminal verification for per-task checks (aggregates: see Important #2).
- **Check 10 fail-closed where it counts**: post-validation abs/`..` paths die in git pathspec errors → FAIL; unresolvable base ref → infra FAIL with blocker; merge-base fallback degrades toward FAIL. The stale-origin fixture is genuinely adversarial; fixture 7 mirrors this feature's own pre-completion shape.
- **No stale assertions** (base-ref change shipped with its own fixtures; no earlier test pinned the old order); `main()` initializes the N18 attributes in all phases. **Docs match code.** No debug leftovers/TODOs.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)

1. **Malformed `integration_test` declaration falls through all three layers silently (fail-open by shape).** `integration_test: tests/foo.sh` (flat string — the natural authoring mistake) or `{path: ""}`: (a) model layer skipped in the enforced path — plan-validation-gate-hook.sh:165 invokes validate-plan with bare python3; validators.py exits 2 without pydantic, and the gate blocks only on rc 1; (b) WARNING suppressed — `check_integration_test_risk` keys on `is not None`, so malformed counts as "declared"; (c) Check 10's `_integration_test_paths` requires dict+non-empty path, so malformed → "No integration_test declared — check skipped" PASS. Author believes they declared a gate; every layer reports green. Fix: `_integration_test_paths` surfaces present-but-malformed entries; Check 10 FAILs on them; +2 tests (string shape, empty-path shape). No existing test covers the string shape (verified).

2. **Terminal aggregate gates only police the final module — seam activated by this branch.** Check 7 (min-tier ratio) reads observed tiers via the intentionally-flat glob (archived module-1 reviews vanish from numerator AND denominator); Check 9 (git-reality) skips tasks absent from the live dispatch log, which transition truncates. `validate_module_completion` backstops existence + provenance at the boundary but not tier-ratio or git-reality. The "intentionally flat" note covers N4-era lookups, not this policy-aggregate consequence. Disposition required: fix (archive-aware inputs) or register (deviations + BACKLOG).

#### Minor (Nice to Have)
1. Stale CLAUDE.md gotcha: "pre-execution FAILs on Source Contracts: None — log as accepted deviation" — N7 inverted this to OK; add to the doc-pass reconcile list.
2. Check 10's nothing-declared path uses PASS+"skipped" detail (sibling convention) — a SKIP status would make non-evaluation machine-distinguishable.
3. `_resolve_base_ref` aborts all candidates if any single rev-parse times out — fail-closed, acceptable; per-candidate skip would be more resilient.
4. e2e Step 11 exercises only the untracked branch live; merge-base path is unit-only (deliberate fixture mirror — acceptable).
5. Confirmed-but-already-registered: duplicated `_git` helper; non-line-anchored `find("---", 3)`; N7 `!= FAIL` assertion; fence-blind risk-scan self-warning.

### Recommendations
1. Fix Important #1 before merge (~15 lines + 2 tests) — the exact silent-green failure mode C2 exists to eliminate.
2. Disposition Important #2 explicitly — the first real multi-module run on main is the named acceptance test for this work.
3. Doc pass: add the N7 gotcha rewrite to the reconcile list (unit count 405→456, writing-plans word count, spec.md blocker rename).

### Assessment
**Ready to merge?** With fixes
**Reasoning:** Cross-task wiring, module-boundary lifecycle, and test hygiene are genuinely sound — every backstop claim verified, and the deviations register demonstrates the enforcement system catching real fabrication. But Check 10 silently classifies a malformed declaration as "not declared" in the only layer guaranteed to run — close that (and disposition the aggregate seam) before this becomes the live enforcement code on main.
