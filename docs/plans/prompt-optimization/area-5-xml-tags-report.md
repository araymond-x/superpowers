# XML Tag Usage Audit — Superpowers Skills

**Date:** 2026-03-23
**Scope:** All 15 SKILL.md files + 3 prompt templates
**Reference:** `docs/prompting-best-practices.md` — "Structure prompts with XML tags" section

---

## XML Tag Inventory

All tags found across audited files. Tags that are HTML in visual-companion.md or TypeScript generics in code examples are excluded — those are not semantic XML prompt tags.

| Tag | File(s) | Line(s) | Purpose | Best Practice Compliant? |
|-----|---------|---------|---------|--------------------------|
| `<HARD-GATE>` | `brainstorming/SKILL.md` | 12–14 | Gate/constraint: blocks LLM from taking implementation action until design approved | No — UPPERCASE-WITH-HYPHENS |
| `<SUBAGENT-STOP>` | `using-superpowers/SKILL.md` | 6–8 | Gate/constraint: tells subagents to skip the skill | No — UPPERCASE-WITH-HYPHENS |
| `<EXTREMELY-IMPORTANT>` | `using-superpowers/SKILL.md` | 10–16 | Emphasis/urgency: makes skill invocation non-negotiable | No — UPPERCASE-WITH-HYPHENS |
| `<Good>` / `</Good>` | `test-driven-development/SKILL.md` | 75, 92, 134, 148 | Example labeling: marks correct pattern examples | No — PascalCase |
| `<Bad>` / `</Bad>` | `test-driven-development/SKILL.md` | 94, 106, 150, 164 | Example labeling: marks anti-pattern examples | No — PascalCase |
| `<Good>` / `</Good>` | `writing-skills/SKILL.md` | 475, 485 | Example labeling: marks correct pattern | No — PascalCase |
| `<Bad>` / `</Bad>` | `writing-skills/SKILL.md` | 469, 473 | Example labeling: marks anti-pattern | No — PascalCase |

### Already-Fixed: Tags Replaced With Markdown Headers

These tags appeared in earlier (non-v0.1) versions of skills but have been replaced in v0.1:

| Tag (removed) | v0.1 File | Replacement | Status |
|---------------|-----------|-------------|--------|
| `<HARD-GATE>` | `brainstorming/SKILL-v0.1.md` | `## CRITICAL CONSTRAINT` (markdown header + bold text) | Fixed in v0.1 |

Note: `brainstorming/SKILL.md` (non-v0.1, the upstream version) still contains `<HARD-GATE>`. The v0.1 fork correctly replaced it with markdown.

### Excluded: Not Semantic Prompt Tags

These were found by the grep but are NOT XML prompt tags:

| Pattern | File | Reason Excluded |
|---------|------|-----------------|
| HTML tags (`<h2>`, `<div>`, `<p>`, etc.) | `brainstorming/visual-companion.md` | Literal HTML content sent to browser companion — not prompt structure tags |
| TypeScript generics (`<T>`, `Promise<T>`) | `test-driven-development/SKILL.md` | TypeScript code in fenced code blocks — not prompt tags |
| Template placeholders (`<feature-name>`, `<N>`, etc.) | Multiple files | Shell/markdown template syntax — not prompt tags |
| `<Note>`, `<Warning>`, `<Tip>`, `<Card>` | `writing-skills/anthropic-best-practices.md` | MDX/Mintlify doc components from the upstream Anthropic docs site — not prompt tags |
| `<Before>` / `<After>` | `writing-skills/testing-skills-with-subagents.md` | Example labeling (same pattern as `<Good>/<Bad>`) — see Recommendations |
| `<available_skills>`, `<important_info_about_skills>` | `writing-skills/examples/CLAUDE_MD_TESTING.md` | Example file showing CLAUDE.md context injection format — lowercase-with-hyphens, compliant |
| `<details>` / `<summary>` | `writing-skills/anthropic-best-practices.md` | Standard HTML disclosure elements in MDX — not prompt tags |

---

## Categorized Tag Summary

### Category 1: Gate / Constraint Tags

Tags that block the LLM from taking certain actions until conditions are met.

| Tag | File | Compliant? | Notes |
|-----|------|------------|-------|
| `<HARD-GATE>` | `brainstorming/SKILL.md` (upstream) | No | UPPERCASE. v0.1 already migrated to markdown. |
| `<SUBAGENT-STOP>` | `using-superpowers/SKILL.md` | No | UPPERCASE. Unique pattern with no markdown equivalent currently. |

### Category 2: Emphasis / Urgency Tags

Tags that signal mandatory compliance or heightened attention.

| Tag | File | Compliant? | Notes |
|-----|------|------------|-------|
| `<EXTREMELY-IMPORTANT>` | `using-superpowers/SKILL.md` | No | UPPERCASE. Single use. |

### Category 3: Example Labeling Tags

Tags that mark good/bad or before/after pattern examples.

| Tag | File | Compliant? | Notes |
|-----|------|------------|-------|
| `<Good>` / `<Bad>` | `test-driven-development/SKILL.md` | No | PascalCase. Used 4 pairs. |
| `<Good>` / `<Bad>` | `writing-skills/SKILL.md` | No | PascalCase. Used 1 pair. |
| `<Before>` / `<After>` | `writing-skills/testing-skills-with-subagents.md` | No | PascalCase. Same purpose as Good/Bad. |

### Category 4: Already-Compliant Tags (in example files)

| Tag | File | Compliant? | Notes |
|-----|------|------------|-------|
| `<available_skills>` | `writing-skills/examples/CLAUDE_MD_TESTING.md` | Yes | lowercase-with-hyphens, purposeful |
| `<important_info_about_skills>` | `writing-skills/examples/CLAUDE_MD_TESTING.md` | Yes | lowercase-with-hyphens, purposeful |

---

## Consistency Assessment

### Same Concept, Different Tags?

**Example labeling** is the most inconsistently tagged concept:

- `test-driven-development/SKILL.md` uses `<Good>` / `<Bad>`
- `writing-skills/SKILL.md` uses `<Good>` / `<Bad>` (consistent with TDD)
- `writing-skills/testing-skills-with-subagents.md` uses `<Before>` / `<After>` (different tag, same role)
- `brainstorming/SKILL-v0.1.md` uses `## WRONG WAY` / `## RIGHT WAY` markdown headers (no tags at all)
- `writing-plans/SKILL-v0.1.md` uses no example labels at all for its inline comparisons

The `<Good>/<Bad>` pair has the most adoption (5 uses across 2 files) but is inconsistently applied — several skills that show right/wrong comparisons use neither this tag nor any other.

**Gate/constraint patterns** also diverge:

- `brainstorming/SKILL.md` (upstream): `<HARD-GATE>` (XML tag)
- `brainstorming/SKILL-v0.1.md` (fork): `## CRITICAL CONSTRAINT` (markdown header + bold block)
- `using-superpowers/SKILL.md`: `<SUBAGENT-STOP>` / `<EXTREMELY-IMPORTANT>` (XML tags, no markdown equivalent)
- All other skills: markdown bold + `**MUST**` / `**REQUIRED**` language (no structural tags at all)

---

## Naming Convention Assessment

Per the best practices reference: tags should be **lowercase-with-hyphens**.

| Tag | Convention Used | Verdict |
|-----|----------------|---------|
| `<HARD-GATE>` | UPPERCASE-WITH-HYPHENS | Non-compliant |
| `<SUBAGENT-STOP>` | UPPERCASE-WITH-HYPHENS | Non-compliant |
| `<EXTREMELY-IMPORTANT>` | UPPERCASE-WITH-HYPHENS | Non-compliant |
| `<Good>` / `<Bad>` | PascalCase | Non-compliant |
| `<Before>` / `<After>` | PascalCase | Non-compliant |
| `<available_skills>` | lowercase-with-hyphens | Compliant |
| `<important_info_about_skills>` | lowercase-with-hyphens | Compliant |

**Zero of the actively-used semantic prompt tags (gate + example) are naming-compliant.**

---

## Proposed Standard Vocabulary

### For Example Labeling

The `<Good>/<Bad>` pattern is the most widely adopted and semantically clear. Standardize it, rename to compliant case.

| Purpose | Current Tags | Proposed Standard | Notes |
|---------|-------------|-------------------|-------|
| Correct pattern example | `<Good>`, `<Before>`, `## RIGHT WAY` | `<good>` / `</good>` | Lowercase |
| Anti-pattern example | `<Bad>`, `<After>`, `## WRONG WAY` | `<bad>` / `</bad>` | Lowercase |

Alternative: If the anti-pattern/good-pattern framing feels too evaluative for some contexts, `<example>` (single example, per Anthropic best practices) or `<examples>` (multiple) are already blessed by the docs — but those don't convey polarity. `<good>/<bad>` conveys polarity clearly and is worth keeping.

### For Gate / Constraint Tags

The brainstorming v0.1 migration to markdown headers shows one direction. However, `<SUBAGENT-STOP>` and `<EXTREMELY-IMPORTANT>` serve a distinct parsing purpose: they tell Claude to pay special attention to a bounded block, not just read a header. This use case is legitimate per the best practices guide ("Wrapping each type of content in its own tag reduces misinterpretation").

| Purpose | Current Tags | Proposed Standard | Notes |
|---------|-------------|-------------------|-------|
| Blocking constraint (stop until condition met) | `<HARD-GATE>`, `## CRITICAL CONSTRAINT` | `<critical-constraint>` | lowercase-with-hyphens |
| Subagent early-exit signal | `<SUBAGENT-STOP>` | `<subagent-stop>` | lowercase-with-hyphens |
| Mandatory instruction block | `<EXTREMELY-IMPORTANT>` | `<mandatory>` | Shorter, still clear |

---

## Recommendations

### Priority 1: Rename non-compliant tags in `using-superpowers/SKILL.md`

**File:** `skills/using-superpowers/SKILL.md`
**Change:** `<SUBAGENT-STOP>` → `<subagent-stop>`, `<EXTREMELY-IMPORTANT>` → `<mandatory>`

These are the only active XML tags (other than the legacy `<HARD-GATE>` in upstream brainstorming) that exist in the fork's live skill files. Two tag pairs, one file. Low effort, high compliance gain.

### Priority 2: Standardize example labeling to `<good>` / `<bad>`

**Files:** `skills/test-driven-development/SKILL.md`, `skills/writing-skills/SKILL.md`, `skills/writing-skills/testing-skills-with-subagents.md`
**Change:** Rename `<Good>` → `<good>`, `<Bad>` → `<bad>`, `<Before>` → `<good>`, `<After>` → `<bad>`

This is a mechanical rename. Five occurrences of `<Good>/<Bad>` in two files, one occurrence of `<Before>/<After>` in a supporting file.

### Priority 3: Decide on `<HARD-GATE>` in upstream `brainstorming/SKILL.md`

**File:** `skills/brainstorming/SKILL.md` (non-v0.1, upstream)
**Options:**
1. Leave as-is (it's the upstream version; the fork's v0.1 already fixed it)
2. Apply the same markdown-header fix to the non-v0.1 file for consistency

Since this fork prefers v0.1 files where they exist, option 1 is acceptable. The non-v0.1 file is essentially the upstream source, and its `<HARD-GATE>` tag is not loaded in normal fork operation. However, if the upstream SKILL.md is loaded at all (e.g., when v0.1 does not exist for a given skill), the tag remains non-compliant.

**Recommendation:** Leave upstream files unmodified; only apply changes to v0.1 and fork-owned files. Document the fix as already done in v0.1.

### Priority 4: Extend example labeling to skills that currently have no tagging

Several skills show right/wrong comparisons using only formatting (bold, `❌`/`✅` emoji, or prose) without structural tags:

- `skills/receiving-code-review/SKILL.md` — uses `❌ WRONG:` / `✅ RIGHT:` inline
- `skills/subagent-driven-development/SKILL-v0.1.md` — uses `❌` / `✅` bullets
- `skills/verification-before-completion/SKILL.md` — uses `✅` / `❌` inline

These are readable as-is. Adding `<good>/<bad>` tags would improve machine-parsability. This is a lower-priority consistency improvement — only worth doing if a sweep of all skills is planned.

---

## Summary

| Issue | Files Affected | Count | Priority |
|-------|---------------|-------|----------|
| UPPERCASE gate/emphasis tags | `using-superpowers/SKILL.md` | 2 tags | High |
| PascalCase example labels | `test-driven-development/SKILL.md`, `writing-skills/SKILL.md`, `testing-skills-with-subagents.md` | 6 tag pairs | Medium |
| Inconsistent example labeling (no tags) | `receiving-code-review/SKILL.md`, `subagent-driven-development/SKILL-v0.1.md`, `verification-before-completion/SKILL.md` | 3 files | Low |
| Legacy `<HARD-GATE>` (upstream file only) | `brainstorming/SKILL.md` | 1 tag | Leave as-is (v0.1 already fixed) |

**Net result if Priority 1 + 2 are applied:** All fork-owned skill files will use lowercase-with-hyphens XML tags consistently. Gate-style tags will follow a predictable `<verb-noun>` pattern. Example labels will be uniform across all files that use them.
