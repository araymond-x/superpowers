#!/usr/bin/env bash
# plan-validation-gate-hook.sh — Block execution skills without plan validation
#
# PreToolUse hook on the Skill tool. Fires when subagent-driven-development
# or executing-plans is invoked. Blocks if:
#   1. Scoped plan files exist but validate-plan.py reports FAIL on any of them
#   2. No plan-review-report.md exists (>50 bytes)
#
# Plan file scoping (two layers):
#   Primary: docs/imp-plans/plan-manifest.txt — explicit list written by
#            the writing-plans skill after validation. One path per line.
#   Fallback: git diff against base branch — finds plan files changed on
#             the current branch. Handles plans written before manifests existed.
#   If neither yields files, the hook allows (no plans to validate).
#
# Exit codes:
#   0 — Allow (no plans, or validation passed)
#   2 — Block (validation failed or review report missing)

set -o pipefail

MIN_REPORT_BYTES=50

SUPERPOWERS_ROOT="${SUPERPOWERS_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

if [ -f "$SUPERPOWERS_ROOT/.venv/bin/python3" ]; then
  PYTHON="$SUPERPOWERS_ROOT/.venv/bin/python3"
else
  PYTHON="python3"
fi

VALIDATE_PLAN_SCRIPT="$SUPERPOWERS_ROOT/skills/subagent-driven-development/scripts/validate-plan.py"

INPUT=$(cat)

# Check for jq
if ! command -v jq &>/dev/null; then
  echo "WARNING: jq not found — plan-validation-gate-hook.sh cannot enforce. Install jq." >&2
  exit 0
fi

# Extract skill name from tool_input
SKILL=$(echo "$INPUT" | jq -r '.tool_input.skill // (.tool_input.args // "") | split(" ")[0]' 2>/dev/null || true)

# Only gate on execution skills
case "$SKILL" in
  *subagent-driven-development*|*executing-plans*) ;;
  *) exit 0 ;;
esac

# Get CWD from hook payload
CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || true)
if [ -z "$CWD" ] || [ ! -d "$CWD" ]; then
  exit 0
fi

cd "$CWD" || exit 0

# ─── Resolve active feature directory ─────────────────────────────────────
FEAT=""
if [ -f ".active-feature" ]; then
  FEAT=$(cat .active-feature)
fi

# Gate: .active-feature must exist for execution skills
if [ -z "$FEAT" ]; then
  echo "BLOCKED: No .active-feature file found. Establish a feature name by invoking superpowers:brainstorming or superpowers:writing-plans first. The feature name determines the directory structure for all execution artifacts." >&2
  exit 2
fi

# ---- Scope plan files --------------------------------------------------------

PLAN_FILES=()
SCOPE_METHOD=""

# Primary: read plan-manifest.txt — use $FEAT for direct discovery
MANIFEST=""
if [ -n "$FEAT" ]; then
  if [ -f "$FEAT/plan-manifest.txt" ]; then
    MANIFEST="$FEAT/plan-manifest.txt"
  fi
else
  # Legacy fallback: search standard locations
  for dir in docs/imp-plans docs/plans; do
    if [ -f "$dir/plan-manifest.txt" ]; then
      MANIFEST="$dir/plan-manifest.txt"
      break
    fi
    if [ -d "$dir" ]; then
      FOUND=$(find "$dir" -maxdepth 2 -name "plan-manifest.txt" -type f 2>/dev/null | head -1)
      if [ -n "$FOUND" ]; then
        MANIFEST="$FOUND"
        break
      fi
    fi
  done
fi

if [ -n "$MANIFEST" ]; then
  SCOPE_METHOD="manifest"
  while IFS= read -r line; do
    # Skip empty lines and comments
    line=$(echo "$line" | sed 's/#.*//' | xargs)
    [ -z "$line" ] && continue
    # Resolve relative paths from CWD
    if [ -f "$line" ]; then
      PLAN_FILES+=("$line")
    elif [ -f "$CWD/$line" ]; then
      PLAN_FILES+=("$CWD/$line")
    fi
  done < "$MANIFEST"
else
  # Fallback: git diff against base branch
  SCOPE_METHOD="git-diff"
  BASE_BRANCH=""
  for candidate in main master; do
    if git rev-parse --verify "$candidate" &>/dev/null; then
      BASE_BRANCH="$candidate"
      break
    fi
  done

  if [ -n "$BASE_BRANCH" ]; then
    MERGE_BASE=$(git merge-base HEAD "$BASE_BRANCH" 2>/dev/null || echo "")
    if [ -n "$MERGE_BASE" ]; then
      # Files changed on current branch (committed + uncommitted)
      while IFS= read -r f; do
        [ -f "$f" ] && PLAN_FILES+=("$f")
      done < <(
        {
          git diff --name-only "$MERGE_BASE" -- docs/imp-plans/ docs/plans/ 2>/dev/null
          git diff --name-only -- docs/imp-plans/ docs/plans/ 2>/dev/null
          git ls-files --others --exclude-standard -- docs/imp-plans/ docs/plans/ 2>/dev/null
        } | sort -u | grep '\.md$'
      )
    fi
  fi

  # Filter out non-plan files from git results
  FILTERED=()
  for pf in "${PLAN_FILES[@]}"; do
    BASENAME=$(basename "$pf")
    if echo "$BASENAME" | grep -qiE '(review-report|validation-report|context-summary|plan-manifest)'; then
      continue
    fi
    FILTERED+=("$pf")
  done
  PLAN_FILES=("${FILTERED[@]}")
fi

# No plan files scoped — nothing to validate, allow
if [ ${#PLAN_FILES[@]} -eq 0 ]; then
  exit 0
fi

# ---- Gate 1: Run validate-plan.py on each scoped plan file ------------------

ERRORS=()

if [ -f "$VALIDATE_PLAN_SCRIPT" ]; then
  for pf in "${PLAN_FILES[@]}"; do
    BASENAME=$(basename "$pf")

    # Run validator
    OUTPUT=$(python3 "$VALIDATE_PLAN_SCRIPT" --plan-file "$pf" 2>/dev/null || echo "")
    if [ -z "$OUTPUT" ]; then
      continue
    fi

    STATUS=$(echo "$OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")

    if [ "$STATUS" = "FAIL" ]; then
      BLOCKERS=$(echo "$OUTPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for b in data.get('blockers', []):
    print(f'  - {b}')
" 2>/dev/null || echo "  - (could not parse blockers)")
      ERRORS+=("BLOCKED: validate-plan.py FAIL on $BASENAME:\n$BLOCKERS\nFix these issues before proceeding to execution.")
    fi
  done
else
  echo "WARNING: validate-plan.py not found at $VALIDATE_PLAN_SCRIPT — structural validation skipped." >&2
fi

# ---- Gate 1b: Pydantic validation (Phase 1) ---------------------------------

PYDANTIC_VALIDATOR="$SUPERPOWERS_ROOT/skills/scripts/models/validators.py"
if [ -f "$PYDANTIC_VALIDATOR" ]; then
  for pf in "${PLAN_FILES[@]}"; do
    # Only validate files with YAML frontmatter
    if head -1 "$pf" | grep -q '^---$'; then
      $PYTHON "$PYDANTIC_VALIDATOR" plan "$pf" 2>/tmp/pydantic-validator-err
      PYDANTIC_EXIT=$?
      if [ "$PYDANTIC_EXIT" -ne 0 ]; then
        if [ "$PYDANTIC_EXIT" -eq 1 ]; then
          ERRORS+=("Pydantic validation failed for $pf")
          PYDANTIC_ERR=$(jq -Rs . < /tmp/pydantic-validator-err 2>/dev/null || cat /tmp/pydantic-validator-err)
          echo -e "  [FAIL] Pydantic: $pf" >&2
        elif [ "$PYDANTIC_EXIT" -eq 2 ]; then
          echo -e "  [WARN] Pydantic validator infrastructure error for $pf" >&2
        fi
      fi
    fi
  done
fi

# ---- Gate 2: Check for plan-review-report.md --------------------------------
# Search strategy: first check $FEAT directory directly, then directories
# containing scoped plan files, then fall back to top-level docs/imp-plans/ and docs/plans/.

REVIEW_REPORT=""
if [ -n "$FEAT" ]; then
  if [ -f "$FEAT/plan-review-report.md" ]; then
    REVIEW_REPORT="$FEAT/plan-review-report.md"
  fi
fi

if [ -z "$REVIEW_REPORT" ]; then
# Build list of directories to search from the scoped plan files
SEARCH_DIRS=()
for pf in "${PLAN_FILES[@]}"; do
  PF_DIR=$(dirname "$pf")
  # Deduplicate
  ALREADY=false
  for sd in "${SEARCH_DIRS[@]}"; do
    if [ "$sd" = "$PF_DIR" ]; then
      ALREADY=true
      break
    fi
  done
  if [ "$ALREADY" = false ]; then
    SEARCH_DIRS+=("$PF_DIR")
  fi
done

# Also check top-level plan directories as fallback
for dir in docs/imp-plans docs/plans; do
  if [ -d "$dir" ]; then
    ALREADY=false
    for sd in "${SEARCH_DIRS[@]}"; do
      if [ "$sd" = "$dir" ]; then
        ALREADY=true
        break
      fi
    done
    if [ "$ALREADY" = false ]; then
      SEARCH_DIRS+=("$dir")
    fi
  fi
done

for dir in "${SEARCH_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    FOUND=$(find "$dir" -maxdepth 1 -name "*plan-review-report*" -type f 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
      REVIEW_REPORT="$FOUND"
      break
    fi
  fi
done
fi  # end if [ -z "$REVIEW_REPORT" ] (fallback search)

if [ -z "$REVIEW_REPORT" ]; then
  ERRORS+=("BLOCKED: No plan-review-report.md found near scoped plan files or in docs/imp-plans/. The writing-plans skill requires dispatching the plan-document-reviewer and saving its output before execution. Run the Plan Review Loop (checklist steps 8-11) first.")
elif [ -f "$REVIEW_REPORT" ]; then
  REPORT_SIZE=$(wc -c < "$REVIEW_REPORT" 2>/dev/null | tr -d ' ')
  if [ "$REPORT_SIZE" -lt "$MIN_REPORT_BYTES" ] 2>/dev/null; then
    ERRORS+=("BLOCKED: plan-review-report ($REVIEW_REPORT) is only $REPORT_SIZE bytes — likely a placeholder. Save the complete reviewer output (minimum $MIN_REPORT_BYTES bytes).")
  fi
fi

# ---- Report results ----------------------------------------------------------

if [ ${#ERRORS[@]} -gt 0 ]; then
  ERROR_MSG=""
  for err in "${ERRORS[@]}"; do
    ERROR_MSG="${ERROR_MSG}${err}\n\n"
  done
  echo -e "$ERROR_MSG" >&2
  exit 2
fi

# ---- All checks passed — inject reminder and allow --------------------------

CONTEXT="PLAN VALIDATION GATE ($SCOPE_METHOD): ${#PLAN_FILES[@]} plan file(s) validated and review report confirmed. Proceeding to execution. The plan is the source of truth — implement against it, not your assumptions."

ENCODED=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$CONTEXT" 2>/dev/null || echo "\"$CONTEXT\"")

cat << HOOKJSON
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": $ENCODED
  }
}
HOOKJSON

exit 0
