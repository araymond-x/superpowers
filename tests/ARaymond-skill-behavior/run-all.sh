#!/usr/bin/env bash
# ARaymond custom fork: run all behavioral tests
#
# Usage:
#   ./run-all.sh                    # run fast tests only (~5 min)
#   ./run-all.sh --include-slow     # include implicit trigger tests (~15 min)
#   ./run-all.sh --test <name>      # run a single test
#   ./run-all.sh --verbose          # show Claude responses
#
# Each test is an API call — budget accordingly.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

INCLUDE_SLOW=false
SINGLE_TEST=""
export VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --include-slow) INCLUDE_SLOW=true; shift ;;
        --test) SINGLE_TEST="$2"; shift 2 ;;
        --verbose) export VERBOSE=true; shift ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

run_test_script() {
    local name="$1"
    local script="$2"
    if [ -n "$SINGLE_TEST" ] && [ "$SINGLE_TEST" != "$name" ]; then
        return 0
    fi
    echo ""
    echo "================================================================"
    echo " $name"
    echo "================================================================"
    bash "$script"
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "  ^^^ TEST FAILED (exit $exit_code) ^^^"
    fi
    return $exit_code
}

TOTAL_PASS=0
TOTAL_FAIL=0

# Fast tests (~1 min each)
FAST_TESTS=(
    "explicit-skill-requests:$SCRIPT_DIR/test-explicit-requests.sh"
    "sdd-content-validation:$SCRIPT_DIR/test-sdd-content.sh"
    "custom-skill-behavior:$SCRIPT_DIR/test-custom-skills.sh"
)

# Slow tests (~2 min each, 6 API calls)
SLOW_TESTS=(
    "implicit-triggers:$SCRIPT_DIR/test-implicit-triggers.sh"
)

for entry in "${FAST_TESTS[@]}"; do
    name="${entry%%:*}"
    script="${entry#*:}"
    if run_test_script "$name" "$script"; then
        TOTAL_PASS=$((TOTAL_PASS + 1))
    else
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
    fi
done

if [ "$INCLUDE_SLOW" = true ]; then
    for entry in "${SLOW_TESTS[@]}"; do
        name="${entry%%:*}"
        script="${entry#*:}"
        if run_test_script "$name" "$script"; then
            TOTAL_PASS=$((TOTAL_PASS + 1))
        else
            TOTAL_FAIL=$((TOTAL_FAIL + 1))
        fi
    done
fi

echo ""
echo "================================================================"
echo " OVERALL: $TOTAL_PASS test suites passed, $TOTAL_FAIL failed"
if [ "$INCLUDE_SLOW" = false ]; then
    echo " (Run with --include-slow for implicit trigger tests)"
fi
echo "================================================================"

[ "$TOTAL_FAIL" -eq 0 ]
