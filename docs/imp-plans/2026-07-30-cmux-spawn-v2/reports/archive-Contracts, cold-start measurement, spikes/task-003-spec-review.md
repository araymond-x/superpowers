# Spec Compliance Review — Task 3 (SP3 + SP4 design docs + BACKLOG rows)

**Dispatched:** 2026-08-01 (`reports/.dispatch-log`: `task=3 type=spec-review`)
**Model:** sonnet
**Reviewing:** commit `0e4b420` (`git diff 553bbe3..0e4b420`) — 3 files, 626 insertions
**Verdict:** **PASS** — spec compliant AND contract compliant. One ADVISORY finding, non-blocking.

---

## Mechanical checks (run independently by the reviewer, not taken from the report)

| Check | Command | Result |
|---|---|---|
| Byte-identity N80 | tail-anchored fence extractor vs `grep "^\| N80 \|"` | **IDENTICAL** |
| Byte-identity N81 | same, N81 | **IDENTICAL** |
| No line-number citations | `grep -nE '\.(sh\|py\|md):[0-9]+'` over both docs | **clean, zero hits** |
| N54/N57 untouched | `git diff -U0 … \| grep -cE '^[+-]\| N5[47] '` | **0** |
| BACKLOG numstat | `git diff --numstat` | **2 0** (append-only) |
| Scope | `git diff --name-only` | exactly 3 files, no code file |
| Id freedom | enumerated `main` (top N78) and branch at `553bbe3` (top N79) independently | **union max N79 → N80/N81 free on both** |
| `verify-symlink-install.sh` | ran directly | **104 passed / 0 failed / 0 warnings, PASSED** |
| Only CLAUDE.md in tree | `find . -name CLAUDE.md` | **one hit, repo root** |

## Code-claim spot checks

The reviewer checked **seven** load-bearing claims against actual source (four were requested), including the highest-risk one:

1. **Manifest gating.** Banner `─── Require manifest mode (legacy non-manifest path removed) ───` exists; the `if [ "$MANIFEST_MODE" = false ]` block exits early (`exit 0`, or `exit 2` in the SDD-shaped-but-unmanifested sub-case) **before** `IS_IMPLEMENTER` classification and before the context gate. Both branches satisfy the doc's claim. Confirmed.
2. **Context gate scope.** Banner `─── Context-pressure gate (implementer new-task path only) ───`, then `if [ "$IS_IMPLEMENTER" = true ]; then if [ "$MARKED_FIX" = true ]; then ctx_observe_and_log other  # fix dispatch: log only, never gated`. **Quoted verbatim in the doc; matches source verbatim.**
3. **`context-probe.py` stdlib-only + SDD-agnostic.** Imports exactly `argparse, json, os, sys, pathlib.Path, typing.Optional`; `grep -n "sdd\|manifest\|active-feature"` → zero hits; `resolve_transcript` priority matches the documented order.
4. **`transition-module.py` archive + truncate, no inverse.** `shutil.move` into `archive-{completed_module}/`; `shutil.copy2` then `open(dispatch_log, "w").close()  # truncate to empty`. The six `def` names the doc enumerates are the complete and correct list; no inverse operation exists.
5. **HIGHEST-RISK — Check 9 does not police fix dispatches.** `_check_verification_git_reality` opens `if not verification_ids: return []`. `_merged_dispatch_times` compiles `r"(\S+)\s+DISPATCH\s+implementer\s+task=(\d+)\s+type=implementer"`, docstring verbatim: *"Parses ONLY `type=implementer` lines — the shared dispatch-log contract with N26: type=fix / type=fix-unattributed lines never open a verification window."* → **SP4's contradiction of the plan's Check-9 framing is CORRECT, not an error.** Verified by direct source read.
6. **`sdd-stop-hook.sh`.** Header `Exit codes: 0 — Always (advisory injection, never blocks)` verbatim. Reads only `.cwd` via `jq -r '.cwd // ""'`. Three independent `exit 0`s gate on reports-dir / deviations-file / plan-file — matches "SDD-gated three times over".
7. **`check-hooks.sh` `HOOKS=()`.** Hardcoded 7-path array confirmed.

**Negative-evidence check independently re-run** (the wrongly-reported-negative risk): `grep -rn --include='*.md' -e '\$127'` → 3 hits, all spec/plan one-liners; `569k` → nothing further; every reachable `context-observations.log` under `~/projects/claude-custom/` swept → **no ~569k row**, nearest 539691 / 621072. **Exact match to the doc's reported negative. It holds up.**

Further corroborations: `jq -r '.hooks | keys[]'` → `PreToolUse SessionStart Stop UserPromptSubmit`; `claude-usage-pace` exists, dated Jul 2; BACKLOG N26 status `done`, commit `7dc7812`; cited commits `949d310` and `7dc7812` both resolve; the `0→9`/`0→17` rows and Deferred Work table are real; `grep -c 'type=fix' .dispatch-log` → **7**, matching "seven live `type=fix` rows"; task-range validation sits before Checks 4b/4c/5c/5d in file order, confirming the doc's ordering claim.

## Contract constraints

- ★ **SKILL.md word ceiling** — both docs explicitly route recommended protocol content to `skills/subagent-driven-development/references/`, citing `references/context-handoff-protocol.md` as precedent, and both state "never SKILL.md (word ceiling)" in their own text. Verified by reading. **Compliant.**
- **Baselined-hook obligation** — not triggered (no hook edited); SP4's Candidate A explicitly states a future implementing task would owe a same-change `check-hooks.sh --capture` + committed `baseline.txt` if it touches `sdd-pre-dispatch-hook.sh`. **Compliant.**
- **NO implementation** — 3 markdown files only, no code touched; neither doc reads as a build plan (designs framed as options with rationale, explicitly disclaiming implementation: *"Nothing here is scheduled and nothing here is implemented"*). **Compliant.**

## Step coverage

Both Step bullet-lists walked literally against the docs' actual headings. Every enumerated item present and substantively covered:
- **SP3** — evidence / why-not-extend / three candidate homes / probe reuse / recommendation + rollout risk / BACKLOG row.
- **SP4** — today's rule / observed friction / three candidate designs / enforcement-interaction table covering 4c/5c/5d/9/N26 / recommendation / BACKLOG row.

Both end with the BACKLOG row as instructed.

## Findings

**`[ADVISORY] [MISUNDERSTANDING]`** — The implementer report's "Claims Verified" §15 states each quoted `deviations.md` phrase "greps to exactly 1 hit", listing the *"rides the fix round"* phrase among them. Independently, `grep -c "rides the fix round that already owes the other two" deviations.md` returns **2** — the original in the row-79 DeferredWork entry, and a second where a later ProcessNote row quotes the phrase back for context. **The anchor is still real and unambiguous, and SP4's content is unaffected**; the report overclaims the precision of its own verification methodology.

**Controller independently re-verified this finding**: `grep -c` → **2**, at the `| 2 | DeferredWork |` and `| 2 | ProcessNote |` rows. The reviewer is correct.

No BLOCKING findings — no CONTRACT and no MISSING issues. No other EXTRA or MISUNDERSTANDING items survived verification.

## Report completeness

All required sections present and substantive — Status, Implementation Summary, Files Changed (frontmatter), Source Files Read, Tests (frontmatter), Contract Compliance (frontmatter), Deviations from Plan, Self-Review Findings, Concerns. None suspiciously empty. `validate-report.py` → `COMPLETE`, 5/5 prose sections.
