---
schema_version: 1
feature_archetype: refactor
# enforcement_tier: standard — added by this plan's own Task 3
source_contracts: null
shared_constants:
  - path: "skills.scripts.models.sdd_session.TIER_PROFILES"
    value: "dict mapping tier name to enforcement + process_requirements"
    reason: "Hook reads manifest which was materialized from these profiles"
pattern_references:
  - name: "sdd-hook-tests"
    source_files: ["tests/unit/test_sdd_hard_gates.py", "tests/unit/sdd_test_helpers.py"]
    reason: "Hook test patterns: make_hook_input, setup_full_sdd_workspace, subprocess invocation"
tasks:
  - id: 6
    title: "Hook path resolution rewrite"
    pattern_references: ["sdd-hook-tests"]
  - id: 7
    title: "Hook dispatch detection rewrite"
    depends_on: [6]
  - id: 8
    title: "Hook conditional checks by tier"
    depends_on: [7]
  - id: 9
    title: "Hook process requirements injection and dispatch log sentinel"
    depends_on: [8]
  - id: 10
    title: "Hook legacy fallback"
    depends_on: [9]
  - id: 11
    title: "Hook rewrite tests"
    depends_on: [10]
    pattern_references: ["sdd-hook-tests"]
---

# Module 2: Pre-Dispatch Hook Rewrite

**Goal:** Rewrite `sdd-pre-dispatch-hook.sh` to read from the session manifest (when present), conditionalize all checks by tier, inject process requirements, add dispatch log sentinel, and preserve legacy fallback.

**Source Contracts:** None

**Reference spec:** `spec-distilled.md` §Pre-Dispatch Hook (contract verification in Module 1 Task 0)

**Contract Constraints:**
- Hook resolves `.active-feature` from `git rev-parse --show-toplevel` (CWD-stable)
- Hook reads manifest from `$GIT_ROOT/$FEAT/.sdd-session.json`
- All artifact paths come from manifest's `paths` object
- Passthrough: check `tool_input.subagent_type` if available; fall back to description patterns
- Reviewer dispatches logged to dispatch log and allowed (unchanged)
- Task number validated against manifest's `task_range`
- Each check gated by manifest's `enforcement.*` field
- Process requirements injected into `additionalContext`
- Dispatch log sentinel: `# sdd-hook-sentinel <sha256>` on first reviewer dispatch; WARN on implementer dispatch if missing
- Legacy regex path preserved behind manifest-absence check

**Pattern References:**
- `tests/unit/test_sdd_hard_gates.py` — hook subprocess test pattern
- `tests/unit/sdd_test_helpers.py` — `make_hook_input`, `setup_full_sdd_workspace`

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Major rewrite | Manifest-based enforcement with legacy fallback |
| `tests/unit/test_sdd_hard_gates.py` | Extend | Add manifest-mode tests alongside existing legacy tests |
| `tests/unit/sdd_test_helpers.py` | Extend | Add manifest workspace setup helpers |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 6 | `sdd-pre-dispatch-hook.sh` (lines 1-90: path resolution) | — | Module 1 |
| Task 7 | `sdd-pre-dispatch-hook.sh` (lines 91-141: dispatch detection) | — | Task 6 |
| Task 8 | `sdd-pre-dispatch-hook.sh` (lines 185-560: check conditionalization) | — | Task 7 |
| Task 9 | `sdd-pre-dispatch-hook.sh` (lines 560-634: additionalContext + sentinel) | — | Task 8 |
| Task 10 | `sdd-pre-dispatch-hook.sh` (integration: legacy fallback branch) | — | Task 9 |
| Task 11 | `tests/unit/test_sdd_hard_gates.py`, `tests/unit/sdd_test_helpers.py` | `sdd-pre-dispatch-hook.sh` | Task 10 |

Note: Tasks 6-10 are sequential edits to the same file. They MUST execute in order.

## Acceptance Criteria

- [x] Hook resolves all paths from git root when manifest present (Task 6)
- [x] Hook reads tier from manifest and conditionalizes all checks (Task 8)
- [x] Micro-tier dispatches skip partner review, checkpoint, pre-execution audit, dispatch provenance (Task 8 gates; verified by Task 11 `test_micro_tier_skips_partner_review_check`)
- [x] Standard-tier behavior identical to current behavior (Task 10 verification: 35/35 regression tests pass; Task 11 `test_standard_tier_blocks_without_partner_review`)
- [x] Process requirements injected into `additionalContext` on every allowed dispatch (Task 9; verified by Task 11 `test_process_requirements_injected`)
- [x] Dispatch log sentinel written on first reviewer dispatch (Task 9; edge case where REVIEW_TASK is empty noted in deviations and tested by Task 11 `test_unparseable_reviewer_skips_sentinel_write`)
- [x] Legacy fallback works when no manifest exists (Tasks 6-9 wrapping; Task 10 verification + manual smoke test)
- [x] All existing hook tests still pass (16/16 after Tasks 6-9 each; 35/35 after Task 10; 41/41 after Task 11)

---

### Task 6: Hook Path Resolution Rewrite ✅ (commit ede52a8)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (lines 54-90)

- [x] **Step 1: Add manifest resolution block after CWD extraction** (deviated: used `$GIT_ROOT/$FEAT/` for active_module_file reconstruction — see deviations.md row 3)

After line 61 (`cd "$CWD" || exit 0`), insert a new block that attempts manifest-based resolution first:

```bash
# ─── Manifest-based path resolution (CWD-stable) ────────────────────────
# Try git-root-relative resolution first. Falls back to legacy CWD-relative
# resolution if no manifest exists.
MANIFEST=""
MANIFEST_MODE=false
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")

if [ -n "$GIT_ROOT" ] && [ -f "$GIT_ROOT/.active-feature" ]; then
  FEAT_FROM_ROOT=$(cat "$GIT_ROOT/.active-feature" 2>/dev/null | tr -d '\n' | sed 's|/$||')
  if [ -n "$FEAT_FROM_ROOT" ] && [ -f "$GIT_ROOT/$FEAT_FROM_ROOT/.sdd-session.json" ]; then
    MANIFEST="$GIT_ROOT/$FEAT_FROM_ROOT/.sdd-session.json"
    MANIFEST_MODE=true
    # Read all paths from manifest — CWD-stable
    FEAT="$FEAT_FROM_ROOT"
    DEVIATIONS_FILE="$GIT_ROOT/$(jq -r '.paths.deviations_file' "$MANIFEST")"
    REPORTS_DIR="$GIT_ROOT/$(jq -r '.paths.reports_dir' "$MANIFEST")"
    DISPATCH_LOG="$GIT_ROOT/$(jq -r '.paths.dispatch_log' "$MANIFEST")"
    # Read enforcement and tier
    MANIFEST_TIER=$(jq -r '.tier' "$MANIFEST")
    MANIFEST_TASK_START=$(jq -r '.task_range[0]' "$MANIFEST")
    MANIFEST_TASK_END=$(jq -r '.task_range[1]' "$MANIFEST")
    MANIFEST_PLAN_FILE="$GIT_ROOT/$(jq -r '.plan_file' "$MANIFEST")"
    MANIFEST_MODULE_FILE=$(jq -r '.active_module_file // empty' "$MANIFEST")
    if [ -n "$MANIFEST_MODULE_FILE" ]; then
      MANIFEST_MODULE_FILE="$GIT_ROOT/$MANIFEST_MODULE_FILE"
    fi
  fi
fi
```

- [x] **Step 2: Wrap existing path resolution in else branch**

Wrap the existing `FEAT=""` / `.active-feature` / `feat_path()` block (lines 64-90) inside:

```bash
if [ "$MANIFEST_MODE" = false ]; then
  # ─── Legacy CWD-relative path resolution ─────────────────────────────
  # (existing code unchanged)
  ...
fi
```

- [x] **Step 3: Verify hook still works in legacy mode**

Run existing tests to confirm no breakage:

```bash
.venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v -x
```

Expected: All existing tests PASS (16/16 PASS)

- [x] **Step 4: Commit** (`ede52a8`)

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "refactor: add manifest-based path resolution to pre-dispatch hook"
```

---

### Task 7: Hook Dispatch Detection Rewrite ✅ (commit 0888cdc)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (lines 92-141 → actual 133-178 post-Task 6)

- [x] **Step 1: Add manifest-mode dispatch detection** (with set-u initializations — see deviations.md row 5)

In manifest mode, dispatch detection changes from regex to manifest-presence. Before the existing regex block (line 94), add:

```bash
if [ "$MANIFEST_MODE" = true ]; then
  # ─── Manifest-mode dispatch detection ──────────────────────────────────
  # Any Agent dispatch when manifest exists is subject to enforcement.
  # Passthrough: check subagent_type if available, then description patterns.
  SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // ""' 2>/dev/null)

  # Known non-implementer agent types pass through
  if echo "$SUBAGENT_TYPE" | grep -qiE '^(Explore|general-purpose|Plan|debugger|feature-dev|code-reviewer|code-simplifier)$'; then
    exit 0
  fi

  # Reviewer detection (log to dispatch log, then allow)
  IS_REVIEWER=false
  if echo "$DESCRIPTION" | grep -qiE '(review|spec.compliance|code.quality|spec.review|quality.review|trace.audit|partner.review)'; then
    IS_REVIEWER=true
  fi

  if [ "$IS_REVIEWER" = true ]; then
    # Log reviewer dispatch (same as legacy) and allow
    if [ -d "$(dirname "$DISPATCH_LOG")" ]; then
      REVIEW_TASK=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
      REVIEW_TYPE="unknown"
      if echo "$DESCRIPTION" | grep -qiE '(spec.compliance|spec.review)'; then REVIEW_TYPE="spec-review"
      elif echo "$DESCRIPTION" | grep -qiE '(code.quality|quality.review)'; then REVIEW_TYPE="quality-review"
      elif echo "$DESCRIPTION" | grep -qiE 'trace.audit'; then REVIEW_TYPE="trace-audit"
      elif echo "$DESCRIPTION" | grep -qiE '(partner.review|controller.partner)'; then REVIEW_TYPE="partner-review"
      fi
      if [ -n "$REVIEW_TASK" ]; then
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH reviewer task=$REVIEW_TASK type=$REVIEW_TYPE" >> "$DISPATCH_LOG"
      fi
    fi
    # (Sentinel logic added in Task 9)
    exit 0
  fi

  # All other dispatches in manifest mode: treat as implementer
  IS_IMPLEMENTER=true
  TASK_NUMBER=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  if [ -z "$TASK_NUMBER" ]; then
    TASK_NUMBER=$(echo "$PROMPT" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  fi

  # Validate task number is in manifest range
  if [ -n "$TASK_NUMBER" ]; then
    if [ "$TASK_NUMBER" -lt "$MANIFEST_TASK_START" ] || [ "$TASK_NUMBER" -gt "$MANIFEST_TASK_END" ] 2>/dev/null; then
      echo "BLOCKED: Task $TASK_NUMBER is outside the manifest's task_range [$MANIFEST_TASK_START, $MANIFEST_TASK_END]. Check the active module in .sdd-session.json." >&2
      exit 2
    fi
  fi
fi
```

- [x] **Step 2: Wrap existing regex detection in else branch**

Wrap lines 94-141 (existing regex detection) in:

```bash
if [ "$MANIFEST_MODE" = false ]; then
  # ─── Legacy regex-based dispatch detection ─────────────────────────────
  # (existing code unchanged)
  ...
fi
```

- [x] **Step 3: Run existing tests** (16/16 PASS)

```bash
.venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v -x
```

Expected: All existing tests PASS

- [x] **Step 4: Commit** (`0888cdc`)

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "refactor: add manifest-mode dispatch detection to pre-dispatch hook"
```

---

### Task 8: Hook Conditional Checks by Tier ✅ (commit 87664e5)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (checks 1-6b)

- [x] **Step 1: Gate each check with manifest enforcement flags** (5 NEED_* vars added at outer scope — see deviations.md row 8)

For each existing check in the ERRORS accumulation section, add a manifest-mode conditional. The pattern for each check:

```bash
# Check 2: Pre-execution audit
if [ "$MANIFEST_MODE" = true ]; then
  NEED_AUDIT=$(jq -r '.enforcement.pre_execution_audit' "$MANIFEST")
  if [ "$NEED_AUDIT" = "false" ]; then
    : # Skip — tier doesn't require pre-execution audit
  else
    # (existing audit check code)
  fi
else
  # (existing audit check code — unchanged)
fi
```

Apply this pattern to:
- **Check 2** (pre-execution audit): gate on `enforcement.pre_execution_audit`
- **Check 4** (N-1 reports): always runs, but task at `task_range[0]` has no N-1 requirement
- **Check 4c** (dispatch provenance): gate on `enforcement.dispatch_provenance`
- **Check 5** (Task 0 / source contracts): always runs when plan has `source_contracts` (check plan file, not enforcement flag)
- **Check 5c** (checkpoint file): gate on `enforcement.checkpoint_files`
- **Check 5d** (partner review): gate on `enforcement.partner_review`
- **Check 6** (token estimation): use `MANIFEST_MODULE_FILE` or `MANIFEST_PLAN_FILE` instead of glob
- **Check 6b** (context summary): use manifest's `enforcement.context_summary_at` instead of computing midpoint

- [x] **Step 2: Update plan file resolution for token estimation** (Check 6 manifest mode uses MANIFEST_MODULE_FILE/MANIFEST_PLAN_FILE — see deviations row 9)

Replace the glob-based plan file search (lines 468-482) in manifest mode:

```bash
if [ "$MANIFEST_MODE" = true ]; then
  PLAN_FILE=""
  if [ -n "$MANIFEST_MODULE_FILE" ] && [ -f "$MANIFEST_MODULE_FILE" ]; then
    PLAN_FILE="$MANIFEST_MODULE_FILE"
  elif [ -f "$MANIFEST_PLAN_FILE" ]; then
    PLAN_FILE="$MANIFEST_PLAN_FILE"
  fi
  # (rest of token estimation with PLAN_FILE)
fi
```

- [x] **Step 3: Update midpoint check for context summary**

Replace the midpoint computation (lines 514-551) in manifest mode:

```bash
if [ "$MANIFEST_MODE" = true ]; then
  CONTEXT_SUMMARY_AT=$(jq -r '.enforcement.context_summary_at // empty' "$MANIFEST")
  if [ -n "$CONTEXT_SUMMARY_AT" ] && [ "$TASK_NUMBER" -ge "$CONTEXT_SUMMARY_AT" ]; then
    if [ ! -f "${REPORTS_DIR}/context-summary.md" ]; then
      ERRORS+=("BLOCKED: Context summary required. Task $TASK_NUMBER >= context_summary_at ($CONTEXT_SUMMARY_AT) from manifest. Run context-summary.py.")
    fi
  fi
fi
```

- [x] **Step 4: Run existing tests** (16/16 PASS)

```bash
.venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v -x
```

Expected: All existing tests PASS (they don't use manifests, so they hit legacy path)

- [x] **Step 5: Commit** (`87664e5`)

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "refactor: conditionalize hook checks by manifest enforcement flags"
```

---

### Task 9: Hook Process Requirements Injection and Dispatch Log Sentinel ✅ (commit c8e8d7e)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (output section)

- [x] **Step 1: Add process requirements injection to additionalContext** (12 new outer-scope vars — see deviations row 11)

In the manifest-mode success path (after all checks pass), build the additionalContext string from manifest:

```bash
if [ "$MANIFEST_MODE" = true ]; then
  # Read process requirements from manifest for injection
  PR_DISPATCH=$(jq -r '.process_requirements.subagent_dispatch' "$MANIFEST")
  PR_SPEC=$(jq -r '.process_requirements.spec_review_mode' "$MANIFEST")
  PR_QUALITY=$(jq -r '.process_requirements.quality_review_mode' "$MANIFEST")
  PR_PARTNER=$(jq -r '.process_requirements.partner_review_mode' "$MANIFEST")
  PR_DEVLOG=$(jq -r '.process_requirements.deviations_log' "$MANIFEST")
  PR_CHECKPOINT=$(jq -r '.process_requirements.checkpoint_script' "$MANIFEST")

  PROCESS_CONTRACT="SDD SESSION CONTRACT (from .sdd-session.json): Tier: $MANIFEST_TIER | Subagent dispatch: $PR_DISPATCH | Spec review: $PR_SPEC | Quality review: $PR_QUALITY | Partner review: $PR_PARTNER | Deviations log: $PR_DEVLOG | Checkpoint script: $PR_CHECKPOINT"

  CONTEXT="$CONTEXT | $PROCESS_CONTRACT"
fi
```

- [x] **Step 2: Add dispatch log sentinel logic** (sentinel write replaces line 175 placeholder; WARN-only verify at enforcement entry. Task 11 should test the edge case where REVIEW_TASK is unparseable.)

In the reviewer branch (Task 7's reviewer handling), after logging the dispatch:

```bash
# Dispatch log sentinel — write on first reviewer dispatch
if [ -f "$DISPATCH_LOG" ]; then
  SENTINEL_LINE=$(head -1 "$DISPATCH_LOG" 2>/dev/null)
  if ! echo "$SENTINEL_LINE" | grep -q "^# sdd-hook-sentinel "; then
    # First dispatch — write sentinel
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null)
    SENTINEL_HASH=$(echo -n "${SESSION_ID}-$(date -u +%Y%m%d%H%M%S)" | shasum -a 256 | cut -d' ' -f1)
    SENTINEL="# sdd-hook-sentinel $SENTINEL_HASH"
    # Prepend sentinel to dispatch log
    TEMP_LOG=$(mktemp)
    echo "$SENTINEL" > "$TEMP_LOG"
    cat "$DISPATCH_LOG" >> "$TEMP_LOG"
    mv "$TEMP_LOG" "$DISPATCH_LOG"
  fi
fi
```

In the implementer check path, add sentinel verification (WARN only):

```bash
# Check dispatch log sentinel integrity
if [ "$MANIFEST_MODE" = true ] && [ -f "$DISPATCH_LOG" ]; then
  SENTINEL_LINE=$(head -1 "$DISPATCH_LOG" 2>/dev/null)
  if ! echo "$SENTINEL_LINE" | grep -q "^# sdd-hook-sentinel "; then
    echo "WARNING: Dispatch log exists but has no hook-written sentinel. The log may have been manually created." >&2
  fi
fi
```

- [x] **Step 3: Commit** (`c8e8d7e`)

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "feat: add process requirements injection and dispatch log sentinel"
```

---

### Task 10: Hook Legacy Fallback ✅ (commit 1ee6a01)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`

- [x] **Step 1: Verify the legacy code path is intact** (4 structural claims confirmed)

Ensure all existing code paths are inside `if [ "$MANIFEST_MODE" = false ]` blocks or duplicated in both branches. Walk through the script:

1. Path resolution: legacy block inside `if [ "$MANIFEST_MODE" = false ]` — ✓ (Task 6)
2. Dispatch detection: legacy block inside `if [ "$MANIFEST_MODE" = false ]` — ✓ (Task 7)
3. Checks 1-6b: each check has manifest + legacy branches — ✓ (Task 8)
4. Output section: legacy output unchanged — ✓

- [x] **Step 2: Run the full existing test suite** (35/35 PASS across 4 test files)

```bash
.venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py tests/unit/test_sdd_dispatch_log.py tests/unit/test_sdd_midpoint_check.py tests/unit/test_sdd_partner_gate.py -v
```

Expected: All existing tests PASS

- [x] **Step 3: Manual smoke test** (manifest-mode workspace; both passthrough and blocked-implementer paths confirmed)

Create a minimal manifest-mode workspace and pipe a test dispatch:

```bash
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/reports"
echo "feat-dir" > "$TMPDIR/.active-feature"
# (Run hook with mock input to verify it reads manifest)
```

- [x] **Step 4: Commit** (`1ee6a01`)

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "refactor: verify legacy fallback intact in pre-dispatch hook"
```

---

### Task 11: Hook Rewrite Tests ✅ (commit d21df59)

**Files:**
- Modify: `tests/unit/test_sdd_hard_gates.py` — add manifest-mode test class
- Modify: `tests/unit/sdd_test_helpers.py` — add manifest workspace helper

**Pattern References:**
- `tests/unit/sdd_test_helpers.py` — `setup_full_sdd_workspace` pattern

- [x] **Step 1: Add manifest workspace helper to sdd_test_helpers.py** (Module 1 midpoint formula — see deviations row 12)

```python
def setup_manifest_workspace(
    tmp_path, tier="standard", task_range=(0, 7), total_tasks=8
):
    """Set up a workspace with .sdd-session.json for manifest-mode testing.

    Initializes a git repo so git rev-parse --show-toplevel works (required by hook).
    """
    import json
    import subprocess
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "skills" / "scripts" / "models"))
    from sdd_session import TIER_PROFILES

    # Initialize git repo — hook requires git rev-parse --show-toplevel
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "checkout", "-b", "test-feature"], cwd=str(tmp_path), capture_output=True)

    feat_dir = tmp_path / "docs" / "imp-plans" / "test-feature"
    feat_dir.mkdir(parents=True)
    reports_dir = feat_dir / "reports"
    reports_dir.mkdir()

    # .active-feature
    (tmp_path / ".active-feature").write_text(str(feat_dir.relative_to(tmp_path)))

    # .sdd-session.json
    start, end = task_range
    range_size = end - start + 1
    midpoint = start + (range_size + 1) // 2

    profile = TIER_PROFILES[tier]
    enforcement = dict(profile["enforcement"])
    if enforcement["context_summary_at"] is None and tier == "standard":
        enforcement["context_summary_at"] = midpoint

    manifest = {
        "schema_version": 1,
        "tier": tier,
        "paths": {
            "feature_dir": str(feat_dir.relative_to(tmp_path)),
            "reports_dir": str(reports_dir.relative_to(tmp_path)),
            "dispatch_log": str((reports_dir / ".dispatch-log").relative_to(tmp_path)),
            "deviations_file": str((feat_dir / "deviations.md").relative_to(tmp_path)),
        },
        "plan_file": str((feat_dir / "plan.md").relative_to(tmp_path)),
        "active_module_id": None,
        "active_module_file": None,
        "task_range": list(task_range),
        "total_tasks": total_tasks,
        "midpoint": midpoint,
        "enforcement": enforcement,
        "process_requirements": profile["process_requirements"],
        "completed_modules": [],
        "module_reports_archived": False,
        "modules": None,
        "dispatch_log_sentinel": False,
    }

    (feat_dir / ".sdd-session.json").write_text(json.dumps(manifest, indent=2))
    (feat_dir / "deviations.md").write_text("# Deviations\n")
    (feat_dir / "plan.md").write_text("# Plan\n### Task 0: Setup\n- [ ] Do thing\n")

    return {
        "root": tmp_path,
        "feat_dir": feat_dir,
        "reports_dir": reports_dir,
        "manifest_path": feat_dir / ".sdd-session.json",
    }
```

- [x] **Step 2: Add manifest-mode test class to test_sdd_hard_gates.py** (6 tests: 5 required + 1 optional sentinel-edge)

```python
class TestManifestModeDispatchDetection:
    """Tests for manifest-mode dispatch detection."""

    def test_micro_tier_skips_partner_review_check(self, tmp_path):
        ws = setup_manifest_workspace(tmp_path, tier="micro", task_range=(0, 1), total_tasks=2)
        # Create required reports for task 0
        create_reports_for_task(ws["reports_dir"], 0, include_partner=False)
        hook_input = make_hook_input("Implement task 1", cwd=str(tmp_path))
        result = run_hook(SDD_PRE_DISPATCH_HOOK_PATH, hook_input)
        # Micro tier should NOT block on missing partner review
        assert result.returncode == 0

    def test_standard_tier_blocks_without_partner_review(self, tmp_path):
        ws = setup_manifest_workspace(tmp_path, tier="standard")
        create_reports_for_task(ws["reports_dir"], 0, include_partner=False)
        hook_input = make_hook_input("Implement task 1", cwd=str(tmp_path))
        result = run_hook(SDD_PRE_DISPATCH_HOOK_PATH, hook_input)
        assert result.returncode == 2
        assert "partner" in result.stderr.lower()

    def test_task_outside_range_blocked(self, tmp_path):
        ws = setup_manifest_workspace(tmp_path, task_range=(0, 3))
        hook_input = make_hook_input("Implement task 99", cwd=str(tmp_path))
        result = run_hook(SDD_PRE_DISPATCH_HOOK_PATH, hook_input)
        assert result.returncode == 2
        assert "task_range" in result.stderr.lower()

    def test_explore_agent_passes_through(self, tmp_path):
        ws = setup_manifest_workspace(tmp_path)
        hook_input = json.dumps({
            "tool_input": {
                "description": "Search for files",
                "prompt": "",
                "subagent_type": "Explore",
            },
            "cwd": str(tmp_path),
        })
        result = run_hook(SDD_PRE_DISPATCH_HOOK_PATH, hook_input)
        assert result.returncode == 0

    def test_process_requirements_injected(self, tmp_path):
        ws = setup_manifest_workspace(tmp_path, tier="standard")
        # Satisfy all prerequisites for task 1
        create_full_task_prerequisites(ws, 0)
        hook_input = make_hook_input("Implement task 1", cwd=str(tmp_path))
        result = run_hook(SDD_PRE_DISPATCH_HOOK_PATH, hook_input)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "SESSION CONTRACT" in output.get("hookSpecificOutput", {}).get("additionalContext", "")
```

- [x] **Step 3: Run all tests** (22/22 PASS in test_sdd_hard_gates.py; 41/41 across the 4-file hook test suite)

```bash
.venv/bin/python3 -m pytest tests/unit/test_sdd_hard_gates.py -v
```

Expected: All tests PASS (existing + new)

- [x] **Step 4: Commit** (`d21df59`)

```bash
git add tests/unit/sdd_test_helpers.py tests/unit/test_sdd_hard_gates.py
git commit -m "test: add manifest-mode hook tests and workspace helpers"
```
