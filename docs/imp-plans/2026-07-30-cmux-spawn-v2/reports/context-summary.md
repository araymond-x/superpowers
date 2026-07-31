# Context Summary — cmux-spawn-v2, Module 1 midpoint (after Tasks 0 and 1)

Written at the manifest's `context_summary_at: 2` boundary, before the Task 2 dispatch. Compresses the completed tasks' reports so a fresh controller can resume without re-reading ~180KB of flight recorder. Source reports remain in `reports/` and are authoritative where this summary is terse.

## Where the sprint stands

| | |
|---|---|
| Feature | `docs/imp-plans/2026-07-30-cmux-spawn-v2/` — parent + 4 modules, 19 tasks (0–18) |
| Module | 1 of 4 — "Contracts, cold-start measurement, spikes", tasks 0–3 |
| Complete | **Task 0** (11/11 boxes, commit `474c1bb`), **Task 1** (4/4 boxes, commit `9669b09`) |
| Next | **Task 2** (SP1 — `context-probe.py` `[task N fix]` attribution root cause), then Task 3, then the Module 1→2 transition |
| Tier | `standard`. Dispatch, spec review, quality review, partner review all **dispatched**, not self-written |
| Baseline | unit suite 641; `verify-symlink-install.sh` 104/0/0; plan gate PASS / 0 blockers / 0 warnings on all 5 files; tree clean; zero residual cmux probe workspaces |

## Task 0 — contract verification + cold-start measurement (COMPLETE)

Captured the installed binary's per-verb shapes as fixtures and measured true cold start. Round-1 quality review found **17 surviving mutations**; the fix round closed them and round-2 re-review returned **APPROVED** (71 mutations, 0 survivors, 38/38 expected-RED caught, 4 negative controls held GREEN).

**Findings that bind later modules — these are the reason to read this section:**

- **`rename-tab` and `close-surface` resolve refs within the CALLER's workspace unless `--workspace` is passed.** `send` / `send-key` / `read-screen` resolve cross-workspace with a bare `--surface`. The successor surface is by definition not in the caller's workspace. → **Pending Module 3 amendment.**
- **The directory-trust modal is a live handshake-failure mode.** An interactive launch into an untrusted `--working-directory` raises a modal and sits there — never reaching SessionStart, so the token never signals: `handshake=timeout` plus a consumed hop on a session one keystroke would have fixed. A fresh worktree is exactly that case. → **Pending Module 3 decision** (trust preflight).
- **A1 answered — `surface_uuid_source.available = true`** via `cmux identify --json --id-format both`, key `caller.surface_id`. Deferred order B3 therefore resolves to IMPLEMENT, not decline; operator addendum #1 is buildable.
- **A2 answered — `wait_for_latching = true`.** Task 10's two-call re-wait is sound as designed. The latch is ONE-SHOT and consumed only by a *successful* wait, which is exactly what makes the re-wait safe.
- **A3a answered — the `/rc` anchor is `/remote-control is active`.** Bare `/remote-control` is unsafe: the composer expands the alias so it appears in the submitted line too. Same defeat applies to `/rename` → use `Session renamed to:`.
- **`default_seconds = 60`, but the 60s FLOOR dominated** — `max(60, 2 × 11) = 60`. Measured runs `[11, 10, 11, 8, 8]`. Task 9's import assertion must say *"spec floor; Task 0 measured 8–11s cold start"*, not imply 60 was measured.
- **The awk bug (finding 4) had a CONSUMER half.** Module 3's `list-pane-surfaces` parser read `$1`, which returns `*` on a real selected row because the `* ` marker is its own field. The broken branch wins deterministically on the only path that reaches it. Fixed by plan amendment `949d310` — the parser now matches `surface:N` by PATTERN. Verified against five real shapes.

## Task 1 — SP2 `--env` / `--env-file` probe + disposition (COMPLETE)

Review tier **upgraded minimum → standard** by controller decision (shared file with three writers this module; the deliverable is a factual claim about the CLI surface, and this repo has already filed two BACKLOG rows on false premises). Four review rounds; the adversarial quality review found a real defect on a green upstream **three consecutive times** across Tasks 0–1.

**Disposition (settled, do not reopen):** `--env`/`--env-file` work exactly as documented but cannot subtract the spawn script's quoting machinery. The primary `new-surface` topology has **no env channel any documented CLI verb reaches** (127-verb sweep, exactly one `--env` hit: `new-workspace`). Adopting `--env` on the fallback alone would fork the shared wrapper Decision 2 exists to unify. → BACKLOG **N79** filed (renumbered from N76 after the Task 2 partner review found that `main` already claims N76 for the sibling SP1 row); **N67** upgraded a-help → a-run and partially closed as a topology-conditioned watch item.

**Method lessons worth carrying:**

- **A negative control reversed an apparent find.** `cmux new-surface --env FOO=bar` returns exit 0 / `OK surface:N` — but so does `--sp2-not-a-real-flag`, because `new-surface` **silently ignores unknown flags** while `workspace create` strictly validates. Without the control this would have been the repo's third false-premise row. **Never infer capability from an exit code.**
- **`cmux workspace env` is not ground truth.** It reports the workspace-level *configured* set only — it is blind to per-surface layout env and misreports protected `CMUX_*` keys (which are silently stored and only overridden at spawn).
- **`cmux rpc <method> [json-params]` is a CLI path to arbitrary v2 methods.** It invalidated an earlier "no CLI path exists" bound, which was withdrawn from five locations. It also **silently ignores unrecognized param names** — `{"workspace": …}` is ignored, `{"workspace_id": "<uuid>"}` is honored — so settling whether `rpc surface.create` takes an env param needs a correctly-guessed param name *plus* a create *plus* a read-back.
- **Sweep per finding, not per severity.** Round 3 swept exhaustively for the BLOCKING finding (five sites found where the review named three) but fixed the lesser findings only at named sites, leaving one gap in the BACKLOG row — closed in round 4.

## Live SP1 evidence captured out-of-band (read before dispatching Task 2)

`reports/sp1-live-observation-controller-session.md` records a probe reading of **539,691** followed by **305,208** minutes later on the controller's own transcript, with both instruments agreeing on the re-run. Sidechain contamination and cross-session entries are **ruled out by evidence**; the residual hypothesis is auto-compaction, stated as a hypothesis and not established. Two consequences for Task 2: the probe total is **not monotonic**, so the plan's suggested *"drop rows that jump >50% against both neighbors"* exclusion rule would discard true pre-compaction peaks; and the archived `373139` row's spike shape is consistent with BOTH misattribution and a genuine pre-compaction peak, so the implementer must positively discriminate rather than infer from the shape.

## Standing process constraints (carry into every remaining dispatch)

- **Reviewer premises are claims to verify, not verdicts to execute.** Two premises were wrong this sprint and both refusals were upheld on independent verification.
- **A finding with a CONSUMER half needs a PLAN EDIT, not a register row.** `transition-module.py` archives the completing module's reports at the boundary, so anything left only in a report is unfindable by the module that must act on it.
- **Plan amendments must be net-zero in line count** — the 200-line `validate-plan.py` cap has bitten twice. Module 3 Task 9 sits at exactly 200. **Operator has authorized a compression pass (register row OP-1) before Task 9's next amendment** — run it as a discrete step at Module 3 entry, never folded into a semantic change.
- **Every `controller-checkpoint.py` run needs `--manifest` AND `--deviations-file` AND `--reports-dir`** (the N35 trap; argparse marks the latter two optional but the phase handlers hard-require them). Exit 2 means warnings present, not failure.
- **Check 5c** (checkpoint file) has no Task-0 exemption; **Check 5d** (partner review) does. The hook checks the FILE exists — redirect script output to disk.
- Hand-written reports: ATX `## Section` headings, never `**Section:**`; `tests.written` is an int; `tests.passing` may not exceed it.
- `handoff_spawn` must appear in NO frontmatter until Task 4 lands the model field (`Plan` is `extra=forbid`).
- Never `git stash` in this tree; stage explicit paths; never `git add -A`. The `.venv` is a symlink to the main checkout — never recreate it.

## Undispositioned register entries (all Pending are owned)

| Row | Owner |
|---|---|
| `rename-tab`/`close-surface` need `--workspace` | Module 3 amendment |
| Trust-preflight decision | Module 3 decision |
| N72 absorption (4th enumeration hole: `--json` works but is absent from help AND from the binary's own "Known flags" error) | N72 |
| `cmux workspace <sub> --help` prints noun help — canonical spelling never shows `--env` | N70 / N58 |
| Pre-existing N54/N57 BACKLOG pipe corruption (9 and 11 vs header's 8) | Unowned — do NOT fix, do NOT propagate |
| OP-1 Task 9 compression pass | Module 3, before its first amendment |
| Deferred audit orders B1, A3b/c+B2, B3, B4, B7, B8a | Their owning tasks — see Deferred Work table |
| **N67 will conflict on merge** — `main` edited it since the merge-base and so did this branch. The resolution MUST preserve both sides: main's edits AND this branch's `UPDATE 2026-07-30 — DISPOSITIONED BY N79` clause. A "take theirs" drops the discharge instruction and sends a future reader to re-run a probe already run. Rows main touched since `fa2d482`: N55, N56, N57, N61, N63, N64, N66, N67, N68, N70, N73, plus new N76–N78 | Merge step |
| **Task 3 must allocate ids against `main`, not this branch.** Free on both: **N80, N81**. Enumerate at execution time rather than trusting these | Task 3 |
