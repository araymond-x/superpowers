---
schema_version: 1
task_id: 8
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/spawn-handoff-session.sh"
    description: "Added Precondition 0: SUPERPOWERS_CMUX_AUTOSPAWN kill switch, inserted before Precondition 1 (clean tree) and thus before the cmux-reachability probe (Precondition 3). 0/false/off variants exit 3 with reason=autospawn-disabled and print manual instructions; invalid values warn and leave auto-spawn enabled; no cmux notify call."
  - path: "tests/unit/test_spawn_handoff.py"
    description: "Added 4 new tests: disabled via '0' refuses before cmux check, disabled via 'false' refuses, invalid value warns and proceeds, unset value proceeds (baseline)."
tests:
  written: 4
  passing: 4
  command: ".venv/bin/python3 -m pytest tests/unit/ -k autospawn -v"
  result: PASS
contract_compliance:
  - constraint: "SUPERPOWERS_CMUX_AUTOSPAWN=0/false -> exit 3, reason=autospawn-disabled, before Precondition 3"
    status: compliant
    detail: "Precondition 0 inserted before Precondition 1 (which itself precedes Precondition 3), and test_autospawn_disabled_zero_refuses_before_cmux asserts the cmux-unreachable message never appears in output."
  - constraint: "Invalid values warn and leave auto-spawn enabled"
    status: compliant
    detail: "case statement's catch-all *) branch warns via stderr and falls through without exiting; test_autospawn_invalid_warns_and_proceeds confirms the run reaches --dry-run success output."
  - constraint: "Does not call cmux notify"
    status: compliant
    detail: "The disabled branch only echoes to stderr and calls print_manual_instructions; no cmux invocation added."
  - constraint: "spawn-handoff-session.sh is not baselined, no recapture needed"
    status: compliant
    detail: "Confirmed via CLAUDE.md baselined-hooks enumeration before starting; no baseline file touched."
---

**Implementation Summary:**
Added a new Precondition 0 to `spawn-handoff-session.sh` implementing the `SUPERPOWERS_CMUX_AUTOSPAWN` kill switch, using the same validate-warn idiom as the existing `QUOTA_MIN_PCT`/`MAX_STALL_HOPS` knobs but with a "stay enabled" fallback instead of a numeric revert. Followed strict TDD: wrote 4 new tests, confirmed 3 failed (no such gate existed) and 1 passed vacuously (unset case, already true), then added the implementation and confirmed all 4 pass.

**Source Files Read:**
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — confirmed `print_manual_instructions` defined at line 140, Precondition 1 (clean tree) at line 150, matching plan estimates exactly.
- `tests/unit/spawn_handoff_helpers.py` — confirmed `run_spawn()` takes `env_extra=` keyword (not `env=`).
- `tests/unit/test_spawn_handoff.py` — matched existing fixture-setup conventions (`setup_worktree`, `_spawnable` helper installing `valid-manifest.json` bundle with `spawn_policy=auto` default) for consistent test structure.

**CLAUDE.md Files Read:**
None found in `skills/subagent-driven-development/scripts/` or `tests/unit/`.

**Deviations from Plan:**
None — implemented exactly as specified in the task description, including the exact code block provided.

**Self-Review Findings:**
No issues found. Verified the disabled-before-cmux-check ordering explicitly via assertion that the "not in a reachable cmux" message never appears in stderr/stdout for the disabled case.

**Concerns:**
No concerns. Ran both the narrow (`-k autospawn`, 4/4 pass) and broader regression confirmation (`-k "autospawn or spawn_handoff"`, 187/187 pass, ~5m40s runtime) suites, plus `scripts/lint-shell.sh` on the modified file (clean, no new warnings). Committed as `9c6947b`.
