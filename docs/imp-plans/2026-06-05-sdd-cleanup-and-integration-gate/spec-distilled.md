# SDD Cleanup + Integration-Test Gate — Distilled Implementation Spec

> **Source**: `spec.md` (10 decisions, archetype: extension)
> **Distilled**: 2026-06-05
> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

## Contract Facts

Non-negotiable interface facts. All paths repo-root-relative.

**Model fields (new, both optional + defaulted → NO `CURRENT_SCHEMA_VERSION` bump):**
- `ImplementerReport.task_type: Literal["implementation", "verification"] = "implementation"`
  (`skills/scripts/models/implementer_report.py`). When `verification`, the
  `files_changed_non_empty_for_done` validator (L48-53) is **exempt** (verification tasks change 0 files).
- `IntegrationTest(StrictModel)` with single field `path: str`; `Plan.integration_test: IntegrationTest | None = None`
  (`skills/scripts/models/plan.py`). **Presence == required.**

**Regex (BOTH sites must skip `### Task N` headers inside ```` ``` ```` fenced blocks):**
- `TASK_HEADER_RE` — `validate-plan.py:48`
- `TASK_HEADER_PATTERN` — `controller-checkpoint.py:58`

**N7 pre-execution:** `controller-checkpoint.py` `source_contracts` check must treat `None` / empty /
prose `"None"` as **valid-absent → PASS** (currently FAILs). Prefer reading the frontmatter
`source_contracts` field.

**N12 transition gate:** `transition-module.py:validate_module_completion` gates provenance on
`enforcement.dispatch_provenance` (NOT `process_requirements.{spec,quality}_review_mode != "skip"`).

**N17 transition fallback:** `transition-module.py:validate_module_completion` (~L110) reads verification
task ids from `MANIFEST_PLAN_FILE` when `module.file` is empty (mirrors hook `sdd-pre-dispatch-hook.sh:297-298`).

**N1 hook:** `sdd-pre-dispatch-hook.sh` implementer-dispatch enforcement block accumulates ALL missing
prereqs into one BLOCKED message (still `exit 2`). **Re-capture hook-integrity baseline in the same
change**: `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture`, commit `baseline.txt`.

**C2 Check 10 git mechanism (NEW code — does not exist today):**
- Reuse ONLY `_resolve_git_root` (`controller-checkpoint.py` ~L517) for repo root.
- `_check_verification_git_reality` is a timestamp-window `git log --after/--before` — NOT reusable for a diff.
- diff base = `git merge-base <default-branch> HEAD`.
- existence-in-changeset = `git diff --name-only <base> -- <path>` against the **working tree** (NOT
  `<base>..HEAD`) so an uncommitted new test is still seen.
- There is **no** base/branch field in `SddSession`/`ArtifactPaths`/`Enforcement` — derive base via
  merge-base; do not add a manifest field.

**C2 risk-surface WARNING patterns** (`validate-plan.py`, advisory only): `router`, `routes/`,
`middleware`, `auth`, `migration`, `cache`, `cors`, `security`.

**Docs:** C2 documentation goes in `writing-plans/SKILL.md` (NOT SDD SKILL.md — at 5029-word ceiling).

**Plan/process facts:** `Source Contracts: None` (no external contract); **no Task 0**; current source
files injected as Pattern References. Two modules; Module 1 → `transition-module.py` → Module 2.

## Open Decisions

(none — all resolved)

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| D1 | Packaging | One combined 2-module feature (Module 1 cleanup → transition → Module 2 C2) |
| D2 | Module 1 scope | Core 7 (N16,N5,N7,N1,N12,N13,N17) + N9 |
| D3 | C2 gate strength | Declaration + git-diff existence gate + plan-time risk WARNING |
| D4 | N16 | Add `task_type` to `ImplementerReport`, exempt `verification` |
| D5 | N7 | Read frontmatter `source_contracts`; None/empty = valid-absent → PASS |
| D6 | N12 | Align transition gate to `enforcement.dispatch_provenance` |
| D7 | N13 | Fold into the N5 task as a trailing doc chore |
| D8 | C2 docs | `writing-plans/SKILL.md` |
| D9 | Contracts | `Source Contracts: None`; Pattern References, no Task 0 |
| D10 | Workspace | Worktree (recommended; confirm at workspace setup) |

## Component Specifications

### Module 1 — Cleanup bundle

| Item | File(s) | Change |
|---|---|---|
| N16 | `implementer_report.py` | Add `task_type` field; exempt `verification` from `files_changed_non_empty_for_done`. |
| N5 | `validate-plan.py:48`, `controller-checkpoint.py:58` | Both regexes skip `### Task N` inside fenced blocks. If `_report_utils.py` is importable by both, make a single fence-aware helper; else fix both inline. |
| N7 | `controller-checkpoint.py` (pre-execution) | `source_contracts` None/empty → PASS. |
| N9 | `controller-checkpoint.py` | Collapse `_declared_minimum_task_ids` + `_verification_task_ids` into `_task_ids_where(plan_contents, field, value) -> (set, parsed_any)`. Behavior-preserving. **Do before C2** (Check 10 may reuse). |
| N12 | `transition-module.py` | Provenance gate keys on `enforcement.dispatch_provenance`. |
| N17 | `transition-module.py` (~L110) | Main-plan fallback for verification-id lookup when `module.file` empty. |
| N1 | `sdd-pre-dispatch-hook.sh` | Accumulate all missing prereqs into one BLOCKED message; re-capture hook baseline same change. Riskiest — sequence last in module. |
| N13 | `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md` | Backport 2 `mkdir()` lines into the Task-4 verbatim snippet (folded into N5 task). |

**Module-1 internal ordering:** N9 and N5 before C2-relevant work; N1 last (blast radius + baseline).

### Module 2 — C2 integration-test gate

1. **Model** (`plan.py`): add `IntegrationTest{path}` + `Plan.integration_test` (see Contract Facts).
2. **Plan-time WARNING** (`validate-plan.py`): risk-surface patterns matched in File Map / write-scope
   AND `integration_test` absent → advisory WARNING (not blocking).
3. **Pre-completion Check 10** (`controller-checkpoint.py`, sibling to Check 8/9 in `run_pre_completion`):
   if `integration_test` declared, verify `path` (a) exists on disk AND (b) is in this feature's
   changeset (git mechanism per Contract Facts). Pass → `checks["integration_test_present"]=PASS`;
   fail either → FAIL + blocker `integration_test_missing`. No declaration → PASS (skipped).
4. **Fixtures** (required deliverable): (1) route-touching plan, no declaration → WARNING; (2) declared
   path missing/not-in-diff → Check 10 FAIL; (3) declared path present-in-diff → Check 10 PASS.
5. **Docs** (`writing-plans/SKILL.md`): "Declaring an integration test" subsection.

### Testing / closeout

- pytest units per item; extend `tests/integration/sdd-e2e-test.sh` with a C2 Check-10 step.
- Keep `tests/ARaymond-skill-regression/validate-all-skills.py` + `tests/ARaymond-installation/verify-symlink-install.sh` green.
- After merge: update CLAUDE.md (Check 10, N1 hook behavior, test counts), customization manifest,
  BACKLOG.md (flip N16/N5/N7/N1/N12/N13/N17/N9 + C2 to `done`).
- The 2-module execution IS the live multi-module validation (Track 3 multi-module half).
- **Out of scope — do NOT pull into this plan:** N6, N8 (opportunistic); C1, C3, C4, C5 (sprint-4 spikes); Track 3 verification-task half (separate post-merge run, needs N16 on main first).

## Acceptance Criteria

- [ ] N16: `verification` report w/ empty `files_changed` validates; `implementation` report w/ empty `files_changed` + DONE still FAILs.
- [ ] N5: fenced `### Task N` headers not counted by either regex.
- [ ] N7: `Source Contracts: None` → pre-execution PASS.
- [ ] N9: `_task_ids_where` is the single parser; both ratio paths behavior-unchanged.
- [ ] N12: transition provenance gate keys on `enforcement.dispatch_provenance`.
- [ ] N17: transition reads verification ids from main plan when `module.file` empty.
- [ ] N1: dispatch missing multiple prereqs lists all in one BLOCKED message; hook baseline re-captured + committed.
- [ ] N13: the 2026-06-01 plan.md Task-4 snippet runs as written.
- [ ] C2: model accepts `integration_test`; validate-plan WARNs on risk-surface + no declaration; Check 10 FAILs on missing/not-in-diff and PASSes on present-in-diff; 3 fixtures exist.
- [ ] 2-module feature completes through `transition-module.py` with no manual manifest advances.
- [ ] Full static + integration suites green; `validate-all-skills.py` PASS-with-≤current-warnings.
