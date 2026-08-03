# Task 17 — e2e Step 14 rewrite: Adversarial Quality Review

Every claim below is grounded in a mutation actually run (apply → `bash tests/integration/sdd-e2e-test.sh` → observe → restore from backup, verifying `git diff --quiet fd672ed` after each). The file was confirmed pristine at the end.

## Strengths

The load-bearing success-path assertions are **genuine discriminators**, not vacuous greps:

- **M1** — broke the `/rc` read-screen anchor (`/remote-control is active` → garbage): RED at line 801 (`post_spawn=partial:rc`). **M2** — broke the `/rename` anchor: RED at 801 (`post_spawn=partial:rename`). `handshake=ok` itself comes from `wait-for` (not read-screen), so the `case … *post_spawn=partial*` companion check (line 801) is what makes the read-screen content load-bearing — and it is genuinely load-bearing.
- **M3** — `new-surface` stdout `surface:7`→`surface:8`: RED at line 772. Captured-ref plumbing pinned.
- **M4** — `wait-for) exit 0`→`exit 1`: RED at line 760. Handshake is real.
- **M7** — uninstalled picker version (fixture degrades to picker-manual): RED at line 764 (`expected launch=auto`). `launch=auto` fails loudly rather than passing hollow; asserting it first is correct.
- **M9** — policy sub-run set to `off` instead of `ask` (rc 3 but a different reason): RED at line 828. Discriminates policy-ask from a spurious rc-3-for-another-reason.
- **M11b** — over-expected sub-run with report DONE→BLOCKED (tasks_done stays 0 → stall fires): RED at line 864 (`reason=stall`). Proves the committed DONE report is load-bearing and a stall refusal cannot satisfy the over-expected assertion. **M6** (expected_hops 1→5, advisory suppressed) independently RED at line 866.
- Exactly-one `wait-for` is real (instrumented counts: new-surface 1, rename-tab 1, send 3, send-key 2, read-screen 2, wait-for 1, notify 1).
- Self-satisfying-grep trap honored: composed-command greps (782, 787) and send-line grep (776) anchor on `successor command:` / `export SUPERPOWERS_SPAWN_ID=`. Label-increment pin (`Proj-Session-3`) specific.
- House style correct: expected-nonzero sub-runs run to assertions without the file's `set -e`/ERR trap aborting; `( … ) || SPAWN_RC=$?` + `grep -c … || true` guards work.
- Fixture integrity: `.sdd-session.json` produced by real `materialize-manifest.py`, not hand-forged. No leftover `new-workspace` assertion.

## Issues

### Important
1. **The workspace-fallback topology has ZERO e2e coverage, and two stub verbs + a "load-bearing" comment create false confidence that it doesn't.** (`tests/integration/sdd-e2e-test.sh:705–710`)
   - **Mutation M8**: replaced the entire `list-pane-surfaces)` case arm with a disabled label. Suite stayed **GREEN**. Verb-count instrumentation confirms `workspace`(create) and `list-pane-surfaces` are **never invoked** in any of the three sub-runs — all take the surface topology, so `create_workspace_target` never runs.
   - The stub comment at 706–709 states the `* ` marker "is load-bearing … what let the old field-position parser pass while failing 100% in production." True in production and the unit suite — but **this e2e never parses it**, so the comment overstates what Step 14 proves.
   - Not Critical/merge-blocking: the stub verbs are legitimate test-double fidelity mirroring `_CMUX_V2_STUB`; the fallback path IS covered by the unit suite (`CMUX_LIST_SURFACES_NO_REF`/`_TWO_ROWS` knobs). Task 17's plan scoped Step 14 to success + policy + over-expected. Coverage gap + locally-misleading comment, not misleading production logic. **Suggested fix (cheap):** trim the two dead verbs' bodies to a bare `echo OK` and/or amend the comment to note the fallback topology is exercised in the unit suite, not here.

### Minor
2. **`--focus false` (line 770) and `--working-directory` are matched against the whole `cmux.log`, not anchored to the `new-surface` line.** Only `new-surface` emits `--focus false` in the current path, so it passes, but the assertion doesn't pin the flag to the verb. Tighten to `grep -q "new-surface .*--focus false"` if you want it airtight.
3. **The "exactly one `wait-for`" assertion (793) is partly shadowed by the `rc==0` check (760).** The likely regression (a wait that fails → doubles the count and flips rc to 3) is caught at 760 first. Still adds value for a hypothetical double-wait-on-success regression — not dead, just narrower than it looks.

### Report accuracy
- `tests.written: 19 / passing: 19` vs 22 `"FAIL"`-guard statements — honest ballpark, not wildly off. No undisclosed deviations: diff matches the DONE report; status "no deviations/concerns" accurate.

## Assessment

**Ready-with-fixes** (leaning ready-to-merge). Every success-, policy-, and over-expected-path assertion is a proven discriminator — no surviving mutations on the paths the three sub-runs actually exercise. The one substantive issue (Important #1) is a coverage gap for the workspace-fallback topology plus a comment that overstates local coverage; it's covered by the unit suite and within Task 17's scope, so it does not block on its own. Recommend correcting the `list-pane-surfaces` marker comment before merge.

_(Quality reviewer: opus model, adversarial mutation testing. Saved verbatim by controller.)_
