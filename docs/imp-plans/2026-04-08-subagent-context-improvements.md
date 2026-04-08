# Subagent Context Improvements Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first -- direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Prevent three categories of architectural violations that persist despite the SDD review process: duplicated constants across subagent boundaries, fixture-only contract tests, and symptom-level bug fixes.

**Architecture:** Three targeted additions to existing skill prompt templates. (1) A Shared Constants Passthrough section in the implementer prompt template and corresponding ingestion step in the SDD SKILL.md, (2) an import assertion step in the Task 0 contract verification template, (3) a fix complexity classification gate in the systematic-debugging SKILL.md. Each improvement inserts a decision point at the exact moment the failure mode occurs.

**Tech Stack:** Markdown (prompt templates, skill files)

**Source Contracts:** None

**Contract Constraints:** None

**Feature Archetype:** Extension -- adds sections to existing prompt templates without replacing them.

**File Map / Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| Modified | `skills/subagent-driven-development/implementer-prompt.md` | Add Shared Constants section | Existing sections preserved |
| Modified | `skills/subagent-driven-development/SKILL.md` | Add ingestion step + passthrough section | Existing 7 steps + passthrough preserved |
| Modified | `skills/writing-plans/references/task-0-template.md` | Add import assertion step | Existing 6 steps preserved |
| Modified | `skills/writing-plans/SKILL.md` | Add Shared Constants to plan header | Existing header fields preserved |
| Modified | `skills/systematic-debugging/SKILL.md` | Add Fix Complexity Gate to Phase 4 | Existing 4 phases preserved |

---

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 1 | `skills/writing-plans/SKILL.md` (plan header section only) | -- | -- |
| Task 2 | `skills/subagent-driven-development/SKILL.md` (ingestion + passthrough sections) | -- | Task 1 |
| Task 3 | `skills/subagent-driven-development/implementer-prompt.md` | -- | Task 2 |
| Task 4 | `skills/writing-plans/references/task-0-template.md` | -- | -- |
| Task 5 | `skills/systematic-debugging/SKILL.md` | -- | -- |
| Task 6 | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md` | All modified files | Tasks 1-5 |

---

### Task 1: Add Shared Constants Field to Plan Header Template

**Files:**
- Modify: `skills/writing-plans/SKILL.md` (plan header template, ~line 168)

**Context:** The plan header currently has Source Contracts and Contract Constraints fields. We add a Shared Constants field that forces the plan author to enumerate constants, type definitions, and canonical value lists that subagents must import rather than redefine. This is the "declaration" side -- Task 2 adds the "injection" side.

- [ ] **Step 1: Add Shared Constants field to the plan header template**

In `skills/writing-plans/SKILL.md`, locate the plan header template (the markdown code block starting at ~line 155). Insert the new field after `**Contract Constraints:**` and before `**Feature Archetype:**`:

```markdown
**Shared Constants:** [Constants, type definitions, enum values, and canonical value lists that subagents must import -- not redefine. Format: `CONSTANT_NAME` from `path/to/file.py`. Write "None" if no shared constants apply.]
```

- [ ] **Step 2: Add explanatory paragraph after the header template**

After the paragraph ending with "do not plan against an unverified handoff" (~line 188), add:

```markdown
The **Shared Constants** field prevents a specific failure mode: subagents that need a value (e.g., `LIABILITY_TYPES`, `VALID_ACCOUNT_TYPES`) but don't know it exists as a constant, so they hardcode an array. When the constant changes, the hardcoded copy diverges silently. By enumerating shared constants in the plan, the controller can inject them into every subagent dispatch (see the SDD skill's Shared Constants Passthrough). If the plan has no shared constants, verify that no tasks import from files that define reusable constants.
```

- [ ] **Step 3: Verify no structural issues**

```bash
python3 ~/.claude/skills/superpowers/subagent-driven-development/scripts/validate-plan.py --plan-file skills/writing-plans/SKILL.md 2>/dev/null || echo "N/A — SKILL.md is not a plan file"
```

This file is a skill, not a plan -- validate-plan.py won't apply. Instead, verify the skill regression tests pass:

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```
Expected: 122 checks PASS

- [ ] **Step 4: Commit**

```bash
git add skills/writing-plans/SKILL.md
git commit -m "feat: Add Shared Constants field to plan header template"
```

---

### Task 2: Add Shared Constants Ingestion and Passthrough to SDD SKILL

**Files:**
- Modify: `skills/subagent-driven-development/SKILL.md` (Plan Ingestion + new passthrough section)

**Context:** The SDD SKILL.md has 7 ingestion steps and a Contract Constraints Passthrough section. We add: (1) a new ingestion step to extract shared constants from the plan, and (2) a Shared Constants Passthrough section that mirrors the Contract Constraints Passthrough pattern.

- [ ] **Step 0: Extract content to references/ to stay under 5000-word limit**

The SDD SKILL.md is currently at 5018 words (already over the 5000-word limit). Task 2 adds ~195 words. To make room, extract the DEVIATIONS.md header template (the markdown code block in Step 6 of Plan Ingestion, ~lines 189-206) to `skills/subagent-driven-development/references/deviations-template.md` and replace the inline template with: "Use the template in `references/deviations-template.md`." This saves ~65 words. Also extract the Report Naming Convention table (~lines 437-457) to `skills/subagent-driven-development/references/report-naming-convention.md` and replace inline with a reference. This saves ~120 words. Net: ~185 words freed, sufficient for the ~195-word addition.

Verify after extraction:
```bash
wc -w skills/subagent-driven-development/SKILL.md
```
Expected: Under 4850 words (leaving headroom).

- [ ] **Step 1: Add Step 2b to Plan Ingestion**

After Step 2 ("Extract Contract Constraints", ~line 165) and before Step 3 ("Read source files"), insert:

```markdown
**Step 2b: Extract Shared Constants.**
If the plan includes a Shared Constants section, copy it verbatim into working memory. This section will be injected into every implementer subagent dispatch alongside Contract Constraints. Shared constants are import paths -- the subagent must import them, not redefine them. If the plan says "None", verify by scanning the File Map for files that define reusable constants (files named `constants.py`, `types.ts`, `config.py`, etc.).
```

- [ ] **Step 2: Add Shared Constants Passthrough section**

After the existing "Contract Constraints Passthrough" section (~line 260) and before "Context Budget Management", insert:

```markdown
## Shared Constants Passthrough

When dispatching each implementer subagent, include the plan's Shared Constants section in the subagent prompt, along with this note:

> "These constants are defined in the codebase. Import them -- do not redefine, hardcode, or approximate them. If you need a constant not listed here, check the source files for existing definitions before creating a new one. If no existing constant fits, report DONE_WITH_CONCERNS so the controller can evaluate whether a new constant should be added to a shared location."

Subagents working on isolated tasks will encounter values they need (account types, status codes, category lists). Without this passthrough, they hardcode them. With it, they import from the canonical source. The difference is invisible during implementation but catastrophic when the constant changes.
```

- [ ] **Step 3: Verify skill regression**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```
Expected: 122 checks PASS (or check count +/- if the size check triggers a warning)

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/SKILL.md
git commit -m "feat: Add Shared Constants ingestion step and passthrough to SDD skill"
```

---

### Task 3: Add Shared Constants Section to Implementer Prompt Template

**Files:**
- Modify: `skills/subagent-driven-development/implementer-prompt.md` (~line 31, after Source Files)

**Context:** The implementer prompt template currently has Contract Constraints and Source Files sections. We add a Shared Constants section between Source Files and Subdirectory CLAUDE.md Files. This is what the subagent actually sees -- the controller fills it in from the plan's Shared Constants field (extracted in Task 2).

- [ ] **Step 1: Add Shared Constants section**

In `implementer-prompt.md`, after the Source Files section (ends ~line 44) and before the "Subdirectory CLAUDE.md Files" section (starts ~line 46), insert:

```markdown
    ## Shared Constants

    [CONTROLLER: Insert the Shared Constants from the plan header here.
     If plan has no Shared Constants, write "None — no shared constants for this task."]

    These constants are defined in the codebase. Import them -- do not redefine,
    hardcode, or approximate them. If you need a constant not listed here, check
    the source files for existing definitions before creating a new one. If no
    existing constant fits, report DONE_WITH_CONCERNS and explain what you need --
    the controller will evaluate whether to add it to a shared location.

    Hardcoding values that exist as constants is a plan violation. Prior incident:
    an agent hardcoded ["credit_card", "line_of_credit"] instead of importing
    LIABILITY_TYPES, missing "loan". When the constant was updated, the frontend
    copy was silently wrong.
```

Note: Preserve the 4-space indentation to match the surrounding template content (the entire prompt is inside a code block).

- [ ] **Step 2: Add to Contract Compliance self-review checklist**

In the "Contract Compliance" section of the self-review (~line 140), add a bullet:

```markdown
    - Did I import all Shared Constants listed above, or did I redefine any of them?
      If I defined a local array, object, or enum that overlaps with a Shared Constant,
      replace it with an import.
```

- [ ] **Step 3: Verify skill regression**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add skills/subagent-driven-development/implementer-prompt.md
git commit -m "feat: Add Shared Constants section to implementer prompt template"
```

---

### Task 4: Add Import Assertion Step to Task 0 Template

**Files:**
- Modify: `skills/writing-plans/references/task-0-template.md` (add Step 5.5 between Steps 5 and 6)

**Context:** The current Task 0 template creates fixture files and verifies their shape matches the source contract. But fixtures can drift from both the spec and the code. The fix: add a step that writes assertions importing values from the Python source code and comparing against the fixture. This closes the loop between fixture, spec, and live code.

- [ ] **Step 1: Add import assertion step**

In `task-0-template.md`, after Step 5 ("Run and verify", ends ~line 53) and before Step 6 ("Commit", starts ~line 55), insert:

```markdown
- [ ] **Step 5b: Write import assertions**
  For every constant, type enumeration, or canonical value list in the contract,
  write an assertion that imports the value from the source code and compares it
  against the fixture. This ensures the fixture stays anchored to what the code
  actually uses -- not what the plan described.

  ```python
  from app.constants import VALID_ACCOUNT_TYPES  # adjust import path

  def test_fixture_matches_code_constants():
      """Fixture account types must match the canonical code constant."""
      with open("tests/fixtures/<feature>/contract_samples.json") as f:
          sample = json.load(f)
      # Fixture values must be a subset of (or equal to) the code constant
      assert set(sample["account_types"]) == set(VALID_ACCOUNT_TYPES), (
          f"Fixture has {sample['account_types']} but code defines {VALID_ACCOUNT_TYPES}"
      )
  ```

  **Why both fixture tests and import assertions:**
  - Fixture tests (Step 3) verify the shape is correct: required fields exist, types match.
  - Import assertions (this step) verify the values are current: the fixture agrees with
    what the code actually defines.
  - A fixture that passes shape tests but fails import assertions means the fixture was
    written from the spec (or plan) but the code has since diverged. This is exactly the
    drift that causes silent bugs.

  Write one import assertion per constant or enumeration in the contract. If the contract
  has no constants (only field shapes), this step produces no assertions -- note "N/A --
  no enumerable constants in contract" and proceed.
```

- [ ] **Step 2: Update Step 5 to reference the new step**

In the existing Step 5 text (~line 51), change:
```
**Do not proceed to Task 1 until this test passes.**
```
To:
```
**Do not proceed to Step 5b until this test passes.**
```

- [ ] **Step 3: Update Step 6 to include new test file**

In Step 6's git add command (~line 57), the commit already covers `tests/unit/test_<feature>_contracts.py` which is where the import assertions would go (same file as Step 3's contract tests). No change needed unless the import assertions go in a separate file. Keep in same file -- they're all contract verification.

- [ ] **Step 4: Verify skill regression**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/writing-plans/references/task-0-template.md
git commit -m "feat: Add import assertion step to Task 0 contract verification template"
```

---

### Task 5: Add Fix Complexity Gate to Systematic Debugging Skill

**Files:**
- Modify: `skills/systematic-debugging/SKILL.md` (Phase 4, before Step 1)

**Context:** When the user reports a bug mid-session, the agent fixes it inline. Principle #6 says "fix the architecture, not just the symptom." The current debugging skill has "If 3+ fixes failed, question architecture" (Phase 4, Step 5) but nothing that forces architectural evaluation BEFORE the first fix. The Fix Complexity Gate inserts a classification step between diagnosis (Phase 3) and implementation (Phase 4).

- [ ] **Step 1: Add Fix Complexity Gate section**

In `skills/systematic-debugging/SKILL.md`, at the beginning of Phase 4 ("Implementation"), between the bold subheading "Fix the root cause, not the symptom:" (~line 173) and Step 1 "Create Failing Test Case" (~line 175), insert:

```markdown
**Before implementing any fix, classify its complexity:**

| Classification | Criteria | Action |
|---|---|---|
| **Point fix** | Bug is in the logic, not the structure. Wrong value, off-by-one, missing condition. Fix changes 1-2 lines in one location. | Proceed to Step 1 below. |
| **Structural fix** | Bug reveals duplication, missing abstraction, or wrong separation of concerns. The same class of bug could recur elsewhere. Fix requires changes across multiple locations or introduces a new pattern. | STOP. Invoke `superpowers:brainstorming` before implementing. The fix needs design, not just code. |

**Write the classification before proceeding:**
```
Fix type: [point | structural]
Rationale: [one sentence explaining why]
```

**Examples:**
- "Fix type: point. Rationale: Missing `null` check on optional field before accessing `.length`." -> Proceed.
- "Fix type: structural. Rationale: `get_summary()` reimplements `compute_balance_to_date()` instead of calling it -- two copies of balance logic will diverge." -> Brainstorm first.
- "Fix type: structural. Rationale: `LIABILITY_TYPES` is hardcoded in 3 frontend files instead of imported from a shared constant." -> Brainstorm first.

**If uncertain:** Default to structural. A point fix wrongly classified as structural costs 15 minutes of brainstorming. A structural fix wrongly classified as point ships technical debt that compounds across future changes.
```

- [ ] **Step 2: Add Fix Complexity to Red Flags section**

At the end of the "Red Flags" bullet list (~line 230, after the last bullet), add:

```markdown
- "It's just a quick fix" (without classifying point vs structural)
- Fixing a symptom when the same pattern exists in multiple locations
```

- [ ] **Step 3: Verify skill regression**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```
Expected: PASS (check that systematic-debugging SKILL.md stays under 5000 words)

- [ ] **Step 4: Commit**

```bash
git add skills/systematic-debugging/SKILL.md
git commit -m "feat: Add Fix Complexity Gate to systematic debugging skill"
```

---

### Task 6: Documentation Update and Verification

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/ARaymond-customization-manifest.md`
- Read: All modified files for verification

- [ ] **Step 1: Run all test suites**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/ARaymond-installation/verify-symlink-install.sh
.venv/bin/python3 -m pytest tests/unit/ -v
```
Expected: All pass. Note any new check counts.

- [ ] **Step 2: Update CLAUDE.md**

Add a new section or update existing documentation:
- Note the Shared Constants Passthrough as a new ingestion step in SDD
- Note the import assertion step in Task 0
- Note the Fix Complexity Gate in systematic-debugging

- [ ] **Step 3: Update customization manifest**

Update `docs/ARaymond-customization-manifest.md` to document the three new additions with their file paths and rationale.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/ARaymond-customization-manifest.md
git commit -m "docs: Document subagent context improvements"
```

---

## Acceptance Criteria

1. **Plan header template** in writing-plans SKILL.md includes `**Shared Constants:**` field
2. **SDD SKILL.md** has Step 2b (Extract Shared Constants) in Plan Ingestion and a Shared Constants Passthrough section
3. **Implementer prompt** has a Shared Constants section with import-not-redefine instructions and prior incident reference
4. **Task 0 template** has Step 5b (import assertions) that verifies fixtures against live code imports
5. **Systematic debugging** has Fix Complexity Gate at the start of Phase 4 with point/structural classification
6. All 3 test suites pass (skill regression, installation, unit tests)
7. Skill word counts remain under 5000 words (SDD SKILL.md is at 5018 pre-extraction -- Task 2 Step 0 extracts ~185 words to references/, then adds ~195 words)
