---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: null
integration_test:
  path: tests/integration/sdd-e2e-test.sh
shared_constants: []
pattern_references:
  - name: "fence-tests"
    source_files: ["tests/unit/test_fence_aware_parsing.py"]
    reason: "_unfenced_content characterization + validate-plan fence tests; _load_script importlib loader (hoisted in Task 5)"
  - name: "c2-tests"
    source_files: ["tests/unit/test_c2_integration_gate.py"]
    reason: "validate-plan risk-surface WARNING tests + Check 10 git-repo harness (_setup_repo/_git/_run_checkpoint); _load_script loader"
  - name: "checkpoint-tests"
    source_files: ["tests/unit/test_pre_completion_gates.py"]
    reason: "Check 10 / git-reality test patterns and _init_temp_git_repo helpers"
  - name: "e2e-step-pattern"
    source_files: ["tests/integration/sdd-e2e-test.sh"]
    reason: "Step 5 transition + Step 11 Check-10 assertion patterns to mirror for the new archive-aware Step 12"
  - name: "n6-exemplar"
    source_files: ["skills/subagent-driven-development/SKILL.md"]
    reason: "Context Budget Management section (lines 257-265) is the C6(a) 'hook enforces this automatically' exemplar to mirror for N6"
tasks:
  - id: 5
    title: "N20: fence-helper tilde + unclosed-fence WARNING + _load_script hoist"
    pattern_references: ["fence-tests"]
  - id: 6
    title: "N22: risk-surface stem patterns + unfenced scan"
    depends_on: [5]
    pattern_references: ["c2-tests"]
  - id: 7
    title: "N25c: _git_run subprocess consolidation (SSOT)"
    depends_on: [6]
    pattern_references: ["c2-tests", "checkpoint-tests"]
  - id: 8
    title: "N25a: Check 10 feature-window fallback"
    depends_on: [7]
    pattern_references: ["c2-tests", "checkpoint-tests"]
  - id: 9
    title: "N25b+d+f: frontmatter line-anchored scan + directory/malformed diagnostics"
    depends_on: [8]
    pattern_references: ["c2-tests"]
  - id: 10
    title: "N6: SDD SKILL.md hook-enforces-this framing pass"
    depends_on: [9]
    review_tier: minimum
    pattern_references: ["n6-exemplar"]
  - id: 11
    title: "N8: intent-based F6 regression check"
    depends_on: [10]
  - id: 12
    title: "Archive-awareness inventory docs (5 sites)"
    depends_on: [11]
    review_tier: minimum
  - id: 13
    title: "Verification: archive-awareness inventory audit"
    depends_on: [12]
    task_type: verification
    review_tier: minimum
  - id: 14
    title: "e2e Step 12 (archive-aware proof) + BACKLOG flips + final suites"
    depends_on: [13]
    pattern_references: ["e2e-step-pattern"]
---

# Module 2 — Calibration & Hygiene

> **For agentic workers:** This is a module of a larger plan. Invoke `superpowers:subagent-driven-development` before implementing. See `plan.md` for the parent coordination document and the resolved O1–O4 decisions. Module 1 MUST be complete and transitioned before this module begins.

**Goal:** Ship the deferred calibration batch: fence-helper edge cases (N20), risk-surface stemming (N22, depends on N20's helper), the Check-10 follow-up batch (N25 a–d,f), two doc-only passes (N6 framing, the 5-site inventory), the intent-based F6 check (N8), the live non-last verification task, and the in-sprint e2e proof of archive-aware aggregates — then flip the BACKLOG rows.

**Source Contracts:** None

No external contract; no Task 0.

**Contract Constraints:** None external. N22 (Task 6) depends on N20 (Task 5) because the risk-surface scan consumes the fence helper `_unfenced_content`. N25's three tasks (7 = `_git_run` SSOT, 8 = feature-window fallback, 9 = frontmatter scan + diagnostics) all edit `controller-checkpoint.py` and are serialized.

**Shared Constants:** None. (Task 8 introduces a module-level `_EMPTY_TREE_SHA` constant local to `controller-checkpoint.py`; it is not shared across tasks.)

**Pattern References:**
- `tests/unit/test_fence_aware_parsing.py` — `_unfenced_content` characterization tests; the `_load_script` loader hoisted in Task 5.
- `tests/unit/test_c2_integration_gate.py` — risk-surface WARNING tests + the `TestCheck10*` git-repo harness (`_setup_repo`/`_git`/`_run_checkpoint`).
- `tests/unit/test_pre_completion_gates.py` — `_init_temp_git_repo`/`_commit_file_at`.
- `tests/integration/sdd-e2e-test.sh:130-162` (Step 5 transition) + `:390-444` (Step 11 assertion).
- `skills/subagent-driven-development/SKILL.md:257-265` — the C6(a) "hook enforces this automatically — there is no manual step" exemplar for N6.

**Feature Archetype:** Extension (calibration + diagnostics; N25c consolidates git subprocesses with all 4 callers audited per O4).

## Code Footprint

| Category | File / Function | Action | Dependencies to Verify |
|----------|-----------------|--------|------------------------|
| Modified | `_report_utils.py` :: `_unfenced_content` (+ new `_fence_marker`, `ends_in_open_fence`) | Extend | Consumers validate-plan.py, controller-checkpoint.py — behavior pinned by characterization tests |
| Modified | `validate-plan.py` :: import line, new `check_unclosed_fence`, `_C2_RISK_PATTERNS`, `check_integration_test_risk` | Extend | Imports from `_report_utils` |
| Modified | `controller-checkpoint.py` :: new `_git_run`/`_merge_base_is_head`/`_feature_window_base`, Check 10 block, `_resolve_base_ref`/`_in_changeset`/`_check_verification_git_reality` git calls, `_integration_test_paths`/`_task_ids_where` frontmatter scan | Extend/Refactor | O4: `_resolve_git_root` deliberately excluded from `_git_run` |
| Modified | `skills/subagent-driven-development/SKILL.md` (N6 framing, 3 sites) | Extend (doc) | Net `wc -w` MUST NOT increase |
| Modified | `tests/ARaymond-skill-regression/validate-all-skills.py` :: F6 (line 569) | Extend | Scope stays `writing-plans/SKILL.md` ONLY |
| Modified | `CLAUDE.md` (:206), `docs/ARaymond-customization-manifest.md` (:329) | Extend (doc) | Inventory "3 → 5 sites" at BOTH |
| Modified | `tests/integration/sdd-e2e-test.sh` (new Step 12), `docs/process-improvement-findings/BACKLOG.md` | Extend | Final echo "12 → 13 steps" |
| Modified | Tests: `sdd_test_helpers.py` (+`_load_script`), `test_fence_aware_parsing.py`, `test_c2_integration_gate.py` | Extend | `_load_script` single-source |

## File Map

- `_report_utils.py` — Task 5
- `validate-plan.py` — Tasks 5 (WARNING), 6 (risk patterns)
- `controller-checkpoint.py` — Tasks 7 (git SSOT), 8 (feature-window), 9 (frontmatter scan + diagnostics)
- `SDD SKILL.md` — Task 10
- `validate-all-skills.py` — Task 11
- `CLAUDE.md`, `docs/ARaymond-customization-manifest.md` — Task 12
- (no writes) — Task 13 (verification)
- `tests/integration/sdd-e2e-test.sh`, `BACKLOG.md` — Task 14
- Tests: `sdd_test_helpers.py`, `test_fence_aware_parsing.py`, `test_c2_integration_gate.py`

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| 5 | `_report_utils.py`, `validate-plan.py` (WARNING), `sdd_test_helpers.py`, `test_fence_aware_parsing.py` | — | 4 (M1) |
| 6 | `validate-plan.py` (`_C2_RISK_PATTERNS`), `test_c2_integration_gate.py` | Task 5's `_unfenced_content` | 5 |
| 7 | `controller-checkpoint.py` (`_git_run` SSOT), `test_c2_integration_gate.py` | the 3 git call sites | 6 |
| 8 | `controller-checkpoint.py` (Check 10 feature-window), `test_c2_integration_gate.py` | Task 7's `_git_run` | 7 |
| 9 | `controller-checkpoint.py` (frontmatter scan + diagnostics), `test_c2_integration_gate.py` | Task 8's edits | 8 |
| 10 | `SDD SKILL.md` | `references/context-health-protocol.md` | 9 |
| 11 | `validate-all-skills.py` | `writing-plans/SKILL.md` | 10 |
| 12 | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md` | controller-checkpoint.py, hook | 11 |
| 13 | (none — `task_type: verification`) | code + Task 12 docs | 12 |
| 14 | `tests/integration/sdd-e2e-test.sh`, `BACKLOG.md` | all | 13 |

All tasks serialized. Tasks 5/6 share `validate-plan.py`; Tasks 7/8/9 share `controller-checkpoint.py` — `depends_on` enforces ordering.

---

### Task 5: N20 — fence-helper tilde + unclosed-fence WARNING + `_load_script` hoist

**Files:**
- Modify: `skills/subagent-driven-development/scripts/_report_utils.py` (`_unfenced_content`, lines 61-82; add `_fence_marker`, `ends_in_open_fence`)
- Modify: `skills/subagent-driven-development/scripts/validate-plan.py` (import line 31; add `check_unclosed_fence`; wire into main flow ~705)
- Modify: `tests/unit/sdd_test_helpers.py` (hoist `_load_script`, D15)
- Modify: `tests/unit/test_fence_aware_parsing.py` (import hoisted `_load_script`; add characterization tests)

**Context:** `_unfenced_content` recognizes only ` ``` ` fences and toggles on any backtick fence. N20 adds `~~~` support with own-marker-type closing, PINS the unclosed-fence-at-EOF blank-to-EOF behavior (CommonMark-consistent) with a characterization test, and adds an advisory `validate-plan.py` WARNING when a plan ends inside an unclosed fence. D15 hoists the duplicated `_load_script` importlib loader into `sdd_test_helpers.py` (this task touches one of the two duplicating files).

- [x] **Step 1: Write failing characterization tests** in `tests/unit/test_fence_aware_parsing.py` (add a new class; the `_H` self-hosting guard already exists):

```python
class TestFenceHelperEdges:
    """N20: tilde fences, own-marker-type closing, unclosed-at-EOF, open-fence detector."""

    def test_tilde_fence_blanked(self):
        from _report_utils import _unfenced_content
        text = "before\n~~~\nfenced line\n~~~\nafter\n"
        out = _unfenced_content(text)
        assert "fenced line" not in out
        assert "before" in out and "after" in out

    def test_backtick_not_closed_by_tilde(self):
        from _report_utils import _unfenced_content
        # A ~~~ line inside a ``` fence is content, not a close.
        text = "```\nstill fenced\n~~~\nstill fenced too\n```\nout\n"
        out = _unfenced_content(text)
        assert "still fenced" not in out
        assert "still fenced too" not in out
        assert "out" in out

    def test_unclosed_fence_blanks_to_eof(self):
        from _report_utils import _unfenced_content
        text = "head\n```\nshadowed 1\nshadowed 2\n"  # no closing fence
        out = _unfenced_content(text)
        assert "head" in out
        assert "shadowed 1" not in out and "shadowed 2" not in out

    def test_ends_in_open_fence_true(self):
        from _report_utils import ends_in_open_fence
        assert ends_in_open_fence("x\n```\nunclosed\n") is True
        assert ends_in_open_fence("x\n~~~\nunclosed\n") is True

    def test_ends_in_open_fence_false(self):
        from _report_utils import ends_in_open_fence
        assert ends_in_open_fence("x\n```\nclosed\n```\n") is False
        assert ends_in_open_fence("no fences here\n") is False
```

- [x] **Step 2: Run to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py::TestFenceHelperEdges -v`
Expected: FAIL — `~~~` not recognized; `ends_in_open_fence` does not exist.

- [x] **Step 3: Rewrite `_unfenced_content`** and add `_fence_marker` + `ends_in_open_fence` in `_report_utils.py` (replace lines 61-82). Add `import re` is already present (line 14):

```python
_FENCE_RE = re.compile(r"^([`~]{3,})")


def _fence_marker(line):
    # type: (str) -> Optional[str]   # 3.9-safe type comment (PEP-604 unions fail regression Category-8)
    """Return the fence marker char ('`' or '~') if the line is a fence
    delimiter (>=3 of the same char after stripping), else None."""
    stripped = line.strip()
    return stripped[0] if _FENCE_RE.match(stripped) else None


def _unfenced_content(text: str) -> str:
    """Return text with lines inside code fences replaced by blank lines.

    Recognizes both ``` and ~~~ fences (N20). A fence closes only on its OWN
    marker type — a ~~~ line inside a ``` fence is content, not a close.
    Preserves line count so line-index-based logic (span measurement, header
    positions) stays valid. An unclosed fence at EOF blanks to end-of-document
    (CommonMark: an unclosed code block runs to the end) — pinned by a
    characterization test.

    Single source of truth — imported by validate-plan.py and
    controller-checkpoint.py for fence-aware task-header parsing (N5).
    """
    result = []
    fence_char = None  # None = outside a fence; '`' or '~' = inside that fence
    for line in text.splitlines(keepends=True):
        marker = _fence_marker(line)
        if fence_char is None:
            if marker is not None:
                fence_char = marker
                result.append("\n")
            else:
                result.append(line)
        else:
            if marker == fence_char:  # only the same marker type closes
                fence_char = None
            result.append("\n")
    return "".join(result)


def ends_in_open_fence(text: str) -> bool:
    """Return True if text ends while still inside an unclosed code fence (N20).

    Shares fence semantics with _unfenced_content (same _fence_marker primitive).
    """
    fence_char = None
    for line in text.splitlines(keepends=True):
        marker = _fence_marker(line)
        if fence_char is None:
            if marker is not None:
                fence_char = marker
        elif marker == fence_char:
            fence_char = None
    return fence_char is not None
```

- [x] **Step 4: Add the validate-plan WARNING.** In `validate-plan.py`, extend the import on line 31:

```python
from _report_utils import _unfenced_content, ends_in_open_fence  # noqa: E402  (single source of truth)
```

Add a check function near `check_integration_test_risk` (~line 426):

```python
def check_unclosed_fence(content: str) -> List[str]:
    """Advisory WARNING when a plan ends inside an unclosed code fence (N20).

    A fence-shadowed tail hides task headers and checkboxes from the validator
    AND from all_tasks_have_reports (which then silently skips those tasks).
    """
    if ends_in_open_fence(content):
        return [
            "unclosed_fence: Plan ends inside an unclosed code fence (``` or ~~~). "
            "Content after the opening fence is invisible to the validator and to "
            "all_tasks_have_reports — close the fence."
        ]
    return []
```

Wire it into the main validation flow next to the existing `check_integration_test_risk` call (~line 705):

```python
    fence_warnings = check_unclosed_fence(content)
    for w in fence_warnings:
        warnings.append(w)
    if fence_warnings:
        sections["unclosed_fence"] = {"status": "WARNING", "detail": fence_warnings[0]}
```

- [x] **Step 5: Hoist `_load_script` into `sdd_test_helpers.py`** (D15). Add near the top (after the existing `import` block, ~line 11):

```python
import importlib.util

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_script(name, filename):
    """Load a hyphenated SDD script (validate-plan.py, controller-checkpoint.py)
    as an importable module. Single source of truth (D15) — previously
    duplicated in test_fence_aware_parsing.py and test_c2_integration_gate.py."""
    path = os.path.join(
        ROOT, "skills", "subagent-driven-development", "scripts", filename
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
```

In `test_fence_aware_parsing.py`, replace the local `ROOT`/`_load_script` definition (lines 11-19) with:

```python
from sdd_test_helpers import _load_script
```

(Leave the `_vp`/`_ckpt` assignments on lines 22-23 unchanged — they call the imported `_load_script`.)

- [x] **Step 6: Run all touched suites**

Run: `.venv/bin/python3 -m pytest tests/unit/test_fence_aware_parsing.py tests/unit/test_validate_plan.py -v`
Expected: PASS (new characterization tests + pre-existing fence-aware tests, which exercise the unchanged backtick path).

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/_report_utils.py \
        skills/subagent-driven-development/scripts/validate-plan.py \
        tests/unit/sdd_test_helpers.py tests/unit/test_fence_aware_parsing.py
git commit -m "feat(report-utils): N20 — tilde fences + unclosed-fence WARNING + _load_script hoist (D15)"
```

---

### Task 6: N22 — risk-surface stem patterns + unfenced scan

**Files:**
- Modify: `skills/subagent-driven-development/scripts/validate-plan.py` (`_C2_RISK_PATTERNS` line 420; `check_integration_test_risk` line 435)
- Test: `tests/unit/test_c2_integration_gate.py`

**Pattern References:**
- `tests/unit/test_c2_integration_gate.py` — risk-surface WARNING tests (RISK_PLAN fixture); replace its local `_load_script` with the hoisted import.

**Context:** `_C2_RISK_PATTERNS` is singular-only (`migrations`/`caches`/`routers`/`authentication` all miss; `\bauth\b` excludes `authentication`) and scans raw content, so plans QUOTING keywords in fences self-warn. N22 moves to stem patterns and scans `_unfenced_content(content)` (Task 5's helper). Ordered AFTER N20 (the scan consumes the fence helper).

- [x] **Step 1: Write the failing tests** in `tests/unit/test_c2_integration_gate.py`. First replace the file's local `_load_script` (lines 18-25) and `ROOT` with `from sdd_test_helpers import _load_script` (D15), then add:

```python
def _warns_risk(content):
    """True if validate-plan emits the integration_test_risk_surface WARNING."""
    return any(
        "integration_test_risk_surface" in w
        for w in _vp.check_integration_test_risk(content, {})
    )


class TestRiskSurfaceStemming:
    def test_inflected_forms_match(self):
        # Words the spec's stem patterns (D8) must match. NOTE: "security" matches
        # securit\w* but "securing" does NOT (stem is securit, not secur) — keep
        # test words aligned to the spec's chosen stems.
        for kw in ("migrations", "caches", "routers", "authentication", "security"):
            body = f"---\nschema_version: 1\n---\n# Plan\nThis touches {kw} logic.\n"
            assert _warns_risk(body), f"{kw} should trigger the risk WARNING"

    def test_fenced_only_keyword_does_not_warn(self):
        body = "---\nschema_version: 1\n---\n# Plan\n```\nauth migration router\n```\nNo risk prose.\n"
        assert not _warns_risk(body), "fence-only keywords must not warn"

    def test_declared_integration_test_suppresses(self):
        body = "# Plan\nTouches authentication.\n"
        assert _vp.check_integration_test_risk(body, {"integration_test": {"path": "x"}}) == []
```

- [x] **Step 2: Run to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestRiskSurfaceStemming -v`
Expected: FAIL — `authentication`/`migrations`/etc. don't match the singular patterns; fence-only keywords warn (raw-content scan).

- [x] **Step 3: Replace `_C2_RISK_PATTERNS`** (lines 420-423):

```python
_C2_RISK_PATTERNS = re.compile(
    r"\b(?:auth\w*|migrat\w*|rout(?:e|er)\w*|cach\w*|middleware\w*|cors\b|securit\w*)",
    re.IGNORECASE,
)
```

- [x] **Step 4: Scan unfenced content.** In `check_integration_test_risk`, change line 435 from:

```python
    if _C2_RISK_PATTERNS.search(content):
```

to:

```python
    if _C2_RISK_PATTERNS.search(_unfenced_content(content)):
```

(`_unfenced_content` is imported via Task 5's extended import on line 31.)

- [x] **Step 5: Run to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py -v`
Expected: PASS (new class + pre-existing C2 tests; the existing RISK_PLAN fixture still warns).

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/validate-plan.py tests/unit/test_c2_integration_gate.py
git commit -m "feat(validate-plan): N22 — risk-surface stem patterns + unfenced scan"
```

---

### Task 7: N25c — `_git_run` subprocess consolidation (SSOT)

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py` (add `_git_run`; refactor the 3 git call sites)
- Test: `tests/unit/test_c2_integration_gate.py`

**Pattern References:**
- `tests/unit/test_pre_completion_gates.py` — `_init_temp_git_repo` / git-reality test patterns.

**Context (O4 resolved in `plan.md`):** Three git call sites share identical `timeout=10` + swallow-`(TimeoutExpired, OSError)` semantics: the inline call in `_check_verification_git_reality` (~:353), `_resolve_base_ref`'s inner `_git` (~:454), and `_in_changeset`'s inner `_git` (~:505). N25(c) consolidates them into a module-level `_git_run`. **`_resolve_git_root` (~:703) is deliberately EXCLUDED** — it has no timeout, lets errors propagate to drive its explicit `parent.parent.parent` fallback-with-warning, and bootstraps git_root before it is known; folding it in would silently change behavior. This is a behavior-preserving refactor.

- [x] **Step 1: Write the failing test** in `tests/unit/test_c2_integration_gate.py` (load controller-checkpoint via the hoisted loader near the top of the module: `_vp_ckpt = _load_script("controller_checkpoint_n25", "controller-checkpoint.py")`):

```python
class TestGitRunSSOT:
    """N25(c): module-level _git_run swallows failures, returns CompletedProcess|None."""

    def test_git_run_handles_failure(self):
        # A failing git invocation (bad cwd) returns CompletedProcess(rc!=0) —
        # git execs fine and exits 128 without raising, so subprocess.run does
        # not throw. Callers gate on returncode. _git_run returns None ONLY on
        # TimeoutExpired / OSError (the except branch).
        result = _vp_ckpt._git_run(["status"], cwd="/no/such/dir/xyz")
        assert result is None or result.returncode != 0

    def test_git_run_returns_completed_process(self, tmp_path):
        import subprocess
        repo = str(tmp_path)
        subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
        result = _vp_ckpt._git_run(["rev-parse", "--is-inside-work-tree"], cwd=repo)
        assert result is not None and result.returncode == 0
```

- [x] **Step 2: Run to verify it fails**

Run: `.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestGitRunSSOT -v`
Expected: FAIL — `_git_run` does not exist (AttributeError).

- [x] **Step 3: Add the module-level `_git_run`** near the other git helpers (e.g. just above `_resolve_base_ref`, line 437):

```python
def _git_run(args, cwd=None, timeout=10):
    # type: (list, Optional[str], int) -> Optional[subprocess.CompletedProcess]
    """Run a git subprocess; swallow TimeoutExpired/OSError (returns None).

    Module-level SSOT (N25c) for the THREE git call sites that share identical
    timeout + error-swallowing semantics: the inline call in
    _check_verification_git_reality, _resolve_base_ref's git helper, and
    _in_changeset's git helper. NOT used by _resolve_git_root, which keeps
    no-timeout + error-propagation to drive its explicit fallback-with-warning
    and bootstraps git_root before it is known (O4).
    """
    cmd = ["git", "-C", cwd] + args if cwd else ["git"] + args
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
```

- [x] **Step 4: Consolidate the 3 git call sites.** Replace the inner `_git` helper in `_resolve_base_ref` (lines 454-463) with a delegation:

```python
    def _git(cmd_args: list):
        return _git_run(cmd_args, cwd=git_root)
```

Replace the inner `_git` helper in `_in_changeset` (lines 505-514) identically:

```python
    def _git(cmd_args: list):
        return _git_run(cmd_args, cwd=git_root)
```

Replace the inline git call in `_check_verification_git_reality` (lines 344-364, the `git_cmd` build + `subprocess.run` + try/except) with:

```python
        git_args = ["log", "--oneline", f"--after={start_ts}"]
        if end_ts:
            git_args.append(f"--before={end_ts}")
        git_args.extend(["--diff-filter=ACDMR", "--name-only"])

        result = _git_run(git_args, cwd=git_root)
        if result is not None and result.returncode == 0 and result.stdout.strip():
            findings.append(
                {
                    "task": vid,
                    "start": start_ts,
                    "end": end_ts or "now",
                    "commits": result.stdout.strip(),
                }
            )
```

- [x] **Step 5: Audit ALL 4 git sites (O4).** Confirm the only remaining raw `subprocess.run([... "git" ...])` is in `_resolve_git_root`:

Run: `grep -nE "subprocess\.run" skills/subagent-driven-development/scripts/controller-checkpoint.py`
Expected: the only git `subprocess.run` is inside `_resolve_git_root` (~:703) plus the new `_git_run` definition. Any other match is a bug — fold it into `_git_run`. (The `_resolve_git_root` exclusion is justified in `plan.md` O4.)

- [x] **Step 6: Run the suites** (behavior-preserving — all pre-existing tests must still pass)

Run: `.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py tests/unit/test_pre_completion_gates.py -v`
Expected: PASS (new `_git_run` tests + ALL pre-existing Check-10/Check-9 tests unchanged).

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_c2_integration_gate.py
git commit -m "refactor(checkpoint): N25c — module-level _git_run SSOT (3 sites; _resolve_git_root excluded per O4)"
```

---

### Task 8: N25a — Check 10 feature-window fallback

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py` (add `_EMPTY_TREE_SHA`, `_merge_base_is_head`, `_feature_window_base`; capture `manifest_feature_dir`; Check 10 effective-base)
- Test: `tests/unit/test_c2_integration_gate.py`

**Pattern References:**
- `tests/unit/test_c2_integration_gate.py::TestCheck10*` — `_setup_repo`/`_git`/`_run_checkpoint` git-repo harness.

**Context (O4 resolved in `plan.md`):** When `merge-base(base_ref, HEAD) == HEAD` (SDD on main, remoteless repo), the diff window vs merge-base is empty so committed feature files are invisible to `_in_changeset`. N25(a) recomputes an effective base = parent of the first commit touching `paths.feature_dir` (root-commit edge → empty tree). Fail-closed is preserved: a file committed BEFORE the feature window still FAILs. Uses Task 7's `_git_run`.

- [x] **Step 1: Write the failing tests** in `tests/unit/test_c2_integration_gate.py`:

```python
class TestFeatureWindowBase:
    """N25(a): _merge_base_is_head, _feature_window_base, on-main Check 10."""

    def test_feature_window_base_none_when_no_feature_commit(self, tmp_path):
        import subprocess
        repo = str(tmp_path)
        subprocess.run(["git", "-C", repo, "init", "-q", "-b", "main"], check=True)
        assert _vp_ckpt._feature_window_base(repo, "docs/imp-plans/feat") is None

    def test_on_main_committed_integration_test_passes(self, tmp_path):
        """N25(a): remoteless repo, work on main, integration test committed in
        the feature window → PASS (today FAILs — merge-base==HEAD hides it)."""
        # Mirror TestCheck10._setup_repo: init -b main, NO origin; commit the
        # feature dir (plan.md/spec) FIRST, then commit tests/integration/<it>.sh;
        # run pre-completion with --manifest at the feature's manifest.
        ...  # assert check["status"] == "PASS"

    def test_on_main_prewindow_file_still_fails(self, tmp_path):
        """Counter-fixture: a tracked file committed BEFORE the feature window
        still FAILs (fail-closed preserved)."""
        ...  # assert "integration_test_present" in blockers
```

> NOTE: mirror `TestCheck10._setup_repo`/`_git` for the on-main fixtures. The key fixture properties: `git init -b main`, NO `origin` remote (so `_resolve_base_ref` → `main` and `merge-base(main, HEAD) == HEAD`); commit the feature dir FIRST, then commit the declared integration test inside the window. `_setup_repo` makes the feature-dir commit the repo ROOT, so `_feature_window_base` returns the empty-tree SHA and Step 3b's direct-diff is what makes the committed test visible (the PASS fixture exercises that edge). The counter-fixture commits a NON-feature file BEFORE the feature dir (giving `_feature_window_base` a real parent), then asserts that pre-window file still FAILs.

- [x] **Step 2: Run to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestFeatureWindowBase -v`
Expected: FAIL — `_merge_base_is_head`/`_feature_window_base` do not exist; the on-main fixture FAILs Check 10 (committed file invisible).

- [x] **Step 3: Add the constant + helpers** near `_git_run` (added in Task 7), e.g. just above `_resolve_base_ref`:

```python
_EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # git's well-known empty tree


def _merge_base_is_head(git_root, base_ref):
    # type: (str, str) -> bool
    """True when merge-base(base_ref, HEAD) == HEAD (we are ON the base branch),
    so the diff window vs merge-base is empty and committed feature files are
    invisible to _in_changeset (N25a triggers a feature-window base here)."""
    mb = _git_run(["merge-base", base_ref, "HEAD"], cwd=git_root)
    head = _git_run(["rev-parse", "HEAD"], cwd=git_root)
    if mb is None or head is None or mb.returncode != 0 or head.returncode != 0:
        return False
    return bool(head.stdout.strip()) and mb.stdout.strip() == head.stdout.strip()


def _feature_window_base(git_root, feature_dir):
    # type: (str, str) -> Optional[str]
    """Parent of the first commit touching feature_dir, or None (N25a).

    Root-commit edge: the first feature commit has no parent → return the empty
    tree SHA, which the caller's _in_changeset special-cases as a DIRECT diff
    base (Step 3b) — it cannot flow through _in_changeset's merge-base path (a
    tree object has no merge-base with HEAD). No commit touches feature_dir yet
    → None (caller keeps the untracked-only changeset, on-main FAIL note).
    """
    if not feature_dir:
        return None
    log = _git_run(
        ["log", "--reverse", "--format=%H", "--", feature_dir], cwd=git_root
    )
    if log is None or log.returncode != 0 or not log.stdout.strip():
        return None
    first = log.stdout.strip().splitlines()[0].strip()
    parent = _git_run(["rev-parse", "--verify", "--quiet", first + "^"], cwd=git_root)
    if parent is not None and parent.returncode == 0 and parent.stdout.strip():
        return parent.stdout.strip()
    return _EMPTY_TREE_SHA
```

- [x] **Step 3b: Make `_in_changeset` accept the empty-tree base.** `_in_changeset` (controller-checkpoint.py:494-527) computes `merge-base(base, HEAD)` first; `merge-base(<empty-tree>, HEAD)` FAILS (a tree is not a commit) and silently falls back to `diff HEAD`, hiding committed files. Add a direct-diff special-case AFTER the untracked check and BEFORE the `merge-base` block (uses the inner `_git`, which Task 7 routed through `_git_run`):

```python
    if base_ref == _EMPTY_TREE_SHA:
        # Root-commit feature window: diff the empty tree directly against the
        # working tree (merge-base is undefined for a tree object).
        diff = _git(["diff", "--name-only", _EMPTY_TREE_SHA, "--", path])
        return diff is not None and diff.returncode == 0 and bool(diff.stdout.strip())
```

- [x] **Step 4: Capture `manifest_feature_dir`.** In `run_pre_completion`, initialize a variable before the `all_plan_contents` block (line 1290) and set it inside the manifest branch:

```python
    manifest_feature_dir = ""
    if getattr(args, "manifest", None):
        try:
            _mp = Path(args.manifest)
            _md = json.loads(_mp.read_text(encoding="utf-8"))
            _gr = _resolve_git_root(_mp)
            all_plan_contents = _load_all_plan_contents(_md, _gr)
            manifest_feature_dir = _md.get("paths", {}).get("feature_dir", "")
        except Exception:
            all_plan_contents = [plan_content]
    else:
        all_plan_contents = [plan_content]
        if getattr(args, "additional_plan_files", None):
            for path in args.additional_plan_files:
                if os.path.isfile(path):
                    try:
                        all_plan_contents.append(read_file(path))
                    except OSError:
                        pass
```

- [x] **Step 5: Apply the feature-window base in Check 10.** In the `else` branch (after `base_ref = _resolve_base_ref(it_git_root)` is confirmed non-None, line 1625), compute `effective_base` BEFORE the `_in_changeset` loop, pass `effective_base` (not `base_ref`) to `_in_changeset`, and name `effective_base` in the PASS detail:

```python
        else:
            # N25(a): on-base-branch detection. merge-base(base, HEAD) == HEAD
            # (SDD on main, remoteless) makes committed feature files invisible
            # to _in_changeset. Recompute the effective base = parent of the
            # first commit touching the feature dir.
            effective_base = base_ref
            on_base_no_window = False
            if _merge_base_is_head(it_git_root, base_ref):
                fw_base = _feature_window_base(it_git_root, manifest_feature_dir)
                if fw_base:
                    effective_base = fw_base
                else:
                    on_base_no_window = True

            it_problems = [
                "malformed declaration: {}".format(d) for d in malformed_it_decls
            ]
            for rel_path in declared_it_paths:
                abs_path = os.path.join(it_git_root, rel_path)
                if not os.path.isfile(abs_path):
                    it_problems.append("{}: missing on disk".format(rel_path))
                elif not _in_changeset(rel_path, effective_base, it_git_root):
                    msg = (
                        "{}: exists but is not part of this feature's changeset "
                        "(no diff vs {})".format(rel_path, effective_base)
                    )
                    if on_base_no_window:
                        msg += (
                            " — on the base branch (merge-base==HEAD) with no "
                            "commit yet touching the feature dir; only untracked "
                            "files are visible until the feature window opens"
                        )
                    it_problems.append(msg)
            if it_problems:
                checks["integration_test_present"] = {
                    "status": "FAIL",
                    "detail": (
                        "Declared integration test(s) failed the gate: "
                        + "; ".join(it_problems)
                        + ". The declared file must exist and be added or "
                        "modified by this feature."
                    ),
                }
                blockers.append("integration_test_present")
            else:
                checks["integration_test_present"] = {
                    "status": "PASS",
                    "detail": (
                        "{} declared integration test(s) exist and are in the "
                        "feature changeset (base: {})".format(
                            len(declared_it_paths), effective_base
                        )
                    ),
                }
```

> NOTE: the `is_dir()` detail (N25d) is added in Task 9 — this task keeps the existing "missing on disk" message for the not-a-file branch.

- [x] **Step 6: Run the suites**

Run: `.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py tests/unit/test_pre_completion_gates.py -v`
Expected: PASS (new feature-window tests + all pre-existing Check-10/Check-9 tests — behavior unchanged for the non-on-base paths).

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_c2_integration_gate.py
git commit -m "feat(checkpoint): N25a — Check 10 feature-window fallback (on-main false-block fix)"
```

---

### Task 9: N25b+d+f — frontmatter line-anchored scan + directory/malformed diagnostics

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py` (`_task_ids_where` line 250; `_integration_test_paths` line 393 + malformed messages; Check 10 not-a-file branch)
- Test: `tests/unit/test_c2_integration_gate.py`

**Context:** N25(b) — both `_task_ids_where` (line 250) and `_integration_test_paths` (line 393) close the frontmatter with `content.find("---", 3)`, which matches the first `---` anywhere (e.g. a `---` inside a YAML value or a hr). Make both line-anchored (`^---$`). N25(d) — a declared path that exists but is a directory FAILs with "is a directory, not a file" (currently the misleading "missing on disk"). N25(f) — malformed-declaration messages name the source plan file.

- [x] **Step 1: Write the failing tests** in `tests/unit/test_c2_integration_gate.py`:

```python
class TestN25Diagnostics:
    def test_frontmatter_line_anchored(self):
        # A value containing '---' must not prematurely close the frontmatter.
        content = (
            "---\nschema_version: 1\n"
            "note: 'see --- below'\n"
            "tasks:\n  - id: 1\n    review_tier: minimum\n---\n# Plan\n"
        )
        ids, parsed = _vp_ckpt._task_ids_where([content], "review_tier", "minimum")
        assert parsed is True and ids == {1}

    def test_directory_path_says_is_a_directory(self, tmp_path):
        # _integration_test_paths returns the path; Check 10 reports is_dir.
        # (Assert via run_pre_completion on a manifest whose declared path is a
        # dir — mirror TestCheck10 harness; assert detail contains
        # "is a directory, not a file".)
        ...

    def test_malformed_names_source_plan_file(self):
        # _integration_test_paths malformed messages should be attributable to a
        # plan file by the caller. Assert the malformed list is non-empty for a
        # bare-string declaration; Check 10 detail must name the plan file.
        bad = "---\nschema_version: 1\nintegration_test: just-a-string\n---\n# Plan\n"
        paths, malformed = _vp_ckpt._integration_test_paths([bad])
        assert paths == [] and malformed and "bare string" in malformed[0]
```

> NOTE for the implementer: `_integration_test_paths` currently takes only `plan_contents` (no filenames), so to "name the source plan file" (N25f) either thread an optional parallel list of file labels into `_integration_test_paths`, OR have the Check-10 caller prefix the malformed details with the plan file(s) it loaded. Choose the minimal change that makes `test_malformed_names_source_plan_file`'s Check-10 detail include a plan filename; document the choice in the implementer report. The directory test asserts the Check-10 FAIL detail contains "is a directory, not a file".

- [x] **Step 2: Run to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py::TestN25Diagnostics -v`
Expected: FAIL — the `---`-in-value closes the frontmatter early (parsed/ids wrong); directory path reports "missing on disk"; malformed detail lacks the plan filename.

- [x] **Step 3: Line-anchor the frontmatter close (N25b).** A shared helper is cleanest. Add near the top helpers:

```python
def _frontmatter_block(content: str) -> Optional[str]:
    """Return the YAML frontmatter body (between the opening and the first
    line-anchored ^---$), or None. Line-anchored so a '---' inside a value or a
    markdown hr does not prematurely close the block (N25b)."""
    if not content or not content.startswith("---"):
        return None
    m = re.search(r"^---$", content[3:], re.MULTILINE)
    if not m:
        return None
    return content[3 : 3 + m.start()]
```

In `_task_ids_where`, replace the open/find/parse (lines 248-256) so it uses `_frontmatter_block`:

```python
    for content in plan_contents:
        block = _frontmatter_block(content)
        if block is None:
            continue
        try:
            fm = yaml.safe_load(block)
        except Exception:
            continue
```

In `_integration_test_paths`, replace the equivalent block (lines 391-399) the same way:

```python
    for content in plan_contents:
        block = _frontmatter_block(content)
        if block is None:
            continue
        try:
            fm = yaml.safe_load(block)
        except Exception:
            continue
```

- [x] **Step 4: Directory-as-path detail (N25d).** In Check 10's not-a-file branch (Task 8's Step 5 left it as "missing on disk"), distinguish a directory:

```python
                if not os.path.isfile(abs_path):
                    if os.path.isdir(abs_path):
                        it_problems.append(
                            "{}: is a directory, not a file".format(rel_path)
                        )
                    else:
                        it_problems.append("{}: missing on disk".format(rel_path))
```

- [x] **Step 5: Name the source plan file in malformed messages (N25f).** Implement the minimal approach chosen in Step 1's NOTE. Recommended: in the Check-10 caller, when `malformed_it_decls` is non-empty, prefix the detail with the loaded plan file(s) — e.g. derive from `manifest_feature_dir`/`args.plan_file`. Ensure the FAIL detail for the malformed-only and mixed branches names a plan file.

- [x] **Step 6: Run the suites**

Run: `.venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py tests/unit/test_pre_completion_gates.py -v`
Expected: PASS (new diagnostics tests + all pre-existing — the line-anchored helper is behavior-preserving for well-formed frontmatter).

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_c2_integration_gate.py
git commit -m "feat(checkpoint): N25(b,d,f) — line-anchored frontmatter scan + directory/malformed diagnostics"
```

---

### Task 10: N6 — SDD SKILL.md hook-enforces-this framing pass (doc)

**Files:**
- Modify: `skills/subagent-driven-development/SKILL.md` (three sites: lines 282-286, line 286 tail, lines 428-430)

**Pattern References:**
- `skills/subagent-driven-development/SKILL.md:257-265` — the C6(a) exemplar ("runs automatically … there is no manual step for you to run … This is a deterministic, hook-enforced check").

**Context:** Doc-only, no behavior change. Apply the C6(a) treatment to the three remaining manual-prescription sites so they state the hook/gate enforces the step automatically, making the manual run an optional early check (removes skip-guilt + the false "controller-only honor system" impression). **Hard constraint: net `wc -w` MUST NOT increase** (5000 hard limit; current ~4911).

- [x] **Step 1: Record the pre-edit word count**

Run: `wc -w skills/subagent-driven-development/SKILL.md`
Note the number (call it `W0`). The post-edit count must be `<= W0`.

- [x] **Step 2: Reframe the pre-dispatch checkpoint + context summary (lines 282-286).** Replace:

```
**Before each task dispatch**:
```bash
python ~/.claude/skills/superpowers/subagent-driven-development/scripts/controller-checkpoint.py --phase pre-dispatch --task-number N --plan-file <plan.md> --feature-dir <feature-dir>
```
Verify: previous task complete, report filed, no pending deviations from prior task, context load reasonable. If FAIL, address the blocker before dispatching. If WARNING about context load, run the context summary script to compress state.
```

with:

```
**Before each task dispatch** — the pre-dispatch hook enforces this automatically (Check 5c requires the saved checkpoint file; Check 6b blocks past the midpoint without a context summary), so running it by hand first is an optional early check:
```bash
python ~/.claude/skills/superpowers/subagent-driven-development/scripts/controller-checkpoint.py --phase pre-dispatch --task-number N --plan-file <plan.md> --feature-dir <feature-dir>
```
Verify: previous task complete, report filed, no pending deviations, context load reasonable.
```

- [x] **Step 3: Reframe report validation (lines 428-430).** Replace:

```
3. **Validate report completeness** using the validation script:
   `python ~/.claude/skills/superpowers/subagent-driven-development/scripts/validate-report.py --report-file <feature-dir>/reports/task-NNN-implementer-report.md`
   If the script returns INCOMPLETE, do not proceed to review.
```

with:

```
3. **Validate report completeness** — the pre-dispatch hook enforces this on the next dispatch (Check 4b blocks if the prior report fails validation), so this manual run is an optional early check:
   `python ~/.claude/skills/superpowers/subagent-driven-development/scripts/validate-report.py --report-file <feature-dir>/reports/task-NNN-implementer-report.md`
```

- [x] **Step 4: Verify the word count did not increase**

Run: `wc -w skills/subagent-driven-development/SKILL.md`
Expected: `<= W0`. If it increased, trim wording (e.g. shorten the "Verify:" lists) until `<= W0`. Do not touch unrelated sections.

- [x] **Step 5: Run the regression suite**

Run: `python3 tests/ARaymond-skill-regression/validate-all-skills.py`
Expected: PASS-with-warnings unchanged (SDD word-count WARNING stays a WARNING, not a FAIL; no new FAIL).

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/SKILL.md
git commit -m "docs(sdd): N6 — hook-enforces-this framing pass (net words <= current)"
```

---

### Task 11: N8 — intent-based F6 regression check

**Files:**
- Modify: `tests/ARaymond-skill-regression/validate-all-skills.py` (F6, line 569)

**Pattern References:**
- `skills/writing-plans/SKILL.md:16-18` — the `2. **Direct entry** —` bold label that the new structural signal matches.

**Context (O3 resolved in `plan.md`):** F6 currently greps for the literal phrases `"invoked directly"` / `"skipping brainstorming"` — a semantically-equivalent rewording silently FAILs. N8 keys on a structural "Direct entry" signal (bold label or heading). **Scope stays `writing-plans/SKILL.md` ONLY** — no other skill gains a direct-entry section. The existing `2. **Direct entry** —` already satisfies the structural signal, so `writing-plans/SKILL.md` needs NO edit (O3, zero word cost).

- [x] **Step 1: Confirm the current heading satisfies the chosen signal**

Run: `grep -nE '\*\*Direct entry\*\*' skills/writing-plans/SKILL.md`
Expected: matches line 18 (`2. **Direct entry** —`). (If it does not match, adjust the heading per O3 in the SAME task, word-ceiling aware. It does match today, so no edit is expected.)

- [x] **Step 2: Replace the F6 literal-phrase check (line 569).** Add a module-level regex near the other patterns and rewrite the check. Replace:

```python
        # F6: standalone invocation guidance
        if "skipping brainstorming" in wp_content or "invoked directly" in wp_content:
```

with:

```python
        # F6: standalone invocation guidance — intent-based (N8). Keys on a
        # structural "Direct entry" signal (bold label or heading) rather than
        # brittle literal phrases. Scope stays writing-plans/SKILL.md ONLY.
        import re as _re
        _direct_entry_re = _re.compile(
            r"(?im)^#{1,6}.*direct entry|\*\*\s*direct entry"
        )
        if _direct_entry_re.search(wp_content):
```

(The check_pass/check_fail branch below is unchanged.)

- [x] **Step 3: Run the regression suite**

Run: `python3 tests/ARaymond-skill-regression/validate-all-skills.py`
Expected: F6 PASSes ("writing-plans SKILL: has standalone invocation guidance"); overall result PASS-with-warnings; no new FAIL.

- [x] **Step 4: Negative check (intent robustness).** Temporarily confirm the regex is intent-based, not phrase-based: it must still match if `"invoked directly"` were reworded but the `**Direct entry**` label remains. (No file change — reason about the regex; the live SKILL.md keeps its bold label.)

- [x] **Step 5: Commit**

```bash
git add tests/ARaymond-skill-regression/validate-all-skills.py
git commit -m "test(regression): N8 — intent-based F6 Direct-entry signal"
```

---

### Task 12: Archive-awareness inventory docs (5 sites)

**Files:**
- Modify: `CLAUDE.md` (line 206 — the N4 inventory statement)
- Modify: `docs/ARaymond-customization-manifest.md` (line 329 — the controller-checkpoint row)

**Context:** N27 raised the archive-aware lookup count from 3 to 5. Both doc statements of the inventory must be updated BEFORE the verification task (Task 13) audits them. The 5 sites: (1) `find_report_file`, (2) `find_all_report_files` [N4], (3) `_review_tiers_per_task` [N27 Check 7], (4) `_merged_dispatch_times` [N27 Check 9] — all in `controller-checkpoint.py` — plus (5) the hook's Check 5 Task-0 lookup [N10] in `sdd-pre-dispatch-hook.sh`.

- [x] **Step 1: Update CLAUDE.md line 206.** Replace:

```
Archive-awareness applies to **exactly these two lookups** (N4) plus the hook's Check 5 Task-0 lookup (N10) — **every other report glob stays intentionally flat** (e.g. `task_report_glob`, the per-task report checks).
```

with:

```
Archive-awareness applies to **exactly five lookups** (N4: `find_report_file` + `find_all_report_files`; N10: the hook's Check 5 Task-0 lookup; N27: `_review_tiers_per_task` for Check 7 + `_merged_dispatch_times` for Check 9) — **every other report glob stays intentionally flat** (e.g. `task_report_glob`, the per-task report checks).
```

- [x] **Step 2: Update the customization manifest (line 329).** Find the sentence in the `controller-checkpoint.py` row that reads "these two are the ONLY pre-completion lookups made archive-aware; every other report glob stays flat by design" and replace it with:

```
(2026-06-22, sdd-aggregate-gate-visibility:) N27 made Check 7 (`_review_tiers_per_task`) and Check 9 (`_merged_dispatch_times`) archive-aware too — the archive-aware lookup inventory is now FIVE sites total: `find_report_file` + `find_all_report_files` (N4) + the hook's Check 5 Task-0 lookup (N10) + `_review_tiers_per_task` + `_merged_dispatch_times` (N27). Every other report glob stays flat by design.
```

- [x] **Step 3: Cross-check there is no other stale "three / two lookups" inventory statement**

Run: `grep -rnE "two lookups|three lookups|3 lookups|exactly these two|stays (intentionally )?flat" CLAUDE.md docs/ARaymond-customization-manifest.md`
Expected: every match either now says five, or is an unrelated context (e.g. the historical N4/N10 changelog entries that DESCRIBE the prior state — leave those as dated history; only the live inventory statements change). Document which matches were updated vs left as history in the implementer report.

- [x] **Step 4: Commit**

```bash
git add CLAUDE.md docs/ARaymond-customization-manifest.md
git commit -m "docs: N27 — archive-awareness inventory now 5 sites"
```

---

### Task 13: Verification — archive-awareness inventory audit (`task_type: verification`)

**Files:** None (read-only audit — `task_type: verification`).

**Context:** First live exercise of the N16 verification-report path in this sprint. This is a NON-LAST task (Task 14 follows) so its implementer dispatch is in the LIVE log at pre-completion. It greps the code and the docs and confirms the 5-site inventory is consistent, with ZERO file writes. The report validates with empty `files_changed` (N16 on main).

- [x] **Step 1: Confirm exactly 5 code sites glob `archive-*/`.** Run:

```bash
grep -nE 'archive-\*' skills/subagent-driven-development/scripts/controller-checkpoint.py
grep -nE 'archive-\*' skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh
```

Expected — the FIVE named archive-aware lookups each glob `archive-*/`:
1. `find_report_file` (controller-checkpoint.py)
2. `find_all_report_files` (controller-checkpoint.py)
3. `_review_tiers_per_task` (controller-checkpoint.py, N27)
4. `_merged_dispatch_times` (controller-checkpoint.py, N27)
5. hook Check 5 Task-0 lookup (sdd-pre-dispatch-hook.sh, N10)

Note: a raw line count of `archive` matches is NOT the metric — verify each of the 5 NAMED lookups globs `archive-*/`, and that no OTHER glob (e.g. `task_report_glob`, `detect_stale_artifacts`, per-task report checks) does.

- [x] **Step 2: Confirm the docs state 5 sites.** Run:

```bash
grep -nE "five lookups|FIVE sites|5 sites" CLAUDE.md docs/ARaymond-customization-manifest.md
```

Expected: CLAUDE.md (Task 12 Step 1) and the manifest (Task 12 Step 2) both state five sites; no live inventory statement still says "two"/"three".

- [x] **Step 3: Confirm every OTHER report glob stays flat.** Run:

```bash
grep -nE "glob\(|glob\.glob" skills/subagent-driven-development/scripts/controller-checkpoint.py
```

Expected: every `glob` that is NOT one of the 5 named lookups operates on the live `reports_dir` only (no `archive-*` segment). Record the audited list in the report.

- [x] **Step 4: Write the verification report** to `<feature-dir>/reports/task-013-implementer-report.md` with `task_type: verification` frontmatter and empty `files_changed: []` (N16 path). The 5 prose sections summarize: the 5 code sites confirmed, the 2 doc statements confirmed, and the flat-glob audit result. No files are modified.

> This task makes NO code changes. If the audit finds a discrepancy (a 6th site, a missing doc update, an unintended archive-aware glob), STOP and log it as a deviation — do not silently fix it here; route the fix to a follow-up task or re-open the relevant prior task.

---

### Task 14: e2e Step 12 (archive-aware proof) + BACKLOG flips + final suites

**Files:**
- Modify: `tests/integration/sdd-e2e-test.sh` (new Step 12 before the final echo; update "12 steps" → "13 steps")
- Modify: `docs/process-improvement-findings/BACKLOG.md` (flip rows)

**Pattern References:**
- `tests/integration/sdd-e2e-test.sh:130-162` (Step 5 transition), `:390-444` (Step 11 Check-10 assertion).

**Context:** The in-sprint proof (self-hosting hazard #1): this run's live enforcement uses main's pre-fix scripts, so the e2e test — which runs THIS checkout's `$PROJECT` scripts — is the only place the archive-aware fix is exercised end-to-end this sprint.

- [x] **Step 1: Add Step 12** to `tests/integration/sdd-e2e-test.sh`, inserted BEFORE the final `echo "" ; echo "E2E PIPELINE PASS ..."` block (line 446). Build a self-contained 2-module fixture (mirror Step 11's `$IT` pattern and Step 5's transition), then assert BOTH archive-aware behaviors after a transition:

```bash
# Step 12: archive-aware aggregate gates (N27) — Check 7 counts archived
# minimum-tier reviews AND Check 9 sees an archived-module verification window.
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

$PYTHON $PROJECT/skills/subagent-driven-development/scripts/materialize-manifest.py \
  --plan-file "$AV/plan.md" --feature-dir "$AV" > /dev/null

# Archived Module 1: all quality reviews minimum-tier (undeclared) → today the
# flat glob misses them; archive-aware Check 7 must count them.
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
$PYTHON $PROJECT/skills/subagent-driven-development/scripts/controller-checkpoint.py \
  --phase pre-completion --manifest "$AV/.sdd-session.json" \
  --deviations-file "$AV_DEV" --reports-dir "$AV/reports" > "$AVOUT" 2>&1 || true

# Check 7: archived minimum-tier reviews counted (2 min / 3 total > 50% → FAIL).
Q_STATUS=$(python3 -c "import json;print(json.load(open('$AVOUT'))['checks']['excessive_minimum_tier_quality']['status'])")
# Check 9: archived-module verification window sees the in-window commit → FAIL.
G_STATUS=$(python3 -c "import json;print(json.load(open('$AVOUT'))['checks']['verification_git_reality']['status'])")
rm "$AVOUT"
[ "$Q_STATUS" = "FAIL" ] || { echo "FAIL: Check 7 not archive-aware (got $Q_STATUS)"; exit 1; }
[ "$G_STATUS" = "FAIL" ] || { echo "FAIL: Check 9 not archive-aware (got $G_STATUS)"; exit 1; }
echo "PASS: Step 12 — Check 7 + Check 9 are archive-aware after a transition"
```

> NOTE for the implementer: tune the fixture to the live JSON shape — confirm the check keys (`excessive_minimum_tier_quality`, `verification_git_reality`) and that the manifest's `paths.reports_dir`/`dispatch_log` resolve under `$AV`. The minimum-tier ratio math: archived tasks 1,2 minimum + live task 4 full = 2/3 > 0.5 → FAIL (proving the archived reviews are counted). Verify task 3 is NOT in the ratio (it has no quality review — it is `task_type: verification`).

- [x] **Step 2: Update the final step count.** Change the closing line from `echo "E2E PIPELINE PASS - 12 steps composed correctly"` to `... - 13 steps ...`.

- [x] **Step 3: Run the e2e test**

Run: `bash tests/integration/sdd-e2e-test.sh`
Expected: `E2E PIPELINE PASS - 13 steps composed correctly`.

- [x] **Step 4: Flip the BACKLOG rows** in `docs/process-improvement-findings/BACKLOG.md`. Set status `open` → `done` with a commit ref + "Done 2026-06-22 (sdd-aggregate-gate-visibility)" note for: **N6** (line 43), **N8** (line 45), **N19** (line 67), **N20** (line 68), **N22** (line 70), **N26** (line 74), **N27** (line 75). For **N25** (line 73): mark (a),(b),(c),(d),(f) done; explicitly note (e) and (g) **remain open**, pointed at this feature. Update any summary/outcome lines that reference these as open. Leave N21/N23/N24/N28(a,b,d) open with a one-line pointer to this feature.

- [x] **Step 5: Run ALL four suites**

```bash
.venv/bin/python3 -m pytest tests/unit/ -v
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/ARaymond-installation/verify-symlink-install.sh
bash tests/integration/sdd-e2e-test.sh
```

Expected: unit all green; regression PASS-with-warnings (no new FAIL); install 104 checks PASS; e2e 13 steps PASS.

- [x] **Step 6: Commit**

```bash
git add tests/integration/sdd-e2e-test.sh docs/process-improvement-findings/BACKLOG.md
git commit -m "test(e2e): N27 — Step 12 archive-aware aggregate proof; flip BACKLOG rows"
```

## Acceptance Criteria (Module 2)

- [x] `_unfenced_content` handles `~~~` (own-marker close); unclosed-fence behavior pinned; validate-plan WARNs on an unclosed fence; `_load_script` hoisted to `sdd_test_helpers.py`.
- [x] Risk-surface WARNING matches `migrations`/`caches`/`routers`/`authentication`; ignores fence-only keywords.
- [x] Check 10 PASSes for a committed integration test in an on-main remoteless feature window; pre-window tracked files still FAIL; `_git_run` consolidates 3 sites (all 4 audited; `_resolve_git_root` justified-excluded).
- [x] Frontmatter scan line-anchored in both `_task_ids_where` and `_integration_test_paths`; directory path → "is a directory, not a file"; malformed declarations name the source plan file.
- [x] SDD SKILL.md framing pass: net `wc -w` ≤ pre-edit; regression green.
- [x] F6 intent-based (structural Direct-entry signal), scoped to `writing-plans/SKILL.md`; full regression green.
- [x] Archive-awareness inventory states 5 sites in CLAUDE.md + manifest; verified by Task 13 (zero writes; report validates with empty `files_changed`).
- [x] e2e Step 12 proves Check 7 + Check 9 archive-awareness after a transition; e2e reports 13 steps.
- [x] All four suites green; BACKLOG rows N6/N8/N19/N20/N22/N25(a-d,f)/N26/N27 flipped with commit refs; N25(e,g)+N21/N23/N24/N28(a,b,d) remain open with a pointer.
