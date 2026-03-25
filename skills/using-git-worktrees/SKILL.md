---
name: using-git-worktrees
description: "Use when starting feature work that needs isolation from the current workspace, or before executing implementation plans in a dedicated directory"
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection Process

Follow this priority order:

### Standard Location: `.worktrees/` Inside the Project

All worktrees are created at `<project-root>/.worktrees/<feature-name>/`. This is the ONLY supported location.

```bash
# Check if .worktrees/ exists
ls -d .worktrees 2>/dev/null
```

**If found:** Use it. **If not found:** Create it, add to `.gitignore`, commit.

Do NOT create worktrees as sibling directories (`~/projects/project-name-feature/`), in global locations (`~/.config/.../`), or anywhere else. Sibling worktrees clutter the projects directory and create naming inconsistency. The SDD enforcement hooks verify the session CWD contains `.worktrees` in the path — worktrees created elsewhere will trigger warnings during execution.

**Naming convention:** `.worktrees/<feature-name>/` matching the branch name.
```
.worktrees/statement-reconciliation-v1/
.worktrees/auth-system/
.worktrees/notification-service/
```

## Safety Verification

### For Project-Local Directories (.worktrees or worktrees)

**Verify directory is ignored before creating worktree:**

```bash
# Check if directory is ignored (respects local, global, and system gitignore)
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**If NOT ignored:**

Per Jesse's rule "Fix broken things immediately":
1. Add appropriate line to .gitignore
2. Commit the change (committing the .gitignore update before creating the worktree ensures contents are excluded from the first git status)
3. Proceed with worktree creation

**Why critical:** Prevents accidentally committing worktree contents to repository.

## Branch Name Collisions

If the branch name you want already exists, an existing worktree or prior implementation attempt may be using it.

**Do not delete existing branches or worktrees to resolve a naming collision.** The prior work may be needed for comparison, rollback, or reference.

Instead:
- Check if a worktree already exists: `git worktree list | grep <branch-name>`
- If it does, ask the user whether to reuse it, remove it, or create a versioned branch
- For re-implementations of the same feature, use a versioned branch name: `feature/<name>-v2`, `feature/<name>-v3`
- Only delete a branch/worktree with explicit user confirmation

## Creation Steps

### 1. Detect Project Name

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Create Worktree

```bash
# Always use .worktrees/ inside the project
path=".worktrees/$BRANCH_NAME"

# Create .worktrees/ if it doesn't exist
mkdir -p .worktrees

# Create worktree with new branch
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

### 3. Run Project Setup

Auto-detect and run appropriate setup (worktrees share the repo but not node_modules or build artifacts — skipping setup causes baseline tests to fail for wrong reasons):

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

### 4. Verify Clean Baseline

Run tests to ensure worktree starts clean:

```bash
# Examples - use project-appropriate command
npm test
cargo test
pytest
go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate. Some repos have pre-existing failures on main — the human needs to confirm whether failures are known or indicate wrong setup.

**If tests pass:** Report ready.

### 5. Session Handoff (MANDATORY — do not skip or continue past this step)

After the worktree is created, set up, and baseline-verified, you MUST hand off to a new session. Claude Code hooks receive CWD from the session start directory — `! cd` does not change hook CWD. SDD enforcement hooks (review gates, audit gates, token checks) will not work unless the session was started from inside the worktree.

**You cannot continue implementation in this session.** Present this exact output to the user and STOP:

```
════════════════════════════════════════════════════════════════
 WORKTREE READY — NEW SESSION REQUIRED
════════════════════════════════════════════════════════════════

 Worktree: <full-path>
 Branch:   <branch-name>
 Tests:    <N> passing, 0 failures

 SDD enforcement hooks require the session to start FROM the
 worktree directory. This session started from the project root
 and cannot be used for implementation.

 To continue, start a new Claude Code session:

   cd <full-path> && claude

 Then give it this prompt:

   Resume SDD execution. Read the plan files in docs/imp-plans/
   to see progress (checkboxes). Invoke superpowers:subagent-driven-development
   and continue from the next unchecked task.

════════════════════════════════════════════════════════════════
```

After presenting this output, STOP. Do not dispatch any implementation tasks, do not invoke SDD, do not continue with "let me just start the first task." The user must start a new session from the worktree directory.

Why this is mandatory: In previous implementations, the agent continued from the project root, causing all SDD hooks to check the wrong directory. Reports, DEVIATIONS.md, and audit artifacts were invisible to the hooks, and enforcement silently failed.

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `.worktrees/` doesn't exist | Create it, add to `.gitignore`, commit |
| Directory not ignored | Add to `.gitignore` + commit before creating worktree |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |
| Branch name already exists | Use versioned name (`-v2`, `-v3`) — do NOT delete |

## Common Mistakes

### Skipping ignore verification

- **Problem:** Worktree contents get tracked, pollute git status
- **Fix:** Always use `git check-ignore` before creating project-local worktree

### Assuming directory location

- **Problem:** Creates inconsistency, violates project conventions
- **Fix:** Follow priority: existing > CLAUDE.md > ask

### Proceeding with failing tests

- **Problem:** Can't distinguish new bugs from pre-existing issues
- **Fix:** Report failures, get explicit permission to proceed

### Hardcoding setup commands

- **Problem:** Breaks on projects using different tools
- **Fix:** Auto-detect from project files (package.json, etc.)

## Example Workflow

```
You: I'm using the using-git-worktrees skill to set up an isolated workspace.

[Check .worktrees/ - exists]
[Verify ignored - git check-ignore confirms .worktrees/ is ignored]
[Create worktree: git worktree add .worktrees/auth -b feature/auth]
[Run npm install]
[Run npm test - 47 passing]

════════════════════════════════════════════════════════════════
 WORKTREE READY — NEW SESSION REQUIRED
════════════════════════════════════════════════════════════════

 Worktree: /Users/aaron/myproject/.worktrees/auth
 Branch:   feature/auth
 Tests:    47 passing, 0 failures

 To continue, start a new Claude Code session:

   cd /Users/aaron/myproject/.worktrees/auth && claude

════════════════════════════════════════════════════════════════

[STOP — do not continue implementation in this session]
```

## Red Flags

**Never:**
- Create worktree without verifying it's ignored (project-local)
- Skip baseline test verification
- Proceed with failing tests without asking
- Assume directory location when ambiguous
- Skip CLAUDE.md check

**Always:**
- Follow directory priority: existing > CLAUDE.md > ask
- Verify directory is ignored for project-local
- Auto-detect and run project setup
- Verify clean test baseline

## Integration

**Called by:**
- **brainstorming** (Phase 4) - REQUIRED when design is approved and implementation follows
- **subagent-driven-development** - REQUIRED before executing any tasks
- **executing-plans** - REQUIRED before executing any tasks
- Any skill needing isolated workspace

**Pairs with:**
- **finishing-a-development-branch** - REQUIRED for cleanup after work complete
