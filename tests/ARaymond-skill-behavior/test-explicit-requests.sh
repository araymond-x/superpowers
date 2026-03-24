#!/usr/bin/env bash
# Test explicit skill requests with premature action detection
# Adapted from upstream tests/explicit-skill-requests/ for symlink install.
# Reuses upstream prompt files where they exist.
set -uo pipefail
# No -e: all tests run even if one fails. print_summary handles exit code.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

UPSTREAM_PROMPTS="$REPO_ROOT/tests/explicit-skill-requests/prompts"

echo "=== Explicit Skill Requests (symlink install) ==="

# Test 1: SDD explicit request
echo ""
echo "--- Test 1: subagent-driven-development explicit ---"
PROMPT=$(cat "$UPSTREAM_PROMPTS/subagent-driven-development-please.txt")
LOG=$(run_claude_log "$PROMPT" 120 3)
assert_skill_triggered "$LOG" "subagent-driven-development"
assert_no_premature_action "$LOG"

# Test 2: brainstorming explicit request
echo ""
echo "--- Test 2: brainstorming explicit ---"
PROMPT=$(cat "$UPSTREAM_PROMPTS/please-use-brainstorming.txt")
LOG=$(run_claude_log "$PROMPT" 120 3)
assert_skill_triggered "$LOG" "brainstorming"
assert_no_premature_action "$LOG"

# Test 3: systematic-debugging explicit request
echo ""
echo "--- Test 3: systematic-debugging explicit ---"
PROMPT=$(cat "$UPSTREAM_PROMPTS/use-systematic-debugging.txt")
LOG=$(run_claude_log "$PROMPT" 120 3)
assert_skill_triggered "$LOG" "systematic-debugging"
assert_no_premature_action "$LOG"

# Test 4: handoff-acceptance explicit (custom skill — new prompt)
echo ""
echo "--- Test 4: handoff-acceptance explicit (custom) ---"
LOG=$(run_claude_log "please use superpowers:handoff-acceptance to verify the handoff package" 120 3)
assert_skill_triggered "$LOG" "handoff-acceptance"

print_summary
