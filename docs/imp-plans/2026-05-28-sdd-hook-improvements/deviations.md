# Deviations Register

> Auto-maintained by controller during subagent-driven-development execution.
> Review all entries before merge.

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
| Ingestion | ScopeChange | Parent `plan.md` frontmatter had `tasks: []`; `materialize-manifest.py` requires a non-empty flat `tasks:` list even for modular plans (guard at line 112 precedes the modules block). Populated the flat list with all 9 tasks (id+title) to match the established modular convention shown in `tests/integration/sdd-e2e-test.sh` (which lists tasks flat AND in modules). No `review_tier` added (field not in model until Task 1). | Accepted |
| Ingestion | ProcessNote | Run executed with `subagent_type: general-purpose` per user decision. Live main-checkout hook passes general-purpose dispatches through (Item-1 bug being fixed), so hook enforcement is a no-op this run; controller runs `controller-checkpoint.py` manually at each phase and dispatches all spec+quality reviews by hand. Worktree isolation confirmed: live hook = main checkout, not worktree. | Accepted |
| Pre-exec checkpoint | ToolFalsePositive | `controller-checkpoint.py --phase pre-execution` reports BLOCKER `source_contracts` FAIL on "Source Contracts: None". Documented false positive (CLAUDE.md): `validate-plan.py` accepts "None" (PASSed); the checkpoint treats the literal "None" as non-empty content. The `writing-plans` skill requires the section present and "None" is the correct value (this feature has no external contracts). Tool-improvement opportunity: checkpoint should treat "None" as valid no-contracts, matching validate-plan.py. Not patched (out of scope; untested mid-run change to enforcement system). | Accepted |
| Pre-exec checkpoint | ToolFalsePositive | `stale_artifacts` WARNING (non-blocking) flags this session's own ingestion artifacts (deviations.md content + the 2 pre-execution-audit files just created) as "prior session" artifacts. Verified: no uppercase DEVIATIONS.md exists; workspace was clean (self-assessment Q8); baseline was 328 green. Inherent ordering tension — the audit must exist before dispatch but the check assumes reports/ empty at pre-execution. | Accepted |

| Task 2 | IndependentObservation | `check_review_tier_heuristic` uses substring matching (`kw in title`) per the plan's verbatim code, so "auth"⊂"author", "data"⊂"database", "delete"⊂"deleted" could draw a false-positive WARNING on a minimum-tier task with such a title. Non-blocking (author resolves/accepts) and spec-faithful — the plan prescribed the exact keyword list + substring match. Not fixed (would diverge from plan's exact code). Candidate for a future word-boundary improvement. (Spec review refined: "data"⊂"database" is a non-issue — data keywords only fire when "migration" is in title; only "auth"⊂"author" is a real, rare FP.) | Accepted |
| Task 3 | TestCoverageGap | Manifest-modules branch (Step 3b: _resolve_git_root + feature_dir join + modules[].file reconstruction) has no DIRECT unit test. Cross-file exclusion behavior is proven via --additional-plan-files (same all_plan_contents path); the manifest-reading glue is exercised by integration e2e (7/7 PASS). Task 9 Step 1 must add a manifest-modules review_tier exclusion assertion to the e2e to close this. Kept Pending to block completion until Task 9 verifies. | Pending |
| Task 3 | IndependentObservation | Manifest module files also feed pre-existing checkbox/task aggregation (plan-directed). Harmless: if --manifest and --additional-plan-files name overlapping files, progress.tasks_total inflates cosmetically only; checkbox PASS/FAIL and the set-based ratio are unaffected. | Accepted |
| Task 3 | QualityReviewNit | Quality review Minor 1: redundant `from pathlib import Path as _P` (Path already imported module-level). Controller fixed directly (2-line cosmetic, code already fully seen via both reviews → context-pollution moot; fix subagent disproportionate). Suite re-confirmed 345 green; Path confirmed module-level. | Resolved |
| Task 3 | FutureHardening | Quality review Minor 2: module-read failures in the manifest-modules block are silent (`except Exception: pass`); only the primary plan emits `review_tier_plan_parse_skipped`. A module-read throw would give no diagnostic → potential silent under-exclusion (false block, hard to debug). Optional debuggability nicety: add a distinct `module_plan_read_skipped` warning. Not implemented (path empirically verified working via reviewer smoke test; broad-except matches file's existing manifest graceful-degradation pattern; precise test fiddly, expands scope). Candidate for future hardening. | Accepted |

## Deferred Work
[Items deferred from plan scope]

## Independent Decisions
[Decisions made by subagents without plan guidance]

## Scope Changes
[Requirements that changed during execution]
