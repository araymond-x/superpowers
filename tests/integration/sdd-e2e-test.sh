#!/bin/bash
# E2E smoke test: materialize-manifest.py → validators session → controller-checkpoint --manifest → transition-module.py

set -e
trap 'echo "FAIL on line $LINENO with exit $?"; exit 1' ERR

# Resolve the repo root from this script's location so the test exercises THIS
# checkout's scripts (worktree-correct), not a hardcoded sibling path. Must run
# before the `cd "$WORK"` below.
PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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
echo "=== STEP 8: review_tier:minimum exclusion via manifest modules (non-active module) ==="
# Item 4b path-resolution glue (Task 3 Step 3b): pre-completion must read the
# NON-active module's plan file (via manifest .modules + feature_dir join) to
# collect declared review_tier:minimum task IDs and exclude them from the ratio.
# Non-vacuous: WITHOUT the cross-module scan, 3/4 quality reviews are minimum
# (75% > 50% -> excessive_minimum_tier_quality blocker); WITH it, tasks 2 & 3
# (declared minimum in the non-active module-2.md) are excluded -> considered
# {0:full, 1:minimum} = 50%, no blocker.
RT=docs/imp-plans/rt-feature
mkdir -p "$RT/reports"
RT_DEV="$RT/deviations.md"; echo "# Deviations" > "$RT_DEV"

cat > "$RT/plan.md" << 'INNER'
---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
tasks:
  - id: 0
    title: "Zero"
  - id: 1
    title: "One"
  - id: 2
    title: "Two"
    review_tier: minimum
  - id: 3
    title: "Three"
    review_tier: minimum
modules:
  - id: 1
    title: "Active"
    task_ids: [0, 1]
    file: rt-module-1.md
  - id: 2
    title: "Later"
    task_ids: [2, 3]
    file: rt-module-2.md
---
# RT Feature
**Source Contracts**: None
**Feature Archetype**: Extension
## Code Footprint
### Task 0: Zero
- [x] done
INNER

# Active module (module-1): no minimum declarations.
cat > "$RT/rt-module-1.md" << 'INNER'
---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 0
    title: "Zero"
  - id: 1
    title: "One"
---
# RT Module 1
### Task 0: Zero
- [x] done
### Task 1: One
- [x] done
INNER

# Non-active module (module-2): declares tasks 2 & 3 as review_tier:minimum.
cat > "$RT/rt-module-2.md" << 'INNER'
---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 2
    title: "Two"
    review_tier: minimum
  - id: 3
    title: "Three"
    review_tier: minimum
---
# RT Module 2
### Task 2: Two
- [x] done
### Task 3: Three
- [x] done
INNER

$PYTHON $PROJECT/skills/subagent-driven-development/scripts/materialize-manifest.py \
  --plan-file "$RT/plan.md" --feature-dir "$RT" > /dev/null

# Quality reviews: task 0 full; tasks 1,2,3 minimum-tier (3/4 = 75% raw).
: > "$RT/reports/task-000-quality-review.md"; printf 'x%.0s' {1..80} > "$RT/reports/task-000-quality-review.md"
for tid in 1 2 3; do
  padded=$(printf "%03d" $tid)
  printf 'x%.0s' {1..80} > "$RT/reports/task-${padded}-quality-review-minimum-tier.md"
done

# Sanity: the active manifest points at module-1 (so module-2 is non-active).
RT_ACTIVE=$(python3 -c "import json; print(json.load(open('$RT/.sdd-session.json'))['active_module_file'])")
test "$RT_ACTIVE" = "rt-module-1.md"

RTOUT=$(mktemp)
$PYTHON $PROJECT/skills/subagent-driven-development/scripts/controller-checkpoint.py \
  --phase pre-completion --manifest "$RT/.sdd-session.json" \
  --deviations-file "$RT_DEV" --reports-dir "$RT/reports" > "$RTOUT" 2>&1 || true
test -s "$RTOUT"  # checkpoint produced output (proves it ran)
RT_BLOCKERS=$(python3 -c "import json; print(json.load(open('$RTOUT')).get('blockers', []))")
rm "$RTOUT"
echo "$RT_BLOCKERS" | grep -q "excessive_minimum_tier_quality" && {
  echo "FAIL: review_tier:minimum tasks in the non-active module were NOT excluded (blockers: $RT_BLOCKERS)"; exit 1; }
echo "  PASS: declared review_tier:minimum tasks (non-active module) excluded from ratio"

echo ""
echo "E2E PIPELINE PASS - 8 steps composed correctly"
rm -rf "$WORK"
