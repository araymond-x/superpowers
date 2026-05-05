# Superpowers Custom Fork

Custom fork of obra/superpowers. Installed via symlinks to ~/.claude/, NOT as a marketplace plugin.

## Skill Invocation Rule
When a prompt says "invoke skill X" or "use skill X" → load it via the **Skill tool** before ANY implementation. Direct implementation without the Skill tool bypasses all enforcement hooks. (See `docs/ARaymond-skills-best-practices.md` for why.)

## Key Documentation
- **Customization Manifest**: `docs/ARaymond-customization-manifest.md` — complete inventory of every modification, installation steps, upstream sync, rollback procedures. Start here for "what was changed and why."
- **Skills Best Practices**: `docs/ARaymond-skills-best-practices.md` — operational learnings: enforcement layers, hook patterns, testing strategy, common failure modes. Consult when building or modifying skills.
- **Prompting Best Practices**: `docs/prompting-best-practices.md` — Claude 4.6 prompt engineering reference for skill/prompt template authoring.
- **External References**: `docs/external-references/` — captured external content (LinkedIn posts, articles) used as input for fork improvement planning. Files named `YYYY-MM-DD-<topic>.md`. Mirror into Obsidian vault `References/` for QMD searchability.

## Documentation Maintenance
After each production-deployable update to the fork, review:
1. `CLAUDE.md` — update sections affected by the change (hooks, settings, test counts)
2. `docs/ARaymond-customization-manifest.md` — update the relevant inventory section (scripts, hooks, skills, settings)
3. `docs/ARaymond-skills-best-practices.md` — add any new learnings, gotchas, or failure modes discovered
4. Run both test suites to verify the documented check counts are still accurate

## Installation Architecture
- Skills: `~/.claude/skills/superpowers` → `./skills/` (single parent symlink, loads into context for auto-invocation)
- Commands: `~/.claude/commands/superpowers/*.md` — stubs with `!`bash strip-frontmatter.sh`` preprocessing that dynamically include the full SKILL.md content (minus frontmatter) at invocation time. These provide the `superpowers:` namespace in the `/skills` picker (personal skills don't support nested directory namespacing; commands do via `commands/<group>/<name>.md`). **These files live outside the repo** — regenerate on new machines (see below)
- Agent: `~/.claude/agents/superpowers-code-reviewer.md` → `./agents/code-reviewer.md`
- Hook: SessionStart in `~/.claude/settings.json` calls `./hooks/session-start` with `CLAUDE_PLUGIN_ROOT` set

## Fork Customizations (preserve during upstream merge)
- `agents/code-reviewer.md` — `name:` changed to `superpowers-code-reviewer`
- `skills/requesting-code-review/SKILL.md` — agent refs changed to `superpowers-code-reviewer`
- `skills/subagent-driven-development/code-quality-reviewer-prompt.md` — agent ref changed to `superpowers-code-reviewer`

## Subagent Context Improvements (2026-04-08)
Three additions to prevent architectural violations that persist despite the SDD review process:
- **Shared Constants Passthrough**: Plan header field + SDD ingestion Step 2b + implementer prompt section. Forces subagents to import canonical constants instead of hardcoding values. Files: `writing-plans/SKILL.md`, `subagent-driven-development/SKILL.md`, `implementer-prompt.md`.
- **Import Assertions in Task 0**: Step 5b in `task-0-template.md`. Writes assertions that import values from source code and compare against fixtures, preventing fixture drift.
- **Fix Complexity Gate**: Point-vs-structural classification at start of Phase 4 in `systematic-debugging/SKILL.md`. Routes structural fixes to brainstorming instead of direct coding.
- **Pattern References**: Plan header field + Pattern Discovery section in writing-plans Step 2 + SDD ingestion Step 2c + implementer prompt section. Forces plan authors to search for existing implementations and inject them as reading requirements for subagents. Prevents "built from scratch, corrected 10 times" when the codebase already has established patterns. Greenfield projects get a user question instead.
- Extracted DEVIATIONS template, report naming convention, and honesty check block to `references/` to stay under SDD SKILL.md 5000-word limit (4983 after all changes).

## v0.1 Skill Improvements (2026-03-23) — PROMOTED
All v0.1 files have been promoted to active and the originals removed. The improvements are now live in the main SKILL.md and prompt template files. See `docs/ARaymond-customization-manifest.md` for the complete inventory of customizations per skill.

### Deterministic Scripts (`skills/subagent-driven-development/scripts/`)
- `_report_utils.py` — shared library for report parsing (single source of truth — do NOT duplicate logic)
- `estimate-task-tokens.py` — pre-dispatch context budget check (OK/WARNING/TOO_LARGE)
- `validate-report.py` — two-layer report validation: Pydantic frontmatter (via validators.py) then 5 prose sections
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
**All 15 SKILL.md files have diverged from upstream.** Any upstream change to a SKILL.md will conflict. Before merging, run a three-way comparison (merge-base vs ours vs upstream) for each conflicted file — do NOT rely on this documentation alone. See `docs/ARaymond-customization-manifest.md` "Upstream Conflict Files" for the full list and resolution guide.

Known conflict files (always): `CLAUDE.md`, `agents/code-reviewer.md`, `skills/requesting-code-review/SKILL.md`, `skills/subagent-driven-development/code-quality-reviewer-prompt.md`
Likely conflict files (when upstream touches these): `brainstorming/SKILL.md`, `writing-plans/SKILL.md`, `subagent-driven-development/SKILL.md`, `using-superpowers/SKILL.md`, `writing-skills/SKILL.md`

Last sync: `b557648` on 2026-04-17

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

!\`bash ~/.claude/skills/superpowers/scripts/strip-frontmatter.sh ~/.claude/skills/superpowers/$name/SKILL.md\`
CMDEOF
done
```

## Testing
Quick reference: 4 test layers — regression (static, 138 checks), install (static, 105 checks), unit (pytest, 266 tests), behavior (API, ~15m). Structural PASS ≠ semantic PASS — run both static and behavioral tests for significant changes. Details below.

- `tests/ARaymond-skill-regression/validate-all-skills.py` — 138-check regression test for all skill files (frontmatter, size, cross-refs, scripts, sections, Python 3.9). Run after ANY skill edit: `python3 tests/ARaymond-skill-regression/validate-all-skills.py`
- `docs/testing.md` describes the integration test framework but references a plugin-based setup (`superpowers@superpowers-dev`) — not applicable to this fork's symlink install
- Token analysis works standalone: `python3 tests/claude-code/analyze-token-usage.py <session.jsonl>`
- `tests/ARaymond-installation/verify-symlink-install.sh` — 105 checks for symlink+command-stub architecture (no API calls). Includes a regression guard that pins `hooks/session-start`'s `EXPECTED_SKILL_COUNT`/`EXPECTED_CMD_COUNT` to the real filesystem counts so adding or removing a skill without updating the hook fails the test. Run after upstream merges or installation changes.
- `tests/unit/` — 266 pytest tests: Pydantic models (implementer_report, checkpoint_result, plan, schema versioning), validators CLI (plan, handoff, report subcommands), controller-checkpoint.py (stale artifacts, honesty check, trace audit, minimum-tier ratio), sdd-pre-dispatch-hook.sh (dispatch provenance, hard gates, checkpoint file, partner review), sdd-report-guard.sh (dispatch log protection), sdd-stop-hook.sh (honesty log capture). Run: `.venv/bin/python3 -m pytest tests/unit/ -v`
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
All 5 areas addressed by v0.1 skill improvements (2026-03-23 session). See `docs/plans/2026-03-23-sdd-improvement-plan-v0.1.md` for the master plan and `docs/plans/2026-03-23-final-audit-results.md` for the audit. v0.1 promotion complete — all improvements are live.

## `.superpowers/` Directory
The visual brainstorming companion writes session data to `.superpowers/brainstorm/` in the project root. Each session gets a timestamped subdirectory with two peer directories: `content/` (HTML mockups served to the browser) and `state/` (events, server-info, pid, log). This directory is gitignored — it's ephemeral working state, not project artifacts. (Restructured in upstream v5.0.6.)

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
- SDD SKILL.md is at 5029 words — **over the 5000-word soft limit**. Any addition MUST be offset by extracting existing content to `references/` first. Re-check with `wc -w skills/subagent-driven-development/SKILL.md` before editing.

## Hooks-Based Enforcement
- Skill frontmatter hooks do NOT fire for symlink-installed skills (confirmed 2026-03-24). Use `~/.claude/settings.json` with absolute paths instead.
- SDD enforcement hook: `PreToolUse` → `Agent` → `sdd-pre-dispatch-hook.sh` (path in settings.json). Hook self-resolves `SUPERPOWERS_ROOT` from `BASH_SOURCE`; override via env var for team distribution.
- Bash report guard: `PreToolUse` → `Bash` → same directory `/scripts/sdd-report-guard.sh`
- Hook blocks implementer dispatches without: DEVIATIONS.md, reports/ dir, previous task's 3 report files (>50 bytes each), Task 0 report (if Source Contracts), dispatch provenance log entries, checkpoint file, context summary (at midpoint), token estimation (task header in plan)
- Hook injects `additionalContext` reminder on every allowed dispatch
- Reviewers log to `reports/.dispatch-log` then pass through (exit 0)
- **Dispatch provenance**: The hook logs reviewer dispatches to `reports/.dispatch-log` with `task=N type={spec-review|quality-review}`. On implementer dispatch, Check 4c verifies matching entries exist. Controllers cannot satisfy the review gate by self-writing review files — only actual Agent tool dispatches through the hook create log entries. Minimum-tier quality reviews are exempt (file must be named `task-NNN-quality-review-minimum-tier.md`).
- **Checkpoint file gate** (Check 5c): Requires `reports/checkpoint-pre-dispatch-NNN.json` (>50 bytes) before dispatching task NNN. Forces the controller to run `controller-checkpoint.py` and save its output.
- **Token estimation** (Check 6): Now BLOCKS (not warns) when the task header isn't found in any plan file. Script errors still warn.
- **Context summary** (Check 6b): Now BLOCKS (not warns) past the midpoint without `reports/context-summary.md`.
- **Partner review gate** (Check 5d): Requires `reports/partner-review-NNN.md` (>50 bytes) before dispatching task NNN (Task 0 exempt). The controller must dispatch the partner agent (see `controller-partner-prompt.md`) or write a minimum-tier review. The partner independently verifies dispatch quality -- context completeness, accuracy against plan, prior task awareness, and escalation check.
- Plan validation gate: `PreToolUse` → `Skill` → `.../skills/writing-plans/scripts/plan-validation-gate-hook.sh`
- Gate blocks `subagent-driven-development` and `executing-plans` invocation if: validate-plan.py FAIL on any scoped plan file, `plan-review-report.md` missing/empty (<50 bytes), or `.active-feature` file absent/invalid
- Plan file scoping: primary = `<feature-dir>/plan-manifest.txt` (explicit file list from writing-plans skill; resolved via `.active-feature`); fallback = git diff against base branch (files changed on current branch). Old plans from prior features are never validated.
- `plan-validation-gate-hook.sh` and `sdd-stop-hook.sh` now use `SUPERPOWERS_ROOT` (self-resolved via `BASH_SOURCE`) for portable path resolution.
- Rollback: remove Agent matcher block and sdd-report-guard.sh entry from PreToolUse in `~/.claude/settings.json`
- Full plan: `docs/plans/2026-03-24-hooks-enforcement-plan.md`
- Research: `docs/plans/2026-03-24-deterministic-ai-agent-discipline-hooks-analysis.md` — Gemini deep research on hooks enforcement, symlink issues, advisory instruction failures, Swiss Cheese defense model, and community patterns (March 2026)
- **Pre-Completion Gates** (added 2026-04-21, commit `1de0a5f`): `controller-checkpoint.py` pre-completion phase blocks on three additional checks before allowing SDD completion:
  - Honesty check log present (`reports/honesty-check.md`, 9 required questions answered)
  - Trace audit complete (`reports/trace-audit.md` from `extract-execution-trace.py` + `trace-auditor-prompt.md`)
  - Minimum-tier quality review ratio ≤ 20% (too many minimum-tier reviews triggers FAIL)
- Stop hook (`sdd-stop-hook.sh`) captures honesty logs globally so trace audit can cross-reference across sessions.

## Pydantic Validation (Phase 1 + Phase 2)
- Models at `skills/scripts/models/` — `_base.py`, `plan.py`, `handoff.py`, `errors.py`, `validators.py`
- `implementer_report.py` — ImplementerReport model (YAML frontmatter + markdown body), 2 validators
- `checkpoint_result.py` — CheckpointResult model (pure JSON), 3 validators
- Two base classes: `StrictModel` (nested types, `extra="forbid"`) and `SchemaVersionedModel` (top-level artifacts, `schema_version` pinned)
- CLI: `python3 validators.py plan <path>` / `python3 validators.py handoff <dir>`
- CLI: `python3 validators.py report <path>` — validates implementer report frontmatter
- `validate-report.py` runs Pydantic validation before prose section checks
- Exit codes: 0 pass / 1 validation fail / 2 infrastructure
- Bypass: `export SUPERPOWERS_VALIDATOR_BYPASS=1` (emergency unblock, stderr warning)
- Schema version: `CURRENT_SCHEMA_VERSION = 1` in `_base.py`. Bump per `docs/plans/2026-04-24-pydantic-meta-design.md` Section 4.2.
- Plans and reports without YAML frontmatter are hard FAILs — add frontmatter to validate.

## Worktree Sessions
- Hooks receive CWD from session start, NOT from `! cd`. Worktree SDD sessions must be started FROM the worktree: `cd /path/to/worktree && claude`
- `! cd` changes the prompt CWD but NOT the hook CWD — hooks always run from the original session directory
- Branch check blocks on main when SDD artifacts exist (agent drifted out of worktree). Override with `.allow-main` file.

## .active-feature File
- Single-line plaintext file at project root containing relative path to active feature directory
- Format: `docs/imp-plans/YYYY-MM-DD-<feature-name>`
- Created by entry-point skills (brainstorming, writing-plans, handoff-acceptance)
- Read by all hooks for artifact path resolution
- Cleaned up by `finishing-a-development-branch`
- Gitignored — workspace state, not project state
- Conflict detection: entry-point skills check for stale/conflicting `.active-feature` at startup

## Hook Development Gotchas
- Hook scripts use `$PYTHON` (resolved to `$SUPERPOWERS_ROOT/.venv/bin/python3`). Scripts called by hooks that import PyYAML or Pydantic MUST use this — system `python3` doesn't have these packages. If adding a new `python3` call to a hook, use `$PYTHON` instead.
- Stop hooks: use `systemMessage` not `hookSpecificOutput.additionalContext` (not supported for Stop events)
- Bash hooks: avoid `set -u` — jq pipe chains produce empty vars that cause silent exits with no stderr
- Permission globs: `*` does NOT cross path separators in Bash permissions (`**` is literal, not recursive). Use `/*/*` for two-level paths. The `!`...`` preprocessor rejects piped commands — use wrapper scripts instead.
- Pre-execution audit gate: `reports/pre-execution-audit.md` must exist (>50 bytes) before any Task dispatch. Creates a mandatory honesty checkpoint between planning and execution.
- Pre-dispatch hook assumes sequential task execution. TDD reordering (test tasks before implementation) triggers false blocks because the hook requires task N-1 reports before allowing task N. Workaround: use non-implementer description patterns for test-writing dispatches (they bypass the implementer gate).
- controller-checkpoint.py pre-execution phase reports FAIL on `Source Contracts: None` — it treats "None" as non-empty. This is a false positive when the writing-plans skill requires the field present. Log as accepted deviation and proceed.

## Global Settings Changes
Four additions to `~/.claude/settings.json`:
1. `PreToolUse` → `Agent` matcher: SDD pre-dispatch enforcement hook (absolute path in settings.json, self-resolves internally via SUPERPOWERS_ROOT)
2. `PreToolUse` → `Bash` matcher: report forgery guard (absolute path in settings.json)
3. `PreToolUse` → `Skill` matcher: handoff-gate-hook + plan-validation-gate-hook (absolute paths)
4. `permissions.allow`: `Bash(bash ~/.claude/skills/superpowers/scripts/strip-frontmatter.sh *)` for skill command stub loading. Command stubs use `strip-frontmatter.sh` (single command, no pipe) instead of `cat | awk` (piped compound command). The `!`...`` preprocessor has a stricter permission checker than the Bash tool — it rejects piped commands even when individual subcommands are allowed. The helper script at `skills/scripts/strip-frontmatter.sh` eliminates the pipe.

## Execution Trace Audit
- `extract-execution-trace.py` parses `.jsonl` session files into structured JSON with per-task records and 6 anomaly detection rules
- `trace-auditor-prompt.md` dispatches a subagent to review the trace for skipped reviews, unlogged concerns, missing reports
- Integrated as Pre-Completion Gate step 8 in the SDD skill
- To find current session file: `ls -t ~/.claude/projects/*/$(pwd | sed 's|/|%|g')/*.jsonl | head -1`

## Output Path Convention
All feature artifacts are consolidated in a per-feature directory:
- Feature directory → `docs/imp-plans/YYYY-MM-DD-<feature-name>/`
- Design specs → `<feature-dir>/spec.md` and `spec-distilled.md`
- Implementation plans → `<feature-dir>/plan.md` and `module-N-*.md`
- Plan manifest → `<feature-dir>/plan-manifest.txt`
- Plan review → `<feature-dir>/plan-review-report.md`
- Deviations → `<feature-dir>/deviations.md`
- All execution reports → `<feature-dir>/reports/`

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
- macOS gotcha: BSD `sed` fails on curly brace range expressions. Use `skills/scripts/strip-frontmatter.sh` to strip YAML frontmatter (wraps the awk command). Command stubs use this script to avoid piped commands that the `!`...`` preprocessor rejects.
