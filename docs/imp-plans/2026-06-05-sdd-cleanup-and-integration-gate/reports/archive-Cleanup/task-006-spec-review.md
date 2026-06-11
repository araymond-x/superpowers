# Task 6 Spec Compliance Review (N17)

> Dispatched 2026-06-10 (provenance: `.dispatch-log` task=6 type=spec-review).
> Reviewed: commit 28b8f1a against module-1-cleanup.md Task 6 (base edc5ff2).

## Verdict: PASS — Spec compliant AND contract compliant

### Verification performed (independent, code-level)

**1. Fix matches the spec snippet exactly.** `transition-module.py:108-116` — the `else` branch joins `git_root` with `manifest.plan_file` and calls the existing `_verification_task_ids_from_file` helper (defined at line 53; now called from exactly two sites, lines 113/116). No duplicated YAML parsing. `manifest.plan_file` is a real top-level `SddSession` field, git-root-relative, so the join is correct.

**2. Test fixture is genuine.** `tests/unit/test_transition_module.py:235-253` — blanks `modules[0]["file"]` to `""`, writes the main plan at `feat_dir/plan.md` (exactly what `create_manifest` sets as `plan_file`), declares `task_type: verification` on task 3 (in-range), gives tasks 0-2 full reports+provenance and task 3 an implementer report ONLY, asserts `returncode == 0`. The exemption is the only thing that can make this pass.

**3. RED state reproduced.** Extracted BASE_SHA (`edc5ff2`) script into a mirrored /tmp layout and ran the exact scenario: **rc=1, stderr = `INCOMPLETE: Task 3: missing or empty spec review` / `quality review`** — precisely the N17 symptom. Base code had no `else` branch, leaving `verif_ids` empty.

**4. Hook-parity fidelity note verified accurate.** Hook (sdd-pre-dispatch-hook.sh:294-299) uses `-n` + `-f` (existence) checks; Python checks truthiness only — a *set-but-missing* module file falls back in the hook but yields an empty exemption set in Python. "Fail-closed" is correct: exemption not granted = strictly tighter gating. Matching the plan snippet over byte-parity with the hook is the right spec-compliance call. The Python path is also internally fail-closed for a missing main plan (`_verification_task_ids_from_file` returns `set()`).

**5. Test runs (actual counts):** transition suite → **13 passed** (incl. the new N17 test); full suite → **430 passed, 1 warning**.

**6. Commit verified.** `28b8f1a` subject exact; contents only the two specified files (+6/-1 script, +20 tests); trailers present.

**7. Self-hosting guard verified.** No column-0 `### Task` literal anywhere in the new fixtures (grep-confirmed).

### Report completeness
All frontmatter + five prose sections present and substantive; Self-Review contains a real finding (hook-parity divergence), not boilerplate.

### Findings

- **[ADVISORY]** `transition-module.py:112` vs `sdd-pre-dispatch-hook.sh:294-299` — the set-but-missing-module-file edge diverges between hook (falls back) and transition (empty exemption set). Fail-closed and spec-faithful, not blocking; if a future plan hits that state, a verification task would pass the hook live yet block at transition. One-line BACKLOG note warranted; arguably the transition's stricter behavior is the better semantic and the hook is the one to revisit.

### Verdict

**PASS** — all 5 plan steps satisfied, acceptance criterion demonstrably met, RED→GREEN independently reproduced. 13/13 transition tests, 430/430 full unit suite.
