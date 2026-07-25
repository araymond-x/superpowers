# Spec Compliance Review — Task 9 (Rewrite context-handoff-protocol.md steps 3–5)

**Reviewer:** dispatched spec compliance auditor (sonnet), round 1
**Range reviewed:** `fdfef9b..f787039`
**Output budget given:** 800–1400 words
**Verdict: PASS** — no findings, blocking or advisory.

**Controller note on what this reviewer was asked to do differently:** because the controller had deliberately
deviated from the plan's verbatim replacement text in two places, the reviewer was told **not** to flag those as spec
violations but to do the harder thing — verify the corrections are themselves *true* and were applied *faithfully*,
and to treat a correction that replaced a false claim with a differently-false claim as BLOCKING. It was also told the
controller's own verification section in the implementer report is a claim to check, not established fact.

---

## Reviewer output (verbatim, as returned)

**Verified independently:**
- Anchor grep (`context-handoff-protocol` in `sdd-pre-dispatch-hook.sh:840`) — ran it myself; matched exactly the string the report quotes. CONFIRMED.
- Steps 1–2 byte-identical — diffed `fdfef9b` lines 1–21 vs. current lines 1–21: identical. Ran a positive control by appending a perturbation line and re-diffing: the diff correctly reported the injected difference, proving the comparison actually executes rather than silently no-opping. CONFIRMED.
- Only the target file changed — `git diff --stat fdfef9b..f787039` shows exactly one file, 30 insertions/9 deletions. CONFIRMED.
- Script freeze — `md5sum` of `spawn-handoff-session.sh` at `fdfef9b` and `f787039` identical; `git diff fdfef9b..f787039` for the script, `sdd-pre-dispatch-hook.sh`, and `baseline.txt` is empty. CONFIRMED.
- `validate-all-skills.py` result — re-ran it myself: `PASS: 159 FAIL: 0 WARNING: 2`. CONFIRMED, matches the report.
- Correction 1 (five-cause exit-3 enumeration incl. "a reservation write failed") — enumerated all `exit 3` sites myself: `:125` (cmux unreachable), `:137` (hop limit), `:195` (quota low), `:464`+`:469` (two reservation-write failures, `.handoff-hops` and the intent-log append — both collapse into the doc's single "a reservation write failed" cause), `:491` (spawn failed after reservation). Six call sites, five distinct causes, matching the doc text exactly. CONFIRMED accurate.
- Correction 2 (picker-manual notification claim) — traced the success path: `spawn_claude_workspace` (`:409-433`) fires one `cmux notify` call (`:429`) with a fixed body template `"Hop $SP_HOP/$MAX_HOPS — successor spawned in {workspace}"`, called identically for both `LAUNCH_MODE=auto` and `LAUNCH_MODE=picker-manual` at the single call site `:472`. The body never mentions picker or mode. In `picker-manual`, `SUCCESSOR_CMD="claude-picker $PICKUP_ARG"` (`:377`) — no `--non-interactive`, so a human genuinely must interact with the picker. The corrected sentence ("the spawn notification fires either way and does not name the mode") is TRUE — it claims the call is invoked regardless of mode and is mode-agnostic in content, not that delivery always succeeds (notify failure at `:429-430` degrades to a stderr warning only, doesn't change exit code). CONFIRMED, not a differently-false claim.
- Commit — `f787039`, message exact match to spec. CONFIRMED.
- Report completeness — all required sections present (frontmatter contract_compliance, Implementation Summary, Source Files Read, CLAUDE.md Files Read, Deviations, Self-Review, Concerns, plus embedded controller verification); none suspiciously empty. CONFIRMED.
- The 41-vs-40-line discrepancy — `wc -l` on `fdfef9b`'s copy and the pre-edit working tree both give 40. The report's "41-line" is an off-by-one in prose only; it doesn't affect any load-bearing claim (the diff hunks, byte-identical check, and final line count 40→61 are all independently correct). I agree with the controller's disposition: immaterial, correctly logged rather than smoothed over. It's a minor signal about report care, not reliability — every other quoted number/artifact in the report checked out exactly against git.

Both deviations.md rows (lines 69–70) for Task 9 match my independent findings precisely, including the same "six sites, five causes" framing and the same notify-template citation.

**Placement/consistency checks:** "Soft-nudge use" note is appended after the "A soft nudge" paragraph as its own paragraph (lines 58–61), not merged in. "Why a block" (unchanged, still says "...depends on you following steps 2–5") still coheres — steps 2–5 still exist and cover commit/build-handoff/spawn/stop. Opening paragraph (blind-streak block mention, lines 1–10) is untouched and still coherent.

No unauthorized content deltas found beyond the two logged corrections.

**Verdict: PASS** — spec-compliant and contract-compliant. No findings, blocking or advisory.

---

## Controller disposition

**PASS accepted. Proceeding to code quality review.**

Two things recorded about this round:

1. **The reviewer ran its own positive control, and it was a MUTATING one.** It appended a perturbation line to
   `context-handoff-protocol.md` and re-diffed to prove the byte-identical comparison was not silently no-opping.
   That is exactly the discipline this run demands — but it means a reviewer temporarily modified a committed file.
   **The controller verified restoration independently** after the review returned: `git status --short` and
   `git diff --name-only` for the target file are both **empty**, and `wc -l` is 61 (the committed length). The only
   dirty paths in the tree are SDD harness artifacts (`deviations.md`, the module plan, `.dispatch-log`,
   `context-observations.log`) plus this task's three new untracked report files. Nothing leaked.
   Worth noting for future rounds: the run's standing rule is that mutating an artifact to prove a test is fine, but
   restoration must be **verified, not assumed**. The reviewer did not state that it restored the file; the controller
   checked rather than trusting.

2. **The strongest part of this review is the answer the controller specifically probed for and did NOT get as a
   rubber stamp.** The reviewer was asked to scrutinize whether the *new* phrase "the spawn notification fires either
   way and does not name the mode" is itself true, including under notify failure. It answered the precise question:
   the sentence claims **invocation** and **content**, not **delivery** — and notify failure at `:429-430` degrades to
   a stderr warning without changing the exit code, so the sentence remains true. That is a real distinction, not a
   restatement, and it is the distinction that would have made the correction a differently-false claim if it had gone
   the other way.

No claim in this review was rejected.
