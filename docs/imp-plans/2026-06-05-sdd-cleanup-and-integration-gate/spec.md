# SDD Cleanup + Integration-Test Gate — Design Spec

> **Feature dir**: `docs/imp-plans/2026-06-05-sdd-cleanup-and-integration-gate/`
> **Created**: 2026-06-05 · **Revised**: 2026-06-06 (Codex review, bundle `2026-06-06T21-45-51Z-superpowers` → findings `2026-06-06T23-46-31Z-superpowers`)
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
  integration test in its own changeset. Closes the practerus M15 cache-poisoning class (a real
  security bug that passed every unit test + structural validator because no integration test
  exercised the cross-module path — `docs/process-improvement-findings/2026-05-21-skill-evaluation.md` §2.2, §9.8 quote 1).

Module 1 must fully complete and transition (via `transition-module.py`) before Module 2 begins.

## 2. Goals / Non-Goals

**Goals**
- Every Module-1 item fixed with a failing-test-first treatment for the true bug-fixes (N16, N5, N7)
  and behavior-preserving tests for the refactors (N9, N12, N17). N1 is a **test-only regression item**
  (see §4 — the hook already accumulates).
- C2 ships: a Plan-model declaration field, a plan-time risk-surface WARNING, a pre-completion Check 10
  (changeset existence, tracked-or-untracked, parent+modules aware), and fixtures proving a missing
  integration path is caught.
- The 2-module execution validates the live multi-module transition path.

**Non-Goals (explicitly deferred)**
- The **non-last `verification` task** half of Track 3 — requires N16 on main first (the live hook runs
  main's `validate-report.py`), so it is a small **post-merge** run, logged as a follow-up.
- C4 computed risk heuristics beyond the single advisory WARNING.
- Making the pre-completion gate itself hook-enforced (C3, separately tracked).
- Forgery-proofing the gate (controller-written evidence files are a known class — C3/C5).
- N6 (SKILL.md framing pass) and N8 (F6 regression-check rewrite) — left standalone-opportunistic.

## 3. Decision Log

| # | Decision | Chosen | Notes |
|---|----------|--------|-------|
| D1 | Packaging | One combined 2-module feature | Module 1 cleanup → transition → Module 2 C2; the run exercises the merged transition machinery live. |
| D2 | Module 1 scope | Core 7 (N16,N5,N7,N1,N12,N13,N17) + N9 | N9 helper reused by C2. N6/N8 opportunistic. |
| D3 | C2 gate strength | Declaration + changeset-existence gate + plan-time risk WARNING | vs. WARNING-only (doesn't close the gap); vs. run-evidence (M→L, over-engineers "did it pass"). |
| D4 | N16 fix shape | Add `task_type` to `ImplementerReport`, exempt `verification` | Non-breaking, no schema bump. **Must also update report template + verification prompt** (D11). |
| D5 | N7 fix shape | Read frontmatter `source_contracts`; None/empty → valid-absent → PASS | Uses the structured field. |
| D6 | N12 fix shape | Gate **only** `_has_dispatch_provenance()` on `enforcement.dispatch_provenance` | Keep self-review file-existence under process review modes (D13). |
| D7 | N13 handling | Fold into the N5 task as a trailing doc chore | 1-line doc edit; no own task. |
| D8 | C2 docs location | `writing-plans/SKILL.md` | SDD SKILL.md at 5029-word ceiling. |
| D9 | Task 0 / contracts | `Source Contracts: None`; Pattern References, no Task 0 | No external contract. **This run's pre-execution still FAILs on `Source Contracts: None`** (main's pre-fix gate — see §6 self-hosting hazards) → pre-log an accepted deviation in Module 1; N7 clears it only post-merge. |
| D10 | Workspace | Worktree (**required** — D16) | Feature edits the very scripts that gate it. |

**Review revisions (Codex findings, verified against code 2026-06-06):**

| # | Finding → Decision | Detail |
|---|--------------------|--------|
| D11 | **N16 must update all consumers** (Major 4, verified `implementer-prompt.md:193-206` lacks `task_type`; SKILL.md verification guidance doesn't emit it) | Model field + exempt verification is **insufficient** — model defaults to `implementation`, so a verification report without `task_type:verification` still fails. Also: add `task_type` to the implementer-report frontmatter template, instruct verification subagents to set `task_type: verification`, and add a `validate-report.py` fixture for a real markdown verification report with `files_changed: []`. |
| D12 | **N5 covers ALL task-header consumers** (Major 2, verified 7 sites) | Not just `TASK_HEADER_RE` (validate-plan.py:48) + `TASK_HEADER_PATTERN` (controller-checkpoint.py:58). Also the inline regexes at validate-plan.py:160 (`analyse_tasks`), :264 (Task 0); controller-checkpoint.py:429 (`has_task_zero`), :474/:486 (checkbox range). Route each script's task-header parsing through ONE fence-aware helper (per-script; not necessarily shared). |
| D13 | **N12 splits file-existence from provenance** (Major 3, verified transition-module.py:122-130 wraps both) | Gate ONLY the `_has_dispatch_provenance()` call on `enforcement.dispatch_provenance`. Keep spec/quality review **file-existence** under `process_requirements.{spec,quality}_review_mode != "skip"` (micro tier is self_review, so self-review artifacts are still required). |
| D14 | **N1 re-scoped to test-only** (Major 5, verified the hook ALREADY accumulates) | `sdd-pre-dispatch-hook.sh:320` inits `ERRORS=()`; all enforcement checks append; :702-709 emits all together then `exit 2`. The "reports only the first" premise is false for the enforcement block. The only true early-exits are the manifest guard (:130) and range guard (:207) — legitimate preconditions that must NOT accumulate. → N1 becomes a **regression test** locking in multi-error accumulation. **No hook control-flow change → no hook-baseline recapture, and NO item edits the hook at all.** |
| D15 | **C2 changeset = added-or-modified, tracked-or-untracked** (Blocker 1 + Major 1) | `git diff --name-only <base> -- <path>` does NOT list untracked files — a brand-new test that exists on disk but was never `git add`ed would fail. Changeset membership = tracked-diff `OR` untracked: `git diff --name-only <base> -- <path>` ∪ `git ls-files --others --exclude-standard -- <path>`. Contract wording: the declared test must be **part of this feature's changeset (added or modified)** — drop the "proves a NEW test" claim; modifying an existing integration test is explicitly acceptable. |
| D16 | **Parent+modules plan aggregation** (Blocker 2, verified `_load_manifest_config:591-600` overwrites `plan_file` with the active module; `run_pre_completion:1046-1067` scans active-module + `modules[]` but never the parent) | Add a de-duped helper `_load_all_plan_contents(manifest)` → parent `manifest.plan_file` + every module file. Use it for C2 Check 10 AND retrofit the existing declared-minimum / verification-id / task-count / report-matching scans (hardens the same latent gap). Fold into N9. |
| D17 | **Worktree is a hard requirement; name which copy enforces what** (Major 6) | C2's new Check 10 lives in the **worktree** copy of `controller-checkpoint.py`; the live SDD gates during this run resolve to **main** (symlink). So C2 is validated by **worktree unit + e2e ONLY**; the live main pre-completion gate does NOT enforce C2 until after merge. Before execution, verify `~/.claude/skills/superpowers` still symlinks to main. |
| D18 | **Minors folded in** | (m1) default-branch resolver order `origin/HEAD` → `main` → `master`, clear infra error if none; define on-default-branch behavior (`merge-base == HEAD`). (m2) multiple `integration_test` declarations across parent+modules → collect, de-dupe, require ALL to pass. (m3) `IntegrationTest.path` pydantic validator: repo-root-relative, non-absolute, no `..`; Check 10 uses `Path.is_file()` (not bare `exists`). |

## 4. Module 1 — Cleanup Bundle

All paths repo-root-relative. Each task lists its source file(s) as a Pattern Reference (required read).

| Item | File(s) | Fix | Test obligation |
|---|---|---|---|
| **N16** | `skills/scripts/models/implementer_report.py` **+** `skills/subagent-driven-development/implementer-prompt.md` (frontmatter template ~L193-206) **+** `skills/subagent-driven-development/SKILL.md` (verification guidance ~L355-362) | Add `task_type: Literal["implementation","verification"]="implementation"`; exempt `verification` from `files_changed_non_empty_for_done` (L48-53). Add `task_type` to the report frontmatter template; instruct verification subagents to set `task_type: verification`. (D11) | RED: real markdown verification report (`task_type: verification`, `files_changed: []`, status DONE) currently fails `validate-report.py` → after fix, validates. `implementation` report w/ empty `files_changed` still FAILs. |
| **N5** | `validate-plan.py` (L48 `TASK_HEADER_RE`, L160 `analyse_tasks`, L264 Task 0) + `controller-checkpoint.py` (L58 `TASK_HEADER_PATTERN`, L429 `has_task_zero`, L474/L486 checkbox range) | Route **all** task-header parsing in each script through ONE fence-aware helper that skips `### Task N` inside ```` ``` ```` fenced blocks. (D12) | RED: a plan with `### Task 91` in a fenced fixture currently inflates validate-plan task count/spans + Task-0 detection AND checkpoint `all_tasks_have_reports` / checkbox ranges / verification ratio → after fix, ignored at every site. |
| **N7** | `controller-checkpoint.py` (pre-execution `source_contracts` check, L444-465 + L690-694) | Read the frontmatter `source_contracts` field; treat `None`/empty/"None" as **valid-absent → PASS**. | RED: `Source Contracts: None` currently FAILs pre-execution → after fix, PASS. |
| **N9** | `controller-checkpoint.py` | (a) Extract `_task_ids_where(plan_contents, field, value) -> (set, parsed_any)` (collapses `_declared_minimum_task_ids` + `_verification_task_ids`). (b) Add `_load_all_plan_contents(manifest)` → parent plan + every module file (de-duped); route declared-min / verification-id / counts / report-matching / C2 through it (D16). | Behavior-preserving for existing ratio paths (tests still pass) + new test: parent-only declaration is now seen; helper de-dupes. **Do before C2.** |
| **N12** | `transition-module.py` (`validate_module_completion`, L122-130) | Split file-existence from provenance: keep spec/quality **file** checks under `pr.{spec,quality}_review_mode != "skip"`; gate the **`_has_dispatch_provenance()`** call on `enforcement.dispatch_provenance`. (D13) | Test: micro+modules (self_review modes, dispatch_provenance=False) with self-review files + no dispatch log → PASS; same manifest missing self-review files → still FAIL. |
| **N17** | `transition-module.py:validate_module_completion` (~L110) | Main-plan fallback for verification-id lookup when `module.file` empty (mirror hook `sdd-pre-dispatch-hook.sh:297-298`). | Test: manifest w/ empty `module.file` reads verification ids from `MANIFEST_PLAN_FILE`. |
| **N1** | `tests/` only (**no hook edit** — D14) | The enforcement block already accumulates (`ERRORS=()` :320 → emit-all :702-709). Add a regression test asserting a dispatch missing **multiple** prereqs lists all of them in one BLOCKED message. Leave the manifest-guard (:130) and range-guard (:207) early-exits as-is (legitimate preconditions). | New regression test (the accumulation invariant). No RED-against-current-behavior (it already passes) — this locks it against future refactors. |
| **N13** | `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/plan.md` | Backport 2 `mkdir()` lines into the Task-4 verbatim snippet. Folded into the N5 task. | None (doc-only). |

**Module-1 internal ordering**: N9 (helpers — incl. `_load_all_plan_contents`) and N5 (fence-aware headers) land before C2 consumes them; N12/N17 (transition) independent; N1 (test-only) and N13 (doc) any time.

## 5. Module 2 — C2 Integration-Test Gate

**5.1 Plan model** (`skills/scripts/models/plan.py`)
```python
class IntegrationTest(StrictModel):
    path: str   # repo-root-relative; validated non-absolute, no "..", relative (D18/m3)

class Plan(SchemaVersionedModel):
    ...
    integration_test: IntegrationTest | None = None   # presence == required
```
Optional, default `None`, **no schema bump**. Path validator rejects absolute paths and `..` segments.

**5.2 Plan-time WARNING** (`validate-plan.py`)
Scan File Map / write-scope paths for risk-surface patterns (`router`, `routes/`, `middleware`, `auth`,
`migration`, `cache`, `cors`, `security`). If matched **and** `integration_test` absent → **WARNING**
(advisory, not blocking).

**5.3 Pre-completion Check 10** (`controller-checkpoint.py`, sibling to Check 8/9 in `run_pre_completion`)
Aggregate declarations across parent + module plans via `_load_all_plan_contents` (D16). For each
declared `integration_test.path` (de-duped across parent+modules — D18/m2), verify:
- (a) `path` resolves to a real file: `Path(<git_root>/<path>).is_file()` (D18/m3), AND
- (b) `path` is **in this feature's changeset** (added or modified — D15): membership =
  `git diff --name-only <base> -- <path>` **∪** `git ls-files --others --exclude-standard -- <path>`
  (tracked-diff OR untracked; the union catches a never-`git add`ed new test).
- ALL declared paths must pass → `checks["integration_test_present"]=PASS`; any fail → FAIL + blocker
  `integration_test_present`. No declaration → PASS (skipped, mirrors Check 9 empty case).
  (As-built: blocker unified to the check key — CheckpointResult's `blockers_reference_check_names`
  validator requires blockers ∈ checks keys; deviations.md Task 10 row. As-built also FAILs on
  present-but-malformed declarations — flat string / empty path — closing a silent fail-open found
  by the final review; commit 911f025.)

**Git mechanism (NEW code — does not exist today).** Reuse ONLY `_resolve_git_root`
(`controller-checkpoint.py` ~L517). `_check_verification_git_reality` is a timestamp-window `git log`,
**not** a base diff — not reusable for (b). Diff base resolver (D18/m1): `origin/HEAD` → local `main` →
`master`; if none, FAIL with an infrastructure error (exit 2-class). On the default branch
(`merge-base == HEAD`), committed diff is empty — rely on the untracked + working-tree set; document
this edge. Compare against the **working tree** (not `<base>..HEAD`).

**Contract honesty (D15/M1):** the gate proves the declared test is *part of this feature's changeset*,
NOT that it is brand-new — modifying an existing integration test is acceptable and passes.

**5.4 Fixtures** (the required C2 deliverable)
1. Route-touching plan, **no** `integration_test` → `validate-plan.py` emits the WARNING.
2. Declared path **does not exist** → Check 10 FAILs.
3. Declared path exists but **not in changeset** (pre-existing, unchanged) → Check 10 FAILs.
4. Declared path exists as an **untracked new file** (never `git add`ed) → Check 10 **PASSes** (B1 regression).
5. Declared path exists as a **modified tracked file** → Check 10 PASSes.
6. **Modular plan** where only the **parent** declares `integration_test` → Check 10 sees it (B2 regression).
Fixtures 2-6 model the practerus cache-poisoning miss + the two Blocker classes.

**5.5 Docs** (`writing-plans/SKILL.md`): "Declaring an integration test" subsection — when to declare,
what Check 10 verifies, and that it accepts added-or-modified (not strictly new). (Not SDD SKILL.md — D8.)

## 6. Cross-Cutting

- **No item edits a baselined hook** (post-D14): N1 is test-only; nothing touches `sdd-pre-dispatch-hook.sh`
  or any of the 7 baselined hooks. **No `check-hooks.sh --capture` needed.** (The scripts edited —
  `controller-checkpoint.py`, `validate-plan.py`, `transition-module.py`, the models — are *called by*
  hooks but are not themselves baselined hook scripts.)
- **Which copy enforces what (D17):** the live SDD gates during this run resolve to **main** (symlink),
  so they run main's pre-fix scripts — stable enforcement throughout, but they do NOT exercise this
  feature's own new code. C2's Check 10, N5's fence fixes, N7/N9 all live in the **worktree** copy and
  are validated by **worktree unit + e2e ONLY**; the live main gate does not enforce C2 until after
  merge. Before execution, confirm `~/.claude/skills/superpowers` → main. **Worktree is required**
  (the feature self-modifies its gate scripts).
- **What the run proves:** a genuine first live exercise of the *already-merged* N3/N4/N10/N11
  `transition-module.py` machinery — NOT this feature's new code (unit+e2e carry that burden until merge).
- **Self-hosting hazards (the feature fixes bugs that are still live in main during its own run):**
  (1) **N5** — main's `validate-plan.py` is still fence-blind, so plan.md / module plan files must NOT
  contain fenced ```` ``` ````-wrapped `### Task N` examples; the live plan-validation-gate would
  miscount them and could FAIL before SDD starts. (2) **N7** — main's pre-execution gate still FAILs on
  `Source Contracts: None`; pre-register an accepted deviation in Module 1 (per CLAUDE.md Hook Dev
  Gotchas). Both clear only post-merge.
- **Module boundary = the live test**: Module 1 completes → `transition-module.py` archives Module-1
  reports, truncates dispatch log, recomputes `context_summary_at` → Module 2.
- **Pattern References** (plan header): `implementer_report.py`, `implementer-prompt.md`, `plan.py`,
  `controller-checkpoint.py` (Check 8/9 + helpers + `_load_manifest_config`/`run_pre_completion`),
  `validate-plan.py` (all task-header sites), `transition-module.py` (`validate_module_completion`).
- **Testing**: pytest units per item; extend `tests/integration/sdd-e2e-test.sh` with a C2 Check-10 step
  (untracked + parent-only cases); keep `validate-all-skills.py` + `verify-symlink-install.sh` green.
- **Documentation maintenance** (per repo CLAUDE.md): after merge, update CLAUDE.md (Check 10, N5 scope,
  test counts), the customization manifest, and BACKLOG.md (flip N16/N5/N7/N1/N12/N13/N17/N9 + C2 to
  `done`; annotate N1's re-scope and N5's expanded consumer set).

## 7. Acceptance Criteria

- [ ] N16: a real-markdown `task_type:verification` report with empty `files_changed` validates; an
      `implementation` report with empty `files_changed` + DONE still FAILs; report template + verification
      prompt emit `task_type`.
- [ ] N5: fenced `### Task N` headers are ignored at **all** task-header sites (validate-plan count/spans/Task-0;
      checkpoint has_task_zero/checkbox-range/verification-ratio).
- [ ] N7: `Source Contracts: None` → pre-execution PASS.
- [ ] N9: `_task_ids_where` is the single ID parser; `_load_all_plan_contents` is the single plan loader;
      parent-only declarations are visible; existing ratio paths behavior-unchanged.
- [ ] N12: micro+modules with self-review files but no dispatch log PASSes transition; missing self-review files FAILs.
- [ ] N17: transition reads verification ids from main plan when `module.file` empty.
- [ ] N1: regression test asserts multi-error accumulation; no hook control-flow change; baseline untouched.
- [ ] N13: the 2026-06-01 plan.md Task-4 snippet runs as written.
- [ ] C2: model accepts `integration_test` (+ path validator); validate-plan WARNs on risk-surface + no
      declaration; Check 10 FAILs on missing/not-in-changeset, PASSes on untracked-new and modified-tracked,
      and sees parent-only declarations; ≥6 fixtures exist.
- [ ] The 2-module feature completes through `transition-module.py` with **no manual manifest advances**.
- [ ] Full static + integration suites green (worktree copy); `validate-all-skills.py` PASS-with-≤current-warnings.

## 8. Deferred Follow-ups (logged, out of scope)

- **Track 3 — verification-task half**: after N16 merges, a small post-merge run with a *non-last*
  `task_type:verification` task crossing a module boundary, to exercise the live verification path.
- **N6, N8**: standalone-opportunistic.
- **C4** (computed risk heuristics), **C3** (gameable gates → hooks), **C1** (plan-ref execution),
  **C5** (cross-artifact validation): sprint-4 design spikes.
