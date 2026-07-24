# Partner Review — Task 4 (Launch composition A: metadata decode, strip guard, label rule, telemetry)

**Status: APPROVED**
**Review tier:** full (dispatched)
**Round:** 1 (approved first pass — the proposed prompt was fully inlined, no placeholders, per the Task 3 round-1 lesson)

| Dimension | Verdict |
|---|---|
| Context Completeness | **PASS** — all 11 Contract Constraints verbatim (word-for-word vs `plan.md:104–114`), Shared Constants, Pattern References, Source Files, working dir, write scope; report format matches the `ImplementerReport` Pydantic model. No unsubstituted placeholders. |
| Context Accuracy | **PASS** — every factual claim verified against the repo (see below). |
| Prior Task Awareness | **PASS** — committed-task inventory, reusable script/helper inventory, `_spawnable` reuse, the file-watcher gotcha, and three of six "Patterns to copy" bullets from `task-003-quality-review.md`, including the two load-bearing ones. |
| Escalation Check | **PASS** — the bash-version self-contradiction is escalated with both halves named, machine facts stated, constructs enumerated, evidence required in a dedicated report section; matches the `deviations.md` carry-forward. |
| Architectural Alignment | **PASS** — write scope exactly matches the plan's Write-Scope Partitioning for Task 4; all relevant non-goals restated. |
| Pattern Completeness | **PASS** — `test_context_gate_tier.py` + `sdd-pre-dispatch-hook.sh`, matching the plan's `pattern_references` for Task 4. |

## Accuracy verification performed by the partner

Marker at line 199, Task 6 marker at 200 (script 202 lines); `SUPERPOWERS_ROOT` L16, `PYTHON` L17, `BUNDLE_ID`/`DRY_RUN` L38, `SP_HOP` L132 all exact. `encode_args` (L29) and `install_version` (L76) exist. **`install_version` writes to `tmp_path/home/.local/share/claude/versions`, matching the snippet's `VERSIONS_DIR="$HOME/.local/share/claude/versions"`.** `run_spawn` remaps `HOME` (L115). `_spawnable` exists at `test_spawn_handoff.py:163` and installs bundle `b1` with no `.handoff-hops`, so `SP_HOP=1` and the `b1-hop1.md` assertion holds. All five prior commits present. Suite re-run: **24/24 in 11.78s**.

## Recommended addition — ACTIONED by controller before dispatch

The partner flagged that the prompt never mentions Task 3's committed code intentionally diverging from this same module doc's Task 3 Step 2 snippet. Since the implementer is told the module doc is the task source **and** that the committed script is ground truth with "report BLOCKED on contradiction", opening that doc surfaces a real-looking contradiction. Tail risk: an implementer "restoring" the broken snippet over committed Task 3 code.

**Controller added this bullet to the dispatched prompt:**

> Task 3's committed quota/timeout code intentionally diverges from this module doc's Task 3 snippet (justified in `deviations.md`); that doc correction is owed separately — do not "restore" the snippet.

## Watch-fors on report-back (partner-supplied)

1. **Bash minimum must be empirical, not reasoned.** Partner's independent read: `FORWARDED=()`, `+=`, `read -r -d ''`, and `${FORWARDED[*]}` on an empty array are all 3.2-safe given the script deliberately omits `set -u` (L6-7), and no `mapfile`/`readarray` appears. So "3.2 suffices" is expected — but must be backed by an actual `/bin/bash` 3.2.57 run. If the report says "≥4.x", it must name the specific construct; scrutinize rather than accept, because Task 9 ships whatever it says.
2. **`VERSIONS_DIR` must survive the diff.** Unused in Task 4 (Task 5's preflight consumes it); a YAGNI-minded self-review could cut it and break Task 5. Same class as the accepted `QUOTA_STATUS` forward-scaffolding.
3. **`ARGS_OK` likewise has no Task 4 consumer** beyond guarding the decode — its degrade-to-picker-manual effect only becomes observable in Task 5. Expect no test for the corrupt-v1 path; that is correct, not a coverage miss.
4. **Per-task test counting** with `passing ≤ written`; Task 4's suite is parametrized (4 label cases + 2 append-form cases), so confirm the convention is coherent and the full-file total appears in prose only.
5. **`DECODE_TMP` cleanup is already correct** in the snippet (the `rm -f` sits after the if/else, covering the `ARGS_OK=0` path). If the implementer "fixes" this by moving the `rm`, verify no leak was introduced.
