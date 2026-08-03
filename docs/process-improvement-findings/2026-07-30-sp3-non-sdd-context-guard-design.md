# SP3 — where a context guard for non-SDD sessions should live

**Written 2026-07-31** by the `cmux-spawn-v2` SDD run, Module 1 Task 3.
**Status: DESIGN DOC. Nothing here is scheduled and nothing here is implemented.** The spike's
deliverable is explicitly *"Design doc + BACKLOG row; NO implementation"* (`spec.md` §6,
`spec-distilled.md` §Spikes). Its job is to let a future reader **decide**.
**Files as BACKLOG N80.**

**Read `2026-07-31-context-measurement-architecture-recommendation.md` alongside this.** That
document owns the *measurement* question — what number to read and from where. This one owns the
*scope* question — which sessions get guarded at all, and with what force. They are deliberately
not duplicated: where a fact belongs to both, this doc cites it by section rather than restating it,
because this sprint spent three review rounds chasing one claim across five and six copies.

**Confidence labels** follow this directory's convention: **a-run** = exercised; **a-help** = read
from `--help` or a docstring; **a-file** = read from a source file; **inferred** = reasoned, not
observed. Per `CLAUDE.md`, citations name **constructs**, never line numbers.

---

## The question

> Where should a context guard for non-SDD sessions live? (`$127`/569k unguarded planning session)

---

## Bottom line

**The real decision is advisory versus blocking, and the answer is advisory. The hook-event choice
is downstream of it, and it should not be made until the contract-verification spike that
`2026-07-31-context-measurement-architecture-recommendation.md` §6 already prescribes has run.**

Three reasons, in order of weight:

1. **A non-SDD session has nothing to block *into*.** The SDD gate's HARD block works because it
   fires at a **clean task boundary**, tells the controller that retrying is wrong, and hands it a
   concrete protocol (commit, build a handoff, `/pickup` in a fresh session). None of that exists
   in an unstructured planning or exploration session: there is no task boundary, no successor
   contract, and no "this dispatch is the expensive thing" moment. Blocking a user's own prompt
   mid-thought is a **different product**, not the same product with a wider matcher.
2. **The blocker is measurement, not placement, and it is already being solved generically.** Every
   candidate home below has the same problem — none of the non-`statusLine` hook surfaces carries
   context data, so each would have to parse the transcript exactly as the SDD gate does. The
   sidecar architecture recommended in that document's §3 produces a **session-scoped, SDD-agnostic**
   reading, which is precisely what a non-SDD guard needs. Sequencing SP3 behind it turns SP3 from
   "build a second measurement path" into "add a consumer."
3. **The reusable half already exists and is genuinely SDD-agnostic** (§The probe reuse story), so
   the marginal cost of an advisory observer is small — which is another argument for not spending
   it on a blocking design that would need its own protocol.

---

## The evidence — and an honest problem with it

The spike question cites *"the `$127` planning session"* and *"`$127`/569k unguarded planning
session"*. Those are the words in `spec.md` §3 and §6 (the Spikes table), carried into the module
plan.

**I could not find a primary artifact for either number, and the doc must not pretend otherwise.**
Searched: `grep -rn --include='*.md' -e '\$127'` across the repo returned exactly three hits — the
two spec lines and the plan's own restatement of them, all one-liners with no linked measurement.
**Three at the time of writing, before this doc and its review round existed.** That count is
self-invalidating by construction: every artifact of this spike quotes the figure, so the number
only grows. Re-run the command; do not trust the count recorded here. A matching scan for `569k` /
`569,` / a six-digit `56xxxx` returns nothing beyond the same lines.

A read-only sweep of every `context-observations.log` under `~/projects/claude-custom/` contains
**no ~569k row**:

    find ~/projects/claude-custom/ -name context-observations.log -print0 | xargs -0 /usr/bin/grep -hoE 'tokens=[0-9]{6,}' | sort -t= -k2,2n -u | tail -2

As of that sweep the two largest readings are `tokens=539691` and `tokens=621072`. Substituting
`'tokens=56[0-9]{4}'` returns nothing across the same seven files, while the unrestricted pipeline
returns hundreds of rows and locates `621072` — a positive control proving the pipeline reads the
files rather than silently matching nothing. These logs are live and append-only, so treat every
figure here as point-in-time and re-measure rather than citing.

**Instrument note — this one bites, and it is repo-wide.** `grep` in this environment is not
`/usr/bin/grep`: it is a shell function wrapping `ugrep … --ignore-files`, and `--ignore-files`
makes recursive greps honor `.gitignore`. `.worktrees/` is gitignored, so **every recursive wrapped
`grep` rooted above a worktree silently skips it.** Measured on this same sweep: `find` reaches
seven logs, a recursive wrapped `grep` reaches four, `/usr/bin/grep -r` reaches seven — and the
three it skips are all under `.worktrees/`, which is exactly where this repo executes SDD work. The
truncated four-file form reports `523426`/`621072` as its top two, so a reader running the wrong
instrument would conclude this section is wrong. Run recursive sweeps with `/usr/bin/grep` or
`find … | xargs`.

**And the null is weak coverage, not strong — read it that way.** This doc's own §Why the SDD gate
cannot simply extend establishes that a non-SDD session exits the hook *before any observation row
is written*. So for the very session class the `$127` figure describes, the absence of a row in
these logs is **largely predetermined**: the sweep can rule out a mis-filed SDD row, but it cannot
rule out an unguarded session, because an unguarded session leaves no row by construction. The
conclusion — no primary artifact, derive no threshold from the figure — stands unchanged; its
evidentiary weight is simply lower than a clean null usually implies.

Two consequences a future reader must carry:

- **The figure is `a-file` at one remove — spec-recorded, not instrument-traceable.** It is
  perfectly adequate as *motivation* (a long, expensive, unguarded session happened) and inadequate
  as a *threshold input*. No number in any design should be derived from it.
- **If it came from `claude-ctx-check` or from pre-SP1 `context-probe.py`, it may be inflated.**
  SP1 established that the transcript's top-level `usage` fields double-count multi-iteration turns
  — measured `539,691` against a true `270,851`. The nearest in-repo neighbour to "569k" is exactly
  that poisoned class of reading. **This is a hypothesis about the figure's provenance, not a
  finding**; it cannot be settled without knowing which instrument produced it. It is recorded
  because designing a guard around a possibly-2× number would be the same error twice.

The qualitative claim survives all of this intact: **sessions outside SDD run long and expensive
with no instrument watching them at all.** That is what justifies the spike; the specific dollar and
token figures do not need to be load-bearing and should not be made so.

---

## Why the SDD gate cannot simply extend

Two independent reasons, both **a-file**, both verified in
`skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`.

**1. It is manifest-gated, and the gating happens before anything else.** The hook resolves
`MANIFEST` only when `$GIT_ROOT/.active-feature` exists *and* names a directory containing
`.sdd-session.json`. Immediately after, under the banner
`─── Require manifest mode (legacy non-manifest path removed) ───`, it does:

```
if [ "$MANIFEST_MODE" = false ]; then
  ...
  exit 0
fi
```

A session with no active feature manifest therefore exits **before** dispatch classification, before
the context gate, and before any observation line is written. There is no configuration that makes
the existing gate see a non-SDD session; the early exit is unconditional on that path.

**2. It fires on the implementer new-task path only.** The gate is introduced by the comment
`─── Context-pressure gate (implementer new-task path only) ───` and is structured as
`if [ "$IS_IMPLEMENTER" = true ]`, whose first branch is
`if [ "$MARKED_FIX" = true ]; then ctx_observe_and_log other  # fix dispatch: log only, never gated`.
So the nudge/block ladder is reached only when a dispatch is an implementer **and** is not a marked
fix — the `IS_IMPLEMENTER && ! MARKED_FIX` condition, expressed as a nested branch rather than a
compound test.

**A useful nuance that shapes the design.** Reviewer and ad-hoc dispatches are not blind: they call
`ctx_observe_and_log`, which probes and appends an observation row without nudging or blocking. **So
"observe everywhere, gate narrowly" is already this codebase's established pattern** — an advisory
non-SDD observer is an extension of an existing idea, not a new one. (`ctx_observe_and_log`'s own
comment: *"Probe + log only (no nudge/block)"*.)

---

## The probe reuse story

`skills/subagent-driven-development/scripts/context-probe.py` is reusable essentially as-is
(**a-file**):

- **Stdlib-only.** Its complete import set is `argparse`, `json`, `os`, `sys`, `pathlib.Path`,
  `typing.Optional`. Nothing from `skills/scripts/models/`, no PyYAML, no Pydantic — which is why
  it can run under a bare `python3` in a hook.
- **Transcript-driven and SDD-agnostic.** `resolve_transcript(args)` implements the priority
  `--transcript` → `--session-id` → `$CLAUDE_CODE_SESSION_ID`, with `--session-id` globbing
  `~/.claude/projects/*/<id>.jsonl`. There is no reference anywhere in the file to `.active-feature`,
  `.sdd-session.json`, a manifest, a reports directory, or any other SDD artifact.
- **A clean CLI contract.** Exit 0 prints the token total (bare int, or JSON with `--json`); exit 1
  means no transcript resolvable or no usage block found.

So the sensor half of a non-SDD guard is **free**. What is not free is everything around it: which
event supplies the transcript path, what threshold applies to a session with no task structure, and
what the guard is allowed to say.

**Caveat inherited from SP1, and it is the important one.** The probe reads
`message.usage.iterations` — a shape the documentation itself calls internal and *"not a stable
contract."* A second consumer doubles the exposure to that instability. The **version canary**
recommended in `2026-07-31-context-measurement-architecture-recommendation.md` §3 is therefore a
prerequisite for widening the probe's blast radius, not a nicety — and that document already flags
it as separable and highest-value.

---

## Candidate homes

### 1. A `UserPromptSubmit` / `PreToolUse` hook independent of SDD artifacts

A hook registered on a session-wide event that reads the transcript and warns.

- **`PreToolUse` carries no context data — established, do not re-litigate.** That document's §2
  table records it, and the SDD gate's own design corroborates it: the hook reads
  `.transcript_path` from the payload precisely because nothing better is offered. So this candidate
  is a *transcript-parsing* candidate, whichever event it uses.
- **Whether `UserPromptSubmit` carries `transcript_path` is a separate, unverified question.** §2's
  table addresses context data, not the field inventory, and §7 labels that table
  documentation-sourced rather than first-hand. **I did not verify it.** A builder must dump a real
  payload — which is exactly the contract-verification spike §6 already prescribes. Do not assume
  the field is there.
- `UserPromptSubmit` is **already a registered event** on this machine
  (`jq -r '.hooks | keys[]' ~/.claude/settings.json` → `PreToolUse`, `SessionStart`, `Stop`,
  `UserPromptSubmit`), carrying two unrelated commands. So adding one is additive, not novel —
  but the registration is shared, which is a coordination cost, not a blocker.
- **Baseline status, verified rather than assumed:** `tests/ARaymond-hook-baseline/check-hooks.sh`
  pins a **hardcoded `HOOKS=(…)` array** of seven paths. A *new* hook does **not** enter the
  baseline automatically; it enters only if it is added to that array — at which point every future
  edit owes a same-change `check-hooks.sh --capture` plus a committed `baseline.txt`. Adding it is
  the right call for an enforcement-bearing script; the point is that it is a deliberate step, not
  an automatic consequence.

**Assessment: the right home *eventually*, and the wrong thing to build first.** Its value is
bounded by the measurement question, which is being answered elsewhere.

### 2. A stop-hook advisory

Extend or mirror `skills/subagent-driven-development/scripts/sdd-stop-hook.sh`.

What that hook actually does (**a-file**, read in full):

- It reads **only `.cwd`** from its payload (`jq -r '.cwd // ""'`). It does not read
  `transcript_path` today — so a context reading would need a field this hook has never used, and
  the same unverified-payload caveat applies.
- It is **SDD-gated three times over**: `exit 0` unless the reports directory exists, unless a
  deviations file exists, and unless a plan file is found. So it is not a non-SDD surface as written.
- It emits `systemMessage`, and says why in a code comment:
  *"Use systemMessage for Stop hooks (hookSpecificOutput not supported for Stop events)."*
- Its contract is explicit at the top: *"Exit codes: 0 — Always (advisory injection, never blocks)."*

**The decisive property is timing.** A Stop hook fires **after** the turn has completed — after the
tokens are spent. It can report, it cannot prevent. A Stop-based guard is therefore an **observer**,
and calling it a "guard" would overstate it.

Note also that `2026-07-31-context-measurement-architecture-recommendation.md` §4 explicitly
declines a `Stop`/`PostToolUse` **second gate** in an SDD session, on two grounds: those surfaces
have no context data either, and a second gate is a second place to maintain.

**How this doc differs from §4, said plainly so no reader thinks it was missed.** §4 argues against
adding a *second* gate to an *already-guarded* session. SP3 asks about a *first* observer in an
*unguarded* one — a different question. Of §4's two objections:

- *"inherits the same measurement problem"* — **weakened but not eliminated.** A non-SDD observer on
  the transcript rung inherits exactly that problem. It is only retired once the sidecar rung exists.
- *"a second place to maintain"* — **survives fully, and is the stronger objection.** It is the
  main argument for building one advisory path with one shared reader rather than several.

**Assessment: honest fit for the recommended product** (advisory, post-turn), but the *SDD* stop
hook is the wrong vehicle — it is gated on SDD artifacts by construction and would have to be
loosened or duplicated.

### 3. A `claude-usage-pace`-based session monitor

- **The binary exists**: `~/.claude/bin/claude-usage-pace`, executable, dated 2026-07-02.
- **It measures a different quantity.** Its docstring and `--help` (**a-help — I did not run it**)
  describe a *"burn-rate & pacing report for Claude Code subscription limits"*: it runs
  `claude -p "/usage"`, parses **three limit windows** (session, weekly all-models, weekly premium)
  and computes pacing. That is **quota consumption**, not **context-window occupancy** — the thing
  the SDD gate exists to bound. They are correlated, not interchangeable, and a guard keyed on the
  wrong one will fire at the wrong times.
- **Polling it costs the allotment it reports.** Its own docstring says so: *"each run spawns a
  headless `claude -p '/usage'` turn, so measuring consumes a (tiny) amount of the very allotment it
  reports."* A per-prompt monitor is therefore self-defeating in a way the transcript probe is not.
- This repo already treats it as a *precondition* rather than a continuous monitor: the spawn
  script's quota gate calls it once, bounded by `SUPERPOWERS_CMUX_QUOTA_TIMEOUT`, fail-open by
  contract. That is the shape it suits.

**Assessment: reject as the context guard.** It answers a genuinely useful and genuinely different
question. If a *quota* advisory is wanted, that is its own item — do not conflate it with context.

---

## Recommendation

**An advisory, SDD-independent context observer — sequenced after the contract-verification spike,
built on the sidecar rung when available and the probe otherwise. No blocking behavior for non-SDD
sessions.**

Concretely, in order:

1. **Nothing now.** This sprint ships no implementation for SP3 by design.
2. **The version canary first** (that document's §6 already calls it separable and highest-value).
   It protects the probe fix already shipped and is a prerequisite for a second probe consumer.
3. **The contract-verification spike** — dump a real payload for each candidate event and record the
   field inventory first-hand, Task 0 style. This settles the one thing SP3 could not: whether
   `UserPromptSubmit` even carries `transcript_path`. **This repo has filed two BACKLOG rows on
   false premises and nearly a third; an unverified field inventory is exactly that shape.**
4. **Then** an advisory observer, reusing one shared reader with the SDD gate rather than forking a
   second measurement path.

**Explicitly not recommended:** a blocking non-SDD gate; a `claude-usage-pace`-derived context
signal; any threshold derived from the `$127`/569k figures.

### Rollout risk

- **False positives are expensive in a way they are not in SDD.** The SDD gate speaks to a
  controller at a task boundary. A non-SDD observer speaks to a **human mid-thought**. A noisy
  advisory gets muted, and a muted guard is worse than none because it looks like coverage.
  Mitigations: fire once per session per tier, not per prompt; make it silenceable per session.
- **A second probe consumer doubles exposure to an undocumented shape.** Hence the canary
  prerequisite. The failure mode to design against is silent mis-measurement, not a crash — this
  codebase's own rule that *"a silently-inert gate is not allowed"* applies with equal force to an
  advisory one.
- **One-turn lag is inherent and fails open.** Any transcript-derived reading reflects the previous
  completed turn, so it **understates** current context, most exactly when a large tool result has
  just landed. Tolerable only with threshold headroom — and on a 200k window that headroom does not
  exist, which is the same argument for percentage-based thresholds made in §3 of the other document.
- **Shared `settings.json` and shared events.** `UserPromptSubmit` and `Stop` already carry
  unrelated commands from other tools. Registration must be read-merge-validate; a replacement would
  silently break a teammate's tooling.
- **Baseline obligation, conditional.** A new hook does not enter
  `tests/ARaymond-hook-baseline/check-hooks.sh`'s `HOOKS=(…)` array automatically. If the observer
  is added to it — appropriate for anything enforcement-bearing — every subsequent edit owes a
  same-change `--capture` and committed `baseline.txt`. If any *existing* baselined hook is modified,
  that obligation applies immediately.
- **Where the guidance would live.** Any controller- or user-facing protocol text belongs in
  `skills/subagent-driven-development/references/` (precedent:
  `references/context-handoff-protocol.md`), **never** in `SKILL.md`, which is at its word ceiling —
  a binding Contract Constraint of this sprint's plan.

## What could not be established

- **The provenance of `$127`/569k.** No primary artifact found; see §The evidence for the exact
  commands and their results.
- **Whether `UserPromptSubmit` carries `transcript_path`.** Not verified; routed to the
  contract-verification spike. No recommendation here rests on it.
- **`claude-usage-pace`'s runtime behavior.** Read from `--help` and its module docstring only
  (**a-help**); deliberately not executed, since each run consumes the allotment it measures. The
  rejection rests on the *quantity* it reports, which its own documentation states plainly, not on
  observed behavior.
- **Whether a non-SDD guard is wanted at all.** One session motivates this spike. Nothing here
  measures how often unguarded sessions run long, and a frequency measurement would be a cheap input
  to the decision.

---

## BACKLOG row

Filed as **N80**, appended verbatim to `docs/process-improvement-findings/BACKLOG.md`. The id was
allocated at execution time against **both** `main` and this branch — `main`'s highest is N78 and
this branch adds N79, so N80/N81 are the first pair free on both. Enumerating this branch alone is
what produced the earlier N76 collision (`deviations.md`, "Cross-branch BACKLOG id collision").

```
| N80 | Context guard for non-SDD sessions — advisory observer, sequenced behind the measurement spike | SP3 design spike, `cmux-spawn-v2` Module 1 Task 3, 2026-07-31 | quality, friction | M | open (blocked on the contract-verification spike) | **Design doc: `2026-07-30-sp3-non-sdd-context-guard-design.md`. Spike deliverable was design-only; nothing implemented.** **Recommendation: an ADVISORY, SDD-independent context observer — never a blocking gate for non-SDD sessions.** A non-SDD session has nothing to block into: the SDD HARD block works only because it fires at a clean task boundary with a successor protocol (commit, handoff, `/pickup`), none of which exists in an unstructured session. **Why the existing gate cannot extend (a-file):** `sdd-pre-dispatch-hook.sh` resolves its manifest from `.active-feature` + `.sdd-session.json` and then `exit 0`s under `Require manifest mode` before dispatch classification, so a non-SDD session never reaches the gate at all; and the gate itself is `Context-pressure gate (implementer new-task path only)` — `IS_IMPLEMENTER` true with the `MARKED_FIX` branch diverted to `ctx_observe_and_log other  # fix dispatch: log only, never gated`. Reviewer and ad-hoc dispatches already observe-without-gating, so **observe everywhere, gate narrowly** is an existing pattern, not a new one. **Probe reuse is free:** `context-probe.py` is stdlib-only (`argparse`, `json`, `os`, `sys`, `pathlib`, `typing`) and SDD-agnostic — `resolve_transcript` takes `--transcript` / `--session-id` / `$CLAUDE_CODE_SESSION_ID` with zero references to any SDD artifact. **Candidates:** `UserPromptSubmit`/`PreToolUse` hook = right home eventually, but `PreToolUse` carries no context data and whether `UserPromptSubmit` carries `transcript_path` is UNVERIFIED — route to the contract-verification spike; stop-hook advisory = honest fit for an advisory product but fires AFTER the turn (observer, not guard) and `sdd-stop-hook.sh` reads only `.cwd`, emits `systemMessage` because `hookSpecificOutput` is unsupported for Stop events, and is SDD-gated three ways; `claude-usage-pace` = **rejected**, it reports subscription QUOTA windows (session/weekly), not context occupancy, and each run spawns a headless `claude -p /usage` turn so polling consumes the allotment it measures (a-help, not executed). **Sequencing: nothing now → version canary first → contract-verification spike → then the observer**, reusing ONE shared reader with the SDD gate rather than forking a second measurement path. Depends on `2026-07-31-context-measurement-architecture-recommendation.md` §3/§6 — that doc owns the measurement question, this one owns scope and force; §4's "do not add a second gate" is about a second gate in a GUARDED session, and of its two objections the maintenance one survives fully here. **Evidence caveat — important:** the motivating `$127`/569k figures are spec-recorded with NO primary artifact. Swept every `context-observations.log` under `~/projects/claude-custom/` with `/usr/bin/grep -rhoE 'tokens=[0-9]{6,}' --include=context-observations.log ~/projects/claude-custom/` (sort the output; as of that sweep the two largest are 539691 and 621072): **no ~569k row exists**, and a `tokens=56[0-9]{4}` probe returns nothing against a positive control that returns hundreds of rows. **Method gotcha, repo-wide — the reason this needed re-measuring:** `grep` here is a shell function wrapping `ugrep --ignore-files`, which honors `.gitignore`; `.worktrees/` is gitignored, so a recursive WRAPPED `grep` reaches only 4 of the 7 logs and reports 523426/621072 instead. Use `/usr/bin/grep` or a `find`-plus-`xargs` pipeline for recursive sweeps — `.worktrees/` is exactly where this repo executes SDD work. **The null is weak coverage, not strong:** a non-SDD session exits the hook before any observation row is written, so the absence of a row is largely predetermined for precisely the session class this figure describes. And if produced by a pre-SP1 instrument the figure may be inflated up to ~2x by the multi-iteration double-count. Adequate as motivation, NOT as a threshold input — derive no number from it. **Risks:** false positives interrupt a human mid-thought (fire once per session per tier, make it silenceable); a second probe consumer doubles exposure to the undocumented version-unstable `iterations` shape, so the canary is a prerequisite; one-turn lag understates context and fails open; `UserPromptSubmit`/`Stop` already carry unrelated commands so registration must be read-merge-validate. **Baseline:** `check-hooks.sh` pins a hardcoded `HOOKS=(…)` array, so a NEW hook does not enter the baseline automatically — adding it there is a deliberate step that then obliges a same-change `--capture` on every later edit. Any protocol text goes in `subagent-driven-development/references/`, never `SKILL.md` (word ceiling). |
```
