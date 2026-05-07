---
schema_version: 1
package: "docs/handoffs/2026-05-07-general-purpose-migration/"
date: "2026-05-07"
reviewer: "controller (main session)"
verdict: "ACCEPTED"
---

# Handoff Acceptance Report — general-purpose-migration

## Checklist Results

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Contract Summary at top | PASS | Frontmatter `contract_constraints` + "Contract Constraints" prose, both within first 50 lines |
| 2 | Executable code snippets | PASS | Markdown text-edit instructions and shell verification commands; no ambiguous pseudocode |
| 3 | Acceptance fixtures | PASS | `samples/current-state.json` — parseable JSON with file/line/current/target for all 4 references and 2 behaviors |
| 4 | Acceptance test | PASS | 7-step "Post-Migration Verification" block; regression + install suites cover the rest |
| 5 | Document authority | PASS | Authority table at lines 197–204 |
| 6 | Open decisions | PASS | 2 decisions tabled, both delegated to plan writer |

## Contract Facts Extracted

**Behaviors to add to `skills/requesting-code-review/code-reviewer.md`:**
1. `**Needs Context**` severity category in Calibration section (verbatim from handoff)
2. Pre-writing reflection step before Output Format section (verbatim from handoff)

**SDD-specific behaviors that must remain unchanged in `skills/subagent-driven-development/code-quality-reviewer-prompt.md`:**
- Dead code findings = **BLOCKING** (not Minor)
- `[NEEDS_CONTEXT]` label for uncertain findings
- `IMPLEMENTER_REPORT` passthrough
- Per-file single-responsibility check
- Contract constraint tracing (input → storage/output)

**Dispatch type change (4 locations):**
- `skills/requesting-code-review/SKILL.md` lines 8, 34, 58
- `skills/subagent-driven-development/code-quality-reviewer-prompt.md` line 10

**Files to delete:**
- `agents/code-reviewer.md` (`git rm`)
- `~/.claude/agents/superpowers-code-reviewer.md` (symlink, outside repo)

## Live-State Cross-Check

- 4 dispatch references confirmed on disk at documented locations (grep verified)
- Both behaviors confirmed in `agents/code-reviewer.md:39,49` and **absent** from `skills/requesting-code-review/code-reviewer.md` — migration is genuinely needed

## Open Decisions (deferred to plan writer)

| # | Decision | Notes |
|---|----------|-------|
| 1 | Installation test count after symlink removal | `verify-symlink-install.sh` checks agent symlink existence — needs a count update or check inversion |
| 2 | CLAUDE.md "Verify Installation" agent check | Current `ls ~/.claude/agents/superpowers-code-reviewer.md` line — remove or replace with absence-check |

## Verdict: ACCEPTED

No remediation required. Proceed to writing-plans with this report and the handoff package as inputs.
