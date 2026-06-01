---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
source_contracts: "docs/imp-plans/2026-05-31-pipeline-flexibility/spec-distilled.md"
pattern_references: []
tasks:
  - id: 6
    title: "Writing-plans SKILL.md: direct entry path and verification guidance"
    depends_on: []
    review_tier: minimum
  - id: 7
    title: "SDD SKILL.md: verification tasks documentation"
    depends_on: []
    review_tier: minimum
  - id: 8
    title: "Integration test: add verification task e2e step"
    depends_on: []
    review_tier: minimum
  - id: 9
    title: "SSOT audit investigation"
    depends_on: []
    review_tier: minimum
---

# Module 3: Documentation and Audit

**Goal:** Update SKILL.md documentation for direct entry and verification tasks, add integration test coverage, and produce the SSOT audit findings document.

**Source Contracts:** None

**Contract Constraints:**
- SDD SKILL.md is at 4753 words with 5000-word soft limit — new section must fit within ~247 words or extract existing content
- `check-distillation.sh` takes a single path argument, returns JSON with `status: PASS|FAIL`
- SSOT audit scope: 15 SKILL.md files vs 4 active hooks (exclude `sdd-skill-enforcement-hook.sh` and `sdd-stop-hook.sh` — not registered in `settings.json`)
- Task 9 is a read-only investigation — no code changes, produces findings document + BACKLOG.md rows

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 6 | `skills/writing-plans/SKILL.md` | — | Tasks 0, 1 |
| Task 7 | `skills/subagent-driven-development/SKILL.md` | — | Task 3 |
| Task 8 | `tests/integration/sdd-e2e-test.sh` | All scripts from Modules 1-2 | Tasks 2, 3, 4, 5 |
| Task 9 | `docs/process-improvement-findings/2026-05-31-ssot-audit.md`, `docs/process-improvement-findings/BACKLOG.md` | All 15 SKILL.md files, `~/.claude/settings.json` | — |

---

### Task 6: Writing-plans SKILL.md — direct entry path and verification guidance

**Files:**
- Modify: `skills/writing-plans/SKILL.md`

- [x] **Step 1: Enhance Step 0.5 with direct entry guardrails**

Replace the Step 0.5 description (currently a single line at line 29 of writing-plans/SKILL.md) with the expanded version that includes 4-branch conflict detection:

```markdown
0.5. **Resolve feature directory** — Check for `.active-feature` and handle all entry scenarios:

**If `.active-feature` exists**, read the path and check the referenced directory:
- Directory doesn't exist → stale reference; auto-clean `.active-feature`, proceed as new
- Directory exists, plan has all tasks completed → prior feature completed; auto-clean, proceed as new
- Directory exists, has incomplete work → prompt: "Active feature `<name>` has incomplete work. Resume it, or archive to `docs/imp-plans/archive/` and start fresh?"
- Directory exists, no plan file → prompt: "Feature directory `<name>` exists but has no plan. Resume with this directory, or start fresh?"

**If `.active-feature` doesn't exist** (or was just cleaned): prompt for a kebab-case feature name, create `docs/imp-plans/YYYY-MM-DD-<feature-name>/`, and write the path to `.active-feature`.

**Worktree/branch guard** (after resolving feature directory): Check the current branch. If on `main` (or `master`), offer: "You're on `main`. Recommend creating a worktree via `superpowers:using-git-worktrees`. Proceed on `main` with acknowledgment?" Allow proceeding if the user confirms.

**Optional spec input**: If the user provides a distilled spec, run `check-distillation.sh` to validate it. Record the spec path in the plan's `Source Contracts` field. Neither a spec nor a handoff is required — planning directly from conversation context is valid.

**Entry mode recording**: If no brainstorming artifacts exist in the feature directory (no `spec.md`, no `spec-distilled.md` from a prior brainstorming run), set `entry_mode: direct` in the plan YAML frontmatter. Otherwise, default `entry_mode: brainstorming`.
```

- [x] **Step 2: Update the Context block**

Replace the current Context section (lines 16-19 of writing-plans/SKILL.md) with:

```markdown
**Context:** This skill has two entry paths:
1. **After brainstorming** — `superpowers:brainstorming` produces a spec, sets up a worktree, and creates `.active-feature`. This skill reads those artifacts and writes the plan.
2. **Direct entry** — Invoke this skill directly with a spec, handoff package, or just conversation context. The skill handles setup guardrails (conflict detection, worktree guard, optional spec validation) that brainstorming would otherwise provide. Direct entry is a first-class path, not a fallback.

For direct entry, provide any of:
- Path to a spec or distilled spec (runs `check-distillation.sh` if distilled)
- Path to a handoff package (verify it passed `superpowers:handoff-acceptance` first)
- Just a description of what to build — the plan can be written from conversation context alone
```

- [x] **Step 3: Add verification task classification guidance**

Add a new section after the `review_tier` section (after line 396), before "No Placeholders":

```markdown
## Declaring `task_type` per Task

Each task may declare `task_type: verification` in the plan's YAML frontmatter to signal that the task is read-only — it observes, audits, or reports but does not modify any files. Omit it (or set `implementation`) by default.

**Bright line: if the task modifies any file in the repo, it's `implementation`.**

| Appropriate for `verification` | Stay as `implementation` |
|---|---|
| Grep for orphaned code/stale references | Code deletion based on grep results |
| Run test suite, report results | Fix failing tests |
| Consistency audit (naming, imports) | Refactor to fix inconsistencies |
| Count/inventory tasks | Anything that modifies files |
| Smoke test / manual verification | Test-writing (creates test files) |
| SSOT audit (compare docs vs hooks) | Documentation updates |

`task_type` is orthogonal to `review_tier`. A verification task automatically gets reduced ceremony (no dispatched reviews), but you can declare both fields explicitly.

`validate-plan.py` emits a WARNING when verification task titles contain write-suggesting keywords (`create`, `add`, `implement`, `fix`, `modify`, `write`, `update`, `refactor`, `migrate`, `delete`, `remove`). The plan reviewer provides the semantic check.
```

- [x] **Step 4: Verify word count**

Run: `wc -w skills/writing-plans/SKILL.md`
Expected: Under 5000 words

- [x] **Step 5: Commit**

```bash
git add skills/writing-plans/SKILL.md
git commit -m "docs(writing-plans): add direct entry path and verification task guidance

- Step 0.5 enhanced with 4-branch conflict detection, worktree guard,
  optional spec validation, and entry mode recording
- Context block updated: direct entry is first-class, not fallback
- New section: task_type classification with bright-line rule and table

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 7: SDD SKILL.md — verification tasks documentation

**Files:**
- Modify: `skills/subagent-driven-development/SKILL.md`

- [x] **Step 1: Check current word count and headroom**

Run: `wc -w skills/subagent-driven-development/SKILL.md`
Expected: ~4753 words (247 words headroom)

- [x] **Step 2: Add Verification Tasks section**

Add after "Controller Partner Verification" section (after line 345 of current SDD SKILL.md), before "Model Selection":

```markdown
## Verification Tasks

Tasks with `task_type: verification` are read-only audits dispatched as subagents but exempt from the review cycle. They observe, grep, count, or report — never modify files.

**Controller flow for verification tasks:**
1. Dispatch implementer with read-only auditor prompt (see below)
2. Read the implementer report
3. Mark task complete — no spec review, no quality review, no partner review

**Modified implementer prompt for verification tasks:**

> "You are a read-only auditor. Do not create, modify, or delete any repository files. Your report text is your only output. If you discover something that needs fixing, describe it in your report — do not fix it."

**Defense-in-depth:**
- Plan-time: `validate-plan.py` warns on write-suggesting keywords in verification titles
- Pre-completion: verification tasks capped at ≤30% of total tasks
- Pre-completion: git log check detects file modifications during verification windows
- Dispatch: hook skips review checks (4b, 4c, 5d) for verification tasks
```

> **Disposition note (pre-execution audit, Order 5):** Spec D3 lists four defense
> layers; layer 4 ("restricted prompt") is delivered **advisorily** — the controller
> hands the read-only auditor prompt to the verification subagent via this SKILL.md
> text. It is intentionally NOT mechanically enforced (no separate prompt file, no
> `implementer-prompt.md` change, no hook/checkpoint gate that inspects the dispatch
> prompt). The **git reality check** (Task 5) is the mechanical backstop for that
> layer: if a verification subagent ignores the prompt and modifies files, the
> pre-completion git-log check catches it. This is the intended design per D2
> ("dispatch subagent, skip reviews"), not a dropped layer. Keep the four bullets
> above as-is; do not add a prompt-enforcement mechanism.

- [x] **Step 3: Verify word count stays under 5000**

Run: `wc -w skills/subagent-driven-development/SKILL.md`
Expected: Under 5000 words. If over, tighten adjacent sections or extract content to `references/`.

- [x] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/SKILL.md
git commit -m "docs(sdd): add verification tasks section

Documents controller flow, read-only auditor prompt, and 4-layer
defense-in-depth for verification task type.

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 8: Integration test — add verification task e2e step

**Files:**
- Modify: `tests/integration/sdd-e2e-test.sh`

- [x] **Step 1: Read the current integration test**

Read `tests/integration/sdd-e2e-test.sh` to understand the structure: `$PROJECT` resolution, `$PYTHON` setup, `$TEMP_DIR` usage, step numbering, success/failure reporting.

- [x] **Step 2: Add Step 9 — verification task type validation**

Add before the final summary output:

```bash
# Step 9: Verification task type — validate-plan accepts it
echo "=== Step 9: Verification task type ==="

cat > "$TEMP_DIR/plan-verif.md" << 'PLAN_EOF'
---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
tasks:
  - id: 93
    title: "Implement core feature"
  - id: 94
    title: "Audit orphaned references"
    task_type: verification
    depends_on: [93]
---
# Verification Test Plan

**Source Contracts**: None
**Feature Archetype**: Extension

## Code Footprint
- foo.py (modified)

## Write-Scope Partitioning

| Task | Owned Files | Read-Only | Depends On |
|------|-------------|-----------|------------|
| Task 93 | foo.py | — | — |
| Task 94 | — | foo.py | Task 93 |

### Task 93: Implement core feature
- [x] Step 1: implement

### Task 94: Audit orphaned references
- [x] Step 1: grep for orphans
PLAN_EOF

# NOTE: append `|| true` — the e2e harness runs under `set -e` + an ERR trap, and
# validate-plan.py exits 2 on WARNING. Without `|| true` the command substitution's
# non-zero exit aborts the whole test before the STATUS check (matches the existing
# `... 2>&1 || true` convention at Steps 3/7/8).
RESULT=$($PYTHON "$PROJECT/skills/subagent-driven-development/scripts/validate-plan.py" --plan-file "$TEMP_DIR/plan-verif.md" 2>&1 || true)
STATUS=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
if [ "$STATUS" = "FAIL" ]; then
  echo "FAIL: validate-plan.py rejected verification task plan"
  exit 1
fi
echo "PASS: Step 9 — verification task validation"
```

- [x] **Step 3: Add Step 10 — verification keyword WARNING**

```bash
# Step 10: Verification task with write-suggesting keyword → WARNING
echo "=== Step 10: Verification keyword WARNING ==="

cat > "$TEMP_DIR/plan-verif-kw.md" << 'PLAN_EOF'
---
schema_version: 1
feature_archetype: extension
tasks:
  - id: 95
    title: "Create cleanup script"
    task_type: verification
---
# Keyword Test Plan

**Source Contracts**: None
**Feature Archetype**: Extension

## Code Footprint
- foo.py (modified)

## Write-Scope Partitioning

| Task | Owned Files | Read-Only | Depends On |
|------|-------------|-----------|------------|
| Task 95 | — | foo.py | — |

### Task 95: Create cleanup script
- [x] Step 1: create
PLAN_EOF

# NOTE: `|| true` is REQUIRED here — this plan intentionally triggers a WARNING
# (exit 2), which would otherwise abort the `set -e` harness at this command
# substitution before the STATUS check runs.
RESULT=$($PYTHON "$PROJECT/skills/subagent-driven-development/scripts/validate-plan.py" --plan-file "$TEMP_DIR/plan-verif-kw.md" 2>&1 || true)
STATUS=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
if [ "$STATUS" != "WARNING" ]; then
  echo "FAIL: expected WARNING for verification task with 'Create' keyword, got $STATUS"
  exit 1
fi
echo "PASS: Step 10 — verification keyword WARNING"
```

- [x] **Step 4: Update step count in test summary**

Update the final summary line to reflect 10 steps.

- [x] **Step 5: Run the integration test**

Run: `bash tests/integration/sdd-e2e-test.sh`
Expected: ALL 10 steps PASS

- [x] **Step 6: Commit**

```bash
git add tests/integration/sdd-e2e-test.sh
git commit -m "test(e2e): add verification task type steps (9-10)

Step 9: validate-plan accepts plans with task_type: verification
Step 10: verification + write keyword triggers WARNING

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 9: SSOT audit investigation

**Files:**
- Create: `docs/process-improvement-findings/2026-05-31-ssot-audit.md`
- Modify: `docs/process-improvement-findings/BACKLOG.md`

This task is a **read-only investigation** — it reads SKILL.md files and hook scripts, compares them, and produces a findings document. No code is modified.

- [x] **Step 1: Read all 15 SKILL.md files**

Read each SKILL.md under `skills/*/SKILL.md`. For each, identify sections that prescribe a manual step the controller must perform (e.g., "Run script X", "Before dispatching, check Y", "Create file Z").

- [x] **Step 2: Read the 4 active hooks**

Read the 4 hook scripts registered in `~/.claude/settings.json`:
1. `sdd-pre-dispatch-hook.sh` (PreToolUse → Agent) — all checks
2. `sdd-report-guard.sh` (PreToolUse → Bash) — report file protection
3. `plan-validation-gate-hook.sh` (PreToolUse → Skill) — plan quality gate
4. `hooks/session-start` (SessionStart) — skill loading

Do NOT audit `sdd-skill-enforcement-hook.sh` or `sdd-stop-hook.sh` — they exist on disk but are not registered in `settings.json`.

- [x] **Step 3: Compare and classify**

For each manual prescription that overlaps with hook enforcement:
- Document: SKILL.md file + line range, hook script + check number, any argument/threshold drift
- Classify:
  - **retire** — hook is authoritative, manual step is redundant ceremony (may cause false honesty-check guilt)
  - **strengthen** — manual step prescribes something the hook doesn't enforce (hook should add it)
  - **keep** — genuinely complementary (e.g., skill provides guidance, hook provides enforcement)

- [x] **Step 4: Write findings document**

Create `docs/process-improvement-findings/2026-05-31-ssot-audit.md` with:

```markdown
# SSOT Audit: SKILL.md Manual Prescriptions vs Hook Enforcement

**Date:** 2026-05-31
**Scope:** 15 SKILL.md files vs 4 active hooks
**Excluded:** sdd-skill-enforcement-hook.sh, sdd-stop-hook.sh (not registered in settings.json)

## Methodology
[How the audit was conducted — which files were read, what constituted a "manual prescription"]

## Findings

| # | SKILL.md | Location | Prescription | Hook | Check | Drift | Classification |
|---|----------|----------|-------------|------|-------|-------|---------------|
| 1 | ... | L123-130 | "Run X before Y" | sdd-pre-dispatch-hook.sh | Check 6 | args differ | retire |

## Summary
- Total manual prescriptions found: N
- Retire: N (hook is authoritative)
- Strengthen: N (hook should add enforcement)
- Keep: N (genuinely complementary)

## Recommended Sprint 3 Quick Wins
[List the top 3-5 most impactful retire/strengthen items with BACKLOG IDs]
```

- [x] **Step 5: Update BACKLOG.md**

Update existing rows:
- `N2`: status `open` → `done`, add "2026-05-31-ssot-audit.md" to Where/Notes
- `B6`: status `open` → `in-flight` (when SDD execution begins)
- `P1`: status `open` → `in-flight` (when SDD execution begins)

Add new rows (one per actionable finding) with IDs in the `N*` series, size estimates, and classification.

- [x] **Step 6: Commit**

```bash
git add docs/process-improvement-findings/2026-05-31-ssot-audit.md docs/process-improvement-findings/BACKLOG.md
git commit -m "docs: SSOT audit — manual prescriptions vs hook enforcement

Audit of 15 SKILL.md files against 4 active hooks.
Findings classified as retire/strengthen/keep.
New BACKLOG.md rows for actionable items.

Prompted by Aaron; Co-Authored by Claude"
```

## Module 3 Acceptance Criteria

- [x] Writing-plans SKILL.md Step 0.5 has 4-branch conflict detection, worktree guard, spec input, entry mode recording
- [x] Writing-plans context block describes direct entry as first-class
- [x] Verification task classification table with bright-line rule documented
- [x] SDD SKILL.md has Verification Tasks section (controller flow, auditor prompt, defense-in-depth)
- [x] SDD SKILL.md stays under 5000 words
- [x] Integration test has 10 passing steps (was 8)
- [x] SSOT audit findings document exists with classification table
- [x] BACKLOG.md updated with N2 done + new rows from audit
