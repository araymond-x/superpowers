#!/usr/bin/env bash
# check-safe-branch.sh — Block if on main/master branch
#
# Exit codes:
#   0 — Safe (on feature branch)
#   2 — Blocked (on main/master)
#   1 — Error (can't determine branch)

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)

if [ -z "$CURRENT_BRANCH" ]; then
  echo '{"status": "ERROR", "message": "Could not determine current branch"}' >&2
  exit 1
fi

if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "BLOCKED: Currently on '$CURRENT_BRANCH' branch. Switch to a feature branch or create a worktree before implementing." >&2
  exit 2
fi

echo "{\"status\": \"OK\", \"branch\": \"$CURRENT_BRANCH\"}"
exit 0
