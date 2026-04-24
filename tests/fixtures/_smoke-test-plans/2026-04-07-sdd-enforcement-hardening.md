---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 1
    title: "Fix Permission Glob for Skill Tool Invocation"
  - id: 2
    title: "Add Dispatch Provenance Logging to Pre-Dispatch Hook"
  - id: 3
    title: "Add Dispatch Provenance Verification to Implementer Gate"
    depends_on: [2]
  - id: 4
    title: "Convert Token Estimation SKIPPED to BLOCK"
  - id: 5
    title: "Convert Context Summary Warning to BLOCK at Midpoint"
  - id: 6
    title: "Add Controller Checkpoint File Gate"
  - id: 7
    title: "Extend Report Guard to Protect Dispatch Log"
    depends_on: [2]
  - id: 8
    title: "Create Shared Test Helpers and Dispatch Provenance Tests"
    depends_on: [2, 3, 7]
  - id: 9
    title: "Write Hard Gate Tests"
    depends_on: [4, 5, 6]
  - id: 10
    title: "Integration Verification and Documentation Update"
    depends_on: [1, 8, 9]
---
# SDD Enforcement Hardening Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first -- direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Convert advisory SDD enforcement warnings into hard gates so that controller agents cannot circumvent the review cycle, token estimation, checkpoint execution, or context management steps -- even under context pressure.

**Architecture:** All changes target the existing hook scripts in `skills/subagent-driven-development/scripts/` and the global permissions in `~/.claude/settings.json`. The core mechanism is the `sdd-pre-dispatch-hook.sh` which fires on every `Agent` tool call. We extend it with: (1) a dispatch provenance log that records reviewer dispatches, (2) blocking gates for token estimation and context summary, and (3) checkpoint file requirements. The report guard is enhanced to protect the new dispatch log from forgery.

**Tech Stack:** Bash (hooks), Python 3.12+ (scripts, tests), jq (JSON parsing in hooks)

**Source Contracts:** None

**Contract Constraints:** None

**Feature Archetype:** Extension -- adds enforcement depth to existing hook infrastructure without replacing it.

**File Map / Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Extend with dispatch log, blocking gates | All 7 existing checks still pass |
| Modified | `skills/subagent-driven-development/scripts/sdd-report-guard.sh` | Extend to protect dispatch log | Existing report-forgery detection still works |
| Modified | `~/.claude/settings.json` (permissions.allow) | Fix piped command permission glob | Existing permissions preserved |
| New | `tests/unit/test_sdd_dispatch_log.py` | Create tests for dispatch provenance logic | pytest infrastructure in tests/unit/ |
| New | `tests/unit/test_sdd_hard_gates.py` | Create tests for blocking gate conversions | pytest infrastructure in tests/unit/ |
| Retained | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Keep -- called by controller, not modified | -- |
| Retained | `skills/subagent-driven-development/scripts/estimate-task-tokens.py` | Keep -- called by hook, not modified | -- |
| Retained | `skills/subagent-driven-development/scripts/context-summary.py` | Keep -- called by controller, not modified | -- |
| Retained | `skills/subagent-driven-development/scripts/validate-report.py` | Keep -- called by hook, not modified | -- |

---

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 1 | `~/.claude/settings.json` (permissions section only) | -- | -- |
| Task 2 | `sdd-pre-dispatch-hook.sh` (reviewer dispatch logging section) | -- | -- |
| Task 3 | `sdd-pre-dispatch-hook.sh` (implementer provenance check section) | -- | Task 2 |
| Task 4 | `sdd-pre-dispatch-hook.sh` (token estimation gate section) | -- | -- |
| Task 5 | `sdd-pre-dispatch-hook.sh` (context summary gate section) | -- | -- |
| Task 6 | `sdd-pre-dispatch-hook.sh` (checkpoint file gate section) | -- | -- |
| Task 7 | `sdd-report-guard.sh` (dispatch log protection section) | -- | Task 2 |
| Task 8 | `tests/unit/test_sdd_dispatch_log.py` | `sdd-pre-dispatch-hook.sh`, `sdd-report-guard.sh` | Tasks 2, 3, 7 |
| Task 9 | `tests/unit/test_sdd_hard_gates.py` | `sdd-pre-dispatch-hook.sh` | Tasks 4, 5, 6 |
| Task 10 | (none -- verification only) | All modified files | Tasks 1-9 |

Note: Tasks 2-7 all modify `sdd-pre-dispatch-hook.sh` but target distinct, non-overlapping sections (clearly delimited by `# ---` section headers). They MUST be executed sequentially because they share the same file.

**TDD execution order:** Tasks 8-9 create the test files. For strict TDD (red-green), execute in this order: Task 1, Task 8 (tests fail), Tasks 2-3-7 (tests pass), Task 9 (tests fail), Tasks 4-5-6 (tests pass), Task 10. Each implementation task's "Step 1: Write the failing test" is a reference to the corresponding test in Task 8 or 9 — the implementer should verify the test exists and fails before implementing.

---

### Task 1: Fix Permission Glob for Skill Tool Invocation

**Files:**
- Modify: `~/.claude/settings.json` (permissions.allow array)

**Context:** The current permission `Bash(cat ~/.claude/skills/superpowers/**)` matches only the `cat` portion. All 15 command stubs use `cat ... | awk ...` piped commands. The `awk` pipe falls outside the permission glob, blocking Skill tool invocation in autonomous sessions. This was confirmed in the current session (Issue 1 from honesty check) and reproduced live during this planning session.

- [x] **Step 1: Read current permissions**

Read `~/.claude/settings.json` and locate the `permissions.allow` array. Current value:
```json
"allow": [
    "Bash(cat ~/.claude/skills/superpowers/**)"
]
```

- [ ] **Step 2: Update permission to cover piped commands**

Use Edit to change the permission glob to cover the full `cat | awk` pipeline:
```json
"allow": [
    "Bash(cat ~/.claude/skills/superpowers/** | awk *)"
]
```

This matches any `cat` of a superpowers skill file piped to any `awk` command -- which is exactly what the command stubs do. The `**` glob in the cat path covers all subdirectories. The `*` after `awk` covers any awk program.

Important: Use Edit tool (not Write) to modify settings.json -- Write would overwrite the entire file and destroy all other settings.

- [ ] **Step 3: Verify the permission works**

Run the same command that the command stubs use:
```bash
cat ~/.claude/skills/superpowers/subagent-driven-development/SKILL.md | awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' | head -5
```
Expected: First 5 lines of the SKILL.md body (after YAML frontmatter is stripped). If the command executes, the permission glob works.

- [ ] **Step 4: Document the change**

Note: `~/.claude/settings.json` is a user-level config file, not part of this git repository. Do not `git add` it. The change should be noted in the project's CLAUDE.md "Global Settings Changes" section (handled in Task 10).

---

### Task 2: Add Dispatch Provenance Logging to Pre-Dispatch Hook

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (add section after the IS_REVIEWER early exit at line 73)

**Context:** The pre-dispatch hook already identifies reviewer dispatches (`IS_REVIEWER=true`) and exits early (line 73: `exit 0`). Instead of exiting silently, it should log the reviewer dispatch to a tracking file before exiting. This creates a mechanical record that a reviewer was actually dispatched via the Agent tool -- not just that a review file exists on disk.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_sdd_dispatch_log.py` with a test that verifies: when the hook processes a reviewer dispatch, it appends an entry to `reports/.dispatch-log`.

```python
def test_reviewer_dispatch_creates_log_entry():
    """When hook processes a reviewer dispatch, it should append to .dispatch-log."""
    # Setup: create reports/ dir, simulate reviewer dispatch input
    # Run: invoke hook with reviewer-like description
    # Assert: reports/.dispatch-log exists and contains entry with task number + review type
```

(Full test code in Task 8 -- this step just establishes the contract.)

- [ ] **Step 2: Add dispatch log section to hook**

Insert the following section in `sdd-pre-dispatch-hook.sh` BETWEEN the `IS_REVIEWER` detection block (line 67-69) and the early exit (line 73). The existing `exit 0` for reviewers moves to after the logging.

Replace the current reviewer early exit:
```bash
# If this is a reviewer dispatch, always allow
if [ "$IS_REVIEWER" = true ]; then
  exit 0
fi
```

With:
```bash
# If this is a reviewer dispatch, log it and allow
if [ "$IS_REVIEWER" = true ]; then
  # ─── Dispatch provenance logging ──────────────────────────────────────
  # Log reviewer dispatches to reports/.dispatch-log so the next implementer
  # dispatch can verify reviews were actually dispatched (not self-written).
  DISPATCH_LOG="reports/.dispatch-log"
  if [ -d "reports" ]; then
    # Extract task number from description (e.g., "Review task 3 spec compliance")
    REVIEW_TASK=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
    # Determine review type from description
    REVIEW_TYPE="unknown"
    if echo "$DESCRIPTION" | grep -qiE '(spec.compliance|spec.review)'; then
      REVIEW_TYPE="spec-review"
    elif echo "$DESCRIPTION" | grep -qiE '(code.quality|quality.review|superpowers-code-reviewer)'; then
      REVIEW_TYPE="quality-review"
    elif echo "$DESCRIPTION" | grep -qiE 'trace.audit'; then
      REVIEW_TYPE="trace-audit"
    fi

    if [ -n "$REVIEW_TASK" ]; then
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH reviewer task=$REVIEW_TASK type=$REVIEW_TYPE" >> "$DISPATCH_LOG"
    fi
  fi
  exit 0
fi
```

- [ ] **Step 3: Run test to verify logging works**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && .venv/bin/python3 -m pytest tests/unit/test_sdd_dispatch_log.py -v -k "test_reviewer_dispatch_creates_log_entry"
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "feat: Add dispatch provenance logging for reviewer dispatches in SDD hook"
```

---

### Task 3: Add Dispatch Provenance Verification to Implementer Gate

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (add check in the implementer enforcement section, after Check 4 at ~line 274)

**Context:** Currently Check 4 verifies that `reports/task-NNN-spec-review.md` and `reports/task-NNN-quality-review.md` files exist and are >50 bytes. This check is necessary but insufficient -- the controller can satisfy it by writing the files directly. The new check verifies that the dispatch log (written by Task 2) contains matching reviewer dispatch entries.

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_sdd_dispatch_log.py`:
```python
def test_implementer_blocked_without_dispatch_log_entries():
    """Task N dispatch should be blocked if dispatch log has no reviewer entries for task N-1."""
    # Setup: create reports/ with valid report files for task N-1 but NO dispatch log
    # Run: invoke hook with implementer dispatch for task N
    # Assert: hook exits 2 with BLOCKED message mentioning dispatch provenance
```

- [ ] **Step 2: Add dispatch provenance check**

Add a new check section INSIDE the existing `if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ]` block (after the quality review check at ~line 273, before the closing `fi` of that block). This ensures `$PREV` is in scope (set at line 212). Do NOT place it after the `fi` — `$PREV` would be unbound with `set -u`:

```bash
  # Check 4c: Dispatch provenance — verify reviewers were actually dispatched
  # Report files can be self-written by the controller. The dispatch log is written
  # by THIS HOOK when it processes Agent calls with reviewer descriptions.
  # The controller cannot forge dispatch log entries without going through the Agent tool.
  DISPATCH_LOG="reports/.dispatch-log"
  if [ -f "$DISPATCH_LOG" ]; then
    # Check for spec-review dispatch entry for previous task
    SPEC_DISPATCHED=false
    if grep -q "task=$PREV .*type=spec-review" "$DISPATCH_LOG" 2>/dev/null; then
      SPEC_DISPATCHED=true
    fi

    # Check for quality-review dispatch entry for previous task
    # quality-review-minimum-tier is acceptable if the report file matches that pattern
    QUAL_DISPATCHED=false
    QUAL_GLOB_MIN=$(task_report_glob "$PREV" "quality-review-minimum-tier")
    HAS_MINIMUM_TIER=$(ls $QUAL_GLOB_MIN 2>/dev/null | head -1)
    if grep -q "task=$PREV .*type=quality-review" "$DISPATCH_LOG" 2>/dev/null; then
      QUAL_DISPATCHED=true
    elif [ -n "$HAS_MINIMUM_TIER" ]; then
      # Minimum tier allows controller-written quality review (no dispatch needed)
      # BUT only if a spec review WAS dispatched
      QUAL_DISPATCHED=true
    fi

    if [ "$SPEC_DISPATCHED" = false ]; then
      ERRORS+=("BLOCKED: No spec-review dispatch recorded for Task $PREV. The dispatch log (reports/.dispatch-log) has no entry for a spec reviewer being dispatched via the Agent tool. Spec reviews must be dispatched subagents, not self-written by the controller. Dispatch the spec reviewer now.")
    fi

    if [ "$QUAL_DISPATCHED" = false ]; then
      ERRORS+=("BLOCKED: No quality-review dispatch recorded for Task $PREV. Dispatch the code quality reviewer via the Agent tool. Controller-written quality reviews are only allowed for minimum-tier tasks (and the file must be named task-NNN-quality-review-minimum-tier.md).")
    fi
  else
    # No dispatch log exists at all — first task or log was deleted
    # For Task 1+, this is suspicious (Task 0 wouldn't have a prior review)
    if [ "$PREV" -gt 0 ] 2>/dev/null; then
      ERRORS+=("BLOCKED: No dispatch log found (reports/.dispatch-log). This file is created automatically by the SDD hook when reviewers are dispatched. Its absence means no reviewers were dispatched via the Agent tool for any task. Start by dispatching the spec reviewer for Task $PREV.")
    fi
  fi
```

- [ ] **Step 3: Run tests**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && .venv/bin/python3 -m pytest tests/unit/test_sdd_dispatch_log.py -v
```
Expected: All dispatch log tests PASS

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "feat: Add dispatch provenance verification — block if reviewers not dispatched"
```

---

### Task 4: Convert Token Estimation SKIPPED to BLOCK

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (Check 6, lines 314-356)

**Context:** When token estimation can't find the task header in any plan file, it currently sets `TOKEN_WARNING="TOKEN ESTIMATION SKIPPED: ..."` and injects it as `additionalContext`. This is advisory -- the dispatch proceeds. Under context pressure, the controller ignores this warning. The fix: when estimation is SKIPPED (not failed due to script error, but skipped because the plan/task couldn't be found), block the dispatch.

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_sdd_hard_gates.py`:
```python
def test_token_estimation_skipped_blocks_dispatch():
    """When plan file exists but task header not found, dispatch should be blocked."""
    # Setup: create a plan file in docs/imp-plans/ with Task 1 only
    # Run: invoke hook with implementer dispatch for Task 5 (not in plan)
    # Assert: hook exits 2 with BLOCKED message about token estimation
```

- [ ] **Step 2: Convert SKIPPED warnings to ERRORS**

In the token estimation section (Check 6), change the two `TOKEN_WARNING` assignments for SKIPPED conditions to `ERRORS+=` entries:

Replace:
```bash
    TOKEN_WARNING="TOKEN ESTIMATION SKIPPED: Task $TASK_NUMBER header not found in plan files (searched:${SEARCHED_DIRS}). Token budget check could not run. Verify task numbering matches plan headers."
```

With:
```bash
    ERRORS+=("BLOCKED: Token estimation could not run for Task $TASK_NUMBER — task header not found in plan files (searched:${SEARCHED_DIRS}). Verify task numbering matches plan headers (expected: '### Task $TASK_NUMBER'). The token budget check is mandatory before dispatch.")
```

Replace:
```bash
    TOKEN_WARNING="TOKEN ESTIMATION SKIPPED: No plan files found in docs/imp-plans/ or docs/plans/. Token budget check could not run for Task $TASK_NUMBER."
```

With:
```bash
    ERRORS+=("BLOCKED: Token estimation could not run for Task $TASK_NUMBER — no plan files found in docs/imp-plans/ or docs/plans/. Create the plan file or ensure it is in the expected location.")
```

Keep the `TOKEN ESTIMATION FAILED` case as a warning (script error is a different failure mode -- the script exists but produced no output, which may be a transient issue).

- [ ] **Step 3: Run tests**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && .venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v -k "test_token_estimation"
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "feat: Convert token estimation SKIPPED to blocking gate"
```

---

### Task 5: Convert Context Summary Warning to BLOCK at Midpoint

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (Check 6b, lines 358-382)

**Context:** When the controller is past the midpoint of task execution and `reports/context-summary.md` doesn't exist, the hook currently injects a `CONTEXT_SUMMARY_WARNING` in `additionalContext`. The fix: make this a blocking gate. Context pressure is the proximate cause of review-skipping and the context summary is the prescribed remedy.

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_sdd_hard_gates.py`:
```python
def test_context_summary_required_at_midpoint():
    """Past midpoint, dispatch should be blocked without context-summary.md."""
    # Setup: plan with 10 tasks, create reports for tasks 0-4
    # Run: invoke hook for task 6 dispatch (past midpoint of 5)
    # Assert: hook exits 2 with BLOCKED message about context summary
```

- [ ] **Step 2: Convert warning to ERRORS entry**

Replace:
```bash
      if [ ! -f "reports/context-summary.md" ]; then
        CONTEXT_SUMMARY_WARNING="CONTEXT SUMMARY REQUIRED: You are at Task $TASK_NUMBER of $TOTAL_TASKS (past midpoint $MIDPOINT). Run context-summary.py to compress completed task reports before proceeding: python3 ~/.claude/skills/superpowers/subagent-driven-development/scripts/context-summary.py --reports-dir reports/ --deviations-file DEVIATIONS.md --output reports/context-summary.md"
      fi
```

With:
```bash
      if [ ! -f "reports/context-summary.md" ]; then
        ERRORS+=("BLOCKED: Context summary required at midpoint. You are at Task $TASK_NUMBER of $TOTAL_TASKS (past midpoint $MIDPOINT). Run context-summary.py before dispatching: python3 ~/.claude/skills/superpowers/subagent-driven-development/scripts/context-summary.py --reports-dir reports/ --deviations-file DEVIATIONS.md --output reports/context-summary.md")
      fi
```

Also remove the `CONTEXT_SUMMARY_WARNING` variable and its injection into `additionalContext` later in the script (the `if [ -n "$CONTEXT_SUMMARY_WARNING" ]` block near line 443) since the condition is now handled as a blocking error.

- [ ] **Step 3: Run tests**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && .venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v -k "test_context_summary"
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "feat: Convert context summary midpoint warning to blocking gate"
```

---

### Task 6: Add Controller Checkpoint File Gate

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (add new check section after Check 5b)

**Context:** The controller is supposed to run `controller-checkpoint.py --phase pre-dispatch` before each task dispatch. Currently this is advisory-only instruction in the SKILL.md. The fix: the pre-dispatch hook checks for evidence that the checkpoint was run. The checkpoint script outputs JSON to stdout -- the controller must save this output to a file. The hook checks the file exists.

The approach: require a `reports/checkpoint-pre-dispatch-NNN.json` file for the CURRENT task (not previous). This forces the controller to run the checkpoint script and save its output before dispatching.

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_sdd_hard_gates.py`:
```python
def test_checkpoint_file_required_before_dispatch():
    """Dispatch should be blocked without checkpoint-pre-dispatch-NNN.json."""
    # Setup: valid reports for previous task, no checkpoint file for current task
    # Run: invoke hook for task N dispatch
    # Assert: hook exits 2 with BLOCKED message about checkpoint
```

- [ ] **Step 2: Add checkpoint file check**

Add a new check section after Check 5b (pending deviations) and before Check 6 (token estimation):

```bash
# Check 5c: Controller checkpoint evidence
# The controller must run controller-checkpoint.py --phase pre-dispatch before each
# dispatch and save the JSON output. This replaces the advisory instruction with
# a mechanical gate.
if [ -n "$TASK_NUMBER" ]; then
  TASK_PADDED=$(printf "%03d" "$TASK_NUMBER" 2>/dev/null || echo "$TASK_NUMBER")
  CHECKPOINT_FILE="reports/checkpoint-pre-dispatch-${TASK_PADDED}.json"
  if [ ! -f "$CHECKPOINT_FILE" ]; then
    ERRORS+=("BLOCKED: No pre-dispatch checkpoint found for Task $TASK_NUMBER (expected: $CHECKPOINT_FILE). Run controller-checkpoint.py and save the output: python3 ~/.claude/skills/superpowers/subagent-driven-development/scripts/controller-checkpoint.py --phase pre-dispatch --task-number $TASK_NUMBER --plan-file <plan.md> --deviations-file DEVIATIONS.md --reports-dir reports/ > $CHECKPOINT_FILE")
  elif [ "$(wc -c < "$CHECKPOINT_FILE" 2>/dev/null | tr -d ' ')" -lt "$MIN_REPORT_BYTES" ]; then
    ERRORS+=("BLOCKED: Checkpoint file $CHECKPOINT_FILE is too small (< $MIN_REPORT_BYTES bytes). Run the full controller-checkpoint.py command and redirect its JSON output to this file.")
  fi
fi
```

- [ ] **Step 3: Run tests**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && .venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v -k "test_checkpoint"
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "feat: Add controller checkpoint file gate to pre-dispatch hook"
```

---

### Task 7: Extend Report Guard to Protect Dispatch Log

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-report-guard.sh`

**Context:** The report guard currently watches for suspicious `Bash` commands that create empty report files (touch, empty echo/cat redirects). The new dispatch log (`reports/.dispatch-log`) is a critical enforcement artifact -- if the controller can write to it via Bash, it can forge dispatch provenance entries. Extend the guard to detect and warn about direct writes to `.dispatch-log`.

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_sdd_dispatch_log.py`:
```python
def test_report_guard_warns_on_dispatch_log_manipulation():
    """Report guard should warn when Bash command targets .dispatch-log."""
    # Setup: simulate Bash hook input with command: echo "fake" >> reports/.dispatch-log
    # Run: invoke report guard hook
    # Assert: stderr contains WARNING about dispatch log manipulation
```

- [ ] **Step 2: Add dispatch log protection**

In `sdd-report-guard.sh`, insert a new detection block BEFORE the existing `reports/task-` early-exit check (line 25). The early exit at line 25 (`if ! echo "$COMMAND" | grep -qiE 'reports/task-'; then exit 0; fi`) would skip the new code because `.dispatch-log` doesn't contain `reports/task-`. Insert the new block between lines 22-24 (after `COMMAND` is extracted) and line 25 (before the `reports/task-` check):

```bash
# Detect direct manipulation of the dispatch provenance log
if echo "$COMMAND" | grep -qiE '\.dispatch-log'; then
  echo "" >&2
  echo "WARNING: Direct manipulation of dispatch provenance log detected." >&2
  echo "Command: $COMMAND" >&2
  echo "" >&2
  echo "The .dispatch-log file is written automatically by the SDD pre-dispatch" >&2
  echo "hook when reviewer subagents are dispatched. Manual writes to this file" >&2
  echo "compromise review provenance tracking. If you need to reset the log," >&2
  echo "delete reports/.dispatch-log and re-dispatch all pending reviewers." >&2
  echo "" >&2
fi
```

- [ ] **Step 3: Run tests**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && .venv/bin/python3 -m pytest tests/unit/test_sdd_dispatch_log.py -v -k "test_report_guard"
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-report-guard.sh
git commit -m "feat: Extend report guard to detect dispatch log manipulation"
```

---

### Task 8: Create Shared Test Helpers and Dispatch Provenance Tests

**Files:**
- Create: `tests/unit/sdd_test_helpers.py`
- Create: `tests/unit/test_sdd_dispatch_log.py`

**Context:** Tests for Tasks 2, 3, and 7. Tests invoke hook scripts via subprocess with JSON input matching the Claude Code PreToolUse payload format. Shared helpers are extracted to avoid duplication with Task 9's tests. Follow the existing test pattern in `tests/unit/test_controller_checkpoint_stale.py`.

- [ ] **Step 1: Create shared helper module**

Create `tests/unit/sdd_test_helpers.py` with these functions (follow patterns from existing tests):

```python
# Key functions to implement:
def make_hook_input(description: str, prompt: str = "", cwd: str = "") -> str:
    """JSON payload matching Claude Code PreToolUse hook input."""

def setup_sdd_workspace(tmpdir: str, task_count: int) -> None:
    """Create: reports/, DEVIATIONS.md, pre-execution-audit (>50 bytes), plan with N task headers, git init on feature branch."""

def create_task_reports(tmpdir: str, task_number: int, include_dispatch_log: bool = True) -> None:
    """Create: implementer-report (9 required sections, >50 bytes), spec-review, quality-review. Optionally append to .dispatch-log."""

def setup_full_sdd_workspace(tmpdir: str, total_tasks: int, completed_tasks: int) -> None:
    """Full workspace: plan, DEVIATIONS.md, audit, reports + dispatch log + checkpoint files for all completed tasks."""
```

Important implementation details:
- Implementer reports must have all 9 sections from `validate-report.py` (Status, Implementation Summary, Files Changed, Source Files Read, Tests, Contract Compliance, Deviations from Plan, Self-Review Findings, Concerns)
- All report files must be >50 bytes (`MIN_REPORT_BYTES` in the hook)
- Checkpoint files: `reports/checkpoint-pre-dispatch-NNN.json` with `{"status": "PASS"}` (>50 bytes)
- Dispatch log entries: `YYYY-MM-DDTHH:MM:SSZ DISPATCH reviewer task=N type={spec-review|quality-review}`
- Git init with `feature-test` branch (hook checks branch name)
- Plan source contracts must be "None" (not "None -- explanation")

- [ ] **Step 2: Create dispatch provenance test file**

Create `tests/unit/test_sdd_dispatch_log.py` with these test classes (using helpers from step 1):

```python
class TestReviewerDispatchLogging:  # Task 2 verification
    def test_reviewer_dispatch_creates_log_entry(self, tmp_path):
        # Input: description="Review task 3 spec compliance", reports/ dir exists
        # Assert: exit 0, reports/.dispatch-log has "task=3" and "type=spec-review"

    def test_quality_reviewer_dispatch_logged(self, tmp_path):
        # Input: description="Dispatch code quality review for task 5"
        # Assert: .dispatch-log has "task=5" and "type=quality-review"

    def test_non_reviewer_dispatch_does_not_add_log_entry(self, tmp_path):
        # Input: full SDD workspace, implementer dispatch for task 1
        # Assert: no new "task=1" reviewer entry in .dispatch-log

class TestDispatchProvenanceVerification:  # Task 3 verification
    def test_blocked_without_dispatch_log(self, tmp_path):
        # Setup: task 0 reports exist, NO .dispatch-log, checkpoint for task 1
        # Assert: exit 2, stderr mentions "dispatch"

    def test_allowed_with_valid_dispatch_log(self, tmp_path):
        # Setup: task 0 reports + dispatch log + checkpoint for task 1
        # Assert: exit 0

    def test_minimum_tier_quality_allowed_without_dispatch(self, tmp_path):
        # Setup: spec-review in dispatch log, quality-review-minimum-tier.md file (no quality dispatch)
        # Assert: exit 0 (minimum tier exempts quality dispatch requirement)

class TestReportGuardDispatchLog:  # Task 7 verification
    def test_warns_on_dispatch_log_echo(self):
        # Input to GUARD hook: command='echo "fake" >> reports/.dispatch-log'
        # Assert: exit 0 (warning only), stderr contains "WARNING" and "dispatch"

    def test_no_warning_for_unrelated_command(self):
        # Input to GUARD hook: command="ls -la reports/"
        # Assert: exit 0, stderr does NOT contain "dispatch"
```

- [ ] **Step 3: Run tests (expect failures until Tasks 2, 3, 7 are implemented)**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && .venv/bin/python3 -m pytest tests/unit/test_sdd_dispatch_log.py -v
```

- [ ] **Step 4: Commit**

```bash
git add tests/unit/sdd_test_helpers.py tests/unit/test_sdd_dispatch_log.py
git commit -m "test: Add dispatch provenance tests and shared SDD test helpers"
```

---

### Task 9: Write Hard Gate Tests

**Files:**
- Create: `tests/unit/test_sdd_hard_gates.py`

**Context:** Tests for Tasks 4, 5, and 6. Uses shared helpers from `sdd_test_helpers.py`.

- [ ] **Step 1: Create hard gate test file**

Create `tests/unit/test_sdd_hard_gates.py` with these test classes:

```python
class TestTokenEstimationBlocking:  # Task 4 verification
    def test_blocks_when_task_header_not_in_plan(self, tmp_path):
        # Setup: full workspace with 3 tasks, dispatch task 99 (not in plan)
        # Assert: exit 2, stderr mentions "token" or "BLOCKED"

    def test_allows_when_task_header_found(self, tmp_path):
        # Setup: full workspace with 5 tasks, dispatch task 1 (in plan)
        # Assert: exit 0

class TestContextSummaryBlocking:  # Task 5 verification
    def test_blocks_past_midpoint_without_summary(self, tmp_path):
        # Setup: 10 tasks, 6 completed (past midpoint 5), no context-summary.md
        # Assert: exit 2, stderr mentions "context" or "midpoint"

    def test_allows_past_midpoint_with_summary(self, tmp_path):
        # Setup: same as above + reports/context-summary.md (>50 bytes)
        # Assert: exit 0

    def test_allows_before_midpoint_without_summary(self, tmp_path):
        # Setup: 10 tasks, 2 completed (before midpoint), no summary
        # Assert: exit 0

class TestCheckpointFileGate:  # Task 6 verification
    def test_blocks_without_checkpoint_file(self, tmp_path):
        # Setup: full workspace, remove checkpoint-pre-dispatch-001.json
        # Assert: exit 2, stderr mentions "checkpoint"

    def test_allows_with_checkpoint_file(self, tmp_path):
        # Setup: full workspace (includes checkpoint files)
        # Assert: exit 0

    def test_blocks_with_tiny_checkpoint_file(self, tmp_path):
        # Setup: overwrite checkpoint with "{}" (2 bytes, below 50-byte minimum)
        # Assert: exit 2
```

- [ ] **Step 2: Run tests (expect failures until Tasks 4, 5, 6 are implemented)**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && .venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v
```

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_sdd_hard_gates.py
git commit -m "test: Add hard gate enforcement tests for SDD hook"
```

---

### Task 10: Integration Verification and Documentation Update

**Files:**
- Read: all modified files
- Modify: `CLAUDE.md` (documentation section updates)

**Context:** Verify all changes work together. Run the full test suite. Update CLAUDE.md to document the new enforcement layers.

- [ ] **Step 1: Run all unit tests**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && .venv/bin/python3 -m pytest tests/unit/ -v
```
Expected: All tests PASS (existing 20 + new tests from Tasks 8-9)

- [ ] **Step 2: Run skill regression tests**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && python3 tests/ARaymond-skill-regression/validate-all-skills.py
```
Expected: All 122 checks PASS

- [ ] **Step 3: Run installation verification**

```bash
cd /Users/araymond/projects/claude-custom/superpowers && bash tests/ARaymond-installation/verify-symlink-install.sh
```
Expected: All 101 checks PASS

- [ ] **Step 4: Update CLAUDE.md documentation**

Update the following sections in `CLAUDE.md`:

1. **"SDD Hooks Enforcement Architecture"** (or "Hooks-Based Enforcement"): Add documentation for:
   - Dispatch provenance log (`reports/.dispatch-log`) and how it's created/verified
   - Checkpoint file gate (`reports/checkpoint-pre-dispatch-NNN.json`)
   - Token estimation and context summary now block instead of warn

2. **"Global Settings Changes"**: Note the updated permission glob

3. **"Testing" section**: Update test counts (existing 20 + new tests)

- [ ] **Step 5: Update customization manifest**

Update `docs/ARaymond-customization-manifest.md` to document the new enforcement layers.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md docs/ARaymond-customization-manifest.md
git commit -m "docs: Update documentation for SDD enforcement hardening"
```

---

## Acceptance Criteria

1. Permission glob fix: `Skill` tool invocation of `superpowers:subagent-driven-development` succeeds without permission prompts in autonomous sessions
2. Dispatch provenance: controller cannot satisfy the review gate by self-writing review files -- a dispatched Agent call with reviewer description is required for each task's spec review
3. Token estimation: dispatch is blocked (exit 2) when estimation is SKIPPED, not just warned
4. Context summary: dispatch is blocked (exit 2) past the midpoint without `reports/context-summary.md`
5. Controller checkpoint: dispatch is blocked (exit 2) without `reports/checkpoint-pre-dispatch-NNN.json` for the current task
6. Report guard: warns on direct Bash manipulation of `.dispatch-log`
7. All existing tests continue to pass (20 existing + new tests)
8. All 3 test suites pass: unit tests, skill regression (122 checks), installation verification (101 checks)
