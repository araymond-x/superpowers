---
schema_version: 1
task_id: 16
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "skills/subagent-driven-development/references/context-handoff-protocol.md"
    description: "Rewrote step 4 + exit-code guidance for v2 surface topology and handshake states; added post-spawn /rename+/rc recipe, --session-label-vs-/rename note, inline-env guidance, env-knob defaults, mechanics-card section, hop-budget scoping, and the decline one-liner."
tests:
  written: 0
  passing: 0
  command: "python3 tests/ARaymond-skill-regression/validate-all-skills.py"
  result: PASS
contract_compliance:
  - constraint: "protocol content stays in references/, SKILL.md body does not grow"
    status: compliant
    detail: "Only the references/ doc was edited. SDD SKILL.md was NOT touched — its 'workspace' hits are git-worktree/SDD-workspace references (Step 5 archival, using-git-worktrees), not cmux spawn-topology claims."
  - constraint: "baselined hooks unchanged"
    status: compliant
    detail: "No hook files touched. Doc-only change."
  - constraint: "stage explicit paths, never git add -A"
    status: compliant
    detail: "Staged only the one doc path; committed with a quoted heredoc."
---

**Implementation Summary:**

Rewrote `context-handoff-protocol.md` to match the shipped v2 `spawn-handoff-session.sh`, preserving the numbered step-1–5 spine, bold-lead paragraphs, and the "failure that does not look like one" candor.

- **Step 4 / topology:** default successor is now a new **surface (top tab) in the caller's workspace**; `topology=workspace-fallback` (a new left-sidebar workspace) is described as the one-shot fallback only.
- **Exit 0:** requires a received wait-for token (`handshake=ok`); `--dry-run` also exits 0; `picker-manual` caveat kept in spirit (still needs the human; notify still doesn't name the mode).
- **Exit 3 causes** enumerated from the script: not-in-cmux, `reason=policy-off`, retryable `reason=policy-ask` (no hop; re-run `--user-approved`), `reason=stall` (raise `SUPERPOWERS_CMUX_MAX_STALL_HOPS` via inline env), hop ceiling, quota low, malformed hop counter, reservation-write-failed (two sites, silent), spawn-failed-after-reservation, and `handshake=timeout` with `diagnosis=` (trust-dialog/banner → go to the existing tab, never a fresh session).
- **Exit 1** unchanged + the N64 note: successful spawn self-commits `chore(sdd): record handoff hop N`; `--no-commit` means the successor's step-2 commit must fold those artifacts in.
- **New sections:** `/rename`+`/rc` recipe (script behavior + by-hand `cmux send`→`send-key enter`→verify, with exact verify strings `Session renamed to: <title>` and `/remote-control is active`); `--session-label` is telemetry vs `/rename` is phone-visible; `settings.local.json` not read by a running session → inline env; env-knob defaults (incl. SPAWN_WAIT_TIMEOUT Task-0 provenance, derived `max(6, 2×expected)` ceiling); mechanics-card section with the standalone regeneration command; per-feature hop-budget scoping (expected vs ceiling vs stall); the decline one-liner.

**Source Files Read:**
- `references/context-handoff-protocol.md` (the v1 file rewritten)
- `scripts/spawn-handoff-session.sh` (full ~971 lines — authoritative for exits, launch modes, handshake states, policy dial, env defaults, decline/notify wording, topology)
- `scripts/write-mechanics-card.py` (card contents, path `reports/handoff-mechanics.md`, regeneration command)
- `hooks/session-start` (successor side: `cmux wait-for -S sdd-hop-<id>` signal gated on `SUPERPOWERS_SPAWN_ID`)
- `docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md` (Decisions + section 5.7 doc-change list, for the WHY)
- `scripts/sdd-stop-hook.sh` (canonical decline one-liner)

**CLAUDE.md Files Read:**
Checked `skills/subagent-driven-development/` and its `references/` dir — no CLAUDE.md in either. The repo-root CLAUDE.md's "cmux Auto-Spawn Handoff" section is the maintainer-facing contract; per the task, runtime facts were kept in the doc, not cross-referenced to it.

**Deviations from Plan:**
None material. The plan's prose and the script agreed on every documented fact.

**Self-Review Findings:**
Verified each required fact against the script by grep:
- Exit-3 causes — all present: policy-off, policy-ask, cmux-unreachable, malformed hop counter, hop ceiling, stall, quota low, reservation-write HOPS_FILE + SPAWN_LOG, spawn-failed-after-reservation, handshake=timeout (line citations in the implementer's live report; re-verify at review).
- Env defaults — QUOTA_MIN_PCT=15, MAX_STALL_HOPS=1, TITLE_FORMAT=`hop{hop} SDD {feature}`, SPAWN_WAIT_TIMEOUT=60, POST_SPAWN=`rename,rc`, QUOTA_TIMEOUT=60, QUOTA_TOOL=`$HOME/.claude/bin/claude-usage-pace`, MAX_HOPS derived `max(6, 2×expected)` — all match.
- Decline one-liner — matches the stop hook's `printf '%s - decline bundle=%s reason=<word>\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" $BID >> ...`.
- No stale "new cmux workspace" default — the only workspace-topology mention is the `topology=workspace-fallback` case.
- `validate-all-skills.py` PASS (161 pass / 0 fail / 2 advisory word-count warnings).

**Concerns:**
- **`picker-manual` + handshake interaction (noted, not a defect):** in `picker-manual` mode the composed command drops `--non-interactive`, so the successor sits on the picker menu and will not signal the readiness token until a human finishes it — meaning that path can legitimately `handshake=timeout` (exit 3) if the human is slow. The doc documents both the launch=picker-manual exit-0 caveat and the handshake=timeout exit-3 branch faithfully to the script; the implementer did not attempt to reconcile the edge where they overlap, since the script's behavior is exactly as written and the task said the script wins. Flagged for awareness only.
- Status is DONE_WITH_CONCERNS solely due to that observability note; no plan/script contradiction was found and nothing was invented.
