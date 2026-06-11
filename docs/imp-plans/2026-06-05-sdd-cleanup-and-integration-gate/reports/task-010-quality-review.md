# Task 10 Code Quality Review (C2 Check 10)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=10 type=quality-review).
> Reviewed: commits 0f8db91 + fa9fe44 against module-2-integration-gate.md Task 10 (base 14e5906).
> Resolution of Important Issue 1: controller-dispatched fix (newest-merge-base selection) — see deviations.md.

### Strengths
- **The 7th (BLOCKING) merge-base fixture is exactly right** — the only fixture where merge-base != HEAD; proves the primary diff path; the exact shape this feature hits at its own pre-completion.
- **Fail-closed on every infrastructure path** (git missing/not-a-repo → infra FAIL + actionable blocker; probed: absolute/`../` declared paths that bypass the Pydantic validator still FAIL via git pathspec errors).
- **Audit Order 3 honored**; lenient-parse philosophy deliberately mirrors `_task_ids_where`.
- **Subprocess hygiene consistent with Check 9** (capture, text, timeout=10, rc-first, TimeoutExpired/OSError caught).
- **Blocker==check-key deviation properly handled** (validator makes the plan's pairing unrepresentable; documented).
- **Step 0 parity genuine**; **rename case verified empirically** (renamed-to passes; renamed-away fails as missing).
- Fixtures pin identity + gpgsign per-repo, `git init -b main`; 19 tests / 4.46s.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
1. **`origin/HEAD`-first base-ref priority is fail-open in THIS repo, today** (probed live: origin/HEAD resolves and always wins, but merge-base(origin/HEAD, HEAD) = 67df0cb — 21 commits behind merge-base(main, HEAD) = 5767609, because merges are local-only). Consequence: the "feature changeset" includes prior features' windows — a plan declaring `tests/integration/sdd-e2e-test.sh` without touching it would PASS because a prior feature modified it in the stale window. Precisely the staleness C2 exists to catch. Plan-level design defect (implementer followed Step 3 exactly). Smallest fix: prefer the candidate whose merge-base with HEAD is NEWEST (or local main/master before origin/HEAD) + one fixture.
2. **False-block when HEAD is the base branch in a remoteless repo** (on-main SDD via .allow-main: merge-base(main, HEAD)==HEAD, committed test invisible to both paths → FAIL despite legitimate work). [NEEDS_CONTEXT → BACKLOG: Aaron prefers improving on-main flows, so worth a row.]

#### Minor (Nice to Have)
3. Fixture global-config bleed-through: `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` not nulled — host hooksPath could break fixtures on another machine; one `env=` dict hardens.
4. `content.find("---", 3)` not line-anchored in `_integration_test_paths` — inherited verbatim from `_task_ids_where` (consistency was right); fix both together if ever fixed.
5. Third near-identical git subprocess wrapper — a module-level `_git_run` would SSOT the runner (check semantics separation is correct). `_resolve_git_root` has no timeout (pre-existing).
6. Untested edges: declared path is a directory (fail-closed but "missing on disk" detail misleading); multi-file different declarations; rename. `.format()` vs f-string cosmetic.

### Recommendations
1. Fix Issue 1 now (newest-merge-base selection, ~10 lines + 1 fixture) — the leniency is invisible when it bites.
2. BACKLOG row for Issue 2 (on-base-branch detection when merge_base == HEAD).
3. Null host git config in fixtures (Issue 3).
4. Remember spec.md reconcile debt (integration_test_missing → integration_test_present) at the doc pass.

### Assessment
**Ready to merge?** With fixes
**Reasoning:** Faithful to the plan, fail-closed on every error path, well-tested (19/19 C2 file; full suite **455 passed, 1 warning**) — but the plan-prescribed origin/HEAD-first base ref is demonstrably fail-open in this repo right now; fix the ref selection before this gate is trusted.
