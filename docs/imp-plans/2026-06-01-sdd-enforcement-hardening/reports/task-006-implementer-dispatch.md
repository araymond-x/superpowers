You are a focused technical writer/engineer. You are implementing Task 6 of the SDD Enforcement Hardening plan — DOCUMENTATION ONLY (`review_tier: minimum`). No production code, no tests.

Work from: `/Users/araymond/projects/claude-custom/superpowers/.worktrees/sdd-enforcement-hardening` (git worktree, branch `sdd-enforcement-hardening`).

## Task Description (VERBATIM from plan.md, Task 6)

### Task 6: Update documentation (CLAUDE.md, manifest, BACKLOG)

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/ARaymond-customization-manifest.md`
- Modify: `docs/process-improvement-findings/BACKLOG.md`

`review_tier: minimum` — mechanical documentation edits, no behavior change.

**Context:** Document the five components (plus the folded-in N11 recompute) so a future session knows they exist. Per CLAUDE.md "Documentation Maintenance," update the affected sections and refresh test counts. Read each target section first; add (do not rewrite) the facts below.

- [ ] **Step 1: CLAUDE.md — "Hooks-Based Enforcement" section.** Add bullets recording:
  - N3a: Check 4c now skips when `PREV < MANIFEST_TASK_START` (module-first task, or no-Task-0 plan); boundary provenance is re-verified at transition time.
  - N10: Check 5's Task-0 lookup now globs `archive-*/` (a Source-Contracts plan finds an archived Task 0 at module 2). Local glob only — `task_report_glob` unchanged.
  - N3b: `transition-module.py:validate_module_completion` verifies dispatch-log provenance for each completing-module task before truncation, with a file-based minimum-tier waiver and a `task_type:verification` per-task exemption.
  - N11: `transition-module.py:transition()` recomputes `enforcement.context_summary_at` for the next module on transition (was pinned to the completed module's midpoint, firing Check 6b early in later modules).
  - N4: `controller-checkpoint.py` `find_report_file`/`find_all_report_files` recurse into `archive-*/` (pre-completion passes with archived reports). Name the intentionally-flat lookups.
  - C5: `sdd-skill-enforcement-hook.sh` is now **blocking** (`exit 2`) on an explicit SDD imperative + impl-file + skill-not-loaded; `SUPERPOWERS_SDD_BYPASS` is the escape hatch.

- [ ] **Step 2: CLAUDE.md — "Hook Development Gotchas" section.** Add: `SUPERPOWERS_SDD_BYPASS` env var (allow + stderr warning) mirrors `SUPERPOWERS_VALIDATOR_BYPASS`. Note the C5 detection regex `(invoke|use|run|follow|start|let'?s use)\b.{0,20}(...)` is verified under both ugrep and stock BSD `/usr/bin/grep -iE`.

- [ ] **Step 3: CLAUDE.md — "Pipeline Flexibility" Known follow-ups.** Mark **N3 (N3a+N3b)**, **N4**, **N10**, and **N11** resolved by this feature. Update the "Testing" line's unit-test count (it increases by the number of new tests added in Tasks 0–4 — compute the real number from `pytest` collection, do not guess).

- [ ] **Step 4: docs/ARaymond-customization-manifest.md.** Add an inventory entry for this feature under the SDD scripts section (the four modified scripts + new test files), dated 2026-06-01.

- [ ] **Step 5: BACKLOG.md.** Mark N3/N4/N10 done (find their rows and update status; add a brief "resolved by 2026-06-01-sdd-enforcement-hardening" note). Add a **row N11 marked DONE** (discovered during this feature's plan review and fixed here, Task 3): *"`transition-module.py` did not recompute `enforcement.context_summary_at` on module transition — it stayed pinned to the completed module's midpoint, firing Check 6b early for later-module tasks. Fixed: `transition()` recomputes it for the next module's range."*

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md docs/ARaymond-customization-manifest.md docs/process-improvement-findings/BACKLOG.md
git commit -m "docs(sdd): record enforcement-hardening changes; mark N3/N4/N10/N11 done"
```

## VERIFIED FACTS & COUNTS (use these; re-verify counts yourself before writing)

**Real test counts (controller measured — re-confirm via pytest before writing):**
- Unit tests: **380 → 405** (+25). New/changed test files this feature: `test_sdd_skill_enforcement.py` (new, 10), `test_checkpoint_archive_aware.py` (new, 4), `test_sdd_hook_hardening.py` (new, 4), `test_ssot_minimum_agreement.py` (new, 4), `test_transition_module.py` (modified, +3). Re-verify with `.venv/bin/python3 -m pytest tests/unit/ -q | tail -1` → should read `405 passed`.
- Integration e2e: **10 → 11 steps** (`bash tests/integration/sdd-e2e-test.sh` → `E2E PIPELINE PASS - 11 steps composed correctly`).
- Regression suite: **145 PASS / 3 advisory WARNING** — UNCHANGED (no SKILL.md structural changes this feature). Confirm with `python3 tests/ARaymond-skill-regression/validate-all-skills.py` if you wish.
- Install checks: **104** — UNCHANGED (no registration/symlink changes; settings.json:78 registration of the skill-enforce hook is unchanged — C5 only changed the hook's BEHAVIOR, not its registration).

**Commits this feature (for the manifest inventory):** Task 0 `2b3c5b1`+`8b7a95c` (sdd-skill-enforcement-hook.sh blocking + C1/I1 fix), Task 1 `d8cf7e9` (controller-checkpoint.py N4), Task 2 `fe52b67` (sdd-pre-dispatch-hook.sh N3a+N10), Task 3 `004ba75` (transition-module.py N3b+N11), Task 4 `db7e25f` (test_ssot_minimum_agreement.py), Task 5 `82e344f` (e2e). The 4 modified production scripts: sdd-skill-enforcement-hook.sh, controller-checkpoint.py, sdd-pre-dispatch-hook.sh, transition-module.py.

## ADDITIONAL BACKLOG rows to add in Step 5 (net-new follow-ups found during execution — aggregated from deviations.md; the controller pre-committed these to BACKLOG)
Add these as NEW rows (use the BACKLOG's existing ID/format convention — e.g., N-prefixed or next available; read the file to match its style):
1. **Transition gate vs hook gate divergence (micro+modules):** `transition-module.py:validate_module_completion` gates provenance on `process_requirements.{spec,quality}_review_mode != "skip"`, while the hook gates on `enforcement.dispatch_provenance`. For a micro+modules plan (dispatch_provenance=False but modes=self_review≠skip), the transition would require provenance the hook never wrote (over-enforcement). Only reachable in micro+modules (which validate-plan.py already WARNs against). Follow-up: align the transition gate with `enforcement.dispatch_provenance`, or document the intent. (Found 2026-06-01, Task 3 spec review.)
2. **plan.md Task-4 SSOT-test snippet un-runnable as written:** the canonical Task 4 test snippet in `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md` passes nonexistent subdirs to two subprocess drivers (git-init-before-mkdir → FileNotFoundError); the SHIPPED test added two `mkdir()` lines. Follow-up: backport the 2 mkdir lines into the plan's verbatim block so a future re-run from plan.md doesn't re-hit the error. (Found 2026-06-01, Task 4.)
3. **C1 pre-existing pipe bug also present in main's advisory skill-enforce hook:** the `grep | grep -q` under pipefail SIGPIPE bug (fixed here for the now-blocking hook) is latent in main's still-advisory copy (it would silently fail to inject the advisory on >64KB transcripts). Low severity while advisory; will be resolved when this feature merges to main. (Found 2026-06-01, Task 0.)

## CRITICAL GUARDRAILS
1. **ADD, do not rewrite.** Read each target section FIRST, then append/insert the facts. Preserve all existing content. Do NOT restructure or reformat unrelated lines.
2. **Counts must be REAL** — re-run `pytest tests/unit/ -q | tail -1` and confirm 405 before writing it; do not guess. If the count differs from 405, use the actual number and note the discrepancy.
3. **Write-scope = exactly 3 files:** CLAUDE.md, docs/ARaymond-customization-manifest.md, docs/process-improvement-findings/BACKLOG.md. Do NOT touch any code, test, the plan, or other docs.
4. **Match each file's existing style** (CLAUDE.md bullet/section conventions; BACKLOG.md row format — read it to match; manifest inventory format — read the SDD scripts section).
5. **N3 = N3a + N3b** (the BACKLOG's N3 covers both the hook skip-guard and the transition provenance). N10, N4 likely have their own rows. N11 is net-new (add it).

## Source Files (read before editing)
- `CLAUDE.md` — read "Hooks-Based Enforcement", "Hook Development Gotchas", "Pipeline Flexibility" (Known follow-ups), and "Testing" sections.
- `docs/process-improvement-findings/BACKLOG.md` — find the N3/N4/N10 rows + the row-format convention.
- `docs/ARaymond-customization-manifest.md` — find the SDD scripts inventory section.

## Subdirectory CLAUDE.md Files
The ROOT CLAUDE.md IS the primary file you're editing. Its "Documentation Maintenance" section is the governing routine. No other subdir CLAUDE.md applies.

## Before You Begin
If a referenced section doesn't exist in CLAUDE.md/BACKLOG (e.g., no N3/N4/N10 rows found), STOP and report — don't invent structure. Ask if the BACKLOG row format is unclear.

## Your Job
1. Read the 3 target files' relevant sections.
2. Re-verify the unit count (405) + e2e step count (11) yourself.
3. Steps 1–5: add the documented facts + counts + the 3 net-new BACKLOG follow-ups, matching each file's style. ADD, don't rewrite.
4. Step 6: commit the 3 files with the exact message.
5. Self-review (counts real; facts accurate; existing content preserved; only the 3 files touched). Report.

## Report Format
Standard YAML frontmatter (schema_version, task_id: 6, status, files_changed [the 3 docs], tests {written: 0, passing: 0, command: "n/a — docs only", result: PASS}, contract_compliance) then prose sections: Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations from Plan, Self-Review Findings, Concerns. Your final message IS the report (saved + validated). DONE_WITH_CONCERNS if any deviations/concerns; BLOCKED if a referenced section is missing.
