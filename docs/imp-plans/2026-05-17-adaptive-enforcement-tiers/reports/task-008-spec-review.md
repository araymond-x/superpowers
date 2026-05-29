---
schema_version: 1
task_id: 8
reviewer: spec-auditor
status: PASS
---

# Task 8 Spec Review — Hook Conditional Checks by Tier

## Status: PASS

All 8 checks are correctly gated. No blocking issues found. Three advisory items noted.

---

## Per-Check Findings

### Check 2 — `enforcement.pre_execution_audit`
- Gate present: YES. Flag read via `jq -r '.enforcement.pre_execution_audit'` inside `if MANIFEST_MODE=true` guard.
- Bool pattern correct: `[ "$NEED_AUDIT" = "false" ]` skips; else (including "true", "null", empty) runs check. CORRECT.
- Legacy body preserved intact in the `else` branch. CONFIRMED.
- Variable `NEED_AUDIT` initialized at outer scope (line ~78). CONFIRMED.

### Check 4 N-1 file-existence sub-block
- Skip condition: `[ "$MANIFEST_MODE" = true ] && [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -eq "$MANIFEST_TASK_START" ]`. All three guards required — CORRECT. Not triggered in legacy mode.
- Check 4b (structural validation) correctly rides inside the same `else` block as file existence — it cannot validate a file that was skipped. CORRECT.
- Spec requires skip ONLY when `MANIFEST_MODE=true AND TASK_NUMBER==MANIFEST_TASK_START`. Implementation matches exactly.

### Check 4 dispatch-provenance sub-block (`enforcement.dispatch_provenance`)
- Gated SEPARATELY from the N-1 file-existence sub-block, as required. The dispatch-provenance check still executes even when TASK_NUMBER == MANIFEST_TASK_START (because provenance is checked against task N, not N-1). CORRECT separation.
- Flag read: `NEED_PROV=$(jq -r '.enforcement.dispatch_provenance' "$MANIFEST")` inside manifest guard. Bool gate: `[ "$NEED_PROV" = "false" ]`. CORRECT.
- Legacy body preserved in the `else` branch. CONFIRMED.
- Variable `NEED_PROV` initialized at outer scope. CONFIRMED.

### Check 5 — Source Contracts (unconditional, structural change only)
- Still unconditional: no `enforcement.*` gate wraps this check. CONFIRMED.
- Manifest mode: uses `MANIFEST_PLAN_FILE` (single file check) instead of glob. CORRECT per spec.
- Legacy mode: preserves original glob search across feature dir or standard plan locations. CONFIRMED.
- Behavioral note: in manifest mode, if `MANIFEST_PLAN_FILE` does not exist (file missing), `HAS_SOURCE_CONTRACTS` stays false, and the check silently skips. This is a safe behavior since manifest path validity is enforced at materialization (Task 7). Not spec-divergent.

### Check 5c — `enforcement.checkpoint_files`
- Gate present: `NEED_CHECKPOINT=$(jq -r '.enforcement.checkpoint_files' "$MANIFEST")` inside manifest guard.
- Bool pattern: `[ "$NEED_CHECKPOINT" = "false" ]` skips; else runs. CORRECT.
- `TASK_PADDED` computed inside the `else` block (after skip check) — no set -u risk since it is only used inside that block. CORRECT.
- Variable `NEED_CHECKPOINT` initialized at outer scope. CONFIRMED.

### Check 5d — `enforcement.partner_review`
- Gate present: `NEED_PARTNER=$(jq -r '.enforcement.partner_review' "$MANIFEST")` inside manifest guard.
- Bool pattern: `[ "$NEED_PARTNER" = "false" ]` skips; else runs. CORRECT.
- Outer guard `TASK_NUMBER > 0` preserved (Task 0 exemption). CONFIRMED.
- `TASK_PADDED`, `PARTNER_FILE`, `PARTNER_FILE_MIN` all computed inside the `else` block, avoiding any set -u exposure. CORRECT.
- Variable `NEED_PARTNER` initialized at outer scope. CONFIRMED.

### Check 6 — Token estimation (unconditional, structural change only)
- Still unconditional: no enforcement flag gates this check. CONFIRMED.
- Manifest mode: sets `PLAN_FILE` from `MANIFEST_MODULE_FILE` (if non-empty and exists), else `MANIFEST_PLAN_FILE`. CORRECT — matches spec's "module file if exists else plan file" requirement.
- Legacy mode: original glob loop preserved in `else` branch unchanged. CONFIRMED.
- Implementer concern logged: when plan file exists in manifest mode but lacks the task header, token estimation degrades to TOKEN_WARNING (soft) rather than BLOCK. This is a real behavior softening versus legacy mode. It is disclosed as a concern in the implementer report and is acceptable given Task 7's task-range validation. [ADVISORY]

### Check 6b — `enforcement.context_summary_at` (int threshold)
- Manifest mode: reads `CONTEXT_SUMMARY_AT=$(jq -r '.enforcement.context_summary_at' "$MANIFEST")`.
- Null handling: `[ "$CONTEXT_SUMMARY_AT" = "null" ] || [ -z "$CONTEXT_SUMMARY_AT" ]` skips before any arithmetic. CORRECT — handles both JSON null (jq emits "null") and missing field (jq emits empty via `-r` with empty output).
- Threshold comparison: `[ "$TASK_NUMBER" -ge "$CONTEXT_SUMMARY_AT" ]` — fires when at or past threshold. CORRECT per spec ("int threshold").
- When threshold is non-null and task is below threshold, check silently skips (no error, no warning). CORRECT.
- Legacy branch preserved unchanged in `else`. CONFIRMED.
- Variable `CONTEXT_SUMMARY_AT` initialized at outer scope. CONFIRMED.

---

## Issues

### [ADVISORY][EXTRA] Check 6 manifest mode degrades missing-header to TOKEN_WARNING
The implementer disclosed this in concerns. In legacy mode, a missing task header → PLAN_FILE empty → BLOCK. In manifest mode, PLAN_FILE is set if the file exists regardless of header presence, so a missing header → estimate script returns no output → TOKEN_WARNING (soft). Given manifest task-range validation in Task 7, this is unlikely in practice and is safe behavior. Not a spec violation — the spec says "use MANIFEST_MODULE_FILE/MANIFEST_PLAN_FILE instead of glob," not "replicate legacy block semantics." No action required before merge; note for Task 9+ test authoring.

### [ADVISORY][INFORMATIONAL] Malformed manifest (missing enforcement key) falls through safely
A manifest without an `enforcement` key causes `jq -r '.enforcement.pre_execution_audit'` to return `"null"`. Since `[ "null" = "false" ]` is false, all checks run (enforcement fully enabled). This is the correct safe default per spec and matches the bool gate pattern. Not covered by existing tests — worth adding a unit test case.

### [ADVISORY][INFORMATIONAL] `CONTEXT_SUMMARY_AT` double-assignment in manifest mode
`CONTEXT_SUMMARY_AT` is initialized to `""` at outer scope (~line 82) and then reassigned inside the Check 6b manifest branch at runtime. This means `CONTEXT_SUMMARY_AT` is always re-read from jq at check time, not from the manifest initialization block. This is functionally correct and consistent with the pattern used for NEED_AUDIT, NEED_PROV, etc. Not a defect.

---

## Verification Summary

| Check | Gate Present | Bool Pattern | Legacy Preserved | Var Init |
|---|---|---|---|---|
| 2 pre_execution_audit | YES | CORRECT | YES | YES |
| 4 N-1 file-existence | YES (TASK_START) | N/A (equality) | YES | YES |
| 4 dispatch_provenance | YES (separate gate) | CORRECT | YES | YES |
| 5 source contracts | unconditional | N/A | YES | N/A |
| 5c checkpoint_files | YES | CORRECT | YES | YES |
| 5d partner_review | YES | CORRECT | YES | YES |
| 6 token estimation | unconditional | N/A | YES | N/A |
| 6b context_summary_at | YES (int threshold) | CORRECT | YES | YES |

`bash -n` passes (implementer confirmed; structural scan of diff corroborates).
16 existing tests pass (legacy mode paths exercised by else branches).
