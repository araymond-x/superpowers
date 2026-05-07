---
schema_version: 1
feature_archetype: migration
source_contracts: "docs/handoffs/2026-05-07-general-purpose-migration/README.md"
shared_constants: []
pattern_references: []
tasks:
  - {id: 0, title: "Contract Verification"}
  - {id: 1, title: "Update test suites for post-migration state", depends_on: [0]}
  - {id: 2, title: "Add Needs Context + reflection to code-reviewer.md template", depends_on: [1]}
  - {id: 3, title: "Migrate dispatch type to general-purpose", depends_on: [2]}
  - {id: 4, title: "Update CLAUDE.md", depends_on: [3]}
  - {id: 5, title: "Update customization manifest", depends_on: [4]}
  - {id: 6, title: "Obsolescence Verification", depends_on: [5]}
---

# Code Reviewer Agent Migration Implementation Plan

> Invoke `superpowers:subagent-driven-development` or `superpowers:executing-plans` before implementing.

**Goal:** Migrate fork from `superpowers-code-reviewer` to upstream's `general-purpose` task type, preserving two fork-only behaviors (Needs Context severity, pre-writing reflection) by promoting them into the inline `code-reviewer.md` template.

**Source Contracts:** `docs/handoffs/2026-05-07-general-purpose-migration/README.md` (accepted; see `handoff-acceptance-report.md` in feature dir).

**Feature Archetype:** Migration

**Contract Constraints:**
- `**Needs Context**` (Calibration bullet, verbatim per handoff) must appear in `skills/requesting-code-review/code-reviewer.md` post-migration.
- `Before writing findings, reflect on whether your assessment accounts for the full context of the change.` must appear in the same file before the Output Format section.
- `superpowers-code-reviewer` must NOT appear in any file under `skills/`, `agents/`, or in `CLAUDE.md` post-migration.
- `Task tool (general-purpose):` must appear at line 10 of `skills/subagent-driven-development/code-quality-reviewer-prompt.md`.
- Dead code findings remain BLOCKING in `code-quality-reviewer-prompt.md` (do NOT reclassify to Minor).
- `[NEEDS_CONTEXT]` label and `IMPLEMENTER_REPORT` placeholder remain in `code-quality-reviewer-prompt.md`.

**Code Footprint** (full table below in File Map section): 7 files modified, 2 deletions, hooks untouched.

**Architecture:** Surgical text-migration across 7 in-repo files plus a user-side symlink. The behavioral delta lives only in `agents/code-reviewer.md`; we copy it into the prompt template, change 4 dispatch-type strings, then delete the agent file. Tests are inverted (assert ABSENT instead of PRESENT) so a future regression that re-introduces the named agent fails loudly.

**Tech Stack:** Markdown skill files, Bash test scripts, Python regression validator. No runtime application code touched.

**Shared Constants:** None — only text edits.

**Pattern References:**
- `tests/ARaymond-skill-regression/validate-all-skills.py:755` (`check_critical_fixes`) — append migration invariants, follow existing `check_pass`/`check_fail` style.
- `tests/ARaymond-installation/verify-symlink-install.sh:304-344` (`Cross-Skill References`) — invert PRESENT-style assertions to ABSENT.
- `skills/requesting-code-review/code-reviewer.md:65-74` (existing Calibration) — match 4-space indent + bullet style when adding `**Needs Context**`.

## Code Footprint

| Category | File | Action |
|----------|------|--------|
| Modified | `skills/requesting-code-review/code-reviewer.md` | Add `**Needs Context**` + reflection step |
| Modified | `skills/requesting-code-review/SKILL.md` | 3 dispatch-string replacements (lines 8, 34, 58) |
| Modified | `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | 1 dispatch replacement (line 10) |
| Modified | `tests/ARaymond-installation/verify-symlink-install.sh` | Invert agent-symlink + 2 cross-skill-ref assertions |
| Modified | `tests/ARaymond-skill-regression/validate-all-skills.py` | Append migration invariants to `check_critical_fixes` |
| Modified | `CLAUDE.md` | Drop agent symlink + 3 fork-customization bullets; invert Verify Installation check |
| Modified | `docs/ARaymond-customization-manifest.md` | Drop agent rows from architecture/conflict/sync tables |
| Obsolete | `agents/code-reviewer.md` | `git rm` after Task 2 promotes behaviors |
| Obsolete | `~/.claude/agents/superpowers-code-reviewer.md` | `rm` (symlink, outside repo) |
| Retained | All hook scripts | Hooks reference file names, not agent types |

---

## File Map

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 0 | `docs/imp-plans/2026-05-07-code-reviewer-agent-migration/contract-verification.sh` | `docs/handoffs/2026-05-07-general-purpose-migration/samples/current-state.json`, `agents/code-reviewer.md`, `skills/requesting-code-review/SKILL.md`, `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | — |
| Task 1 | `tests/ARaymond-skill-regression/validate-all-skills.py`, `tests/ARaymond-installation/verify-symlink-install.sh` | `docs/handoffs/2026-05-07-general-purpose-migration/README.md` | Task 0 |
| Task 2 | `skills/requesting-code-review/code-reviewer.md` | `agents/code-reviewer.md` (verbatim source for the two behaviors) | Task 1 |
| Task 3 | `skills/requesting-code-review/SKILL.md`, `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | — | Task 2 |
| Task 4 | `CLAUDE.md` | — | Task 3 |
| Task 5 | `docs/ARaymond-customization-manifest.md` | — | Task 4 |
| Task 6 | `agents/code-reviewer.md` (delete), `~/.claude/agents/superpowers-code-reviewer.md` (delete, outside repo) | All previously modified files (final cross-grep) | Task 5 |

**Rules honored:**
- No two tasks write the same file (Task 1 owns both test files because they encode the same migration invariants and must land together to keep the suites coherent; Task 3 owns both dispatch-string sites for the same reason).
- All tasks are serialized via `depends_on`; no parallel execution intended.

**Test-state expectations:** Task 1 commits suites in RED state (tests describe end state, not reached yet). Task 2 turns the 2 behavior invariants GREEN; Task 3 turns the 2 dispatch invariants + 2 install cross-skill checks GREEN; Task 6 turns the agent-symlink absence check GREEN. Intermediate failures are EXPECTED — do NOT alter tests mid-flight.

---

## Open Decisions (resolved in this plan)

| # | Decision | Resolution | Where applied |
|---|----------|-----------|---------------|
| 1 | `verify-symlink-install.sh` agent-symlink check after symlink removal | Invert the assertion to require the symlink to be ABSENT (so a future regression that re-introduces it fails). Check count drops by ~5 in the agent-symlink section (the replacement is leaner than the current branchy logic — current section has 7 pass/fail/warn calls, replacement has 2 + 2 for the new repo-side absence check); Task 4 Step 5b reconciles CLAUDE.md's quoted check count after running the suite. The 2 cross-skill reference checks also invert (require ABSENT instead of PRESENT). | Task 1 (Step 3–5) |
| 2 | CLAUDE.md "Verify Installation" agent-symlink check | Replace `ls -la ~/.claude/agents/superpowers-code-reviewer.md` with an absence check that prints a clear "STALE — please remove" message if the symlink reappears. | Task 4 (Step 4) |

---

## Tasks

### Task 0: Contract Verification

**Files:**
- Create: `docs/imp-plans/2026-05-07-code-reviewer-agent-migration/contract-verification.py`

**Purpose:** Confirm the live filesystem matches the `current` snapshot in `samples/current-state.json`. If anything has drifted, abort before any edits start.

- [x] **Step 1: Write the verification script**

Create `docs/imp-plans/2026-05-07-code-reviewer-agent-migration/contract-verification.py`:

```python
#!/usr/bin/env python3
"""Pre-migration contract anchor: every `current` string in the handoff
snapshot must still appear at its documented location.
Exit 0 = matches; exit 1 = drift."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "docs/handoffs/2026-05-07-general-purpose-migration/samples/current-state.json"

data = json.loads(FIXTURE.read_text())
failed = 0

for r in data["references_to_change"]:
    line = (ROOT / r["file"]).read_text().splitlines()[r["line"] - 1]
    if r["current"] in line:
        print(f"PASS: {r['file']}:{r['line']}")
    else:
        print(f"FAIL: {r['file']}:{r['line']}\n  expected: {r['current']}\n  actual:   {line}")
        failed += 1

for b in data["behaviors_to_add_to_code_reviewer_template"]:
    text = (ROOT / b["source_file"]).read_text()
    if b["verbatim"] in text:
        print(f"PASS: {b['source_file']} contains '{b['behavior']}' verbatim")
    else:
        print(f"FAIL: {b['source_file']} missing '{b['behavior']}'")
        failed += 1

print(f"\nSTATUS: {'FAILED' if failed else 'PASSED'} ({failed} drifts)")
sys.exit(1 if failed else 0)
```

- [x] **Step 2: Run it**

```bash
python3 docs/imp-plans/2026-05-07-code-reviewer-agent-migration/contract-verification.py
```

Expected: `STATUS: PASSED (0 drifts)` and exit code 0. If FAILED: STOP. The handoff is stale and must be regenerated before the migration proceeds.

Note for the implementer: `skills/requesting-code-review/code-reviewer.md` line 8 already reads `Task tool (general-purpose):` — that's pre-existing state from the v5.1.0 upstream merge, not part of this migration. The migration touches `code-quality-reviewer-prompt.md` line 10 and `requesting-code-review/SKILL.md` lines 8/34/58, NOT `code-reviewer.md` line 8. Don't be misled by the file-name overlap.

- [x] **Step 3: Commit**

```bash
git add docs/imp-plans/2026-05-07-code-reviewer-agent-migration/contract-verification.py
git commit -m "feat(plan): add contract verification for code-reviewer migration

Anchors the migration against samples/current-state.json. Run before any
edits start; FAIL means the handoff is stale.

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 1: Update test suites for post-migration state

**Files:**
- Modify: `tests/ARaymond-skill-regression/validate-all-skills.py` — add migration-invariant assertions in `check_critical_fixes`
- Modify: `tests/ARaymond-installation/verify-symlink-install.sh` — invert 3 assertions, add behavior-presence checks

**Pattern References:**
- `tests/ARaymond-skill-regression/validate-all-skills.py:755` (`check_critical_fixes`) — append new checks at the end of this function, following the existing `check_pass`/`check_fail` style.
- `tests/ARaymond-installation/verify-symlink-install.sh:304-344` (`Cross-Skill References` section) — replace existing PRESENT-style `grep -q ... && pass || fail` blocks with ABSENT-style `! grep -q ... && pass || fail` blocks, preserving the section structure and comment style.

**Purpose:** Encode the migration's end state as test invariants BEFORE any source changes. After this commit, both suites FAIL — that is the intended TDD "red" state. Subsequent tasks turn checks green one at a time.

- [x] **Step 1: Add migration invariants to `check_critical_fixes` in validate-all-skills.py**

Open `tests/ARaymond-skill-regression/validate-all-skills.py`. At the end of the `check_critical_fixes` function (before the next `def`), append:

```python
    # Migration invariants (2026-05-07): post-migration the agent file is
    # gone, so the template must carry the two fork behaviors AND no skill
    # file may still reference the named agent.
    template_path = os.path.join(skills_dir, "requesting-code-review/code-reviewer.md")
    template = read_file(template_path)
    if template is not None:
        # Note: needles are substrings short enough to survive line-wrap in the
        # template form (the reflection paragraph is wrapped at "accounts for\n
        # the full context" — a single-line needle would never match).
        for needle, label in [
            ("**Needs Context**", "Needs Context severity category"),
            ("reflect on whether your assessment accounts for", "pre-writing reflection step"),
        ]:
            if needle in template:
                check_pass(CATEGORY_6, "code-reviewer.md template: contains {}".format(label))
            else:
                check_fail(CATEGORY_6, "code-reviewer.md template: missing {} — fork behavior dropped".format(label))

    for rel in ["requesting-code-review/SKILL.md",
                "subagent-driven-development/code-quality-reviewer-prompt.md"]:
        content = read_file(os.path.join(skills_dir, rel))
        if content is None:
            continue
        if "superpowers-code-reviewer" in content:
            check_fail(CATEGORY_6, "{}: still references 'superpowers-code-reviewer' — agent migration incomplete".format(rel))
        else:
            check_pass(CATEGORY_6, "{}: general-purpose migration complete (no named-agent reference)".format(rel))
```

- [x] **Step 2: Run regression and confirm new failures**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

Expected: 3 new FAIL lines (Needs Context missing, reflection step missing, requesting-code-review/SKILL.md still references the named agent — and the same for code-quality-reviewer-prompt.md, so likely 4 fails total). Overall STATUS: FAILED. This is correct — these failures are the migration's "red" tests.

- [x] **Step 3: Update install test — invert agent symlink check**

Open `tests/ARaymond-installation/verify-symlink-install.sh`. Replace the entire `# ─── 3. Agent Symlink ───` block (currently lines 186–210) with:

```bash
# ─── 3. Agent Symlink (must be ABSENT post-migration) ─────────────────────────

section "Agent (post-migration: must be absent)"

# After the general-purpose migration the named agent symlink should be gone.
# If it reappears, a regression has re-introduced the fork's old named-agent
# pattern — fail loudly so it's caught immediately.
if [[ -e "$AGENT_FILE" ]]; then
  if [[ -L "$AGENT_FILE" ]]; then
    fail "Agent symlink still present at $AGENT_FILE — migration regression: the fork moved to general-purpose dispatch on 2026-05-07. Run: rm $AGENT_FILE"
  else
    fail "Agent file still present at $AGENT_FILE (not a symlink) — unexpected regression: investigate before deleting"
  fi
else
  pass "Agent symlink correctly absent (post-general-purpose-migration state)"
fi

# Repo-side agents/code-reviewer.md should also be gone.
if [[ -e "$REPO_ROOT/agents/code-reviewer.md" ]]; then
  fail "agents/code-reviewer.md still present in repo — should have been git rm'd during migration"
else
  pass "agents/code-reviewer.md correctly absent from repo"
fi
```

- [x] **Step 4: Update install test — invert cross-skill reference checks**

In the same file, replace the two existing `superpowers-code-reviewer`-presence checks in the `# ─── 5. Cross-Skill References ───` section (currently lines 332–344) with absence assertions:

```bash
# requesting-code-review → must NOT reference superpowers-code-reviewer
# (post-migration: dispatch type is general-purpose, agent file deleted)
if grep -q "superpowers-code-reviewer" "$SKILLS_DIR/requesting-code-review/SKILL.md" 2>/dev/null; then
  fail "requesting-code-review still references 'superpowers-code-reviewer' — migration regression"
else
  pass "requesting-code-review correctly uses general-purpose (no named-agent reference)"
fi

# SDD code-quality-reviewer-prompt → must NOT reference superpowers-code-reviewer
if grep -q "superpowers-code-reviewer" "$SKILLS_DIR/subagent-driven-development/code-quality-reviewer-prompt.md" 2>/dev/null; then
  fail "SDD code-quality-reviewer-prompt still references 'superpowers-code-reviewer' — migration regression"
else
  pass "SDD code-quality-reviewer-prompt correctly uses general-purpose (no named-agent reference)"
fi
```

- [x] **Step 5: Run install test and confirm new failures**

```bash
bash tests/ARaymond-installation/verify-symlink-install.sh
```

Expected: STATUS: FAILED. The agent file/symlink still exist (Task 6 removes them) and the cross-skill references still exist (Task 3 removes them). The new assertions correctly identify the work that remains. This is the migration's "red" state for the install suite.

- [x] **Step 6: Commit**

```bash
git add tests/ARaymond-skill-regression/validate-all-skills.py tests/ARaymond-installation/verify-symlink-install.sh
git commit -m "test: assert post-migration state for code-reviewer agent removal

Adds migration invariants to the regression suite:
  - **Needs Context** severity category present in code-reviewer.md template
  - Pre-writing reflection step present in code-reviewer.md template
  - 'superpowers-code-reviewer' absent from skills/requesting-code-review/SKILL.md
  - 'superpowers-code-reviewer' absent from SDD code-quality-reviewer-prompt.md

Inverts the install suite's agent-symlink check and 2 cross-skill reference
checks to require ABSENT instead of PRESENT (a future regression that
re-introduces the named agent will fail loudly).

Both suites are intentionally RED after this commit — Tasks 2-3 and Task 6
turn the failures green.

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 2: Add Needs Context category and reflection step to code-reviewer.md template

**Files:**
- Modify: `skills/requesting-code-review/code-reviewer.md`

**Pattern References:**
- `skills/requesting-code-review/code-reviewer.md:65-74` — existing Calibration section. Match its four-space indentation (the section sits inside a fenced ` ``` ` prompt block, so all bullets are indented 4 spaces) and its bullet style.

**Source for verbatim text:** Handoff README lines 113-130 (the structured target wording with bulleted severity list). Note: `agents/code-reviewer.md:39` uses an older em-dash phrasing — use the handoff target wording, NOT the agent file's literal text.

- [x] **Step 1: Insert the bulleted severity list and reflection paragraph between the existing prose and the "If you find…" paragraph**

Open `skills/requesting-code-review/code-reviewer.md`. Find the current Calibration block (line 65 `## Calibration` through line 74). The first paragraph (lines 67–69) and the closing two paragraphs (lines 71–74) stay UNCHANGED. Insert the bulleted severity list and reflection paragraph between line 69 and line 71. The full section after editing must read exactly:

```markdown
    ## Calibration

    Categorize issues by actual severity. Not everything is Critical.
    Acknowledge what was done well before listing issues — accurate praise
    helps the implementer trust the rest of the feedback.

    Issue severity categories:
    - **Critical** — bugs, security issues, data loss risks, broken functionality
    - **Important** — architecture problems, missing features, poor error handling
    - **Minor** — code style, optimization, documentation polish
    - **Needs Context** — finding may be valid but requires additional information
      to confirm severity; describe what context would resolve the uncertainty

    Before writing findings, reflect on whether your assessment accounts for
    the full context of the change.

    If you find significant deviations from the plan, flag them specifically
    so the implementer can confirm whether the deviation was intentional.
    If you find issues with the plan itself rather than the implementation,
    say so.
```

Note: The block sits inside a fenced ` ``` ` prompt template. Preserve the four-space indent on every line. The "If you find significant deviations…" paragraph already exists below — do not delete it; the bulleted severity list and reflection paragraph are inserted ABOVE it.

- [x] **Step 2: Run regression and confirm 2 invariants turn green**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

Expected: the 2 template invariants from Task 1 (Needs Context + reflection step) now PASS. The 2 dispatch-reference invariants still FAIL (Task 3 fixes them). Overall STATUS: still FAILED, but for fewer reasons.

- [x] **Step 3: Verify behavior count via grep (matches handoff verification step)**

```bash
grep -c "Needs Context\|reflect on whether" skills/requesting-code-review/code-reviewer.md
```

Expected: `2` (one match per behavior). If the count is higher, the section was duplicated — undo and retry.

- [x] **Step 4: Commit**

```bash
git add skills/requesting-code-review/code-reviewer.md
git commit -m "feat(code-reviewer): add Needs Context category and reflection step

Promotes the two fork-only reviewer behaviors from agents/code-reviewer.md
into the requesting-code-review prompt template. After this commit the
agent file is no longer the unique carrier of these behaviors — it can be
deleted in Task 6 once dispatch references are migrated.

  - **Needs Context** severity category (4th category alongside
    Critical/Important/Minor) — per handoff README target wording (lines 125-126)
  - Pre-writing reflection step before findings — per handoff target wording from
    agents/code-reviewer.md:49

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 3: Migrate dispatch type to general-purpose in 4 locations

**Files:**
- Modify: `skills/requesting-code-review/SKILL.md` (3 occurrences at lines 8, 34, 58)
- Modify: `skills/subagent-driven-development/code-quality-reviewer-prompt.md` (1 occurrence at line 10)

**Pattern References:** None — these are direct text replacements specified verbatim in the handoff (`docs/handoffs/2026-05-07-general-purpose-migration/samples/current-state.json`).

- [x] **Step 1: Edit `skills/requesting-code-review/SKILL.md` line 8**

Replace:
```
Dispatch superpowers-code-reviewer subagent to catch issues before they cascade.
```
with:
```
Dispatch a code reviewer subagent to catch issues before they cascade.
```

- [x] **Step 2: Edit `skills/requesting-code-review/SKILL.md` line 34**

Replace:
```
Use Task tool with superpowers-code-reviewer type, fill template at `code-reviewer.md`
```
with:
```
Use Task tool with general-purpose type, fill template at `code-reviewer.md`
```

- [x] **Step 3: Edit `skills/requesting-code-review/SKILL.md` line 58**

Replace:
```
[Dispatch superpowers-code-reviewer subagent]
```
with:
```
[Dispatch code reviewer subagent]
```

- [x] **Step 4: Edit `skills/subagent-driven-development/code-quality-reviewer-prompt.md` line 10**

Replace:
```
Task tool (superpowers-code-reviewer):
```
with:
```
Task tool (general-purpose):
```

- [x] **Step 5: Verify zero `superpowers-code-reviewer` references remain in the migrated files**

```bash
grep -n "superpowers-code-reviewer" skills/requesting-code-review/SKILL.md skills/subagent-driven-development/code-quality-reviewer-prompt.md
```

Expected: no output (exit code 1 from grep).

Note: `agents/code-reviewer.md` and `CLAUDE.md` and `docs/ARaymond-customization-manifest.md` still contain references — those are removed in Tasks 4, 5, 6 respectively.

- [x] **Step 6: Run regression and install suites**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/ARaymond-installation/verify-symlink-install.sh
```

Expected:
- Regression: 4 migration invariants from Task 1 now all PASS. Other categories unchanged. If category 6 was the only failing category, STATUS: PASSED. (Other unrelated FAILs would indicate an unintended side effect — investigate before continuing.)
- Install suite: the 2 inverted cross-skill ref checks now PASS. The agent-symlink absence check still FAILs (Task 6 fixes it). STATUS: still FAILED, expected.

- [x] **Step 7: Commit**

```bash
git add skills/requesting-code-review/SKILL.md skills/subagent-driven-development/code-quality-reviewer-prompt.md
git commit -m "refactor: dispatch code reviewer via general-purpose task type

Migrates 4 dispatch-type strings from 'superpowers-code-reviewer' (named
agent) to 'general-purpose' (upstream pattern). The inline code-reviewer.md
template carries the full reviewer instructions, so removing the named
agent does not change behavior — only how dispatches are wrapped.

  - skills/requesting-code-review/SKILL.md (3 occurrences)
  - skills/subagent-driven-development/code-quality-reviewer-prompt.md (1)

The two fork-only behaviors (Needs Context, reflection step) were
promoted into the template in Task 2, so the agent file (deleted in
Task 6) is now redundant.

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 4: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Pattern References:** None — straight documentation updates.

- [x] **Step 1: Update Installation Architecture section**

In `CLAUDE.md`, find the "Installation Architecture" section (around line 21). Delete the line that reads:

```
- Agent: `~/.claude/agents/superpowers-code-reviewer.md` → `./agents/code-reviewer.md`
```

(This is currently line 24; verify with `grep -n "Agent: \`~/.claude/agents" CLAUDE.md` before editing.)

- [x] **Step 2: Remove the Fork Customizations bullets that reference the named agent**

In the "Fork Customizations (preserve during upstream merge)" section (around line 27), delete these three lines:

```
- `agents/code-reviewer.md` — `name:` changed to `superpowers-code-reviewer`
- `skills/requesting-code-review/SKILL.md` — agent refs changed to `superpowers-code-reviewer`
- `skills/subagent-driven-development/code-quality-reviewer-prompt.md` — agent ref changed to `superpowers-code-reviewer`
```

If those three lines are the entire body of the "Fork Customizations" section, also delete the `## Fork Customizations (preserve during upstream merge)` heading itself — don't leave an empty section. (Verify by inspecting the next section header to confirm there are no other customizations remaining under it.)

- [x] **Step 3: Update the "Verify Installation" code block — replace agent symlink check with absence check**

In the "Verify Installation" section (around line 88), replace the block:

```bash
# Agent symlink intact
ls -la ~/.claude/agents/superpowers-code-reviewer.md
```

with:

```bash
# Agent symlink must be ABSENT (post-2026-05-07 general-purpose migration)
[ ! -e ~/.claude/agents/superpowers-code-reviewer.md ] \
  && echo "OK — agent symlink absent (correct post-migration state)" \
  || echo "STALE — agent symlink still present; run: rm ~/.claude/agents/superpowers-code-reviewer.md"
```

- [x] **Step 4: Update upstream-conflict-files note**

Find the "Known conflict files (always)" line (around line 70). Edit it to remove `agents/code-reviewer.md` from the list. The current line reads:

```
Known conflict files (always): `CLAUDE.md`, `agents/code-reviewer.md`, `skills/requesting-code-review/SKILL.md`, `skills/subagent-driven-development/code-quality-reviewer-prompt.md`
```

Replace with:

```
Known conflict files (always): `CLAUDE.md` (other historical conflict files were resolved by the 2026-05-07 general-purpose migration; see `docs/ARaymond-customization-manifest.md` Upstream Conflict Files for current state)
```

- [x] **Step 5: Update the Key Architecture Notes line about the formal agent**

Find the bullet that reads (around line 281):

```
- Only 1 formal agent exists (`code-reviewer.md`) — used for final whole-implementation review
```

Replace with:

```
- No formal agents are defined in this fork. Code review is dispatched as a `general-purpose` Task carrying the inline `skills/requesting-code-review/code-reviewer.md` template (migrated 2026-05-07 — see `docs/ARaymond-customization-manifest.md` Upstream Sync Log).
```

- [x] **Step 5b: Update the Testing quick-reference line**

Find the line in the "Testing" section (around line 119):

```
Quick reference: 4 test layers — regression (static, 139 checks), install (static, 105 checks), unit (pytest, 273 tests), behavior (API, ~15m). Structural PASS ≠ semantic PASS — run both static and behavioral tests for significant changes. Details below.
```

Update the regression count to reflect Task 1's added invariants. Run the regression suite first to get the exact post-migration count, then write that number into CLAUDE.md (replace `139 checks` with the actual count). The install count typically stays the same because Task 1 inverts assertions rather than adding/removing them — verify by running the install suite and replace `105 checks` only if the count changed.

- [x] **Step 6: Final verification grep**

```bash
grep -n "superpowers-code-reviewer\|agents/code-reviewer\.md" CLAUDE.md
```

Expected: no output. (If anything matches, re-read CLAUDE.md and clean it up.)

- [x] **Step 7: Run regression to confirm CLAUDE.md changes haven't broken anything**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

Expected: same green/red state as after Task 3 — no new failures.

- [x] **Step 8: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): remove named-agent references after general-purpose migration

  - Drop agent symlink line from Installation Architecture
  - Drop 3 Fork Customizations bullets (no longer applicable)
  - Replace 'agent symlink intact' check with absence assertion
  - Update Known conflict files note to reflect resolved conflicts
  - Update Key Architecture Notes — no formal agents remain in the fork

Resolves Open Decision 2 from the migration plan.

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 5: Update docs/ARaymond-customization-manifest.md

**Files:**
- Modify: `docs/ARaymond-customization-manifest.md`

**Pattern References:** None — straight documentation updates following the existing table styles.

- [x] **Step 1: Update Installation Architecture diagram (around line 18)**

Delete the line:
```
~/.claude/agents/superpowers-code-reviewer.md  → .../agents/code-reviewer.md
```

- [x] **Step 2: Delete the entire `## Step 2: Symlink Agent` section (around lines 54–67)**

Remove everything from the heading `## Step 2: Symlink Agent` through (and including) its trailing horizontal rule `---`. After deletion, "Step 3: Command Stubs" remains the next section. **Do not renumber subsequent steps** — Step 3 stays Step 3 (the numbers are historical references, and renumbering would break any external doc that links to "Step 4" etc.).

- [x] **Step 3: Update "Verify Complete Installation" code block (around line 237)**

Delete the lines:
```
# Agent symlink
ls -la ~/.claude/agents/superpowers-code-reviewer.md

```

(both the comment and the `ls` line — leave a single blank line between the previous block and the next `# Session-start hook` block).

- [x] **Step 4: Update Upstream Sync conflict-resolution table (around lines 263–278)**

Delete the 3 rows that reference the migrated files:

```
| `agents/code-reviewer.md` | `name: superpowers-code-reviewer` in frontmatter |
| `skills/requesting-code-review/SKILL.md` | `superpowers-code-reviewer` (3 occurrences) |
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | `superpowers-code-reviewer` (1 occurrence) |
```

For the `code-quality-reviewer-prompt.md` row, REPLACE rather than delete (it still has SDD-specific fork content beyond the agent ref):

```
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | All v0.1 fork improvements (dead code BLOCKING, [NEEDS_CONTEXT] label, IMPLEMENTER_REPORT placeholder, per-file SRP check, contract-constraint tracing) |
```

- [x] **Step 5: Update Skills Inventory note for `code-quality-reviewer-prompt.md` (around line 329)**

Find the table row in "Prompt Templates (8 active)":

```
| `subagent-driven-development/code-quality-reviewer-prompt.md` | SDD | Dispatched after spec review for code quality review | Dead code = BLOCKING (not Minor), implementer report placeholder `[CONTROLLER: paste full report]`, agent ref `superpowers-code-reviewer`, role statement |
```

Replace with:

```
| `subagent-driven-development/code-quality-reviewer-prompt.md` | SDD | Dispatched after spec review for code quality review | Dead code = BLOCKING (not Minor), implementer report placeholder `[CONTROLLER: paste full report]`, dispatch type `general-purpose` (post-2026-05-07 migration), role statement |
```

- [x] **Step 6: Update Upstream Conflict Files table (around lines 480–490)**

Delete the 3 rows referencing `agents/code-reviewer.md`, `skills/requesting-code-review/SKILL.md`, and the agent-ref portion of `skills/subagent-driven-development/code-quality-reviewer-prompt.md`. For the `code-quality-reviewer-prompt.md` row, replace the "Agent ref + prompt body" wording with just "Prompt body":

```
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | Prompt body | Keep fork v0.1 improvements (dead code BLOCKING, [NEEDS_CONTEXT], IMPLEMENTER_REPORT) |
```

- [x] **Step 7: Append migration entry to the Upstream Sync Log**

In the "Upstream Sync Log" table, replace the existing 2026-05-07 row's "Cherry-picks" cell. Currently it says "rejected agent deletion (kept superpowers-code-reviewer)". Update it to:

```
| 2026-05-07 | v5.1.0 (`f2cbfbe`) | 3 | 8 files (CLAUDE.md, agents/code-reviewer.md, using-git-worktrees, finishing-a-development-branch, requesting-code-review, subagent-driven-development + code-quality-reviewer-prompt, executing-plans) | Accepted upstream's using-git-worktrees full rewrite + re-added NEW SESSION REQUIRED block; accepted finishing-a-development-branch env detection + kept Step 7 post-completion cleanup; deferred agent deletion at merge time, then completed it on 2026-05-07 via `code-reviewer-agent-migration` (Needs Context + reflection step promoted to template); absorbed "continuous execution" paragraph in SDD |
```

- [x] **Step 8: Final verification grep**

```bash
grep -n "superpowers-code-reviewer\|agents/code-reviewer\.md" docs/ARaymond-customization-manifest.md
```

Expected: no output. If anything matches, clean it up before committing.

- [x] **Step 9: Run regression**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

Expected: same state as after Task 3 (no new failures introduced by docs changes).

- [x] **Step 10: Commit**

```bash
git add docs/ARaymond-customization-manifest.md
git commit -m "docs(manifest): drop named-agent rows after general-purpose migration

  - Remove agent symlink from Installation Architecture diagram
  - Remove Step 2 (Symlink Agent) — no longer applicable
  - Remove agent symlink check from Verify Complete Installation
  - Drop 3 conflict-resolution rows for migrated files
  - Update code-quality-reviewer-prompt.md row to dispatch type general-purpose
  - Update Upstream Sync Log entry for 2026-05-07 to reflect completion

Prompted by Aaron; Co-Authored by Claude"
```

---

### Task 6: Obsolescence Verification

**Files:**
- Delete: `agents/code-reviewer.md` (in repo)
- Delete: `~/.claude/agents/superpowers-code-reviewer.md` (user-side symlink, outside repo)

**Purpose:** Confirm zero remaining consumers, remove the dead file + symlink, run full test suite green.

- [x] **Step 1: Final cross-cutting grep** (found 2 extra refs beyond plan scope — cleaned up, logged in deviations.md)

```bash
grep -rn "superpowers-code-reviewer" CLAUDE.md agents/ skills/ docs/ARaymond-customization-manifest.md tests/ARaymond-installation/ tests/ARaymond-skill-regression/
```

Expected: no output. If any hits, STOP and clean up. If hits appear in `tests/unit/` or `hooks/`, document in DEVIATIONS.md (those would require additional migration outside this plan's scope).

- [x] **Step 2: Delete the agent file**

```bash
git rm agents/code-reviewer.md
rmdir agents/ 2>/dev/null || true   # only succeeds if empty; safe
```

- [x] **Step 3: Remove the user-side symlink**

Outside version control — run on the developer's machine:

```bash
[[ -e ~/.claude/agents/superpowers-code-reviewer.md ]] && rm ~/.claude/agents/superpowers-code-reviewer.md && echo "removed" || echo "already clean"
```

- [x] **Step 4: Run all three test suites**

```bash
python3 tests/ARaymond-skill-regression/validate-all-skills.py
bash tests/ARaymond-installation/verify-symlink-install.sh
.venv/bin/python3 -m pytest tests/unit/ -v
```

Expected: regression PASSED (~143 checks); install PASSED (inverted assertions green); unit 273/273.

- [x] **Step 5: Final clean-state grep**

```bash
grep -rn "superpowers-code-reviewer" CLAUDE.md skills/ docs/ARaymond-customization-manifest.md tests/ARaymond-installation/ tests/ARaymond-skill-regression/ 2>/dev/null || echo "CLEAN"
```

Expected: `CLEAN`.

- [x] **Step 6: Smoke-test the contract-verification script**

```bash
python3 docs/imp-plans/2026-05-07-code-reviewer-agent-migration/contract-verification.py || echo "EXPECTED FAILURE — migration ran"
```

Expected: FAIL (source files migrated, current strings no longer match). This is correct — the script was a pre-migration anchor; failing now proves the migration ran. Do NOT "fix" it; leave it as a historical artifact.

- [x] **Step 7: Commit**

```bash
git commit -m "feat: complete general-purpose migration; delete superpowers-code-reviewer agent

Removes agents/code-reviewer.md from the repo. The two fork-only behaviors
(Needs Context, reflection step) were promoted into the inline template in
Task 2; the 4 dispatch references were migrated in Task 3. The named agent
is now redundant.

  - git rm agents/code-reviewer.md
  - rm ~/.claude/agents/superpowers-code-reviewer.md (user-side, by hand)

Test status:
  - regression: PASSED (~143 checks, +4 migration invariants)
  - install:    PASSED (3 inverted assertions now green)
  - unit:       PASSED (273/273)

Closes the deferred agent-deletion item from the 2026-05-07 v5.1.0 merge.

Prompted by Aaron; Co-Authored by Claude"
```

---

## Acceptance Criteria

All of the following must hold:
1. `grep -r "superpowers-code-reviewer" CLAUDE.md skills/ docs/ARaymond-customization-manifest.md tests/ARaymond-{installation,skill-regression}/` → no output.
2. `agents/code-reviewer.md` is gone from the repo; `~/.claude/agents/superpowers-code-reviewer.md` is gone from the dev machine.
3. `skills/requesting-code-review/code-reviewer.md` contains both `**Needs Context**` and the reflection step (`grep -c` ≥ 2).
4. `skills/subagent-driven-development/code-quality-reviewer-prompt.md` line 10 = `Task tool (general-purpose):`; file retains 5 SDD behaviors (dead code BLOCKING, `[NEEDS_CONTEXT]`, `IMPLEMENTER_REPORT`, per-file SRP, contract tracing).
5. All three suites PASSED: regression, install, unit (273/273).

## Out of Scope

`contract-verification.py` cleanup; historical refs in `docs/external-references/`, session logs, commits; enforcement hooks (file-name based); `code-reviewer.md` template structure outside Calibration; renumbering manifest Step headings.
