---
schema_version: 1
task_id: 7
task_type: implementation
status: DONE
files_changed:
  - path: "skills/subagent-driven-development/scripts/controller-checkpoint.py"
    description: "Added module-level `_git_run(args, cwd=None, timeout=10)` just above `_resolve_base_ref` (3.9-safe `# type:` comment, NOT a PEP-604 union — file is Python-3.9-pinned). Consolidated the 3 git call sites that shared identical timeout=10 + swallow-(TimeoutExpired,OSError)→None semantics: (1) `_resolve_base_ref`'s inner `_git` → `def _git(cmd_args): return _git_run(cmd_args, cwd=git_root)`; (2) `_in_changeset`'s inner `_git` → identical delegation; (3) the inline call in `_check_verification_git_reality` → build `git_args` then `result = _git_run(git_args, cwd=git_root)` with the `if result is not None and result.returncode == 0 and result.stdout.strip()` guard (findings.append keys task/start/end/commits UNCHANGED). `_resolve_git_root` (O4) deliberately UNTOUCHED."
  - path: "tests/unit/test_c2_integration_gate.py"
    description: "Added the hoisted controller-checkpoint load `_vp_ckpt = _load_script(\"controller_checkpoint_n25\", \"controller-checkpoint.py\")` right after the existing `_vp` load (uses the Tasks-5/6 `from sdd_test_helpers import ROOT, _load_script`). Added `TestGitRunSSOT` (2 tests verbatim from the plan: `test_git_run_handles_failure` bad-cwd → None-or-rc!=0; `test_git_run_returns_completed_process` real repo → rc==0)."
tests:
  written: 2
  passing: 2
  command: ".venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py tests/unit/test_pre_completion_gates.py -v"
  result: PASS
contract_compliance:
  - constraint: "Behavior-preserving: the 3 consolidated sites must be SEMANTICALLY IDENTICAL (same git args, same timeout=10, same swallow→None, same `git -C git_root` targeting)"
    status: compliant
    detail: "_git_run builds `[\"git\",\"-C\",cwd]+args if cwd else [\"git\"]+args` and `subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)` with `except (subprocess.TimeoutExpired, OSError): return None` — byte-for-byte the prior semantics. All 65 tests in test_c2_integration_gate.py + test_pre_completion_gates.py (incl. every pre-existing Check-9 git-reality and Check-10 changeset test) pass unchanged."
  - constraint: "O4 exclusion is load-bearing: do NOT fold `_resolve_git_root` (:755) into `_git_run`"
    status: compliant
    detail: "`_resolve_git_root` left fully intact — no timeout, no try/except, errors propagate to drive its `parent.parent.parent` fallback-with-warning. Post-edit `grep -nE 'subprocess\\.run' controller-checkpoint.py` returns exactly TWO matches: line 496 (the new `_git_run` def) and line 751 (`_resolve_git_root`). No third/missed site."
  - constraint: "Audit ALL 4 git sites (O4): only remaining raw git subprocess.run is in _resolve_git_root + the new _git_run def"
    status: compliant
    detail: "grep audit ran (Step 5). 2 matches total, both expected. The 3 former call sites now delegate to `_git_run`; zero raw `subprocess.run` git calls remain outside the def and the O4 exclusion."
  - constraint: "Write-scope: Task 7 OWNS controller-checkpoint.py (_git_run + 3 sites ONLY) + test_c2_integration_gate.py (TestGitRunSSOT). Do NOT touch _review_tiers_per_task/_merged_dispatch_times [Tasks 1-2], the Check 10 block [Task 8], _resolve_git_root, validate-plan.py, _report_utils.py"
    status: compliant
    detail: "`git show --stat HEAD` lists exactly controller-checkpoint.py + test_c2_integration_gate.py. The Task-2 code feeding `dispatch_times = _merged_dispatch_times(...)` and the `start_ts`/`end_ts` window computation above the inline site were left untouched (replacement bounded to `git_cmd build`→`except…pass`). No Task-8 _EMPTY_TREE_SHA / direct-diff special-case added to _in_changeset. No other files changed."
  - constraint: "3.9-safe types: use the `# type:` comment with Optional, NOT a PEP-604 `|` union (would fail regression Category-8 — invisible to pytest on 3.12)"
    status: compliant
    detail: "Copied the plan's signature verbatim: `def _git_run(args, cwd=None, timeout=10):` + `# type: (list, Optional[str], int) -> Optional[subprocess.CompletedProcess]`. `Optional` is already imported (controller-checkpoint.py:43). No modern union syntax introduced."
  - constraint: "venv-python: run tests with .venv/bin/python3 (controller-checkpoint.py imports pydantic models); run the full unit suite at the end with no regression"
    status: compliant
    detail: "Targeted run (test_c2 + test_pre_completion_gates) = 65 passed. Full suite `.venv/bin/python3 -m pytest tests/unit/ -q` = 488 passed, 1 pre-existing unrelated PytestCollectionWarning (TestSummary __init__). Module also exec-loads clean and exposes `_git_run`."
---

**Implementation Summary:**
Implemented Task 7 (N25c) per the module-2 plan's 7 steps — a behavior-preserving consolidation of git subprocess calls into a single module-level SSOT. (Step 1) Added `_vp_ckpt = _load_script("controller_checkpoint_n25", "controller-checkpoint.py")` after the existing `_vp` load and appended `TestGitRunSSOT` (2 tests, verbatim) to `test_c2_integration_gate.py`. (Step 2) Confirmed RED — both tests failed with `AttributeError: module has no attribute '_git_run'`. (Step 3) Added the module-level `_git_run(args, cwd=None, timeout=10)` just above `_resolve_base_ref`, with the 3.9-safe `# type:` comment (NOT a PEP-604 union — the file is Python-3.9-pinned and a `|` union would fail the regression suite's Category-8 check while passing silently under pytest on 3.12). (Step 4) Consolidated the 3 sites: `_resolve_base_ref`'s inner `_git` and `_in_changeset`'s inner `_git` both became `def _git(cmd_args): return _git_run(cmd_args, cwd=git_root)`; the inline call in `_check_verification_git_reality` became a `git_args` build + `result = _git_run(git_args, cwd=git_root)` with the same returncode/stdout guard (the `findings.append` dict keys task/start/end/commits are unchanged). (Step 5) Ran the grep audit — exactly 2 `subprocess.run` matches remain: the new `_git_run` def (:496) and `_resolve_git_root` (:751, the O4 exclusion). (Step 6) 65 passed across `test_c2_integration_gate.py` + `test_pre_completion_gates.py` (new tests + every pre-existing Check-9/Check-10 test); full unit suite 488 passed. (Step 7) Committed the two owned files with explicit paths (c06b230).

**Source Files Read:**
- `docs/imp-plans/2026-06-10-sdd-aggregate-gate-visibility/module-2-calibration.md` — Task 7's 7 steps + verbatim code blocks; cross-checked the plan's STALE line numbers against the live file (plan said inline call ~:353, `_resolve_base_ref` ~:454, `_in_changeset` ~:505, `_resolve_git_root` ~:703; live = :405, :506, :557, :755 — Tasks 1-2 shifted ~50 lines down, exactly as the task prompt warned).
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` — read `_check_verification_git_reality` (:362+) fully to reconcile the inline replacement against Task 2's current code (`dispatch_times = _merged_dispatch_times(...)` feeds the window loop); read `_resolve_base_ref` and `_in_changeset` inner `_git` defs; confirmed `subprocess` + `from typing import Optional, Tuple` imports present (no new imports needed); confirmed `_resolve_git_root` at :751 is the O4 exclusion (no timeout, errors propagate).
- `tests/unit/test_c2_integration_gate.py` — confirmed the Tasks-5/6 `from sdd_test_helpers import ROOT, _load_script` and the existing `_vp = _load_script(...)` site to mirror for the controller-checkpoint load; located the file end to append `TestGitRunSSOT`.
- `tests/unit/test_pre_completion_gates.py` (READ-ONLY) — the Check-9 git-reality tests that must still pass (verified green post-refactor).
- `docs/imp-plans/2026-06-10-sdd-aggregate-gate-visibility/reports/task-006-implementer-report.md` — exact implementer-report frontmatter shape.

**CLAUDE.md Files Read:**
- Repo-root `CLAUDE.md` — controller-checkpoint.py's Check 9 (git-reality) + Check 10, `_resolve_base_ref`/`_in_changeset` semantics, the "audit ALL callers" refactor rule, venv-python hook requirement (pydantic models), and the 3.9-compat regression constraint.
- User global `~/.claude/CLAUDE.md` + rules (architectural-principles: single-source-of-truth, audit-ALL-callers; coding-style: but DEFERRED to existing-file 3.9 convention — see Deviations).

**Deviations from Plan:**
- None to the prescribed steps. One intentional NON-application of a global style rule: `~/.claude/rules/coding-style.md` says "modernize type hints in functions you touch" (`str | None`), but I deliberately used the legacy `# type:` comment with `Optional` exactly as the plan prescribes — controller-checkpoint.py is Python-3.9-pinned (the regression suite's Category-8 check FAILs on PEP-604 unions, and that failure is invisible to pytest on 3.12). The advisor flagged this as the silent-failure trap; following the plan verbatim is correct here. The plan's line numbers were stale (documented above) — I located by function name/content per the task prompt, not by line number.

**Self-Review Findings:**
- `git show --stat c06b230` lists exactly the two owned files (controller-checkpoint.py: 72 lines net; test_c2_integration_gate.py: +20). Zero leakage into validate-plan.py, _report_utils.py, sdd_test_helpers.py, or the Task-1/2/8 regions.
- Replacement boundaries verified exact: the inline-site Edit started at `git_cmd = [...]` and ended at the prior `except…pass`, leaving Task-2's `_merged_dispatch_times` / `start_ts`/`end_ts` block above and `return findings` below untouched (8-space indent preserved inside the `for vid` loop).
- O4 audit: post-edit grep = exactly 2 `subprocess.run` (the new def + `_resolve_git_root`); `_resolve_git_root` byte-identical (no timeout, no swallow) — the load-bearing exclusion held.
- Behavior-preservation proof is the 65-test green across both files (every pre-existing Check-9 git-reality and Check-10 changeset test), not re-reasoning the diff — per the advisor.
- Module exec-loads clean and exposes `_git_run` (sanity check beyond unit tests).
- Full unit suite 488 passed (up from the 458 baseline by this task's +2 plus Tasks 5/6 in this module); the lone warning is a pre-existing unrelated `TestSummary` collection warning.

**Concerns:**
None. RED→GREEN demonstrated, all 65 targeted tests + the full 488-test unit suite pass, the refactor is semantically identical at all 3 consolidated sites (same args/timeout/swallow/`git -C` targeting), the O4 `_resolve_git_root` exclusion is intact, and the write-scope boundary held (only the 2 owned files changed). Status DONE.
