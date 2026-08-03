# Pre-Execution Audit — Verdict and Order Resolutions

**Feature:** cmux-spawn-v2
**Date:** 2026-07-30
**Auditor verdict:** ORDERS_ISSUED — 3 Block-A orders (Task-0 window), 8 Block-B orders.
**Controller disposition:** all 11 orders accepted. None rejected, none silently dropped.

The auditor split orders by **deadline**, not severity, and that split is honored literally.
Block A can only be satisfied inside Task 0 — it is the sprint's sole live-cmux capture window,
and Task 0 is the next dispatch. Block B orders land before their owning task dispatches;
deferring those is correct sequencing, not deferral of in-scope work. Every deferred order below
names its owning task and the gate it must clear.

**Independent verification:** I did not take the auditor's findings on trust. B1 and A1 were the
load-bearing claims, so I verified both against the filesystem before acting (transcript in the
session): `tests/unit/test_spawn_handoff_hardening.py` exists (9620 bytes), `_did_not_spawn` is
literally `return "new-workspace" not in _cmux_log(tmp_path)`, the file is referenced nowhere in
the plan set, and `surface_uuid` appears in no plan file. Both claims held exactly as stated.

**Gate state after amendments:** `validate-plan.py` → PASS, **zero warnings**, zero blockers on all
five plan files — the same state the plan was committed in. My first amendment pass pushed Task 0 to
263 lines and Task 9 to 225 (over the 200-line limit); I compressed the prose rather than accept the
regression. No contract fact or escalation duty was cut to achieve that.

---

## Block A — resolved as Task 0 plan amendments (before dispatch)

| # | Finding | Resolution | Status |
|---|---------|-----------|--------|
| A1 | `surface_uuid=` (operator addendum #1) had **no source and no capture** anywhere in the plan — accepted in `deviations.md`, implemented nowhere, and cmux capture would be over by Task 13. | Added **Step 2b** to Task 0: probe `cmux identify --json`, `--id-format both`, `list-pane-surfaces`, and `new-surface --help` against the live surface, before `close-surface`. Records `surface_uuid_source` as `{available: true, verb, key_path, example}` or `{available: false, transcript}`. Explicitly states that **unavailable is a legitimate documented outcome** converting addendum #1 into a recorded refusal — and forbids inventing a substitute identity scheme. | RESOLVED |
| A2 | `wait-for` **latching is never probed**, yet Task 10 calls `wait_for_token` twice. A token signaled in the gap between the two waits, if not latched, yields `handshake=timeout` on a *healthy* successor — a false negative on the sprint's central "token is the only exit-0 path" contract. | Added **Step 2c**: probes both signal-then-wait and the gap case that models the re-wait. Records `wait_for_latching: {latching, transcript}`. Made an explicit **escalation trigger**: if `latching` is false, Task 10's two-call re-wait is unsound as designed — STOP and report, do not redesign or work around. | RESOLVED |
| A3a | Task 11's post-spawn `/rename` verification searches the screen for the **very title text it just sent**, so the shell echo satisfies the check whether or not `/rename` ran. `spec-distilled.md` records this precise defeat as already paid for ("shell echo defeating composer verify"). | Added **Step 4b**: capture the real `/rc` and `/rename` confirmation screens verbatim into `rc_confirmation_screen`, and require the report to name the exact substring that proves `/rc` is active **and cannot appear in the sent line**. Ordering is pinned as load-bearing — Step 4b runs only *after* all five Step-4 timing runs, in its own `task0-rc` workspace, because Step 4's method requires no warm claude process. `/rename` is probed *after* `/rc` deliberately, so a non-landing second send cheaply reproduces the addendum-#3 hazard. | RESOLVED |

A3b/A3c (Task 11's anchor rewrite + negative fixture) are the **consuming** half of A3 and are
deferred to Task 11 — see Block B. A3a is what could only happen now.

Supporting amendments made alongside Block A:
- Task 0's fixture-contract test gains `test_audit_ordered_probe_keys_present`, asserting all three
  probe keys exist **including negative answers** — an absent key is otherwise indistinguishable
  from an unrun probe. Expected count updated 2 PASS → 3 PASS.
- Task 0 Step 6 cleanup now enumerates `task0-shapes`, the five `task0-cold-*`, and `task0-rc`.
- Module 1 acceptance criteria gained the probe-recorded and escalation-fired criteria.

---

## Block B — resolutions and scheduled deferrals

| # | Finding | Resolution | Status |
|---|---------|-----------|--------|
| B5 | Prose-only ordering constraints the frontmatter does not encode: Module 1 has **three** `BACKLOG.md` writers (1, 2-conditional, 3) but only one stated pair; Module 4 serializes 14→15 in prose while both declare `depends_on: [13]`. | Encoded in frontmatter, where the tooling actually reads: Task 3 → `depends_on: [0, 1, 2]`, Task 15 → `depends_on: [13, 14]`, in **both** the module file and the parent `plan.md`. Module 1's prose rewritten to name all three writers and to require Task 3 to read `BACKLOG.md` at execution time rather than assume plan-time-reserved ids. | RESOLVED |
| B6 | The import assertion the sprint's top risk rests on is under-specified. (Auditor also corrected my premise: it lives in **Task 9 Step 4**, not Task 10.) It uses `re` and `SCRIPT`, neither defined in `test_spawn_handoff_v2.py` as Task 0 creates it, and its anchored regex silently requires a column-0 assignment. | Amended Task 9 Step 4: adds the `re` import and `SCRIPT` constant explicitly, states the column-0 requirement, and gives both asserts failure messages that name the requirement. Field names were verified to match already (`default_seconds` written by Task 0 Step 5, read by Task 9). | RESOLVED |
| B8b | Task 0's blocked path says "skip to Step 5", but Step 5 *rewrites* `cold-start-timing.json` with the `measured: true` shape and a `runs_seconds` array the blocked path never produced. | Corrected to **Step 7**, with the reason stated inline so it is not "fixed" back. Also hardened the surrounding text: the blocked path is explicitly **not licensed for this run** (controller verified live reachability), and a failed check must report NEEDS_CONTEXT rather than self-authorize the fallback. | RESOLVED |
| B1 | **Most serious finding.** `tests/unit/test_spawn_handoff_hardening.py` (10 tests guarding two fail-OPEN defects from the 2026-07-28 outside review) is owned by no task and appears in no plan file. Task 8 breaks `test_nonnumeric_max_hops_...` (it seeds `.handoff-hops`=3 *because 3 is the default*; the derived default becomes ≥6). Worse, Task 9 turns `_did_not_spawn` — literally `"new-workspace" not in log` — into a no-op that returns `True` **even when the script spawned**, silently voiding the "nothing was spawned" half of 7 assertions. | **DEFERRED to Module 3.** Must land before Task 8 dispatches: add the file to Module 3's Write-Scope table (Tasks 8 and 9) and the parent's Module-3 row; Task 8 pins `SUPERPOWERS_CMUX_MAX_HOPS=3` explicitly; Task 9 rewrites `_did_not_spawn` to assert absence of **every** spawn verb (`new-surface`, `workspace create`, `new-workspace`) **plus a positive control** proving the helper still detects a real spawn. Gate: Module 2→3 transition. | DEFERRED — Module 3 (pre-Task-8) |
| A3b/c + B2 | A3b/c: post-spawn verification must anchor on a string the sent line cannot contain; drop the loose `remote.control` alternation; add a negative fixture containing only the echoed command. B2: `SUPERPOWERS_CMUX_POST_SPAWN` iterates in **user-supplied order** and its validator accepts `rc,rename` — permitting exactly the ordering operator addendum #3 forbids. | **DEFERRED to Task 11.** Canonicalize the step list so `rc` is always last (or reject a list where it is not, with the standard validate-warn-revert message citing the addendum), add an ordering test, and add a code comment citing the addendum so it is not "simplified" away. Anchor strings come from Task 0 Step 4b's capture. Gate: Task 11 dispatch. | DEFERRED — Task 11 |
| B3 | Addendum #1's record-grammar consequences are unfolded: Task 13 has no `surface_uuid=` step, and the three outcome `printf`s (Tasks 9, 10) omit the field. (Auditor confirms Task 13(a)'s widening from two appends to all three is a correct superset of addendum #2 — that part is fine.) | **DEFERRED to Task 13**, and **conditional on A1's answer**: if A1 returns available, emit `surface_uuid=<value\|->` in all three outcome records and update the parent's §2 grammar, Module 3's assertions, and e2e Step 14 (Task 17). If A1 returns unavailable, replace with an explicit deviations row declining addendum #1 with A1's evidence. Either way it is not silently dropped. Gate: Task 13 dispatch. | DEFERRED — Task 13 (A1-conditional) |
| B4 | `Handoff.expected_hops` is declared required (`Field(ge=1)`, Task 5) but Task 8's `write_manifest` helper emits a handoff block without it — a latent model/fixture divergence exercising a shape `validators.py session` would reject. | **DEFERRED to Module 2.** Pin ONE reading in Module 2's Contract Constraints and apply it in both places: either `expected_hops: int \| None = None` with a Task 5 test for the partial block, or `write_manifest` always emits it and a Task 5 test asserts a partial block is rejected. Do not ship both readings. Gate: Task 5 dispatch. | DEFERRED — Module 2 (pre-Task-5) |
| B7 | Python 3.9 compatibility is a real gate (`validate-all-skills.py` `check_python39_compat` scans every `.py` in `subagent-driven-development/scripts/` and FAILs on PEP-604 unions and builtin generics in annotations). `_handoff_support.py` and `write-mechanics-card.py` land there, but the constraint is stated in no module and is not checked until Task 18 — so a Module 2 violation would surface at sprint's end as exactly the cross-module fix SP4 exists to *design* rather than exercise. | **DEFERRED to Modules 2 and 4** — one Contract Constraints line each. Note the asymmetry that makes this easy to get wrong: `X \| None` **is** correct in `skills/scripts/models/` (not scanned), so Task 5's `Handoff \| None` is right while the same syntax in `_handoff_support.py` would fail. Gate: Module 2 dispatch. | DEFERRED — Modules 2, 4 |
| B8a | `module-4` cites `test_intent_write_failure_exits_3`; the real name is `test_intent_write_failure_exits_3_without_spawning`. | **DEFERRED to Task 13** (citation fix in the owning task's text). Gate: Task 13 dispatch. | DEFERRED — Task 13 |

---

## Auditor findings that closed my open uncertainties (no order needed)

The auditor resolved two of the three type ambiguities I flagged, by reading artifacts I had not:

1. **`handoff.expected_hops` on invalid/zero totals** — `materialize-manifest.py` already errors when
   `total_tasks == 0` and validates tier, both *before* Task 6's wiring point, so the required-field
   model is correct at materialization; "absent-with-warning" applies only to spawn-time
   re-derivation, which Task 8 already handles. My worry was reasonable but the artifacts answer it.
   (A *different* real problem survives in that area → B4.)
2. **`tasks_done` / "verification reports count under their own rules"** — expanded explicitly in
   Module 2's Contract Constraints one file away from where I looked: statuses `DONE`/
   `DONE_WITH_CONCERNS`, with `files_changed` permitted empty. Not inference after all.
3. **`surface_uuid=` field form** — **worse** than I described: not a grammar choice, but a field with
   no source anywhere. → A1 + B3.

My two plan-snippet logic concerns were confirmed benign: the Task 0 `grep -q` pipe is a measurement
shell with no `pipefail` and carries an explicit in-plan comment (Tasks 10 and 11 correctly use
here-strings); the `ELAPSED=timeout` sentinel is guarded by process ("investigate before proceeding")
plus my pre-committed escalation duty.

Verified-clear, recorded so they are not re-audited: `handoff_spawn` appears in no frontmatter before
Task 4 (only Task 6's fixture, correctly after); `REQUIRED_SECTIONS` is a list of 2-tuples so the
card generator's unpacking is right; `hooks/session-start` does run `set -euo pipefail`, making
Task 14's backgrounded-subshell shape correct; Check 3b's real regex matches the plan's quote
character-for-character; `SddSession.total_tasks` is real (=19 on this live manifest).

## Standing escalation duty (pre-committed before reading any Task 0 report)

Task 0 is this sprint's only escalation trigger. If the live captures contradict any pinned Contract
Constraint — `rename-tab` field 2 = `action=rename` (not a ref), `close-surface` returns a plausible
**wrong** ref, `read-screen` on a never-driven surface errors — or if `wait_for_latching` is false,
the SKILL's Task 0 rule is **STOP and escalate**, not adapt-inline. Recording it here, before the
report exists, so a mostly-good report cannot rationalize its way into "fix it as we go."
