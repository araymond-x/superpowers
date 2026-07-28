---
schema_version: 1
task_id: 11
task_type: implementation
status: DONE_WITH_CONCERNS
files_changed:
  - path: "CLAUDE.md"
    description: "New top-level `## cmux Auto-Spawn Handoff (2026-07-22, N43(D))` section (9 bullets: interface, cwd requirement, exit ladder, notify asymmetry, spawn-log format, not-a-hook, bash floor + FORWARDED/`set -u`, cross-repo split, append-prompt accumulation); new `SUPERPOWERS_CMUX_*` env-var bullet in Hook Development Gotchas; Testing e2e bullet gains Step 14 and now carries one current banner count (15)."
  - path: "docs/ARaymond-customization-manifest.md"
    description: "New `spawn-handoff-session.sh` row in Deterministic Scripts; `context-handoff-protocol.md` reference row records the Task-9 steps-3-5 rewrite; `Current real counts` header refreshed (unit 625 / e2e 15 / regression 159 PASS 2 WARN / install 104, dated 2026-07-25); new Document Index row for the feature dir with the repo-1/repo-2 cross-repo pointer."
  - path: "docs/process-improvement-findings/BACKLOG.md"
    description: "New `N43(D)` row inserted after N43 closing component (D) as done-pending-merge (pure insertion, 0 deletions). N51 untouched."
tests:
  written: 0
  passing: 0
  command: "bash tests/ARaymond-installation/verify-symlink-install.sh && python3 tests/ARaymond-skill-regression/validate-all-skills.py && .venv/bin/python3 -m pytest tests/unit/ -q && bash tests/integration/sdd-e2e-test.sh && bash tests/ARaymond-hook-baseline/check-hooks.sh"
  result: PASS
contract_compliance:
  - constraint: "Exit-code contract (0 spawned / 3 manual fallback / 1 refused)"
    status: compliant
    detail: "Documented from the script, not the prose: 0 has TWO causes (:484 spawned, :439 --dry-run) plus the picker-manual caveat; 3 lists five causes across six sites (:125/:137/:195/:464/:469/:491); 1 lists the refused preconditions."
  - constraint: "Script path is `~/.claude/skills/...` for the installed protocol doc and `skills/subagent-driven-development/scripts/...` in-repo"
    status: compliant
    detail: "Both spellings appear in the CLAUDE.md bullet; the manifest row uses the in-repo skill-relative form matching its table convention."
  - constraint: "Do not change `sdd-pre-dispatch-hook.sh` or the hook baseline"
    status: compliant
    detail: "Commit contains exactly 3 doc files; `check-hooks.sh` -> PASS with no re-capture."
  - constraint: "`spawn-handoff-session.sh` is FROZEN — read only"
    status: compliant
    detail: "Read only. This forced one reinterpretation of a Step 1c obligation — see Deviations."
---

**Implementation Summary:** Landed all seven steps (1, 1b, 1c, 2, 3, 4, 5) as read-merge edits to the three target docs. Every factual claim was re-derived from the frozen script, the e2e Step 14 block, repo-2, and the filesystem rather than from the plan or the brief; both controller corrections were written in their corrected form, and the third (letter-overloading) was resolved by naming the thing instead of using "A". Two commits: `f565a16` (the work) and `da7e367` (a self-review fix — see Self-Review Findings).

**Source Files Read:**
- `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (all 492 lines) — exit ladder, notify sites, log printf formats, env vars/defaults/validation, `FORWARDED` sites, cwd resolution. Not edited.
- `docs/imp-plans/2026-07-22-cmux-integration/deviations.md` — the Step 1c obligation list at the "Task 9 doc obligations" bullet (lines 112–116), confirmed to be OLD numbering = this task.
- `skills/subagent-driven-development/references/context-handoff-protocol.md` — what Task 9's steps 3–5 rewrite actually says, for the manifest row.
- `tests/integration/sdd-e2e-test.sh:610-726` — Step 14's real assertions and its `cd "$SPAWN_WT"` subshell, so the CLAUDE.md description matches the test.
- `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` — targets, read before editing (BACKLOG N43 row at :90 and N51 at :98 read in full).
- `~/projects/claude-custom/cmux-custom-skills/README.md:37` + `skills/cmux-workspace/SKILL.md:48` — the fork-guidance-lives-elsewhere convention and the `--focus false` guidance.

**CLAUDE.md Files Read:** `CLAUDE.md` (repo root, itself a target) — "Documentation Maintenance" (this change is exactly its 1/2/3/4 list), "Hook Development Gotchas" as the de-facto env-var registry, and the "Pipeline Flexibility" / N43 sections as the density model. No other target directory carries its own CLAUDE.md (`docs/` has none).

**Deviations from Plan:**
1. **Step 1c(b) "at the `FORWARDED` site" reinterpreted.** As literally worded that means a comment in the script — which the freeze forbids. Landed instead in CLAUDE.md anchored to the concrete construct (`FORWARDED=()` `:217`, `${FORWARDED[*]}` `:308`, `${FORWARDED[@]}` `:342`) with the passes-on-4.4+/fails-on-3.2 asymmetry spelled out, rather than a generic "no `set -u`". Justification from the script itself: `:6-7` already says *"intentionally does NOT use `set -u` … See CLAUDE.md Hook Development Gotchas"* — writing the mechanism there completes that pointer.
2. **BACKLOG closure is a NEW row (`N43(D)`), not an edit to N43's row.** Step 3 says "add a row" and the 0-deletions requirement agrees; editing N43 in place costs a deletion. The ID cell `N43(D)` is a **new format** (every existing ID is a bare `B/I/C/N/P` + number) — chosen over inventing `N52`, which would decouple the closure from N43's own lettering. Nothing parses BACKLOG (`grep -rln 'BACKLOG' tests/ hooks/ skills/*/scripts/` → no hits), so this is cosmetic. One character for the controller to override if unwanted.
3. **Manifest heading `## Deterministic Scripts (15 active)` left unchanged** — see Concerns.
4. **Second commit `da7e367`** beyond Step 5's single-commit instruction: a self-review fix, not amended (amending is not authorized).

**Self-Review Findings:**
- **Found and fixed (commit `da7e367`):** my Step-1 edit left the Testing e2e bullet carrying *two* banner counts — N43's historical "banner step count 13→14" followed by my "14→15". That bullet is the line the manifest header names as "the authoritative running counts", so a reader hits `13→14` first and reads it as current. Rewrote the first parenthetical to "the step that took the banner count to 14" and the second to "**banner step count is now 15**"; `grep -c '13→14' CLAUDE.md` → `0`, exactly one current total remains.
- Verified each of Step 1c's four obligations is present, not just intended: (a) bash ≥ 3.2 with both floors; (b) the `FORWARDED` coupling at named lines; (c) `_QUOTA_TIMEOUT` (60) + `_QUOTA_TOOL` in the gotchas bullet *and* the manifest row; (d) append-prompt accumulation with "no reaper (spec §5.4d defines none)".
- Verified neither correction was reproduced in its plan form: the notify bullet gives both reasons (`:125` **cannot**; `:464`/`:469` **deliberately** don't), and the log bullet says "Neither file is gitignored … committable", never "tracked".
- Checked the trivial precondition the brief warned about: the `cd` requirement is in the CLAUDE.md section, the manifest row, and my Step 14 description.

**Concerns:**
1. **`## Deterministic Scripts (15 active)` is stale and I did not change it.** Measured: **17** table rows before my edit, **18** after. So the heading was already wrong by 2 for reasons predating this feature (most likely `context-probe.py` and `check-safe-branch.sh`); `git log -L` on that heading returned nothing, and I stopped at one command per the budget. I left it because "active" is undefined (18 rows, 15 non-hook-referring rows would be 14 — neither matches 15) and the brief scoped exactly two count-bearing lines to me. **Flagging so the drift is not attributed to Task 11.** Controller's call.
2. **N43's own row at :90 still describes (D) as deferred.** Reconciling it in place would cost a deletion the task forbids, so my new row carries an explicit supersession sentence ("this row, not N43's notes, is (D)'s current state"). A reader who stops at :90 still gets the stale answer.
3. **Line numbers in durable docs rot.** I cite 11 `spawn-handoff-session.sh` line numbers in CLAUDE.md. They are correct today and the script is frozen, but any future edit invalidates them.
4. The Document Index is **not exhaustive** (neither `sdd-aggregate-gate-visibility` nor the 2026-07-14 N43 feature has a row), so my new row follows a partial convention.

---

### Evidence — Step 4 suites, run against the final commit `da7e367`

```
### bash tests/ARaymond-installation/verify-symlink-install.sh
  Passed:   104
  Failed:   0
  Warnings: 0
STATUS: PASSED
### python3 tests/ARaymond-skill-regression/validate-all-skills.py
=== SUMMARY ===
  PASS: 159  FAIL: 0  WARNING: 2
  Result: PASS (with warnings)
### .venv/bin/python3 -m pytest tests/unit/ -q
625 passed, 1 warning in 140.69s (0:02:20)
### .venv/bin/python3 -m pytest tests/unit/test_spawn_handoff.py -q
72 passed in 63.77s (0:01:03)
### bash tests/integration/sdd-e2e-test.sh
E2E PIPELINE PASS - 15 steps composed correctly
### bash tests/ARaymond-hook-baseline/check-hooks.sh
PASS — 7 superpowers hooks intact (scripts unchanged, settings.json entries present)
```

Hook baseline PASSes with **no re-capture** — no hook changed. All counts written into the docs come from this run (an identical pre-commit run produced the same figures).

**Count that disagrees with prose:** the brief's Context section says 58 unit tests as of end-of-Module-1; the file now collects **72**. The run wins; 72 is what I wrote (as a collected/passed count, matching the manifest's `(13 total)` / `(22)` house style).

### Read-merge proof

```
$ git show --numstat --format='%h %s' HEAD~1     # f565a16
f565a16 docs(cmux-int): CLAUDE.md cmux section, manifest, close N43(D) (Task 11)
15	1	CLAUDE.md
4	2	docs/ARaymond-customization-manifest.md
1	0	docs/process-improvement-findings/BACKLOG.md

$ git show --numstat --format='%h %s' HEAD       # da7e367
da7e367 docs(cmux-int): make the e2e Testing bullet carry one current step count (Task 11 self-review)
1	1	CLAUDE.md

$ git diff --numstat 78dcd25..HEAD               # combined, both Task 11 commits
15	1	CLAUDE.md
4	2	docs/ARaymond-customization-manifest.md
1	0	docs/process-improvement-findings/BACKLOG.md
```

**`BACKLOG.md`: 1 insertion / 0 deletions.** Every existing row preserved byte-for-byte.

**The 3 deletions, each named and justified** (all are in-place line modifications, not removals):

| File | Deleted line | Why |
|---|---|---|
| `CLAUDE.md` | the `tests/integration/sdd-e2e-test.sh` Testing bullet | appended the Step 14 sentence; the N43/Step 13 text is preserved in full, with only its `13→14` parenthetical reworded so the line carries one current count |
| manifest | `context-handoff-protocol.md` reference row | appended the Task-9 steps-3–5 rewrite note; original N43 text preserved verbatim ahead of it |
| manifest | `> **Current real counts (2026-07-07 …)**` header | the required refresh — numbers + date + feature enumeration; the two load-bearing sentences ("rows below NOT updated in place", "authoritative counts live in `CLAUDE.md` Testing") preserved |

Working tree after commit contains only the controller's own pre-existing artifacts (`.dispatch-log`, `context-observations.log`, `checkpoint-pre-dispatch-011.json`, `partner-review-011.md`) — nothing of mine, no scratch files in the repo.

### Claim ledger

| Claim written into the docs | Verified at |
|---|---|
| Interface `BUNDLE_ID [--dry-run]` | `spawn-handoff-session.sh:2`, arg parse `:38-50` |
| Bundle validated as type `work` + entry skill `superpowers:subagent-driven-development` + same repo identity | `:33-34`, `:101-102`, `:105-115` |
| cwd resolves the worktree; script cd's there; exits 1 outside a repo | `:53`, `:55`, `:54` |
| Exit 0 = spawned **or** `--dry-run` | `:484`, `:439` |
| Exit 3 — five causes / six sites | `:125`, `:137`, `:195`, `:464`, `:469`, `:491` |
| Exit 1 refused preconditions | `:42`, `:44`, `:49`, `:54`, `:55`, `:57`, `:78`, `:119` |
| Three exit-3 branches notify | `:134`→`:137`, `:192`→`:195`, `:488`→`:491` |
| `:125` **cannot** notify (notify is the failed transport) | `:122-125` (the guard is `cmux ping` ≠ `PONG`) |
| `:464`/`:469` **deliberately** do not notify | `:457-469` (warn + `print_manual_instructions` + exit 3, no notify call) |
| Log record shapes / field order / `workspace=spawn-failed` | `:466`, `:480-481`, `:486-487` |
| `runtime-picker-failure` emitted by the child with the parent's id at compose time | `:375` + the design note at `:360-365` |
| Timestamp format `%Y-%m-%dT%H:%M:%SZ`; spawn id is a uuid4 | `:64`, `:359` |
| Reserve-before-spawn ordering | `:442-470` (Decision 21 comment + both checked writes) |
| Neither `.handoff-hops` nor `handoff-spawn.log` is gitignored (and neither exists yet / is in the index) | `git check-ignore -v` on both → rc 1; `ls` → No such file; `git ls-files …/reports/` → no match |
| Not a hook / no baseline entry | `grep -c 'spawn-handoff' tests/ARaymond-hook-baseline/baseline.txt` → `0`; `check-hooks.sh` PASS unchanged |
| Live sessions resolve to the MAIN checkout | `readlink ~/.claude/skills/superpowers` → `/Users/araymond/projects/claude-custom/superpowers/skills` |
| e2e Step 14 is checkout-path only, runs with cwd inside a fixture repo, asserts `launch=auto`/composed cmd/`--focus false`/notify/intent-before-outcome/hop=1 | `tests/integration/sdd-e2e-test.sh:610-726` |
| `MAX_HOPS` default 3 | `:20` |
| `QUOTA_MIN_PCT` default 15, regex `^[0-9]+(\.[0-9]+)?$`, awk-injection rationale, warn-and-revert fail-open | `:25-30` (+ awk use at `:186`) |
| `QUOTA_TIMEOUT` default 60, integer-only, "gate went permanently inert" rationale | `:148-157` |
| `QUOTA_TOOL` default `$HOME/.claude/bin/claude-usage-pace`; explicit override authoritative → `unchecked`, only the default gets a PATH lookup | `:32`, `:140-147` |
| Bash floor ≥ 3.2 (construct 3.1, verified 3.2.57) | `deviations.md` Task 4 rows (spec-review-confirmed empirical derivation) |
| `set -u` breaks `${FORWARDED[*]}` on 3.2, passes on 4.4+ | `deviations.md:114` (verified under 3.2.57 by the prior task); sites `:217`, `:278`, `:308`, `:342` |
| Append-prompts at `~/.claude-codex-handoff/append-prompts/<bundle>-hop<N>.md`, no reaper | `:218-219` (path construction); no-reaper per spec §5.4d, recorded `deviations.md:116` |
| repo-1 = `telemetry-exp` owns `claude-picker` | filesystem: `claude-picker` → `~/projects/claude-custom/telemetry-exp/launchers/claude-picker`, whose repo root is `…/telemetry-exp` |
| repo-2 is a separate git repo with its own `verify-install.sh`, symlinked into `~/.claude/skills` | `git -C … rev-parse --show-toplevel` returns itself; `ls` shows `verify-install.sh`; `ls -l ~/.claude/skills/` shows 4 live `cmux*` symlinks into repo-2 |
| Fork-specific cmux guidance lives in this CLAUDE.md, not the vendored files | `cmux-custom-skills/README.md:37` |
| `--focus false` is current cmux guidance / the script uses it | `cmux-custom-skills/skills/cmux-workspace/SKILL.md:48`; script `:414` |
| This feature's spec calls repo-2 "Component A" (≠ N43's component A) | `spec.md:181` (re-verified post-commit: `## 6. Component A — cmux-custom-skills repo`); N43's own lettering at `BACKLOG.md:90` ("Scope = spine only (component A)") |
| N51 remains `blocked` on codex-side SDD | `BACKLOG.md:98` (read, not modified) |
| Protocol steps 3–5 drive the script incl. the picker-manual user-telling | `context-handoff-protocol.md:22-55` |

---

## Fix rounds (appended by the controller after review)

Task 11 shipped in **four commits**. The two `[task 11 fix]` rounds are recorded here; the frontmatter above describes the original delivery.

| Commit | Round | What |
|---|---|---|
| `f565a16` | original | The seven steps. |
| `da7e367` | implementer self-review | Removed a double banner count from the CLAUDE.md Testing bullet. |
| `056c453` | **[task 11 fix]** round 1 | Quality-review findings 1, 2, and the accepted half of 3. |
| `3917602` | **[task 11 fix]** round 2 | Re-review finding — a defect round 1 introduced. |

**Round 1 (`056c453`, 2 files / 4 lines):**
1. `## Deterministic Scripts (15 active)` → `(16 active)`. **This was a defect Task 11 caused, not inherited** — see the corrected `deviations.md` row.
2. Inverted the manifest counts header's false pointer (it claimed `CLAUDE.md` "Testing" holds the authoritative running counts; that section carries no pass counts at all — `grep -c '625' CLAUDE.md` → `0`). The header is now the stated authority. The fix implementer ran all five suites **before** writing the sentence, so the four numbers were true at the moment the line became load-bearing.
3. Dropped the six bare `:NNN` exit-3 cites from the CLAUDE.md exit-ladder bullet (cause names and the "five causes across six sites" framing kept; the cmux cause re-anchored on its `cmux ping` ≠ `PONG` construct), and made the manifest's script row **delegate** the ladder and the env-var default *values* to CLAUDE.md rather than duplicating them — matching the delegation it already used for the `set -u` fact. `:484`/`:439` were kept on the exit-0 clause by judgment: only two `exit 0` sites exist in 492 lines with disjoint semantics, so a drifted cite there is visible and recoverable, whereas a drift among six homogeneous exit-3 sites is not.

**Round 2 (`3917602`, 1 file / 1 line) — the re-review caught a defect round 1 introduced.** Round 1's new rationale ("left uncited *here* on purpose, because a drifted line number lands on a different exit-3 branch") **generalized to the very next bullet**, which legitimately keeps `:125`/`:464`/`:469`. The section read as internally inconsistent and invited a future editor to strip cites that are the referents making the notify asymmetry checkable. Round 2 states the real distinction: cites *paired with an assertion about that branch* are self-catching (a drift contradicts its own sentence), while cites in a homogeneous list drift silently. Round 2 also anchored the bullet's grep guidance after proving the bare form returns **9** hits — three comments, one of them about the *decoder's* exit codes rather than the ladder's.

**Controller verification of the final state** (run directly, not accepted from any report):

```
$ git log --oneline 78dcd25..HEAD
3917602 docs(cmux-int): state why the notify bullet keeps its cites; anchor the exit-3 grep [task 11 fix]
056c453 docs(cmux-int): correct script count, invert counts pointer, de-duplicate exit ladder [task 11 fix]
da7e367 docs(cmux-int): make the e2e Testing bullet carry one current step count (Task 11 self-review)
f565a16 docs(cmux-int): CLAUDE.md cmux section, manifest, close N43(D) (Task 11)

$ git diff --numstat 78dcd25..HEAD
15	1	CLAUDE.md
5	3	docs/ARaymond-customization-manifest.md
1	0	docs/process-improvement-findings/BACKLOG.md

$ grep -n '^## Deterministic Scripts' docs/ARaymond-customization-manifest.md
321:## Deterministic Scripts (16 active)
   (SDD-scripts rows = 16, total rows = 18 — convention holds)

$ grep -cE '^[[:space:]]*exit 3' skills/subagent-driven-development/scripts/spawn-handoff-session.sh
6
```

`BACKLOG.md` remains **1 insertion / 0 deletions** across all four commits. The frozen `spawn-handoff-session.sh` and `tests/ARaymond-hook-baseline/baseline.txt` are absent from every commit in the range.

