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
- Saved-prompt commands (added 2026-06-03): `~/.claude/commands/honesty.md` + `honesty-sdd.md` → `./commands/*.md` (per-file symlinks, matching the `runtime-qa-tools.md` precedent). Hand-authored top-level personal commands invoked as `/honesty` and `/honesty-sdd` (no namespace). **Source IS version-controlled in this repo's `commands/` dir** — UNLIKE the auto-generated `superpowers:` stubs above. `/honesty` is general-purpose (net-new); `/honesty-sdd` is a curated copy of `skills/subagent-driven-development/honesty-check-prompt.md` — keep in sync if those 9 questions change.
- Hook: SessionStart in `~/.claude/settings.json` calls `./hooks/session-start` with `CLAUDE_PLUGIN_ROOT` set

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
- `_report_utils.py` — shared library for report parsing (single source of truth — do NOT duplicate logic). Also hosts `_unfenced_content` (the fence-aware line-blanking helper imported by validate-plan.py + controller-checkpoint.py since N5/SSOT, 2026-06-10). Its `implementer_report` import is LAZY (module `__getattr__`) — importing `_unfenced_content` must never pull pydantic, because the plan-validation gate runs validate-plan.py with bare `python3`.
- `_midpoint.py` — shared `compute_midpoint(start, end)` for materialize-manifest.py and transition-module.py (added 2026-05-20; consolidates the previously triplicated formula). Future SDD scripts that need it MUST import from here.
- `estimate-task-tokens.py` — pre-dispatch context budget check (OK/WARNING/TOO_LARGE)
- `validate-report.py` — two-layer report validation: Pydantic frontmatter (via validators.py) then 5 prose sections
- `controller-checkpoint.py` — 3-phase controller health (pre-execution/pre-dispatch/pre-completion). Supports `--manifest` flag (added 2026-05-20, Task 14): reads plan_file, tier, enforcement from `.sdd-session.json` via `_load_manifest_config()` (which also stashes `manifest_task_range` + `manifest_has_prior_modules` since N18). Micro tier gates Checks 5/6 (honesty + trace audit) to SKIP. Since 2026-06-10: pre-dispatch module-boundary skip-guard (N18), pre-execution `Source Contracts: None` = OK (N7), pre-completion Check 10 integration-test gate (C2) with `_resolve_base_ref` (newest-merge-base) + `_in_changeset` helpers.
- `context-summary.py` — compresses completed task reports into one summary file
- `validate-plan.py` — mechanical plan structure checks (size, sections, Task 0). Added `enforcement_tier` validation 2026-05-20: BLOCKER on invalid tier; WARNING on micro + >3 tasks; WARNING on micro + modules. Since 2026-06-10 (C2): advisory `integration_test_risk_surface` WARNING + sections entry when risk-surface keywords appear without an `integration_test` declaration; stdlib-only property restored (fence helper imported lazily from `_report_utils`).
- `materialize-manifest.py` — (added 2026-05-20, Module 1) writes `.sdd-session.json` from plan frontmatter. Reads `enforcement_tier` (default `standard`), produces tier-specific `enforcement` + `process_requirements` dicts via `TIER_PROFILES`. Imports `compute_midpoint` from `_midpoint.py`.
- `transition-module.py` — (added 2026-05-20, Module 3) manages module boundary lifecycle. Validates completion, archives reports to `archive-<module>/`, updates manifest, archives + truncates dispatch log, appends transition row to deviations. Imports `compute_midpoint` from `_midpoint.py`. **First live run 2026-06-10 (sdd-cleanup-and-integration-gate Module 1→2): clean, zero manual workarounds** — and it surfaced N18 (checkpoint pre-dispatch lacked the boundary guard), fixed same-day. Since 2026-06-10: provenance gated only on `enforcement.dispatch_provenance` (N12); main-plan fallback for verification ids when `module.file` empty (N17).
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

Known conflict files (always): `CLAUDE.md` (other historical conflict files were resolved by the 2026-05-07 general-purpose migration; see `docs/ARaymond-customization-manifest.md` Upstream Conflict Files for current state)
Likely conflict files (when upstream touches these): `brainstorming/SKILL.md`, `writing-plans/SKILL.md`, `subagent-driven-development/SKILL.md`, `using-superpowers/SKILL.md`, `writing-skills/SKILL.md`

Last sync: `80fc5c5` on 2026-05-07

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
# Agent symlink must be ABSENT (post-2026-05-07 general-purpose migration)
[ ! -e ~/.claude/agents/superpowers-code-reviewer.md ] \
  && echo "OK — agent symlink absent (correct post-migration state)" \
  || echo "STALE — agent symlink still present; run: rm ~/.claude/agents/superpowers-code-reviewer.md"
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
Quick reference: 5 test layers — regression (static, 145 checks: 142 PASS / 3 advisory WARNING / 0 FAIL), install (static, 104 checks), unit (pytest, 458 tests), integration (e2e pipeline, 12 steps), behavior (API, ~15m). Structural PASS ≠ semantic PASS — run all static + integration tests for significant changes. Details below.

- `tests/ARaymond-skill-regression/validate-all-skills.py` — regression test, currently **142 PASS / 3 advisory WARNING / 0 FAIL** (result PASS-with-warnings). Tests frontmatter, size, cross-refs, scripts, sections, Python 3.9 compat. The 3 WARNINGs are advisory soft-threshold notices (writing-plans/SKILL.md body is **4727 words** by the suite's count — `wc -w` reports 4753 for the whole file — over the 4000 soft-warning threshold but under the 5000 hard limit; only ~273 words of headroom remain, so any addition needs an offsetting `references/` extraction; SDD SKILL word count; 2 historical bare-DEVIATIONS.md refs). Run after ANY skill edit: `python3 tests/ARaymond-skill-regression/validate-all-skills.py`
- `docs/testing.md` describes the integration test framework but references a plugin-based setup (`superpowers@superpowers-dev`) — not applicable to this fork's symlink install
- Token analysis works standalone: `python3 tests/claude-code/analyze-token-usage.py <session.jsonl>`
- `tests/ARaymond-installation/verify-symlink-install.sh` — 104 checks for symlink+command-stub architecture (no API calls). Includes a regression guard that pins `hooks/session-start`'s `EXPECTED_SKILL_COUNT`/`EXPECTED_CMD_COUNT` to the real filesystem counts so adding or removing a skill without updating the hook fails the test. Run after upstream merges or installation changes.
- `tests/unit/` — 458 pytest tests (was 405; +53 across the **sdd-cleanup-and-integration-gate** feature: N16 verification-report exemption (`test_n16_verification_report.py`, 8), N9 plan-loading helpers (`test_n9_plan_loading_helpers.py`, 7), N5 fence-aware parsing + N7 valid-absent (`test_fence_aware_parsing.py`, 7), N12/N17 transition gating (`test_transition_module.py`, +3), N1 hook multi-error accumulation (`test_n1_multi_error_accumulation.py`, 1), N18 checkpoint boundary skip-guard (`test_checkpoint_archive_aware.py`, +5), and C2 integration-test gate — model/WARNING/Check 10 incl. stale-origin + malformed-declaration fixtures (`test_c2_integration_gate.py`, 22). Prior +25 from **sdd-enforcement-hardening**: skill-bypass-hook blocking + I1 regex/C1 pipe-bug tests (`test_sdd_skill_enforcement.py`, 10), archive-aware checkpoint lookups (`test_checkpoint_archive_aware.py`, 4), Check 4c skip-guard + Check 5 archive glob (`test_sdd_hook_hardening.py`, 4), hook↔transition minimum-signal SSOT agreement (`test_ssot_minimum_agreement.py`, 4), and transition provenance + verification exemption + N11 recompute (`test_transition_module.py`, +3). The prior +29 came from the **pipeline-flexibility** feature: `entry_mode`/`task_type` model tests (`test_plan_model.py`), verification write-keyword heuristic (`test_validate_plan.py`), hook `task_type` classification + implementer-dispatch-log format (`test_sdd_classification.py`), and checkpoint **verification-ratio cap** + **git-reality** checks (`test_pre_completion_gates.py`)). Pydantic models (implementer_report, checkpoint_result, plan incl. **`review_tier`** + **`task_type`** + **`entry_mode`**, sdd_session, schema versioning), validators CLI (plan, handoff, report, session subcommands), validate-plan.py (**review_tier heuristic**, **verification write-keyword heuristic**), controller-checkpoint.py (stale artifacts, honesty check, trace audit, minimum-tier ratio incl. **declared-minimum exclusion**, **verification-ratio cap >30%**, **git-reality check**, manifest-mode), sdd-pre-dispatch-hook.sh (**3-stage classification: general-purpose reviewer logged / implementer enforced / ad-hoc passthrough; manifest guard; dispatch-log auto-create; inline validation excerpts; `task_type` verification review-skip**), sdd-report-guard.sh, sdd-stop-hook.sh, transition-module.py. Test helpers (`sdd_test_helpers.py`) run in **manifest mode** (`_write_manifest`). Run: `.venv/bin/python3 -m pytest tests/unit/ -v`
- `tests/integration/sdd-e2e-test.sh` — composed-pipeline smoke test (added 2026-05-20), now **12 steps**: Step 11 (added 2026-06-10, sdd-cleanup-and-integration-gate) declares an `integration_test` in plan frontmatter, creates the file untracked, runs pre-completion, and asserts `integration_test_present` PASSes — the live C2 Check 10 proof. Earlier steps: `materialize-manifest.py → validators.py session → controller-checkpoint.py --manifest → transition-module.py → post-transition checkpoint → review_tier-modules exclusion`. Step 8 (added 2026-05-29) drives pre-completion against a manifest whose NON-active module declares `review_tier:minimum` tasks and asserts they're excluded from the ratio (covers the Task 3 path-resolution glue). Steps 9-10 (added 2026-05-31, pipeline-flexibility) validate a `task_type: verification` plan through `validate-plan.py` and assert the verification write-keyword WARNING fires. Step 7b (added 2026-06-01, sdd-enforcement-hardening) dispatches the module-2 first task through the live hook **after** a transition and asserts it is allowed — the live proof of both the N3a Check 4c skip-guard and the N11 `context_summary_at` recompute. `PROJECT` now resolves from the script location (repo root) so the e2e tests THIS checkout, not a hardcoded main path. Caught one integration bug (`_load_manifest_config` missing feature_dir join) on first run that all unit tests had missed. Run before declaring SDD feature work complete: `bash tests/integration/sdd-e2e-test.sh`
- Run all static + integration after upstream merges: `bash tests/ARaymond-installation/verify-symlink-install.sh && python3 tests/ARaymond-skill-regression/validate-all-skills.py && bash tests/integration/sdd-e2e-test.sh`
- macOS PDF reading: requires `brew install poppler` for `pdftotext` command
- All other test suites (`tests/claude-code/`, `tests/skill-triggering/`, `tests/explicit-skill-requests/`) use `--plugin-dir` — they test plugin mode, NOT the symlink install
- macOS has no `timeout` command — test scripts use background-process-kill pattern instead
- `claude -p --output-format stream-json` requires `--verbose` flag — headless tests must include both
- Avoid running `claude -p` integration tests from within an active Claude session — nested API calls exhaust quota quickly

## Process Improvement Findings (`docs/process-improvement-findings/`)
Real-world issues from using superpowers in production projects. Use these to inform fork customizations.
- `BACKLOG.md` — **living ledger** of open/in-flight/done improvements (stable IDs B*/I*/C*/N*/P*, size estimates, sequencing). Start here for "what's left to improve and how big is it."
- `2026-05-21-skill-evaluation.md` — Cross-repo Critical findings (plan-reference code unrun, integration bugs pass unit tests, controller skips discipline under pressure)
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
  - Honesty check log present (`reports/honesty-check-*.md`, 9 required questions answered)
  - Trace audit complete (`reports/execution-trace-audit.md` from `extract-execution-trace.py` + `trace-auditor-prompt.md`)
  - Minimum-tier quality review ratio ≤ 50% (the actual code threshold; do not assume 20% from older docs)
- Stop hook (`sdd-stop-hook.sh`) captures honesty logs globally so trace audit can cross-reference across sessions.
- **SDD Hook Improvements (2026-05-29)**: `sdd-pre-dispatch-hook.sh` restructured into a **3-stage manifest-mode classification pipeline** — order is load-bearing: **reviewer detection → implementer detection → passthrough**.
  - **Item 1 fix**: a `general-purpose` reviewer is now correctly **logged** (previously a `subagent_type` passthrough at the old line 169 exited *before* reviewer detection, so general-purpose reviewers were silently skipped). A `general-purpose` implementer is correctly **enforced**; genuine ad-hoc dispatches (non-reviewer/non-implementer) pass through without logging or enforcement.
  - **Item 3**: the dispatch log is **auto-created** on the first reviewer dispatch (`mkdir -p` + `touch`, idempotent) — no longer requires `reports/` to pre-exist.
  - **Item 2**: when the previous task's implementer report fails `validate-report.py`, the BLOCKED message now **embeds the first 12 lines of the validator output** (`head -n 12`) so the controller sees the failing field name, not just the exit code. (`head -n 12`, NOT `head -n 5`: the validator prints a 4-line banner + blank first; the first field name is at output line 6.)
  - **Item 5**: the **legacy non-manifest path is removed entirely**. Manifest mode is now required: no manifest + SDD artifacts present → **BLOCK** (exit 2, message names the missing manifest); no manifest + no artifacts → ALLOW (not an SDD session). All dead legacy `else` branches removed from the enforcement checks.
  - **Item 4 (review_tier)**: plans may declare per-task `review_tier: minimum` (orthogonal to `enforcement_tier`); the pre-completion minimum-tier ratio (`controller-checkpoint.py`) excludes declared-minimum tasks from BOTH numerator and denominator (quality + partner), aggregating declarations across all module plan files. `validate-plan.py` warns on `review_tier:minimum` for high-risk task titles.
  - Feature dir: `docs/imp-plans/2026-05-28-sdd-hook-improvements/`.
- **SDD Enforcement Hardening (2026-06-01)**: closes the multi-module SDD enforcement gaps so a 2-module plan runs end-to-end through `transition-module.py` with zero manual workarounds, and promotes the SDD skill-bypass hook from advisory to blocking. Feature dir: `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/`.
  - **N3a (Check 4c skip-guard)**: Check 4c (dispatch provenance for task N-1) now **skips when `PREV < MANIFEST_TASK_START`** — i.e. the previous task belongs to a prior/archived module, or precedes a no-Task-0 plan's first task. Boundary provenance is not lost: it is re-verified at transition time by `transition-module.py:validate_module_completion` (the N3b sibling). Plans that legitimately declare Task 0, and non-first tasks within a module, are still fully provenance-checked.
  - **N10 (Check 5 archive glob)**: Check 5's Task-0 lookup now globs `archive-*/` as well, so a Source-Contracts plan still finds an archived Task 0 at module 2. **Local glob only** — the shared `task_report_glob` helper is unchanged.
  - **N3b (transition provenance)**: `transition-module.py:validate_module_completion` now verifies dispatch-log provenance (the same `task=<id> type=<review>` substring Check 4c greps) for each completing-module task **before** it truncates the live log. Quality-review provenance is **waived when the file `task-NNN-quality-review-minimum-tier.md` exists** (the file signal, NOT the `review_tier:minimum` plan declaration); a per-task **`task_type: verification`** exemption (mirroring the hook) skips spec/quality/provenance for verification tasks.
  - **N11 (context_summary_at recompute)**: `transition-module.py:transition()` now recomputes `enforcement.context_summary_at` for the **next** module's range on transition. Previously it stayed pinned to the completed module's midpoint, firing Check 6b early for later-module tasks.
  - **N4 (archive-aware pre-completion)**: `controller-checkpoint.py` `find_report_file` / `find_all_report_files` now recurse into `archive-*/`, so the pre-completion gate passes with archived (completed-module) reports. Archive-awareness applies to **exactly these two lookups** (N4) plus the hook's Check 5 Task-0 lookup (N10) — **every other report glob stays intentionally flat** (e.g. `task_report_glob`, the per-task report checks).
  - **C5 (skill-bypass hook now blocking)**: `sdd-skill-enforcement-hook.sh` is now **blocking** (`exit 2`) when it detects an explicit SDD imperative + an implementation-file write + the SDD skill not loaded. `SUPERPOWERS_SDD_BYPASS` is the escape hatch (see "Hook Development Gotchas"). Its settings.json registration is unchanged — only the hook's behavior changed, not its matcher/path.
- **SDD Cleanup & Integration Gate (2026-06-10)**: sprint-3 feature (2 modules, 11 tasks + N18, executed via SDD with the **first-ever live `transition-module.py` module transition** — which itself surfaced and fixed N18). Feature dir: `docs/imp-plans/2026-06-05-sdd-cleanup-and-integration-gate/`.
  - **Module 1 (cleanup)**: **N16** ImplementerReport gains `task_type` (verification reports validate with empty `files_changed`; implementation+DONE still FAILs). **N9** `_task_ids_where(plan_contents, field, value)` + `_load_all_plan_contents(manifest, git_root)` collapse the duplicated frontmatter walkers in controller-checkpoint.py (also fixed a latent double-count/parent-omission in manifest-mode aggregation). **N5** fence-aware task-header parsing at ALL sites in validate-plan.py + controller-checkpoint.py via a single `_unfenced_content` helper consolidated into `_report_utils.py` (SSOT; `_report_utils`'s `implementer_report` import is now lazy via module `__getattr__`, so validate-plan.py is stdlib-only again — the plan-validation gate invokes it with bare `python3`). **N7** pre-execution treats `Source Contracts: None` as valid-absent (OK, not FAIL). **N12** transition gates provenance ONLY on `enforcement.dispatch_provenance` (file-existence stays on review modes ≠ skip) — hook↔transition SSOT. **N17** transition falls back to the main plan for verification-id lookup when `module.file` is empty (mirrors the hook). **N1** regression test pins the hook's multi-error accumulation. **N13** hardening-plan mkdir backport corrected (the originally prescribed backport was a no-op — plan defect found by the remediated Task 3 quality review).
  - **N18 (live-discovered)**: `controller-checkpoint.py` pre-dispatch now has the hook's N3a-mirror **module-boundary skip-guard** — previous-task checks SKIP when `previous_task < manifest task_range[0]` (boundary completion is re-verified by `transition-module.py`; checkboxes/report-completeness are backstopped terminally by pre-completion). Detail string distinguishes prior-module vs no-Task-0 cells via `manifest_has_prior_modules`.
  - **Module 2 (C2 integration-test gate)**: plans may declare `integration_test: {path: ...}` in frontmatter (IntegrationTest model: non-absolute, no `..`, non-empty). `validate-plan.py` emits an advisory `integration_test_risk_surface` WARNING (+ sections entry) when risk-surface keywords (router/middleware/auth/migration/cache/cors/security) appear without a declaration — note: raw-content scan, so plans QUOTING those words in code fences also warn (advisory-only; the gate blocks only on FAIL). **Pre-completion Check 10** (`integration_test_present`, blocker == check key) verifies each declared path `is_file()` AND is in the feature changeset: untracked ∪ diff vs merge-base, with the base ref chosen as the resolvable candidate (origin/HEAD/main/master) whose **merge-base with HEAD is newest** (a stale unpushed origin/HEAD is fail-open otherwise — found live in this repo) and HEAD-diff fallback when merge-base fails. Present-but-MALFORMED declarations (flat string, empty path, no path key) → FAIL with shape guidance (closing a silent fail-open found by the final review). No declaration / explicit null → PASS "check skipped". Docs in `writing-plans/SKILL.md` ("Declaring `integration_test` per Plan"); e2e Step 11.
  - **Known limitation (accepted, BACKLOG)**: pre-completion AGGREGATE gates (Check 7 min-tier ratio, Check 9 git-reality) only police the final module after transitions (archived reviews leave the flat glob; the dispatch log is truncated) — per-task existence/provenance IS boundary-verified by `validate_module_completion`; only cross-module policy aggregates lose visibility.

## Pydantic Validation (Phase 1 + Phase 2)
- Models at `skills/scripts/models/` — `_base.py`, `plan.py`, `handoff.py`, `errors.py`, `validators.py`
- `implementer_report.py` — ImplementerReport model (YAML frontmatter + markdown body), 2 validators
- `checkpoint_result.py` — CheckpointResult model (pure JSON), 3 validators
- `sdd_session.py` — (added 2026-05-20, Module 1) `SddSession` model for `.sdd-session.json` manifests. Exports `TIER_PROFILES` dict mapping tier name to `enforcement` + `process_requirements` substructures. Tier literal: `"micro" | "standard"`. Includes `midpoint_in_range` model validator.
- Two base classes: `StrictModel` (nested types, `extra="forbid"`) and `SchemaVersionedModel` (top-level artifacts, `schema_version` pinned)
- CLI: `python3 validators.py plan <path>` / `python3 validators.py handoff <dir>`
- CLI: `python3 validators.py report <path>` — validates implementer report frontmatter
- CLI: `python3 validators.py session <path>` — (added 2026-05-20, Module 4 Task 16) validates `.sdd-session.json` manifests
- `validate-report.py` runs Pydantic validation before prose section checks
- Exit codes: 0 pass / 1 validation fail / 2 infrastructure
- Bypass: `export SUPERPOWERS_VALIDATOR_BYPASS=1` (emergency unblock, stderr warning)
- Schema version: `CURRENT_SCHEMA_VERSION = 1` in `_base.py`. Bump per `docs/plans/2026-04-24-pydantic-meta-design.md` Section 4.2.
- Plans and reports without YAML frontmatter are hard FAILs — add frontmatter to validate.
- `plan.py` `Task` model has an optional **`review_tier: Literal["minimum", "full"] = "full"`** field (added 2026-05-29, SDD Hook Improvements). Optional, defaults to `"full"`, orthogonal to `enforcement_tier`. Non-breaking — `CURRENT_SCHEMA_VERSION` was NOT bumped.
- `plan.py` adds two more optional fields (added 2026-05-31, Pipeline Flexibility; non-breaking, no schema bump): `Task.task_type: Literal["implementation", "verification"] = "implementation"` (orthogonal to `review_tier`; `verification` tasks run no-code checks and the hook skips their spec/quality review gates) and `Plan.entry_mode: Literal["brainstorming", "direct"] = "brainstorming"` (records whether the plan came through brainstorming or direct-to-`writing-plans`).
- `plan.py` also has `IntegrationTest(StrictModel)` + optional `Plan.integration_test` (added 2026-06-10, C2; non-breaking, no schema bump): `path` must be non-empty, non-absolute, no `..` segments. Consumed by validate-plan.py's risk-surface WARNING and pre-completion Check 10. `implementer_report.py` gained `task_type: Literal["implementation","verification"] = "implementation"` (N16) — verification reports validate with empty `files_changed`.

## Adaptive Enforcement Tiers (2026-05-20)
Tier-based SDD enforcement for varying feature complexity. Plans declare `enforcement_tier: micro|standard` in YAML frontmatter; SDD ingestion materializes `.sdd-session.json` from it; the hook reads the manifest exclusively. **(2026-05-29, SDD Hook Improvements:) the legacy non-manifest fallback was REMOVED — manifest mode is now required; a session with SDD artifacts but no manifest is BLOCKED with guidance to run `materialize-manifest.py`.**

- **Tiers**:
  - `standard` (default): full enforcement — partner reviews, checkpoint files, pre-execution audit, dispatch provenance, dispatched spec/quality reviews.
  - `micro`: relaxed enforcement for 1-2 task changes — self-review OK, no partner review, no real-time hook enforcement. Pre-completion gate skips honesty + trace audit.
- **Materialization**: `materialize-manifest.py --plan-file <plan.md> --feature-dir <dir>` writes the manifest from plan frontmatter. `validate-plan.py` warns on micro + >3 tasks, micro + modules.
- **Multi-module support**: `modules:` array in plan frontmatter declares per-module task ranges + per-module plan files. `transition-module.py --manifest <manifest> --completed-module <name> --next-module <name>` archives the completed module's reports, updates manifest, truncates dispatch log, appends to deviations.
- **Manifest is git-root-relative**: all `paths` entries (feature_dir, reports_dir, dispatch_log, deviations_file, plan_file) are relative to git root. Scripts MUST resolve via `git rev-parse --show-toplevel`. `active_module_file` is a bare filename (Module 1 convention); reconstruct as `<git_root>/<feature_dir>/<active_module_file>`.
- **Hook integration**: `sdd-pre-dispatch-hook.sh` detects manifest mode (`.sdd-session.json` exists), reads `enforcement.*` flags, conditionalizes 8 gate checks (pre_execution_audit, partner_review, dispatch_provenance, checkpoint_files, context_summary_at). Injects `process_requirements` into `additionalContext` on every allowed dispatch.
- **Documentation**: feature spec at `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/`. End-to-end smoke test at `tests/integration/sdd-e2e-test.sh`. 40 deviation rows in `deviations.md`.

## Pipeline Flexibility (2026-05-31)
Two orthogonal dials for the planning/execution pipeline (BACKLOG B6 + P1), merged to main 2026-05-31 (merge `e53cbaf`). Feature dir: `docs/imp-plans/2026-05-31-pipeline-flexibility/`.

- **`task_type: verification` (B6)** — a per-task dial for no-code tasks (run a check, grep, doc edit) that skips the full dispatch/review cycle. Model field `Task.task_type` (see Pydantic section). Enforcement is a **paired anti-smuggling guard** (chosen instead of C4 computed heuristics):
  - **Hook review-skip** (`sdd-pre-dispatch-hook.sh`): `get_task_type()` reads the per-task frontmatter (via `$PYTHON`/PyYAML); Checks 4b/4c/5d skip the spec/quality/partner review gates for a `verification` task. The hook still **logs the implementer dispatch** (`<ISO> DISPATCH implementer task=N type=implementer`) so the git-reality check can cross-reference.
  - **Checkpoint verification-ratio cap** (`controller-checkpoint.py` Check 8): pre-completion FAILs if `verification_count / total_tasks > 0.30` — stops a plan from smuggling real implementation past review by labeling tasks `verification`.
  - **Checkpoint git-reality check** (Check 9): cross-references the dispatch log against `git` — a task that dispatched an implementer (logged) but produced no code change, or vice-versa, is flagged.
  - **`validate-plan.py` write-keyword WARNING**: a `verification` task whose title contains a write-suggesting verb (create/add/implement/fix/modify/write/update/refactor/migrate/delete/remove) gets a plan-time WARNING.
- **`entry_mode: direct` (P1)** — direct-to-`writing-plans` entry that re-installs the setup guardrails brainstorming normally provides. Model field `Plan.entry_mode`. `writing-plans/SKILL.md` Step 0.5 ("Resolve feature directory") ports brainstorming's 4-branch stale-`.active-feature` conflict detection + worktree/branch guard, optionally runs `check-distillation.sh` when a distilled spec is supplied, and records the entry mode in plan frontmatter.
- **Docs**: SDD SKILL.md "Verification Tasks" section; `writing-plans/SKILL.md` "Declaring `task_type` per Task". E2E steps 9-10 (verification-task validation + keyword WARNING). SSOT audit at `docs/process-improvement-findings/2026-05-31-ssot-audit.md`; net-new BACKLOG rows N2–N9.
- **Known follow-ups (BACKLOG)**: **N3** — Check 4c rejects plans whose first in-scope task isn't Task 0 (both no-Task-0 plans and module boundaries; fix: skip PREV check when `PREV < MANIFEST_TASK_START`). **N4** — pre-completion gate isn't archive-aware. **N5** — the `^###\s+Task` regex is fence-blind at BOTH `validate-plan.py:48` and `controller-checkpoint.py:58`. This execution worked around N3/N4 with manual manifest advances (no `transition-module.py`). **Caveat**: the live verification flow has never run in a real SDD session — the running hooks resolve to the main checkout, so coverage is unit + e2e, not a live end-to-end run; the first real post-merge verification task is the first live exercise.
  - **Resolved 2026-06-01 (SDD Enforcement Hardening):** **N3** (both N3a Check 4c skip-guard + N3b transition provenance), **N4** (archive-aware pre-completion lookups), **N10** (Check 5 archive glob), and **N11** (`context_summary_at` recompute on transition) are fixed — a 2-module plan now runs end-to-end through `transition-module.py` with no manual manifest advances. See "Hooks-Based Enforcement → SDD Enforcement Hardening (2026-06-01)". **N5 resolved 2026-06-10** (sdd-cleanup-and-integration-gate — fence-aware parsing at all sites via the shared `_unfenced_content` helper in `_report_utils.py`).
  - **Verification flow first live run (2026-06-03, SDD Enforcement Hardening Task 7):** `task_type:verification` ran live for the first time and surfaced **N16** — `validate-report.py` (`ImplementerReport.files_changed_non_empty_for_done`, implementer_report.py:48-53) rejects a verification report because `files_changed` is legitimately empty. Harmless ONLY when the verification task is LAST (no next-dispatch Check 4b, no per-report pre-completion validation); **fix N16 before any non-last verification task.** Check-9 (git-reality) sequencing: if a verification task surfaces a fix needing a commit, commit it THEN re-dispatch the verification task — Check 9 keys on the LATEST `task=N` implementer timestamp with an open-ended `--after`, so the fix commit must precede the final dispatch. **Multi-module enforcement paths still never run live** (validated by unit+e2e only).

## New Harness Support

If your PR adds support for a new harness (IDE, CLI tool, agent runner), you MUST include a session transcript proving the integration works end-to-end.

A real integration loads the `using-superpowers` bootstrap at session start. The bootstrap is what causes skills to auto-trigger at the right moments. Without it, the skills are dead weight — present on disk but never invoked.

**The acceptance test.** Open a clean session in the new harness and send exactly this user message:

> Let's make a react todo list

A working integration auto-triggers the `brainstorming` skill before any code is written. Paste the complete transcript in the PR.

**These are not real integrations and will be closed:**

- Manually copying skill files into the harness
- Wrapping with `npx skills` or similar at-runtime shims
- Anything that requires the user to opt in to skills per-session
- Anything where `brainstorming` does not auto-trigger on the acceptance test above

If you are not sure whether your integration loads the bootstrap at session start, it does not.

## Skill Changes Require Evaluation

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
- controller-checkpoint.py pre-execution: `Source Contracts: None` is treated as valid-absent (status OK) since the N7 fix (2026-06-10, sdd-cleanup-and-integration-gate). The old behavior FAILed on "None" and required a per-run accepted deviation — that guidance is obsolete; a FAIL here now indicates a genuinely missing/malformed section.
- `SUPERPOWERS_SDD_BYPASS` env var (added 2026-06-01): the escape hatch for the now-blocking `sdd-skill-enforcement-hook.sh`. Set it to allow the write (the hook emits a stderr warning, then exits 0) — mirrors `SUPERPOWERS_VALIDATOR_BYPASS`. Use only to recover from a heuristic false-positive (e.g. an incidental "run the sdd tests" phrasing that trips the SDD-imperative regex).
- The C5 SDD-imperative detection regex (source of truth: `sdd-skill-enforcement-hook.sh:76`) is `\b(invoke|use|run|follow|start|let'?s use)\b.{0,20}\b(subagent-driven-development|sdd)\b` — the `\b` word boundaries around BOTH the verb group and the `sdd` group are the I1 tightening (without them, `reuse the sdd module` / `misuse sdd` / `assddata` false-block). It is verified to behave identically under both `ugrep` and stock BSD `/usr/bin/grep -iE` — so the hook blocks/allows the same way regardless of which `grep` is on PATH. Semantic false-positives (e.g. "run the sdd tests") remain an inherent heuristic limitation; `SUPERPOWERS_SDD_BYPASS` recovers.
- Bash hooks: never pipe a producer into `grep -q` under `set -o pipefail`. When `grep -q` matches it exits early → the upstream producer takes SIGPIPE → pipefail makes the whole pipeline non-zero, so `if producer | grep -q …` reads as NO-match (fail-OPEN). Only triggers past the ~64KB pipe buffer, so small test fixtures hide it (this shipped in `sdd-skill-enforcement-hook.sh` until code review caught it; promoting the hook to blocking turned a latent miss into fail-open-on-every-real-session). Fix: here-string — `grep -qiE "PATTERN" <<< "$VAR"` (no upstream process = no SIGPIPE; pipefail N/A to a non-pipeline).
- Editing ANY of the 7 baselined hooks requires re-capturing the integrity baseline in the SAME change: `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture` + commit `tests/ARaymond-hook-baseline/baseline.txt`. It pins sha256 of every hook script, so any hook edit FAILs `check-hooks.sh` until re-captured (ship together, like migrations+code). It reports hash drift and `settings.json` registration drift separately. (Baseline was stale on main since 2026-04-14 until re-captured 2026-06-03.)

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
- No formal agents are defined in this fork. Code review is dispatched as a `general-purpose` Task carrying the inline `skills/requesting-code-review/code-reviewer.md` template (migrated 2026-05-07 — see `docs/ARaymond-customization-manifest.md` Upstream Sync Log).
- Personal skills (`~/.claude/skills/`) only support one level of nesting for the `/skills` picker. The `superpowers:` namespace in the picker comes from command stubs at `~/.claude/commands/superpowers/`, NOT from the skills directory structure
- Agents do NOT support nested directory namespacing — must use flat files with unique names
- Brainstorm visual companion server: `skills/brainstorming/scripts/start-server.sh` (NOT repo root `scripts/`)
- macOS gotcha: BSD `sed` fails on curly brace range expressions. Use `skills/scripts/strip-frontmatter.sh` to strip YAML frontmatter (wraps the awk command). Command stubs use this script to avoid piped commands that the `!`...`` preprocessor rejects.
