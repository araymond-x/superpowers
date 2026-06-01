# Plan Review Report — SDD Enforcement Hardening

**Plan:** `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md`
**Spec:** `spec-distilled.md` (full design: `spec.md`)
**Reviewer:** plan-document-reviewer (general-purpose), two passes (initial + confirmation)
**Final status:** ✅ **APPROVED**

The reviewer read the four production scripts, the test helpers, the transition test harness, the e2e, and the Pydantic Plan model independently; grepped 24,656 real Claude Code transcript lines; and ran the actual hook against a replica of the e2e Step 7b workspace.

---

## Pass 1 — Initial Review: Issues Found (2 blocking, both test-code, both one-line)

### Blocking Issue 1 — Task 0 `_transcript` helper used spaced JSON
Real Claude Code transcripts use the **compact** form `"role":"user"` (24,656 occurrences; 0 spaced). The hook's outer guard (`sdd-skill-enforcement-hook.sh:54`) greps for the compact literal. The plan's `_transcript` used `json.dumps(...)` default spacing (`"role": "user"`), which the grep would not match — so the hook short-circuits at its early `exit 0` and `test_blocks_when_sdd_requested_skill_not_loaded` + `test_bypass_env_var_recovers` could never reach GREEN. The hook is correct; the test helper was the defect. **Fix:** emit compact JSON (`separators=(",", ":")`). Isolated to Task 0 (pre-dispatch/SSOT tests use `make_hook_input`+jq, unaffected).

### Blocking Issue 2 — e2e Step 7b omitted a `context-summary.md` stub
`materialize-manifest.py` sets `enforcement.context_summary_at=1` for module-1 (`task_range [0,1]`), and `transition-module.py` Step 4 never recomputes it on transition — so post-transition it stays `1`. Hook Check 6b (`TASK_NUMBER=2 > 1` and `2 >= 1`) then BLOCKS unless `reports/context-summary.md` exists. Verified by running the hook against an exact Step-7b replica (`BLOCKED: Context summary required at task 1 threshold`, exit 2). The unit test `test_check4c_skipped_for_module_first_task` is NOT affected (its `task_range=(2,3)` computes `context_summary_at=3`). **Fix (in-scope):** add a `context-summary.md` stub to Step 7b. **Root cause:** new gap → BACKLOG N11 (out of scope; recompute `context_summary_at` in `transition-module.py` Step 4).

### Snippet Verification (Pass 1)
- **Check 4c skip-guard `elif [ "$PREV" -lt "$MANIFEST_TASK_START" ]`** — VERIFIED. Real chain (`sdd-pre-dispatch-hook.sh:500–536`) is `if NEED_PROV / elif PREV_TASK_TYPE==verification / else`; new `elif` slots in as a third sibling. `PREV=$((TASK_NUMBER-1))` (line 413), `MANIFEST_TASK_START` (line 112) both in scope. Truth table holds.
- **`find_report_file`/`find_all_report_files` rewrites** — VERIFIED. Current code uses `sorted(matches)[-1]` / `sorted(glob.glob(...))`; archive glob added; live-wins semantics correct (`/archive-` sorts before `/task-`).
- **`validate_module_completion` rewrite** — VERIFIED. Preserves impl-report check + `pr.spec_review_mode`/`pr.quality_review_mode` gating; `_has_dispatch_provenance` needle `task={id} type={type}` matches the hook's writer format; minimum waiver keys on the FILE (`os.path.isfile(quality_min)`), not the declaration; verification exemption mirrors `_verification_task_ids`; `validate_module_completion` runs at Step 1 BEFORE the Step 5 truncation (live log intact).
- **Task 0 detection regex** — VERIFIED (modulo Issue 1's transcript fix). Replaces only the inner grep; preserves SKILL_LOADED allow, path filter, early exits.

### Cross-Document Audit (Pass 1) — all MATCH
`setup_manifest_workspace` keys (`root/feat_dir/reports_dir/manifest_path`); `make_hook_input(description=,prompt=,cwd=)`; `create_manifest`/`create_task_reports`/`run_transition` signatures; the N3b backward-compat breakage claim (TRUE — existing `create_task_reports` writes no provenance; plan correctly updates it + e2e Step 4); write-scope disjointness (`sdd-pre-dispatch-hook.sh` → Task 2 only; `test_transition_module.py` → Task 3 only); e2e banner update; frontmatter validity (`validators.py plan` exit 0, `validate-plan.py` PASS); intentionally-flat lookups all five named and untouched; Task 7 dogfooding (12.5% ≤ 30%; no commits in window).

---

## Pass 2 — Confirmation Review: APPROVED

**Blocking Issue 1 — RESOLVED.** Both `json.dumps` calls pass `separators=(",", ":")` (`plan.md:174–180`); emitted strings contain `"role":"user"` and `"name":"Skill"` matching the hook greps (lines 54/56/69); block tests can now reach GREEN.

**Blocking Issue 2 — RESOLVED.** Step 7b creates a non-empty `context-summary.md` in the manifest's `reports_dir` (`plan.md:923`; resolves to `$FEAT/reports`, matching `hook:108`/`hook:683`). The reviewer re-traced the hook control flow: Check 4/4b skip via `hook:420–421` (`TASK==MANIFEST_TASK_START`), so archived task-001 reports are correctly not required; Check 4c is gated *separately, outside* that block (`hook:495–536`), so pre-fix it greps the empty log for `task=1 type=spec-review` and is the **sole remaining BLOCK**; all other gates satisfied/inert (5 no-contracts, 5b clean deviations, 5c checkpoint-002, 5d partner-002+provenance, 6 header present, 6b context-summary stub). A `0` exit therefore **non-vacuously** proves the N3a skip-guard. N11 follow-up recorded (`plan.md:919–922` stub comment; `plan.md:974` BACKLOG row).

**No new blocking findings.** Non-blocking precision note (already correct in the plan): `hook:420`'s skip is pre-existing and covers Checks 4/4b; Task 2 adds the equivalent `PREV < MANIFEST_TASK_START` skip to Check 4c specifically (plan's Task 5 Context states this correctly).

---

## Post-approval additive edits (main-agent, after APPROVED — do not invalidate the verdict)
Two purely-additive refinements applied after the confirmation pass, per a final advisor review:
1. **Task 2** gained a 4th test `test_check4c_skipped_for_no_task0_single_module` (`task_range=(1,2)`, dispatch task 1, PREV=0<1) so acceptance criterion #3 (no-Task-0 single-module start=1) is verified directly, not only as a side-effect of the module-boundary scenario.
2. **Task 7** gained an explicit point-of-action note: Check 9 (git-reality) gives the last verification task an open-ended `--after` window, so no commits may occur at/after Task 7's dispatch (commit all of Task 6 first).
Both are additive (new test + clarifying prose); `validate-plan.py` and `validators.py plan` re-run PASS; no production-code snippet changed.

3. **N11 folded into Task 3 (user decision, 2026-06-02).** Per the user's choice, the reviewer's backlog candidate N11 was pulled into scope: `transition()` now recomputes `enforcement.context_summary_at` for the next module on transition (~3 lines, mirroring the existing `midpoint` recompute the reviewer itself pointed to). Verification is line-efficient — `create_manifest` seeds a non-None `context_summary_at` and one assertion is added to the existing `test_manifest_updated_after_transition`; the e2e Step 7b `context-summary.md` workaround stub was REMOVED (its removal + an explicit `context_summary_at == 3` assertion is now the integration proof of N11). Docs/BACKLOG (Task 6) flipped N11 from "open" to "done". This is the reviewer's own recommended alternative, narrowly scoped to the file Task 3 already owns (no write-scope change). Task 3 re-measured at ≤200 lines after offsetting trims; `validate-plan.py` PASS, `validators.py plan` PASS.

## Deterministic gate status
- `validate-plan.py`: **PASS** — 8 tasks, 0 blockers, 0 warnings.
- `validators.py plan` (Pydantic): **PASS** (exit 0) — sequential IDs 0–7, valid `depends_on`, declared `pattern_references`, valid `task_type`/`review_tier` literals.
