---
schema_version: 1
feature_archetype: migration
source_contracts: null
shared_constants: []
pattern_references:
  - name: "superpowers-root-resolution"
    source_files: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    reason: "SUPERPOWERS_ROOT self-resolution preamble pattern (lines 27-34)"
  - name: "hook-feat-prefix"
    source_files: ["tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh"]
    reason: "POC demonstration of feature-dir prefix for artifact paths"
modules: null
tasks:
  - id: 4
    title: "Migrate sdd-pre-dispatch-hook.sh path resolution"
  - id: 5
    title: "Migrate plan-validation-gate-hook.sh"
  - id: 6
    title: "Migrate sdd-stop-hook.sh"
  - id: 7
    title: "Update sdd-report-guard.sh regexes"
  - id: 8
    title: "Add --feature-dir to controller-checkpoint.py and context-summary.py"
  - id: 9
    title: "Update unit tests for hook migrations"
    depends_on: [4, 5, 6, 7, 8]
---

# Per-Feature Directory — Module 2: Hook Script Migration

> **Parent plan:** `docs/imp-plans/2026-05-02-per-feature-directory-plan.md`
> **Module:** 2 of 3
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Migrate all 4 hook scripts and 2 Python scripts to resolve artifact paths from `.active-feature` instead of project root, with root-level fallback for backwards compatibility.

**Source Contracts:** None

**Contract Constraints:**
- Common preamble: `FEAT=""` then `if [ -f ".active-feature" ]; then FEAT=$(cat .active-feature); fi`
- When `$FEAT` is empty, all paths fall back to root-level (backwards compat)
- When `$FEAT` is set, all artifact paths are prefixed: `$FEAT/reports/...`, `$FEAT/deviations.md`, etc.
- `SUPERPOWERS_ROOT` self-resolution must be added to `plan-validation-gate-hook.sh` and `sdd-stop-hook.sh`
- Error messages must dynamically interpolate `$FEAT/` prefix
- `sdd-report-guard.sh` suspicious-pattern regexes need `\S*` before `reports/`

**Pattern References:**
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` lines 27-34 — `SUPERPOWERS_ROOT` self-resolution preamble
- `tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh` — POC feature-dir prefix pattern

**Feature Archetype:** Migration

## File Map

| File | Responsibility |
|------|----------------|
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Pre-dispatch enforcement — ~30 path refs to prefix with `$FEAT` |
| `skills/writing-plans/scripts/plan-validation-gate-hook.sh` | Plan validation gate — add `.active-feature` gate + SUPERPOWERS_ROOT |
| `skills/subagent-driven-development/scripts/sdd-stop-hook.sh` | Stop hook — add `.active-feature` reading + SUPERPOWERS_ROOT |
| `skills/subagent-driven-development/scripts/sdd-report-guard.sh` | Report guard — update suspicious-pattern regexes |
| `skills/subagent-driven-development/scripts/controller-checkpoint.py` | Checkpoint script — add `--feature-dir` argument |
| `skills/subagent-driven-development/scripts/context-summary.py` | Context summary — add `--feature-dir` argument |
| `tests/unit/test_sdd_hard_gates.py` | Update fixture paths for feature-dir layout |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 4 | `sdd-pre-dispatch-hook.sh` | distilled spec | Task 2 |
| Task 5 | `plan-validation-gate-hook.sh` | distilled spec | Task 2 |
| Task 6 | `sdd-stop-hook.sh` | distilled spec | Task 2 |
| Task 7 | `sdd-report-guard.sh` | distilled spec | Task 2 |
| Task 8 | `controller-checkpoint.py`, `context-summary.py` | distilled spec | Task 2 |
| Task 9 | `tests/unit/test_sdd_hard_gates.py` | all hook scripts | Tasks 4-8 |

## Acceptance Criteria

- [ ] `sdd-pre-dispatch-hook.sh` reads `.active-feature` and prefixes all ~30 artifact paths with `$FEAT`
- [ ] `sdd-pre-dispatch-hook.sh` falls back to root-level paths when `.active-feature` absent
- [ ] `plan-validation-gate-hook.sh` blocks SDD/executing-plans when `.active-feature` is missing
- [ ] `plan-validation-gate-hook.sh` has `SUPERPOWERS_ROOT` self-resolution (no hardcoded absolute paths)
- [ ] `sdd-stop-hook.sh` reads `.active-feature`, has `SUPERPOWERS_ROOT` self-resolution
- [ ] `sdd-report-guard.sh` suspicious-pattern regexes match feature-dir report paths
- [ ] `controller-checkpoint.py` and `context-summary.py` accept `--feature-dir` and resolve paths relative to it
- [ ] All existing unit tests in `test_sdd_hard_gates.py` updated and passing
- [ ] Error messages in hooks show `$FEAT/`-prefixed paths when `$FEAT` is set

---

## Tasks

### Task 4: Migrate sdd-pre-dispatch-hook.sh path resolution

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`

**Pattern References:**
- `tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh` — POC feature-dir prefix pattern

- [x] **Step 1: Add `.active-feature` preamble after CWD resolution**

After line 61 (`cd "$CWD" || exit 0`), add:

```bash
# ─── Resolve active feature directory ─────────────────────────────────────
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi

# Helper: resolve artifact path with feature-dir prefix (falls back to root)
feat_path() {
  if [ -n "$FEAT" ]; then
    echo "$FEAT/$1"
  else
    echo "$1"
  fi
}

# Resolved artifact locations
DEVIATIONS_FILE=$(feat_path "deviations.md")
REPORTS_DIR=$(feat_path "reports")
DISPATCH_LOG=$(feat_path "reports/.dispatch-log")
# Note: when FEAT is empty, DEVIATIONS_FILE="deviations.md" which doesn't exist
# in old layout (was "DEVIATIONS.md"). The fallback handles this:
if [ -z "$FEAT" ] && [ ! -f "$DEVIATIONS_FILE" ] && [ -f "DEVIATIONS.md" ]; then
  DEVIATIONS_FILE="DEVIATIONS.md"
fi
if [ -z "$FEAT" ] && [ ! -d "$REPORTS_DIR" ] && [ -d "reports" ]; then
  REPORTS_DIR="reports"
  DISPATCH_LOG="reports/.dispatch-log"
fi
```

- [x] **Step 2: Update `task_report_glob()` to use `$REPORTS_DIR`**

Change the `task_report_glob()` function (around line 118-124):

```bash
task_report_glob() {
  local task_num="$1"
  local report_type="$2"
  local padded
  padded=$(printf "%03d" "$task_num" 2>/dev/null || echo "$task_num")
  echo "${REPORTS_DIR}/task-${padded}-${report_type}*"
}
```

- [x] **Step 3: Update Check 1 (branch safety) to use resolved paths**

Replace the `SDD_ARTIFACTS_EXIST` check (around line 164-166):

```bash
  if [ -d "$REPORTS_DIR" ] && [ -f "$DEVIATIONS_FILE" ]; then
    SDD_ARTIFACTS_EXIST=true
  fi
```

- [x] **Step 4: Update Check 2 (pre-execution audit) to use `$REPORTS_DIR`**

Replace line ~197:

```bash
AUDIT_RESULT=$(check_report_file "${REPORTS_DIR}/pre-execution-audit*" "pre-execution audit")
```

Update the BLOCKED error message to use `$REPORTS_DIR`:

```bash
    ERRORS+=("BLOCKED: No pre-execution audit report found (${REPORTS_DIR}/pre-execution-audit*). Complete the Pre-Execution Audit: (1) Write self-assessment to ${REPORTS_DIR}/pre-execution-audit-self-assessment.md, (2) Dispatch auditor via pre-execution-audit-prompt.md, (3) Resolve all remediation orders, (4) Save audit report to ${REPORTS_DIR}/pre-execution-audit.md.")
```

- [x] **Step 5: Update Check 3 (DEVIATIONS.md and reports/) to use resolved paths**

Replace lines ~208-216:

```bash
if [ ! -f "$DEVIATIONS_FILE" ]; then
  ERRORS+=("BLOCKED: ${DEVIATIONS_FILE} does not exist. Create it with the SDD template before dispatching tasks.")
fi

if [ ! -d "$REPORTS_DIR" ]; then
  ERRORS+=("BLOCKED: ${REPORTS_DIR}/ directory does not exist. Create it before dispatching tasks.")
fi
```

- [x] **Step 6: Update Check 3b (report naming) to use `$REPORTS_DIR`**

Replace the glob at line ~223:

```bash
  for rf in "${REPORTS_DIR}"/*.md; do
```

And the BLOCKED message at line ~238 to reference `$REPORTS_DIR`.

- [x] **Step 7: Update Check 4 (previous task reports) error messages**

All error messages in Check 4 (lines ~252-308) that reference `reports/task-NNN-*` should use `${REPORTS_DIR}/task-NNN-*`. The `task_report_glob()` change in Step 2 handles the glob patterns; only the error message strings need updating.

- [x] **Step 8: Update Check 4c (dispatch provenance) to use `$DISPATCH_LOG`**

Replace line ~314:

```bash
  DISPATCH_LOG_PATH="$DISPATCH_LOG"
  if [ -f "$DISPATCH_LOG_PATH" ]; then
```

Update all references to `"reports/.dispatch-log"` in error messages to `"$DISPATCH_LOG"`.

- [x] **Step 9: Update Check 5 (Source Contracts / plan search) to use `$FEAT`**

Replace the plan file search loop (lines ~350-357). When `$FEAT` is set, search only `$FEAT/*.md`. When empty, search `docs/imp-plans/*.md docs/plans/*.md`:

```bash
  if [ -n "$FEAT" ]; then
    PLAN_SEARCH_GLOB="$FEAT/*.md"
  else
    PLAN_SEARCH_GLOB="docs/imp-plans/*.md docs/plans/*.md"
  fi
  for plan_file in $PLAN_SEARCH_GLOB; do
```

- [x] **Step 10: Update Check 5b (pending deviations) to use `$DEVIATIONS_FILE`**

Replace line ~378:

```bash
if [ -f "$DEVIATIONS_FILE" ]; then
  PENDING_COUNT=$(grep -ciE '\|\s*Pending\s*\|' "$DEVIATIONS_FILE" 2>/dev/null || echo "0")
```

- [x] **Step 11: Update Check 5c (checkpoint file) to use `$REPORTS_DIR`**

Replace line ~391:

```bash
  CHECKPOINT_FILE="${REPORTS_DIR}/checkpoint-pre-dispatch-${TASK_PADDED}.json"
```

Update the BLOCKED error message to reference `$REPORTS_DIR`. **Note:** The error message at line ~393 contains an embedded command string with `--deviations-file DEVIATIONS.md --reports-dir reports/` — update both path arguments in the command to use `$DEVIATIONS_FILE` and `$REPORTS_DIR`.

- [x] **Step 12: Update Check 5d (partner review) to use `$REPORTS_DIR`**

Replace lines ~405-406:

```bash
  PARTNER_FILE="${REPORTS_DIR}/partner-review-${TASK_PADDED}.md"
  PARTNER_FILE_MIN="${REPORTS_DIR}/partner-review-${TASK_PADDED}-minimum-tier.md"
```

- [x] **Step 13: Update Check 6 (token estimation plan search) to use `$FEAT`**

Replace the plan search loop (lines ~425-433) with the same `PLAN_SEARCH_GLOB` pattern from Step 9.

- [x] **Step 14: Update Check 6b (context summary) to use `$REPORTS_DIR`**

Replace the plan search (lines ~482-488) and the context-summary check (line ~493):

```bash
      if [ ! -f "${REPORTS_DIR}/context-summary.md" ]; then
```

Update the BLOCKED error message to use `$REPORTS_DIR` and `$DEVIATIONS_FILE`. **Note:** The error message at line ~494 contains an embedded command string with `--reports-dir reports/ --deviations-file DEVIATIONS.md --output reports/context-summary.md` — update all three path arguments to use `$REPORTS_DIR`, `$DEVIATIONS_FILE`, and `${REPORTS_DIR}/context-summary.md`.

- [x] **Step 15: Update Check 7 (context load) to use resolved paths**

Replace the file size summation (lines ~521-540):

```bash
  if [ -n "$FEAT" ]; then
    PLAN_GLOB="$FEAT/*.md"
  else
    PLAN_GLOB="docs/imp-plans/*.md docs/plans/*.md"
  fi
  for pf in $PLAN_GLOB; do
```

And the DEVIATIONS.md size check:

```bash
  if [ -f "$DEVIATIONS_FILE" ]; then
    DEV_SIZE=$(wc -c < "$DEVIATIONS_FILE" 2>/dev/null | tr -d ' ')
```

And the reports glob:

```bash
  for rf in "${REPORTS_DIR}"/*.md; do
```

- [x] **Step 16: Update reviewer dispatch logging to use `$DISPATCH_LOG`**

Replace line ~87-102 (reviewer logging section):

```bash
  if [ -d "$REPORTS_DIR" ]; then
    ...
    if [ -n "$REVIEW_TASK" ]; then
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH reviewer task=$REVIEW_TASK type=$REVIEW_TYPE" >> "$DISPATCH_LOG"
    fi
  fi
```

- [x] **Step 17: Update the SDD REMINDER additionalContext**

Find the `CONTEXT=` string near the end of the file (line ~552). Replace the hardcoded paths with resolved variables:

```bash
CONTEXT="SDD REMINDER: After this subagent completes, you must: (1) Save the implementer report to ${REPORTS_DIR}/task-N-implementer-report.md, (2) Dispatch spec compliance review and save to ${REPORTS_DIR}/task-N-spec-review.md, (3) Dispatch code quality review and save to ${REPORTS_DIR}/task-N-quality-review.md, (4) Log any DONE_WITH_CONCERNS to ${DEVIATIONS_FILE}, (5) Update plan checkboxes. The next task dispatch will be BLOCKED if these reports are missing or empty."
```

Also update the context-summary warning (line ~545) to reference `$REPORTS_DIR` if it contains hardcoded paths.

- [x] **Step 18: Verify the hook runs without errors**

Run the hook with mock JSON input against a temp directory with `.active-feature`:

```bash
echo '{"tool_input":{"description":"test dispatch","prompt":"test"},"cwd":"/tmp/test-hook"}' | bash skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
```

Expected: exits 0 (allows — non-SDD dispatch).

- [x] **Step 19: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "feat: migrate sdd-pre-dispatch-hook to .active-feature path resolution"
```

---

### Task 5: Migrate plan-validation-gate-hook.sh

**Files:**
- Modify: `skills/writing-plans/scripts/plan-validation-gate-hook.sh`

**Pattern References:**
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` lines 27-34 — `SUPERPOWERS_ROOT` self-resolution preamble

- [x] **Step 1: Add SUPERPOWERS_ROOT self-resolution and PYTHON derivation**

Replace the hardcoded `VALIDATE_PLAN_SCRIPT` line (line 24) with:

```bash
SUPERPOWERS_ROOT="${SUPERPOWERS_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

if [ -f "$SUPERPOWERS_ROOT/.venv/bin/python3" ]; then
  PYTHON="$SUPERPOWERS_ROOT/.venv/bin/python3"
else
  PYTHON="python3"
fi

VALIDATE_PLAN_SCRIPT="$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/validate-plan.py"
```

- [x] **Step 2: Add `.active-feature` preamble and gate**

After `cd "$CWD" || exit 0` (line 49), add:

```bash
# ─── Resolve active feature directory ─────────────────────────────────────
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi

# Gate: .active-feature must exist for execution skills
if [ -z "$FEAT" ]; then
  echo "BLOCKED: No .active-feature file found. Establish a feature name by invoking superpowers:brainstorming or superpowers:writing-plans first. The feature name determines the directory structure for all execution artifacts." >&2
  exit 2
fi
```

- [x] **Step 3: Update manifest discovery to use `$FEAT` directly**

Replace the manifest discovery block (lines ~56-78):

```bash
MANIFEST=""
if [ -n "$FEAT" ]; then
  if [ -f "$FEAT/plan-manifest.txt" ]; then
    MANIFEST="$FEAT/plan-manifest.txt"
  fi
else
  # Legacy fallback: search standard locations
  for dir in docs/imp-plans docs/plans; do
    if [ -f "$dir/plan-manifest.txt" ]; then
      MANIFEST="$dir/plan-manifest.txt"
      break
    fi
    if [ -d "$dir" ]; then
      FOUND=$(find "$dir" -maxdepth 2 -name "plan-manifest.txt" -type f 2>/dev/null | head -1)
      if [ -n "$FOUND" ]; then
        MANIFEST="$FOUND"
        break
      fi
    fi
  done
fi
```

- [x] **Step 4: Update Pydantic validator path and Python invocation**

Replace the `PYDANTIC_VALIDATOR` path (line ~169) to use `$SUPERPOWERS_ROOT` for consistency with the `VALIDATE_PLAN_SCRIPT` path:

```bash
PYDANTIC_VALIDATOR="$SUPERPOWERS_ROOT/skills/scripts/models/validators.py"
```

Replace line ~174 (`.venv/bin/python3`) with `$PYTHON`:

```bash
      $PYTHON "$PYDANTIC_VALIDATOR" plan "$pf" 2>/tmp/pydantic-validator-err
```

- [x] **Step 5: Update review report search to check `$FEAT` first**

Replace the review report search (lines ~193-236):

```bash
REVIEW_REPORT=""
if [ -n "$FEAT" ]; then
  if [ -f "$FEAT/plan-review-report.md" ]; then
    REVIEW_REPORT="$FEAT/plan-review-report.md"
  fi
fi

if [ -z "$REVIEW_REPORT" ]; then
  # Existing search logic as fallback
  SEARCH_DIRS=()
  for pf in "${PLAN_FILES[@]}"; do
    PF_DIR=$(dirname "$pf")
    ALREADY=false
    for sd in "${SEARCH_DIRS[@]}"; do
      [ "$sd" = "$PF_DIR" ] && ALREADY=true && break
    done
    [ "$ALREADY" = false ] && SEARCH_DIRS+=("$PF_DIR")
  done
  for dir in docs/imp-plans docs/plans; do
    [ -d "$dir" ] && SEARCH_DIRS+=("$dir")
  done
  for dir in "${SEARCH_DIRS[@]}"; do
    FOUND=$(find "$dir" -maxdepth 1 -name "*plan-review-report*" -type f 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
      REVIEW_REPORT="$FOUND"
      break
    fi
  done
fi
```

- [x] **Step 6: Verify the hook runs**

Test with mock input:

```bash
echo '{"tool_input":{"skill":"superpowers:subagent-driven-development"},"cwd":"/tmp/test"}' | bash skills/writing-plans/scripts/plan-validation-gate-hook.sh
```

Expected: exits 2 (BLOCKED — no `.active-feature`).

- [x] **Step 7: Commit**

```bash
git add skills/writing-plans/scripts/plan-validation-gate-hook.sh
git commit -m "feat: migrate plan-validation-gate to .active-feature with SUPERPOWERS_ROOT"
```

---

### Task 6: Migrate sdd-stop-hook.sh

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-stop-hook.sh`

**Pattern References:**
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` lines 27-34 — `SUPERPOWERS_ROOT` preamble

- [x] **Step 1: Add SUPERPOWERS_ROOT resolution**

Replace the hardcoded `CHECKPOINT_SCRIPT` (line 14):

```bash
SUPERPOWERS_ROOT="${SUPERPOWERS_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

if [ -f "$SUPERPOWERS_ROOT/.venv/bin/python3" ]; then
  PYTHON="$SUPERPOWERS_ROOT/.venv/bin/python3"
else
  PYTHON="python3"
fi

CHECKPOINT_SCRIPT="$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/controller-checkpoint.py"
```

- [x] **Step 2: Add `.active-feature` preamble after CWD extraction**

After line 28 (`fi`), add:

```bash
# ─── Resolve active feature directory ─────────────────────────────────────
FEAT=""
if [ -f "${CWD}/.active-feature" ]; then
  FEAT=$(cat "${CWD}/.active-feature")
fi
```

- [x] **Step 3: Update SDD detection to use `$FEAT`**

Replace the detection block (lines ~34-39):

```bash
if [ -n "$FEAT" ]; then
  REPORTS_DIR="${CWD}/${FEAT}/reports"
  DEVIATIONS_FILE="${CWD}/${FEAT}/deviations.md"
else
  REPORTS_DIR="${CWD}/reports"
  DEVIATIONS_FILE="${CWD}/DEVIATIONS.md"
fi

if [ ! -d "$REPORTS_DIR" ]; then
  exit 0
fi

if [ ! -f "$DEVIATIONS_FILE" ]; then
  exit 0
fi
```

- [x] **Step 4: Update plan discovery to use `$FEAT`**

Replace the plan file search (lines ~50-56):

```bash
PLAN_FILE=""
if [ -n "$FEAT" ]; then
  for candidate in "${CWD}/${FEAT}/"*.md; do
    if [ -f "$candidate" ]; then
      PLAN_FILE="$candidate"
      break
    fi
  done
else
  for candidate in "${CWD}/docs/imp-plans/"*.md "${CWD}/docs/plans/"*.md; do
    if [ -f "$candidate" ]; then
      PLAN_FILE="$candidate"
      break
    fi
  done
fi
```

- [x] **Step 5: Update honesty check archival to use `$REPORTS_DIR`**

Replace the honesty file search (lines ~70-75):

```bash
  for candidate in "${REPORTS_DIR}"/honesty-check-*.md; do
```

- [x] **Step 6: Update checkpoint invocation to use resolved paths**

Replace lines ~108-114:

```bash
CHECKPOINT_OUTPUT=$(
  $PYTHON "$CHECKPOINT_SCRIPT" \
    --phase pre-completion \
    --plan-file "$PLAN_FILE" \
    --deviations-file "$DEVIATIONS_FILE" \
    --reports-dir "$REPORTS_DIR/" \
    2>/dev/null
)
```

**Note:** Line ~149 uses bare `python3` (not `$PYTHON`) for a stdlib-only JSON encoding call. This is intentional — consistent with the pattern in `sdd-pre-dispatch-hook.sh` (lines 273/275/563) where `$PYTHON` is reserved for scripts that need the venv (PyYAML, Pydantic). Do not change this to `$PYTHON`.

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-stop-hook.sh
git commit -m "feat: migrate sdd-stop-hook to .active-feature with SUPERPOWERS_ROOT"
```

---

### Task 7: Update sdd-report-guard.sh regexes

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-report-guard.sh`

- [x] **Step 1: Update suspicious-pattern regexes**

Replace the regex on line ~46:

```bash
if echo "$COMMAND" | grep -qiE '(touch\s+\S*reports/|>\s*\S*reports/task-|echo\s+["'"'"']?\s*["'"'"']?\s*>\s*\S*reports/|cat\s*/dev/null\s*>\s*\S*reports/)'; then
```

The `\S*` before `reports/` matches zero-or-more non-whitespace characters, handling both:
- Old: `touch reports/task-001-...`
- New: `touch docs/imp-plans/2026-05-02-feature/reports/task-001-...`

- [x] **Step 2: Verify the regex matches both old and new paths**

```bash
echo "touch reports/task-001-implementer-report.md" | grep -qiE '(touch\s+\S*reports/)' && echo "OLD MATCH"
echo "touch docs/imp-plans/2026-05-02-feature/reports/task-001-implementer-report.md" | grep -qiE '(touch\s+\S*reports/)' && echo "NEW MATCH"
```

Expected: Both print their respective MATCH messages.

- [x] **Step 3: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-report-guard.sh
git commit -m "fix: update report-guard regexes to match feature-dir paths"
```

---

### Task 8: Add --feature-dir to controller-checkpoint.py and context-summary.py

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py`
- Modify: `skills/subagent-driven-development/scripts/context-summary.py`

- [x] **Step 1: Read controller-checkpoint.py argument parsing**

Read `skills/subagent-driven-development/scripts/controller-checkpoint.py` and find the `argparse` section. Note the existing `--reports-dir` and `--deviations-file` arguments.

- [x] **Step 2: Add --feature-dir argument to controller-checkpoint.py**

In the argparse section, add:

```python
parser.add_argument(
    "--feature-dir",
    help="Active feature directory. When provided, --reports-dir and --deviations-file "
         "are resolved relative to this path (if not explicitly set).",
    default=None,
)
```

After parsing args, add resolution logic:

```python
if args.feature_dir:
    if not args.reports_dir:
        args.reports_dir = f"{args.feature_dir}/reports/"
    if not args.deviations_file:
        args.deviations_file = f"{args.feature_dir}/deviations.md"
```

- [x] **Step 3: Read context-summary.py argument parsing**

Read `skills/subagent-driven-development/scripts/context-summary.py` and find the argparse section. Note that `--reports-dir`, `--deviations-file`, and `--output` are all `required=True`.

- [x] **Step 4: Add --feature-dir argument to context-summary.py**

**Important:** `context-summary.py` has `--reports-dir`, `--deviations-file`, and `--output` as `required=True`. Change all three to `required=False, default=None`. Add `--feature-dir` argument. After parsing, add resolution logic that fills in defaults from `--feature-dir`:

```python
if args.feature_dir:
    if not args.reports_dir:
        args.reports_dir = f"{args.feature_dir}/reports/"
    if not args.deviations_file:
        args.deviations_file = f"{args.feature_dir}/deviations.md"
    if not args.output:
        args.output = f"{args.feature_dir}/reports/context-summary.md"

# Validate that all required paths are set (either explicitly or via --feature-dir)
missing = []
if not args.reports_dir:
    missing.append("--reports-dir")
if not args.deviations_file:
    missing.append("--deviations-file")
if not args.output:
    missing.append("--output")
if missing:
    parser.error(f"Missing required arguments (provide explicitly or via --feature-dir): {', '.join(missing)}")
```

- [x] **Step 5: Verify both scripts accept the new argument**

```bash
.venv/bin/python3 skills/subagent-driven-development/scripts/controller-checkpoint.py --help | grep feature-dir
.venv/bin/python3 skills/subagent-driven-development/scripts/context-summary.py --help | grep feature-dir
```

Expected: Both show the `--feature-dir` argument.

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py skills/subagent-driven-development/scripts/context-summary.py
git commit -m "feat: add --feature-dir argument to checkpoint and context-summary scripts"
```

---

### Task 9: Update unit tests for hook migrations

**Files:**
- Modify: `tests/unit/test_sdd_hard_gates.py`

- [x] **Step 1: Read current test file**

Read `tests/unit/test_sdd_hard_gates.py` in full. Note the fixture setup — it creates temp directories with `reports/` and `DEVIATIONS.md` at root. These need to support both root-level (backwards compat) and feature-dir layouts.

- [x] **Step 2: Add feature-dir fixture**

Add a pytest fixture that creates a feature-dir layout with `.active-feature`:

```python
@pytest.fixture
def feature_dir_workspace(tmp_path):
    """Create a workspace with per-feature directory layout."""
    feat_path = "docs/imp-plans/2026-05-02-test-feature"
    feat_dir = tmp_path / feat_path
    reports_dir = feat_dir / "reports"
    reports_dir.mkdir(parents=True)

    (feat_dir / "deviations.md").write_text("# Deviations\n\n| # | Description | Disposition |\n")
    (feat_dir / "plan.md").write_text("### Task 0: Setup\n### Task 1: Build\n")

    active_feature = tmp_path / ".active-feature"
    active_feature.write_text(feat_path)

    return tmp_path, feat_path, feat_dir, reports_dir
```

- [x] **Step 3: Update existing tests that create root-level fixtures**

For each test that creates `reports/` and `DEVIATIONS.md` at `tmp_path` root, add a parallel test (or parameterize) that uses the `feature_dir_workspace` fixture instead. The hook should produce the same behavior with both layouts.

Key tests to update/duplicate:
- Pre-execution audit check (Check 2)
- DEVIATIONS.md existence check (Check 3)
- Previous task report checks (Check 4)
- Checkpoint file check (Check 5c)
- Partner review check (Check 5d)

- [x] **Step 4: Add test for `.active-feature` missing gate (plan-validation-gate)**

```python
def test_plan_validation_gate_blocks_without_active_feature(tmp_path):
    """plan-validation-gate should block SDD invocation when no .active-feature exists."""
    hook_input = json.dumps({
        "tool_input": {"skill": "superpowers:subagent-driven-development"},
        "cwd": str(tmp_path),
    })
    result = subprocess.run(
        ["bash", PLAN_VALIDATION_GATE_PATH],
        input=hook_input, capture_output=True, text=True
    )
    assert result.returncode == 2
    assert ".active-feature" in result.stderr
```

- [x] **Step 5: Add test for backwards-compat fallback**

```python
def test_pre_dispatch_falls_back_to_root_without_active_feature(tmp_path):
    """Without .active-feature, hook should check root-level reports/ and DEVIATIONS.md."""
    (tmp_path / "reports").mkdir()
    (tmp_path / "DEVIATIONS.md").write_text("# Deviations")
    (tmp_path / "reports" / "pre-execution-audit.md").write_text("x" * 100)

    hook_input = json.dumps({
        "tool_input": {
            "description": "Implement task 0",
            "prompt": "you are implementing task 0"
        },
        "cwd": str(tmp_path),
    })
    result = subprocess.run(
        ["bash", SDD_PRE_DISPATCH_HOOK_PATH],
        input=hook_input, capture_output=True, text=True
    )
    # Should not fail on "missing .active-feature" — falls back to root paths
    # May fail on other checks (missing task reports, etc.) but not on path resolution
    assert ".active-feature" not in result.stderr
```

- [x] **Step 6: Run all tests**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v`
Expected: All tests pass.

- [x] **Step 7: Commit**

```bash
git add tests/unit/test_sdd_hard_gates.py
git commit -m "test: update hard gates tests for .active-feature and feature-dir layout"
```
