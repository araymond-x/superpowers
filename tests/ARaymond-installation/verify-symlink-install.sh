#!/usr/bin/env bash
# ARaymond custom fork: symlink installation verification
#
# Verifies that the symlink+command-stub installation is intact.
# Fast, deterministic, no API calls — safe to run anytime.
#
# Usage:
#   ./verify-symlink-install.sh           # run all checks
#   ./verify-symlink-install.sh --verbose  # show passing checks too
#
# Exit codes:
#   0 = all checks passed
#   1 = one or more checks failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SKILLS_DIR="$HOME/.claude/skills/superpowers"
COMMANDS_DIR="$HOME/.claude/commands/superpowers"
AGENT_FILE="$HOME/.claude/agents/superpowers-code-reviewer.md"
SETTINGS_FILE="$HOME/.claude/settings.json"

VERBOSE=false
[[ "${1:-}" == "--verbose" ]] && VERBOSE=true

passed=0
failed=0
warned=0

pass() {
  passed=$((passed + 1))
  [[ "$VERBOSE" == true ]] && echo "  [PASS] $1" || true
}

fail() {
  failed=$((failed + 1))
  echo "  [FAIL] $1"
}

warn() {
  warned=$((warned + 1))
  echo "  [WARN] $1"
}

section() {
  echo ""
  echo "=== $1 ==="
}

# ─── 1. Skills Symlink ────────────────────────────────────────────────────────

section "Skills Symlink"

if [[ -L "$SKILLS_DIR" ]]; then
  pass "Skills directory is a symlink"
  target=$(readlink "$SKILLS_DIR")
  if [[ -d "$target" ]]; then
    pass "Symlink target exists: $target"
  else
    fail "Symlink target missing: $target"
  fi
else
  if [[ -d "$SKILLS_DIR" ]]; then
    warn "Skills directory exists but is not a symlink (individual symlinks inside?)"
  else
    fail "Skills directory missing: $SKILLS_DIR"
  fi
fi

# Count skills
skill_count=$(find -L "$SKILLS_DIR" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$skill_count" -ge 15 ]]; then
  pass "Found $skill_count skills (expected >= 15)"
else
  fail "Found $skill_count skills (expected >= 15)"
fi

# Verify each SKILL.md is readable
for skill_dir in "$SKILLS_DIR"/*/; do
  name=$(basename "$skill_dir")
  skill_file="$skill_dir/SKILL.md"
  if [[ -r "$skill_file" ]]; then
    # Check frontmatter exists
    if head -1 "$skill_file" | grep -q '^---$'; then
      pass "Skill '$name' has valid SKILL.md with frontmatter"
    else
      fail "Skill '$name' SKILL.md missing frontmatter"
    fi
  else
    fail "Skill '$name' SKILL.md not readable: $skill_file"
  fi
done

# ─── 2. Command Stubs ─────────────────────────────────────────────────────────

section "Command Stubs"

if [[ -d "$COMMANDS_DIR" ]]; then
  pass "Commands directory exists"
else
  fail "Commands directory missing: $COMMANDS_DIR"
fi

command_count=$(ls "$COMMANDS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
if [[ "$command_count" -ge 15 ]]; then
  pass "Found $command_count command stubs (expected >= 15)"
else
  fail "Found $command_count command stubs (expected >= 15)"
fi

# Verify skill/command count match
if [[ "$skill_count" -eq "$command_count" ]]; then
  pass "Skill count ($skill_count) matches command count ($command_count)"
else
  fail "Skill count ($skill_count) != command count ($command_count) — orphans exist"
fi

# Check each command stub
for cmd_file in "$COMMANDS_DIR"/*.md; do
  name=$(basename "$cmd_file" .md)

  # Corresponding skill directory must exist
  if [[ -d "$SKILLS_DIR/$name" ]]; then
    pass "Command '$name' has matching skill directory"
  else
    fail "Command '$name' has no matching skill directory at $SKILLS_DIR/$name"
  fi

  # Check frontmatter has name field with superpowers: prefix
  if grep -q "^name: superpowers:$name" "$cmd_file"; then
    pass "Command '$name' frontmatter has correct name"
  else
    fail "Command '$name' frontmatter missing or wrong name (expected 'superpowers:$name')"
  fi

  # Check description field exists
  if grep -q "^description:" "$cmd_file"; then
    pass "Command '$name' has description"
  else
    fail "Command '$name' missing description in frontmatter"
  fi

  # Check !`cat` preprocessing target resolves
  cat_target=$(grep -o "cat [^ |]*" "$cmd_file" 2>/dev/null | head -1 | sed 's/^cat //')
  if [[ -n "$cat_target" ]]; then
    # Expand ~ to $HOME
    expanded_target="${cat_target/#\~/$HOME}"
    if [[ -r "$expanded_target" ]]; then
      pass "Command '$name' cat target exists: $cat_target"
    else
      fail "Command '$name' cat target missing: $cat_target (expanded: $expanded_target)"
    fi
  else
    fail "Command '$name' has no !cat preprocessing line"
  fi
done

# Check for orphaned commands (command exists but no matching skill)
for cmd_file in "$COMMANDS_DIR"/*.md; do
  name=$(basename "$cmd_file" .md)
  if [[ ! -d "$SKILLS_DIR/$name" ]]; then
    fail "Orphaned command stub '$name' — no matching skill"
  fi
done

# Check for orphaned skills (skill exists but no matching command)
for skill_dir in "$SKILLS_DIR"/*/; do
  name=$(basename "$skill_dir")
  if [[ ! -f "$COMMANDS_DIR/$name.md" ]]; then
    fail "Orphaned skill '$name' — no matching command stub (won't appear in /skills picker)"
  fi
done

# ─── 3. Agent Symlink ─────────────────────────────────────────────────────────

section "Agent"

if [[ -L "$AGENT_FILE" ]]; then
  pass "Agent file is a symlink"
  target=$(readlink "$AGENT_FILE")
  if [[ -r "$AGENT_FILE" ]]; then
    pass "Agent symlink resolves"
    # Check name field
    if grep -q "^name: superpowers-code-reviewer" "$AGENT_FILE"; then
      pass "Agent name is 'superpowers-code-reviewer'"
    else
      fail "Agent name field incorrect (expected 'superpowers-code-reviewer')"
    fi
  else
    fail "Agent symlink broken: $target"
  fi
else
  if [[ -f "$AGENT_FILE" ]]; then
    warn "Agent file exists but is not a symlink"
  else
    fail "Agent file missing: $AGENT_FILE"
  fi
fi

# ─── 4. SessionStart Hook ─────────────────────────────────────────────────────

section "SessionStart Hook"

if [[ -r "$SETTINGS_FILE" ]]; then
  if grep -q "session-start" "$SETTINGS_FILE"; then
    pass "SessionStart hook references session-start script"
  else
    fail "SessionStart hook missing from settings.json"
  fi

  if grep -q "CLAUDE_PLUGIN_ROOT" "$SETTINGS_FILE"; then
    pass "Hook sets CLAUDE_PLUGIN_ROOT env var"
  else
    fail "Hook missing CLAUDE_PLUGIN_ROOT env var"
  fi
else
  fail "Settings file not readable: $SETTINGS_FILE"
fi

# ─── 4b. Enforcement Hooks in Settings ───────────────────────────────────────

section "Enforcement Hooks"

# Check Agent matcher exists in PreToolUse
if grep -q '"matcher": "Agent"' ~/.claude/settings.json 2>/dev/null; then
    pass "PreToolUse has Agent matcher (SDD enforcement hook)"
else
    fail "PreToolUse missing Agent matcher — SDD enforcement not registered"
fi

# Check Skill matcher exists in PreToolUse
if grep -q '"matcher": "Skill"' ~/.claude/settings.json 2>/dev/null; then
    pass "PreToolUse has Skill matcher (handoff gate hook)"
else
    fail "PreToolUse missing Skill matcher — handoff gate not registered"
fi

# Check Agent hook script (sdd-pre-dispatch-hook.sh) is referenced and exists
AGENT_HOOK_PATH=$(grep -o '"[^"]*sdd-pre-dispatch-hook\.sh"' ~/.claude/settings.json 2>/dev/null | head -1 | tr -d '"')
if [ -n "$AGENT_HOOK_PATH" ] && [ -f "$AGENT_HOOK_PATH" ]; then
    pass "Agent hook script exists at configured path: $AGENT_HOOK_PATH"
else
    fail "Agent hook script (sdd-pre-dispatch-hook.sh) missing or not in settings.json"
fi

# Check Skill hook script (handoff-gate-hook.sh) is referenced and exists
SKILL_HOOK_PATH=$(grep -o '"[^"]*handoff-gate-hook\.sh"' ~/.claude/settings.json 2>/dev/null | head -1 | tr -d '"')
if [ -n "$SKILL_HOOK_PATH" ] && [ -f "$SKILL_HOOK_PATH" ]; then
    pass "Skill hook script exists at configured path: $SKILL_HOOK_PATH"
else
    fail "Skill hook script (handoff-gate-hook.sh) missing or not in settings.json"
fi

# Check sdd-report-guard.sh is in Bash hooks
if grep -q "sdd-report-guard.sh" ~/.claude/settings.json 2>/dev/null; then
    pass "Bash hooks include sdd-report-guard.sh"
else
    fail "Bash hooks missing sdd-report-guard.sh — report forgery guard not registered"
fi

# Check sdd-stop-hook.sh is in Stop hooks
if grep -q "sdd-stop-hook.sh" ~/.claude/settings.json 2>/dev/null; then
    pass "Stop hooks include sdd-stop-hook.sh"
else
    fail "Stop hooks missing sdd-stop-hook.sh — pre-completion enforcement not registered"
fi

# ─── 5. Cross-Skill References ────────────────────────────────────────────────

section "Cross-Skill References"

# brainstorming → visual-companion.md
ref="$SKILLS_DIR/brainstorming/visual-companion.md"
if [[ -r "$ref" ]]; then
  pass "brainstorming/visual-companion.md exists"
else
  fail "brainstorming references visual-companion.md but file missing"
fi

# brainstorming → scripts/start-server.sh
ref="$SKILLS_DIR/brainstorming/scripts/start-server.sh"
if [[ -r "$ref" ]]; then
  pass "brainstorming/scripts/start-server.sh exists"
else
  fail "brainstorming references start-server.sh but file missing"
fi

# subagent-driven-development → code-quality-reviewer-prompt.md
ref="$SKILLS_DIR/subagent-driven-development/code-quality-reviewer-prompt.md"
if [[ -r "$ref" ]]; then
  pass "subagent-driven-development/code-quality-reviewer-prompt.md exists"
else
  fail "SDD references code-quality-reviewer-prompt.md but file missing"
fi

# requesting-code-review → should reference superpowers-code-reviewer agent
if grep -q "superpowers-code-reviewer" "$SKILLS_DIR/requesting-code-review/SKILL.md" 2>/dev/null; then
  pass "requesting-code-review references superpowers-code-reviewer agent"
else
  fail "requesting-code-review should reference superpowers-code-reviewer (fork customization)"
fi

# SDD code-quality-reviewer-prompt → should reference superpowers-code-reviewer agent
if grep -q "superpowers-code-reviewer" "$SKILLS_DIR/subagent-driven-development/code-quality-reviewer-prompt.md" 2>/dev/null; then
  pass "SDD code-quality-reviewer-prompt references superpowers-code-reviewer agent"
else
  fail "SDD code-quality-reviewer-prompt should reference superpowers-code-reviewer (fork customization)"
fi

# handoff-acceptance → SKILL.md exists
ref="$SKILLS_DIR/handoff-acceptance/SKILL.md"
if [[ -r "$ref" ]]; then
  pass "handoff-acceptance/SKILL.md exists"
else
  fail "handoff-acceptance/SKILL.md missing"
fi

# handoff-acceptance → scripts/check-handoff.sh
ref="$SKILLS_DIR/handoff-acceptance/scripts/check-handoff.sh"
if [[ -r "$ref" ]]; then
  pass "handoff-acceptance/scripts/check-handoff.sh exists"
else
  fail "handoff-acceptance references check-handoff.sh but file missing"
fi

# handoff-acceptance → references/acceptance-flow.dot
ref="$SKILLS_DIR/handoff-acceptance/references/acceptance-flow.dot"
if [[ -r "$ref" ]]; then
  pass "handoff-acceptance/references/acceptance-flow.dot exists"
else
  fail "handoff-acceptance references acceptance-flow.dot but file missing"
fi

# ─── 6. .gitignore ────────────────────────────────────────────────────────────

section "Gitignore"

if grep -q "\.superpowers/" "$REPO_ROOT/.gitignore" 2>/dev/null; then
  pass ".superpowers/ is gitignored"
else
  warn ".superpowers/ not in .gitignore — visual companion output may be committed"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "========================================"
echo " Installation Verification Summary"
echo "========================================"
echo ""
echo "  Passed:   $passed"
echo "  Failed:   $failed"
echo "  Warnings: $warned"
echo ""

if [[ $failed -gt 0 ]]; then
  echo "STATUS: FAILED"
  exit 1
else
  echo "STATUS: PASSED"
  exit 0
fi
