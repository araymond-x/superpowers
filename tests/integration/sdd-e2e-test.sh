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
  # N3b: transition now verifies dispatch-log provenance before truncating.
  echo "2026-06-01T00:00:00Z DISPATCH reviewer task=${tid} type=spec-review" >> "$FEAT/reports/.dispatch-log"
  echo "2026-06-01T00:00:00Z DISPATCH reviewer task=${tid} type=quality-review" >> "$FEAT/reports/.dispatch-log"
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
echo "=== STEP 7b: module-2 first task dispatches post-transition (N3a skip-guard + N11) ==="
# After the Core->API transition the live log is empty (truncated), task_range is
# [2,3], and (N11) context_summary_at has been recomputed to module-2's midpoint
# (3). Dispatching task 2 (module-first) must be ALLOWED: PREV=1 < START=2 ->
# Check 4c skip-guard. Non-vacuous on TWO axes: pre-N3a the hook greps the empty
# log for `task=1 type=spec-review` and BLOCKS; pre-N11 context_summary_at stays 1,
# so Check 6b (2 >= 1) BLOCKS task 2 for a missing context summary. Live proof of both.
CS=$(python3 -c "import json; print(json.load(open('$FEAT/.sdd-session.json'))['enforcement']['context_summary_at'])")
test "$CS" = "3" || { echo "FAIL: N11 — context_summary_at not recomputed for module 2 (got $CS, want 3)"; exit 1; }
HOOK="$PROJECT/skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
echo "$FEAT" > "$WORK/.active-feature"          # hook resolves manifest via .active-feature
touch "$WORK/.allow-main"                         # git init default branch is main; allow SDD here
# Support files so the only gate that could fire for task 2 is Check 4c (NO
# context-summary stub needed — N11's recompute means 2 < context_summary_at=3):
{ echo "# audit"; printf 'x%.0s' {1..60}; } > "$FEAT/reports/pre-execution-audit.md"
echo '{"status":"PASS","detail":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}' > "$FEAT/reports/checkpoint-pre-dispatch-002.json"
{ echo "# partner"; printf 'x%.0s' {1..60}; } > "$FEAT/reports/partner-review-002.md"
echo "2026-06-01T00:00:00Z DISPATCH reviewer task=2 type=partner-review" >> "$FEAT/reports/.dispatch-log"
HOOK_INPUT='{"tool_input":{"description":"Implement task 2","prompt":"You are implementing task 2"},"cwd":"'"$WORK"'"}'
set +e
echo "$HOOK_INPUT" | bash "$HOOK"; HOOK_RC=$?
set -e
test "$HOOK_RC" -eq 0 || { echo "FAIL: hook blocked module-2 first task post-transition (rc=$HOOK_RC)"; exit 1; }
echo "  PASS: task 2 dispatched post-transition — skip-guard (N3a) + recomputed context_summary_at (N11)"

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
printf 'x%.0s' {1..80} > "$RT/reports/task-000-quality-review.md"
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
# Step 9: Verification task type — validate-plan accepts it
echo "=== Step 9: Verification task type ==="

cat > "$WORK/plan-verif.md" << 'PLAN_EOF'
---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
tasks:
  - id: 93
    title: "Implement core feature"
  - id: 94
    title: "Audit orphaned references"
    task_type: verification
    depends_on: [93]
---
# Verification Test Plan

**Source Contracts**: None
**Feature Archetype**: Extension

## Code Footprint
- foo.py (modified)

## Write-Scope Partitioning

| Task | Owned Files | Read-Only | Depends On |
|------|-------------|-----------|------------|
| Task 93 | foo.py | — | — |
| Task 94 | — | foo.py | Task 93 |

### Task 93: Implement core feature
- [ ] Step 1: implement

### Task 94: Audit orphaned references
- [ ] Step 1: grep for orphans
PLAN_EOF

# `|| true` REQUIRED — harness runs under `set -e`+ERR trap; validate-plan exits 2 on WARNING.
RESULT=$($PYTHON "$PROJECT/skills/subagent-driven-development/scripts/validate-plan.py" --plan-file "$WORK/plan-verif.md" 2>&1 || true)
STATUS=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
if [ "$STATUS" = "FAIL" ]; then
  echo "FAIL: validate-plan.py rejected verification task plan"
  exit 1
fi
echo "PASS: Step 9 — verification task validation"

echo ""
# Step 10: Verification task with write-suggesting keyword → WARNING
echo "=== Step 10: Verification keyword WARNING ==="

cat > "$WORK/plan-verif-kw.md" << 'PLAN_EOF'
---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 95
    title: "Create cleanup script"
    task_type: verification
---
# Keyword Test Plan

**Source Contracts**: None
**Feature Archetype**: Extension

## Code Footprint
- foo.py (modified)

## Write-Scope Partitioning

| Task | Owned Files | Read-Only | Depends On |
|------|-------------|-----------|------------|
| Task 95 | — | foo.py | — |

### Task 95: Create cleanup script
- [ ] Step 1: create
PLAN_EOF

# `|| true` REQUIRED — this plan intentionally triggers a WARNING (exit 2).
RESULT=$($PYTHON "$PROJECT/skills/subagent-driven-development/scripts/validate-plan.py" --plan-file "$WORK/plan-verif-kw.md" 2>&1 || true)
STATUS=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
if [ "$STATUS" != "WARNING" ]; then
  echo "FAIL: expected WARNING for verification task with 'Create' keyword, got $STATUS"
  exit 1
fi
echo "PASS: Step 10 — verification keyword WARNING"

echo ""
# Step 11: integration_test declaration → pre-completion Check 10 PASS (C2)
echo "=== Step 11: Integration-test gate (Check 10) ==="

IT=docs/imp-plans/it-feature
mkdir -p "$IT/reports"
IT_DEV="$IT/deviations.md"; echo "# Deviations" > "$IT_DEV"
IT_TEST=tests/integration/it-feature-e2e-test.sh

cat > "$IT/plan.md" << 'INNER'
---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
integration_test:
  path: tests/integration/it-feature-e2e-test.sh
tasks:
  - id: 0
    title: "Zero"
---
# IT Feature
**Source Contracts**: None
**Feature Archetype**: Extension
## Code Footprint
### Task 0: Zero
- [x] done
INNER

$PYTHON $PROJECT/skills/subagent-driven-development/scripts/materialize-manifest.py \
  --plan-file "$IT/plan.md" --feature-dir "$IT" > /dev/null

# Check 10's changeset verification needs a resolvable base ref with a commit
# (the workspace repo has none so far): commit everything, pin the branch name
# to main, THEN create the declared test file UNTRACKED — the untracked-file
# branch of _in_changeset is what this step exercises.
git -C "$WORK" add -A
git -C "$WORK" -c user.name=e2e -c user.email=e2e@test commit -q -m "base" --no-gpg-sign
git -C "$WORK" branch -M main
mkdir -p "$(dirname "$IT_TEST")"
echo '#!/bin/bash' > "$IT_TEST"

ITOUT=$(mktemp)
# `|| true` REQUIRED — other pre-completion blockers (honesty, trace audit) FAIL
# in this stub fixture; we assert only the integration_test_present check.
$PYTHON $PROJECT/skills/subagent-driven-development/scripts/controller-checkpoint.py \
  --phase pre-completion --manifest "$IT/.sdd-session.json" \
  --deviations-file "$IT_DEV" --reports-dir "$IT/reports" > "$ITOUT" 2>&1 || true
IT_STATUS=$(python3 -c "import json; print(json.load(open('$ITOUT'))['checks']['integration_test_present']['status'])")
IT_DETAIL=$(python3 -c "import json; print(json.load(open('$ITOUT'))['checks']['integration_test_present']['detail'])")
rm "$ITOUT"
if [ "$IT_STATUS" != "PASS" ]; then
  echo "FAIL: integration_test_present is $IT_STATUS ($IT_DETAIL)"
  exit 1
fi
echo "PASS: Step 11 — declared integration test (untracked) passes Check 10"

echo ""
# Step 12: archive-aware aggregate gates (N27) — Check 7 counts archived
# minimum-tier reviews AND Check 9 sees an archived-module verification window.
# The in-sprint archive-aware proof (H1 self-hosting hazard): this run's LIVE
# hooks resolve to main's pre-N27 scripts, so this e2e step — which exercises
# THIS checkout's $PROJECT controller-checkpoint.py — is the only place the
# archive-aware aggregate fix runs end-to-end this sprint.
echo "=== Step 12: Archive-aware aggregate gates (N27) ==="

AV=docs/imp-plans/av-feature
mkdir -p "$AV/reports/archive-Mod1"
AV_DEV="$AV/deviations.md"; echo "# Deviations" > "$AV_DEV"

cat > "$AV/plan.md" << 'INNER'
---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
modules:
  - id: 1
    title: "Mod1"
    task_ids: [1, 2]
    file: module-1.md
  - id: 2
    title: "Mod2"
    task_ids: [3, 4]
    file: module-2.md
tasks:
  - id: 1
    title: "One"
  - id: 2
    title: "Two"
  - id: 3
    title: "Three"
    task_type: verification
  - id: 4
    title: "Four"
---
# AV Feature
**Source Contracts**: None
**Feature Archetype**: Extension
## Code Footprint
INNER

# Fixture adjustment vs. the plan snippet: the module plan files MUST exist on
# disk. materialize-manifest.py sets active_module_file to the first module's
# file, and pre-completion hard-errors ({"error": "Plan file not found"}) before
# producing the checks dict if that file (or any declared module plan) is
# missing. Minimal frontmatter + a task header is enough for the plan-file read
# and _load_all_plan_contents. (We hand-build the archived state rather than
# running transition-module.py — the N27 assertion is purely about the
# checkpoint reading archived reports/logs, so a real transition adds heavy
# completion-fixture overhead with no extra coverage.)
cat > "$AV/module-1.md" << 'INNER'
---
schema_version: 1
tasks:
  - id: 1
    title: "One"
  - id: 2
    title: "Two"
---
# Mod1
### Task 1: One
### Task 2: Two
INNER
cat > "$AV/module-2.md" << 'INNER'
---
schema_version: 1
tasks:
  - id: 3
    title: "Three"
    task_type: verification
  - id: 4
    title: "Four"
---
# Mod2
### Task 3: Three
### Task 4: Four
INNER

$PYTHON $PROJECT/skills/subagent-driven-development/scripts/materialize-manifest.py \
  --plan-file "$AV/plan.md" --feature-dir "$AV" > /dev/null

# Archived Module 1: both quality reviews minimum-tier (undeclared) → today the
# flat glob would miss them; archive-aware Check 7 must count them.
echo "x" > "$AV/reports/archive-Mod1/task-001-quality-review-minimum-tier.md"
echo "x" > "$AV/reports/archive-Mod1/task-002-quality-review-minimum-tier.md"
# Live Module 2: one full quality review.
echo "x" > "$AV/reports/task-004-quality-review.md"

# Archived dispatch log: verification task 3 implementer dispatch + bounding 4.
cat > "$AV/reports/archive-Mod1/.dispatch-log" << 'INNER'
2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer
2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer
INNER
: > "$AV/reports/.dispatch-log"   # live log truncated (post-transition)

# Commit a file INSIDE task 3's window so Check 9 (archive-aware) FAILs.
git -C "$WORK" add -A
GIT_AUTHOR_DATE="2026-03-01T10:30:00" GIT_COMMITTER_DATE="2026-03-01T10:30:00" \
  git -C "$WORK" -c user.name=e2e -c user.email=e2e@test commit -q -m "in-window" --no-gpg-sign

AVOUT=$(mktemp)
# `|| true` REQUIRED — other pre-completion blockers (honesty, trace audit,
# missing reports) FAIL in this stub fixture; we assert only Checks 7 + 9.
$PYTHON $PROJECT/skills/subagent-driven-development/scripts/controller-checkpoint.py \
  --phase pre-completion --manifest "$AV/.sdd-session.json" \
  --deviations-file "$AV_DEV" --reports-dir "$AV/reports" > "$AVOUT" 2>&1 || true

# Check 7: archived minimum-tier reviews counted. Considered = {1:min, 2:min,
# 4:full} (task 3 has NO quality review — it is task_type: verification). 2/3 >
# 50% → FAIL, proving the archived reviews are in the ratio.
Q_STATUS=$(python3 -c "import json;print(json.load(open('$AVOUT'))['checks']['excessive_minimum_tier_quality']['status'])")
# Check 9: archived-module verification window (the live log is truncated, so
# only the merged archive log opens task 3's window) sees the in-window commit
# → FAIL.
G_STATUS=$(python3 -c "import json;print(json.load(open('$AVOUT'))['checks']['verification_git_reality']['status'])")
rm "$AVOUT"
[ "$Q_STATUS" = "FAIL" ] || { echo "FAIL: Check 7 not archive-aware (got $Q_STATUS)"; exit 1; }
[ "$G_STATUS" = "FAIL" ] || { echo "FAIL: Check 9 not archive-aware (got $G_STATUS)"; exit 1; }
echo "PASS: Step 12 — Check 7 + Check 9 are archive-aware after a transition"

echo ""
echo "=== Step 13: context gate blocks over-HARD implementer dispatch (checkout-path proof) ==="
# NOTE: this exercises THIS checkout's hook, not the installed live hook
# (settings.json resolves the live hook to the main checkout). A post-merge
# live-hook smoke check is required separately (see spec §9 constraint 2).
CTX_WORK=$(mktemp -d)
# Minimal manifest workspace with task 0 complete, dispatching task 1.
# setup_full_sdd_workspace does its own git init + checkout + initial commit,
# so no manual git setup is needed here.
PYTHONPATH="$PROJECT/tests/unit" $PYTHON - "$CTX_WORK" "$PROJECT" << 'PYEOF'
import sys
sys.path.insert(0, sys.argv[2] + "/tests/unit")
from sdd_test_helpers import setup_full_sdd_workspace
setup_full_sdd_workspace(sys.argv[1], total_tasks=4, completed_tasks=1)
PYEOF
CTX_FIX="$PROJECT/tests/unit/fixtures/context-probe/hard.jsonl"
CTX_PAYLOAD=$($PYTHON - "$CTX_WORK" "$CTX_FIX" << 'PYEOF'
import json, sys
print(json.dumps({
  "tool_input": {"description": "Implement task 1", "prompt": "You are implementing task 1"},
  "cwd": sys.argv[1],
  "transcript_path": sys.argv[2],
}))
PYEOF
)
CTX_OUT=$(mktemp)
# `|| CTX_RC=$?` REQUIRED — the hook exits 2 by design here; the script runs
# under `set -e` + an ERR trap, so a bare invocation would abort before the
# exit code is captured (Steps 11/12 guard their non-zero calls the same way).
CTX_RC=0
SUPERPOWERS_ROOT="$PROJECT" bash "$PROJECT/skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh" \
  <<< "$CTX_PAYLOAD" > "$CTX_OUT" 2>"$CTX_OUT.err" || CTX_RC=$?
grep -qi "do not retry" "$CTX_OUT.err" || { echo "FAIL: block message missing non-retryable text"; exit 1; }
[ "$CTX_RC" -eq 2 ] || { echo "FAIL: expected exit 2, got $CTX_RC"; exit 1; }
grep -q "source=probe" "$CTX_WORK/reports/context-observations.log" || { echo "FAIL: no source=probe observation line"; exit 1; }
grep -q "action=block" "$CTX_WORK/reports/context-observations.log" || { echo "FAIL: no action=block observation line"; exit 1; }
rm -rf "$CTX_WORK" "$CTX_OUT" "$CTX_OUT.err"
echo "PASS: Step 13 — context gate blocks over-HARD implementer dispatch + logs source=probe"

echo ""
echo "=== Step 14: spawn-handoff-session.sh end-to-end (v2 surface topology + handshake + policy dial) ==="
# NOTE: exercises THIS checkout's script. The installed live path resolves to the
# main checkout — a post-merge live smoke is required separately (spec §7).
#
# Drives the REAL reworked (surface-topology) spawn-handoff-session.sh through its
# v2 SUCCESS path, then a policy=ask refusal and an over-expected advisory. The
# cmux stub emits real per-verb stdout mirroring the frozen shapes in
# tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json and the unit stub
# _CMUX_V2_STUB (tests/unit/spawn_handoff_helpers.py). A catch-all `echo "$@"`
# stub returns empty stdout, so capture_cmux_ref() would get no ref from
# new-surface and the success path would be UNREACHABLE — hence the per-verb shapes.
SPAWN_WORK=$(mktemp -d -t sdd-spawn-XXXXXX)
SPAWN_HOME="$SPAWN_WORK/home"
SPAWN_STUBS="$SPAWN_WORK/stubs"
mkdir -p "$SPAWN_HOME/.claude-codex-handoff/bundles/b14" \
         "$SPAWN_HOME/.local/share/claude/versions" "$SPAWN_STUBS"
# The picker version must be an executable FILE, not a directory: preflight_ok()
# tests `[ -f … ] && [ -x … ]`, mirroring the picker's own `find -type f -perm -u+x`.
# A directory PASSES -x (0755) and FAILS -f, silently degrading to
# launch=picker-manual — where the successor command is a bare `claude-picker
# '/pickup b14'` and the ARGS/LABEL/TELEMETRY vars below are inert, making every
# composed-command assertion vacuous. This is the MX-A trap from Task 7.
printf '#!/usr/bin/env bash\nexit 0\n' > "$SPAWN_HOME/.local/share/claude/versions/2.1.218"
chmod +x "$SPAWN_HOME/.local/share/claude/versions/2.1.218"

# Fixture worktree with .active-feature + reports
SPAWN_WT="$SPAWN_WORK/wt"; mkdir -p "$SPAWN_WT/docs/imp-plans/feat/reports"
( cd "$SPAWN_WT" && git init -q && git config user.email t@t && git config user.name t \
  && echo docs/imp-plans/feat > .active-feature && echo seed > seed \
  && git add -A && git commit -qm seed )
SPAWN_REPO_ID=$(cd "$SPAWN_WT" && $PYTHON - <<'PY'
import os,subprocess
c=subprocess.run(["git","rev-parse","--git-common-dir"],capture_output=True,text=True).stdout.strip()
print(os.path.realpath(c if os.path.isabs(c) else os.path.join(os.getcwd(),c)))
PY
)

# Valid work/SDD bundle manifest with the matching repo_id
cat > "$SPAWN_HOME/.claude-codex-handoff/bundles/b14/manifest.json" <<JSON
{"session":{"bundle_type":"work","entry_skill":"superpowers:subagent-driven-development"},
 "project":{"repo_id":"$SPAWN_REPO_ID","repo_name":"feat"}}
JSON

# Committed .sdd-session.json — generated by the REAL materialize-manifest.py from a
# tiny 5-task standard-tier plan (handoff_spawn: auto), so its shape matches what the
# pipeline emits: total_tasks=5, task_range=[0,4], handoff={expected_hops:2,
# spawn_policy:auto}. The script reads handoff.spawn_policy + handoff.expected_hops
# from it — the policy and budget dials the two sub-runs below exercise.
cat > "$SPAWN_WT/docs/imp-plans/feat/plan.md" <<'PLAN'
---
schema_version: 1
enforcement_tier: standard
handoff_spawn: auto
tasks:
  - id: 0
    title: "T0"
  - id: 1
    title: "T1"
  - id: 2
    title: "T2"
  - id: 3
    title: "T3"
  - id: 4
    title: "T4"
---
plan body
PLAN
( cd "$SPAWN_WT" && $PYTHON "$PROJECT/skills/subagent-driven-development/scripts/materialize-manifest.py" \
    --plan-file docs/imp-plans/feat/plan.md --feature-dir docs/imp-plans/feat >/dev/null )
( cd "$SPAWN_WT" && git add docs/imp-plans/feat/plan.md docs/imp-plans/feat/.sdd-session.json \
    && git commit -qm "seed plan + manifest" )
SPAWN_MANIFEST="$SPAWN_WT/docs/imp-plans/feat/.sdd-session.json"

# v2 surface-topology cmux stub — per-verb stdout mirrors _CMUX_V2_STUB /
# cmux-verb-shapes.json. `ping` is answered BEFORE logging (reachability probe,
# matches production). new-surface's `OK surface:7 …` is what capture_cmux_ref()
# parses into SPAWN_SURFACE_REF; rename-tab's field 2 is `action=rename` (NOT a ref,
# do not truncate); read-screen carries the post-spawn /rename + /rc verification
# anchors; list-pane-surfaces MUST carry the `* ` selected-row marker.
cat > "$SPAWN_STUBS/cmux" <<'SH'
#!/usr/bin/env bash
if [ "$1" = "ping" ]; then echo PONG; exit 0; fi
echo "$@" >> "$CMUX_LOG"
case "$1" in
  new-surface)   echo "OK surface:7 pane:2 workspace:5"; exit 0 ;;
  rename-tab)    echo "OK action=rename tab=tab:77 workspace=workspace:29"; exit 0 ;;
  send)          echo "OK surface:7 workspace:5"; exit 0 ;;
  send-key)      echo "OK surface:7 workspace:5"; exit 0 ;;
  wait-for)      exit 0 ;;
  read-screen)   # post-spawn verification: rename step greps
                 # "Session renamed to: <tab title>" (title "hop<N> SDD feat"), rc
                 # step greps the rc_anchor "/remote-control is active". Both the
                 # success run (hop1) and over-expected run (hop2) titles emitted.
                 printf 'Session renamed to: hop1 SDD feat\nSession renamed to: hop2 SDD feat\n/remote-control is active\n'; exit 0 ;;
  notify)        echo OK; exit 0 ;;
  workspace)     [ "$2" = "create" ] && { echo "OK workspace:9"; exit 0; }; echo OK; exit 0 ;;
  list-pane-surfaces)
                 # `list-pane-surfaces` and `workspace create` (below) are the
                 # workspace-FALLBACK topology, not the surface-topology success path
                 # this e2e's three Step-14 sub-runs all take (new-surface always
                 # succeeds above, so the script never falls back to these verbs
                 # here). The `* ` selected-row marker is nonetheless kept in its
                 # faithful frozen shape (cmux-verb-shapes.json selected_row_marker)
                 # for test-double fidelity — a marker-less row is what let the old
                 # field-position parser pass while failing 100% in production — so
                 # the double still behaves like real cmux if a future change routes
                 # through the fallback, NOT because Step 14 asserts against it. The
                 # fallback marker-parser itself is exercised by the unit suite
                 # (tests/unit/spawn_handoff_helpers.py CMUX_LIST_SURFACES_NO_REF /
                 # CMUX_LIST_SURFACES_TWO_ROWS knobs), not here.
                 printf '* surface:7  SDD resume: demo  [selected]\n'; exit 0 ;;
  *)             echo OK; exit 0 ;;
esac
SH
cat > "$SPAWN_STUBS/claude-picker" <<'SH'
#!/usr/bin/env bash
if [ "$1" = "--handoff-contract" ]; then echo 1; exit 0; fi
exit 0
SH
cat > "$SPAWN_STUBS/claude-usage-pace" <<'SH'
#!/usr/bin/env bash
echo '{"windows":[{"key":"session","remaining_pct":63.0}]}'
SH
chmod +x "$SPAWN_STUBS"/*

SPAWN_ARGS=$($PYTHON - <<'PY'
import base64,json
print("v1:"+base64.b64encode(json.dumps(["--append-system-prompt-file","/tmp/a b.md"]).encode()).decode())
PY
)
SPAWN_LOG="$SPAWN_WT/docs/imp-plans/feat/reports/handoff-spawn.log"
HOPS_FILE="$SPAWN_WT/docs/imp-plans/feat/reports/.handoff-hops"

# spawn_run OUT CMUXLOG [extra script args…] — runs the script and captures its rc
# into SPAWN_RC. The `cd "$SPAWN_WT"` is REQUIRED: spawn-handoff-session.sh resolves
# WORKTREE_ROOT via `git rev-parse --show-toplevel` against the CALLER's cwd (it
# never receives a path argument); without it the script inherits this harness's own
# cwd ($WORK) — a different git repo — and prints "REFUSED: worktree not clean"
# instead of exercising the fixture. Ambient SUPERPOWERS_CMUX_MAX_HOPS /
# _MAX_STALL_HOPS are neutralized to empty (=unset) so a developer's shell knobs
# cannot skew the ceiling/stall math (mirrors the unit harness NO_AMBIENT_HOP_KNOBS).
spawn_run() {
  local out="$1" clog="$2"; shift 2
  SPAWN_RC=0
  ( cd "$SPAWN_WT" && \
    CMUX_LOG="$clog" \
    PATH="$SPAWN_STUBS:$PATH" HOME="$SPAWN_HOME" \
    CMUX_WORKSPACE_ID=TEST-WS \
    SUPERPOWERS_CMUX_MAX_HOPS= SUPERPOWERS_CMUX_MAX_STALL_HOPS= \
    CLAUDE_CODE_PICKER_VERSION=2.1.218 \
    CLAUDE_CODE_PICKER_ARGS="$SPAWN_ARGS" \
    CLAUDE_CODE_PICKER_LABEL="Proj-Session-2" \
    CLAUDE_CODE_ENABLE_TELEMETRY=1 \
    SUPERPOWERS_ROOT="$PROJECT" \
    bash "$PROJECT/skills/subagent-driven-development/scripts/spawn-handoff-session.sh" b14 "$@" \
    > "$out" 2>&1 ) || SPAWN_RC=$?
}

# ── Sub-run 1: SUCCESS (surface topology, launch=auto, handshake=ok) ─────────
spawn_run "$SPAWN_WORK/out" "$SPAWN_WORK/cmux.log"
[ "$SPAWN_RC" -eq 0 ] || { echo "FAIL: success spawn exit $SPAWN_RC"; cat "$SPAWN_WORK/out"; exit 1; }
# launch=auto is LOAD-BEARING, asserted FIRST: under picker-manual the successor
# command is a bare `claude-picker '/pickup b14'` and every composed-command
# assertion below becomes vacuous.
grep -q "launch=auto" "$SPAWN_WORK/out" \
  || { echo "FAIL: expected launch=auto — fixture degraded to picker-manual"; cat "$SPAWN_WORK/out"; exit 1; }
# new-surface argv carries the surface-topology flags (successor is a sibling tab
# in the CALLER's own workspace, TEST-WS). Anchored to the new-surface line itself
# (not the whole log) and to the script's actual emission order — --workspace,
# --type terminal, --working-directory, --focus false (create_surface_target()) —
# so this can't pass on a `--focus false` emitted by some other verb.
grep -q "^new-surface .*--workspace TEST-WS .*--type terminal .*--focus false" "$SPAWN_WORK/cmux.log" \
  || { echo "FAIL: new-surface line missing --workspace TEST-WS / --type terminal / --focus false in expected order"; cat "$SPAWN_WORK/cmux.log"; exit 1; }
# rename-tab scoped to the captured surface ref (surface:7 from new-surface stdout).
grep -q "rename-tab .*--surface surface:7" "$SPAWN_WORK/cmux.log" \
  || { echo "FAIL: rename-tab not scoped to --surface surface:7"; cat "$SPAWN_WORK/cmux.log"; exit 1; }
# The launch `send` carries the inline env prefix (SUPERPOWERS_SPAWN_ID) + the
# composed picker command on one line.
grep -F "export SUPERPOWERS_SPAWN_ID=" "$SPAWN_WORK/cmux.log" | grep -qF "claude-picker --non-interactive --pick-version 2.1.218" \
  || { echo "FAIL: send line missing SUPERPOWERS_SPAWN_ID export + composed picker command"; cat "$SPAWN_WORK/cmux.log"; exit 1; }
# Composed successor command, pinned against the `[spawn-handoff] successor
# command: …` diagnostic line (not bare $out) so an unrelated earlier line cannot
# satisfy it (same self-satisfying-grep trap the Task 5 deviations row warned about).
# The label is INCREMENTED, not passed through: Proj-Session-2 -> Proj-Session-3.
grep -qF -- "successor command: claude-picker --non-interactive --pick-version 2.1.218 --telemetry on --session-label Proj-Session-3" "$SPAWN_WORK/out" \
  || { echo "FAIL: composed command missing expected flag order/telemetry/incremented label"; cat "$SPAWN_WORK/out"; exit 1; }
# Forwarded --append-system-prompt-file arg with its shell re-quoting intact (value
# contains a space, so it must survive as one quoted token), immediately followed by
# '/pickup b14' as the LAST argument before the runtime-fallback tail.
grep -qF -- "--append-system-prompt-file '/tmp/a b.md' '/pickup b14' ||" "$SPAWN_WORK/out" \
  || { echo "FAIL: composed command missing forwarded arg (re-quoted) + trailing /pickup b14"; cat "$SPAWN_WORK/out"; exit 1; }
grep -q "notify" "$SPAWN_WORK/cmux.log" || { echo "FAIL: no notify"; exit 1; }
# Exactly ONE wait-for on the success path: the happy path issues a single bounded
# wait; the bounded re-wait fires only after a FIRST wait times out. Two never occur here.
WAITFOR_N=$(grep -c "wait-for" "$SPAWN_WORK/cmux.log" || true)
[ "$WAITFOR_N" -eq 1 ] || { echo "FAIL: expected exactly one wait-for, got $WAITFOR_N"; cat "$SPAWN_WORK/cmux.log"; exit 1; }
# Outcome record: handshake=ok on the captured surface, in the caller's workspace,
# tasks_done=0 (no DONE reports yet). NO post_spawn=partial — the read-screen anchors
# verified both /rename and /rc, so post-spawn setup completed cleanly.
OUTCOME=$(grep " outcome " "$SPAWN_LOG" | head -1)
for tok in "handshake=ok" "surface=surface:7" "workspace=TEST-WS" "tasks_done=0"; do
  printf '%s\n' "$OUTCOME" | grep -qF "$tok" || { echo "FAIL: outcome missing $tok"; echo "$OUTCOME"; exit 1; }
done
case "$OUTCOME" in *post_spawn=partial*) echo "FAIL: post-spawn unverified — read-screen anchors not consumed ($OUTCOME)"; exit 1 ;; esac
# reservation ordering: intent line precedes outcome line
INTENT_LN=$(grep -n " intent " "$SPAWN_LOG" | head -1 | cut -d: -f1)
OUTCOME_LN=$(grep -n " outcome " "$SPAWN_LOG" | head -1 | cut -d: -f1)
[ -n "$INTENT_LN" ] && [ -n "$OUTCOME_LN" ] && [ "$INTENT_LN" -lt "$OUTCOME_LN" ] \
  || { echo "FAIL: reservation ordering (intent before outcome)"; cat "$SPAWN_LOG"; exit 1; }
# hop reserved to 1
[ "$(cat "$HOPS_FILE")" = "1" ] || { echo "FAIL: hop not incremented to 1"; exit 1; }
# N64 self-commit: the successful spawn commits its own bookkeeping, leaving a clean tree.
LAST_SUBJECT=$(git -C "$SPAWN_WT" log --format=%s -1)
[ "$LAST_SUBJECT" = "chore(sdd): record handoff hop 1" ] \
  || { echo "FAIL: bookkeeping commit subject '$LAST_SUBJECT' != 'chore(sdd): record handoff hop 1'"; exit 1; }
[ -z "$(git -C "$SPAWN_WT" status --porcelain)" ] \
  || { echo "FAIL: tree not clean after bookkeeping commit"; git -C "$SPAWN_WT" status --porcelain; exit 1; }
echo "PASS: Step 14a — success: surface topology, launch=auto, handshake=ok, self-commit"

# ── Sub-run 2: POLICY=ask refusal (no --user-approved) ───────────────────────
# Rewrite the committed manifest to spawn_policy=ask and commit it — the clean-tree
# precondition would REFUSE a dirty tree with exit 1, masking the policy gate.
$PYTHON - "$SPAWN_MANIFEST" <<'PY'
import json,sys
p=sys.argv[1]; m=json.load(open(p)); m["handoff"]["spawn_policy"]="ask"
open(p,"w").write(json.dumps(m,indent=2)+"\n")
PY
( cd "$SPAWN_WT" && git commit -qm "policy ask" -- docs/imp-plans/feat/.sdd-session.json )
spawn_run "$SPAWN_WORK/out-ask" "$SPAWN_WORK/cmux-ask.log"
[ "$SPAWN_RC" -eq 3 ] || { echo "FAIL: policy=ask expected rc 3, got $SPAWN_RC"; cat "$SPAWN_WORK/out-ask"; exit 1; }
grep -q "reason=policy-ask" "$SPAWN_WORK/out-ask" \
  || { echo "FAIL: policy=ask missing reason=policy-ask"; cat "$SPAWN_WORK/out-ask"; exit 1; }
# policy-ask refuses BEFORE reserving (Precondition 2b): hop unchanged, no 2nd intent.
[ "$(cat "$HOPS_FILE")" = "1" ] || { echo "FAIL: policy=ask consumed a hop"; exit 1; }
INTENT_N=$(grep -c " intent " "$SPAWN_LOG" || true)
[ "$INTENT_N" -eq 1 ] || { echo "FAIL: policy=ask wrote a second intent record ($INTENT_N)"; cat "$SPAWN_LOG"; exit 1; }
echo "PASS: Step 14b — policy=ask refuses (rc 3, reason=policy-ask, no hop consumed)"

# ── Sub-run 3: OVER-EXPECTED advisory (hop > expected_hops, NOT a stall) ──────
# expected_hops=1 (< the next hop, 2) trips the advisory notify; policy back to auto.
# A prior zero-progress outcome PLUS one committed DONE report (tasks_done becomes 1)
# means progress WAS made this cycle, so the stall gate does not fire.
$PYTHON - "$SPAWN_MANIFEST" <<'PY'
import json,sys
p=sys.argv[1]; m=json.load(open(p))
m["handoff"]["spawn_policy"]="auto"; m["handoff"]["expected_hops"]=1
open(p,"w").write(json.dumps(m,indent=2)+"\n")
PY
# prior zero-progress outcome record
printf '2026-08-03T00:00:00Z prioruuid outcome hop=1 workspace=TEST-WS surface=surface:7 launch=auto bundle=b14 quota=ok tasks_done=0 handshake=ok\n' >> "$SPAWN_LOG"
# one committed DONE report -> count_tasks_done()=1 -> progress -> no stall refusal
cat > "$SPAWN_WT/docs/imp-plans/feat/reports/task-000-implementer-report.md" <<'RPT'
---
schema_version: 1
task_id: 0
status: DONE
files_changed: [{path: x, description: y}]
tests: {written: 1, passing: 1, command: x, result: PASS}
---
body
RPT
( cd "$SPAWN_WT" && git add docs/imp-plans/feat/.sdd-session.json \
    docs/imp-plans/feat/reports/handoff-spawn.log \
    docs/imp-plans/feat/reports/task-000-implementer-report.md \
    && git commit -qm "over-expected fixture state" )
spawn_run "$SPAWN_WORK/out-over" "$SPAWN_WORK/cmux-over.log"
[ "$SPAWN_RC" -eq 0 ] || { echo "FAIL: over-expected spawn exit $SPAWN_RC"; cat "$SPAWN_WORK/out-over"; exit 1; }
# The advisory notify names the budget overrun ("Hop 2 exceeds expected_hops=1 …").
grep "notify" "$SPAWN_WORK/cmux-over.log" | grep -qi "expected" \
  || { echo "FAIL: over-expected missing advisory notify mentioning 'expected'"; cat "$SPAWN_WORK/cmux-over.log"; exit 1; }
echo "PASS: Step 14c — over-expected advisory notify fires without a stall refusal"

rm -rf "$SPAWN_WORK"
echo "PASS: Step 14 — spawn end-to-end: surface topology, handshake, policy dial, bookkeeping commit"

echo ""
echo "E2E PIPELINE PASS - 15 steps composed correctly"
rm -rf "$WORK"
