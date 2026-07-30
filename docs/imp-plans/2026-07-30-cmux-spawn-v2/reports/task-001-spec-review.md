# Task 1 — Spec Compliance Review

**Verdict: PASS**

Module 1 Task 1 conforms to `module-1-contracts-spikes.md` `### Task 1`. All four steps executed with
their required outputs present, write scope is exact, the disposition answers the plan's scoped
question inside its option set, and the headline claims trace to captured evidence — including the
load-bearing negative control.

## Verified by re-running read-only commands

| Claim | Independent check |
|---|---|
| Binary pinned `cmux 0.64.20 (100) [14e3400b9]` | `cmux --version` exact match; `cmux ping` → `PONG` |
| H1: `cmux workspace create --help` prints the **noun** help, never lists `--env` | Confirmed — byte-matches the doc's transcript |
| H2: `new-workspace --help` is the only help documenting the flags | Confirmed verbatim, incl. "Reserved CMUX_* variables cannot be overridden" |
| H3: `new-surface --help` has no env flag | `grep -i env` → rc=1, no match |
| Axis 3: exactly one env method in the whole RPC set | `cmux capabilities` → `"workspace.env"` only |
| "none among the **26** `surface.*` methods" | Enumerated: 26 unique, none env-related. Count exactly right (includes dotted names like `surface.resume.set`) |
| D2: the error message omits a working `--json` | `workspace env --env FOO=bar` → `Known flags: --workspace, --window, --mask`; `workspace env workspace:2 --json` → exit 0, well-formed JSON. **Both halves confirmed** |
| Step 4 cleanup — zero residual `sp2-*` | `cmux list-workspaces` — five workspaces, no `sp2-*`, no `workspace:38/39/40` |
| Step 4 `verify-symlink-install.sh` PASS | Re-ran: **104 passed, 0 failed, 0 warnings** |
| Contract-shape compliance vs Task 0 fixtures | `cmux-verb-shapes.json` carries the same `OK workspace:29` / `OK surface:77 pane:29 workspace:29` shapes the report claims it observed |
| Report is a valid artifact | `validate-report.py` → exit 0, `COMPLETE`, zero missing sections — matters because Self-Review #3 admits the first frontmatter failed four ways; the fix landed |

## Verified by reading files

- **Write scope.** `git show --stat 811b19e` = exactly the disposition doc (+509) and `BACKLOG.md` (+1).
  Nothing else. `git log` confirms `811b19e` is the *only* Task 1 commit, which is what makes the
  single `--stat` check conclusive.
- **BACKLOG appended, not rewritten.** Diff is one `+` line, zero `-` lines.
- **N76 correctness.** Free at commit time (`git show 811b19e^:…BACKLOG.md` → 0 occurrences; prior max
  N75). Placed after N75 and before the out-of-sequence N51 tail — consistent with the numeric block,
  not blind EOF. Table integrity: 8 unescaped pipes (negative-lookbehind count), matching the header
  and the N75/N51 neighbours. Cites the disposition doc by name.
- **Negative control recorded** — required, since the entire primary-path conclusion rests on it.
  Present in the doc (§Axis 2: `--sp2-not-a-real-flag zzz` → exit 0 on `new-surface` vs
  `workspace create` → exit 1 with an enumerating error), carried into the BACKLOG row, and named as
  Self-Review finding #1. The read-back (`SP2_SURF_MARK=|alpha`, empty) closes it empirically rather
  than by argument.
- **Contract Constraints honored.** `read-screen` used only to read env values back inside throwaway
  workspaces — instrument use, exactly as the module header licenses. The commit contains no
  production code, so no screen read could have become a readiness signal.

## Disposition-option judgment

**Within option (a), not an invented third option.** The plan's (a) is "viable → BACKLOG row proposing
the swap, this sprint still shipping the command string per Decision 2." The implementer answered (a)
on viability — exercised on *both* halves (configured view and inherited-process view) — and layered a
recommendation against adoption.

The discriminating evidence sits in the plan's own authority chain: `spec-distilled.md:59` Decision 2
states verbatim that **both** topologies use "ONE shared launch-and-handshake wrapper (same inline
env…)". Combined with the measured finding that the *primary* topology has no env channel on any axis,
a fallback-only swap would fork the very wrapper Decision 2 exists to unify. The implementer followed
the plan's cited authority to a conclusion the option prose did not anticipate — **a spike doing its
job, not hedging.** Self-Review #6 shows the trap was consciously avoided: the architectural cost was
recorded as a recommendation, not smuggled in as evidence the flag fails.

The primary-path investigation is **plan-mandated, not scope creep**: Step 1 asks for
`new-surface --help` ("any surface-scoped env equivalent? … confirm and record") and
`spec-distilled.md:111` makes "any surface-scoped equivalent" an explicit SP2 deliverable.

## Report honesty

Four concerns real and correctly non-blocking. On the axis-3 admission: stated in **three** places
(the doc's "Honest limit of axis 3" blockquote, the doc's "Could not establish" #1, Self-Review #4),
and the narrowing is the correct one — `cmux capabilities` returns method names without schemas, so
"no CLI path reaches such a param" is what the evidence supports, and the spawn script is a CLI
consumer, so the narrower claim suffices for the disposition. A properly bounded limit, not a blocker
buried in a caveat. Concern #4 (`--layout` fitness unassessed) is likewise fenced with an explicit
"not a green light."

## Non-blocking observations

1. **One deviation unrecorded — carry it as #8.** Option (a)'s consequent is "a row proposing the
   swap"; the row instead proposes a topology-conditioned *watch item*. This appears in neither the
   report's nor the doc's 7-item deviations table. Not concealed (Concerns #1 and the doc's "PARTIALLY
   closed" state it plainly), but those tables are the only route these departures take to
   `deviations.md`. **Controller action.** *(Done — logged as the eighth Task 1 row.)*
2. **Un-rerunnable claims, corroborated by coherence rather than re-execution.** The live read-back
   values and the two negative-control exit codes cannot be re-verified read-only — reproducing them
   creates workspaces. What holds: the refs form a coherent monotonic sequence above Task 0's fixture
   (`workspace:29`/`surface:77` → `workspace:38/39/40`, `surface:99–105`), and none of 38/39/40 survive
   in the live list. Internal-consistency corroboration, explicitly **not** re-execution.
3. **H1's transcript is elided, not literally complete** — the noun-help block ends `...` before
   `group <subcommand>`. The elided lines were confirmed real (`reconnect`, `disconnect`, `loading`).
   Honest abridgement; worth knowing if anyone diffs it against the binary.
4. **Downstream note for Task 3:** N76 consumed the next free id, so Task 3 must re-enumerate at
   execution time rather than assuming N76/N77 — which the module's Write-Scope prose already requires.
