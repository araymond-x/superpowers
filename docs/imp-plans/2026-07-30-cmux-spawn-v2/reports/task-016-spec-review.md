# Task 16 Spec Review — context-handoff-protocol.md rewrite

**Verdict (round 1):** PASS on all 10 enumerated factual checks against the shipped script; one recommended reword (internal contradiction on the exit-0 picker-manual note) surfaced and routed to a `[task 16 fix]`.

## Spec coverage
All Step-1 and Step-2 required items PRESENT (verified line-by-line):
- Surface default topology + `topology=workspace-fallback` (doc 62–74); exit-0 = spawned AND `handshake=ok` (77–84); all 11 exit-3 causes (88–114); exit-1 + N64 self-commit note (119–132).
- Step 2 sections: `/rename`+`/rc` recipe (148–169); `--session-label` telemetry vs `/rename` phone name (171–174); `settings.local.json` not read by running session (176–180); env knobs w/ defaults incl. SPAWN_WAIT_TIMEOUT provenance + derived MAX_HOPS ceiling (182–207); mechanics card = `reports/handoff-mechanics.md` + regen command (209–224); hop-budget scoping (54–60); decline one-liner (226–232).

## Factual accuracy vs shipped script — all CONFIRMED
1. Exit ladder: all 11 exit-3 sites (script 212/216/223/247/313/334/398/791/796/839/879) map to doc causes; two reservation sites correctly folded "two sites, one cause"; exit-1 set matches.
2. Tokens: `reason=policy-off/policy-ask/stall`, `handshake=ok/timeout`, `diagnosis={trust-dialog,banner,picker-error,unreadable,none}`, `topology=workspace-fallback`, `launch=auto|picker-manual`, `budget=over-expected` — all appear in the script exactly.
3. Env defaults: MAX_HOPS derived `max(6, 2×expected)`, fallback 6, override absolute, 0 valid; MAX_STALL_HOPS=1; SPAWN_WAIT_TIMEOUT=60 + Task-0 8–11s provenance; POST_SPAWN=`rename,rc`, empty disables, /rc-last; TITLE_FORMAT=`hop{hop} SDD {feature}`; QUOTA_MIN_PCT=15; QUOTA_TIMEOUT=60; QUOTA_TOOL=`$HOME/.claude/bin/claude-usage-pace` override authoritative→`unchecked`. Every default matches.
4. Decline one-liner byte-identical to `sdd-stop-hook.sh` printf (format + field order).
5. Topology default = `cmux new-surface` (top tab); `cmux workspace create` is the one-shot fallback; no stale "new cmux workspace" default; no `new-workspace` reference.
6. `/rename`+`/rc` verify anchors (`Session renamed to: <title>`, `/remote-control is active`) + POST_SPAWN default match.
7. N64 commit message `chore(sdd): record handoff hop N` matches script.
8. Mechanics card path `reports/handoff-mechanics.md` + standalone regen command match write-mechanics-card.py.
9. validate-all-skills.py: `PASS: 161  FAIL: 0  WARNING: 2` (advisory word-count only). Cross-refs valid.
10. SKILL.md untouched (`git show 58f872c --stat` = 1 file). Independent `grep -n workspace SKILL.md` = 4 hits, all git-worktree/SDD-artifact refs, none cmux-spawn-topology. Implementer's claim correct.

## Recommended reword (routed to [task 16 fix])
Exit-0 `picker-manual` note said the user "must go finish the picker … or the successor never starts" — contradicts the exit-0 precondition (`handshake=ok`). Verified against control flow: `wait_for_token` gates exit 0 unconditionally (no launch-mode branch); the readiness token is emitted by the child's session-start hook only after the child boots, which in picker-manual mode requires the human to have already finished the picker. So exit-0 + picker-manual ⟹ picker completed. The genuine unfinished-picker case is exit-3 `handshake=timeout` (already handled correctly). Fix: scope the "go finish the picker" imperative to the exit-3 branch; reword exit-0 picker-manual to note `handshake=ok` already confirms boot.

Controller note: independently re-derived the control flow from spawn-handoff-session.sh lines 803–970 and confirmed the reviewer's reasoning; the conflicting CLAUDE.md "picker-manual exits 0 while a human must still finish" gotcha describes pre-handshake v1 behavior, superseded by v2's unconditional handshake gate.

## Round 2 (re-review after [task 16 fix] 630b7ab) — PASS
The exit-0 picker-manual reword closes the finding: no longer claims "the successor never starts"; correctly states exit-0 ⟹ `handshake=ok` ⟹ picker completed + child booted; routes the unfinished-picker case to exit-3 `handshake=timeout` (where the script actually surfaces it, lines 845–879). Residual-tension check on the unchanged mode-definition line above the bullet: ACCEPTABLE (a general mode-definition precondition followed by "and at exit 0 that precondition is satisfied" is logically consistent — the removed defect was the imperative asserting completion had NOT happened at exit 0). validate-all-skills.py still `PASS: 161 FAIL: 0 WARNING: 2`. All 10 factual checks remain CONFIRMED (fix touched only exit-0 prose; 1 file, 6 ins/3 del). **Spec review PASS.**
