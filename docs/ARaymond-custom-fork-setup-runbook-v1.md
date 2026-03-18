# Superpowers Custom Fork — Setup Runbook

**Author**: Aaron Raymond
**Version**: 1.0
**Date**: 2026-03-17
**Fork Repo**: `~/projects/claude-custom/superpowers`
**Upstream**: `https://github.com/obra/superpowers`

---

## Prerequisites

- Superpowers marketplace plugin must be uninstalled (`/plugin uninstall superpowers@claude-plugins-official`)
- Delete orphaned plugin cache: `rm -rf ~/.claude/plugins/cache/claude-plugins-official/superpowers/`
- Fork repo must be cloned and up to date with upstream

---

## Step 1: Symlink Skills (single parent symlink)

```bash
ln -s ~/projects/claude-custom/superpowers/skills ~/.claude/skills/superpowers
```

This creates `superpowers:<skill-name>` namespace for all 14 skills automatically.

**Verify:**
```bash
find -L ~/.claude/skills/superpowers -name "SKILL.md" | wc -l
# Expected: 14
```

---

## Step 2: Symlink Agent (renamed)

```bash
ln -s ~/projects/claude-custom/superpowers/agents/code-reviewer.md ~/.claude/agents/superpowers-code-reviewer.md
```

The agent file in the fork has `name: superpowers-code-reviewer` in its frontmatter (changed from `code-reviewer` to avoid conflict with the existing `~/.claude/agents/code-reviewer.md`).

---

## Step 3: Add SessionStart Hook

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

`CLAUDE_PLUGIN_ROOT` must be set in the command so the hook script outputs the correct Claude Code JSON format.

---

## Not Installed

- **Commands** (`commands/brainstorm.md`, `execute-plan.md`, `write-plan.md`) — deprecated stubs that just say "use the skill instead." Not needed since skills are directly discoverable.

---

## Fork Customizations (applied to repo files)

These edits live in the fork and must be preserved when pulling upstream changes.

### 1. Agent name change
**File**: `agents/code-reviewer.md`
**Change**: Frontmatter `name:` field from `code-reviewer` to `superpowers-code-reviewer`

### 2. Skill references to renamed agent
**File**: `skills/requesting-code-review/SKILL.md`
**Change**: All `superpowers:code-reviewer` → `superpowers-code-reviewer` (3 occurrences)

**File**: `skills/subagent-driven-development/code-quality-reviewer-prompt.md`
**Change**: `superpowers:code-reviewer` → `superpowers-code-reviewer` (1 occurrence)

---

## External File Updates (outside the fork)

### `~/.claude/CLAUDE.md`
1. "Plugin Cache Fragility" section — superpowers entry updated to reference custom fork instead of plugin cache re-apply instructions
2. "Agent subagent_type naming" — example updated from `superpowers:code-reviewer` to `superpowers-code-reviewer`

### `~/projects/personal-finance-api/docs/subagents/subagent-claude-md-enforcement.md`
- Header updated: plugin path → fork path
- "How to Re-Apply" section rewritten for fork workflow
- Version bumped to 1.1

---

## What Does NOT Need Changing

- All `superpowers:<skill-name>` references in CLAUDE.md files and plan documents are correct as-is (the nested symlink preserves the namespace)
- RELEASE-NOTES.md historical entries — leave as-is
- OLD- prefixed archived plan files — leave as-is

---

## Pulling Upstream Updates

```bash
cd ~/projects/claude-custom/superpowers
git fetch upstream
git merge upstream/main
```

Resolve merge conflicts in these files (they contain fork customizations):
- `agents/code-reviewer.md` — preserve `name: superpowers-code-reviewer`
- `skills/requesting-code-review/SKILL.md` — preserve `superpowers-code-reviewer` references
- `skills/subagent-driven-development/code-quality-reviewer-prompt.md` — preserve `superpowers-code-reviewer` reference
