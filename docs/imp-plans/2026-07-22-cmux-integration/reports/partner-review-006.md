# Partner Review — Task 6 dispatch (spawn sequence, reservation ordering, exit codes, --dry-run)

**Reviewer:** controller partner (general-purpose, sonnet)
**Reviewed artifact:** proposed Task 6 core implementer prompt
**Date:** 2026-07-24

**Status:** APPROVED

## Check results

| Check | Result |
|---|---|
| Context Completeness | PASS |
| Context Accuracy | PASS (one non-blocking gap) |
| Prior Task Awareness | PASS |
| Escalation Check | PASS |
| Architectural Alignment | PASS |
| Pattern Completeness | PASS |
| Spawn-ID Deviation Verification | **CONFIRMED** |
| Scope Boundary | PASS (one non-blocking omission) |
| Write-Scope Conflict | PASS |
| Verifiability | PASS (one recommendation) |

## Detail

**Context Completeness:** Contract Constraints, Shared Constants, Pattern References, Source
Files, Subdirectory CLAUDE.md reminder, and Report Format all present.

**Context Accuracy:** Contract Constraints are a word-for-word verbatim match against
`plan.md:103-114`, checked line by line. Shared Constants complete and correct vs
`plan.md:116-119`. Task 6 description is an exact, unparaphrased copy of
`module-1-spawn-script.md:971-1122` including all four Steps and both code fences (only the
`- [ ]` checkbox markers dropped, appropriate for a dispatch). Line/variable citations
spot-checked against the live script and all correct: `SP_HOP`(:132), `MAX_HOPS`(:20),
`QUOTA_STATUS`(:158/191/196/197), `DRY_RUN`(:38), `LAUNCH_MODE`(:286/298),
`SUCCESSOR_CMD`(:331/333), `PICKUP_ARG`(:320), `now_iso()`(:64),
`print_manual_instructions()`(:66).
*Gap (non-blocking):* Pattern References omitted `tests/integration/sdd-e2e-test.sh`. Partner
judged it irrelevant to Task 6 (no e2e step) and the substituted in-file reference better
targeted. **Controller action: ADDED anyway, flagged as background-only with an explicit
"do NOT add an e2e step" instruction.**

**Prior Task Awareness:** Verified against `task-005-implementer-report.md` (DONE_WITH_CONCERNS,
4 concerns), `task-005-spec-review.md` (PASS) and `task-005-quality-review.md` (PASS +
re-review). All Task-5 concerns are mirrored into `deviations.md` rows 24–30 and 45. The two
that bind Task 6 (spawn-id placeholder; Task-4 mkdir gating, rows 13/46) are correctly carried
into the dispatch. Concerns explicitly accepted-with-no-action (telemetry not `shq`'d, `shq`
per-element spawn cost, picker-manual append-path caveat) are correctly NOT re-opened.

**Escalation Check:** No unresolved BLOCKED/NEEDS_CONTEXT across Tasks 0–5. All
DONE_WITH_CONCERNS items logged with non-Pending dispositions.

**Architectural Alignment:** The SSOT instruction ("generate SPAWN_ID once, before the compose
block… do NOT generate a second uuid") is unambiguous and closes the real defect. No shared-
infrastructure edits without co-deployment note; fix scoped to the file Task 6 already owns.

**Spawn-ID Deviation Verification — CONFIRMED.** Partner independently read the primary sources
rather than trusting the controller's claim:
- Script `:331` contains the bareword `spawn` (not a variable), compose-time-literal, landing
  in the spawn-id field of the `runtime-picker-failure` record.
- `spec.md:162` §5.4d log format: "ISO-8601 timestamp, spawn id, record type
  (`intent`|`outcome`|`runtime-picker-failure`), hop number." The second field must be the uuid.
- `module-1-spawn-script.md:1086` generates `SPAWN_ID` only after the dry-run short-circuit —
  i.e. after the compose block at `:329-334`. Verbatim compliance bakes in the literal
  permanently.
- Corroborated by `deviations.md:24,45` and both Task-5 reviews.
- The prescribed fix (generate once before `:329`, remove the Step-2 duplicate, interpolate at
  all four record sites, regenerate the worked-example comment at `:323-328`, confirm
  `--dry-run` still passes) is correct and complete.

**Scope Boundary:** The in-scope/deferred split correctly maps onto `deviations.md:46-52` and
`context-summary.md:23` — the deferred items need a new knob in the read-only
`spawn_handoff_helpers.py`; `mkdir` gating needs no helper change and is testable by this
task's own new real-spawn test.
*Omission (non-blocking):* the `_successor_cmd` `lines[0]` newline-truncation item was in
neither list — silently dropped rather than named. **Controller action: ADDED to the explicit
deferred list so nothing is dropped silently.**

**Write-Scope Conflict:** Tension confirmed real — the plan's Write-Scope table marks
`spawn_handoff_helpers.py` READ-ONLY for Task 6 while `context-summary.md:23` says Task 6 "MAY
modify" it. The dispatch resolves in favor of the approved plan's table (higher-authority
artifact) over the controller's own compressed summary, with an explicit escape valve (report
DONE_WITH_CONCERNS and name the knob; do not add it). Unambiguous and correctly prioritized.

**Verifiability:** All five listed mutations are concrete and genuinely discriminating against
the described assertions.
*Recommendation:* the required spawn-id test proves the fallback field is *a* uuid, not that it
is the *same* uuid as the intent/outcome records — a duplicate-generation-site bug (forgetting
to delete the Step-2 duplicate) would pass every listed check. Partner rated this
"recommended, not required," and suggested routing it to the reviewers as a check-item.
**Controller action: ADOPTED AS REQUIRED instead of deferred to review** — the dispatch now
mandates a correlation assertion (extract the uuid from the composed fallback tail and from the
`intent` log line, assert EQUAL) plus a discriminating mutation (re-introduce a second uuid
generation; correlation test must go RED while a shape-only check stays green).

**Findings:** None blocking.

## Controller disposition

APPROVED with three advisory items, all three folded into the dispatch before it was sent
(rather than deferred): the missing pattern reference, the unnamed deferred item, and the
uuid-correlation assertion upgraded from "recommended" to required.
