---
schema_version: 1
task_id: 4
task_type: implementation
status: DONE
files_changed:
  - path: "skills/brainstorming/SKILL.md"
    description: "Added checklist step 3.6 'Establish execution mode (handoff_spawn)' immediately after step 3.5's conflict-detection bullets, presenting the auto/ask/off consent choice in the same prompt style as the feature-name step. Added a sentence to Distillation Rule 4 (Contract facts promoted) instructing the Contract Facts section to record handoff_spawn: <auto|ask|off> as a plan execution variable."
tests:
  written: 0
  passing: 0
  command: ".venv/bin/python3 tests/ARaymond-skill-regression/validate-all-skills.py"
  result: PASS
contract_compliance:
  - constraint: "Consent values are exactly auto (default) / ask / off — no fourth value, no renaming"
    status: compliant
    detail: "Prompt text lists exactly auto/ask/off, auto marked as default (press-enter behavior)."
  - constraint: "Choice is a plan execution variable carried in the spec/distilled spec, not session memory"
    status: compliant
    detail: "Step 3.6 explicitly says session memory does not survive a separate writing-plans invocation and directs the answer to be recorded as a Contract Fact in the spec; the Contract Facts guidance now names handoff_spawn as a plan execution variable materialized into plan frontmatter by the plan writer."
  - constraint: "off must be documented as unquoted-safe (post-N83) AND quotable"
    status: not_applicable
    detail: "This task's scope is the user-facing prompt and Contract Facts guidance in brainstorming/SKILL.md, which does not touch YAML frontmatter authoring mechanics. The unquoted/quotable coercion detail belongs to writing-plans (Task 5), which materializes the frontmatter field — brainstorming only records the plain-text choice."
---

**Implementation Summary:**
Added a new checklist step 3.6 to `skills/brainstorming/SKILL.md` right after the existing feature-name step (3.5), presenting the `handoff_spawn` execution-mode choice (auto/ask/off) as its own message in the same tone as the feature-name prompt. Added one sentence to the Spec Distillation "Contract facts promoted" rule so the chosen mode is recorded as a Contract Fact (`handoff_spawn: <auto|ask|off>`) that flows into the distilled spec for the plan writer.

**Source Files Read:**
- `skills/brainstorming/SKILL.md` — full file read; located step 3.5 (feature-name establishment, lines ~27-36) and the Spec Distillation section's Contract Facts guidance (Rule 4, line ~158) and the `## Contract Facts` template section (line ~183-185) by content.

**CLAUDE.md Files Read:**
- None found in `skills/brainstorming/` (checked with `ls`; no CLAUDE.md present in that directory).

**Deviations from Plan:**
- None — implemented exactly as specified. (Word count landed at 2686, not the ~2550 the task estimated, but still well under the 5000-word ceiling, and the regression test's soft-threshold warning list is unchanged — 2 WARNING entries both pre-existing on writing-plans/SDD, not brainstorming.)

**Self-Review Findings:**
- No issues found. The new step numbering (3.6) sits correctly between 3.5 and 4 in the checklist; prompt style/format matches the adjacent feature-name prompt (own message, "press enter to accept default," blockquote). Contract Facts sentence placed where Rule 4 already describes what gets promoted to that section, keeping the guidance co-located rather than scattered.

**Concerns:**
- No concerns.

Commit: `2b7b0bf`.
