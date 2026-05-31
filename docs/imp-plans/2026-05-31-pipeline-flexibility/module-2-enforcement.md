---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: "docs/imp-plans/2026-05-31-pipeline-flexibility/spec-distilled.md"
pattern_references:
  - name: "hook-task-type-parsing"
    source_files: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    reason: "3-stage classification pipeline for dispatch enforcement"
  - name: "checkpoint-pre-completion"
    source_files: ["skills/subagent-driven-development/scripts/controller-checkpoint.py"]
    reason: "Pre-completion phase check patterns (ratio checks, file-based gates)"
tasks:
  - id: 2
    title: "Hook: add task_type YAML reader and implementer dispatch logging"
    depends_on: []
    pattern_references: ["hook-task-type-parsing"]
  - id: 3
    title: "Hook: skip review checks for verification tasks"
    depends_on: [2]
    pattern_references: ["hook-task-type-parsing"]
  - id: 4
    title: "Checkpoint: add verification ratio check"
    depends_on: []
    pattern_references: ["checkpoint-pre-completion"]
  - id: 5
    title: "Checkpoint: add git reality check for verification tasks"
    depends_on: [2, 4]
    pattern_references: ["checkpoint-pre-completion"]
---

# Module 2: Enforcement

**Goal:** Thread `task_type` awareness through the SDD pre-dispatch hook (implementer logging, review skip logic) and controller checkpoint (verification ratio cap, git reality check).

**Source Contracts:** None

**Contract Constraints:**
- Hook uses `$PYTHON` (`$SUPERPOWERS_ROOT/.venv/bin/python3`) for PyYAML-dependent scripts
- Dispatch log format: existing entries use `<ISO-8601> DISPATCH reviewer task=N type=<review_type>`; new implementer entries use `<ISO-8601> DISPATCH implementer task=N type=implementer` — additive, nothing currently greps for `type=implementer`
- Existing Check 4c only greps for reviewer entries — adding implementer entries is non-breaking
- `controller-checkpoint.py` pre-completion phase uses `_declared_minimum_task_ids()` pattern for plan YAML parsing
- Verification ratio threshold: 30% (FAIL if exceeded)
- Git reality check: best-effort heuristic backstop using `git log --after/--before`
- Task_type defaults to `"implementation"` when absent — full backwards compatibility

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 2 | `sdd-pre-dispatch-hook.sh`, `tests/unit/test_sdd_classification.py` | `plan.py` (model from Task 0) | Task 0 |
| Task 3 | `sdd-pre-dispatch-hook.sh` (cont.), `test_sdd_classification.py` (cont.) | Task 2 output | Task 2 |
| Task 4 | `controller-checkpoint.py`, `tests/unit/test_pre_completion_gates.py` | `plan.py` | Task 0 |
| Task 5 | `controller-checkpoint.py` (cont.), `test_pre_completion_gates.py` (cont.) | Task 4 output, dispatch log format (Task 2) | Task 2, 4 |

---

### Task 2: Hook — add task_type YAML reader and implementer dispatch logging

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
- Test: `tests/unit/test_sdd_classification.py`

**Pattern References:**
- `sdd-pre-dispatch-hook.sh:34-38` — `$PYTHON` resolution
- `sdd-pre-dispatch-hook.sh:150-174` — reviewer dispatch log writes (Stage 1)
- `sdd-pre-dispatch-hook.sh:177-188` — Stage 2 implementer detection

- [x] **Step 1: Write failing tests for implementer dispatch logging**

Read `tests/unit/sdd_test_helpers.py` and `tests/unit/test_sdd_classification.py` to understand the existing test setup patterns (manifest mode, temp directories, subprocess-based hook invocation).

**Important (pre-execution audit, Order 3 — VERIFIED against `sdd_test_helpers.py`):** Both `setup_sdd_workspace()` and `setup_manifest_workspace()` write plan files WITHOUT YAML frontmatter and set `active_module_file: None`. The new `get_task_type()` reads `task_type` from plan YAML frontmatter, so against the default fixtures it returns `"implementation"` for *every* task — meaning a verification test built on the default helper passes **vacuously** (it never exercises the verification path). To make `task_type: verification` actually read:
> 1. Write a plan file WITH `---` YAML frontmatter containing a `tasks:` array whose entries carry explicit `task_type:` values, e.g.:
>    ```yaml
>    ---
>    schema_version: 1
>    feature_archetype: extension
>    tasks:
>      - id: 0
>        title: "Setup"
>      - id: 1
>        title: "Audit"
>        task_type: verification
>    ---
>    ```
> 2. Point the manifest at it. The hook resolves the plan via `MANIFEST_PLAN_FILE` (and `MANIFEST_MODULE_FILE` if set) as `"$GIT_ROOT/<plan_file>"`. So after `setup_manifest_workspace(...)`, overwrite the manifest's `plan_file` (git-root-relative) to point at your frontmatter plan AND write that plan at the resolved path — OR set `active_module_file` to it. `get_task_type()` prefers `MANIFEST_MODULE_FILE` over `MANIFEST_PLAN_FILE` (see Task 2 Step 5), so be consistent about which one you populate.
> 3. **Positive control (required):** include at least one assertion proving the fixture is non-vacuous — e.g., a test where the SAME setup with `task_type: implementation` (or absent) BLOCKS while flipping ONLY `task_type` to `verification` flips BLOCK→ALLOW. A test that only checks the verification case can pass even if `get_task_type()` is broken.

Add a `TestImplementerDispatchLogging` class that:
- Sets up manifest mode with all prerequisites met (pre-execution audit, deviations, reports dir, previous task reports and reviews)
- Invokes the hook with an implementer dispatch for task N
- Asserts the dispatch log contains `type=implementer task=N`

Follow the existing patterns in `test_sdd_classification.py` for fixture setup and subprocess invocation.

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py::TestImplementerDispatchLogging -v`
Expected: FAIL — no implementer entries written to dispatch log

- [x] **Step 3: Add `get_task_type()` helper function**

Add after the `check_report_file()` function (around line 239) in `sdd-pre-dispatch-hook.sh`:

```bash
# ─── Helper: read task_type from plan YAML frontmatter ────────────────────
# Uses $PYTHON (PyYAML) to parse the YAML frontmatter's tasks array.
# Returns "implementation" (default) or "verification".
get_task_type() {
  local plan_file="$1"
  local task_id="$2"
  if [ ! -f "$plan_file" ]; then
    echo "implementation"
    return
  fi
  local result
  result=$($PYTHON -c "
import yaml, sys
with open(sys.argv[1]) as f:
    content = f.read()
if not content.startswith('---'):
    print('implementation')
    sys.exit(0)
end = content.find('---', 3)
if end == -1:
    print('implementation')
    sys.exit(0)
try:
    fm = yaml.safe_load(content[3:end])
except Exception:
    print('implementation')
    sys.exit(0)
tasks = fm.get('tasks', []) if isinstance(fm, dict) else []
tid = int(sys.argv[2])
for t in tasks:
    if isinstance(t, dict) and t.get('id') == tid:
        print(t.get('task_type', 'implementation'))
        sys.exit(0)
print('implementation')
" "$plan_file" "$task_id" 2>/dev/null)
  echo "${result:-implementation}"
}
```

- [x] **Step 4: Add implementer dispatch logging to Stage 2**

After the `IS_IMPLEMENTER=true` assignment in Stage 2 (around line 183), add:

```bash
# Log implementer dispatch (gives git reality check reliable timestamps)
if [ -n "$TASK_NUMBER" ]; then
  if [ -f "$DISPATCH_LOG" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH implementer task=$TASK_NUMBER type=implementer" >> "$DISPATCH_LOG"
  elif [ -d "$(dirname "$DISPATCH_LOG")" ]; then
    touch "$DISPATCH_LOG"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH implementer task=$TASK_NUMBER type=implementer" >> "$DISPATCH_LOG"
  fi
fi
```

- [x] **Step 5: Resolve task types for current and previous tasks**

Add after the implementer dispatch logging (before the enforcement checks section):

```bash
# Resolve plan file for task_type lookups
EFFECTIVE_PLAN_FILE=""
if [ -n "$MANIFEST_MODULE_FILE" ] && [ -f "$MANIFEST_MODULE_FILE" ]; then
  EFFECTIVE_PLAN_FILE="$MANIFEST_MODULE_FILE"
elif [ -n "$MANIFEST_PLAN_FILE" ] && [ -f "$MANIFEST_PLAN_FILE" ]; then
  EFFECTIVE_PLAN_FILE="$MANIFEST_PLAN_FILE"
fi

# Read current and previous task types
CURRENT_TASK_TYPE="implementation"
PREV_TASK_TYPE="implementation"
if [ -n "$EFFECTIVE_PLAN_FILE" ] && [ -n "$TASK_NUMBER" ]; then
  CURRENT_TASK_TYPE=$(get_task_type "$EFFECTIVE_PLAN_FILE" "$TASK_NUMBER")
  if [ "$TASK_NUMBER" -gt 0 ] 2>/dev/null; then
    PREV_TASK_TYPE=$(get_task_type "$EFFECTIVE_PLAN_FILE" "$((TASK_NUMBER - 1))")
  fi
fi
```

- [x] **Step 6: Run tests**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v`
Expected: ALL PASS

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/unit/test_sdd_classification.py
git commit -m "feat(hook): add task_type YAML reader and implementer dispatch logging

- get_task_type() helper reads task_type from plan YAML via \$PYTHON
- Stage 2 implementer detection now logs to dispatch log (type=implementer)
- Resolve CURRENT_TASK_TYPE and PREV_TASK_TYPE for downstream check skipping

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 3: Hook — skip review checks for verification tasks

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`
- Test: `tests/unit/test_sdd_classification.py`

**Pattern References:**
- `sdd-pre-dispatch-hook.sh:343-416` — Check 4 block (previous task review reports)
- `sdd-pre-dispatch-hook.sh:422-457` — Check 4c (dispatch provenance)
- `sdd-pre-dispatch-hook.sh:519-551` — Check 5d (partner review)

- [x] **Step 1: Write failing tests for verification task check skipping**

Add to `tests/unit/test_sdd_classification.py`:

```python
class TestVerificationTaskCheckSkipping:
    """Verification tasks skip review-related checks."""

    def test_current_verification_skips_partner_review(self):
        """Check 5d skipped when current task is task_type: verification."""
        # Setup: manifest mode, current task has task_type=verification in plan frontmatter
        # No partner review file exists
        # Expected: hook exits 0 (ALLOW), not exit 2 (BLOCKED)

    def test_previous_verification_skips_review_reports(self):
        """Checks 4b/4c skipped when previous task was task_type: verification."""
        # Setup: manifest mode, previous task had task_type=verification in plan frontmatter
        # No spec/quality review files exist for previous task
        # Expected: hook exits 0 (ALLOW)

    def test_implementation_task_still_requires_reviews(self):
        """Regular implementation tasks still require all review checks."""
        # Setup: manifest mode, all tasks task_type=implementation (or absent)
        # No reviews for previous task
        # Expected: hook exits 2 (BLOCKED) — existing behavior unchanged
```

Follow existing test patterns for subprocess hook invocation with manifest + plan fixtures. **Remember (Order 3):** the verification tests MUST use a frontmatter plan pointed at by the manifest — follow the concrete 3-step recipe in Task 2 Step 1's "Important" callout. `test_implementation_task_still_requires_reviews` is the required positive control: build it from the SAME workspace setup as `test_current_verification_skips_partner_review`, differing ONLY in the `task_type` value (absent/implementation → BLOCK; verification → ALLOW). If both the implementation and verification variants ALLOW, your fixture isn't reading `task_type` from the manifest-pointed frontmatter plan — fix the fixture, not the assertion.

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py::TestVerificationTaskCheckSkipping -v`
Expected: FAIL — hook still blocks on missing reviews

- [x] **Step 3: Skip Check 4b review reports when previous task was verification**

Wrap the spec review and quality review checks for the previous task (around lines 389-416). The existing code is inside the `if [ -n "$TASK_NUMBER" ] && [ "$TASK_NUMBER" -gt 0 ]` block, after the first-in-module check. Add a guard:

```bash
    if [ "$PREV_TASK_TYPE" = "verification" ]; then
      : # Previous task was verification — no spec/quality reviews to check
    else
      # Previous task spec review report [existing code stays here]
      ...
      # Previous task quality review report [existing code stays here]
      ...
    fi
```

- [x] **Step 4: Skip Check 4c dispatch provenance when previous task was verification**

Inside the dispatch provenance block (around line 424-457), add a guard before the existing checks:

```bash
    if [ "$PREV_TASK_TYPE" = "verification" ]; then
      : # Previous task was verification — no dispatch provenance to verify
    else
      # [existing dispatch provenance checks]
    fi
```

- [x] **Step 5: Skip Check 5d partner review when current task is verification**

Modify the partner review check (around line 530). The existing code checks `$NEED_PARTNER`. Add `$CURRENT_TASK_TYPE` as a higher-priority guard:

```bash
  if [ "$CURRENT_TASK_TYPE" = "verification" ]; then
    : # Current task is verification — no partner review required
  elif [ "$NEED_PARTNER" = "false" ]; then
    : # Skip — manifest tier does not require partner review
  else
    # [existing partner review checks — no changes]
  fi
```

- [x] **Step 6: Run tests**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v`
Expected: ALL PASS

- [x] **Step 7: Run full unit test suite**

Run: `.venv/bin/python3 -m pytest tests/unit/ -v`
Expected: ALL PASS (351 existing + new tests)

- [x] **Step 8: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/unit/test_sdd_classification.py
git commit -m "feat(hook): skip review checks for verification tasks

- Check 5d (partner review) skipped when current task is verification
- Checks 4b/4c (review reports/provenance) skipped when prev task was verification
- Implementation tasks unchanged

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 4: Checkpoint — add verification ratio check

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py`
- Test: `tests/unit/test_pre_completion_gates.py`

**Pattern References:**
- `controller-checkpoint.py:224-251` — `_declared_minimum_task_ids()` for YAML parsing pattern
- `controller-checkpoint.py:1113-1141` — `_ratio_check()` for ratio check pattern in pre-completion

- [x] **Step 1: Write failing tests**

Read `tests/unit/test_pre_completion_gates.py` to understand the existing test setup. Add:

```python
class TestVerificationRatioCheck:
    """Pre-completion verification task ratio capped at 30%."""

    def test_no_verification_tasks_passes(self):
        """Plan with all implementation tasks passes ratio check."""
        # Create plan YAML with 5 implementation tasks (no task_type field = implementation default)
        # Run pre-completion checkpoint
        # Assert verification_ratio check is PASS

    def test_30_percent_passes(self):
        """3 verification out of 10 tasks (30%) passes."""
        # Create plan YAML with 7 implementation + 3 verification tasks
        # Assert verification_ratio is PASS

    def test_over_30_percent_fails(self):
        """4 verification out of 10 tasks (40%) fails."""
        # Create plan YAML with 6 implementation + 4 verification tasks
        # Assert verification_ratio is FAIL
        # Assert blocker names the verification tasks

    def test_ratio_with_no_tasks_passes(self):
        """Empty plan passes (no divide-by-zero)."""
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py::TestVerificationRatioCheck -v`
Expected: FAIL

- [x] **Step 3: Add `_verification_task_ids()` helper**

Add after `_declared_minimum_task_ids()` in `controller-checkpoint.py`:

```python
def _verification_task_ids(plan_contents):
    # type: (list) -> set
    """Collect task IDs declaring task_type=='verification' from plan frontmatter."""
    import yaml
    result = set()
    for content in plan_contents:
        if not content or not content.startswith("---"):
            continue
        end = content.find("---", 3)
        if end == -1:
            continue
        try:
            fm = yaml.safe_load(content[3:end])
        except Exception:
            continue
        tasks = fm.get("tasks") if isinstance(fm, dict) else None
        if not isinstance(tasks, list):
            continue
        for t in tasks:
            if isinstance(t, dict) and t.get("task_type") == "verification" and isinstance(t.get("id"), int):
                result.add(t["id"])
    return result
```

- [x] **Step 4: Add verification ratio check to pre-completion**

Add after the minimum-tier ratio checks in `run_pre_completion()` (after line 1143):

```python
    # Check 8: Verification task ratio cap (>30% triggers blocker)
    verification_ids = _verification_task_ids(all_plan_contents)
    all_task_ids = set(
        int(n) for content in all_plan_contents
        for n in TASK_HEADER_PATTERN.findall(content)
    )
    total_tasks = len(all_task_ids)
    verif_count = len(verification_ids & all_task_ids)
    if total_tasks > 0 and verif_count / total_tasks > 0.3:
        verif_list = ", ".join(f"Task {t}" for t in sorted(verification_ids & all_task_ids))
        checks["verification_ratio"] = {
            "status": "FAIL",
            "detail": (
                f"{verif_count}/{total_tasks} tasks are verification type "
                f"({round(100 * verif_count / total_tasks)}%). "
                f"Maximum is 30%. Verification tasks: {verif_list}. "
                "Consider reclassifying some as implementation."
            ),
        }
        blockers.append("verification_ratio")
    else:
        checks["verification_ratio"] = {
            "status": "PASS",
            "detail": (
                f"{verif_count}/{total_tasks} tasks are verification type"
                if total_tasks > 0
                else "No tasks to ratio"
            ),
        }
```

- [x] **Step 5: Run tests**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v`
Expected: ALL PASS

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_pre_completion_gates.py
git commit -m "feat(checkpoint): add verification task ratio check

Pre-completion blocks when >30% of tasks are verification type.
Names the verification tasks in the FAIL message.

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 5: Checkpoint — add git reality check for verification tasks

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py`
- Test: `tests/unit/test_pre_completion_gates.py`

**Pattern References:**
- `controller-checkpoint.py` — pre-completion phase, subprocess usage for git commands

- [x] **Step 1: Write failing tests**

Add to `tests/unit/test_pre_completion_gates.py`:

```python
class TestGitRealityCheck:
    """Pre-completion detects file modifications during verification task windows."""

    def test_no_verification_tasks_skips(self):
        """No verification tasks → check PASS with skip message."""

    def test_clean_window_passes(self):
        """No commits during verification window → PASS."""
        # Setup: temp git repo, dispatch log with implementer timestamps
        # No commits between verification task's window
        # Assert: verification_git_reality PASS

    def test_file_modifying_commits_fails(self):
        """Commits modifying files during verification window → FAIL."""
        # Setup: temp git repo with a commit inside the verification window
        # Assert: verification_git_reality FAIL
        # Assert: blocker message names the task

    def test_missing_dispatch_log_passes(self):
        """No dispatch log → can't check, PASS (best-effort)."""
```

**Test construction requirements (pre-execution audit, Order 4 — VERIFIED against `test_pre_completion_gates.py`):**

1. **Dispatch-log path:** the existing `run_pre_completion` helper invokes the checkpoint with `--plan-file` + `--reports-dir` and NO `--manifest`. In that mode the wiring (Step 4) resolves `dispatch_log_path = os.path.join(args.reports_dir, ".dispatch-log")`. So the test must create the log at exactly `<reports_dir>/.dispatch-log`.
2. **Exact writer format:** build the implementer log line **verbatim** in Task 2's writer format — `<ISO-8601> DISPATCH implementer task=N type=implementer` — matching the reader regex `(\S+)\s+DISPATCH\s+implementer\s+task=(\d+)\s+type=implementer`. Do NOT hand-type an approximation; the highest-risk failure mode (silent false-PASS) is a writer/reader format drift. Prefer copying the literal line shape from Task 2 Step 4.
3. **Git isolation (critical):** `_check_verification_git_reality` is wired with `git_root=None`, so it runs `git log` in the subprocess's CWD. The default harness CWD is the host superpowers repo — its real commits would land inside any `--after/--before` window and produce a **false FAIL**. The test MUST run the checkpoint subprocess with `cwd=` an isolated `git init` temp repo (extend `run_pre_completion` to thread a `cwd` kwarg, or call `subprocess.run([... checkpoint ...], cwd=<temp_git_repo>)` directly). Alternatively, import `_check_verification_git_reality` in-process and pass an explicit `git_root=<temp_repo>`.
4. **`test_clean_window_passes` must be non-vacuous:** assert PASS even though the *host* repo has commits — i.e., the isolation in (3) is what makes it pass. If it passes without isolation, the test proves nothing.
5. **`test_file_modifying_commits_fails`:** in the temp repo, create a commit whose date falls inside the verification window. Control commit time via `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE` env so it lands between the task-N and task-(N+1) dispatch timestamps in your log. Assert `verification_git_reality` FAIL and that the blocker detail names `Task N`.

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py::TestGitRealityCheck -v`
Expected: FAIL

- [x] **Step 3: Implement `_check_verification_git_reality()`**

Add to `controller-checkpoint.py`:

```python
def _check_verification_git_reality(
    verification_ids,  # type: set
    dispatch_log_path,  # type: str
    git_root=None,  # type: Optional[str]
):
    # type: (...) -> list
    """Check whether verification tasks produced file-modifying commits.

    Reads implementer dispatch timestamps from the dispatch log,
    runs git log between consecutive task windows,
    returns findings for any file modifications detected.
    """
    if not verification_ids or not os.path.isfile(dispatch_log_path):
        return []

    dispatch_times = {}  # type: dict
    with open(dispatch_log_path) as f:
        for line in f:
            m = re.match(
                r"(\S+)\s+DISPATCH\s+implementer\s+task=(\d+)\s+type=implementer",
                line,
            )
            if m:
                dispatch_times[int(m.group(2))] = m.group(1)

    findings = []
    sorted_tasks = sorted(dispatch_times.keys())
    for vid in sorted(verification_ids):
        if vid not in dispatch_times:
            continue
        start_ts = dispatch_times[vid]
        idx = sorted_tasks.index(vid)
        end_ts = dispatch_times[sorted_tasks[idx + 1]] if idx + 1 < len(sorted_tasks) else None

        git_cmd = ["git", "log", "--oneline", f"--after={start_ts}"]
        if end_ts:
            git_cmd.append(f"--before={end_ts}")
        git_cmd.extend(["--diff-filter=ACDMR", "--name-only"])

        if git_root:
            git_cmd = ["git", "-C", git_root] + git_cmd[1:]

        try:
            result = subprocess.run(git_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                findings.append({
                    "task": vid,
                    "start": start_ts,
                    "end": end_ts or "now",
                    "commits": result.stdout.strip(),
                })
        except (subprocess.TimeoutExpired, OSError):
            pass

    return findings
```

- [x] **Step 4: Wire into pre-completion phase**

Add after the verification ratio check:

```python
    # Check 9: Git reality check — verification tasks must not modify files
    if verification_ids:
        dispatch_log_path = ""
        if getattr(args, "manifest", None):
            try:
                _mp = Path(args.manifest)
                _md = json.loads(_mp.read_text(encoding="utf-8"))
                _gr = _resolve_git_root(_mp)
                dispatch_log_path = os.path.join(
                    _gr, _md.get("paths", {}).get("dispatch_log", "")
                )
            except Exception:
                pass
        elif args.reports_dir:
            dispatch_log_path = os.path.join(args.reports_dir, ".dispatch-log")

        git_findings = _check_verification_git_reality(
            verification_ids, dispatch_log_path
        )
        if git_findings:
            detail_parts = [
                f"Task {f['task']} (window {f['start']}–{f['end']}): file modifications detected"
                for f in git_findings
            ]
            checks["verification_git_reality"] = {
                "status": "FAIL",
                "detail": "Verification task(s) produced file modifications — requires review. " + "; ".join(detail_parts),
            }
            blockers.append("verification_git_reality")
        else:
            checks["verification_git_reality"] = {
                "status": "PASS",
                "detail": f"No file modifications during {len(verification_ids)} verification window(s)",
            }
    else:
        checks["verification_git_reality"] = {
            "status": "PASS",
            "detail": "No verification tasks — git reality check skipped",
        }
```

- [x] **Step 5: Run tests**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v`
Expected: ALL PASS

- [x] **Step 6: Run full unit test suite**

Run: `.venv/bin/python3 -m pytest tests/unit/ -v`
Expected: ALL PASS (351 existing + new tests)

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_pre_completion_gates.py
git commit -m "feat(checkpoint): add git reality check for verification tasks

Pre-completion checks git log between implementer dispatch timestamps.
If a verification task's window contains file-modifying commits, FAIL.
Best-effort heuristic — plan-time warnings and ratio cap are primary defenses.

Prompted by Aaron; Co-Authored by Claude"
```

## Module 2 Acceptance Criteria

- [x] Hook `get_task_type()` reads task_type from plan YAML frontmatter via `$PYTHON`
- [x] Hook logs implementer dispatches to dispatch log with timestamps
- [x] Check 5d (partner review) skipped when current task is verification
- [x] Checks 4b/4c (reviews/provenance) skipped when previous task was verification
- [x] Implementation tasks unchanged — all review checks still enforced
- [x] Verification ratio FAIL when >30% of tasks are verification
- [x] Git reality check detects file modifications during verification windows
- [x] All existing hook, checkpoint, and classification tests pass
