#!/usr/bin/env bash
# ARaymond custom fork: skill invocation integration tests
#
# Verifies that skills installed via symlinks are properly invoked by Claude.
# Unlike the upstream tests in explicit-skill-requests/ and skill-triggering/,
# this script does NOT use --plugin-dir. Skills are already present in the
# environment via the symlink at ~/.claude/skills/superpowers/.
#
# Usage:
#   ./verify-skill-invocation.sh           # run all three tests
#   ./verify-skill-invocation.sh --verbose # show full assistant response
#
# Exit codes:
#   0 = all tests passed
#   1 = one or more tests failed
#
# Tests:
#   1. Explicit by skill name: "please use the superpowers:brainstorming skill"
#   2. Explicit by command syntax: "superpowers:writing-plans, please"
#   3. Content verification: confirm SKILL.md content was loaded (not just the stub)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VERBOSE=false
[[ "${1:-}" == "--verbose" ]] && VERBOSE=true

TIMESTAMP=$(date +%s)
BASE_OUTPUT_DIR="/tmp/superpowers-tests/${TIMESTAMP}/ARaymond-installation"
mkdir -p "$BASE_OUTPUT_DIR"

TIMEOUT_SECS=60
MAX_TURNS=2

passed=0
failed=0

# ─── Helpers ──────────────────────────────────────────────────────────────────

run_test() {
    local test_name="$1"
    local prompt="$2"
    local output_dir="$BASE_OUTPUT_DIR/$test_name"
    mkdir -p "$output_dir"

    local log_file="$output_dir/claude-output.json"

    # Status lines go to stderr so stdout stays clean for the path return value
    echo "" >&2
    echo "--- Running: $test_name ---" >&2
    echo "Prompt: $prompt" >&2
    echo "" >&2

    # Use a throw-away project dir so Claude has a cwd to operate in
    local project_dir="$output_dir/project"
    mkdir -p "$project_dir"

    # Run claude headless. No --plugin-dir: skills come from the symlink install.
    # --verbose is required when using --output-format=stream-json with -p.
    # Use a background process + kill for macOS compatibility (GNU timeout not available by default).
    cd "$project_dir"
    claude -p "$prompt" \
        --dangerously-skip-permissions \
        --max-turns "$MAX_TURNS" \
        --output-format stream-json \
        --verbose \
        > "$log_file" 2>&1 &
    local claude_pid=$!
    # Kill the process if it hasn't finished within TIMEOUT_SECS
    ( sleep "$TIMEOUT_SECS" && kill "$claude_pid" 2>/dev/null ) &
    local watchdog_pid=$!
    wait "$claude_pid" 2>/dev/null || true
    kill "$watchdog_pid" 2>/dev/null || true
    wait "$watchdog_pid" 2>/dev/null || true

    echo "$log_file"
}

report_pass() {
    passed=$((passed + 1))
    echo "  [PASS] $1"
}

report_fail() {
    failed=$((failed + 1))
    echo "  [FAIL] $1"
}

show_assistant_response() {
    local log_file="$1"
    echo ""
    echo "  First assistant text response (truncated to 500 chars):"
    grep '"type":"assistant"' "$log_file" \
        | jq -r '.message.content[]? | select(.type == "text") | .text' 2>/dev/null \
        | head -c 500 \
        || echo "  (could not extract)"
}

show_skills_triggered() {
    local log_file="$1"
    echo "  Skills triggered:"
    grep -o '"skill":"[^"]*"' "$log_file" 2>/dev/null | sort -u || echo "    (none)"
}

# ─── Test 1: Explicit by full namespace ───────────────────────────────────────

echo ""
echo "=== Test 1: Explicit skill request by namespace ==="

PROMPT_1="please use the superpowers:brainstorming skill"
LOG_1=$(run_test "test-1-explicit-namespace" "$PROMPT_1")

# Match "skill":"brainstorming" or "skill":"superpowers:brainstorming"
SKILL_PATTERN_1='"skill":"(superpowers:)?brainstorming"'
if grep -q '"name":"Skill"' "$LOG_1" && grep -qE "$SKILL_PATTERN_1" "$LOG_1"; then
    report_pass "Skill 'brainstorming' was invoked"
else
    report_fail "Skill 'brainstorming' was NOT invoked"
fi

show_skills_triggered "$LOG_1"
[[ "$VERBOSE" == true ]] && show_assistant_response "$LOG_1"
echo "  Log: $LOG_1"

# ─── Test 2: Explicit by command syntax ───────────────────────────────────────

echo ""
echo "=== Test 2: Explicit skill request by command syntax ==="

PROMPT_2="superpowers:writing-plans, please"
LOG_2=$(run_test "test-2-command-syntax" "$PROMPT_2")

SKILL_PATTERN_2='"skill":"(superpowers:)?writing-plans"'
if grep -q '"name":"Skill"' "$LOG_2" && grep -qE "$SKILL_PATTERN_2" "$LOG_2"; then
    report_pass "Skill 'writing-plans' was invoked"
else
    report_fail "Skill 'writing-plans' was NOT invoked"
fi

show_skills_triggered "$LOG_2"
[[ "$VERBOSE" == true ]] && show_assistant_response "$LOG_2"
echo "  Log: $LOG_2"

# ─── Test 3: Content verification — SKILL.md loaded, not just the stub ────────

echo ""
echo "=== Test 3: SKILL.md content verification ==="
echo "(Confirms real skill content was loaded, not just the command stub's placeholder text)"

PROMPT_3="What does the superpowers:brainstorming skill require before implementation? Summarize briefly."
LOG_3=$(run_test "test-3-content-verification" "$PROMPT_3")

# The brainstorming SKILL.md explicitly requires presenting a "design" and getting
# "approval" before any implementation. The command stub only says to invoke the skill.
# If any assistant text response mentions "design" or "approval", the SKILL.md content was loaded.
# We scan ALL assistant messages and ALL content items (not just content[0] of the first message)
# because Claude may invoke the skill as a tool before producing the descriptive text answer.
RESPONSE_3=$(grep '"type":"assistant"' "$LOG_3" \
    | jq -r '.message.content[]? | select(.type == "text") | .text' 2>/dev/null \
    | tr '\n' ' ' || true)

if echo "$RESPONSE_3" | grep -qiE "design|approval"; then
    report_pass "Response mentions 'design' or 'approval' — SKILL.md content was loaded"
else
    report_fail "Response does not mention 'design' or 'approval' — SKILL.md content may not have loaded"
    echo "  Response preview: $(echo "$RESPONSE_3" | head -c 300)"
fi

[[ "$VERBOSE" == true ]] && show_assistant_response "$LOG_3"
echo "  Log: $LOG_3"

# ─── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "========================================"
echo " Skill Invocation Test Summary"
echo "========================================"
echo ""
echo "  Passed: $passed / $((passed + failed))"
echo "  Failed: $failed / $((passed + failed))"
echo ""
echo "  Output dir: $BASE_OUTPUT_DIR"
echo ""

if [[ $failed -gt 0 ]]; then
    echo "STATUS: FAILED"
    exit 1
else
    echo "STATUS: PASSED"
    exit 0
fi
