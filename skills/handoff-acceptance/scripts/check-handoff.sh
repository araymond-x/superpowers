#!/usr/bin/env bash
# check-handoff.sh — Verify handoff README has contract summary in first 50 lines
# Usage: bash check-handoff.sh /path/to/handoff/README.md
# Exit: 0=found, 1=not found, 2=usage error

set -euo pipefail

if [ $# -lt 1 ] || [ ! -f "$1" ]; then
  echo '{"status": "ERROR", "message": "Usage: check-handoff.sh /path/to/README.md"}' >&2
  exit 2
fi

FILE="$1"
FIRST_50=$(head -50 "$FILE")

# Check for contract-related headers in first 50 lines
if echo "$FIRST_50" | grep -qiE '(contract\s*(constraints|summary|facts)|field\s+types|non-negotiable)'; then
  LINE=$(echo "$FIRST_50" | grep -niE '(contract\s*(constraints|summary|facts)|field\s+types|non-negotiable)' | head -1)
  echo "{\"status\": \"PASS\", \"message\": \"Contract section found\", \"line\": \"$LINE\"}"
  exit 0
else
  TOTAL_LINES=$(wc -l < "$FILE")
  # Check if it exists anywhere in the file (buried)
  if grep -qiE '(contract\s*(constraints|summary|facts)|field\s+types)' "$FILE"; then
    BURIED_LINE=$(grep -niE '(contract\s*(constraints|summary|facts)|field\s+types)' "$FILE" | head -1)
    echo "{\"status\": \"FAIL\", \"message\": \"Contract section exists but is BURIED past line 50. Must be promoted to the top.\", \"found_at\": \"$BURIED_LINE\", \"total_lines\": $TOTAL_LINES}"
  else
    echo "{\"status\": \"FAIL\", \"message\": \"No contract section found anywhere in the file. A Contract Constraints section is required.\", \"total_lines\": $TOTAL_LINES}"
  fi
  exit 1
fi
