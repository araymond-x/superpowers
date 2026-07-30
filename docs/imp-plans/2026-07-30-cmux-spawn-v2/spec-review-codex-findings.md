<!--
PROVENANCE — captured from the review bundle so the verbatim record survives pruning;
everything below the `---` rule is the reviewer's original document, unmodified.

  Reviewer : Codex (codex-cli 0.146.0), read-only round trip on cmux surface:71,
             dispatched 2026-07-30 by the brainstorming session for cmux-spawn-v2.
  Found at : ~/.claude-codex-handoff/bundles/2026-07-30T18-21-11Z-superpowers/findings.md
  Reviewed : spec.md + spec-distilled.md at commit eed17e1.
  Disposition: ALL findings verified valid and remediated in 9b80490
             (see that commit message for the per-finding mapping).
-->

---
# cmux-spawn-v2 planning-readiness review

Verdict: **request changes**.

## Blocker

### `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md:79-80, 115-119, 216-219`; `spec-distilled.md:26, 40, 62, 84`

**Evidence:** The spec defines the wait-for token as the sole readiness signal and says screen reading is never a success signal. Yet after wait-for times out, a banner or dialog observed by read-screen produces exit 0 (`handshake=late|dialog`). Exit 0 remains the spawned rung, so a controller following the documented ladder stops the current session without receiving a handshake. The scrape therefore controls the success-class exit status.

**Suggested fix:** Make a successful wait-for the only exit-0 / `handshake=ok` path. Treat every token timeout as exit 3, using read-screen only to enrich manual instructions (`diagnosis=banner` or `diagnosis=trust-dialog`). If late continuation is wanted, use a second bounded wait-for whose result, not screen output, selects exit 0. Test that a banner with no token is non-success.

## Major

### `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md:83-86, 154-163`; `spec-distilled.md:29-34, 92-93`

**Evidence:** `tasks_done` is the count of implementer-report files in live and archived directories. A filename is not proof of completed work: a report can be BLOCKED or incomplete, and re-runs can yield multiple matching files for one task. A no-progress chain can thus appear to advance and bypass the two-zero-progress stop.

**Suggested fix:** Define a completed-task set: unique task IDs across live/archive, counted only when the report validates and records the specified completed status; state verification-task treatment. Persist this value at reservation. Test blocked/incomplete, duplicate, archived, and verification reports.

### `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md:120-123, 125-127`; `spec-distilled.md:84`

**Evidence:** The surface route explicitly waits for a token, but the workspace fallback is only described as `workspace create`, then manual. It does not state that fallback gets the same inline environment, handshake, timeout ladder, post-spawn setup, and outcome fields. Reusing N43(D)'s current workspace core would return exit 0 immediately after creation, bypassing the new closed-loop contract.

**Suggested fix:** Specify one shared launch-and-handshake wrapper for both topologies. Permit workspace fallback only before the surface command is accepted; never spawn a second successor after a send succeeds but the token times out. Add an E2E fallback success and timeout case.

### `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md:84, 154-158`; `spec-distilled.md:31-33, 92-93`

**Evidence:** The formula uses `total_tasks`, but pre-v2 recovery says to derive from manifest task ranges. Existing manifests expose `total_tasks`, active `task_range`, and potentially module task IDs, which can yield different ceilings. The first-hop and missing/malformed-prior-outcome cases are also unspecified.

**Suggested fix:** Pin precedence: validated `total_tasks`, otherwise unique module task IDs, otherwise inclusive active range; reject invalid/zero totals. Define the first-hop baseline as zero and define missing/malformed outcome handling. Add legacy-shape and first-hop tests.

### `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md:89, 104-107, 128-132`; `spec-distilled.md:26, 71, 83, 131`

**Evidence:** `off` is exit 3/manual fallback, while `ask` says it refuses without `--user-approved` but assigns neither exit code nor controller action. This leaves an observable 0/3/1 ambiguity and whether the retry consumes a hop unclear.

**Suggested fix:** Pin `ask` without approval to one rung, log `reason=policy-ask`, state retryability, and require it before reservation. Test exit code, log, hop counter, and post-consent retry.

## Minor

### `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md:228-240`; `spec-distilled.md:117-119`

**Evidence:** cmux 0.64.20 help supports the proposed verbs and their stated flags. But per-verb OK parsing does not require negative/malformed-response fixtures for `new-surface`, `rename-tab`, `send`, and `send-key`.

**Suggested fix:** Require an exit-status plus verb-specific response predicate for each state-changing verb. Keep the `new-surface` ref authoritative; never reuse rename-tab or close-surface output as a target ref.

### `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec.md:193-203, 239-240`; `spec-distilled.md:42-43, 104-105`

**Evidence:** The three-hook baseline list is complete: check-hooks.sh covers session-start, pre-dispatch, and stop (plus unchanged hooks). The interference audit is also complete for the new handoff artifacts: Check 3b is the needed allowlist change, task/archive globs do not match, and the byte-proxy inclusion is intentional.

**Suggested fix:** Keep this invariant explicit and test that handoff-mechanics.md contributes to byte-proxy estimation without matching task-report or stale-artifact scans.
