# Pre-Execution Audit — Controller Self-Assessment

**Feature:** cmux-spawn-v2 (`docs/imp-plans/2026-07-30-cmux-spawn-v2/`)
**Date:** 2026-07-30
**Controller role:** EXECUTION controller. I did not author this plan — it was written and
reviewed in a prior session and handed to me via handoff bundle
`2026-07-30T19-35-24Z-cmux-spawn-v2`. Answers below distinguish what I did from what the
planning session did (which I can only assess from committed artifacts).

---

### 1. Did you follow every step of each skill used before this point? List any steps you skipped and why.

Followed, in order:

- `/pickup` — resolved the bundle, confirmed `Guard: MATCH`, read `CONTINUE.md`. Noted
  `Staleness: HEAD advanced since capture (564e78c -> ffe6902)` and verified current git state
  directly rather than trusting the bundle's snapshot: tree clean, HEAD `ffe6902` (the extra
  commit is the priming prompt, not code).
- Invoked `superpowers:subagent-driven-development` via the **Skill tool** (not Read) so the
  PreToolUse Skill hook fired. Plan-validation gate reported: 5 plan files validated, review
  report confirmed.
- Plan Ingestion Step 1: read `plan.md` in full (not skimmed), `module-1-contracts-spikes.md`
  in full, and `spec-distilled.md` in full.
- Steps 2/2b/2c: extracted Contract Constraints, Shared Constants, and Pattern References
  verbatim into working memory for per-dispatch passthrough.
- Step 3 (Source Contracts): the parent declares `Source Contracts: None` by the modular-parent
  convention; the real contracts resolve to Module 1. I read the distilled spec's Contract Facts
  and verified the live binary contract directly (`cmux --version` → `cmux 0.64.20 (100)
  [14e3400b9]`, exactly the pinned build).
- Step 4: extracted the module-level Write-Scope Partitioning table; confirmed
  `spawn-handoff-session.sh` is written by Modules 3 and 4 (Task 13) and is serialized by
  module order plus `depends_on: [11, 12]`.
- Step 5 (archive stale artifacts): none to archive — see Q8.
- Manifest Materialization: ran `materialize-manifest.py` FIRST, before creating any tracker.
- Step 6: created `reports/` and `deviations.md`.

**Steps not yet done (correctly ordered after this audit, not skipped):** the task tracker,
the Task 0 pre-dispatch checkpoint, and the Task 0 dispatch itself.

**Deliberate deviation from the SKILL's literal tracker instruction:** I am keeping the
in-session tracker lean (active module + boundary) rather than seeding all 19 tasks. The SKILL
itself designates plan-file checkboxes as the durable source of truth and the in-session
tracker as "a convenience only"; a 19-row tracker would be re-seeded at every transition.
Flagging it so the auditor can overrule.

### 2. Did you dispatch all required reviewer subagents? If you batched or skipped any, state which and why.

None were required yet — no task has been dispatched. Zero reviews are outstanding.

For the planning session I can only report the committed record: `plan-review-report.md`
documents a two-round `plan-document-reviewer` loop — round 1 raised 5 blockers (validate-report
CLI shape; card checkpoint invocations repeating the N35 `--manifest` omission; an awk two-line
surface-ref bug; an incomplete test-migration list; a missing byte-proxy invariant test), all
fixed; round 2 Approved; 3 residual advisories applied. I did not independently re-verify each
of those five fixes — I am treating the reviewer's approval plus `validate-plan.py` PASS
(zero warnings, all 5 files) as the gate, per the authority order I was given.

### 3. Did you re-dispatch reviewers after fixing issues they found?

Not applicable to me yet (no dispatches). The planning session's record shows a genuine
round-2 re-dispatch after round-1 fixes, not a self-certification.

### 4. Are there any type ambiguities in the plan that you're uncertain about? List each with the specific fields.

1. **`handoff.expected_hops` on invalid/zero totals.** Contract Facts say invalid/zero totals
   are "absent-with-warning (notify suppressed, WARN logged)". Ambiguous whether the manifest
   `handoff` block is then written *without* the `expected_hops` key or omitted entirely. The
   `sdd_session.py` field type (`Optional[int]` vs key-absent) differs between those readings.
   Owned by Tasks 5/6 — flagging for the implementer to pin explicitly.
2. **`tasks_done` and verification reports.** Contract Facts: unique task IDs whose implementer
   report frontmatter "parses AND records completed status (verification reports count under
   their own rules)". "Their own rules" is not expanded anywhere I read. Task 7 owns this;
   the N16 precedent (verification reports validate with empty `files_changed`) is the likely
   intent but is inference, not a stated contract.
3. **`surface_uuid=` field type (operator addendum #1).** The addendum offers "a `surface_uuid=`
   field (or a `ref (uuid)` pair)" — two different log grammars. The record grammar in the
   Shared Contract Section is space-separated `key=value`, so a `ref (uuid)` pair containing a
   space would break field parsing. I read this as forcing the separate-field form, but the
   addendum does not say so. Task 13 owns it.

### 5. Are there any plan sections where you wrote code quickly and aren't confident in the logic? List each.

I wrote none of this plan's code. The plan's embedded snippets I have *read* and would flag:

- Module 1 Task 0 Step 4's measurement loop uses `cmux read-screen ... | grep -q "READY"` —
  a producer piped into `grep -q`, which is the exact SIGPIPE fail-open pattern CLAUDE.md
  forbids. It is **legitimate here** (measurement shell, no `pipefail`, and the plan says so
  explicitly in a comment), but an implementer pattern-matching on house style could either
  "fix" it or, worse, carry it into the spawn script. Worth an explicit instruction.
- Task 0 Step 4 sets `ELAPSED=timeout` as a sentinel string then compares numerically later in
  Step 5's derivation (`2 × max(runs_seconds)`). If any run times out, `runs_seconds` would
  contain a non-integer. The plan says to investigate before proceeding, so this is guarded by
  process rather than by code — acceptable, but the implementer must not silently coerce.

### 6. Are there any implicit assumptions in the plan that an implementer might miss? List each.

1. **The blocked path is not a fallback of convenience.** Task 0 Step 1 routes to a
   documented blocked path (`"measured": false, "default_seconds": 120`, matrix-fallback verb
   shapes) if cmux is unreachable. I have **verified live reachability at ingestion** (`cmux ping`
   → `PONG`, `CMUX_WORKSPACE_ID` exported and inherited by nested subshells, version exactly the
   pinned build). So for this run a failed check means something changed mid-flight, not that
   the blocked path is licensed. Downstream, Task 10 consumes `default_seconds` via an import
   assertion — a provisional 120 would silently ship a wrong production timeout. I will instruct
   the implementer to report NEEDS_CONTEXT rather than take the blocked path.
2. **`review_tier: minimum` on Tasks 1 and 3 does not waive the spec review** — it waives only
   the code-quality review and converts partner review to a controller-written minimum-tier file.
   Both tasks still write to `BACKLOG.md`.
3. **Task ordering inside Module 1 is not purely `depends_on`.** Tasks 1, 2, 3 all declare only
   `depends_on: [0]`, but the module text adds a constraint the frontmatter does not encode:
   "execute Task 1 before Task 3" (both append `BACKLOG.md` rows). An implementer reading only
   frontmatter would miss it. I will hold strict 0→1→2→3 order.
4. **Cleanup is part of the contract, not politeness.** Task 0 Step 6 and Task 1 Step 4 require
   deleting `task0-*` / `sp2-*` workspaces; Module 1 acceptance criteria assert none remain in
   `cmux list-workspaces`. These are the user's real sidebar entries — leaked workspaces are a
   visible defect.
5. **`handoff_spawn` must not appear in any frontmatter before Task 4.** `Plan` is
   `extra="forbid"`; adding it early fails validation loudly. Applies to fixtures and test
   manifests too, not just the plan files.
6. **The `.venv` symlink must not be recreated.** It points at the main checkout; ~60 tests
   spawn `.venv/bin/python3` by relative path.

### 7. What is the single highest-risk item in this plan?

**Task 0's measured `default_seconds` becoming wrong-but-plausible.** It is the one value in
this sprint produced by live measurement rather than by code, it is consumed downstream by an
import assertion in Task 10, and both of its failure modes are silent: the blocked path writes a
provisional 120 that *looks* like a real value, and a mis-run measurement (warm claude process,
picker version downloaded during timing, a `timeout` sentinel coerced to a number) produces a
plausible number with no signal that it is wrong. Everything else in the sprint is verified by
tests that would fail loudly.

Second-order: Task 0 is also the sprint's only escalation trigger. Three plan-wide Contract
Constraints rest on pinned live shapes (`rename-tab` field 2 = `action=rename` not a ref;
`close-surface` returns a plausible **wrong** ref; `read-screen` on a never-driven surface
errors). If the live captures contradict any of them, the SKILL's Task 0 rule is STOP-and-
escalate, not adapt-inline. **I am pre-committing to that duty now, before reading the report**,
so a mostly-good report cannot rationalize its way into "fix it as we go."

### 8. Were stale SDD artifacts found in the workspace from a prior session? If so, what was found and how were they archived?

**No stale artifacts. The pre-execution checkpoint's WARNING on this is a false positive**, and
I verified that rather than assuming it:

- `controller-checkpoint.py --phase pre-execution` returned `status: PASS`, `blockers: []`, exit
  code 2 (= warnings present; confirmed against the script's own `return 2` on
  `result.get("warnings")` — not a failure code).
- The warning reads: "deviations.md (has content from prior session)". The heuristic fires on
  *deviations.md being non-empty*. It is non-empty because I seeded it minutes earlier with the
  two adjudication rows the plan and the handoff explicitly require at ingestion.
- Evidence it is not prior-session state: `reports/` was empty at check time (created in the same
  minute); `git ls-files` shows `deviations.md` **untracked**; `git log` for the feature dir shows
  only spec/plan commits and no execution artifacts; the worktree is clean.

Logged here as the FYI the protocol asks for.

---

## Accepted deviations already recorded at ingestion (in `deviations.md`)

1. **`reason=policy-off` beats `reason=policy`.** The distilled spec's Acceptance Criteria say
   `off` refuses with `reason=policy`; its Contract Facts and Decision 14 say `reason=policy-off`.
   Contract Facts are binding per the plan's Contract Constraints. Adjudicated, not re-litigated.
2. **Operator addendum (3 amendments), relayed in `CONTINUE.md`.** Folded into existing tasks, no
   new tasks: (a) `surface_uuid=` in outcome records (refs renumber across cmux app restarts;
   UUIDs are permanent) — Task 13; (b) the two post-spawn `outcome` appends become **checked**
   writes using the reservation-write `if ! printf` pattern, closing BACKLOG N63 — Task 13;
   (c) post-spawn ordering hazard — `cmux send` was observed (N=1, mechanism unproven) to stop
   landing after `/remote-control` activation, so all terminal driving precedes `/rc`, `/rc` is
   sent LAST, and no post-`/rc` send step may be designed — Tasks 11 and 16.
