# SDD Cleanup + Integration-Test Gate — Distilled Implementation Spec

> **Source**: `spec.md` (18 decisions; archetype extension). **Revised** 2026-06-06 per Codex review.
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

## Contract Facts

Non-negotiable interface facts. All paths repo-root-relative.

**Model fields (new, optional + defaulted → NO `CURRENT_SCHEMA_VERSION` bump):**
- `ImplementerReport.task_type: Literal["implementation","verification"] = "implementation"`
  (`skills/scripts/models/implementer_report.py`). When `verification`, the
  `files_changed_non_empty_for_done` validator (L48-53) is **exempt**.
- `IntegrationTest(StrictModel)` with `path: str` + a validator (non-absolute, no `..`, repo-relative);
  `Plan.integration_test: IntegrationTest | None = None` (`plan.py`). **Presence == required.**

**N16 needs ALL consumers (model change alone is insufficient — default is `implementation`):**
- Add `task_type` to the report frontmatter template `implementer-prompt.md` (~L193-206).
- `subagent-driven-development/SKILL.md` verification guidance (~L355-362): instruct subagent to emit
  `task_type: verification`.
- `validate-report.py` fixture: real markdown verification report, `files_changed: []`, status DONE → validates.

**N5 — fence-aware at ALL task-header sites (7), not just the 2 named constants:**
- `validate-plan.py`: `TASK_HEADER_RE` (L48), `analyse_tasks` inline (L160), Task-0 (L264).
- `controller-checkpoint.py`: `TASK_HEADER_PATTERN` (L58), `has_task_zero` (L429), checkbox range (L474/L486).
- Route each script's parsing through ONE fence-aware helper that skips `### Task N` inside ```` ``` ```` blocks.

**N7:** `controller-checkpoint.py` pre-execution `source_contracts` (L444-465 + L690-694) treats
`None`/empty/"None" as **valid-absent → PASS**.

**N9 — two helpers in `controller-checkpoint.py`:**
- `_task_ids_where(plan_contents, field, value) -> (set, parsed_any)` (collapses `_declared_minimum_task_ids` + `_verification_task_ids`).
- `_load_all_plan_contents(manifest)` → parent `manifest.plan_file` + every module file, **de-duped**.
  Route declared-min / verification-id / counts / report-matching / C2 through it. (Fixes the parent-plan
  blind spot: `_load_manifest_config:591-600` overwrites `plan_file` with the active module; the parent is
  never otherwise scanned.) **Land before C2.**

**N12:** `transition-module.py:validate_module_completion` (L122-130) — keep spec/quality **file-existence**
under `process_requirements.{spec,quality}_review_mode != "skip"`; gate ONLY `_has_dispatch_provenance()`
on `enforcement.dispatch_provenance`.

**N17:** `transition-module.py` (~L110) — main-plan fallback for verification-id lookup when `module.file`
empty (mirror `sdd-pre-dispatch-hook.sh:297-298`).

**N1 — TEST ONLY (no hook edit):** the hook already accumulates (`sdd-pre-dispatch-hook.sh:320` `ERRORS=()`
→ all checks append → L702-709 emit all then `exit 2`). Add a regression test asserting multi-error
accumulation. Leave early-exits :130 (manifest guard) and :207 (range guard) as-is. **No item edits any
baselined hook → NO `check-hooks.sh --capture`.**

**N13:** backport 2 `mkdir()` lines into the Task-4 snippet in
`docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md` (folded into N5 task).

**C2 Check 10 (NEW pre-completion check in `controller-checkpoint.py`, sibling to Check 8/9):**
- Aggregate `integration_test` across parent+modules via `_load_all_plan_contents`; de-dupe paths; ALL must pass.
- Per path: (a) `Path(<git_root>/<path>).is_file()` AND (b) **in this feature's changeset (added or modified)**:
  `git diff --name-only <base> -- <path>` **∪** `git ls-files --others --exclude-standard -- <path>`
  (tracked-diff OR untracked — the union catches a never-`git add`ed new test).
- Reuse ONLY `_resolve_git_root` (~L517). NOT `_check_verification_git_reality` (it's a timestamp-window
  `git log`, not a diff). Base resolver: `origin/HEAD` → `main` → `master`; FAIL (infra error) if none.
  On default branch (`merge-base == HEAD`) committed diff is empty → rely on untracked + working-tree set.
  Compare against the **working tree** (not `<base>..HEAD`).
- Pass → `checks["integration_test_present"]=PASS`; any fail → FAIL + blocker `integration_test_missing`.
  No declaration → PASS (skipped).
- **Contract honesty:** proves the test is *part of the changeset* (added OR modified) — NOT brand-new;
  modifying an existing integration test is acceptable.

**C2 risk-surface WARNING patterns** (`validate-plan.py`, advisory): `router`, `routes/`, `middleware`,
`auth`, `migration`, `cache`, `cors`, `security`.

**Docs:** C2 documentation → `writing-plans/SKILL.md` (NOT SDD SKILL.md — word ceiling).

**Which copy enforces what:** live SDD gates resolve to **main** (symlink) — they run main's pre-fix
scripts and do NOT exercise this feature's new code. C2/N5/N7/N9 validated by **worktree unit + e2e ONLY**;
live main gate does not enforce C2 until merge. **Worktree required**; verify `~/.claude/skills/superpowers` → main before execution.

**Self-hosting hazards (feature fixes bugs still live in main during its own run):** (1) N5 — main's
`validate-plan.py` is still fence-blind → plan.md / module files must NOT contain fenced ```` ``` ````-wrapped
`### Task N` examples (live plan-validation-gate would miscount → could FAIL before SDD). (2) N7 — main's
pre-execution still FAILs on `Source Contracts: None` → pre-log an accepted deviation in Module 1. Both clear only post-merge.

**Plan/process facts:** `Source Contracts: None`; **no Task 0**; current source files as Pattern References.
Two modules; Module 1 → `transition-module.py` → Module 2.

## Open Decisions

(none — all resolved)

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| D1 | Packaging | One combined 2-module feature (M1 cleanup → transition → M2 C2) |
| D2 | Module 1 scope | Core 7 + N9 |
| D3 | C2 gate strength | Declaration + changeset-existence gate + plan-time risk WARNING |
| D4 | N16 | Add `task_type` to `ImplementerReport`, exempt `verification` |
| D5 | N7 | Frontmatter `source_contracts`; None/empty = valid-absent → PASS |
| D6 | N12 | Gate only provenance on `enforcement.dispatch_provenance` |
| D7 | N13 | Fold into the N5 task |
| D8 | C2 docs | `writing-plans/SKILL.md` |
| D9 | Contracts | `Source Contracts: None`; Pattern References, no Task 0 |
| D10 | Workspace | Worktree (required) |
| D11 | N16 scope | Also update report template + verification prompt + validate-report fixture |
| D12 | N5 scope | ALL 7 task-header consumers via fence-aware helper(s) |
| D13 | N12 precision | Split file-existence (review modes) from provenance (dispatch_provenance) |
| D14 | N1 | Test-only regression (hook already accumulates); no hook edit; no baseline recapture |
| D15 | C2 changeset | Added-or-modified, tracked `∪` untracked; drop "new test" claim |
| D16 | Parent+modules | `_load_all_plan_contents` helper; retrofit declared-min/verif/counts |
| D17 | Which-copy | C2 validated by worktree tests/e2e only; main gate enforces post-merge |
| D18 | Minors | base resolver order; multi-declaration de-dupe (all pass); path validator + `is_file()` |

## Component Specifications

### Module 1 (see Contract Facts for exact targets)
N16 (model + template + prompt + fixture) · N5 (7 sites, fence-aware) · N7 (source_contracts None=PASS) ·
N9 (`_task_ids_where` + `_load_all_plan_contents`; **before C2**) · N12 (split file/provenance) ·
N17 (main-plan fallback) · N1 (test-only) · N13 (doc, folded into N5).
Ordering: N9 + N5 before C2 consumes them; N12/N17 independent; N1/N13 any time.

### Module 2 — C2
1. Model `IntegrationTest{path}` + `Plan.integration_test` + path validator (Contract Facts).
2. `validate-plan.py` risk-surface WARNING.
3. Pre-completion **Check 10** (Contract Facts: parent+modules aggregate, tracked∪untracked changeset, base resolver).
4. **Fixtures (≥6):** (1) risk-surface no-decl → WARNING; (2) path missing → FAIL; (3) path exists but unchanged → FAIL; (4) untracked-new → PASS; (5) modified-tracked → PASS; (6) parent-only declaration in modular plan → seen.
5. Docs in `writing-plans/SKILL.md`.

### Testing / closeout
pytest units per item; extend `sdd-e2e-test.sh` with a C2 Check-10 step (untracked + parent-only cases);
keep `validate-all-skills.py` + `verify-symlink-install.sh` green. **No hook-baseline recapture** (no hook edits).
After merge: update CLAUDE.md / manifest / BACKLOG (flip items done; annotate N1 re-scope + N5 expanded scope).
The 2-module execution validates the live multi-module transition path only (not the new code).

## Acceptance Criteria

- [ ] N16: real-markdown `verification` report w/ empty `files_changed` validates; `implementation` empty + DONE still FAILs; template + prompt emit `task_type`.
- [ ] N5: fenced `### Task N` ignored at ALL sites (validate-plan count/spans/Task-0; checkpoint has_task_zero/checkbox/verif-ratio).
- [ ] N7: `Source Contracts: None` → pre-execution PASS.
- [ ] N9: single `_task_ids_where` + single `_load_all_plan_contents`; parent-only declarations visible; ratio paths unchanged.
- [ ] N12: micro+modules w/ self-review files + no dispatch log → transition PASS; missing self-review files → FAIL.
- [ ] N17: transition reads verif ids from main plan when `module.file` empty.
- [ ] N1: regression test for multi-error accumulation; no hook edit; baseline untouched.
- [ ] N13: 2026-06-01 plan.md Task-4 snippet runs as written.
- [ ] C2: model + path validator; validate-plan WARNs on risk-surface + no decl; Check 10 FAILs on missing/unchanged, PASSes on untracked-new + modified-tracked, sees parent-only; ≥6 fixtures.
- [ ] 2-module feature completes via `transition-module.py` with no manual manifest advances.
- [ ] Static + integration suites green (worktree copy); `validate-all-skills.py` PASS-with-≤current-warnings.

## Out of scope — do NOT pull into this plan
Track-3 verification-task half (post-merge, needs N16 on main); N6, N8; C1/C3/C4/C5 (sprint-4 spikes).
