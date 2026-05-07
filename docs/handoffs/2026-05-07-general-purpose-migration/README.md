---
schema_version: 1
package_name: "general-purpose-migration"
feeds_into: "writing-plans"
one_sentence_purpose: "Migrate the superpowers fork from a named superpowers-code-reviewer agent to the general-purpose task type, preserving all fork-specific reviewer behaviors in the inline prompt template."
contract_constraints:
  - name: "needs_context_category"
    kind: "string"
    format_hint: "Must appear verbatim in code-reviewer.md Calibration section"
    nullable: false
  - name: "reflection_step"
    kind: "string"
    format_hint: "Must appear in code-reviewer.md before the output format section"
    nullable: false
  - name: "dead_code_blocking"
    kind: "string"
    format_hint: "Must remain BLOCKING (not Minor) in code-quality-reviewer-prompt.md"
    nullable: false
samples:
  - path: "samples/current-state.json"
    description: "Current inventory of all superpowers-code-reviewer references and their required post-migration state"
---

# General-Purpose Migration Handoff

Migrate the superpowers fork from a named `superpowers-code-reviewer` agent to upstream's `general-purpose` task type, preserving all fork-specific reviewer behaviors in the inline prompt template.

## Contract Constraints

These are non-negotiable facts. Every plan, implementation, and test must honor them.

**Behaviors that MUST survive migration (currently in `agents/code-reviewer.md` only):**
- `**Needs Context**` issue severity category — verbatim: *"finding may be valid but requires additional information to confirm — describe what context would resolve the uncertainty"* — must be added to `code-reviewer.md` Calibration section
- Pre-writing reflection step — verbatim: *"Before writing findings, reflect on whether your assessment accounts for the full context of the change"* — must be added to `code-reviewer.md` before the Output Format section

**SDD-specific behaviors in `code-quality-reviewer-prompt.md` (already separate — MUST NOT be lost):**
- Dead code findings are **blocking** — must be resolved (or justified in DEVIATIONS.md) before a task is marked complete. Do NOT reclassify as Minor.
- `[NEEDS_CONTEXT]` label for findings where severity requires additional context
- `IMPLEMENTER_REPORT` passthrough — controller pastes full implementer report so reviewer has deviation/concern context
- Per-file single-responsibility check
- Contract constraint tracing (data path from input to storage/output)

**Dispatch type change (the point of this migration):**
- `superpowers-code-reviewer` → `general-purpose` in all 4 dispatch locations (see File Inventory)
- The `code-reviewer.md` template is still used as the prompt body — only the task type wrapper changes

**What does NOT change:**
- `code-quality-reviewer-prompt.md` content (add behaviors → only the dispatch type line changes)
- The `requesting-code-review/code-reviewer.md` template structure — behaviors are ADDED, nothing removed
- All SDD enforcement hook behavior — hooks reference file names, not agent types

---

## Background and Rationale

### Why upstream made this change

Upstream v5.1.0 deleted `agents/code-reviewer.md` and switched the review dispatch from a named agent to a `general-purpose` task carrying `code-reviewer.md` as its inline prompt. The motivation: named agents require a file on disk at a known path, making them fragile across installations and harnesses. A `general-purpose` task is self-contained — the full reviewer instructions travel with the dispatch, not as a separate installed artifact.

### Why we deferred it during the v5.1.0 merge

We kept `superpowers-code-reviewer` during the merge because we had added behaviors to `agents/code-reviewer.md` that were NOT in the upstream `code-reviewer.md` template. Blindly accepting upstream's agent deletion would have silently dropped those behaviors. The right move was: inventory the behavioral delta first, then migrate.

### What the delta is

Two behaviors in `agents/code-reviewer.md` are not in `code-reviewer.md`:

1. **`**Needs Context**` severity category** — our fork uses this as a fourth severity level (alongside Critical/Important/Minor) for findings where the reviewer can't confirm severity without context. This maps to `[NEEDS_CONTEXT]` in the SDD-specific prompt and must be consistent.

2. **Pre-writing reflection gate** — "Before writing findings, reflect on whether your assessment accounts for the full context of the change." This prevents reflexive issue-filing before the reviewer has fully synthesized the change.

These go into `requesting-code-review/code-reviewer.md`. Once they're there, the agent file is redundant.

---

## File Inventory

Complete list of files that change.

### Files to modify

| File | Change |
|------|--------|
| `skills/requesting-code-review/code-reviewer.md` | ADD `**Needs Context**` category to Calibration section; ADD reflection step before Output Format section |
| `skills/requesting-code-review/SKILL.md` | 3 occurrences: change `superpowers-code-reviewer` → `general-purpose` (lines 8, 34, 58) |
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | 1 occurrence: change `Task tool (superpowers-code-reviewer):` → `Task tool (general-purpose):` (line 10) |
| `CLAUDE.md` | Update Installation Architecture section (remove agent symlink entry), Fork Customizations section (remove 3 lines), Verify Installation section (remove agent symlink check), remove agent symlink from `ls` command |
| `docs/ARaymond-customization-manifest.md` | Update symlink table, fork customizations table, conflict resolution table (3 rows), Skills Inventory table (`code-quality-reviewer-prompt.md` row), Upstream Sync Log (add note) |

### Files to delete

| File | Action |
|------|--------|
| `agents/code-reviewer.md` | Delete from repo (`git rm`) |
| `~/.claude/agents/superpowers-code-reviewer.md` | Remove symlink (outside repo) |

### Files NOT changed

| File | Why left alone |
|------|---------------|
| `skills/requesting-code-review/code-reviewer.md` — structure | Behaviors added; nothing removed |
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` — content | All SDD-specific checks remain; only dispatch type line changes |
| All hook scripts | Hooks reference file names and bash commands, not agent types |
| `tests/` | No test files reference `superpowers-code-reviewer`; regression test count unchanged |

---

## Exact Text Changes

### `skills/requesting-code-review/code-reviewer.md`

**Add to the Calibration section** (after "Not everything is Critical."):

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
```

### `skills/requesting-code-review/SKILL.md`

Three line replacements (all `superpowers-code-reviewer` → `general-purpose`):
- Line 8: "Dispatch superpowers-code-reviewer subagent" → "Dispatch a code reviewer subagent"
- Line 34: "Use Task tool with superpowers-code-reviewer type" → "Use Task tool with general-purpose type"
- Line 58: "[Dispatch superpowers-code-reviewer subagent]" → "[Dispatch code reviewer subagent]"

### `skills/subagent-driven-development/code-quality-reviewer-prompt.md`

Line 10:
```
# Before:
Task tool (superpowers-code-reviewer):

# After:
Task tool (general-purpose):
```

---

## Post-Migration Verification

Run after implementing:

```bash
# 1. Confirm no superpowers-code-reviewer references remain in skills/
grep -r "superpowers-code-reviewer" skills/ agents/ CLAUDE.md
# Expected: no output

# 2. Confirm agent file is gone
ls agents/ 2>/dev/null
# Expected: directory not found (or empty if other agents added later)

# 3. Confirm symlink is removed
ls ~/.claude/agents/superpowers-code-reviewer.md 2>/dev/null
# Expected: no such file

# 4. Confirm preserved behaviors are in the template
grep -c "Needs Context\|reflect on whether" skills/requesting-code-review/code-reviewer.md
# Expected: 2

# 5. Confirm dead code still blocking in SDD prompt
grep "blocking\|BLOCKING" skills/subagent-driven-development/code-quality-reviewer-prompt.md
# Expected: at least one match

# 6. Run regression tests
python3 tests/ARaymond-skill-regression/validate-all-skills.py
# Expected: 139 PASS, 0 FAIL

# 7. Run installation tests
bash tests/ARaymond-installation/verify-symlink-install.sh
# Expected: 105 PASS, 0 FAIL (agent symlink count drop is expected and correct)
```

---

## Open Decisions

| # | Decision | Options | Must Be Resolved By |
|---|----------|---------|-------------------|
| 1 | Installation test count after symlink removal | verify-symlink-install.sh checks agent symlink existence — it may need a count update or the agent check removed | Plan writer |
| 2 | CLAUDE.md agent count in Verify Installation | Script checks `ls ~/.claude/agents/superpowers-code-reviewer.md` — remove or replace with a check that the symlink is GONE | Plan writer |

---

## Document Authority

| Concern | Authoritative Document |
|---------|----------------------|
| Which behaviors must be preserved | This handoff package |
| Exact line numbers in current files | Run `grep -n` on the live files (line numbers drift; this doc was written 2026-05-07) |
| Installation architecture post-migration | Update `CLAUDE.md` and manifest during implementation |
| Test suite expectations | `tests/ARaymond-installation/verify-symlink-install.sh` source |

---

## Context for New Session

This is the superpowers fork at `~/projects/claude-custom/superpowers`. Key facts:

- Installed via symlinks (not marketplace plugin): `~/.claude/skills/superpowers/` → `./skills/`, agent at `~/.claude/agents/superpowers-code-reviewer.md` → `./agents/code-reviewer.md`
- CLAUDE.md in the project root has comprehensive architecture documentation — read it before editing anything
- The customization manifest at `docs/ARaymond-customization-manifest.md` is the complete rebuild reference
- Four enforcement hooks are active in `~/.claude/settings.json`; they reference file names, not agent types — no hook changes needed
- Regression test suite: `python3 tests/ARaymond-skill-regression/validate-all-skills.py` (139 checks, <1s)
- Installation test suite: `bash tests/ARaymond-installation/verify-symlink-install.sh` (105 checks, <1s)
- Unit tests: `.venv/bin/python3 -m pytest tests/unit/ -v` (273 tests)

The migration is surgical (7 files, well-understood scope). The main risk is accidentally dropping the two behaviors from `agents/code-reviewer.md` that are not yet in the template — the Contract Constraints section above is the guard.
