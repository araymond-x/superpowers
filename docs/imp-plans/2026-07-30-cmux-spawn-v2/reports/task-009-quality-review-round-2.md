# Task 9 — Adversarial Code Quality Review, Round 2 (fix-delta only)

**Scope:** commit `f76e047` (`git diff HEAD~1 HEAD`) only. Task 9's substance is not re-reviewed.

## Method

Baseline re-measured, not inherited: the three spawn files **143 passed in 144.95s**
(and again **143 / 144.26s** on the accidental clean run below — see M3-anchor). The
full unit suite was NOT re-run; this review makes no claim about the 777 figure, and
the delta arithmetic (139 + 5 new − 1 merged = 143) is confirmed at the file level.

Discipline: every anchor asserted to match **exactly once** before replacement (a
Python harness, no `perl`, so no `$`-interpolation accidents); the unified diff printed
and READ every run; restore by **byte copy** with `bytes_identical=True` verified;
never `git checkout --`, never `git stash`; `__pycache__` cleared before every run;
`-p no:cacheprovider`; explicit test paths; nothing mutated in the background. Every
RED was attributed to **a single named assertion** by reading the failure text, not the
pass/fail line. All recursive sweeps used `/usr/bin/grep`.

The exactly-once guard earned its keep: the first M3a anchor matched **0 times** and
was refused rather than silently no-op'ing into a false SURVIVED.

| # | Mutation | Result | RED attributed to |
|---|---|---|---|
| **P-C** | *(positive control)* `capture_cmux_ref` ref-shape check always returns 0 | **RED ×1**, 142 green | `test_empty_ref_capture_fails_the_spawn_instead_of_faking_one` — harness can kill |
| I2 | `$knob=$(shq "$v")` → `$knob=$v` | **RED ×1**, 142 green | `test_forwarded_knob_values_are_shell_quoted`, the **presence** assert |
| I1 | `_did_not_spawn` re-spells the verb tuple locally | **RED ×1**, 13 green | `test_did_not_spawn_delegates_to_the_shared_helper` |
| I3 | fallback ref-shape gate always passes | **RED ×1**, 142 green | `test_fallback_refuses_…`, `assert r.returncode == 3` |
| **I3-spec** | *(my probe)* `create_workspace_target` aborts **before** the resolve step | **SURVIVED** (1 passed, 1.53s) | **no assertion failed** — the test is satisfied by a control flow in which its named subject is unreachable. See Minor 1 |
| M1 | `if(index($0,"[selected]"))` → `if(0)` | **RED ×1**, 142 green | `test_selected_row_wins_…`, the `--surface == surface:11` assert |
| M3a | drop `"$BUDGET_FLAG"` from the `handshake=timeout` printf | **RED ×1**, 142 green | `test_timeout_record_keeps_…`, `out["budget"]` |
| M3b | drop `"$TOPOLOGY_FIELD"` from the same printf | **RED ×1**, 142 green | `test_timeout_record_keeps_…`, `out["topology"]` |
| M4 | `rename-tab --workspace "$CMUX_WORKSPACE_ID"` on both paths | **RED ×1**, 142 green | merged `test_rename_tab_carries_workspace_on_both_topologies`, **fallback leg** |

Two claims were verified by direct measurement rather than mutation:

- **Default stub output unchanged (M1).** Extracted the pre-delta `cmux_v2_stub()` via
  `git show HEAD~1:…`, executed both bodies under `/bin/sh` with no knobs set, and
  compared rc + stdout bytes: **identical** (`* surface:11  SDD resume: demo  [selected]\n`).
  Both `CMUX_LIST_SURFACES_TWO_ROWS` rows carry a valid `surface:N` token
  (`surface:10`, `surface:11`) with the marker on the second, so the ref-shape gate
  still passes on that path. `CMUX_LIST_SURFACES_NO_REF` emits `* pane:3 …` — a row
  with no surface token, so the parser genuinely skips rather than seeing empty input.
- **M4 leg isolation.** `run_spawn` sets `HOME=tmp_path/home` and `CMUX_LOG=tmp_path/cmux.log`,
  and `install_bundle`/`install_version` write under `tmp_path/home`. Every harness path
  is `tmp_path`-derived, so the two per-leg subdirs cannot contaminate each other's
  `.rename-tab.argv`. The claim holds by construction, not by luck.

Restoration verified at the end: `git status --porcelain` shows **no** modification to
`skills/` or `tests/` (only SDD bookkeeping artifacts the controller/hooks own), the
backup directory is empty, and `bash -n` passes on the script.

## Strengths

- **All six claimed fixes are non-vacuous, and each is killed by exactly one assertion.**
  Every mutation in the implementer's own table reproduced independently, with the same
  count and the same test. Nothing in this delta is a pin that pins nothing — which was
  the round's primary risk and the reason it exists.
- **I2 is stronger than claimed.** The vacuity trap the prompt warned about
  (`shlex.quote` output containing the bare substring) is defeated by including the
  `KNOB=` prefix in both assertions: `shlex.quote` inserts `'` immediately after the
  `=`, so `KNOB=a b; touch …` is not a substring of `KNOB='a b; touch …'`. Both legs are
  independently load-bearing. `SUPERPOWERS_CMUX_TITLE_FORMAT` was confirmed present in
  the forwarded knob list, so the pin exercises a real forwarding path.
- **I1 pins delegation, not provenance.** The monkeypatch target resolves correctly —
  `_did_not_spawn` reads `did_not_spawn` from the test module's globals at call time —
  and under the re-spelling mutant it returns `True` instead of the sentinel. A
  `__module__` provenance assert would have survived that mutant (the import is
  untouched); this one does not. The exact drift the old comment *claimed* to catch is
  now genuinely caught.
- **M3's reachability was proven, not asserted.** Fallback + timeout together is real:
  both drops RED on the same test, so `TOPOLOGY_FIELD` moved from INFERRED to MEASURED
  legitimately.
- **M4 genuinely fixes the survivorship.** The merged test dies under the M-M mutation
  its pre-merge form survived, and no assertion was lost in the merge — the deleted
  sibling's `returncode == 0` and `workspace:9` checks both survive, and the surface
  leg gained an `r_s.stderr` failure message it previously lacked.
- **Nothing the delta added is dead surface.** Swept with
  `/usr/bin/grep -rn "CMUX_LIST_SURFACES_NO_REF\|CMUX_LIST_SURFACES_TWO_ROWS" tests/ skills/`:
  each knob has its stub definition plus **exactly one live consumer**
  (`test_spawn_handoff_v2.py:1097` and `:1126`), and each of those consumers is a test
  proven above to die under its own subject's mutation. A knob defined with no consumer
  would have been a producer-less obligation committed while fixing producer-less
  obligations; there isn't one.
- **Fence discipline.** All four touched files are inside Task 9's Write-Scope row
  (`module-3-spawn-script.md:52`). The three declared deviations are accurate, and M4's
  merge really does *close* a prior undeclared departure rather than open a new one.
- **The report's honesty register is calibrated.** It declines the instructed message
  pin rather than faking one, records `END{if(!f)print first}` as still-unpinned so a
  later reviewer does not re-file it, and separates measured from inferred.

## Issues

### Critical

None.

### Important

None. Every fix in the delta was mutation-verified to be load-bearing; no vacuous fix,
no regression, no unpinned addition, no undeclared fence departure.

### Minor

**Minor 1 — `test_fallback_refuses_when_no_surface_ref_can_be_resolved` cannot separate
the ref-shape gate from an abort *earlier in the same function*.** `test-specificity`

Measured, not argued. I inserted `return 1` into `create_workspace_target` immediately
after the `[ $rc -eq 0 ] || return 1` line — i.e. the fallback aborts **before
`list-pane-surfaces` is ever invoked**, so the ref-shape gate is unreachable — and the
test **PASSED** (1 passed in 1.53s).

Every assertion in the evidence combination is satisfied by any post-`workspace create`
failure: `workspace create` is logged before its rc is consumed, `rename-tab`/`send` are
absent, `surface == "-"`, `topology == "workspace-fallback"`, the hop is consumed, and
`rc == 3`. The same is true of `CMUX_WS_CREATE_RC=1`. So the substituted pin, while
strictly stronger than a bare `returncode == 3`, still inherits that assertion's
misattribution hazard: it names the ref-shape refusal but proves only "the fallback
failed somewhere after the create call was logged."

Note also that the RED under the real I3 mutation was attributed to
`assert r.returncode == 3` — the first assertion, and precisely the one the fix
instruction warned about. The evidence legs never executed.

This does **not** invalidate the fix: the test demonstrably kills its subject (I3 mutation
→ 1 RED), which is what the finding asked for. What is missing is one discriminator
proving the run reached the resolve step:

```python
assert "list-pane-surfaces" in verbs, "never reached the ref-resolve step"
```

That is the only assertion available to this test that becomes **false** under a
pre-resolve abort — every other leg, including `rc == 3`, is true in both worlds. One
line; no behavior change; not a blocker.

**Minor 2 — the I2 test's docstring (and the report) misstate which assertion
discriminates.** `docs-accuracy`

Both say: *"Presence alone therefore proves nothing. The discriminator is the pair."*
Empirically false. Under `$(shq "$v")` → `$v` the **presence** assertion is what fired:

```
AssertionError: forwarded knob value is not shell-quoted:
  'export SUPERPOWERS_SPAWN_ID=… SUPERPOWERS_CMUX_TITLE_FORMAT=a b; touch /tmp/PWNED; claude-picker …'
```

The quoted form `KNOB='a b; …'` is absent from the mutant output, so presence alone
discriminates; and the raw output confirms the bare form *is* present, so the absence
leg is independently load-bearing too. The test is **stronger** than documented, not
weaker — the reasoning is wrong in the safe direction.

Why it is worth a line at all: a docstring that declares one of its two assertions
vacuous invites a future reader to delete it. The correct statement is that the `KNOB=`
prefix plus `shlex.quote`'s leading `'` is what defeats the substring trap, and that
both legs kill the mutant. Cosmetic; a comment edit.

### Observations (recorded so they are not re-filed as findings)

- **The delegation test's `tmp_path` argument is inert.** `cmux_log_text` returns `""`
  for a missing log, so the test would pass identically with any path, and it pins
  nothing about the log argument being passed through. That is acceptable within I1's
  stated scope — the finding was delegation, not argument fidelity — and the sentinel
  form is the reviewer's own prescribed shape.
- **A cosmetic line-wrap landed on an untouched assertion** in
  `test_spawn_handoff_hardening.py` (the `"control leg never reached the verb"` assert,
  reflowed to the parenthesized form). Whitespace only, inside a file in this task's
  write scope. Not a fence departure and not a finding.
- **`END{if(!f)print first}` remains unpinned**, as the report itself records. Both stub
  shapes carry a `[selected]` row; pinning it needs a third shape. Correctly declared,
  correctly not chased.
- **I4 is untouched by instruction** and remains an accepted risk owned by merge.

## Assessment

The round's own premise — that a fix round is where defects are introduced — was tested
directly rather than assumed. It did not happen here. Nine mutations plus a harness
positive control reproduce the implementer's table exactly: six claimed fixes, six
single-assertion REDs, no regression in the surrounding 142, and the two non-mutation
claims (byte-identical default stub output, per-leg isolation) verified by measurement
rather than accepted.

The one gap I found is a specificity gap, not a vacuity gap: a test that provably kills
its own subject but whose supporting evidence cannot name *which* step refused. It costs
one line. The second is a comment that describes the test as weaker than it is. Neither
touches production behavior, neither leaves a guard unpinned, and inflating either into
a blocker would be the manufactured finding the instructions rightly warn against.

Both stopping-rule conjuncts are satisfied: the findings are cosmetic, and I approve.

**ASSESSMENT: APPROVED**
