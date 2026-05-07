---
schema_version: 1
task_id: 4
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
    description: "Added .active-feature preamble, feat_path() helper, resolved all ~30 artifact path refs, updated error messages and additionalContext"
tests:
  written: 0
  passing: 0
  command: "echo JSON | bash hook.sh (smoke test: non-SDD exit 0)"
  result: PASS
contract_compliance:
  - constraint: ".active-feature is single-line plaintext, gitignored, contains relative path"
    status: compliant
    detail: "Hook reads .active-feature via cat, strips trailing newline/slash"
  - constraint: "Hooks fall back to root-level paths when FEAT is empty"
    status: compliant
    detail: "Fallback checks for uppercase DEVIATIONS.md and root reports/ when FEAT empty"
  - constraint: "deviations.md is lowercase"
    status: compliant
    detail: "Default DEVIATIONS_FILE is lowercase; fallback checks for old uppercase name"
---

**Implementation Summary:**
Migrated all ~30 hardcoded artifact path references in sdd-pre-dispatch-hook.sh to use resolved variables from `.active-feature`. Added feat_path() helper, DEVIATIONS_FILE/REPORTS_DIR/DISPATCH_LOG resolved variables, and backwards-compat fallback for root-level paths. Updated Checks 1-7, reviewer dispatch logging, and SDD REMINDER additionalContext. Committed at `7ce3366`.

**Source Files Read:**
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — full file (574 lines)
- `tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh` — POC pattern reference

**Deviations from Plan:**
1. Added trailing-slash strip (`tr -d '\n' | sed 's|/$||'`) to .active-feature reader — not in plan but prevents double-slash paths when the file has a trailing slash.
2. Two error message strings at lines 198 and 397 still contain hardcoded `reports/` and `DEVIATIONS.md` as informational text (the actual path checks use resolved variables). These are acceptable — they describe what was found, not the paths to check.

**Self-Review Findings:**
Grep audit confirmed no remaining hardcoded path references used for actual file operations. Two informational error messages retained old strings (see Deviations).

**Concerns:**
The trailing-slash strip is a defensive addition not in the plan. It prevents a common user error (writing `docs/imp-plans/2026-05-02-feature/` with trailing slash) from producing broken paths. If the plan intended `.active-feature` to never have a trailing slash, this is unnecessary but harmless.
