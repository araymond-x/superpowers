---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: null
shared_constants: []
pattern_references:
  - name: "early-skip-guard-chain"
    source_files: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    reason: "Check 4c's if/elif/else short-circuit chain (NEED_PROV / PREV_TASK_TYPE==verification). N3a adds a sibling guard in the same style — not nested in the grep."
  - name: "verification-task-id-parser"
    source_files: ["skills/subagent-driven-development/scripts/controller-checkpoint.py"]
    reason: "_verification_task_ids() — frontmatter YAML parse for task_type. Mirror for the per-task verification exemption in transition-module.py."
  - name: "bash-hook-subprocess-test"
    source_files: ["tests/unit/test_sdd_classification.py", "tests/unit/sdd_test_helpers.py"]
    reason: "run_hook() subprocess pattern + setup_manifest_workspace()/make_hook_input() manifest-mode helpers for testing the bash hook."
  - name: "transition-test-harness"
    source_files: ["tests/unit/test_transition_module.py"]
    reason: "create_manifest/create_task_reports/run_transition multi-module subprocess test setup."
  - name: "bypass-env-var"
    source_files: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    reason: "SUPERPOWERS_VALIDATOR_BYPASS handling — mirror for SUPERPOWERS_SDD_BYPASS (allow + stderr warning)."
tasks:
  - id: 0
    title: "Promote sdd-skill-enforcement-hook.sh to blocking"
    pattern_references: ["bypass-env-var", "bash-hook-subprocess-test"]
  - id: 1
    title: "Archive-aware report lookups in controller-checkpoint.py"
    depends_on: [0]
  - id: 2
    title: "Harden sdd-pre-dispatch-hook.sh: Check 4c skip-guard plus Check 5 archive glob"
    depends_on: [1]
    pattern_references: ["early-skip-guard-chain", "bash-hook-subprocess-test"]
  - id: 3
    title: "transition-module.py: provenance + verification exemption + context_summary_at recompute"
    depends_on: [2]
    pattern_references: ["verification-task-id-parser", "transition-test-harness"]
  - id: 4
    title: "SSOT agreement test for the file-based minimum signal"
    depends_on: [2, 3]
    pattern_references: ["bash-hook-subprocess-test", "transition-test-harness"]
  - id: 5
    title: "E2E: provenance in transition plus module-2-first-task post-transition"
    depends_on: [2, 3]
  - id: 6
    title: "Update documentation: CLAUDE.md, manifest, BACKLOG"
    review_tier: minimum
    depends_on: [4, 5]
  - id: 7
    title: "Run full test matrix and confirm counts"
    task_type: verification
    depends_on: [6]
---

# SDD Enforcement Hardening Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Close the multi-module SDD enforcement gaps (N3a/N3b/N4/N10, plus the N11 `context_summary_at` recompute folded into Task 3) and promote the SDD skill-bypass hook from advisory to blocking, so a 2-module plan runs end-to-end through `transition-module.py` with zero manual workarounds.

**Architecture:** Surgical edits across four existing enforcement scripts plus a new dedicated test file. (1) The pre-dispatch hook gets a Check 4c early-skip when the previous task lives in an archived/prior module, and a Check 5 glob that also looks in `archive-*/`. (2) `transition-module.py` re-verifies dispatch provenance for the completing module's tasks *before* it truncates the live log (with a per-task `task_type: verification` exemption mirroring the hook), and recomputes `enforcement.context_summary_at` for the next module on transition (N11). (3) `controller-checkpoint.py`'s two implementer-report lookups recurse into `archive-*/`. (4) The skill-bypass hook tightens its detection to an explicit SDD imperative and `exit 2`s (with a `SUPERPOWERS_SDD_BYPASS` escape hatch). A cross-language SSOT test pins the file-based "minimum" signal agreement between the hook and the transition validator; the e2e gains a live module-2-first-task-post-transition assertion that proves both the N3a skip-guard and the N11 recompute.

**Tech Stack:** Bash (PreToolUse hooks, `jq`, `grep -iE`), Python 3.9+ (stdlib + PyYAML + Pydantic via the `.venv`), pytest (unit), bash e2e harness.

**Source Contracts:** None

(Internal refactor/extension of our own enforcement scripts — no external schema, API, or handoff package. The load-bearing internal contract facts are pinned in **Contract Constraints** below, verbatim from the reviewer-approved `spec-distilled.md`, and are already covered by existing tests plus the new SSOT test in Task 4 — nothing is left unpinned, so no Contract-Verification Task 0 is warranted. Task numbering still starts at Task 0 as the first implementation task: this keeps the plan's own execution on the standard sequential flow the current main-checkout hook already handles, since the hardened hook is not live until merge.)

**Plan size & single-module rationale (for the reviewer):** This plan is intentionally a **single-module** plan (no `modules:` frontmatter) even though it is ~1000 lines. The line count is predominantly *complete test code* (the skill requires showing the actual code in every step); no individual task exceeds the 200-line task limit, and each task is dispatched to a separate subagent, so no execution context ever loads the whole plan. Modularizing is **not** an option here: declaring `modules:` would make this plan execute through `transition-module.py` under the **unhardened main-checkout hook** — exactly the N3a/N3b/N4 code paths being fixed — which would require manual workarounds during the plan's own run. Single-module execution side-steps that recursion entirely.

**Contract Constraints** (non-negotiable; from `spec-distilled.md` → "Contract Facts"):
- **Dispatch-log provenance line format** (written by `sdd-pre-dispatch-hook.sh`): reviewer lines are `<ts> DISPATCH reviewer task=<N> type=<spec-review|quality-review|partner-review|trace-audit>`; implementer lines are `<ts> DISPATCH implementer task=<N> type=implementer`. Provenance grep is keyed on the substring `task=<N> type=<review_type>` — timestamp is irrelevant to matching.
- **Two distinct "minimum" signals — do not conflate:**
  - *File signal:* the file `reports/task-NNN-quality-review-minimum-tier.md` exists ⇒ a controller-written quality review is allowed (no dispatch provenance required). This is the signal **Check 4c** and **N3b** consult.
  - *Plan-declaration signal:* `review_tier: minimum` in plan frontmatter ⇒ used **only** by `controller-checkpoint.py`'s ratio exclusion. **Not** the signal for N3b.
- **Manifest is git-root-relative.** All `paths.*` resolve via `git rev-parse --show-toplevel`. `MANIFEST_TASK_START = task_range[0]`.
- **Module boundary lifecycle** (`transition-module.py`): Step 1 `validate_module_completion` → Step 3 archive `task-NNN-*` → `reports/archive-<module>/` → Step 4 manifest advance → Step 5 copy + **truncate** the live `.dispatch-log`. **The live dispatch log is intact during Step 1**, so transition-time provenance must be checked there.
- **Tier review modes:** `process_requirements.spec_review_mode` / `quality_review_mode` may be `"skip"`; `"skip"` ⇒ that review type is not required (existing `validate_module_completion` already branches on this).
- **Block convention:** `exit 2` + a stderr message (matches `sdd-pre-dispatch-hook.sh`). The bypass env var mirrors `SUPERPOWERS_VALIDATOR_BYPASS` (set ⇒ allow + stderr warning).
- **Archive-awareness applies to EXACTLY two lookups:** `controller-checkpoint.py` `find_report_file` / `find_all_report_files` (N4) and the hook's Check 5 Task-0 lookup (N10). **Every other report glob stays flat** — see "Intentionally Flat" below.

**Shared Constants:** None.

**Pattern References:** (also declared in frontmatter; injected per-task by the SDD skill)
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — Check 4c's `if NEED_PROV / elif PREV_TASK_TYPE==verification / else` short-circuit chain (the style N3a's sibling guard must match); the `SUPERPOWERS_VALIDATOR_BYPASS` handling style (mirror for `SUPERPOWERS_SDD_BYPASS`).
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — `_verification_task_ids()` (the YAML-frontmatter task_type parser to mirror in `transition-module.py`).
- `tests/unit/test_sdd_classification.py` + `tests/unit/sdd_test_helpers.py` — `run_hook()` subprocess pattern and `setup_manifest_workspace()` / `make_hook_input()` helpers.
- `tests/unit/test_transition_module.py` — `create_manifest` / `create_task_reports` / `run_transition` multi-module subprocess harness.

**Feature Archetype:** Extension. Adds enforcement to existing hooks/scripts; existing behavior is preserved except one advisory hook (`sdd-skill-enforcement-hook.sh`) is promoted to blocking. **No code is removed** (the skill-hook's `additionalContext` JSON emission is replaced in place by a stderr+`exit 2` path; nothing external consumed it). No obsolescence — therefore **no Obsolescence Verification task**.

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| Modified | `skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh` | Tighten detection regex; add `SUPERPOWERS_SDD_BYPASS`; `exit 2` on block (was `exit 0` + advisory inject) | Registered at `settings.json:78` (Write\|Edit). Live hook resolves to the **main checkout** — change takes effect at merge. No other consumer of its output. |
| Modified | `skills/subagent-driven-development/scripts/controller-checkpoint.py` | `find_report_file` + `find_all_report_files` recurse into `archive-*/` | Callers: Check 3 `all_tasks_have_reports`, Check 4 `all_reports_complete`, `estimate_context_load`. Intentionally-flat lookups must NOT change. |
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Check 4c skip-guard (N3a); Check 5 archive glob (N10) | `check_report_file` accepts space-separated globs (`ls $pattern`). Do NOT modify `task_report_glob`. |
| Modified | `skills/subagent-driven-development/scripts/transition-module.py` | `_has_dispatch_provenance` + `_verification_task_ids_from_file` helpers; wire into `validate_module_completion`; recompute `context_summary_at` in `transition()` (N11) | Runs at transition Step 1 (live log intact). Imports PyYAML (inside helper) — runs via `.venv` python in tests. |
| New | `tests/unit/test_sdd_skill_enforcement.py` | Create | Behavioral tests for the promoted hook (none existed). |
| New | `tests/unit/test_checkpoint_archive_aware.py` | Create | Archive-aware lookup tests + flat-lookup regression. |
| New | `tests/unit/test_sdd_hook_hardening.py` | Create | Check 4c skip-guard + Check 5 archive-glob tests. |
| Modified | `tests/unit/test_transition_module.py` | Add provenance to `create_task_reports`; add provenance/minimum/verification tests | Existing tests break without the provenance update (they create reports but no log entries). |
| New | `tests/unit/test_ssot_minimum_agreement.py` | Create | Cross-language agreement matrix (hook ↔ validator) on the file-based minimum signal. |
| Modified | `tests/integration/sdd-e2e-test.sh` | Provenance in Step 4; new Step 11 (module-2-first-task post-transition) | Step 4 transition breaks without provenance after N3b lands. |
| Modified | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | Document new behavior; mark N3/N4/N10 done | Test counts in CLAUDE.md change. |

## File Structure

Each task owns one production file (or one new test file). The two production files touched by more than one component — `sdd-pre-dispatch-hook.sh` (N3a + N10) — are deliberately combined into a single task (Task 2) so no file is co-owned by parallel tasks. Test files are partitioned one-per-task; the only shared production-test file, `test_transition_module.py`, is owned solely by Task 3.

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 0 | `skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh`, `tests/unit/test_sdd_skill_enforcement.py` | — | — |
| Task 1 | `skills/subagent-driven-development/scripts/controller-checkpoint.py`, `tests/unit/test_checkpoint_archive_aware.py` | — | Task 0 |
| Task 2 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`, `tests/unit/test_sdd_hook_hardening.py` | `sdd_test_helpers.py` | Task 1 |
| Task 3 | `skills/subagent-driven-development/scripts/transition-module.py`, `tests/unit/test_transition_module.py` | `controller-checkpoint.py` (pattern) | Task 2 |
| Task 4 | `tests/unit/test_ssot_minimum_agreement.py` | `sdd-pre-dispatch-hook.sh`, `transition-module.py`, `sdd_test_helpers.py` | Task 2, Task 3 |
| Task 5 | `tests/integration/sdd-e2e-test.sh` | all scripts | Task 2, Task 3 |
| Task 6 | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | reports/ | Task 4, Task 5 |
| Task 7 | — (read-only verification) | all test suites | Task 6 |

Each file appears in exactly one task's "Owned Files" column. No two tasks write the same file.

## Intentionally Flat — DO NOT make these archive-aware

The spec scopes archive-awareness to **exactly two** lookups (N4's `find_report_file`/`find_all_report_files` and N10's Check 5 Task-0 glob). Every other report glob stays flat **by design**. An implementer or reviewer who "helpfully" makes any of the following archive-aware is **expanding scope past the approved spec** and introducing a bug:

- `controller-checkpoint.py` → `detect_stale_artifacts` (pre-execution stale scan — must NOT see archived reports, or it would warn forever).
- `controller-checkpoint.py` → `_review_tiers_per_task` (Check 7 minimum-tier ratio — flat by spec; archived module reviews are out of the active ratio).
- `controller-checkpoint.py` → `_check_verification_git_reality`'s dispatch-log read (Check 9 — reads the live log only).
- `sdd-pre-dispatch-hook.sh` → Check 3b (non-standard-naming scan) and Check 7 (context-load `for rf in "${REPORTS_DIR}"/*.md` loop).

---

### Task 0: Promote sdd-skill-enforcement-hook.sh to blocking

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh`
- Test: `tests/unit/test_sdd_skill_enforcement.py` (create)

**Pattern References:** `bypass-env-var` (mirror `SUPERPOWERS_VALIDATOR_BYPASS`), `bash-hook-subprocess-test` (subprocess `run_hook` style).

**Context:** Today this hook emits `additionalContext` and `exit 0` (advisory). The spec promotes it to blocking: explicit SDD imperative + impl-file + skill-not-loaded + no bypass ⇒ `exit 2`. The detection regex `(invoke|use|run|follow|start|let'?s use)\b.{0,20}(subagent-driven-development|sdd)` has been **verified to work and discriminate correctly under both ugrep 7.5 and stock `/usr/bin/grep -iE`** (BSD) — imperatives match, casual mentions ("reading about subagent-driven-development", "the SDD hook") do not. Keep the `SKILL_LOADED` allow, the impl-file path filter, and all early exits.

- [x] **Step 1: Write the failing tests** in `tests/unit/test_sdd_skill_enforcement.py`

```python
"""C5: sdd-skill-enforcement-hook.sh promoted to blocking.
Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_skill_enforcement.py -v
"""
import json
import os
import subprocess

HOOK_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "sdd-skill-enforcement-hook.sh",
))


def _transcript(tmp_path, user_text, skill_loaded=False):
    """Write a JSONL transcript with one user line (+ optional Skill tool line).

    IMPORTANT: emit COMPACT JSON (separators=(",", ":")). The hook greps the
    transcript for the literal `"role":"user"` and `"name":"Skill"` (no spaces) —
    matching real Claude Code transcripts. json.dumps' default spacing
    (`"role": "user"`) would NOT match the hook's grep, so the hook would
    short-circuit at its early `exit 0` and the block tests could never go GREEN.
    """
    sep = (",", ":")
    lines = [json.dumps({"role": "user", "content": user_text}, separators=sep)]
    if skill_loaded:
        lines.append(json.dumps({"role": "assistant",
                                 "content": [{"type": "tool_use", "name": "Skill",
                                              "input": {"skill": "superpowers:subagent-driven-development"}}]},
                                separators=sep))
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(lines) + "\n")
    return str(p)


def run_hook(file_path, transcript_path, env_extra=None):
    payload = json.dumps({"tool_input": {"file_path": file_path},
                          "transcript_path": transcript_path})
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", HOOK_PATH], input=payload,
                          capture_output=True, text=True, timeout=10, env=env)


def test_blocks_when_sdd_requested_skill_not_loaded(tmp_path):
    t = _transcript(tmp_path, "please invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 2, f"stdout={r.stdout} stderr={r.stderr}"
    assert "subagent-driven-development" in r.stderr


def test_allows_when_skill_loaded(tmp_path):
    t = _transcript(tmp_path, "let's use SDD", skill_loaded=True)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0


def test_casual_mention_does_not_block(tmp_path):
    t = _transcript(tmp_path, "I was reading about subagent-driven-development in the docs", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0


def test_non_impl_file_does_not_block(tmp_path):
    t = _transcript(tmp_path, "invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("docs/notes.md", t)
    assert r.returncode == 0


def test_bypass_env_var_recovers(tmp_path):
    t = _transcript(tmp_path, "invoke subagent-driven-development", skill_loaded=False)
    r = run_hook("src/app/feature.py", t, env_extra={"SUPERPOWERS_SDD_BYPASS": "1"})
    assert r.returncode == 0
    assert "SUPERPOWERS_SDD_BYPASS" in r.stderr


def test_no_sdd_request_allows(tmp_path):
    t = _transcript(tmp_path, "fix the login bug", skill_loaded=False)
    r = run_hook("src/app/feature.py", t)
    assert r.returncode == 0
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_skill_enforcement.py -v`
Expected: `test_blocks_*` FAILS (current hook returns 0, not 2); `test_bypass_*` FAILS (no bypass handling yet); `test_casual_mention_*` likely FAILS (current bare-mention regex matches it but current hook returns 0 anyway, so it may pass vacuously — the block tests are the real RED).

- [x] **Step 3: Tighten the detection regex.** In `sdd-skill-enforcement-hook.sh`, replace the SDD-request grep (currently `grep ... | grep -qiE '(subagent-driven-development|SDD|superpowers:subagent-driven|invoke.*sdd|use.*sdd|follow.*sdd)'`) with the imperative-only pattern:

```bash
  # Require an explicit SDD imperative (not a bare mention) to avoid false blocks.
  # Verified under ugrep 7.5 and stock /usr/bin/grep -iE (BSD): imperatives match,
  # casual mentions ("reading about subagent-driven-development", "the SDD hook") do not.
  if grep '"role":"user"' "$TRANSCRIPT_PATH" | grep -qiE "(invoke|use|run|follow|start|let'?s use)\b.{0,20}(subagent-driven-development|sdd)" 2>/dev/null; then
    SDD_REQUESTED=true
  fi
```

- [x] **Step 4: Add the bypass + block.** Replace the advisory `additionalContext` JSON emission (the final `cat << HOOKJSON ... HOOKJSON; exit 0` block) with a `SUPERPOWERS_SDD_BYPASS` check followed by a blocking exit. Keep the same warning text on stderr:

```bash
# ─── SDD requested but skill NOT loaded — bypass or block ─────────────────
WARNING_MSG="BLOCKED: The user requested subagent-driven-development but you have not loaded the skill via the Skill tool. You are writing implementation code directly, bypassing the SDD review cycle, enforcement hooks, and quality gates. Load the skill now: invoke superpowers:subagent-driven-development. Direct implementation without the skill means zero spec reviews, zero code quality reviews, and no hook enforcement."

# Emergency escape hatch (mirrors SUPERPOWERS_VALIDATOR_BYPASS): allow + warn.
if [ -n "${SUPERPOWERS_SDD_BYPASS:-}" ]; then
  echo "WARNING: $WARNING_MSG (bypassed via SUPERPOWERS_SDD_BYPASS)" >&2
  exit 0
fi

echo "$WARNING_MSG" >&2
exit 2
```

> Note: this hook uses `set -o pipefail` but **not** `set -u` today; `${SUPERPOWERS_SDD_BYPASS:-}` is written defensively regardless. Do not add `set -u` (jq pipe chains produce empty vars — see CLAUDE.md Hook Development Gotchas).

- [x] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_skill_enforcement.py -v`
Expected: all 6 PASS.

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh tests/unit/test_sdd_skill_enforcement.py
git commit -m "feat(sdd): promote skill-enforcement hook to blocking with bypass"
```

---

### Task 1: Archive-aware report lookups in controller-checkpoint.py

**Files:**
- Modify: `skills/subagent-driven-development/scripts/controller-checkpoint.py` (`find_report_file`, `find_all_report_files`)
- Test: `tests/unit/test_checkpoint_archive_aware.py` (create)

**Context (N4):** After a module transition, the completed module's reports live under `reports/archive-<module>/`. The pre-completion gate (Check 3 `all_tasks_have_reports`, Check 4 `all_reports_complete`) calls these two functions and currently only globs the flat `reports_dir`, so it FAILs once a module is archived. Make exactly these two functions recurse into `archive-*/`. **Read the "Intentionally Flat" section above — do not touch any other lookup.** `sorted(matches)[-1]` makes the **live** copy win when a report exists in both (`reports/task-000-...` sorts after `reports/archive-*/task-000-...`).

- [x] **Step 1: Write the failing tests** in `tests/unit/test_checkpoint_archive_aware.py`

```python
"""N4: controller-checkpoint.py find_report_file/find_all_report_files recurse into archive-*/.
Run: .venv/bin/python3 -m pytest tests/unit/test_checkpoint_archive_aware.py -v
"""
import importlib.util
import os

_SPEC = importlib.util.spec_from_file_location(
    "controller_checkpoint",
    os.path.join(os.path.dirname(__file__), "..", "..",
                 "skills", "subagent-driven-development", "scripts", "controller-checkpoint.py"),
)
cc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cc)


def _impl(p):
    p.write_text("x" * 80)


def test_find_report_file_in_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    assert cc.find_report_file(str(reports), 0).endswith("archive-Core/task-000-implementer-report.md")


def test_find_report_file_prefers_live_over_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    _impl(reports / "task-000-implementer-report.md")
    # Live copy must win (sorts last).
    assert cc.find_report_file(str(reports), 0) == str(reports / "task-000-implementer-report.md")


def test_find_all_report_files_includes_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    _impl(reports / "task-002-implementer-report.md")
    found = cc.find_all_report_files(str(reports))
    bases = sorted(os.path.basename(f) for f in found)
    assert bases == ["task-000-implementer-report.md", "task-002-implementer-report.md"]


def test_detect_stale_artifacts_stays_flat(tmp_path):
    # Regression: archived reports must NOT trip the pre-execution stale scan.
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    dev = tmp_path / "deviations.md"; dev.write_text("")  # empty = no content
    result = cc.detect_stale_artifacts(str(dev), str(reports))
    assert result["status"] == "OK", result
```

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_checkpoint_archive_aware.py -v`
Expected: `test_find_report_file_in_archive` and `test_find_all_report_files_includes_archive` FAIL (flat glob misses archive); the other two PASS (already correct).

- [x] **Step 3: Make the two lookups archive-aware.** Replace `find_report_file` and `find_all_report_files`:

```python
def find_report_file(reports_dir: str, task_number: int) -> str:
    """Return the path to the implementer report for the given task, or "" if not found.

    Searches the live reports dir AND archived module dirs (reports/archive-*/).
    When a report exists in both, the live copy wins (sorts last). N4.
    """
    pattern = report_filename_pattern(task_number)
    matches = glob.glob(os.path.join(reports_dir, pattern))
    matches += glob.glob(os.path.join(reports_dir, "archive-*", pattern))
    return sorted(matches)[-1] if matches else ""


def find_all_report_files(reports_dir: str) -> list:
    """Return all implementer report files, live AND archived (reports/archive-*/). N4."""
    pattern = "task-*-implementer-report*"
    matches = glob.glob(os.path.join(reports_dir, pattern))
    matches += glob.glob(os.path.join(reports_dir, "archive-*", pattern))
    return sorted(matches)
```

- [x] **Step 4: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_checkpoint_archive_aware.py -v`
Expected: all 4 PASS.

- [x] **Step 5: Confirm no regression in the existing pre-completion suite**

Run: `.venv/bin/python3 -m pytest tests/unit/test_pre_completion_gates.py tests/unit/test_controller_checkpoint_stale.py -v`
Expected: all PASS.

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/scripts/controller-checkpoint.py tests/unit/test_checkpoint_archive_aware.py
git commit -m "feat(sdd): archive-aware implementer-report lookups in controller-checkpoint (N4)"
```

---

### Task 2: Harden sdd-pre-dispatch-hook.sh — Check 4c skip-guard + Check 5 archive glob

**Files:**
- Modify: `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (Check 4c block; Check 5 Task-0 glob)
- Test: `tests/unit/test_sdd_hook_hardening.py` (create)

**Pattern References:** `early-skip-guard-chain` (compose N3a as a sibling `elif`, NOT nested in the grep), `bash-hook-subprocess-test`.

**Context (N3a + N10):** After a module transition the live dispatch log is truncated, so the previous task's provenance lives in the archived log. Check 4c must **skip** when `PREV < MANIFEST_TASK_START` (the previous task belongs to a prior/archived module, or precedes a no-Task-0 plan's first task). Boundary provenance is re-verified at transition time by `transition-module.py:validate_module_completion` (the sibling enforcement — Task 3). Separately, Check 5's Task-0 lookup (N10) must also glob `archive-*/` so a Source-Contracts plan still finds an archived Task 0 at module 2.

Skip-guard truth table (verified against the code): module-first-task (`TASK_NUMBER==MANIFEST_TASK_START` ⇒ `PREV=START-1<START`) → skip; no-Task-0 plan (start=1, task 1, `PREV=0<1`) → skip; within-module (`PREV>=START`) → check runs; Task-0 plan (start=0, task 1, `PREV=0`, `0<0` false) → check runs.

- [x] **Step 1: Write the failing tests** in `tests/unit/test_sdd_hook_hardening.py`

```python
"""N3a (Check 4c skip-guard) + N10 (Check 5 archive glob) for sdd-pre-dispatch-hook.sh.
Run: .venv/bin/python3 -m pytest tests/unit/test_sdd_hook_hardening.py -v
"""
import json
import os
import subprocess
from datetime import datetime, timezone

from sdd_test_helpers import make_hook_input, setup_manifest_workspace

HOOK_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh",
))
NOW = "2026-06-01T00:00:00Z"


def run_hook(stdin_data):
    return subprocess.run(["bash", HOOK_PATH], input=stdin_data,
                          capture_output=True, text=True, timeout=10)


def _impl(p):
    p.write_text("x" * 80)


def _full_support(reports, task_num, *, partner=True):
    """Create audit + checkpoint (+ partner review & provenance) so that the ONLY
    gate that could fire for `task_num` is Check 4c. Returns nothing."""
    _impl(reports / "pre-execution-audit.md")
    padded = f"{task_num:03d}"
    (reports / f"checkpoint-pre-dispatch-{padded}.json").write_text(
        json.dumps({"status": "PASS", "phase": "pre-dispatch", "detail": "x" * 60}))
    if partner:
        _impl(reports / f"partner-review-{padded}.md")
        with open(reports / ".dispatch-log", "a") as f:
            f.write(f"{NOW} DISPATCH reviewer task={task_num} type=partner-review\n")


def test_check4c_skipped_for_module_first_task(tmp_path):
    # Module 2 active (task_range starts at 2); empty log (post-truncation).
    # Dispatching task 2 must ALLOW: PREV=1 < START=2 -> skip-guard. Non-vacuous:
    # pre-fix Check 4c looks for `task=1 type=spec-review` in the empty log -> BLOCK.
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(2, 3), total_tasks=4)
    reports = ws["reports_dir"]
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    _full_support(reports, 2)
    r = run_hook(make_hook_input(description="Implement task 2",
                                 prompt="You are implementing task 2", cwd=str(ws["root"])))
    assert r.returncode == 0, f"stderr={r.stderr}"


def test_check4c_enforced_within_module(tmp_path):
    # Within-module dispatch (PREV >= START) still requires provenance.
    # task_range (2,3); dispatch task 3; PREV=2 >= START=2 -> check runs; no
    # task=2 provenance in log -> BLOCK.
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(2, 3), total_tasks=4)
    reports = ws["reports_dir"]
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    # Task 2 reports exist (so N-1 file checks pass) but NO spec/quality provenance.
    for kind in ("implementer-report", "spec-review", "quality-review"):
        _impl(reports / f"task-002-{kind}.md")
    _full_support(reports, 3)
    r = run_hook(make_hook_input(description="Implement task 3",
                                 prompt="You are implementing task 3", cwd=str(ws["root"])))
    assert r.returncode == 2
    assert "spec-review dispatch recorded for Task 2" in r.stderr


def test_check4c_skipped_for_no_task0_single_module(tmp_path):
    # Acceptance criterion #3: no-Task-0 single-module plan starting at Task 1
    # (no transition, no archive). task_range (1,2); dispatch task 1; PREV=0 <
    # START=1 -> skip-guard -> ALLOW. Non-vacuous: pre-fix Check 4c greps the
    # empty log for `task=0 type=spec-review` and BLOCKS, forcing a forged task=0
    # entry. (Check 6b is inert here: TASK_NUMBER=1 is not > 1.)
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(1, 2), total_tasks=2)
    reports = ws["reports_dir"]
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    _full_support(reports, 1)
    r = run_hook(make_hook_input(description="Implement task 1",
                                 prompt="You are implementing task 1", cwd=str(ws["root"])))
    assert r.returncode == 0, f"stderr={r.stderr}"


def test_check5_finds_archived_task0(tmp_path):
    # N10: Source-Contracts plan, Task 0 report archived; dispatching task 2 must
    # NOT block on the Task-0 gate (Check 5 globs archive-*/).
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(2, 3), total_tasks=4)
    root, reports, feat = ws["root"], ws["reports_dir"], ws["feat_dir"]
    # Give the plan real Source Contracts so Check 5 activates.
    plan = feat / "plan.md"
    plan.write_text(plan.read_text().replace("**Source Contracts:** None",
                                             "**Source Contracts:** docs/spec.md"))
    (reports / ".dispatch-log").write_text("# sdd-hook-sentinel abc123\n")
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")     # archived Task 0
    _full_support(reports, 2)
    r = run_hook(make_hook_input(description="Implement task 2",
                                 prompt="You are implementing task 2", cwd=str(root)))
    # Must not block for the Task-0 reason (skip-guard handles Check 4c via PREV<START).
    assert "no Task 0 report found" not in r.stderr.lower()
    assert r.returncode == 0, f"stderr={r.stderr}"
```

> Note for the implementer: `setup_manifest_workspace` initializes git on a feature branch and writes `.active-feature` + manifest + a plan with `### Task N` headers and `**Source Contracts:** None`. `make_hook_input` is imported from `sdd_test_helpers` (already on `sys.path` via `conftest.py`).

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_hook_hardening.py -v`
Expected: `test_check4c_skipped_for_module_first_task`, `test_check4c_skipped_for_no_task0_single_module`, and `test_check5_finds_archived_task0` FAIL (hook blocks); `test_check4c_enforced_within_module` PASSES (already enforced). (4 tests total.)

- [x] **Step 3: Add the Check 4c skip-guard (N3a).** In `sdd-pre-dispatch-hook.sh`, extend the existing short-circuit chain in Check 4c. After the `elif [ "$PREV_TASK_TYPE" = "verification" ]; then` branch and before the final `else`, insert a sibling `elif`:

```bash
  elif [ "$PREV" -lt "$MANIFEST_TASK_START" ] 2>/dev/null; then
    # N3a: PREV belongs to a prior (archived) module, or precedes the module's
    # first task (no-Task-0 plan, start=1). The live dispatch log was truncated
    # at the module boundary, so PREV's provenance lives in the archived log.
    # The completing module's boundary provenance is re-verified at transition
    # time by transition-module.py:validate_module_completion (sibling enforcement).
    : # Skip — boundary provenance verified at transition, not here
```

- [x] **Step 4: Make Check 5's Task-0 lookup archive-aware (N10).** In Check 5, replace the `T0_GLOB=$(task_report_glob "0" "implementer-report")` line with a local glob covering live + archive (do NOT modify the shared `task_report_glob` helper):

```bash
    # N10: cover both the live reports dir and archived module dirs. A multi-
    # module plan with Source Contracts archives Task 0's report under
    # reports/archive-<module>/ at the first transition; Check 5 must still find
    # it. check_report_file runs `ls $pattern`, so space-separated globs work.
    T0_GLOB="${REPORTS_DIR}/task-000-implementer-report* ${REPORTS_DIR}/archive-*/task-000-implementer-report*"
```

- [x] **Step 5: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_hook_hardening.py -v`
Expected: all 3 PASS.

- [x] **Step 6: Confirm no regression in the existing hook suites**

Run: `.venv/bin/python3 -m pytest tests/unit/test_sdd_classification.py tests/unit/test_sdd_hard_gates.py tests/unit/test_sdd_partner_gate.py tests/unit/test_sdd_dispatch_log.py -v`
Expected: all PASS.

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh tests/unit/test_sdd_hook_hardening.py
git commit -m "feat(sdd): Check 4c skip-guard (N3a) + Check 5 archive glob (N10)"
```

---

### Task 3: transition-module.py — provenance, verification exemption, context_summary_at recompute

**Files:**
- Modify: `skills/subagent-driven-development/scripts/transition-module.py` (`validate_module_completion` + `transition()`; add two helpers)
- Modify: `tests/unit/test_transition_module.py` (update `create_task_reports` + `create_manifest`; add tests)

**Pattern References:** `verification-task-id-parser` (mirror `controller-checkpoint.py:_verification_task_ids`), `transition-test-harness`.

**Context (N3b + verification exemption + N11):** `validate_module_completion` runs at transition **Step 1**, while the live dispatch log is still intact. Extend it so that, for each completing-module task, it verifies dispatch-log provenance (the same `task=<id> type=<review>` substring Check 4c greps) — refusing to archive/truncate when provenance is missing. Quality-review provenance is **waived when the file `task-NNN-quality-review-minimum-tier.md` exists** (the *file* signal — NOT the `review_tier:minimum` plan declaration). A per-task **`task_type: verification`** exemption (mirroring the hook) skips spec/quality/provenance for verification tasks — they file an implementer report only. **N11 (folded in):** `transition()` also recomputes `enforcement.context_summary_at` for the next module so Check 6b does not fire early in later modules.

- [x] **Step 1: Write/adjust the failing tests** in `tests/unit/test_transition_module.py`.

First, update the existing `create_task_reports` helper so existing tests keep passing (it must now also write provenance to the live log, since N3b requires it):

```python
def create_task_reports(reports_dir, task_ids):
    """Create implementer, spec-review, quality-review reports AND dispatch-log
    provenance for each task (N3b requires provenance at transition time)."""
    log = reports_dir / ".dispatch-log"
    for tid in task_ids:
        padded = f"{tid:03d}"
        for report_type in ["implementer-report", "spec-review", "quality-review"]:
            (reports_dir / f"task-{padded}-{report_type}.md").write_text(
                f"# {report_type} for task {tid}\n" + "x" * 100)
        with open(log, "a") as f:
            f.write(f"2026-06-01T00:00:00Z DISPATCH reviewer task={tid} type=spec-review\n")
            f.write(f"2026-06-01T00:00:00Z DISPATCH reviewer task={tid} type=quality-review\n")
```

Then add new tests:

```python
def test_blocks_when_provenance_missing(tmp_path):
    manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
    # Reports present but NO provenance lines (log only has the sentinel).
    for tid in [0, 1, 2, 3]:
        padded = f"{tid:03d}"
        for rt in ["implementer-report", "spec-review", "quality-review"]:
            (reports_dir / f"task-{padded}-{rt}.md").write_text(f"# {rt}\n" + "x" * 100)
    result = run_transition(manifest_path, "Core", "API")
    assert result.returncode == 1
    assert "not provenance-logged" in result.stderr


def test_minimum_tier_file_waives_quality_provenance(tmp_path):
    manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
    log = reports_dir / ".dispatch-log"
    for tid in [0, 1, 2, 3]:
        padded = f"{tid:03d}"
        (reports_dir / f"task-{padded}-implementer-report.md").write_text("# impl\n" + "x" * 100)
        (reports_dir / f"task-{padded}-spec-review.md").write_text("# spec\n" + "x" * 100)
        # Quality via the FILE signal (minimum-tier), NOT a full quality review.
        (reports_dir / f"task-{padded}-quality-review-minimum-tier.md").write_text("# min\n" + "x" * 100)
        with open(log, "a") as f:
            f.write(f"2026-06-01T00:00:00Z DISPATCH reviewer task={tid} type=spec-review\n")
            # NO quality-review provenance line — the file signal must waive it.
    result = run_transition(manifest_path, "Core", "API")
    assert result.returncode == 0, f"stderr={result.stderr}"


def test_verification_task_exempt_from_reviews(tmp_path):
    manifest_path, reports_dir, feat_dir = create_manifest(tmp_path)
    # Declare task 3 as verification in the completing module's plan file.
    (feat_dir / "m1.md").write_text(
        "---\nschema_version: 1\ntasks:\n"
        "  - id: 0\n  - id: 1\n  - id: 2\n  - id: 3\n    task_type: verification\n---\n# M1\n")
    # Tasks 0-2 full (reports + provenance); task 3 implementer report ONLY.
    create_task_reports(reports_dir, [0, 1, 2])
    (reports_dir / "task-003-implementer-report.md").write_text("# impl\n" + "x" * 100)
    result = run_transition(manifest_path, "Core", "API")
    assert result.returncode == 0, f"stderr={result.stderr}"
```

> **N11 test seed (also in Step 1):** in `create_manifest`, change `"enforcement": profile["enforcement"]` to `"enforcement": {**profile["enforcement"], "context_summary_at": 2}` (a fresh dict so the shared `TIER_PROFILES` is never mutated; `2` = module-1 midpoint). Then add to the **existing** `test_manifest_updated_after_transition`: `assert updated["enforcement"]["context_summary_at"] == 6` (module-2 midpoint — proves the N11 recompute). The verification test writes `m1.md`; the other tests leave it absent, so `_verification_task_ids_from_file` returns an empty set — backward compatible.

- [x] **Step 2: Run to verify failure**

Run: `.venv/bin/python3 -m pytest tests/unit/test_transition_module.py -v`
Expected: the three new tests FAIL (no provenance enforcement yet; the verification test fails because reviews are still demanded). Existing tests PASS (helper now writes provenance).

- [x] **Step 3: Add the two helpers** to `transition-module.py` (near `_find_module`):

```python
def _has_dispatch_provenance(dispatch_log_path: str, task_id: int, review_type: str) -> bool:
    """True if the live log has a `task=<id> type=<type>` line (mirrors hook Check 4c).
    Called at transition Step 1, before the Step 5 truncation — live log intact."""
    if not os.path.isfile(dispatch_log_path):
        return False
    needle = f"task={task_id} type={review_type}"
    try:
        with open(dispatch_log_path, encoding="utf-8") as fh:
            return any(needle in line for line in fh)
    except OSError:
        return False


def _verification_task_ids_from_file(plan_file: str) -> set:
    """task_type=='verification' IDs from a plan file's frontmatter
    (mirrors controller-checkpoint.py:_verification_task_ids)."""
    import yaml  # PyYAML available via the .venv python the hook/tests use

    if not os.path.isfile(plan_file):
        return set()
    try:
        content = Path(plan_file).read_text(encoding="utf-8")
    except OSError:
        return set()
    if not content.startswith("---"):
        return set()
    end = content.find("---", 3)
    if end == -1:
        return set()
    try:
        fm = yaml.safe_load(content[3:end])
    except Exception:
        return set()
    tasks = fm.get("tasks") if isinstance(fm, dict) else None
    if not isinstance(tasks, list):
        return set()
    return {
        t["id"]
        for t in tasks
        if isinstance(t, dict)
        and t.get("task_type") == "verification"
        and isinstance(t.get("id"), int)
    }
```

- [x] **Step 4: Wire provenance + exemption into `validate_module_completion`.** Inside the function, after resolving `module` and `reports_dir`, add the dispatch log path and the verification-id set, then extend the per-task loop:

```python
    reports_dir = os.path.join(git_root, manifest.paths.reports_dir)
    dispatch_log = os.path.join(git_root, manifest.paths.dispatch_log)
    pr = manifest.process_requirements

    # Per-task verification exemption (mirrors sdd-pre-dispatch-hook.sh): read the
    # completing module's own plan file for task_type declarations.
    verif_ids: set = set()
    if module.file:
        module_plan = os.path.join(git_root, manifest.paths.feature_dir, module.file)
        verif_ids = _verification_task_ids_from_file(module_plan)

    for task_id in module.task_ids:
        padded = f"{task_id:03d}"
        impl_report = os.path.join(reports_dir, f"task-{padded}-implementer-report.md")
        if not os.path.isfile(impl_report) or os.path.getsize(impl_report) < 50:
            errors.append(f"Task {task_id}: missing or empty implementer report")

        if task_id in verif_ids:
            continue  # verification task: implementer report only; no spec/quality/provenance

        if pr.spec_review_mode != "skip":
            spec_report = os.path.join(reports_dir, f"task-{padded}-spec-review.md")
            if not os.path.isfile(spec_report) or os.path.getsize(spec_report) < 50:
                errors.append(f"Task {task_id}: missing or empty spec review")
            elif not _has_dispatch_provenance(dispatch_log, task_id, "spec-review"):
                errors.append(f"Task {task_id}: spec review not provenance-logged")

        if pr.quality_review_mode != "skip":
            quality_report = os.path.join(reports_dir, f"task-{padded}-quality-review.md")
            quality_min = os.path.join(reports_dir, f"task-{padded}-quality-review-minimum-tier.md")
            has_full = os.path.isfile(quality_report) and os.path.getsize(quality_report) >= 50
            has_min = os.path.isfile(quality_min) and os.path.getsize(quality_min) >= 50
            if not (has_full or has_min):
                errors.append(f"Task {task_id}: missing or empty quality review")
            elif has_min:
                pass  # file-based minimum signal waives quality-review provenance
            elif not _has_dispatch_provenance(dispatch_log, task_id, "quality-review"):
                errors.append(f"Task {task_id}: quality review not provenance-logged")

    return errors
```

Replace the existing per-task loop body with the above (it supersedes the old spec/quality file-only checks).

- [x] **Step 5: Recompute `context_summary_at` on transition (N11).** In `transition()`'s Step 4 manifest-update block, immediately after the `data["midpoint"] = compute_midpoint(...)` line, add:

```python
    # N11: recompute context_summary_at for the new module's range. Without this
    # it stays pinned to the completed module's midpoint and Check 6b fires early
    # in later modules. Only when the tier uses it (non-null; micro leaves None).
    if data.get("enforcement", {}).get("context_summary_at") is not None:
        data["enforcement"]["context_summary_at"] = data["midpoint"]
```

- [x] **Step 6: Run to verify pass**

Run: `.venv/bin/python3 -m pytest tests/unit/test_transition_module.py -v`
Expected: all tests PASS (existing + the 3 new provenance/verification tests + the N11 assertion on `test_manifest_updated_after_transition`).

- [x] **Step 7: Commit**

```bash
git add skills/subagent-driven-development/scripts/transition-module.py tests/unit/test_transition_module.py
git commit -m "feat(sdd): transition provenance + verification exemption (N3b) + context_summary_at recompute (N11)"
```

---

### Task 4: SSOT agreement test for the file-based minimum signal

**Files:**
- Test: `tests/unit/test_ssot_minimum_agreement.py` (create)

**Pattern References:** `bash-hook-subprocess-test`, `transition-test-harness`.

**Context (D6):** Two enforcement sites consult the **file-based** minimum signal (`task-NNN-quality-review-minimum-tier.md`) to decide whether quality-review dispatch provenance is required: the hook's **Check 4c** (per-dispatch, on PREV) and `transition-module.py:validate_module_completion` (per-task, at transition). This test asserts both sites reach the **same require/exempt decision** across the matrix (minimum-file present/absent × quality-provenance present/absent), keyed strictly on the file signal. It compares the *decision*, not the two invocation contexts — each side is driven via subprocess and we check for its own quality-provenance error string.

- [x] **Step 1: Write the test** in `tests/unit/test_ssot_minimum_agreement.py`

```python
"""D6: SSOT agreement on the FILE-based minimum signal between
sdd-pre-dispatch-hook.sh (Check 4c) and transition-module.py
(validate_module_completion). Both must require quality-review provenance UNLESS
task-NNN-quality-review-minimum-tier.md exists.
Run: .venv/bin/python3 -m pytest tests/unit/test_ssot_minimum_agreement.py -v
"""
import json
import os
import subprocess

import pytest
from sdd_test_helpers import make_hook_input, setup_manifest_workspace

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", "sdd-pre-dispatch-hook.sh")
TRANSITION = os.path.join(ROOT, "skills", "subagent-driven-development", "scripts", "transition-module.py")
PYTHON = os.path.join(ROOT, ".venv", "bin", "python3")
NOW = "2026-06-01T00:00:00Z"


def _impl(p):
    p.write_text("x" * 80)


def _hook_requires_quality_prov(tmp_path, min_file, provenance):
    """Decision from Check 4c: does the hook block on MISSING quality provenance
    for the previous task? Set up a single module [0,1]; dispatch task 1 (PREV=0,
    within-module so Check 4c runs). Returns True if it blocks for quality."""
    ws = setup_manifest_workspace(tmp_path, tier="standard", task_range=(0, 1), total_tasks=2)
    reports = ws["reports_dir"]
    reports.mkdir(exist_ok=True)
    (reports / ".dispatch-log").parent.mkdir(parents=True, exist_ok=True)
    log = reports / ".dispatch-log"
    log.write_text("# sdd-hook-sentinel abc123\n")
    # Task 0 fully present + spec provenance (isolate the quality decision).
    for kind in ("implementer-report", "spec-review"):
        _impl(reports / f"task-000-{kind}.md")
    with open(log, "a") as f:
        f.write(f"{NOW} DISPATCH reviewer task=0 type=spec-review\n")
    if min_file:
        _impl(reports / "task-000-quality-review-minimum-tier.md")
    else:
        _impl(reports / "task-000-quality-review.md")
    if provenance:
        with open(log, "a") as f:
            f.write(f"{NOW} DISPATCH reviewer task=0 type=quality-review\n")
    # Support files so only Check 4c quality can fire for task 1.
    _impl(reports / "pre-execution-audit.md")
    (reports / "checkpoint-pre-dispatch-001.json").write_text(
        json.dumps({"status": "PASS", "detail": "x" * 60}))
    _impl(reports / "partner-review-001.md")
    with open(log, "a") as f:
        f.write(f"{NOW} DISPATCH reviewer task=1 type=partner-review\n")
    r = subprocess.run(["bash", HOOK],
                       input=make_hook_input(description="Implement task 1",
                                             prompt="You are implementing task 1",
                                             cwd=str(ws["root"])),
                       capture_output=True, text=True, timeout=10)
    return "quality-review dispatch recorded for Task 0" in r.stderr


def _transition_requires_quality_prov(tmp_path, min_file, provenance):
    """Decision from validate_module_completion: does the transition error on
    MISSING quality provenance for task 0 of the completing module?"""
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    feat = tmp_path / "docs" / "imp-plans" / "f"; (feat / "reports").mkdir(parents=True)
    reports = feat / "reports"
    (feat / "deviations.md").write_text("# Deviations\n")
    log = reports / ".dispatch-log"; log.write_text("# sdd-hook-sentinel abc\n")
    _impl(reports / "task-000-implementer-report.md")
    _impl(reports / "task-000-spec-review.md")
    with open(log, "a") as f:
        f.write(f"{NOW} DISPATCH reviewer task=0 type=spec-review\n")
    if min_file:
        _impl(reports / "task-000-quality-review-minimum-tier.md")
    else:
        _impl(reports / "task-000-quality-review.md")
    if provenance:
        with open(log, "a") as f:
            f.write(f"{NOW} DISPATCH reviewer task=0 type=quality-review\n")
    import sys
    sys.path.insert(0, os.path.join(ROOT, "skills", "scripts", "models"))
    from sdd_session import TIER_PROFILES
    profile = TIER_PROFILES["standard"]
    manifest = {
        "schema_version": 1, "tier": "standard",
        "paths": {"feature_dir": str(feat.relative_to(tmp_path)),
                  "reports_dir": str(reports.relative_to(tmp_path)),
                  "dispatch_log": str(log.relative_to(tmp_path)),
                  "deviations_file": str((feat / "deviations.md").relative_to(tmp_path))},
        "plan_file": str((feat / "plan.md").relative_to(tmp_path)),
        "active_module_id": 1, "active_module_file": "m1.md",
        "task_range": [0, 0], "total_tasks": 2, "midpoint": 0,
        "enforcement": profile["enforcement"], "process_requirements": profile["process_requirements"],
        "completed_modules": [], "module_reports_archived": False,
        "modules": [{"id": 1, "title": "Core", "file": "m1.md", "task_ids": [0]},
                    {"id": 2, "title": "API", "file": "m2.md", "task_ids": [1]}],
        "dispatch_log_sentinel": False,
    }
    mp = feat / ".sdd-session.json"; mp.write_text(json.dumps(manifest))
    r = subprocess.run([PYTHON, TRANSITION, "--manifest", str(mp),
                       "--completed-module", "Core", "--next-module", "API"],
                      capture_output=True, text=True, timeout=10)
    return "Task 0: quality review not provenance-logged" in r.stderr


@pytest.mark.parametrize("min_file,provenance", [(True, False), (False, False), (False, True), (True, True)])
def test_minimum_signal_agreement(tmp_path, min_file, provenance):
    hook = _hook_requires_quality_prov(tmp_path / "hook", min_file, provenance)
    trans = _transition_requires_quality_prov(tmp_path / "trans", min_file, provenance)
    assert hook == trans, (
        f"Disagreement (min_file={min_file}, provenance={provenance}): "
        f"hook_requires={hook} transition_requires={trans}")
    # Anchor the expected decision: require ONLY when no min-file AND no provenance.
    assert hook == (not min_file and not provenance)
```

- [x] **Step 2: Run the test**

Run: `.venv/bin/python3 -m pytest tests/unit/test_ssot_minimum_agreement.py -v`
Expected: all 4 parametrized cases PASS (depends on Task 2's Check 4c and Task 3's validate_module_completion both being in place).

- [x] **Step 3: Commit**

```bash
git add tests/unit/test_ssot_minimum_agreement.py
git commit -m "test(sdd): SSOT agreement on file-based minimum signal (D6)"
```

---

### Task 5: E2E — provenance in transition + module-2-first-task post-transition

**Files:**
- Modify: `tests/integration/sdd-e2e-test.sh`

**Context:** Two changes. (a) Step 4 must append dispatch-log provenance for the Module 1 tasks, or the Step 5 transition now FAILs under N3b. (b) A new step dispatches the **module-2 first task (task 2) through the live hook after the transition** and asserts it is allowed — the live proof of BOTH the N3a skip-guard (pre-fix, Check 4c looks for `task=1` provenance in the truncated/empty log and blocks) AND the N11 recompute (pre-fix, `context_summary_at` stays 1 and Check 6b blocks task 2; the step also asserts the manifest recomputed it to 3). N10's archived-Task-0 path is covered by Task 2's unit test (`test_check5_finds_archived_task0`).

- [x] **Step 1: Add provenance to Step 4.** In the Module-1 report-creation loop (the `for tid in 0 1; do ... done` block around the existing Step 4), append provenance lines to the dispatch log so the transition validator passes:

```bash
for tid in 0 1; do
  padded=$(printf "%03d" $tid)
  for kind in implementer-report spec-review quality-review; do
    { echo "# ${kind} for task ${tid}"; echo ""; printf 'x%.0s' {1..100}; } > "$FEAT/reports/task-${padded}-${kind}.md"
  done
  # N3b: transition now verifies dispatch-log provenance before truncating.
  echo "2026-06-01T00:00:00Z DISPATCH reviewer task=${tid} type=spec-review" >> "$FEAT/reports/.dispatch-log"
  echo "2026-06-01T00:00:00Z DISPATCH reviewer task=${tid} type=quality-review" >> "$FEAT/reports/.dispatch-log"
done
```

- [x] **Step 2: Add the post-transition module-2-first-task step.** After the existing Step 7 (post-transition checkpoint) — before the rt-feature Step 8 block — insert a new step that drives the live hook. Keep the existing `=== STEP N ===` numbering style; renumber subsequent steps' echo labels if you prefer, or label this `STEP 7b`:

```bash
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
```

> Note: the hook no-ops (exit 0) if `jq` is missing — this step assumes `jq` is installed (it is on the dev machine; the hook depends on it). The `set +e/-e` dance is required because the harness runs under `set -e` + an ERR trap.

- [x] **Step 3: Update the final banner.** Change the closing `echo "E2E PIPELINE PASS - 10 steps composed correctly"` to reflect the new count (11 steps).

- [x] **Step 4: Run the e2e**

Run: `bash tests/integration/sdd-e2e-test.sh`
Expected: `E2E PIPELINE PASS - 11 steps composed correctly`.

- [x] **Step 5: Commit**

```bash
git add tests/integration/sdd-e2e-test.sh
git commit -m "test(sdd): e2e provenance in transition + module-2-first-task post-transition"
```

---

### Task 6: Update documentation (CLAUDE.md, manifest, BACKLOG)

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/ARaymond-customization-manifest.md`
- Modify: `docs/process-improvement-findings/BACKLOG.md`

`review_tier: minimum` — mechanical documentation edits, no behavior change.

**Context:** Document the five components (plus the folded-in N11 recompute) so a future session knows they exist. Per CLAUDE.md "Documentation Maintenance," update the affected sections and refresh test counts. Read each target section first; add (do not rewrite) the facts below.

- [x] **Step 1: CLAUDE.md — "Hooks-Based Enforcement" section.** Add bullets recording:
  - N3a: Check 4c now skips when `PREV < MANIFEST_TASK_START` (module-first task, or no-Task-0 plan); boundary provenance is re-verified at transition time.
  - N10: Check 5's Task-0 lookup now globs `archive-*/` (a Source-Contracts plan finds an archived Task 0 at module 2). Local glob only — `task_report_glob` unchanged.
  - N3b: `transition-module.py:validate_module_completion` verifies dispatch-log provenance for each completing-module task before truncation, with a file-based minimum-tier waiver and a `task_type:verification` per-task exemption.
  - N11: `transition-module.py:transition()` recomputes `enforcement.context_summary_at` for the next module on transition (was pinned to the completed module's midpoint, firing Check 6b early in later modules).
  - N4: `controller-checkpoint.py` `find_report_file`/`find_all_report_files` recurse into `archive-*/` (pre-completion passes with archived reports). Name the intentionally-flat lookups.
  - C5: `sdd-skill-enforcement-hook.sh` is now **blocking** (`exit 2`) on an explicit SDD imperative + impl-file + skill-not-loaded; `SUPERPOWERS_SDD_BYPASS` is the escape hatch.

- [x] **Step 2: CLAUDE.md — "Hook Development Gotchas" section.** Add: `SUPERPOWERS_SDD_BYPASS` env var (allow + stderr warning) mirrors `SUPERPOWERS_VALIDATOR_BYPASS`. Note the C5 detection regex `(invoke|use|run|follow|start|let'?s use)\b.{0,20}(...)` is verified under both ugrep and stock BSD `/usr/bin/grep -iE`.

- [x] **Step 3: CLAUDE.md — "Pipeline Flexibility" Known follow-ups.** Mark **N3 (N3a+N3b)**, **N4**, **N10**, and **N11** resolved by this feature. Update the "Testing" line's unit-test count (it increases by the number of new tests added in Tasks 0–4 — compute the real number from `pytest` collection, do not guess).

- [x] **Step 4: docs/ARaymond-customization-manifest.md.** Add an inventory entry for this feature under the SDD scripts section (the four modified scripts + new test files), dated 2026-06-01.

- [x] **Step 5: BACKLOG.md.** Mark N3/N4/N10 done (find their rows and update status; add a brief "resolved by 2026-06-01-sdd-enforcement-hardening" note). Add a **row N11 marked DONE** (discovered during this feature's plan review and fixed here, Task 3): *"`transition-module.py` did not recompute `enforcement.context_summary_at` on module transition — it stayed pinned to the completed module's midpoint, firing Check 6b early for later-module tasks. Fixed: `transition()` recomputes it for the next module's range."*

- [x] **Step 6: Commit**

```bash
git add CLAUDE.md docs/ARaymond-customization-manifest.md docs/process-improvement-findings/BACKLOG.md
git commit -m "docs(sdd): record enforcement-hardening changes; mark N3/N4/N10/N11 done"
```

---

### Task 7: Run full test matrix and confirm counts

**Files:** none (read-only verification).

`task_type: verification` — this task observes and reports; it modifies no files and makes **no commits**. (This is also the first live exercise of the verification-task flow — see the Acceptance Criteria note.)

> **Controller, read before dispatching Task 7:** Check 9 (git-reality) gives the LAST verification task an open-ended window — `git log --after=<task7_dispatch_ts>` with **no `--before`** — so it flags *any* commit made at or after Task 7's dispatch. Therefore: (1) commit ALL of Task 6's documentation work **before** dispatching Task 7, and (2) make **no commits** between Task 7's dispatch and the pre-completion checkpoint run. If Check 9 false-flags Task 7 during execution, an out-of-window commit is the cause.

**Context:** Run every suite the change touches and confirm the doc-stated counts are accurate. Report PASS/FAIL with the actual output. Do not fix anything here — if a suite fails, that is a finding to route back to the owning task.

- [x] **Step 1: Static + regression + install**

Run:
```bash
bash tests/ARaymond-installation/verify-symlink-install.sh
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/ARaymond-hook-baseline/check-hooks.sh
```
Expected: install checks PASS; regression PASS-with-advisory-WARNINGs (no FAIL); hook baseline PASS (registration unchanged — C5 only changed behavior, not the `settings.json:78` registration).

- [x] **Step 2: Full unit suite**

Run: `.venv/bin/python3 -m pytest tests/unit/ -v`
Expected: all PASS. Record the new total and confirm it matches the count written in CLAUDE.md by Task 6.

- [x] **Step 3: Integration e2e**

Run: `bash tests/integration/sdd-e2e-test.sh`
Expected: `E2E PIPELINE PASS - 11 steps composed correctly`.

- [x] **Step 4: Report.** Write the implementer report summarizing each suite's result (pass counts, the e2e step count, the unit-test total) and confirming the documented counts match reality. No commit.

---

## Acceptance Criteria

- [x] 2-module plan **without** Source Contracts runs end-to-end through `transition-module.py` with zero manual workarounds (e2e Steps 4–5 + 7b: module-2 first task dispatches; pre-completion passes with archived reports).
- [x] 2-module plan **with** Source Contracts does not BLOCK at module 2 (Check 5 finds archived Task 0 — `test_check5_finds_archived_task0`).
- [x] No-Task-0 single-module plan starting at Task 1 dispatches without forging a `task=0` log entry (Check 4c skip-guard: `PREV=0 < START=1`).
- [x] `transition-module.py` **refuses** to transition when a completing-module task's dispatch provenance is missing (`test_blocks_when_provenance_missing`).
- [x] Pre-completion gate passes with completed-module reports under `archive-*/` (Task 1 archive-aware lookups + existing pre-completion suite).
- [x] `sdd-skill-enforcement-hook.sh` blocks (`exit 2`) an impl Write/Edit when SDD was explicitly requested + skill never loaded; `SUPERPOWERS_SDD_BYPASS` recovers; a casual SDD mention does not false-block (Task 0 tests).
- [x] Check 4c and `validate_module_completion` agree on require/exempt decisions, keyed on the file-based minimum signal (`test_minimum_signal_agreement`, 4 cases).
- [x] A completing module containing a `task_type:verification` task transitions without demanding spec/quality reviews for it (`test_verification_task_exempt_from_reviews`) — the folded-in exemption matching the hook.
- [x] On transition, `enforcement.context_summary_at` is recomputed for the next module's range (N11) — verified by the assertion on `test_manifest_updated_after_transition` and by e2e Step 7b dispatching the module-2 first task with no context-summary stub.
- [x] All existing static + unit + integration suites pass; new tests added; `sdd-e2e-test.sh` exercises module-2-first-task **post-transition** (Task 7).

**Note on dogfooding:** This plan's own execution is the first live exercise of `task_type: verification` (Task 7). Two interactions to respect during execution: (1) Task 7 must produce **no commits** (its window must be clean for the pre-completion git-reality check, Check 9); commit all of Task 6's docs before dispatching Task 7. (2) The verification-ratio cap is 30% — this plan is 1/8 = 12.5%, well under.
