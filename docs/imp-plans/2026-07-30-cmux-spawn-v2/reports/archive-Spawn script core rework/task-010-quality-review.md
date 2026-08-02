# Task 10 Code Quality Review — cmux-spawn-v2

## Strengths

- **Handshake/enrichment separation is real, not just labeled.** `diagnose_target()` is called exactly once, only inside the second failed-re-wait branch, after exit 3 is already the only possible outcome. Traced the full control-flow block — no path from `DIAG` reaches the success stanza.
- **Fixture provenance claims are honest and independently verifiable.** Re-derived `trust-dialog.txt`/`banner.txt`/`noise.txt` byte-for-byte against `cmux-verb-shapes.json` in a standalone check (all three match), and re-ran all four anchor patterns against `both-anchors.txt`, `picker-error.txt`, and `noise.txt` independently — every result matches the implementer's table exactly.
- **The `CMUX_READ_SCREEN_RC` stub knob genuinely isolates the two `unreadable` disjuncts.** Traced the stub logic in `spawn_handoff_helpers.py` line by line — real, not asserted.
- **Anchor provenance labeling (MEASURED/INFERRED/INVENTED) is applied per-anchor, not per-branch**, correctly surfacing that the `banner` branch's two anchors have different evidence quality.
- **Never claims "nothing was spawned"** in any of the four diagnosis arms — verified by grep across the whole timeout tail.
- **Clean by every mechanical instrument**: `shellcheck --severity=warning --external-sources` exits clean, `bash -n` clean, no dead code, no leftover amendment-round scaffolding.
- **`SPAWN_SURFACE_REF` traced correctly** — only assigned after `LAUNCH_ACCEPTED=1` on whichever topology actually fired, so `diagnose_target` can never read a stale or wrong surface.
- **Tests exercise real script behavior, not mocks-of-mocks** — `cmux_v2_stub()` is a real script on `PATH` intercepting the actual subprocess.

## Issues

### Critical (Must Fix)
None found.

### Important (Should Fix)
1. **Trust-dialog/banner arms carry no printed recovery guidance beyond "attach to that tab".** This is correct, spec-mandated behavior — the module AC requires these two arms to steer to the existing tab and omit `print_manual_instructions()` (verified: it fires only at lines 852/855, picker-error/default, never at 847/849). Not an implementation defect. But since `diagnose_target` has never run against a live cmux surface, a false-positive classification (banner/trust text present, successor actually dead) would leave an operator with no printed fallback if the tab turns out unusable. Recommended follow-up, not a gating fix: either a one-line escape-hatch mention or an explicit accepted-risk row.

### Minor (Nice to Have)
1. **No test exercises a malformed/truncated multi-byte screen capture.** `diagnose_target` greps real terminal output containing box-drawing characters and emoji. All fixtures are clean, complete UTF-8. Design bounds the risk (fail-safe direction is toward `none`/`unreadable`, never a wrong-but-confident diagnosis), but this specific claim was never measured with a positive control, unlike everything else in this task.

## Recommendations
- Fast follow (not blocking): append a short escape-hatch line to the trust-dialog/banner arms, or record an explicit accepted-risk row in `deviations.md`.
- Both findings are evidence-quality gaps consistent with what the implementer already disclosed (n=1 banner sample, zero live runs) — watch at first real production timeout rather than gating this merge.

## Test Results (independently re-run, twice)
```
.venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider
796 passed, 1 warning in ~260s
```
Run twice from a clean `__pycache__` state: **796 passed, 0 failed** both times — matches the implementer's report and the spec review's independent run exactly.

## Assessment

**Ready to merge?** Yes

**Reasoning:** The handshake/diagnosis separation is structurally sound and independently verified against raw fixtures and stub logic, not just report prose; all 19 new tests pin real disjuncts; dead-code and contract-constraint checks came back clean. The Important/Minor findings are genuine residual risks proportionate to the "first live run" caveat the implementer already disclosed — they warrant a tracked follow-up, not a blocked merge.
