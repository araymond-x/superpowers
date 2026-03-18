# Plan Review Findings: Statement Reconciliation UI Design

**Date**: 2026-03-16 ~01:00 MST
**Source agent**: AWS-Explore agent (aws-explore project)
**Source repo**: `aws-explore` — `/Users/araymond/projects/aws-explore`
**Plan reviewed**: `docs/plans/2026-03-15-statement-reconciliation-ui-design.md` (v1.1 Approved)
**Handoff reviewed**: `docs/plans/2026-03-11-statement-parsing-handoff/README.md` (v3)
**Review checklist**: `statement-parsing-experiment/implementation-plan-review-checklist.md`

---

## Summary

The AWS-Explore agent performed an independent review of the statement reconciliation plan, focused on integration accuracy between the plan and the Bedrock experiment handoff package. 9 issues were identified across 4 root cause categories. All were resolved during the review session. This document captures the findings for process improvement.

---

## Findings by Root Cause Category

### Category 1: Cross-Document Drift (4 findings)

Issues where the plan and handoff package described the same concept inconsistently, creating ambiguity for the implementation agent who reads both.

| # | Finding | Severity | Root Cause | Resolution |
|---|---------|----------|------------|------------|
| 1 | **LOC-WF rate mapping contradicted between docs** — Plan (line 223) resolved `apr` → `cash_advance_apr` citing frontend evidence. Handoff README left it as "implementation must decide." | P1 | Plan resolved an open question but didn't update the handoff. Two documents pointed different directions. | Updated handoff README to close the open decision with the same `StatementEditForm.tsx:51` citation. Committed as `12210fa`. |
| 2 | **Gate severity reclassification undocumented** — Handoff gates 2 (balance checksum) and 3 (date range) were both "hard / reject." Plan reclassified them to "approval gate" and "soft warning" respectively — reasonable design evolution but never noted. | P2 | Plan evolved gate severities during design but didn't add a reconciliation note explaining the change from the handoff's definitions. | Other reviewing agent added explicit rationale note at plan line 557. |
| 3 | **Balance sign inversion absent from handoff** — Plan (line 203) said "sign-inverted for liability accounts" when populating balances. Handoff was completely silent on balance sign convention — it only covered transaction sign inversion. | P2 | The handoff describes what the model outputs. The plan describes what the system does with it. The transformation between those two was only in the plan author's head until the plan was written. | Other reviewing agent added explicit documentation to plan step 1 with formula rationale and reference to `docs/reconciliation/statement-reconciliation-process.md:226`. |
| 4 | **Rate field mapping owned by neither document** — Handoff listed extracted fields per schema. Plan listed DB columns. Neither document contained the complete extraction-to-column mapping table. | P2 | Mapping table fell between document boundaries. Handoff knew the "from" side, plan knew the "to" side, but the explicit connection was never written down. | Created the Extraction-to-Column Mapping section in the handoff README. Committed as `12210fa`. |

**Process improvement**: Added "Cross-Document Consistency Audit" section to `docs/plans/CLAUDE.md` plan authoring guidelines.

---

### Category 2: Internal Plan Inconsistency (2 findings)

Issues where the same concept was described differently in multiple locations within the plan itself.

| # | Finding | Severity | Root Cause | Resolution |
|---|---------|----------|------------|------------|
| 5 | **Exception name drift** — Plan line 535-541 (error table) listed `ModelTimeoutException`. Plan line 782 (error summary) listed `ServiceUnavailableException`. Same error case, different exception name. | P2 | Error contracts appeared in 3+ locations within the plan (error table, flow narrative, UI spec). When one was updated, the others weren't synchronized. | Identified — cleanup recommendation provided (replace `ServiceUnavailableException` with `ModelTimeoutException`, add missing `AccessDeniedException` and `ValidationException`, remove "malformed response"). |
| 6 | **Exception list incomplete** — Line 782 omitted `AccessDeniedException` and `ValidationException`, both of which are handled by the handoff's `extract_statement_safe()` and listed in the plan's own error table. | P3 | Same root as #5 — the summary line was written separately from the error table and wasn't verified against it. | Same resolution as #5. |

**Process improvement**: Added "Error/exception name drift" bullet to the Internal Consistency Audit section in `docs/plans/CLAUDE.md`.

---

### Category 3: Missing Transformation Documentation (1 finding)

Issues where a data transformation existed in the plan but wasn't traceable end-to-end.

| # | Finding | Severity | Root Cause | Resolution |
|---|---------|----------|------------|------------|
| 7 | **Balance sign inversion not end-to-end traceable** — The handoff extracts balances as positive strings (as printed on credit card statements). The DB stores them as negative (liability convention). The transformation was in the plan but not connected to the handoff's output format or the DB's storage convention. | P2 | The End-to-End Data Flow Trace in the review process didn't explicitly check for transformations between extraction and storage. | Other reviewing agent documented the full chain: what Haiku returns → negation for liabilities → why (`compute_balance_to_date()` formula) → where the convention is defined. |

**Process improvement**: Added step 5 to the End-to-End Data Flow Trace section in `docs/plans/CLAUDE.md` — explicitly check for transformations between extraction and storage.

---

### Category 4: Schema/Implementation Divergence (2 findings)

Issues where the implementation diverged from the handoff's schema design, causing runtime failures.

| # | Finding | Severity | Root Cause | Resolution |
|---|---------|----------|------------|------------|
| 8 | **Amount `type` changed from `string` to `number`** — The handoff schemas define all amount fields as `"type": "string"` with descriptions saying "commas preserved." An implementation agent apparently changed this to `"type": "number"`, causing Haiku to return comma-separated strings that failed Gate 4's format validation. | P1 | Implementation agent modified the schema type without understanding why it was `string` in the first place. The handoff's rationale (amounts are formatted strings parsed later) wasn't prominent enough. | Identified during review. Root cause investigation delegated to the implementation agent — need to confirm whether the schema was actually changed and restore to `"type": "string"` if so. |
| 9 | **Gate 4 parser strictness unspecified** — Plan didn't specify whether the matching algorithm's amount parser should be strict (expect clean numbers, fail on format noise) or lenient (strip `$`, commas, `CR`/`DR`). The handoff had both approaches: `validate_amount_format()` is strict, `_parse_amount()` is lenient. | P2 | Design decision was never made — the plan described what Gate 4 detects but not what the downstream parser expects. | Recommended strict parser + Gate 4 as hard gate. Rationale: Haiku with `toolChoice` has never produced format noise in 9 experiment runs. Fail fast on unexpected output rather than silently accepting garbage. |

**Process improvement**: Added "Handoff Package Maintenance" section to `docs/plans/CLAUDE.md` — handoff and plan must be consistent at approval time, and changes to either must be mirrored in the same commit.

---

## Recommendations Applied to Plan Authoring Guidelines

All four process improvements were drafted as additions to `docs/plans/CLAUDE.md`:

1. **Cross-Document Consistency Audit** (new section) — When a plan references external deliverables, verify shared concepts are consistent across the boundary.
2. **Error/exception name drift** (new bullet in Internal Consistency Audit) — Verify exception/error names match across all occurrences.
3. **Transformation tracing** (new step 5 in End-to-End Data Flow Trace) — Explicitly check for transformations between extraction and storage.
4. **Handoff Package Maintenance** (new section under File Management) — Both documents must be consistent at plan approval time.

Copy-pastable text for these additions was provided to the user in the review session. Application status: pending user action.

---

## Artifacts Modified During This Review

| File | Change | Commit |
|------|--------|--------|
| `docs/plans/2026-03-11-statement-parsing-handoff/README.md` | Added Extraction-to-Column Mapping section; closed LOC-WF open decision | `12210fa` |
| S3: `statements/staging/4/AMZN-VISA_02-05-2026.pdf` | Deleted (test artifact) | N/A |
| S3: `statements/staging/4/DELTA-AMEX_02-08-2026.pdf` | Deleted (test artifact) | N/A |
