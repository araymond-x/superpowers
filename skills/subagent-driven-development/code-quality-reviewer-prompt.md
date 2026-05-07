# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality reviewer subagent.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes.**

```
Task tool (superpowers-code-reviewer):
  Use template at requesting-code-review/code-reviewer.md

  DESCRIPTION: [task summary, from implementer's report]
  PLAN_OR_REQUIREMENTS: Task N from [plan-file]
  BASE_SHA: [commit before task]
  HEAD_SHA: [current commit]
  IMPLEMENTER_REPORT: [CONTROLLER: Paste the implementer's full report here — the additional checks below reference its Deviations and Concerns sections]
```

**In addition to standard code quality concerns, the reviewer should check:**
- Does each file have one clear responsibility with a well-defined interface?
- Are units decomposed so they can be understood and tested independently?
- Is the implementation following the file structure from the plan?
- Did this implementation create new files that are already large, or significantly grow existing files? (Don't flag pre-existing file sizes — focus on what this change contributed.)
- Did this change leave any dead code (unused imports, unreachable branches, commented-out code, deprecated functions with no callers)? **Dead code findings are blocking** — they must be resolved (removed or explicitly justified in DEVIATIONS.md with controller approval) before the task is marked complete. Do not classify dead code as Minor.
- If dead code was identified but not removed, is it documented in the implementer's Deviations section? If not documented, flag as Critical.
- If Contract Constraints were provided: does the implementation honor them? Trace at least one data path from input to storage/output and verify types are consistent.
- For any finding where you cannot confirm the severity without additional context, label it as [NEEDS_CONTEXT] and describe what context would confirm or dismiss it. Do not classify uncertain findings as Minor to avoid surfacing them.

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment
