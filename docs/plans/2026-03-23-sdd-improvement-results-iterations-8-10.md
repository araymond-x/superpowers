# SDD Improvement Results — Iterations 8 + 10: Plan Review Rigor & Context Window Protection

**Date**: 2026-03-23

---

## Iteration 8: Plan Review Rigor

**File Created**: `skills/writing-plans/plan-document-reviewer-prompt-v0.1.md` (111 lines, up from 49)

### Changes

| Addition | Purpose |
|----------|---------|
| Source contracts placeholder | Reviewer reads source files independently |
| 13-category checklist (from 4) | Mechanical verification beyond "does it look right" |
| Cross-document consistency audit | 3-field trace across handoff/spec/plan; mismatch = blocking |
| Code snippet verification | Read 3 snippets, compare to source, label VERIFIED/MISMATCH/ILLUSTRATIVE |
| Size/complexity assessment | 800-line plan, 200-line task, 10+ tasks, missing Task 0 = blocking |
| Enhanced output format | Category tags, snippet labels, field trace results |
| Calibration update | Type mismatches always blocking (citing prior incident) |

### Test: Would this reviewer have caught the reconciliation plan issues?

| Known Issue | Would Reviewer Catch? |
|------------|----------------------|
| String-vs-numeric type mismatch in snippets | YES — snippet verification + cross-doc audit |
| 2816-line plan size | YES — size assessment, blocking |
| Exception name drift | YES — cross-document consistency |
| Missing rate field mapping | YES — 3-field end-to-end trace |
| Missing write-scope partitioning | YES — blocking for subagent plans |
| 5 of 9 plan-review findings | YES — all 5 are in the 13-category checklist |

---

## Iteration 10: Context Window Protection & File-Based Persistence

**Files Created**:
- `scripts/estimate-task-tokens.py` (208 lines) — deterministic pre-dispatch size estimation
- `scripts/validate-report.py` (219 lines) — mechanical report completeness check

**Sections Added to SDD SKILL-v0.1.md** (now 578 lines):
- Context Budget Management
- File-Based Report Persistence
- Session Recovery
- Red Flags additions (2 new NEVER items)
- BLOCKED handler strengthened (200-line task limit reference)

### Script Test Results

| Test | Input | Result | Correct? |
|------|-------|--------|----------|
| Token estimation (small file) | implementer-prompt-v0.1.md (183 lines) | 3,874 tokens, OK | YES |
| Token estimation (large plan at 200K budget) | reconciliation plan (2816 lines) | 30,066 tokens, OK | YES (fits in 200K) |
| Token estimation (large plan at 50K budget) | reconciliation plan (2816 lines) | 30,066 tokens, TOO_LARGE | YES (exits 1) |
| Report validation (complete) | 9-section report | COMPLETE, exit 0 | YES |
| Report validation (incomplete) | 3-section report | INCOMPLETE, 6 missing, exit 1 | YES |

### Context Window Protection Matrix

| Protection | Before | After |
|-----------|--------|-------|
| Pre-dispatch size estimation | MISSING | **Script-based** (deterministic, exit codes) |
| Subagent context-pressure detection | MISSING | **Indirect** (task splitting prevents overload) |
| File-based report persistence | MISSING | **reports/ directory** (flight recorder) |
| Controller recovery from interrupted session | MISSING | **5-step recovery protocol** (plan + DEVIATIONS.md + reports/) |
| Cap on injected prompt size | MISSING | **Script-enforced** (50% of budget = TOO_LARGE) |
| Task splitting protocol | MISSING | **Defined** (BLOCKED handler + estimation script) |
| Report completeness validation | MISSING | **Script-based** (9 required sections) |

### Answers to the User's Questions

1. **Have we put an explicit solution to prevent oversized tasks?**
   YES — writing-plans v0.1 has a 200-line task limit, and the estimation script enforces a token budget before dispatch. TOO_LARGE is a hard stop.

2. **How does the controller know before handoff that a task is too large?**
   The controller runs `estimate-task-tokens.py` before every dispatch. The script outputs OK/WARNING/TOO_LARGE with token counts. TOO_LARGE exits 1 — the controller must split.

3. **What happens when a subagent is in danger of overrunning context?**
   The pre-dispatch estimation prevents this from happening. If a task somehow exceeds expectations at runtime, the subagent can report BLOCKED ("task is too large") and the controller's BLOCKED handler now explicitly references the 200-line limit and instructs splitting.

4. **Is this reported clearly with actionable data?**
   YES — the estimation script outputs JSON with exact token counts per component (task, constraints, context, overhead, total, budget remaining). The controller has all the data needed to decide how to split.

5. **Does the subagent have a hard file output?**
   YES — the controller saves every report to `reports/task-N-*.md`. The `validate-report.py` script mechanically verifies completeness. If the session crashes, the reports directory persists.
