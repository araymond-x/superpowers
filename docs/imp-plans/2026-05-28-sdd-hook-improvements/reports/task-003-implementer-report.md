---
schema_version: 1
task_id: 3
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "Renamed _count_review_tiers → _review_tiers_per_task (returns [(task_id,is_minimum)]); added _declared_minimum_task_ids (raw yaml.safe_load); run_pre_completion reads module plan files from --manifest, gathers declared_min across all plan contents, emits review_tier_plan_parse_skipped warning on parse failure; rewrote Check 7 as symmetric _ratio_check closure for quality+partner excluding declared_min."
  - path: "tests/unit/test_pre_completion_gates.py"
    description: "Added _plan_with_review_tiers builder + TestDeclaredMinimumExclusion (5 parametrized + unparseable-fallback + cross-file via --additional-plan-files); added import pytest."
tests:
  written: 7
  passing: 7
  command: ".venv/bin/python3 -m pytest tests/unit/ -q"
  result: PASS
contract_compliance:
  - constraint: "Threshold stays 50%; only denominator changes (exclude declared-minimum from num AND denom)"
    status: compliant
    detail: "_ratio_check filters declared_min from considered set; threshold 0.5 unchanged."
  - constraint: "Apply exclusion symmetrically to quality AND partner"
    status: compliant
    detail: "_ratio_check called for both quality-review and partner-review."
  - constraint: "Zero-denominator guard: filtered denom 0 → PASS"
    status: compliant
    detail: "if total > 0 ... else PASS (No non-declared reviews to ratio)."
  - constraint: "Plan-parse failure → empty exclusion set + WARNING"
    status: compliant
    detail: "_declared_minimum_task_ids returns ([], False) on failure; warnings.append('review_tier_plan_parse_skipped')."
  - constraint: "Raw yaml.safe_load, NOT Pydantic Plan model"
    status: compliant
    detail: "yaml.safe_load(content[3:end]) in try/except; reads only tasks[].review_tier/id."
  - constraint: "review_tier orthogonal to enforcement_tier"
    status: compliant
    detail: "No reference to enforcement_tier in the new logic."
---

**Implementation Summary:**
Refactored the pre-completion minimum-tier ratio gate so plan-declared `review_tier: minimum` tasks are excluded from both numerator and denominator. Three coordinated changes in one atomic commit: (1) `_count_review_tiers` → `_review_tiers_per_task` returning `[(task_id, is_minimum)]` via filename regex (minimum files captured first, full glob dedup-skips them); (2) new `_declared_minimum_task_ids` using raw `yaml.safe_load` (graceful degradation, not Pydantic); (3) `run_pre_completion` reads module plan files from `--manifest` (feature_dir + modules[].file via `_resolve_git_root`, try/except), gathers `declared_min` across all plan contents, and Check 7 rewritten as a symmetric `_ratio_check` closure for quality + partner. Unit suite 345 (338+7), regression 146/0, integration e2e 7/7.

**Source Files Read:**
- `controller-checkpoint.py` — `_count_review_tiers` (188-212), `run_pre_completion` all_plan_contents (888-896), ratio block (1054-1098), `_resolve_git_root` (372), `read_file` (93), argparse (--manifest/--additional-plan-files/--reports-dir). Verified `_count_review_tiers` had only the 2 ratio-block callers repo-wide.
- `tests/unit/test_pre_completion_gates.py` — run_pre_completion, _make_reports_with_minimum_tier, SCRIPT_PATH, imports.
- `skills/scripts/models/sdd_session.py` — manifest modules/paths shape (read-only).

**CLAUDE.md Files Read:**
- Project CLAUDE.md (worktree root) — testing layers, Python 3.9 compat. No subdir CLAUDE.md in scripts/ or tests/unit/ (absent).

**Deviations from Plan:**
- None functional. All snippet variable names matched real code (checks, blockers, warnings, all_plan_contents, args.manifest, args.reports_dir, blocker keys). Added `import pytest` (was missing). Corrected the misleading `# full glob excludes -minimum-tier.md` comment (true for quality, false for partner) to describe the actual dedup mechanism.

**Self-Review Findings:**
- RED confirmed: 3 exclusion/all-declared cases + cross-file test failed pre-change; 2 undeclared-block cases + fallback passed pre-change (regression guards). Python 3.9 compatible (# type: comments). Two-path git add (.venv excluded).

**Concerns:**
1. Manifest-modules branch (Step 3b: _resolve_git_root + feature_dir join + modules[].file reconstruction) has no DIRECT unit test. Cross-file behavior proven via --additional-plan-files (same all_plan_contents list); manifest-reading glue exercised by integration e2e (7/7 PASS, the exact bug class it historically caught). Task 9 Step 1 explicitly adds a manifest-modules review_tier exclusion assertion to the e2e — gap closed there.
2. Manifest module files also feed pre-existing checkbox/task aggregation (~906-914), plan-directed. Harmless: if --manifest and --additional-plan-files name overlapping files, progress.tasks_total inflates cosmetically, but checkbox PASS/FAIL and set-based ratio are unaffected.
