# SDD Context-Aware Auto-Handoff — Design Spec

> **Feature:** `sdd-context-aware-handoff` (Component A — "the spine")
> **Status:** design, pending review
> **Date:** 2026-07-14
> **BACKLOG:** N43 (unblocks B10; supersedes C6(b)'s "gives B10 a pressure signal" linkage)
> **Archetype:** Extension — adds a context-pressure gate to the existing SDD pre-dispatch hook and SKILL; reuses the N39 fresh-session handoff and the documented SDD mid-plan resume path.

---

## 1. Problem

Long SDD runs degrade. The **controller** (the main orchestrator session) is a sustained-context role: it accumulates context across every task — reading each implementer report, both review outputs, checkpoint results, and its own reasoning — turn after turn. As its context window fills, response quality erodes: it starts taking shortcuts, making unflagged judgment calls, and skipping discipline. The subagents it dispatches are *not* affected — each gets a fresh context and returns — so the problem is the controller's alone.

Today the hook has a weak proxy for this (Check 7): it sums the byte sizes of the plan, deviations, and report files (`bytes/4 ≈ tokens`) and prints a non-blocking warning. It systematically **undercounts** — it is blind to review outputs, tool results, the controller's reasoning, and skill loads — and it never acts.

We want the controller to notice real context pressure at a clean boundary and, before quality slips, hand its remaining work to a fresh session that resumes exactly where it left off.

## 2. Goals & Non-Goals

### In scope
- A **deterministic context sensor** in `sdd-pre-dispatch-hook.sh` that reads the controller's *actual* accumulated token count.
- A **two-tier response**: an informational nudge, and a hard block that stops the next new-task dispatch and instructs a fresh-session handoff (it stops the dispatch; it does not, by itself, force the handoff — see §5.4).
- An **observation log** capturing every reading, so thresholds are tuned from real data after the first run.
- The controller's **handoff-response protocol**, reusing the existing N39 fresh-session bundle and the existing SDD mid-plan resume.

### Out of scope — do not build
- Component **B** — cross-session honesty aggregation → its own spec.
- Component **C** — pace-aware pause/resume around the 5h/weekly rate-limit windows via `cupace` → its own spec (different sensor, different remedy: sleep-until-reset, not handoff).
- Component **D** — cmux auto-spawn of the next session → its own spec (unattended self-spawn carries runaway + quota-burn risk).
- **B10** — making the context-summary gate (Check 6b) pressure-conditional → fast-follow on this sensor, once it is proven live.
- **Window auto-detection / a `ctxload` tool** — optional standalone diagnostic; never a dependency of this hook.
- **Context handoff for `writing-plans` / `brainstorming`** — those are single long sessions with few clean pause points → later.
- **Percentage-of-window triggering** — rejected (the window is unreachable from a hook; see §4).

## 3. Affected Code

| Path | Change |
|---|---|
| `skills/subagent-driven-development/scripts/context-probe.py` | **NEW** — vendored, stdlib-only token-count sensor |
| `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Add a shared probe+observation-log helper at **all** dispatch exit paths; nudge/block only in the implementer new-task path. Keep Check 7's byte-sum as the fallback branch; retire only its standalone warning. |
| `skills/subagent-driven-development/references/context-handoff-protocol.md` | **NEW** — the controller's block-response protocol only |
| `skills/subagent-driven-development/SKILL.md` | Short pointer to the protocol reference. Offset the added words by extracting existing SKILL.md prose to a **separate** reference file (not the protocol doc) — the file is at its word ceiling. |
| `tests/unit/` | New tests: `context-probe.py`, and the hook's context-gate branches |
| `tests/integration/sdd-e2e-test.sh` | New step exercising an over-threshold reading → block |
| `tests/ARaymond-hook-baseline/baseline.txt` | Re-capture (a baselined hook was edited) |
| `docs/ARaymond-customization-manifest.md`, `CLAUDE.md`, `docs/ARaymond-skills-best-practices.md` | **Operational + troubleshooting docs** (see §12) — env vars, observation-log format/tuning, byte-proxy fallback diagnosis, disable path, identify/troubleshoot runbook. Not just an inventory entry. |

## 4. Key Design Decisions

| # | Decision | Options considered | Chosen | Why |
|---|----------|--------------------|--------|-----|
| 1 | Enforcement mechanism | advisory SKILL text · deterministic hook · hybrid | **Hook (deterministic) enforces; SKILL text teaches the response** | Self-monitoring paradox: the degraded controller is exactly who ignores advisory prose. Hooks hold under pressure (fork philosophy). |
| 2 | Trigger metric | percentage-of-window · absolute token count | **Absolute token count** | The window is unreachable from a hook (bare `model` in transcript, nothing in env, `[1m]` only in non-universal OTEL), and runs are mixed 200k/1M. Absolute needs no window and better matches degradation (an absolute-load effect). |
| 3 | Sensor source | call external `~/.claude/bin/claude-ctx-check` · vendor a probe into the fork · inline in the hook | **Vendor `context-probe.py`** | Self-contained, team-distributable, and testable (fixture transcript). No coupling to a personal tool outside the repo. |
| 4 | Enforcement posture | advisory-only · two-tier nudge+block · hard-block-only | **Two-tier nudge + block** | Deterministic ceiling for unattended runs *plus* an early grace window. Advisory-only gives no guarantee; hard-only is abrupt. |
| 5 | Thresholds | (see §5.6) | **Absolute: soft 300k / hard 400k, catch-early, env-overridable, log-tuned** | Optimized for the common 1M window; conservative enough to catch degradation, high enough not to nag from 13%. |
| 6 | Where nudge/block apply | every dispatch · implementer new-task dispatches only | **Implementer new-task boundary only** (observation log on all) | Blocking a reviewer/partner/fix dispatch would strand a half-done task. The new-task implementer dispatch is the clean pause point (prior task committed). |
| 7 | Handoff + resume | build new · reuse N39 + `session-recovery.md` | **Reuse existing** | The fresh-session bundle (entry skill `subagent-driven-development`) and mid-plan resume already exist. SSOT. |
| 8 | Sensor failure | fail-open · byte-proxy advisory · fail-closed | **Byte-proxy advisory + persistent-fallback escalation** | The byte-proxy is non-blocking, so a single probe failure degrades to *advisory* (honestly NOT a hard ceiling — it undercounts and only warns). `K` consecutive fallbacks (`SUPERPOWERS_CTX_FALLBACK_STREAK`, default 3) escalate to a block + loud diagnostic, so a systematically-broken gate cannot stay silently inert. Chosen over strict fail-closed (which over-blocks on a transient hiccup). |
| 9 | Observation log location | extend `.dispatch-log` · separate file | **Separate `reports/context-observations.log`** | `.dispatch-log` has a parsed format that Check 9 / provenance depends on. |
| 10 | SKILL.md addition | inline · `references/` extraction | **Reference file + short pointer** | The SDD SKILL.md is at its word-count ceiling; any addition must be offset. |
| 11 | Transcript resolution | `CLAUDE_CODE_SESSION_ID` env var · hook stdin payload | **Hook stdin `.transcript_path` → probe `--transcript`** | The PreToolUse payload carries `transcript_path` (guaranteed); the env var is a different spawn path and is not guaranteed inside a hook — using it risks silently falling back to the byte-proxy every dispatch. Unifies with the test seam. |

## 5. Architecture

### 5.1 Context sensor — `context-probe.py`
Stdlib-only Python (no pydantic/PyYAML), so it runs under bare `python3`. Logic mirrors the proven `claude-ctx-check`:

- Resolve the transcript in priority order: (1) `--transcript <path>` if given (the **primary input** — the hook passes it, and it doubles as the **test seam**); (2) `--session-id <id>` → resolve `~/.claude/projects/*/<id>.jsonl`; (3) `$CLAUDE_CODE_SESSION_ID` via the same lookup (standalone/CLI use only). The hook uses (1), and only if the payload's `transcript_path` is empty falls to (2) — never the env-var path (see §5.2). All path-resolution logic lives solely in the probe (SSOT); the hook holds none.
- Scan from the end for the most recent assistant message carrying a `usage` block.
- Return `total_tokens = input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens`.
- Output: the integer token count (or `--json`). Exit non-zero with a diagnostic when the session id is unset, no transcript exists, or no turn has completed — the hook treats any non-zero exit as "probe unavailable" and falls back (§7).

- **Parity contract:** the transcript scan + 4-field sum mirror `claude-ctx-check` exactly; record the source version the copy was vendored from. Missing or non-numeric `usage` fields count as 0; a malformed trailing JSONL line is skipped. Differential/shared-fixture tests pin parity so the external tool and the vendored copy cannot silently diverge.

Deliberately **no window** and **no percentage** — the hook owns the thresholds.

### 5.2 Two-tier decision — in the hook
**Transcript resolution (guaranteed, no env var).** The hook already reads its stdin payload (`INPUT=$(cat)`; it parses `.session_id`, `.cwd`, `.tool_input.*` today at lines 44/200/53/56/59). It reads `.transcript_path` from that same payload — the PreToolUse payload carries it, and the sibling `sdd-skill-enforcement-hook.sh:35` already does exactly this — and passes it to `context-probe.py --transcript`. Only if the payload's `transcript_path` is empty does it instead pass `--session-id "$SESSION_ID"`, letting the probe resolve the file — so the hook holds no path-resolution logic of its own. **The hook must hoist `.session_id` extraction to immediately after the `INPUT=$(cat)` parse, before dispatch classification.** Today `SESSION_ID` is assigned only inside the reviewer sentinel branch (~L200), so implementer / fix / partner / passthrough dispatches would reach this fallback with an empty id and the probe would fail — silently degrading to the byte-proxy on exactly the dispatches the gate targets. This avoids `CLAUDE_CODE_SESSION_ID` entirely (a hook is a different spawn path than the `!` passthrough, so the env var is not guaranteed there) and unifies with the `--transcript` test seam.

**Shared probe+log helper.** The probe call and the observation-log append (§5.3) form a single helper invoked at **every** dispatch exit path — reviewer (`exit 0`, ~L208), fix/re-review (~L165), passthrough (~L242), and implementer — so the trajectory is captured for all dispatch types. This is *not* a single edit to Check 7; it is a helper threaded into multiple exit points. **Nudge and block apply only in the implementer new-task path** (predicate `IS_IMPLEMENTER && ! MARKED_FIX`); re-reviews and fixes already exit before that path, so they can never be blocked mid-task. A `task_type: verification` task IS an implementer dispatch and a clean new-task boundary, so it is **eligible** for nudge/block — only reviewer / partner / fix / re-review dispatches are exempt.

The hook already classifies each dispatch (reviewer / implementer / passthrough). The block/nudge tier attaches to the **implementer enforcement path**, evaluated only at a **new-task boundary** (not fix/re-review cycles — identified via the existing dispatch markers):

| Reading `T` | Action |
|---|---|
| `T < SOFT` | Allow. Normal SDD reminder. |
| `SOFT ≤ T < HARD` | Allow **+ nudge** appended to `additionalContext`: "Context ~`T` tokens — this is a clean task boundary. Consider handing off to a fresh session now (see context-handoff-protocol) rather than starting task N." |
| `T ≥ HARD` | **`exit 2` block.** Message states plainly: *do not retry*; commit pending state, build the fresh-session handoff, then stop. |

On every dispatch of any type, the gate appends one line to the observation log (§5.3) — even below `SOFT`, even for reviewers — so the trajectory is fully captured.

### 5.3 Observation log — `reports/context-observations.log`
One line per dispatch, greppable, distinct from `.dispatch-log`:
```
<ISO-8601> task=<N> type=<implementer|spec-review|quality-review|partner|other> tokens=<T> source=<probe|byte-proxy|bypass> tier=<below|soft|hard> action=<allow|nudge|block|fallback>
```
The `source` field is load-bearing: **threshold tuning consumes only `source=probe` rows** — byte-proxy and bypass rows don't reflect the real count and are excluded from the analysis. This recovers the evidence the deferred "instrument-first" step would have provided, so thresholds are set from data after run 1.

- **Append is best-effort:** a write failure (unwritable/missing `reports/` path) logs to stderr and **never breaks the dispatch**.
- **Scope:** the shared helper runs only after `INPUT` and the manifest have parsed. Pre-parse early exits (missing `jq` / CWD / manifest) happen before the helper and cannot log — they are not SDD-enforced dispatches, so they are out of scope.
- The hook already records its own output as an `attachment` record in the transcript, so the trace-audit step can later cross-reference.

### 5.4 Handoff-response protocol — `references/context-handoff-protocol.md`
The block's stderr is terse by necessity; the durable protocol lives in a reference the controller is pointed to from the SKILL body. It states: (1) the block is **not** a fix-and-retry — retrying is wrong; (2) commit any pending state; (3) invoke the `handoff` skill to build a bundle with entry skill `superpowers:subagent-driven-development` (the N39 flow); (4) tell the user to start a fresh session from the worktree and run `/pickup`; (5) then STOP — do not dispatch. Pairing the deterministic block with taught guidance is the standard fork pattern (advisory-in-skill + enforced-in-hook).

**Guarantee boundary.** The hook guarantees the *next task will not dispatch*; it does not, by itself, guarantee a clean handoff — building the bundle and stopping still depends on the controller reading and following this protocol. The block is the hard stop; the clean handoff is the taught response. The plan must not over-promise that "the hook forces a handoff."

### 5.5 Resume — existing, no new code
The fresh session's `/pickup` invokes SDD via the entry skill (arming the enforcement hooks). SDD resumes mid-plan per `references/session-recovery.md`: read plan checkboxes, `deviations.md`, and `reports/` (the flight recorder), then continue from the first unchecked task. `.sdd-session.json` is validated against the plan on resume.

### 5.6 Configuration
| Env var | Default | Meaning |
|---|---|---|
| `SUPERPOWERS_CTX_SOFT_TOKENS` | `300000` | Soft-nudge threshold |
| `SUPERPOWERS_CTX_HARD_TOKENS` | `400000` | Hard-block threshold |
| `SUPERPOWERS_CTX_HANDOFF_BYPASS` | unset | When set, skip the gate entirely (stderr warning), matching the `SUPERPOWERS_*_BYPASS` pattern |
| `SUPERPOWERS_CTX_FALLBACK_STREAK` | `3` | Consecutive byte-proxy fallbacks after which the hook escalates to a block + diagnostic (persistent-failure surface) |

Non-numeric or `HARD ≤ SOFT` overrides fall back to defaults with a stderr warning.

**Window policy (explicit).** The defaults (300k/400k) are tuned for the common **1M** window. The hard-block guarantee applies only to sessions large enough to reach `HARD` before their window forces auto-compaction — i.e. 1M sessions. On a **200k** session `HARD=400000` is unreachable; those runs are backstopped by their own (lossy) auto-compaction, and a user who wants active protection sets a lower per-session override — **lowering both** (e.g. `SOFT=100000 HARD=130000`). Setting only `HARD` below the default `SOFT=300000` trips the `HARD ≤ SOFT` guard and silently reverts both to defaults. **Auto-compaction interaction:** when a window auto-compacts, the latest transcript `usage` shrinks, so the probe reading drops and the tier resets — the gate will not fire post-compaction. This is documented behavior and must be covered by a reading-across-compaction test.

## 6. Data Flow
```
controller about to dispatch task N (implementer)
  └─ PreToolUse → Agent → sdd-pre-dispatch-hook.sh
       ├─ existing enforcement checks (unchanged)
       ├─ read .transcript_path from stdin payload
       ├─ context-probe.py --transcript <path> → total_tokens T   (fallback: byte-proxy on non-zero exit)
       ├─ append observation-log line  (shared helper, every exit path)
       └─ T ≥ HARD?  ── yes → exit 2  (block: commit, build N39 handoff, STOP)
                     └─ no  → allow (+ nudge if T ≥ SOFT)
controller (on block) → commit → handoff skill → STOP
you → fresh session → /pickup → SDD → session-recovery → first unchecked task
```

## 7. Error Handling & Edge Cases
- **Probe unavailable** (no session id / no transcript / no completed turn / malformed) → **byte-proxy advisory (degraded — honestly NOT the hard ceiling):** compute the Check-7 byte estimate, warn if over its threshold, log `source=byte-proxy action=fallback`, and never crash the dispatch. The byte-proxy undercounts and only warns, so this is *not* a deterministic block — do not describe it as "never fail open." **Persistent failure is surfaced:** after `SUPERPOWERS_CTX_FALLBACK_STREAK` (default 3) consecutive fallbacks, the hook escalates to a block with a diagnostic ("context gate has run blind for N dispatches — the probe is failing"), so a systematically-inert gate cannot hide.
- **Bypass set** → skip the gate, stderr warning, log `source=bypass action=allow`.
- **Observation-log append failure** → stderr note, dispatch proceeds (never breaks a dispatch); see §5.3.
- **Mid-task pressure** → the in-flight task's reviewer/fix dispatches are never blocked, so the task completes cleanly; the block fires at the *next* new-task boundary. Correct by construction.
- **First task** → thresholds naturally unmet (context is small); no special-casing.
- **Subagents** → the gate runs only in the controller session and measures the controller; subagent prompts and dispatch are untouched.
- **Repeated nudges** → informational only; the controller may keep going until the hard block. Acceptable (the block is the hard stop; the clean handoff remains the taught response — §5.4).
- **Post-block evasion** → the block stops the next *classified new-task* dispatch; a determined controller could still retry, dispatch an unclassified passthrough, set the bypass, or commit without a bundle. Honest scoping (no durable handoff-required state this spine); the objective and acceptance criteria are worded to match what the block actually delivers. Retry and bypass behavior are tested.

## 8. Testing Strategy
- **Unit — `context-probe.py`:** fixture transcript → correct `total_tokens`; empty/malformed → non-zero exit; missing session id → non-zero exit. **Parity/differential:** missing or non-numeric `usage` fields count as 0; a malformed trailing JSONL line is skipped; a shared fixture cross-checks parity with `claude-ctx-check`. (`--transcript` seam.)
- **Unit — hook context gate:** below / soft / hard branches; block only on implementer new-task dispatch, **never** on reviewer/partner/fix/re-review; **verification task IS eligible** (block/nudge fires); **`--session-id` fallback works for every dispatch class** with `transcript_path` omitted (proves the hoist — the pre-fix version fails here); **persistent fallback** — `K` consecutive probe failures escalate to a block; env-override parsing incl. invalid values; bypass logs `source=bypass`; observation-log append failure (unwritable `reports/` path) → dispatch proceeds; **retry + bypass** behavior after a block. Feed a deterministic reading via the `--transcript` fixture on the stdin payload.
- **Integration — e2e:** a step drives an over-threshold reading and asserts the dispatch is blocked with the non-retryable handoff instruction, and that an observation-log line (with `source=probe`) was written. **This is checkout-path proof only** — the live hook resolves to the main checkout via settings.json, so the e2e exercises *this checkout*, not the installed live hook (see §9).
- **Regression:** `validate-all-skills.py` — SDD SKILL.md must stay under the hard word limit (offset the pointer with a `references/` extraction).
- **Baseline:** `check-hooks.sh --capture` in the same change (a baselined hook was edited).

## 9. Constraints
1. **SDD SKILL.md is at its word ceiling** — the protocol pointer must be offset by extracting existing content to `references/`.
2. **Self-hosting hazard (H1)** — the live hook resolves to this main checkout via settings.json absolute paths, so editing it affects the running session. Implement in a worktree; the e2e tests *this checkout*, not the live hook. Baseline re-capture alone does not validate the active settings path, so add a **post-merge live-hook smoke check** (or explicitly label the e2e as checkout-path proof only) to confirm the installed path fires.
3. **Test seam is a first-class design element**, not an afterthought — `context-probe.py` must accept a fixture transcript so tests never depend on real context.
4. **Stdlib-only probe** — `context-probe.py` must not import pydantic/PyYAML (it may be invoked with bare `python3`).

## 10. Acceptance Criteria
- [ ] `context-probe.py` returns the correct summed token count from a fixture transcript and from the live session; exits non-zero on the three unavailable cases.
- [ ] Hook allows with a normal reminder when `T < SOFT`.
- [ ] Hook injects a nudge when `SOFT ≤ T < HARD` on an implementer new-task dispatch.
- [ ] Hook blocks (`exit 2`, non-retryable message) when `T ≥ HARD` on an implementer new-task dispatch.
- [ ] Hook never blocks on reviewer / partner / fix / re-review dispatches; a `verification` task IS eligible for nudge/block.
- [ ] `--session-id` fallback resolves the transcript for **every** dispatch class with `transcript_path` omitted (`.session_id` hoisted before classification).
- [ ] Every dispatch appends one line (with `source=<probe|byte-proxy|bypass>`) to `reports/context-observations.log`; append failure never breaks a dispatch; tuning excludes non-`probe` rows.
- [ ] Probe failure → byte-proxy advisory (degraded, logged `source=byte-proxy action=fallback`, no crash); `K` consecutive fallbacks escalate to a block + diagnostic.
- [ ] `context-probe.py` parity with `claude-ctx-check` (missing/non-numeric usage → 0; malformed trailing JSONL skipped) is pinned by a differential test.
- [ ] Reading-across-auto-compaction behavior (reading drops, tier resets) is covered by a test.
- [ ] Retry + bypass behavior after a hard block is tested.
- [ ] `SUPERPOWERS_CTX_SOFT_TOKENS` / `_HARD_TOKENS` / `_FALLBACK_STREAK` override the defaults; invalid values fall back with a warning.
- [ ] `SUPERPOWERS_CTX_HANDOFF_BYPASS` skips the gate with a stderr warning.
- [ ] SDD SKILL.md stays under the hard word limit; hook baseline re-captured; e2e labeled checkout-path proof + post-merge live-hook smoke check; regression + unit + e2e green.
- [ ] Operational + troubleshooting docs written per §12 (CLAUDE.md hook entry + `SUPERPOWERS_CTX_*` env-var list + test counts; skills-best-practices troubleshooting runbook; manifest inventory); BACKLOG N43 → done.

## 11. Open Questions
- **"New-task boundary" predicate** (spec-review confirmed sound): `IS_IMPLEMENTER && ! MARKED_FIX` — re-reviews and fixes already exit before the implementer path, so they cannot be blocked. The plan finalizes the exact variable names against the hook's existing dispatch-marker classification (`[task N fix]`, `[task N re-review:...]`).
- **Hook test seam** (resolved by the §5.2 transcript-from-stdin design): hook branch tests supply a stdin payload whose `.transcript_path` points at a fixture transcript built to yield a chosen token total (below / soft / hard). No separate override env var is needed — the same `--transcript` path serves production and tests. Remaining detail: author the small set of fixture transcripts at known totals.

## 12. Operational Documentation (deliverable)

So a future session can *identify and troubleshoot* the gate without re-deriving it, the implementation must document — not merely inventory:

- **`CLAUDE.md`** — a Hooks-Based Enforcement entry for the context gate (what it does, where it lives, that it is manifest-gated to SDD sessions); the three `SUPERPOWERS_CTX_*` env vars added to the Hook Development Gotchas env-var list (alongside `SUPERPOWERS_VALIDATOR_BYPASS` / `SUPERPOWERS_SDD_BYPASS`); updated test counts.
- **`docs/ARaymond-skills-best-practices.md`** — a troubleshooting/failure-modes runbook: *gate never fires* → check `transcript_path` resolution and the observation log for `action=fallback`; *falling back every dispatch* → probe exit code / stdlib-only; *fires too early/late* → tune thresholds from `context-observations.log`; *how to disable* → `SUPERPOWERS_CTX_HANDOFF_BYPASS`. Include the transcript-from-payload rationale (why not the env var) so it isn't "fixed" back to the fragile path.
- **`docs/ARaymond-customization-manifest.md`** — inventory entry for `context-probe.py`, the hook change, the protocol reference, and the observation log.
- **BACKLOG N43** — flip to `done` with the merge commit; note B10 is now ready as the fast-follow.
