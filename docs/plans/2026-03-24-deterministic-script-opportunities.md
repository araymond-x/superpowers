# Deterministic Script Opportunities — Superpowers Skills

**Date:** 2026-03-24
**Scope:** All 15 skills under `skills/`. Research only — no files modified.
**Purpose:** Identify where deterministic scripts would improve input/output integrity across the pipeline.

---

## Existing Coverage Summary

Before cataloguing gaps, here is what the existing scripts already cover:

| Script | Skill | What It Checks |
|--------|-------|----------------|
| `check-handoff.sh` | handoff-acceptance | Contract Constraints section in first 50 lines of handoff README |
| `check-distillation.sh` | brainstorming | Exploration artifacts (Options Considered, rationale, we considered) in distilled spec |
| `validate-plan.py` | writing-plans | Plan size (<800 lines), task size (<200 lines/task), required header sections (Source Contracts, Contract Constraints, Feature Archetype, Code Footprint, Write-Scope Partitioning), Task 0 presence when Source Contracts exist, checkbox syntax |
| `estimate-task-tokens.py` | subagent-driven-development | Pre-dispatch context budget for a single task (OK / WARNING / TOO_LARGE) |
| `validate-report.py` | subagent-driven-development | Implementer report completeness (9 required sections present) |
| `controller-checkpoint.py` | subagent-driven-development | 3-phase controller health: pre-execution (plan readable, DEVIATIONS.md exists, reports/ exists, Task 0 ordering), pre-dispatch (previous task checkboxes complete, previous report exists and is complete, no pending deviations, context load), pre-completion (all checkboxes checked, no pending deviations, all tasks have reports, all reports complete) |
| `context-summary.py` | subagent-driven-development | Compresses N report files into one summary file when context load is high |
| `extract-execution-trace.py` | subagent-driven-development | Post-session anomaly detection from .jsonl session files (skipped reviews, unlogged concerns, missing reports) |

---

## Skill-by-Skill Analysis

---

## brainstorming

### Current Coverage
- `check-distillation.sh` — Exploration artifact detection in distilled spec (grep for Options Considered, rationale, etc.)

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 1 | Distilled spec size vs. original spec size | Post-condition | `original-spec.md`, `distilled-spec.md` | PASS (distilled < 40% of original) / FAIL (too large) / WARNING (borderline) | HIGH | The SKILL.md mandates <40% of original line count. This is measurable in 3 lines of wc. Without the check, distillation drift (verbosity creeping back in) goes undetected. |
| 2 | Required distilled spec sections present | Post-condition | `distilled-spec.md` | PASS / FAIL with missing sections | HIGH | SKILL.md defines a mandatory template with `Contract Facts`, `Open Decisions`, `Decision Summary`, `Component Specifications`, `Acceptance Criteria`. The LLM reviewer can miss structural gaps; a grep-based check cannot. |
| 3 | Contract Facts section at top (within first N lines) | Post-condition | `distilled-spec.md` | PASS / FAIL | MEDIUM | The whole point of distillation is contract facts first. Without verifying position, the section may exist but be buried — the same failure mode that triggered `check-handoff.sh`. |
| 4 | Open Decisions table not silently empty | Post-condition | `distilled-spec.md`, `original-spec.md` | PASS / WARNING (open decisions detected in original but table empty in distilled) | MEDIUM | Ambiguous items in the original spec that were flagged as "OPEN DECISION" must appear in the distilled table. If the distiller skips them, downstream plan writers miss them entirely. |
| 5 | Spec file naming convention matches date and slug | Post-condition | `docs/specs/` directory | PASS / FAIL | LOW | SKILL.md specifies `docs/specs/YYYY-MM-DD-<topic>-design.md` and `YYYY-MM-DD-<topic>-design-distilled.md`. A naming check ensures the plan writer receives the right file and the distillation reviewer is dispatched on the paired doc. |

### Recommended Scripts
- `check-distilled-spec.py` — Combines checks 1-4 into a single post-distillation validator. Takes `--original-spec` and `--distilled-spec`. Checks size ratio, required sections, Contract Facts position, and Open Decisions coverage. Replaces the cruder `check-distillation.sh` (which only does artifact detection) with a complete structural validator.

---

## writing-plans

### Current Coverage
- `validate-plan.py` — Structural validation: size, section presence, Task 0 rules, checkbox syntax.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 6 | Write-Scope Partitioning table: no file appears in multiple Owned Files columns | Post-condition | Plan file | PASS / FAIL with list of conflicting files | HIGH | The SKILL.md states "No two parallel tasks may write to the same file" and "each file appears in exactly one task's Owned Files column." `validate-plan.py` checks the section exists but does not parse the table rows. Two tasks owning the same file is the specific failure mode this table was designed to prevent — it must be verified mechanically, not just by LLM reviewer. |
| 7 | Obsolescence Verification Task present for Replacement/Refactor/Migration archetypes | Post-condition | Plan file | PASS / FAIL / SKIP (if Greenfield/Extension) | HIGH | The SKILL.md mandates this task for those three archetypes. `validate-plan.py` checks Feature Archetype presence and task structure but does not cross-check archetype value against obsolescence task existence. This is a deterministic archetype-conditional check. |
| 8 | Task 0 has required 6 steps | Post-condition | Plan file | PASS / WARNING | MEDIUM | The SKILL.md references a Task 0 template with 6 specific steps. `validate-plan.py` checks Task 0 exists and is first, but not whether it has meaningful content. A minimal size check (>N lines) or step-count check prevents empty "Task 0" stubs that pass structural validation but cannot perform contract verification. |
| 9 | Module decomposition: parent plan has required 4 sections | Post-condition | Parent plan file | PASS / FAIL | MEDIUM | SKILL.md specifies parent plans must include: module inventory, module dependency graph, parallel execution annotations, shared contract section. `validate-plan.py` detects Module headers but does not verify the parent plan's required sections. |
| 10 | Plan file naming convention | Post-condition | `docs/imp-plans/` | PASS / FAIL | LOW | SKILL.md specifies `docs/imp-plans/YYYY-MM-DD-<feature-name>.md`. Naming mismatches cause the controller to reference wrong files and break the handoff from writing-plans to subagent-driven-development. |
| 11 | Source Contracts reference exists on disk (when not "None") | Pre-condition | Plan file | PASS / FAIL with missing file paths | MEDIUM | If Source Contracts lists file paths, verify they exist before handing off to subagent-driven-development. A non-existent source contract file causes Task 0 to fail with a confusing error rather than a clear plan-authoring error. |

### Recommended Scripts
- Extend `validate-plan.py` with two new checks:
  - Write-scope disjointness: parse the Write-Scope Partitioning table and detect files listed in multiple Owned Files cells (check #6).
  - Archetype-to-task cross-check: if Feature Archetype is Replacement/Refactor/Migration, verify a task named "Obsolescence" or containing obsolescence-related language exists (check #7).
- `check-source-contract-files.py` — Standalone pre-handoff check that extracts file paths from the Source Contracts section and verifies each exists on disk (check #11). Produces PASS/FAIL per file.

---

## handoff-acceptance

### Current Coverage
- `check-handoff.sh` — Contract Constraints section presence in first 50 lines.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 12 | Acceptance report file exists and has required verdict | Post-condition | Project docs directory | PASS / FAIL (report missing) / FAIL (verdict REJECTED) / PASS (ACCEPTED or ACCEPTED_WITH_REMEDIATION) | HIGH | brainstorming and writing-plans both say "verify it passed handoff-acceptance" before consuming a handoff. Without a mechanical check, this gate is advisory — the controller may skip it. A script that finds and reads the acceptance report, extracts the Verdict field, and returns PASS/FAIL/REMEDIATION creates a real gate. |
| 13 | Fixture files exist in expected directories | Post-condition | Handoff package directory | PASS (fixtures found) / FAIL (no fixtures) | HIGH | Acceptance check #3 (Acceptance Fixtures) is BLOCKING per the skill, but `check-handoff.sh` only checks the contract section header. The fixture check requires directory presence, not header text — a different mechanical check. |
| 14 | Code snippets labeled as pseudocode when missing imports | Post-condition | Handoff README.md | PASS / WARNING per snippet | MEDIUM | A script that finds code blocks without import statements and verifies they carry a `# pseudocode` or `# illustrative` marker would mechanically check acceptance criterion #2 (Executable Code Snippets). This is not perfect (some languages don't need imports) but catches the most common pattern that generated the original incident. |
| 15 | Remediation items fully resolved before plan authoring | Pre-condition | Acceptance report for an ACCEPTED_WITH_REMEDIATION verdict | PASS (remediation complete) / FAIL (items still open) | MEDIUM | When verdict is ACCEPTED_WITH_REMEDIATION, the skill says "The downstream agent can proceed but must extract and consolidate the information as a prerequisite." A check that scans the remediation table in the report and verifies all rows have been addressed prevents the "proceed anyway" failure mode. |

### Recommended Scripts
- `check-acceptance-report.py` — Reads the acceptance report in the project docs directory. Verifies the report exists, extracts the Verdict field (ACCEPTED / ACCEPTED_WITH_REMEDIATION / REJECTED), checks fixture directory existence, and returns structured PASS/FAIL/REMEDIATION output with the extracted Contract Facts block. This would replace the bare call to `check-handoff.sh` as the primary handoff gate.

---

## subagent-driven-development

### Current Coverage
- `validate-report.py` — Implementer report section completeness (9 sections).
- `estimate-task-tokens.py` — Pre-dispatch context budget.
- `controller-checkpoint.py` — 3-phase controller discipline (pre-execution, pre-dispatch, pre-completion).
- `context-summary.py` — Context compression after many tasks.
- `extract-execution-trace.py` — Post-session anomaly detection.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 16 | Spec reviewer report file exists for each completed task | Pre-condition (pre-dispatch N+1) | `reports/` directory, task number | PASS / FAIL | HIGH | `controller-checkpoint.py pre-dispatch` checks for the implementer report but not the spec reviewer report or quality reviewer report. Both are required by the skill ("Mark task complete ONLY THEN"). A task with an implementer report but no spec-review file has not completed the review loop — this is the exact failure mode that produced 3 production bugs in the incident referenced in the skill. |
| 17 | Quality reviewer report file exists for each completed task | Pre-condition (pre-dispatch N+1) | `reports/` directory, task number | PASS / FAIL / SKIP (minimum review tier) | HIGH | Same rationale as #16 but for the quality review. The skill defines `task-N-spec-review.md` and `task-N-quality-review.md` as the expected file names. Neither file is currently checked by `controller-checkpoint.py`. |
| 18 | DEVIATIONS.md has correct header template | Pre-condition (pre-execution) | DEVIATIONS.md | PASS / FAIL | MEDIUM | The skill specifies an exact DEVIATIONS.md header template with four required columns (Task, Type, Description, Disposition) and three subsections (Deferred Work, Independent Decisions, Scope Changes). If the controller created DEVIATIONS.md with a wrong structure, later tools that grep for "Pending" will give incorrect results. |
| 19 | Cross-task wiring: exported names match import sites | Pre-condition (pre-completion) | Source files, plan's Code Footprint table | PASS / WARNING per pair | MEDIUM | The pre-completion gate step 7 ("Cross-task wiring audit") requires verifying every component created by one task is imported by consumers. This is currently a prose instruction. A script that extracts the Code Footprint table's new-file rows, identifies their exports, and greps for those names in expected consumer files would mechanically check this. Even a simple "does this export exist in the consuming file" check catches the missing-wire failure mode. |
| 20 | Review tier declaration present in each task dispatch record | Post-condition (per-task) | `reports/task-N-spec-review.md` | PASS / WARNING | LOW | The skill requires the controller to "declare the review tier before dispatching each task." The spec-review report should include the declared tier. A structural check on review report files could verify the tier was recorded, making the declaration verifiable rather than advisory. |

### Recommended Scripts
- Extend `controller-checkpoint.py pre-dispatch` to check for `task-N-spec-review.md` and `task-N-quality-review.md` in `reports/` (checks #16, #17). Add `--minimum-review-tier` flag to allow the quality review check to be suppressed when the controller declared minimum tier.
- `check-deviations-structure.py` — Validates DEVIATIONS.md has the required header template and table columns. Run at pre-execution phase alongside DEVIATIONS.md creation (check #18).
- `check-wiring.py` — Reads the Code Footprint table from a plan file, extracts new-file/function names, and greps each against its declared consumer files. Reports PASS/WARNING per pair (check #19).

---

## finishing-a-development-branch

### Current Coverage
- None. This skill has no scripts.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 21 | Branch divergence check: uncommitted changes present | Pre-condition (before offering options) | Git state | PASS / WARNING (uncommitted changes exist) | HIGH | The skill's Step 1 runs the test suite but does not verify the working tree is clean before offering merge/PR options. A dirty worktree (uncommitted modifications) means the tests passed against different code than what will be merged. A `git status --short` check that FAILs if untracked or modified files exist prevents this. |
| 22 | Merge result test pass (post-merge verification) | Post-condition (Option 1 only) | Git state after merge | PASS / FAIL | HIGH | The skill prescribes running tests after merging (Option 1, "Verify tests on merged result"). This step is in the skill prose but there is no script to enforce it. A post-merge test runner with a mandatory PASS gate (not just "run tests") prevents merge-and-forget. |
| 23 | PR body completeness: Summary and Test Plan sections present | Post-condition (Option 2 only) | PR body text or gh pr view | PASS / FAIL | MEDIUM | The skill provides a PR body template with Summary and Test Plan sections. Without a structural check on the generated PR, the sections may be empty or missing. A `gh pr view --json body` pipe to a grep check ensures both sections exist with non-empty content. |
| 24 | Worktree cleanup verification | Post-condition (Options 1, 4) | Git worktree list | PASS / FAIL | LOW | After Option 1 or 4, the skill removes the worktree. A `git worktree list` check confirms the worktree was actually removed — relevant because `git worktree remove` can silently fail if there are modified files, leaving orphaned worktrees. |

### Recommended Scripts
- `check-branch-ready.sh` — Pre-merge gate: checks for uncommitted changes (`git status --short`), verifies the test suite exits 0, and checks that the branch has at least one commit since its divergence from base. Single script run before presenting the 4-option menu.
- `check-pr-body.sh` — Post-PR-creation: takes the PR number, calls `gh pr view N --json body`, and verifies Summary and Test Plan sections are present and non-empty.

---

## executing-plans

### Current Coverage
- None specific to this skill. It inherits `validate-plan.py` indirectly (plan should have been validated before being handed to this skill).

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 25 | Plan has been validated by `validate-plan.py` (validation artifact present) | Pre-condition | Plan file or a `.validated` marker file | PASS / WARNING (not validated) | MEDIUM | `executing-plans` Step 1 says "Read plan file, review critically." If the plan came from outside the writing-plans skill (e.g., a human wrote it), it may not have been run through `validate-plan.py`. A simple check that either runs the validator or checks for a validation artifact prevents executing a structurally broken plan. |
| 26 | Branch is not main/master | Pre-condition | `git branch --show-current` | PASS / FAIL | HIGH | The skill explicitly says "Never start implementation on main/master branch without explicit user consent." This is the highest-consequence failure mode (breaks the production branch). A one-line `git branch --show-current` check that exits 1 on main/master would make this mechanical rather than advisory. |

### Recommended Scripts
- `check-safe-branch.sh` — One-liner that reads `git branch --show-current` and exits 1 if the result is `main`, `master`, or other configured production branch names. Shared between `executing-plans` and `subagent-driven-development` (SDD skill also warns about this but has no script for it).

---

## test-driven-development

### Current Coverage
- None. This is a discipline/process skill with no scripts.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 27 | Test file pre-dates its implementation file (RED step happened first) | Post-condition | File system, git timestamps or commit log | PASS / WARNING per test-implementation pair | HIGH | The Iron Law is "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST." A script that checks git commit order — was the test file committed before the implementation file for a given pair? — would mechanically verify TDD was followed, not just claimed. This requires the plan's task structure (test committed first, then implementation) to be serialized into commits. |
| 28 | No production code files committed without a corresponding test file | Post-condition | Git diff of a task commit, test file naming conventions | PASS / WARNING | MEDIUM | A simpler check than timestamp ordering: for each new `.py` / `.ts` / etc. file committed, verify a corresponding test file exists (`test_foo.py`, `foo.test.ts`). This catches "test written after merge" and "test in a different commit that wasn't part of this task." |
| 29 | Test count is non-zero before implementation commit | Decision point | Test runner output captured in report | PASS / FAIL | MEDIUM | Verify that the implementer's report (filed under SDD) shows test results with at least one test per new function/method. An implementer report with "0 tests run" or "no tests" on a non-trivial implementation is a signal TDD was skipped. This is a validate-report extension rather than a standalone script. |

### Recommended Scripts
- `check-tdd-commit-order.py` — Takes `--implementation-file` and `--test-file`, reads the git log for each, and verifies the first test commit predates the first implementation commit. PASS/FAIL with commit SHAs. Designed to be run as part of the SDD spec-reviewer phase.

---

## systematic-debugging

### Current Coverage
- None. This is a discipline/process skill.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 30 | Bug fix includes a new test that demonstrates the fix | Post-condition | Git diff of fix commit, test file | PASS / FAIL / WARNING | HIGH | The skill's Phase 4 Step 1 states: "Create Failing Test Case — MUST have before fixing." A fix commit with no new test lines fails this check. The check is: does the git diff for the fix commit include changes to a test file? This is crude but catches the most common violation (fixing with no test at all). |
| 31 | Fix is a single-concern commit (not bundled with unrelated changes) | Post-condition | Git diff stats | PASS / WARNING | LOW | The skill forbids "bundled refactoring" and "while I'm here improvements." A heuristic check that counts changed files in a commit and warns if it exceeds a threshold (e.g., >5 files changed) catches bundled fixes. |

### Recommended Scripts
- `check-bug-fix-has-test.sh` — Takes a commit SHA. Counts lines changed in test files vs. total lines changed. FAIL if 0 test lines changed. WARNING if test coverage ratio is very low. Run from the SDD spec-reviewer for tasks identified as bug fixes.

---

## verification-before-completion

### Current Coverage
- None. This is a discipline/process skill with no scripts.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 32 | Fresh test run timestamp vs. last code change timestamp | Pre-condition (before claiming DONE) | Test result file, git status | PASS / STALE | HIGH | The skill's Iron Law is "NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE." A script that checks whether the most recent test run timestamp (from a CI log, test output file, or similar artifact) is newer than the most recent git commit prevents stale-test completion claims. |
| 33 | Implementer report contains literal test output (not just "tests pass") | Post-condition | Implementer report | PASS / WARNING | MEDIUM | The skill distinguishes between "Test command output: 0 failures" (valid) and "should pass now" (invalid). A script that validates the report's Tests section contains numeric output patterns (e.g., `\d+ (passed|tests? ok|failing: 0)`) mechanically enforces evidence-based claims vs. assertion-based ones. This is a validate-report extension. |

### Recommended Scripts
- Extend `validate-report.py` with an optional `--require-test-output-evidence` flag that scans the Tests section for numeric test result patterns (check #33).

---

## using-git-worktrees

### Current Coverage
- None. This is a procedural skill.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 34 | Worktree directory is gitignored before creation | Pre-condition | `.gitignore`, worktree directory path | PASS / FAIL | HIGH | The skill mandates `git check-ignore -q <dir>` before creating the worktree. This is already in the skill prose, but is currently a manual step. A wrapper script that combines the ignore check, the add-to-gitignore step if needed, and the `git worktree add` command would make this mechanical. |
| 35 | Worktree baseline tests pass | Post-condition | Test runner output | PASS / FAIL with details | MEDIUM | The skill Step 4 ("Verify Clean Baseline") is already a specified step. However, there is no artifact written to disk to prove the baseline was verified. A script that runs the tests and writes a `worktree-baseline.txt` result file would create a verifiable record. |

### Recommended Scripts
- `setup-worktree.sh` — Combines the gitignore check, `.gitignore` update if needed, `git worktree add`, dependency install detection, and baseline test run into a single script. Makes the whole setup mechanical and produces a structured result. Replaces the multi-step prose in the skill with a single command.

---

## requesting-code-review

### Current Coverage
- None specific to this skill.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 36 | Code-review subagent received DEVIATIONS.md contents in its context | Post-condition | `reports/task-N-quality-review.md`, `DEVIATIONS.md` | PASS / WARNING | MEDIUM | The SDD skill requires "Pass DEVIATIONS.md explicitly in the reviewer's context." Without checking that the quality-review report references deviations, this step can be silently skipped. A check that verifies the review report mentions "DEVIATIONS" or "deviations" when DEVIATIONS.md is non-empty catches this omission. |
| 37 | Review result is unambiguously PASS or FAIL (not ambiguous prose) | Post-condition | Review report | PASS / WARNING | MEDIUM | Review reports sometimes contain prose like "mostly good" or "proceed with caveats" that the controller interprets as a pass. A script that checks for an explicit PASS/APPROVED or FAIL/REJECTED verdict in the review report header enforces the binary gate the skill requires. |

### Recommended Scripts
- `check-review-verdict.sh` — Takes a review report path. Greps for PASS, APPROVED, FAIL, REJECTED verdict patterns in the first 20 lines. Returns PASS/FAIL/AMBIGUOUS. Would be called by `controller-checkpoint.py pre-dispatch` as part of check #16/#17 above.

---

## receiving-code-review

### Current Coverage
- None.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 38 | Reviewer suggestions from review report are all addressed or dispositioned | Post-condition | Review report, implementer fix commit | PASS / WARNING | LOW | After receiving a review, the skill requires fixing Critical and Important issues before proceeding. A script that parses the review report for "Critical:" and "Important:" sections and cross-checks them against DEVIATIONS.md (as resolved) or git diff (as fixed) would make this mechanically verifiable. This is complex to implement reliably but high-value when it works. |

### Recommended Scripts
- Low priority given complexity. Consider as a future extension of `extract-execution-trace.py`.

---

## dispatching-parallel-agents

### Current Coverage
- None.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 39 | Parallel agent tasks have disjoint file sets | Pre-condition | Task prompts or plan sections | PASS / FAIL with conflicting files | HIGH | The skill states "Agents would interfere (editing same files, using same resources)" as a reason NOT to use parallel dispatch. The same write-scope disjointness check from writing-plans (#6 above) applies here: before dispatching parallel tasks, verify their file sets don't overlap. Currently purely advisory. |
| 40 | All parallel agents have consistent summary output format | Post-condition | Returned summaries | PASS / WARNING | LOW | The skill requires "Specific output: Return summary of root cause and changes" for comparison across agents. A structural check that each agent's summary contains the required fields (root cause, files changed) would ensure the controller can synthesize them. |

### Recommended Scripts
- Reuse the write-scope disjointness logic from `validate-plan.py` extension (check #6). Extract it as a standalone `check-write-scope-disjoint.py` that takes two lists of files and checks for overlap.

---

## using-superpowers

### Current Coverage
- None. This is a meta-skill for skill invocation.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 41 | Skill count parity: skills/ count matches commands/ count | Post-condition (installation check) | `~/.claude/skills/superpowers/`, `~/.claude/commands/superpowers/` | PASS / FAIL with missing stubs | MEDIUM | The CLAUDE.md install architecture requires 1 command stub per skill. The verification command in CLAUDE.md uses `find | wc -l` manually. A dedicated script wrapping this check with clear output would make the installation verification mechanical and runnable in CI. |

### Recommended Scripts
- `verify-install.sh` (already exists at `tests/ARaymond-installation/verify-symlink-install.sh` per CLAUDE.md). The gap is that this script is not referenced from the `using-superpowers` skill itself. No new script needed — add a reference.

---

## writing-skills

### Current Coverage
- None. This is a meta-skill for skill authoring.

### Gaps (not yet covered)

| # | Check | Type | Input | Output | Priority | Rationale |
|---|-------|------|-------|--------|----------|-----------|
| 42 | SKILL.md frontmatter size within 1024 chars | Post-condition | SKILL.md | PASS / FAIL | HIGH | The skill states "Max 1024 characters total" for frontmatter. This is not validated anywhere. A skill with oversized frontmatter will fail to load in the skill picker. A script that measures frontmatter length (between the first and second `---` delimiters) provides an instant authoring check. |
| 43 | SKILL.md name uses only valid characters (letters, numbers, hyphens) | Post-condition | SKILL.md | PASS / FAIL | HIGH | The skill warns "special characters in skill names cause failures in shell scripts and the command stub generation loop." This is easy to check mechanically but is not currently checked. |
| 44 | Description starts with "Use when" | Post-condition | SKILL.md | PASS / FAIL | MEDIUM | Claude Search Optimization (CSO) requires descriptions to start with "Use when..." The check is a two-line grep. The skill's CSO section explains that descriptions that summarize workflow instead of triggering conditions cause Claude to follow the description rather than read the full skill — a known production failure mode. |
| 45 | Word count within target range | Post-condition | SKILL.md | PASS / WARNING | LOW | The skill provides word count targets (<150 words for frequently-loaded, <500 for others). `wc -w` gives an instant check. |

### Recommended Scripts
- `check-skill-meta.sh` — Takes a SKILL.md path. Validates frontmatter size (<1024 chars), name character set, description prefix ("Use when"), and word count. Single script for all skill authoring quality checks. Run after writing any new skill before committing.

---

## Cross-Cutting Summary

### Total Gaps Found

45 gaps across 15 skills (multiple gaps were combined into groups in some skills; the numbered items above are the distinct check opportunities).

Distribution by skill:
- brainstorming: 5
- writing-plans: 6
- handoff-acceptance: 4
- subagent-driven-development: 5
- finishing-a-development-branch: 4
- executing-plans: 2
- test-driven-development: 3
- systematic-debugging: 2
- verification-before-completion: 2
- using-git-worktrees: 2
- requesting-code-review: 2
- receiving-code-review: 1
- dispatching-parallel-agents: 2
- using-superpowers: 1
- writing-skills: 4

---

### Top 10 Highest-Priority Scripts to Build

Ranked by: prevents known production failure modes first, then covers BLOCKING gaps in existing skills, then structural gaps.

| Rank | Script | Skill | Checks | Why High Priority |
|------|--------|-------|--------|-------------------|
| 1 | Extend `controller-checkpoint.py` with spec/quality review file checks | subagent-driven-development | #16, #17 | Skipped reviews are the documented root cause of 3 production bugs in the reconciliation incident. The controller already runs this checkpoint — adding two file-existence checks makes the most impactful improvement with the smallest implementation cost. |
| 2 | `check-distilled-spec.py` | brainstorming | #1, #2, #3, #4 | Replaces `check-distillation.sh` (artifact detection only) with a complete structural validator. The distilled spec feeds writing-plans — structural defects propagate into every downstream task. |
| 3 | `check-acceptance-report.py` | handoff-acceptance | #12, #13 | The existing `check-handoff.sh` checks only the README header. A wrong verdict (REJECTED) consumed as ACCEPTED, or missing fixtures, poisons the entire downstream plan. This check creates a real machine-readable gate between handoff acceptance and planning. |
| 4 | Extend `validate-plan.py` with write-scope disjointness | writing-plans | #6 | The Write-Scope Partitioning table's purpose is to prevent parallel task file conflicts. Without parsing it for overlaps, the table is documentation with no enforcement. |
| 5 | `check-safe-branch.sh` | executing-plans, subagent-driven-development | #26 | Both skills warn against implementing on main/master. One-line check, catastrophic failure mode. |
| 6 | Extend `validate-plan.py` with archetype-to-obsolescence cross-check | writing-plans | #7 | Replacement/Refactor/Migration archetypes require an Obsolescence Verification Task. The omission silently allows orphaned code to ship. The archetype value is already in the plan header and parseable. |
| 7 | `check-source-contract-files.py` | writing-plans | #11 | Non-existent source contract paths fail at Task 0 dispatch time with a confusing error. Catching at plan-validation time produces a clearer error earlier. |
| 8 | `check-skill-meta.sh` | writing-skills | #42, #43, #44 | Frontmatter size and name character violations cause skill loading failures that are hard to diagnose. The description CSO issue is a documented production failure mode (Claude skips skill body). All three checks are trivially implementable. |
| 9 | `check-branch-ready.sh` | finishing-a-development-branch | #21 | The test suite passes against a dirty worktree is a silent failure that reaches main. A pre-option-presentation gate for uncommitted changes is a straightforward `git status --short` check. |
| 10 | `check-review-verdict.sh` | requesting-code-review | #37 | Ambiguous review verdict prose ("mostly good, proceed") is interpreted as PASS. A grep for explicit PASS/FAIL patterns in the first 20 lines of each review report enforces the binary gate that both spec and quality reviews require. |

---

### Handoff Boundary Checks That Don't Exist Yet

The pipeline has five major handoff boundaries. Current script coverage at each:

| Boundary | From → To | Current Coverage | Gap |
|----------|-----------|-----------------|-----|
| **Handoff → Brainstorming** | External handoff package → brainstorming session | `check-handoff.sh` (README header only) | No acceptance report existence check, no fixture verification, no verdict extraction |
| **Brainstorming → Writing Plans** | Distilled spec → plan | `check-distillation.sh` (artifact grep only) | No structure check, no size ratio check, no Contract Facts position check |
| **Writing Plans → Execution** | Plan → subagent-driven-development or executing-plans | `validate-plan.py` (structure) | No source contract file existence, no write-scope disjointness, no safe-branch check |
| **Task → Next Task (mid-execution)** | Implementer report → next dispatch | `controller-checkpoint.py pre-dispatch` (implementer report, checkboxes, deviations) | No spec-review or quality-review report existence check per task |
| **Execution → Branch Finish** | All tasks complete → finishing-a-development-branch | `controller-checkpoint.py pre-completion` (checkboxes, deviations, reports) | No uncommitted-changes check, no cross-task wiring check, no review verdict scan |

The highest-impact gap is the **Task → Next Task** boundary (check #16, #17). This is where the review-skipping failure mode lives — the controller can falsely declare a task complete because it only checks for the implementer report, not the review reports that are supposed to follow it.

The second-highest-impact gap is the **Handoff → Brainstorming** boundary (checks #12, #13). The acceptance report verdict is the gate that prevents poisoned contracts from entering the pipeline, but no script currently reads and validates that report.
