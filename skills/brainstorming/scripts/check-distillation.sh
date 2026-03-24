#!/usr/bin/env bash
# check-distillation.sh — Verify distilled spec has no exploration artifacts
# Usage: bash check-distillation.sh /path/to/distilled-spec.md
# Exit: 0=clean, 1=artifacts found, 2=usage error

set -euo pipefail

if [ $# -lt 1 ] || [ ! -f "$1" ]; then
  echo '{"status": "ERROR", "message": "Usage: check-distillation.sh /path/to/distilled-spec.md"}' >&2
  exit 2
fi

FILE="$1"
ARTIFACTS=()

# Check for exploration artifact patterns
while IFS= read -r line; do
  ARTIFACTS+=("$line")
done < <(grep -niE '(options?\s+considered|rationale|we\s+considered|earlier\s+design|prior\s+art|rejected\s+alternative|we\s+chose.*instead|we\s+decided\s+against)' "$FILE" 2>/dev/null || true)

LINE_COUNT=$(wc -l < "$FILE")
WORD_COUNT=$(wc -w < "$FILE")

if [ ${#ARTIFACTS[@]} -eq 0 ]; then
  echo "{\"status\": \"PASS\", \"message\": \"No exploration artifacts found\", \"lines\": $LINE_COUNT, \"words\": $WORD_COUNT}"
  exit 0
else
  echo "{\"status\": \"FAIL\", \"artifact_count\": ${#ARTIFACTS[@]}, \"lines\": $LINE_COUNT, \"words\": $WORD_COUNT, \"artifacts\": ["
  for i in "${!ARTIFACTS[@]}"; do
    ESCAPED=$(echo "${ARTIFACTS[$i]}" | sed 's/"/\\"/g')
    if [ $i -lt $((${#ARTIFACTS[@]} - 1)) ]; then
      echo "    \"$ESCAPED\","
    else
      echo "    \"$ESCAPED\""
    fi
  done
  echo "]}"
  exit 1
fi
