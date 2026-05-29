# Plan Review Report — SDD Hook Improvements

**Plan files reviewed:** `plan.md`, `module-1-review-tier.md`, `module-2-hook-classification.md`
**Reviewer:** plan-document-reviewer (general-purpose subagent), two passes
**Final status:** ✅ **APPROVED** (re-review pass 2)

---

## Pass 1 — Issues Found (2)

The reviewer read all three plan files, the spec + distilled spec, and the actual source files (plan.py, sdd_session.py, controller-checkpoint.py, validate-plan.py, sdd-pre-dispatch-hook.sh, the test helpers and hook test files), verifying snippets against ground truth.

**Snippet verification (pass 1):** all VERIFIED.
- `_review_tiers_per_task` refactor — VERIFIED (regexes extract correct task IDs; full-glob-minus-min-glob avoids double-counting; `_count_review_tiers` has only the two ratio-block callers).
- `_write_manifest` helper + `setup_sdd_workspace` migration — VERIFIED (matches `SddSession`/`ArtifactPaths`/`Enforcement`/`ProcessRequirements`; reviewer prototyped the change and ran the full suite — 328 tests — green against the unchanged hook; `feature_dir="."` keeps `reports/` at `tmpdir/reports`).
- Hook 3-stage classification pipeline — VERIFIED (line ranges accurate; `DISPATCH_LOG`/`MANIFEST_TASK_START/END` set before the guard clause; classification order reviewer→implementer→passthrough).

**Cross-document audit (pass 1):** `review_tier` type MATCH; `TIER_PROFILES` structure MATCH; dispatch-log line format MATCH. `CURRENT_SCHEMA_VERSION` confirmed unchanged.

### Blocking Issue 1 — `head -n 5` misses the field names
The Contract Constraint and Task 8 test pinned `head -n 5` for the inline validation excerpt. The reviewer found (and I empirically re-verified by running the real `validate-report.py`) that its first 5 output lines are a decorative `═══` banner; the first failing field (`task_id`) is at line **6**, `status` at line **10**. So `head -n 5` surfaces no field name and Task 8's test would fail — and the feature's purpose (controller sees which field failed) is defeated. The spec's "first 5 lines includes field names" (spec.md:110) was wrong about the output format.

**Resolution:** changed to `head -n 12` (surfaces the first two failing fields) in the Task 8 hook snippet and the Contract Constraints of both module-2 and the parent plan, each with a spec-correction note. Task 8's test assertion tightened to require `task_id` specifically (the prior `status` OR-chain would spuriously match the trailing JSON `{"status":...}` line). **Re-review: CONFIRMED.**

### Blocking Issue 2 (borderline) — modular-plan exclusion glue untested
Task 3's manifest-modules reading (Step 3b) — resolving module plan files via `<git_root>/<feature_dir>/<module.file>` — had zero test coverage; the `run_pre_completion` test helper passes neither `--manifest` nor `--additional-plan-files`. This is the bug class that previously bit `_load_manifest_config` (missing feature_dir join). The reviewer accepted "a test passing a manifest with modules OR `--additional-plan-files`" as sufficient.

**Resolution:** added `test_declared_minimum_across_module_files` to Task 3 using `--additional-plan-files` (a real argparse arg — controller-checkpoint.py:1218, `nargs="+"`), which feeds the same `all_plan_contents` path Step 3b feeds. The test genuinely distinguishes the cross-file scan (without it, 3/4 quality reviews are minimum → block; with it, only task 0 counts → PASS). Task 9 additionally extends the e2e integration test to cover the manifest auto-resolution branch (the path-resolution glue) at the integration layer. Task 3 also now documents the raw-`yaml.safe_load`-vs-Pydantic-`Plan`-model parse choice (intentional divergence from spec:171, for graceful degradation). **Re-review: CONFIRMED.**

---

## Pass 2 — Approved

Both fixes CONFIRMED. The reviewer independently re-verified the `validate-report.py` banner/field line numbers and confirmed `--additional-plan-files` is registered argparse (so the modular test produces real output and the assertion is non-vacuous). Task IDs run cleanly 1–9 (module-1: 1–4, module-2: 5–9); no step-number or renamed-symbol breakage from the edits.

### Minor items found in pass 2 (both fixed)
- **Cosmetic off-by-one:** parent File Map prose read "Tasks 5-8" for module-2; corrected to "Tasks 5-9" (frontmatter `task_ids` and the dependency diagram were already correct).
- **Test hardening:** added `assert r.stdout.strip()` to the multi-file test to prove the checkpoint ran (guards against future silent argparse breakage). *Note:* the reviewer suggested `assert r.returncode == 0`, but that would be wrong here — pre-completion correctly exits non-zero on the unrelated missing honesty/trace checks; `assert r.stdout.strip()` is the correct robustness check.

---

## Accepted Deviation (documented, non-blocking)

**Module-1 Task 3 is ~220 plan-lines, over the advisory 200-line guideline.** `validate-plan.py` reports this as a WARNING (exit 2), which does **not** block the plan-validation gate — only FAILs (exit 1) do. Task 3 is a single atomic refactor: renaming `_count_review_tiers` → `_review_tiers_per_task` breaks its two callers immediately, so the function change, the declared-minimum helpers, the ratio rewrite, and their tests must land together — splitting would create a broken intermediate. It also now carries the reviewer-required multi-file test. Logged per the architectural principle's allowance for advisory gate warnings ("satisfy structurally where sensible + record the rationale"); the reviewer explicitly treated this as accepted and did not block on it.

## Final Status

**APPROVED.** All `validate-plan.py` checks PASS (no FAIL/blockers); the only residual is the documented Task 3 size WARNING. Plan is ready for execution.
