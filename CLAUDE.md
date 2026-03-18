# Superpowers Custom Fork

Custom fork of obra/superpowers. Installed via symlinks to ~/.claude/, NOT as a marketplace plugin.

## Setup Reference
- Full setup runbook: `docs/ARaymond-custom-fork-setup-runbook-v1.md`

## Installation Architecture
- Skills: `~/.claude/skills/superpowers` → `./skills/` (single parent symlink, creates `superpowers:` namespace)
- Agent: `~/.claude/agents/superpowers-code-reviewer.md` → `./agents/code-reviewer.md`
- Hook: SessionStart in `~/.claude/settings.json` calls `./hooks/session-start` with `CLAUDE_PLUGIN_ROOT` set
- Commands: NOT installed (deprecated stubs, unnecessary)

## Fork Customizations (preserve during upstream merge)
- `agents/code-reviewer.md` — `name:` changed to `superpowers-code-reviewer`
- `skills/requesting-code-review/SKILL.md` — agent refs changed to `superpowers-code-reviewer`
- `skills/subagent-driven-development/code-quality-reviewer-prompt.md` — agent ref changed to `superpowers-code-reviewer`

## Upstream Sync
```bash
git fetch upstream && git merge upstream/main
```
Conflict files: `agents/code-reviewer.md`, `skills/requesting-code-review/SKILL.md`, `skills/subagent-driven-development/code-quality-reviewer-prompt.md`

## Verify Installation
```bash
# Skills: expect 14
find -L ~/.claude/skills/superpowers -name "SKILL.md" | wc -l
# Agent symlink intact
ls -la ~/.claude/agents/superpowers-code-reviewer.md
# Hook present in settings
grep -c "session-start" ~/.claude/settings.json
```

## Testing
- `docs/testing.md` describes the integration test framework but references a plugin-based setup (`superpowers@superpowers-dev`) — not applicable to this fork's symlink install
- Token analysis works standalone: `python3 tests/claude-code/analyze-token-usage.py <session.jsonl>`

## Process Improvement Findings (`docs/process-improvement-findings/`)
Real-world issues from using superpowers in production projects. Use these to inform fork customizations.
- `subagent-claude-md-enforcement.md` — Subagents skip subdirectory CLAUDE.md files; prompt template fix for implementer and spec-reviewer
- `2026-03-16-statement-reconciliation-lessons-learned.md` — Post-mortem from a large SDD session; handoff quality and context gaps
- `2026-03-16-plan-review-findings-aws-explore.md` — Plan review gaps found during aws-explore project
- `2026-03-16-handoff-quality-recommendations-aws-explore.md` — Recommendations for improving subagent handoff quality
- `ResponseCapture-*.txt` — Raw session captures documenting failure modes

## Key Architecture Notes
- Skills use inline prompt templates (`./implementer-prompt.md`) for subagent dispatch, NOT formal agent files
- Only 1 formal agent exists (`code-reviewer.md`) — used for final whole-implementation review
- Nested skill directories create colon namespaces (`skills/superpowers/brainstorming/` → `superpowers:brainstorming`)
- Agents do NOT support nested directory namespacing — must use flat files with unique names
