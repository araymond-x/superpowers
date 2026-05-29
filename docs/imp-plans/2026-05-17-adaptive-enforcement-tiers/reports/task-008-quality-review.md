---
task_id: 8
reviewer: superpowers-code-reviewer
review_type: quality-review
status: PASS
---

# Task 8 Quality Review — Hook Conditional Checks by Tier

**File reviewed:** `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (diff 0888cdc..87664e5)

---

## Strengths

- All 8 check modifications applied correctly. Each bool-gated check (2, 4c, 5c, 5d) reads the enforcement flag only when inside the `MANIFEST_MODE=true` branch — jq is never called without a confirmed manifest on disk.
- Legacy `else` branches are byte-for-byte identical to the original code modulo re-indentation. No opportunistic "improvements" to legacy paths.
- The 5 NEED_* variables are correctly co-located with the other MANIFEST_* vars at lines 78-82, matching the pattern established in Tasks 6-7. The initializations are required: `set -uo pipefail` is active at line 14.
- Null handling is correct. `jq -r '.enforcement.X'` returns the literal string `"null"` when the key is absent. The guards compare against `"false"` exclusively, so null, missing, and true all run the check — enforcement enabled by default, as the spec requires.
- Check 6b null guard (`[ "$CONTEXT_SUMMARY_AT" = "null" ] || [ -z "$CONTEXT_SUMMARY_AT" ]`) correctly handles both the literal string and empty string before any arithmetic comparison.
- Check 4b (structural validation) correctly nests inside the N-1 file-existence skip block: it depends on `$IMPL_LATEST`, which is only set when the file-existence branch runs.
- Check 5 drops the `break` in manifest mode (no loop); `break` is preserved in the legacy glob loop. Correct.
- The `${PLAN_SEARCH_GLOB:-manifest}` fallback at line 674 is only reachable when manifest mode set no PLAN_FILE. The diagnostic message is meaningful and doesn't trigger a `set -u` error.

---

## MINOR — Repeated bool-gate pattern is a maintainability liability

**Location:** Checks 2, 4c, 5c, 5d (lines 330-600)

**Problem:** Each bool gate is an identical 5-line block:

```bash
if [ "$MANIFEST_MODE" = true ]; then
  NEED_X=$(jq -r '.enforcement.flag_name' "$MANIFEST")
fi
if [ "$MANIFEST_MODE" = true ] && [ "$NEED_X" = "false" ]; then
  : # Skip
else
  # check body
fi
```

The null-means-enabled semantic is implicit and replicated four times. Task 9 will add more manifest reads. A helper function centralizes this:

```bash
enforcement_enabled() {
  # Returns 0 (true) when manifest mode AND enforcement flag is not "false"
  # Returns 1 (skip) when manifest mode AND flag = "false"
  # Returns 0 (true) when not in manifest mode (legacy always runs checks)
  [ "$MANIFEST_MODE" = false ] && return 0
  local val
  val=$(jq -r ".enforcement.$1" "$MANIFEST")
  [ "$val" = "false" ] && return 1 || return 0
}
```

Each gate collapses to: `if enforcement_enabled pre_execution_audit; then (check body); fi`

**Timing:** Extracting before Task 9 is cheaper than after — Task 9 adds process_requirements reads. Not a blocker for this commit.

---

## [NEEDS_CONTEXT] — Concern #1: Check 6 missing-header degrades to TOKEN_WARNING in manifest mode

**Location:** Lines 629-677

**Finding:** In manifest mode, `PLAN_FILE` is set when the manifest's designated file exists, regardless of whether `### Task N` is present. In legacy mode, the glob loop only sets `PLAN_FILE` when the task header is found — missing header → `PLAN_FILE` empty → BLOCK. In manifest mode, a file that exists but lacks the header sends the dispatch to `TOKEN_WARNING` (soft) rather than BLOCK.

**Assessment:** This is a deliberate softening, not a regression. Task 7 already validates `TASK_NUMBER` is within `[MANIFEST_TASK_START, MANIFEST_TASK_END]`, which prevents the common case where the number is entirely wrong. A manifest file that exists but has no task header is a workspace corruption scenario that is unlikely under normal operation.

**Action needed:** Task 11 should add a test for this boundary: manifest mode with a plan file missing the task header should produce TOKEN_WARNING (not BLOCK), documenting the intentional behavior difference.

---

## Assessment

**PASS**

No correctness bugs. No security issues. No legacy regressions. One minor abstraction opportunity that is easier to address before Task 9 than after. Concern #1 is a legitimate behavior difference that is intentional and bounded by Task 7's prior guard — document it in Task 11 tests.
