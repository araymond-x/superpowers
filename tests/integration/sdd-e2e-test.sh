#!/bin/bash
# E2E smoke test: materialize-manifest.py → validators session → controller-checkpoint --manifest → transition-module.py

set -e
trap 'echo "FAIL on line $LINENO with exit $?"; exit 1' ERR

PROJECT=/Users/araymond/projects/claude-custom/superpowers
PYTHON=$PROJECT/.venv/bin/python3
WORK=$(mktemp -d -t sdd-e2e-XXXXXX)
echo "Workspace: $WORK"
cd "$WORK"
git init -q

FEAT=docs/imp-plans/test-feature
mkdir -p "$FEAT/reports"
DEVIATIONS="$FEAT/deviations.md"
PLAN="$FEAT/plan.md"

echo "# Deviations" > "$DEVIATIONS"

cat > "$PLAN" << 'INNER'
---
schema_version: 1
feature_archetype: refactor
enforcement_tier: standard
source_contracts: null
tasks:
  - id: 0
    title: "First"
  - id: 1
    title: "Second"
  - id: 2
    title: "Third"
  - id: 3
    title: "Fourth"
modules:
  - id: 1
    title: "Core"
    task_ids: [0, 1]
    file: module-1.md
  - id: 2
    title: "API"
    task_ids: [2, 3]
    file: module-2.md
---
# Test Feature

**Source Contracts**: None
**Feature Archetype**: Refactor

## Code Footprint
- app/foo.py

### Task 0: First
- [x] Step 1
INNER

cat > "$FEAT/module-1.md" << 'INNER'
# Module 1

### Task 0: First
- [x] Step 1

### Task 1: Second
- [x] Step 1
INNER

cat > "$FEAT/module-2.md" << 'INNER'
# Module 2

### Task 2: Third
- [x] Step 1

### Task 3: Fourth
- [x] Step 1
INNER

echo "# sdd-hook-sentinel abc123" > "$FEAT/reports/.dispatch-log"

echo ""
echo "=== STEP 1: materialize-manifest.py ==="
$PYTHON $PROJECT/skills/subagent-driven-development/scripts/materialize-manifest.py \
  --plan-file "$PLAN" --feature-dir "$FEAT" > /dev/null
test -f "$FEAT/.sdd-session.json"
ACTIVE_FILE=$(python3 -c "import json; print(json.load(open('$FEAT/.sdd-session.json'))['active_module_file'])")
test "$ACTIVE_FILE" = "module-1.md"
echo "  PASS: Manifest created with active_module_file=module-1.md"

echo ""
echo "=== STEP 2: validators.py session ==="
$PYTHON $PROJECT/skills/scripts/models/validators.py session "$FEAT/.sdd-session.json"
echo "  PASS: Pydantic validates manifest"

echo ""
echo "=== STEP 3: controller-checkpoint.py --manifest ==="
TMPOUT=$(mktemp)
$PYTHON $PROJECT/skills/subagent-driven-development/scripts/controller-checkpoint.py \
  --phase pre-execution --manifest "$FEAT/.sdd-session.json" \
  --deviations-file "$DEVIATIONS" --reports-dir "$FEAT/reports" > "$TMPOUT" 2>&1 || true
PLAN_STATUS=$(python3 -c "import json; d=json.load(open('$TMPOUT')); print(d['checks']['plan_file']['status'])")
if [ "$PLAN_STATUS" != "PASS" ]; then
  echo "FAIL: plan_file check status is $PLAN_STATUS"
  cat "$TMPOUT"
  exit 1
fi
rm "$TMPOUT"
echo "  PASS: Manifest read; active_module_file resolved with feature_dir"

echo ""
echo "=== STEP 4: Create Module 1 reports ==="
for tid in 0 1; do
  padded=$(printf "%03d" $tid)
  for kind in implementer-report spec-review quality-review; do
    {
      echo "# ${kind} for task ${tid}"
      echo ""
      printf 'x%.0s' {1..100}
    } > "$FEAT/reports/task-${padded}-${kind}.md"
  done
done
echo "  PASS: 6 stub reports created"

echo ""
echo "=== STEP 5: transition-module.py Core to API ==="
$PYTHON $PROJECT/skills/subagent-driven-development/scripts/transition-module.py \
  --manifest "$FEAT/.sdd-session.json" \
  --completed-module Core --next-module API

test -d "$FEAT/reports/archive-Core"
test -f "$FEAT/reports/archive-Core/task-000-implementer-report.md"
test -f "$FEAT/reports/archive-Core/.dispatch-log"
test ! -s "$FEAT/reports/.dispatch-log"

ACTIVE_ID=$(python3 -c "import json; print(json.load(open('$FEAT/.sdd-session.json'))['active_module_id'])")
test "$ACTIVE_ID" = "2"
TASK_RANGE=$(python3 -c "import json; print(json.load(open('$FEAT/.sdd-session.json'))['task_range'])")
test "$TASK_RANGE" = "[2, 3]"

$PYTHON $PROJECT/skills/scripts/models/validators.py session "$FEAT/.sdd-session.json"
echo "  PASS: active_module 1->2, task_range [0,1]->[2,3], reports archived, log truncated, manifest re-validates"

echo ""
echo "=== STEP 6: Verify deviations log ==="
grep -q "Module transition: Core" "$DEVIATIONS"
echo "  PASS: Deviation row appended"

echo ""
echo "=== STEP 7: Post-transition checkpoint reads new active module ==="
TMPOUT=$(mktemp)
$PYTHON $PROJECT/skills/subagent-driven-development/scripts/controller-checkpoint.py \
  --phase pre-execution --manifest "$FEAT/.sdd-session.json" \
  --deviations-file "$DEVIATIONS" --reports-dir "$FEAT/reports" > "$TMPOUT" 2>&1 || true
PLAN_DETAIL=$(python3 -c "import json; print(json.load(open('$TMPOUT'))['checks']['plan_file']['detail'])")
rm "$TMPOUT"
echo "$PLAN_DETAIL" | grep -q "module-2.md"
echo "  PASS: Post-transition checkpoint resolves module-2.md"

echo ""
echo "E2E PIPELINE PASS - 7 steps composed correctly"
rm -rf "$WORK"
