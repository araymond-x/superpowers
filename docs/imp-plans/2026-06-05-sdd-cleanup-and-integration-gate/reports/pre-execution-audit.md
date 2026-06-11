# Pre-Execution Audit Report

**Feature:** sdd-cleanup-and-integration-gate
**Date:** 2026-06-07
**Auditor:** Claude Opus 4.6 (pre-execution auditor role)
**Verdict:** ORDERS_ISSUED

---

## Remediation Orders

| # | Finding | Severity | What Must Be Fixed | Definition of Done |
|---|---------|----------|-------------------|-------------------|
| 1 | C2 Check 10 primary merge-base diff path has zero unit coverage | BLOCKING | Task 10 fixtures all run in a single-commit `git init` repo where `merge-base == HEAD`. This means every test exercises only the fallback path (`git diff HEAD` / untracked working-tree set). The **primary** path — `git diff --name-only <merge_base> -- <path>` where `merge_base != HEAD` (a file committed on a feature branch, working tree clean) — is untested. This path is exactly what runs when this feature gates its own completion: `sdd-e2e-test.sh` is committed in Task 11, so at pre-completion the working tree is clean for it and detection relies entirely on the merge-base diff. | Add a 7th fixture to Task 10 that: (a) creates a base commit on a `main` branch, (b) creates a feature branch, (c) commits the integration test file on the branch, (d) leaves the working tree clean, and (e) asserts Check 10 PASS. Verify it would FAIL if `_in_changeset` used `<base>..HEAD` instead of `git diff <merge_base> -- <path>`. |
| 2 | Task 2 Step 5 retrofit of `all_plan_contents` is underspecified — risks multi-module double-count | BLOCKING | `_load_manifest_config` (L1010) rewrites `args.plan_file` to the **active module** file (L595-598). `plan_content = read_file(args.plan_file)` at L1040 then reads the active module. The seed `all_plan_contents = [plan_content]` contains the active module. If `_load_all_plan_contents(manifest)` returns parent + all modules (including the active one), and the retrofit either (a) extends the seed with `_load_all_plan_contents` results, or (b) replaces the seed but keeps the L1040 read for single-file fallback, the active module gets double-counted. This skews `count_tasks` / checkbox aggregation (L1084-1089) and Check 8's verification ratio. The plan says "replace" but does not specify: should `all_plan_contents` be set to `_load_all_plan_contents(...)` exclusively (discarding the seed)? What is the no-manifest fallback? | Amend Task 2 Step 5 to state explicitly: (1) When manifest is present, `all_plan_contents = _load_all_plan_contents(manifest_data, git_root)` — full replacement, NOT extend. (2) When manifest is absent, `all_plan_contents = [plan_content]` — unchanged from current single-file behavior. (3) The `_load_all_plan_contents` helper already de-duplicates by `os.path.realpath`, so the active module appears exactly once. Remove the L1046 seed and the L1057-1068 ad-hoc block in the manifest case. |
| 3 | Task 10 Step 4 mis-frames integration_test extraction as "`_task_ids_where` pattern" | IMPORTANT | Step 4 says aggregate `integration_test.path` "same pattern as `_task_ids_where`." But `integration_test` is a **top-level** frontmatter field; `_task_ids_where` walks `fm["tasks"][]`. An implementer reusing that helper would find nothing. | Correct Task 10 Step 4 instruction: write a top-level extractor (`fm.get("integration_test", {}).get("path")` or equivalent) over the results of `_load_all_plan_contents`, not the task-level `_task_ids_where` helper. The helper to reuse is `_load_all_plan_contents` for aggregation + raw YAML parsing for the top-level field. |
| 4 | Task 3 Step 1/Step 3 conflict on whether `get_task_checkbox_range` unfences internally or receives pre-unfenced content | IMPORTANT | Step 1 test calls `get_task_checkbox_range(plan, 1)` with **raw fenced content** and expects the function to ignore fenced checkboxes. Step 3 says "pass the **entire** unfenced content to the function" (caller-side unfencing). These are contradictory. If the implementer follows Step 3, the test assertion is wrong (caller passes unfenced, function receives already-clean content). If they follow Step 1, Step 3's instruction is wrong. | Clarify: the function should unfence internally (apply `_unfenced_content` inside the function body, not at the call site). This matches the Step 1 test fixture which passes raw content. Update Step 3 item (4) to say "apply `_unfenced_content` inside `get_task_checkbox_range`" rather than "pass the entire unfenced content to the function." |
| 5 | Task 1 Step 6 assumes SDD SKILL.md is under 5000 words; actual count is 4904 — headroom is 96 words | IMPORTANT | The SDD SKILL.md is at 4904 words. Task 1 Step 6 adds verification emit guidance. CLAUDE.md documents this file as having a 5000-word hard limit with a rule that additions must be offset by extraction. 96 words of headroom is tight for a prose addition. If the addition exceeds ~96 words, it will breach the limit and `validate-all-skills.py` will issue a WARNING or FAIL. | Before implementing Step 6, measure the planned addition's word count. If it exceeds 96 words, extract an equivalent amount of existing content to `references/` first. Alternatively, keep the addition to a single sentence (e.g., "Set `task_type: verification` in your report frontmatter.") which is well within budget. Pre-log an accepted deviation if the resulting count is 4950-5000 (approaching limit). |

---

## Self-Assessment Review

### Shortcuts admitted
- **"Test stubs have intentionally sparse stubs to let the implementer follow existing test patterns"** (Tasks 5, 6, 7) — Impact: LOW. This is deliberate and correct for these tasks. The pattern reference files are well-specified, and the stub + pattern approach is the standard SDD pattern.

### Uncertainties flagged
- **"File-write serialization: Tasks 2/3/4 all modify controller-checkpoint.py — order matters."** — RESOLVED by plan: dependency chain Task 2 -> Task 3 -> Task 4 enforces ordering. No issue.
- **"`_H` variable pattern for self-hosting"** — RESOLVED and correct. The `_H = "##" + "# Task"` concatenation prevents the literal `### Task <digit>` from appearing in plan files. Implementers are warned.

### Concerns raised
- **"Self-hosting hazard (N7): pre-execution checkpoint FAILs on Source Contracts: None"** — Investigated. The N7 deviation was pre-logged during SDD ingestion per the spec's self-hosting section. Correct handling.
- **"Self-hosting hazard (N5): fence-blind validate-plan.py"** — Investigated. Plan files correctly use `_H` pattern and avoid fenced task-header examples. No risk.

---

## Cross-Reference Findings

### Items the controller did NOT flag

1. **The parent plan is never loaded by the current ad-hoc block (L1057-1068).** The spec explicitly requires `_load_all_plan_contents` to read parent + modules. The current code only loads module files. This is actually the N9 bug being fixed, but the controller did not flag the subtlety of the seed/replacement during retrofit. (Covered by Order #2.)

2. **The `all_tasks_have_reports` function at L506 is an 8th fence-affected site.** The spec says "7 sites" and lists only 7, but `all_tasks_have_reports` at L506 uses `TASK_HEADER_PATTERN.findall(plan_content)` to extract task numbers. A fenced `### Task 99` would add a phantom task number, causing a spurious "missing report" FAIL. However, this site is only used in `run_pre_completion` where `combined_plan_content` is constructed from `all_plan_contents`, and plan files don't typically contain fenced task headers (that's a code-snippet-in-plan scenario). The self-hosting guard (`_H` pattern) already prevents this in practice. **Not blocking** — the 7 sites listed in the spec are the critical ones, and this 8th site has the same defense. But the implementer of Task 3 should consider applying `_unfenced_content` here too for completeness. Note this as an IMPORTANT suggestion to the implementer, not a remediation order.

3. **Task 4's test fixture (N7) creates an `argparse.Namespace` with `manifest=None` to call `run_pre_execution`.** Verified: `_load_manifest_config` returns `(None, None)` when `args.manifest` is falsy (L560). Existing tests already exercise this path. No issue.

4. **`_load_manifest_config` mutates `args.plan_file` as a side effect.** This side effect is what makes Order #2 load-bearing — a manifest-mode `run_pre_completion` call reads the *active module* as `plan_content`, not the parent. The `_load_all_plan_contents` helper must account for this by independently resolving the parent plan from the manifest's `plan_file` field, not from `args.plan_file`.

---

## Verdict Rationale

**ORDERS_ISSUED.** The plans are well-grounded, line-number-accurate against the actual source code, and structurally sound. However, two coverage gaps (Orders #1 and #2) affect paths that the feature's own self-hosting verification depends on — Check 10's merge-base diff is how this feature proves its own integration test exists, and the `all_plan_contents` seed is how every pre-completion check aggregates across modules. Both must be resolved before their respective tasks dispatch. Orders #3-#5 are plan-text clarifications that prevent implementer thrash.

All five orders must be RESOLVED and documented before implementation begins.

---

## Remediation Resolutions

### Order 1: RESOLVED — C2 Check 10 merge-base fixture
**Resolution:** Controller will inject a 7th fixture requirement into the Task 10 implementer dispatch. The fixture creates a `main` branch with a base commit, creates a feature branch, commits the integration test file, and asserts Check 10 PASS with a clean working tree. This exercises the primary `git diff --name-only <merge_base> -- <path>` path.
**Status:** RESOLVED — injected into implementer dispatch context.

### Order 2: RESOLVED — Task 2 Step 5 all_plan_contents replacement
**Resolution:** Controller will inject the following clarification into the Task 2 implementer dispatch:
- When manifest is present: `all_plan_contents = _load_all_plan_contents(manifest_data, git_root)` — FULL REPLACEMENT, not extend. Remove the L1046 seed and the L1057-1068 ad-hoc block entirely.
- When manifest is absent: `all_plan_contents = [plan_content]` — unchanged single-file fallback.
- `_load_all_plan_contents` already de-duplicates by `os.path.realpath`.
**Status:** RESOLVED — injected into implementer dispatch context.

### Order 3: RESOLVED — Task 10 integration_test extraction pattern
**Resolution:** Controller will clarify in the Task 10 dispatch that `integration_test` is a top-level frontmatter field, NOT a per-task field. The extraction should use `fm.get("integration_test", {}).get("path")` over YAML-parsed `_load_all_plan_contents` results, not `_task_ids_where`. The helper to reuse is `_load_all_plan_contents` for aggregation.
**Status:** RESOLVED — injected into implementer dispatch context.

### Order 4: RESOLVED — Task 3 get_task_checkbox_range unfencing
**Resolution:** Controller will clarify in the Task 3 dispatch: `get_task_checkbox_range` should unfence INTERNALLY (apply `_unfenced_content` inside the function body), matching the Step 1 test which passes raw content. The Step 3 instruction "pass the entire unfenced content" is corrected to "apply `_unfenced_content` inside `get_task_checkbox_range`."
**Status:** RESOLVED — injected into implementer dispatch context.

### Order 5: RESOLVED — Task 1 SDD SKILL.md word count headroom
**Resolution:** The Step 6 addition will be kept to a single sentence: "Set `task_type: verification` in your report frontmatter." This is well within the 96-word headroom. Implementer will verify with `wc -w` after editing.
**Status:** RESOLVED — injected into implementer dispatch context.

### Auditor Cross-Reference Note (non-order)
The auditor noted an 8th fence-affected site (`all_tasks_have_reports` at L506). Controller will include this as a suggestion in the Task 3 implementer dispatch for completeness.

**All 5 orders RESOLVED. Proceeding to task loop.**
