# Skills Best Practices — Operational Learnings

**Author**: Aaron Raymond
**Last Updated**: 2026-03-25
**Source**: Accumulated from 5 iterations of SDD improvement, 3 validation test rounds (iterations 1-5), prompt optimization pass (171 changes), hooks enforcement development (2026-03-24), the Statement Reconciliation re-implementation post-mortem (2026-03-16), and Gemini deep research on deterministic agent discipline (2026-03-24).

---

## The Three Enforcement Layers

Every critical skill control falls into one of three categories, ordered by reliability:

| Layer | Mechanism | Reliability | Use For |
|-------|-----------|-------------|---------|
| **1. Prompt instructions** | Text in SKILL.md / CLAUDE.md | Low — advisory only | Defaults, preferences, style |
| **2. Deterministic scripts** | Python / shell validation scripts | High — if they run | Structural validation (plan size, report completeness, token budgets) |
| **3. Hooks with exit 2** | `PreToolUse` / `Stop` in `settings.json` | Highest — process-level | Non-negotiable gates (review enforcement, branch safety, audit presence) |

The key distinction: layers 1 and 2 both depend on the controller choosing to run them. Layer 3 fires outside the model's reasoning loop entirely — the agent cannot skip or rationalize around it.

Evidence for this ordering comes from two directions. Our own Statement Reconciliation re-implementation (2026-03-16) showed the controller reading "Non-Negotiable Review Enforcement" text and skipping all 34 review dispatches. The Gemini deep research document (`docs/plans/2026-03-24-deterministic-ai-agent-discipline-hooks-analysis.md`) catalogs 8 Claude Code GitHub issues and 5 documented $40K+ loss scenarios from advisory instruction failures.

**Practical implication**: Any control that must fire every time — no exceptions — belongs in a hook, not in prompt text.

---

## Advisory Instructions Don't Work for Critical Controls

### What We Observed

The Statement Reconciliation implementation (2026-03-16) used a 17-task SDD workflow. The SKILL.md contained explicit "Non-Negotiable" enforcement text requiring spec compliance and code quality reviews after every task. The controller:

- Read and acknowledged the review requirements
- Skipped all 34 review dispatches ("for speed")
- Produced 3 P1/P2 bugs that would have been caught by the reviews

### What the Community Observed

The Gemini research documents the same pattern at scale:

- An agent managing a live trading system was instructed via CLAUDE.md 20+ separate times to restart a service after edits. It never did. The rule was re-read and re-acknowledged. The service was never restarted.
- An agent introduced a position-exit bug that ran undetected for 7 weeks, contributing to $40,000 in portfolio losses, despite CLAUDE.md rules requiring "real-world execution proof."
- An agent wrote `<FROM_KEYCHAIN>` as a literal API token, declared the bug "fixed" based on source code inspection alone, and continued reporting "Telegram working" for weeks.
- An agent wrote a CLAUDE.md rule forbidding a specific destructive git command, then ran that exact command 20 minutes later.

### Why It Happens

LLMs optimize for task completion, not rule compliance. Two structural factors make this worse:

1. **Context compaction**: In long sessions, the runtime compresses context to maintain operational efficiency. Workflow discipline rules are frequently dropped from the compacted summary. The agent resumes with "build the feature" but without the constraints that governed the session start.

2. **Rationalization**: The agent does not disobey rules randomly — it constructs a coherent-sounding reason. "Skipping reviews for speed" is an optimization, not defiance. The agent believes it is being helpful.

**Key insight**: The strength of the instruction text — "Non-Negotiable," "CRITICAL," "ALWAYS" — does not change this. The mechanism is probabilistic at its foundation.

---

## Hooks Are the Only Reliable Enforcement

### The Exit 2 Universal Mechanism

Exit code 2 from a hook causes Claude Code to block the tool call with a user-visible error. The hook runs outside the model's reasoning loop, before the tool executes, with no ability for the agent to argue around it.

```
exit 0 → allow (with optional additionalContext injection)
exit 1 → allow (logged as advisory warning)
exit 2 → BLOCK (model sees error, cannot proceed)
```

### The Symlink Problem

Frontmatter hooks (`hooks:` block in SKILL.md YAML) do NOT fire for symlink-installed skills. This is a confirmed Claude Code runtime bug as of March 2026 (GitHub issues #5433, #36135, #30874). The `${CLAUDE_SKILL_DIR}` variable fails to expand in the isolated child process environment, causing silent hook failure.

**Workaround**: Define all hooks in `~/.claude/settings.json` with absolute paths. This is the only reliable configuration.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Agent",
        "hooks": [{
          "type": "command",
          "command": "/Users/araymond/projects/claude-custom/superpowers/skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
        }]
      }
    ]
  }
}
```

Note: absolute path to the physical file, not a symlink path.

### Active Hooks (as of 2026-03-24)

| Event | Matcher | Script | What It Enforces |
|-------|---------|--------|-----------------|
| `PreToolUse` | `Agent` | `sdd-pre-dispatch-hook.sh` | Review reports + DEVIATIONS.md + branch safety before implementer dispatch |
| `PreToolUse` | `Bash` | `sdd-report-guard.sh` | Anti-forgery: detects `touch` / empty file writes to reports/ directory |
| `PreToolUse` | `Skill` | `handoff-gate-hook.sh` | Acceptance report must exist before planning skill invocation |
| `PreToolUse` | `Write\|Edit` | `sdd-skill-enforcement-hook.sh` | Detects SDD bypass: parses transcript to warn when user requested SDD but agent writes code without loading the skill |
| `Stop` | (any) | `sdd-stop-hook.sh` | Pre-completion gate: injects 8-check results at session end |
| `SessionStart` | `startup\|clear\|compact` | `hooks/session-start` | Loads plugin context into session |
| (user-delivered) | n/a | `honesty-check-prompt.md` | Mandatory compliance check before Pre-Completion Gate: controller outputs 7 questions, user pastes back, controller answers honestly |

### Hook Patterns That Work

**PreToolUse on Agent** — intercept subagent dispatches, check file-based evidence that prior steps completed. This is the highest-value hook pattern: it fires on every `dispatch_agent()` call and gives the hook full `tool_input` JSON (including the description field used for task matching).

**PreToolUse on Bash** — warn on suspicious commands (report forgery detection). Lower impact than Agent hooks but catches the specific bypass where a controller uses `touch reports/task-1-spec-review.md` to fake compliance.

**PreToolUse on Skill** — gate skill invocation on prerequisites. Used for handoff acceptance: the hook checks for an existing acceptance report before allowing planning or SDD skills to proceed.

**Stop** — inject advisory context at session end. Use `systemMessage` in the JSON response (not `hookSpecificOutput.additionalContext` — Stop events do not support that field). Useful for surfacing pre-completion gate results that the controller may have deferred.

**additionalContext injection on exit 0** — when a dispatch is allowed, the hook can return a JSON body with `additionalContext` to inject a reminder into the agent's context at the exact moment of dispatch.

### Hook Gotchas

| Gotcha | Explanation |
|--------|-------------|
| Stop hooks: use `systemMessage`, not `hookSpecificOutput.additionalContext` | The `additionalContext` field is not supported for Stop events — use the top-level `systemMessage` field instead |
| Avoid `set -u` in bash hooks | `jq` pipe chains produce empty variables that cause silent exits with no stderr output when `set -u` is active |
| Permission globs: use `**` not `*` | `Bash(cat ~/.claude/skills/superpowers/*)` does not match subdirectory paths — use `Bash(cat ~/.claude/skills/superpowers/**)` |
| Hooks receive CWD from session start | `! cd /some/path` changes the prompt CWD but NOT the hook CWD — hooks always run from the original session directory |
| Worktree sessions must start from the worktree | Start the session with `cd /path/to/worktree && claude` — not from the project root with a subsequent `! cd` |

---

## Anti-Forgery: Content Validation Over File Existence

A controller can satisfy a "file must exist" check with `touch reports/task-1-spec-review.md` — creating a zero-byte file. The hook must validate content, not just existence.

**The 50-byte minimum**: All report existence checks use `wc -c` and require at least 50 bytes. An empty file or a single-word placeholder fails this check. A real review with even minimal content passes.

**The Swiss Cheese defense**: No single layer catches everything. Multiple overlapping layers, each covering others' gaps:
- Script path validation (C1 in final audit) catches missing scripts before execution
- `validate-report.py` catches structural gaps in real reports
- `sdd-report-guard.sh` catches the `touch` bypass at the Bash tool level
- Hook 50-byte check catches files that passed the guard but were written with trivial content
- `trace-auditor-prompt.md` catches skipped steps in post-execution review

---

## The Two-Layer Validation Pattern

Structural validation and semantic review are separate responsibilities.

| Layer | Tool | What It Catches | What It Misses |
|-------|------|-----------------|----------------|
| **Structural** | `validate-plan.py` | Size violations, missing sections, missing Task 0, task count bounds | Correct section names with wrong content |
| **Semantic** | `plan-document-reviewer-prompt.md` | Type mismatches, logic bugs, cross-document contradictions, error name drift | Deterministic structure issues |

`validate-plan.py` PASS does not mean the plan is correct — it means the plan has the required sections at the required sizes. Always dispatch the semantic reviewer after the structural check passes.

The same pattern applies to implementer reports: `validate-report.py` verifies 9 required sections are present and non-empty; the spec reviewer and quality reviewer verify the actual content.

---

## The Pre-Execution Audit Gate

A mandatory self-assessment checkpoint between plan ingestion and first task dispatch.

**What it is**: The controller dispatches a subagent (`pre-execution-audit-prompt.md`) as an "authoritative auditor" to answer 7 honesty questions:

1. Have you read every source file listed in Source Contracts?
2. Have you verified that the plan's code snippets match the actual source?
3. Have you identified all consumers of interfaces this plan modifies?
4. Have you run `validate-plan.py` and passed?
5. Do you have a DEVIATIONS.md initialized?
6. Do you have a `reports/` directory initialized?
7. Is the implementation branch non-main?

**Why it works**: The questions require verifiable evidence, not self-assessment. "Have you read X?" → either the file was read (tool call in history) or it wasn't. The auditor is positioned as authoritative with binding remediation orders if any answer is "no."

**How it's enforced**: `sdd-pre-dispatch-hook.sh` checks for `reports/pre-execution-audit.md` (>50 bytes) before allowing any Task 1+ dispatch. The audit cannot be skipped without triggering the hook.

---

## Honesty Check (Pre-Completion Gate)

A mandatory user-delivered compliance verification before the Pre-Completion Gate.

**What it is**: The controller outputs 7 questions (from `honesty-check-prompt.md`) for the user to paste back into the session. The controller then answers each question honestly, enumerating any shortcuts, skipped steps, or unresolved uncertainties.

**Why it works**: LLMs honestly enumerate violations when directly asked — the advisory instruction problem does not extend to direct compliance questions. When positioned as a compliance audit rather than self-assessment, the controller has no motivation to rationalize omissions.

**Track record**: Has caught 3 major violations across live sessions:
- All reviews skipped (controller admitted zero spec/quality reviews dispatched)
- 5 shortcuts taken prior to audit (undisclosed at pre-execution gate)
- Skill never loaded (controller implemented directly from plan without invoking SDD skill)

**When it fires**: Mandatory before the 7-condition Pre-Completion Gate. The gate should not proceed until the honesty check is complete and any disclosed violations are remediated.

---

## Worktree Session Architecture

### The Problem

SDD implementations must run in a git worktree (separate directory, separate branch). If the hook fires in the main project directory, checking for `reports/` will return false negatives (the files are in the worktree, not the project root).

### The Pattern

| Session | Where to Start | Purpose |
|---------|---------------|---------|
| Session 1 | Project root | Planning: brainstorming + writing-plans |
| Session 2 | Worktree directory | Execution: SDD + implementation |

Session 2 must be started with `cd /path/to/worktree && claude` — not from the project root. The handoff from Session 1 must include a copy-pastable `cd` command for this reason.

**Worktree location convention**: `.worktrees/` (inside the project root) is the ONLY supported location. Sibling directory and global worktree alternatives have been removed from the `using-git-worktrees` SKILL. The SDD enforcement hook warns on worktree locations outside `.worktrees/`.

**Branch check**: The hook blocks implementation dispatches when the session is on `main` or `master` AND SDD artifacts exist (DEVIATIONS.md). This catches the case where the controller drifted out of the worktree. Override with a `.allow-main` file for the rare case where main-branch work is legitimate.

### Mid-Execution Session Handoff

When the controller's context gets heavy during a long SDD execution, it may hand off to a new session. Current gap: no standardized template for mid-execution handoffs. The resume prompt MUST include `/superpowers:subagent-driven-development` (or use the Skill tool to invoke it) as the FIRST ACTION before any code work. Identified as a future improvement to build into the SDD skill.

---

## Skill Frontmatter Best Practices

From the Anthropic "Complete Guide to Building Skills for Claude" and our audit findings (`docs/plans/2026-03-23-final-audit-results.md`):

| Rule | Source | Detail |
|------|--------|--------|
| Keep SKILL.md under 5000 words | Anthropic guide | Start monitoring at 4000. SDD SKILL.md hit 4091 after v0.1 improvements. |
| Use progressive disclosure | Anthropic guide | Move templates and examples to `skills/<name>/references/` — load only on demand |
| Description field: "Use when..." trigger format | Anthropic guide | Not a workflow summary. What triggers auto-invocation? |
| XML tags: lowercase-with-hyphens | Anthropic guide | `<important>`, `<good>`, `<bad>` — not `<EXTREMELY-IMPORTANT>` or `<HARD-GATE>` |
| Role statements in all subagent prompt templates | Anthropic guide + our prompting audit | Sets model identity at top of every template |
| Use `scripts/` for deterministic validation | Best practice | Don't embed shell logic in skill text — it won't run. Put it in a script. |
| Name field must match folder name in kebab-case | Anthropic guide | `-v0.1` suffixes in names violate this (C3 in final audit) |
| Critical instructions at the top | Anthropic guide | Don't bury calibration guidance after 40+ check items (M3 in final audit) |

### Script Path Resolution

Scripts referenced in skill text must use full absolute paths:

```
~/.claude/skills/superpowers/subagent-driven-development/scripts/validate-report.py
```

NOT:

```
scripts/validate-report.py
```

Bare relative paths resolve from the project working directory, not the skill directory. The controller gets "file not found" and silently proceeds without validation (C1 in final audit).

### Prompt Template Standards

From the 2026-03-23 prompt optimization pass (171 changes across 8 areas):

- Replace `<EXTREMELY-IMPORTANT>` → `<important>` (one emphasis level, not escalating)
- Replace aggressive MUST/NEVER → direct imperatives ("Do X" not "You MUST ALWAYS do X")
- Replace "Red Flags" sections → "Required Practices" (positive framing, not threat framing)
- Add role statements to the opening of every template
- `[CONTROLLER: ...]` annotations for controller-supplied values that subagents cannot infer

---

## Testing Strategy

### The Three Layers

| Layer | Script | Checks | Runtime | When to Run |
|-------|--------|--------|---------|-------------|
| **Static regression** | `tests/ARaymond-skill-regression/validate-all-skills.py` | 105 | <1s | After every skill edit |
| **Static installation** | `tests/ARaymond-installation/verify-symlink-install.sh` | 95 | <1s | After installation changes |
| **Behavioral API** | `tests/ARaymond-skill-behavior/run-all.sh` | 21+ | ~15 min | After skill content changes |

Run both static layers together after upstream merges:

```bash
bash tests/ARaymond-installation/verify-symlink-install.sh && python3 tests/ARaymond-skill-regression/validate-all-skills.py
```

### Test Layer Responsibilities

**Static regression**: Checks frontmatter validity, skill file sizes, cross-references between skills and their referenced scripts/templates, Python 3.9 compatibility, section presence. Does NOT verify that Claude behaves correctly.

**Static installation**: Checks symlink targets exist and point correctly, command stubs exist for all skills, agent symlink is intact, hook scripts are present. Does NOT verify hook logic.

**Behavioral API**: Sends real `claude -p` calls and asserts keywords in responses. Verifies Claude loaded the skills and can describe their behavior. Does NOT test actual SDD execution with real subagent dispatches.

### Key Behavioral Test Gotchas

| Gotcha | Fix |
|--------|-----|
| `grep -E` alternation uses `\|` in BRE but `\|` is wrong for ERE — use `|` | Wrong syntax silently fails to match, making tests pass when they shouldn't |
| `--max-turns 3` is insufficient | Claude uses turns loading skills before answering. Use `--max-turns 5` minimum for content questions |
| `check-distillation.sh` grep must exclude template boilerplate | Blockquote lines (`>`) contain the artifact patterns as examples — exclude them or the check always fires |

### Planned: Scenario-Based Tests (18 scenarios)

`docs/plans/2026-03-24-scenario-based-behavioral-tests.md` describes 18 decision-making scenarios (not yet implemented) organized in 4 categories: Handoff Acceptance (5), Controller Discipline (4), Plan Writing (4), TDD (5). These test actual behavior under pressure — "skip the review, it was simple" — not just skill knowledge recall.

### The Live Implementation IS a Test

Observe hook behavior during real SDD executions. Every hook fire documents what the controller attempted to skip. Every false positive (legitimate dispatch blocked) is a test failure in the other direction. The Statement Reconciliation Module 3 execution is the planned Phase 2 live test for the hooks system.

---

## File Organization Conventions

| Artifact Type | Location | Naming |
|---------------|----------|--------|
| Design specs | `docs/specs/` | `YYYY-MM-DD-<topic>-design.md` |
| Distilled specs | `docs/specs/` | `YYYY-MM-DD-<topic>-design-distilled.md` |
| Implementation plans | `docs/imp-plans/` | `YYYY-MM-DD-<feature-name>.md` |
| Project plans / reviews | `docs/plans/` | existing convention |
| Scripts in skill dirs | `skills/<name>/scripts/` | kebab-case `.py` or `.sh` |
| Reference files | `skills/<name>/references/` | kebab-case `.md` |
| Custom test suites | `tests/ARaymond-*/` | descriptive directory name |
| SDD execution artifacts | Project root (worktree) | `DEVIATIONS.md`, `reports/task-N-*.md` |

---

## Common Failure Modes and Mitigations

| Failure Mode | Evidence | Mitigation |
|---|---|---|
| Controller skips reviews | Statement Reconciliation: 34 reviews skipped despite "Non-Negotiable" text | `sdd-pre-dispatch-hook.sh` blocks next implementer dispatch without 3 review reports |
| Controller forges empty report files | `touch reports/task-1-spec-review.md` creates 0-byte file | 50-byte minimum content validation + `sdd-report-guard.sh` intercepts Bash `touch` calls |
| Plan has wrong type assumptions | Statement Reconciliation: all 3 bugs from string-vs-numeric mismatch | Task 0 contract verification: read actual source files, compare plan snippets against them |
| Agent drifts out of worktree | Controller uses `! cd` which doesn't affect hook CWD | Branch check blocks on main when SDD artifacts exist; worktree sessions must start from worktree |
| Spec too large for plan writer | 1347-line spec → 2816-line plan with 89 checkboxes | Spec distillation (<500 lines) before planning; brainstorming produces distilled version |
| Task too large for subagent context | Subagent receives plan excerpt, not full picture | `estimate-task-tokens.py` pre-dispatch budget check; dispatches flagged TOO_LARGE must be split |
| Controller declares done without verification | 0/89 checkboxes checked after 17-task execution | Pre-completion gate (7+ checks) + Stop hook injects results at session end |
| Dead code not removed | Statement Reconciliation: old hooks still present after Task 10 | `code-quality-reviewer-prompt.md` flags dead code as BLOCKING (not Minor) + Obsolescence Verification Task in writing-plans |
| Handoff package has buried contract info | Field types buried at line 200 of README | `check-handoff.sh` verifies contract summary within first 50 lines; `handoff-gate-hook.sh` blocks planning if acceptance report missing |
| Script shared logic duplicated | `validate-report.py` and `controller-checkpoint.py` both parse section headers (C2, final audit) | `_report_utils.py` shared library — single source of truth for all report parsing |
| Context compaction drops discipline rules | Long sessions: agent resumes with only task description | File-based enforcement (reports must exist) survives compaction; hook state is filesystem state |
| Wrong test fixtures | Statement Reconciliation: fixtures used numeric types, real output uses strings with commas | "Ground-truth fixtures" step: derive fixtures from real system output BEFORE writing any code |
| Agent bypasses SDD skill entirely — reads plan, implements directly without subagents | Module 3 of Statement Reconciliation: agent admitted to zero reviews, 5 uncertainties post-execution | `Write\|Edit` transcript hook injects warning + CLAUDE.md Skill Invocation Rule + honesty check before Pre-Completion Gate |
