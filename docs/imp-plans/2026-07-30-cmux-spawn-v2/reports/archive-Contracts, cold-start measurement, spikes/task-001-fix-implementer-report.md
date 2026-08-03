---
schema_version: 1
task_id: 1
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md
    description: "Fix round for the Task 1 quality review: axis-3 limit withdrawn and rewritten (cmux rpc is a CLI path to arbitrary RPC params); new Axis 4 (exhaustive 127-verb CLI sweep, a-run) added as the leg that actually carries the primary-path conclusion; new Re-capture section with the complete live transcript of the keystone SP2_SURF_MARK read-back plus the workspace-level read-back; flip condition rewritten against shipped code; H2/H3 help captures made byte-complete and H1's elision marked; fence annotations moved outside code blocks; D5 (per-invocation deprecation hint) added to the divergence table; a-run label on both spellings now earned; deviations table extended to 10 rows."
  - path: docs/process-improvement-findings/BACKLOG.md
    description: "Two rows, both edited in place, no other line touched: N76 clause (1) now carries the read-back evidence (I1), its flip condition is rewritten against the shipped spawn verb with the cmux rpc residual stated (I3+B1), its summary clause's unqualified 'no env channel on any axis' is scoped to documented CLI verbs, and its status column is aligned with the rewritten flip condition; N67's status column and Notes gain an UPDATE 2026-07-30 discharging the stale 'not exercised — probe before building' instruction and pointing at N76 (I2). Delivered across two commits — the summary-clause and status-column qualification landed in a follow-up after a coherence re-read."
tests:
  written: 0
  passing: 0
  command: "bash tests/ARaymond-installation/verify-symlink-install.sh"
  result: PASS
contract_compliance:
  - constraint: "Write scope: only the disposition doc and BACKLOG.md (N76 + N67 rows)"
    status: compliant
    detail: "git diff touched exactly those two paths. The BACKLOG diff is 2 changed lines, verified by `git diff --unified=0` hunk headers: line 114 (N67) and line 123 (N76). No plan file, no deviations.md, no production code, no other findings doc, and no other BACKLOG row."
  - constraint: "Do not propagate or fix the pre-existing N54/N57 unescaped-pipe corruption"
    status: compliant
    detail: "Neither row is in the diff. Table integrity of my two rows checked with a negative-lookbehind unescaped-pipe count: N67 and N76 both = 8, matching the header row and the N72/N75/N51 controls. The new `SP2_SURF_MARK=\\|alpha` is escaped."
  - constraint: "Do not overwrite task-001-implementer-report.md"
    status: compliant
    detail: "Untouched; this is a new file at task-001-fix-implementer-report.md. The original remains available to the re-reviewer alongside it."
  - constraint: "Live cmux probing: throwaway sp2fix-* workspace, --focus false, deleted, zero residual"
    status: compliant
    detail: "One workspace created (`sp2fix-env` = workspace:41) with --focus false, closed with exit 0. Post-cleanup listing checked mechanically: `grep -c sp2` = 0 and `grep -c workspace:41` = 0 over the captured listing. Asserted on the SET of 5 surviving workspaces, not their order."
  - constraint: "Capture stdout and stderr separately and gate on exit code (Task 0 precedent)"
    status: compliant
    detail: "Every probe in the re-capture redirected stdout and stderr to separate files and printed the exit code. This immediately paid off: `cmux new-workspace` emitted the deprecation hint on stderr while stdout carried a clean `OK workspace:41` — recorded as new divergence D5."
  - constraint: "Bash discipline: no set -u / set -e / pipefail, bash >= 3.2, printf not echo, no producer piped into grep -q"
    status: compliant
    detail: "No shell script was modified. The ad-hoc probe commands used printf, set none of those options, and used a here-string (`grep -qi -- '--env' <<< \"$out\"`) rather than piping a producer into grep -q."
  - constraint: "Never git stash; never git add -A; stage explicit paths"
    status: compliant
    detail: "No stash. Only the two allowed paths plus this report were staged by name. The controller's in-flight artifacts (deviations.md, .dispatch-log, context-observations.log, checkpoint/partner/review files) were left untouched and unstaged."
  - constraint: "The worktree .venv symlink must never be deleted or recreated"
    status: compliant
    detail: "Not touched. No venv operation performed."
  - constraint: "handoff_spawn must appear in no frontmatter until Task 4"
    status: compliant
    detail: "Not used in either changed file or in this report's frontmatter."
  - constraint: "Screen polling is a measurement instrument only, never a production readiness signal"
    status: compliant
    detail: "read-screen was used solely to read env values back inside a throwaway workspace. No production code changed, so nothing gates on a screen read."
---

# Task 1 (fix round) — remediating the adversarial quality review

## Implementation Summary

Documentation-only remediation of `task-001-quality-review.md` (CHANGES_REQUESTED): one BLOCKING
finding, four IMPORTANT, four MINOR. All ten are closed. Nothing was deferred.

The blocking finding was verified independently before acting on it, and one live probe session was
run to close the un-re-verifiable keystone datum. **The headline disposition survived** — see below
for why, and for the one place where the review's own prescription was factually wrong.

## Source Files Read

Authority sources for this fix round, read before touching anything:

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-001-quality-review.md` — the specification
  for this round; read in full, including the "Checked and found sound — do not re-litigate" list and
  the empirical-vs-reasoned split.
- `docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md` — the document under
  repair.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-001-implementer-report.md` and
  `task-001-spec-review.md` — what was already established and already checked, so the fix neither
  re-derives nor contradicts them.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-1-contracts-spikes.md`, `### Task 1` — all four
  steps plus the module's write-scope partitioning.
- Root `CLAUDE.md` — read in full; specifically the "cmux Auto-Spawn Handoff" section (the
  no-line-numbers/no-counts policy, the `--help`-is-not-an-enumeration trap, and the "run the binary
  for contract, read the docs for semantics" rule, which is load-bearing for the B1 rewrite).
- `docs/process-improvement-findings/BACKLOG.md` — rows **N67**, **N76**, **N70**, **N72**, and
  **N56** (the in-place-UPDATE precedent cited for the N67 fix).
- `docs/process-improvement-findings/2026-07-28-cmux-capability-usage-matrix.md` — §1 table row for
  `rpc` and **§2.9** in full. This is where the review's B1 fix bullet #4 turned out to be wrong (see
  §"Contradiction with the review").
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` — grepped for its spawn verbs
  to verify I3's premise first-hand.
- `skills/scripts/models/implementer_report.py` — the strict report contract, read before writing
  this report's frontmatter.

The installed binary was the primary authority throughout, per the "binary outranks documents for
contract" rule.

## What I verified before changing anything

The review's B1 rests on `cmux rpc` being a CLI path to arbitrary RPC params. Re-confirmed on the
same binary (`cmux --version` → `cmux 0.64.20 (100) [14e3400b9]`, `cmux ping` → `PONG`):

- `cmux --help` lists `rpc <method> [json-params]` in its Commands block.
- `cmux rpc --help` → exit 0, *"Call a raw v2 method with an optional JSON object for params."*
- `cmux rpc workspace.env '{"workspace":"workspace:2"}'` → exit 0, normal JSON payload.
- `cmux rpc workspace.env '{"workspace":"workspace:2","sp2BogusParam":1}'` → exit 0, **byte-identical
  payload**. Unknown params are silently ignored, so a future probe cannot use an exit code.

The review's B1 is correct. One detail differs from its transcript and is worth recording rather than
smoothing over: the payload carries `window_id`, `window_ref`, `workspace_id` **and**
`workspace_ref`; the review's abbreviated rendering showed only `window_id` and `workspace_ref`. The
doc now quotes what I observed.

## Findings closed, and how

### B1 (BLOCKING) — the axis-3 limit

The invalid chain was: capabilities is names-only → the socket was not driven → *"no CLI path
exists"* → sufficient, because the spawn script is a CLI consumer. That requires CLI and socket to be
disjoint layers, and `cmux rpc` is the counterexample.

**Fixed in five places, not one.** The review pointed at the blockquote; the same unearned bound also
appeared in §"What could not be established" #1, in the Bottom line's item 3, in §Disposition's
"Why not to adopt it here" bullet, and in the N76 row's summary clause. All five now carry the
corrected framing or an explicit pointer to the limit. **The last two were caught on a coherence
re-read after the first commit, not by the original edit pass** — the Disposition bullet was the
worst of them, because it is the sentence that carries the do-not-adopt recommendation and a reader
who goes Bottom line → Disposition and stops would have seen the corrected claim once and the
withdrawn one once, with no pointer. (The mirrors in the *original* implementer report — its
"Could not establish" #1 and Self-Review #4 — are outside this round's write scope and are corrected
here instead; that file is an immutable historical artifact.)

The rewritten limit does four things:

1. **Withdraws the bound explicitly** and shows the `cmux rpc --help` and working-invocation
   transcripts, so a reader sees why.
2. **States what is actually established**, split into halves: no *documented* CLI verb reaches such
   a param (axis 4), and `cmux capabilities` **cannot settle a parameter question at all** — it is
   names-only, so completeness does not even arise. I deliberately did **not** claim `capabilities`
   is demonstrably incomplete; there is no evidence of a missing *method*, and inventing one would
   repeat the defect. What I did do is connect it to the doc's own D2: this binary's self-enumerations
   have four recorded instances of omitting working items, so none should be decisive alone. That is
   the caution the original axis 3 failed to inherit, and the doc now says so in those terms.
3. **Records that an exit code is useless** for the follow-up probe, with the `sp2BogusParam`
   transcript, and routes the residual to "What could not be established" with the method that would
   close it (create + read-back).
4. **Argues the disposition rather than inferring it** — three converging reasons the spawn script
   would not adopt an `rpc`-based env channel even if the param exists.

**Added Axis 4** (new): an exhaustive sweep I ran myself of all 127 top-level commands in
`cmux --help`'s Commands block, running each one's `--help` and grepping for `--env`. **Exactly one
hit: `new-workspace`.** Broadening to any mention of `env` returns 8; the other 7 were read
individually and none is a surface-env channel. This is now the leg that carries the primary-path
conclusion, and it is strictly stronger than the capabilities-name argument it replaces.

I ran this sweep myself rather than importing the reviewer's — in a document whose subject is
evidence provenance, labelling someone else's execution as this document's **a-run** would be the
same class of defect being remediated.

I also stated the sweep's **scope limits honestly, including one that is a genuine residual**: the
sweep covers what `--help` prints, which N72 establishes is a floor, so a *hidden* verb carrying env
to a surface is not excluded. I probed the two hidden verbs this repo currently knows about
(`workspace-group`, `claude-hook`) — both exit 0 with zero `--env` occurrences — which closes the two
known cases without pretending to close the class.

### I1 — N76 omitted the read-back

`grep -o 'SP2_SURF[^ ]*' BACKLOG.md` was empty; clause (1) rested on two absence-of-evidence signals.
Clause (1) now names them **as** absence of evidence, then carries the read-back that converts the
claim into evidence of absence, plus the positive control and the third leg from the re-capture. Pipe
escaped per the file's convention (`SP2_SURF_MARK=\|alpha`).

### I2 — N67 was stale (scope expanded by the controller)

N67 still read "not exercised — probe before building", status `open`, with no pointer to N76 —
telling a future reader to run a probe already run, and leaving two rows with contradictory guidance.
Per the controller's explicit in-scope decision and the file's N56 precedent (in-place UPDATE), N67
now carries:

- a **status-column change**: `open (probe DISCHARGED 2026-07-30 — dispositioned by N76; watch item,
  not a subtraction — see the UPDATE in Notes)`;
- an **`UPDATE 2026-07-30` clause** in Notes stating the probe is discharged, what was confirmed
  (flags half, a-run on both spellings), what was blocked (the subtraction, by topology), the
  explicit "do not schedule as a subtraction, do not close as not-viable", and two sharpenings
  (`--layout` env is creation-time only; `cmux workspace env` is not ground truth).

No other row touched; the diff is 2 lines total.

### I3 — the flip condition was written against an unshipped topology

Confirmed the premise myself: `spawn-handoff-session.sh`'s sole spawn verb is the
`nw=(cmux new-workspace --name … --focus false)` array in `spawn_claude_workspace`. So the old
condition's consequent ("`workspace create` becomes the only spawn path") was **already satisfied**,
and "abandoned" presupposed an adoption that has not happened.

Rewritten in both the doc and the N76 row to condition on the **shipped script's spawn path**, with
both branches spelled out: sprint landed ⇒ not actionable; sprint stalled or reverted ⇒ actionable.
The check is one `grep`, not a judgment about intent. Per this repo's no-line-numbers policy I cite
the construct, not `:471`.

### I4 — the keystone datum had no transcript

Re-captured live. New §"Re-capture" documents a **second probe session with its own refs**
(`workspace:41`, `surface:107`, `surface:108`), deliberately not spliced into the first session's
`workspace:38` / `surface:99–105` transcript. Every step has its command, both streams and its exit
code:

- **Step A** `cmux new-workspace … --env SP2_PROBE=alpha --env SP2_SECOND=beta --env-file <fixture>`
  → exit 0, stdout `OK workspace:41`, stderr = the deprecation hint.
- **Step B** `cmux workspace env workspace:41` → exit 0, all four keys, all four `--env-file`
  semantics reproduced on this spelling.
- **Step C** `cmux new-surface --workspace workspace:41 --type terminal --focus false
  --env SP2_SURF=gamma` → exit 0, `OK surface:108 pane:42 workspace:41`; then `workspace env` again
  showing **`SP2_SURF` absent** — a third leg the first session did not have: the surface-level
  `--env` is not merely unexported, it is **never recorded**.
- **Step D** `cmux send --surface surface:108 'echo "SP2_SURF_MARK=$SP2_SURF|$SP2_PROBE"\n'` → exit 0;
  `cmux read-screen --surface surface:108 --scrollback` → exit 0 → **`SP2_SURF_MARK=|alpha`**.
- **Step E** the same for `surface:107` → `SP2_WS_MARK=alpha|beta|file_plain|file_export`.

Three confounds the review named are now excluded rather than argued away:

- **Wrong-surface read** — the ref returned by `new-surface` is the ref `send` and `read-screen` were
  given, all three visible in the transcript.
- **Local variable expansion** — the scrollback shows the command line echoed with `$SP2_SURF` and
  `$SP2_PROBE` **unexpanded**, proving expansion happened in the surface's shell. A local expansion
  would have produced no `alpha` at all. (This was a live hazard: the doc's original Half-2 rendering
  used local double quotes and, as written, could not have produced its own recorded output. I record
  that plainly in §"Half 2" rather than quietly re-rendering it.)
- **Name mismatch** — `SP2_SURF` is now shown absent from the configured view as well.

`$SP2_PROBE` is named explicitly as the **in-band positive control**, as the review asked; the review
credited the trick and it is kept.

### M1 — the `a-run` label

I took the "exercise it" branch rather than downgrading the label: the re-capture deliberately used
the `cmux new-workspace` spelling, which the first session never exercised. Both spellings are now
genuinely a-run on **both** halves (configured view + inherited process env). The Bottom line now
says which session exercised which.

### M2 — annotations inside code fences

Removed from all four blocks (env-file fixture, reserved-key, Axis 2 read-back, `--layout`). The
fixture is now byte-copyable, with the per-line explanation moved to prose beneath it.

### M3 — "reproduced verbatim"

Fixed the doc half more strongly than the review asked: **H2 and H3 are now byte-complete** (29 and
26 lines, re-captured from the binary) rather than abridged-with-a-marker. H1 keeps its `...` but now
declares itself abridged and names what is elided (the `reconnect`/`disconnect`/`loading` rows, the
trailing paragraph, the Examples block).

The report-side half is **not in this round's write scope** — `task-001-implementer-report.md` is
immutable here by explicit instruction. **The correction is recorded here instead: that report's
"All three are reproduced verbatim in the disposition doc" was false for all three at the time it was
written.** The conclusion it supported is unaffected.

### M4 — the fifth divergence

Added as **D5**: the noun help's "one-time deprecation hint" prints on **every** invocation — 3/3 on
consecutive `cmux list-workspaces` runs, and again on `cmux new-workspace` during the re-capture.
Recorded with its practical consequence: it goes to **stderr**, so `spawn-handoff-session.sh`'s
`OK <ref>` stdout parse is unaffected — and it is a second independent reason the plan's `2>&1`
recipe was departed from.

## Testing

No automated tests: docs-only. Ran the required
`bash tests/ARaymond-installation/verify-symlink-install.sh` → **PASSED, 104 passed, 0 failed,
0 warnings.**

Two mechanical gates run instead of eyeballing:

- **Table integrity** — negative-lookbehind unescaped-pipe count on both edited rows: N67 = 8,
  N76 = 8, matching the header and the N72/N75/N51 controls. The D-table's new D5 row = 6, matching
  D1–D4 and its header.
- **Diff containment** — `git diff --unified=0` on BACKLOG.md shows exactly two hunks, at the N67 and
  N76 lines. N54 and N57 are not in the diff.

Code fences in the doc: 44 markers, balanced.

## Deviations from Plan

The disposition doc's own deviations table now runs to **10 rows**; rows 8–10 are new this round:

- **Row 8** — disposition (a)'s consequent departed from (watch item rather than "the swap"). Raised
  by the Task 1 spec review as an unrecorded eighth deviation; folded into the table so it reaches
  `deviations.md`.
- **Row 9** — a **second live probe session** was run beyond the plan's single `sp2-env` workspace
  (quality-review-directed, for I4/M1).
- **Row 10** — the **127-verb CLI sweep** was added as axis 4 (quality-review-directed, for B1).

`deviations.md` remains outside this task's write scope, so this report and the doc's table are the
only route these take to the deviations register. **Controller action required for rows 8–10.**

## Self-Review Findings

1. **I nearly imported the reviewer's CLI sweep as this document's own evidence.** The review's fix
   bullet says "I re-ran it; see §Empirical", and the path of least resistance was to cite that as
   a-run. In a document whose entire subject is evidence provenance that would have been the same
   defect I was remediating, one level up. I re-ran the sweep myself. Anyone auditing should note the
   127-command sweep is mine, executed this round.
2. **My first instinct on the axis-3 fix was to call `cmux capabilities` incomplete** — it would have
   made a tidier parallel with D2. There is no evidence of a missing *method*, and asserting one
   would have swapped an unearned inference for a fabricated claim. The correct statement is that
   `capabilities` is the **wrong instrument** for a parameter question, which is what the doc says.
3. **The axis-4 scope limit is a real residual and I initially understated it.** My first draft said
   the limits "would only ever add an env channel on the workspace-creation verb," which is false — a
   hidden verb could carry env to a surface. I rewrote it and probed the two known hidden verbs. The
   class remains open and the doc says so.
4. **My first pass fixed the blocking claim in three of its five locations and I called it done.** A
   coherence re-read found it surviving verbatim in §Disposition's "Why not to adopt" bullet and in
   the N76 row's summary clause — including one I had *already* identified as needing scoping in the
   BACKLOG row while leaving its twin in the doc untouched. The lesson is mechanical, not
   attitudinal: after withdrawing a claim, `grep` for the claim's *phrasing* across the artifact
   rather than trusting the review's location list, because a review points at instances it happened
   to read. Both were fixed in a follow-up commit.
5. **The Axis 4 fence I added reintroduced M2 in the very section I added this round.** My first
   draft rendered the sweep with a `<cmds>` placeholder and a `<(cmux --help)` process substitution I
   had not actually used — an un-copyable block reconstructed from memory, in the leg designated as
   the one that carries the conclusion, in a document about transcript fidelity. Replaced with the
   exact bytes.
6. **The `send` payload had a quoting trap I could have walked into.** `cmux send` interprets `\n` as
   Enter, so a `printf` format string containing `\n` would have been mangled mid-payload; and double
   quotes locally would have expanded the probe variables in my own shell. I used a single-quoted
   `echo` payload and verified by **result** (the `alpha` had to appear), not by shape. Had the
   expansion leaked, I would have seen `SP2_SURF_MARK=|` and the probe would have proved nothing —
   which is exactly the confound that made the original datum unfalsifiable.

## Concerns

1. **One residual is now openly unknown where the doc previously implied closure.** Whether
   `cmux rpc surface.create` accepts an undocumented env param has **not** been excluded. I did not
   probe it: it mutates cmux state, the review called it discretionary, and its natural home is the
   capability matrix (outside this round's write scope). The doc states it, states that an exit code
   cannot settle it, and states the method that would. A reader who wants certainty rather than a
   reasoned judgment does not have it.
2. **The disposition now rests partly on a recommendation, not only on measurement.** "The spawn
   script would not adopt an `rpc` channel" is a judgment supported by the capability matrix §2.9, a
   `CLAUDE.md` rule and N72. I characterised §2.9 as *a recorded recommendation in a findings doc,
   not ratified policy*, deliberately — overstating its authority would just swap one unearned
   inference for another.
3. **The first probe session's Half-2 command rendering was inaccurate**, in a way that could not
   have produced its own recorded output. The *result* is now independently reproduced with exact
   bytes, so nothing downstream is affected — but this is a second instance of I4's class sitting
   next to it, and it argues that the underlying discipline gap was "render from memory" rather than
   "one block got skipped."
4. **Cross-session ref coherence, not re-execution.** The first session's `workspace:38–40` /
   `surface:99–105` values remain un-re-verifiable read-only. My new refs (`41`, `107`, `108`)
   continue the monotonic sequence above them, which is corroboration, not proof.

## Contradiction with the review — reported, not reconciled

**The review's B1 fix bullet #4 is factually wrong, and I did not act on it.** It says:

> Route `cmux rpc` to `2026-07-28-cmux-capability-usage-matrix.md` as an unexamined command. The
> matrix exists to prevent exactly this class of gap, and a generic RPC passthrough is the single
> highest-leverage entry it is currently missing.

**It is not missing.** The matrix already carries `rpc` in its §1 table (`| rpc | unexamined | a-run |
Raw v2 method call. §2.9. |`) and drills into it at **§2.9 `rpc` + `capabilities` — the control
plane**, which quotes the same usage line, notes the `cmuxOnly` access mode, and concludes
*"Recommendation: do not build on `rpc`. Its value is as an enumeration tool."*

Two consequences, both of which I acted on deliberately:

- **No matrix edit was made** — it would have duplicated an existing entry, and the matrix is outside
  this task's write scope in any case.
- **§2.9 is now cited from the corrected axis-3 limit** rather than duplicated, and it turned out to
  be the *strongest* of the three reasons the disposition survives: the repo had already recorded a
  recommendation against building on `rpc` before this probe existed.

This is recorded in the doc's §"BACKLOG rows" as "One item deliberately not done", so a re-reviewer
checking the review's checklist finds the discrepancy explained rather than silently unaddressed.

**Nothing else I measured contradicted the review or the prompt.** Every other claim in the review
that I could re-check read-only re-verified: `cmux rpc`'s existence and its silent-ignore behavior,
the deprecation hint firing on every invocation, the shipped script's sole spawn verb, the absent
`SP2_SURF` string in BACKLOG.md, and N67's missing N76 pointer.

## Could not establish

1. **Whether `cmux rpc surface.create` accepts an env param.** Requires a create plus a read-back;
   an exit code is useless (a-run). Deliberately out of scope — see Concerns #1.
2. **Whether any *hidden* CLI verb carries env into an existing workspace's surfaces.** The two
   hidden verbs currently known to this repo were probed and neither does. The class is open and is
   what N72's drift guard exists to close.
3. **Whether the first probe session's un-re-runnable values were exactly as recorded.** Both of the
   read-backs I re-captured reproduced their recorded results, which raises confidence in the rest;
   it does not verify them.

## Status

**DONE_WITH_CONCERNS** — all ten review findings closed, nothing deferred, one live re-capture
performed and cleaned up. The concerns are the honest residuals the fix creates by *removing* an
overclaim (Concerns #1 and #2), plus one contradiction with the review's own prescription reported
above rather than reconciled.
