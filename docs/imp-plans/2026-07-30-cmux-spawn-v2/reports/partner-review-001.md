# Task 1 — Controller Partner Review (round 1)

**Verdict: BLOCKED** — 2 blocking, 4 should-fix, several minors. Tier upgrade judged **justified**.

Partner verified by reading: the proposed prompt, `module-1-contracts-spikes.md`, `plan.md`, root
`CLAUDE.md`, `deviations.md`, `task-000-implementer-report.md`, BACKLOG rows N56/N57/N67/N70/N72,
and one live read-only `cmux workspace --help`.

## BLOCKING

### B1 — `cmux new-surface --help` dropped, and the trap section displaces it

Plan Step 1 requires **two** help surfaces: `cmux workspace create --help` **and**
`cmux new-surface --help` ("any surface-scoped env equivalent? Per the 2026-07-30 planning check
there is none in the flag list — confirm and record"). `spec-distilled.md:111` makes it a
spec-level deliverable: probe transcript for `new-workspace --env`/`--env-file` **+ any
surface-scoped equivalent**.

The prompt's only enumeration was `{workspace create, new-workspace}` — a **substitution, not an
addition** — placed inside the section the implementer is told to "read twice", so it would
plausibly be taken as the definitive probe list and Step 1 considered satisfied.

Why it matters more than a dropped line: this sprint's **primary** topology is a surface in the
caller's workspace; `workspace create` is the demoted **fallback**. The surface-scoped-env question
governs the primary path, while the prompt scoped the whole task to the fallback.

### B2 — Disposition question missing its scoping qualifier; N67 never given to the implementer

(a) Plan Step 3 asks whether `--env` can replace the inline-env prefix on the FALLBACK path
**"(scalars only; the append-prompt is content and stays on the rematerialization path)"**. The
prompt dropped the parenthetical in both places it posed the question. Without it the implementer may
answer a different question ("can `--env` carry everything?" → no → wrongly closes N67 as not-viable)
or over-claim the other way.

(b) The prompt says "close BACKLOG N67's premise accordingly" but never tells the implementer to read
N67 or where it lives. An implementer cannot close a premise it has not read.

These are one fix because **N67's own text supplies the counterweight the prompt lacked**: it records
that the append-prompt is CONTENT not a scalar, that `--env-file` may still serve, that reserved
`CMUX_*` names cannot be overridden, and it self-grades "a-help … not exercised — probe before
building."

This also corrects an asymmetry: the trap section spent ~15 lines guarding against wrongly concluding
**absence** and zero against wrongly concluding **sufficiency** — yet the risky disposition here is
(a) viable, since the flags' existence is already known at a-help confidence and the open question is
whether they *work* and *suffice*.

## SHOULD-FIX

- **S1 — Step 2's `2>&1` repeats a bug Task 0 already fixed.** Plan Step 2 does
  `W=$(cmux workspace create … 2>&1)` then `awk '{print $2}'`, feeding the result to
  `cmux workspace env`. Task 0 split stdout/stderr precisely because no verb writes error text to
  stdout. If `create` rejects `--env`, `W` holds error text, field 2 is garbage, and it is passed on —
  producing a second confusing error readable as the probe result. Capture streams separately; gate on
  **exit code**, not field 2.
- **S2 — Task 0 reproduced the `--help` gotcha live, in this sprint** (`--id-format` documented in
  neither `identify --help` nor `list-pane-surfaces --help`). Stronger and one task old vs. the
  2026-07-29 history cited.
- **S3 — Cross-workspace verb scoping is load-bearing for Step 2.** Task 0 established
  `send`/`send-key`/`read-screen` DO resolve cross-workspace with a bare `--surface`, while
  `rename-tab`/`close-surface` do not. Step 2 sends to and reads the throwaway workspace from the
  caller's session, so the positive half is needed to avoid misdiagnosing a failed send.
- **S4 — The "two false premises" warning is one-directional.** The claim is an accurate relay of
  `CLAUDE.md`, but per N72 one of the two (**N56**) died to a `--help` call **never being run** — the
  opposite error. N57 is the genuine over-trust case. Both failure modes are reachable in Task 1.

## Minors

- Overstatement: the prompt said the contract doc covers `--mask` as a semantic "`--help` omits
  entirely". Partner read `--mask` directly off the installed binary (`cmux workspace --help` shows
  `env [workspace] [--mask]`, "(--mask redacts the values)"). Not omitted.
- BACKLOG placement: max id is **N75** (next free N76) but the last row in *file order* is **N51** —
  the tail is not numerically ordered, so a literal "append to end" misplaces the row.
- The alias question (`workspace create` vs `new-workspace`) resolves in one call —
  `cmux workspace --help` says create takes "same flags as new-workspace" — and **N70** already
  records the legacy-alias/deprecation-hint relationship. Point at those rather than hand over the answer.
- "Write scope — exactly two files … Nothing else" sits in tension with the later instruction to write
  the implementer report. Scope that sentence to the change.

## Verified correct — preserved unchanged

Contract Constraints verbatim (character-for-character) and correctly framed as STOP-and-report-BLOCKED;
write scope matches the Write-Scope Partitioning table and Task 1's Files block; BACKLOG append
discipline matches the plan prose (and correctly strengthens the execution-time-id rule from Task 3 to
Task 1); **escalation path honest** — BLOCKED/NEEDS_CONTEXT both offered, "report the contradiction and
stop", "an honest 'could not determine' is worth more than a confident guess", no pressure toward a
confident answer; every `CLAUDE.md` claim in the trap section checks out; cmux hygiene correct
(`--focus false` convention, workspace=sidebar/surface=top-tab gloss, zero-residual assertion matching
Module 1 Acceptance Criteria); report-shape guidance right and hard-won.

## Tier upgrade: JUSTIFIED

Reason (b) is load-bearing: minimum-tier review checks conformance to the task, not correctness of the
conclusion — and here the conclusion *is* the deliverable, in a repo with a documented history of
false-premise rows. Reason (a) (shared BACKLOG.md) is true but weaker alone, since Task 1 writes first
and only appends. No gate is affected. Not unnecessary process weight.

---

# Task 1 — Controller Partner Review (round 2)

**Verdict: APPROVED.** All eight round-1 findings CLOSED; nothing in the "verified correct" list was
broken; 3 non-blocking improvements raised, **all applied by the controller before dispatch**.

Partner re-verified against the live binary and the repo, not by reading the revision alone:

- Contract Constraints diffed programmatically against `module-1-contracts-spikes.md` module header →
  `IDENTICAL: True`. Still framed as STOP-and-report-BLOCKED.
- `cmux workspace --help` → `env [workspace] [--mask]` … "(--mask redacts the values)" and
  `create [flags]  Create a workspace (same flags as new-workspace)` — both fresh claims accurate.
- `cmux --help` → `read-screen` IS listed (so **N56 = the enumeration was never read**), while
  `workspace-group` and `claude-hook` are absent (so **N57 = help-silence over-trust**). The
  revision's two-mechanism split is therefore correct, not a rhetorical flourish.
- Task 0's `--id-format` finding and its cross-workspace verb scoping match
  `task-000-implementer-report.md` and the Task 0 `deviations.md` rows.
- BACKLOG max id N75 / main-ledger tail N51 (the later `N6, N8, N9` line belongs to the Sprint-3
  table, which is why a literal append misplaces a row).

**The third failure mode the revision added — "concluding a flag is SUFFICIENT because it exists" — was
judged correct rather than padding:** both N67 and matrix §2.7 self-grade the flags as
"a-help … not exercised — probe before building", so existence is already settled and only sufficiency
is open; disposition (a) proposes touching shipped spawn machinery; and N67 names two concrete
sufficiency blockers (append-prompt is content; reserved `CMUX_*` unoverridable).

## The three non-blocking findings, and how each was applied

1. **The prompt set an evidence bar it did not equip the implementer to clear.** Step 1 item 3
   pre-announced the answer ("there is none in the flag list — confirm and record") while a later line
   ruled that "not in `--help`" alone is an insufficient basis. An implementer could reproduce the N56
   pattern *while following the prompt exactly*. **Applied:** absence now requires two independent
   checks — the CLI contract's flag table (URL from `cmux docs api`) and a **live rejection probe**
   (`cmux new-surface … --env SP2_PROBE=alpha`), with acceptance flagged as a significant finding of
   the same class `--id-format` fell into.
2. **Two deliberate departures from plan text could not reach the ledger.** The dispatch directs three
   help surfaces where the plan lists two, and separated streams where the plan uses `2>&1`;
   `deviations.md` is outside Task 1's write scope. **Applied:** a Reporting bullet now requires the
   implementer to name any departure from the plan's literal text and why — the same path by which
   Task 0's stdout/stderr split reached the register.
3. **`cmux workspace env` was never requested as a capture**, though it discriminates the two halves of
   the sufficiency question (env *configured on the workspace* vs. env *actually inherited by the
   process*). **Applied:** named as a required output, paired with the in-surface `echo $SP2_PROBE`
   read-back, with the explicit note that a flag recording a value without exporting it would look
   successful from one half alone.

Partner found no internal contradictions beyond #1, no conflicts with the plan, and no pressure toward
a predetermined disposition. On length: 137 lines, task summary at line 18, Step 1 at line 49 — the
trap section interrupts the procedure but the task is not buried, and the prompt correctly makes the
plan's four steps the authority.
