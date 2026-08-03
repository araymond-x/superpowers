# Context measurement in SDD — what we learned, and the recommended architecture

**Status: RECOMMENDATION, not a decision. Nothing here is scheduled.** Written 2026-07-31 mid-sprint
(`cmux-spawn-v2`, Module 1) so the findings are not lost. The explicit intent is **not** to re-architect
before the sprint finishes — see §6 for what to do now versus later.

**Portability is a first-class constraint.** This tooling gets handed to other engineers with different
models, different context windows (200k vs 1M), and possibly no custom statusline. Any recommendation
that only works on one machine's configuration is rejected on that basis alone.

---

## 1. What we actually established

Two things were proven this session, both by execution rather than reasoning.

**(a) The transcript's top-level `usage` fields double-count multi-iteration turns.** A single assistant
turn can contain several sequential model calls, recorded under `message.usage.iterations` with a `type`
discriminator (`"message"`, `"advisor_message"`). The top-level fields aggregate across the
**`message`-type** iterations, so the same `cache_read_input_tokens` is counted once per iteration.
Measured: top-level `539,691` against a true `270,851`, with `268840 + 270851 = 539691` exactly.
Fixed in `context-probe.py` (SP1 / Task 2) by reading the last `message` iteration.

Note the precision: it is the sum of the **`message`-type** iterations, *not* of all iterations —
summing all three of that turn's iterations gives `811,442`, which matches nothing.

**(b) The statusline is NOT affected, and the harness's own figure is correct.** Falsified by
pre-registered experiment. `~/.claude/statusline-command.sh` reads `.context_window.used_percentage`
from its stdin payload and does no arithmetic. On an induced `['message','advisor_message','message']`
turn the branches predicted ~40% (correct) / ~79% (sums message-type) / ~118% (sums all); **observed 40%
against a true 395,645.** N=1, one turn, one harness version — decisive against the shared-bug claim,
not a proof of general correctness.

**(c) The error is TRANSIENT, and its window is exactly where the gate samples.** `claude-ctx-check`
misreports only while the newest usage block is the multi-iteration one. The next ordinary turn
self-corrects it. That is why manual spot-checks looked fine while the hook caught a 2× reading: the
hook samples at dispatch time, and a controller dispatches immediately after the kind of turn that
produces the poisoned block.

---

## 2. The constraint that determines the architecture

Confirmed against current official documentation:

| surface | carries context/token data? |
|---|---|
| `statusLine` | **YES** — `context_window.used_percentage`, `remaining_percentage`, `total_input_tokens`, `total_output_tokens`, and a `current_usage` breakdown |
| `PreToolUse` (our gate) | **NO** |
| `UserPromptSubmit`, `PostToolUse`, `Stop`, `PreCompact`, `PostCompact`, `SessionStart` | **NO** |

`PreToolUse` receives `session_id`, `prompt_id`, `transcript_path`, `cwd`, `permission_mode`,
`hook_event_name`, `effort.level`, `tool_name`, `tool_input`, `tool_use_id` — and nothing about context.

**So transcript parsing was never a lazy shortcut. At the gate point it is the only option.** That
reframes the whole design: the question is not "should we parse the transcript?" but "how do we get the
authoritative number to a place that has none?"

**And the shape we parse is undocumented.** The docs state the transcript entry format is internal and
changes between versions — *"not a stable contract."* `iterations` and its `type` discriminator are not
documented anywhere. Our fix is correct today and is **structurally brittle** by construction. That is
the single most important thing to design around.

---

## 3. Recommended architecture — a statusline sidecar with a fallback ladder

**The pattern:** the only surface with authoritative data (`statusLine`) writes a tiny state file; the
surface that needs it (`PreToolUse`) reads that file.

```
statusLine hook ──writes──> <session-scoped state file> ──reads──> PreToolUse gate
  (authoritative,                {pct, tokens, window,              (needs it, has
   window-aware)                  session_id, turn, mtime}           no data of its own)
```

Resolution ladder at the gate, most to least trustworthy — the gate already has this shape
(`source=probe|byte-proxy|bypass`); this adds one rung above `probe`:

| rung | source | trust | when used |
|---|---|---|---|
| 1 | `sidecar` | authoritative, harness-computed, window-aware | sidecar present, session matches, fresh |
| 2 | `probe` | correct today, undocumented shape | no sidecar, or stale/mismatched |
| 3 | `byte-proxy` | advisory only | probe fails |
| 4 | escalate | — | K consecutive fallbacks (existing rule) |

### Why this beats the alternatives

- **OpenTelemetry export** — post-session, cannot gate a live dispatch.
- **Agent SDK cost tracking** — wrong runtime; we are hooks, not an SDK app.
- **`/status`** — UI only, no programmatic surface.
- **Keep transcript-only** — works, but stays permanently exposed to an undocumented shape with no
  authoritative cross-check.

### Portability — the part that needs care

`settings.json` holds exactly **one** `statusLine` entry, so we cannot simply claim it. Requirements:

1. **Ship a composable writer, not a replacement.** Our script writes the sidecar and then
   `exec`s/delegates to the user's existing statusline command, passing the payload through unchanged.
   A teammate with a custom statusline keeps it; a teammate with none gets a no-op renderer.
2. **The sidecar must be strictly optional.** Absent → rung 2, silently and correctly. Nobody is
   *required* to install a statusline for SDD to work.
3. **Percentage, not just absolute tokens, when the sidecar is available.** This is the portability
   win. Today's thresholds are absolute (300k/400k) and 1M-tuned, which is why `CLAUDE.md` documents
   the "HARD≤SOFT trap" — a 200k user must lower *both* env vars or the guard reverts to defaults.
   `used_percentage` is window-aware by construction and needs no per-teammate tuning. Recommendation:
   express thresholds as **percentages with absolute floors**, use percentage when rung 1 is available,
   fall back to absolute on rung 2.

### Guards the sidecar needs — each earned by something observed

- **Freshness.** One-turn latency is inherent (see §4). Stamp `session_id` + turn/mtime; if the sidecar
  is stale beyond a bound or belongs to another session, drop to rung 2. A stale sidecar
  *under*-reports, which fails open.
- **Null handling.** Documented: `context_window.current_usage` is `null` before the first API call and
  again immediately after `/compact` until the next call. The writer must skip or write an explicit
  unknown; the reader must treat unknown as *fall back*, never as zero. **A zero silently disables the
  gate** — the codebase's existing "a silently-inert gate is not allowed" rule applies directly.
- **Version canary.** Because `iterations` is undocumented: assert the expected shape and **fail loudly**
  when it changes, rather than silently mis-measuring. The Task 2 fixtures already pin real blocks; the
  canary is the missing half. This is the mitigation for §2's brittleness, and it is the highest-value
  item in this document.
- **Rung-1-vs-rung-2 differential.** When both are available, log both and alert on divergence beyond a
  tolerance. That is precisely the check that would have caught the double-count on day one — and note
  it only works because they are *independent* implementations. Two implementations of the same formula
  are one witness, which is the trap that produced the original wrong conclusion.

---

## 4. On timing — the question of *when* to check

**Keep the gate where it is.** `PreToolUse` on the implementer dispatch is the correct decision point:
it is the last moment before committing to expensive work, and it is the only point where refusing is
cheap. The defect was never the timing; it was the measurement.

Two properties to document rather than fix:

**One-turn lag is inherent to every source.** At `PreToolUse` the current turn's usage block has not
been written, so any measurement — sidecar or probe — reflects the *previous* completed turn. It
therefore **understates** current context, and understates most exactly when a large tool result has
just landed, which is when context jumps hardest. This is a fail-open direction. It is tolerable only
because the thresholds carry headroom (300k/400k against a 1M window). **On a 200k window that headroom
does not exist**, which is a second, independent reason percentage-based thresholds are the portable
answer.

**Do not add a second gate.** A `Stop`/`PostToolUse` check was considered and is not recommended: those
surfaces have no context data either, so a second gate would inherit the same measurement problem while
adding a second place to maintain. If more visibility is wanted, add **observability** (log the reading
at more points), not more gates.

---

## 5. What would have caught this sooner

Recorded because the process lesson generalizes beyond this bug.

1. **Two instruments agreeing is not corroboration when they share a formula.** `context-probe.py` and
   `claude-ctx-check` agreed exactly — because both summed the top-level fields. That agreement was read
   as confirmation and it was the reason a false "auto-compaction" hypothesis survived. Independence is
   the property that matters, not agreement.
2. **A doc comment is not a verified fact.** *"the same underlying data the statusline's `ctx:` field"*
   says shared **data**, not shared **code**. It was over-read into "the statusline shares the bug",
   which propagated to six sites — including committed code — before anyone tested it. One
   twenty-minute experiment refuted it.
3. **Pre-register predictions, and bucket every outcome.** The first prediction table had two branches;
   the observed 1.99× came from message-type iterations only, leaving a 3× branch unbucketed. Any
   mid-range reading would have been rounded to whichever branch was nearer.
4. **Validity-check the instrument before reading the result.** The statusline reading was only
   meaningful once the discriminating turn was confirmed present in the transcript. Without that, the
   reading could have come from the turn before or after.

---

## 6. Recommended sequencing — deliberately conservative

### Do now, inside this sprint (near-zero cost)

- **Nothing architectural.** The probe fix is correct and the gate works. Re-architecting mid-sprint
  buys nothing and risks the feature.
- **One docstring addition**, folded into the `[task 2 fix]` round that already owes two corrections:
  state that `iterations` is an **undocumented, version-unstable internal shape**, with the
  documentation's own "not a stable contract" caveat cited. Cheap, and it is the honest label on a
  known risk. No new dispatch — it rides along.

### Do next, as its own scoped work

- **A spike, not an implementation.** Contract-verify first, in this repo's own Task 0 style: dump a
  **real** `PreToolUse` payload and a **real** `statusLine` payload and confirm the field inventory
  first-hand. The §2 table is from documentation via a research subagent — good enough to design
  against, **not** good enough to build on unverified. This repo has filed two BACKLOG rows on false
  premises and nearly a third; the whole point of Task 0 is that external facts get checked.
- **Then** the sidecar writer + gate rung + guards from §3, as a normal planned feature.
- **The version canary is separable and should go first** — it is the cheapest item here and it protects
  the fix we already shipped, independent of whether the sidecar is ever built.

### BACKLOG rows to file at merge (ids allocated against `main` at the time)

1. **`claude-ctx-check` carries the multi-iteration double-count** — port the `context-probe.py` fix.
   Confirmed by source inspection (zero `iterations` references) and by replay. **Scope to
   `claude-ctx-check` only — the statusline is measured correct and must not be named.**
2. **Version canary for the undocumented `iterations` shape** — fail loudly on drift.
3. **Statusline-sidecar context source for the SDD gate** — the §3 architecture, gated behind the
   contract-verification spike.
4. **Percentage-based thresholds with absolute floors** — retires the documented "HARD≤SOFT trap" and
   removes per-teammate tuning. Depends on (3).

---

## 7. Honest limits of this document

- §2's field inventory is **documentation-sourced via a research subagent**, not verified first-hand.
  It is consistent with our own hook's design (it reads `.transcript_path` precisely because nothing
  better is offered) but that is corroboration, not proof. §6 makes verifying it the first step.
- §1(b) is **N=1**. It refutes the shared-bug claim decisively; it does not establish the harness figure
  as correct in general.
- **Zero compaction events were observed** in either corpus examined. Compaction's interaction with any
  of these sources is reasoned from documentation, not measured.
- The sidecar architecture has **not been prototyped**. The composable-statusline requirement in
  particular (delegating to a teammate's existing script) is a design claim, not a demonstrated one.
