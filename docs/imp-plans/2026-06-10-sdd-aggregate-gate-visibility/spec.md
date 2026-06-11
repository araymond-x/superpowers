# SDD Aggregate-Gate Visibility — Design Spec

> **Feature dir**: `docs/imp-plans/2026-06-10-sdd-aggregate-gate-visibility/`
> **Created**: 2026-06-10
> **Status**: design (brainstorming output, pre-plan)
> **Archetype**: extension (no obsolescence; targeted refactor elements in N19/N25)
> **Entry mode**: brainstorming
> **Sprint**: superpowers fork sprint 4 (anchor = N27; see `docs/process-improvement-findings/BACKLOG.md`)

## 1. Purpose

Sprint 3's first live `transition-module.py` run proved the multi-module path works — and exposed
its last blind spot: **the pre-completion AGGREGATE gates only police the final module** (BACKLOG
N27, sourced from the sprint-3 final review, Important #2). Each transition moves evidence out of
the aggregate gates' field of view: review files are **moved** to `archive-<module>/`
(transition-module.py:225) and the dispatch log is **copied then truncated**
(transition-module.py:249–250). The gates weren't weakened — their inputs were archived.

Sprint 4 is one combined deliverable, executed as a **2-module SDD feature**:

- **Module 1 — Aggregate-gate visibility**: make Check 7 (min-tier ratio) and Check 9
  (git-reality) archive-aware (N27), close the dispatch-log classification gaps that hide fix
  cycles from provenance (N26), and align the hook↔transition `module.file` fallback semantics
  (N19).
- **Module 2 — Calibration & hygiene**: Check 10 follow-up batch incl. the on-main false-block
  (N25), C2 risk-surface scan calibration (N22), fence-helper edge cases (N20), SDD SKILL.md
  "hook enforces this" framing pass (N6), and the intent-based F6 regression check (N8).

The sprint additionally closes sprint 3's Track-3 residue: the plan **deliberately includes a
non-last `task_type: verification` task** (the first live exercise of the N16-fixed verification
report path), and the 2-module structure live-exercises transitions again on a base that now
includes N18.

## 2. Goals / Non-Goals

**Goals**
- Cross-module aggregate visibility: after any number of transitions, Check 7 ratios cover ALL
  modules' reviews and Check 9 windows cover ALL modules' verification tasks. Fixtures prove a
  policy violation in an archived module is caught at the terminal gate.
- The provenance log sees the fix cycle: review-driven fix dispatches and re-review rounds
  produce log entries; the gate-required post-gate artifact names no longer trip Check 3b.
- Check 10 works in Aaron's preferred on-main flow (remoteless repo + `.allow-main`): committed
  integration tests in the feature window are visible to the changeset check, fail-closed
  semantics preserved.
- The risk-surface WARNING stops self-firing on plans that merely QUOTE risk keywords in fences,
  and stops missing plural/inflected forms.
- Bug-fix items (N20 fail-open, N25(a) false-block, N27 blindness) get failing-test-first
  treatment.
- Live exercises: one non-last verification task; one live module transition; the sprint's own
  e2e step proving archive-aware aggregates.

**Non-Goals (explicitly deferred)**
- N25(e) (config-nulling the checkpoint's own git calls) and N25(g) (exotic-topology probing of
  the newest-merge-base heuristic) — logged, not shipped.
- N21 (tier-faithful `create_manifest` helper), N23 (trace-extractor dead ref), N24 (Py3.9
  portability) — deferred to a future bundle. N28 is deferred EXCEPT sub-item (c), which becomes
  a free fold-in (see D15).
- Transition-time aggregate snapshots (rejected alternative for N27, see D2).
- C1 / C3 / B8 design spikes — sprint-5 candidates.
- Making aggregate gates hook-enforced rather than controller-invoked (C3's scope).

## 3. Decision Log

| # | Decision | Chosen | Notes |
|---|----------|--------|-------|
| D1 | Packaging | One combined 2-module feature | M1 = N27+N26+N19 (visibility theme); M2 = N20→N22, N25, N6, N8 + verification task. Transition live-exercises M1's own theme. |
| D2 | N27 approach | **Archive-aware inputs** (not transition-time snapshots, not hybrid) | Evidence already on disk (move :225, copy2 :249). Zero new state/schema. Follows N4/N10 precedent. Decisive: Check 9 verdicts depend on git state that keeps moving after transition — snapshots of verdicts go stale; snapshots of raw timestamps just rebuild the archived log. |
| D3 | Check 7 mechanics | `_review_tiers_per_task` additionally globs `archive-*/` for both patterns; dedupe by task id per review type, **live dir takes precedence** over archives | Live-wins handles post-transition re-reviews without double-count. Task ids are globally unique across modules, so archives can't collide with each other. |
| D4 | Check 9 mechanics | Merge dispatch timestamps from all `archive-*/.dispatch-log` files (module order) then the live log; later entries overwrite same task id | Preserves current latest-wins re-dispatch semantics. Side effect: archived modules' last windows get closed by the next module's first dispatch instead of running open-ended. |
| D5 | Archive-awareness inventory | Documented list expands from 3 lookups to 5 | CLAUDE.md + customization manifest updated: N4's two checkpoint lookups + N10's hook Check 5 + N27's Check 7 glob + Check 9 log merge. Every other glob stays intentionally flat. |
| D6 | N25(a) fix shape | **Feature-window fallback**: when the selected base ref's merge-base == HEAD, changeset base = parent of the first commit touching `paths.feature_dir`; no anchor resolvable → current FAIL behavior with a detail message naming the on-main case | Anchor always exists by implementation time (spec/plan committed first). Fail-closed preserved: a stale pre-existing test file outside the feature window still FAILs. |
| D7 | N25 scope | Sub-items (a),(b),(c),(d),(f) in; (e),(g) deferred | (b) line-anchored `---` frontmatter scan fixed in BOTH `_integration_test_paths` and `_task_ids_where` (same inherited bug); (c) module-level `_git_run` SSOT replaces the three near-identical wrappers; (d) directory-as-path detail says "is a directory, not a file"; (f) malformed-declaration messages name the source plan file. |
| D8 | N22 fix shape | Stem-style patterns (`auth\w*`, `migrat\w*`, `rout(e\|er)\w*`, `cach\w*`, `middleware\w*`, `cors\b`, `securit\w*`) + scan `_unfenced_content(content)` | Ordered AFTER N20 (the scan consumes the fence helper). Advisory-only semantics unchanged. |
| D9 | N26(a) log shape | Hook classifier gains a fix-dispatch stage: implementer-pattern dispatch whose description matches a fix/remediation pattern with a derivable task number logs `task=N type=fix`; reviewer re-dispatches append repeat `type={spec\|quality\|partner}-review` entries (idempotent append, duplicates fine) | Provenance greps are substring-based (`task=N type=spec-review`), so extra entries are backward-compatible. Exact regex left to plan. |
| D10 | N26(b) fix shape | Check 3b allowed-prefix list gains the gate-required artifact names: `honesty-check-*`, `execution-trace-audit.md`, `final-code-review.md` | `checkpoint-pre-completion.json` already exempt as `.json`. Closes the latent post-gate fix-dispatch block hit live in sprint 3 (`fix-n18-*`). |
| D11 | N19 fix shape | Transition adopts the hook's stricter semantic: use `module.file` only when set AND the file exists; otherwise fall back to the main plan. Same pass removes the dead `verif_ids = set()` initializer and replaces line-number comment refs with construct names | SET-but-missing now falls back (matches hook) instead of yielding an empty exemption set. |
| D12 | N20 fix shape | Keep blank-to-EOF for unclosed fences (CommonMark: unclosed code block runs to end of document) + add tilde-fence (`~~~`) support + characterization tests; add an advisory `validate-plan.py` WARNING when an unclosed fence is detected | The `all_tasks_have_reports` fail-open is mitigated at the source: authors get warned at plan time that the tail of their file is fence-shadowed. |
| D13 | N6 fix shape | Apply the C6(a) treatment to SDD SKILL.md §282–286 (pre-dispatch checkpoint / Check 5c), §286/Check-6b (context summary), §426–428 (report validation / Check 4b) | Word-count-aware: C6(a) reduced the count; this pass must too (re-check `wc -w` against the 5000 hard limit before commit). |
| D14 | N8 fix shape | F6 keys on a structural signal (presence of a "Direct entry"-style heading/section) instead of the literal phrases `"invoked directly"`/`"skipping brainstorming"` | New check verified green against all 15 current skills before merge. |
| D15 | N28(c) fold-in | Hoist the duplicated `_load_script` importlib loader into `sdd_test_helpers.py` | Free fold-in: sprint-4 tests touch both duplicating files anyway. Rest of N28 stays deferred. |
| D16 | Verification task | Non-last, Module 2: "archive-awareness inventory audit" — grep-audit that exactly the 5 documented lookups are archive-aware, code vs CLAUDE.md/manifest, zero writes | Placed in Module 2 so its dispatch entry is in the LIVE log at pre-completion (main's pre-fix Check 9 can see it — see §6 hazards). Exercises N16 report path + hook review-skip live. |
| D17 | Workspace | Worktree **required** (`.worktrees/sdd-aggregate-gate-visibility/`) | The feature edits the very scripts that gate it; live enforcement resolves to the main checkout via `~/.claude/skills/superpowers` symlinks. |
| D18 | Hook baseline | N26 edits `sdd-pre-dispatch-hook.sh` → re-capture `tests/ARaymond-hook-baseline/baseline.txt` in the SAME commit | Per the migrations+code rule (N15 lesson). |
| D19 | Plan declares `integration_test` | `path: tests/integration/sdd-e2e-test.sh` | The new e2e step modifies this file → in changeset → Check 10 PASS. Also silences the risk-surface WARNING the plan would otherwise self-trigger by quoting N22's keywords (advisory, but declaring is honest here: the e2e step IS the integration test). |
| D20 | Source Contracts / Task 0 | `Source Contracts: None`; Pattern References instead; no Task 0 | No external contracts. N7 (merged) makes `None` valid-absent → pre-execution OK; the no-Task-0 start is covered by N3a (hook) + N18 (checkpoint), both on main. |

## 4. Component Specifications

### 4.1 N27 — Check 7 archive-aware review-tier inputs (`controller-checkpoint.py`)

`_review_tiers_per_task(reports_dir, review_type)` (currently :200) gains archive awareness:

- Glob `reports_dir/task-*-quality-review*.md` (and partner equivalents) AND
  `reports_dir/archive-*/` with the same basename patterns.
- Build the result keyed by task id per review type. When the same task id appears in both the
  live dir and an archive, the **live** entry wins (D3). Minimum-vs-full classification per file
  stays basename-driven (existing `-minimum-tier` suffix logic unchanged).
- Check 7's ratio logic (:1466–1498) is unchanged — only its input widens. The `declared_min`
  exclusion already aggregates across all plan files via `_task_ids_where`.

**Failing-test-first fixture**: a manifest-mode workspace where an archived module's reviews are
ALL minimum-tier (undeclared) and the live module's are full — today the ratio PASSes (blind);
post-fix it FAILs (>50%).

### 4.2 N27 — Check 9 archive-aware dispatch-log merge (`controller-checkpoint.py`)

`_check_verification_git_reality` (currently :305) reads from a merged timestamp map:

- A new helper collects dispatch lines from `reports_dir/archive-*/.dispatch-log` (lexicographic
  archive order — archives are created in module order) followed by the live dispatch log,
  parsing with the existing format regex (:324). Later lines overwrite earlier per task id (D4).
- Window computation over the merged, sorted task set is otherwise unchanged.
- The silent `continue` for tasks absent from the map (:334) remains — but after the merge,
  archived-module verification tasks are present, so the fail-open class is closed.

**Failing-test-first fixture**: a verification task whose implementer dispatch lives only in an
archived log, with a file-modifying commit inside its window — today silently skipped; post-fix
FAILs `verification_git_reality`.

### 4.3 N26 — dispatch-log classification + Check 3b allowlist (`sdd-pre-dispatch-hook.sh`)

- **(a)** New classification outcome between the reviewer and implementer stages: a dispatch
  matching the implementer pattern whose description matches a fix/remediation pattern AND
  carries a derivable task number logs `<ISO> DISPATCH fix task=N type=fix` and is then enforced
  exactly as an implementer dispatch (no gate relaxation — only the log line is new). Reviewer
  re-dispatches already pass the reviewer stage; they now ALWAYS append their entry even when an
  identical entry exists (idempotent append; provenance greps are substring-based and unaffected
  by duplicates).
- **(b)** Check 3b's allowed-prefix list gains `honesty-check-`, `execution-trace-audit.md`,
  `final-code-review.md` (D10).
- Hook edit ⇒ baseline re-capture in the same commit (D18).

### 4.4 N19 — transition `module.file` semantics (`transition-module.py`)

In `validate_module_completion`: use the completing module's `module.file` only when it is set
AND exists on disk (the hook's `-n` + `-f` semantic); otherwise fall back to the main plan file
for verification-id lookup. Remove the dead `verif_ids = set()` initializer; replace
"hook lines ~294-299"-style comments with construct names.

### 4.5 N25 — Check 10 follow-up batch (`controller-checkpoint.py`)

- **(a)** After base-ref selection, if `merge-base(base, HEAD) == HEAD` (on-base-branch: SDD on
  main, remoteless repo), recompute the changeset with base = parent of the first commit
  touching `paths.feature_dir` (`git log --reverse --format=%H -- <feature_dir>` → first hash,
  `^` parent; root-commit edge: use the empty tree). If no commit touches the feature dir yet,
  keep the current changeset (untracked-only) and, on FAIL, emit a detail that names the
  on-main case and the feature-window rule.
- **(b)** Frontmatter close-delimiter scan becomes line-anchored (regex on `^---$` after the
  opening line) in `_integration_test_paths` AND `_task_ids_where`.
- **(c)** One module-level `_git_run(args, cwd, timeout)` helper replaces the three
  near-identical subprocess wrappers.
- **(d)** A declared path that exists but `is_dir()` FAILs with "is a directory, not a file"
  (currently misleading "missing on disk").
- **(f)** Malformed-declaration FAIL messages name the source plan file.

**Failing-test-first fixture for (a)**: remoteless repo, work committed directly on `main`,
integration test committed within the feature window — today Check 10 FAILs (invisible);
post-fix PASSes. Counter-fixture: a tracked file predating the feature window still FAILs.

### 4.6 N22 — risk-surface scan calibration (`validate-plan.py`)

`_C2_RISK_PATTERNS` move to stem-style regexes (D8) and the scan input becomes
`_unfenced_content(content)`. Fixtures: `migrations`/`caches`/`routers`/`authentication` now
match; a plan whose ONLY risk keywords sit inside code fences no longer warns. Ordered after
N20 in the plan.

### 4.7 N20 — fence-helper edge cases (`_report_utils.py`)

`_unfenced_content` recognizes `~~~` fences as fence delimiters (same nesting rules as
backticks; a fence closes only on its own marker type). Unclosed-fence-at-EOF keeps the
blank-to-EOF behavior (CommonMark-consistent, D12) with a characterization test pinning it.
`validate-plan.py` adds an advisory WARNING when a plan ends inside an unclosed fence.

### 4.8 N6 — "hook enforces this" framing pass (SDD `SKILL.md`)

Doc-only. Apply the C6(a) treatment to the three remaining manual-prescription sites (D13):
state the hook/gate enforces the step automatically, manual runs are an optional early check.
Net word count must not increase (verify `wc -w` pre/post; 5000 hard limit).

### 4.9 N8 — intent-based F6 check (`validate-all-skills.py`)

F6 asserts the presence of a structural "Direct entry" signal (heading match, exact form chosen
at plan time) instead of two literal phrases. Run the suite to verify all 15 skills pass with
the new check; if a skill legitimately lacks the section, fix the skill (not the check) in the
same task.

### 4.10 Verification task — archive-awareness inventory audit (Module 2, non-last)

`task_type: verification`. Grep-audit that the archive-aware lookup inventory in CLAUDE.md and
`docs/ARaymond-customization-manifest.md` matches the code (exactly 5 sites post-N27, D5). Zero
file writes; report validates via the N16 path with empty `files_changed`.

## 5. Module Structure

| Module | Items | Files (primary) |
|---|---|---|
| **module-1-aggregate-visibility** | N27 (Check 7), N27 (Check 9), N26(a)+(b)+baseline, N19 | `controller-checkpoint.py`, `sdd-pre-dispatch-hook.sh`, `transition-module.py`, baseline.txt |
| **module-2-calibration** | N20 → N22, N25, N6, N8, verification task, e2e step + docs pass | `_report_utils.py`, `validate-plan.py`, `controller-checkpoint.py`, SDD `SKILL.md`, `validate-all-skills.py`, `sdd-e2e-test.sh`, CLAUDE.md |

Module 1 completes and transitions via `transition-module.py` before Module 2 begins. Within
Module 2, N20 precedes N22 (dependency, D8). The verification task sits mid-module (non-last,
D16). Standard enforcement tier.

## 6. Self-Hosting Hazards (pre-logged)

Live enforcement during this run resolves to **main's** (pre-fix) scripts via the
`~/.claude/skills/superpowers` symlinks:

1. **This run's own pre-completion Check 7/9 are still blind to Module-1 archives.** Not
   blocking — blindness narrows the denominator to Module-2 evidence (same as sprint 3).
   Pre-log as an accepted deviation; the fix first protects the NEXT multi-module run. The new
   e2e step is the in-sprint proof.
2. **The plan will quote risk-surface keywords** (N22's own pattern list) → main's raw-content
   scan self-WARNs. Advisory-only; D19's `integration_test` declaration is the honest mitigation.
3. **Check 9 visibility for the verification task** depends on its dispatch entry being in the
   live log at pre-completion — guaranteed by placing it in Module 2 (D16).
4. N7/N3a/N18/N16 are all on main → the sprint-3 hazards (Source Contracts None, no-Task-0
   start, verification report rejection) do NOT recur.

## 7. Error Handling

- All new file reads (archived logs, archived review globs) tolerate absence: a workspace with
  no archives behaves byte-identically to today (single-module runs unaffected).
- `_git_run` (N25c) preserves the existing timeout/OSError swallowing semantics of the wrappers
  it replaces; Check 10's fail-closed posture is unchanged.
- Malformed archived dispatch-log lines are skipped by the existing regex (no new parse errors).

## 8. Testing

- **TDD obligations** (failing test first): N27 Check 7 fixture (§4.1), N27 Check 9 fixture
  (§4.2), N25(a) on-main fixture + counter-fixture (§4.5), N20 unclosed-fence/tilde fixtures
  (§4.7).
- **Unit**: new/extended tests in `test_pre_completion_gates.py`, `test_c2_integration_gate.py`,
  `test_fence_aware_parsing.py`, `test_sdd_classification.py` (N26), `test_transition_module.py`
  (N19). `_load_script` hoisted to `sdd_test_helpers.py` (D15).
- **Integration**: new e2e step — after a transition, run pre-completion and assert Check 7
  counts archived reviews and Check 9 sees an archived-module verification window. This is the
  N27 live proof (mirrors C2's Step 11 pattern).
- **Static**: `validate-all-skills.py` (N8's own change — all 15 skills green),
  `verify-symlink-install.sh`, hook-baseline check (re-captured per D18).
- **Suites to run before completion**: unit (pytest), regression, install, e2e.

## 9. Acceptance Criteria

- [ ] Check 7 FAILs on the archived-minimum-tier fixture; PASSes unchanged on single-module
      workspaces.
- [ ] Check 9 FAILs on the archived-window file-modification fixture; silent-skip class closed.
- [ ] Fix dispatches and re-reviews produce dispatch-log entries; `fix-n18-*`-style post-gate
      dispatch names no longer trip Check 3b.
- [ ] Check 10 PASSes for a committed integration test in an on-main remoteless feature window;
      still FAILs for pre-window files and malformed declarations.
- [ ] Risk-surface WARNING matches inflected keyword forms and ignores fenced quotes.
- [ ] `_unfenced_content` handles tilde fences; unclosed-fence behavior pinned; validate-plan
      WARNs on unclosed fences.
- [ ] SDD SKILL.md framing pass lands with net word count ≤ current; regression suite green.
- [ ] F6 is intent-based and green across all 15 skills.
- [ ] Sprint executed as 2 modules with a live transition AND a non-last verification task whose
      report validates (Track 3 closed).
- [ ] Archive-awareness inventory (5 sites) consistent across code, CLAUDE.md, manifest —
      verified by the verification task.
- [ ] Hook baseline re-captured in the same commit as the hook edit.
- [ ] All four suites green; BACKLOG rows N19/N20/N22/N25(a–d,f)/N26/N27/N6/N8 flipped with
      commit refs; N25(e,g) + N21/N23/N24/N28(a,b,d) remain open with a pointer to this feature.

## 10. Sources

- `docs/process-improvement-findings/BACKLOG.md` — rows N19, N20, N22, N25, N26, N27, N6, N8.
- `docs/imp-plans/2026-06-05-sdd-cleanup-and-integration-gate/` — sprint-3 final review
  (N27 provenance), trace audit (N26 provenance), deviations.
- Prior-session feedback (2026-06-10): live verification exercise pending; N27 meatiest;
  `writing-plans/SKILL.md` ~273-word headroom (no edits planned there this sprint; if N25(a)
  needs a doc sentence it stays under ~50 words or pairs with a `references/` extraction).
- `controller-checkpoint.py` :200, :305, :1466–1576 (read 2026-06-10);
  `transition-module.py` :218–250 (read 2026-06-10).
