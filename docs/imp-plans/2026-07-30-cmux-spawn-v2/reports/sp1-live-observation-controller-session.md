# SP1 — a live, first-hand probe observation from the controller's own session

**Captured 2026-07-31 by the controller, unplanned.** Not a Task 2 deliverable and not a substitute for one. Task 2 owns the root cause; this is retained evidence the implementer should test its hypotheses against, because unlike the archived `373139` row **this transcript is live, local, and inspectable right now**.

## What happened

The controller's own context-pressure gate logged a HARD-tier reading and the controller handed off. Minutes later `claude-ctx-check` reported a number ~43% lower. Both instruments were then re-run against the same transcript and **agreed exactly** — so the discrepancy was temporal, not instrumental.

| When | Reading | Source |
|---|---|---|
| `2026-07-31T01:08:20Z` | **539,691** | `context-observations.log`, `task=1 type=other source=probe tier=hard action=allow` |
| `2026-07-31T01:19:17Z` | **305,208** | `context-probe.py --transcript` and `claude-ctx-check`, agreeing to the token |

## The component breakdown — this is the useful part

Same transcript, same session, both blocks `isSidechain: false`:

```
PEAK   line 326  2026-07-31T01:06:46  model=claude-opus-5
  input_tokens                    =        4
  cache_creation_input_tokens     =     4038
  cache_read_input_tokens         =   534685      <-- the whole story
  output_tokens                   =      964
  TOTAL                           =   539691

LATER  line 443  2026-07-31T18:53:49  model=claude-opus-5
  input_tokens                    =        2
  cache_creation_input_tokens     =     2000
  cache_read_input_tokens         =   305269
  output_tokens                   =     1397
  TOTAL                           =   308668
```

The total did not *shift between components* (which cache expiry would produce — the same prompt re-billed from `cache_read` to `cache_creation`). It **fell**, driven entirely by `cache_read_input_tokens`. The prompt genuinely got smaller.

## What was ruled out, and how

- **Sidechain / subagent contamination — RULED OUT.** The plan's hypothesis (a). The peak blocks carry `isSidechain: false`, and this transcript contains **zero** sidechain entries (145 usage blocks, all `false`). Subagent turns are written to their own transcript files, not interleaved here. A sidechain filter in `find_latest_total` would not have changed this reading.
- **A different session's entries — RULED OUT.** Peak blocks and ordinary blocks are metadata-identical: same `sessionId` (matching the transcript filename), same `userType: external`, same `isSidechain`. There is no discriminator field separating them, so no filter could distinguish them either.
- **Instrument disagreement — RULED OUT.** `context-probe.py` and `claude-ctx-check` returned the identical 305,208 on the same file. The probe is a faithful mirror.

## The residual hypothesis, stated as a hypothesis

The reading appears to have been **correct at the time**: the context really was ~540k, and something reduced it to ~305k in the interval — auto-compaction being the obvious candidate, since the harness summarizes context as a conversation grows and does so without an in-band marker the probe can see.

**Not asserted as established.** Compaction was not directly observed, no compaction record was located in the transcript, and no attempt was made to find one. That search is Task 2's, not this note's.

## Why this matters to SP1, concretely

The plan offers three hypotheses — (a) sidechain, (b) inflated `cache_creation`, (c) genuine spike — and the partner review added a fourth from `main`'s N76 and the run-analysis doc's F7: the value matches the **predecessor session's** end-of-session total.

This observation is (c), **with a mechanism the plan does not name** and which changes what the deliverable should be:

1. **The probe's absolute total is not monotonic.** It can legitimately fall between consecutive dispatches. Any exclusion rule shaped like *"drop rows that jump >50% against both neighbors"* — the plan's own suggested wording — would discard a **true** pre-compaction peak as noise. A tuning consumer needs to distinguish "poisoned reading" from "real peak, since compacted", and a bare spike-shape test cannot.
2. **It supplies a competing explanation for the archived row's own shape.** `373139` sitting between `171666` and `210693` neighbors is exactly what a genuine pre-compaction peak followed by a post-compaction reading looks like. The implementer must **positively discriminate** between that and misattribution rather than assuming the spike shape proves a bug — a spike is consistent with both.
3. **The gate's behavior was correct either way.** A HARD block on a genuine 540k is the gate working, not misfiring. If the root cause is compaction, `context-probe.py` may need no fix at all and the deliverable is the exclusion rule — but that conclusion must be *earned* against the retained cmux-transport transcript, not inherited from this note.

## How to reproduce

```bash
T=$(ls -t ~/.claude/projects/*-Users-araymond-projects-claude-custom-superpowers--worktrees-cmux-spawn-v2/*.jsonl | head -1)
python3 skills/subagent-driven-development/scripts/context-probe.py --transcript "$T"
```

Session `3cc7b8ba-2d17-473b-b8c6-aaf8197f81cd`. **Retention is not guaranteed** — if the root cause turns on this transcript, copy it somewhere durable before it rotates.

## Scope note

The controller did not extend this into the root-cause investigation: that is Task 2's dispatched work, and doing it here would both pollute controller context and pre-empt the review cycle. What is recorded above is only what fell out of checking a discrepancy in the controller's own gate reading.
