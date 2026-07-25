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
echo "=== Step 14: spawn-handoff-session.sh end-to-end (stubbed cmux + picker) ==="
# NOTE: exercises THIS checkout's script. The installed live path resolves to the
# main checkout — a post-merge live smoke is required separately (spec §7).
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

# Stubs
cat > "$SPAWN_STUBS/cmux" <<'SH'
#!/usr/bin/env bash
if [ "$1" = "ping" ]; then echo PONG; exit 0; fi
echo "$@" >> "$CMUX_LOG"; exit 0
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
SPAWN_RC=0
# `cd "$SPAWN_WT"` is REQUIRED inside the subshell: spawn-handoff-session.sh
# resolves WORKTREE_ROOT via `git rev-parse --show-toplevel` against the
# CALLER's cwd (it never receives a path argument). Without this cd the script
# would inherit this harness's own cwd ($WORK, set at line 14) — a different
# git repo whose .active-feature and cleanliness have nothing to do with this
# fixture, producing "REFUSED: worktree not clean" instead of exercising the
# fixture at all. Verified empirically: omitting the cd reproduces that exact
# REFUSED line against $WORK.
( cd "$SPAWN_WT" && \
CMUX_LOG="$SPAWN_WORK/cmux.log" \
PATH="$SPAWN_STUBS:$PATH" HOME="$SPAWN_HOME" \
CMUX_WORKSPACE_ID=TEST-WS \
CLAUDE_CODE_PICKER_VERSION=2.1.218 \
CLAUDE_CODE_PICKER_ARGS="$SPAWN_ARGS" \
CLAUDE_CODE_PICKER_LABEL="Proj-Session-2" \
CLAUDE_CODE_ENABLE_TELEMETRY=1 \
SUPERPOWERS_ROOT="$PROJECT" \
bash "$PROJECT/skills/subagent-driven-development/scripts/spawn-handoff-session.sh" b14 \
  > "$SPAWN_WORK/out" 2>&1 ) || SPAWN_RC=$?

[ "$SPAWN_RC" -eq 0 ] || { echo "FAIL: spawn exit $SPAWN_RC"; cat "$SPAWN_WORK/out"; exit 1; }
# launch=auto is LOAD-BEARING, not cosmetic: under picker-manual the successor
# command is a bare `claude-picker '/pickup b14'` and every composed-command
# assertion below becomes vacuous. Assert it FIRST so a fixture regression fails
# here with a clear cause rather than silently passing a hollow test.
grep -q "launch=auto" "$SPAWN_WORK/out" \
  || { echo "FAIL: expected launch=auto — fixture degraded to picker-manual"; cat "$SPAWN_WORK/out"; exit 1; }
grep -q "new-workspace" "$SPAWN_WORK/cmux.log" || { echo "FAIL: no new-workspace"; exit 1; }
grep -q -- "--focus false" "$SPAWN_WORK/cmux.log" || { echo "FAIL: missing --focus false"; exit 1; }
grep -q "notify" "$SPAWN_WORK/cmux.log" || { echo "FAIL: no notify"; exit 1; }
# Composed successor command, pinned against the ACTUAL line this fixture emits
# (`[spawn-handoff] successor command: …`), derived from a real run, not
# hand-authored (see deviations.md Task 10 IndependentDecision). Anchored on
# that specific line's text — not bare `$SPAWN_WORK/out` — so the assertion
# cannot be satisfied by an unrelated earlier diagnostic line (the same
# self-satisfying-grep trap Task 5's deviations row warned Task 6 about).
# 1. Flag ORDER + telemetry value + the label transformation: the label is
#    INCREMENTED, not passed through — the fixture sets Proj-Session-2 and the
#    composed command carries Proj-Session-3 (spawn-handoff-session.sh:284).
grep -qF -- "successor command: claude-picker --non-interactive --pick-version 2.1.218 --telemetry on --session-label Proj-Session-3" "$SPAWN_WORK/out" \
  || { echo "FAIL: composed command missing expected flag order/telemetry/incremented label"; cat "$SPAWN_WORK/out"; exit 1; }
# 2. Forwarded --append-system-prompt-file argument with its shell re-quoting
#    intact (its value contains a space, so it must survive as a single quoted
#    token), immediately followed by '/pickup b14' as the LAST argument before
#    the runtime-fallback tail.
grep -qF -- "--append-system-prompt-file '/tmp/a b.md' '/pickup b14' ||" "$SPAWN_WORK/out" \
  || { echo "FAIL: composed command missing forwarded arg (re-quoted) + trailing /pickup b14"; cat "$SPAWN_WORK/out"; exit 1; }
# reservation ordering: intent line precedes outcome line
SPAWN_LOG="$SPAWN_WT/docs/imp-plans/feat/reports/handoff-spawn.log"
INTENT_LN=$(grep -n " intent " "$SPAWN_LOG" | head -1 | cut -d: -f1)
OUTCOME_LN=$(grep -n " outcome " "$SPAWN_LOG" | head -1 | cut -d: -f1)
[ -n "$INTENT_LN" ] && [ -n "$OUTCOME_LN" ] && [ "$INTENT_LN" -lt "$OUTCOME_LN" ] \
  || { echo "FAIL: reservation ordering (intent before outcome)"; cat "$SPAWN_LOG"; exit 1; }
# hop incremented
[ "$(cat "$SPAWN_WT/docs/imp-plans/feat/reports/.handoff-hops")" = "1" ] \
  || { echo "FAIL: hop not incremented to 1"; exit 1; }
rm -rf "$SPAWN_WORK"
echo "PASS: Step 14 — spawn end-to-end: composed command, notify, reservation-then-outcome"

echo ""
echo "E2E PIPELINE PASS - 15 steps composed correctly"
rm -rf "$WORK"
