---
schema_version: 1
task_id: 5
task_type: implementation
status: DONE
files_changed:
  - path: "skills/writing-plans/references/plan-header-template.md"
    description: "New file — extracted the Plan Document Header example block (Goal/Architecture/Tech Stack/Source Contracts/Contract Constraints/Shared Constants/Pattern References/Feature Archetype/Code Footprint table) verbatim from SKILL.md to create word-ceiling headroom for the new content."
  - path: "skills/writing-plans/SKILL.md"
    description: "Replaced the inline header example with a one-line pointer to references/plan-header-template.md; added 'Execution-mode materialization' guidance to checklist item 0.5 (direct-path handoff_spawn choice); added new '## Declaring `handoff_spawn` per Plan' section after 'Declaring `integration_test` per Plan', mirroring the three sibling 'Declaring X' sections; added `handoff_spawn: auto` line to the YAML Frontmatter Required example next to `enforcement_tier`."
tests:
  written: 0
  passing: 0
  command: ".venv/bin/python3 tests/ARaymond-skill-regression/validate-all-skills.py"
  result: PASS
contract_compliance:
  - constraint: "Consent values are exactly auto (default) / ask / off. Do not add a fourth or rename."
    status: compliant
    detail: "New section's table and Step 0.5 prompt both use exactly auto/ask/off, matching plan.py's Literal[\"auto\",\"ask\",\"off\"]."
  - constraint: "The choice is a plan execution variable carried in the spec/distilled spec — NOT session memory."
    status: compliant
    detail: "New section explicitly states the brainstorming-path value is recorded in the spec (step 3.6, verified in brainstorming/SKILL.md) and read by writing-plans; Step 0.5 text says the same."
  - constraint: "Word ceiling: writing-plans/SKILL.md is 4726 words currently; additions must be offset by the Step 1 extraction. Verify with an explicit wc -w number under 5000."
    status: compliant
    detail: "Ran wc -w skills/writing-plans/SKILL.md after all edits: exact result 4819 words (previously 4726) — under the 5000 hard limit. Regression test independently reports 4793 (its own word-counting method differs slightly from wc -w but agrees it's under 5000)."
  - constraint: "off must be documented as unquoted-safe (post-N83) AND quotable — both accepted."
    status: compliant
    detail: "New section states: 'Write off unquoted or quoted — both are accepted (the model coerces YAML-1.1 off->False->\"off\")', citing plan.py's _coerce_yaml_bool_handoff_spawn validator read directly from source."
---

**Implementation Summary:**
Extracted the Plan Document Header example block from `skills/writing-plans/SKILL.md` into a new `references/plan-header-template.md` (Step 1, done first as prescribed), then added the "Declaring `handoff_spawn` per Plan" author section, a Step 0.5 direct-path execution-mode choice, and a `handoff_spawn` line in the YAML frontmatter example. Final word count via `wc -w skills/writing-plans/SKILL.md` is **4819** (was 4726), comfortably under the 5000 hard limit; the regression suite reports PASS with 0 FAIL (2 pre-existing soft-threshold WARNINGs on writing-plans and SDD SKILL.md, unchanged in kind from before this task).

**Source Files Read:**
- `skills/writing-plans/SKILL.md` (full file) — located all four anchor points by content: Plan Document Header section (~line 189), the three sibling "Declaring X" sections (review_tier ~387, task_type ~416, integration_test ~435), checklist item 0.5 (~line 33-47), and the YAML Frontmatter example (~line 234-267). All matched the plan's approximate line numbers closely.
- `skills/scripts/models/plan.py` (lines 40-134) — confirmed `Plan.handoff_spawn: Literal["auto","ask","off"] = "auto"` and the `_coerce_yaml_bool_handoff_spawn` validator: `False`→`"off"` accepted, `True` (bare `on`) rejected with an explicit error message. Used this to write an accurate, source-grounded description of the coercion behavior rather than re-deriving/re-verifying N83 from scratch.
- `skills/brainstorming/SKILL.md` (grep for `handoff_spawn`/`3.6`) — confirmed step 3.6 records `handoff_spawn: <auto|ask|off>` as a Contract Fact in the distilled spec, matching my "brainstorming step 3.6" citation exactly.

**CLAUDE.md Files Read:**
- None found in `skills/writing-plans/` (verified via `ls`/test for the file before editing).

**Deviations from Plan:**
None — implemented exactly as specified, Steps 1-6 in order.

**Self-Review Findings:**
- Verified `git status --short` before commit showed only the two prescribed files staged (some unrelated dispatch-log/checkpoint artifacts from the surrounding SDD session were present but left untouched and unstaged, per the task's "touching only the two files listed" instruction).
- Reviewed the full commit diff (`git show 0ccb4e8`) — confirms the extraction is byte-faithful (no accidental content loss/duplication) and all four additions landed in the correct locations.
- Confirmed the "0.5" checklist numbering renders correctly despite the new paragraph being inserted before the literal `1.` list item — this mirrors the pre-existing "Entry mode recording" paragraph pattern already in that same spot, so it's consistent with established document structure, not a new risk.

**Concerns:**
No concerns.

Commit: `0ccb4e8`.
