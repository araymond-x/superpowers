---
schema_version: 1
feature_archetype: migration
source_contracts: null
shared_constants: []
pattern_references: []
modules: null
tasks:
  - id: 10
    title: "Update entry-point skills (brainstorming, writing-plans, handoff-acceptance)"
  - id: 11
    title: "Update execution skills (SDD, executing-plans, finishing-a-development-branch)"
  - id: 12
    title: "Update prompt templates and references"
    depends_on: [11]
  - id: 13
    title: "Update regression tests and POC tests"
    depends_on: [12]
  - id: 14
    title: "Update CLAUDE.md and documentation"
    depends_on: [13]
---

# Per-Feature Directory — Module 3: Skills, Templates & Documentation

> **Parent plan:** `docs/imp-plans/2026-05-02-per-feature-directory-plan.md`
> **Module:** 3 of 3
> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Module Goal:** Update all SKILL.md files, prompt templates, reference documents, regression tests, and project documentation to use per-feature directory paths and the `.active-feature` lifecycle.

**Source Contracts:** None

**Contract Constraints:**
- Entry-point skills (brainstorming, writing-plans, handoff-acceptance) prompt for feature name and create `.active-feature`
- Feature name prompt: agent suggests name from context, user confirms or overrides
- Conflict detection at entry: stale pointer → auto-clean, completed → auto-clean, incomplete → prompt
- `finishing-a-development-branch` removes `.active-feature` + `.allow-main` on completion
- Spec output path: `<feature-dir>/spec.md` (was `docs/specs/YYYY-MM-DD-<topic>-design.md`)
- Plan output path: `<feature-dir>/plan.md` (was `docs/imp-plans/YYYY-MM-DD-<feature>.md`)
- All report paths: `<feature-dir>/reports/task-NNN-*.md`

**Feature Archetype:** Migration

## File Map

| File | Responsibility |
|------|----------------|
| `skills/brainstorming/SKILL.md` | Feature name prompt, spec output path |
| `skills/writing-plans/SKILL.md` | Feature name prompt, plan/manifest/review paths |
| `skills/handoff-acceptance/SKILL.md` | Feature name prompt on ACCEPTED |
| `skills/subagent-driven-development/SKILL.md` | All artifact path references (~30 refs) |
| `skills/executing-plans/SKILL.md` | Artifact path references |
| `skills/finishing-a-development-branch/SKILL.md` | Cleanup step |
| `skills/subagent-driven-development/controller-partner-prompt.md` | Partner review path |
| `skills/subagent-driven-development/pre-execution-audit-prompt.md` | Audit report path |
| `skills/subagent-driven-development/trace-auditor-prompt.md` | Trace/deviations paths |
| `skills/subagent-driven-development/references/report-naming-convention.md` | Example paths |
| `skills/writing-plans/references/module-template.md` | Parent plan path |
| `tests/ARaymond-skill-regression/validate-all-skills.py` | New checks |
| `tests/poc-feature-directory/test-feature-dir-hooks.sh` | Switch to real hooks |
| `CLAUDE.md` | Document new conventions |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 10 | `brainstorming/SKILL.md`, `writing-plans/SKILL.md`, `handoff-acceptance/SKILL.md` | distilled spec | Task 4 |
| Task 11 | `subagent-driven-development/SKILL.md`, `executing-plans/SKILL.md`, `finishing-a-development-branch/SKILL.md` | distilled spec | Task 4 |
| Task 12 | `controller-partner-prompt.md`, `pre-execution-audit-prompt.md`, `trace-auditor-prompt.md`, `report-naming-convention.md`, `module-template.md` | SKILL.md files | Task 11 |
| Task 13 | `validate-all-skills.py`, `test-feature-dir-hooks.sh` | all changed files | Tasks 9, 12 |
| Task 14 | `CLAUDE.md` | all changed files | Task 13 |

## Acceptance Criteria

- [ ] Brainstorming, writing-plans, and handoff-acceptance SKILL.md files include feature name prompt instructions
- [ ] All SKILL.md files reference `<feature-dir>/` paths instead of root-level paths
- [ ] `finishing-a-development-branch` includes `.active-feature` + `.allow-main` cleanup step
- [ ] Prompt templates reference `<feature-dir>/reports/` paths
- [ ] `report-naming-convention.md` shows feature-dir-prefixed example paths
- [ ] Regression tests check for `.active-feature` in `.gitignore` and verify no SKILL.md references bare root-level `DEVIATIONS.md`
- [ ] POC tests use real hooks (patched hook deleted)
- [ ] CLAUDE.md documents `.active-feature`, new directory structure

---

## Tasks

### Task 10: Update entry-point skills

**Files:**
- Modify: `skills/brainstorming/SKILL.md`
- Modify: `skills/writing-plans/SKILL.md`
- Modify: `skills/handoff-acceptance/SKILL.md`

- [x] **Step 1: Read current brainstorming SKILL.md**

Read `skills/brainstorming/SKILL.md`. Find spec output path references (lines ~29, ~89, ~146).

- [x] **Step 2: Add feature name prompt to brainstorming**

After the "Ask clarifying questions" checklist item (item 3), add a new step:

```markdown
3.5. **Establish feature name** — after 1-2 clarifying questions, when scope is clear:
   - Suggest a kebab-case feature name based on the conversation context
   - Prompt: *"All artifacts for this work will be organized under a feature directory. I suggest: **`<name>`**. Press enter to accept, or type a different name."*
   - Create `docs/imp-plans/YYYY-MM-DD-<feature-name>/`
   - Write `docs/imp-plans/YYYY-MM-DD-<feature-name>` to `.active-feature`
   - **Conflict detection:** If `.active-feature` already exists, check the referenced directory:
     - Dir doesn't exist → auto-clean `.active-feature`, proceed
     - Dir exists, all plan tasks completed → auto-clean, proceed
     - Dir exists, incomplete work → prompt: resume or archive
     - Dir exists, no plan → prompt: resume or start fresh
   - If brainstorming is abandoned before producing a spec, the empty feature directory and `.active-feature` are cleaned up by the next entry-point skill's conflict detection.
```

- [x] **Step 3: Update brainstorming spec output paths**

Change spec output path references:
- `docs/specs/YYYY-MM-DD-<topic>-design.md` → `<feature-dir>/spec.md`
- Distilled spec: `<feature-dir>/spec-distilled.md`
- The `Save to: same directory as the full spec, with -distilled suffix` instruction still works since both live in `<feature-dir>/`

- [x] **Step 4: Read and update writing-plans SKILL.md**

Read `skills/writing-plans/SKILL.md`. Update:
- Line ~21: `docs/imp-plans/YYYY-MM-DD-<feature-name>.md` → `<feature-dir>/plan.md`
- Line ~37: `docs/imp-plans/plan-review-report.md` → `<feature-dir>/plan-review-report.md`
- Line ~38: `docs/imp-plans/plan-manifest.txt` → `<feature-dir>/plan-manifest.txt`
- Line ~50: `docs/imp-plans/plan-manifest.txt` → `<feature-dir>/plan-manifest.txt`
- Line ~419: `docs/imp-plans/plan-review-report.md` → `<feature-dir>/plan-review-report.md`

Add feature name prompt at the start of the checklist (before Step 1):

```markdown
0.5. **Establish feature name** (if no `.active-feature` exists) — prompt user for feature name using the same mechanism as brainstorming. If `.active-feature` already exists, read it and use the established feature directory. Run the same conflict detection logic.
```

- [x] **Step 5: Read and update handoff-acceptance SKILL.md**

Read `skills/handoff-acceptance/SKILL.md`. Add feature name prompt instruction after the ACCEPTED verdict handling:

```markdown
When verdict is ACCEPTED and the work starts a new feature (not continuing an existing one):
- Run the feature name prompt and `.active-feature` creation (same as brainstorming step 3.5)
```

- [x] **Step 6: Commit**

```bash
git add skills/brainstorming/SKILL.md skills/writing-plans/SKILL.md skills/handoff-acceptance/SKILL.md
git commit -m "feat: add feature name prompt and .active-feature to entry-point skills"
```

---

### Task 11: Update execution skills

**Files:**
- Modify: `skills/subagent-driven-development/SKILL.md`
- Modify: `skills/executing-plans/SKILL.md`
- Modify: `skills/finishing-a-development-branch/SKILL.md`

- [x] **Step 1: Read current SDD SKILL.md**

Read `skills/subagent-driven-development/SKILL.md` in full. This is the file with the most path references (~30).

**Warning:** SDD SKILL.md is at ~5029 words, over the 5000-word soft limit. Path changes should be roughly word-neutral (replacing `DEVIATIONS.md` with `<feature-dir>/deviations.md` is similar length). Check word count after edits with `wc -w`.

- [x] **Step 2: Update SDD stale artifact handling (lines ~182-188)**

Replace root-level archive instructions with feature-dir archive:

```markdown
| Current State | Action |
|---|---|
| `<feature-dir>/reports/task-*.md` exist | Move to `<feature-dir>/reports/archive-<timestamp>/` |
| `<feature-dir>/deviations.md` exists with content | Archive to `<feature-dir>/reports/archive-<timestamp>/deviations.md` |
```

- [x] **Step 3: Update SDD Plan Ingestion step 5 (line ~192)**

Change `Create DEVIATIONS.md at the project root` to:

```markdown
Create `<feature-dir>/deviations.md` (read the feature directory from `.active-feature`).
Use the Write tool to create the file using the template in `references/deviations-template.md`.
Create `<feature-dir>/reports/` directory if it doesn't exist.
```

- [x] **Step 4: Update SDD pre-execution audit paths (lines ~202-224)**

Replace all occurrences of:
- `reports/pre-execution-audit.md` → `<feature-dir>/reports/pre-execution-audit.md`
- `reports/pre-execution-audit-self-assessment.md` → `<feature-dir>/reports/pre-execution-audit-self-assessment.md`

- [x] **Step 5: Update SDD checkpoint commands (lines ~289-301)**

Replace `--deviations-file DEVIATIONS.md --reports-dir reports/` with:
```
--feature-dir <feature-dir> --deviations-file <feature-dir>/deviations.md --reports-dir <feature-dir>/reports/
```

- [x] **Step 6: Update SDD partner review paths (lines ~352-357)**

Replace `reports/partner-review-NNN.md` with `<feature-dir>/reports/partner-review-NNN.md`.

- [x] **Step 7: Update SDD DEVIATIONS.md references (lines ~388-399)**

Replace all `DEVIATIONS.md` references with `<feature-dir>/deviations.md`.

- [x] **Step 8: Update SDD report naming and save paths (lines ~407-426)**

Replace:
- `reports/task-NNN-implementer-report.md` → `<feature-dir>/reports/task-NNN-implementer-report.md`
- `reports/task-NNN-spec-review.md` → `<feature-dir>/reports/task-NNN-spec-review.md`
- `reports/task-NNN-quality-review.md` → `<feature-dir>/reports/task-NNN-quality-review.md`
- `reports/` directory reference → `<feature-dir>/reports/`

- [x] **Step 9: Update SDD honesty check path (line ~438)**

Replace `reports/honesty-check-YYYY-MM-DD.md` with `<feature-dir>/reports/honesty-check-YYYY-MM-DD.md`.

- [x] **Step 10: Update SDD execution trace paths (line ~454)**

Replace `--deviations-file DEVIATIONS.md --reports-dir reports/ --output execution-trace.json` with feature-dir paths.

- [x] **Step 11: Check SDD SKILL.md word count**

Run: `wc -w skills/subagent-driven-development/SKILL.md`
If over 5100 words, extract content to `references/` to stay under the limit.

- [x] **Step 12: Read and update executing-plans SKILL.md**

Read `skills/executing-plans/SKILL.md`. Update any artifact path references to use `<feature-dir>/` prefix.

- [x] **Step 13: Update finishing-a-development-branch SKILL.md**

Read `skills/finishing-a-development-branch/SKILL.md`. Add cleanup step to all 4 options:

```markdown
**Post-completion cleanup** (applies to all options):
After the chosen option completes:
1. Remove `.active-feature` if it exists
2. Remove `.allow-main` if it exists (main branch only)
```

- [x] **Step 14: Commit**

```bash
git add skills/subagent-driven-development/SKILL.md skills/executing-plans/SKILL.md skills/finishing-a-development-branch/SKILL.md
git commit -m "feat: update execution skills for per-feature directory paths"
```

---

### Task 12: Update prompt templates and references

**Files:**
- Modify: `skills/subagent-driven-development/controller-partner-prompt.md`
- Modify: `skills/subagent-driven-development/pre-execution-audit-prompt.md`
- Modify: `skills/subagent-driven-development/trace-auditor-prompt.md`
- Modify: `skills/subagent-driven-development/references/report-naming-convention.md`
- Modify: `skills/writing-plans/references/module-template.md`

- [x] **Step 1: Update controller-partner-prompt.md**

Read `skills/subagent-driven-development/controller-partner-prompt.md`. Update line ~128:

```markdown
**Controller saves partner output to:** `<feature-dir>/reports/partner-review-NNN.md`
```

- [x] **Step 2: Update pre-execution-audit-prompt.md**

Read `skills/subagent-driven-development/pre-execution-audit-prompt.md`. Update:
- Line ~22: `reports/pre-execution-audit-self-assessment.md` → `<feature-dir>/reports/pre-execution-audit-self-assessment.md`
- Line ~114: `reports/pre-execution-audit.md` → `<feature-dir>/reports/pre-execution-audit.md`

- [x] **Step 3: Update trace-auditor-prompt.md**

Read `skills/subagent-driven-development/trace-auditor-prompt.md`. Update:
- Line ~26: `DEVIATIONS.md` → `<feature-dir>/deviations.md`
- Line ~68: `reports/` → `<feature-dir>/reports/`

- [x] **Step 4: Update report-naming-convention.md**

Read `skills/subagent-driven-development/references/report-naming-convention.md`. Update example paths (lines ~8-13):

```
<feature-dir>/reports/task-000-implementer-report.md   (first task in the plan)
<feature-dir>/reports/task-000-spec-review.md
<feature-dir>/reports/task-000-quality-review.md
<feature-dir>/reports/task-001-implementer-report.md   (second task)
```

Add a note: *"`<feature-dir>` is the path from `.active-feature` (e.g., `docs/imp-plans/2026-05-02-my-feature`)."*

- [x] **Step 5: Update module-template.md**

Read `skills/writing-plans/references/module-template.md`. Update line ~10:

```markdown
> **Parent plan:** `<feature-dir>/plan.md`
```

- [x] **Step 6: Commit**

```bash
git add skills/subagent-driven-development/controller-partner-prompt.md \
      skills/subagent-driven-development/pre-execution-audit-prompt.md \
      skills/subagent-driven-development/trace-auditor-prompt.md \
      skills/subagent-driven-development/references/report-naming-convention.md \
      skills/writing-plans/references/module-template.md
git commit -m "docs: update prompt templates and references for per-feature directory paths"
```

---

### Task 13: Update regression tests and POC tests

**Files:**
- Modify: `tests/ARaymond-skill-regression/validate-all-skills.py`
- Modify: `tests/poc-feature-directory/test-feature-dir-hooks.sh`
- Delete: `tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh`

- [x] **Step 1: Read validate-all-skills.py**

Read `tests/ARaymond-skill-regression/validate-all-skills.py`. Find where skill content checks are defined.

- [x] **Step 2: Add .active-feature checks to regression tests**

Add checks:
1. `.gitignore` contains `.active-feature`
2. Entry-point SKILL.md files (brainstorming, writing-plans) contain "active-feature" or "feature name" reference
3. No SKILL.md file references bare `DEVIATIONS.md` (without `<feature-dir>` context) — except in archived/historical references

- [x] **Step 3: Update POC test to use real hooks**

Read `tests/poc-feature-directory/test-feature-dir-hooks.sh`. Update tests that currently use the patched hook to use the real `sdd-pre-dispatch-hook.sh` instead. The real hook now natively supports `.active-feature`.

Add two new tests:
- Test 8: `.active-feature` lifecycle (create → hooks resolve → cleanup → hooks fall back)
- Test 9: Conflict detection (existing `.active-feature` + new feature)

- [x] **Step 4: Delete the patched hook**

```bash
rm tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh
```

- [x] **Step 5: Run regression tests**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

Expected: All checks pass (updated count).

- [x] **Step 6: Run POC tests**

```bash
bash tests/poc-feature-directory/test-feature-dir-hooks.sh
```

Expected: All tests pass (9/9 or updated count).

- [x] **Step 7: Commit**

```bash
git add tests/ARaymond-skill-regression/validate-all-skills.py \
      tests/poc-feature-directory/test-feature-dir-hooks.sh
git rm tests/poc-feature-directory/sdd-pre-dispatch-hook-patched.sh
git commit -m "test: update regression and POC tests for per-feature directory migration"
```

---

### Task 14: Update CLAUDE.md and documentation

**Files:**
- Modify: `CLAUDE.md`

- [x] **Step 1: Read current CLAUDE.md**

Read `CLAUDE.md`. Find sections that reference artifact paths.

- [x] **Step 2: Add .active-feature documentation**

Add a new section after "Worktree Sessions":

```markdown
## .active-feature File
- Single-line plaintext file at project root containing relative path to active feature directory
- Format: `docs/imp-plans/YYYY-MM-DD-<feature-name>`
- Created by entry-point skills (brainstorming, writing-plans, handoff-acceptance)
- Read by all hooks for artifact path resolution
- Cleaned up by `finishing-a-development-branch`
- Gitignored — workspace state, not project state
- Conflict detection: entry-point skills check for stale/conflicting `.active-feature` at startup
```

- [x] **Step 3: Update Output Path Convention section**

Update the existing Output Path Convention section:

```markdown
## Output Path Convention
All feature artifacts are consolidated in a per-feature directory:
- Feature directory → `docs/imp-plans/YYYY-MM-DD-<feature-name>/`
- Design specs → `<feature-dir>/spec.md` and `spec-distilled.md`
- Implementation plans → `<feature-dir>/plan.md` and `module-N-*.md`
- Plan manifest → `<feature-dir>/plan-manifest.txt`
- Plan review → `<feature-dir>/plan-review-report.md`
- Deviations → `<feature-dir>/deviations.md`
- All execution reports → `<feature-dir>/reports/`
```

- [x] **Step 4: Update test counts**

Update the testing section's check counts to reflect the new regression test additions.

- [x] **Step 5: Update Hooks-Based Enforcement section**

Add `.active-feature` gate to the plan-validation-gate description. Note that `SUPERPOWERS_ROOT` was added to `plan-validation-gate-hook.sh` and `sdd-stop-hook.sh`.

- [x] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for per-feature directory migration"
```
