# SP1 — the `[task N fix]` context-probe anomaly is a multi-iteration double-count

**Status: root-caused, fixed, regression-tested.** Spike SP1 of the `cmux-spawn-v2` sprint
(Task 2), against BACKLOG **N76** / run-analysis finding **F7**.

The anomalous row is not a misattribution, not a wrong transcript, and not a genuine spike.
`context-probe.py` summed the **top-level** `usage` fields of an assistant turn that contained
**three sequential model calls**. Claude Code records those calls in `usage.iterations`, and the
top-level fields are the sum of the **`type: "message"`** iterations only — a non-`message`
iteration such as `advisor_message` is *excluded* from them. So the same cached prompt was
counted once per `message` call, and the probe reported ~2x the context that existed.

The outcome is a code fix, not an exclusion rule. Measurements below were taken **2026-07-31**;
each is paired with the command that recomputes it.

## The evidence

The archived row, in
`~/projects/claude-custom/claude-codex-handoff/.worktrees/cmux-transport/docs/imp-plans/2026-07-29-cmux-transport/reports/context-observations.log`:

```
2026-07-30T00:48:28Z task=  type=quality-review tokens=171666 source=probe tier=below action=allow
2026-07-30T00:56:54Z task=5 type=other          tokens=373139 source=probe tier=soft  action=allow
2026-07-30T01:02:54Z task=  type=other          tokens=210693 source=probe tier=below action=allow
```

The dispatch at `00:56:54Z` ran against session **`d8a9d842-d458-44dd-a280-a458ec9cdd9f`**
(transcript span `2026-07-30T00:24:59Z` → `02:21:58Z`, under
`~/.claude/projects/-Users-araymond-projects-claude-custom-claude-codex-handoff--worktrees-cmux-transport/`).
The value `373139` is present **in that transcript**, on the assistant turn timestamped
`00:55:22Z`–`00:56:53Z`, `isSidechain: false`, whose final content block is the
`Agent` tool-use carrying `"description": "[task 5 fix] trailing-comment regex"`. The probe
read the right file and the right block.

Its `usage`:

```
top-level                              iterations
  input_tokens                 4         [0] type=message           in=2       cc=1043  cr=180524  out=1641   -> 183210
  cache_creation_input_tokens  4039      [1] type=advisor_message   in=184836  cc=0     cr=0       out=1352   -> 186188
  cache_read_input_tokens      362091    [2] type=message           in=2       cc=2996  cr=181567  out=5364   -> 189929
  output_tokens                7005
  TOTAL                        373139
```

The arithmetic is exact and identifies the mechanism:

- `cache_read_input_tokens`: `180524 + 181567 = 362091` — **the same ~181k cached prompt,
  counted twice.**
- `cache_creation_input_tokens`: `1043 + 2996 = 4039`.
- `input_tokens`: `2 + 2 = 4`, and `output_tokens`: `1641 + 5364 = 7005` — the
  `advisor_message` iteration's own `in`/`out` are *excluded* from the top level, which is why
  the inflation shows up entirely in the cache fields.

The true context at the end of that turn is the last model call's prompt plus its output:
**189,929**. The next turn confirms it independently — it reads `cache_read_input_tokens =
181567`, exactly iteration [2]'s value, i.e. the conversation continued unbroken from a ~182k
prompt. There was never a 373k context.

**Why it correlated with a `[task N fix]` dispatch.** Not a code path. `ctx_observe_and_log`
is called identically on the fix path and the gated path, and both resolve the transcript from
`.transcript_path` with a `SESSION_ID` fallback — there is no fix-specific resolution code, so
N76's "on the fix-marked path" framing describes a correlation, not a mechanism. The real
cause is behavioral: a controller consults the advisor about a review finding and then
dispatches the fix **in the same turn**. That turn is multi-iteration by construction. The
archived block is exactly this — advisor consult, then `Agent` dispatch, one turn.

## Disposition of all five hypotheses

| | Hypothesis | Verdict | Basis |
|---|---|---|---|
| (a) | Sidechain/subagent misattribution | **FALSE** | The block is `isSidechain: false` and its own `sessionId` matches the transcript filename. Re-tested against the cmux-transport transcripts on their own evidence, not inherited from the controller's case. |
| (b) | A retry/error turn carried inflated `cache_creation` | **Closest, but the stated mechanism is wrong** | It *is* an extra-model-call turn, but `cache_creation` contributed 4,039 tokens. The inflation is entirely `cache_read`, and the trigger is an advisor call, not a retry. |
| (c) | Genuine transient spike | **FALSE** | True context was 189,929, corroborated by the following turn's `cache_read`. |
| (d) | Wrong transcript — matches the predecessor's end-of-session total | **FALSE** | `373139` is byte-exact present in the *correct* transcript at the *correct* time. The predecessor session `08d5a306` was still climbing through 373,208 → 405,505+ in the same minutes and never ended on 373,139; the near-miss with its `00:24:39Z` block (373,208) is coincidence. This was the leading hypothesis in the durable record and it is now retired. |
| (e) | Genuine pre-compaction peak | **FALSE — and it is false for the controller's own case too** | See below. |

## (e) is falsified, including for the observation that motivated it

`reports/task-002-controller-observation.md` records the controller's own session
(`3cc7b8ba-2d17-473b-b8c6-aaf8197f81cd`) reading **539,691** and then **305,208** minutes
later, and names auto-compaction as the residual hypothesis. That reading is **the same bug**.

Its peak turn is also `['message', 'advisor_message', 'message']`, with
`cache_read` of `266177 + 268508 = 534685`. Corrected: **270,851**. The later 305,208 is simply
a later, single-iteration turn — the context grew normally from 270,851. No compaction is
needed to explain the pair, and no compaction event was found.

The decisive test is monotonicity. Accumulated context should never fall within a session.
Counting turns whose total drops more than 15% below the previous turn (deduplicated by
`requestId`, since one turn writes several content-block rows):

| Session | Turns | Drops, current probe | Drops, corrected probe |
|---|---|---|---|
| `3cc7b8ba` (controller, the 539,691 case) | 77 | 2 | **0** |
| `d8a9d842` (cmux-transport, the 373,139 case) | 132 | 2 | **0** |

Every apparent non-monotonicity in both sessions is this one bug. **The probe total is
monotonic once iteration double-counting is removed** — which reverses the standing claim in
`reports/task-002-controller-observation.md` and in `reports/context-summary.md` that "the
probe total is not monotonic". Those two artifacts are the controller's flight recorder and
were left unedited by this task; the correction is recorded here and in the Task 2 report's
Concerns so it is not lost when `transition-module.py` archives them at the module boundary.

Caveat, stated because it bounds the claim: this shows **no compaction occurred in the
retained range of these two sessions**. It does not prove compaction never truncates a
transcript. If it does, it would appear as a drop — and after this fix a drop is once again a
meaningful signal rather than noise.

## Prevalence

Corpus sweep over the 120 largest transcripts under `~/.claude/projects` (33,004
usage-bearing rows):

| Shape | Rows |
|---|---|
| `('message',)` — single iteration | 32,160 |
| `('message', 'advisor_message', 'message')` | 775 |
| `('message', 'message')` | 18 |
| `iterations: []` | 15 |
| no `iterations` key | 36 |

Multi-iteration turns are **793**, every one of them carrying exactly two `message` iterations —
one prompt counted twice. The inflation ratio is therefore **~2x, but never exactly 2.0**:
re-measured across **822** multi-`message` turns the ratio (top-level ÷ last-`message`
iteration) runs **min 1.9427, max 1.9979, and is exactly 2.0 in 0 of 822**. It falls short of 2
because the last iteration's own `cache_creation` and `output` tokens are not duplicated — only
the re-read prompt is. Note the 18 `('message','message')` rows: **the bug is not
advisor-specific**, so it is not confined to sessions that use that tool.

**The ratio is not a structural constant — it scales with the `message` iteration count.** A
three-`message` turn measures **2.97x** (built and measured against the shipped probe; pinned by
`test_three_message_iterations_scale_beyond_2x`). Nothing in the data rules such a turn out; it
is merely unobserved in this corpus.

Within the cmux-transport feature's own corpus (15 transcripts, 1,803 usage rows, 81
multi-iteration turns), matching each of the **80** observation-log rows to a transcript block
**by value** — every row matched, none ambiguously — exactly **one** row landed on a
multi-iteration turn: the `373139` row, corrected to **189,929**. That is a positive control as
well as a count: the method resolved all 80 rows, so a second poisoned row would have been
found had one existed.

Reproduce the sweep, the row match and the no-op proof:

```bash
cd ~/.claude/projects && python3 - <<'EOF'
import json, glob, os, collections
F=("input_tokens","cache_creation_input_tokens","cache_read_input_tokens","output_tokens")
def s(d): return sum(d.get(f,0) if isinstance(d.get(f),int) and not isinstance(d.get(f),bool) else 0 for f in F)
seq=collections.Counter(); single=0; mismatch=0
for p in sorted(glob.glob("*/*.jsonl"), key=lambda q:-os.path.getsize(q))[:120]:
    for l in open(p, errors="replace"):
        try: u=(json.loads(l).get("message") or {}).get("usage")
        except Exception: continue
        if not isinstance(u,dict): continue
        it=u.get("iterations")
        if not isinstance(it,list): seq["<no key>"]+=1; continue
        seq[tuple(x.get("type") for x in it)]+=1
        if len(it)==1:
            single+=1; mismatch += (s(u)!=s(it[0]))
print(seq.most_common()); print("single:",single,"top-level != iterations[0]:",mismatch)
EOF
```

## The fix

`skills/subagent-driven-development/scripts/context-probe.py` — `usage_total` now reads the
**last `type: "message"` iteration** and falls back to the top-level fields when no such
iteration exists (`iterations` absent, not a list, empty, or carrying none) **or when the
iteration it finds yields no usable total**. Every branch corresponds to a shape observed in the
table above except `advisor_message`-last, which is unobserved and pinned by test so the
behavior is chosen rather than accidental.

**The fallback-on-zero is a safety property, not a tidy-up.** `_coerce_int` maps every non-int —
including floats, which are valid JSON numbers — to 0, so a malformed `message` iteration would
otherwise make the probe return **0 while exiting 0**: a *successful measurement* of an empty
context. This probe feeds a **blocking** gate, where 0 reads as `tier=below action=allow`, and a
poisoned `action=allow` row additionally **resets an in-progress fallback streak**, disarming
the K-consecutive escalation. That is strictly worse than a probe failure, which routes to the
byte-proxy and eventually blocks. Falling back to the top-level reading was measured to produce
**zero differences across all 273 retained transcripts** — a pure safety net, not a behavior
change. Because `iterations` is an **undocumented internal shape that is not version-stable**
(Claude Code's own documentation: *"the transcript entry format is internal to Claude Code and
changes between versions, so it's not a stable contract"*), this branch is also the degradation
path for a future shape change, not merely for corruption today.

The fallback is the legacy behavior, and the fix is **provably a no-op on the majority path**:
across all **32,160** single-iteration turns in the sweep, the top-level fields equal
`iterations[0]` exactly — **zero** mismatches (the detector was positive-controlled against a
planted mismatch before the count was trusted).

Live end-to-end proof, replaying each real transcript truncated at exactly the entry the hook
saw when it wrote the row:

| Logged | Corrected |
|---|---|
| 373,139 (archived cmux-transport row) | **189,929** |
| 539,691 (controller's own session) | **270,851** |

The script remains **stdlib-only** — verified by running it under bare `/usr/bin/python3`, not
the venv — and Python 3.9-compatible (`Optional[int]`, no builtin generics).

**Parity.** This is documented divergence **#2** from `~/.claude/bin/claude-ctx-check`, whose
`SOURCE_VERSION` is unchanged at `f83727ff80c0`. The source has the **identical bug** — its
`main()` sums the top-level fields with no iteration awareness — so `claude-ctx-check` and the
statusline `ctx:` field were both believed to over-report multi-iteration turns by ~2x. **The statusline claim was FALSIFIED by experiment on 2026-07-31 — see the correction note in this document's final section. Only `claude-ctx-check` over-reports.** It lives
outside this worktree and was **read only**; fixing it is a separate change and the
controller's call. The differential parity test is
`test_differential_parity_with_ctx_check` in `tests/unit/test_context_probe_sessionid.py` — it
is the only test that actually invokes both implementations. (`test_context_probe_fixtures.py`,
cited here in an earlier draft, is *not* a differential test: it invokes neither binary and
asserts a hand reimplementation against itself.) The parity test still passes untouched: its
fixture carries no `iterations` key, so both implementations take the fallback path.

**What parity now certifies, post-divergence.** The two implementations genuinely disagree on
multi-iteration transcripts — that disagreement *is* the fix. So this test no longer certifies
whole-behavior parity; it certifies only that **the fallback path still matches the source
byte-for-byte**. Divergence on multi-iteration input is pinned separately, by
`tests/unit/test_context_probe_iterations.py`, and nothing pins the two implementations against
each other on that input.

## Severity — two registers, deliberately kept apart

**Observed.** N76's "Harmless at runtime (`action=allow`)" is **falsified**. The controller's
own session read 539,691 against a true 270,851 and **handed off on that number** — a premature
handoff at ~68% of the true HARD threshold, costing a hop, a session and its warm context. The
gate's recorded `action` was indeed `allow` (the row was `type=other`, not the gated
implementer new-task path); the harm was the controller acting on a 2x inflated reading, not
the gate firing.

**Potential, not observed.** An inflated read on the implementer new-task path with a true
context of ~200k crosses `HARD=400000` and produces a **non-retryable spurious block**. No
instance of this exists in the corpus — it is a consequence of the same defect, not a sighting.

The tuning corruption N76 describes is real but is the least of the three.

## Guidance for tuning consumers

**Post-fix rows need no exclusion rule.** The plan's suggested rule — *drop rows that jump
>50% against both neighbors* — is not adopted, and would have been the wrong instrument twice
over: it treats a code defect as data noise, and its shape cannot distinguish a poisoned
reading from a real peak.

**Pre-fix rows** (everything already written to a `context-observations.log`), in order of
preference:

1. **Recompute from the retained transcript.** This is exact and is what was done here: match
   each row's token value against the transcript's usage blocks, and where the matched block
   has more than one iteration, substitute the last `message` iteration's total. Retention is
   not guaranteed, so do this while the transcripts exist.
2. **If transcripts have rotated**, use the sharper discriminator the data actually supports: a
   poisoned row sits in the **range 1.94x–2.00x** of its neighbors *and* the following row
   returns to the prior level. **State the discriminator as a range, not a point.** Measured
   across 822 multi-`message` turns the ratio never once equals 2.0 (min 1.9427, max 1.9979), so
   a rule keyed on "exactly 2.0" matches **none** of the real poisoned turns — it is inoperable,
   not merely imprecise. The range is still far tighter than ">50%". **It also assumes a
   two-`message` turn:** the ratio scales with the `message` iteration count (a three-`message`
   turn measures ~2.97x), so this rule would miss a 3-iteration poisoned row. Widen the band, or
   accept the miss, if such turns are possible in the corpus being cleaned.
3. **Residual, stated rather than glossed:** zero compaction events were observed, so the ~2x
   discriminator has **never been tested against a real pre-compaction peak**. If compaction
   can produce a similar shape, rule 2 could discard a true peak. Rule 1 has no such weakness —
   prefer it whenever the transcript survives.

## Files changed

| Path | Change |
|---|---|
| `skills/subagent-driven-development/scripts/context-probe.py` | `usage_total` (prefer last `message` iteration, fall back on absent-or-zero) / `_last_message_iteration` / `_sum_fields`; docstring records divergence #2 |
| `tests/unit/test_context_probe_iterations.py` | new — differential tests; count: `.venv/bin/python3 -m pytest tests/unit/test_context_probe_iterations.py --collect-only -q \| tail -1` |
| `tests/unit/fixtures/context-probe/iterations-*.jsonl` | new fixtures, one carrying the real archived block verbatim; count: `ls tests/unit/fixtures/context-probe/iterations-*.jsonl \| wc -l` |

`context-probe.py` is **not** a baselined hook — `grep -c 'context-probe' tests/ARaymond-hook-baseline/baseline.txt`
returns **0** (and a broader `grep -n 'probe'` over the same file returns no match), so no
integrity baseline re-capture is required for this change.

## BACKLOG merge action — apply to `main`'s N76, do not add a row

This branch appends nothing to `BACKLOG.md`. `main` already carries **N76** as this spike's
row, marked `in flight (cmux-spawn-v2 SP1)`. At merge, **replace** N76's status cell with
`done (cmux-spawn-v2 SP1)` and **replace its notes cell** with the text below.

> **ROOT-CAUSED AND FIXED (cmux-spawn-v2 SP1, 2026-07-31).** Not misattribution and not a wrong
> transcript — `context-probe.py` summed the TOP-LEVEL `usage` fields of an assistant turn
> containing several sequential model calls. Claude Code records those in `usage.iterations`
> and the top-level fields are the sum of the **`type:"message"`** iterations ONLY (a
> non-`message` iteration such as `advisor_message` is excluded), so the same cached prompt is
> counted once per `message` iteration: the archived
> `2026-07-30T00:56:54Z … tokens=373139` row's turn read
> `cache_read` of `180524 + 181567 = 362091` against a true context of **189,929**. The
> earlier "matches the predecessor's end-of-session total" reading is **withdrawn** — the value
> is byte-exact present in the correct transcript at the correct time, `isSidechain: false`.
> Also withdrawn: "on the fix-marked path" is a correlation, not a mechanism —
> `ctx_observe_and_log` resolves the transcript identically on both paths; `[task N fix]`
> dispatches simply tend to share a turn with an advisor consult. **Severity was understated:**
> "Harmless at runtime (`action=allow`)" is false — the controller's own session read 539,691
> against a true 270,851 and *handed off on that number*, wasting a hop and a session; an
> inflated read on the gated implementer new-task path could produce a spurious non-retryable
> HARD block (not observed). **Fix:** `usage_total` reads the last `type:"message"` iteration,
> falling back to the top-level fields; provably a no-op on all 32,160 single-iteration turns
> in the retained corpus. Multi-iteration turns are ~4.5% of usage rows and inflate by **~2x —
> measured range 1.94x–2.00x across 822 turns, exactly 2.0 in none of them**, and the ratio
> scales with the `message` iteration count (a three-`message` turn measures ~2.97x), so it is
> not a structural constant; **not advisor-specific** (`('message','message')` also occurs). **No exclusion rule is
> needed for post-fix rows;** pre-fix rows should be recomputed from the retained transcript
> (exactly 1 of 80 rows in the cmux-transport log was poisoned). **`~/.claude/bin/claude-ctx-check`
> carries the uncorrected bug** (the statusline does NOT — falsified by experiment 2026-07-31, see below) — out of scope here,
> worth its own row. Full evidence:
> `docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md`.

Two consequences for other rows, for the merge step to route rather than for this task to act
on: **N43 threshold tuning** may now consume `source=probe` rows without a poison filter once
the pre-fix rows are recomputed; and the **`claude-ctx-check` defect** (statusline excluded — measured correct) is
un-owned by any existing row.


## Correction 2026-07-31 — the statusline does NOT carry this bug (experiment)

**Statusline EXONERATED by experiment, 2026-07-31 (N=1, pre-registered).** The statusline's `ctx:` is NOT computed by any script here: `~/.claude/statusline-command.sh` reads `.context_window.used_percentage` from the JSON payload Claude Code writes to its stdin, and contains zero references to `claude-ctx-check`, `context-probe`, `.jsonl` or `transcript_path` — it does no arithmetic. A pre-registered test on a deliberately induced `['message','advisor_message','message']` turn (validity-checked: the discriminating block was confirmed present before the reading was read) predicted ~40% correct / ~79% if it summed message-type iterations / ~118% if it summed all. **Observed: 40%, matching true context 395,645.** The harness computes true context. `claude-ctx-check` alone carries the double-count, and its error is TRANSIENT — it misreports only while the newest usage block is the multi-iteration one, which is exactly the window the pre-dispatch hook samples in.

**Method, so it can be re-run.** Baseline taken on a single-iteration turn (all three sources agree there, so it cannot discriminate). Predictions pre-registered BEFORE the reading, with three branches rather than two — the two-branch version was too narrow, because the observed 1.99x came from summing the *message-type* iterations only, leaving a 3x all-iterations branch unbucketed and any mid-range reading ambiguous. An advisor call was then used to induce a multi-iteration turn. The transcript's newest multi-iteration block was confirmed to contain `advisor_message` BEFORE the statusline reading was interpreted — without that check the reading could have come from the turn before or after the discriminating one.

**Strength of the claim.** One observation, one turn, one harness version. It decisively refutes 'the statusline shares the bug' (a 40% reading is incompatible with both buggy branches) but does not establish correctness as a general property across all multi-iteration shapes.

**Provenance of the original error.** The claim was inferred from `claude-ctx-check`'s own docstring — *"the same underlying data the statusline's `ctx:` field"* — which asserts shared *data*, not shared *code*. It was propagated to six sites, including committed code, before being tested. Same infer-without-verifying class this document exists to document.
