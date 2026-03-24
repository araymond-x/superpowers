#!/usr/bin/env bash
# Test SDD skill content — verifies Claude's answers about the skill.
# Adapted from upstream tests/claude-code/test-subagent-driven-development.sh
# with additional tests for custom fork features (DEVIATIONS.md, Task 0, etc.)
set -uo pipefail
# Note: no -e — we want all tests to run even if one fails. print_summary handles exit code.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== SDD Content Validation (custom fork) ==="

# Prompts include "Answer from what you know" to prevent Claude from
# spending all its turns reading files instead of answering the question.
# Max turns = 5 gives Claude room to load the skill then answer.

# --- Upstream tests (adapted) ---

echo ""
echo "--- Test 1: Review ordering ---"
output=$(run_claude "In the subagent-driven-development skill, what comes first: spec compliance review or code quality review? Answer from the skill content." 90 5)
assert_contains "$output" "spec.*compliance" "Mentions spec compliance" || true
assert_contains "$output" "before|first|then|followed" "Indicates ordering" || true

echo ""
echo "--- Test 2: Reviewer skepticism ---"
output=$(run_claude "What is the spec compliance reviewer's attitude toward the implementer's report in subagent-driven-development? Answer from the skill content, do not read files." 90 5)
assert_contains "$output" "not trust|skeptical|verify|independently|do not trust|assume.*incomplete|verify independently" "Reviewer is skeptical" || true

echo ""
echo "--- Test 3: Full task text ---"
output=$(run_claude "In subagent-driven-development, how does the controller provide task information to the implementer? Answer from the skill content." 90 5)
assert_contains "$output" "provide.*directly|full.*text|paste|include.*prompt|verbatim|directly in" "Provides text directly" || true

# --- Custom fork tests ---

echo ""
echo "--- Test 4: DEVIATIONS.md ---"
output=$(run_claude "In subagent-driven-development, what is DEVIATIONS.md and when does the controller update it? Answer from the skill content." 90 5)
assert_contains "$output" "DEVIATIONS|deviations" "Mentions DEVIATIONS.md" || true
assert_contains "$output" "concern|defer|decision|scope|deviation" "Describes deviation types" || true

echo ""
echo "--- Test 5: Task 0 ---"
output=$(run_claude "What is Task 0 in subagent-driven-development and when is it required? Answer from the skill content." 90 5)
assert_contains "$output" "task.0|Task 0|contract.*verification" "Mentions Task 0" || true
assert_contains "$output" "block|before|first|must.*pass|no other task" "Task 0 is blocking" || true

echo ""
echo "--- Test 6: Review enforcement ---"
output=$(run_claude "Can the controller skip reviews in subagent-driven-development? Under what circumstances? Answer from the skill content." 90 5)
assert_contains "$output" "no|never|cannot|should not|without exception|not skip|every task" "Cannot skip reviews" || true

echo ""
echo "--- Test 7: Pre-completion gate ---"
output=$(run_claude "What checks must pass before declaring implementation complete in subagent-driven-development? Answer from the skill content." 90 5)
assert_contains "$output" "checkbox|DEVIATIONS|test.*suite|wiring|TodoWrite|report" "Lists gate conditions" || true

echo ""
echo "--- Test 8: Contract Constraints passthrough ---"
output=$(run_claude "How does the SDD controller handle Contract Constraints when dispatching implementer subagents? Answer from the skill content." 90 5)
assert_contains "$output" "verbatim|include|inject|pass.*through|provide|each.*subagent" "Constraints passed to subagents" || true

print_summary
