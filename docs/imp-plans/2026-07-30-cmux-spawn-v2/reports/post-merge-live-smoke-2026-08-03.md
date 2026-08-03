# Post-Merge Live-Hook Smoke Check — cmux-spawn-v2 (2026-08-03, spec §8 "Live smoke")

Run immediately after merging cmux-spawn-v2 to local main (`7f5c1a9`). The installed
hooks/skill path resolve to the MAIN checkout, so this is the first proof against the
real installed code (worktree coverage was never final proof).

## Preconditions (all verified)
- `~/.claude/skills/superpowers` → `/Users/araymond/projects/claude-custom/superpowers/skills` (main checkout).
- Installed `spawn-handoff-session.sh` is **byte-identical to merged main** (sha256 unique count = 1) and carries the v2 surface-topology code.
- cmux reachable: `cmux 0.64.20 (100) [14e3400b9]`, `cmux ping` → `PONG`.

## Dry-run smoke (installed script + LIVE cmux) — PASS
`spawn-handoff-session.sh 2026-08-03T19-54-05Z-cmux-spawn-v2 --dry-run`, run from the
feature worktree, exit 0. Real (not stubbed) outputs:
- `quota=ok:76.0` — LIVE quota read via `claude-usage-pace`.
- `launch=auto`; `forwarded= label=[...] telemetry=on`.
- Composed successor command emitted correctly: `claude-picker --non-interactive --pick-version 2.1.220 --telemetry on --session-label ... '/pickup <bundle>'` with the `runtime-picker-failure` fallback interpolated (parent spawn-uuid + hop=2 baked into the fallback log-append).
- `--dry-run: would spawn surface in <workspace-uuid> (workspace fallback armed) — quota=ok:76.0 launch=auto policy=auto tasks_done=19` — surface-topology primary decision + `tasks_done=19` counted from the completed reports.
- `--dry-run: no hop increment, no spawn` — dry-run safety honored.

This exercises, against the merged installed code + live cmux: reachability, live quota,
bundle validation, hop/stall/tasks_done accounting, surface-vs-workspace topology
decision, and the composed successor command.

## Deferred (by the spec's own framing)
The full **real surface spawn** ("one real surface spawn into a throwaway workspace") is
deferred to **the next real SDD run**, which spec §8 explicitly names as the acceptance
test. Force-spawning a real successor of THIS (completed) bundle would launch a pointless
session picking up a done feature; the dry-run + live cmux + live quota is honest proof of
the mechanism. The two live-only ACs (plan.md 266 phone-app visibility, 272 live
`diagnosis=trust-dialog`/banner branches) remain checked-with-caveat until that run.

## Verdict
Installed merged code + live cmux integration confirmed working end-to-end (dry-run).
No regressions. The feature is live in the main checkout.
