---
schema_version: 1
plan_file: "docs/imp-plans/2026-05-07-code-reviewer-agent-migration/plan.md"
reviewer: "general-purpose subagent (plan-document-reviewer-prompt)"
date: "2026-05-07"
status: "Approved"
---

# Plan Review

**Status:** Approved

The plan is implementation-ready. All 4 dispatch references and both fork-only behaviors trace correctly from the JSON fixture through the handoff README to the plan task steps. Source line numbers (CLAUDE.md 24/27-30/70/281; manifest 18/54/237/329; install test 186-210/332-344) match the live filesystem. The TDD ordering (Task 1 RED → Task 2 GREEN behaviors → Task 3 GREEN dispatch → Task 6 GREEN symlink) is internally consistent. Write-scope partitioning is clean; `depends_on` chain prevents Task 6 from running before Task 2.

**Blocking Issues:** None.

## Snippet Verification

- **Snippet 1** [Task 0 `contract-verification.py`, plan lines 114–145]: VERIFIED — `data["references_to_change"][i]["current"]` matches fixture keys exactly; `r["file"]`, `r["line"]`, `r["current"]`, `b["source_file"]`, `b["verbatim"]`, `b["behavior"]` all present in `samples/current-state.json`. `(ROOT / r["file"]).read_text().splitlines()[r["line"] - 1]` correctly handles 1-based line numbers.
- **Snippet 2** [Task 1 Step 1 regression invariants, plan lines 185–211]: VERIFIED — `check_pass`/`check_fail` signatures match the existing `check_critical_fixes` body; `read_file`, `os.path.join`, `skills_dir` are in scope; `CATEGORY_6` is the active constant.
- **Snippet 3** [Task 1 Step 3 inverted symlink check, plan lines 226–249]: VERIFIED — `$AGENT_FILE`, `$REPO_ROOT`, `pass`/`fail`/`section` are defined upstream in the test script (lines 1–185); replacement preserves section-comment style.
- **Snippet 4** [Task 2 Step 1 Calibration block]: VERIFIED — 4-space indentation matches the fenced template at `code-reviewer.md:65-74`; bullet text matches handoff README target wording at lines 125-126 verbatim.
- **Snippet 5** [Task 3 dispatch text changes]: VERIFIED — every "Replace … with …" pair matches the `current` and `target` fields in `samples/current-state.json` exactly.

## Cross-Document Audit

- **SKILL.md line 8 wording**: fixture `current="Dispatch superpowers-code-reviewer subagent to catch issues before they cascade."` → README line 135 → plan Task 3 Step 1 — **MATCH**.
- **SKILL.md line 34 wording**: fixture `current="Use Task tool with superpowers-code-reviewer type, fill template at \`code-reviewer.md\`"` → README line 136 → plan Task 3 Step 2 — **MATCH**.
- **SKILL.md line 58 wording**: fixture `current="[Dispatch superpowers-code-reviewer subagent]"` → README line 137 → plan Task 3 Step 3 — **MATCH**.
- **code-quality-reviewer-prompt.md line 10**: fixture `current="Task tool (superpowers-code-reviewer):"` / `target="Task tool (general-purpose):"` → README lines 144-147 → plan Task 3 Step 4 — **MATCH**.
- **`**Needs Context**` Calibration bullet**: fixture `behaviors_to_add[0].verbatim` (source-file probe) → README target wording (lines 125-126, "to confirm severity; describe…") → plan Task 2 Step 1 — **MATCH** (plan correctly uses the README's restructured target wording, not the agent file's older em-dash phrasing).
- **Reflection step**: fixture verbatim → README lines 128-129 → plan Task 2 Step 1 — **MATCH**.

## Recommendations (advisory)

1. **APPLIED** — `contract-verification.sh` → `contract-verification.py` in Out of Scope (extension consistency).
2. **APPLIED** — Task 2 Step 1 reworded from "Replace lines 67–74" to "Insert the bulleted list and reflection paragraph between line 69 and line 71" (less ambiguous for the implementer).
3. **APPLIED** — Task 2 Step 4 commit message updated from "verbatim from agents/code-reviewer.md:39" to "per handoff README target wording (lines 125-126)".
4. **NOT APPLIED** — Task 4 Step 4 Known conflict files note polish (trivial; current text is accurate post-migration).
5. **APPLIED** — Task 0 Step 2 now notes that `skills/requesting-code-review/code-reviewer.md` line 8 already reads `Task tool (general-purpose):` (pre-existing v5.1.0 state, not part of this migration) so the implementer isn't confused by file-name overlap.
6. **APPLIED** — Task 4 Step 5b added: update CLAUDE.md "Testing" quick-reference line's `139 checks` count to the actual post-migration count, keeping docs synchronized.
