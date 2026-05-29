---
schema_version: 1
task_id: 7
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
    description: "Removed all dead legacy branches past the line-125 manifest guard (where MANIFEST_MODE is always true): collapsed always-true MANIFEST_MODE wrappers and deleted unreachable 'else # Legacy mode' branches in the sentinel check, Check 2 (audit), Check 4c (provenance), Check 5 (Source Contracts, deleted PLAN_SEARCH_GLOB loop), Check 5c/5d, Check 6 (token est, deleted SEARCHED_DIRS glob + rewrote diagnostic to reference manifest plan/module), Check 6b (deleted ~40-line legacy midpoint block), Check 7 (manifest plan+module sizing loop), and the output process-requirements wrapper. Updated stale top-of-file comment. +47/-145."
tests:
  written: 0
  passing: 0
  command: ".venv/bin/python3 -m pytest tests/unit/ -q  (full suite 350 passed, 0 failures — unchanged baseline; pure dead-code removal)"
  result: PASS
contract_compliance:
  - constraint: "No change to manifest-mode enforcement BEHAVIOR — only remove dead legacy alternative + de-indent"
    status: compliant
    detail: "Full suite 350 identical to pre-Task-7; every check still gates as before."
  - constraint: "MANIFEST_MODE=false appears only at declaration + guard"
    status: compliant
    detail: "3 legitimate refs: decl (71), =true assignment (104), guard (125). No dead wrappers remain."
  - constraint: "Residual-legacy grep clean"
    status: compliant
    detail: "No Legacy mode / feat_path / PLAN_SEARCH_GLOB / SEARCHED_DIRS matches."
---

**Implementation Summary:**
Removed all dead legacy branches in `sdd-pre-dispatch-hook.sh` past the line-125 manifest guard (where MANIFEST_MODE is unconditionally true). Each `if [ "$MANIFEST_MODE" = true ]` wrapper collapsed (identity transform); each `else # Legacy mode` branch deleted. Commit `be50eee` (+47/-145, net -98). Implemented by a dispatched subagent (this dispatch succeeded after the API recovered). Controller-verified: bash -n OK; residual-legacy grep CLEAN; MANIFEST_MODE refs = exactly 3 (decl/assign/guard); full suite 350 passed, 0 failures (identical to pre-Task-7 — behavior unchanged).

**Source Files Read:**
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (full; focus 240-760 where checks live; manifest-resolution block ~100-121 sets MANIFEST_PLAN_FILE/MANIFEST_MODULE_FILE/FEAT/MANIFEST/DISPATCH_LOG).

**CLAUDE.md Files Read:**
- skills/subagent-driven-development/scripts/: no CLAUDE.md. Bash set -u handled.

**Deviations from Plan:**
- None. The implementer (advisor-assisted) correctly identified that Check 4's N-1 skip conditional at ~line 354 is a LIVE both-branches conditional (gated on TASK_START), not a dead branch — removed only the redundant `MANIFEST_MODE = true` conjunct, kept both branches. Correct call.

**Self-Review Findings:**
- All NEED_*/PR_* init-block vars retain assignment+read references; FEAT still used (module-file reconstruction). No orphaned vars.

**Concerns:**
- Check 7 (Target 8) is the only genuine rewrite vs pure collapse: it previously summed `$FEAT/*.md` (all feature .md files), now sums only MANIFEST_PLAN_FILE + MANIFEST_MODULE_FILE — this was task-mandated (plan Step 1.7 specified the exact loop), NOT MANIFEST_MODE-gated before. Check 7 only injects a non-blocking CONTEXT_LOAD_WARNING into additionalContext (never ERRORS/exit 2), so gating is unchanged; the byte total narrowed slightly so the soft warning fires marginally less often. Flagged so a diff-skimmer doesn't mistake it for an unintended live-mode change.
