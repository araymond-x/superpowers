# SDD Enforcement Hardening — Design Spec

> **Feature:** `sdd-enforcement-hardening`
> **Date:** 2026-06-01
> **Archetype:** Refactor / extension of SDD enforcement code (no features removed; one advisory behavior replaced by blocking)
> **Status:** Approved design — pending plan
> **Source backlog items:** N3 (Check 4c), N4 (pre-completion archive-awareness), **N10 (new — Check 5 archive-awareness)**, plus an advisory→blocking promotion of `sdd-skill-enforcement-hook.sh` (a C3-class item).

---

## 1. Problem statement

`transition-module.py` introduced a `reports/archive-<module>/` subtree and truncates the live dispatch log at each module boundary. Three downstream consumers were never taught about that new shape, so a `transition-module.py`-driven multi-module SDD run cannot complete without manual workarounds (observed first-hand in the `pipeline-flexibility` execution — see its `deviations.md` Module 1→2 and 2→3 rows, and the practerus `marketing-cta-guard` run for the no-Task-0 variant):

1. **Check 4c (dispatch provenance) — `sdd-pre-dispatch-hook.sh`.** Sits *outside* the "first task in module" skip and assumes the first in-scope task is always Task 0 (`TASK_NUMBER -gt 0` guard). It legitimately isn't in two cases:
   - **No-Task-0 plans:** Task 0 is *conditional* (`writing-plans`/SDD `SKILL.md` mandate it only for plans with external Source Contracts), so a contract-free plan validly starts at Task 1. Check 4c sets `PREV=0` and greps the log for `task=0 type=spec-review`, which can never exist → `BLOCKED`.
   - **Module boundaries:** `transition-module.py` Step 5 truncates the live dispatch log, so the next module's first task has no prior provenance in the live log and Check 4c BLOCKs on the (now-archived) N-1 reviews.

2. **Pre-completion gate (N4) — `controller-checkpoint.py`.** `find_report_file`/`find_all_report_files` glob only `reports_dir`, flat. After a transition archives a completed module's reports to `archive-<module>/`, the final gate reads them as "missing".

3. **Check 5 (Source-Contracts → Task 0) (N10) — `sdd-pre-dispatch-hook.sh`.** `task_report_glob` builds `${REPORTS_DIR}/task-NNN-*` only — never `archive-*/`. Once the first transition archives Task 0 to `archive-module1/`, any multi-module plan *with Source Contracts* hits `BLOCKED: no Task 0 report` at module 2+.

Separately, **`sdd-skill-enforcement-hook.sh`** detects "SDD requested but the skill was never loaded, and implementation code is being written" — the exact failure mode in the CLAUDE.md incident ("Module 3 implemented without loading the SDD skill") — but only injects an advisory reminder (`exit 0`). It can remind but not enforce.

### Root cause (one pattern, four sites)

A value was added to one side of a contract (the multi-module *producer*, `transition-module.py`, which creates `archive-*/` and truncates the log) without updating all *consumers* (Check 4c, Check 5, the pre-completion gate). Fixing any subset still dead-ends a real multi-module run, so all four sites are addressed together.

---

## 2. Decision log

| # | Decision | Options considered | Chosen | Rationale |
|---|----------|--------------------|--------|-----------|
| D1 | Where to re-verify a module-boundary task's dispatch provenance once the Check 4c skip-guard removes it from the live path | (M1) hook reads `archive-<module>/.dispatch-log` at boundary; (M2) `transition-module.py` verifies provenance before truncating; (M3) both | **M2 — transition-time check** | Keeps the hot enforcement path a one-line skip; makes `transition-module.py` the complete boundary gatekeeper; fixes the asymmetry that transition validates report *existence* but not *provenance*. The live log is intact when `validate_module_completion` runs (Step 1, before Step 5 truncation). |
| D2 | How the pre-completion gate finds reports for completed (archived) modules | recurse into `archive-*/`; trust manifest `completed_modules`/`module_reports_archived` | **Recurse into `archive-*/`** | Verifies real existence wherever reports live; robust to a missing/corrupt archive; "trust the manifest" can mask a real gap. |
| D3 | How careful the `sdd-skill-enforcement-hook.sh` advisory→blocking promotion should be | block as-is; tighten + block + bypass; tighten + block, no bypass | **Tighten detection + `exit 2` + `SUPERPOWERS_SDD_BYPASS` escape hatch** | Flipping the exit code on the current loose heuristic would false-positive-block any SDD-mentioning session. Blocking enforcement on a heuristic needs a recovery path; mirror the existing `SUPERPOWERS_VALIDATOR_BYPASS` pattern. |
| D4 | Whether to fold N10 (Check 5 archive-awareness) into this effort | fold in now; file as standalone backlog item | **Fold in** | Without it, "multi-module is runnable" is still false for Source-Contracts plans; it's an S-sized symmetric fix to the same archive-blindness as N4. |
| D5 | How to make Check 5 archive-aware | global change to `task_report_glob`; a dedicated archive-inclusive lookup in Check 5 only | **Dedicated Check-5 lookup** | A blanket change to `task_report_glob` widens the blast radius to every check that uses it; scoping the change to Check 5 keeps Check 4's within-module checks untouched and the diff reviewable. (Sequential 3-digit numbering means a global change would be *safe*, but the narrow change is *clearer*.) |
| D6 | How N3b avoids drifting from Check 4c's exemption logic (bash hook vs Python script can't share code) | accept drift risk; cross-reference comments + an agreement test | **Cross-reference comments in both + a test asserting agreement on a sample manifest** | N2 was literally an SSOT audit; shipping a second copy of the exemption rules without a drift guard would re-create the class of problem we just fixed. |

---

## 3. Components

### 3.1 N3a — Check 4c skip-guard (`sdd-pre-dispatch-hook.sh`)

Add a guard so the Check 4c dispatch-provenance block (the `task=$PREV type=spec-review` / `type=quality-review` checks) is **skipped when `PREV < MANIFEST_TASK_START`** — i.e., there is no prior *in-scope* task.

- **Behavior:**
  - Module's first task (`TASK_NUMBER == MANIFEST_TASK_START`) → `PREV = MANIFEST_TASK_START - 1 < MANIFEST_TASK_START` → **skip**.
  - No-Task-0 single-module plan (`MANIFEST_TASK_START == 1`, task 1) → `PREV = 0 < 1` → **skip**.
  - Within a module (`TASK_NUMBER > MANIFEST_TASK_START`) → `PREV >= MANIFEST_TASK_START` → **check runs** (full provenance enforcement preserved).
  - A plan that *does* declare Task 0 (`MANIFEST_TASK_START == 0`) → task 1 has `PREV = 0`, `0 < 0` is false → **check runs** (Task 0's provenance is still verified).
- **Placement:** inside the existing `dispatch_provenance` enforcement branch (the guard composes with the existing micro-tier `enforcement.dispatch_provenance == "false"` skip — both can short-circuit).
- **Cross-reference comment** naming `transition-module.py:validate_module_completion` as the place that verifies the skipped boundary provenance (D6).

### 3.2 N3b — transition-time provenance verification (`transition-module.py`)

Extend `validate_module_completion` so that, for each task in the completing module, it verifies dispatch-log **provenance** (not just report-file existence), honoring the same exemptions Check 4c uses. This runs in Step 1, before the log is archived/truncated in Step 5, so the live log is intact.

- **New helper:** `_has_dispatch_provenance(dispatch_log_path, task_id, review_type) -> bool` — returns whether the live dispatch log contains a `task=<id> type=<review_type>` line.
- **Logic (mirrors Check 4c exactly):**
  - If `process_requirements.spec_review_mode != "skip"`: require `spec-review` provenance for the task (in addition to the existing spec-report-file existence check).
  - If `process_requirements.quality_review_mode != "skip"`: require `quality-review` provenance **unless** a `task-NNN-quality-review-minimum-tier.md` file exists in the live reports dir (the same minimum-tier exemption Check 4c applies).
- **Failure mode:** a missing provenance entry is a validation failure (`return 1`, `INCOMPLETE: Task N: <review> review not provenance-logged`) — `transition` refuses to archive/truncate. This catches controller-forged boundary reviews at the choke point.
- **Cross-reference comment** naming `sdd-pre-dispatch-hook.sh` Check 4c as the sibling enforcement (D6).

### 3.3 N4 — pre-completion gate archive-awareness (`controller-checkpoint.py`)

`find_report_file(reports_dir, task_number)` and `find_all_report_files(reports_dir)` also search `reports/archive-*/`.

- `find_report_file`: glob both `<reports_dir>/<pattern>` and `<reports_dir>/archive-*/<pattern>`; return the sorted-last match.
- `find_all_report_files`: glob both `<reports_dir>/task-*-implementer-report*` and `<reports_dir>/archive-*/task-*-implementer-report*`.
- **Consumer note:** every caller of these two functions inherits archive-awareness. The plan must audit all callers (pre-completion `all_tasks_have_reports`, minimum-tier ratio, verification ratio, etc.) and confirm archive-inclusion is correct for each (it is — all want "does this task's report exist anywhere it legitimately could").

### 3.4 N10 — Check 5 archive-awareness (`sdd-pre-dispatch-hook.sh`)

Check 5's Task-0 lookup searches both the live dir and archives, without changing the shared `task_report_glob` (D5).

- Build a Check-5-local glob: `${REPORTS_DIR}/task-000-implementer-report* ${REPORTS_DIR}/archive-*/task-000-implementer-report*` and pass it to `check_report_file` (which already word-splits its `ls $pattern`).
- Behavior: a Source-Contracts plan whose Task 0 has been archived at a module boundary no longer false-BLOCKs at module 2+.

### 3.5 Skill-enforce promotion (`sdd-skill-enforcement-hook.sh`)

Promote from advisory (`exit 0` + `additionalContext`) to blocking (`exit 2` + stderr), behind a tightened detection heuristic and an escape hatch.

- **Tighten detection:** require an explicit SDD *imperative* in a user message (e.g. `(invoke|use|run|follow|start|let'?s use)\b.{0,20}(subagent-driven-development|sdd)`), not a bare mention of "SDD"/"subagent-driven-development". Removes the bare-mention alternatives that match any reference (including meta-discussion).
- **Keep:** the `SKILL_LOADED` check — if the Skill tool loaded `subagent-driven-development`, allow silently (enforcement hooks are active).
- **Keep:** the impl-file path filter and all early exits.
- **Bypass:** if `SUPERPOWERS_SDD_BYPASS` is set, allow with a stderr warning (mirrors `SUPERPOWERS_VALIDATOR_BYPASS`).
- **Block:** when SDD imperative + skill-not-loaded + impl-file + no bypass → `exit 2` with the existing warning text on stderr (matches `sdd-pre-dispatch-hook.sh`'s block convention).
- **Residual risk:** heuristic detection is imperfect by nature; the bypass is the safety valve and is documented in CLAUDE.md.

---

## 4. Data flow — module-boundary lifecycle (after this change)

```
… module 1 executes (tasks 1..4) — Check 4c verifies task N-1 provenance live as each task dispatches …
controller runs transition-module.py (module1 → module2):
  Step 1 validate_module_completion(module1):
     - report files exist (existing)            ── NEW: + dispatch provenance present (N3b) ──> refuse if forged
  Step 3 archive task-00N-* → reports/archive-module1/
  Step 5 copy .dispatch-log → archive; truncate live .dispatch-log
  Step 4 manifest.task_range → [5, 8]  (MANIFEST_TASK_START becomes 5)
controller dispatches task 5 (module2 first task):
  Check 4c: PREV=4 < MANIFEST_TASK_START=5 → SKIP (N3a)   [boundary provenance already verified at transition]
  Check 5 (if Source Contracts): finds Task 0 in reports/ OR archive-*/ (N10) → PASS
… module 2 executes (tasks 6..8) — Check 4c verifies task N-1 provenance live again (PREV >= 5) …
controller reaches completion:
  pre-completion gate: all_tasks_have_reports finds module1 reports in archive-*/ (N4) → PASS
```

---

## 5. Cross-cutting requirements (the plan must encode these)

- **Consumer audit before editing** every changed function: `task_report_glob`/`check_report_file` (Check 5 path), `validate_module_completion` (transition), `find_report_file`/`find_all_report_files` (all checkpoint callers), `sdd-skill-enforcement-hook.sh` (settings.json registration).
- **SSOT drift guard (D6):** cross-referencing comments in both Check 4c and `validate_module_completion`, plus a test asserting both agree (same require/exempt decision) on a sample manifest with one full-tier and one declared-minimum task.
- **Obsolescence:** the advisory-only path of `sdd-skill-enforcement-hook.sh` (inject + `exit 0` for the "SDD requested, not loaded" case) is *replaced* by the blocking path. The `exit 0` early-exits for non-SDD sessions, non-impl files, and skill-loaded sessions remain. No other code is removed.
- **Docs:** update CLAUDE.md (Hooks-Based Enforcement, Hook Development Gotchas — add `SUPERPOWERS_SDD_BYPASS`, the N3a skip-guard, transition-time provenance, archive-aware checks), `docs/ARaymond-customization-manifest.md`, and mark N3/N4/N10 done in `BACKLOG.md` on completion.

---

## 6. Testing strategy

- **Unit (pytest / shell):**
  - N3a: a Task-1-start manifest dispatch PASSes Check 4c; a module-2-first-task dispatch PASSes; a Task-0 plan still gets PREV provenance-checked; a within-module task still gets checked.
  - N3b: `validate_module_completion` PASSes when provenance present; **FAILs (refuses transition) when a completing-module task's spec/quality provenance is missing**; respects `*_review_mode == "skip"` and the minimum-tier file exemption.
  - N4: `find_report_file`/`find_all_report_files` locate reports under `archive-*/`; pre-completion `all_tasks_have_reports` PASSes with archived reports.
  - N10: Check 5 finds an archived Task 0; no false-BLOCK for a Source-Contracts multi-module plan at module 2.
  - Skill-enforce: non-SDD session → allow; casual SDD mention → allow (no false block); SDD imperative + skill-not-loaded + impl file → `exit 2`; skill loaded → allow; `SUPERPOWERS_SDD_BYPASS` → allow + warning; non-impl file → allow. (New test file — none exists today.)
  - SSOT agreement test (D6).
- **Integration (`sdd-e2e-test.sh`):** extend to drive a real 2-module pipeline that **dispatches a module-2-first-task through the hook *post-transition*** (the path whose absence let this ship green), and a Source-Contracts variant. Add a step proving transition refuses on forged provenance.
- **Regression:** `validate-all-skills.py`, `verify-symlink-install.sh` (hook EXPECTED counts unchanged), full `tests/unit/`.

---

## 7. Acceptance criteria

- [ ] A 2-module plan **without** Source Contracts runs end-to-end through `transition-module.py` with **zero manual workarounds** (module-2 first task dispatches; pre-completion passes).
- [ ] A 2-module plan **with** Source Contracts does not BLOCK at module 2 (Check 5 finds archived Task 0).
- [ ] A no-Task-0 single-module plan starting at Task 1 dispatches without forging a `task=0` log entry.
- [ ] `transition-module.py` **refuses** to transition when a completing-module task's dispatch provenance is missing (forgery caught at the boundary).
- [ ] The pre-completion gate passes with completed-module reports living under `archive-*/`.
- [ ] `sdd-skill-enforcement-hook.sh` blocks (`exit 2`) an implementation Write/Edit when SDD was explicitly requested and the skill was never loaded; `SUPERPOWERS_SDD_BYPASS` recovers; a casual SDD mention does **not** false-block.
- [ ] Check 4c and `validate_module_completion` agree on require/exempt decisions (SSOT test passes).
- [ ] All existing static + unit + integration suites pass; new tests added; `sdd-e2e-test.sh` exercises the module-2-first-task-post-transition path.
