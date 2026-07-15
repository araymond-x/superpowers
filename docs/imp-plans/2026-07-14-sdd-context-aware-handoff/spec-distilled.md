# SDD Context-Aware Auto-Handoff — Distilled Implementation Spec

> **Source:** `spec.md` (v1, 11 decisions, spec-review approved)
> **Distilled:** 2026-07-14
> **For:** Plan writer and implementation agents ONLY. For full rationale, see source.
> **Archetype:** Extension of `sdd-pre-dispatch-hook.sh` + SDD skill; reuses N39 handoff + `session-recovery.md` resume.

## Out of scope — do not build

- **Component B** — cross-session honesty aggregation → own spec.
- **Component C** — pace-aware pause/resume around 5h/weekly rate-limit windows via `cupace` → own spec (different sensor; remedy is sleep-until-reset, not handoff).
- **Component D** — cmux auto-spawn of the next session → own spec (unattended self-spawn has runaway + quota-burn risk).
- **B10** — pressure-conditional context-summary (hook Check 6b) → fast-follow on this sensor, after it is proven live.
- **Window auto-detection / a `ctxload` tool** → optional standalone diagnostic; never a dependency of this hook.
- **Context handoff for `writing-plans` / `brainstorming`** → later (single long sessions, few clean pause points).
- **Percentage-of-window triggering** → rejected (window unreachable from a hook).

## Contract Facts

- **Metric — absolute token count.** `T = input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens`, taken from the most recent assistant message carrying a `usage` block in the controller's transcript. No window, no percentage.
- **Thresholds (absolute tokens):** `SOFT = 300000`, `HARD = 400000`. Action: `T < SOFT` → allow; `SOFT ≤ T < HARD` → allow + nudge; `T ≥ HARD` → block (`exit 2`).
- **Env vars:** `SUPERPOWERS_CTX_SOFT_TOKENS` (default `300000`), `SUPERPOWERS_CTX_HARD_TOKENS` (default `400000`), `SUPERPOWERS_CTX_FALLBACK_STREAK` (default `3`), `SUPERPOWERS_CTX_HANDOFF_BYPASS` (unset → gate active; set → gate skipped with stderr warning). Non-numeric override, or `HARD ≤ SOFT`, → fall back to defaults with a stderr warning.
- **Window policy:** defaults are 1M-tuned; the hard guarantee applies only to sessions that reach `HARD` before auto-compaction (1M). On a 200k session `HARD` is unreachable (auto-compaction backstops; set a lower per-session override). Auto-compaction shrinks the latest `usage` reading → the tier resets and the gate won't fire post-compaction (must be tested).
- **Transcript source:** hook reads `.transcript_path` from its PreToolUse stdin payload and passes `--transcript <path>` to the probe. If `transcript_path` is empty, pass `--session-id "$SESSION_ID"`. **`.session_id` must be extracted right after the `INPUT` parse, before classification** — today it is set only inside the reviewer branch (~L200), so implementer/fix/partner/passthrough would otherwise hit an empty id. Never uses `CLAUDE_CODE_SESSION_ID`. All path resolution lives in the probe.
- **Nudge/block predicate:** implementer new-task path only — `IS_IMPLEMENTER && ! MARKED_FIX`. Reviewer / fix / re-review / passthrough dispatches are never nudged or blocked. A `task_type: verification` task IS an implementer dispatch → eligible for nudge/block (not exempt).
- **Observation log:** one line per dispatch (all types) to `reports/context-observations.log` — NOT `.dispatch-log`. Format: `<ISO-8601> task=<N> type=<implementer|spec-review|quality-review|partner|other> tokens=<T> source=<probe|byte-proxy|bypass> tier=<below|soft|hard> action=<allow|nudge|block|fallback>`. Append is best-effort (failure → stderr, never breaks the dispatch); threshold tuning uses only `source=probe` rows.
- **Probe:** stdlib-only Python (no pydantic/PyYAML — may run under bare `python3`). Accepts `--transcript <path>`, `--session-id <id>`, `--json`. Exits non-zero (with diagnostic) when the session id is unset, no transcript exists, or no completed turn carries a `usage` block.
- **Fallback:** probe non-zero exit → byte-proxy **advisory** (retain Check 7's byte-sum; warn if over its threshold; log `source=byte-proxy action=fallback`; never crash). This is NOT a hard ceiling (the byte-proxy undercounts + only warns). `SUPERPOWERS_CTX_FALLBACK_STREAK` (default 3) consecutive fallbacks escalate to a block + diagnostic so a broken gate cannot stay silently inert.
- **Handoff (reuse):** on hard block, controller commits → invokes the `handoff` skill to build a bundle with entry skill `superpowers:subagent-driven-development` (the N39 flow) → STOPs. Fresh session `/pickup` resumes mid-plan per `references/session-recovery.md` (plan checkboxes + `deviations.md` + `reports/` → first unchecked task).
- **Guarantee boundary:** the block guarantees the next task will not dispatch; it does not by itself guarantee a clean handoff (that depends on the controller following the taught protocol).
- **Self-hosting hazard (H1):** the live hook resolves to this main checkout via settings.json absolute paths, so editing it affects the running session. Implement in a worktree; re-capture the hook baseline (`check-hooks.sh --capture`) in the same change; the e2e tests *this checkout*, not the live hook.

## Open Decisions

| # | Decision | Options | Resolution required by |
|---|----------|---------|------------------------|
| 1 | Exact variable names for the `IS_IMPLEMENTER && ! MARKED_FIX` predicate | (align to the hook's existing dispatch-marker classification) | Plan (low-risk; predicate itself confirmed) |
| 2 | Fixture transcripts at known token totals (below / soft / hard) for hook + probe tests | (author small fixtures; supply via stdin `.transcript_path`) | Plan / implementation |

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Enforcement mechanism | Deterministic hook enforces; SKILL text teaches the response |
| 2 | Trigger metric | Absolute token count |
| 3 | Sensor source | Vendored `context-probe.py` (self-contained, testable) |
| 4 | Enforcement posture | Two-tier nudge + block |
| 5 | Thresholds | Soft 300k / hard 400k, env-overridable, log-tuned |
| 6 | Nudge/block scope | Implementer new-task path only; observation log on all dispatches |
| 7 | Handoff + resume | Reuse N39 bundle + `session-recovery.md` |
| 8 | Sensor failure | Byte-proxy advisory + `K`-consecutive-fallback escalation to block (not fail-open) |
| 9 | Observation log location | Separate `reports/context-observations.log` |
| 10 | SKILL.md addition | Separate `references/` file + short pointer (offset the word-ceiling) |
| 11 | Transcript resolution | Hook stdin `.transcript_path` → probe `--transcript` |

## Component Specifications

### `context-probe.py` (NEW)
Stdlib-only. Resolve transcript by priority: `--transcript` → `--session-id` (resolve `~/.claude/projects/*/<id>.jsonl`) → `$CLAUDE_CODE_SESSION_ID` (standalone only). Scan transcript from the end for the most recent assistant `usage` block; print `T` (or `--json`). Non-zero exit on unavailable. **Parity** with `claude-ctx-check` (missing/non-numeric `usage` → 0; malformed trailing JSONL skipped; record vendored source version); differential test pins it.

### `sdd-pre-dispatch-hook.sh` (MODIFY)
- **Hoist `.session_id`** to right after the `INPUT` parse (before classification) so the `--session-id` fallback works for all dispatch classes (today it is set only in the reviewer branch ~L200).
- **Shared helper** invoked at every dispatch exit path (reviewer `exit 0` ~L208, fix/re-review ~L165, passthrough ~L242, implementer): read `.transcript_path` from payload → run probe → append observation-log line (with `source=`). On probe failure, use the byte-proxy and log `source=byte-proxy action=fallback`.
- **Nudge/block** in the implementer new-task path only (a `verification` task IS eligible): `SOFT ≤ T < HARD` → append nudge to `additionalContext`; `T ≥ HARD` → `exit 2` with a **non-retryable** message (do not retry; commit; build fresh-session handoff; stop; see the protocol reference).
- Keep Check 7's byte-sum as the fallback branch (advisory, NOT a hard ceiling); retire only its standalone warning. `K` consecutive fallbacks escalate to a block.

### `references/context-handoff-protocol.md` (NEW)
The controller's block-response protocol ONLY: (1) the block is not fix-and-retry — retrying is wrong; (2) commit pending state; (3) invoke `handoff` skill (entry skill `superpowers:subagent-driven-development`); (4) tell the user to start a fresh session from the worktree and run `/pickup`; (5) STOP.

### `SKILL.md` (MODIFY)
Short pointer to the protocol reference. Offset the added words by extracting existing prose to a **separate** reference file (not the protocol doc). Keep the file under the hard word limit.

## Acceptance Criteria

- [ ] `context-probe.py` returns the correct summed `T` from a fixture transcript (`--transcript`) and resolves via `--session-id`; exits non-zero on the three unavailable cases.
- [ ] Hook allows with a normal reminder when `T < SOFT`.
- [ ] Hook injects a nudge when `SOFT ≤ T < HARD` on an implementer new-task dispatch.
- [ ] Hook blocks (`exit 2`, non-retryable message) when `T ≥ HARD` on an implementer new-task dispatch.
- [ ] Hook never nudges/blocks on reviewer / partner / fix / re-review dispatches; a `verification` task IS eligible.
- [ ] `--session-id` fallback resolves the transcript for every dispatch class with `transcript_path` omitted (`.session_id` hoisted before classification).
- [ ] Every dispatch appends one line (with `source=<probe|byte-proxy|bypass>`) to `reports/context-observations.log`; append failure never breaks a dispatch; tuning excludes non-`probe` rows.
- [ ] Probe failure → byte-proxy advisory (degraded, `source=byte-proxy action=fallback`, no crash); `K` consecutive fallbacks escalate to a block.
- [ ] Probe parity with `claude-ctx-check` (missing/non-numeric usage → 0; malformed trailing JSONL skipped) pinned by a differential test.
- [ ] Reading-across-auto-compaction (reading drops, tier resets) covered by a test.
- [ ] Retry + bypass after a hard block is tested.
- [ ] `SUPERPOWERS_CTX_SOFT_TOKENS` / `_HARD_TOKENS` / `_FALLBACK_STREAK` override defaults; invalid values fall back with a warning.
- [ ] `SUPERPOWERS_CTX_HANDOFF_BYPASS` skips the gate with a stderr warning.
- [ ] SDD SKILL.md stays under the hard word limit; hook baseline re-captured; e2e labeled checkout-path proof + post-merge live smoke check; regression + unit + e2e green.
- [ ] Operational + troubleshooting docs: `CLAUDE.md` (context-gate hook entry + `SUPERPOWERS_CTX_*` env-var list + test counts), `docs/ARaymond-skills-best-practices.md` (troubleshooting runbook: `action=fallback` diagnosis, threshold tuning from `context-observations.log`, disable via bypass, transcript-from-payload design note), `docs/ARaymond-customization-manifest.md` (inventory). BACKLOG N43 → done.
