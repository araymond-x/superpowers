# SP1 — the `[task N fix]` context-probe anomaly is a multi-iteration double-count

**Status: root-caused, fixed, regression-tested.** Spike SP1 of the `cmux-spawn-v2` sprint
(Task 2), against BACKLOG **N76** / run-analysis finding **F7**.

The anomalous row is not a misattribution, not a wrong transcript, and not a genuine spike.
`context-probe.py` summed the **top-level** `usage` fields of an assistant turn that contained
**three sequential model calls**. Claude Code records those calls in `usage.iterations` and the
top-level fields are their *sum*, so the same cached prompt was counted once per call. The
probe reported ~2x the context that existed.

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

Multi-iteration turns are **793**, and the inflation ratio is **exactly 2.0 in every one** —
two `message` iterations, one prompt counted twice. Note the 18 `('message','message')` rows:
**the bug is not advisor-specific**, so it is not confined to sessions that use that tool.

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
iteration exists (`iterations` absent, not a list, empty, or carrying none). Two branches, one
fallback; every branch corresponds to a shape observed in the table above except
`advisor_message`-last, which is unobserved and pinned by test so the behavior is chosen
rather than accidental.

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
statusline `ctx:` field it mirrors both over-report multi-iteration turns by ~2x. It lives
outside this worktree and was **read only**; fixing it is a separate change and the
controller's call. The existing differential parity test (`test_context_probe_fixtures.py`)
still passes untouched: its fixtures carry no `iterations` key, so both implementations take
the fallback path.

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
   poisoned row is **≈2.0x** its neighbors *and* the following row returns to the prior level.
   The observed ratio was exactly 2.0 in all 793 multi-iteration turns, which is far tighter
   than ">50%".
3. **Residual, stated rather than glossed:** zero compaction events were observed, so the 2.0x
   discriminator has **never been tested against a real pre-compaction peak**. If compaction
   can produce a similar shape, rule 2 could discard a true peak. Rule 1 has no such weakness —
   prefer it whenever the transcript survives.

## Files changed

| Path | Change |
|---|---|
| `skills/subagent-driven-development/scripts/context-probe.py` | `usage_total` / `_last_message_iteration` / `_sum_fields`; docstring records divergence #2 |
| `tests/unit/test_context_probe_iterations.py` | new — 8 tests, differential |
| `tests/unit/fixtures/context-probe/iterations-*.jsonl` | new — 7 fixtures, one carrying the real archived block verbatim |

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
> and the top-level fields are their SUM, so the same cached prompt is counted once per
> iteration: the archived `2026-07-30T00:56:54Z … tokens=373139` row's turn read
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
> in the retained corpus. Multi-iteration turns are ~4.5% of usage rows and inflate by exactly
> 2.0x; **not advisor-specific** (`('message','message')` also occurs). **No exclusion rule is
> needed for post-fix rows;** pre-fix rows should be recomputed from the retained transcript
> (exactly 1 of 80 rows in the cmux-transport log was poisoned). **`~/.claude/bin/claude-ctx-check`
> and the statusline `ctx:` field carry the identical uncorrected bug** — out of scope here,
> worth its own row. Full evidence:
> `docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md`.

Two consequences for other rows, for the merge step to route rather than for this task to act
on: **N43 threshold tuning** may now consume `source=probe` rows without a poison filter once
the pre-fix rows are recomputed; and the **`claude-ctx-check` / statusline defect** is
un-owned by any existing row.
