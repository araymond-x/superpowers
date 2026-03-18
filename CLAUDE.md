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
# Skills: expect 14
find -L ~/.claude/skills/superpowers -name "SKILL.md" | wc -l
# Commands: expect 14 (powers /skills picker)
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
- `docs/testing.md` describes the integration test framework but references a plugin-based setup (`superpowers@superpowers-dev`) — not applicable to this fork's symlink install
- Token analysis works standalone: `python3 tests/claude-code/analyze-token-usage.py <session.jsonl>`

## Process Improvement Findings (`docs/process-improvement-findings/`)
Real-world issues from using superpowers in production projects. Use these to inform fork customizations.
- `subagent-claude-md-enforcement.md` — Subagents skip subdirectory CLAUDE.md files; prompt template fix for implementer and spec-reviewer
- `2026-03-16-statement-reconciliation-lessons-learned.md` — Post-mortem from a large SDD session; handoff quality and context gaps
- `2026-03-16-plan-review-findings-aws-explore.md` — Plan review gaps found during aws-explore project
- `2026-03-16-handoff-quality-recommendations-aws-explore.md` — Recommendations for improving subagent handoff quality
- `ResponseCapture-*.txt` — Raw session captures documenting failure modes

## `.superpowers/` Directory
The visual brainstorming companion writes session data to `.superpowers/brainstorm/` in the project root. Each session gets a timestamped subdirectory containing HTML mockups, browser click events (`.events`), and server info. This directory is gitignored — it's ephemeral working state, not project artifacts.

## Key Architecture Notes
- Skills use inline prompt templates (`./implementer-prompt.md`) for subagent dispatch, NOT formal agent files
- Only 1 formal agent exists (`code-reviewer.md`) — used for final whole-implementation review
- Personal skills (`~/.claude/skills/`) only support one level of nesting for the `/skills` picker. The `superpowers:` namespace in the picker comes from command stubs at `~/.claude/commands/superpowers/`, NOT from the skills directory structure
- Agents do NOT support nested directory namespacing — must use flat files with unique names
