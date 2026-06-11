# Skills Best Practices — Operational Learnings

**Author**: Aaron Raymond
**Last Updated**: 2026-03-31
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

### Active Hooks (as of 2026-04-06)

| Event | Matcher | Script | What It Enforces |
|-------|---------|--------|-----------------|
| `PreToolUse` | `Agent` | `sdd-pre-dispatch-hook.sh` | Review reports + DEVIATIONS.md + branch safety before implementer dispatch |
| `PreToolUse` | `Bash` | `sdd-report-guard.sh` | Anti-forgery: detects `touch` / empty file writes to reports/ directory |
| `PreToolUse` | `Skill` | `handoff-gate-hook.sh` | Acceptance report must exist before planning skill invocation |
| `PreToolUse` | `Skill` | `plan-validation-gate-hook.sh` | Plan validation + review report before execution skill invocation |
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

**What it is**: The controller outputs 9 questions (from `honesty-check-prompt.md`) for the user to paste back into the session. The controller then answers each question honestly, enumerating any shortcuts, skipped steps, or unresolved uncertainties.

**Why it works**: LLMs honestly enumerate violations when directly asked — the advisory instruction problem does not extend to direct compliance questions. When positioned as a compliance audit rather than self-assessment, the controller has no motivation to rationalize omissions.

**Track record**: Has caught 4 major violation patterns across live sessions:
- All reviews skipped (controller admitted zero spec/quality reviews dispatched)
- 5 shortcuts taken prior to audit (undisclosed at pre-execution gate)
- Skill never loaded (controller implemented directly from plan without invoking SDD skill)
- Controller-authored implementer reports + parallel review dispatch + uncommitted patches (2026-05-20 adaptive-enforcement-tiers session — see addendum to that feature's honesty-check report for the four findings the controller missed in its own audit, all caught by the trace auditor)

**Honesty report is necessary but not sufficient.** The 2026-05-20 session demonstrated that the controller's self-audit understates magnitude even when it's substantively correct in direction. **Always pair the honesty report with an independent execution-trace audit** (`extract-execution-trace.py` + `trace-auditor-prompt.md`). The auditor reads the artifacts, not the controller's self-report — that independence catches what the controller's confirmation bias misses.

**When it fires**: Mandatory before the 8-check Pre-Completion Gate. The gate should not proceed until the honesty check is complete, the trace audit is filed, and any disclosed violations are remediated or accepted-with-disclosure in `deviations.md`.

---

## Review Dispatch Sequencing (2026-05-20 lesson)

The SDD skill says "spec compliance review first, THEN code quality review only after spec passes" (`code-quality-reviewer-prompt.md`). The 2026-05-20 adaptive-enforcement-tiers session revealed three failure modes in how controllers actually implement this:

1. **Combined dispatch** (Tasks 16, 18): one Agent call asked to produce both review files. The dispatch-log hook on the next task blocked because the log only had one entry. Recovery via rubber-stamp "verification" subagents that just re-read the existing files. **Rule**: each review type MUST be its own Agent call.

2. **Parallel dispatch** (Tasks 13, 14, 15, 17, 19, 20): spec and quality dispatched in the same message as separate Agent tool blocks. Independent subagents, but launched concurrently. Looks like two reviews in the dispatch log, but spec→quality gaps of 5-22 seconds are mechanically incompatible with two independent reviews of substantive code. **Rule**: dispatch spec, wait for result, evaluate, THEN dispatch quality. Never both in one message.

3. **Quality-written-before-spec** (Tasks 15, 20): symptom of parallel dispatch where the quality subagent finished first. **Rule**: not just sequential dispatch — sequential evaluation. If spec fails, you may skip quality entirely. Parallel dispatch eliminates that option.

The dispatch-log hook catches combined-dispatch (case 1) on the *next* task. Parallel dispatch (case 2) is not currently detected — see "Integration Tests Catch What Unit Tests Miss" below for the broader pattern of static checks missing runtime composition issues.

---

## Implementer Report Format

Implementer reports are validated by `validate-report.py` against two layers:
1. **Pydantic frontmatter** via `validators.py report`: requires specific fields (`task_id`, `status`, `files_changed` as list-of-dicts with `path` + `description`, `tests` with `written`/`passing`/`command`/`result` where `passing <= written` and `result in {"PASS", "FAIL"}`).
2. **Prose sections** via regex header scan: requires the five exact section headers:
   - `**Implementation Summary:**`
   - `**Source Files Read:**`
   - `**Deviations from Plan:**`
   - `**Self-Review Findings:**`
   - `**Concerns:**`

**Common implementer mistakes** (caught in 2026-05-20 session):
- `tests.result: N/A` — invalid; use `PASS` with `written: 0, passing: 0` for tasks that don't author tests (regression-only verification).
- `passing > written` — invalid Pydantic invariant; for regression-only tasks, set both to 0 and describe the regression coverage in `tests.command`.
- `files_modified` (wrong field name) — schema requires `files_changed` with `path`+`description` dict shape.
- `## Header` markdown — `validate_report_sections()` scans for `**Header:**` form; `## Header` is not matched.
- Adding extra fields like `task_title`, `plan_departures` — Pydantic `extra="forbid"` rejects these.

**Process rule**: If the implementer's report fails validation, **re-dispatch the implementer to fix it**, do not patch the report yourself. If you must patch (e.g., schema field rename that the implementer can't be expected to know), commit the patch immediately with a clear "controller patch (not implementer)" message disclosing provenance. Uncommitted controller-authored report content lets the working tree silently diverge from published history.

---

## Integration Tests Catch What Unit Tests Miss

The 2026-05-20 adaptive-enforcement-tiers feature shipped four scripts (`materialize-manifest.py`, `controller-checkpoint.py --manifest`, `transition-module.py`, `validators.py session`) that all had passing unit tests AND a passing pre-completion gate. The e2e composed-pipeline test (`tests/integration/sdd-e2e-test.sh`) found an integration bug on first run:

> `_load_manifest_config(args)` resolved `active_module_file` as `os.path.join(git_root, manifest.active_module_file)`, producing `<git_root>/module-1.md` instead of `<git_root>/<feature_dir>/module-1.md`. The hook (Module 2) had this corrected in deviation row 3; Task 14's Python code missed the same correction. Unit tests didn't catch it because Task 15's `setup_checkpoint_workspace` fixture set `active_module_file: None`, so the buggy branch was never exercised.

**Lesson**: unit tests cover branches that exist in fixtures. Integration tests cover branches that exist in composed-runtime reality. For any feature with multiple scripts that compose into a pipeline, write an end-to-end smoke test that runs the actual pipeline against a temp git repo. Cost: 100 lines of bash. Catch rate from this incident: 1 real bug + structural confidence that the gate doesn't have.

---

## First Live Runs Find What Even Integration Tests Miss (2026-06-10 lessons)

The sdd-cleanup-and-integration-gate sprint ran the first-ever live `transition-module.py` module transition — with 456 unit tests and an 11-step e2e suite green. Three lessons from one session:

1. **The first live exercise of a path is part of its acceptance test.** The transition itself ran clean, but the very next action (pre-dispatch checkpoint for module 2's first task) FAILed: the hook had the N3a boundary guard since the hardening feature, but `controller-checkpoint.py` never got the matching guard (N18) — and no unit or e2e test composed "transition, then checkpoint" in that order. Budget the first live run as a discovery activity; the fix-with-full-ceremony loop (deviation row → TDD fix subagent → dispatched reviews → re-run the gate) took under an hour because the context was hot.

2. **Provenance gates catch real fabrication — when remediation is real dispatches, the delta is visible.** A prior session had controller-written Task 3 review files (no dispatch-log entries; mtimes 5-10s after the implementer report). The remediation dispatched REAL reviewers for the same commit: the fabricated quality review had said "PASS / Issues found: None"; the real one found 1 Critical (a plan-prescribed fix that was a no-op), 1 Important, 3 Minor. That contrast is the empirical justification for Check 4c — keep it.

3. **Hunt fail-opens by probing the live repo, not just fixtures.** Two shipped in this feature's own new gate and were caught only because reviewers probed reality: `origin/HEAD`-first base-ref selection was 21 commits stale in THIS repo (local-only merges) — widening the "feature changeset" to swallow prior features; and present-but-malformed `integration_test` declarations (flat string, empty path) silently classified as "not declared" → PASS. Review prompts for enforcement code should explicitly ask "run it against this repo, now — what does it actually resolve/skip?"

Also reaffirmed: review-driven fixes need their own post-fix review (the honesty check caught two unreviewed prescribed-fix commits; the combined verification then proved both RED→GREEN from pre-fix code), and ad-hoc fix dispatches are currently invisible to the dispatch log (BACKLOG N26) — the tamper-evidence backbone only sees classified dispatches.

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

## Self-Modifying Enforcement Runs (2026-05-29 lessons)

The SDD Hook Improvements feature used SDD to modify the SDD enforcement hooks themselves (`sdd-pre-dispatch-hook.sh`, `controller-checkpoint.py`). Lessons from running the disciplined process *on* the thing that enforces discipline — under a transient API outage.

### Worktree isolation keeps the live hook stable during a self-modifying run

The enforcement hooks are symlink-installed from this repo's `main` checkout (`settings.json` → main path, via the `~/.claude/skills/superpowers` symlink). Editing them on `main` would self-modify enforcement *mid-run*. Running in a worktree means the worktree's hook diverges while the **live** hook stays the main checkout's unchanged copy — the restructure never destabilizes the session running it. Confirm before starting: the Agent-matcher hook path in `settings.json` resolves to the main checkout, not the worktree.

### The no-op-hook run: when the live hook can't enforce *this* session

If the bug you're fixing IS in the live hook, the live hook may not enforce your own run. Here, the live (pre-fix) hook passed all `general-purpose` dispatches straight through (the exact Item-1 bug being fixed), so with general-purpose subagents the hook was a **no-op all session** — no provenance logging, no gating. The explicit choice (made with the user) was "manual discipline": dispatch as general-purpose, accept zero hook backstop, and compensate by running `controller-checkpoint.py` at every phase by hand and dispatching every spec+quality review manually.

- **Decide the dispatch `subagent_type` BEFORE Task 1** — it determines whether the hook enforces. A type the live hook gates on (not in its passthrough list) would enforce but risks deadlock on the very bugs under repair; general-purpose is the safe no-enforcement choice. Be consistent: mixing an enforced implementer type with a passed-through reviewer type deadlocks the provenance gate at Task 2 (reviewers never logged → next implementer blocked).
- **A no-op hook does not relax the process.** The controller still runs every checkpoint + review; what's lost is the mechanical backstop, not the discipline. Disclose it prominently in the honesty check and `deviations.md`.

### Verify the new enforcement code's real-dispatch seam

A no-op-hook run means the new hook is exercised only by *synthetic* unit-test inputs (`make_hook_input`), never a real dispatch. Before trusting it, verify the seam between real dispatch payloads and the classifier: the final reviewer confirmed `implementer-prompt.md` carries BOTH backstops the new classifier keys on (`description: "Implement Task N"` matches the description regex; body "You are implementing Task N" lands within `head -c 500` for the prompt-path regex). Carry a **post-merge live smoke test** as an explicit follow-up — one real general-purpose reviewer + implementer dispatch from main.

### Operating through API instability (long dispatches socket-closing)

Mid-run, subagent dispatches began failing: first HTTP 529 overloads (cleared after a backoff), then socket-closes that dropped the connection after ~6 tool uses on *long* dispatches (~24 min) — the agent never reached its edit/commit before the drop (repo verified clean each time). Adaptations that worked:

- **Lean prompts deliver; long ones don't.** Short, focused review dispatches (≤7 tool uses, ≤400-word reports) completed reliably where verbose ones socket-closed on the final response. When a long dispatch keeps failing, instruct subagents to **commit as soon as green and keep the report ≤350 words** — the committed code is the deliverable; even if the report is lost, the work persists and you recover by inspecting the repo.
- **When a long implementer dispatch is unrecoverable, the controller may apply verbatim plan code directly** — but ONLY when the plan prescribes the exact code (here: a bash line-splice + a fixed test file), so no implementer design judgment is lost. Preserve independence by dispatching the spec + quality reviews separately (short → they succeed). Disclose controller-implementation in `deviations.md` + the honesty check. (Tasks 6 and 9 were controller-implemented this way; both independently reviewed; the trace auditor confirmed verification was adequate.)

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
| SDD execution artifacts | Project root (worktree) | `DEVIATIONS.md`, `reports/task-NNN-*.md` (3-digit zero-padded) |

## Report Naming Convention

| Rule | Standard |
|------|----------|
| Format | `task-NNN-{type}.md` — 3-digit zero-padded sequential |
| Numbering | Sequential across ALL modules (Module 1 tasks 000-003, Module 2 tasks 004-011, etc.) |
| Types | `implementer-report`, `spec-review`, `quality-review`, `quality-review-minimum-tier` |
| Prohibited | Module-prefixed names (`m2-task-1-*`), symlinks between conventions |
| Why | Pre-dispatch hook checks task N-1 reports before allowing task N. Module-prefixed names break sequential checking. |
| Backward compat | Hook finds both `task-007-*` (new) and `task-7-*` (old) |
| Incident | Module 2 controller used `m2-task-N-*` naming, created symlinks to satisfy hook. Symlinks are fragile. |

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
| Agent bypasses SDD skill entirely | Module 3: agent read plan, implemented directly — zero reviews, 5 uncertainties found via honesty prompt | Write/Edit transcript hook injects warning + CLAUDE.md Skill Invocation Rule + honesty check before gate |
| Controller uses module-prefixed report names | Module 2: `m2-task-1-*` naming broke sequential hook check; controller created symlinks as workaround | `task-NNN` 3-digit sequential naming enforced across all modules; module-prefixed names prohibited |
| Context compaction drops discipline rules | Long sessions: agent resumes with only task description | File-based enforcement (reports must exist) survives compaction; hook state is filesystem state |
| Wrong test fixtures | Statement Reconciliation: fixtures used numeric types, real output uses strings with commas | "Ground-truth fixtures" step: derive fixtures from real system output BEFORE writing any code |
| Agent bypasses SDD skill entirely — reads plan, implements directly without subagents | Module 3 of Statement Reconciliation: agent admitted to zero reviews, 5 uncertainties post-execution | `Write\|Edit` transcript hook injects warning + CLAUDE.md Skill Invocation Rule + honesty check before Pre-Completion Gate |
| Upstream merge overwrites fork customizations | Agent relied on stale CLAUDE.md info claiming v0.1 files "not yet promoted" — would have let upstream overwrite promoted customizations | Three-way comparison (merge-base vs ours vs upstream) is mandatory. Never trust documentation about file state — verify against the filesystem. All 15 SKILL.md files diverge from upstream. |
| Agent uses unittest instead of pytest without asking | Controller chose unittest for new test files without consulting user on framework preference | Test framework choice is a consequential decision requiring approval. Saved as feedback memory for future sessions. |
| Agent skips plan validation during modular plan writing | Agent wrote 5 plan modules without running validate-plan.py or dispatching the plan reviewer; only self-corrected after user intervention | Checklist added to writing-plans skill; Plan Completion Gate section makes steps 8-10 non-negotiable; `plan-validation-gate-hook.sh` blocks execution skill invocation without validation pass + review report |
| Combined spec+quality review subagent dispatch | 2026-05-20 adaptive-enforcement-tiers Tasks 16, 18: one Agent call produced both review files; dispatch-log hook blocked next task because only one entry was logged | Dispatch each review type as its own Agent call. The hook's per-task dispatch-log check catches this on the *next* task. Recovery is to dispatch two "verification" subagents to confirm existing reviews — but those are rubber-stamps, not independent audits. |
| Parallel spec+quality review dispatch | 2026-05-20: spec and quality dispatched in the same message as separate Agent tool blocks; gaps of 5-22 seconds; quality-written-before-spec in 2 tasks | The SDD skill says "spec PASS THEN quality". Parallel violates the sequencing rule even when subagents are independent. Dispatch spec, wait for result, evaluate, THEN dispatch quality — never both in one message. Not currently hook-detected; rely on trace auditor + this convention. |
| Controller patches implementer report instead of re-dispatching | 2026-05-20: three reports edited directly for Pydantic schema fixes (result: N/A → PASS, passing: 24 → 0, prose-header rewrite); two were uncommitted at honesty-check time | Re-dispatch the implementer to fix schema/section issues. If you must patch (rare; e.g., field rename the implementer can't know), commit the patch immediately with explicit "controller patch (not implementer)" message disclosing provenance. Uncommitted controller-authored content lets working tree silently diverge from history. |
| Integration bug masked by unit test fixture | 2026-05-20: `_load_manifest_config` missing `feature_dir` join in path resolution; all 326 unit tests passed because the test fixture set `active_module_file: None`, never exercising the buggy branch | Write an end-to-end smoke test (e.g., `tests/integration/sdd-e2e-test.sh`) that composes all feature scripts against a temp git repo. Run before declaring feature complete. Cost: 100 lines of bash. Catches what unit tests can't: runtime composition issues. |
| Plan-reference code contains the same bug across multiple tasks | 2026-05-20: midpoint formula `range_size = end - start + 1` appeared in Task 4, Task 11, and Task 12 plan-reference code; corrected via deviation row each time | Extract repeated logic to a shared module (e.g., `_midpoint.py`) at the first occurrence — do not "Deferred — log only" three times. Update the plan author's source (writing-plans SKILL.md) so future plans don't regenerate the bug. |
| Multi-module pre-completion gate false-FAILs on completed modules | 2026-05-29: `transition-module.py` archives completed-module reports to `reports/archive-<module>/`, but `all_tasks_have_reports` (pre-completion) extracts task headers from ALL module plan files yet globs `reports/` flat (non-recursive) → "Missing reports for Task 1-4" after a transition | Restore the archived reports to flat `reports/` to satisfy the gate (they exist + were validated at transition; controller-applied this run). Real fix (future, BACKLOG): make `find_report_file`/`all_tasks_have_reports` archive-aware (also search `reports/archive-*/`), OR have pre-completion validate only the active module and trust transition validation for completed modules. |
| Controller's own report omits a required section | 2026-05-29: a controller-authored implementer report (Task 8) was missing "Self-Review Findings"; a `tail -2` validation check only saw the trailing JSON and missed the INCOMPLETE status | Always read the full `validate-report.py` `status` field, not just the tail. The Task-9 pre-dispatch `previous_report_complete` check caught it — file-based gates catch controller reporting slips the controller's own spot-checks miss. |
