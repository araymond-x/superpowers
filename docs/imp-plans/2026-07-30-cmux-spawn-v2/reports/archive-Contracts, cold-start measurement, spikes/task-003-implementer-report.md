---
schema_version: 1
task_id: 3
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "docs/process-improvement-findings/2026-07-30-sp3-non-sdd-context-guard-design.md"
    description: "SP3 design doc: where a context guard for non-SDD sessions should live. Evidence (with a negative result on its provenance), why the SDD gate cannot extend (manifest early-exit + implementer-new-task-only), three candidate homes each independently verified, probe-reuse story, advisory-not-blocking recommendation with rollout risk, and the verbatim N80 BACKLOG row."
  - path: "docs/process-improvement-findings/2026-07-30-sp4-carry-forward-fix-lane-design.md"
    description: "SP4 design doc: sanctioned carry-forward fix lane across module transitions. Today's rule as enforced (measured, not read), four real in-repo friction instances, three candidate designs plus a reserved-slot variant, an enforcement-interaction table, recommendation, an explicitly unsolved residual, and the verbatim N81 BACKLOG row."
  - path: "docs/process-improvement-findings/BACKLOG.md"
    description: "Two appended rows, N80 (SP3) and N81 (SP4), byte-identical to their docs' fenced row blocks. Append-only: +2 lines, 0 deletions."
tests:
  written: 0
  passing: 0
  command: "bash tests/ARaymond-installation/verify-symlink-install.sh"
  result: PASS
contract_compliance:
  - constraint: "SDD SKILL.md is near its word ceiling: protocol content goes in references/, never the SKILL body."
    status: compliant
    detail: "Both docs route recommended protocol content to skills/subagent-driven-development/references/, citing references/context-handoff-protocol.md as precedent, and both say explicitly 'never SKILL.md (word ceiling)'."
  - constraint: "Baselined-hook edits ship with one check-hooks.sh --capture + committed baseline.txt in the same change."
    status: not_applicable
    detail: "This task changes no hook. Both docs state the conditional obligation for a future implementing task. Verified rather than assumed that check-hooks.sh pins a hardcoded HOOKS=() array, so a NEW hook does not enter the baseline automatically."
  - constraint: "NO implementation in either doc — design docs only."
    status: compliant
    detail: "Write scope was exactly the three listed files. No code file touched. The one experiment ran against a throwaway git fixture, never the repo."
---

## Implementation Summary

Wrote two design docs and appended two BACKLOG rows. Every factual claim about existing code was verified by grep or by execution before being written, citing constructs rather than line numbers per the repo's rule. The single most consequential act was running a measurement: SP4's centerpiece claim (that a cross-module fix is refused at task-range validation) was **executed** in an isolated fixture rather than reasoned from source, with one case and two controls.

Commit: `0e4b420` — 3 files, 626 insertions, BACKLOG `+2 / -0`.

## Source Files Read

- `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-1-contracts-spikes.md` — the task's literal steps; confirmed Task 3 is the module's third `BACKLOG.md` writer and must enumerate ids at execution time.
- `spec.md` / `spec-distilled.md` — SP3/SP4 deliverable rows; both say design-doc-only. Located the `$127`/569k wording exactly (§3 and the §6 Spikes table).
- `deviations.md` — source of SP4's four real friction instances (`949d310`, the `0→9`/`0→17` rows, the Deferred Work table) and of the N76 collision record. Also confirmed the Task 3 ProcessNote's Check 9 short-circuit finding independently.
- `sdd-pre-dispatch-hook.sh` — manifest gating, context gate structure, Checks 4c/5c/5d, `type=fix` logging, task-range validation.
- `context-probe.py`, `transition-module.py`, `controller-checkpoint.py`, `sdd-stop-hook.sh`, `check-hooks.sh`, `~/.claude/bin/claude-usage-pace`.
- `2026-07-31-context-measurement-architecture-recommendation.md` (in full) — SP3 cites it by section rather than restating it, including where SP3's question differs from its §4.
- `2026-07-30-sp2-workspace-env-probe.md`, `2026-07-30-sp1-context-probe-attribution.md` — house style and the BACKLOG-row-block precedent.

## CLAUDE.md Files Read

- `CLAUDE.md` (repo root) — the only CLAUDE.md in the tree (`find . -name CLAUDE.md` → one hit). Shaped the docs directly: the **no-line-numbers / cite-the-construct** policy (and its parallel for counts — give the command, not the number), the "**`--help` is NOT a complete enumeration**" rule and the two-false-premise history, the five documented archive-aware lookups with "every other report glob stays intentionally flat", the `handoff-spawn.log` vs `context-observations.log` distinction (not conflated), and the runtime-facts-in-`references/` vs maintainer-facts-in-`CLAUDE.md` split.

## Claims Verified

### SP3 claims

1. **Gate is manifest-gated.** Read the block under `─── Require manifest mode (legacy non-manifest path removed) ───`: `if [ "$MANIFEST_MODE" = false ]; then … exit 0; fi`, reached before dispatch classification. Non-SDD sessions exit before any observation is written.
2. **Fires on the implementer new-task path only.** Quoted the actual construct, not the dispatch's paraphrase: the banner `─── Context-pressure gate (implementer new-task path only) ───`, then `if [ "$IS_IMPLEMENTER" = true ]` whose first branch is `if [ "$MARKED_FIX" = true ]; then ctx_observe_and_log other  # fix dispatch: log only, never gated`. It is a **nested branch, not a compound test** — the doc says so.
3. **Probe is stdlib-only and SDD-agnostic.** `grep -nE "^(import|from) "` → `argparse, json, os, sys, pathlib.Path, typing.Optional`. `grep -n "sdd\|manifest\|active-feature"` → zero artifact references. `resolve_transcript` implements `--transcript` → `--session-id` → `$CLAUDE_CODE_SESSION_ID`.
4. **`claude-usage-pace`.** Binary exists (`ls -l` → executable, 2026-07-02). Read `--help` and the module docstring; **did not execute it**, and the doc says so, labelled **a-help**. It reports subscription quota windows, and its own docstring states each run spawns a headless `claude -p "/usage"` turn.
5. **Stop-hook mechanics.** Read the whole script: reads only `.cwd`; exits 0 unless reports dir + deviations file + plan file exist; the in-file comment `# Use systemMessage for Stop hooks (hookSpecificOutput not supported for Stop events)`; header contract `Exit codes: 0 — Always (advisory injection, never blocks)`. Timing point (fires after the turn → observer, not guard) stated as the decisive property.
6. **`UserPromptSubmit`/`PreToolUse` payload.** Did **not** contradict the established "`PreToolUse` carries NO context data; only `statusLine` does". Whether `UserPromptSubmit` carries `transcript_path` is **explicitly labelled unverified** and routed to the contract-verification spike. `jq -r '.hooks | keys[]' ~/.claude/settings.json` → `PreToolUse, SessionStart, Stop, UserPromptSubmit` (already registered, carrying unrelated commands).
7. **Baseline.** `check-hooks.sh` pins a hardcoded `HOOKS=(…)` array of 7 paths — a new hook does **not** enter it automatically. Verified, not assumed.
8. **Negative result on the evidence.** `grep -rn --include='*.md' -e '\$127' .` → three hits, all spec/plan one-liners. No `569k` match anywhere. `grep -rhoE 'tokens=[0-9]{6,}'` across every reachable `context-observations.log` under `~/projects/claude-custom/` → **no ~569k row** (nearest: 539691, 621072). Recorded as an honest gap; no threshold rests on it.

### SP4 claims

9. **Archive + truncate.** `transition()` Step 3: `shutil.move` of `task-<NNN>-*` into `archive-<module>/`. Step 5: `shutil.copy2` then `open(dispatch_log, "w").close()  # truncate to empty`. Also rewrites `task_range`. `grep -n '^def '` confirms no inverse operation exists.
10. **The measurement — the claim that could have inverted SP4.** Built a throwaway git fixture with `task_range: [4, 8]` — never the live repo, so no live dispatch log was polluted. Ran the hook with `SUPERPOWERS_CTX_HANDOFF_BYPASS=1`:
    - **A (cross-module fix)** `[task 2 fix] …` → **exit 2**, `BLOCKED: Task 2 is outside the manifest's task_range [4, 8]`.
    - **B (positive control, in-range)** `[task 5 fix] …` → passes the range guard, refused later by `BLOCKED: No pre-execution audit report found` — i.e. it reaches the normal gate stack.
    - **C (control, plain implementer out of range)** → same range message.

    **Ordering proof, from data already captured:** the fixtures were identical except the task id, and the range check `exit 2`s immediately while the check stack accumulates into `ERRORS+=(…)` and prints them together. B emitted the pre-execution-audit error; A emitted **only** the range message. So A exited before the check stack — Checks 4b/4c/5c/5d were never reached. (Naming why this is evidence, rather than resting on "the output looked like that".)
11. **Bonus finding.** In case A the log ends carrying `DISPATCH fix task=2 type=fix` for a dispatch that never happened — **the dispatch log records fix *attempts*, not fix *dispatches*.**
12. **Check 9 does not constrain fixes.** `_check_verification_git_reality` opens `if not verification_ids: return []`; `_merged_dispatch_times` compiles `…type=implementer` only, with the docstring stating `type=fix`/`type=fix-unattributed` never open a window. **The dispatch's premise that Check 9 constrains fix dispatches is wrong**, and SP4 says so.
13. **N26.** Read the row: status **`done`** (2026-06-22, `7dc7812`). It is the change that *created* the `type=fix`/`type=fix-unattributed` rows. Described as such, not as an open item.
14. **Flat lookups.** `grep -n 'archive-'` over the hook → **one** hit, Check 5's `T0_GLOB` (N10). So Check 5c's checkpoint lookup and Check 5d's partner-review lookup are flat, consistent with CLAUDE.md's "exactly five archive-aware lookups".
15. **Quote anchors resolve.** Each quoted `deviations.md` phrase greps to exactly 1 hit (the `949d310` reason, the "rides the fix round" phrase, the "pollute context and bypass the review cycle" phrase). `grep -nE '\.(sh|py|md):[0-9]+'` over both docs → **none**.

### Id enumeration (against both branches)

```
git show main:docs/.../BACKLOG.md | grep -oE '\bN[0-9]+\b' | sort -t N -k2 -n -u | tail  → …N76 N77 N78
grep -oE '\bN[0-9]+\b' docs/.../BACKLOG.md | sort -t N -k2 -n -u | tail                 → …N74 N75 N79
{ both } | grep -oE '\bN[0-9]+\b' | sort -t N -k2 -n -u | tail                          → …N78 N79
```

Union max **N79** → **N80/N81** free on both. **Agrees with the controller's independent enumeration.** Worth recording: **N76–N78 appear free on this branch alone** — exactly the trap that produced the earlier N76 collision.

### Byte-identity — including a false alarm not to re-trip

The first check reported `N80: DIFFERS`. **The check was wrong, not the content.** SP3 contains **two** fenced blocks (an early hook snippet, then the row), so first-fence extraction is wrong by construction. Working command:

```bash
tac "$DOC" | awk '/^```$/{n++; next} n==1{print} n>=2{exit}' | tac > extracted
grep "^| N80 |" BACKLOG.md > appended
diff -u extracted appended
```

→ **BYTE-IDENTICAL** for both rows (N80 4021 bytes, N81 2717 bytes, 1 line each), re-run **after** the later SP4 body edits and still identical. A reviewer running a naive first-fence extraction will see DIFFERS; that is the extractor, not a divergence.

**Controller independently re-verified this** after the commit, using the same tail-anchored extractor: N80 4021 bytes, N81 2717 bytes, both BYTE-IDENTICAL.

### Pipe integrity (unescaped counts, computed with `(?<!\\)\|`)

| row | raw | escaped | unescaped | cols |
|---|---|---|---|---|
| header | 8 | 0 | **8** | 7 |
| N80 | 8 | 0 | **8** | 7 |
| N81 | 8 | 0 | **8** | 7 |
| N79 | 12 | 4 | **8** | 7 |
| N54 | 9 | 0 | 9 | 8 |
| N57 | 11 | 0 | 11 | 10 |

A naive `tr -cd '|'` shows N79 at 12 — that is 4 correctly-escaped `\|`, not corruption. **N54/N57 neither fixed nor worsened:** `git diff -U0 | grep -cE '^[+-]\| N5[47] '` → **0**; the whole BACKLOG diff is `2 0` (2 insertions, 0 deletions). Controller re-verified both against the commit.

**Suites:** `verify-symlink-install.sh` → **104 passed / 0 failed / 0 warnings, PASSED**. `validate-all-skills.py` not run — nothing under `skills/` was touched (staged numstat confirms 3 files).

## Deviations from Plan

- None on substance — implemented exactly as specified. One presentational choice: the BACKLOG row blocks use a **fenced** block rather than SP1's blockquote, because a `>` prefix makes byte-identity impossible. This satisfies the dispatch's byte-identity requirement.

## Self-Review Findings

- **Caught and fixed:** two line-number-style citations (`deviations.md` row 73/79) had slipped into SP4 — replaced with quoted grep anchors, each verified to resolve exactly once. This is the repo's own anti-rot rule, violated in the first draft.
- **Caught and corrected:** the first byte-identity extractor grabbed the wrong fence. Diagnosed the check rather than "fixing" the doc to match a broken check.
- **Caught:** the N79 12-pipe reading traced to escaped pipes before reporting it as corruption.
- **Walked both Step lists literally.** SP3: evidence / why-not-extend / three candidate homes / probe reuse / recommendation + rollout risk / row — all present. SP4: today's rule / friction / three candidates / enforcement interactions (4c, 5c, 5d, 9, N26) / recommendation / row — all present.

## Concerns

1. **The `$127`/569k evidence has no primary artifact — the most important item in this report.** It exists only as two spec one-liners. No `context-observations.log` anywhere reachable contains a ~569k row. Worse, if it came from `claude-ctx-check` or pre-SP1 `context-probe.py`, SP1 established such readings can be inflated ~2×. SP3 states this plainly, uses the figure only as motivation, and forbids deriving any threshold from it — but **the controller should know the spike's headline evidence is unverifiable as stated.**
2. **The dispatch's SP4 framing was partly wrong and was not followed.** It listed Check 9 among the enforcement interactions; Check 9 provably does not police ordinary fix dispatches. SP4 says so explicitly rather than repeating the premise. Flagged because the plan text carries the same framing.
3. **New finding, not fixed (out of scope):** the hook writes the `type=fix` dispatch-log row **before** the task-range refusal, so a refused cross-module fix leaves a row claiming a fix dispatch happened. Benign today (Check 9 ignores `type=fix`), but it is a real property of the tamper-evidence log. Described in SP4; **deliberately not fixed** — a hook change, outside the three-file write scope.
4. **N54/N57 remain corrupt by design.** Confirmed pre-existing and untouched (add/remove count 0). Left alone under the append-one-row-only discipline, per the standing unowned-deferral row.
5. **One scratch file retained, disclosed:** `/private/tmp/claude-501/…/scratchpad/sp4-range-experiment.sh` — the reproducer for claim 10. Outside the repo, in the session-scoped scratchpad, kept so a reviewer can re-run the measurement that could have inverted SP4.
6. **SP4's recommendation defers rather than enables.** Design B routes a carry-forward fix to a later task; it does not let one land now. The residual — a module-N defect blocking module N+1 immediately — is stated in the doc as explicitly unsolved rather than papered over.
