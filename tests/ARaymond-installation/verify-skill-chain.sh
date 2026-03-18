#!/usr/bin/env bash
# ARaymond custom fork: skill-to-skill handoff (chain) test
#
# Verifies that the brainstorming -> writing-plans skill chain works end-to-end
# via the symlink installation (no --plugin-dir).
#
# Turn 1: Invoke superpowers:brainstorming for a simple feature request.
# Turn 2: Fast-track approval to trigger the writing-plans handoff.
#
# Usage:
#   ./verify-skill-chain.sh
#
# Exit codes:
#   0 = all checks passed
#   1 = one or more checks failed
#
# Requires: claude CLI in PATH, jq

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TIMESTAMP=$(date +%s)
OUTPUT_DIR="/tmp/superpowers-tests/${TIMESTAMP}/skill-chain"
mkdir -p "$OUTPUT_DIR"

# Temp project directory — brainstorming will look at project context
PROJECT_DIR="$OUTPUT_DIR/project"
mkdir -p "$PROJECT_DIR"

# Cleanup on exit
cleanup() {
    rm -rf "$OUTPUT_DIR"
}
trap cleanup EXIT

passed=0
failed=0

pass() {
    passed=$((passed + 1))
    echo "  [PASS] $1"
}

fail() {
    failed=$((failed + 1))
    echo "  [FAIL] $1"
}

echo "=== Skill Chain Test: brainstorming -> writing-plans ==="
echo "Output dir: $OUTPUT_DIR"
echo "Project dir: $PROJECT_DIR"
echo ""

# ─── Turn 1: Invoke brainstorming ─────────────────────────────────────────────

echo ">>> Turn 1: Invoking superpowers:brainstorming..."
TURN1_LOG="$OUTPUT_DIR/turn1.json"

timeout 120 claude \
    -p "I want to add a hello-world CLI command to this project. It should print 'Hello, World!' and exit. Use the superpowers:brainstorming skill." \
    --dangerously-skip-permissions \
    --max-turns 3 \
    --output-format stream-json \
    > "$TURN1_LOG" 2>&1 || true

echo "Turn 1 complete."
echo ""

# ─── Turn 1 Checks ────────────────────────────────────────────────────────────

echo "--- Turn 1 checks ---"

# Check: superpowers:brainstorming was invoked
BRAINSTORM_PATTERN='"skill":"(superpowers:)?brainstorming"'
if grep -q '"name":"Skill"' "$TURN1_LOG" && grep -qE "$BRAINSTORM_PATTERN" "$TURN1_LOG"; then
    pass "Turn 1: superpowers:brainstorming was invoked"
else
    fail "Turn 1: superpowers:brainstorming was NOT invoked"
    echo "       Skills triggered in Turn 1:"
    grep -o '"skill":"[^"]*"' "$TURN1_LOG" 2>/dev/null | sort -u | sed 's/^/         /' || echo "         (none)"
fi

# Check: no premature tool use before the Skill call
FIRST_SKILL_LINE=$(grep -n '"name":"Skill"' "$TURN1_LOG" | head -1 | cut -d: -f1)
if [ -n "$FIRST_SKILL_LINE" ]; then
    PREMATURE_TOOLS=$(head -n "$FIRST_SKILL_LINE" "$TURN1_LOG" | \
        grep '"type":"tool_use"' | \
        grep -v '"name":"Skill"' | \
        grep -v '"name":"TodoWrite"' || true)
    if [ -n "$PREMATURE_TOOLS" ]; then
        fail "Turn 1: tools invoked BEFORE Skill call (premature action)"
        echo "$PREMATURE_TOOLS" | head -5 | sed 's/^/         /'
    else
        pass "Turn 1: no premature tool invocations before Skill call"
    fi
else
    # No Skill call at all — already failed above, don't double-count
    echo "       (skipping premature-tool check — no Skill invocation found)"
fi

echo ""

# ─── Turn 2: Fast-track approval to trigger writing-plans handoff ─────────────

echo ">>> Turn 2: Fast-tracking approval to trigger writing-plans handoff..."
TURN2_LOG="$OUTPUT_DIR/turn2.json"

timeout 120 claude \
    -p "The design is simple — just a bash script that prints Hello World. I approve this design. Skip the spec review and move to writing the implementation plan." \
    --continue \
    --dangerously-skip-permissions \
    --max-turns 5 \
    --output-format stream-json \
    > "$TURN2_LOG" 2>&1 || true

echo "Turn 2 complete."
echo ""

# ─── Turn 2 Checks ────────────────────────────────────────────────────────────

echo "--- Turn 2 checks ---"

# Check: superpowers:writing-plans was invoked (the handoff)
WRITING_PLANS_PATTERN='"skill":"(superpowers:)?writing-plans"'
if grep -q '"name":"Skill"' "$TURN2_LOG" && grep -qE "$WRITING_PLANS_PATTERN" "$TURN2_LOG"; then
    pass "Turn 2: superpowers:writing-plans was invoked (skill chain handoff succeeded)"
else
    fail "Turn 2: superpowers:writing-plans was NOT invoked (skill chain handoff failed)"
    echo "       Skills triggered in Turn 2:"
    grep -o '"skill":"[^"]*"' "$TURN2_LOG" 2>/dev/null | sort -u | sed 's/^/         /' || echo "         (none)"
    echo "       Tools triggered in Turn 2:"
    grep '"type":"tool_use"' "$TURN2_LOG" | grep -o '"name":"[^"]*"' | sort -u | head -10 | sed 's/^/         /' || echo "         (none)"
fi

# Check: no premature tool use before the Skill call
FIRST_SKILL_LINE2=$(grep -n '"name":"Skill"' "$TURN2_LOG" | head -1 | cut -d: -f1)
if [ -n "$FIRST_SKILL_LINE2" ]; then
    PREMATURE_TOOLS2=$(head -n "$FIRST_SKILL_LINE2" "$TURN2_LOG" | \
        grep '"type":"tool_use"' | \
        grep -v '"name":"Skill"' | \
        grep -v '"name":"TodoWrite"' || true)
    if [ -n "$PREMATURE_TOOLS2" ]; then
        fail "Turn 2: tools invoked BEFORE Skill call (premature action)"
        echo "$PREMATURE_TOOLS2" | head -5 | sed 's/^/         /'
    else
        pass "Turn 2: no premature tool invocations before Skill call"
    fi
else
    echo "       (skipping premature-tool check — no Skill invocation found)"
fi

echo ""

# ─── Diagnostic Output ────────────────────────────────────────────────────────

echo "--- Diagnostic ---"

echo "All skills triggered across both turns:"
{ grep -oh '"skill":"[^"]*"' "$TURN1_LOG" "$TURN2_LOG" 2>/dev/null || true; } | sort -u | sed 's/^/  /'
[ $? -ne 0 ] && echo "  (none)"

echo ""
echo "Turn 1 first assistant response (truncated):"
grep '"type":"assistant"' "$TURN1_LOG" | head -1 \
    | jq -r '.message.content[0].text // .message.content' 2>/dev/null \
    | head -c 400 \
    || echo "  (could not extract)"

echo ""
echo "Turn 2 first assistant response (truncated):"
grep '"type":"assistant"' "$TURN2_LOG" | head -1 \
    | jq -r '.message.content[0].text // .message.content' 2>/dev/null \
    | head -c 400 \
    || echo "  (could not extract)"

# ─── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "========================================"
echo " Skill Chain Verification Summary"
echo "========================================"
echo ""
echo "  Passed: $passed"
echo "  Failed: $failed"
echo ""

if [[ $failed -gt 0 ]]; then
    echo "STATUS: FAILED"
    echo ""
    echo "Logs (not cleaned up for inspection):"
    # Override the trap so logs survive on failure
    trap - EXIT
    echo "  Turn 1: $TURN1_LOG"
    echo "  Turn 2: $TURN2_LOG"
    echo "  Timestamp: $TIMESTAMP"
    exit 1
else
    echo "STATUS: PASSED"
    exit 0
fi
