# Task 11 — Spec Compliance Review

**Status: PASS** (no Critical, no Important; 4 Minor)

> Reviewer model: opus. Independently re-ran 4 of the 5 Step-4 suites; did NOT re-run the full pytest suite
> (declared, not implied — see "Could NOT confirm").

## Step-by-step compliance

| Step | Verdict | Evidence |
|---|---|---|
| **1** (CLAUDE.md section) | **delivered** — all 5 content sub-items + env-var addition | New `## cmux Auto-Spawn Handoff (2026-07-22, N43(D))` at CLAUDE.md:262–274, between "Pipeline Flexibility" and "New Harness Support" (a top-level feature section, as asked). Interface+exit ladder ✓; cross-repo split ✓; log format + explicit "**This is NOT `context-observations.log`**" ✓; not-a-hook + main-checkout resolution ✓; `--focus false` pointer ✓. Env-var bullet added to Hook Development Gotchas (CLAUDE.md:322) with `MAX_HOPS` (3) and `QUOTA_MIN_PCT` (15). |
| **1b** (notify asymmetry) | **delivered, in corrected form** | "*Three exit-3 branches notify … `:125` **cannot** notify — `cmux notify` is the very transport the reachability probe just failed. `:464`/`:469` **deliberately** do not …*" Two distinct reasons, plus "do not 'fix' them into consistency". |
| **1c** | **delivered** | See per-obligation table below. |
| **2** (manifest) | **delivered**, all 5 bullets | Script row (:342), test+fixtures folded into that row's `Tests:` field, e2e 14→15 in the counts header (:390), protocol-doc rewrite (:373), cross-repo pointer in both the script row and a new Document Index row (:528). |
| **3** (BACKLOG) | **delivered** | New `N43(D)` row at :91, references the feature dir, 0 deletions. |
| **4** (suites) | **delivered**; reviewer re-ran 4 of 5 | install **104/0/0 PASSED**; regression **PASS 159 / FAIL 0 / WARN 2**; `check-hooks.sh` → **PASS, 7 hooks intact, no re-capture**; e2e → **`E2E PIPELINE PASS - 15 steps composed correctly`**. `test_spawn_handoff.py --collect-only` → **72 collected**, matching the doc. |
| **5** (commit) | **delivered, +1 extra commit** | `f565a16` (message verbatim per spec) + `da7e367` (self-review fix; implementer Deviation #4, disclosed). |

## Step 1c obligations

- **(a) bash floor ≥ 3.2, both floors** — ✓ "*Bash floor is ≥ 3.2, not 4.x (construct floor 3.1 for `FORWARDED+=`; verified against `/bin/bash` 3.2.57)*".
- **(b) `set -u` ↔ `${FORWARDED[*]}` at the `FORWARDED` site** — ✓ **intent met.** Literal reading (a comment in the script) is barred by the freeze; anchored to the three concrete construct sites instead. **Empirically re-verified by the reviewer:** `/bin/bash` 3.2.57 → `A[*]: unbound variable` *and* `A[@]: unbound variable`; `/opt/homebrew/bin/bash` 5.3.9 → prints `[]` and `ok`. The asymmetry is exactly as documented.
- **(c) `QUOTA_TIMEOUT` (60) + `QUOTA_TOOL`** — ✓ in both the CLAUDE.md env bullet and the manifest row; defaults confirmed at `:152`/`:32`.
- **(d) append-prompt accumulation, no reaper** — ✓ path construction confirmed at `:218-219`.

## Scope discipline — PASS

Exactly three files. `git diff --name-only 78dcd25..HEAD -- spawn-handoff-session.sh sdd-pre-dispatch-hook.sh baseline.txt` → **empty**. Nothing beyond the seven steps.

## Read-merge — PASS

```
15	1	CLAUDE.md
4	2	docs/ARaymond-customization-manifest.md
1	0	docs/process-improvement-findings/BACKLOG.md
```

BACKLOG **0 deletions** ✓. The 3 deletions verified as in-place modifications **by word-multiset diff, not by trusting the report**:
- CLAUDE.md e2e bullet (line 128 both sides): OLD words absent from NEW = **`13→14).` only**; 278 → 334 words, every other original token retained.
- Manifest counts header: OLD words absent from NEW = only the refreshed numbers/date/label. Both load-bearing sentences preserved.
- Manifest `context-handoff-protocol.md` row: original N43 text present verbatim, new note appended.

## Factual accuracy

**Confirmed (every line opened):** `:53`, `:55`, `:484`, `:439`, `:125`, `:137`, `:195`, `:464`, `:469`, `:491`, `:217`, `:308`, `:342` — **13/13 OK**.

**Notify asymmetry — CONFIRMED and precisely stated.** Exactly three exit-3 notifies (`:134`, `:192`, `:488`); the `:429` notify is on the rc==0 path and correctly excluded. "Five causes across six sites" is exactly right (reservation-write failure is one cause at two sites). `:122`'s guard is `cmux ping` ≠ `PONG`, so "cannot notify" is causally correct rather than a rationalization; `:457-470` contains warn + `print_manual_instructions` + `exit 3` with **no** notify call.

**"tracked" wording — CONFIRMED CORRECT.** Docs say "*Neither file is gitignored … committable*", never "tracked". `git check-ignore` → rc 1 on both; `git ls-files …/reports/` → no match.

**"component A" collision — CONFIRMED AVOIDED.** No occurrence of "component A" in CLAUDE.md at all. `BACKLOG.md:91` names the repo and explicitly flags the overload against N43's lettering at `:90`.

**Other confirmations:** log record shapes/field order at `:466`/`:480-481`/`:486-487` incl. `workspace=spawn-failed`; `runtime-picker-failure` composed at `:375` with `$SPAWN_ID`; `--focus false` at `:414`; not-a-hook (`grep -c 'spawn-handoff'` → **0** in both `baseline.txt` and the settings file); `readlink ~/.claude/skills/superpowers` → the MAIN checkout; repo-1 `claude-picker` → `…/telemetry-exp/launchers/claude-picker`; repo-2 its own toplevel with `verify-install.sh` + 4 live `cmux*` symlinks; `cmux-custom-skills/README.md:37`; `cmux-workspace/SKILL.md:48`; `spec.md:181`; N51 = `**blocked**`; protocol steps 3–5 match, including the picker-manual user-telling.

**e2e Step 14 description — CONFIRMED against `sdd-e2e-test.sh:610-726`:** stubs (:646-660); `cd "$SPAWN_WT"` subshell (:676); asserts `launch=auto` (:693), composed command (:707/:713), `--focus false` (:696), notify (:697), intent-before-outcome (:719), hop=1 (:722); banner `15` (:728). Every clause backed.

**Counts consistency:** `grep -c '13→14' CLAUDE.md` → **0**; exactly one current banner statement.

**Could NOT confirm (declared):** (1) the **unit 625** figure — full pytest not re-run by the reviewer (the controller re-ran it independently: `625 passed`). (2) The bash **3.1** *construct* floor — only 3.2.57 and 5.3.9 exist on this machine; the ≥3.2 claim as written is what was verified.

## Positive control

**#1 (wrong-line assertion):** ran the checker against deliberately wrong cites — `:485`→`else`, `:309`→empty, `:218`→`APPEND_TARGET_DIR=…` — all three returned **MISMATCH** while the 13 real cites returned OK.
**#2 (file mutation):** `sed -i ''` changed the CLAUDE.md exit-ladder cite `:484`→`:485`; the checker flipped `VERDICT: CONFIRMED` → `VERDICT: DEFECT`. Restored with `git checkout -- CLAUDE.md`; `git diff --name-only` no longer lists it (remaining entries are the controller's own in-flight artifacts). **No `git stash` used** — controller re-verified the restore independently.

## Findings

1. **Minor — `## Deterministic Scripts (15 active)` heading is stale.** Counted 17 table rows before, 18 after. Called pre-existing drift widened by this task. *Fix:* controller decides — drop the parenthetical or set it to the row count.
   > **⚠ SUPERSEDED by the quality review, which was right and this finding was wrong.** The heading never counted total rows — it counts `subagent-driven-development/scripts/` rows, verified across 4 snapshots. It was **exactly correct (15/15) at `78dcd25`**, and Task 11 introduced the drift by 1. Correct value: **16**. Controller independently reproduced. See quality-review Finding 1.
2. **Minor — `BACKLOG.md:90` (N43) still lists (D) as deferred.** Reconciling in place would cost a deletion Step 3 forbids; the new row carries an explicit supersession sentence. *Fix:* fold into `finishing-a-development-branch`'s merge-annotation pass.
3. **Minor (report-internal only) — two stale line cites in the implementer's claim ledger.** Cites `BACKLOG.md:98` for N51 (actual **:99**) and `deviations.md:112–116` for the Step-1c list (actual **:119–123** now). Both were correct when written; the files shifted underneath (the implementer's own BACKLOG insertion, and the controller's deviation rows). **No claim in any delivered doc depends on these.**
4. **Minor (informational, not a defect) — the installed path spelled in CLAUDE.md does not resolve pre-merge.** `~/.claude/skills/superpowers/…/spawn-handoff-session.sh` → ENOENT today: the symlink points at the main checkout and the script is unmerged. The adjacent bullet makes this coherent, and the already-shipped protocol doc uses the same spelling. Covered by the post-merge live smoke already tracked in the BACKLOG row.

**No Critical or Important findings.** Both controller corrections landed in corrected form, all four Step-1c obligations are present and independently re-verified, and every factual claim opened against the frozen script, the e2e test, repo-2, and the filesystem was true.
