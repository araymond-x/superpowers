<!--
PROVENANCE — added when this file was captured into the repo; everything below the
`---` rule is the original document, byte-for-byte unmodified.

  Author   : SDD/audit session `2b988cec-6c4c-435c-a76f-f75c636edb84` (the BACKLOG N60
             cmux capability audit), written 2026-07-29.
  Found at : ~/.claude-codex-handoff/bundles/2026-07-29T02-01-24Z-claude-codex-handoff/
             artifacts/included/cmux-mode-option-surface.md
  Captured : 2026-07-29, unchanged apart from this header.

WHY IT MOVED. It was written into a /handoff bundle, which is the correct place for an
artifact that CARRIES work to another repo but the wrong place for the durable record of
a finding: `~/.claude-codex-handoff/` is not version-controlled, and
`claude-codex-handoff prune` deletes bundles. The analysis is reproduced here so it
survives; the bundle copy stays where it is for the toolkit session that will consume it.

SCOPE. These are RECOMMENDATIONS addressed to the `claude-codex-handoff` toolkit repo, not
to this fork. Nothing in either repo's `src/` was changed by their author. Read the
confidence labels the document defines (`a-run` / `a-file` / `a-help` / `inferred`) — they
are load-bearing, and one step in the trust-inheritance argument is explicitly `inferred`
and flagged as needing a two-minute test before anything relies on it.
-->

# The cmux mode's option surface — what to add, and at which layer

**Added 2026-07-29** in answer to: *"does it make sense to contemplate new arguments to
configure/setup the cmux-based handoff process? What options or variables would the cmux integration
need to operate seamlessly as a full round trip or one way?"*

This bundle's `next_action` says *"…to see the shape before designing the mode token."* This document
is input to that design step. **Recommendations only — nothing in `src/` was changed.**

Facts below were read from the live contract (`claude-codex-handoff describe`, which this repo's
`CLAUDE.md` names as the single source of truth) and from `src/`. Labels: `a-run` exercised this
session, `a-file` read from a live file.

---

## 1. Answer up front

**Yes — but most of it does not belong in the command's argument tokens.**

The instinct is to add `cmux-cdx` beside `auto-cdx`. That is the smallest change and it is the wrong
shape for everything except the operator's one-word intent. The reason is visible in the current hint:

```
argument-hint: "[code|plan] [focus] [codex|auto-cdx|auto-cdx-noconfirm]"
```

`auto-cdx-noconfirm` is already a **compound token encoding two orthogonal dials** (transport=auto,
confirm=skip). Adding a transport axis multiplies that set rather than extending it —
`cmux-cdx`, `cmux-cdx-noconfirm`, `cmux-claude`… The taxonomy is already strained, and this bundle
independently flags the same disease in `--review-subject code|plan` (a two-option split that caused
a real misfire). **Do not grow the token soup a third time.**

Split by layer instead:

| Layer | Holds | Why there |
|---|---|---|
| **Command / skill token** | operator's one-word intent | terse, per-invocation, human-typed |
| **Backend flag** (`describe` = SSOT) | the contract | introspected from argparse, testable, already how `dispatch` works |
| **Env var** | site/machine config | shouldn't be typed every time; kill switch |

---

## 2. The structural finding: half of what you asked about already exists, the other half doesn't exist here at all

**Round trip is built.** `describe` labels the `dispatch` profile verbatim as *"Automated
non-interactive review **round trip** (auto-cdx path)"*, and it already owns
`--reviewer {codex|claude|jules}`, `--model`, `--reasoning-effort`, `--timeout`, `--ignore-rules`
(`a-file`). The return leg exists too — `claude-codex-handoff findings` attaches the report, and
`/pickup` keys on `Findings: attached` to present results instead of resuming. **The loop already
closes.** A cmux transport is a new *way to run the reviewer*, not a new loop.

> Consequence: `--transport` belongs on `dispatch`. That is a one-word addition to an existing,
> tested verb whose contract `describe` picks up automatically — not a new command surface.

**One way does not exist in this toolkit.** Measured: `grep -rniE 'cmux|new-workspace|spawn' src/`
returns **nothing** (`a-file`). The only one-way cmux spawn on this machine is
`spawn-handoff-session.sh` in the *superpowers* fork, which spawns a successor to continue work and
never returns. So:

| | Round trip (review) | One way (work continuation) |
|---|---|---|
| Bundle type | `review` | `work` |
| Verb | `dispatch` — **exists** | **none in this repo** |
| Ends when | findings attached | successor confirmed started |
| Lives in | this toolkit | superpowers `spawn-handoff-session.sh` |

**This is the real design question, and it is bigger than an argument list:** two repos are about to
contain two implementations of the same cmux spawn mechanic. See §6.

---

## 3. Backend flags — the substantive additions

### On `dispatch` (round trip)

| Flag | Values / default | Why it must exist |
|---|---|---|
| `--transport` | `subprocess` (default) \| `cmux` | The core dial. Default preserves today's behavior exactly. |
| `--placement` | `surface` (default) \| `workspace` | The operator's model is repo = workspace, session = **top tab**. `surface` is the default; `workspace` stays available (recipe §2 keeps those commands as a fallback). |
| `--focus` | `false` (default) \| `true` | Verified `a-run` that `--focus false` holds on `new-surface`; an automated spawn must not steal attention. |
| `--tab-label` | text, default derived from bundle id | How the incremented session numbering is expressed — `cmux rename-tab` is the only command that names a tab (`a-run`). |
| `--ready-timeout` | seconds, default ~90 | **Distinct from `--timeout`.** See the warning below. |
| `--on-prompt` | `escalate` (default) \| `fail` | There is deliberately **no `answer` value**. See §5. |
| `--keep-tab` | `on-failure` (default) \| `always` \| `never` | Preserving the failed tab is the whole reason to launch with `send` rather than `respawn-pane`. |

> **⚠ `--ready-timeout` and `--timeout` are different clocks and conflating them is a bug.**
> `--timeout` (default 900s, `a-file`) bounds *the review*. Readiness bounds *the launch* — cold
> `claude`/`codex` start + skill load + `/pickup` ingestion, on the order of seconds. One number
> cannot serve both: sized for the review, a hung launch burns 15 minutes before anyone notices;
> sized for the launch, every real review is killed. They also have **different failure meanings** —
> ready-timeout means *never started*, timeout means *started and did not finish*. Those route
> differently.

### A new verb for one way

`dispatch` is review-shaped (it waits, it expects findings). A one-way spawn is a different verb:

```
claude-codex-handoff spawn <bundle-id> [--transport cmux] [--placement surface]
                                       [--ready-timeout <s>] [--max-hops <n>] [--dry-run]
```

Sharing `--transport`/`--placement`/`--ready-timeout` with `dispatch` keeps one vocabulary.
`--dry-run` is worth copying from `spawn-handoff-session.sh` — it validates every precondition and
composes the command without spawning, and it is how that script's launch composition is testable at
all.

> **`--max-hops` is not optional, and this toolkit has no equivalent today.** Verified: `grep -rniE
> 'hop|max_hops|recursion|depth' src/bin/claude-codex-handoff` returns **nothing** (`a-file`). A
> one-way spawn whose successor can itself spawn is an unbounded chain. superpowers learned this the
> expensive way — its `SUPERPOWERS_CMUX_MAX_HOPS` guard **failed OPEN on a malformed value** (a
> non-numeric operand made `[ "$HOPS" -ge "$MAX_HOPS" ]` error, the branch was not taken, and
> execution fell through and spawned). **A guard whose input is malformed must refuse, not proceed.**

---

## 4. Env vars — site config, and the naming precedent

The toolkit already reads exactly one: **`HANDOFF_DISPATCH_POLL_INTERVAL`** (`a-file`). That sets the
prefix convention — use `HANDOFF_*`, not `SUPERPOWERS_CMUX_*` (different tool, different repo; sharing
a prefix would imply a coupling that does not exist).

| Var | Default | Purpose |
|---|---|---|
| `HANDOFF_CMUX_ENABLED` | `1` | **Kill switch.** Honest opt-out, so nobody has to abuse a numeric guard as one — superpowers' N55 records exactly that: `MAX_HOPS=0` works as a kill switch but **logs the wrong reason**. |
| `HANDOFF_CMUX_TRANSPORT` | unset | Default transport when no token is given. |
| `HANDOFF_CMUX_PLACEMENT` | `surface` | Site default topology. |
| `HANDOFF_CMUX_READY_TIMEOUT` | `90` | Launch clock. |
| `HANDOFF_CMUX_MAX_HOPS` | `3` | One-way chain bound. |

**Validation contract for all of them:** invalid value ⇒ warn on stderr and revert to the default;
never fall through, never exit. That is the fail-safe pattern superpowers arrived at for
`_QUOTA_MIN_PCT` and `_QUOTA_TIMEOUT` — and the direction its `MAX_HOPS` originally got wrong.

---

## 5. Command tokens — add exactly one

```
argument-hint: "[code|plan] [focus] [codex|auto-cdx|auto-cdx-noconfirm] [cmux]"
```

**`cmux` as a standalone modifier**, not a new compound. It sets `transport=cmux` and implies
`mode=auto`; it composes with the existing tokens instead of multiplying them, so
`/handoff-review code cmux` and `/handoff-review code auto-cdx-noconfirm cmux` both parse without
new combinations. Longest-match-first parsing already exists in step 2 for the `auto-cdx` /
`auto-cdx-noconfirm` prefix case, so a bare `cmux` slots in without touching that logic.

**There is deliberately no token to auto-answer a prompt, and `--on-prompt` has no `answer` value.**
The operator's approval *is* what this transport adds over headless `auto-cdx`; automating it away
deletes the reason the mode exists and turns a safety gate into a rubber stamp. A future session will
be tempted to add `--on-prompt answer` or a `send y` — the answer is no. Escalate via `cmux notify` +
`cmux set-status` and stop.

---

## 6. The SSOT question, which is bigger than the option surface

After this ships, **two repos will implement the same cmux spawn**: `dispatch --transport cmux` /
`spawn` here, and `spawn_claude_workspace()` in superpowers' `spawn-handoff-session.sh`. They already
need the same pieces — surface creation and ref parsing, `rename-tab`, launch via `send`, a
`wait-for` readiness handshake, prompt/stall escalation, hop bounding, an exit ladder.

Worth noting: superpowers' spawn core was **deliberately built extraction-ready** for a second
consumer (its Decision 15 — the function is documented as holding "pure mechanics: no SDD *sequencing*
policy"). It was written anticipating codex parity; a second *toolkit* is the same shape of consumer.

Three options, with a recommendation:

1. **Duplicate.** Cheapest now. Guarantees drift — and the drift will be in the *guards*, which is
   where drift is most expensive.
2. **This toolkit owns the generic spawn; superpowers calls it.** Architecturally right — this is the
   portable, installable, cross-tool toolkit with a tested CLI contract and a `describe` SSOT. Cost: a
   new dependency direction, and superpowers' spawn carries SDD-specific policy (hop reservation,
   quota refusal, `.active-feature` resolution) that must stay on its side of the seam.
3. **Extract a third shared thing.** Most correct, most overhead, and premature at two consumers.

**Recommend (2), sequenced after both work independently.** Do not attempt the extraction as part of
this feature — build the cmux transport here, let both run, then move the seam once the duplication is
concrete rather than predicted. Note the asymmetry that makes (2) viable: the *mechanics* are shared,
the *policy* is not.

---

## 7. Minimum viable vs. complete

**Ship first** — enough for a working, honest round trip:

- `dispatch --transport {subprocess|cmux}`
- `--ready-timeout` (separate clock)
- `--on-prompt escalate` behavior
- `HANDOFF_CMUX_ENABLED` kill switch
- the `cmux` command token
- `--placement surface` as the default (the operator's model), workspace retained as fallback

**Defer until asked** — `--tab-label`, `--keep-tab`, `--focus`, `HANDOFF_CMUX_PLACEMENT`,
`HANDOFF_CMUX_TRANSPORT`. Each is a refinement of a default that is already correct.

**Do not build until the one-way path is actually wanted** — the `spawn` verb, `--max-hops`,
`HANDOFF_CMUX_MAX_HOPS`. But if `spawn` is built, `--max-hops` ships **with it**, not after.

**Never build** — any form of automatic prompt answering.
