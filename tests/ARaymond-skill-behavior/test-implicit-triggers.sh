#!/usr/bin/env bash
# Test implicit skill triggering from natural prompts.
# Adapted from upstream tests/skill-triggering/ for symlink install.
# Reuses upstream prompt files.
#
# SLOW: 6 API calls, ~2 min each = ~12 min total
set -uo pipefail
# No -e: all tests run even if one fails. print_summary handles exit code.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

UPSTREAM_PROMPTS="$REPO_ROOT/tests/skill-triggering/prompts"

echo "=== Implicit Skill Triggering (symlink install) ==="

# Test each upstream trigger prompt
TRIGGER_TESTS=(
    "systematic-debugging:systematic-debugging.txt"
    "test-driven-development:test-driven-development.txt"
    "writing-plans:writing-plans.txt"
    "dispatching-parallel-agents:dispatching-parallel-agents.txt"
    "executing-plans:executing-plans.txt"
    "requesting-code-review:requesting-code-review.txt"
)

for entry in "${TRIGGER_TESTS[@]}"; do
    skill="${entry%%:*}"
    prompt_file="${entry#*:}"
    echo ""
    echo "--- Trigger test: $skill ---"
    PROMPT=$(cat "$UPSTREAM_PROMPTS/$prompt_file")
    LOG=$(run_claude_log "$PROMPT" 180 3)
    assert_skill_triggered "$LOG" "$skill" || true
done

print_summary
