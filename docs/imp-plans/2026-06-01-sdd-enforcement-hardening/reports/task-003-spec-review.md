# Spec Review: Task 3 — transition-module.py provenance + verification exemption (N3b) + N11

## Verdict: PASS

All 7 checklist items verified against primary evidence (code read + mutation test + tier introspection + cross-reference vs the hook writer/reader). Commit 004ba75 (parent fe52b67). Full unit suite: 401 passed.

### Checklist (all PASS)
1. **Helpers:** `_has_dispatch_provenance` (:38-50) needle EXACTLY `task={task_id} type={review_type}` — byte-matches the hook writer (`sdd-pre-dispatch-hook.sh:161`) and reader (Check 4c). `_verification_task_ids_from_file` (:53-84) mirrors `controller-checkpoint.py:_verification_task_ids` (same frontmatter parse + filter).
2. **validate_module_completion:** impl-report kept; `verif_ids` `continue` (:120-121) BEFORE spec/quality; spec provenance via `_has_dispatch_provenance` when mode≠skip; quality provenance UNLESS minimum-tier FILE (`has_min`→pass); `!= "skip"` gating preserved; verif_ids read from the COMPLETING module's `module.file`.
3. **N11:** recompute immediately after `data["midpoint"]=compute_midpoint(...)`, guarded by `context_summary_at is not None`, set to `data["midpoint"]`; midpoint line unchanged. `compute_midpoint(4,7)==6` verified.
4. **Minimum-signal:** keys on the FILE `task-NNN-quality-review-minimum-tier.md`, not `review_tier:minimum`. Mirrors the hook waiver.
5. **Tests:** 3 new tests present + correct; `create_task_reports` writes provenance; N11 seed is a FRESH dict (verified NOT mutating TIER_PROFILES — standard default is None, so the seed is load-bearing); `== 6` assertion on `test_manifest_updated_after_transition`. The strengthened `test_blocks_when_provenance_missing` (2 assertions) was MUTATION-TESTED: deleting the quality `elif` fails only the quality assertion → genuine discrimination. 10 transition tests pass; full suite 401.
6. **N3a comment now accurate:** validate_module_completion verifies provenance at Step 1 (live log intact; truncation is Step 5), so Task 2's `sdd-pre-dispatch-hook.sh` comment is now true.
7. **Report completeness:** validates COMPLETE; all sections substantive.

### Findings (ADVISORY — none blocking Task 3)
- **[SCOPE] Integration suite RED at HEAD — BY DESIGN, pending Task 5.** e2e Step 4 doesn't write dispatch-log provenance, so after N3b the transition validation correctly fires `INCOMPLETE: Task 0: spec review not provenance-logged` (exit 1). Plan explicitly sequences this (plan:106 "Step 4 transition breaks without provenance after N3b lands"; Task 5 adds the provenance). Task 3 is compliant; **the e2e cannot go green until Task 5 lands** — a PASS here is NOT "all suites green."
- **[FOLLOW-UP] Transition gate (`!= "skip"`) vs hook gate (`enforcement.dispatch_provenance`) can diverge for micro+modules.** standard: both enforce (agree). micro: `dispatch_provenance=False` but modes=`self_review` (≠skip) → transition would require provenance the hook never wrote (over-enforcement). Reachable only in micro+modules (which `validate-plan.py` already warns against). Task 3 is spec-compliant (spec MANDATED `!= "skip"`; gating on dispatch_provenance would have diverged from spec). Tracked as a follow-up (align the transition gate with `enforcement.dispatch_provenance`, or document the intent) — see deviations.md / BACKLOG (Task 6).
- **[NOTE] Commit-hash discrepancy:** report body cites `8af32fe`/128 insertions; HEAD is `004ba75`/131 (orphaned pre-amend hash; implementer amended for a docstring reflow). History linear + clean; reviewed artifact verified directly. Benign.
- **[NOTE] `module.file` truthiness guard** — defensive only (`ModuleState.file` is required). Acceptable.

No [BLOCKING] issues. The two additive deviations (strengthened test, RED-count note) are sound.
