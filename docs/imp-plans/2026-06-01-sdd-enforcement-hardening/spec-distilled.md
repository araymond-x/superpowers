# SDD Enforcement Hardening — Distilled Implementation Spec

> **Source:** `spec.md` (2026-06-01, 6 decisions). For full rationale/alternatives, see source.
> **For:** Plan writer and implementation agents ONLY.
> **Archetype:** Refactor/extension of SDD enforcement code. One advisory behavior (`sdd-skill-enforcement-hook.sh`) becomes blocking; no other code removed.

## Contract Facts

- **Manifest is git-root-relative.** All `paths.*` resolve via `git rev-parse --show-toplevel`. `MANIFEST_TASK_START = task_range[0]`.
- **Module boundary lifecycle** (`transition-module.py`): Step 1 `validate_module_completion` → Step 3 archive `task-NNN-*` → `reports/archive-<module>/` → Step 5 copy + **truncate** live `.dispatch-log` → Step 4 manifest `task_range`/`active_module_*` advance. **The live dispatch log is intact during Step 1.**
- **Dispatch-log provenance line format:** `<ts> DISPATCH reviewer task=<N> type=<spec-review|quality-review|partner-review|trace-audit>`.
- **Two distinct "minimum" signals — do not conflate:**
  - *File signal:* `reports/task-NNN-quality-review-minimum-tier.md` present → controller-written quality review allowed (this is what **Check 4c** and **N3b** consult).
  - *Plan-declaration signal:* `review_tier: minimum` in plan frontmatter → used only by `controller-checkpoint.py` ratio exclusion. **Not** the signal for N3b.
- **Tier review modes:** `process_requirements.spec_review_mode` / `quality_review_mode` ∈ {…, `"skip"`}. `"skip"` ⇒ that review type is not required (existing `validate_module_completion` already branches on this).
- **Block convention:** `exit 2` + stderr message (matches `sdd-pre-dispatch-hook.sh`). Bypass env vars mirror `SUPERPOWERS_VALIDATOR_BYPASS`.
- **Archive-awareness applies to EXACTLY two lookups:** `controller-checkpoint.py` `find_report_file`/`find_all_report_files` (N4) and the hook's Check 5 Task-0 lookup (N10). All other report globs stay flat (see "Intentionally flat" below).

## Open Decisions

| # | Decision | Resolution Required By |
|---|----------|------------------------|
| — | None — all resolved | — |

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| D1 | Where to re-verify boundary provenance after the Check 4c skip-guard | **M2** — verify at transition time in `validate_module_completion` (before truncation) |
| D2 | How pre-completion finds archived reports | Recurse into `reports/archive-*/` |
| D3 | Skill-enforce promotion safety | Tighten detection + `exit 2` + `SUPERPOWERS_SDD_BYPASS` escape hatch |
| D4 | Include N10 (Check 5 archive-awareness) | Yes — fold in |
| D5 | How Check 5 becomes archive-aware | Dedicated Check-5 lookup (do NOT change shared `task_report_glob`) |
| D6 | Avoid Check 4c ↔ `validate_module_completion` drift | Cross-reference comments in both + an agreement test on the file-based minimum signal |

## Component Specifications

### C1 — N3a: Check 4c skip-guard (`sdd-pre-dispatch-hook.sh`)
Skip the Check 4c dispatch-provenance block when `PREV < MANIFEST_TASK_START`.
- Compose as a **third early-skip** alongside the existing `NEED_PROV == "false"` and `PREV_TASK_TYPE == "verification"` short-circuits (a sibling guard, not nested in the grep).
- Outcomes: module-first-task (`TASK_NUMBER == MANIFEST_TASK_START`) → skip; no-Task-0 plan (start=1, task 1, PREV=0<1) → skip; within-module (`PREV >= MANIFEST_TASK_START`) → check runs; Task-0 plan (start=0, task 1, PREV=0, `0<0` false) → check runs.
- Add a comment naming `transition-module.py:validate_module_completion` as where the skipped boundary provenance is verified.

### C2 — N3b: transition-time provenance (`transition-module.py`)
Extend `validate_module_completion` to verify dispatch-log provenance for each completing-module task, before Step 5 truncation.
- New helper `_has_dispatch_provenance(dispatch_log_path, task_id, review_type) -> bool` (grep live log for `task=<id> type=<review_type>`).
- Inside existing `if spec_review_mode != "skip":` → also require `spec-review` provenance.
- Inside existing `if quality_review_mode != "skip":` → require `quality-review` provenance **unless** the `task-NNN-quality-review-minimum-tier.md` **file** exists (file signal, not plan declaration).
- Missing provenance ⇒ validation failure (`return 1`, message `INCOMPLETE: Task N: <review> review not provenance-logged`) — transition refuses to archive/truncate.
- Add a comment naming `sdd-pre-dispatch-hook.sh` Check 4c as the sibling enforcement.

### C3 — N4: pre-completion archive-awareness (`controller-checkpoint.py`)
- `find_report_file`: glob both `<reports_dir>/<pattern>` and `<reports_dir>/archive-*/<pattern>`; return sorted-last.
- `find_all_report_files`: glob both `<reports_dir>/task-*-implementer-report*` and `<reports_dir>/archive-*/task-*-implementer-report*`.
- **Intentionally flat — DO NOT change:** `detect_stale_artifacts` (pre-execution stale scan), the hook's Check 3b (non-standard-naming scan), Check 7 (context-load loop). Name these in the plan as deliberately left flat.

### C4 — N10: Check 5 archive-awareness (`sdd-pre-dispatch-hook.sh`)
- Check 5's Task-0 lookup uses a local glob covering both live and archive: `${REPORTS_DIR}/task-000-implementer-report* ${REPORTS_DIR}/archive-*/task-000-implementer-report*` passed to `check_report_file`. Do **not** modify `task_report_glob`.

### C5 — Skill-enforce promotion (`sdd-skill-enforcement-hook.sh`)
- **Tighten detection:** require an explicit SDD *imperative* in a user message (e.g. `(invoke|use|run|follow|start|let'?s use)\b.{0,20}(subagent-driven-development|sdd)`); drop the bare-mention alternatives. Keep the `SKILL_LOADED` allow, the impl-file path filter, and all early exits.
- **Bypass:** `SUPERPOWERS_SDD_BYPASS` set → allow + stderr warning.
- **Block:** SDD imperative + skill-not-loaded + impl-file + no bypass → `exit 2` with the existing warning text on stderr.
- New dedicated test file (none exists today).

## Acceptance Criteria

- [ ] 2-module plan **without** Source Contracts runs end-to-end through `transition-module.py` with zero manual workarounds (module-2 first task dispatches; pre-completion passes).
- [ ] 2-module plan **with** Source Contracts does not BLOCK at module 2 (Check 5 finds archived Task 0).
- [ ] No-Task-0 single-module plan starting at Task 1 dispatches without forging a `task=0` log entry.
- [ ] `transition-module.py` **refuses** to transition when a completing-module task's dispatch provenance is missing.
- [ ] Pre-completion gate passes with completed-module reports under `archive-*/`.
- [ ] `sdd-skill-enforcement-hook.sh` blocks (`exit 2`) an impl Write/Edit when SDD was explicitly requested + skill never loaded; `SUPERPOWERS_SDD_BYPASS` recovers; a casual SDD mention does not false-block.
- [ ] Check 4c and `validate_module_completion` agree on require/exempt decisions (SSOT agreement test passes, keyed on the file-based minimum signal).
- [ ] All existing static + unit + integration suites pass; new tests added; `sdd-e2e-test.sh` exercises module-2-first-task **post-transition**.

## Docs to update on completion

CLAUDE.md (Hooks-Based Enforcement + Hook Development Gotchas: add `SUPERPOWERS_SDD_BYPASS`, the skip-guard, transition-time provenance, archive-aware checks); `docs/ARaymond-customization-manifest.md`; mark N3/N4/N10 done in `BACKLOG.md`.
