# Superpowers Customization Manifest

**Author**: Aaron Raymond
**Last Updated**: 2026-06-23
**Fork**: `~/projects/claude-custom/superpowers` (from `obra/superpowers`)
**Upstream**: `https://github.com/obra/superpowers`
**Baseline snapshot**: `snapshot-pre-sdd-improvements-v1` at commit `f352ea9`
**Last upstream sync**: v5.1.0 (`f2cbfbe`) merged 2026-05-07 (fork commit `80fc5c5`); v6.0.3 (`896224c`) assessed 2026-06-22 — NOT merged, selective cherry-picks only (see Upstream Sync Log)

---

## Installation Architecture

This fork is installed via symlinks, NOT as a marketplace plugin. The symlink approach makes edits live immediately without cache invalidation, and eliminates the problem of plugin updates overwriting custom prompt templates.

```
~/.claude/skills/superpowers/       → ~/projects/claude-custom/superpowers/skills/
~/.claude/commands/superpowers/*.md  (standalone files — NOT in repo, regenerate per machine)
~/.claude/commands/honesty.md       → ~/projects/claude-custom/superpowers/commands/honesty.md
~/.claude/commands/honesty-sdd.md   → ~/projects/claude-custom/superpowers/commands/honesty-sdd.md
~/.claude/settings.json             (hooks + permissions — NOT in repo)
```

**Key distinction**: The `/skills` picker namespace comes from command stubs at `~/.claude/commands/superpowers/`, NOT from the skills directory structure. Personal skills support only one level of nesting in the picker; command stubs provide the `superpowers:` namespace.

**Saved-prompt commands (added 2026-06-03)**: `commands/honesty.md` and `commands/honesty-sdd.md` are hand-authored top-level personal slash commands (invoked `/honesty`, `/honesty-sdd` — no namespace), version-controlled IN this repo and symlinked into `~/.claude/commands/` (per-file, matching the `runtime-qa-tools.md` precedent). This differs from the `superpowers:` stubs above, which are auto-generated and live outside the repo. `/honesty` is a general-purpose session honesty check (net-new content); `/honesty-sdd` is a curated copy of the SDD dispatch prompt at `skills/subagent-driven-development/honesty-check-prompt.md` — if those 9 questions change, update the command to match. These have no command stubs (they're not skills) and are not counted by `verify-symlink-install.sh`.

---

## Prerequisites

Before installing:

1. Uninstall marketplace plugin (if previously installed): `/plugin uninstall superpowers@claude-plugins-official`
2. Delete orphaned plugin cache: `rm -rf ~/.claude/plugins/cache/claude-plugins-official/superpowers/`
3. Clone fork: `git clone <fork-url> ~/projects/claude-custom/superpowers`
4. Add upstream remote: `git remote add upstream https://github.com/obra/superpowers`

---

## Step 1: Symlink Skills (single parent symlink)

```bash
ln -s ~/projects/claude-custom/superpowers/skills ~/.claude/skills/superpowers
```

All 15 skills are available immediately (14 upstream + 1 new: `handoff-acceptance`).

**Verify:**
```bash
find -L ~/.claude/skills/superpowers -name "SKILL.md" | wc -l
# Expected: 15
```

---

## Step 3: Command Stubs (required for `/skills` picker)

Command stubs must exist for every skill. They live outside the repo — regenerate on each new machine.

**Generate all stubs (run once after install, and after upstream adds skills):**

```bash
for dir in ~/.claude/skills/superpowers/*/; do
  name=$(basename "$dir")
  desc=$(sed -n '/^---$/,/^---$/p' "$dir/SKILL.md" | grep '^description:' | head -1 | sed 's/^description: *//' | sed "s/^'//" | sed "s/'$//")
  cat > ~/.claude/commands/superpowers/"$name".md << CMDEOF
---
name: superpowers:$name
description: $desc
---

!\`cat ~/.claude/skills/superpowers/$name/SKILL.md | awk 'BEGIN{c=0} /^---\$/{c++; next} c>=2{print}'\`
CMDEOF
done
```

**Gotcha**: Changing `description:` in SKILL.md does NOT update the picker. The `!`cat`` preprocessing only pulls body content (stripping frontmatter via the `awk` command). To update the description shown in the picker, edit BOTH the SKILL.md frontmatter AND the command stub's frontmatter independently.

**Verify:**
```bash
ls ~/.claude/commands/superpowers/*.md | wc -l
# Expected: 15 (must match skill count)
```

---

## Step 4: SessionStart Hook

Add this block to `~/.claude/settings.json` inside the `"hooks"` object:

```json
"SessionStart": [
  {
    "matcher": "startup|clear|compact",
    "hooks": [
      {
        "type": "command",
        "command": "CLAUDE_PLUGIN_ROOT=/Users/araymond/projects/claude-custom/superpowers /Users/araymond/projects/claude-custom/superpowers/hooks/session-start",
        "async": false
      }
    ]
  }
]
```

`CLAUDE_PLUGIN_ROOT` must be set in the command so the hook script outputs the correct Claude Code JSON format. Use the absolute path to the physical file — symlink paths fail silently in hook commands.

**Verify:**
```bash
grep -c "session-start" ~/.claude/settings.json
# Expected: 1+
```

---

## Step 5: Enforcement Hooks

Four enforcement hooks were added 2026-03-24. All use absolute paths to physical files (symlink paths cause silent failures — see `docs/plans/2026-03-24-deterministic-ai-agent-discipline-hooks-analysis.md`).

**Important**: Frontmatter hooks in SKILL.md do NOT fire for symlink-installed skills (confirmed 2026-03-24, documented in GitHub issues #5433, #36135, #30874). All hooks must be in `settings.json`.

Add these entries to `~/.claude/settings.json`:

### PreToolUse: Agent matcher (SDD dispatch enforcement)

```json
{
  "matcher": "Agent",
  "hooks": [
    {
      "type": "command",
      "command": "/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh",
      "statusMessage": "Checking SDD dispatch requirements..."
    }
  ]
}
```

Blocks implementer dispatches when: prior task's 3 report files are missing or <50 bytes, DEVIATIONS.md is absent, pre-execution audit is absent, or session is on main/master branch with SDD artifacts present.

### PreToolUse: Bash matcher (anti-forgery guard)

Add `sdd-report-guard.sh` as a second hook under the existing `"Bash"` matcher entry:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/sdd-report-guard.sh"
    }
  ]
}
```

Intercepts `touch` or other trivial Bash writes to `reports/` directory (the bypass path for the 50-byte minimum check).

### PreToolUse: Skill matcher (handoff acceptance + plan validation gates)

```json
{
  "matcher": "Skill",
  "hooks": [
    {
      "type": "command",
      "command": "/Users/araymond/projects/claude-custom/superpowers/skills/handoff-acceptance/scripts/handoff-gate-hook.sh",
      "statusMessage": "Checking handoff acceptance..."
    },
    {
      "type": "command",
      "command": "/Users/araymond/projects/claude-custom/superpowers/skills/writing-plans/scripts/plan-validation-gate-hook.sh",
      "statusMessage": "Checking plan validation..."
    }
  ]
}
```

Two gates on the Skill matcher:
- **handoff-gate-hook**: Blocks planning/SDD skill invocation if an acceptance report does not exist in the project.
- **plan-validation-gate-hook**: Blocks `subagent-driven-development` and `executing-plans` invocation if validate-plan.py fails on any plan file or `plan-review-report.md` is missing/empty (<50 bytes).

### Stop: Pre-completion gate injection

Add `sdd-stop-hook.sh` to the existing `"Stop"` matcher array:

```json
{
  "type": "command",
  "command": "/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/sdd-stop-hook.sh",
  "timeout": 30
}
```

Injects pre-completion gate results into session context at end of turn. Uses `systemMessage` (not `hookSpecificOutput.additionalContext` — Stop events do not support that field).

**Rollback**: Remove the four entries above from `settings.json`. The SessionStart hook is independent and does not need to be rolled back.

---

## Step 6: Global Permission

Add this to the `"permissions"` → `"allow"` array in `~/.claude/settings.json`:

```json
"Bash(cat ~/.claude/skills/superpowers/**)"
```

Required for command stub `!`cat`` preprocessing to load skill content when stubs are invoked. Use `**` (not `*`) — subdirectory paths must match.

---

## Verify Complete Installation

```bash
# Skills: expect 15
find -L ~/.claude/skills/superpowers -name "SKILL.md" | wc -l

# Commands: expect 15 (must match skills)
ls ~/.claude/commands/superpowers/*.md | wc -l

# Session-start hook
grep -c "session-start" ~/.claude/settings.json

# Enforcement hooks
grep -c "sdd-pre-dispatch-hook" ~/.claude/settings.json
grep -c "sdd-report-guard" ~/.claude/settings.json
grep -c "handoff-gate-hook" ~/.claude/settings.json
grep -c "sdd-stop-hook" ~/.claude/settings.json

# Static tests
bash tests/ARaymond-installation/verify-symlink-install.sh
python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

---

## Upstream Sync

```bash
cd ~/projects/claude-custom/superpowers
git fetch upstream
git merge upstream/main
```

After merge, resolve conflicts in these files (all contain fork customizations):

| File | What to Preserve |
|------|-----------------|
| `skills/brainstorming/SKILL.md` | All v0.1 improvements (spec distillation, feature archetypes, worktree step, mandatory handoff) |
| `skills/writing-plans/SKILL.md` | All v0.1 improvements (plan modules, Task 0, Contract Constraints, Feature Footprint, 15-category reviewer) |
| `skills/subagent-driven-development/SKILL.md` | All v0.1 improvements (controller discipline, review enforcement, DEVIATIONS.md, file-based reports, pre-completion gate) |
| `skills/subagent-driven-development/implementer-prompt.md` | 10-section structured report, Contract Constraints passthrough, Source Files mandate |
| `skills/subagent-driven-development/spec-reviewer-prompt.md` | Contract verification, severity gradation, BASE_SHA placeholder |
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | All v0.1 fork improvements (dead code BLOCKING, [NEEDS_CONTEXT] label, IMPLEMENTER_REPORT placeholder, per-file SRP check, contract-constraint tracing) |
| `skills/writing-plans/plan-document-reviewer-prompt.md` | 15-category mechanical checklist, cross-doc audit |
| `skills/using-git-worktrees/SKILL.md` | Worktree location convention. Legacy global dir (`~/.config/superpowers/worktrees/`) removed (A4, v6 sync 2026-06-22) — `.worktrees/` preferred. (CLAUDE.md mandates `.worktrees/` only; the SKILL.md still accepts a `worktrees/` sibling fallback from upstream — minor residual divergence, not yet reconciled.) **2026-06-25 hybrid fix:** Step 1a now branches Case A (no mandate → native `EnterWorktree {name:}`) vs Case B (mandated location/branch → `git worktree add .worktrees/<feature> -b <feature>` then `EnterWorktree {path:}` to switch in place). Step 4 report split: native in-place switch = "continue here" (NO restart); pure-git fallback keeps "NEW SESSION REQUIRED" (preserves the `claude-picker` telemetry line). Resolves the recurring location-conflict-dance + mandatory-restart friction; empirically verified the path-switch re-roots the session CWD (`git rev-parse --show-toplevel` resolves into the worktree); hooks inherit that session CWD (same as the Bash tool), so they bind to the worktree without a new session. Mirrored into global CLAUDE.md "Worktree Convention". |

After merge: if upstream added new skills, create matching command stubs (see Step 3 regeneration script) and run both static test suites.

---

## Skills Inventory (15 total)

### New Skills (1)

**`handoff-acceptance`** — Created 2026-03-23. Verifies external handoff packages (from other agents, teams, or systems) before they are consumed by the Superpowers pipeline. Operates in two modes: acceptance mode (verifying an incoming package) and producer mode (when asked to create a handoff package, surfaces `references/handoff-package-spec.md`). Has no upstream equivalent.

### Rewritten Skills (3)

**`brainstorming`** — Upstream version produces a spec and hands off. V0.1 adds: spec distillation step (produces <500-line distilled spec from full exploration), feature archetype classification (New, Augmentation, Replacement — drives Feature Footprint template in plan writing), mandatory worktree creation step before handing off to writing-plans, mandatory session handoff with copy-pastable `cd` command. Has `distillation-reviewer-prompt.md` and `spec-document-reviewer-prompt.md` as reviewer templates, and `check-distillation.sh` for artifact detection. **2026-07-07 (N38) — scope-fence preservation:** distillation had no category for negative contract material (out-of-scope/deferred lists pattern-matched Rule 2's "rejected alternatives" stripping — the telemetry-exp stable-fact-store distillation dropped its spec's §1.2 fence entirely, review finding M1). Added Distillation Rule 3 ("Scope fences preserved"; rules renumbered 3–6→4–7), a `## Out of scope — do not build` template section preceding Contract Facts, distillation-review checklist item 6, reviewer-prompt fence-preservation check + explicit not-an-artifact carve-out, a scope-boundaries item leading the design-presentation coverage list, and `check-distillation.sh` two-arg mode (see scripts table).

**`writing-plans`** — Upstream version produces an implementation plan. V0.1 adds: plan modularization (800-line/module limit, separate plans per module), Task 0 contract verification (mandatory first task to read source files and verify plan assumptions against ground truth), Contract Constraints section in plan header (passed through to all subagent prompts), Feature Footprint table (maps new/changed/obsolete file surfaces), 15-category mechanical review checklist dispatched before finalizing, `validate-plan.py` structural validation script. Has `plan-document-reviewer-prompt.md` and 3 reference templates (`task-0-template.md`, `module-template.md`, `obsolescence-verification-template.md`). **2026-07-07 (N39):** Execution Handoff menu gains a standard third option — Subagent-Driven in a **fresh session** via a claude-codex-handoff bundle (entry skill `superpowers:subagent-driven-development`; `/pickup` invokes it via the Skill tool, arming the SDD hooks; fresh session starts FROM the worktree). Prefer when the planning session is context-heavy or the plan is multi-module.

**`subagent-driven-development`** — Most extensively modified skill. V0.1 adds: mandatory DEVIATIONS.md (controller appends every subagent deviation before dispatch), file-based structured reports (3 per task: implementer, spec-review, quality-review), controller discipline rules (read source files, not just plan text), pre-execution audit gate (7-question self-assessment before Task 1), execution trace audit (step 8 of pre-completion gate), 7-condition pre-completion gate (verifies all tasks have reports, all checkboxes checked, full test suite passes, wiring audit complete). All scripts use full absolute paths to avoid project-root resolution errors.

### Prompt-Optimized Skills (11)

All 14 upstream SKILL.md files + `handoff-acceptance` received 171 changes in 3 passes (2026-03-23) based on Claude 4.6 prompting best practices (`docs/prompting-best-practices.md`):

| Skill | Prompt Optimization Changes |
|-------|---------------------------|
| `dispatching-parallel-agents` | De-escalated XML tags, positive framing |
| `executing-plans` | De-escalated XML tags, role statement addition |
| `finishing-a-development-branch` | De-escalated XML tags, direct imperatives |
| `receiving-code-review` | De-escalated XML tags, motivation framing |
| `requesting-code-review` | Agent ref change + de-escalation, positive framing |
| `systematic-debugging` | De-escalated XML tags, direct imperatives |
| `test-driven-development` | De-escalated XML tags, positive framing |
| `using-git-worktrees` | Branch collision safety fix + de-escalation |
| `using-superpowers` | De-escalated XML tags, motivation framing |
| `verification-before-completion` | De-escalated XML tags, direct imperatives |
| `writing-skills` | De-escalated XML tags, direct imperatives |

**`finishing-a-development-branch` update (2026-07-14):** Added Step 1.5 ("Check for External References") — an advisory, non-blocking reminder to update an external charter/parent-doc's status when the completed feature's spec/plan pointed at one outside its own feature directory. Surfaced by a telemetry-exp charter-module handoff where a completed module's status went stale in its program charter after merge, with nothing in the pipeline prompting a fix.

Key changes applied across all skills:
- `<EXTREMELY-IMPORTANT>` → `<important>` (single emphasis level)
- "MUST ALWAYS NEVER" → direct imperatives ("Do X")
- "Red Flags" sections → "Required Practices" (positive framing)
- Motivation context added to explain why rules exist

---

## Prompt Templates (8 active)

| File | Skill | Purpose | Key Customizations |
|------|-------|---------|-------------------|
| `subagent-driven-development/implementer-prompt.md` | SDD | Dispatched per task to implementing subagent | 10-section structured report format, Contract Constraints passthrough, Source Files mandate (`[CONTROLLER: paste list]`), role statement, CLAUDE.md enforcement reminder |
| `subagent-driven-development/spec-reviewer-prompt.md` | SDD | Dispatched after each task for spec compliance review | Contract verification, BLOCKING vs ADVISORY severity gradation, BASE_SHA/HEAD_SHA placeholder, role statement |
| `subagent-driven-development/code-quality-reviewer-prompt.md` | SDD | Dispatched after spec review for code quality review | Dead code = BLOCKING (not Minor), implementer report placeholder `[CONTROLLER: paste full report]`, dispatch type `general-purpose` (post-2026-05-07 migration), role statement |
| `subagent-driven-development/pre-execution-audit-prompt.md` | SDD | NEW: authoritative auditor before Task 1 dispatch | 7 honesty questions, binding remediation orders, role as "authoritative auditor" |
| `subagent-driven-development/honesty-check-prompt.md` | SDD | User-facing compliance verification prompt. Mandatory before Pre-Completion Gate. | Controller outputs 7 questions for the user to paste back; controller then answers honestly. Has caught 3 major violations. |
| `subagent-driven-development/trace-auditor-prompt.md` | SDD | NEW: execution trace review at pre-completion gate | Parses `.jsonl` session file via `extract-execution-trace.py`, checks for skipped reviews, unlogged concerns, missing reports |
| `writing-plans/plan-document-reviewer-prompt.md` | writing-plans | 15-category mechanical review of draft plan | Cross-document consistency audit, snippet-vs-source verification, error name drift detection |
| `brainstorming/distillation-reviewer-prompt.md` | brainstorming | Verifies distilled spec preserves all decisions | Checks for omitted decisions, altered rationale, added assumptions not in original. **2026-07-07 (N38):** scope-fence preservation check (every out-of-scope/non-goals item must survive under the fence heading, deferral targets intact) + explicit not-an-artifact carve-out so a preserved fence is never flagged for removal + "near the top" Contract Facts tolerance (fence may precede it) |

---

## Deterministic Scripts (16 active)

All scripts live in `skills/<name>/scripts/`. Reference them via full absolute paths in skill text (bare `scripts/` paths resolve from project root, not skill directory).

| Script | Skill | Purpose |
|--------|-------|---------|
| `subagent-driven-development/scripts/_report_utils.py` | SDD | Shared library: `extract_status()`, `find_section_headers()`, `section_is_present()`, `is_placeholder_text()`, and (2026-06-10, sdd-cleanup) `_unfenced_content()` — the fence-aware line-blanking helper imported by validate-plan.py + controller-checkpoint.py (N5 SSOT consolidation). The `implementer_report` import is LAZY (PEP 562 module `__getattr__`) so importing the fence helper never pulls pydantic — validate-plan.py must stay stdlib-only (the plan-validation gate runs it with bare `python3`). Single source of truth — do NOT duplicate in other scripts. |
| `subagent-driven-development/scripts/_midpoint.py` | SDD | (added 2026-05-20) Shared `compute_midpoint(start, end)` formula. Single source of truth — consolidates the previously triplicated formula in `materialize-manifest.py` and `transition-module.py`. The plan-reference midpoint bug (off-by-one for small ranges) surfaced three times before consolidation. |
| `subagent-driven-development/scripts/estimate-task-tokens.py` | SDD | Pre-dispatch context budget check: OK / WARNING / TOO_LARGE based on task size and plan context |
| `subagent-driven-development/scripts/validate-report.py` | SDD | Implementer report completeness: 9 required sections, non-empty content, no placeholder text |
| `subagent-driven-development/scripts/controller-checkpoint.py` | SDD | 3-phase controller health check: pre-execution, pre-dispatch, pre-completion. Supports `--manifest <path>` (added 2026-05-20, Task 14) to read plan_file, tier, enforcement from `.sdd-session.json` via `_load_manifest_config()`. Micro tier sets honesty/trace checks to SKIP. (2026-05-29, SDD Hook Improvements:) the pre-completion minimum-tier ratio uses `_review_tiers_per_task` + `_declared_minimum_task_ids` (raw `yaml.safe_load`, not Pydantic) to exclude plan-declared `review_tier:minimum` tasks from BOTH numerator and denominator (quality + partner), aggregating declarations across all module plan files (via the manifest `modules` array). (2026-06-01, SDD Enforcement Hardening:) `find_report_file` / `find_all_report_files` now recurse into `archive-*/` (N4) so the pre-completion gate passes with archived completed-module reports — (2026-06-22, sdd-aggregate-gate-visibility:) N27 made Check 7 (`_review_tiers_per_task`) and Check 9 (`_merged_dispatch_times`) archive-aware too — the archive-aware lookup inventory is now FIVE sites total: `find_report_file` + `find_all_report_files` (N4) + the hook's Check 5 Task-0 lookup (N10) + `_review_tiers_per_task` + `_merged_dispatch_times` (N27). Every other report glob stays flat by design. Tests: `test_checkpoint_archive_aware.py` (4). (2026-06-10, sdd-cleanup:) pre-dispatch module-boundary skip-guard (N18 — previous-task checks SKIP when `previous_task < manifest task_range[0]`; `_load_manifest_config` stashes `manifest_task_range` + `manifest_has_prior_modules`); pre-execution `Source Contracts: None` = OK valid-absent (N7); `_task_ids_where` + `_load_all_plan_contents` SSOT helpers (N9); fence-aware parsing via `_unfenced_content` import (N5); pre-completion **Check 10** `integration_test_present` (C2) — declared integration-test paths must `is_file()` AND be in the feature changeset (untracked ∪ diff vs the NEWEST merge-base among origin/HEAD/main/master; present-but-malformed declarations FAIL with shape guidance). Tests: `test_checkpoint_archive_aware.py` (9), `test_c2_integration_gate.py` (22), `test_fence_aware_parsing.py` (7), `test_n9_plan_loading_helpers.py` (7). |
| `subagent-driven-development/scripts/context-summary.py` | SDD | Compresses completed task reports into one summary file for context management |
| `subagent-driven-development/scripts/context-probe.py` | SDD | (added 2026-07-14, N43) **stdlib-only** context-window token sensor — a vendored mirror of `~/.claude/bin/claude-ctx-check`'s `find_latest_usage`: scans a transcript JSONL from the end for the most recent assistant `message.usage` block and sums `input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens`. Window-less/percentage-less — emits ONLY the absolute total (thresholds live in the consuming hook). Resolution priority `--transcript` → `--session-id` → `$CLAUDE_CODE_SESSION_ID` (the hook always passes the first two, never relying on the env var). `--json` shape `{total_tokens, transcript, source_version}`. Consumed by `sdd-pre-dispatch-hook.sh`'s context-pressure gate; falls back to a byte-proxy when it fails. Tests: `test_context_probe.py`, `test_context_probe_fixtures.py` (differential parity vs `claude-ctx-check` on well-formed fixtures), `test_context_probe_sessionid.py`. |
| `subagent-driven-development/scripts/validate-plan.py` | SDD / writing-plans | Mechanical plan structure checks: size, section presence, Task 0, task count bounds. Plus (added 2026-05-20, Task 17) `enforcement_tier` validation: BLOCKER on invalid tier; WARNING on micro + >3 tasks; WARNING on micro + modules. Plus (2026-05-29) `check_review_tier_heuristic`: WARNING when a task declares `review_tier:minimum` but its title contains a high-risk keyword (refactor/service/security/business logic/auth; or migration co-occurring with backfill/update/delete/transform/data). Plus (2026-06-10, sdd-cleanup/C2) `check_integration_test_risk`: advisory `integration_test_risk_surface` WARNING + sections entry when risk-surface keywords (router/middleware/auth/migration/cache/cors/security) appear without an `integration_test` frontmatter declaration; fence-aware task-header parsing via `_unfenced_content` (N5); stdlib-only property restored. |
| `subagent-driven-development/scripts/materialize-manifest.py` | SDD | (added 2026-05-20, Module 1) Writes `.sdd-session.json` from plan frontmatter. Reads `enforcement_tier` (default `standard`); produces tier-specific `enforcement` + `process_requirements` dicts via `TIER_PROFILES`. Computes `task_range` and `midpoint` (via `_midpoint.compute_midpoint`). For multi-module plans, sets `active_module_id`/`active_module_file` to the first module's bare filename. |
| `subagent-driven-development/scripts/transition-module.py` | SDD | (added 2026-05-20, Module 3) Manages module boundary lifecycle. Validates completion (all tasks have reports >=50 bytes, honoring tier skip semantics), archives reports to `archive-<module>/`, updates manifest (active_module_*, task_range, midpoint, completed_modules, module_reports_archived), archives + truncates dispatch log, appends transition row to deviations.md. Exit codes: 0 (complete), 1 (validation failure), 2 (script error). (2026-06-01, SDD Enforcement Hardening:) `validate_module_completion` now verifies dispatch-log provenance for each completing-module task BEFORE truncation (N3b — the sibling enforcement to the hook's Check 4c skip-guard), with a file-based minimum-tier waiver (`task-NNN-quality-review-minimum-tier.md`) and a per-task `task_type: verification` exemption; `transition()` recomputes `enforcement.context_summary_at` for the next module's range (N11) so Check 6b does not fire early in later modules. Tests: `test_transition_module.py` (+3). (2026-06-10, sdd-cleanup:) provenance gated ONLY on `enforcement.dispatch_provenance` — file-existence stays on review modes ≠ skip (N12, hook↔transition SSOT); main-plan fallback for verification ids when `module.file` empty (N17). **First live run 2026-06-10: clean Module 1→2 transition, zero manual workarounds** (and it surfaced checkpoint-side N18, fixed same-day). Tests: `test_transition_module.py` (13 total). |
| `subagent-driven-development/scripts/extract-execution-trace.py` | SDD | Parses `.jsonl` session files into structured JSON with per-task records and 6 anomaly detection rules. **Known limitation** (2026-05-20): per-task dispatch-count detection is unreliable; the `anomaly_summary.total_anomalies: 0` output should NOT be trusted alone — manually verify dispatch-log timestamps for review-independence claims. |
| `subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | SDD (hook) | See Enforcement Hooks section. Rewrote 2026-05-20 (Module 2) to be manifest-aware: reads `.sdd-session.json` via git-root-relative paths; 8 enforcement checks gated by `enforcement.*` flags; process_requirements injected into additionalContext; dispatch log sentinel prevents forgery. (2026-05-29, SDD Hook Improvements:) restructured into a 3-stage manifest-mode classification pipeline (reviewer→implementer→passthrough) — `general-purpose` reviewers now logged / implementers enforced / ad-hoc passed through; dispatch log auto-created (mkdir -p + touch); validation-failure BLOCK embeds `head -n 12` of validate-report.py output; **legacy non-manifest path REMOVED** (no manifest + artifacts → BLOCK; all dead legacy branches deleted). (2026-06-01, SDD Enforcement Hardening:) Check 4c now skips when `PREV < MANIFEST_TASK_START` (N3a — prior-module-first or no-Task-0 first task; boundary provenance re-verified by `transition-module.py:validate_module_completion`); Check 5's Task-0 lookup also globs `archive-*/` (N10) so a Source-Contracts plan finds an archived Task 0 at module 2 (local glob only — `task_report_glob` unchanged). Tests: `test_sdd_hook_hardening.py` (4), `test_ssot_minimum_agreement.py` (4, cross-language hook↔transition minimum-signal SSOT). (2026-06-26, N35:) Check 5c's BLOCKED checkpoint-remediation command now emits `--manifest $MANIFEST` (was missing it → at a module boundary the suggested `controller-checkpoint.py` command couldn't arm the N18 boundary-skip and failed on archived prior-module reports; also dropped the unfilled `<plan.md>` placeholder). The 3 SKILL.md "Controller Health Checkpoints" commands were reconciled the same way (had a non-existent `--feature-dir` flag). Baseline re-captured. Surfaced when a real downstream SDD session (`inbox-agent-int`) first crossed a module boundary following the hook's emitted command (Sprint 3's earlier first-ever `transition-module.py` transition was in-repo while building the N18 machinery and drove the checkpoint with `--manifest` directly, masking the emitted-command gap). (2026-07-14, N43:) added a **context-pressure gate** on the implementer new-task path (`IS_IMPLEMENTER && ! MARKED_FIX`) — reads the controller's real token count via `context-probe.py`, nudges at `SUPERPOWERS_CTX_SOFT_TOKENS` (300000), blocks (`exit 2`, non-retryable → N39 handoff) at `SUPERPOWERS_CTX_HARD_TOKENS` (400000), reverts BOTH to defaults on a non-numeric or `HARD ≤ SOFT` threshold; probe failure degrades to the repurposed Check-7 byte-proxy (advisory), with `SUPERPOWERS_CTX_FALLBACK_STREAK` (3) consecutive fallbacks escalating to a block; `SUPERPOWERS_CTX_HANDOFF_BYPASS` skips the gate. Writes a per-dispatch observation line to `reports/context-observations.log` (a runtime artifact, SEPARATE from `reports/.dispatch-log`; format `<ISO-8601> task=<N> type=<...> tokens=<T> source=<probe|byte-proxy|bypass> tier=<below|soft|hard> action=<allow|nudge|block|fallback>`). Baseline re-captured to a new sha256. Tests: `test_context_gate_log.py`, `test_context_gate_impl_log.py`, `test_context_gate_tier.py`, `test_context_gate_fallback.py`; e2e Step 13. |
| `subagent-driven-development/scripts/sdd-report-guard.sh` | SDD (hook) | See Enforcement Hooks section |
| `subagent-driven-development/scripts/sdd-stop-hook.sh` | SDD (hook) | See Enforcement Hooks section |
| `subagent-driven-development/scripts/check-safe-branch.sh` | SDD | Shared: exits non-zero when on main or master branch. Called by `sdd-pre-dispatch-hook.sh`. |
| `subagent-driven-development/scripts/spawn-handoff-session.sh` | SDD | (added 2026-07-22, **N43 component (D)**) Auto-spawns the controller's successor SDD session in a new cmux workspace via repo-1's extended `claude-picker`, after the context-pressure gate's HARD block. Interface `spawn-handoff-session.sh BUNDLE_ID [--dry-run]`; driven by `references/context-handoff-protocol.md` steps 3–5. **Must be run with cwd inside the target worktree** — it takes no path argument and resolves `git rev-parse --show-toplevel` against the caller's cwd. Exit ladder **0** spawned / **3** manual fallback / **1** refused precondition — per-cause breakdown in CLAUDE.md "cmux Auto-Spawn Handoff", which is the single source of truth for it (same delegation as the bash-floor note later in this row). Reserves BEFORE spawning — hop in `reports/.handoff-hops`, `intent` record in `reports/handoff-spawn.log` — so a bookkeeping failure can never look retryable. Env knobs: `SUPERPOWERS_CMUX_MAX_HOPS`, `SUPERPOWERS_CMUX_QUOTA_MIN_PCT`, `SUPERPOWERS_CMUX_QUOTA_TIMEOUT`, `SUPERPOWERS_CMUX_QUOTA_TOOL`, `SUPERPOWERS_CMUX_AUTOSPAWN` (added 2026-08-04, Precondition 0 — plan-less per-run kill switch, fires before the clean-tree check) — defaults and validation semantics in CLAUDE.md "Hook Development Gotchas" (the de-facto env-var registry). **Not a hook** — no settings.json registration, no `baseline.txt` entry, so no baseline re-capture on edit. Bash floor ≥ 3.2; no `set -u`/`set -e`/`pipefail` (see CLAUDE.md "cmux Auto-Spawn Handoff"). Cross-repo (Decision 19): the picker lives in **repo-1** `telemetry-exp`; the pristine-vendored cmux skills live in **repo-2** `~/projects/claude-custom/cmux-custom-skills` — a separate git repo with its own `verify-install.sh` (this fork's `verify-symlink-install.sh` is unchanged). Tests: `test_spawn_handoff.py` (72), harness `spawn_handoff_helpers.py`, fixtures `tests/unit/fixtures/spawn-handoff/`; e2e Step 14. |
| `handoff-acceptance/scripts/check-handoff.sh` | handoff-acceptance | Verifies contract summary appears within first 50 lines of handoff README |
| `brainstorming/scripts/check-distillation.sh` | brainstorming | Greps for exploration artifacts (`Options Considered`, `Rationale`, `We considered`) in distilled specs; with the optional 2nd arg (full-spec path), FAILs when the source declares a heading-level out-of-scope/non-goals fence with no counterpart heading in the distilled spec (N38, 2026-07-07). One-arg mode unchanged — writing-plans direct entry calls it with one arg. Pytest: `tests/unit/test_check_distillation.py` |

---

## Hook Scripts (5 enforcement hooks)

| Script | Event | Matcher | What It Enforces |
|--------|-------|---------|-----------------|
| `sdd-pre-dispatch-hook.sh` | `PreToolUse` | `Agent` | Manifest-required 3-stage classifier (reviewer→implementer→passthrough). Blocks implementer dispatches when: prior task's 3 reports missing or <50 bytes; DEVIATIONS.md absent; pre-execution audit absent; on main/master with SDD artifacts; no `.sdd-session.json` manifest but SDD artifacts present. Logs `general-purpose` reviewers (auto-creating the dispatch log); embeds validate-report.py excerpt in validation-failure blocks. Injects `additionalContext` reminder on allowed dispatches. |
| `sdd-report-guard.sh` | `PreToolUse` | `Bash` | Detects `touch` or trivial writes to `reports/` directory (the 0-byte file bypass path) |
| `sdd-stop-hook.sh` | `Stop` | (any) | Runs pre-completion gate checks and injects results via `systemMessage` at session end |
| `handoff-gate-hook.sh` | `PreToolUse` | `Skill` | Checks for acceptance report before planning/SDD skill invocation |
| `sdd-skill-enforcement-hook.sh` | `PreToolUse` | `Write\|Edit` | Detects SDD bypass — **blocks (`exit 2`)** when the transcript shows an explicit SDD imperative + an implementation-file write + the SDD skill not loaded (advisory-only before 2026-06-01, now blocking — C5). `SUPERPOWERS_SDD_BYPASS` is the escape hatch (allow + stderr warning, mirrors `SUPERPOWERS_VALIDATOR_BYPASS`). Detection regex `\b(invoke\|use\|run\|...)\b.{0,20}\b(subagent-driven-development\|sdd)\b` verified identical under ugrep and stock BSD `/usr/bin/grep -iE`. Swiss Cheese "Point-of-Decision Routing" pattern. Tests: `test_sdd_skill_enforcement.py` (10). |

**Hook exit codes**:
- `exit 0` — allow (optional `additionalContext` injection via JSON stdout)
- `exit 2` — BLOCK (model sees error, cannot proceed)

---

## Reference Files (custom)

| File | Skill | Purpose |
|------|-------|---------|
| `subagent-driven-development/references/example-workflow.md` | SDD | Full worked example of SDD execution (moved from SKILL.md body per progressive disclosure) |
| `subagent-driven-development/references/advantages.md` | SDD | Why SDD architecture beats sequential implementation (moved from SKILL.md body) |
| `subagent-driven-development/references/module-template.md` | SDD | Module structure template for multi-module plans |
| `subagent-driven-development/references/obsolescence-verification-template.md` | SDD | Template for Obsolescence Verification task |
| `subagent-driven-development/references/task-0-template.md` | SDD | Task 0 (contract verification) structure template |
| `subagent-driven-development/references/context-handoff-protocol.md` | SDD | (added 2026-07-14, N43) The controller's block-response protocol when the context-pressure gate BLOCKS the next new-task dispatch at the HARD threshold: not a fix-and-retry — commit pending state, build an N39 fresh-session `/handoff` bundle (entry skill `superpowers:subagent-driven-development`), tell the user to resume from the worktree via `/pickup`, and STOP. Surfaced by `sdd-pre-dispatch-hook.sh`'s block message + the SKILL.md Context Health Protocol pointer. (2026-07-22, N43(D):) **steps 3–5 rewritten** so the protocol DRIVES `spawn-handoff-session.sh` — step 3 builds the bundle and captures its id, step 4 runs the script and dispatches on its 0/3/1 exit code (including telling the user in so many words when `launch=picker-manual` needs them to finish the picker), step 5 STOPs. The soft nudge uses the same script, earlier. |
| `subagent-driven-development/references/controller-health-checkpoints.md` | SDD | (added 2026-07-14, N43) The three deterministic `controller-checkpoint.py` invocations (pre-execution / pre-dispatch / pre-completion) with their `Verify:` lines — extracted verbatim from SKILL.md §272–292 as the word-offset for the two new context pointers (SKILL.md now points here). |
| `subagent-driven-development/references/model-selection.md` | SDD | Per-role model + reasoning-effort selection guidance. **Rewritten 2026-07-06** from the model/effort allocation analysis (`docs/process-improvement-findings/2026-07-06-model-effort-allocation-fable5.md`): two-dial capability/effort framing, the open-vs-closed heuristic (effort substitutes for capability on closed problems only), a per-role table (separate Capability + Effort columns), and a dated current-model footnote (Haiku 4.5 / Sonnet 5 / Opus 4.8 / Fable 5). Body is model-neutral by design so a model launch touches only the footnote (validated across the 2026-07-06 Sonnet 5 / Opus 4.8 / Fable 5 launches). SKILL.md pointer updated word-neutrally (§Model Selection). Executable-defaults follow-up tracked as BACKLOG N37. |
| `writing-plans/references/module-template.md` | writing-plans | Duplicate reference for plan writers |
| `writing-plans/references/obsolescence-verification-template.md` | writing-plans | Duplicate reference for plan writers |
| `writing-plans/references/task-0-template.md` | writing-plans | Duplicate reference for plan writers |
| `handoff-acceptance/references/acceptance-flow.dot` | handoff-acceptance | Graphviz flowchart of the acceptance decision process |
| `handoff-acceptance/references/handoff-package-spec.md` | handoff-acceptance | Canonical spec for handoff package structure. Surfaced automatically in failure reports and producer mode. |
| `brainstorming/references/process-flow.dot` | brainstorming | Graphviz flowchart of the brainstorming process |
| `using-superpowers/references/codex-tools.md` | using-superpowers | Reference for Codex tool use patterns (upstream; includes named agent dispatch, env detection; updated v5.1.0 with environment detection section) |
| `using-superpowers/references/copilot-tools.md` | using-superpowers | Reference for Copilot CLI tool use patterns (upstream; added v5.0.7) |
| `using-superpowers/references/gemini-tools.md` | using-superpowers | Reference for Gemini tool use patterns |

---

## Test Suites (4 custom)

> **Current real counts (2026-08-03, post-cmux-spawn-v2):** unit **849** (+1 xfailed) · e2e **15 steps** · regression **161 PASS / 2 WARN** · install **104**. The unit/e2e rows below predate the **pipeline-flexibility** (+29, 380), **sdd-enforcement-hardening** (+25, 405; e2e 10→11), **sdd-cleanup-and-integration-gate** (458; e2e 12), **sdd-aggregate-gate-visibility** (497), **N38** (+12 check-distillation tests, 509), **sdd-context-aware-handoff** (N43; e2e 13→14), **cmux-integration** (N43(D); unit 625 incl. `test_spawn_handoff.py` (72); e2e 14→15), and **cmux-spawn-v2** (`2026-07-30-cmux-spawn-v2`; the N43(D) workspace→surface topology rework, 4 modules / 19 tasks; unit 625→849 incl. `test_spawn_handoff_v2.py`; e2e Step 14 rewritten to 14a/b/c sub-runs, still 15 steps) features and carry their own per-feature narrative — they are NOT updated in place to avoid contradicting that history. **This header line is the authority for the running counts** — keep it current against a real suite run. `CLAUDE.md` "Testing" carries only the e2e **step index** (a structural reference), not pass counts.

| Suite | Location | Checks | Runtime | What It Tests |
|-------|----------|--------|---------|---------------|
| Static regression | `tests/ARaymond-skill-regression/validate-all-skills.py` | 145 PASS / 3 WARN / 0 FAIL | <1s | Frontmatter validity, skill file sizes, cross-references, Python 3.9 compatibility, section presence, script existence. The 3 WARNINGs are advisory soft-threshold notices (writing-plans/SKILL.md body 4157 words by the suite's count / `wc -w` 4183, > 4000 soft / < 5000 hard, after the 2026-05-29 review_tier table; SDD SKILL word count; 2 historical bare-DEVIATIONS.md refs) — result is PASS-with-warnings. |
| Static installation | `tests/ARaymond-installation/verify-symlink-install.sh` | 104 | <1s | Symlink targets, command stub count/format, agent symlink, hook script existence, settings.json entries |
| Skill invocation | `tests/ARaymond-installation/verify-skill-invocation.sh` | ~4 | ~5 min | Actual Claude behavior: symlink-installed skills load and trigger correctly via `claude -p` |
| Skill chain | `tests/ARaymond-installation/verify-skill-chain.sh` | ~10 | ~10 min | Brainstorming → writing-plans skill handoff chain works end-to-end via symlink install |
| Unit tests (pytest) | `tests/unit/` | 351 | ~40s | Pydantic models (implementer report, checkpoint, plan incl. **review_tier**, sdd_session, schema), validators CLI (plan/handoff/report/session), validate-plan.py (**review_tier heuristic**), controller-checkpoint.py (manifest-mode, **declared-minimum ratio exclusion**), sdd-pre-dispatch-hook.sh (**3-stage classification**, manifest guard, dispatch-log auto-create, inline validation excerpt via `test_sdd_classification.py`), sdd-report-guard.sh, sdd-stop-hook.sh, transition-module.py. Bumped from 326 to 351 by the 2026-05-29 SDD Hook Improvements feature (+25 net). |
| Integration (e2e) | `tests/integration/sdd-e2e-test.sh` | 8 steps | ~4s | Composed-pipeline smoke test (added 2026-05-20): `materialize-manifest.py → validators.py session → controller-checkpoint.py --manifest → transition-module.py → post-transition checkpoint → (2026-05-29) review_tier-modules exclusion`. Step 8 asserts declared `review_tier:minimum` tasks in a NON-active module are excluded from the ratio. `PROJECT` resolves from script location (repo root) so the e2e tests the current checkout. Caught one integration bug (`_load_manifest_config` missing feature_dir join) on first run that all unit tests had missed. |
| Behavioral API | `tests/ARaymond-skill-behavior/run-all.sh` | 21+ | ~15 min | Actual Claude behavior: skill loading, content recall, invocation triggers. Requires `claude -p` with `--verbose --max-turns 5`. |

**Run schedule**:
```bash
# After any skill edit:
python3 tests/ARaymond-skill-regression/validate-all-skills.py

# After installation changes:
bash tests/ARaymond-installation/verify-symlink-install.sh

# After skill content changes:
bash tests/ARaymond-skill-behavior/run-all.sh

# After upstream merge (run both static):
bash tests/ARaymond-installation/verify-symlink-install.sh && python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

**Behavioral test gotchas**:
- Use `grep -E` with `|` alternation (not `\|` — BRE syntax fails silently in ERE context)
- Use `--max-turns 5` minimum (Claude uses turns loading skills before answering content questions)
- Do not run `claude -p` integration tests from within an active Claude session (nested API calls exhaust quota)
- macOS has no `timeout` command — test scripts use background-process-kill pattern

---

## Global Settings Changes

Four categories of additions to `~/.claude/settings.json`. These live OUTSIDE the repo.

### 1. SessionStart hook (required for skill context injection)

```json
"SessionStart": [
  {
    "matcher": "startup|clear|compact",
    "hooks": [{ "type": "command", "command": "CLAUDE_PLUGIN_ROOT=... hooks/session-start", "async": false }]
  }
]
```

### 2. PreToolUse enforcement hooks (added 2026-03-24)

Four matchers in `PreToolUse`: `Bash` (sdd-report-guard.sh), `Agent` (sdd-pre-dispatch-hook.sh), `Skill` (handoff-gate-hook.sh), `Write|Edit` (sdd-skill-enforcement-hook.sh). See Step 5 for exact JSON.

1. `PreToolUse` → `Bash` matcher: anti-forgery report guard
2. `PreToolUse` → `Agent` matcher: SDD dispatch enforcement (review reports + branch safety)
3. `PreToolUse` → `Skill` matcher: handoff acceptance gate
4. `PreToolUse` → `Write|Edit` matcher: SDD skill enforcement hook (transcript-parsing bypass detection)

### 3. Stop pre-completion gate (added 2026-03-24)

One additional command in the existing `Stop` array: `sdd-stop-hook.sh`.

### 4. Permissions

```json
"permissions": {
  "allow": ["Bash(cat ~/.claude/skills/superpowers/**)"]
}
```

Use `**` (not `*`) — subdirectory paths must match.

**Rollback procedure**: Remove the four enforcement hook entries (Agent, Skill, Write|Edit matchers and the sdd-report-guard.sh entry under Bash). SessionStart and permissions do not need rollback.

---

## Upstream Conflict Files (complete list)

**All 15 skill SKILL.md files have diverged from upstream** due to the v0.1 promotion and prompt optimization passes. Any upstream change to a SKILL.md will conflict. The table below lists files that have historically conflicted or are likely to conflict on future merges.

**Pre-merge review process (established 2026-03-31)**: Before merging, run a three-way comparison for each conflicted skill file (merge-base vs ours vs upstream). Extract each side's delta from the common ancestor independently, then evaluate upstream changes for cherry-pick value. Do NOT rely on CLAUDE.md documentation about which files are "v0.1" or "promoted" — verify against the filesystem.

| File | Conflict Type | Resolution |
|------|--------------|------------|
| `CLAUDE.md` | Fork docs vs upstream contributor guidelines | Merged both sides: kept fork docs + integrated upstream's Worktree Sessions section and Skill Changes Require Evaluation notes (v5.1.0) |
| `skills/brainstorming/SKILL.md` | Entire skill body (v0.1 promoted) | Keep fork version; cherry-pick upstream additions manually |
| `skills/writing-plans/SKILL.md` | Entire skill body (v0.1 promoted) | Keep fork version; cherry-pick upstream additions manually |
| `skills/subagent-driven-development/SKILL.md` | Entire skill body (v0.1 promoted) | Keep fork version; cherry-pick upstream additions manually |
| `skills/subagent-driven-development/implementer-prompt.md` | Entire prompt body | Keep fork version; review upstream changes |
| `skills/subagent-driven-development/spec-reviewer-prompt.md` | Entire prompt body | Keep fork version; review upstream changes |
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | Prompt body | Keep fork v0.1 improvements (dead code BLOCKING, [NEEDS_CONTEXT], IMPLEMENTER_REPORT) |
| `skills/writing-plans/plan-document-reviewer-prompt.md` | Entire prompt body | Keep fork version; review upstream changes |
| `skills/using-git-worktrees/SKILL.md` | Full philosophy rewrite (v5.1.0: env detection, native tool preference, Codex App) | Accepted upstream full rewrite wholesale; re-added NEW SESSION REQUIRED handoff block to Step 4 (hook CWD gotcha) |
| `skills/using-superpowers/SKILL.md` | Prompt optimization changes | Keep fork version; cherry-pick new platform additions |
| `skills/writing-skills/SKILL.md` | Prompt optimization changes | Keep fork version; cherry-pick factual corrections |
| All other `skills/*/SKILL.md` | Prompt optimization (de-escalation, positive framing) | Keep fork version; may auto-merge if upstream changes are on different lines |

Files with no expected conflicts (fork-only additions):
- All files under `skills/handoff-acceptance/` (new skill, no upstream equivalent)
- All files under `skills/*/scripts/` (fork additions)
- All files under `skills/*/references/` (fork additions, except `codex-tools.md` in using-superpowers and `visual-companion.md` in brainstorming — these are shared with upstream)
- `skills/brainstorming/distillation-reviewer-prompt.md`
- `skills/brainstorming/spec-document-reviewer-prompt.md`
- `skills/subagent-driven-development/pre-execution-audit-prompt.md`
- `skills/subagent-driven-development/trace-auditor-prompt.md`

### Upstream Sync Log

| Date | Upstream Version | Commits | Conflicts | Cherry-picks |
|------|-----------------|---------|-----------|-------------|
| 2026-03-31 | v5.0.7 (`dd23728`) | 27 | 4 files (CLAUDE.md, brainstorming, writing-plans, codex-tools.md) + writing-skills/using-superpowers auto-merged | "No Placeholders" section from writing-plans; Copilot CLI lines auto-merged into using-superpowers; "two required fields" fix auto-merged into writing-skills |
| 2026-05-07 | v5.1.0 (`f2cbfbe`) | 3 | 8 files (CLAUDE.md, agents/code-reviewer.md, using-git-worktrees, finishing-a-development-branch, requesting-code-review, subagent-driven-development + code-quality-reviewer-prompt, executing-plans) | Accepted upstream's using-git-worktrees full rewrite + re-added NEW SESSION REQUIRED block; accepted finishing-a-development-branch env detection + kept Step 7 post-completion cleanup; deferred agent deletion at merge time, then completed it on 2026-05-07 via `code-reviewer-agent-migration` (Needs Context + reflection step promoted to template); absorbed "continuous execution" paragraph in SDD |
| 2026-06-22 | v6.0.3 (`896224c`) | 169 (assessed, **NOT merged**) | N/A — no merge attempted. All 13 SKILL.md upstream touched would conflict; the v6 SDD review-rewrite collides with our hook enforcement. Method: hand-port specific content deltas, not `git merge`/`cherry-pick`. | **A1** systematic-debugging ultrathink-keyword fix `"Ultrathink"→"Ultra-think"` (`90e1721`/#1558); **A2** `scripts/lint-shell.sh` ShellCheck+shfmt harness (`21b44e4`); **A4** using-git-worktrees legacy global-dir removal (`d00f4ad`/#1476). **Declined:** v6.0.3 `.git/`-scratch fix (N/A — we use `docs/imp-plans/`), new-harness support (Kimi/Pi/Antigravity), vendor-neutral prose rewrite (CSO→SDO/"your agent" — primary conflict source), evals submodule split. **Deferred to BACKLOG:** N29 (writing-skills authoring sections — content-port), N30 (architecture-neutral SDD cost wins), N31 (one-vs-two-reviewer strategic decision). Full assessment: `docs/process-improvement-findings/2026-06-22-upstream-v6-sync-assessment.md` |

---

## Document Index

| Document | Location | Purpose |
|----------|----------|---------|
| **This file** | `docs/ARaymond-customization-manifest.md` | Complete rebuild reference for this fork |
| Skills best practices | `docs/ARaymond-skills-best-practices.md` | Operational learnings: enforcement layers, hooks, testing |
| Setup runbook v1 | `docs/ARaymond-custom-fork-setup-runbook-v1.md` | Original installation runbook (superseded by this document) |
| Prompting best practices | `docs/prompting-best-practices.md` | Claude 4.6 prompt engineering reference; source of truth for all prompt edits |
| Statement Reconciliation post-mortem | `docs/process-improvement-findings/2026-03-16-statement-reconciliation-lessons-learned.md` | Root cause analysis for 3 production bugs; primary motivation for v0.1 improvements |
| Hooks enforcement plan | `docs/plans/2026-03-24-hooks-enforcement-plan.md` | Phased implementation plan for process-level enforcement hooks |
| Hooks Gemini research | `docs/plans/2026-03-24-deterministic-ai-agent-discipline-hooks-analysis.md` | Exhaustive analysis of Claude Code hooks, symlink vulnerabilities, advisory instruction failures, Swiss Cheese model |
| SDD improvement plan | `docs/plans/2026-03-23-sdd-improvement-plan-v0.1.md` | 6 root causes + 20-issue inventory from Statement Reconciliation |
| Final audit results | `docs/plans/2026-03-23-final-audit-results.md` | 13-file audit of all v0.1 skill files against Anthropic guide (critical/important/medium/low) |
| Iteration 5 final scorecard | `docs/plans/2026-03-23-sdd-improvement-results-iteration-5-final.md` | 14 PREVENTED / 5 SUBSTANTIAL / 0 NOT ADDRESSED across 20 issues |
| Prompt optimization plan | `docs/plans/2026-03-23-PromptingBestPracticesImprovementPlan.md` | 171 changes across 8 areas for Claude 4.6 prompting best practices |
| Scenario-based tests plan | `docs/plans/2026-03-24-scenario-based-behavioral-tests.md` | 18 planned decision-making tests (not yet implemented) |
| Improvements backlog | `docs/process-improvement-findings/BACKLOG.md` | Living ledger of open/in-flight/done process & tooling improvements (stable IDs B/I/C/N/P) — start here for "what's left to improve" |
| SSOT audit (2026-05-31) | `docs/process-improvement-findings/2026-05-31-ssot-audit.md` | SKILL.md-vs-hook single-source-of-truth audit; sources BACKLOG N2–N9 |
| Pipeline Flexibility feature | `docs/imp-plans/2026-05-31-pipeline-flexibility/` | `task_type: verification` + `entry_mode: direct` SDD execution record (plan, deviations, reports) |
| SDD Enforcement Hardening feature | `docs/imp-plans/2026-06-01-sdd-enforcement-hardening/` | Multi-module enforcement gap closure (N3a/N3b/N4/N10/N11) + skill-bypass hook blocking (C5) — SDD execution record (plan, deviations, reports) |
| SDD Cleanup & Integration Gate feature | `docs/imp-plans/2026-06-05-sdd-cleanup-and-integration-gate/` | Sprint-3: 7 enforcement-pipeline bug fixes (N16/N9/N5+N13/N7/N12/N17/N1) + live-discovered N18 + C2 integration-test gate (IntegrationTest model, risk-surface WARNING, pre-completion Check 10) — SDD execution record incl. first live module transition, Task 3 provenance-violation remediation, honesty check + trace audit + final review |
| cmux auto-spawn handoff feature | `docs/imp-plans/2026-07-22-cmux-integration/` | N43 component **(D)**: `spawn-handoff-session.sh` (cmux auto-spawn of the successor SDD session) + `context-handoff-protocol.md` steps 3–5 rewrite + e2e Step 14 — SDD execution record (spec, plan, 2 modules / 12 tasks, deviations, reports). Cross-repo (Decision 19): the `claude-picker` half lives in **repo-1** `telemetry-exp`; the vendored cmux skills live in **repo-2** `~/projects/claude-custom/cmux-custom-skills` (separate repo, own `verify-install.sh`) |
| Upstream v6 sync assessment | `docs/process-improvement-findings/2026-06-22-upstream-v6-sync-assessment.md` | Categorized assessment of obra/superpowers v6.0.0–v6.0.3 (`896224c`) vs our fork; what was cherry-picked (A1/A2/A4), the one-vs-two-reviewer strategic decision, and what was declined. Sources BACKLOG N29–N31 |
| CLAUDE.md | `CLAUDE.md` (project root) | Session-level reference: architecture, gotchas, editing workflow, verification |
