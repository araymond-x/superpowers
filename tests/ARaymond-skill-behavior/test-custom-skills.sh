#!/usr/bin/env bash
# Test custom fork skills that don't exist in upstream
set -uo pipefail
# No -e: all tests run even if one fails. print_summary handles exit code.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== Custom Skill Behavior Tests ==="

# Test 1: handoff-acceptance skill content
echo ""
echo "--- Test 1: handoff-acceptance checklist ---"
output=$(run_claude "What are the blocking checks in the handoff-acceptance skill? Answer from the skill content." 90 5)
assert_contains "$output" "contract.*summary|contract.*constraints" "Mentions contract summary check" || true
assert_contains "$output" "snippet|code.*snippet|executable" "Mentions snippet check" || true
assert_contains "$output" "fixture|sample" "Mentions fixture check" || true

# Test 2: spec distillation in brainstorming
echo ""
echo "--- Test 2: brainstorming spec distillation ---"
output=$(run_claude "In the brainstorming skill, what is spec distillation and when does it happen? Answer from the skill content." 90 5)
assert_contains "$output" "distill|distilled" "Mentions distillation" || true
assert_contains "$output" "500.*line|implementation.*agent|plan.*writer|definitive|decision" "Describes purpose" || true

# Test 3: Feature Footprint in writing-plans
echo ""
echo "--- Test 3: writing-plans feature archetype ---"
output=$(run_claude "What are the feature archetypes defined in the writing-plans skill? Answer from the skill content." 90 5)
assert_contains "$output" "greenfield|replacement|extension|refactor|migration" "Lists archetypes" || true

# Test 4: writing-plans two-layer validation
echo ""
echo "--- Test 4: writing-plans two-layer validation ---"
output=$(run_claude "In the writing-plans skill, what is two-layer validation? Answer from the skill content." 90 5)
assert_contains "$output" "structural|validate-plan|script" "Mentions structural layer" || true
assert_contains "$output" "semantic|reviewer|plan.*document.*reviewer" "Mentions semantic layer" || true

# Test 5: ACCEPTED_WITH_REMEDIATION
echo ""
echo "--- Test 5: handoff-acceptance three verdicts ---"
output=$(run_claude "What are the possible verdicts from handoff-acceptance? When would you use each? Answer from the skill content." 90 5)
assert_contains "$output" "ACCEPTED_WITH_REMEDIATION|accepted.*with.*remediation" "Mentions conditional acceptance" || true

print_summary
