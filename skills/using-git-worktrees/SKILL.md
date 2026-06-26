---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback
---

# Using Git Worktrees

## Overview

Ensure work happens in an isolated workspace. Prefer your platform's native worktree tools. Fall back to manual git worktrees only when no native tool is available.

**Core principle:** Detect existing isolation first. Then use native tools. Then fall back to git. Never fight the harness.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Step 0: Detect Existing Isolation

**Before creating anything, check if you are already in an isolated workspace.**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**Submodule guard:** `GIT_DIR != GIT_COMMON` is also true inside git submodules. Before concluding "already in a worktree," verify you are not in a submodule:

```bash
# If this returns a path, you're in a submodule, not a worktree — treat as normal repo
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**If `GIT_DIR != GIT_COMMON` (and not a submodule):** You are already in a linked worktree. Skip to Step 3 (Project Setup). Do NOT create another worktree.

Report with branch state:
- On a branch: "Already in isolated workspace at `<path>` on branch `<name>`."
- Detached HEAD: "Already in isolated workspace at `<path>` (detached HEAD, externally managed). Branch creation needed at finish time."

**If `GIT_DIR == GIT_COMMON` (or in a submodule):** You are in a normal repo checkout.

Has the user already indicated their worktree preference in your instructions? If not, ask for consent before creating a worktree:

> "Would you like me to set up an isolated worktree? It protects your current branch from changes."

Honor any existing declared preference without asking. If the user declines consent, work in place and skip to Step 3.

## Step 1: Create Isolated Workspace

**You have two mechanisms. Try them in this order.**

### 1a. Native Worktree Tools (preferred)

The user has asked for an isolated workspace (Step 0 consent). Do you have a native worktree tool — something named like `EnterWorktree`, `WorktreeCreate`, a `/worktree` command, or a `--worktree` flag?

**Why prefer it:** a native tool switches *this* session's working directory into the worktree in place, so enforcement hooks (SDD, review gates, audit) re-root to the new directory automatically — **no new session needed.** Plain `git worktree add` alone cannot move the running session, which is why the Step 1b fallback requires a restart.

Choose by whether your instructions mandate a location or branch name:

**Case A — no mandated location/branch.** Use the native tool's create-and-enter directly (e.g. `EnterWorktree { name: <feature> }`) and skip to Step 3. It handles placement, branch creation, and cleanup.

**Case B — your instructions mandate a specific location and/or branch** (e.g. CLAUDE.md requires `.worktrees/<feature>/`, branch = feature). The native create path can't honor a custom location/branch — inside a git repo `EnterWorktree { name: x }` is fixed to `.claude/worktrees/worktree-x/` on branch `worktree-x`. If your native tool can **switch into an existing worktree by path** (e.g. `EnterWorktree { path: … }`), use the hybrid:

```bash
# 1. Verify the mandated dir is ignored (see Step 1b → Safety Verification), then:
git worktree add <mandated-location>/<feature> -b <feature>   # exact location + branch (branches from local HEAD; add a base ref for a fresh base)
# 2. Switch this session into it natively (no restart — hooks re-root):
#    EnterWorktree { path: "<mandated-location>/<feature>" }
```

The native tool accepts an existing worktree as long as it appears in `git worktree list` (verified against current `EnterWorktree` behavior — entry from the main session into a `.worktrees/`-located worktree). Switching in place re-roots the **session** CWD (verified: `pwd` and `git rev-parse --show-toplevel` — the exact call the SDD hooks make — resolve to the worktree). PreToolUse hooks are spawned with the current session CWD (same as the Bash tool), so they bind to the worktree **without a new session.** Skip to Step 3.

Cleanup is manual for a path-entered worktree: the native tool tracks the session switch but won't auto-remove it on exit. Use `git worktree remove` (or your finishing-a-development-branch flow) when done.

If your native tool cannot switch into an existing worktree by path, fall through to Step 1b (git fallback + restart). Only proceed to Step 1b if you have no native worktree tool available.

### 1b. Git Worktree Fallback

**Only use this if Step 1a does not apply** — you have no native worktree tool available. Create a worktree manually using git.

#### Directory Selection

Follow this priority order. Explicit user preference always beats observed filesystem state.

1. **Check your instructions for a declared worktree directory preference.** If the user has already specified one, use it without asking.

2. **Check for an existing project-local worktree directory:**
   ```bash
   ls -d .worktrees 2>/dev/null     # Preferred (hidden)
   ls -d worktrees 2>/dev/null      # Alternative
   ```
   If found, use it. If both exist, `.worktrees` wins.

3. **If there is no other guidance available**, default to `.worktrees/` at the project root.

#### Safety Verification (project-local directories only)

**MUST verify directory is ignored before creating worktree:**

```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**If NOT ignored:** Add to .gitignore, commit the change, then proceed.

**Why critical:** Prevents accidentally committing worktree contents to repository.

#### Create the Worktree

```bash
# Determine path based on chosen location
path="$LOCATION/$BRANCH_NAME"

git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

**Sandbox fallback:** If `git worktree add` fails with a permission error (sandbox denial), tell the user the sandbox blocked worktree creation and you're working in the current directory instead. Then run setup and baseline tests in place.

## Step 3: Project Setup

Auto-detect and run appropriate setup:

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

## Step 4: Verify Clean Baseline

Run tests to ensure workspace starts clean:

```bash
# Use project-appropriate command
npm test / cargo test / pytest / go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### Report

**If you switched in place via a native tool (Step 1a, Case A or B):** the session is already inside the worktree and hooks have re-rooted — no new session needed. Report and continue working here:

```
 WORKTREE READY

Worktree: <full-path>
Branch:   <branch-name>
Tests:    passing (<N> tests, 0 failures)

Session is already working inside the worktree — continue here.
```

**If you used the pure-git fallback (Step 1b, no native tool):** the running session cannot be moved into the worktree, so enforcement hooks still bind to the launch directory. A new session is required:

```
 WORKTREE READY — NEW SESSION REQUIRED

Worktree: <full-path>
Branch:   <branch-name>
Tests:    passing (<N> tests, 0 failures)

Claude Code hooks (SDD enforcement, review gates, audit gates) receive their
working directory from session start — `! cd` does NOT change hook CWD. To
ensure all enforcement hooks work correctly, you must start a new Claude Code
session from inside the worktree:

  cd <full-path> && claude-picker   # stamps project/branch (=worktree) into telemetry

Do not dispatch implementation tasks or invoke SDD from this session.
```

**STOP after presenting this output** (git-fallback path only). The user must open a new session from inside the worktree. Do not proceed with implementation in the current session.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Already in linked worktree | Skip creation (Step 0) |
| In a submodule | Treat as normal repo (Step 0 guard) |
| Native tool, no mandated location | Create-and-enter natively (Step 1a Case A) |
| Native tool + mandated location/branch | Hybrid: `git worktree add … -b <feature>` then native switch-by-path — no restart (Step 1a Case B) |
| Native tool can't switch-by-path, or no native tool | Git worktree fallback + restart (Step 1b) |
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check instruction file, then default `.worktrees/` |
| Directory not ignored | Add to .gitignore + commit |
| Permission error on create | Sandbox fallback, work in place |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |

## Common Mistakes

### Fighting the harness

- **Problem:** Using `git worktree add` *alone* when the platform already provides isolation, leaving the session and harness unaware of the worktree
- **Fix:** Step 0 detects existing isolation. Step 1a defers to native tools. (The Case B hybrid is not this — it hands the worktree to the native tool via `EnterWorktree { path: … }`, so the session switches in and the harness stays in sync.)

### Skipping detection

- **Problem:** Creating a nested worktree inside an existing one
- **Fix:** Always run Step 0 before creating anything

### Skipping ignore verification

- **Problem:** Worktree contents get tracked, pollute git status
- **Fix:** Always use `git check-ignore` before creating project-local worktree

### Assuming directory location

- **Problem:** Creates inconsistency, violates project conventions
- **Fix:** Follow priority: existing > instruction file > default

### Proceeding with failing tests

- **Problem:** Can't distinguish new bugs from pre-existing issues
- **Fix:** Report failures, get explicit permission to proceed

## Red Flags

**Never:**
- Create a worktree when Step 0 detects existing isolation
- Use plain `git worktree add` *instead of* a native switch when one is available (it strands the running session outside the worktree). Exception: the Step 1a Case B hybrid — `git worktree add` to honor a mandated path, immediately followed by the native switch-into-existing (e.g. `EnterWorktree { path: … }`) — is correct.
- Skip Step 1a by jumping straight to Step 1b's git commands
- Create worktree without verifying it's ignored (project-local)
- Skip baseline test verification
- Proceed with failing tests without asking

**Always:**
- Run Step 0 detection first
- Prefer native tools over git fallback
- Follow directory priority: existing > instruction file > default
- Verify directory is ignored for project-local
- Auto-detect and run project setup
- Verify clean test baseline
