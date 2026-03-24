#!/usr/bin/env bash
# ARaymond custom fork: behavioral test helpers
# Adapted from upstream tests/claude-code/test-helpers.sh for symlink install.
#
# Differences from upstream:
#   - No --plugin-dir (skills loaded via symlink at ~/.claude/skills/superpowers/)
#   - --verbose required with --output-format stream-json in headless mode
#   - macOS-compatible timeout (background-process-kill, no GNU timeout)
#
# Source this file from test scripts: source "$(dirname "$0")/test-helpers.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TIMESTAMP=$(date +%s)
BASE_OUTPUT_DIR="/tmp/superpowers-tests/${TIMESTAMP}/ARaymond-skill-behavior"
mkdir -p "$BASE_OUTPUT_DIR"

VERBOSE="${VERBOSE:-false}"
DEFAULT_TIMEOUT=120
DEFAULT_MAX_TURNS=3

passed=0
failed=0
skipped=0

# Run Claude headless with symlink-install conventions
# Usage: run_claude "prompt" [timeout_secs] [max_turns] [allowed_tools]
# Returns: output text on stdout, log file path on stderr
run_claude() {
    local prompt="$1"
    local timeout_secs="${2:-$DEFAULT_TIMEOUT}"
    local max_turns="${3:-$DEFAULT_MAX_TURNS}"
    local allowed_tools="${4:-}"

    local test_dir
    test_dir=$(mktemp -d "$BASE_OUTPUT_DIR/run-XXXXX")
    local project_dir="$test_dir/project"
    mkdir -p "$project_dir"
    local log_file="$test_dir/claude-output.json"

    local tool_args=""
    if [ -n "$allowed_tools" ]; then
        tool_args="--allowed-tools=$allowed_tools"
    fi

    # Run with symlink conventions: no --plugin-dir, add --verbose
    cd "$project_dir"
    claude -p "$prompt" \
        --dangerously-skip-permissions \
        --max-turns "$max_turns" \
        --output-format stream-json \
        --verbose \
        $tool_args \
        > "$log_file" 2>&1 &
    local claude_pid=$!

    # macOS-compatible timeout (no GNU timeout available)
    ( sleep "$timeout_secs" && kill "$claude_pid" 2>/dev/null ) &
    local watchdog_pid=$!
    wait "$claude_pid" 2>/dev/null || true
    kill "$watchdog_pid" 2>/dev/null || true
    wait "$watchdog_pid" 2>/dev/null || true

    # Extract assistant text response
    local output
    output=$(grep '"type":"assistant"' "$log_file" 2>/dev/null \
        | jq -r '.message.content[]? | select(.type == "text") | .text' 2>/dev/null \
        | head -c 5000 || echo "")

    # Log file path to stderr for callers that need it
    echo "$log_file" >&2
    # Output text to stdout
    echo "$output"
}

# Run Claude and return the log file path (not the text output)
run_claude_log() {
    local prompt="$1"
    local timeout_secs="${2:-$DEFAULT_TIMEOUT}"
    local max_turns="${3:-$DEFAULT_MAX_TURNS}"

    local test_dir
    test_dir=$(mktemp -d "$BASE_OUTPUT_DIR/run-XXXXX")
    local project_dir="$test_dir/project"
    mkdir -p "$project_dir"
    local log_file="$test_dir/claude-output.json"

    cd "$project_dir"
    claude -p "$prompt" \
        --dangerously-skip-permissions \
        --max-turns "$max_turns" \
        --output-format stream-json \
        --verbose \
        > "$log_file" 2>&1 &
    local claude_pid=$!
    ( sleep "$timeout_secs" && kill "$claude_pid" 2>/dev/null ) &
    local watchdog_pid=$!
    wait "$claude_pid" 2>/dev/null || true
    kill "$watchdog_pid" 2>/dev/null || true
    wait "$watchdog_pid" 2>/dev/null || true

    echo "$log_file"
}

# ─── Assertions ──────────────────────────────────────────────────────────────

assert_contains() {
    local output="$1"
    local pattern="$2"
    local description="$3"
    if echo "$output" | grep -qiE "$pattern"; then
        report_pass "$description"
        return 0
    else
        report_fail "$description (expected pattern: $pattern)"
        return 1
    fi
}

assert_not_contains() {
    local output="$1"
    local pattern="$2"
    local description="$3"
    if echo "$output" | grep -qiE "$pattern"; then
        report_fail "$description (unexpected pattern found: $pattern)"
        return 1
    else
        report_pass "$description"
        return 0
    fi
}

assert_skill_triggered() {
    local log_file="$1"
    local skill_name="$2"
    local description="${3:-Skill '$skill_name' was triggered}"
    local pattern='"skill":"([^"]*:)?'"${skill_name}"'"'
    if grep -q '"name":"Skill"' "$log_file" && grep -qE "$pattern" "$log_file"; then
        report_pass "$description"
        return 0
    else
        report_fail "$description"
        return 1
    fi
}

assert_no_premature_action() {
    local log_file="$1"
    local description="${2:-No premature tool invocations before Skill load}"
    local first_skill_line
    first_skill_line=$(grep -n '"name":"Skill"' "$log_file" | head -1 | cut -d: -f1)
    if [ -z "$first_skill_line" ]; then
        report_fail "No Skill invocation found at all"
        return 1
    fi
    local premature
    premature=$(head -n "$first_skill_line" "$log_file" | \
        grep '"type":"tool_use"' | \
        grep -v '"name":"Skill"' | \
        grep -v '"name":"TodoWrite"' | \
        grep -v '"name":"TodoCreate"' | \
        grep -v '"name":"TaskCreate"' || true)
    if [ -n "$premature" ]; then
        report_fail "$description — premature tools found"
        return 1
    else
        report_pass "$description"
        return 0
    fi
}

# ─── Reporting ───────────────────────────────────────────────────────────────

report_pass() {
    passed=$((passed + 1))
    echo "  [PASS] $1"
}

report_fail() {
    failed=$((failed + 1))
    echo "  [FAIL] $1"
}

report_skip() {
    skipped=$((skipped + 1))
    echo "  [SKIP] $1"
}

print_summary() {
    echo ""
    echo "========================================"
    echo " Behavioral Test Summary"
    echo "========================================"
    echo ""
    echo "  Passed:   $passed"
    echo "  Failed:   $failed"
    echo "  Skipped:  $skipped"
    echo ""
    if [ "$failed" -gt 0 ]; then
        echo "STATUS: FAILED"
        echo "Logs: $BASE_OUTPUT_DIR"
        return 1
    else
        echo "STATUS: PASSED"
        return 0
    fi
}
