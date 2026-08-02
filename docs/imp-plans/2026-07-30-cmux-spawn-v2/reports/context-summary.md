# Context Summary — cmux-spawn-v2, **MODULE 2 COMPLETE (Tasks 4-7) — resume at Module 3, Task 8**

Updated 2026-08-01 **after Task 7 closed and Module 2 completed** (superseding the post-Task-5 version, whose detail is retained below). Compresses Module 1 + Tasks 4-7 so a fresh controller can resume at Task 8 without re-reading the full flight recorder. **Module 1's reports live under `reports/archive-Contracts, cold-start measurement, spikes/`**; Module 2's are live in `reports/` until the transition archives them. Both remain authoritative where this summary is terse.

> **Hand-maintained.** `context-summary.py` is NOT archive-aware and cannot regenerate this after a module transition; Check 6b gates on EXISTENCE, not freshness, so nothing warns when it goes stale. A merge-time BACKLOG row is already logged.

## SESSION 8 — Tasks 6 + 7 COMPLETE, MODULE 2 DONE, resume at Module 3 Task 8

| | |
|---|---|
| **Task 6 — COMPLETE** | `_handoff_support.py` formula/precedence SSOT + `materialize-manifest.py` wiring. 8 checkboxes. `9b32c25` (impl), `55e96a1` (fix r1), `bf4343a` (fix r2), `f343bc1` (close). Converged at **quality round 3** |
| **Task 7 — COMPLETE** | `tasks_done` counting + stall streak + `_cli`. `83a9ccf` (impl), `cf5de3b` (fix), `c28e33d` (close). Converged at **quality round 2** |
| **Plan amendments before dispatch** | `64ba56a` (B9 + R3-2, net-zero), `bbd3773` (shared-helper spec sync), `b8131b2` (**consent fail-open fix**), `d12f83c` (P7-1 address fix) |
| **Suite** | 694 → **707 passed**. Regression PASS 160 / FAIL 0 / WARNING 2. e2e PASS 15 steps. Plan gate PASS/0/0 on all 5 files |
| **Module 2 checkboxes** | 11 total: **10 checked + AC-5 as an annotated `[~]` PARTIAL** (deliberately not green — see below) |
| **Next** | **Task 8 implementer dispatch — but a PARTNER ROUND 3 is owed first.** Module 2 transitioned; OP-1 CLOSED as mis-specified (`f06ae2b`/`da5bf58`/`e020e59`); Task 8 pre-dispatch work landed across `ca70612`, `3f6cbe6`, `f135c4f`, `50623b6`. Partner rounds 1 and 2 both BLOCKED and both found real defects; round 2's four findings are addressed but UNREVIEWED. The reviewed dispatch prompt is at `task-008-dispatch-prompt.md` (feature-dir root). Checkpoint `checkpoint-pre-dispatch-008.json` PASSes (0 blockers). |
| **Controller context** | ~300k at the Module 2/3 boundary (SOFT 300k / HARD 400k). The gate arms ONLY on the implementer new-task path (`IS_IMPLEMENTER && ! MARKED_FIX`), so reviews and fix rounds are never blocked; the next gateable moment is **Task 8's dispatch** |

**Six things from Tasks 6-7 worth carrying:**

1. **The adversarial quality review is now 13-for-13 on green upstreams.** Task 7's round 1 ran against implementer DONE + a spec review that *mechanically diffed* the plan's fenced block against the landed code and found only whitespace + 704 tests green — and still found **12 of 14 mutations surviving**.
2. **THE PARTNER REVIEW BLOCKED THE TASK 7 DISPATCH AND FOUND A CONSENT FAIL-OPEN IN THE PLAN'S OWN CODE** — the second such catch on this feature. `spawn-policy` printed `auto` (spawn-without-asking) for any missing/unreadable/corrupt manifest, because `except → {}` is indistinguishable from a readable manifest with no `handoff` block. It is the SOLE consent gate, and **the defaults STACK**: Module 3's `*) SPAWN_POLICY="auto"` independently coerces anything unrecognized. Fixed to fail closed to `ask` (retryable, pre-reservation). **Pre-dispatch controller/partner work has now been the highest-leverage act on three consecutive tasks.**
3. **VACUOUSNESS IS THE DEFECT CLASS, AND IT REACHED THE FIXES THEMSELVES.** Quality r1 prescribed a `task_id: yes` fixture to pin a bool guard; the implementer **measured it and it does not discriminate** — `yes` → `True`, `True == 1`, so `done.add(True)` collapses into an already-counted task 1 and the mutation SURVIVES. `no` → `False` → `0` works. Round 2 confirmed and generalized: `{"task_ids": [True, 2]}` in existing code discriminates ONLY because the sibling is `2`. **Standing rule now in `deviations.md`.**
4. **The bool-guard family is at SIX sites plus a near-miss, and four rounds each believed they had closed it.** Treat "the family is closed" as a claim to disprove.
5. **NINE instrument failures this sprint.** ugrep `--ignore-files` skipping `.worktrees/`; a vacuous pytest glob; `ruff` absent from PATH; an inherited `cd`; a `cmux --help` truncated by `head -50` from which absence was inferred; a `grep -E` using backslash-pipe for alternation; a PyYAML-absent probe using `/usr/bin/python3`, which *ships* PyYAML here; the `task_id: yes` fixture; and a restore that silently dropped a trailing newline. **Positive-control every probe — an empty or passing result is a claim, not a fact.**
6. **The pre-commit format hook now attacks EVERY Python commit** (three consecutive), black-rewriting whole files and deleting the pinned seam imports `HOP_DIVISOR` / `CEILING_FACTOR`. **Standing procedure: check `git diff --cached --stat`, then `git commit --no-verify`.**

**AC-5 is a `[~]` annotated partial, not green** — three measured paths violate "degradation is observable at exit 0" (**P7-3** fake `0`, **P7-6** `UnicodeDecodeError` → exit 1, **P7-8** `stall_streak` returns proceed on any `OSError`), each needing a production edit to a plan-verbatim body. Quality r2 **blocked the transition until these were in `deviations.md`**, because the reports carrying them get archived at the boundary while the register survives it. **That is the reusable lesson: a finding recorded only in a report is a finding you are about to lose.**

**Module 3 inherits nine scheduled rows**: P7-1 (i shell + ii Python, both required — neither subsumes the other), P7-3, P7-4, P7-5, P7-6, P7-7, P7-8, P7-9, plus OP-1 and the standing bool-guard rule.

## SESSION 7 — Task 5 COMPLETE, resume at Task 6

| | |
|---|---|
| **Task 5 — COMPLETE** | `sdd_session.py: optional handoff block`. All 5 checkboxes. Commits `f91b94f` (impl), `d1741e0` (`[task 5 fix]`), `d52baf8` (flight recorder). Plan amendment `0529136` landed BEFORE dispatch |
| **Trajectory** | partner APPROVED (1 Major actioned) → implementer DONE → spec PASS → quality **r1 CHANGES_REQUESTED** (3 surviving mutations, 2 over-permissive) → fix → quality r2 APPROVED, cosmetics only = convergence |
| **Suite** | **674 passed** (was 671 at `fe2437e`; +8 Task 5 tests, +3 fix-round tests, −8… i.e. 663+8+3) |
| **Next** | **Task 6** — `_handoff_support.py` (formula + precedence) + `materialize-manifest.py` wiring. `checkpoint-pre-dispatch-006.json` saved; owes `partner-review-006.md` before dispatch |
| **Controller context** | 242,376 tokens at the Task 5/6 boundary (SOFT 300k / HARD 400k). **Verified in the hook source that the context gate arms ONLY on the implementer new-task path** (`IS_IMPLEMENTER && ! MARKED_FIX`) — fix dispatches are logged not gated, reviews aren't implementers. So Task 6 cannot be blocked mid-cycle; the next possible block is **Task 7's dispatch**, a clean boundary |

**Four things from Task 5 worth carrying:**

1. **The adversarial quality review found real defects on a fully green upstream for the NINTH consecutive round** — implementer DONE, spec PASS with behavior-level evidence, 671 tests green. Three mutations survived: `ge=1`→`ge=2`, `int`→`float`, and a `mode="before"` validator silently coercing unknown `spawn_policy` to `"auto"`. All three fixes were **test-only** and passed against the code exactly as committed — zero behavioral risk.
2. **An annotation guard is not a behavior guard.** `test_spawn_policy_literal_is_closed_set` pins `get_args(...)`, which a coercing `mode="before"` validator leaves untouched. Consequential because the reviewer checked the consumer side: the `_handoff_support` CLI **and** `spawn-handoff-session.sh` both silently default an unrecognized consent value to `"auto"` — the spawn-*without*-asking value — making the Pydantic model the only layer that would reject a typo'd policy loudly.
3. **The controller's own pre-dispatch amendment was the highest-leverage act of the task.** Before dispatching, the advisor asked whether the seven planned tests could distinguish `StrictModel` from `BaseModel`. They could not — none supplied an undeclared key. `test_extra_key_rejected` was added to the PLAN (`0529136`), and round 1 later confirmed it kills that mutation and nothing else.
4. **A reviewer caught a bug in its OWN harness and re-ran before reporting.** Round 1's first battery mis-attributed 13 failures to two different mutations — a stale `__pycache__` `.pyc` surviving between runs (mtime+size aliasing at sub-second cadence). It self-reported on the grounds that *a harness that mis-attributes failures can equally mis-attribute survivals*. **Clear `__pycache__` between mutation runs and use `-p no:cacheprovider`.**

**Two premises that FAILED at execution this session** (eighth and ninth in the sprint): (a) the partner review measured the global pre-commit format hook as registered and predicted a whole-file reformat — **it did not fire on either commit**, twice; (b) `_materialize()` in Task 6 Step 5 **does not exist** (third phantom-helper instance after `_minimal_plan()`/`_minimal_session()`), pre-resolved in the plan text before dispatch. **A FOURTH vacuous-harness instance hit the controller directly:** Bash cwd persists between tool calls, so an earlier `cd` into the feature dir made a `validate-plan.py` check run against a nonexistent path — and it surfaced as a `KeyError` in the *parsing* code, which reads like a script bug rather than "validation never ran."

## SESSION 6 — what changed at the Task 4/5 boundary

| | |
|---|---|
| **Task 4 — COMPLETE** | `plan.py: handoff_spawn` field. All 5 checkboxes. Commits `ab1ffd2` (impl), `fe2437e` (`[task 4 fix]`), `dcd327a` (flight recorder) |
| **Deferred order B7** | **DISCHARGED for Module 2** (`cf867be`) — premise re-verified, not inherited. Module 4 still owes its copy |
| **Deferred order B4** | **DISCHARGED** (`00ce70e`) — reading pinned **all-or-nothing**; consumer half in Module 3 Task 8's helper was real and is fixed |
| **Next** | **Task 5** — `sdd_session.py: optional handoff block`. Owes `checkpoint-pre-dispatch-005.json` + `partner-review-005.md` before dispatch |
| **Controller context at handoff** | 304,678 tokens (SOFT 300k / HARD 400k) — handed off at the Task 4/5 boundary rather than risk a mid-cycle HARD block |

**Task 4's trajectory:** partner APPROVED → implementer DONE → spec PASS → quality r1 APPROVED *with one substantive Minor* → `[task 4 fix]` → quality r2 APPROVED (cosmetics only) = convergence.

**Five things from Task 4 worth carrying:**

1. **The adversarial quality review found a real defect on a fully green upstream AGAIN** (implementer DONE + spec PASS + 166 tests green). Nothing pinned the `handoff_spawn` Literal as a **closed set** — widening it to a 4th value left all 51 tests green. **The reviewer graded it Minor and returned APPROVED; the controller actioned it anyway.** The stopping rule is "cosmetic **AND** approve"; this satisfied only the second conjunct. Controller reproduced first, with a discriminating positive control (field-deleted → 3 failed; widened → 51 passed).
2. **Every mutation anyone had run was RESTRICTIVE** — the implementer's self-review and the spec review's three (`Literal→str`, default flip, dropping a value). **A one-directional mutation battery cannot find an over-permissive defect.** Ask of any battery: does it mutate in both directions?
3. **A VACUOUS PROBE gave the right answer for no reason.** Investigating whether ruff would break B7, the controller's first probe reported "no rewrite" — while `ruff` was not on its PATH at all. Nothing ran; the empty diff meant nothing; the conclusion was right by luck. The re-run added positive controls (an unused import that must vanish, bad spacing that must normalize) and both fired before the clean result was trusted. **A harness that cannot fail cannot confirm.** Same class as the earlier vacuous-pytest-glob incident.
4. **A plan-wide construct is a plan-wide defect.** Task 4's first finding was that the plan's `_minimal_plan()` test helper does not exist. The sibling `_minimal_session()` in Task 5 was the same fiction one task away — **and the B4 amendment, written by the party who had just fixed the first one, added two more tests against it.** Now fixed in the plan text itself, not in a dispatch.
5. **Round 2 upgraded its own instrument.** Asked to confirm nothing hid inside a 94-line auto-format diff, it did not diff — it compared `ast.dump()` of both revisions with imports stripped. Blind to reformatting by construction, so it answers "did semantics change?" rather than "do the lines match?"

**New standing hazard — a GLOBAL pre-commit hook, not this repo's.** `~/.claude/hooks/pre-commit-format.sh` runs `ruff format` + `ruff check --fix` on staged `.py` and **re-stages**. It turned Task 4's 8-line fix into a 94/28 commit and removed five pre-existing dead imports. Expect the same one-time whole-file reformat on the first commit of Task 5's `test_sdd_session_model.py` and Task 6/7's files — **do not read that diff size as implementer overreach.** The B7 collision is **disproven**: no ruff config exists, so the default `E4,E7,E9,F` set runs and `UP007` is absent — `Optional[X]`/`Dict[str,int]` survive untouched.

**Line-count ceiling is NOT just Task 9.** Measured at the B4 amendment: M1 `T0=199`; M2 `T4=47 T5=114 T6=199 T7=199`; M3 `T8=194 T9=200`; M4 `T12=192`. **Tasks 6 and 7 have ONE line of headroom each** and OP-1's compression authorization covers Task 9 only. Per-task counts live at `d["tasks"][i]["lines"]` in `validate-plan.py`'s JSON — **not** under `checks`.

> **Why this file was hand-updated, not regenerated.** `context-summary.py` returns `{"error": "No implementer report files found"}` after a transition — **it is not archive-aware**, so it cannot see the reports `transition-module.py` just moved. This is the sibling of the N4/N27 archive-awareness fixes already applied to `controller-checkpoint.py`. Logged in `deviations.md`; file a BACKLOG row at merge. **Consequence: after every module transition the context summary must be written by hand, or the script taught to glob `archive-*/`.**

## Where the sprint stands

| | |
|---|---|
| Feature | `docs/imp-plans/2026-07-30-cmux-spawn-v2/` — parent + 4 modules, 19 tasks (0–18) |
| Module | **2 of 4** — "Models + hop-budget support layer", tasks **4–7** |
| Complete | **Module 1 in full** (+ Task 4, see above) — Task 0 (11/11), Task 1 (4/4), Task 2 (4/4), Task 3 (3/3) **+ all 8 acceptance criteria** = 30/30 checkboxes. Commits `474c1bb`, `9669b09`, `43bdcee`, `783973b`, transition `dafc119` |
| Next | ~~Task 4~~ ~~Task 5~~ **BOTH DONE** — the live next task is **Task 6** (see the Session 7 section at the top). _This row is the Module-1-boundary snapshot, retained as written._ |
| Manifest | `active_module_id: 2`, `task_range: [4,7]`, `midpoint: 6`, `context_summary_at: 6` (recomputed by the transition — the N11 fix working) |
| Tier | `standard`. Dispatch, spec review, quality review, partner review all **dispatched**, not self-written |
| Baseline at transition | unit **658 passed**; `verify-symlink-install.sh` **104/0/0**; plan gate **PASS / 0 / 0** on all 5 files; tree clean; zero residual cmux probe workspaces (verified live twice) |

## Post-transition state — read before your first dispatch

- **The live `.dispatch-log` is truncated to 0 lines.** Correct and expected. The archived copy keeps its `# sdd-hook-sentinel …` header; the live one gets a **fresh sentinel written lazily** by the hook on the next reviewer dispatch (its integrity check is WARN-only, never blocks). **Do not try to restore it.**
- ~~**Check 4c will SKIP for Task 4**~~ — it did, exactly as predicted (`PREV=3 < MANIFEST_TASK_START=4`, the N3a boundary guard; the pre-dispatch checkpoint reported all five previous-task checks `SKIP` with the prior-module reason). **Historical now** — Task 5's `PREV=4` is in range, so Check 4c and the previous-task checks all arm normally and Task 4's reports must satisfy them. They do.
- ~~**Still owed before the Task 4 implementer dispatch**~~ — **SATISFIED and committed.** **The live equivalent is `reports/checkpoint-pre-dispatch-005.json` + `reports/partner-review-005.md` before the Task 5 dispatch.** Note the checkpoint flag is `--task-number`, not `--next-task`; and Check 5c gates on the FILE existing, not on the script having succeeded — an argparse usage error redirected into that file would satisfy the hook while proving nothing.
- `checkpoint-pre-dispatch-00{0..3}.json`, `partner-review-00{1,2,3}.md`, `pre-execution-audit*.md` and the two live logs stayed in `reports/` — the archive glob is `task-NNN-*` only.
- ~~**Module 2 gates two deferred audit orders**~~ — **BOTH DISCHARGED; do not re-litigate either.** **B7** landed in `cf867be` (a Contract Constraints line in `module-2-models-budget.md`; its premise was re-verified rather than inherited — `check_python39_compat` flat-globs `subagent-driven-development/scripts/*.py` only, so `Handoff | None` is right in `skills/scripts/models/` while the same syntax in `_handoff_support.py` would FAIL). **Module 4 still owes its copy of B7.** **B4** landed in `00ce70e`: the pinned reading is **all-or-nothing** — `expected_hops` stays required, absent-entirely is legal, present-but-partial is not — applied in Task 5 Step 1 (`test_partial_block_rejected`) AND in Module 3 Task 8's `write_manifest` helper, whose `None` defaults really were emitting an invalid empty block. Rationale in `deviations.md`.

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
- ~~`handoff_spawn` must appear in NO frontmatter until Task 4 lands the model field~~ — **Task 4 has landed it (`ab1ffd2`), so this constraint is DISCHARGED**; plan frontmatter may now declare `handoff_spawn`. The sibling constraint is still live for Task 5: nothing may write a manifest `handoff` block until Task 5 lands the `Handoff` model (`SddSession` is also `extra=forbid`).
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
| Deferred audit orders B1, A3b/c+B2, B3, B8a — **B4 DONE (`00ce70e`), B7 DONE for Module 2 (`cf867be`) but Module 4 still owes its copy** | Their owning tasks — see Deferred Work table |
| **N67 will conflict on merge** — `main` edited it since the merge-base and so did this branch. The resolution MUST preserve both sides: main's edits AND this branch's `UPDATE 2026-07-30 — DISPOSITIONED BY N79` clause. A "take theirs" drops the discharge instruction and sends a future reader to re-run a probe already run. Rows main touched since `fa2d482`: N55, N56, N57, N61, N63, N64, N66, N67, N68, N70, N73, plus new N76–N78 | Merge step |
| **Main's N76 (the SP1 row) must be UPDATED at merge**, not duplicated. Its replacement text is the final section of `docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md` (Task 2's deliverable), which states the merge action verbatim. Task 2 appends no BACKLOG row by design | Merge step |
| ~~Task 3 must allocate ids against `main`~~ — **DONE**: N80 (SP3) and N81 (SP4) filed, both byte-identical to their doc fences. Next free id on both branches is now **N82** — re-enumerate at execution time rather than trusting this | ~~Task 3~~ closed |
| **Module 4 to evaluate**: the hook writes its `type=fix` / `type=implementer` dispatch-log row BEFORE the task-range guard, so a refused dispatch leaves a row claiming it happened. Benign for Check 9 today (it reads only `type=implementer` and only for verification tasks), but it is a real property of an append-only tamper-evidence log | Module 4 (hooks trio, Task 14) |
| **`context-summary.py` is not archive-aware** — after a transition it reports "No implementer report files found" and cannot regenerate. Hand-write the summary at each boundary, or teach it to glob `archive-*/` (the N4/N27 treatment) | Merge-time BACKLOG row |

## Task 8 — COMPLETE except F1 (state as of 2026-08-02)

Task 8 landed across `239532a` (feature), `43ff224` (seam imports), `2f677e6` (quality fixes), `69ece98` (SSOT test), with plan/register work in `0f56c28`, `e0960ac`, `f4ba60e`. **Suite 707 → 748 green.** All six Task-8 step checkboxes ticked; step (e)'s fence amended to match the landed code.

**Review sequence, for the record:** FIVE partner rounds (1–4 BLOCKED, 5 APPROVED — fifteen findings including a fail-open regression, four count defects, two vacuous prescriptions, a nonexistent test seam, and a hang), then implementer → spec review PASS → quality review CHANGES_REQUESTED (four surviving mutations) → fix → spec re-review PASS → quality re-review CHANGES_REQUESTED (F1–F4, all test-side).

**THE ONE OPEN ITEM: F1.** The SSOT re-duplication test (`test_handoff_support.py::test_shared_constants_are_the_ssot_the_shell_mirrors`) is shape-sensitive and a working escape was DEMONSTRATED: `CEIL=$(( EXPECTED_HOPS * 2 ))` plus a `-gt`-form clamp is a second, fully functional ceiling derivation that PASSES. Its three assertions are whitespace-exact / bracket-form-specific / name-specific, and that shape clears all three. **This matters because the test is the only thing standing between Task 9 and a silently reintroduced split guard — the exact defect the whole fix round eliminated.** F2/F3 are unpinned-but-fail-safe (floor clamp; outer knob-set test), F4 is a Task 9 tripwire (whole-file regexes misattribute an unrelated `-lt` as a ceiling regression). Full detail + suggested fixes: `reports/task-008-quality-review-round-2.md`.

## Instrument lessons — these changed how this sprint verifies anything

- **`grep` in this shell is a FUNCTION wrapping `ugrep … --ignore-files`**, which honors `.gitignore` and therefore **silently skips `.worktrees/`** — where all SDD work happens. Measured: `find`=7 observation logs, wrapped `grep -rl`=**4**, `/usr/bin/grep -rl`=7. It produced a **false BLOCKING review finding AND a false corroboration of it** (a spec review "re-verified" the same sweep through the same truncated instrument). **Independence of reviewer is not independence of instrument. Use `/usr/bin/grep` or `find -print0 | xargs -0` for every recursive sweep.**
- **A name-anchored regex cannot falsify its own expectation** — a check anchored on `IMPL_GLOB|SPEC_GLOB|QUAL_GLOB` "proved exactly three" call sites; a bare grep returns **four**. Pair every name-anchored check with a bare one.
- **A review can be measurably WRONG.** One BLOCKING finding inverted its own measurement; executing it as written would have replaced correct numbers with wrong ones. **Re-measure before dispatching a fix**, and tell fix rounds to report contradictions rather than edit against their own measurement. The measuring party was right against a written premise **four times**, once against the controller's own dispatch.
- **Give the command, never the number.** A live `type=fix` count went 7→8→9→10 across the rounds *including the rounds editing the sentence*; a bare `grep -c '0→'` drifted 4→7 while an anchored `grep -cE '^\| 0→'` held at 4.
- **Every propagation sweep undercounted**, including one written to correct an undercount. Treat any enumerated site list as a lower bound and require the sweep as a deliverable.
- **Walk module acceptance criteria by hand** — `validate_module_completion` polices per-task reports and provenance, **not** the AC list. One AC here was a live `cmux list-workspaces` check nobody had run in four sessions.
- **Dispatch-description trap**: the hook matches `(spec.compliance|spec.review)` and `(code.quality|quality.review)`. The SDD skill's own `[task N re-review:quality]` marker matches **neither** → `type=unknown` → hard-blocks the next task. Include a classifiable phrase alongside the marker; check `.dispatch-log` after every review dispatch.
