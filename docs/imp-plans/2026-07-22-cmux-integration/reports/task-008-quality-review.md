# Task 8 — Adversarial Quality Review

**Verdict: PASS-with-fixes** — one surviving mutation found on the green 625-test suite.

---

**Reviewed:** `80a118e..7a46dae` (4 files: `spawn-handoff-session.sh` +41, `test_spawn_handoff.py`
+241/−17, `conftest.py` +28/−2, `module-1-spawn-script.md` +34/−20).
**Suite at HEAD:** `tests/unit/` **625 passed** (72 in `test_spawn_handoff.py`), verified by my own
run. `scripts/lint-shell.sh --all` reports nothing for this script.

## Strengths

The reservation hardening is correct and minimal — no new exit code, `print_manual_instructions`
before `exit 3` on both branches. Leg B's isolating fixture (`handoff-spawn.log` pre-created as a
*directory* → EISDIR) is genuinely clever and mutation-solid. The version-as-directory test ships a
real positive control. The fractional-threshold pair correctly adds a behavioral leg (13.0% vs a 12.5
threshold) rather than relying on an absence assertion. The report's self-caught hollow assertion and
its refusal to overclaim `max(0, …)` (Concern #4) are both accurate. `conftest.py` merged rather than
replaced the `MODELS_DIR` insert.

## Issues

### Important

**1. `tests/unit/test_spawn_handoff.py:1131` — leg A pins that the hops guard *detects*, never that it *stops*. Surviving mutation confirmed.**

Mutation **MX1**: replace the `exit 3` in the `.handoff-hops` guard
(`spawn-handoff-session.sh:450`) with `:` — guard still warns and prints manual instructions, but
falls through.
Observed: **`72 passed`** on the whole file. Nothing went red.

The fixture (`os.chmod(ctx["reports"], 0o555)`) fails *both* reservation writes, so control flow
never has to leave the block for the assertions to hold: `rc==3` and `"new-workspace" not in
cmux.log` are both satisfied by the *intent* guard downstream. Anchoring on `"cannot record hop"`
fixed message attribution — it does not fix the conjunction trap, it just moved it up a level. This
is the same class the implementer self-caught, one layer deeper.

The mutant is not merely under-tested, it is *wrong*, and I proved the reachable scenario. Probe
appended to `test_spawn_handoff.py` (same file, so the conftest fixture applies — the Task-7 lesson),
fixture = `.handoff-hops` pre-created as a **directory** (hops write fails EISDIR, log write
succeeds):

- **on the MX1 mutant:** `rc=0 spawned=True` — a workspace is spawned with **no hop recorded**, while
  stderr says "manual fallback" and stdout prints the manual-resume instructions. Worse than silent:
  the operator is told to resume manually while a successor is already running. That is a live
  double-spawn path and the exact Decision-21 hole Step 1 exists to close.
- **positive control, unmutated script, identical fixture:** `rc=3 spawned=False`.

**Fix (test-only — compatible with the "script freezes after this task" constraint):** swap leg A's
fixture to the isolating one and adjust the one assertion it breaks.

```python
(ctx["reports"] / ".handoff-hops").mkdir()   # only the hops write fails
r = run_spawn(ctx, tmp_path, "b1", env_extra=env)
assert r.returncode == 3
assert _reservation_warning_lines(r, "cannot record hop")
assert "new-workspace" not in _cmux_log_text(tmp_path)
assert not (ctx["reports"] / ".handoff-hops").is_file()   # was .exists()
assert "Manual resume required" in r.stdout
```

Drop the `chmod`/`try`/`finally`. This also retires implementer Concern #5's root-dependence for leg
A (EISDIR binds root too) and mirrors leg B's technique. I verified this fixture discriminates in
both directions above; re-run MX1 after the change to confirm RED.

### Minor

**2. `spawn-handoff-session.sh:265-267` — the `ARGS_OK=0` degrade now emits no reason at all.**
Implementer Concern #2 is a real, if small, operability regression. `DECODE_TMP="$(mktemp)"` (`:221`)
is unchecked; an empty path made `open("", "wb")` raise, which previously printed a traceback naming
the cause. The new `try` swallows it into `sys.exit(5)`, so an mktemp failure (or any decode failure)
now degrades to `picker-manual` with *no* diagnostic — the operator sees only `launch=picker-manual`.
One line closes it and simultaneously gives the surrogate test a real discriminator instead of
`"Traceback" not in stderr` (Concern #3):

```bash
if [ $? -ne 0 ]; then
  echo "[spawn-handoff] warn: forwarded-args decode failed — degrading to picker-manual" >&2
  ARGS_OK=0
```

**3. `spawn-handoff-session.sh:448` — "no hop consumed" is not accurate in every failure mode of that
write.** `>` truncates at open. On a permission failure (the tested case) the file is untouched and
the wording is right; on a *partial* failure (ENOSPC, quota) the file is already truncated to zero,
so the next run reads empty → `HOPS=0` → the whole hop chain silently resets. The message would then
claim less damage than occurred. Not introduced by this change (the unchecked write truncated too),
but Step 1 asked for branch-accurate wording. Suggest "hop not recorded (counter may have been
truncated)" or writing via a temp+`mv`. **`[NEEDS_CONTEXT]`** on severity: confirm/dismiss by
deciding whether ENOSPC is in scope for a script that already fails open on quota.

**4. `cmux notify` asymmetry — verdict: defensible to omit, but ratify it rather than leaving it
open.** Three of the four reachable `exit 3` branches notify (hop-limit `:117`, quota-low `:192`,
spawn-failed `:474`); the not-in-cmux branch can't. The two new ones don't. My judgment: the notified
branches are *routine, expected* stops a human may want pushed to them; a reservation-write failure
is a broken-filesystem condition the agent relays via exit 3 + printed instructions, and the plan
text was explicit. But the inconsistency is one line and a user who sees a notification for "quota
low" and nothing for "your reports dir is unwritable" has no way to infer the difference. Recommend
adding the notify for consistency, or recording the omission as a deliberate rule in Task 11's docs —
not both silences.

**5. `module-1-spawn-script.md:1097+` — the Task 6 Step 2 snippet is now stale against the shipped
script.** Step 5 correctly fixed the three named defects, but the same snippet still shows the
*unchecked* `printf '%s\n' "$SP_HOP" > "$HOPS_FILE"` reservation pair that Task 8 just replaced. Out
of the task's literal scope; worth a one-line "hardened in Task 8 Step 1" annotation so the doc
doesn't reacquire the exact divergence class Step 5 was cleaning up.

**6. Minor test duplication.** `_cmux_log_text` and `_notify_line` both read `tmp_path / "cmux.log"`
with different existence semantics; `_notify_line` could be expressed over `_cmux_log_text`.
Cosmetic. Otherwise the three new helpers have clear docstring contracts, and
`_reservation_warning_lines`' docstring correctly names *why* it is prefix-anchored.

## Verified clean (independent checks, not re-runs of the spec review)

- **Contract constraint, exit ladder, traced end-to-end.** `grep -nE '(^|[^_a-z.])exit [0-9]+' | grep
  -v sys.exit` → `3× exit 0`, `8× exit 1`, `8× exit 3`, and one `exit 4` **inside a comment** at
  `:242`. No fourth code. Both new branches route to the existing 3 after `print_manual_instructions`.
- **`sys.exit(5)` cannot surface.** Confirmed independently: the heredoc's status is consumed at
  `:265` by `if [ $? -ne 0 ]; then ARGS_OK=0`, whose only effect is the `preflight_ok` degrade.
  Decoder-internal, as the spec review said.
- **Step 4d blast radius — reasoning is sound, not just non-erroring.** `grep -rn` over all of
  `tests/` finds no other reference to the five vars, and `grep -rn CLAUDE_CODE_ENABLE_TELEMETRY
  skills/ hooks/` finds exactly one consumer: `spawn-handoff-session.sh:296`. No test reads them,
  sets them, or shells into anything that does. `delenv(raising=False)` for 616 unrelated tests is
  strictly hermeticity-improving. Full suite 625 green confirms it.
- **`max(0, …)` claim is accurate as stated** (deterministic truncation, not a 255 ceiling), and the
  test pins the right property (no fragment of the old base leaks).
- Lint vacuity, Step 5 doc-vs-`7131698` fidelity, and the single `PICKER_ENV_VARS` definition —
  already established by the spec review; I did not re-derive them.

## Mutations run (all restored; `git diff --name-only skills/ tests/` = 0 files)

| # | Mutation | Target test | Result |
|---|---|---|---|
| **MX1** | hops guard's `exit 3` → `:` (warn, don't stop) | full file | **SURVIVED — 72 passed** |
| MX1-probe | as above, `.handoff-hops` as dir | ad-hoc probe | mutant `rc=0 spawned=True`; control `rc=3 spawned=False` |
| MX2 | intent guard's `exit 3` → `:` | `-k write_failure` | RED (`test_intent_write_failure…`) |
| M3 | delete failure-branch `cmux notify` (`:474`) | `-k spawn_failure_keeps_hop` | RED |
| M4 | delete the uncaptured `else` arm in `spawn_claude_workspace` | `-k mktemp_failure_still_spawns` | RED |
| M5 | `rc=$?` → `rc=0` in that arm | `-k mktemp_failure_preserves` | RED |
| M8 | `except Exception: sys.exit(5)` → `pass` | `-k lone_surrogate` | RED |
| M9 | `max(0, 255-len)` → `abs(255-len)` (the real footgun shape) | `-k label_slice` | RED |

## Assessment

**PASS-with-fixes.** **Yes — I found one surviving mutation on the green 625-test suite**: the
`.handoff-hops` reservation guard can be reduced from "stop" to "warn and continue" with the entire
suite still green, and the resulting behavior spawns a successor against a reservation that never
landed while telling the operator to resume manually. The shipped script is correct; the test is
hollow. Finding 1 is a required test-only fix (no script edit, freeze-compatible). Findings 2–4 are
one-line judgment calls the controller should resolve rather than carry forward as open deviations;
5–6 are documentation/cosmetic.

---

## Controller verification (MX1 independently reproduced)

The load-bearing finding was re-run by the controller before dispatching any fix, with a positive
control that the mutation actually took effect:

```
$ cp spawn-handoff-session.sh /tmp/spawn-pristine.sh          # copy-restore, NOT git stash
$ sed -i '' '450s/^  exit 3$/  :/' spawn-handoff-session.sh
$ sed -n '447,452p' spawn-handoff-session.sh                  # positive control: edit took
  if ! printf '%s\n' "$SP_HOP" > "$HOPS_FILE"; then
    echo "[spawn-handoff] reservation write failed: cannot record hop … " >&2
    print_manual_instructions
    :                                                          # <-- exit 3 removed
  fi
$ .venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q
  72 passed in 64.57s
$ cp /tmp/spawn-pristine.sh spawn-handoff-session.sh
$ git diff --name-only <script>                                # EMPTY
```

**CONFIRMED.** 72/72 green with the hops guard reduced to warn-and-continue. Finding 1 is real and
required. The structural cause is exactly as described: the `chmod 0555` fixture fails both writes,
so the downstream intent guard supplies the `rc==3` and the absent `new-workspace` that leg A's
assertions read, while the hops `echo` — which is *not* what was mutated — still satisfies the
warning assertion.

**Controller dispositions of findings 2–6** (dispatched as `[task 8 fix]`):
- **F1 — FIX (required).** Test-only isolating fixture as prescribed; must be mutation-proven RED
  under MX1.
- **F2 — FIX.** In scope: the missing diagnostic is a regression *introduced by this task's own*
  `try`-wrap (Step 4), and the script freezes after this task, so it is now or never. Must be
  mutation-proven and audited for test-echo collision, since it adds a new stderr line.
- **F3 — FIX (wording only).** Step 1 explicitly asked for branch-accurate wording; "no hop consumed"
  overclaims under a partial/ENOSPC write. Soften to state only what is known. No behavior change.
- **F4 — RATIFY THE OMISSION, do not add the notify.** The plan text prescribes exactly "warn, print
  manual instructions, exit 3"; the implementer correctly declined unrequested scope, and adding a
  notify to a freezing script risks perturbing existing `cmux.log` assertions for a consistency gain.
  Per "disposition ≠ done", the reviewer's alternative is taken instead and given a **plan checkbox**
  in Task 11 (document the rule: reservation-write failures exit 3 silently by design).
- **F5 — FIX.** One-line annotation in the same doc Step 5 already edits.
- **F6 — DECLINED.** Cosmetic helper dedup on a test file that is about to freeze; not worth the
  churn or the regression surface.

---

# Round 2 — Quality Re-Review after the fix round (verdict: PASS)

**Scope:** `7a46dae..53318b5` (3 files: `spawn-handoff-session.sh` +15/−1, `test_spawn_handoff.py`
+55/−19 incl. formatter reflow, `module-1-spawn-script.md` +4). F4 and F6 treated as dispositioned;
not re-raised.

## Strengths

The MX1 fix is the right one and is implemented better than my sketch. Both new script edits are
comment-heavy in the way this file has earned — the hops-guard comment now records *why* it declines
to claim "no hop consumed" (`>` truncates at open), and the decode-echo comment records both the
placement constraint and the deliberate avoidance of the `launch=picker-manual` literal. Each of
those is a note that would otherwise be re-litigated by the next reader. `_decode_warning_lines`
follows the established prefix-anchored-on-stderr idiom rather than inventing a fourth extractor
shape. The `module-1-spawn-script.md` annotation sits inside the fence, so a reader copying the
snippet cannot miss it.

## Verification performed

**1. MX1 is closed.** Located the guard by content (`grep -n "cannot record hop"` → `:462`), mutated
`:464` `exit 3` → `:` (warn and continue), and confirmed the edit landed by printing the mutated
block before running. Result: **`1 failed, 71 passed`** —
`test_hops_write_failure_exits_3_without_spawning`, `tests/unit/test_spawn_handoff.py:1166`
(`assert r.returncode == 3` → `assert 0 == 3`). Matches the controller's independent run exactly.
Restored; `diff -q` byte-identical.

**2. The new leg A fixture does not hide a deeper substitution.** I asked the question that produced
the round-1 finding and answered it empirically, with a probe that dumps the full stderr for the leg
A fixture at HEAD:

```
[spawn-handoff] quota=ok:63.0
[spawn-handoff] forwarded=… label=[Proj-Session-3] telemetry=on
[spawn-handoff] launch=auto
[spawn-handoff] successor command: …
…/spawn-handoff-session.sh: line 457: …/.handoff-hops: Is a directory
[spawn-handoff] reservation write failed: cannot record hop in … — manual fallback.
rc=3   LOGEXISTS=False
```

This settles every candidate alternative cause: quota passed (`ok:63.0`, not the stopper), the
hop-limit gate passed (`cat` of a directory → empty → `HOPS=0`, and `SP_HOP=1` reached composition),
and **`launch=auto`** proves all five preflight predicates held, so the clean-tree, bundle,
cmux-reachability and version checks all passed. The only failing write is the hops write (EISDIR at
`:457`), and the only exit path taken is the reservation guard's. The bash `Is a directory`
diagnostic on stderr is exactly the noise `_reservation_warning_lines`' prefix anchor exists to
reject, and it does.

**3. Leg A and leg B are now independently pinned.** MX1 (hops guard `exit 3` → `:`) → **only** leg A
red. MX2 (intent guard `exit 3` → `:`, `:469`) → `1 failed, 1 passed` under `-k write_failure`, i.e.
**only** leg B red, leg A green. Neither leg can stand in for the other in either direction.

**4. The assertion substitution is stronger, not weaker.** My sketched
`assert not (…/".handoff-hops").is_file()` is dead under a directory fixture — the path can never
become a regular file, so the assertion is a tautology that would survive any mutation. Dropping it
was correct. `assert "intent" not in _spawn_log_text(ctx)` asserts a real state property (nothing was
reserved at all), it is false under MX1 (round 1's probe showed the mutant reaching
`rc=0 spawned=True`, which requires the intent write to have landed), and it mirrors leg B's
`.handoff-hops == "1"` so the two legs now have symmetric distinguishing signatures. One honest
caveat, not a defect: `_spawn_log_text` returns `""` when the file is absent, so this assertion alone
would also pass if the script never reached the reservation block. It is the paired
`_reservation_warning_lines(r, "cannot record hop")` assertion that proves the guard was reached, and
probe 2 above confirms it. The pair is sound; neither half is sufficient alone.

**5. Decode-diagnostic collision audit — implementer's conclusion confirmed, in all three directions.**
- *Forward:* all nine `picker-manual` assertions in the file use the literal `"launch=picker-manual"`.
  That literal appears in the script exactly once outside the new line's own comment — in
  `echo "[spawn-handoff] launch=$LAUNCH_MODE"`. The new diagnostic says
  `degrading to picker-manual (forwarded args dropped)`, which cannot satisfy any of them.
- *Reverse:* the `_decode_warning_lines` prefix occurs exactly once in the script (`grep -c` → 1), so
  nothing else can satisfy the new assertion.
- *Absence-style:* the only two negative stderr assertions in the file are
  `not _warning_lines(r, "MIN_PCT")` (anchored on `WARNING: invalid SUPERPOWERS_CMUX_QUOTA_`) and
  `"Traceback" not in r.stderr`. The new line matches neither prefix and contains no traceback text.

**6. Echo placement is load-bearing, proven not asserted.** Mutation **MX-P**: moved the echo from
inside the branch to the line immediately *above* `if [ $? -ne 0 ]`. Result: `2 failed` —
`test_corrupt_v1_body_degrades_to_picker_manual` and
`test_lone_surrogate_arg_degrades_without_traceback`. `[ … ]` then reads the echo's status (0),
`ARGS_OK` stays 1, and a decode failure silently proceeds with empty forwarded args on `launch=auto`
— a silent arg-drop, the exact failure the comment warns about. The implementer's note is empirically
correct.

**7. No regression, no scope drift.** Full `tests/unit/` → **625 passed** (my own run). Shell exit
statements remain **0 / 1 / 3** only: the raw `grep` count for `exit 3` rose 8→9 between commits, but
the added match is inside the new decoder comment (`exit 3/4/5`) at `:269` — actual `exit 3`
statements are unchanged at `:125 :137 :195 :464 :469 :491`. The fix diff touches zero lines of
`sdd-pre-dispatch-hook.sh`, `tests/ARaymond-hook-baseline/baseline.txt`,
`tests/unit/spawn_handoff_helpers.py`, or `tests/unit/conftest.py`. Working tree left clean:
`git diff --name-only skills/ tests/` = 0 files after every mutation (copy-restore throughout; no
`git stash`).

I also confirmed the F4 disposition is real rather than asserted: Task 11 Step 1b now exists in
`module-2-protocol-e2e-docs.md` as an unchecked box that names the asymmetry and the reason, which is
the alternative I proposed.

## Issues

**Critical:** none. **Important:** none. **Minor:** none.

This is a clean round. The one caveat worth carrying (leg A's `"intent" not in …` is trivially true
when the log file is absent, and depends on its paired warning assertion for meaning) is a property
of a sound two-assertion pair, not a defect, and I am recording it as an observation rather than
manufacturing it into a finding.

## Mutations run this round

| # | Mutation | Observed |
|---|---|---|
| MX1-r2 | hops guard `exit 3` → `:` (`:464`) | **RED** — 1 failed / 71 passed, leg A only (`assert 0 == 3`) |
| MX2-r2 | intent guard `exit 3` → `:` (`:469`) | **RED** — leg B only; leg A green (independence) |
| MX-P | decode echo moved above `if [ $? -ne 0 ]` | **RED** — 2 failed (`corrupt_v1`, `lone_surrogate`) |
| probe | leg A fixture, full stderr dump at HEAD | `launch=auto`, `quota=ok:63.0`, EISDIR at `:457`, rc 3, log never created |

## Assessment

**PASS.** MX1 is genuinely closed — I reproduced the controller's result independently and confirmed
the fix works because the fixture now isolates the first write, not because a downstream guard is
standing in. Leg A and leg B are each RED only under their own mutation. **I found no new surviving
mutation.** Suite 625 green, exit ladder still 0/3/1, hook/baseline/helpers/conftest untouched.
