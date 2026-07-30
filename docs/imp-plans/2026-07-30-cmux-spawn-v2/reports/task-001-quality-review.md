# Task 1 — Adversarial Code-Quality Review

**Verdict: CHANGES_REQUESTED**

Reviewed: `docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md`, the appended
BACKLOG **N76** row, and `reports/task-001-implementer-report.md`, at commit `811b19e`.

This is a strong probe. The negative control is real, the both-halves verification is the right
design, and the disposition's substantive conclusion **survives independent scrutiny** — I swept the
entire `cmux --help` Commands block plus `respawn-pane --help` and `surface resume --help` and found
no env-setting verb beyond `new-workspace` / `workspace create`. Every doc↔binary divergence the doc
records (D1, D2, D3-by-inference, D4) re-verified accurate, and D4 is if anything understated.

It is nonetheless CHANGES_REQUESTED, on one blocking defect of *reasoning* (not of conclusion) plus
four defects that would mislead the future reader the artifact exists to serve.

---

## BLOCKING

### B1. The limits section states a bound that a read-only command falsifies: `cmux rpc` is a CLI path to arbitrary RPC params

**Where:** doc §"Honest limit of axis 3" (blockquote) and §"What could not be established" item 1;
mirrored in report §"Could not establish" #1 and Self-Review #4.

The doc's chain is:

> `cmux capabilities` gives method names only, no schemas, and **the socket was not driven directly**.
> This bounds axis 3 to **"no CLI path exists"** — sufficient for the spawn script, **which is a CLI
> consumer**, but not a claim about the RPC layer.

That inference requires "CLI" and "socket" to be disjoint layers. On this binary they are not:

```
$ cmux rpc --help
Usage: cmux rpc <method> [json-params]
Call a raw v2 method with an optional JSON object for params.

$ cmux rpc workspace.env '{"workspace":"workspace:2"}'
exit=0   { "count": 0, "env": {}, "window_id": "836F…", "workspace_ref": "workspace:2" }
```

`cmux rpc` is a first-class, top-level CLI verb (listed in `cmux --help`'s Commands block, between
`ai-accounts` and `identify`) that calls **any** v2 method with **arbitrary** JSON params. I exercised
it. Therefore:

- **"no CLI path exists [to such a param]" is not established.** `cmux rpc surface.create '{…,"env":…}'`
  is precisely a CLI path to an undocumented param on the exact method the doc names as the residual
  exposure. It was never probed.
- **The reassurance built on it does not follow.** "Sufficient for the spawn script, which is a CLI
  consumer" is the sentence that lets a reader stop worrying. The spawn script being a CLI consumer is
  not a reason the exposure is out of reach — `cmux rpc` is the CLI.

**Why this is blocking rather than important.** Two reasons, both about where the defect sits.
(1) It is in the *limits* section — the place a careful reader extends the most trust, precisely
because the author is being explicit about humility. A reader who skips everything else reads this.
(2) It is the document's own thesis violated at the moment it declares its own limit. The doc's
governing rule is *"'not in `--help`' is a documented-insufficient basis in this repo"* — invoked
correctly for `new-surface --env`, and not applied to its own completeness claim.

**Two supporting facts that belong in the fix, both new:**

1. **`cmux rpc` silently ignores unknown params**, so a future probe cannot use an exit code either:

```
$ cmux rpc workspace.env '{"workspace":"workspace:2","sp2BogusParam":1}'
exit=0   → identical normal payload, no error, no warning
```

   This is the same silent-ignore trap as `new-surface`, one layer down. Any future `cmux rpc
   surface.create` probe needs a **read-back**, not an exit code — exactly the lesson §Axis 2 already
   teaches, now shown to generalize to the RPC layer.

2. **The doc's own D2 already establishes the premise it fails to apply here.** D2 says the binary's
   own error-message flag enumeration is incomplete. Axis 3 then rests decisively on another of the
   binary's self-enumerations (`cmux capabilities`) without inheriting that caution. Same defect,
   named twice in the same document, connected in neither place.

**Fix (documentation only — the conclusion stands):**

- Restate the limit as: *no **documented** CLI verb reaches such a param. `cmux rpc <method>
  [json-params]` is an undocumented-param-capable CLI path and was **not** probed; because `cmux rpc`
  silently ignores unknown params (a-run), probing it requires a read-back, not an exit code.*
- Delete or requalify "sufficient for the spawn script, which is a CLI consumer."
- Add a fifth axis, or fold into axis 3, that the CLI verb sweep was exhaustive over the documented
  command list (I re-ran it; see §Empirical) — this is what actually carries the conclusion, and
  saying so is stronger than the capabilities-name argument currently doing the work.
- Route `cmux rpc` to `2026-07-28-cmux-capability-usage-matrix.md` as an unexamined command. The
  matrix exists to prevent exactly this class of gap, and a generic RPC passthrough is the single
  highest-leverage entry it is currently missing.

---

## IMPORTANT

### I1. The N76 BACKLOG row omits the read-back — standalone, it commits the inference CLAUDE.md forbids

`grep -o 'SP2_SURF[^ ]*' BACKLOG.md` → **empty**. The row's clause (1) reads, in full:

> (1) `new-surface` has no `--env` (absent from `--help`; the upstream contract's `new-surface` row is
> bare);

That is absence-of-evidence twice over. The row *does* carry the negative control, but in a later
"Methodology note" framed as a lesson — and the control only **neutralizes** the exit-0 evidence; it
establishes nothing about `--env`. The datum that converts this into evidence-of-absence — the
read-back showing the value never arrives — appears **nowhere in the row**.

The BACKLOG row is the durable artifact future work reads first, often without opening the cited doc.
Read standalone it fails the repo's own standard, in a row whose stated purpose is to record how that
standard was upheld.

**Fix:** extend clause (1): `…the upstream contract's `new-surface` row is bare; **and a read-back
confirms the value never arrives** — a surface created with `--env SP2_SURF=gamma` reported
`SP2_SURF_MARK=\|alpha`, i.e. `SP2_SURF` empty while the workspace-level `SP2_PROBE` arrived)`. One
clause; keeps the row's pipe-escaping convention.

### I2. N67 is left with a stale "not exercised — probe before building" and no pointer to N76

`sed -n '114p' BACKLOG.md | grep -c N76` → **0**. N67 still reads, verbatim:

> (confidence: a-help, read from the installed binary; **not exercised — probe before building**)

with status `open` and no qualifier. A future reader who reaches N67 first — by grepping `--env`, or
by working the backlog in id order — is told to run a probe that has already been run, and gets no
signal that a disposition exists. The BACKLOG now carries two rows about one item with contradictory
guidance: "probe before building" and "probed; do not adopt."

**This is a plan-scope defect the artifact surfaces, not implementer disobedience.** The plan says
"Modify: `BACKLOG.md` (one disposition row)" and Step 4 says "Append the BACKLOG row"; option (b) is
the only branch that contemplates touching N67. The implementer followed the literal text.

But the file's own convention for a corrected premise is an **in-place UPDATE**, and there is a
precedent in this very file: N56's title reads *"(originally filed as 'structurally unverifiable';
**that premise was disproven 2026-07-28** — see the UPDATE in Notes)"*.

**Fix:** append one clause to N67's Notes — `**UPDATE 2026-07-30: dispositioned by N76** — probed
a-run; flags confirmed, subtraction blocked by topology; do not adopt this sprint.` **Owner exists:**
Task 3 also writes `BACKLOG.md` in this module, so this is a cheap fold-in and needs no new task.

### I3. The flip condition is written against a topology that has not shipped — so a future reader gets no branch for "never adopted"

The doc and row both state the blocker in the present tense —

> This sprint's *primary* topology is a surface in the caller's existing workspace (Decision 2)

— and phrase the flip condition as *abandonment* of that topology:

> if the surface topology is ever **abandoned** and `workspace create` becomes the only spawn path…

But the surface topology is an unshipped decision in `spec-distilled.md`. The **shipped**
`spawn-handoff-session.sh` uses `cmux new-workspace` as its only spawn verb:

```
skills/subagent-driven-development/scripts/spawn-handoff-session.sh:471
  nw=(cmux new-workspace --name "$ws_name" --cwd "$cwd" --command "$launch_cmd" --focus false)
```

So the flip condition's consequent — "workspace create becomes the only spawn path" — is **already
true of shipped code today**, and stays true if cmux-spawn-v2 never lands. "Abandoned" presupposes
adoption; there is no branch for "never adopted." A reader in six months, holding a repo where this
sprint stalled, reads a present-tense claim that is false and a flip condition that appears
unsatisfied while it is in fact satisfied. That is the failure mode the row exists to prevent.

**Fix:** condition on the **shipped** script's spawn path rather than on abandoning a planned
decision. E.g.: *"Actionable whenever the shipped `spawn-handoff-session.sh` reaches successor state
**only** through workspace creation. That is true of the code as of 2026-07-30 (`new-workspace` is its
sole spawn verb) and would remain true if cmux-spawn-v2's surface topology is never adopted; it stops
being true once the surface path ships as primary."* Same sentence, both directions covered.

### I4. The keystone datum has no transcript — the one place the doc's own capture discipline is not visibly honored

§Step 2 opens with a promise:

> **Stdout and stderr were captured to separate files and every result gated on the exit code**, never
> on a parsed field

Every other probe honors it. The single datum on which the entire primary-path conclusion rests does
not:

```
SP2_SURF_MARK=|alpha
```

No `send` command, no `read-screen` invocation, no surface ref, no exit code. §Axis 2 names surfaces
100 / 101 / 102; the `--env SP2_SURF=gamma` surface is a fourth, never identified, and `surface:103`
is separately cited as the "created later" inheritance probe — so a reader cannot tell whether one
surface served both roles or which surface was read.

**Credit where due:** there *is* a real internal positive control — the `|alpha` half proves the
`printf` ran, the shell expanded variables, and the read-back reached a surface in `workspace:38`. That
is genuinely good design and it rules out the most likely confounds. It does **not** rule out a
wrong-surface read or a name mismatch between the create-time `--env SP2_SURF=…` and the read-time
`$SP2_SURF` — both of which produce this exact output.

**This is un-re-verifiable read-only** (reproducing it requires creating a surface), which is precisely
why the transcript needed to be complete the first time.

**Fix:** paste the two commands with their surface ref and exit codes, as every neighbouring probe
does; and state explicitly that `$SP2_PROBE` served as the in-band positive control — the argument is
better once named.

---

## MINOR

### M1. `a-run` label overstates: `new-workspace --env` was never exercised

Bottom line item 1 — *"`--env` / `--env-file` are accepted on **both** spellings … **a-run**"*. Only
`cmux workspace create` was exercised (§H4's exercised row, §"Create — the canonical spelling"). For
`new-workspace` the evidence is `--help` (a-help) plus the noun help's "same flags as new-workspace"
plus the contract. The alias equivalence has three converging sources including the binary's own
error-message enumeration, so the *claim* is near-certainly right — only the *label* is wrong.

Worth fixing anyway because `new-workspace` is the spelling a future adopter would type first: it is
what the shipped script already calls (I3). Fix: split the label, or say "exercised on `workspace
create`; a-help + a-file for `new-workspace`."

### M2. Annotations inside code fences make "transcripts" un-copyable

The env-file fixture block, the reserved-key block, the read-back block and the layout block all carry
inline annotations inside the fence (`← blank line`, `← ACCEPTED, no warning`, `↑ SP2_SURF is EMPTY`,
`← same key --env also sets, to test precedence`). Copying the fixture verbatim yields a file whose
last line is `SP2_PROBE=from_file_should_lose      ← same key --env also sets, to test precedence`.
Fix: move annotations to a caption or a trailing comment column outside the fence.

### M3. The report's "reproduced verbatim" is false for all three help captures

Report §"Help output captured": *"All three are reproduced verbatim in the disposition doc."* Verified
against the live binary:

| Block | Actual |
|---|---|
| H1 | elided with an explicit `...` (drops `reconnect` / `disconnect` / `loading`) — plus the whole trailing `env/reconnect/disconnect accept a positional handle…` paragraph and the 6-line Examples block, with no marker |
| H2 | abridged, **no marker** — drops the `cmux new-workspace` title line, "Create a new workspace in the caller's window.", and the 6-line Examples |
| H3 | abridged, **no marker** — drops the title line, "Create a new surface (tab) in a pane.", and the 4-line Examples |

The conclusion is unaffected: I re-ran `cmux new-surface --help 2>&1 | grep -i env` → rc=1, no match
over both streams, including the omitted lines. Fix: change the report's claim to "abridged to the
flags block" and add an ellipsis marker to H2/H3, as H1 already has.

### M4. Bonus for the D-table — a fifth doc↔binary divergence, in the doc's own genre

The `workspace` noun help states legacy verbs *"keep working and print a **one-time** deprecation
hint."* They print it **every** invocation — I ran `cmux list-workspaces` three consecutive times and
got the hint each time. It goes to **stderr**, so stdout `OK`-ref parsing is unaffected (relevant
because `spawn-handoff-session.sh` parses `new-workspace` stdout). The doc already quotes this hint
under H4 as confirming N70; it just didn't notice the "one-time" claim is false. Free addition to the
D1–D4 table.

---

## Checked and found sound — do not re-litigate

- **Disposition logic.** The scalars-only qualifier is honored; the architectural cost is recorded as
  a recommendation and not smuggled in as evidence the flag fails (the trap Self-Review #6 names). The
  reasoning from Decision 2's "ONE shared launch-and-handshake wrapper (same inline env…)" to "a
  fallback-only swap forks the wrapper" is valid — `spec-distilled.md:59` says exactly that, and
  `:37` confirms `workspace create` is the fallback-path verb.
- **The negative control's logical role is stated correctly.** The doc does *not* claim the control
  proves absence; it says the control makes the acceptance "worth nothing" and that the **read-back**
  proves the value never arrives. That is the correct division of labour. My objection (I4) is to the
  read-back's *documentation*, not its logic.
- **Blank-line / comment "ignored" reasoning.** Inferred from "create succeeded AND no spurious key,"
  which is adequate — a rejecting parser would have failed the create.
- **Scope.** The primary-path investigation is plan-mandated (Step 1 asks for "any surface-scoped env
  equivalent"), not creep.
- **D4 is understated, not overstated.** The contract's help-output index lists ~60 per-command
  entries and contains **no** entry for any `cmux workspace <sub>` spelling at all.
- **`--mask` two-point generalization, `--type terminal`-only scoping, and the unevidenced "answer is
  no" for the unscoped question** are all real imprecisions. I am deliberately not filing them: each
  is a clause, none affects a conclusion, and padding the list would misrepresent this work's quality.

---

## Empirical vs. reasoned

### Verified by execution (read-only, this review, against `cmux 0.64.20 (100) [14e3400b9]`)

| Claim | Result |
|---|---|
| Binary pin | `cmux --version` exact match; `cmux ping` → `PONG` |
| H1 noun-help dispatch | **Stronger than the doc claims.** All 8 real subcommands (`create env close list status rename select group`) print byte-identical noun help, exit 0 — same sha256 across all eight. The doc generalizes from 3 samples; the generalization holds |
| H1 elision | Elided lines confirmed real (`reconnect`, `disconnect`, `loading`); trailing paragraph + Examples also dropped |
| H2 / H3 flag text | Flags blocks byte-match the binary. `grep -i env` over **both** streams of `new-surface --help` → rc=1 |
| "26 `surface.*` methods, none env-related" | **Exact.** 26 unique, enumerated; none env-related. `surface.create` present (the residual exposure the doc correctly names) |
| "exactly one env-related method in the whole RPC set" | Confirmed: `workspace.env` only, across 252 unique methods |
| `capabilities` is names-only | Confirmed: top keys `access_mode, methods, protocol, socket_path, version`; `methods` is a flat string array. The doc's stated limit is accurate |
| Mutation probes | `workspace env set …` → exit 1 "Invalid workspace handle: set"; `workspace env … --env K=V` → exit 1 `Known flags: --workspace, --window, --mask`; `set-environment` → exit 2 unknown command. All three byte-match the doc |
| "silently ignores the extra arg" | Confirmed with a **non-**`KEY=VALUE` positional (`sp2ReviewExtraArg`) → exit 0, read view. I did **not** re-run the `KEY=VALUE` form — that is a mutation attempt |
| D1 / D2 | `workspace env workspace:2 --json` → exit 0, well-formed JSON (`count`/`env`/`window_ref`/`workspace_ref`); `--json` absent from the noun help's `env [workspace] [--mask]` **and** from the error message's Known-flags list. Both halves confirmed |
| D4 | Contract's "Current Help Caveats" enumerates exactly `version`, `claude-teams`, `codex-teams`, `remote-daemon-status` — noun-help dispatch absent. Confirmed, and understated |
| Contract's `new-surface` row is bare | Confirmed — `cli-contract.md:119` `\| new-surface \| Create a surface inside a pane. \|` |
| Contract `--env` semantics | Confirmed at `cli-contract.md:236-239`, including "(and the same flags on `cmux workspace create`)" |
| **New: `cmux rpc` exists and works** | `cmux rpc workspace.env '{…}'` → exit 0 (B1) |
| **New: `cmux rpc` ignores unknown params** | `sp2BogusParam` → exit 0, identical payload (B1) |
| **New: CLI verb sweep** | Full `cmux --help` Commands block + `respawn-pane --help` (`--command` only) + `surface resume --help` (no env) + `workspace-action` — **no env-setting verb beyond `new-workspace`/`workspace create`.** The doc's conclusion is corroborated |
| **New: deprecation hint is not one-time** | 3/3 invocations printed it, on stderr (M4) |
| Cleanup | `cmux list-workspaces` → 5 workspaces, zero `sp2-*`, no `workspace:38/39/40` |
| N76 id | Max N id = 76; exactly 1 occurrence; N67 line contains 0 occurrences of "N76" (I2); `grep SP2_SURF BACKLOG.md` empty (I1) |
| Shipped spawn verb | `spawn-handoff-session.sh:471` — `cmux new-workspace` is the sole spawn verb (I3) |

### Concluded by inference, not execution

- B1's severity: `cmux rpc`'s existence does not *prove* an env param exists on `surface.create` — it
  proves the doc's **bound** is unearned. I am not claiming the primary-path conclusion is wrong; my
  own CLI sweep supports it.
- I4's confound analysis (wrong-surface read / name mismatch) is reasoning about what the elided
  transcript cannot exclude, not a demonstration that either occurred. Both are unlikely.
- I3 rests on reading `spec-distilled.md` as unshipped intent and `spawn-handoff-session.sh` as
  shipped reality — a documentary comparison, not a runtime one.
- M1's "the claim is near-certainly right" is judgment about three converging sources, not a probe.

### Could not check at all (would require mutating cmux state — prohibited by this review's scope)

- Both negative-control exit codes (`new-surface --sp2-not-a-real-flag` → 0; `workspace create
  --sp2-not-a-real-flag` → 1). Reproducing either creates a surface or attempts a create.
- Every in-surface read-back value: `SP2_WS_MARK=alpha|beta|file_plain|file_export`, the
  `surface:103` inheritance read, `SP2_RES=…|xterm-256color|yes`, and `SP2_SURF_MARK=|alpha` (I4).
- All `--env` / `--env-file` acceptance and the four `--env-file` semantics — they require a create.
- `--mask` rendering (`SP2_PROBE=••••`, `SP2_FILE_PLAIN=fi••••`): `workspace:2` has zero env vars, so
  there is nothing to mask read-only.
- `--layout` `surfaces[].env` (`SP2_LAYOUT=delta`) and the "layout env absent from the configured
  view" observation.
- Whether `cmux rpc surface.create` accepts an env param — settling it requires creating a surface
  **and** a read-back (exit code is useless, per B1).

For all of the above I applied the spec reviewer's coherence check and found nothing inconsistent: the
refs form a monotonic sequence above Task 0's fixtures, and none of `workspace:38/39/40` survive.

---

## Review hygiene

Every command I ran was read-only. I created, modified, and destroyed **no** cmux workspace or surface,
ran no `git stash`, and edited no file other than this report. Verified before and after probing:
`git status --short` unchanged apart from this report (same 3 modified + 4 untracked controller
artifacts), and `cmux list-workspaces` returning the identical **set** of 5 workspaces
(`2, 11, 20, 22, 28`) with `workspace:2` still selected. Their sidebar display order differed between
my first and last listing; I ran no mutating command, so I attribute that to the app's own
ordering/recency behavior rather than to this review — flagging it rather than claiming a
byte-identical listing I did not observe. `workspace:2` reported `count: 0` env vars both before and
after my `workspace env` probes.

## Suggested disposition

Documentation-only remediation; no probe needs re-running except the optional `cmux rpc surface.create`
follow-up, which is discretionary and belongs in the capability matrix rather than this sprint.

1. **B1** — restate the axis-3 limit; add the `cmux rpc` fact and its silent-ignore behavior; route
   `cmux rpc` to the capability matrix as unexamined.
2. **I1** — one clause into N76 clause (1) carrying the read-back.
3. **I2** — one UPDATE clause into N67 (fold into Task 3's BACKLOG write).
4. **I3** — rephrase the flip condition against the shipped spawn path.
5. **I4** — paste the missing transcript; name the in-band positive control.
6. **M1–M4** — label split, fence annotations, "verbatim" correction, D-table addition.
