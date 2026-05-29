---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
shared_constants:
  - path: "skills/scripts/models/sdd_session.py::TIER_PROFILES"
    value: "tier->enforcement/process_requirements profiles"
    reason: "Helper migration must build manifests from TIER_PROFILES, not hand-rolled dicts"
pattern_references:
  - name: "manifest-workspace-helper"
    source_files: ["tests/unit/sdd_test_helpers.py"]
    reason: "setup_manifest_workspace (lines 313-431) is the canonical .sdd-session.json layout"
tasks:
  - id: 5
    title: "Migrate SDD test helpers to manifest mode"
  - id: 6
    title: "Restructure hook classification + auto-create log + remove legacy path"
    depends_on: [5]
  - id: 7
    title: "Remove dead legacy branches (Item 5 cleanup)"
    depends_on: [6]
  - id: 8
    title: "Surface validation errors inline"
    depends_on: [7]
  - id: 9
    title: "Verification and documentation"
    depends_on: [6, 7, 8]
---

# Module 2 — Hook classification and legacy removal

> **For agentic workers:** Invoke `superpowers:subagent-driven-development` before implementing. Part of the SDD Hook Improvements feature; see `plan.md`.

**Goal:** Restructure `sdd-pre-dispatch-hook.sh` into a 3-stage classification pipeline so `general-purpose` reviewers/implementers are correctly handled (Item 1), auto-create the dispatch log on the first reviewer dispatch (Item 3), surface validation errors inline (Item 2), and remove the legacy non-manifest path and all dead legacy branches (Item 5). The test-helper migration (Task 5) is the prerequisite that lets every existing hook test run in manifest mode so legacy removal does not silently invert them.

**Source Contracts:** None

Internal hook/test changes only.

**Contract Constraints:**
- Classification order is exactly **reviewer → implementer → passthrough**.
- Reviewers logged **before** any passthrough (the unfixed bug: `general-purpose` at line 169 exits before reviewer detection at line 174).
- Dispatch-log auto-create: `mkdir -p "$(dirname "$DISPATCH_LOG")"` + `touch "$DISPATCH_LOG"` (idempotent).
- Validation-error excerpt: `head -n 12` (line-based). **Corrects the spec's `head -n 5`:** `validate-report.py` emits a 4-line banner + blank first; the first field name is at line 6, so `head -n 5` would show only the banner. `head -n 12` surfaces the first two failing fields. (Verified empirically against the real script.)
- Legacy non-manifest path removed entirely; replaced by a guard clause: no manifest + SDD artifacts → BLOCK (exit 2); no manifest + no artifacts → ALLOW (exit 0).
- Dead `else`/legacy branches in Checks 5/6/6b/7 and the now-unreachable `IS_IMPLEMENTER=false` guard must be removed (architectural principle: "dead code must be removed").
- Do not weaken any enforcement check that runs in manifest mode.

**Feature Archetype:** Extension (with one removal — the legacy path — handled inside the hook restructure).

## Code Footprint

| Category | File | Action |
|----------|------|--------|
| Modified | `tests/unit/sdd_test_helpers.py` | Add `_write_manifest`; migrate `setup_sdd_workspace`/`setup_full_sdd_workspace` to manifest mode |
| Modified | `tests/unit/test_sdd_dispatch_log.py` | Rewrite bare-`reports/` reviewer tests to manifest setup |
| Modified | `tests/unit/test_sdd_partner_gate.py` | Runs in manifest mode via migrated helper (verify green) |
| Modified | `tests/unit/test_sdd_midpoint_check.py` | Remove legacy plan-globbing tests; adapt the zero-header test to manifest mode |
| Modified | `tests/unit/test_sdd_hard_gates.py` | Migrate `feature_dir_workspace` fixture to manifest mode; delete `TestBackwardsCompatFallback` |
| New | `tests/unit/test_sdd_classification.py` | Item 1/3/5 classification + guard-clause tests |
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | 3-stage pipeline, auto-create log, inline errors, legacy + dead-branch removal |
| Modified | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md` | Test counts + behavior notes |
| Obsolete | hook legacy resolution (123-153), legacy dispatch detection (226-273), `IS_IMPLEMENTER=false` guard (276-278), dead `else` branches in Checks 5/6/6b/7, `feat_path()` helper, `subagent_type` passthrough (168-171) | Remove (Task 6) |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| 5 | `tests/unit/sdd_test_helpers.py`, `tests/unit/test_sdd_dispatch_log.py`, `tests/unit/test_sdd_partner_gate.py`, `tests/unit/test_sdd_midpoint_check.py`, `tests/unit/test_sdd_hard_gates.py` | hook (unchanged), `sdd_session.py` | — |
| 6 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`, `tests/unit/test_sdd_classification.py` (new) | migrated test files | 5 |
| 7 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | — | 6 |
| 8 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`, `tests/unit/test_sdd_classification.py` | — | 7 |
| 9 | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md` | all | 6, 7, 8 |

> **Tasks 6, 7, 8 all edit the hook file but are strictly serial (6→7→8).** Serial ownership keeps them conflict-free. Task 5 owns all four *existing* hook-test files and converges them to manifest mode; the net-new classification tests live in `test_sdd_classification.py` (created by Task 6, appended by Task 8) to avoid re-touching Task 5's files. If Task 6's restructure regresses a manifest-mode classification test inside `test_sdd_hard_gates.py` (e.g. `test_explore_agent_passes_through`), Task 6 may make the minimal fix there — safe because the tasks are serial.

---

### Task 5: Migrate SDD test helpers to manifest mode

**Files:**
- Modify: `tests/unit/sdd_test_helpers.py` (add `_write_manifest`; call it from `setup_sdd_workspace`)
- Modify: `tests/unit/test_sdd_dispatch_log.py` (`TestReviewerDispatchLogging`)
- Modify: `tests/unit/test_sdd_midpoint_check.py` (remove legacy tests)
- Modify: `tests/unit/test_sdd_hard_gates.py` (`feature_dir_workspace` fixture; delete `TestBackwardsCompatFallback`)
- Read-only: `tests/unit/test_sdd_partner_gate.py` (should pass unchanged once the helper is migrated; verify)

**Pattern References:** `tests/unit/sdd_test_helpers.py` `setup_manifest_workspace` (313-431) — mirror its manifest dict and TIER_PROFILES usage.

**Why this task exists / acceptance gate:** After Item 5 (Task 6) removes the legacy path, any test whose workspace lacks a `.sdd-session.json` will hit the new guard clause and exit 0 *without enforcing* — silently inverting block tests. This task makes every hook-test workspace manifest-mode FIRST, while the hook is **unchanged**, so the legacy removal in Task 6 changes no test outcomes. **Acceptance: `tests/unit/` is fully green against the unchanged hook after this task.**

Verified design fact: a root-level `feature_dir="."` (manifest at git root, `reports_dir="reports"`) activates manifest mode and keeps `reports/` at `tmpdir/reports`, so existing hardcoded paths like `os.path.join(tmpdir, "reports", ".dispatch-log")` resolve unchanged.

- [x] **Step 1: Add the shared `_write_manifest` helper**

Add to `tests/unit/sdd_test_helpers.py` (it already imports `json`, `os`, `subprocess`):

```python
def _write_manifest(root, feature_dir, reports_rel, deviations_rel, plan_rel,
                    task_count, tier="standard"):
    """Write .active-feature + .sdd-session.json for manifest-mode hook testing.

    Args:
        root: workspace root (str) — the git root / hook CWD.
        feature_dir: feature dir relative to root ('.' or 'docs/imp-plans/x').
        reports_rel, deviations_rel, plan_rel: git-root-relative paths.
        task_count: number of tasks (task_range = [0, task_count-1]).
        tier: 'standard' or 'micro'.
    The manifest is written at <root>/<feature_dir>/.sdd-session.json.
    """
    import sys as _sys
    from pathlib import Path as _Path
    _models = str(_Path(__file__).resolve().parent.parent.parent
                  / "skills" / "scripts" / "models")
    if _models not in _sys.path:
        _sys.path.insert(0, _models)
    from sdd_session import TIER_PROFILES  # noqa: PLC0415

    start, end = 0, max(task_count - 1, 0)
    range_size = end - start
    midpoint = start + (range_size + 1) // 2  # Module 1 deviation-row-1 formula

    profile = TIER_PROFILES[tier]
    enforcement = dict(profile["enforcement"])
    if tier == "standard" and enforcement.get("context_summary_at") is None:
        enforcement["context_summary_at"] = midpoint

    manifest = {
        "schema_version": 1,
        "tier": tier,
        "paths": {
            "feature_dir": feature_dir,
            "reports_dir": reports_rel,
            "dispatch_log": os.path.join(reports_rel, ".dispatch-log"),
            "deviations_file": deviations_rel,
        },
        "plan_file": plan_rel,
        "active_module_id": None,
        "active_module_file": None,
        "task_range": [start, end],
        "total_tasks": max(task_count, 1),
        "midpoint": midpoint,
        "enforcement": enforcement,
        "process_requirements": dict(profile["process_requirements"]),
        "completed_modules": [],
        "module_reports_archived": False,
        "modules": None,
        "dispatch_log_sentinel": False,
    }
    with open(os.path.join(root, ".active-feature"), "w") as f:
        f.write(feature_dir)
    manifest_dir = os.path.join(root, feature_dir) if feature_dir != "." else root
    os.makedirs(manifest_dir, exist_ok=True)
    with open(os.path.join(manifest_dir, ".sdd-session.json"), "w") as f:
        json.dump(manifest, f, indent=2)
```

- [x] **Step 2: Call it from `setup_sdd_workspace`**

In `setup_sdd_workspace`, insert the manifest write **immediately before the `git init` block** (after the plan/DEVIATIONS/audit files are written). Root layout → `feature_dir="."`:

```python
    # Manifest-mode activation (root-level feature dir keeps reports/ at root)
    _write_manifest(
        tmpdir,
        feature_dir=".",
        reports_rel="reports",
        deviations_rel="DEVIATIONS.md",
        plan_rel=os.path.join("docs", "imp-plans", "plan.md"),
        task_count=task_count,
    )
```

`setup_full_sdd_workspace` calls `setup_sdd_workspace`, so it inherits the manifest automatically — no separate change.

- [x] **Step 3: Verify the migrated helpers against the UNCHANGED hook**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_partner_gate.py tests/unit/test_sdd_hard_gates.py::TestTokenEstimationBlocking tests/unit/test_sdd_hard_gates.py::TestContextSummaryBlocking tests/unit/test_sdd_hard_gates.py::TestCheckpointFileGate -v`
Expected: PASS — these now run in manifest mode (manifest present) against the unchanged hook. Fix any path/expectation drift (the manifest's `context_summary_at` is the midpoint, matching the legacy midpoint these tests assumed).

- [x] **Step 4: Rewrite the bare-`reports/` reviewer tests in `test_sdd_dispatch_log.py`**

`TestReviewerDispatchLogging::test_reviewer_dispatch_creates_log_entry` and `test_quality_reviewer_dispatch_logged` create only `os.makedirs(reports_dir)` — no manifest. Rewrite them to set up a manifest workspace first (they do NOT set `subagent_type`, so the unchanged hook's reviewer detection still fires):

```python
    def test_reviewer_dispatch_creates_log_entry(self, tmp_path):
        tmpdir = str(tmp_path)
        setup_sdd_workspace(tmpdir, task_count=5)
        log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
        if os.path.exists(log_path):
            os.remove(log_path)  # prove the dispatch creates it
        hook_input = make_hook_input(description="Review task 3 spec compliance", cwd=tmpdir)
        result = run_hook(HOOK_PATH, hook_input)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert os.path.isfile(log_path), "Hook should create .dispatch-log"
        log = open(log_path).read()
        assert "task=3" in log and "type=spec-review" in log
```

Apply the same pattern to `test_quality_reviewer_dispatch_logged` (description "Dispatch code quality review for task 5", assert `task=5`/`type=quality-review`). `test_non_reviewer_dispatch_does_not_add_log_entry` already uses `setup_sdd_workspace` — leave it (verify green).

- [x] **Step 5: Migrate the `feature_dir_workspace` fixture to manifest mode**

In `test_sdd_hard_gates.py`, the `feature_dir_workspace` fixture and `_setup_feature_dir_sdd_workspace` build a feature-dir layout with `.active-feature` but **no manifest**. Add a manifest so these run in manifest mode (passing against both the unchanged hook and the post-Task-6 hook). Add to the END of `_setup_feature_dir_sdd_workspace` (it has `total_tasks` and `feat_path` in scope), importing the helper:

```python
    from sdd_test_helpers import _write_manifest  # noqa: PLC0415
    _write_manifest(
        str(tmp_path),
        feature_dir=feat_path,
        reports_rel=os.path.join(feat_path, "reports"),
        deviations_rel=os.path.join(feat_path, "deviations.md"),
        plan_rel=os.path.join(feat_path, "plan.md"),
        task_count=total_tasks,
    )
```

If any `TestFeatureDirLayout` test uses the bare `feature_dir_workspace` fixture WITHOUT calling `_setup_feature_dir_sdd_workspace`, add the same `_write_manifest(...)` call to the fixture itself (task_count=2, matching its 2-task plan). Verify which tests need it by running them.

- [x] **Step 6: Rework `test_sdd_midpoint_check.py` (legacy plan-globbing tests)**

This file tests the hook's **legacy** plan-globbing midpoint logic (hook lines 737-775), which Item 5 deletes. In manifest mode the midpoint comes from `enforcement.context_summary_at`. Therefore:
- **Delete** `test_stale_plan_does_not_inflate_total_tasks` and `test_allows_before_midpoint_with_stale_plans_present` — their premise (stale plan files inflating the task count) does not exist in manifest mode; midpoint blocking is already covered by `test_sdd_hard_gates.py::TestContextSummaryBlocking`.
- **Adapt** `test_tolerates_plan_file_with_zero_task_headers` to manifest mode: it should still assert the hook does not crash with a bash math error. With the migrated `setup_full_sdd_workspace`, this runs in manifest mode automatically; keep the "no bash math error / no syntax error" assertions, drop any assertion that depends on legacy plan-count globbing.
- Add a module docstring note: "Legacy plan-globbing midpoint tests removed with Item 5 (legacy path removal); manifest-mode midpoint is covered by TestContextSummaryBlocking."

- [x] **Step 7: Delete `TestBackwardsCompatFallback`**

In `test_sdd_hard_gates.py`, delete the entire `TestBackwardsCompatFallback` class — it tests the legacy root-fallback that Item 5 removes. The new "no manifest" guard-clause behavior is covered by `test_sdd_classification.py` in Task 6.

- [x] **Step 8: Full suite green against the UNCHANGED hook**

Run: `.venv/bin/python3 -m pytest tests/unit/ -v`
Expected: PASS (0 failures). This is the task's acceptance gate. Do not proceed to Task 6 until the full unit suite is green with the hook unmodified.

- [x] **Step 9: Commit**

```bash
git add tests/unit/sdd_test_helpers.py tests/unit/test_sdd_dispatch_log.py tests/unit/test_sdd_midpoint_check.py tests/unit/test_sdd_hard_gates.py
git commit -m "test(sdd): migrate hook test helpers to manifest mode (pre-legacy-removal)"
```

---

### Task 6: Restructure hook classification + auto-create log + remove legacy path

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
- Create: `tests/unit/test_sdd_classification.py`

**Context:** Items 1, 3, and 5 are one cohesive rewrite of the dispatch-classification region. After the rewrite, `MANIFEST_MODE` is always `true` past the guard clause, so the legacy `else` branches in the enforcement checks become dead and must be removed in the same task.

- [x] **Step 1: Write the failing classification tests**

Create `tests/unit/test_sdd_classification.py`:

```python
"""Item 1/3/5: 3-stage manifest-mode classification + non-manifest guard.
Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v
"""
import os
import subprocess

from sdd_test_helpers import create_checkpoint_file, make_hook_input, setup_sdd_workspace

HOOK_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh",
))


def run_hook(stdin_data):
    return subprocess.run(["bash", HOOK_PATH], input=stdin_data,
                          capture_output=True, text=True, timeout=10)


def test_general_purpose_reviewer_is_logged(tmp_path):
    # Item 1 bug: a general-purpose reviewer must be logged, not passed through.
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=5)
    log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
    if os.path.exists(log_path):
        os.remove(log_path)
    result = run_hook(make_hook_input(
        description="Review task 2 spec compliance",
        subagent_type="general-purpose", cwd=tmpdir))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert os.path.isfile(log_path) and "task=2" in open(log_path).read()


def test_general_purpose_implementer_is_enforced(tmp_path):
    # Task 0 reports missing -> implementer for task 1 must be blocked.
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=3)
    result = run_hook(make_hook_input(
        description="Implement task 1", prompt="You are implementing task 1",
        subagent_type="general-purpose", cwd=tmpdir))
    assert result.returncode == 2, f"stderr: {result.stderr}"


def test_adhoc_dispatch_passes_through(tmp_path):
    # Non-reviewer, non-implementer -> Stage 3 allow, no log entry.
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=3)
    log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
    before = open(log_path).read() if os.path.exists(log_path) else ""
    result = run_hook(make_hook_input(
        description="Investigate the database schema",
        prompt="Look at the schema", subagent_type="general-purpose", cwd=tmpdir))
    after = open(log_path).read() if os.path.exists(log_path) else ""
    assert result.returncode == 0 and after == before, f"stderr: {result.stderr}"


def test_no_manifest_no_artifacts_allowed(tmp_path):
    tmpdir = str(tmp_path)
    subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
    result = run_hook(make_hook_input(
        description="Implement task 1", prompt="You are implementing task 1", cwd=tmpdir))
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_no_manifest_with_artifacts_blocked(tmp_path):
    tmpdir = str(tmp_path)
    subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
    os.makedirs(os.path.join(tmpdir, "docs", "imp-plans", "x", "reports"))
    with open(os.path.join(tmpdir, ".active-feature"), "w") as f:
        f.write("docs/imp-plans/x")
    result = run_hook(make_hook_input(
        description="Implement task 1", prompt="You are implementing task 1", cwd=tmpdir))
    assert result.returncode == 2 and "manifest" in result.stderr.lower(), f"stderr: {result.stderr}"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v`
Expected: FAIL — `test_general_purpose_reviewer_is_logged` fails (current line 169 passes `general-purpose` through without logging); the `test_no_manifest_*` guard tests fail (no guard clause yet).

- [x] **Step 3: Replace the dispatch-classification region (Items 1, 3, 5)**

In `sdd-pre-dispatch-hook.sh`, replace **everything from the start of the legacy resolution block through the `IS_IMPLEMENTER=false` guard** — i.e. the current lines 123-278 (the `if [ "$MANIFEST_MODE" = false ]` legacy-resolution block, the `if [ "$MANIFEST_MODE" = true ]` classification block, the second `if [ "$MANIFEST_MODE" = false ]` legacy-dispatch block, and the trailing `if [ "$IS_IMPLEMENTER" = false ]; then exit 0; fi`) — with this:

```bash
# ─── Require manifest mode (legacy non-manifest path removed) ───────────────
# No manifest + SDD artifacts present → upstream failure, block with guidance.
# No manifest + no artifacts → not an SDD session, allow.
if [ "$MANIFEST_MODE" = false ]; then
  if [ -f ".active-feature" ]; then
    FEAT_CHECK=$(cat .active-feature | tr -d '\n' | sed 's|/$||')
    if [ -d "$FEAT_CHECK/reports" ] || [ -f "$FEAT_CHECK/deviations.md" ]; then
      echo "BLOCKED: SDD artifacts found in $FEAT_CHECK/ but no .sdd-session.json manifest. Run Plan Ingestion (materialize-manifest.py) to create the session manifest before dispatching tasks." >&2
      exit 2
    fi
  fi
  exit 0
fi

# ─── Manifest-mode dispatch classification (3-stage pipeline) ───────────────
# Order is load-bearing: reviewers are logged BEFORE any passthrough so that
# general-purpose reviewers (the post-2026-05-07 default) are recorded.
IS_REVIEWER=false
IS_IMPLEMENTER=false
REVIEW_TASK=""
REVIEW_TYPE="unknown"
TASK_NUMBER=""

# Stage 1: Reviewer detection (by description).
if echo "$DESCRIPTION" | grep -qiE '(review|spec.compliance|code.quality|spec.review|quality.review|trace.audit|partner.review)'; then
  IS_REVIEWER=true
fi

if [ "$IS_REVIEWER" = true ]; then
  # Item 3: ensure dispatch log dir + file exist (idempotent) before logging.
  mkdir -p "$(dirname "$DISPATCH_LOG")"
  touch "$DISPATCH_LOG"
  REVIEW_TASK=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  if echo "$DESCRIPTION" | grep -qiE '(spec.compliance|spec.review)'; then REVIEW_TYPE="spec-review"
  elif echo "$DESCRIPTION" | grep -qiE '(code.quality|quality.review)'; then REVIEW_TYPE="quality-review"
  elif echo "$DESCRIPTION" | grep -qiE 'trace.audit'; then REVIEW_TYPE="trace-audit"
  elif echo "$DESCRIPTION" | grep -qiE '(partner.review|controller.partner)'; then REVIEW_TYPE="partner-review"
  fi
  if [ -n "$REVIEW_TASK" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH reviewer task=$REVIEW_TASK type=$REVIEW_TYPE" >> "$DISPATCH_LOG"
  fi
  # Sentinel — write on first reviewer dispatch.
  SENTINEL_LINE=$(head -1 "$DISPATCH_LOG" 2>/dev/null)
  if ! echo "$SENTINEL_LINE" | grep -q "^# sdd-hook-sentinel "; then
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null)
    SENTINEL_HASH=$(echo -n "${SESSION_ID}-$(date -u +%Y%m%d%H%M%S)" | shasum -a 256 | cut -d' ' -f1)
    SENTINEL="# sdd-hook-sentinel $SENTINEL_HASH"
    TEMP_LOG=$(mktemp)
    echo "$SENTINEL" > "$TEMP_LOG"
    cat "$DISPATCH_LOG" >> "$TEMP_LOG"
    mv "$TEMP_LOG" "$DISPATCH_LOG"
  fi
  exit 0
fi

# Stage 2: Implementer detection (by description or prompt).
if echo "$DESCRIPTION" | grep -qiE '(implement|dispatch).*task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$DESCRIPTION" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
elif echo "$PROMPT" | grep -qiE 'you are implementing task\s*[0-9]'; then
  TASK_NUMBER=$(echo "$PROMPT" | grep -oiE 'task\s*[0-9]+' | grep -oE '[0-9]+' | head -1)
  IS_IMPLEMENTER=true
fi

# Stage 3: Not a reviewer, not an implementer → allow (Explore, Plan, ad-hoc).
if [ "$IS_IMPLEMENTER" = false ]; then
  exit 0
fi

# Validate task number is within the manifest's task range.
if [ -n "$TASK_NUMBER" ]; then
  if [ "$TASK_NUMBER" -lt "$MANIFEST_TASK_START" ] || [ "$TASK_NUMBER" -gt "$MANIFEST_TASK_END" ] 2>/dev/null; then
    echo "BLOCKED: Task $TASK_NUMBER is outside the manifest's task_range [$MANIFEST_TASK_START, $MANIFEST_TASK_END]. Check the active module in .sdd-session.json." >&2
    exit 2
  fi
fi
```

This deletes (per the Contract Constraints): the `subagent_type` passthrough (old 168-171), the unconditional `IS_IMPLEMENTER=true` (old 211), the legacy resolution + dispatch blocks, and the `IS_IMPLEMENTER=false` guard. Do not declare `SUBAGENT_TYPE` (now unused).

- [x] **Step 4: Run the classification tests and the full suite**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v` → PASS
Run: `.venv/bin/python3 -m pytest tests/unit/ -v` → PASS (0 failures). The legacy `else` branches in the enforcement checks are now unreachable (the guard clause guarantees `MANIFEST_MODE=true` past it) but still present — they are removed in Task 7. If `test_explore_agent_passes_through` or another manifest-mode classification test in `test_sdd_hard_gates.py` regressed, make the minimal fix there (serial-safe per the write-scope note).

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/unit/test_sdd_classification.py
git commit -m "feat(sdd-hook): 3-stage classification, auto-create dispatch log, require manifest"
```

---

### Task 7: Remove dead legacy branches (Item 5 cleanup)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`

**Context:** After Task 6's guard clause, `MANIFEST_MODE` is always `true` in the enforcement section, so the legacy `else` branches are unreachable dead code (architectural principle: dead code must be removed). This task references code *patterns*, not line numbers, since Task 6 shifted them.

- [x] **Step 1: Remove each dead legacy branch**

Work top-down through the enforcement checks; remove the dead branch and de-indent the kept manifest branch:

1. **Sentinel integrity check:** `if [ "$MANIFEST_MODE" = true ] && [ -f "$DISPATCH_LOG" ]; then` → `if [ -f "$DISPATCH_LOG" ]; then`.
2. **Check 2 (pre-execution audit):** collapse `if [ "$MANIFEST_MODE" = true ]; then NEED_AUDIT=$(jq ...); fi` + `if [ "$MANIFEST_MODE" = true ] && [ "$NEED_AUDIT" = "false" ]` into unconditional `NEED_AUDIT=$(jq -r '.enforcement.pre_execution_audit' "$MANIFEST")` then `if [ "$NEED_AUDIT" = "false" ]; then : ; else ... fi`.
3. **Check 5 (Source Contracts / Task 0):** delete the `else  # Legacy mode: glob ...` branch (the `PLAN_SEARCH_GLOB` loop). Keep only the manifest branch, de-indented; remove the `if [ "$MANIFEST_MODE" = true ]` wrapper.
4. **Check 5c (checkpoint) and Check 5d (partner):** collapse the `MANIFEST_MODE` gating to unconditional jq read + `if [ "$NEED_X" = "false" ]`.
5. **Check 6 (token estimation):** delete the `else  # Legacy mode: glob ...` branch. Keep the manifest branch. Update the "couldn't find task" diagnostic to reference the manifest plan file (drop `SEARCHED_DIRS`).
6. **Check 6b (context summary):** delete the entire legacy `else` branch (plan-globbing midpoint, ~40 lines). Keep the manifest `enforcement.context_summary_at` branch, de-indented.
7. **Check 7 (context load estimate):** replace the `if [ -n "$FEAT" ]; then PLAN_SEARCH_GLOB="$FEAT/*.md"; else ...; fi` plan-file sizing with:
   ```bash
   for pf in "$MANIFEST_PLAN_FILE" "$MANIFEST_MODULE_FILE"; do
     if [ -n "$pf" ] && [ -f "$pf" ]; then
       PF_SIZE=$(wc -c < "$pf" 2>/dev/null | tr -d ' ')
       TOTAL_BYTES=$((TOTAL_BYTES + PF_SIZE))
     fi
   done
   ```
8. **Remove dead helpers/vars:** `feat_path()` (already removed with the 123-153 block) and any now-unused variable. Keep `FEAT` only if still referenced.
9. **Update the stale top-of-file comment** (the "Legacy fallback verified intact" block, ~lines 16-19) — replace with a one-line note that the legacy non-manifest path was removed in this change.

- [x] **Step 2: Audit for residual legacy code**

Run: `grep -nE 'MANIFEST_MODE = false|Legacy mode|feat_path|PLAN_SEARCH_GLOB|SEARCHED_DIRS|subagent_type' skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
Expected: no functional matches.

- [x] **Step 3: Run the full suite**

Run: `.venv/bin/python3 -m pytest tests/unit/ -v` → PASS (0 failures).

- [x] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
git commit -m "refactor(sdd-hook): remove dead legacy branches after manifest-only restructure"
```

---

### Task 8: Surface validation errors inline (Item 2)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (Check 4b validation-error branch)
- Test: `tests/unit/test_sdd_dispatch_log.py` (or `test_sdd_classification.py`) — add one focused test

- [x] **Step 1: Write the failing test**

Add to `tests/unit/test_sdd_classification.py`:

```python
class TestValidationErrorSurfacing:
    def test_validation_error_excerpt_inline(self, tmp_path):
        """When the prev task's implementer report fails validation, the hook
        error must include excerpt lines from validate-report.py, not just the exit code."""
        tmpdir = str(tmp_path)
        setup_sdd_workspace(tmpdir, task_count=3)
        reports_dir = os.path.join(tmpdir, "reports")
        # Task 0 report present but with BROKEN frontmatter (fails Pydantic validation),
        # large enough to pass the size gate so validation actually runs.
        with open(os.path.join(reports_dir, "task-000-implementer-report.md"), "w") as f:
            f.write("---\nschema_version: 1\ntask_id: not_an_int\nstatus: BOGUS\n---\n\n"
                    + "Body padding to exceed the 50-byte size gate. " * 5)
        create_checkpoint_file(tmpdir, task_number=1)
        hook_input = make_hook_input(
            description="Implement task 1", prompt="You are implementing task 1", cwd=tmpdir,
        )
        result = run_hook(hook_input)
        assert result.returncode == 2, f"stderr: {result.stderr}"
        # The excerpt must surface the FAILING FIELD NAME, not just the banner.
        # (task_id: not_an_int is the first failing field, at output line 6 —
        # reachable only with head -n 12, not head -n 5.) Assert on task_id
        # specifically: "status" would spuriously match the trailing JSON line.
        low = result.stderr.lower()
        assert "validation" in low and "task_id" in low, \
            f"Expected an inline validation excerpt naming task_id. stderr: {result.stderr}"
```

- [x] **Step 2: Run to verify it fails**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py::TestValidationErrorSurfacing -v`
Expected: FAIL — current message reports only the exit code, no field excerpt.

- [x] **Step 3: Add the excerpt to the error message**

In Check 4b, the branch where `validate-report.py` exits non-zero currently reads:
```bash
        if [ "$VALIDATE_EXIT" -ne 0 ]; then
          ERRORS+=("BLOCKED: Implementer report for Task $PREV ($IMPL_LATEST) failed validation (exit $VALIDATE_EXIT). Re-dispatch the implementer to fix Pydantic frontmatter or complete all 5 required prose sections before proceeding.")
```
Change it to include the first 12 lines of `$VALIDATE_OUTPUT`. **`head -n 12`, not the spec's `head -n 5`:** `validate-report.py` prints a 4-line `═══` banner + blank line first, so the first failing field name (`[1] Field: task_id`) lands on line 6. `head -n 12` reaches the first two fields:
```bash
        if [ "$VALIDATE_EXIT" -ne 0 ]; then
          VALIDATE_EXCERPT=$(echo "$VALIDATE_OUTPUT" | head -n 12)
          ERRORS+=("BLOCKED: Implementer report for Task $PREV ($IMPL_LATEST) failed validation (exit $VALIDATE_EXIT):\n${VALIDATE_EXCERPT}\n\nRe-dispatch the implementer to fix Pydantic frontmatter or complete all 5 required prose sections before proceeding.")
```
Leave the INCOMPLETE branch (missing-sections) unchanged — it already surfaces section names.

- [x] **Step 4: Run the test and the full suite**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v` → PASS
Run: `.venv/bin/python3 -m pytest tests/unit/ -v` → PASS

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/unit/test_sdd_classification.py
git commit -m "feat(sdd-hook): surface validate-report.py error excerpt inline"
```

---

### Task 9: Verification and documentation

**Files:**
- Modify: `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`

**Context:** Final coordination task. Depends on Tasks 6, 7, 8 AND all of Module 1. No new behavior — runs every test layer and reconciles documentation/counts.

- [ ] **Step 1: Extend the e2e test for the manifest-modules review_tier path**

The pre-completion `review_tier` exclusion has a manifest auto-resolution branch (Task 3, Step 3b) that reads module plan files via `<git_root>/<feature_dir>/<module.file>` — the same class of path-resolution glue that bit this repo before (`_load_manifest_config` missing the feature_dir join). The unit tests cover the multi-file scan via `--additional-plan-files`; this step covers the manifest auto-resolution at the integration layer.

In `tests/integration/sdd-e2e-test.sh`, after the manifest is materialized, add a pre-completion invocation against a manifest that declares a `modules` array where a `review_tier: minimum` task lives in a non-active module file, and assert that task is excluded from the minimum-tier ratio (no `excessive_minimum_tier_quality` blocker). If the existing e2e fixture has no modules, add a minimal second module plan file with one declared-minimum task. Keep it a smoke-level assertion.

- [ ] **Step 2: Run all static + unit + integration test layers**

```bash
.venv/bin/python3 -m pytest tests/unit/ -v
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/ARaymond-installation/verify-symlink-install.sh
bash tests/integration/sdd-e2e-test.sh
```
Expected: all PASS. Record the new unit test total. The pre-change baseline is **328** passing (CLAUDE.md's "326" is stale — recount from this green run). Net change = + review_tier tests (model, validate-plan, pre-completion incl. multi-file) + `test_sdd_classification.py` − removed legacy midpoint/backwards-compat tests. Fix any failure before proceeding — a gate FAIL is never "expected" (see architectural principles).

- [ ] **Step 3: Manual smoke test of the classification fix**

Verify the original bug is fixed end-to-end (general-purpose reviewer logged, implementer enforced) using a throwaway manifest workspace, or rely on `test_sdd_classification.py` if Step 2 passed. Record the result.

- [ ] **Step 4: Update `CLAUDE.md`**

Update these sections to reflect the changes:
- **Testing** block: new unit test count (recount from Step 1), mention `test_sdd_classification.py` and the manifest-mode test-helper migration.
- **Hooks-Based Enforcement** block: document the 3-stage classification (reviewer → implementer → passthrough), dispatch-log auto-creation, inline validation-error excerpts, and that the legacy non-manifest path was removed (manifest mode now required; no-manifest + artifacts → BLOCK).
- **Adaptive Enforcement Tiers** block: note that `sdd-pre-dispatch-hook.sh` no longer has a legacy fallback.
- **Pydantic Validation** block: note the new `Task.review_tier` field (non-breaking, no schema bump).

- [ ] **Step 5: Update `docs/ARaymond-customization-manifest.md`**

Add an entry for this feature (SDD Hook Improvements, 2026-05-28): the 5 items, files changed, and the new test file. Update any per-script inventory lines for `sdd-pre-dispatch-hook.sh`, `controller-checkpoint.py`, `validate-plan.py`, and `plan.py`.

- [ ] **Step 6: Final regression re-run + commit**

```bash
.venv/bin/python3 -m pytest tests/unit/ -q
python3 tests/ARaymond-skill-regression/validate-all-skills.py
git add CLAUDE.md docs/ARaymond-customization-manifest.md
git commit -m "docs(sdd): record hook classification + review_tier changes; update test counts"
```

## Acceptance Criteria (Module 2)

- [x] Migrated helpers make `tests/unit/` green against the unchanged hook (Task 5 gate)
- [x] `general-purpose` reviewer dispatches are logged; `general-purpose` implementer dispatches are enforced
- [x] Ad-hoc (non-reviewer/non-implementer) dispatches pass through without logging or enforcement
- [x] First reviewer dispatch creates `reports/` + dispatch log
- [x] No manifest + artifacts → BLOCK with a manifest-guidance message; no manifest + no artifacts → ALLOW
- [x] Validation errors include the first 5 lines of `validate-report.py` output
- [x] All legacy branches removed; residual-legacy grep is clean
- [ ] All five test layers pass; `CLAUDE.md` + customization manifest updated with new counts and behavior
