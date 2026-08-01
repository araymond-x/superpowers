# Task 2 Spec Compliance Review — SP1 context-probe attribution

**Verdict: FAIL** — one blocking finding (one defect class, three sites), two advisories. Report is complete; not `REPORT_INCOMPLETE`.

The root-cause work is correct, and I confirmed it by execution rather than by reading the report. The blocker is that the **stated mechanism** in the durable artifact is factually wrong, and the wrong version is the one scheduled to be pasted into `main`'s BACKLOG at merge.

---

## What I verified independently (all PASS)

Every item below was re-run or re-read, not accepted from the report.

| Claim | How verified | Result |
|---|---|---|
| Root cause block is real, correct transcript, correct time | Read `d8a9d842-…jsonl` cross-repo, read-only | `2026-07-30T00:55:22Z`, `isSidechain: False`, `sessionId` matches filename, top-level total `373139`, iterations `message/advisor_message/message` with subtotals `183210 / 186188 / 189929` — **byte-exact as documented** |
| Fixture `iterations-advisor-triple.jsonl` is the real block verbatim | Field-by-field compare against the archived usage block | **Identical** on all four fields, all three iterations |
| Archived log row + neighbors | Read `…/2026-07-29-cmux-transport/reports/context-observations.log` | Rows `171666 / 373139 / 210693` present as quoted; file is 80 rows as claimed |
| No-op on single-iteration turns | Ran the doc's own reproduce script | `single: 32517, top-level != iterations[0]: 0` — **zero mismatches** |
| Controller-session correction `539691 → 270851` | Read `3cc7b8ba-…jsonl` | `top-level 539691`, `sum-message-iters 539691`, `sum-all-iters 811442`, last `message` iteration `270851` — **confirmed** |
| Stdlib-only under the hook's interpreter | `/usr/bin/python3` (3.9.6) ran the probe directly | Exit 0, printed `189929`. Imports are `argparse, json, os, sys, pathlib.Path, typing.Optional` only |
| Python 3.9 compat | `validate-all-skills.py` | PASS 159 / FAIL 0 / WARNING 2 (the two pre-existing soft word-count advisories) |
| Probe + gate suite | `.venv/bin/python3 -m pytest tests/unit/test_context_probe*.py tests/unit/test_context_gate*.py` | **52 passed** |
| e2e no-regression | `bash tests/integration/sdd-e2e-test.sh` | `E2E PIPELINE PASS - 15 steps`, including Step 13's live context gate |
| Baseline claim recorded **in the doc** (Step 4's actual requirement) | Read the doc's "Files changed" section; re-ran the grep | Doc states `grep -c 'context-probe' tests/ARaymond-hook-baseline/baseline.txt` returns 0 and a broader `grep -n 'probe'` returns no match. **Both reproduce.** Requirement satisfied in the durable artifact, not merely in the report |
| `SOURCE_VERSION` parity pin still accurate | `shasum -a 256 ~/.claude/bin/claude-ctx-check \| cut -c1-12` | `f83727ff80c0` — matches the constant and the doc's parity paragraph |
| Existing parity test unaffected | Checked which fixtures carry an `iterations` key | Only the seven new `iterations-*.jsonl` do; `below/soft/hard/malformed-trailing/missing-fields/non-numeric` do not, so `test_context_probe_fixtures.py` genuinely takes the fallback path as the doc claims |
| Cross-repo read-only | `git -C ~/projects/claude-custom/claude-codex-handoff/.worktrees/cmux-transport status --porcelain` | **Empty** — nothing modified outside this worktree |
| `BACKLOG.md` untouched | `git diff --stat a4dc986..HEAD` | Not in the changeset |
| Code change authorized by the plan's conditional | Root cause is a probe defect | Satisfied — the plan's "if a probe bug, patch it" branch applies |

**Differential integrity of the new tests holds by construction**, so no mutation run was needed: `legacy_total` is an independent reimplementation of the pre-fix behavior, and each multi-iteration test asserts *both* the legacy value and the corrected value. A revert makes `run_probe == legacy_total` and fails the second assertion (`373139 != 189929`). `test_last_message_iteration_wins_when_advisor_is_last` uses a `999999` sentinel top level that no fallback path can produce — a genuinely chosen behavior, not an accidental one.

---

## FINDING 1 — [BLOCKING] [MISSING]: the stated mechanism is wrong in the durable doc, in the N76 merge text, and in the shipped docstring

**One defect class, three sites, one fix round.** This is spec-review item #2, and it did **not** land.

### The claim is empirically false

`docs/process-improvement-findings/2026-07-30-sp1-context-probe-attribution.md`, opening summary:

> "Claude Code records those calls in `usage.iterations` and the top-level fields are their *sum*, so the same cached prompt was counted once per call."

Measured against the controller's own peak block (`3cc7b8ba`, `type` sequence `message / advisor_message / message`):

```
sum of ALL iterations      = 811442
sum of message iterations  = 539691
top-level                  = 539691   <- equals message-only
```

The `advisor_message` iteration is **excluded** from the top-level fields. The correct statement is *"the top-level fields are the sum of the `type: "message"` iterations."*

### The doc contradicts itself, and the wrong version is the one that carries

The evidence section of the same document already states the correct fact:

> "`input_tokens`: `2 + 2 = 4`, and `output_tokens`: `1641 + 5364 = 7005` — the `advisor_message` iteration's own `in`/`out` are *excluded* from the top level"

So the document asserts both readings. The wrong one sits in the summary — the part a reader takes away — and, critically, in the **verbatim BACKLOG N76 replacement text**:

> "Claude Code records those in `usage.iterations` and the top-level fields are their SUM, so the same cached prompt is counted once per iteration"

That block exists to be pasted into `main`'s `BACKLOG.md` at merge. **The false mechanism is scheduled to propagate to a second durable artifact by design.** That is what makes this blocking rather than a prose nit.

### Third site: committed code, and it carries a second falsified claim

`skills/subagent-driven-development/scripts/context-probe.py`, module docstring, parity divergence 2:

> "Claude Code records them in `usage.iterations` and the TOP-LEVEL `usage` fields are their SUM"

and, in the same paragraph:

> "claude-ctx-check (and the statusline `ctx:` field it mirrors) still carry the uncorrected behavior"

The statusline half was **falsified by the controller's own pre-registered experiment** (recorded in the SP1 doc's final section, in `context-summary.md`, and in `deviations.md`). This is the last surviving instance of that claim in committed code — the controller corrected the five artifacts it owned; this one it deliberately left, because the file is inside Task 2's write scope with reviews pending.

### The recorded remediation is scoped too narrowly

`deviations.md` carries a `DeferredWork` row owning this — but it prescribes the fix **only for `context-probe.py`'s docstring**. The durable doc's opening paragraph and the N76 merge block are outside that row's scope. As written, the recorded remediation would ship a corrected docstring and leave the two documentation sites wrong.

(This row was not among the two pre-authorizations the dispatch listed as non-findings, so it is in scope to report.)

### Required

Widen the `[task 2 fix]` round to three sites, one edit each:

1. `2026-07-30-sp1-context-probe-attribution.md` — opening summary paragraph: "sum of the **`type: "message"`** iterations."
2. Same doc — the blockquoted N76 replacement text: same correction, since that text is copied to `main`.
3. `context-probe.py` docstring — same correction, **plus** drop the statusline from divergence 2 (`claude-ctx-check` alone).

**Attribution:** the wording is the implementer's. The controller detected it during independent verification, recorded it in the report and in `deviations.md`, and correctly declined to hand-edit implementer output mid-review — but scoped the remediation to one of the three sites.

---

## ADVISORY 1 — [MISUNDERSTANDING]: the doc promises a recomputation command for every measurement and delivers one

The SP1 doc's opening states:

> "Measurements below were taken **2026-07-31**; each is paired with the command that recomputes it."

Only the prevalence sweep carries a runnable command block. The monotonicity table (77/132 turns, 2/2 drops → 0/0), the 80-row match and its "exactly one poisoned row" positive control, and the live-replay table (`373139 → 189929`, `539691 → 270851`) are bare figures.

This matters because the practice works where it *was* applied: re-running the sweep today returned `32,517` single-iteration turns against the doc's `32,160` — corpus growth, correctly absorbed because the command travels with the number. The unpaired figures have no such recovery path, and the repo's `CLAUDE.md` rule is to give the command rather than the number. Either attach commands to the remaining measurements or soften the opening promise to describe what the doc actually provides.

*Not* a finding: the `32,517`/`32,160` and `797`+`18`/`793` deltas themselves. That is expected drift, and it validates the pairing convention.

## ADVISORY 2 — [EXTRA]: duplicate, misnamed report file; `files_changed` omits the seven fixtures

The implementer wrote its report to `docs/imp-plans/2026-07-30-cmux-spawn-v2/reports/task-002-implementation.md` (commit `529f283`). `skills/subagent-driven-development/references/report-naming-convention.md` prescribes `task-NNN-implementer-report.md`, and the hook gates on that name. The controller supplied the conventional file at `890eacc`, so nothing is blocked — but two report files for one task now coexist with divergent content.

Specifically, the controller-authored `task-002-implementer-report.md` lists **three** paths in `files_changed`, omitting the seven `tests/unit/fixtures/context-probe/iterations-*.jsonl` files. The implementer's misnamed file lists all ten. The reviewed report therefore understates the changeset; the fixtures are mentioned only in prose. Consider consolidating to the conventional filename with the complete `files_changed` list before the module boundary archives both.

---

## Report completeness — COMPLETE

`validate-report.py --report-file …/task-002-implementer-report.md` returns `"status": "COMPLETE"`, `"sections_missing": []`. Every section the dispatch enumerated is present: Status, `files_changed`, `tests`, and `contract_compliance` in frontmatter; Implementation Summary, Source Files Read, Deviations from Plan, Self-Review Findings, Concerns in prose. No section is suspiciously thin — Self-Review Findings and Concerns both carry substantive, falsifiable content, including the implementer's own admission that the mechanism imprecision was caught by the controller and not by self-review.

---

## Checked and deliberately not reported

- **Unchecked Task 2 plan checkboxes.** `subagent-driven-development/SKILL.md` assigns checkbox updates to the controller *after* both reviews pass ("After marking each task complete in TodoWrite, the controller MUST also update the plan file"). Unchecked at spec-review time is the expected state.
- **No exclusion rule adopted; no BACKLOG row appended.** Both pre-authorized by the dispatch. The doc's "Guidance for tuning consumers" section discharges the pre-authorization honestly — it states plainly that the plan's `>50%` rule "cannot distinguish a poisoned reading from a real peak," ranks recomputation-from-transcript first, and explicitly flags the residual that zero compaction events were observed so the 2.0× discriminator has never been tested against a real peak. That is the "cannot discriminate, here is why" branch, not silence.
- **Five hypotheses tested where the plan listed three.** Declared as a deviation; (d) and (e) were injected by the dispatch. Broader than requested, not narrower.
- **Absence of an `iterations`-shape version canary.** Not requested by the plan, and explicitly deferred by the controller in a recorded deviation. Flagging it would be scope expansion.

---

## Bottom line

The engineering is sound and independently reproducible — I confirmed the root cause against the raw archived transcript, reproduced the no-op proof, and ran every suite the plan named. What fails spec compliance is narrow and precise: the mechanism sentence the whole document rests on is wrong in three places, one of which is committed code and one of which is queued for copy into `main`'s BACKLOG. The recorded `[task 2 fix]` round already owns one of the three sites; widen it to all three and this passes.
