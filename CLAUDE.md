# Superpowers Custom Fork

Custom fork of obra/superpowers. Installed via symlinks to ~/.claude/, NOT as a marketplace plugin.

## Setup Reference
- Full setup runbook: `docs/ARaymond-custom-fork-setup-runbook-v1.md`

## Installation Architecture
- Skills: `~/.claude/skills/superpowers` → `./skills/` (single parent symlink, loads into context for auto-invocation)
- Commands: `~/.claude/commands/superpowers/*.md` — stubs with `!`cat`` preprocessing that dynamically include the full SKILL.md content (minus frontmatter) at invocation time. These provide the `superpowers:` namespace in the `/skills` picker (personal skills don't support nested directory namespacing; commands do via `commands/<group>/<name>.md`). **These files live outside the repo** — regenerate on new machines (see below)
- Agent: `~/.claude/agents/superpowers-code-reviewer.md` → `./agents/code-reviewer.md`
- Hook: SessionStart in `~/.claude/settings.json` calls `./hooks/session-start` with `CLAUDE_PLUGIN_ROOT` set

## Fork Customizations (preserve during upstream merge)
- `agents/code-reviewer.md` — `name:` changed to `superpowers-code-reviewer`
- `skills/requesting-code-review/SKILL.md` — agent refs changed to `superpowers-code-reviewer`
- `skills/subagent-driven-development/code-quality-reviewer-prompt.md` — agent ref changed to `superpowers-code-reviewer`

## v0.1 Skill Improvements (2026-03-23)
Improved versions of 3 core skills + 1 new skill, with deterministic scripts and structured prompt templates. v0.1 files coexist with originals until promoted.

### v0.1 Files (not yet promoted to active)
- `skills/brainstorming/SKILL-v0.1.md` — spec distillation, feature archetypes, worktree step
- `skills/writing-plans/SKILL-v0.1.md` — plan modules (<800 lines), Task 0, Contract Constraints, Feature Footprint, 15-category reviewer
- `skills/subagent-driven-development/SKILL-v0.1.md` — controller discipline, review enforcement, DEVIATIONS.md, file-based reports, context health, 7-condition pre-completion gate
- `skills/subagent-driven-development/implementer-prompt-v0.1.md` — 10-section structured report, Contract Constraints passthrough, Source Files mandate
- `skills/subagent-driven-development/spec-reviewer-prompt-v0.1.md` — contract verification, severity gradation (BLOCKING/ADVISORY), BASE_SHA placeholder
- `skills/subagent-driven-development/code-quality-reviewer-prompt-v0.1.md` — dead code blocking, implementer report placeholder
- `skills/writing-plans/plan-document-reviewer-prompt-v0.1.md` — 15-category mechanical checklist, cross-doc audit, snippet verification
- `skills/brainstorming/distillation-reviewer-prompt.md` — verifies distilled spec preserves all decisions
- `skills/handoff-acceptance/SKILL.md` — NEW: verifies external handoff packages before consumption

### Promotion Checklist (when ready to go live)
1. For each v0.1 file: `mv SKILL-v0.1.md SKILL.md` (archive original as `SKILL-original.md` if desired)
2. Same for prompt templates: `mv implementer-prompt-v0.1.md implementer-prompt.md`
3. Create command stub for `handoff-acceptance` (see Regenerate Command Stubs)
4. Update "Verify Installation" expected count from 14 to 15
5. Run regression test: `python3 tests/ARaymond-skill-regression/validate-all-skills.py`

### Deterministic Scripts (`skills/subagent-driven-development/scripts/`)
- `_report_utils.py` — shared library for report parsing (single source of truth — do NOT duplicate logic)
- `estimate-task-tokens.py` — pre-dispatch context budget check (OK/WARNING/TOO_LARGE)
- `validate-report.py` — implementer report completeness (9 required sections)
- `controller-checkpoint.py` — 3-phase controller health (pre-execution/pre-dispatch/pre-completion)
- `context-summary.py` — compresses completed task reports into one summary file
- `validate-plan.py` — mechanical plan structure checks (size, sections, Task 0)
- Scripts are referenced from SKILL-v0.1.md via full paths: `~/.claude/skills/superpowers/subagent-driven-development/scripts/...`
- **Gotcha**: bare `scripts/` paths resolve from the project working directory, not the skill directory. Always use the full `~/.claude/skills/superpowers/...` path.

### Shell Scripts
- `skills/handoff-acceptance/scripts/check-handoff.sh` — verifies contract summary in first 50 lines
- `skills/brainstorming/scripts/check-distillation.sh` — greps for exploration artifacts in distilled specs

### Progressive Disclosure (`references/` directories)
Large templates and flowcharts moved from SKILL bodies to `references/` per Anthropic's skills guide (keep SKILL.md under 5000 words):
- `skills/writing-plans/references/` — task-0-template.md, obsolescence-verification-template.md, module-template.md
- `skills/subagent-driven-development/references/` — example-workflow.md, advantages.md
- `skills/brainstorming/references/` — process-flow.dot
- `skills/handoff-acceptance/references/` — acceptance-flow.dot

## Upstream Sync
```bash
git fetch upstream && git merge upstream/main
```
Conflict files: `agents/code-reviewer.md`, `skills/requesting-code-review/SKILL.md`, `skills/subagent-driven-development/code-quality-reviewer-prompt.md`

**After merge:** If upstream added new skills, create a matching command stub for each:
```bash
# For each new skill directory in skills/<name>/SKILL.md:
cat > ~/.claude/commands/superpowers/<name>.md << 'EOF'
---
name: superpowers:<name>
description: <copy from SKILL.md frontmatter>
---

!`cat ~/.claude/skills/superpowers/<name>/SKILL.md | awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}'`
EOF
```

## Verify Installation
```bash
# Skills: expect 15 (14 upstream + handoff-acceptance)
find -L ~/.claude/skills/superpowers -name "SKILL.md" | wc -l
# Commands: expect 15 (powers /skills picker) — create handoff-acceptance stub if missing
ls ~/.claude/commands/superpowers/*.md | wc -l
# Skill/command count should match
# Agent symlink intact
ls -la ~/.claude/agents/superpowers-code-reviewer.md
# Hook present in settings
grep -c "session-start" ~/.claude/settings.json
```

### Regenerate Command Stubs
If command stubs are missing (new machine, or after upstream adds skills):
```bash
for dir in ~/.claude/skills/superpowers/*/; do
  name=$(basename "$dir")
  desc=$(sed -n '/^---$/,/^---$/p' "$dir/SKILL.md" | grep '^description:' | head -1 | sed 's/^description: *//' | sed 's/^"//' | sed 's/"$//')
  cat > ~/.claude/commands/superpowers/"$name".md << CMDEOF
---
name: superpowers:$name
description: $desc
---

!\`cat ~/.claude/skills/superpowers/$name/SKILL.md | awk 'BEGIN{c=0} /^---\$/{c++; next} c>=2{print}'\`
CMDEOF
done
```

## Testing
- `tests/ARaymond-skill-regression/validate-all-skills.py` — 100-check regression test for all v0.1 skill files (frontmatter, size, cross-refs, scripts, sections, Python 3.9). Run after ANY skill edit: `python3 tests/ARaymond-skill-regression/validate-all-skills.py`
- `docs/testing.md` describes the integration test framework but references a plugin-based setup (`superpowers@superpowers-dev`) — not applicable to this fork's symlink install
- Token analysis works standalone: `python3 tests/claude-code/analyze-token-usage.py <session.jsonl>`
- `tests/ARaymond-installation/verify-symlink-install.sh` — 95 checks for symlink+command-stub architecture (no API calls). Run after upstream merges or installation changes.
- Run both after upstream merges: `bash tests/ARaymond-installation/verify-symlink-install.sh && python3 tests/ARaymond-skill-regression/validate-all-skills.py`
- macOS PDF reading: requires `brew install poppler` for `pdftotext` command
- All other test suites (`tests/claude-code/`, `tests/skill-triggering/`, `tests/explicit-skill-requests/`) use `--plugin-dir` — they test plugin mode, NOT the symlink install
- macOS has no `timeout` command — test scripts use background-process-kill pattern instead
- `claude -p --output-format stream-json` requires `--verbose` flag — headless tests must include both
- Avoid running `claude -p` integration tests from within an active Claude session — nested API calls exhaust quota quickly

## Process Improvement Findings (`docs/process-improvement-findings/`)
Real-world issues from using superpowers in production projects. Use these to inform fork customizations.
- `subagent-claude-md-enforcement.md` — Subagents skip subdirectory CLAUDE.md files; prompt template fix for implementer and spec-reviewer
- `2026-03-16-statement-reconciliation-lessons-learned.md` — Post-mortem from a large SDD session; handoff quality and context gaps
- `2026-03-16-plan-review-findings-aws-explore.md` — Plan review gaps found during aws-explore project
- `2026-03-16-handoff-quality-recommendations-aws-explore.md` — Recommendations for improving subagent handoff quality
- `ResponseCapture-*.txt` — Raw session captures documenting failure modes

## Process Improvement Implementation Status
All 5 areas addressed by v0.1 skill improvements (2026-03-23 session). See `docs/plans/2026-03-23-sdd-improvement-plan-v0.1.md` for the master plan and `docs/plans/2026-03-23-final-audit-results.md` for the audit. Remaining work: promote v0.1 files to active, validate against a real implementation project.

## `.superpowers/` Directory
The visual brainstorming companion writes session data to `.superpowers/brainstorm/` in the project root. Each session gets a timestamped subdirectory containing HTML mockups, browser click events (`.events`), and server info. This directory is gitignored — it's ephemeral working state, not project artifacts.

## Editing Skills
- **Skill content**: Edit `./skills/<name>/SKILL.md` in the repo — live immediately via symlink
- **Skill description in `/skills` picker**: Edit `~/.claude/commands/superpowers/<name>.md` frontmatter — these are standalone files outside the repo
- **Gotcha**: Changing `description:` in SKILL.md does NOT update the picker. You must update BOTH the SKILL.md and the command stub's frontmatter. The `!`cat`` preprocessing only pulls body content, not frontmatter.
- **Hook** (`hooks/session-start`): Referenced by absolute path in `settings.json` — edits are live immediately, no symlink

## Handoff Package Specification
- `skills/handoff-acceptance/references/handoff-package-spec.md` — Required structure for handoff packages consumed by the Superpowers pipeline. Bundled inside the handoff-acceptance skill so agents discover it automatically — when a handoff fails acceptance, the skill surfaces the spec in the failure report. Also used in "producer mode" when an agent is asked to create a handoff package.

## Prompting Best Practices
- `docs/prompting-best-practices.md` — Comprehensive Claude 4.6 prompt engineering reference covering clarity, examples, XML structuring, thinking, tool use, and agentic systems. Source of truth for all prompt optimization decisions. Consult when writing or improving any skill, prompt template, or agent file.

## Prompt Optimization (2026-03-23)
Applied Claude 4.6 prompting best practices across all skills per `docs/plans/2026-03-23-PromptingBestPracticesImprovementPlan.md`.
- 8 audit reports in `docs/plans/prompt-optimization/` (Areas 1-8)
- Consolidated recommendations: `docs/plans/prompt-optimization/phase-5-consolidated-recommendations.md`
- 171 changes applied in 3 passes: descriptions + XML + roles (Pass 1), de-escalation + positive framing (Pass 2), motivation + thinking + agentic patterns (Pass 3)
- Key changes: `<EXTREMELY-IMPORTANT>` → `<important>`, aggressive MUST/NEVER → direct imperatives, Red Flags → Required Practices/positive framing, role statements added to all prompt templates
- SDD SKILL-v0.1.md is at 4091/5000 words (82%) — monitor on future additions

## Execution Trace Audit
- `extract-execution-trace.py` parses `.jsonl` session files into structured JSON with per-task records and 6 anomaly detection rules
- `trace-auditor-prompt.md` dispatches a subagent to review the trace for skipped reviews, unlogged concerns, missing reports
- Integrated as Pre-Completion Gate step 8 in the SDD skill
- To find current session file: `ls -t ~/.claude/projects/*/$(pwd | sed 's|/|%|g')/*.jsonl | head -1`

## Output Path Convention
- Design specs → `docs/specs/YYYY-MM-DD-<topic>-design.md` (from brainstorming)
- Distilled specs → `docs/specs/YYYY-MM-DD-<topic>-design-distilled.md` (from brainstorming)
- Implementation plans → `docs/imp-plans/YYYY-MM-DD-<feature-name>.md` (from writing-plans)
- Project plans/reviews → `docs/plans/` (existing convention, not changed)

## Three-Layer Test Strategy
- **After any skill edit**: `python3 tests/ARaymond-skill-regression/validate-all-skills.py` (static, 105 checks, <1s)
- **After installation changes**: `bash tests/ARaymond-installation/verify-symlink-install.sh` (static, 95 checks, <1s)
- **After skill content changes**: `bash tests/ARaymond-skill-behavior/run-all.sh` (API calls, ~15 min, tests actual Claude behavior)
- Structural PASS does not mean semantic PASS — always run both static and behavioral tests for significant changes

## Behavioral Test Gotchas
- Test scripts use `grep -E` (ERE): alternation is `|` not `\|` (BRE). Wrong syntax silently fails to match.
- Content questions to `claude -p` need `--max-turns 5` minimum — Claude uses turns loading skills before answering. 3 turns is insufficient.
- Scripts that grep for artifact patterns (check-distillation.sh) must exclude template boilerplate lines (blockquotes).

## Key Architecture Notes
- Skills use inline prompt templates (`./implementer-prompt.md`) for subagent dispatch, NOT formal agent files
- Only 1 formal agent exists (`code-reviewer.md`) — used for final whole-implementation review
- Personal skills (`~/.claude/skills/`) only support one level of nesting for the `/skills` picker. The `superpowers:` namespace in the picker comes from command stubs at `~/.claude/commands/superpowers/`, NOT from the skills directory structure
- Agents do NOT support nested directory namespacing — must use flat files with unique names
- Brainstorm visual companion server: `skills/brainstorming/scripts/start-server.sh` (NOT repo root `scripts/`)
- macOS gotcha: BSD `sed` fails on curly brace range expressions. Use `awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}'` to strip YAML frontmatter
