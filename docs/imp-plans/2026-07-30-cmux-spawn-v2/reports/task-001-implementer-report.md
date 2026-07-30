---
schema_version: 1
task_id: 1
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md
    description: "SP2 probe transcript + disposition doc (created): three help surfaces verbatim, live exercise of --env/--env-file on the canonical spelling, both-halves verification (configured + inherited), primary-path answer on three independent axes, four doc-vs-binary divergences, disposition, could-not-establish list, cleanup proof, deviations table."
  - path: docs/process-improvement-findings/BACKLOG.md
    description: "Appended exactly one row (N76, the SP2 disposition) after N75 and before N51; no other line touched."
tests:
  written: 0
  passing: 0
  command: "bash tests/ARaymond-installation/verify-symlink-install.sh"
  result: PASS
contract_compliance:
  - constraint: "Per-verb OK shapes (parent plan Shared Contract Section item 1)"
    status: compliant
    detail: "Every shape observed matched Task 0's fixtures: `OK workspace:38` from workspace create, `OK surface:100 pane:38 workspace:38` from new-surface. No contradiction found."
  - constraint: "Measurement method pinned (true cold start; shipped default = measured p95 x 2)"
    status: not_applicable
    detail: "Task 1 performs no timing measurement and did not read or modify cold-start-timing.json."
  - constraint: "Screen polling is a measurement instrument only, never the production readiness signal"
    status: compliant
    detail: "read-screen was used solely to read back inherited env values in throwaway workspaces. No production code changed; nothing gates on a screen read."
  - constraint: "Write scope: exactly two changed files"
    status: compliant
    detail: "git diff --cached showed exactly the two allowed paths. No production code, plan files, test files, or deviations.md touched."
  - constraint: "handoff_spawn must appear in no frontmatter until Task 4"
    status: compliant
    detail: "grep -c handoff_spawn returned 0 for both changed files, and this report's frontmatter does not use it."
  - constraint: "Never git stash; never git add -A; stage explicit paths"
    status: compliant
    detail: "No stash was run. Both paths staged explicitly; the controller's in-flight artifacts (deviations.md, .dispatch-log, context-observations.log, checkpoint-pre-dispatch-001.json, partner-review-001.md) were left unstaged and are absent from the commit."
  - constraint: "The .venv symlink must never be deleted or recreated"
    status: compliant
    detail: "Not touched. No venv operation was performed."
  - constraint: "Zero residual sp2-* workspaces (Module 1 acceptance)"
    status: compliant
    detail: "All three created workspaces closed (exit 0 each); full `cmux list-workspaces` re-read and pasted in the doc shows no sp2-* entries."
---

# Task 1 — SP2 workspace `--env` / `--env-file` probe + disposition

## Implementation Summary

Probed cmux's workspace/surface environment-variable surface on the installed binary
(`cmux 0.64.20 (100) [14e3400b9]`, re-pinned live; `cmux ping` → `PONG`), exercised `--env` and
`--env-file` end to end, answered both the fallback-path and primary-path halves of the SP2 question,
and recorded the disposition plus one BACKLOG row (N76).

**Disposition: (a) viable — fallback path, scalars only — with a recommendation NOT to adopt it in
this sprint.** N67's premise is **partially closed**: the flags are real and work exactly as
documented (upgraded a-help → a-run), but the *benefit* N67 claimed — subtracting the spawn script's
quoting machinery — does not materialize, because the sprint's primary topology (a surface added to
an **already-existing** workspace) can receive environment variables through no cmux channel. Stated
precisely, because the broader claim would be false: a per-surface env channel **does** exist
(`--layout` `surfaces[].env`, exercised and working), but only at workspace-creation time, so it
cannot serve the primary path. Detail and full transcript:
`docs/process-improvement-findings/2026-07-30-sp2-workspace-env-probe.md`.

Commit: `811b19e docs(cmux-spawn-v2): SP2 — workspace --env probe transcript + disposition`.

## Source Files Read

Authority sources, read before and during execution:

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-1-contracts-spikes.md` — module header (Source
  Contracts, Contract Constraints, write-scope partitioning) and `### Task 1`, all four steps.
- Root `CLAUDE.md` — read in full before starting, per the prompt's non-optional instruction;
  specifically the "cmux Auto-Spawn Handoff" section (the `--help`-is-not-an-enumeration trap, the
  Workspace/Surface vocabulary inversion, the "binary outranks docs for contract" rule, and the
  no-line-numbers/no-counts policy).
- `docs/process-improvement-findings/BACKLOG.md` — rows **N67** (the premise this task dispositions),
  **N70** (legacy-alias / deprecation-hint relationship), **N72** (how the two earlier false-premise
  rows failed, by two different mechanisms). Also enumerated every `N`-id at execution time to pick
  the next free one.
- `docs/process-improvement-findings/2026-07-28-cmux-capability-usage-matrix.md` **§2.7** — N67's
  detail and its own `a-help` confidence grading.
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md` — the SP2 row making "any surface-scoped
  equivalent" an explicit spec-level deliverable, plus Decision 2 (one shared wrapper, same inline
  env for both topologies) and the sent-command env rule.
- `docs/process-improvement-findings/2026-07-29-cmux-mode-option-surface.md` — house style for this
  directory, and the source of the `a-run`/`a-file`/`a-help`/`inferred` confidence-label convention
  reused in the disposition doc.
- `skills/scripts/models/implementer_report.py` — the strict report contract (`extra="forbid"`, the
  `TestResult` and `ComplianceStatus` literals), read after the first validation failure.
- Upstream `docs/cli-contract.md` — fetched at execution time from the URL reported by
  `cmux docs api` (not hardcoded); §"Workspace environment variables", the `new-surface` row, and
  §"Current Help Caveats".

The installed binary itself was the primary authority throughout, per the "binary outranks documents
for contract" rule.

## Evidence And Findings

### Help output captured, and which spelling each came from

Three spellings were probed, not the plan's two.

1. **`cmux workspace create --help`** (exit 0) — did **not** print create-specific help. It printed
   the `cmux workspace` **noun** help, whose only mention of the flags is the pointer
   `create [flags]   Create a workspace (same flags as new-workspace)`. **It never lists `--env` or
   `--env-file`.** This is uniform, not create-specific: `cmux workspace env --help` and
   `cmux workspace close --help` print the identical noun help. So the **canonical** spelling's help
   never documents the env flags — an irony for N70, which wants the spawn script migrated to exactly
   that spelling.
2. **`cmux new-workspace --help`** (exit 0) — the **only** `--help` that documents the flags:
   `--env KEY=VALUE  Set a workspace environment variable. Repeatable. Reserved CMUX_* variables
   cannot be overridden.` and `--env-file <path>  Load KEY=VALUE lines from a file. Repeatable.`
   Also `--layout <json>` ("Layout surfaces define their own commands") and `--focus` defaulting to
   `false`.
3. **`cmux new-surface --help`** (exit 0) — **no env flag**; `grep -i env` over both streams returned
   no match.

All three are reproduced verbatim in the disposition doc.

### The alias question (N70)

Resolved four ways, three agreeing on documentation and one on behavior: the noun help's "same flags
as new-workspace"; the upstream contract's "(and the same flags on `cmux workspace create`)"; the
**live exercise** (`cmux workspace create … --env … --env-file …` → exit 0, `OK workspace:38`); and
`workspace create`'s own unknown-flag **error message**, which enumerates `--env KEY=VALUE,
--env-file <path>`. The legacy deprecation hint also fired live during cleanup, confirming N70's
premise verbatim.

### Fallback path — exercised, both halves

`cmux workspace create --name sp2-env --focus false --env SP2_PROBE=alpha --env SP2_SECOND=beta
--env-file <fixture>` → exit 0.

- **Configured view** (`cmux workspace env workspace:38`) returned all four keys and confirmed all
  four documented `--env-file` semantics in one output: `#` comments ignored, blank lines ignored,
  leading `export ` stripped, and `--env` overriding a same-key file value (`SP2_PROBE=alpha`, not
  `from_file_should_lose`).
- **Inherited view** (send + `read-screen` inside the workspace's surface) returned
  `SP2_WS_MARK=alpha|beta|file_plain|file_export` — **all four values reached the process
  environment.** The flags genuinely export; they do not merely record.
- A surface created **later** in the same workspace also inherited the workspace env, confirming the
  contract's "every pane, surface, and split created later in that workspace".

### Primary path — is there a surface-scoped env equivalent?

**No.** There is no env channel that can reach a surface added to an already-existing workspace.
Established on three independent axes, because "not in `--help`" is a documented-insufficient basis
here:

1. **Upstream contract flag table** — documents `--env`/`--env-file` only for
   `new-workspace`/`workspace create`; the `new-surface` row is bare ("Create a surface inside a
   pane."). This is the source that documented `--env` when `--help` did not, so its silence carries
   weight.
2. **Live rejection probe + negative control** — see the next section; the flag is accepted and
   ignored.
3. **Mutation is impossible** — `workspace env` is read-only (`workspace env set` → exit 1 "Invalid
   workspace handle: set"; `workspace env <ws> --env K=V` → exit 1 unknown flag; `set-environment` →
   exit 2 unknown command), and `cmux capabilities` exposes exactly one env-related method across the
   whole RPC set (`workspace.env`, the read), with none among the 26 `surface.*` methods.

The one per-surface channel that **does** exist — `--layout` `surfaces[].env` — was exercised and
**works** (`SP2_LAYOUT=delta` read back, with the per-surface `command` running too). But `--layout`
is a flag on **workspace creation**, so it cannot add a surface to an existing workspace and does not
serve the primary path.

### The near-miss worth recording

`cmux new-surface --workspace workspace:38 … --env SP2_PROBE=alpha` returned **exit 0 /
`OK surface:100`** — which reads as the discovery of an undocumented flag, exactly the class
`--id-format` fell into. A negative control refuted it: `--sp2-not-a-real-flag zzz` is **also**
accepted (exit 0). `new-surface` **silently ignores unknown flags**. The read-back closed it
empirically — a surface created with `--env SP2_SURF=gamma` reported `SP2_SURF_MARK=|alpha`, i.e.
`SP2_SURF` **empty**. By contrast `workspace create` strictly validates (exit 1 on the same garbage
flag). **Two commands on one binary with opposite unknown-flag policies.** Without the control this
task would have filed a third false-premise row.

## Testing

No automated tests were written: this is a docs-only change whose deliverable is a probe transcript.
Ran the required `bash tests/ARaymond-installation/verify-symlink-install.sh` → **PASSED, 104 passed,
0 failed, 0 warnings.**

Table integrity of the appended BACKLOG row was verified structurally rather than by eye: a count of
**unescaped** pipes (`(?<!\\)\|`) gives 8 for my N76 row, matching the header and the N75/N51/N67/N72
control rows exactly. An initial naive count flagged a false imbalance because escaped `\|` bytes
still match a plain `|`; three literal pipes inside `SP2_WS_MARK=alpha|beta|…` were genuinely
unescaped and were fixed to `\|` per the file's existing convention before commit.

## Deviations from Plan

`deviations.md` is outside this task's write scope, so this report is the only path by which these
reach the deviations register. They are also tabulated in the disposition doc.

**Controller action required: all seven departures below need a `deviations.md` entry.** That
includes the two marked prompt-directed — being directed by the dispatch prompt makes a departure
*authorized*, not *recorded*, and the plan's literal text still says something different from what
was executed. Do not treat items 1–2 as pre-approved and skip them.

**Prompt-directed (2):**

1. **Probed three help surfaces where the plan lists two.** Added `cmux new-workspace --help` because
   `CLAUDE.md` documents the flags on that spelling. This produced the finding that
   `workspace create --help` never shows the flags at all.
2. **Captured stdout/stderr separately and gated on exit code**, rather than the plan's Step 2
   `2>&1` + `awk '{print $2}'`. Task 0 set this precedent; merged streams would have fed error text
   into `cmux workspace env` as a garbage ref.

**Self-initiated (5):**

3. **Used a real `--env-file` fixture instead of the plan's `/dev/null`** — one file carrying a plain
   `KEY=VALUE`, an `export ` line, a `#` comment, a blank line, and a key `--env` also sets. `/dev/null`
   proves nothing, and N67 explicitly asks that `--env-file` be probed. This single fixture tested all
   four documented semantics plus the precedence rule at once.
4. **Added workspace-env mutation probes** (four spellings) **plus `cmux capabilities`.** The
   primary-path conclusion otherwise rested on two documents and zero probes — the N56/N57 shape.
5. **Added an unknown-flag negative control on both commands.** Decisive; see "near-miss" above.
6. **Added a reserved-`CMUX_*` probe.** `--help`'s "cannot be overridden" is an a-help *behavior*
   claim, and this repo has a documented case of one being wrong (`pipe-pane` "stream" → one-shot).
7. **Exercised `--layout` `surfaces[].env`.** The contract asserts a per-surface env channel; the
   primary-path answer is only honest if that claim is tested rather than waved off.

## Self-Review Findings

Reviewing my own work before handing it off, worst-first:

1. **I nearly filed a false-premise finding, and only a control caught it.** `new-surface --env`
   returning exit 0 / `OK surface:100` is exactly what a working undocumented flag looks like, and the
   prompt had pre-announced that acceptance "is a significant finding". The honest account is that my
   first reading was wrong and the negative control (`--sp2-not-a-real-flag`, also exit 0) reversed
   it. Anyone re-reading this evidence should note the *control*, not the acceptance, is what carries
   the conclusion.
2. **My first structural check of the BACKLOG row was wrong and reported a false alarm.** Counting
   `|` bytes flags escaped `\|` as unescaped. Corrected to a negative-lookbehind count validated
   against four known-good control rows — but the three literal pipes it eventually found *were* real
   and would have broken the table, so the check was worth redoing rather than dismissing.
3. **My first report frontmatter failed validation on four counts** (missing `schema_version`, a prose
   `tests.result` where the model wants `PASS`/`FAIL`, `status: consistent` where the enum wants
   `compliant`, and an extra `task_title` key under `extra="forbid"`). Caught by running
   `validate-report.py` rather than by inspection. Noted because the task-000 precedent shows report
   shape costing a debugging cycle.
4. **Axis 3 is narrower than it may read.** "No mutation is possible" is established for the **CLI**;
   `cmux capabilities` returns method names without schemas, so an undocumented param on
   `workspace.create`/`surface.create` is not excluded. I have stated this limit in both the doc and
   the "Could not establish" section rather than letting the stronger phrasing stand.
5. **One prompt expectation was not confirmed.** The prompt anticipated `new-surface --env` producing
   a *rejection* to capture verbatim. It produced silent acceptance instead. This is a difference in
   observed behavior, not a contradiction of a Contract Constraint, so it did not trigger the
   STOP-and-report rule — but it is the kind of thing a reviewer should see flagged rather than
   quietly absorbed.
6. **Disposition framing double-checked against the scoping qualifier.** I verified that my (a)
   answer is evaluated under "scalars only", and that I did not let the architectural cost (the
   forked env channel) push the answer to (b). The cost is recorded as a recommendation against
   adoption, not as evidence the flag fails — which the prompt explicitly warned about.

## Concerns

None blocking. Four things the reviewer and downstream tasks should see:

1. **N67 should stay open as a watch item, not be closed.** The flags work; the benefit is blocked by
   topology. If the surface topology is ever abandoned and `workspace create` becomes the only spawn
   path, `--env` becomes strictly better than the inline prefix and the subtraction becomes available
   in full. Closing N67 as "not viable" would misrecord this.
2. **Feeds N72 — a fourth enumeration hole, and a new kind.** `cmux workspace env --json` **works**,
   yet `--json` is omitted from both the noun help **and** the binary's own *"Known flags:
   --workspace, --window, --mask"* error message. N72's three recorded instances are all help/doc
   omissions; this is an **error message that claims to enumerate a command's known flags and omits a
   working one**, so a drift guard keying on help or error text inherits the hole.
3. **`cmux workspace env` is not ground truth.** Reserved keys are silently accepted and stored — the
   configured view cheerfully reports `CMUX_WORKSPACE_ID=BOGUS_WS` and `TERM=bogusterm` while the
   process gets the real values (protection happens at spawn, as the contract states and `--help`
   does not). It also does not show layout per-surface env. Anything reading it as the effective
   environment will be wrong.
4. **Untested-but-relevant:** `--layout` delivers per-surface `command` + `env` **atomically at
   create**, which further dissolves N57's "`new-surface` has no `--command`". Its fitness for the
   sprint's fallback spawn was **not** assessed — only a minimal two-pane layout was exercised. This
   is not a green light to rewrite the fallback around `--layout`.

## Could not establish

Recorded explicitly, since a wrong disposition here would become a third false-premise row:

1. **Whether `workspace.create` / `surface.create` accept an undocumented env param over the raw
   socket.** `cmux capabilities` returns method *names* only, no parameter schemas, and the socket was
   not driven directly. The established claim is narrower than "no such param exists": it is **"no CLI
   path reaches one"** — sufficient for the spawn script, which is a CLI consumer, but not a statement
   about the RPC layer.
2. **Whether `--layout` can express the sprint's full fallback spawn** (correct cwd + composed command
   + handshake) in one call. Capability proven; fitness unassessed.
3. **Dotfile-precedence exposure.** The contract states a `~/.zshrc` / `~/.zprofile` `export` of the
   same key **wins** over workspace env for the interactive shell. Not exercised — the probe keys are
   `SP2_*`, which no dotfile touches. Harmless for `SUPERPOWERS_*` names for the same reason, but any
   future adoption should not assume workspace env is authoritative for a key a dotfile might export.
4. **Behavior on any cmux build other than `0.64.20 (100) [14e3400b9]`.** Every a-run claim is pinned
   to that build; the contract URL resolves to `main` and may already describe a different one.

Nothing measured contradicted the prompt, the plan, or a pinned Contract Constraint, so no
STOP-and-report condition was triggered.

## Cleanup

Three throwaway workspaces were created — `sp2-env` (`workspace:38`), `sp2-reserved`
(`workspace:39`), `sp2-layout` (`workspace:40`); `sp2-ctl` was never created, its create being the
exit-1 negative control. All three closed with `cmux workspace close` (exit 0 each), all named
`sp2-*`, all created with `--focus false` per the fork convention. `cmux list-workspaces` was then
re-read in full and pasted into the disposition doc: **zero residual `sp2-*` entries**, satisfying
Module 1's acceptance criterion.
