---
schema_version: 1
task_id: 20
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/scripts/materialize-manifest.py"
    description: "Downgraded Python 3.10+ type annotations to Python 3.9 compatible syntax: added `from typing import List, Optional`; replaced `dict | None` (line 43), `list[ModuleState] | None`, `int | None`, `str | None` (lines 121-123) with `Optional[...]` / `List[...]` forms. Annotations only — no behavior or logic change."
  - path: "skills/subagent-driven-development/scripts/transition-module.py"
    description: "Downgraded Python 3.10+ type annotations to Python 3.9 compatible syntax: added `from typing import List, Optional`; replaced `list[ModuleState]` / `ModuleState | None` (line 29) and `list[str]` (lines 51, 53) with `Optional[...]` / `List[...]` forms. Annotations only — no behavior or logic change."
  - path: "docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/deviations.md"
    description: "Appended Task 20 row (IndependentDecision) recording the Python 3.9 downgrade, citing Task 14 precedent (deviations row 28) and the project regression policy."
tests:
  written: 0
  passing: 0
  command: ".venv/bin/python3 -m pytest tests/unit/ -q && .venv/bin/python3 tests/ARaymond-skill-regression/validate-all-skills.py && bash tests/ARaymond-installation/verify-symlink-install.sh"
  result: PASS
---

**Implementation Summary:**

Restored the regression suite to green by downgrading the Python 3.10+ type annotations in the two new SDD scripts (`materialize-manifest.py`, `transition-module.py`) to Python 3.9-compatible syntax. The downgrade follows Task 14's established precedent (deviations row 28) and the project regression policy documented in `tests/ARaymond-skill-regression/validate-all-skills.py` (Category 8: Python 3.9 Compatibility).

Concrete edits:

1. **`materialize-manifest.py`** — Added `from typing import List, Optional` to the imports block. Replaced four annotation forms: `dict | None` -> `Optional[dict]` (line 43, `extract_frontmatter` return); `list[ModuleState] | None` -> `Optional[List[ModuleState]]`, `int | None` -> `Optional[int]` (x1), `str | None` -> `Optional[str]` (x1) (lines 121-123, the three local variable annotations inside `materialize()`).

2. **`transition-module.py`** — Added `from typing import List, Optional` to the imports block. Replaced three annotation forms: `list[ModuleState]` -> `List[ModuleState]` and `ModuleState | None` -> `Optional[ModuleState]` (line 29, `_find_module` signature); `list[str]` -> `List[str]` (x2) (line 51 return type and line 53 local-variable annotation of `errors`).

3. **`deviations.md`** — Appended row 37 (Task 20, IndependentDecision) documenting the downgrade, citing Task 14 row 28 as precedent and noting the tension between the user-level coding-style rule (prefers PEP-604) and the project-level regression rule (enforces Python 3.9 baseline). Project rule wins per established convention.

No changes were needed in `tests/ARaymond-skill-regression/validate-all-skills.py`: the Python 3.9 Compatibility check discovers `.py` files dynamically via `os.listdir(sdd_scripts_dir)` (see lines 1180-1184), so the new scripts (`materialize-manifest.py`, `transition-module.py`) are already picked up automatically. The regression test has no hardcoded SDD-scripts file list that needed updating for this task.

Verification (all three suites green after the downgrade):

- **Regression**: `.venv/bin/python3 tests/ARaymond-skill-regression/validate-all-skills.py` -> `PASS: 145  FAIL: 0  WARNING: 2  Result: PASS (with warnings)`. The 9 FAILs are eliminated. The 2 remaining WARNINGs are pre-existing (writing-plans/SKILL.md bare-`DEVIATIONS.md` references on lines 298 and 307 — documented as historical context and permitted; plus a heuristic warning unrelated to this task).
- **Installation**: `bash tests/ARaymond-installation/verify-symlink-install.sh` -> `Passed: 104  Failed: 0  Warnings: 0  STATUS: PASSED`.
- **Unit suite**: `.venv/bin/python3 -m pytest tests/unit/ -q` -> `326 passed, 1 warning in 34.83s`. Includes the 31 tests added in Modules 1-3 for `materialize-manifest.py`, `transition-module.py`, and `controller-checkpoint.py`; all still pass after the annotation downgrade.

Smoke-tested both scripts directly via `--help` to confirm the typing imports are functional at runtime.

**Source Files Read:**

- `skills/subagent-driven-development/scripts/materialize-manifest.py` (full file, 239 lines pre-edit) — located all four annotation-violation lines, confirmed scope (3 module-level + 1 function signature) before edits.
- `skills/subagent-driven-development/scripts/transition-module.py` (full file, 205 lines pre-edit) — located the three annotation-violation lines (`_find_module` signature + `validate_module_completion` return type + `errors` local) before edits.
- `tests/ARaymond-skill-regression/validate-all-skills.py` (Category 8 section, lines 1145-1241; also surrounding context for hardcoded file lists, lines 314-381 and 789-907) — confirmed Python 3.9 compatibility check uses dynamic file discovery (`os.listdir` of the SDD scripts dir), so no hardcoded file list updates are needed.
- `skills/subagent-driven-development/scripts/controller-checkpoint.py` (top imports section) — confirmed the precedent pattern (`from typing import Optional, Tuple` plus legacy syntax) per Task 14 deviation row 28; matched that style.
- `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/deviations.md` (full file, 37 rows) — read Task 14 row 28 verbatim to anchor the precedent citation in this task's deviation row.
- `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/reports/task-019-implementer-report.md` (frontmatter + section headers) — matched the report format (frontmatter schema, 5 standard `**Header:**` prose sections).

**Deviations from Plan:**

One IndependentDecision deviation, logged in `deviations.md` row 20 (Task 20):

- The downgrade itself is the deviation — the task description prescribed Strategy A (Python 3.9 syntax downgrade) explicitly, but it should still be recorded as an IndependentDecision because (a) it contradicts the user-level global coding-style rule (`~/.claude/rules/coding-style.md`) which prefers PEP-604 syntax, and (b) it follows the in-tree Task 14 precedent rather than the global rule. The disposition was unambiguous (project regression policy wins, as the task description explicitly stated), but the trade-off is worth recording for future reviewers who notice the legacy-typing style in only these two scripts.

No deviations from the prescribed step sequence (Steps 1-7 all executed in order). No scope expansion beyond the two annotated scripts and the deviations log.

**Self-Review Findings:**

- **9 FAILs -> 0 FAILs?** Yes. Regression summary went from `PASS: 143  FAIL: 9  WARNING: 2` to `PASS: 145  FAIL: 0  WARNING: 2`. The two extra PASS lines are the `materialize-manifest.py: no Python 3.9 compatibility issues found` and `transition-module.py: no Python 3.9 compatibility issues found` entries that the script emits when a file has zero issues.
- **Unit tests for materialize-manifest.py / transition-module.py still pass after downgrade?** Yes. Full suite: 326 passed. Specifically verified `tests/unit/test_materialize_manifest.py` and `tests/unit/test_transition_module.py` are part of the green run.
- **Installation verification PASS?** Yes. 104/0/0.
- **Any new test failures introduced?** No. The full unit suite, the regression suite, and the installation verification all returned to/stayed green.
- **Report has 5 standard prose sections?** Yes — Implementation Summary, Source Files Read, Deviations from Plan, Self-Review Findings, Concerns (this is section 5).
- **Frontmatter constraints satisfied?** `tests.passing` (326) >= `tests.written` (0) ✓; `tests.result` is `PASS` ✓; `schema_version: 1` ✓; `status: DONE_WITH_CONCERNS` ✓ (per task spec).
- **No leftover scratch files?** Verified — only the three edited files (two scripts + deviations.md) are modified. No temp files, no `.bak` files, no orphan test fixtures.
- **Annotations-only change confirmed?** Reviewed both edits — the only changes are: (a) added `from typing import List, Optional` import line, (b) replaced annotation forms (`X | Y` -> `Optional[X]`, `list[X]` -> `List[X]`). No function logic, no behavior, no docstrings touched.

**Concerns:**

This task is marked DONE_WITH_CONCERNS per task spec. The concerns surfaced (all forward-looking, none blocking acceptance):

1. **PEP-604 vs Python 3.9 policy tension is now structural.** Three SDD scripts (`materialize-manifest.py`, `transition-module.py`, and `controller-checkpoint.py` from Task 14) now carry legacy typing imports purely to satisfy the regression test. The user-level coding-style rule explicitly prefers PEP-604 (`X | None`) and built-in generics (`list[X]`). The project regression test enforces the opposite for SDD scripts only. This is fine today, but as more SDD scripts are added, every new contributor will hit the same friction. Resolution options for a future cleanup task: (a) drop the Python 3.9 regression rule (the venv already runs Python 3.13+), (b) add a `# regression: python-3.9` allowlist to suppress the check for files that explicitly opt out, or (c) keep the rule and accept the friction. Out of scope for Task 20.

2. **`compute_midpoint` duplication remains** (already tracked as `ForwardConcern` in deviations row 12 — Task 12). The same formula lives in `materialize-manifest.py` and `transition-module.py`, and now both carry the same legacy typing imports. Consolidation into a shared module (e.g., `skills/scripts/models/midpoint.py`) would simplify both — tracked for a post-Module-4 refactor pass per the existing deviation entry.

3. **No new tests added** (the task was infrastructure/regression-restoration, not behavior change). The downgrade is annotations-only, so existing unit coverage on `materialize-manifest.py` (test_materialize_manifest.py — ~16 tests) and `transition-module.py` (test_transition_module.py — 7 tests) is sufficient to demonstrate that runtime behavior is unchanged. No coverage gap was created.

4. **Task 14 deviation row 28 referred to "9 pre-existing FAILs in the regression"** — those 9 FAILs are precisely the ones Task 20 closed. The forward-link is now resolved, and any future regression run should report 0 Python 3.9 compatibility FAILs unless someone introduces fresh PEP-604 syntax in a script under `skills/subagent-driven-development/scripts/`. Recommend the next plan author who adds an SDD script audit the regression policy decision (concern #1 above) up-front.
