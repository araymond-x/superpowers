# SDD Controller Partner Agent Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first -- direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Add an independent partner agent that verifies the controller's dispatch quality before each implementer task, preventing semantic shortcuts (context omissions, inaccurate summaries, missed escalations) that mechanical hooks cannot detect.

**Architecture:** A new prompt template (`controller-partner-prompt.md`) defines the partner role. The controller dispatches the partner before each implementer, providing the proposed dispatch prompt and plan sections for comparison. The pre-dispatch hook enforces this with a file gate (`reports/partner-review-NNN.md`). Low-risk tasks can use a minimum-tier exemption. The SDD SKILL.md describes when and how to dispatch the partner, with content extracted to references/ to stay within the 5000-word limit.

**Tech Stack:** Markdown (prompt template), Bash (hook enhancement)

**Source Contracts:** None

**Contract Constraints:** None

**Shared Constants:** None

**Pattern References:**
- `skills/subagent-driven-development/spec-reviewer-prompt.md` -- prompt template structure, dispatch example format, output format
- `skills/subagent-driven-development/pre-execution-audit-prompt.md` -- independent verification role, cross-referencing pattern
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` -- file gate pattern (Check 5c checkpoint gate)

**Feature Archetype:** Extension -- adds a new agent role to the existing SDD workflow without replacing any existing components.

**File Map / Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| New | `skills/subagent-driven-development/controller-partner-prompt.md` | Create | Template format matches existing prompts |
| Modified | `skills/subagent-driven-development/SKILL.md` | Add partner workflow section + extract content | Word count stays under 5000 |
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Add Check 7: partner-review file gate | Existing checks unaffected |
| New | `skills/subagent-driven-development/references/session-recovery.md` | Create (extracted from SKILL.md) | -- |
| New | `skills/subagent-driven-development/references/model-selection.md` | Create (extracted from SKILL.md) | -- |
| New | `tests/unit/test_sdd_partner_gate.py` | Create | pytest infrastructure |
| Modified | `CLAUDE.md` | Document partner agent | -- |

---

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 1 | `skills/subagent-driven-development/references/session-recovery.md`, `skills/subagent-driven-development/SKILL.md` (extraction + partner section) | -- | -- |
| Task 2 | `skills/subagent-driven-development/controller-partner-prompt.md` | `spec-reviewer-prompt.md`, `pre-execution-audit-prompt.md` | -- |
| Task 3 | `tests/unit/test_sdd_partner_gate.py` | `sdd-pre-dispatch-hook.sh` | -- |
| Task 4 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | -- | Task 3 |
| Task 5 | `CLAUDE.md` | All modified files | Tasks 1-4 |

---

### Task 1: Extract Content and Add Partner Workflow to SDD SKILL.md

**Files:**
- Create: `skills/subagent-driven-development/references/session-recovery.md`
- Modify: `skills/subagent-driven-development/SKILL.md`

**Pattern References:**
- Existing extraction pattern: `references/deviations-template.md`, `references/report-naming-convention.md`, `references/honesty-check-block.md` -- all follow the same format: header comment, content moved verbatim, original replaced with reference

**Context:** The SDD SKILL.md is at 4983 words (test-counted). Adding the partner workflow section (~160 words) requires extracting ~220+ words. Two extraction candidates: Session Recovery (~100 words saved) and Model Selection (~95 words saved). Both are reference guidance, not process steps.

- [ ] **Step 1: Extract Session Recovery to references/**

Create `skills/subagent-driven-development/references/session-recovery.md`:
```markdown
# Session Recovery

> Part of the subagent-driven-development skill. Referenced from SKILL.md.

If a controller session is interrupted (context overflow, crash, or manual stop), a new session can resume execution by:

1. **Read the plan file** -- checked-off checkboxes show what was completed
2. **Read DEVIATIONS.md** -- shows accumulated drift and pending dispositions
3. **Read `reports/` directory** -- shows detailed implementer and reviewer output for each completed task
4. **Read TodoWrite** (if still in session) or reconstruct from plan checkboxes
5. **Resume from the first unchecked task** -- all prior context is in files

This is why file-based persistence matters: the plan file, DEVIATIONS.md, and reports/ directory together form a complete execution log that survives session loss.
```

Replace the Session Recovery section in SKILL.md with:
```markdown
## Session Recovery

See `references/session-recovery.md` for how to resume after a session interruption. All execution state is in files (plan checkboxes, DEVIATIONS.md, reports/).
```

- [ ] **Step 1b: Extract Model Selection to references/**

Create `skills/subagent-driven-development/references/model-selection.md` with the full Model Selection section content (lines 367-380). Replace in SKILL.md with:
```markdown
## Model Selection

See `references/model-selection.md` for guidance on choosing models per role (haiku for mechanical tasks, standard for integration, most capable for architecture/review).
```

Verify combined extraction saved enough:
```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py 2>&1 | grep "SDD SKILL:" | head -1
```
Expected: Under 4850 words (leaving ~150 words headroom for partner section).

- [ ] **Step 2: Add Controller Partner Verification section**

In SKILL.md, insert a new section AFTER "Review Enforcement" and BEFORE "Model Selection". This positions it in the per-task workflow, after the review requirement but before model guidance:

```markdown
## Controller Partner Verification

Before dispatching each implementer subagent, dispatch the controller partner to verify your dispatch quality. The partner reads your proposed prompt and cross-references it against the plan to catch context omissions, inaccurate summaries, and missed escalations.

**When to dispatch (risk-tiered):**
- **Full review**: Tasks with Pattern References, Shared Constants, external contract dependencies, or multi-file changes
- **Minimum tier**: Simple config changes, single-file internal modifications, test-only tasks. Write `reports/partner-review-NNN-minimum-tier.md` with tier rationale instead of dispatching.

**Dispatch sequence:**
1. Prepare the implementer dispatch prompt (all context sections filled in)
2. Dispatch partner (see `./controller-partner-prompt.md`) with: the proposed prompt, plan task description, plan header sections
3. Partner returns APPROVED or BLOCKED with findings
4. Save partner output to `reports/partner-review-NNN.md`
5. If BLOCKED: address findings, re-dispatch partner
6. If APPROVED: proceed to implementer dispatch

The pre-dispatch hook requires `reports/partner-review-NNN.md` (>50 bytes) before allowing implementer dispatch.
```

- [ ] **Step 3: Add partner-prompt.md to Prompt Templates list**

In the "Prompt Templates" section, add:
```markdown
- `./controller-partner-prompt.md` - Dispatch controller partner for dispatch quality verification (before each implementer)
```

- [ ] **Step 4: Verify word count**

```bash
wc -w skills/subagent-driven-development/SKILL.md
python3 tests/ARaymond-skill-regression/validate-all-skills.py 2>&1 | grep "SDD SKILL:" | head -1
```
Expected: Under 5000 words by test count.

- [ ] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/SKILL.md skills/subagent-driven-development/references/session-recovery.md
git commit -m "feat: Add Controller Partner Verification section to SDD skill"
```

---

### Task 2: Create Controller Partner Prompt Template

**Files:**
- Create: `skills/subagent-driven-development/controller-partner-prompt.md`

**Pattern References:**
- `skills/subagent-driven-development/spec-reviewer-prompt.md` -- dispatch example format, role statement, output format
- `skills/subagent-driven-development/pre-execution-audit-prompt.md` -- independent cross-referencing, artifact verification

**Context:** The partner agent is dispatched by the controller before each implementer dispatch. It receives: (1) the proposed implementer prompt, (2) the plan's task description, (3) the plan header sections (Contract Constraints, Shared Constants, Pattern References). It verifies the controller accurately injected all required context. Use haiku model for cost efficiency.

- [ ] **Step 1: Create the prompt template**

Create `skills/subagent-driven-development/controller-partner-prompt.md`:

```markdown
# Controller Partner Prompt Template

Use this template when dispatching the controller partner before an implementer dispatch.

**Purpose:** Independently verify the controller's dispatch quality -- that the proposed implementer prompt contains all required context sections, accurately reflects the plan, and doesn't suppress concerns from prior tasks.

**Dispatch before:** Each implementer dispatch (or minimum-tier exemption for low-risk tasks).

**Model:** Use haiku for cost efficiency. The partner reads and compares -- it doesn't write code.

` ` `
Agent tool (haiku model):
  description: "Partner review for Task N dispatch"
  prompt: |
    You are the SDD Controller Partner. Your job is to verify the controller
    is doing its job correctly before an implementer is dispatched. You are an
    independent check -- the controller prepared this dispatch, and you verify
    it before it goes out.

    You are reviewing the dispatch for Task N: [task name]

    ## Plan Task Description

    [CONTROLLER: Paste the FULL task description from the plan for Task N]

    ## Plan Header Sections

    **Contract Constraints:**
    [CONTROLLER: Paste verbatim from plan header, or "None"]

    **Shared Constants:**
    [CONTROLLER: Paste verbatim from plan header, or "None"]

    **Pattern References for this task:**
    [CONTROLLER: Paste the task-level Pattern References, or "None"]

    ## Proposed Implementer Prompt

    [CONTROLLER: Paste the COMPLETE prompt you are about to send to the implementer]

    ## DEVIATIONS.md Current State

    [CONTROLLER: Paste current contents of DEVIATIONS.md, or "Empty -- no deviations yet"]

    ## Previous Task Report Summary

    [CONTROLLER: Paste the status and concerns from the previous task's implementer report,
     or "First task -- no prior report"]

    ## Your Checks

    1. **CONTEXT COMPLETENESS**: Does the proposed prompt contain ALL of these sections?
       - [ ] Contract Constraints section (matching plan, or "None")
       - [ ] Shared Constants section (matching plan, or "None")
       - [ ] Pattern References section (matching task-level refs, or "None")
       - [ ] Source Files section
       - [ ] Subdirectory CLAUDE.md reminder

    2. **CONTEXT ACCURACY**: Do the injected sections match the plan?
       - Compare Contract Constraints in prompt vs plan header -- verbatim match?
       - Compare Shared Constants in prompt vs plan header -- complete list?
       - Compare Pattern References in prompt vs task description -- all refs included?
       - Is the task description in the prompt complete (not truncated or paraphrased)?

    3. **PRIOR TASK AWARENESS**:
       - Did the previous task report DONE_WITH_CONCERNS? If so, are those concerns
         logged in DEVIATIONS.md?
       - Are there pending deviations that affect this task?
       - Did the previous task modify files that this task reads? If so, is the
         implementer prompt aware of those changes?

    4. **ESCALATION CHECK**:
       - Was the previous task BLOCKED or NEEDS_CONTEXT? If so, was the issue
         resolved before this dispatch, or is the controller pushing through?
       - Are there any DONE_WITH_CONCERNS items from ANY prior task that remain
         unlogged in DEVIATIONS.md?

    ## Output Format

    **Status:** APPROVED | BLOCKED

    **Context Completeness:** [PASS | FAIL -- list missing sections]

    **Context Accuracy:** [PASS | FAIL -- list mismatches]

    **Prior Task Awareness:** [PASS | FAIL -- list missed concerns]

    **Escalation Check:** [PASS | FAIL -- list unresolved issues]

    **Findings (if BLOCKED):**
    - [Finding 1]: [what's wrong] -- [how to fix]

    If ALL four checks pass, return APPROVED. If ANY check fails, return BLOCKED.
    Do not approve with caveats -- either the dispatch is ready or it isn't.
` ` `

**Controller saves partner output to:** `reports/partner-review-NNN.md`

If partner returns BLOCKED: address each finding, update the dispatch prompt, re-dispatch partner.
If partner returns APPROVED: proceed to implementer dispatch.
```

Note: The triple backticks in the template above should not have spaces -- they are escaped here to avoid closing the outer code block.

- [ ] **Step 2: Verify the file renders correctly**

Read the file back and confirm the template structure is intact:
```bash
head -5 skills/subagent-driven-development/controller-partner-prompt.md
```

- [ ] **Step 3: Verify skill regression**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```
Expected: PASS (new prompt template should be detected as a reference)

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/controller-partner-prompt.md
git commit -m "feat: Create controller partner prompt template for dispatch verification"
```

---

### Task 3: Write Partner Review Gate Tests (TDD Red Phase)

**Files:**
- Create: `tests/unit/test_sdd_partner_gate.py`

**Pattern References:**
- `tests/unit/test_sdd_hard_gates.py` -- same hook testing pattern, setup helpers, run_hook function
- `tests/unit/sdd_test_helpers.py` -- shared workspace setup functions

**Context:** Tests for the partner-review file gate in the pre-dispatch hook. The gate requires `reports/partner-review-NNN.md` (>50 bytes) before allowing implementer dispatches. Minimum-tier files (`partner-review-NNN-minimum-tier.md`) are also accepted.

- [ ] **Step 1: Create test file**

Create `tests/unit/test_sdd_partner_gate.py` with these test classes:

```python
class TestPartnerReviewGate:
    def test_blocks_without_partner_review(self, tmp_path):
        # Setup: full SDD workspace, all other gates satisfied, NO partner-review file
        # Assert: exit 2, stderr mentions "partner"

    def test_allows_with_partner_review(self, tmp_path):
        # Setup: full workspace + reports/partner-review-001.md (>50 bytes)
        # Assert: exit 0

    def test_allows_with_minimum_tier(self, tmp_path):
        # Setup: full workspace + reports/partner-review-001-minimum-tier.md (>50 bytes)
        # Assert: exit 0

    def test_blocks_with_tiny_partner_review(self, tmp_path):
        # Setup: full workspace + reports/partner-review-001.md with only "PASS" (5 bytes)
        # Assert: exit 2

    def test_no_partner_required_for_task_zero(self, tmp_path):
        # Setup: full workspace dispatching task 0 (no previous task, no partner needed)
        # Assert: exit 0 (partner gate only applies to tasks with predecessors)
```

Use `setup_full_sdd_workspace` and `run_hook` from existing test helpers/patterns.

- [ ] **Step 2: Run tests (expect failures -- TDD red phase)**

```bash
.venv/bin/python3 -m pytest tests/unit/test_sdd_partner_gate.py -v
```
Expected: `test_blocks_without_partner_review` and `test_blocks_with_tiny_partner_review` FAIL (gate doesn't exist yet). Others should PASS (existing behavior allows without gate).

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_sdd_partner_gate.py
git commit -m "test: Add partner review gate tests for SDD hook (TDD red phase)"
```

---

### Task 4: Add Partner Review Gate to Pre-Dispatch Hook

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`

**Pattern References:**
- Check 5c (checkpoint file gate) in `sdd-pre-dispatch-hook.sh` -- same file-existence + size pattern

**Context:** Add Check 7 after the context load estimate (non-blocking section) and before the additionalContext assembly. The check requires `reports/partner-review-NNN.md` or `reports/partner-review-NNN-minimum-tier.md` (>50 bytes) for the CURRENT task before allowing implementer dispatch.

- [ ] **Step 0: Update Check 3b naming allowlist**

In `sdd-pre-dispatch-hook.sh`, find the Check 3b regex (line ~216):
```bash
if ! echo "$BASENAME" | grep -qE '^(task-[0-9]+-|pre-execution-audit|context-summary)'; then
```

Update to include `partner-review`:
```bash
if ! echo "$BASENAME" | grep -qE '^(task-[0-9]+-|pre-execution-audit|context-summary|partner-review)'; then
```

Without this, partner-review files in `reports/` would be flagged as naming convention violations by Check 3b, blocking dispatch with a misleading error before Check 5d even runs.

- [ ] **Step 1: Add Check 5d to the hook**

In `sdd-pre-dispatch-hook.sh`, insert a new check section in the implementer enforcement block. Add it AFTER Check 5c (checkpoint file gate) and BEFORE Check 6 (token estimation). This keeps it with the other per-task file gates:

```bash
# Check 5d: Partner review evidence
# The controller must dispatch the partner agent (or declare minimum tier)
# before dispatching the implementer. Task 0 is exempt — it's contract
# verification with no prior implementer context to cross-reference.
if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
  TASK_PADDED=$(printf "%03d" "$TASK_NUMBER" 2>/dev/null || echo "$TASK_NUMBER")
  PARTNER_FILE="reports/partner-review-${TASK_PADDED}.md"
  PARTNER_FILE_MIN="reports/partner-review-${TASK_PADDED}-minimum-tier.md"
  if [ -f "$PARTNER_FILE" ] && [ "$(wc -c < "$PARTNER_FILE" 2>/dev/null | tr -d ' ')" -ge "$MIN_REPORT_BYTES" ]; then
    : # Full partner review exists
  elif [ -f "$PARTNER_FILE_MIN" ] && [ "$(wc -c < "$PARTNER_FILE_MIN" 2>/dev/null | tr -d ' ')" -ge "$MIN_REPORT_BYTES" ]; then
    : # Minimum tier partner review exists
  else
    ERRORS+=("BLOCKED: No partner review found for Task $TASK_NUMBER (expected: $PARTNER_FILE or $PARTNER_FILE_MIN). Dispatch the controller partner (see controller-partner-prompt.md) and save the output, or write a minimum-tier review with rationale (>$MIN_REPORT_BYTES bytes).")
  fi
fi
```

- [ ] **Step 2: Run tests to verify gate works**

```bash
.venv/bin/python3 -m pytest tests/unit/test_sdd_partner_gate.py -v
```
Expected: All tests PASS

- [ ] **Step 3: Run full test suite to verify no regressions**

```bash
.venv/bin/python3 -m pytest tests/unit/ -v
```
Expected: All tests PASS (existing tests need partner-review files added to their setup helpers)

Note: If existing tests fail because they don't create partner-review files, update `setup_full_sdd_workspace` in `sdd_test_helpers.py` to create `reports/partner-review-NNN.md` for each completed task. This is a test infrastructure update, not a logic change.

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/unit/sdd_test_helpers.py
git commit -m "feat: Add partner review gate (Check 5d) to SDD pre-dispatch hook"
```

---

### Task 5: Documentation Update and Verification

**Files:**
- Modify: `CLAUDE.md`
- Read: All modified files

- [ ] **Step 1: Run all test suites**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/ARaymond-installation/verify-symlink-install.sh
.venv/bin/python3 -m pytest tests/unit/ -v
```
Expected: All pass.

- [ ] **Step 2: Update CLAUDE.md**

Add to the Hooks-Based Enforcement section:
```markdown
- **Partner review gate** (Check 5d): Requires `reports/partner-review-NNN.md` (>50 bytes) before dispatching task NNN. The controller must dispatch the partner agent (see `controller-partner-prompt.md`) or write a minimum-tier review. The partner independently verifies dispatch quality -- context completeness, accuracy, and prior task awareness.
```

Add to the Prompt Templates note (or wherever the prompt template list is):
```markdown
- `controller-partner-prompt.md` -- independent dispatch quality verification (partner agent)
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: Document controller partner agent and review gate"
```

---

## Acceptance Criteria

1. **Partner prompt template** exists at `controller-partner-prompt.md` with 4 verification checks (context completeness, accuracy, prior task awareness, escalation)
2. **SDD SKILL.md** has Controller Partner Verification section describing when/how to dispatch, with risk-tiered guidance
3. **Pre-dispatch hook** has Check 5d requiring partner-review file before implementer dispatch
4. **Minimum-tier exemption** works (partner-review-NNN-minimum-tier.md accepted for low-risk tasks)
5. **All test suites pass** (unit tests, skill regression under 5000 words, installation)
6. **SDD SKILL.md** stays under 5000 words (Session Recovery extracted to references/)
