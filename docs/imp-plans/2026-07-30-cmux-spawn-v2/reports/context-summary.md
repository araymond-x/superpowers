# Context Summary — cmux-spawn-v2, **MODULE 1 COMPLETE and transitioned**

Updated 2026-08-01 at the Module 1→2 boundary (superseding the Module-1-midpoint version, whose Task 0/1/2 detail is retained below). Compresses Module 1 so a fresh controller can resume at Module 2 without re-reading ~400KB of flight recorder. **The source reports now live under `reports/archive-Contracts, cold-start measurement, spikes/`** and remain authoritative where this summary is terse.

> **Why this file was hand-updated, not regenerated.** `context-summary.py` returns `{"error": "No implementer report files found"}` after a transition — **it is not archive-aware**, so it cannot see the reports `transition-module.py` just moved. This is the sibling of the N4/N27 archive-awareness fixes already applied to `controller-checkpoint.py`. Logged in `deviations.md`; file a BACKLOG row at merge. **Consequence: after every module transition the context summary must be written by hand, or the script taught to glob `archive-*/`.**

## Where the sprint stands

| | |
|---|---|
| Feature | `docs/imp-plans/2026-07-30-cmux-spawn-v2/` — parent + 4 modules, 19 tasks (0–18) |
| Module | **2 of 4** — "Models + hop-budget support layer", tasks **4–7** |
| Complete | **Module 1 in full** — Task 0 (11/11), Task 1 (4/4), Task 2 (4/4), Task 3 (3/3) **+ all 8 acceptance criteria** = 30/30 checkboxes. Commits `474c1bb`, `9669b09`, `43bdcee`, `783973b`, transition `dafc119` |
| Next | **Task 4** — `plan.py: handoff_spawn` field. The sprint's **first code task** |
| Manifest | `active_module_id: 2`, `task_range: [4,7]`, `midpoint: 6`, `context_summary_at: 6` (recomputed by the transition — the N11 fix working) |
| Tier | `standard`. Dispatch, spec review, quality review, partner review all **dispatched**, not self-written |
| Baseline at transition | unit **658 passed**; `verify-symlink-install.sh` **104/0/0**; plan gate **PASS / 0 / 0** on all 5 files; tree clean; zero residual cmux probe workspaces (verified live twice) |

## Post-transition state — read before your first dispatch

- **The live `.dispatch-log` is truncated to 0 lines.** Correct and expected. The archived copy keeps its `# sdd-hook-sentinel …` header; the live one gets a **fresh sentinel written lazily** by the hook on the next reviewer dispatch (its integrity check is WARN-only, never blocks). **Do not try to restore it.**
- **Check 4c will SKIP for Task 4** — `PREV=3 < MANIFEST_TASK_START=4` (the N3a boundary guard). Boundary provenance was already re-verified by `transition-module.py:validate_module_completion`. Not a gap.
- **Still owed before the Task 4 implementer dispatch:** `reports/checkpoint-pre-dispatch-004.json` and `reports/partner-review-004.md`.
- `checkpoint-pre-dispatch-00{0..3}.json`, `partner-review-00{1,2,3}.md`, `pre-execution-audit*.md` and the two live logs stayed in `reports/` — the archive glob is `task-NNN-*` only.
- **Module 2 gates two deferred audit orders**: **B4** (before Task 5 — pin ONE reading of `Handoff.expected_hops`: either `int | None = None` with a test, or `write_manifest` always emits it with a test that a partial block is rejected) and **B7** (new `.py` under `subagent-driven-development/scripts/` is scanned by `check_python39_compat` → **no PEP-604 unions, no builtin generics in annotations** — while `X | None` IS correct in `skills/scripts/models/`, which is not scanned).

## Task 3 — SP3 + SP4 design docs + BACKLOG rows (COMPLETE)

Review tier **upgraded minimum → standard** (third writer of the shared `BACKLOG.md`; the deliverable is an id allocation against `main`, the operation that produced the earlier N76 collision). Partner APPROVED → spec PASS → quality **CHANGES_REQUESTED ×3** → APPROVED. **The adversarial quality review is now 7-for-7 on green upstreams** — and round 4 approved with only cosmetics, which is the convergence signal.

- **SP3 → BACKLOG N80**: a context guard for non-SDD sessions. The SDD gate cannot simply extend — it is manifest-gated and fires on the implementer **new-task** path only (`IS_IMPLEMENTER && ! MARKED_FIX`). Recommendation is an **advisory observer**, sequenced behind a contract-verification spike. **Its `$127`/569k motivating evidence has NO primary artifact** — a full 7-log sweep found no such row — so it is used as motivation only and **no threshold may rest on it**.
- **SP4 → BACKLOG N81**: a sanctioned carry-forward fix lane. Recommendation **defers rather than enables** and says so; the residual (a module-N defect blocking module N+1 *immediately*) is explicitly unsolved. Three axes deliberately left open: always-used vs may-be-unused, **interior vs last-in-range placement**, and **headered vs manifest-only plan shape** — these determine whether an unused reserved slot is caught by 1, 2 or 3 gates.
- Useful facts established while writing it: **Check 9 (`_check_verification_git_reality`) opens `if not verification_ids: return []` and iterates only `task_type: verification` tasks**, so it never polices ordinary implementation or fix dispatches. The hook writes its dispatch-log row **before** the task-range guard, so a refused dispatch still leaves a row claiming it happened (**Module 4 to evaluate**).

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

## SP1 RESOLVED by Task 2 — and it falsified the controller's own note

`reports/task-002-controller-observation.md` claimed the probe total is **not monotonic**, with auto-compaction as the residual hypothesis. **That is false.** Task 2 root-caused the anomaly to a **multi-iteration double-count**: a turn may contain several model calls in `message.usage.iterations`, and the top-level fields aggregate over the `type: "message"` ones, counting the same cached prompt twice (`268840 + 270851 = 539691` exactly; true value 270,851). Fixed in `context-probe.py` — read the last `message` iteration, fall back to top-level when absent. Proven a no-op on all 32,160 single-iteration turns, positive-controlled.

**Carry these forward:**

- **The probe total IS monotonic.** Do not build any exclusion rule on spike shape; no rule was adopted, deliberately.
- **Agreement between `context-probe.py` and `claude-ctx-check` is NOT corroboration** — they share the formula and therefore shared the bug. This is what misled the controller.
- **Un-owned defect, needs a BACKLOG row at merge — scoped to `~/.claude/bin/claude-ctx-check` ONLY.** **Statusline EXONERATED by experiment, 2026-07-31 (N=1, pre-registered).** The statusline's `ctx:` is NOT computed by any script here: `~/.claude/statusline-command.sh` reads `.context_window.used_percentage` from the JSON payload Claude Code writes to its stdin, and contains zero references to `claude-ctx-check`, `context-probe`, `.jsonl` or `transcript_path` — it does no arithmetic. A pre-registered test on a deliberately induced `['message','advisor_message','message']` turn (validity-checked: the discriminating block was confirmed present before the reading was read) predicted ~40% correct / ~79% if it summed message-type iterations / ~118% if it summed all. **Observed: 40%, matching true context 395,645.** The harness computes true context. `claude-ctx-check` alone carries the double-count, and its error is TRANSIENT — it misreports only while the newest usage block is the multi-iteration one, which is exactly the window the pre-dispatch hook samples in. The row must NOT name the statusline. Outside this worktree, so Task 2 could neither fix nor file it.
- **N76's severity is understated** — "harmless at runtime" is false; the controller handed off a session on a 2× inflated number. Its "on the fix-marked path" framing is a correlation, not a mechanism.

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
| **Main's N76 (the SP1 row) must be UPDATED at merge**, not duplicated. Its replacement text is the final section of `docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md` (Task 2's deliverable), which states the merge action verbatim. Task 2 appends no BACKLOG row by design | Merge step |
| ~~Task 3 must allocate ids against `main`~~ — **DONE**: N80 (SP3) and N81 (SP4) filed, both byte-identical to their doc fences. Next free id on both branches is now **N82** — re-enumerate at execution time rather than trusting this | ~~Task 3~~ closed |
| **Module 4 to evaluate**: the hook writes its `type=fix` / `type=implementer` dispatch-log row BEFORE the task-range guard, so a refused dispatch leaves a row claiming it happened. Benign for Check 9 today (it reads only `type=implementer` and only for verification tasks), but it is a real property of an append-only tamper-evidence log | Module 4 (hooks trio, Task 14) |
| **`context-summary.py` is not archive-aware** — after a transition it reports "No implementer report files found" and cannot regenerate. Hand-write the summary at each boundary, or teach it to glob `archive-*/` (the N4/N27 treatment) | Merge-time BACKLOG row |

## Instrument lessons — these changed how this sprint verifies anything

- **`grep` in this shell is a FUNCTION wrapping `ugrep … --ignore-files`**, which honors `.gitignore` and therefore **silently skips `.worktrees/`** — where all SDD work happens. Measured: `find`=7 observation logs, wrapped `grep -rl`=**4**, `/usr/bin/grep -rl`=7. It produced a **false BLOCKING review finding AND a false corroboration of it** (a spec review "re-verified" the same sweep through the same truncated instrument). **Independence of reviewer is not independence of instrument. Use `/usr/bin/grep` or `find -print0 | xargs -0` for every recursive sweep.**
- **A name-anchored regex cannot falsify its own expectation** — a check anchored on `IMPL_GLOB|SPEC_GLOB|QUAL_GLOB` "proved exactly three" call sites; a bare grep returns **four**. Pair every name-anchored check with a bare one.
- **A review can be measurably WRONG.** One BLOCKING finding inverted its own measurement; executing it as written would have replaced correct numbers with wrong ones. **Re-measure before dispatching a fix**, and tell fix rounds to report contradictions rather than edit against their own measurement. The measuring party was right against a written premise **four times**, once against the controller's own dispatch.
- **Give the command, never the number.** A live `type=fix` count went 7→8→9→10 across the rounds *including the rounds editing the sentence*; a bare `grep -c '0→'` drifted 4→7 while an anchored `grep -cE '^\| 0→'` held at 4.
- **Every propagation sweep undercounted**, including one written to correct an undercount. Treat any enumerated site list as a lower bound and require the sweep as a deliverable.
- **Walk module acceptance criteria by hand** — `validate_module_completion` polices per-task reports and provenance, **not** the AC list. One AC here was a live `cmux list-workspaces` check nobody had run in four sessions.
- **Dispatch-description trap**: the hook matches `(spec.compliance|spec.review)` and `(code.quality|quality.review)`. The SDD skill's own `[task N re-review:quality]` marker matches **neither** → `type=unknown` → hard-blocks the next task. Include a classifiable phrase alongside the marker; check `.dispatch-log` after every review dispatch.
