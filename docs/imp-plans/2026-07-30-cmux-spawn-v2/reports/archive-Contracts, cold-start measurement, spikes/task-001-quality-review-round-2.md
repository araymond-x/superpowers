# Task 1 — Adversarial Code-Quality Re-Review (Round 2)

**Verdict: CHANGES_REQUESTED**

Reviewed at commits `24f885a`, `8e4bbf6`, `2623074` (Task 1 original: `811b19e`) against
`cmux 0.64.20 (100) [14e3400b9]` — re-pinned live (`cmux --version` exact match, `cmux ping` → `PONG`).

**Nine of nine round-1 findings are substantively addressed, and the fix round is materially stronger
than the review asked for in three places** (H2/H3 made byte-complete rather than marked-abridged; the
`a-run` label *earned* by exercising the missing spelling rather than downgraded; the CLI sweep re-run
first-hand rather than imported from the reviewer). The headline disposition survives round 2
unchanged, and I independently re-derived the leg that now carries it.

It is nonetheless CHANGES_REQUESTED, on **two newly-introduced reasoning defects — both of the exact
class this fix round was convened to eliminate**, one of them propagated into the standalone durable
BACKLOG row.

**Scope of round 3: documentation-only. No probe needs re-running. No transcript needs deleting.**
The remediation is roughly four sentences across three files, plus two MINOR clauses.

---

## Do NOT redo these — verified closed this round

Listed first so round 3 does not churn work that is genuinely done.

- **B1's five locations** are closed, and no sixth assertion of the withdrawn bound survives.
- **Axis 4 reproduces exactly** — I re-ran the sweep independently: `command count = 127`, one `--env`
  hit (`new-workspace`), eight `env` mentions, the same eight names.
- **H2 and H3 are byte-identical to the live binary** (`diff` → empty, 29 and 26 lines).
- **The BACKLOG diff touches exactly N67 and N76**, 4 changed lines, 8/8 unescaped-pipe integrity
  against the header; **N54 (9) and N57 (11) remain corrupted, untouched and unpropagated.**
- **I3's flip condition reads correctly cold under both branches**; its premise re-verified against
  the shipped script.
- **D5 re-confirmed** (3/3 again this round; 6/6 across both reviews).

---

## Round-1 findings — disposition

### B1 (BLOCKING) — the axis-3 limit → **CLOSED**

**Five locations verified.** I reconstructed the original occurrence set from `811b19e` rather than
trusting the fix report's list. The original doc carried the bound at four sites — the limit
blockquote, §Disposition's do-not-adopt bullet, §"What could not be established" #1, and Bottom line
item 3 ("no env channel **at all**") — plus the fifth in N76's summary clause. All five are corrected.

**No sixth survives.** `grep -niE 'no cli path|cli consumer|sufficient for the spawn script'` over the
doc returns six hits, **every one of which is an explicit withdrawal, a quotation of the withdrawn
text, or the deviations-table entry recording the withdrawal.** A repo-wide sweep found the claim
surviving only in `task-001-implementer-report.md` (immutable, correctly acknowledged as out of
scope), the round-1 review, and the spec review.

**Axis 4 re-derived independently.** Same extraction, same binary:

```
command count =      127
ENV-FLAG: new-workspace
```

and the broadened grep returns exactly the eight the doc names (`ai-accounts`, `claude-teams`,
`new-workspace`, `omc`, `omo`, `omx`, `vm`, `workspace`). The doc's hidden-verb probes also
reproduce: `cmux workspace-group --help` and `cmux claude-hook --help` both exit 0 with **zero**
`env` occurrences of any kind.

**Is "documented top-level verbs" the right population?** Substantially yes, with one imprecision
filed as NEW-3 below. It is *not* the population the doc's prose implies, but I closed the gap myself
and it changes nothing.

**Does the disposition now survive by argument rather than inference?** Yes, and §2.9 does bear the
weight it is asked to bear — because the doc is careful about what it asks. I read §2.9 in full. It
concludes *"Recommendation: do not build on `rpc`. Its value is as an enumeration tool."* The doc
cites it as **"a recommendation in a findings doc, not ratified policy — cite it as such."** That is
the correct characterization: a recommendation-not-to-build has **not** been upgraded into
evidence-that-it-cannot-work. The doc states the residual openly ("an `rpc`-reachable env param on
`surface.create` has not been excluded... What is claimed is that the spawn script would not adopt one
if it existed"). Self-Review #2 shows the stronger, tidier, false claim (`capabilities` is incomplete)
was consciously declined. **This is the fix round's best work.**

The premise correction was independently re-confirmed: the matrix carries `| rpc | unexamined | a-run
| Raw v2 method call. §2.9. |` in §1 and drills in at §2.9. B1 bullet #4 was wrong; correctly not
acted on.

### I1 — N76 omitted the read-back → **CLOSED** (but see NEW-1)

`grep 'SP2_SURF' BACKLOG.md` now hits. Clause (1) names the two documentary signals **as** absence of
evidence, then carries `SP2_SURF_MARK=\|alpha` with the positive control named. Pipe escaped per the
file's convention; row integrity 8/8. The row stands alone. **One of the three legs it carries is
invalid — NEW-1.**

### I2 — N67 stale → **CLOSED**

`sed -n '114p' BACKLOG.md | grep -c N76` → now non-zero. Status column reads `open (probe DISCHARGED
2026-07-30 — dispositioned by **N76**; watch item, not a subtraction — see the UPDATE in Notes)`, and
Notes carries an `UPDATE 2026-07-30` with what was confirmed, what was blocked, an explicit "do not
schedule as a subtraction, do not close as not-viable", and two sharpenings. Matches the N56
in-place-UPDATE precedent the row cites.

**Diff containment verified mechanically**, not from the report: `git diff --unified=0
811b19e..2623074 -- BACKLOG.md` → two hunks (`@@ -114 +114 @@`, `@@ -123 +123 @@`), 4 changed lines,
row ids `N67` and `N76` only. N54/N57 are not in the diff and remain at 9 and 11 unescaped pipes —
neither fixed nor propagated, exactly as instructed.

### I3 — flip condition → **CLOSED**

Premise re-verified first-hand: `grep -nE 'cmux (new-workspace|new-surface|workspace create)'` over
`spawn-handoff-session.sh` returns the `nw=(cmux new-workspace …)` array as the **sole** spawn verb
(the other hits are a comment and an error message). `spec-distilled.md:59` confirms Decision 2's
"ONE shared launch-and-handshake wrapper (same inline env…)" verbatim, and `:84` confirms the
surface-first topology is unshipped intent.

**Read cold, both branches are actionable.** *Sprint landed* ⇒ the script reaches successor state
through `new-surface` primary with a workspace fallback ⇒ not "ONLY through workspace creation" ⇒ not
actionable. *Sprint stalled or reverted* ⇒ `new-workspace` only ⇒ actionable. The predicate is a
property of shipped code, checkable by grep, with no session context required. The construct citation
(`nw=(cmux new-workspace …)` in `spawn_claude_workspace`) survives line-number rot per repo policy.
I could act on this in six months with no memory of this sprint.

### I4 — keystone transcript → **PARTIAL**

**Two of the three claimed confound exclusions are genuinely achieved; the third is invalid.**

- **Wrong-surface read — EXCLUDED.** `new-surface` returns `OK surface:108`; `send` and `read-screen`
  are both pointed at `surface:108`. Traceable end to end.
- **Local expansion — EXCLUDED, and well done.** The scrollback shows the command line echoed with
  `$SP2_SURF` and `$SP2_PROBE` **unexpanded**, proving the payload was single-quoted locally and
  expanded remotely. The reasoning is airtight: a local expansion would have produced no `alpha` at
  all, because the caller's shell does not carry `SP2_PROBE`. The in-band positive control is now
  named explicitly, as asked.
- **Third leg — INVALID.** See NEW-1. It does **not** distinguish "flag not implemented" from "flag
  implemented but not exported."

Note also a mis-attribution: the fix report credits the third leg with excluding *name mismatch*. It
doesn't — what excludes name mismatch is the transcript showing `--env SP2_SURF=gamma` in and
`$SP2_SURF` out. That exclusion is real; the attribution is wrong.

**Zero residual `sp2fix-*` confirmed.** `cmux list-workspaces` → six workspaces, `grep -ci sp2` → 0,
no `workspace:41`. The set has legitimately grown by one (`workspace:42`, ref **above** 41, so it
cannot be a residual of this probe) through ordinary user activity, so I assert the absence of
`sp2*`/`workspace:41`, not a byte-identical listing.

Also credit where due: the fix **volunteered** that the first session's Half-2 rendering could not
have produced its own recorded output, rather than quietly re-rendering it. I verified the original —
`\"$SP2_PROBE\"` inside a locally double-quoted string — and the self-critique is accurate. That is
the disclosure a fix round is supposed to make.

### M1 — the `a-run` label → **PARTIAL**

Step A genuinely exercises `cmux new-workspace --env … --env-file …` (exit 0, `OK workspace:41`), so
the "exercise it rather than downgrade the label" branch was earned. The doc's Bottom line item 1 is
carefully phrased ("both halves verified independently, **and** both spellings were exercised"). But
the fix report and N67's UPDATE both overclaim the cross-product — see NEW-5.

### M2 — fence annotations → **CLOSED**

Programmatic scan: **zero** `←`/`↑` annotations inside any fence; fences balanced (46 markers). The
env-file fixture is byte-copyable with the per-line explanation moved to prose beneath it. The
`exit=0 → byte-identical…` line inside the rpc fence follows the doc's established `exit=N  stdout:`
convention, which round 1 did not flag; not a regression. The new `[ELIDED: …]` marker inside H1's
fence is an annotation, but H1 is explicitly declared abridged in the adjacent prose and the marker
aids the reader — **not filed as a finding.**

### M3 — "reproduced verbatim" → **CLOSED**

Verified by `diff` against the live binary, not by reading: `cmux new-workspace --help` (29 lines) and
`cmux new-surface --help` (26 lines) are **byte-identical** to the doc's H2 and H3 blocks. H1 now
declares itself abridged and names what is elided. The report-side half is correctly recorded as a
correction rather than edited into an immutable artifact.

### M4 — the fifth divergence → **CLOSED**

D5 added with the stderr consequence stated. Re-confirmed: 3/3 consecutive `cmux list-workspaces`
runs emitted the hint on stderr.

---

## New findings

### NEW-1 (BLOCKING). The re-capture's "third leg" is an absence-of-evidence inference that the same document refutes — and it is now in N76 and `deviations.md`

**Where:** doc §"Re-capture" Step C; N76 clause (1) ("A third leg: `SP2_SURF` never appears in `cmux
workspace env` either, so the flag is not merely unexported — it is never recorded");
`deviations.md` row at line 64.

The claim:

> **The third leg the first session lacked:** `SP2_SURF` does not appear in the configured view
> either. So the surface-level `--env` is not merely *unexported* — it is **never recorded at all**.
> The flag is consumed and discarded.

**The same document proves that instrument is blind to exactly this class of value.** §"The one
per-surface env channel that does exist" records a per-surface env that demonstrably **works**:

```
$ cmux read-screen --surface surface:105 --scrollback
SP2_LAYOUT=delta
$ cmux workspace env workspace:40
No environment variables
```

and the doc then states the general rule outright: *"`cmux workspace env` shows **neither**
protected-key effective values **nor** per-surface layout env. It reports the workspace-level
configured set and nothing else."*

So a surface-scoped env that is fully implemented and fully working is **invisible** to `cmux
workspace env`. Its silence about `SP2_SURF` therefore cannot distinguish "`new-surface --env` is not
implemented" from "`new-surface --env` is implemented as surface-scoped, exactly like layout env."
The leg establishes nothing it is credited with.

**Why this is blocking rather than important.** Not because of consequence — the conclusion is
untouched; Step D's read-back carries it and is sound. Three reasons about where the defect sits:

1. **It is a fresh instance of the document's own governing error**, committed in the section written
   to close a review finding about that error, in a round convened for that purpose. The doc's rule is
   *"'not in `--help`' is a documented-insufficient basis in this repo"*; this is "not in `workspace
   env`" used as a sufficient basis, against an instrument the doc itself measured as blind.
2. **N76 contradicts itself internally.** The row carries this inference in clause (1) and, ~5,000
   characters later, its own refutation: *"Consequence: `cmux workspace env` misreports the effective
   environment for protected keys and **shows no layout per-surface env** — never treat the configured
   view as ground truth."* A standalone durable artifact that both makes and forbids the same
   inference is broken as a standalone artifact, which is the whole point of I1.
3. **It has propagated to three durable places** — doc, N76, `deviations.md` — where round 1's B1 sat
   in one.

**Fix — keep the transcript, replace the inference. There is a true, narrower claim available.** Step C
does establish something real: `new-surface --env` does **not** write to the *workspace-level*
configured env, i.e. it is not a covert workspace-env setter. State that, and state that the configured
view is silent about surface-scoped env by construction (cite the `--layout` finding), so it cannot
adjudicate implementation. Then let Step D carry the conclusion, as it already does.

**Owners are split:** the doc and N76 are in Task 1's write scope; `deviations.md` line 64 is
explicitly **not** (the fix report says so) — that clause is controller action.

### NEW-2 (IMPORTANT). The corrected axis-3 limit's own `cmux rpc` transcript passes a parameter this binary silently ignores — so the contrast it draws between "works" and "bogus param" is false

**Where:** doc §"Honest limit of axis 3 — corrected 2026-07-30", the two `cmux rpc` blocks; mirrored
in the fix report §"What I verified before changing anything".

The doc presents this as **a-run** that the verb "exists and works":

```
$ cmux rpc workspace.env '{"workspace":"workspace:2"}'
exit=0
{ … "workspace_ref": "workspace:2" }
```

then contrasts it with a bogus-param call to establish silent-ignore. **Both calls had an ignored
param.** `workspace` is not a parameter name this method honors. Verified read-only:

| Params | Returned `workspace_ref` |
|---|---|
| `{}` | not workspace:2 (volatile — observed 11, later 42) |
| `{"workspace":"workspace:2"}` | identical to `{}` |
| `{"workspace":"workspace:9999"}` | identical to `{}` |
| `{"workspace":"totally-bogus-not-a-ref"}` | identical to `{}` |
| `{"workspace_id":"5BC6A8A3-…"}` | **workspace:2** — honored |
| `{"workspaceId":"5BC6A8A3-…"}` | identical to `{}` |

A syntactically-bogus *value* under the `workspace` key returns the same payload as omitting the key
entirely, while the snake_case `workspace_id` UUID form is honored. The no-param default is also
**not** the caller's workspace: my `$CMUX_WORKSPACE_ID` is `5BC6A8A3…` (= workspace:2), the CLI
`cmux workspace env --json` correctly returns `workspace:2`, and `cmux rpc workspace.env` with no
params returns something else. *(I observed two different defaults on two calls and am deliberately
**not** asserting a mechanism — only that it is volatile and is not the caller.)*

So the doc's rendered payload showing `workspace_ref: workspace:2` immediately after passing
`"workspace":"workspace:2"` is a **coincidence** of whatever that session's default was, and it invites
precisely the reading round 1 blocked on. The doc does not literally claim the param was honored — but
it stages the two calls as a contrast, and there is no contrast.

**This does NOT resurrect the withdrawn bound.** `{"workspace_id":"<uuid>"}` *is* honored, which proves
`cmux rpc` routes correctly-named params to the method. `cmux rpc surface.create '{…,"env":…}'`
therefore remains a live, unprobed CLI path to an undocumented param, and B1's withdrawal stands. What
the transcript fails to show is that *this particular call* exercised that path — not that the path is
unreachable.

**Two things to fix, one of which is a genuine addition to the residual.**

1. Either use the honored form (`{"workspace_id":"<uuid>"}`) in the "it works" transcript, or state
   plainly that the `workspace` key is itself ignored — which makes the silent-ignore point *twice as
   strongly*, from the doc's own first invocation.
2. **The residual is understated.** The doc says settling `cmux rpc surface.create` needs a create plus
   a read-back. It also needs a **correct parameter-name guess**: a wrong name is silently ignored and
   is indistinguishable from an unimplemented feature, and the CLI's own ref vocabulary (`workspace:2`)
   is *not* the RPC vocabulary. This strengthens the do-not-adopt disposition — it is another reason
   the spawn script should not build on `rpc`.

### NEW-3 (MINOR). Axis 4's population is "unique first tokens of indented `Commands:` lines", not "all documented top-level commands" — seven names were never individually probed

The extraction yields 127 unique tokens from 172 matched lines (`browser` alone accounts for 43). It
silently drops the trailing members of alternation rows. Seven real top-level command names are
therefore in `cmux --help` but were never given their own `--help`:

`enable-browser`, `browser-status`, `logout`, `previous-window`, `last-window`, `unbind-key`,
`copy-mode`.

**I probed all seven: exit 0, zero `--env` hits.** The conclusion is unaffected and this residual is
now closed — but "**all** 127 documented top-level commands" (§Axis 4, Bottom line item 3, deviations
row 10) describes a population that is neither exactly the documented command set nor exhaustive of
it. In a document whose subject is enumeration completeness, and which already states two scope limits
for this sweep, a third belongs there. One clause: "127 unique command names extracted from the
`Commands:` block; alternation siblings collapse to their first token and were probed separately."

### NEW-4 (MINOR). A newly-written sentence restates the conclusion without the qualifier the same fix round added three paragraphs earlier

§Disposition's closing branch summary, added this round:

> **sprint landed** ⇒ not actionable (the surface path has **no env channel**, so the command string
> stays)

Bottom line item 3 and the do-not-adopt bullet were both corrected to "no env channel any *documented
CLI verb* reaches". This sentence was written in the same round and carries the unqualified form.

*Not filed:* §"The primary path"'s bold `**Answer: there is no env channel…**` is unchanged from the
original and now carries an explicit adjacent instruction — *"read the limit at the end of axis 3
before quoting this answer"* — which is a deliberate, documented mitigation. Noted, not a finding.

### NEW-5 (MINOR). "a-run on both spellings, on both halves" overclaims — `workspace create`'s inherited-process half was not re-captured

The fix report states: *"Both spellings are now genuinely a-run on **both** halves (configured view +
inherited process env)."* N67's UPDATE reads similarly: *"upgraded a-help → a-run on both spellings:
`--env`/`--env-file` are accepted on the canonical `cmux workspace create` as well as the deprecated
`new-workspace`, and they genuinely **export** — verified on the configured view AND an in-surface
read-back."*

The re-capture ran entirely on the `new-workspace` spelling (`workspace:41` / `surface:107` / `:108`).
`cmux workspace create`'s inherited-process half still rests **only** on the first session's
`SP2_WS_MARK=alpha|beta|file_plain|file_export` — the capture whose command rendering the fix itself
admits "could not have produced its own recorded output," and which Concerns #4 correctly lists as
un-re-verifiable. The doc's own Bottom line item 1 is phrased correctly ("both halves verified…**and**
both spellings exercised"); it is the report and N67 that read as the cross-product.

The alias equivalence has four converging sources including the binary's error-message enumeration, so
the claim is near-certainly true. Only the evidence label is wrong — and N67 is the durable artifact.

### NEW-6 (MINOR). The section headed "**The one** per-surface env channel" quotes a contract sentence naming **two**, and dispositions only one

Pre-existing (round 1 missed it too), conclusion safe, one sentence to fix — filed rather than waived
because the task asked for internal contradictions between sections, and this is one that is checkable
by reading alone.

The heading reads *"**The one** per-surface env channel that does exist — and why it does not help."*
Its opening sentence quotes the contract:

> *"explicit per-surface environment (a layout `surfaces[].env`, **SSH startup env**) overrides the
> workspace value for that surface."*

Two channels named; only the layout half is exercised and dispositioned. `SSH` appears **exactly once
in the entire document** — inside that quote (`grep -c 'SSH'` → 1). The SSH half is quoted and then
silently dropped, under a heading asserting there is only one.

The resolution favours the doc, which is why this is MINOR: `cmux ssh --help` reads *"Create a new
workspace, mark it as remote-SSH, and start an SSH session in that workspace"* and exposes **zero**
`env` mentions. So SSH startup env is not a channel into an **already-existing** workspace's surfaces,
and the primary-path conclusion is untouched. But the doc should say that in a clause rather than
leave a reader to notice that its own quoted evidence outnumbers its own heading.

### Nit (not filed as a finding). Fix report arithmetic

The report states *"one BLOCKING finding, four IMPORTANT, four MINOR. **All ten** are closed"* and
*"all ten review findings closed."* Round 1 had **nine** (`grep -cE '^### (B|I|M)[0-9]\.'` → 9). A
slip, not a substantive error; recorded only because this round's brief is not to take a confident fix
report on its word.

---

## Checked and found sound — do not re-litigate

- Everything round 1 listed as sound survives the fix: the scalars-only qualifier, the architectural
  cost recorded as a recommendation rather than smuggled in as evidence, the negative control's
  division of labour (`new-surface` silently ignores unknown flags ⇒ its acceptance of `--env` is
  worth nothing; the read-back is what proves absence), the blank-line/comment reasoning, scope, and
  D4's understatement.
- Everything the spec review verified survives: 26 unique `surface.*` methods (re-counted: exactly
  26), `workspace.env` as the only env-related method across the RPC set, D2's both halves,
  `verify-symlink-install.sh` (re-ran: **104 passed, 0 failed, 0 warnings**).
- The fix report validates: `validate-report.py --report-file …` → exit 0, `COMPLETE`, zero missing
  sections.
- **Deviations rows 8–10 all reached `deviations.md`** (lines 62, 64, 65). Row 9's entry carries the
  NEW-1 defect; that is the controller-owned half of NEW-1's fix.
- The mutation claim in Bottom line item 3 is **not** collateral damage from B1. "`cmux capabilities`
  exposes no env-setting *method*" is a **method-existence** question, which is exactly what a
  names-only enumeration can answer — and if no method sets env, `cmux rpc` cannot reach one either.
  The residual is confined to undocumented *params* on existing methods. The doc gets this right.
---

## Empirical vs. reasoned

### Verified by execution (read-only, this review, `cmux 0.64.20 (100) [14e3400b9]`)

| Claim | Result |
|---|---|
| Binary pin | `cmux --version` exact match; `cmux ping` → `PONG` |
| **Axis 4 re-derivation** | Independent re-run: `command count = 127`; `ENV-FLAG: new-workspace` — the **only** hit. Broadened `env` grep → the same **eight** names the doc lists. Fully reproducible |
| Axis 4 population gap (NEW-3) | 172 matched lines → 127 unique tokens; 7 alternation-sibling names never individually probed. **I probed all 7** — exit 0, zero `--env` |
| Hidden verbs | `workspace-group --help`, `claude-hook --help` → exit 0, **zero** `env` occurrences of any kind |
| H2 / H3 byte-completeness | `diff` doc-block vs live `--help` → **empty**, both. 29 and 26 lines confirmed |
| **`cmux rpc` param handling (NEW-2)** | `{"workspace":…}` ignored for valid AND bogus values (identical payload to `{}`); `{"workspace_id":"<uuid>"}` **honored**; `{"workspaceId":…}` ignored. No-param default is volatile and is **not** `$CMUX_WORKSPACE_ID` |
| `cmux rpc` silent-ignore | `sp2R2Bogus` → exit 0, `cmp` byte-identical payload. Doc's claim confirmed |
| `cmux rpc --help` | Byte-matches the doc's blockquote |
| `capabilities` | 255 methods; **26** unique `surface.*`; exactly one env-related (`workspace.env`) |
| D5 | 3/3 consecutive `list-workspaces` runs emitted the hint, on stderr |
| `cmux send --help` | Escape-sequence sentence quoted in the doc is verbatim |
| `cmux ssh --help` (NEW-6) | *"Create a new workspace…"*; **zero** `env` mentions. `grep -c 'SSH'` over the doc → **1**, inside the quote only |
| `respawn-pane` / `surface` help | Zero `env`; `surface resume` flags carry no env channel |
| Shipped spawn verb | `cmux new-workspace` is the **sole** spawn verb in `spawn-handoff-session.sh` |
| BACKLOG diff containment | Two hunks (`-114`, `-123`), 4 changed lines, ids `N67`/`N76` only |
| Table integrity | Header 8; N67 = 8; N76 = 8; N72/N75/N51 = 8. **N54 = 9, N57 = 11 — untouched** |
| N76 read-back present | `grep 'SP2_SURF' BACKLOG.md` now hits (was empty in round 1) |
| N67 pointer | Line 114 now contains `N76` (was 0 in round 1) |
| Fence hygiene | Zero `←`/`↑` inside fences; 46 markers, balanced |
| Residual workspaces | `grep -ci sp2` → **0**; no `workspace:41`. Six workspaces (one new, ref **above** 41) |
| Install test | `verify-symlink-install.sh` → 104 passed, 0 failed, 0 warnings |
| Report validity | `validate-report.py` → exit 0, `COMPLETE` |
| Round-1 finding count | `grep -cE '^### (B|I|M)[0-9]\.'` → **9**, not ten |

### Concluded by inference, not execution

- **NEW-1's severity.** That the third leg is *invalid* is demonstrated — by the doc's own `--layout`
  evidence. That it rises to BLOCKING is a judgment about where the defect sits (self-contradiction
  inside a standalone durable artifact; a fresh instance of the governing error class in the
  remediation section), not about consequence. **The conclusion is unaffected.**
- **NEW-2's reconstruction of the fix session.** I demonstrated the param is ignored *today*. That the
  doc's payload showed `workspace:2` *because* the default happened to be workspace:2 is the only
  explanation consistent with my measurements, but I did not observe that session. I deliberately do
  not assert what the rpc default *is* — my two no-param calls returned different workspaces.
- **NEW-5.** Reading which spelling each session exercised is documentary comparison; I did not re-run
  either.
- **I3's cold-read legibility** is a judgment about a future reader, not a measurement.
- **§2.9 bearing its weight** is a judgment about how the doc cites it, from reading both.
- **NEW-6's resolution** rests on `cmux ssh --help` prose ("Create a new workspace…"), not on running
  `cmux ssh`. That the contradiction *exists* is textual and certain; that it resolves harmlessly is
  read from help output.

### Could not check at all (would require mutating cmux state — prohibited)

- Every value in **both** probe sessions' in-surface read-backs, including the keystone
  `SP2_SURF_MARK=|alpha`, `SP2_WS_MARK=…`, `SP2_RES=…`, `SP2_LAYOUT=delta`, and the `surface:103`/`:108`
  inheritance reads. The round-2 re-capture is *better documented* than round 1's — commands, refs,
  exit codes, both streams — but it remains un-re-verifiable read-only. That is inherent, and it is
  why NEW-1 matters: when a datum cannot be re-run, the *reasoning around it* is all a reader has.
- All `--env` / `--env-file` acceptance and the four `--env-file` semantics on either spelling.
- Both negative-control exit codes; `--mask` rendering; `--layout surfaces[].env`.
- Whether `cmux rpc surface.create` accepts an env param — and NEW-2 shows this is now *harder* than
  the doc states, since the param name must also be guessed.
- Cross-session ref coherence: `workspace:41` / `surface:107`/`:108` continue the monotonic sequence
  above the first session's `38–40` / `99–105`, and none survive. Corroboration, not proof.

---

## Review hygiene

Every command was read-only: `--version`, `--help`, `ping`, `capabilities`, `list-workspaces`,
`rpc workspace.env` (a read method), `workspace env --json`, plus `git show`/`diff`/`grep` and two
repo test scripts. **I created, modified and destroyed no cmux workspace or surface**, ran no `git
stash`, and wrote no file other than this report. `git status --short` before and after: the same two
modified controller artifacts (`.dispatch-log`, `context-observations.log`) plus this report.
`cmux list-workspaces` returned the same set at start and end; I assert the **set**, not the order,
per round 1's observation that sidebar order varies with no mutating command.

## Suggested disposition for round 3

Documentation-only. No probe re-run. No transcript deleted.

1. **NEW-1 — BLOCKING.** Replace the "never recorded at all" inference in the doc's Step C and in N76
   clause (1) with the true narrower claim (`new-surface --env` does not write the **workspace-level**
   configured env; the configured view is blind to surface-scoped env by construction — cite the
   `--layout` finding). **Owner split: doc + N76 are in Task 1's write scope; `deviations.md` line 64
   is NOT — that clause is controller action.** Only item 1 blocks.
2. **NEW-2 — IMPORTANT.** Fix the axis-3 rpc transcript (use `workspace_id`, or state the `workspace`
   key is itself ignored), and add the param-name obstacle to the residual. If the severity is
   challenged, the defensible core is the **understated residual**, not the staged-contrast defect.
3. **NEW-3 — MINOR.** One clause on the sweep's extraction semantics.
4. **NEW-4 — MINOR.** Qualify the branch-summary sentence.
5. **NEW-5 — MINOR.** Narrow N67's UPDATE to "exercised on `new-workspace`; `workspace create`'s
   inherited-process half is the first session's un-re-verifiable capture."
6. **NEW-6 — MINOR.** One sentence disposing of the quoted **SSH startup env** half under §"The one
   per-surface env channel."

**Required mechanical gates for round 3 — not optional.** Items 1 and 5 both re-edit BACKLOG rows, and
a surgical edit inside N76's clause (1) is exactly the kind of change that drops a pipe. Re-run the two
gates the round-2 fix ran, and report their output:

- unescaped-pipe count **= 8** on every edited row (negative-lookbehind count, matched against the
  header and the N72/N75/N51 controls);
- `git diff --unified=0 -- BACKLOG.md` showing hunks **only** at the intended row lines.

N54 and N57 sit corrupted at 9 and 11 pipes today precisely because that check was not run once.
