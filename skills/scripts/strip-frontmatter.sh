#!/bin/bash
# strip-frontmatter.sh — Strip YAML frontmatter from a file
# Usage: strip-frontmatter.sh <file>
# Used by command stubs to load skill content without frontmatter.
awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' "$1"
