---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
integration_test:
  path: tests/integration/sdd-e2e-test.sh
shared_constants: []
pattern_references:
  - name: "checkpoint-tests"
    source_files: ["tests/unit/test_pre_completion_gates.py"]
    reason: "Check 7 ratio + Check 9 git-reality test harness: reports_dir setup, _init_temp_git_repo/_commit_file_at, direct _check_verification_git_reality calls"
  - name: "archive-precedent"
    source_files: ["skills/subagent-driven-development/scripts/controller-checkpoint.py"]
    reason: "find_report_file/find_all_report_files (lines 125-197) glob archive-*/ with live-wins via sorted()[-1] — the exact pattern Tasks 1-2 extend"
  - name: "hook-tests"
    source_files: ["tests/unit/test_sdd_classification.py"]
    reason: "Hook subprocess test harness: setup_sdd_workspace/setup_full_sdd_workspace, make_hook_input, run_hook, dispatch-log assertions"
  - name: "transition-tests"
    source_files: ["tests/unit/test_transition_module.py"]
    reason: "transition-module.py validate_module_completion manifest-workspace test patterns"
tasks:
  - id: 1
    title: "N27: Check 7 archive-aware review-tier inputs"
    pattern_references: ["checkpoint-tests", "archive-precedent"]
  - id: 2
    title: "N27: Check 9 archive-aware dispatch-log merge"
    depends_on: [1]
    pattern_references: ["checkpoint-tests", "archive-precedent"]
  - id: 3
    title: "N26: dispatch-log classification + Check 3b allowlist + baseline recapture"
    depends_on: [2]
    pattern_references: ["hook-tests"]
  - id: 4
    title: "N19: transition module.file AND-exists fallback + cleanup"
    depends_on: [3]
    pattern_references: ["transition-tests"]
---

# Module 1 — Aggregate-Gate Visibility

> **For agentic workers:** This is a module of a larger plan. Invoke `superpowers:subagent-driven-development` before implementing. See `plan.md` for the parent coordination document, the Shared Internal Contract (dispatch-log grammar), and the resolved O1–O4 decisions.

**Goal:** Make pre-completion Check 7 (min-tier ratio) and Check 9 (git-reality) archive-aware so they police ALL modules after a transition; add the hook's Stage-0 fix/re-review marker classification plus the Stage-3 unattributed fallback and the Check 3b allowlist additions (closing the dispatch-log fix-cycle blind spots); and align `transition-module.py`'s `module.file` fallback with the hook's stricter `-n` + `-f` semantic.

**Source Contracts:** None

No external contract; no Task 0 (a bare `None` value is valid-absent per N7 on main).

**Contract Constraints:** None external. The one internal contract is the **dispatch-log line grammar** in `plan.md` → *Shared Internal Contract*. Load-bearing invariant for Tasks 2 + 3: Check 9's parser (`controller-checkpoint.py:324`) matches ONLY `type=implementer`; a marked fix emits ONLY `type=fix` and skips the `type=implementer` write.

**Shared Constants:** None.

**Pattern References:**
- `controller-checkpoint.py:125-197` (`find_report_file`/`find_all_report_files`) — archive-aware glob with live-wins; Tasks 1-2 extend it.
- `tests/unit/test_pre_completion_gates.py` — Check 7/9 harness (`run_pre_completion` helper, `_init_temp_git_repo`, `_commit_file_at`).
- `tests/unit/test_sdd_classification.py` — hook subprocess harness.
- `tests/unit/test_transition_module.py` — transition manifest-workspace harness.

**Feature Archetype:** Extension (widens existing check inputs; N19 removes dead code with all branches audited).

## Code Footprint

| Category | File / Function | Action | Dependencies to Verify |
|----------|-----------------|--------|------------------------|
| Modified | `controller-checkpoint.py` :: `_review_tiers_per_task` | Extend (archive glob + dedupe) | Caller `_ratio_check` (:1468) — input widens only |
| Modified | `controller-checkpoint.py` :: `_check_verification_git_reality` + new `_merged_dispatch_times` | Extend | Caller Check 9 (:1553) — signature unchanged |
| Modified | `sdd-pre-dispatch-hook.sh` :: new Stage 0, Stage 1 guard, Stage 2 log-write guard, Stage 3 fallback, Check 3b allowlist, additionalContext | Extend | `tests/ARaymond-hook-baseline/baseline.txt` (re-capture SAME commit) |
| New | `skills/subagent-driven-development/references/dispatch-markers.md` | Create (marker convention doc; zero SKILL.md word cost) | — |
| Modified | `transition-module.py` :: `validate_module_completion` | Refactor (dead-code removal + `-f` guard) | Both branches reassign `verif_ids` today |
| Modified | Tests: `test_pre_completion_gates.py`, `test_sdd_classification.py`, `test_transition_module.py` | Extend | — |

## File Map

- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — Tasks 1, 2
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — Task 3
- `skills/subagent-driven-development/references/dispatch-markers.md` — Task 3 (new)
- `tests/ARaymond-hook-baseline/baseline.txt` — Task 3 (re-capture)
- `skills/subagent-driven-development/scripts/transition-module.py` — Task 4
- `tests/unit/test_pre_completion_gates.py` — Tasks 1, 2
- `tests/unit/test_sdd_classification.py` — Task 3
- `tests/unit/test_transition_module.py` — Task 4

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| 1 | `controller-checkpoint.py` (`_review_tiers_per_task`), `test_pre_completion_gates.py` | `find_report_file` precedent | — |
| 2 | `controller-checkpoint.py` (`_check_verification_git_reality` + `_merged_dispatch_times`), `test_pre_completion_gates.py` | Task 1's func | 1 |
| 3 | `sdd-pre-dispatch-hook.sh`, `references/dispatch-markers.md` (new), `baseline.txt`, `test_sdd_classification.py` | `controller-checkpoint.py:324` (contract) | 2 |
| 4 | `transition-module.py` (`validate_module_completion`), `test_transition_module.py` | hook `get_task_type` construct | 3 |

All tasks are serialized (no parallelism). Tasks 1 and 2 share `controller-checkpoint.py`; the `depends_on` chain enforces that Task 2 runs after Task 1.

---

### Task 1: N27 — Check 7 archive-aware review-tier inputs

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py` (`_review_tiers_per_task`, currently lines 200-233)
- Test: `tests/unit/test_pre_completion_gates.py`

**Pattern References:**
- `controller-checkpoint.py:125-197` — `find_report_file`/`find_all_report_files` glob `archive-*/` and pick live via `sorted()[-1]`. Task 1 applies the same archive-awareness, keyed by task id with live-wins.

**Context:** Check 7's `_ratio_check` (:1468) calls `_review_tiers_per_task(args.reports_dir, review_type)`. After `transition-module.py` archives a completed module's review files into `reports/archive-<module>/`, those reviews vanish from the flat glob, so the ratio only sees the live (final) module. This task widens `_review_tiers_per_task` to also glob `archive-*/`, deduped by task id with the live dir winning.

- [x] **Step 1: Write the failing tests** in `tests/unit/test_pre_completion_gates.py` (add a new test class near `TestGitRealityCheck`):

```python
class TestReviewTiersArchiveAware:
    """N27: _review_tiers_per_task globs archive-*/ with live-wins."""

    def test_review_tiers_includes_archived(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        (archive / "task-001-quality-review-minimum-tier.md").write_text("x")
        (archive / "task-002-quality-review-minimum-tier.md").write_text("x")
        (archive / "task-003-quality-review-minimum-tier.md").write_text("x")
        (reports / "task-004-quality-review.md").write_text("x")
        tiers = dict(
            _checkpoint._review_tiers_per_task(str(reports), "quality-review")
        )
        assert tiers == {1: True, 2: True, 3: True, 4: False}

    def test_review_tiers_live_wins_over_archive(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        # Same task id: archived as minimum, re-reviewed live as full.
        (archive / "task-005-quality-review-minimum-tier.md").write_text("x")
        (reports / "task-005-quality-review.md").write_text("x")
        tiers = dict(
            _checkpoint._review_tiers_per_task(str(reports), "quality-review")
        )
        assert tiers[5] is False  # live full wins over archived minimum

    def test_review_tiers_partner_archive(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        (archive / "partner-review-001-minimum-tier.md").write_text("x")
        (reports / "partner-review-002.md").write_text("x")
        tiers = dict(
            _checkpoint._review_tiers_per_task(str(reports), "partner-review")
        )
        assert tiers == {1: True, 2: False}
```

- [x] **Step 2: Run to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py::TestReviewTiersArchiveAware -v`
Expected: FAIL — today `_review_tiers_per_task` returns only `{4: False}` (live dir), missing all archived ids.

- [x] **Step 3: Replace `_review_tiers_per_task`** (lines 200-233) with the archive-aware version:

```python
def _review_tiers_per_task(reports_dir, review_type):
    # type: (str, str) -> list
    """Return [(task_id:int, is_minimum:bool), ...] for the given review type.

    Recognizes:
      quality-review: task-NNN-quality-review.md / task-NNN-quality-review-minimum-tier.md
      partner-review: partner-review-NNN.md       / partner-review-NNN-minimum-tier.md

    Archive-aware (N27): globs the live reports dir AND reports/archive-*/ with
    the same basename patterns, so the Check 7 ratio still covers reviews that
    transition-module.py moved into archive-<module>/. Result is keyed by task
    id; when a task id appears in both an archive and the live dir, the LIVE
    entry wins (post-transition re-reviews are not double-counted). Task ids are
    globally unique across modules, so archive-vs-archive collisions cannot
    occur. One of the 5 documented archive-aware lookups (see CLAUDE.md).
    """
    if review_type == "quality-review":
        full_name = "task-*-quality-review.md"
        min_name = "task-*-quality-review-minimum-tier.md"
        id_re = re.compile(r"task-(\d+)-quality-review(?:-minimum-tier)?\.md$")
    elif review_type == "partner-review":
        full_name = "partner-review-*.md"
        min_name = "partner-review-*-minimum-tier.md"
        id_re = re.compile(r"partner-review-(\d+)(?:-minimum-tier)?\.md$")
    else:
        return []

    def _classify_dir(directory):
        # type: (str) -> dict
        """Return {task_id: is_minimum} for one directory."""
        result = {}  # type: dict
        min_paths = set(glob.glob(os.path.join(directory, min_name)))
        for path in min_paths:
            m = id_re.search(os.path.basename(path))
            if m:
                result[int(m.group(1))] = True
        # The full glob can also match -minimum-tier.md files (notably the
        # partner pattern), so skip anything already captured as minimum.
        for path in glob.glob(os.path.join(directory, full_name)):
            if path in min_paths:
                continue
            m = id_re.search(os.path.basename(path))
            if m:
                result.setdefault(int(m.group(1)), False)
        return result

    tiers = {}  # type: dict
    # Archives first (sorted = module order), live dir LAST so live wins.
    for archive_dir in sorted(glob.glob(os.path.join(reports_dir, "archive-*"))):
        if os.path.isdir(archive_dir):
            tiers.update(_classify_dir(archive_dir))
    tiers.update(_classify_dir(reports_dir))

    return [(tid, is_min) for tid, is_min in tiers.items()]
```

- [x] **Step 4: Run to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v`
Expected: PASS (new class + all pre-existing ratio tests — the single-dir behavior is unchanged for workspaces with no `archive-*/`).

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_pre_completion_gates.py
git commit -m "feat(checkpoint): N27 — Check 7 archive-aware review-tier inputs"
```

---

### Task 2: N27 — Check 9 archive-aware dispatch-log merge

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py` (`_check_verification_git_reality`, lines 305-366; add new `_merged_dispatch_times`)
- Test: `tests/unit/test_pre_completion_gates.py`

**Context:** Check 9 (`_check_verification_git_reality`) reads implementer dispatch timestamps from ONLY the live `.dispatch-log`. After a transition the live log is truncated (copied to `archive-<module>/.dispatch-log` then emptied), so an archived module's verification tasks vanish from the map and are silently skipped (:334). This task merges archived logs (module order) with the live log, later lines overwriting per task id, preserving the load-bearing contract that ONLY `type=implementer` lines open a window.

- [x] **Step 1: Write the failing tests** in `tests/unit/test_pre_completion_gates.py` (add to a new class; the `_init_temp_git_repo`/`_commit_file_at` helpers already exist in this file):

```python
class TestCheck9ArchiveAware:
    """N27: Check 9 merges archived dispatch logs + live log."""

    def test_merged_dispatch_times_includes_archive(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        (archive / ".dispatch-log").write_text(
            "2026-01-01T00:00:00Z DISPATCH implementer task=3 type=implementer\n"
        )
        (reports / ".dispatch-log").write_text(
            "2026-01-02T00:00:00Z DISPATCH implementer task=5 type=implementer\n"
        )
        times = _checkpoint._merged_dispatch_times(str(reports / ".dispatch-log"))
        assert times == {3: "2026-01-01T00:00:00Z", 5: "2026-01-02T00:00:00Z"}

    def test_merged_dispatch_times_live_overwrites(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        archive = reports / "archive-Mod1"
        archive.mkdir()
        (archive / ".dispatch-log").write_text(
            "2026-01-01T00:00:00Z DISPATCH implementer task=3 type=implementer\n"
        )
        (reports / ".dispatch-log").write_text(
            "2026-02-02T00:00:00Z DISPATCH implementer task=3 type=implementer\n"
        )
        times = _checkpoint._merged_dispatch_times(str(reports / ".dispatch-log"))
        assert times == {3: "2026-02-02T00:00:00Z"}  # live (later) wins

    def test_merged_dispatch_times_ignores_fix_lines(self, tmp_path):
        # N26/N27 contract: type=fix / type=fix-unattributed never open a window.
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / ".dispatch-log").write_text(
            "2026-01-01T00:00:00Z DISPATCH fix task=3 type=fix\n"
            "2026-01-01T00:00:01Z DISPATCH adhoc type=fix-unattributed\n"
        )
        times = _checkpoint._merged_dispatch_times(str(reports / ".dispatch-log"))
        assert times == {}

    def test_archived_window_file_modification_fails(self):
        """A verification task dispatched ONLY in an archived log, with a
        file-modifying commit inside its window, FAILs after the merge (today
        the live-only read silently skips it)."""
        repo = _init_temp_git_repo()
        try:
            _commit_file_at(repo, "modified.txt", "2026-03-01T10:30:00")
            log_dir = tempfile.mkdtemp()
            try:
                reports = os.path.join(log_dir, "reports")
                archive = os.path.join(reports, "archive-Mod1")
                os.makedirs(archive)
                with open(os.path.join(archive, ".dispatch-log"), "w") as f:
                    f.write(
                        "2026-03-01T10:00:00 DISPATCH implementer task=3 type=implementer\n"
                    )
                    f.write(
                        "2026-03-01T11:00:00 DISPATCH implementer task=4 type=implementer\n"
                    )
                live = os.path.join(reports, ".dispatch-log")
                open(live, "w").close()  # truncated live log (post-transition)
                findings = _checkpoint._check_verification_git_reality(
                    {3}, live, git_root=repo
                )
                assert findings, f"Expected finding from archived window: {findings}"
                assert findings[0]["task"] == 3
            finally:
                shutil.rmtree(log_dir, ignore_errors=True)
        finally:
            shutil.rmtree(repo, ignore_errors=True)
```

- [x] **Step 2: Run to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py::TestCheck9ArchiveAware -v`
Expected: FAIL — `_merged_dispatch_times` does not exist (AttributeError); the archived-window test returns `[]` (live-only read skips task 3).

- [x] **Step 3: Add `_merged_dispatch_times`** immediately ABOVE `_check_verification_git_reality` (before line 305):

```python
def _merged_dispatch_times(dispatch_log_path):
    # type: (str) -> dict
    """Merge implementer dispatch timestamps from archived logs + the live log.

    Reads reports/archive-*/.dispatch-log (lexicographic = module order) FIRST,
    then the live dispatch log LAST, so a re-dispatched task id's latest
    timestamp wins (preserves Check 9's latest-wins re-dispatch semantics).
    Parses ONLY `type=implementer` lines — the shared dispatch-log contract with
    N26: type=fix / type=fix-unattributed lines never open a verification
    window. One of the 5 documented archive-aware lookups (see CLAUDE.md).
    """
    times = {}  # type: dict
    reports_dir = os.path.dirname(dispatch_log_path)
    log_re = re.compile(
        r"(\S+)\s+DISPATCH\s+implementer\s+task=(\d+)\s+type=implementer"
    )

    def _ingest(path):
        if not os.path.isfile(path):
            return
        try:
            with open(path) as f:
                for line in f:
                    m = log_re.match(line)
                    if m:
                        times[int(m.group(2))] = m.group(1)
        except OSError:
            pass

    for archive_log in sorted(
        glob.glob(os.path.join(reports_dir, "archive-*", ".dispatch-log"))
    ):
        _ingest(archive_log)
    _ingest(dispatch_log_path)
    return times
```

- [x] **Step 4: Rewire `_check_verification_git_reality`** — replace the guard + inline read (lines 317-329) with a call to the merged helper. The OLD code is:

```python
    if not verification_ids or not os.path.isfile(dispatch_log_path):
        return []

    dispatch_times = {}  # type: dict
    with open(dispatch_log_path) as f:
        for line in f:
            # Format mirrors the writer in sdd-pre-dispatch-hook.sh (~lines 191/194); keep in sync.
            m = re.match(
                r"(\S+)\s+DISPATCH\s+implementer\s+task=(\d+)\s+type=implementer",
                line,
            )
            if m:
                dispatch_times[int(m.group(2))] = m.group(1)
```

Replace it with:

```python
    if not verification_ids:
        return []

    # Archive-aware (N27): merge archived dispatch logs + the live log. The
    # parser inside _merged_dispatch_times matches ONLY type=implementer lines,
    # so N26's type=fix / type=fix-unattributed entries never open a window.
    # (Writer: sdd-pre-dispatch-hook.sh Stage 2; keep the format in sync.)
    dispatch_times = _merged_dispatch_times(dispatch_log_path)
```

Everything below (`findings = []`, `sorted_tasks`, the window/git-log loop) is unchanged.

- [x] **Step 5: Run to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py -v`
Expected: PASS (new class + pre-existing `TestGitRealityCheck` — `test_missing_dispatch_log_passes` still returns `[]` because the merged map is empty for a nonexistent path).

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_pre_completion_gates.py
git commit -m "feat(checkpoint): N27 — Check 9 archive-aware dispatch-log merge"
```

---

### Task 3: N26 — dispatch-log classification + Check 3b allowlist + baseline recapture

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (Stage 0 insertion, Stage 1 guard, Stage 2 log-write guard, Stage 3 fallback, Check 3b allowlist line 404, additionalContext)
- Create: `skills/subagent-driven-development/references/dispatch-markers.md`
- Modify: `tests/ARaymond-hook-baseline/baseline.txt` (re-capture — SAME commit as the hook edit)
- Test: `tests/unit/test_sdd_classification.py`

**Pattern References:**
- `tests/unit/test_sdd_classification.py` — `setup_sdd_workspace`/`setup_full_sdd_workspace`, `make_hook_input`, `run_hook`, dispatch-log assertions.

**Context (O1, O2 resolved in `plan.md`):** The hook's 3-stage pipeline (reviewer → implementer → passthrough) cannot attribute review-driven FIX dispatches or partner RE-review rounds (the three live sprint-3 trace-audit shapes had no derivable task id and one matched the reviewer stage). N26a adds a deterministic **Stage 0** (BEFORE reviewer detection) keyed on an explicit marker, plus a **Stage-3 unattributed fallback**. N26b adds the three gate-required artifact names to the Check 3b allowlist. **Load-bearing invariant:** a marked fix emits ONLY `type=fix` and skips Stage 2's `type=implementer` write (else it moves task N's Check 9 window).

- [x] **Step 1: Write the failing tests** in `tests/unit/test_sdd_classification.py` (add at the end; reuse `setup_sdd_workspace`/`setup_full_sdd_workspace`/`make_hook_input`/`run_hook` as the existing tests do):

```python
def _read_log(tmpdir):
    log_path = os.path.join(tmpdir, "reports", ".dispatch-log")
    if not os.path.exists(log_path):
        return ""
    with open(log_path) as f:
        return f.read()


def test_marked_fix_logs_type_fix_not_implementer(tmp_path):
    # N26a: [task N fix] → type=fix line, and NEVER a type=implementer line.
    tmpdir = str(tmp_path)
    setup_full_sdd_workspace(tmpdir, task_count=5)
    run_hook(make_hook_input(
        description="[task 3 fix] fix the parser regression",
        prompt="", cwd=tmpdir))
    log = _read_log(tmpdir)
    assert "task=3 type=fix" in log
    assert "task=3 type=implementer" not in log  # must NOT move Check 9 window


def test_marked_rereview_logs_reviewer_passthrough(tmp_path):
    # N26a: [task N re-review:quality] → reviewer log entry + passthrough (rc 0).
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=5)
    result = run_hook(make_hook_input(
        description="[task 4 re-review:quality] re-review after fix",
        prompt="", cwd=tmpdir))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "task=4 type=quality-review" in _read_log(tmpdir)


def test_markerless_fix_logs_unattributed(tmp_path):
    # N26a Stage-3 fallback: markerless fix → fix-unattributed, passthrough.
    tmpdir = str(tmp_path)
    setup_sdd_workspace(tmpdir, task_count=5)
    result = run_hook(make_hook_input(
        description="fix the broken merge logic", prompt="", cwd=tmpdir))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "type=fix-unattributed" in _read_log(tmpdir)


def test_check3b_allows_gate_artifact_names(tmp_path):
    # N26b: honesty-check-*, execution-trace-audit.md, final-code-review.md
    # must not trip Check 3b non-standard-naming.
    tmpdir = str(tmp_path)
    setup_full_sdd_workspace(tmpdir, task_count=5)
    reports = os.path.join(tmpdir, "reports")
    open(os.path.join(reports, "final-code-review.md"), "w").write("x" * 60)
    open(os.path.join(reports, "execution-trace-audit.md"), "w").write("x" * 60)
    open(os.path.join(reports, "honesty-check-2026.md"), "w").write("x" * 60)
    result = run_hook(make_hook_input(
        description="implement task 2", prompt="", cwd=tmpdir))
    assert "non-standard naming" not in result.stderr
```

> NOTE: `setup_full_sdd_workspace` stages prior-task reports so a task-N dispatch isn't blocked by unrelated Check-4 gates (mirror existing usage). The marked-fix test asserts log CONTENT (written in Stage 0 before enforcement), so it holds regardless of return code.

- [x] **Step 2: Run to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v`
Expected: FAIL — no Stage 0 (no `type=fix`), no Stage-3 fallback (`type=fix-unattributed` absent), Check 3b blocks the gate-artifact names.

- [x] **Step 3: Insert Stage 0** in `sdd-pre-dispatch-hook.sh` between the variable declarations (after line 151, the `TASK_NUMBER=""` line) and `# Stage 1` (line 153). Add:

```bash
# Stage 0: fix / re-review marker (N26a). Runs BEFORE reviewer detection (a
# fix-REVIEW description contains "review" and would be consumed by Stage 1).
# Markers: see references/dispatch-markers.md.
MARKED_FIX=false
if echo "$DESCRIPTION" | grep -qiE '\[task[[:space:]]+[0-9]+[[:space:]]+re-review:(spec|quality|partner)\]'; then
  mkdir -p "$(dirname "$DISPATCH_LOG")"
  touch "$DISPATCH_LOG"
  RR_TASK=$(echo "$DESCRIPTION" | grep -oiE 'task[[:space:]]*[0-9]+' | grep -oE '[0-9]+' | head -1)
  RR_KIND=$(echo "$DESCRIPTION" | grep -oiE 're-review:(spec|quality|partner)' | grep -oiE '(spec|quality|partner)' | head -1)
  if [ -n "$RR_TASK" ] && [ -n "$RR_KIND" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH reviewer task=$RR_TASK type=${RR_KIND}-review" >> "$DISPATCH_LOG"
  fi
  exit 0
elif echo "$DESCRIPTION" | grep -qiE '\[task[[:space:]]+[0-9]+[[:space:]]+fix\]'; then
  # Marked fix → log type=fix ONLY (skip Stage 2's type=implementer write so
  # Check 9's window isn't moved — :324); then take the implementer path.
  mkdir -p "$(dirname "$DISPATCH_LOG")"
  touch "$DISPATCH_LOG"
  TASK_NUMBER=$(echo "$DESCRIPTION" | grep -oiE 'task[[:space:]]*[0-9]+' | grep -oE '[0-9]+' | head -1)
  if [ -n "$TASK_NUMBER" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH fix task=$TASK_NUMBER type=fix" >> "$DISPATCH_LOG"
  fi
  IS_IMPLEMENTER=true
  MARKED_FIX=true
fi
```

- [x] **Step 4: Guard Stage 1** so a marked fix is not re-classified as a reviewer. On the Stage-1 condition (line 154), insert `[ "$MARKED_FIX" = false ] && ` right after `if ` so it reads:

```bash
if [ "$MARKED_FIX" = false ] && echo "$DESCRIPTION" | grep -qiE '(review|spec.compliance|code.quality|spec.review|quality.review|trace.audit|partner.review)'; then
```

- [x] **Step 5: Guard the Stage-2 implementer log write** so a marked fix does not also write a `type=implementer` line. On the condition at line 197, insert `[ "$MARKED_FIX" = false ] && ` before the `[ -n "$TASK_NUMBER" ]` clause so it reads:

```bash
if [ "$IS_IMPLEMENTER" = true ] && [ "$MARKED_FIX" = false ] && [ -n "$TASK_NUMBER" ]; then
```

- [x] **Step 6: Add the Stage-3 unattributed fallback.** Replace the Stage-3 block (lines 206-209):

```bash
# Stage 3: Not a reviewer, not an implementer → allow (Explore, Plan, ad-hoc).
if [ "$IS_IMPLEMENTER" = false ]; then
  exit 0
fi
```

with:

```bash
# Stage 3: Not a reviewer, not an implementer → allow (Explore, Plan, ad-hoc).
# N26a fallback: a markerless dispatch whose description matches the fix
# heuristic logs an unattributed fix line — tamper-evidence that a fix cycle
# happened, with no enforcement change and no (unknowable) task attribution.
if [ "$IS_IMPLEMENTER" = false ]; then
  if echo "$DESCRIPTION" | grep -qiE '\bfix\b|remediat'; then
    mkdir -p "$(dirname "$DISPATCH_LOG")"
    touch "$DISPATCH_LOG"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DISPATCH adhoc type=fix-unattributed" >> "$DISPATCH_LOG"
  fi
  exit 0
fi
```

- [x] **Step 7: Extend the Check 3b allowlist** (N26b). On line 404, add `|honesty-check-|execution-trace-audit\.md|final-code-review\.md` to the alternation so it reads:

```bash
      if ! echo "$BASENAME" | grep -qE '^(task-[0-9]+-|pre-execution-audit|context-summary|partner-review|checkpoint-pre-dispatch|honesty-check-|execution-trace-audit\.md|final-code-review\.md)'; then
```

- [x] **Step 8: Echo the marker convention in additionalContext.** After the `CONTEXT="$CONTEXT | $PROCESS_CONTRACT"` line (~line 772; the anchor text is unique), add:

```bash
CONTEXT="$CONTEXT | FIX/RE-REVIEW MARKERS: prefix a review-driven fix dispatch with [task N fix] and a re-review round with [task N re-review:{spec|quality|partner}] so the provenance log attributes the fix cycle (see references/dispatch-markers.md)."
```

- [x] **Step 9: Create `skills/subagent-driven-development/references/dispatch-markers.md`** (controller-side doc; zero SKILL.md word cost):

```markdown
# Dispatch Markers (provenance attribution)

The pre-dispatch hook attributes review-driven fix cycles to the dispatch log
when you prefix the Agent dispatch **description** with a marker:

| Marker | Hook behavior | Log line |
|--------|---------------|----------|
| `[task N fix]` | Implementer enforcement path (no gate relaxation); logs the fix WITHOUT a `type=implementer` line | `<ISO> DISPATCH fix task=N type=fix` |
| `[task N re-review:{spec\|quality\|partner}]` | Reviewer passthrough | `<ISO> DISPATCH reviewer task=N type={spec\|quality\|partner}-review` |

Check 9 (git-reality) opens a verification window only on `type=implementer`
lines, so a `[task N fix]` must NOT log `type=implementer` (it would move task
N's window). A markerless dispatch matching `\bfix\b|remediat` is recorded as
`DISPATCH adhoc type=fix-unattributed` (tamper-evidence) but is not attributed.
```

- [x] **Step 10: Run the hook tests**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py -v`
Expected: PASS (new tests + all pre-existing classification tests — Stage 0 only fires on explicit markers, so unmarked reviewer/implementer/ad-hoc behavior is unchanged).

- [x] **Step 11: Re-capture the hook baseline** (D18 — SAME commit as the hook edit):

Run: `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture` then `bash tests/ARaymond-hook-baseline/check-hooks.sh` to verify no unexpected drift.
Expected: PASS (hashes match the freshly captured baseline; settings.json registration unchanged).

- [x] **Step 12: Commit** (hook + new doc + baseline together):

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh \
        skills/subagent-driven-development/references/dispatch-markers.md \
        tests/ARaymond-hook-baseline/baseline.txt \
        tests/unit/test_sdd_classification.py
git commit -m "feat(hook): N26 — fix/re-review dispatch markers + Check 3b allowlist (baseline recaptured)"
```

---

### Task 4: N19 — transition `module.file` AND-exists fallback + cleanup

**Files:**
- Modify: `skills/subagent-driven-development/scripts/transition-module.py` (`validate_module_completion`, lines 107-116)
- Test: `tests/unit/test_transition_module.py`

**Pattern References:**
- `tests/unit/test_transition_module.py` — manifest-workspace + `validate_module_completion` test harness.

**Context:** Today `validate_module_completion` uses `if module.file:` (truthiness only). A SET-but-MISSING `module.file` yields an empty verification-exemption set (fail-closed), diverging from the hook, which checks `-n` AND `-f` and falls back to the main plan. N19 adopts the hook's stricter semantic, removes the dead `verif_ids = set()` initializer (both branches reassign it), and replaces the "hook lines ~294-299" comment with a construct name.

- [x] **Step 1: Write the failing test** in `tests/unit/test_transition_module.py` (mirror the existing manifest-workspace setup; a verification task declared in the MAIN plan must be exempted when `module.file` is set but missing):

```python
def test_set_but_missing_module_file_falls_back_to_main_plan(tmp_path):
    """N19: module.file set but absent on disk → fall back to the main plan for
    verification-id lookup (matches the hook's -n + -f semantic)."""
    # Build a manifest workspace where the completing module's file is declared
    # but does NOT exist, and the MAIN plan declares task 1 as verification.
    # (Mirror the existing manifest/workspace builder in this test module.)
    ...
    # The completing module has task_ids [1] and module.file = "module-1.md"
    # which is NOT written to disk. The main plan frontmatter declares:
    #   tasks: [{id: 1, task_type: verification}]
    # Stage only task 1's implementer report (no spec/quality reviews).
    errors = _transition.validate_module_completion(manifest, "Core", git_root)
    # Task 1 is verification → exempt from spec/quality/provenance, so the only
    # required artifact (implementer report) is present → no errors.
    assert errors == [], f"verification task should be exempt via main-plan fallback: {errors}"
```

> NOTE for the implementer: model the manifest/workspace construction on the existing tests in this file (they already build an `SddSession` and a git_root tmp workspace). The key fixture properties: `module.file = "module-1.md"` (a filename that is never created), and the MAIN `plan_file` frontmatter declares task 1 `task_type: verification`. Today the `if module.file:` branch reads the missing module file → empty `verif_ids` → task 1 is NOT exempt → the test FAILs (missing spec/quality review errors).

- [x] **Step 2: Run to verify it fails**

Run: `.venv/bin/python3 -m pytest tests/unit/test_transition_module.py -v`
Expected: FAIL — the set-but-missing `module.file` yields an empty exemption set, so task 1's missing spec/quality reviews are reported as errors.

- [x] **Step 3: Apply the N19 fix.** Replace lines 107-116 (the comment + dead initializer + truthiness branch):

```python
    # Per-task verification exemption (mirrors sdd-pre-dispatch-hook.sh): read the
    # completing module's own plan file for task_type declarations. N17: when the
    # module has no per-module file, fall back to the main plan (hook lines ~294-299).
    verif_ids: set = set()
    if module.file:
        module_plan = os.path.join(git_root, manifest.paths.feature_dir, module.file)
        verif_ids = _verification_task_ids_from_file(module_plan)
    else:
        main_plan = os.path.join(git_root, manifest.plan_file)
        verif_ids = _verification_task_ids_from_file(main_plan)
```

with:

```python
    # Per-task verification exemption (mirrors get_task_type's EFFECTIVE_PLAN_FILE
    # resolution in sdd-pre-dispatch-hook.sh): use the completing module's own
    # plan file only when module.file is set AND exists on disk (the hook's -n +
    # -f semantic); otherwise fall back to the main plan. N17/N19.
    module_plan = ""
    if module.file:
        module_plan = os.path.join(git_root, manifest.paths.feature_dir, module.file)
    if module_plan and os.path.isfile(module_plan):
        verif_ids = _verification_task_ids_from_file(module_plan)
    else:
        main_plan = os.path.join(git_root, manifest.plan_file)
        verif_ids = _verification_task_ids_from_file(main_plan)
```

(The dead `verif_ids: set = set()` initializer is removed — every path assigns `verif_ids`.)

- [x] **Step 4: Run to verify it passes**

Run: `.venv/bin/python3 -m pytest tests/unit/test_transition_module.py -v`
Expected: PASS (new test + all pre-existing transition tests — a SET-and-PRESENT `module.file` still reads the module plan; only the set-but-missing path changes).

- [x] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/scripts/transition-module.py tests/unit/test_transition_module.py
git commit -m "fix(transition): N19 — module.file AND-exists fallback + dead-code cleanup"
```

## Acceptance Criteria (Module 1)

- [x] `_review_tiers_per_task` returns archived + live entries keyed by task id (live wins); single-module workspaces unchanged.
- [x] `_merged_dispatch_times` merges archived + live logs (live overwrites) and ignores `type=fix`/`type=fix-unattributed`; Check 9 FAILs on the archived-window file-modification fixture.
- [x] Marked `[task N fix]` logs `type=fix` and NEVER `type=implementer`; `[task N re-review:<kind>]` logs a reviewer entry + passes through; markerless fix logs `type=fix-unattributed`; gate-artifact names no longer trip Check 3b.
- [x] Hook baseline re-captured in the same commit as the hook edit.
- [x] `validate_module_completion` falls back to the main plan when `module.file` is set-but-missing; dead initializer removed.
- [x] Full unit suite green: `.venv/bin/python3 -m pytest tests/unit/ -v`.
- [x] Module 1 transitions to Module 2 via `transition-module.py` before Module 2 begins.
