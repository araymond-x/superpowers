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

# --- Pydantic validation (Phase 1) ---
PYDANTIC_VALIDATOR="$(dirname "$0")/../../scripts/models/validators.py"
HANDOFF_DIR="$(dirname "$FILE")"
if [ -f "$PYDANTIC_VALIDATOR" ] && head -1 "$FILE" | grep -q '^---$'; then
  PYDANTIC_EXIT=0
  .venv/bin/python3 "$PYDANTIC_VALIDATOR" handoff "$HANDOFF_DIR" 2>/tmp/pydantic-handoff-err || PYDANTIC_EXIT=$?
  if [ "$PYDANTIC_EXIT" -ne 0 ]; then
    if [ "$PYDANTIC_EXIT" -eq 1 ]; then
      ERR_TEXT=$(cat /tmp/pydantic-handoff-err)
      echo "{\"status\": \"FAIL\", \"message\": \"Pydantic validation failed\", \"detail\": $(echo "$ERR_TEXT" | jq -Rs . 2>/dev/null || echo "\"$ERR_TEXT\"")}"
      exit 1
    elif [ "$PYDANTIC_EXIT" -eq 2 ]; then
      echo "  [WARN] Pydantic validator infrastructure error for $FILE" >&2
    fi
  fi
fi

FIRST_50=$(head -50 "$FILE")

# Check for contract-related headers in first 50 lines
if echo "$FIRST_50" | grep -qiE '(contract\s*(constraints|summary|facts)|field\s+types|non-negotiable|data\s+contract|schema\s+specification|type\s+definitions|field\s+conventions|data\s+types)'; then
  LINE=$(echo "$FIRST_50" | grep -niE '(contract\s*(constraints|summary|facts)|field\s+types|non-negotiable|data\s+contract|schema\s+specification|type\s+definitions|field\s+conventions|data\s+types)' | head -1)
  echo "{\"status\": \"PASS\", \"message\": \"Contract section found\", \"line\": \"$LINE\"}"
  exit 0
else
  TOTAL_LINES=$(wc -l < "$FILE")
  # Check if it exists anywhere in the file (buried)
  if grep -qiE '(contract\s*(constraints|summary|facts)|field\s+types|non-negotiable|data\s+contract|schema\s+specification|type\s+definitions|field\s+conventions|data\s+types)' "$FILE"; then
    BURIED_LINE=$(grep -niE '(contract\s*(constraints|summary|facts)|field\s+types|non-negotiable|data\s+contract|schema\s+specification|type\s+definitions|field\s+conventions|data\s+types)' "$FILE" | head -1)
    echo "{\"status\": \"FAIL\", \"message\": \"Contract section exists but is BURIED past line 50. Must be promoted to the top.\", \"found_at\": \"$BURIED_LINE\", \"total_lines\": $TOTAL_LINES}"
  else
    echo "{\"status\": \"FAIL\", \"message\": \"No contract section found anywhere in the file. A Contract Constraints section is required.\", \"total_lines\": $TOTAL_LINES}"
  fi
  exit 1
fi
