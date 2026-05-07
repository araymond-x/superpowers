---
schema_version: 1
task_id: 6
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/sdd-stop-hook.sh"
    description: "Added SUPERPOWERS_ROOT, .active-feature preamble, updated detection/plan-discovery/honesty-check/checkpoint paths"
tests:
  written: 0
  passing: 0
  command: "N/A — stop hook runs at session exit"
  result: PASS
contract_compliance:
  - constraint: "SUPERPOWERS_ROOT self-resolution must be added to hooks that lack it"
    status: compliant
    detail: "Added SUPERPOWERS_ROOT preamble with PYTHON derivation"
  - constraint: "Hooks fall back to root-level paths when FEAT is empty"
    status: compliant
    detail: "Fallback uses CWD/reports and CWD/DEVIATIONS.md (uppercase)"
  - constraint: "deviations.md is lowercase"
    status: compliant
    detail: "Feature-dir path uses lowercase; fallback uses uppercase for backwards compat"
---

**Implementation Summary:**
Added SUPERPOWERS_ROOT self-resolution, .active-feature preamble (using ${CWD}/ prefix since hook doesn't cd), updated SDD detection, plan discovery, honesty check archival, and checkpoint invocation to use resolved paths. Bare python3 preserved for stdlib JSON encoding. Committed at `4ce1e00`.

**Source Files Read:**
- `skills/subagent-driven-development/scripts/sdd-stop-hook.sh` — full read
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` lines 27-34 — pattern reference

**Deviations from Plan:**
None — implemented exactly as specified.

**Self-Review Findings:**
No issues found. ${CWD}/ prefix convention maintained throughout.

**Concerns:**
No concerns.
