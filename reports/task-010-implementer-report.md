---
schema_version: 1
task_id: 10
status: DONE
files_changed:
  - path: "skills/brainstorming/SKILL.md"
    description: "Added step 3.5 feature name prompt with conflict detection, updated spec output paths to <feature-dir>/"
  - path: "skills/writing-plans/SKILL.md"
    description: "Added step 0.5 feature name prompt, updated plan/manifest/review/module paths to <feature-dir>/"
  - path: "skills/handoff-acceptance/SKILL.md"
    description: "Added feature name prompt on ACCEPTED verdict"
tests:
  written: 0
  passing: 0
  command: "N/A — SKILL.md prose changes"
  result: PASS
contract_compliance:
  - constraint: "Feature name is kebab-case, user-confirmed at entry-point skill prompt"
    status: compliant
    detail: "All 3 entry-point skills now prompt for feature name"
  - constraint: "Conflict detection at entry: stale → auto-clean, completed → auto-clean, incomplete → prompt"
    status: compliant
    detail: "Full conflict detection matrix added to brainstorming, referenced from writing-plans"
---

**Implementation Summary:**
Updated all 3 entry-point skills with feature name prompt, conflict detection, and output path changes. brainstorming gets step 3.5 with full conflict detection. writing-plans gets step 0.5 and all 7 path references updated. handoff-acceptance gets ACCEPTED verdict prompt. Committed at `b73dfd0`.

**Source Files Read:**
- `skills/brainstorming/SKILL.md` — full read
- `skills/writing-plans/SKILL.md` — full read
- `skills/handoff-acceptance/SKILL.md` — full read

**Deviations from Plan:**
None — implemented exactly as specified.

**Self-Review Findings:**
No issues found.

**Concerns:**
No concerns.
