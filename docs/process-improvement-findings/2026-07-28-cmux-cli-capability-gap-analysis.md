# cmux CLI Capability Gap Analysis

**Date:** 2026-07-28
**Trigger:** User asked whether our cmux integration (N43(D), `spawn-handoff-session.sh`) had limited
itself to the CLI surface exposed by the vendored cmux skills, and whether the wider cmux community
had solved problems we had filed as hard or unsolvable.
**External source cross-referenced:** <https://github.com/yigitkonur/awesome-cmux> (README, "170+
community projects").
**Verification baseline:** `cmux 0.64.20 (100) [14e3400b9]` — the installed binary, per this fork's
own rule that `cmux <cmd> --help` outranks the web docs, the vendored skills, and the raw-GitHub
URLs (CLAUDE.md, "cmux documentation, versions, and which source wins").

**Status:** the analysis body below is captured **verbatim** as delivered in session
`Superpowers Backlog Review` (2026-07-28). The **Addendum** that follows it is new material — the
empirical `wait-for` probe run after the analysis was delivered, which settles the N56 disposition.

---

## Analysis (verbatim)

I read the README and then verified every CLI claim against your installed binary (`cmux 0.64.20 (100) [14e3400b9]`), per CLAUDE.md's own rule that `--help` outranks all docs.

### First: a correction that changes our roadmap

**`cmux read-screen` exists.** It is in `cmux --help` on your installed build, listed directly above `send`:

```
read-screen [--workspace ...] [--surface ...] [--window ...] [--scrollback] [--lines <n>]
    Read terminal text from a surface as plain text.
```

BACKLOG **N56** states: *"It cannot be fixed by trying harder, because cmux has no surface-read: `cmux --help` exposes `send`, `send-key`, `send-panel`, `send-key-panel` — write-only. There is **no** capture/read/screen command."* That premise is false against 0.64.20. So is the corollary in **N57** that a surface-based topology can't know when a shell is ready. I repeated N56's framing in my review an hour ago; it was wrong, and it was wrong in the direction that made us stop looking.

There's more than `read-screen`. Verified present, all absent from the vendored `cmux/SKILL.md`:

| Command | What it gives us |
|---|---|
| `read-screen [--scrollback] [--lines n]` | Read a surface's text |
| `capture-pane` | tmux-compat alias of the same |
| `pipe-pane --command <sh>` | **Stream** pane text into a shell command |
| `wait-for [-S\|--signal] <name> [--timeout <s>]` | **Named sync token** — block until signalled |
| `events --name --category --after --cursor-file --reconnect` | **Structured NDJSON event stream** with durable cursor |
| `set-status` / `set-progress` / `log` / `todo` | Sidebar telemetry: pills, progress bar, activity feed |
| `hooks setup \| <agent> install` | Native agent lifecycle hooks |
| `surface resume`, `restore-session`, `agent-hibernation` | Session persistence |
| `respawn-pane --command <cmd>` | Send a command to an **existing** surface |
| `rpc <method>`, `capabilities` | Full JSON-RPC control plane |
| `find-window --content <query>` | Search across surfaces by content |

### Direct answer to your question: yes, we limited ourselves — measurably

Your hypothesis is confirmed. The vendored `cmux/SKILL.md` is 84 lines. I probed it for 13 of the commands above: **0 hits for all 13.** Across the whole vendored set of four skills, exactly one appears — `read-screen`, once, at `cmux-workspace/references/commands.md:66`, in a *different* skill's reference file that the spawn feature's design never consulted.

> **Insight**
>
> This is a specific failure mode worth naming, because your fork already has a rule that would have caught it. CLAUDE.md says: *"for flag-level facts, `cmux <cmd> --help` on the installed binary OUTRANKS all three [doc sources]."* That rule was written on 2026-07-27 — the day N56 was filed — and N56 was nonetheless reasoned from the vendored skill's surface rather than the binary's. The rule existed; the capability *enumeration* never happened. A vendored skill is a curated teaching document, not an API manifest, and treating one as the other silently defines the ceiling of what you'll ever build.

### Mining: ecosystem patterns mapped to our open problems

#### 1. N56 (open-loop spawn) → solved three different ways, best one is `wait-for`

The README's *State Detection* section documents the community's approaches: turn-end detection by screen pattern-matching, heartbeat polling at 3–4s, and full state machines (`niaeee/cmux_skill`, an 802-line IDLE/STALL/ERROR machine). Any of those beats what we have.

But `wait-for` is strictly better than all of them and it's first-party:

```
cmux wait-for -S sdd-hop-<spawn-uuid>          # child signals, once /pickup runs
cmux wait-for   sdd-hop-<spawn-uuid> --timeout 120   # parent blocks, bounded
```

That converts the spawn from open-loop to **closed-loop with a bounded wait** — no polling, no screen-scraping, and critically **no correlation problem**, which was the unsolved half of the transcript-file idea I floated earlier. The token *is* the correlation key, and we already generate exactly the right one (`$SPAWN_ID`, `:359`). It also gives the exit ladder the rung N56 says it lacks: `spawned-but-never-started`.

The directory-trust modal N56 describes as the concrete failure is separately detectable with `read-screen` pattern-matching — belt and braces.

#### 2. N57 (topology) → the blocker is smaller than filed

N57 says surfaces are blocked because `new-surface` has no `--command`, forcing a `send` that races shell readiness. True, but `respawn-pane --surface <ref> --command <cmd>` sends a command to an existing surface, and `wait-for` removes the race outright. The `--group` middle path on `new-workspace` is confirmed in `--help`; there is still **no** `list-workspace-groups`, so N57's "how groups are created/referenced is unverified" stands.

#### 3. O2 (nobody reads the flight recorders) → sidebar telemetry, near-zero cost

The README's *Progress Bars* dimension lists "context-window fill percentage" as an established driver. **We already compute that number** — `context-probe.py` runs in the pre-dispatch hook on every dispatch. Two lines in the hook give a live gauge:

```
cmux set-progress <ctx_tokens / CTX_HARD> --label "ctx"
cmux set-status task "N/M" ; cmux set-status hop "$SP_HOP/$MAX_HOPS"
```

That turns the 300k/400k thresholds from invisible folklore into something you watch in the sidebar — and it's the fastest possible answer to "why did it block?"

#### 4. Someone has already built our feature

`owizdom/context-brdige-for-cmux` — the README describes it as *"cold-start context injection via briefing handoff."* That is N43(D) by another name. Worth reading before we extend ours. Likewise `hummer98/using-cmux` (billed as the complete orchestrator reference) and `cmux-agent-toolkit`, whose *"barrier-style sync primitives"* almost certainly means `wait-for`.

#### 5. Native hooks we aren't using

`cmux hooks` manages agent lifecycle integrations, and notably: *"Claude Code hooks are injected automatically by the cmux Claude wrapper."* Claude Code is absent from the agent list **because it's handled automatically** — meaning there may already be a cmux-side lifecycle channel active in your sessions that our integration neither reads nor coordinates with. Worth a look before we build more inference on top of screen state.

### Confidence, stated plainly

- **CLI facts above: verified** against your installed 0.64.20 binary this session.
- **Community-repo claims: secondhand.** I read the README's summary via WebFetch, not the individual repos. Star counts, tool counts, and behavior descriptions are the README's, unverified.
- **`wait-for` cross-workspace semantics: not empirically probed.** It's a socket-side named token so parent/child signalling across workspaces should work, but that deserves a 5-minute probe before anything is designed on it.

### What I'd do next

1. **Probe `wait-for` across two workspaces** (5 min). If it works, N56 stops being an M-sized research problem and becomes an S-sized wiring change.
2. **Rewrite N56 and amend N57** — both carry a false premise right now, and N56's says the gap is structurally unfixable. That's the most expensive kind of stale backlog entry: one that tells future sessions to stop thinking.
3. **Add a new row: "enumerate the cmux CLI surface against our integration"** — the gap this session found is a *category* of missed capability, not one command.
4. **Ship the sidebar telemetry** — smallest change, most immediate value, no design needed.

---

## Addendum — `wait-for` probe results (run 2026-07-28, after the analysis above)

Step 1 of "What I'd do next" was executed. The analysis body above lists cross-workspace semantics
as **not probed**; that caveat is now discharged. All three tests were run against the installed
`cmux 0.64.20`, from a session inside workspace `5BC6A8A3-28EE-4B50-885E-53C729464DA8`.

### Test 1 — positive control (same context)

```
( cmux wait-for "$TOK" --timeout 10 ) &     # waiter
cmux wait-for -S "$TOK"                     # signaller
```

Result: signaller printed `OK`, exit 0. Waiter unblocked, printed `OK`, **exit 0**.

### Test 1b — negative control (never signalled)

```
time cmux wait-for "never-signalled-$$" --timeout 3
```

Result: `Error: wait-for timed out waiting for 'never-signalled-40365'`, **exit 1**, elapsed
`3.031s` — real elapsed matches `--timeout`, so the timeout is genuinely enforced rather than
returning immediately. **A distinguishable exit code separates "started" from "never started",
which is precisely the rung N56 says the exit ladder lacks.**

### Test 2 — cross-workspace (the test that matters)

Parent waited in the current workspace; a **separate, newly spawned workspace** signalled the token:

```
( cmux wait-for "$TOK" --timeout 25 ) &     # parent, workspace 5BC6A8A3-…
cmux new-workspace --name "probe-signal" --cwd /tmp \
     --command "sleep 2; cmux wait-for -S $TOK; sleep 1; exit" --focus false
```

Result:

```
spawn rc=0 out=[OK workspace:16]
--- parent waiter result ---
OK
PARENT-WAIT-EXIT=0
```

**Cross-workspace signalling CONFIRMED.** A child process in `workspace:16` released a token the
parent was blocked on in a different workspace. The token namespace is server-scoped, not
workspace-scoped — consistent with `cmux wait-for --help` exposing no `--workspace` flag.

Incidental finding: the child self-cleaned. Its trailing `exit` closed the workspace, so the
follow-up `close-workspace` returned `Error: not_found: Workspace not found` and
`cmux list-workspaces` showed no stray entry. A spawned workspace whose command terminates does not
linger.

### Disposition

N56's stated premise — *"It cannot be fixed by trying harder, because cmux has no surface-read"* —
is **false on two independent counts**: `read-screen` exists, and `wait-for` makes screen-reading
unnecessary for the liveness question. The remedy is a bounded closed-loop handshake:

1. Parent composes the successor command with a trailing `cmux wait-for -S sdd-hop-$SPAWN_ID`,
   placed **after** the `/pickup` argument so it fires only once pickup has actually run.
2. Parent spawns, then blocks on `cmux wait-for sdd-hop-$SPAWN_ID --timeout <N>`.
3. Exit 0 from the wait → successor confirmed live; write the `outcome` record as today.
   Exit 1 (timeout) → new ladder rung: spawned-but-never-started, notify + manual instructions.

This reclassifies N56 from **M (structural, needs upstream capability)** to **S (wiring)**, and
supplies the `started` liveness record fix candidate (a) already asks for — without the startup
race or transcript-correlation problem the 2026-07-28 smoke-derived update proposed.

---

## Related

- BACKLOG rows updated/created from this analysis: **N56** (premise corrected), **N57** (blocker
  narrowed), **N60** (capability audit), **N61** (`wait-for` closed-loop handshake).
- `docs/imp-plans/2026-07-22-cmux-integration/` — the feature this analysis reviews.
- CLAUDE.md § "cmux Auto-Spawn Handoff" and § "cmux documentation, versions, and which source wins".
