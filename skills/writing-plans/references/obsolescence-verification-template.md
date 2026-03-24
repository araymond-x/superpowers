# Obsolescence Verification Task Template

> Part of the writing-plans skill. Referenced from SKILL.md.

### Task N: Obsolescence Verification

**Files:**
- Read: all files listed as "Obsolete" in Code Footprint
- Read: all files listed in "Dependencies to Verify" column

- [ ] **Step 1: Grep for each obsolete function/component**
  For each item marked "Obsolete" in the Code Footprint:
  ```bash
  grep -rn "functionName" src/ --include="*.ts" --include="*.tsx" --include="*.py"
  ```
  List all call sites found.

- [ ] **Step 2: Verify no remaining consumers**
  For each call site:
  - Is it in code that this plan creates? (OK — the new code replaces the call)
  - Is it in code that this plan does NOT touch? (BLOCKER — external consumer still needs it)
  - Is it in a test file? (Update or remove the test)

- [ ] **Step 3: Remove or defer with explicit tracking**
  For each obsolete item:
  - If no remaining consumers: remove the code and its tests
  - If remaining consumers exist: log to DEVIATIONS.md as "Deferred Removal" with
    the specific consumers that block removal
  - Do NOT leave dead code undocumented

- [ ] **Step 4: Final grep audit**
  After all removals, re-grep to confirm no stale references remain:
  ```bash
  grep -rn "removedFunctionName" src/ tests/
  ```
  Expected: zero results for each removed item

- [ ] **Step 5: Commit**
  ```bash
  git add -u
  git commit -m "refactor: remove obsolete code per feature footprint"
  ```
