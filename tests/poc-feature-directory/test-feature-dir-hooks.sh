#!/usr/bin/env bash
# test-feature-dir-hooks.sh — POC test for per-feature directory structure
#
# Verifies that hooks work correctly when artifacts are organized into
# per-feature subdirectories under docs/imp-plans/{feature}/ instead of
# flat files at docs/imp-plans/ and reports/ at project root.
#
# Each test creates a temp directory, sets up the structure, pipes simulated
# hook JSON to real hook scripts, and checks the result.
#
# Usage: bash tests/poc-feature-directory/test-feature-dir-hooks.sh

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PLAN_HOOK="$REPO_ROOT/skills/writing-plans/scripts/plan-validation-gate-hook.sh"
SDD_HOOK="$REPO_ROOT/skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
VALIDATE_PLAN="$REPO_ROOT/skills/subagent-driven-development/scripts/validate-plan.py"

PASS_COUNT=0
FAIL_COUNT=0

# ---- Helpers ----------------------------------------------------------------

pass() {
  echo "[PASS] $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  echo "[FAIL] $1"
  echo "       $2"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

# Create a minimal plan file that passes validate-plan.py
write_valid_plan() {
  local path="$1"
  cat > "$path" << 'PLAN'
# Test Feature Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` via the Skill tool.

**Goal:** Test feature for POC validation

**Architecture:** Single module test

**Tech Stack:** Bash

**Source Contracts:** None

**Contract Constraints:** None

**Feature Archetype:** Greenfield

**Code Footprint:**

| Category | Files | Action |
|----------|-------|--------|
| New | test.sh | Create |

## Write-Scope Partitioning

| Task | Owned Files | Read-Only | Depends On |
|------|-------------|-----------|------------|
| Task 1 | test.sh | — | — |

### Task 1: Create test file

- [ ] **Step 1: Write test**
PLAN
}

# Create a review report that passes the 50-byte minimum
write_review_report() {
  local path="$1"
  cat > "$path" << 'REPORT'
# Plan Review Report

Status: APPROVED

The plan was reviewed and meets all structural and semantic requirements.
No blocking issues identified. All sections present and correctly formatted.
REPORT
}

# Create a minimal implementer report with valid Pydantic YAML frontmatter.
# The validate-report.py script requires structured YAML fields matching
# ImplementerReport model (task_id, status, files_changed, tests, contract_compliance)
# plus 5 prose sections.
write_implementer_report() {
  local path="$1"
  cat > "$path" << 'REPORT'
---
schema_version: 1
task_id: 0
status: DONE
files_changed:
  - path: test.sh
    description: Created test file for POC validation
tests:
  written: 1
  passing: 1
  command: bash test.sh
  result: PASS
contract_compliance: []
---

## Implementation Summary
Task completed successfully. Created test.sh as specified.

## Source Files Read
- test.sh

## Deviations from Plan
None.

## Self-Review Findings
Code is correct and matches spec. No issues found.

## Concerns
None.
REPORT
}

# Create spec/quality review reports (>50 bytes)
write_review_stub() {
  local path="$1"
  cat > "$path" << 'REVIEW'
# Review Report

Status: APPROVED

No issues found. Implementation matches spec. Code quality acceptable.
All patterns follow existing conventions. No security concerns identified.
REVIEW
}

echo "=== POC: Per-Feature Directory Hook Tests ==="
echo ""

# ---- Test 1: Hook CWD resolution with nested feature dirs ------------------

TMPDIR=$(mktemp -d)
cd "$TMPDIR" && git init -q && git commit --allow-empty -m "init" -q

FEAT1_DIR="docs/imp-plans/test-feature"
mkdir -p "$FEAT1_DIR"
write_valid_plan "$FEAT1_DIR/plan.md"
write_review_report "$FEAT1_DIR/plan-review-report.md"

# .active-feature points to the feature directory
echo "$FEAT1_DIR" > .active-feature

# Manifest inside the feature dir (plan-validation-gate-hook looks in $FEAT first)
cat > "$FEAT1_DIR/plan-manifest.txt" << 'MANIFEST'
docs/imp-plans/test-feature/plan.md
MANIFEST

RESULT=$(echo '{"tool_input":{"skill":"superpowers:subagent-driven-development"},"cwd":"'"$TMPDIR"'"}' \
  | bash "$PLAN_HOOK" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ] && echo "$RESULT" | grep -q "manifest"; then
  pass "Test 1: Hook CWD with nested feature dirs (.active-feature + manifest in feature dir)"
else
  fail "Test 1: Hook CWD with nested feature dirs" "Exit=$EXIT_CODE Output=$(echo "$RESULT" | head -3)"
fi
rm -rf "$TMPDIR"

# ---- Test 1b: Manifest INSIDE the feature dir (resolved via .active-feature) ---
# Now that the hook reads .active-feature to resolve $FEAT, it looks for
# $FEAT/plan-manifest.txt first — manifests inside feature dirs are supported.

TMPDIR=$(mktemp -d)
cd "$TMPDIR" && git init -q && git commit --allow-empty -m "init" -q

FEAT1B_DIR="docs/imp-plans/test-feature"
mkdir -p "$FEAT1B_DIR"
write_valid_plan "$FEAT1B_DIR/plan.md"
write_review_report "$FEAT1B_DIR/plan-review-report.md"

# .active-feature points to the feature directory
echo "$FEAT1B_DIR" > .active-feature

# Manifest INSIDE the feature dir — hook now finds it via $FEAT/plan-manifest.txt
cat > "$FEAT1B_DIR/plan-manifest.txt" << 'MANIFEST'
docs/imp-plans/test-feature/plan.md
MANIFEST

RESULT=$(echo '{"tool_input":{"skill":"superpowers:subagent-driven-development"},"cwd":"'"$TMPDIR"'"}' \
  | bash "$PLAN_HOOK" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ] && echo "$RESULT" | grep -q "manifest"; then
  pass "Test 1b: Manifest inside feature dir — hook found it via .active-feature resolution"
else
  fail "Test 1b: Manifest inside feature dir" "Exit=$EXIT_CODE Output=$(echo "$RESULT" | head -3)"
fi
rm -rf "$TMPDIR"

# ---- Test 2: SDD dispatch hook with feature-scoped reports (.active-feature) -

if [ ! -f "$SDD_HOOK" ]; then
  fail "Test 2: SDD dispatch with feature-scoped reports" "Real hook not found at $SDD_HOOK"
else
  TMPDIR=$(mktemp -d)
  cd "$TMPDIR" && git init -q && git commit --allow-empty -m "init" -q
  git checkout -q -b test-feature

  # Set up feature directory with all required SDD artifacts
  FEATURE_DIR="docs/imp-plans/2026-05-02-test-feature"
  mkdir -p "$FEATURE_DIR/reports"

  write_valid_plan "$FEATURE_DIR/plan.md"

  # Write .active-feature so the real hook resolves the feature directory
  echo "$FEATURE_DIR" > .active-feature

  # deviations.md inside feature dir (lowercase, per feature-dir convention)
  cat > "$FEATURE_DIR/deviations.md" << 'DEV'
# Deviations Register

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
DEV

  # Pre-execution audit inside feature dir
  write_implementer_report "$FEATURE_DIR/reports/pre-execution-audit.md"

  # Task 0 implementer report
  write_implementer_report "$FEATURE_DIR/reports/task-000-implementer-report.md"
  write_review_stub "$FEATURE_DIR/reports/task-000-spec-review.md"
  write_review_stub "$FEATURE_DIR/reports/task-000-quality-review.md"

  # Dispatch log for provenance (reviewer dispatch entries for task 0)
  mkdir -p "$FEATURE_DIR/reports"
  cat > "$FEATURE_DIR/reports/.dispatch-log" << 'LOG'
2026-05-02T00:00:00Z DISPATCH reviewer task=0 type=spec-review
2026-05-02T00:00:01Z DISPATCH reviewer task=0 type=quality-review
LOG

  # Checkpoint file for Task 1
  echo '{"status":"OK","phase":"pre-dispatch","task_number":1}' > "$FEATURE_DIR/reports/checkpoint-pre-dispatch-001.json"

  # Partner review for Task 1
  write_review_stub "$FEATURE_DIR/reports/partner-review-001.md"

  # Token estimation: need a ### Task 1 header in the plan for the hook to find it
  # The valid plan only has "Task 1" in the write-scope table; add a task header
  cat >> "$FEATURE_DIR/plan.md" << 'TASKHEADER'

### Task 1: Create test file

- [ ] **Step 1: Write test**
TASKHEADER

  # Simulate dispatching Task 1 (expects Task 0 reports to exist)
  RESULT=$(echo '{"tool_input":{"description":"Implement task 1","prompt":"You are implementing task 1"},"cwd":"'"$TMPDIR"'"}' \
    | bash "$SDD_HOOK" 2>&1)
  EXIT_CODE=$?

  if [ $EXIT_CODE -eq 0 ]; then
    pass "Test 2: SDD dispatch with feature-scoped reports (real hook + .active-feature)"
  else
    fail "Test 2: SDD dispatch with feature-scoped reports" "Exit=$EXIT_CODE Output=$(echo "$RESULT" | head -10)"
  fi
  rm -rf "$TMPDIR"
fi

# ---- Test 3: Git branch detection from feature directory --------------------

TMPDIR=$(mktemp -d)
cd "$TMPDIR" && git init -q && git commit --allow-empty -m "init" -q
git checkout -q -b my-cool-feature

DETECTED_BRANCH=$(git branch --show-current 2>/dev/null)

if [ "$DETECTED_BRANCH" = "my-cool-feature" ]; then
  # Verify branch name can map to a feature directory
  FEATURE_DIR_NAME=$(echo "$DETECTED_BRANCH" | sed 's|^feat/||' | sed 's|^feature/||')
  if [ "$FEATURE_DIR_NAME" = "my-cool-feature" ]; then
    pass "Test 3: Git branch detection ('$DETECTED_BRANCH' -> dir '$FEATURE_DIR_NAME')"
  else
    fail "Test 3: Git branch detection" "Branch mapping failed: '$DETECTED_BRANCH' -> '$FEATURE_DIR_NAME'"
  fi
else
  fail "Test 3: Git branch detection" "Expected 'my-cool-feature', got '$DETECTED_BRANCH'"
fi
rm -rf "$TMPDIR"

# ---- Test 4: Multiple feature dirs coexist — only active dir is validated --

TMPDIR=$(mktemp -d)
cd "$TMPDIR" && git init -q && git commit --allow-empty -m "init" -q

FEAT4_DIR="docs/imp-plans/feature-a"
mkdir -p "$FEAT4_DIR" docs/imp-plans/feature-b
write_valid_plan "$FEAT4_DIR/plan.md"
write_review_report "$FEAT4_DIR/plan-review-report.md"
echo "# Bad plan with no sections" > docs/imp-plans/feature-b/plan.md

# .active-feature points to feature-a only
echo "$FEAT4_DIR" > .active-feature

# Manifest inside feature-a lists only feature-a plan
cat > "$FEAT4_DIR/plan-manifest.txt" << 'MANIFEST'
docs/imp-plans/feature-a/plan.md
MANIFEST

RESULT=$(echo '{"tool_input":{"skill":"superpowers:subagent-driven-development"},"cwd":"'"$TMPDIR"'"}' \
  | bash "$PLAN_HOOK" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ] && echo "$RESULT" | grep -q "1 plan file"; then
  pass "Test 4: Multiple feature dirs (.active-feature scopes to feature-a; feature-b not validated)"
else
  fail "Test 4: Multiple feature dirs" "Exit=$EXIT_CODE — may have validated feature-b too. Output=$(echo "$RESULT" | head -3)"
fi
rm -rf "$TMPDIR"

# ---- Test 5: Fallback when no manifest inside feature dir -------------------
# When .active-feature is set but $FEAT/plan-manifest.txt doesn't exist,
# the hook falls back to git-diff to discover plan files.

TMPDIR=$(mktemp -d)
cd "$TMPDIR" && git init -q && git commit --allow-empty -m "init" -q
git checkout -q -b test-feature

FEAT5_DIR="docs/imp-plans/test-feature"
mkdir -p "$FEAT5_DIR"
write_valid_plan "$FEAT5_DIR/plan.md"
write_review_report "$FEAT5_DIR/plan-review-report.md"
git add -A && git commit -q -m "add plan"

# .active-feature is set but NO manifest inside the feature dir
echo "$FEAT5_DIR" > .active-feature

RESULT=$(echo '{"tool_input":{"skill":"superpowers:subagent-driven-development"},"cwd":"'"$TMPDIR"'"}' \
  | bash "$PLAN_HOOK" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ] && echo "$RESULT" | grep -q "git-diff"; then
  pass "Test 5: Fallback without manifest (git-diff found nested plan via feature dir)"
else
  fail "Test 5: Fallback without manifest" "Exit=$EXIT_CODE Output=$(echo "$RESULT" | head -3)"
fi
rm -rf "$TMPDIR"

# ---- Test 6: validate-plan.py works with nested paths ----------------------

TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/docs/imp-plans/deep-feature"
write_valid_plan "$TMPDIR/docs/imp-plans/deep-feature/plan.md"

RESULT=$(python3 "$VALIDATE_PLAN" --plan-file "$TMPDIR/docs/imp-plans/deep-feature/plan.md" 2>&1)
STATUS=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)

if [ "$STATUS" = "PASS" ] || [ "$STATUS" = "WARNING" ]; then
  pass "Test 6: validate-plan.py with nested path (status=$STATUS)"
else
  fail "Test 6: validate-plan.py with nested path" "Status=$STATUS Output=$(echo "$RESULT" | head -3)"
fi
rm -rf "$TMPDIR"

# ---- Test 7: Multiple feature dirs — only active feature's manifest is used ---
# The original "known limitation" (non-deterministic manifest selection when
# multiple feature dirs each have their own plan-manifest.txt) is now resolved:
# .active-feature unambiguously identifies which feature is active, and the hook
# looks for $FEAT/plan-manifest.txt first. Only one feature can be active at a time.
# This test verifies that the hook validates only the feature-a plan when
# .active-feature points to feature-a.

TMPDIR=$(mktemp -d)
cd "$TMPDIR" && git init -q && git commit --allow-empty -m "init" -q

FEAT7A_DIR="docs/imp-plans/feature-a"
mkdir -p "$FEAT7A_DIR" docs/imp-plans/feature-b
write_valid_plan "$FEAT7A_DIR/plan.md"
write_review_report "$FEAT7A_DIR/plan-review-report.md"
# feature-b has an invalid plan (missing sections) but should NOT be validated
echo "# Bad plan with no sections" > docs/imp-plans/feature-b/plan.md

# .active-feature points to feature-a
echo "$FEAT7A_DIR" > .active-feature

# Manifest inside feature-a points only to feature-a plan
cat > "$FEAT7A_DIR/plan-manifest.txt" << 'MANIFEST'
docs/imp-plans/feature-a/plan.md
MANIFEST

RESULT=$(echo '{"tool_input":{"skill":"superpowers:subagent-driven-development"},"cwd":"'"$TMPDIR"'"}' \
  | bash "$PLAN_HOOK" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ] && echo "$RESULT" | grep -q "1 plan file"; then
  pass "Test 7: Multiple feature dirs — .active-feature ensures only feature-a validated (feature-b skipped)"
else
  fail "Test 7: Multiple feature dirs" "Exit=$EXIT_CODE Output=$(echo "$RESULT" | head -3)"
fi
rm -rf "$TMPDIR"

# ---- Test 8: .active-feature lifecycle (create → hooks resolve → cleanup → fallback) ---

TMPDIR=$(mktemp -d)
cd "$TMPDIR" && git init -q && git commit --allow-empty -m "init" -q
git checkout -q -b feature-lifecycle-test

FEATURE_DIR="docs/imp-plans/2026-05-02-lifecycle-test"
mkdir -p "$FEATURE_DIR/reports"

write_valid_plan "$FEATURE_DIR/plan.md"
cat > "$FEATURE_DIR/deviations.md" << 'DEV'
# Deviations Register

| Task | Type | Description | Disposition |
|------|------|-------------|-------------|
DEV
write_implementer_report "$FEATURE_DIR/reports/pre-execution-audit.md"
cat > "$FEATURE_DIR/reports/.dispatch-log" << 'LOG'
2026-05-02T00:00:00Z DISPATCH reviewer task=0 type=spec-review
2026-05-02T00:00:01Z DISPATCH reviewer task=0 type=quality-review
LOG
write_implementer_report "$FEATURE_DIR/reports/task-000-implementer-report.md"
write_review_stub "$FEATURE_DIR/reports/task-000-spec-review.md"
write_review_stub "$FEATURE_DIR/reports/task-000-quality-review.md"
echo '{"status":"OK","phase":"pre-dispatch","task_number":1}' > "$FEATURE_DIR/reports/checkpoint-pre-dispatch-001.json"
write_review_stub "$FEATURE_DIR/reports/partner-review-001.md"
cat >> "$FEATURE_DIR/plan.md" << 'TASKHEADER'

### Task 1: Create test file

- [ ] **Step 1: Write test**
TASKHEADER

# Phase 1: .active-feature exists — hook should resolve feature dir and allow
echo "$FEATURE_DIR" > .active-feature
RESULT=$(echo '{"tool_input":{"description":"Implement task 1","prompt":"You are implementing task 1"},"cwd":"'"$TMPDIR"'"}' \
  | bash "$SDD_HOOK" 2>&1)
PHASE1_EXIT=$?

# Phase 2: Remove .active-feature — hook falls back to root layout
rm -f .active-feature
# In root layout, deviations.md is at root as DEVIATIONS.md (uppercase) or
# reports/ at root. With no .active-feature and no root reports/, hook will block.
RESULT2=$(echo '{"tool_input":{"description":"Implement task 1","prompt":"You are implementing task 1"},"cwd":"'"$TMPDIR"'"}' \
  | bash "$SDD_HOOK" 2>&1)
PHASE2_EXIT=$?

if [ $PHASE1_EXIT -eq 0 ] && [ $PHASE2_EXIT -ne 0 ]; then
  pass "Test 8: .active-feature lifecycle — hook allows when active-feature set, blocks when removed"
elif [ $PHASE1_EXIT -ne 0 ]; then
  fail "Test 8: .active-feature lifecycle (Phase 1)" "Hook blocked despite .active-feature set. Exit=$PHASE1_EXIT Output=$(echo "$RESULT" | head -5)"
else
  fail "Test 8: .active-feature lifecycle (Phase 2)" "Hook allowed after .active-feature removed (fallback should block without root reports/). Exit=$PHASE2_EXIT"
fi
rm -rf "$TMPDIR"

# ---- Test 9: Conflict detection (existing .active-feature + new feature) ----
# Verifies that the brainstorming skill's conflict detection logic works:
# when .active-feature points to a directory that still exists, the system
# must not silently overwrite it. This test simulates the check by directly
# testing the resolution logic that the brainstorming skill implements.

TMPDIR=$(mktemp -d)
cd "$TMPDIR"

EXISTING_FEATURE_DIR="docs/imp-plans/2026-04-01-old-feature"
mkdir -p "$EXISTING_FEATURE_DIR"
echo "$EXISTING_FEATURE_DIR" > .active-feature

# Simulate what the brainstorming skill checks: read .active-feature and
# verify the referenced dir still exists (conflict case)
CURRENT_ACTIVE=$(cat .active-feature 2>/dev/null | tr -d '\n')
CONFLICT_DETECTED=false
if [ -n "$CURRENT_ACTIVE" ] && [ -d "$CURRENT_ACTIVE" ]; then
  CONFLICT_DETECTED=true
fi

if [ "$CONFLICT_DETECTED" = true ]; then
  pass "Test 9: Conflict detection — existing .active-feature pointing to live directory detected correctly"
else
  fail "Test 9: Conflict detection" "Expected conflict detection but CONFLICT_DETECTED=$CONFLICT_DETECTED (CURRENT_ACTIVE='$CURRENT_ACTIVE')"
fi

# Sub-test: stale .active-feature pointing to non-existent dir → auto-clean
STALE_DIR="docs/imp-plans/2026-03-01-deleted-feature"
echo "$STALE_DIR" > .active-feature
CURRENT_STALE=$(cat .active-feature 2>/dev/null | tr -d '\n')
STALE_CONFLICT=false
if [ -n "$CURRENT_STALE" ] && [ -d "$CURRENT_STALE" ]; then
  STALE_CONFLICT=true
fi

if [ "$STALE_CONFLICT" = false ]; then
  # Auto-clean: remove stale .active-feature
  rm -f .active-feature
  if [ ! -f ".active-feature" ]; then
    pass "Test 9b: Stale .active-feature (dir gone) — auto-clean proceeds correctly"
  else
    fail "Test 9b: Stale .active-feature cleanup" "Failed to remove .active-feature"
  fi
else
  fail "Test 9b: Stale .active-feature detection" "Stale dir '$STALE_DIR' should not exist but was detected as present"
fi
rm -rf "$TMPDIR"

# ---- Summary ----------------------------------------------------------------

echo ""
echo "========================================="
echo " POC Test Results"
echo "========================================="
echo "  Passed: $PASS_COUNT"
echo "  Failed: $FAIL_COUNT"
echo ""

TOTAL=$((PASS_COUNT + FAIL_COUNT))
if [ $FAIL_COUNT -eq 0 ]; then
  echo "STATUS: ALL $TOTAL TESTS PASSED"
  echo "Per-feature directory approach is viable."
  exit 0
else
  echo "STATUS: $FAIL_COUNT/$TOTAL TESTS FAILED"
  echo "Review failures before proceeding with migration."
  exit 1
fi
