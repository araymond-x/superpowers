# Final Holistic Code Review — cmux-spawn-v2 (2026-08-03, session 20)

Reviewer: general-purpose subagent (opus), read the full 1938-line production diff +
complete spawn-handoff-session.sh + support/model/hook deltas + Module-4 deviation rows;
ran the 3 key new suites (144 passed); syntax-checked all shell; empirically traced the
handoff_spawn YAML flow. Base `fa2d482`, Head = branch HEAD.

## Verdict: Ready to merge — YES (0 Critical, 0 Important, 3 Minor)

## Strengths (reviewer, verbatim summary)
- House rules honored: no `set -e`/`set -u`/pipefail (only explanatory comments), every
  `grep -q` is a here-string, empty-array `${FORWARDED[*]}`/`[@]` expansions are exactly
  why `set -u` must stay off.
- Reservation-before-spawn correct and both writes checked (`.handoff-hops` then intent,
  each guarded → exit 3 on failure) strictly before any target is created; `>` truncation
  hazard called out honestly rather than falsely claiming "no hop consumed".
- Double-spawn guard sound: `cmux send` rc 0 is the single point-of-no-return; workspace
  fallback only fires while `LAUNCH_ACCEPTED=0 && SPAWN_TOPOLOGY=surface`; readiness token
  is the ONLY exit-0 success signal.
- Command-forwarding injection-safe: bundle id charset-validated + `pwd -P` containment;
  `.active-feature` same lexical+realpath treatment; every forwarded arg/label/knob/pickup
  arg `shlex.quote`d; only unquoted interpolations are uuid4 + int (shell-safe); the
  `eval "v=\${$knob}"` loop iterates a hardcoded name list. No eval of untrusted data.
- Fail-direction discipline consistent: consent fails closed to `ask`; quota fails open
  (documented); Check-9 git-reality now fails closed (structural root fix).
- Dispositions match shipped code (spot-verified rows 338/339/345/348/355). No overclaim.

## Issues — all Minor

### Minor #1 — unquoted `handoff_spawn: off` fails validation instead of setting off policy
- plan.py:62 / materialize-manifest.py:118 / sdd_session.py Handoff.spawn_policy.
- PyYAML (1.1) coerces unquoted `off` → Python `False`; the Literal rejects it.
- **Controller adjudication: ACCEPTED + BACKLOG.** Verified by positive control: the PLAN
  GATE (validate-plan.py Pydantic Plan model) rejects unquoted `off` with a clear
  `handoff_spawn ... Got: False` error BEFORE materialize runs — so the reviewer's
  suggested materialize:118 coercion would NOT be reached; a proper fix spans plan.py +
  sdd_session.py + materialize + tests. Failure is LOUD and SAFE (never silently enables
  spawn); `handoff_spawn: "off"` works; AC 271 runtime (`reason=policy-off`) satisfied.
  Disproportionate to fix at the completion gate → deferred to BACKLOG.

### Minor #2 — sdd-stop-hook.sh interpolates `$BID` into `grep -qE` unescaped
- A bundle-id regex metachar could match the wrong log line (warning-only advisory path).
- **Controller adjudication: ACCEPTED + BACKLOG.** Bundle ids are timestamp-derived and
  rarely contain metachars; warning-only path, low risk. Fix = `grep -qF` or `printf %q`.
  NOTE: sdd-stop-hook.sh is a BASELINED hook — the fix must re-capture the hook baseline
  in the same change, so it is a deliberate separate change, deferred to BACKLOG.

### Minor #3 — write-mechanics-card.py regen line emits literal `$PYTHON` vs resolved sys.executable
- Already logged as Deferred (deviation row 348); reviewer concurs with severity/deferral.
  No new action.

## Recommendations (reviewer)
- Reviewer recommended taking fix #1; controller declined at the gate for the reasons
  above (multi-reader change, loud+safe current behavior) and filed it to BACKLOG instead.
- Live-behavior gap (real cmux/picker/installed-hook, phone-visible successor,
  diagnosis=trust-dialog/banner) remains stub/unit/e2e-only by design; spec §7 post-merge
  live-hook smoke check is the right owner (row 355).

## Assessment
Ready to merge: YES. Spawn/reservation/fallback state machine correct, exit ladder
coherent, forwarding injection-safe, deviations ledger honestly matches shipped code. The
3 Minor items have safe (loud, non-silent) failure directions; none blocks merge.
