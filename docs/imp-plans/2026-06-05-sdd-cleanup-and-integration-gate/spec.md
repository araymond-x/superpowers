# SDD Cleanup + Integration-Test Gate — Design Spec

> **Feature dir**: `docs/imp-plans/2026-06-05-sdd-cleanup-and-integration-gate/`
> **Created**: 2026-06-05
> **Status**: design (brainstorming output, pre-plan)
> **Archetype**: extension (+ refactor elements; no obsolescence)
> **Entry mode**: brainstorming
> **Sprint**: superpowers fork sprint 3 (anchor = C2; see `docs/process-improvement-findings/BACKLOG.md` → "Recommended sprint 3")

## 1. Purpose

Sprint 3 has one combined deliverable, executed as a **2-module SDD feature** that doubles as the
first **live multi-module run** of the merged N3/N4/N10/N11 transition path:

- **Module 1 — Cleanup bundle**: close the loop on the bug-fixes and hardening follow-ups left open
  by the `pipeline-flexibility` and `sdd-enforcement-hardening` merges (BACKLOG items N16, N5, N7,
  N1, N12, N13, N17, N9).
- **Module 2 — C2 integration-test gate**: the sprint anchor. Raise the integration-test floor so a
  risk-surface feature (route / contract / security / migration) cannot reach completion without an
  integration test that actually exists for it. Closes the practerus M15 cache-poisoning class
  (a real security bug that passed every unit test + structural validator because no integration
  test exercised the cross-module path — `docs/process-improvement-findings/2026-05-21-skill-evaluation.md` §2.2, §9.8 quote 1).

Module 1 must fully complete and transition (via `transition-module.py`) before Module 2 begins.
That transition is the live exercise; the run is enforced by **main's current scripts** the whole way
(the live hook resolves `SUPERPOWERS_ROOT` via `BASH_SOURCE` → the symlink → main, and a multi-module
feature transitions within one branch — nothing merges until the end).

## 2. Goals / Non-Goals

**Goals**
- Every Module-1 item fixed with a failing-test-first treatment for the three true bug-fixes
  (N16, N5, N7) and behavior-preserving tests for the refactors (N9, N12, N17, N1).
- C2 ships: a Plan-model declaration field, a plan-time risk-surface WARNING, a pre-completion
  Check 10 (existence + git-diff), and the fixtures that prove a missing integration path is caught.
- The 2-module execution itself validates the live multi-module transition path.

**Non-Goals (explicitly deferred)**
- The **non-last `verification` task** half of Track 3 — requires N16 on main first (the live hook
  runs main's `validate-report.py`), so it is a small **post-merge** run, logged as a follow-up.
- C4 computed risk heuristics beyond the single advisory WARNING (C2's WARNING is the soft overlap).
- Making the pre-completion gate itself hook-enforced (that is C3, separately tracked).
- Forgery-proofing the gate (controller-written evidence files are a known class — C3/C5).
- N6 (SKILL.md framing pass) and N8 (F6 regression-check rewrite) — left standalone-opportunistic.

## 3. Decision Log

| # | Decision | Chosen | Options considered / rationale |
|---|----------|--------|-------------------------------|
| D1 | Packaging | **One combined 2-module feature now** | vs. sequential two features; vs. Track-1-only. User chose the combined path to exercise the live multi-module transition immediately. Accepts that the verification-task half of Track 3 is a separate post-merge run. |
| D2 | Module 1 scope | **Core 7 + N9** | N9's `_task_ids_where` helper is reused by C2's Check 10 → pull it in. N6/N8 stay opportunistic. |
| D3 | C2 gate strength | **Declaration + git-diff existence gate** | vs. plan-time WARNING only (doesn't close the gap — practerus's test never existed); vs. existence+run-evidence (pushes M→L, over-engineers "did it pass"). Existence-in-diff proves a *new* test was written and is harder to fake than a pointed-at pre-existing file. |
| D4 | N16 fix shape | **Add `task_type` to `ImplementerReport`, exempt `verification`** | vs. relax rule on empty `files_changed` + tests PASS. Field-add mirrors `Task.task_type`, keeps the rule strict for real implementation tasks. Non-breaking, no schema bump. |
| D5 | N7 fix shape | **Read frontmatter `source_contracts` field; treat None/empty as valid-absent** | vs. prose string-match on "None". Uses the structured `Plan.source_contracts`. |
| D6 | N12 fix shape | **Align transition gate to `enforcement.dispatch_provenance`** | vs. document the divergence. SSOT: transition gate and hook gate must agree. |
| D7 | N13 handling | **Fold into the N5 task as a trailing doc chore** | vs. own task (ceremony for a 1-line doc edit); vs. `task_type:verification` (would add a verification task to this feature — disallowed, N16 not on main). |
| D8 | C2 docs location | **`writing-plans/SKILL.md`** | The `integration_test` declaration is a plan-authoring concern, and the SDD SKILL.md is at its 5029-word ceiling (would force an offsetting extraction). |
| D9 | Task 0 / contracts | **`Source Contracts: None`; use Pattern References instead** | No external contract. Internal contracts (model schemas, check structures, regexes) are injected as Pattern References (current source files as required reads) — the established mechanism. N7 incidentally fixes the `Source Contracts: None` false-positive this plan would otherwise trip. |
| D10 | Workspace | **Worktree (recommended)** | This feature edits the very enforcement scripts that gate it; a worktree keeps main's live scripts stable for the whole run. To be confirmed at workspace setup. |

## 4. Module 1 — Cleanup Bundle

All paths relative to repo root. Each task lists its source file(s) as a Pattern Reference (required read).

| Item | File(s) | Fix | Test obligation |
|---|---|---|---|
| **N16** | `skills/scripts/models/implementer_report.py` | Add `task_type: Literal["implementation","verification"]="implementation"`; exempt `verification` from `files_changed_non_empty_for_done` (lines 48-53). | RED: verification report w/ empty `files_changed` currently raises → after fix, validates. |
| **N5** | `skills/subagent-driven-development/scripts/validate-plan.py:48` (`TASK_HEADER_RE`) + `controller-checkpoint.py:58` (`TASK_HEADER_PATTERN`) | Make both regexes skip `### Task N` headers inside ```` ``` ```` fenced blocks. Check whether `_report_utils.py` is importable by both → if so, a single fence-aware helper (true SSOT); else fix both inline + note. | RED: a plan with `### Task 91` inside a fenced fixture currently inflates task counts → after fix, ignored. |
| **N7** | `controller-checkpoint.py` (pre-execution `source_contracts` check) | Read the frontmatter `source_contracts` field; treat `None`/empty/"None" as **valid-absent → PASS**, not FAIL. | RED: `Source Contracts: None` currently FAILs pre-execution → after fix, PASS. |
| **N9** | `controller-checkpoint.py` (`_declared_minimum_task_ids` ~L228, `_verification_task_ids` ~L263) | Collapse into `_task_ids_where(plan_contents, field, value) -> (set, parsed_any)`. Behavior-preserving; **C2 Check 10 / C2 parsing reuses it**. Sequence before C2. | Behavior-preserving: existing ratio tests still pass; add a direct helper test. |
| **N12** | `transition-module.py:validate_module_completion` | Gate provenance on `enforcement.dispatch_provenance` (matching the hook), not `process_requirements.{spec,quality}_review_mode != "skip"`. | Test: micro+modules manifest (dispatch_provenance=False, modes=self_review) no longer over-enforces at transition. |
| **N17** | `transition-module.py:validate_module_completion` (~L110) | Add main-plan fallback for verification-id lookup when `module.file` empty (mirror hook `sdd-pre-dispatch-hook.sh:297-298`). | Test: manifest with empty `module.file` reads verification ids from `MANIFEST_PLAN_FILE`. |
| **N1** | `sdd-pre-dispatch-hook.sh` | Accumulate **all** missing prereqs in the implementer-dispatch enforcement block; emit together (still `exit 2`). **Riskiest** — touches hook control flow. **Re-capture hook-integrity baseline in the same change** (`check-hooks.sh --capture`). | RED: a dispatch missing 2 prereqs currently reports only the first → after fix, reports both. |
| **N13** | `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md` | Backport the 2 `mkdir()` lines into the verbatim Task-4 test snippet. Folded into the N5 task as a trailing doc chore (D7). | None (doc-only). |

**Module-1 internal ordering**: N9 (helper) and N5 (accurate task counts) land before anything C2
reuses; N1 last within the module given its blast radius + baseline re-capture.

## 5. Module 2 — C2 Integration-Test Gate

**5.1 Plan model** (`skills/scripts/models/plan.py`)
```python
class IntegrationTest(StrictModel):
    path: str   # path (repo-root-relative) to the integration test this feature must ship

class Plan(SchemaVersionedModel):
    ...
    integration_test: IntegrationTest | None = None   # presence == required
```
Optional, default `None`, **no schema bump** (consistent with `task_type`/`review_tier`/`entry_mode`).

**5.2 Plan-time WARNING** (`validate-plan.py`)
Scan the plan's File Map / write-scope file paths for risk-surface patterns:
`router`, `routes/`, `middleware`, `auth`, `migration`, `cache`, `cors`, `security`.
If any match **and** `integration_test` is absent → emit a **WARNING** (advisory, not blocking):
"This feature appears to touch a contract/route/security surface (matched: `<pattern>`); declare
`integration_test: {path: ...}` or justify its absence." Heuristic → soft on purpose (C4 overlap).

**5.3 Pre-completion Check 10** (`controller-checkpoint.py`, sibling to Check 8/9 in `run_pre_completion`)
If `integration_test` declared (aggregated across plan files):
- (a) `path` **exists on disk**, AND
- (b) `path` is **part of this feature's changeset vs the default branch** — proving a *new* test was
  written for this feature, not a pre-existing file pointed at.
- Pass → `checks["integration_test_present"] = PASS`. Fail either condition → FAIL + append blocker
  `integration_test_missing`.
- **Git mechanism — must be written new; it does NOT exist today.** Reuse *only* `_resolve_git_root`
  (`controller-checkpoint.py` ~L518) for the repo root. `_check_verification_git_reality` performs a
  *timestamp-window* `git log --after/--before` keyed on dispatch-log entries — it is **not** a
  base-relative diff and is **not** reusable for (b). Implement (b) as:
  - diff base = `git merge-base <default-branch> HEAD` (resolve the default branch from the repo, e.g. `main`);
  - compare `<base>` against the **working tree** — `git diff --name-only <base> -- <path>` — **not**
    `<base>..HEAD`: at pre-completion the new integration test may be **uncommitted**, so a commit-only
    diff would miss it and fail (b) even though the test was written.
  - There is **no manifest-recorded base** — the `SddSession` / `ArtifactPaths` / `Enforcement` models
    carry no base/branch field. Derive the base via merge-base; do **not** invent a manifest field.
- No declaration → PASS with "no integration_test declared — check skipped" (mirrors Check 9's empty case).

**5.4 Fixtures** (the required C2 deliverable)
1. Route-touching plan, **no** `integration_test` → `validate-plan.py` emits the WARNING.
2. `integration_test.path` declared but file **missing / not in diff** → Check 10 FAILs.
3. Declared path **exists + in diff** → Check 10 PASSes.
Fixtures (2)/(3) model the practerus cache-poisoning miss: a route feature is forced to ship a test.

**5.5 Docs** (`writing-plans/SKILL.md`): a "Declaring an integration test" subsection — when to declare
`integration_test`, what Check 10 verifies. (Not SDD SKILL.md — word ceiling, D8.)

## 6. Cross-Cutting

- **Module boundary = the live test**: Module 1 completes → `transition-module.py` archives Module-1
  reports, truncates the dispatch log, recomputes `context_summary_at` → Module 2. First live exercise
  of the merged N3/N4/N10/N11 path.
- **Pattern References** (plan header): `implementer_report.py`, `plan.py`,
  `controller-checkpoint.py` (Check 8/9 + helpers), `validate-plan.py` (regex + WARNING patterns),
  `transition-module.py` (`validate_module_completion`), `sdd-pre-dispatch-hook.sh`. Injected into
  every implementer so they edit against current code, not assumptions.
- **Testing**:
  - **pytest units** per item (Module 1) + model/validate-plan/checkpoint tests (C2).
  - **Integration**: extend `tests/integration/sdd-e2e-test.sh` with a C2 Check-10 step (declared
    path present/absent).
  - **Regression**: `tests/ARaymond-skill-regression/validate-all-skills.py` stays green (writing-plans
    SKILL.md edit must not breach word thresholds).
  - **Install**: `tests/ARaymond-installation/verify-symlink-install.sh`.
  - **Hook baseline**: `tests/ARaymond-hook-baseline/check-hooks.sh --capture` after N1; commit
    `baseline.txt` in the same change.
- **Documentation maintenance** (per repo CLAUDE.md): after merge, update CLAUDE.md (new Check 10,
  N1 hook behavior, test counts), the customization manifest, and BACKLOG.md (flip N16/N5/N7/N1/N12/
  N13/N17/N9 + C2 to `done`).

## 7. Acceptance Criteria

- [ ] N16: a `task_type:verification` implementer report with empty `files_changed` validates; an
      `implementation` report with empty `files_changed` + status DONE still FAILs.
- [ ] N5: `### Task N` headers inside fenced blocks are not counted by either regex (both sites).
- [ ] N7: `Source Contracts: None` → pre-execution PASS.
- [ ] N9: `_task_ids_where` is the single parser; both ratio paths behavior-unchanged.
- [ ] N12: transition provenance gate keys on `enforcement.dispatch_provenance`.
- [ ] N17: transition reads verification ids from main plan when `module.file` empty.
- [ ] N1: a dispatch missing multiple prereqs lists all of them in one BLOCKED message; hook baseline
      re-captured + committed.
- [ ] N13: the 2026-06-01 plan.md Task-4 snippet runs as written.
- [ ] C2: Plan model accepts `integration_test`; validate-plan WARNs on risk-surface + no declaration;
      Check 10 FAILs on missing/not-in-diff path and PASSes on present-in-diff; 3 fixtures exist.
- [ ] The 2-module feature completes through `transition-module.py` with **no manual manifest advances**.
- [ ] Full static + integration suites green; `validate-all-skills.py` PASS-with-≤current-warnings.

## 8. Deferred Follow-ups (logged, out of scope)

- **Track 3 — verification-task half**: after N16 merges, a small post-merge run with a *non-last*
  `task_type:verification` task crossing a module boundary, to exercise the live verification path.
- **N6, N8**: standalone-opportunistic, fold into a future edit of the relevant file.
- **C4** (computed risk heuristics), **C3** (gameable gates → hooks), **C1** (plan-ref execution),
  **C5** (cross-artifact validation): sprint-4 design spikes.
