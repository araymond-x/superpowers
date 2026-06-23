---
schema_version: 1
task_id: 11
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: tests/ARaymond-skill-regression/validate-all-skills.py
    description: "F6 check rewired to a module-level DIRECT_ENTRY_RE structural signal; added the compiled regex next to KEBAB_CASE_RE."
tests:
  written: 0
  passing: 0
  command: "python3 tests/ARaymond-skill-regression/validate-all-skills.py"
  result: PASS
contract_compliance:
  - constraint: "Scope stays writing-plans/SKILL.md ONLY"
    status: compliant
    detail: "No SKILL.md or other-skill file was edited; only the test file changed (git status confirms a single modified file)."
  - constraint: "Intent-based, no literal-phrase dependency"
    status: compliant
    detail: "F6 keys on the structural Direct-entry signal (bold label or heading), not on the literal phrases invoked-directly / skipping-brainstorming; negative-check probe confirmed the literal phrase alone no longer matches."
---

# Implementation Summary

Task 11 (N8) made the F6 regression check intent-based. Previously F6 in
`tests/ARaymond-skill-regression/validate-all-skills.py` grepped for the literal
phrases `"skipping brainstorming"` / `"invoked directly"` in
`writing-plans/SKILL.md` — a semantically-equivalent reword of that prose would
silently FAIL the check. N8 replaces that with a structural signal: a compiled
regex matching a "Direct entry" markdown heading or `**Direct entry**` bold
label.

Two edits, both in the test file:

1. Added a module-level `DIRECT_ENTRY_RE = re.compile(r"(?im)^#{1,6}.*direct
   entry|\*\*\s*direct entry")` right after `KEBAB_CASE_RE` (line ~136), with a
   descriptive comment matching the file's `*_RE` convention.
2. Rewrote the F6 check (now ~line 573) from the two-`in`-substring test to
   `if DIRECT_ENTRY_RE.search(wp_content):`. The check_pass/check_fail branches
   are unchanged.

No edit to `writing-plans/SKILL.md`: its existing `2. **Direct entry** —` label
(line 18) already satisfies the structural signal (O3, zero word cost). The
regex matches that label via the `\*\*\s*direct entry` alternative.

Verification:
- F6 line: `[PASS] writing-plans SKILL: has standalone invocation guidance`
- Totals: `PASS: 145  FAIL: 0  WARNING: 3` → `Result: PASS (with warnings)` —
  baseline preserved, no new FAIL.
- Stdlib-only confirmed: `git diff | grep '^\+.*import'` is empty — reuses the
  module-level `re` (line 25). The regex is 3.9-compatible (no PEP-604 syntax).
- Negative-check probe (Step 4) run empirically with a throwaway `python3 -c`:
  - reworded prose with the `**Direct entry**` label but literals removed →
    MATCH True (intent-robust)
  - heading form `### Direct Entry mode` → MATCH True
  - literal phrase `invoked directly` WITHOUT the structural label → MATCH False
    (proves no dependency on the old literal phrases)

Committed as `86ddb95` (1 file changed, 9 insertions, 2 deletions).

# Source Files Read

- `tests/ARaymond-skill-regression/validate-all-skills.py` — read the header/imports
  (confirmed module-level `import re` at line 25, stdlib only), the existing
  module-level `*_RE` patterns (`KEBAB_CASE_RE` line 136; `UNION_SYNTAX_RE`,
  `BUILTIN_GENERIC_RE`, `STRING_LITERAL_RE` lines 1152-1163) to match
  naming/placement/comment style, and the F6 check (lines 568-578) inside
  `check_cross_references()`.
- `skills/writing-plans/SKILL.md:16-18` — confirmed the live `2. **Direct entry** —`
  bold label at line 18 that the structural signal matches. No edit made.

# CLAUDE.md Files Read

- Repo-root `/Users/araymond/projects/claude-custom/superpowers/.worktrees/sdd-aggregate-gate-visibility/CLAUDE.md`
  (loaded into session context) — noted the regression-suite role and the
  documented 145 PASS / 0 FAIL / 3 advisory WARNING baseline that must stay
  PASS-with-warnings. Confirmed the suite still reports exactly that.

# Deviations from Plan

**Module-level `DIRECT_ENTRY_RE` instead of the snippet's inline `import re as
_re`.** The plan's Step-2 code snippet showed an inline `import re as _re` plus
a locally-built `_direct_entry_re`. The task prompt's "IMPORTANT integration
choice" (partner-confirmed) directed me to prefer the cleaner integration the
plan's own prose calls for ("Add a module-level regex near the other
patterns"): the file already imports `re` at module level (line 25) and follows
an `UPPER_SNAKE_CASE` compiled-regex convention (`KEBAB_CASE_RE`,
`UNION_SYNTAX_RE`, …). I therefore defined a module-level
`DIRECT_ENTRY_RE = re.compile(...)` reusing the existing `re` import and
referenced it in the F6 check, rather than adding a redundant `import re as
_re` (which the quality reviewer would flag as a dead/duplicate import). The
**behavior is identical** to the snippet — same regex pattern, same flags
`(?im)`, same `.search(wp_content)` truthiness driving the unchanged
check_pass/check_fail branches. This diverges from the literal snippet text but
follows the file convention + SSOT (single `re` import), exactly as the prompt
instructed me to document here.

# Self-Review Findings

- **Scope:** `git status` confirms only `tests/ARaymond-skill-regression/validate-all-skills.py`
  is modified by this task. `writing-plans/SKILL.md` untouched; no other skill
  file touched. The pre-existing `D`/`??` entries (plan-manifest, plan-review,
  feature-dir artifacts) are SDD-session state, not my changes — I committed
  only the test file.
- **No new imports / stdlib:** verified `git diff` adds no `import` line. The
  regression suite still runs under bare `python3`.
- **3.9 compat:** the regex uses no PEP-604 union syntax; `re.compile` + flags
  are 3.9-safe.
- **Regex correctness:** the heading alternative `^#{1,6}.*direct entry` requires
  `(?m)` so `^` anchors per line (present via `(?im)`); the bold alternative
  `\*\*\s*direct entry` matches `**Direct entry` and `** Direct entry`. Case
  handled by `(?i)`. Alternation precedence is fine — the two alternatives are
  independent top-level branches.
- **Comment quality:** both added comments name N8, state the intent-based
  rationale, and pin the writing-plans-ONLY scope, matching the surrounding
  `*_RE` comment style.

# Concerns

- **Minor (style-only):** `DIRECT_ENTRY_RE` is placed next to `KEBAB_CASE_RE` in
  the top-level module pattern region (line ~138), not immediately adjacent to
  the `UNION_SYNTAX_RE` cluster near CATEGORY_8 (line ~1152). The file uses both
  locations for `*_RE` patterns; I chose the early shared-pattern slot because
  `KEBAB_CASE_RE` (the other general cross-cutting pattern) lives there and it
  keeps the pattern visible at the top. Either location is convention-compliant;
  this is a placement judgment call, not a defect. Flagging it only because the
  status is DONE_WITH_CONCERNS requires honest disclosure of the Deviation
  above — there are no functional concerns.
