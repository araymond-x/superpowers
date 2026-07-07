#!/usr/bin/env bash
# check-distillation.sh — Verify distilled spec has no exploration artifacts
#   and (when the full spec is supplied) that the source's scope fence survived.
# Usage: bash check-distillation.sh /path/to/distilled-spec.md [/path/to/full-spec.md]
#   With the optional 2nd arg: if the full spec declares an out-of-scope/non-goals
#   heading, the distilled spec must carry a counterpart heading or the check FAILs.
# Exit: 0=clean, 1=artifacts found or fence dropped, 2=usage error

set -euo pipefail

if [ $# -lt 1 ] || [ ! -f "$1" ]; then
  echo '{"status": "ERROR", "message": "Usage: check-distillation.sh /path/to/distilled-spec.md [/path/to/full-spec.md]"}' >&2
  exit 2
fi

FILE="$1"
FULL_SPEC="${2:-}"
if [ -n "$FULL_SPEC" ] && [ ! -f "$FULL_SPEC" ]; then
  echo '{"status": "ERROR", "message": "Usage: check-distillation.sh /path/to/distilled-spec.md [/path/to/full-spec.md] — full-spec path not found"}' >&2
  exit 2
fi

ARTIFACTS=()

# Check for exploration artifact patterns
while IFS= read -r line; do
  ARTIFACTS+=("$line")
# Exclude blockquote lines (> ...) which contain template boilerplate like "For full rationale, see source"
done < <(grep -niE '(options?\s+considered|rationale|we\s+considered|earlier\s+design|prior\s+art|rejected\s+alternative|we\s+chose.*instead|we\s+decided\s+against)' "$FILE" 2>/dev/null | grep -v '^\s*[0-9]*:>' || true)

# Scope fence preservation: out-of-scope lists are negative contract material.
# A heading-level fence in the full spec must have a counterpart heading in the
# distilled spec. No pipes into grep -q (SIGPIPE fail-open under pipefail).
FENCE_HEADING='^#{1,6}[[:space:]].*\b(out[- ]of[- ]scope|non-goals|do[- ]not[- ]build)\b'
FENCE_STATUS="NOT_CHECKED"
if [ -n "$FULL_SPEC" ]; then
  if grep -qiE "$FENCE_HEADING" "$FULL_SPEC"; then
    if grep -qiE "$FENCE_HEADING" "$FILE"; then
      FENCE_STATUS="PRESENT"
    else
      FENCE_STATUS="MISSING"
    fi
  else
    FENCE_STATUS="NOT_REQUIRED"
  fi
fi

LINE_COUNT=$(wc -l < "$FILE")
WORD_COUNT=$(wc -w < "$FILE")

if [ ${#ARTIFACTS[@]} -eq 0 ] && [ "$FENCE_STATUS" != "MISSING" ]; then
  echo "{\"status\": \"PASS\", \"message\": \"No exploration artifacts found\", \"fence\": \"$FENCE_STATUS\", \"lines\": $LINE_COUNT, \"words\": $WORD_COUNT}"
  exit 0
else
  echo "{\"status\": \"FAIL\", \"artifact_count\": ${#ARTIFACTS[@]}, \"fence\": \"$FENCE_STATUS\", \"lines\": $LINE_COUNT, \"words\": $WORD_COUNT, \"artifacts\": ["
  for i in "${!ARTIFACTS[@]}"; do
    ESCAPED=$(echo "${ARTIFACTS[$i]}" | sed 's/"/\\"/g')
    if [ $i -lt $((${#ARTIFACTS[@]} - 1)) ]; then
      echo "    \"$ESCAPED\","
    else
      echo "    \"$ESCAPED\""
    fi
  done
  echo "]"
  if [ "$FENCE_STATUS" = "MISSING" ]; then
    echo ", \"fence_detail\": \"Source spec declares an out-of-scope/non-goals section but the distilled spec has no counterpart heading. Scope fences are negative contract material — carry them (see brainstorming SKILL.md, Distillation Rules).\""
  fi
  echo "}"
  exit 1
fi
