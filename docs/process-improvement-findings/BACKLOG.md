# Superpowers Fork — Improvements Backlog

Living ledger of open, in-flight, and completed process/tooling improvements for this fork. Items are derived from production SDD sessions and cross-repo evaluations (see **Sources** below). This is the durable, version-controlled tracker — individual planning memos are ephemeral.

**Last updated:** 2026-05-31

## How to use this

- **IDs are stable.** `B*` = items from the BTD consolidation assessment; `I*` = items inferred from that report's data; `C*` = net-new from cross-repo findings / deferred infra; `N*` = other net-new; `P*` = process entry-point items. Reuse the same ID when an item moves to in-flight/done so history is traceable.
- When an item ships, set **Status** to `done` and record the worktree/commit in **Where / Notes**. Don't delete done rows — they're the audit trail.
- New items: append with the next ID in the relevant series and fill every column.

**Sizing rubric:** **S** = ~1 file, localized, low risk · **M** = a few files across model→script→skill, 2–4 tasks · **L** = cross-cutting / new infrastructure / many consumers / needs new test fixtures + design.

**Status values:** `open` · `in-flight` · `done` · `deferred` · `won't-do`

**Improves axes:** friction · speed · quality (`enabler` = unblocks another item; `—` = no change intended).

---

## Ledger

| ID | Title | Source | Improves | Size | Status | Where / Notes |
|---|---|---|---|---|---|---|
| B1 | Fix `general-purpose` subagent_type bug (hook exits before reviewer detection) | BTD High-1 | friction, speed | M | done (merged 7030b25) | `sdd-hook-improvements` worktree — 3-stage classification in `sdd-pre-dispatch-hook.sh` |
| B2 | Inline validation errors in hook output | BTD High-2 | friction, speed | S | done (merged 7030b25) | `sdd-hook-improvements` — `head -n 12` excerpt in Check 4b |
| B3 | Auto-create dispatch log on first reviewer dispatch (cold start) | BTD High-3 | friction | S | done (merged 7030b25) | `sdd-hook-improvements` — idempotent `mkdir -p`+`touch` |
| B4 | Per-task `review_tier` (task-aware minimum-tier threshold) | BTD High-4 | friction, speed | M | done (merged 7030b25) | `sdd-hook-improvements` Module 1 — `review_tier` field + declared-minimum ratio exclusion (task-aware variant, not raise-to-70%) |
| B5 | Remove legacy (non-manifest) dispatch detection path | BTD High-5 | quality | M | done (merged 7030b25) | `sdd-hook-improvements` — manifest-required guard clause |
| B6 | `verification`/no-code task type (skips full dispatch/review cycle) | BTD Med-5 | friction, speed | M | open | **Top remaining.** Extends `review_tier` pattern: `Task` model → manifest → hook branch on ~4 review checks (`sdd-pre-dispatch-hook.sh` ~L425–541). Pair with C4 anti-smuggling guard. Task 9 (grep-only) cost 39 min. |
| B7 | Batch reviewer dispatches for minimum-tier tasks | BTD Med-6 | speed | M | open | One dispatched reviewer covering several declared-minimum tasks. Must stay *dispatched* (provenance-logged). Lower leverage now that B4 removes most blocking. |
| B8 | Async-compatible honesty check (`mode: autonomous`) | BTD Med-7 | friction | M | open | User-confirmed needed for unattended standard-tier runs. Add field to `Enforcement` (`skills/scripts/models/sdd_session.py`) + gate in `controller-checkpoint.py` (~L999–1028). **Guard:** prominent log + queued human re-review; must not become a silent bypass (see C3). |
| B9 | `reports/` subdirectory organization (`reports/tasks/` + `reports/process/`) | BTD Low-8 | navigation | L | deferred | Broad blast radius — touches every path consumer (hook, checkpoint, validators, transition-module). Revisit only if navigation becomes a real cost. |
| B10 | Context summary conditional on actual context pressure | BTD Low-9 | friction | M | open | In-flight work narrowed the metric but kept the hard task-number trigger (`compute_midpoint` → `enforcement.context_summary_at` → hook Check 6b). Depends on C6. |
| N1 | Hook preflight — report all missing prerequisites at once | inferred I5 | friction, speed | M | open | Audit early-exit points in `sdd-pre-dispatch-hook.sh`; accumulate errors instead of fail-one-retry-fail. The B1 bug cascaded into 6 separate blocks. |
| N2 | SSOT audit: reconcile SKILL.md manual prescriptions vs hook-enforced checks | derived from C6 (confirmed drift) | friction, quality | M | open | C6 confirmed a manual SKILL.md step (token estimation §257–269) duplicating an automatic hook check, with drifted args + false honesty-check guilt. Likely not the only one. Audit `subagent-driven-development/SKILL.md` (and peers) for prescribed *manual* steps a hook already enforces; retire/redirect each to the hook (single source of truth). Catches the structural pattern, not just the C6 symptom. |
| N3 | Check 4c (dispatch provenance) rejects valid plans that start at Task 1 (no Task 0) | live SDD run — practerus marketing-cta-guard, 2026-05-31 | friction, quality | S | open | `sdd-pre-dispatch-hook.sh` Check 4c (dispatch provenance, ~L418–457) sits *outside* the "first task in module" skip (L348–352, which wraps only the N-1 report-file checks). Its exemption guard `TASK_NUMBER -gt 0` (L343) assumes the first task is always Task 0 — but Task 0 is **conditional**: `writing-plans`/SDD SKILL.md mandate it only when the plan has external Source Contracts, so a contract-free plan validly starts at Task 1. When it does, Check 4c sets `PREV=0` and greps the dispatch log for `task=0 type=spec-review`, which can never exist → `BLOCKED: … Start by dispatching the spec reviewer for Task 0.` The only legitimate way past is forging a `task=0` log entry, which violates the exact provenance model the check protects. **Fix:** give Check 4c a parallel exemption — skip the PREV check when `PREV < MANIFEST_TASK_START` (no prior in-scope task), preserving full provenance enforcement for plans that *do* declare Task 0. Add a regression fixture: a Task-1-start manifest PASSes; a Task-0 manifest still gets PREV provenance-checked. Same-file sibling to **N1**; adjacent to **N2** (skill↔hook drift — hook assumes a plan shape SKILL.md treats as optional). |
| P1 | Direct-to-`writing-plans` entry mode (re-installs setup guardrails) | user-raised | friction, speed | M | open | Sometimes a full brainstorm spec+distillation is overkill. Make `writing-plans/SKILL.md` detect direct entry, **record the choice**, port brainstorming's 4-branch stale-`.active-feature` conflict detection, add worktree/branch guard, and run `check-distillation.sh` (make it callable outside brainstorming) if a distilled spec is supplied. Hook already enforces the plan-quality half. Sibling to `adaptive-enforcement-tiers`: an entry-mode dial for the planning pipeline. |
| P2 | Reliable project closeout (lifecycle close) | user-raised | friction, quality | M–L | open | Closeout is purely manual + under-cleans, and there's no persisted "done" signal, so completed features pile up unclosed (`.active-feature` left set, feature dirs never archived). **Decisions:** archive feature dir → existing `docs/imp-plans/archive/`; trigger via SessionStart nudge + entry-time GC (no Stop-hook auto-prompt — would fire mid-smoke-test). **(a) Foundation [S]:** add `completed_at`/`status` to `SddSession`, written by `controller-checkpoint.py` at pre-completion gate PASS; gitignore `.sdd-session.json` ✓ **shipped 2026-05-30** (was un-ignored; written to the *feature dir* so the entry is no-leading-slash. One instance — the merged sdd-hook-improvements manifest — is already committed; `git rm --cached` pending user decision on whether to keep it as feature history). **(b) Closeout [M]:** extend `finishing-a-development-branch` to archive the feature dir + remove the manifest (today it only clears `.active-feature`/`.allow-main`/branch/worktree). **(c) Discovery [S–M]:** SessionStart nudge **gated on `.active-feature` present in repo root AND manifest `status: complete` AND nothing in-flight** — stays silent in BiG/outside/non-superpowers repos (no `.active-feature` → instant no-op). **(d) Backstop [M]:** entry-time GC in brainstorming/writing-plans using the signal; in-flight detection (uncommitted changes, branch≠main, unchecked tasks, pending deviations) protects active work. Pairs with P1 as "lifecycle hygiene" (clean entry + clean exit). |
| C1 | Plan-reference code execution validation | skill-eval §2.1 | quality | L | open | **Highest correctness leverage.** Reference snippets in plans are approved unrun; this fork's own `compute_midpoint` bug shipped 3×. plan-document-reviewer is codebase-isolated by design and can't catch it. Needs new fixtures + design. |
| C2 | Integration-test coverage requirement | skill-eval §2.2 | quality | M | open | Unit coverage enforced, e2e isn't (a cache-poisoning vuln + unreachable endpoint passed all unit tests). Plan-time declaration for contract/route/security-touching features + hook check. |
| C3 | Migrate gameable gates from controller-invoked → PreToolUse hooks | skill-eval §10 | quality | L | open | The meta-pattern: out-of-band hooks hold; controller-invoked steps get skipped under pressure (minimum-tier abuse, forged `.dispatch-log`, honesty run only when prompted). B8 must be designed within this principle. |
| C4 | Computed tier recommendation heuristics | adaptive-tiers v1.1 (deferred) | quality | M | open | Flag high-risk tasks (auth/credentials/migrations) wrongly downgraded by task-count alone. Natural guard for B6. |
| C5 | Cross-artifact validation (Pydantic Phase 3) | pydantic Phase 3 (deferred) | quality | L | open | Detect manifest↔plan↔reports↔deviations drift (e.g., "manifest says spec-review dispatched but report is controller-written" — catches the forgery class behind C3). |
| C6 | Resolve the duplicated/manual context-budget step | adaptive-tiers v1.1 + live honesty-check evidence | friction, quality | M | (a) done 2026-05-30 · (b) open | **Reframed — not a "usability" fix.** **(a) shipped:** SKILL.md §257–269 manual prescription retired → now states the hook enforces it automatically (SDD skill 5029→4753 words; regression 145 PASS). Root cause: SKILL.md §257–269 prescribes a *manual* run of `estimate-task-tokens.py` before each dispatch, but the pre-dispatch hook Check 6 (L660–708) **already runs it automatically** and blocks `TOO_LARGE` — so the manual step is redundant ceremony, correctly skipped on judgment (live evidence: honesty-check "skipped required step"). The two have drifted (skill passes `--task-file --constraints-file`; hook passes `--plan-file --task` only), and *both under-measure*: they count task text (+constraints for the skill variant) but NOT real injected context (source files the task lists, CLAUDE.md refs, prior reports, scene-setting) — so a small ≤200-line task can still dispatch a huge prompt. Note the 200-line cap is only a `validate-plan.py` WARNING, not a blocker, so the "validated ≤200-line plan ⇒ within budget" proxy is unsound. **(a) [S, quick win]** retire the manual prescription in SKILL.md → state the hook enforces it automatically (single source of truth; removes skip-guilt). **(b) [M]** strengthen the hook auto-estimate to pass `--constraints-file` (script already accepts it) + estimate injected context. Instance of C3 (controller-invoked → hook-enforced). Strengthened estimate gives B10 a real pressure signal. |
| I1 | Per-feature pipeline too heavy for refactors | inferred (time table) | friction, speed | — | open | Structural; substantially covered by P1 + B6. Track here so it isn't re-discovered. |
| I2 | Subagent dispatch overhead dominates test/doc tasks | inferred | speed | — | open | Covered by B6 / B7. |
| I3 | Honesty check structurally defeated in autonomous runs | inferred | quality | — | open | = B8. |
| I4 | Report validators (`result ∈ {PASS,FAIL}`, `passing ≤ written`) | inferred | — | — | won't-do | Validators are correct — keep them. The pain was diagnosis, fixed by B2. Logged so they aren't loosened by mistake. |
| I5 | Dispatch-log cold-start cascade | inferred | friction | — | open | = N1. |

---

## Recommended sequencing

Ordered by leverage; sequenced so nothing collides with the in-flight `sdd-hook-improvements` worktree.

1. **Let B1–B5 land first** — don't open concurrent work on the same hook/model files.
2. **Quick wins — ✓ DONE 2026-05-30:** C6(a) manual token-estimate step retired from SKILL.md; `.sdd-session.json` gitignored (one already-committed instance pending untrack decision).
3. **B6** (+ C4 as its anti-smuggling guard) — best friction-per-effort; finishes the assessment's intent.
4. **P1 + P2** — "lifecycle hygiene" (clean entry + clean exit); both user-raised; share the `.active-feature` / completion-signal plumbing, so do them together.
5. **B8** — user-confirmed for unattended runs; design within C3's principle.
6. **C6(b)** strengthen the hook estimate; **C1** highest correctness leverage.
7. **C2 + C3** — trust-at-scale.
8. **N1, N3, B10, C5** — opportunistic, **except N3 which is a hard blocker** for any contract-free (Task-1-start) plan and should land with N1 (same file, `sdd-pre-dispatch-hook.sh`). B10 benefits from C6(b)'s real pressure signal.
9. **B7, B9, C4 (standalone)** — revisit; B7/B9 may prove unnecessary once B6 ships.

Each open item becomes its own brainstorming → writing-plans → SDD cycle, validated by `validate-all-skills.py`, `tests/unit/`, and `tests/integration/sdd-e2e-test.sh`. C1/C2 additionally need a new fixture proving a known-bad reference snippet / missing integration path is now caught.

---

## Sources

- `docs/2026-05-28-sdd-session-assessment-btd-consolidation.md` — BTD consolidation SDD session post-mortem (B*/I* items).
- `docs/process-improvement-findings/2026-05-21-skill-evaluation.md` — cross-repo Critical findings (C1–C3).
- `docs/imp-plans/2026-05-17-adaptive-enforcement-tiers/` — deferred v1.1 candidates (C4, C6).
- `docs/plans/2026-04-24-pydantic-meta-design.md` — Pydantic Phase 3 candidates (C5).
- `docs/imp-plans/2026-05-28-sdd-hook-improvements/` — in-flight work addressing B1–B5.
- Live SDD run in the `practerus-platform` repo — `docs/imp-plans/2026-05-27-marketing-cta-guard/` Task 1 pre-dispatch (2026-05-31); surfaced **N3**.
