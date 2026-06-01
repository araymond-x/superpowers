---
schema_version: 1
task_id: 6
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/writing-plans/SKILL.md"
    description: "Context block → two-entry-paths (direct entry first-class); Step 0.5 → 4-branch conflict detection + worktree guard + spec input + entry-mode recording; new '## Declaring task_type per Task' section (bright-line rule, table, 11-keyword WARNING)."
tests:
  written: 0
  passing: 0
  command: "python3 tests/ARaymond-skill-regression/validate-all-skills.py"
  result: PASS
contract_compliance:
  - constraint: "11 write-keywords in task_type section match validate-plan.py exactly"
    status: compliant
    detail: "create, add, implement, fix, modify, write, update, refactor, migrate, delete, remove — exact match + order."
  - constraint: "writing-plans/SKILL.md UNDER 5000 words"
    status: compliant
    detail: "wc -w total 4641 (was 4183); regression body-count 4615. Under the 5000 hard limit."
  - constraint: "Surgical edits only — no other sections reformatted"
    status: compliant
    detail: "git diff: 1 file changed, 42 insertions(+), 5 deletions(-); only the 3 prescribed insertion points changed."
---

**Implementation Summary**
Applied all three prescribed edits to `skills/writing-plans/SKILL.md`:
1. **Context block** — replaced the single "designed to follow brainstorming / if invoked directly" paragraph with the two-entry-path structure (after-brainstorming vs. direct entry as first-class).
2. **Step 0.5** — replaced the one-line "resolve feature directory" item with the full 4-branch conflict-detection block, worktree/branch guard, optional spec input, and entry-mode recording. Surrounding numbered checklist items preserved.
3. **New `## Declaring task_type per Task` section** — inserted after `## Declaring review_tier per Task` and before `## No Placeholders`, with the bright-line rule, the verification-vs-implementation table, the orthogonality note, and the 11-keyword WARNING.

Word count: 4641 total / 4615 body — under the 5000 hard limit.

**Source Files Read**
- `skills/writing-plans/SKILL.md` (full — confirmed all 3 insertion points by content).
- `tests/ARaymond-skill-regression/validate-all-skills.py` (the F6 check @569 — to diagnose the FAIL described below).

**CLAUDE.md Files Read**
- None in `skills/writing-plans/` (confirmed absent). Project + global CLAUDE.md already in context.

**Deviations from Plan**
**One required deviation, fully resolved.** The verbatim Edit-1 Context block removed the literal substring `"invoked directly"`, which the regression suite's **F6 check** (`validate-all-skills.py:569`) greps for (it asserts standalone-invocation guidance via the literal strings `"skipping brainstorming"` OR `"invoked directly"`). The prescribed block said "Invoke this skill directly with a spec..." — semantically equivalent but not the exact token — so the first regression run reported **FAIL: 1 (missing standalone invocation guidance, F6)**. Per the architectural-principles rule (automated gate FAILs are never "expected" — fix the input), I made the minimal phrasing change `"Invoke this skill directly with a spec"` → `"This skill can be invoked directly with a spec"`, reintroducing the literal substring while preserving the prescribed meaning. After: **145 PASS / 0 FAIL**. Only the wording of the block I was already prescribed to write changed; the `task_type` keyword list and Step 0.5 content are byte-for-byte as specified.

**Self-Review Findings**
- All 11 `task_type` keywords verified against the contract list — exact match, correct order.
- The 3 remaining regression WARNINGs are advisory/pre-existing (writing-plans body over the 4000 soft threshold; SDD SKILL word count; 2 historical bare-DEVIATIONS.md refs @316/325 untouched).
- `git diff`: 1 file changed, +42/-5 — scope contained.

**Concerns**
- **F6 check is brittle (advisory, for the fork maintainer / SSOT audit).** The regression check keys on a hardcoded literal substring (`"invoked directly"` / `"skipping brainstorming"`) rather than semantic intent. The prescribed verbatim block was correct in meaning but would have permanently failed F6 as worded. Satisfied with a one-word phrasing change, but the literal-substring coupling will surprise future editors of this Context block — if "invoked directly" is removed again, F6 FAILs. Candidate finding for the Task 9 SSOT audit / BACKLOG.
