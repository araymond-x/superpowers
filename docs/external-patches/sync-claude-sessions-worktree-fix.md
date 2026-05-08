# sync-claude-sessions: Worktree Project Name Fix

**Plugin**: `personal-os-skills/sync-claude-sessions-skill`
**File**: `scripts/claude-sessions` (function `_detect_project_name` near line 51)
**Date**: 2026-05-07
**Re-apply after**: Any plugin update that overwrites the cache

## Problem

`_detect_project_name()` uses `Path.cwd().name`, which returns the worktree directory name (e.g., `v1.4.2`) instead of the actual project name (e.g., `agent-slack-bridge`). This causes sessions to sync to `Sessions/v1.4.2/` — a new iCloud directory that macOS TCC blocks.

## Original Code

```python
def _detect_project_name() -> str:
    """Derive project name from CWD for subfolder organization."""
    return Path.cwd().name or "unknown"
```

## Patched Code

```python
def _detect_project_name() -> str:
    """Derive project name from CWD for subfolder organization.

    Uses git-common-dir to resolve worktrees to the main repo name.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=3,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).parent.name or Path.cwd().name or "unknown"
    except (subprocess.TimeoutExpired, OSError):
        pass
    return Path.cwd().name or "unknown"
```

## Notes

- `subprocess` is already imported in the file
- `git rev-parse --git-common-dir` returns the shared `.git` dir of the main repo even when run from a worktree
- Falls back to `Path.cwd().name` for non-git directories
