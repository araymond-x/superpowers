# SDD Aggregate-Gate Visibility — Distilled Implementation Spec

> **Source**: `docs/imp-plans/2026-06-10-sdd-aggregate-gate-visibility/spec.md` (20 decisions)
> **Distilled**: 2026-06-11
> **For**: Plan writer and implementation agents ONLY. For full context, see source.

## Contract Facts

- **Dispatch-log line formats** (`reports/.dispatch-log`): existing `<ISO> DISPATCH implementer task=N type=implementer`; new `<ISO> DISPATCH fix task=N type=fix`; new `<ISO> DISPATCH adhoc type=fix-unattributed` (no `task=`); repeat review entries reuse `task=N type={spec|quality|partner}-review`.
- **Check 9 parser matches ONLY `type=implementer` lines** (regex at controller-checkpoint.py:324). `type=fix` / `type=fix-unattributed` lines must never open or move a verification window. A marked fix dispatch emits ONLY the Stage-0 `type=fix` line — it skips Stage 2's implementer log write; fixtures assert the ABSENCE of a `type=implementer` line for it.
- **Marker grammar** (dispatch descriptions): `[task N fix]` and `[task N re-review:{spec|quality|partner}]`.
- **Archive layout** (written by `transition-module.py`): review reports MOVED to `reports/archive-<module>/`; dispatch log COPIED to `reports/archive-<module>/.dispatch-log` then live log truncated. Archives are created in module order; lexicographic glob order matches module order.
- **Check 7 dedupe**: keyed by task id per review type; live dir takes precedence over archives. Invariant: task ids are globally unique across modules, so archive-vs-archive collisions cannot occur. Ratio threshold (>0.5 FAIL) and `declared_min` exclusion unchanged.
- **Check 9 merge order**: `archive-*/.dispatch-log` files (lexicographic) then live log; later lines overwrite earlier per task id.
- **N25(a) trigger**: `merge-base(selected_base, HEAD) == HEAD` → recompute changeset with base = parent of first commit touching `paths.feature_dir` (`git log --reverse --format=%H -- <feature_dir>`, first hash, `^` parent; root commit → empty tree). No commit touches the feature dir → keep current changeset (untracked-only); FAIL detail names the on-main case and the feature-window rule. Gate stays fail-closed: pre-window tracked files still FAIL.
- **Check 3b allowlist additions**: `honesty-check-`, `execution-trace-audit.md`, `final-code-review.md`. Check 3b scans `*.md` only (`checkpoint-pre-completion.json` already exempt).
- **N22 stem patterns**: `auth\w*`, `migrat\w*`, `rout(e|er)\w*`, `cach\w*`, `middleware\w*`, `cors\b`, `securit\w*`; scan input = `_unfenced_content(content)`.
- **N20 fence semantics**: `~~~` recognized as fence delimiter; a fence closes only on its own marker type; unclosed fence at EOF blanks to EOF (pinned by characterization test); `validate-plan.py` emits an advisory WARNING when a plan ends inside an unclosed fence.
- **F6 scope**: `validate-all-skills.py` F6 checks ONLY `writing-plans/SKILL.md`. No other skill gains a "Direct entry" section.
- **Word ceilings**: SDD SKILL.md hard limit 5000 words (verify `wc -w` pre/post for N6 — net count must not increase); `writing-plans/SKILL.md` ~273 words headroom (F6 heading adjustment and any N25(a) doc sentence must fit or pair with a `references/` extraction).
- **Archive-aware lookup inventory**: exactly 5 sites post-N27 (N4's two checkpoint report lookups, N10's hook Check 5 Task-0 lookup, N27's Check 7 glob, N27's Check 9 log merge). Every other glob stays intentionally flat. CLAUDE.md + customization manifest must state 5.
- **Plan frontmatter for this feature**: `enforcement_tier: standard`, `entry_mode: brainstorming`, `integration_test: {path: tests/integration/sdd-e2e-test.sh}`, 2 modules. `Source Contracts: None`; Pattern References; no Task 0.
- **Workspace**: worktree REQUIRED at `.worktrees/sdd-aggregate-gate-visibility/` (live enforcement resolves to the main checkout via symlinks).
- **Hook baseline**: any `sdd-pre-dispatch-hook.sh` edit re-captures `tests/ARaymond-hook-baseline/baseline.txt` in the SAME commit.

## Open Decisions

| # | Decision | Options | Resolution Required By |
|---|----------|---------|----------------------|
| O1 | Exact Stage-0 marker regex | Any regex matching the marker grammar above | Plan writer |
| O2 | Exact Stage-3 fix-heuristic regex | Baseline `\bfix\b|remediat` | Plan writer |
| O3 | Exact F6 structural heading form | Heading text in writing-plans/SKILL.md | Plan writer |
| O4 | `_git_run` in-scope set | All four sites (controller-checkpoint.py ~:353, :456, :507, :703) audited; any exclusion justified in plan | Plan writer |

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| D1 | Packaging | One 2-module feature: M1 = N27+N26+N19; M2 = N20→N22, N25, N6, N8 + verification task |
| D2 | N27 approach | Archive-aware inputs; no new state or schema |
| D3 | Check 7 mechanics | Glob `archive-*/` for both review patterns; dedupe per task id, live wins |
| D4 | Check 9 mechanics | Merge archived logs (module order) + live log; later lines overwrite per task id |
| D5 | Archive-awareness inventory | Documented list expands 3 → 5 sites |
| D6 | N25(a) fix shape | Feature-window fallback (see Contract Facts); fail-closed preserved |
| D7 | N25 scope | Sub-items (a),(b),(c),(d),(f) in; (e),(g) deferred |
| D8 | N22 fix shape | Stem patterns + unfenced scan; ordered AFTER N20 |
| D9 | N26(a) log shape | Stage-0 structured marker (before reviewer detection) + Stage-3 unattributed fallback |
| D10 | N26(b) fix shape | Check 3b allowlist gains the three gate-required artifact names |
| D11 | N19 fix shape | Transition uses `module.file` only when set AND exists; else main-plan fallback; dead initializer + comment-rot cleanup |
| D12 | N20 fix shape | Tilde fences + blank-to-EOF pinned + validate-plan advisory WARNING |
| D13 | N6 fix shape | Hook-enforces-this framing at SDD SKILL.md §282–286, §286/Check-6b, §426–428; net words ≤ current |
| D14 | N8 fix shape | F6 structural-signal check; scope stays writing-plans/SKILL.md only |
| D15 | N28(c) fold-in | Hoist `_load_script` into `sdd_test_helpers.py` |
| D16 | Verification task | Non-last, Module 2: archive-awareness inventory audit (grep-only, zero writes) |
| D17 | Workspace | Worktree required |
| D18 | Hook baseline | Re-capture in same commit as hook edit |
| D19 | Plan `integration_test` | `path: tests/integration/sdd-e2e-test.sh` |
| D20 | Source Contracts / Task 0 | None / no Task 0; Pattern References |

## Component Specifications

### Check 7 archive-aware inputs (`controller-checkpoint.py`, N27)
`_review_tiers_per_task(reports_dir, review_type)` (:200) additionally globs `reports_dir/archive-*/` with the same basename patterns for quality and partner reviews. Result keyed by task id per review type; live entry wins on collision. Minimum-vs-full classification stays basename-driven (`-minimum-tier` suffix). Check 7 ratio logic (:1466–1498) unchanged. Failing-test-first fixture: archived module all undeclared-minimum + live module full → today PASS (blind), post-fix FAIL (>50%).

### Check 9 archive-aware merge (`controller-checkpoint.py`, N27)
New helper feeds `_check_verification_git_reality` (:305) a timestamp map merged per Contract Facts. Silent `continue` for absent tasks (:334) remains; archived-module verification tasks are now present in the map. Window computation otherwise unchanged. Failing-test-first fixture: verification task dispatched only in an archived log + file-modifying commit inside its window → today silently skipped, post-fix FAILs `verification_git_reality`.

### Dispatch-log classification (`sdd-pre-dispatch-hook.sh`, N26a)
Stage 0 runs BEFORE Stage-1 reviewer detection (fix-review descriptions contain "review" and would otherwise be consumed by Stage 1). Marker match → log per Contract Facts; marked fix then takes implementer enforcement WITHOUT Stage 2's log write; marked re-review takes reviewer passthrough. Markerless fix-heuristic dispatches reaching Stage-3 passthrough log `type=fix-unattributed`; no enforcement change. Controller-side: marker convention documented where dispatch guidance lives (SDD SKILL.md or its `references/`, word-ceiling aware) and echoed in the hook's `additionalContext` injection. Fixtures replay the three live sprint-3 trace-audit shapes (items 2/4): with markers → fully attributed; without → at minimum the `fix-unattributed` line for the fix-implementer shape; reviewer-stage behavior for the other two shapes unchanged.

### Check 3b allowlist (`sdd-pre-dispatch-hook.sh`, N26b)
Add the three gate-required artifact names per Contract Facts.

### Transition `module.file` semantics (`transition-module.py`, N19)
`validate_module_completion`: use completing module's `module.file` only when set AND the file exists; else fall back to the main plan for verification-id lookup. Remove dead `verif_ids = set()` initializer; replace line-number comment refs with construct names.

### Check 10 batch (`controller-checkpoint.py`, N25)
(a) Feature-window fallback per Contract Facts; failing-test-first fixture: remoteless on-main repo with integration test committed in the feature window → today FAIL, post-fix PASS; counter-fixture: tracked file predating the window still FAILs. (b) Frontmatter close-delimiter scan line-anchored (`^---$`) in BOTH `_integration_test_paths` and `_task_ids_where`. (c) `_git_run(args, cwd, timeout)` consolidation per O4, preserving existing timeout/OSError-swallowing semantics. (d) Existing-but-directory declared path FAILs with "is a directory, not a file". (f) Malformed-declaration FAIL messages name the source plan file.

### Risk-surface calibration (`validate-plan.py`, N22)
`_C2_RISK_PATTERNS` → stem patterns per Contract Facts; scan `_unfenced_content(content)`. Fixtures: `migrations`/`caches`/`routers`/`authentication` match; fence-only keywords do not warn.

### Fence helper (`_report_utils.py`, N20)
Per Contract Facts. Characterization tests for tilde fences and unclosed-at-EOF.

### SDD SKILL.md framing pass (N6)
State the hook/gate enforces the step automatically at the three sites in D13; manual runs optional. Net word count must not increase.

### F6 intent check (`validate-all-skills.py`, N8)
Structural "Direct entry" signal per O3 replaces the two literal phrases at ~:568. If the current writing-plans heading doesn't match, adjust the heading in the same task. Acceptance = full regression suite green.

### Verification task (Module 2, non-last, D16)
`task_type: verification`. Grep-audit: archive-aware inventory in CLAUDE.md + `docs/ARaymond-customization-manifest.md` matches code (exactly 5 sites). Zero writes; report validates with empty `files_changed`.

### Tests & integration
TDD obligations: N27 Check 7 fixture, N27 Check 9 fixture, N25(a) fixture + counter-fixture, N20 fixtures. Unit homes: `test_pre_completion_gates.py`, `test_c2_integration_gate.py`, `test_fence_aware_parsing.py`, `test_sdd_classification.py`, `test_transition_module.py`; `_load_script` hoisted to `sdd_test_helpers.py` (D15). New e2e step: after a transition, pre-completion asserts Check 7 counts archived reviews AND Check 9 sees an archived-module verification window. Suites before completion: unit, regression, install, e2e.

### Error handling
Absent archives → behavior byte-identical to today (single-module unaffected). Malformed archived log lines skipped by the existing regex. Check 10 stays fail-closed.

### Self-hosting hazards (pre-log as deviations)
(1) This run's own pre-completion Check 7/9 run MAIN's pre-fix scripts → still blind to Module-1 archives; not blocking; e2e step is the in-sprint proof. (2) Plan text quoting risk keywords self-WARNs on main's raw-content scan; advisory; D19 declaration is the mitigation. (3) Verification task must sit in Module 2 so its dispatch entry is in the live log at pre-completion. (4) N7/N3a/N18/N16 are on main → sprint-3 hazards do not recur.

## Acceptance Criteria

- [ ] Check 7 FAILs on the archived-minimum-tier fixture; single-module workspaces unchanged.
- [ ] Check 9 FAILs on the archived-window file-modification fixture; silent-skip class closed.
- [ ] Three live fix-cycle shapes WITH markers → fully attributed log entries; markerless fix → `fix-unattributed` line; marked fix emits NO `type=implementer` line; `fix-n18-*`-style names no longer trip Check 3b.
- [ ] Check 10 PASSes for a committed integration test in an on-main remoteless feature window; still FAILs pre-window files and malformed declarations.
- [ ] Risk-surface WARNING matches inflected forms; ignores fence-only keywords.
- [ ] `_unfenced_content` handles tilde fences; unclosed-fence behavior pinned; validate-plan WARNs on unclosed fence.
- [ ] N6 lands with net SDD SKILL.md word count ≤ current; regression suite green.
- [ ] F6 intent-based, scoped to writing-plans/SKILL.md; full regression suite green.
- [ ] Sprint executed as 2 modules with a live transition AND a non-last verification task whose report validates.
- [ ] Archive-awareness inventory (5 sites) consistent across code, CLAUDE.md, manifest — verified by the verification task.
- [ ] Hook baseline re-captured in the same commit as the hook edit.
- [ ] All four suites green; BACKLOG rows N19/N20/N22/N25(a–d,f)/N26/N27/N6/N8 flipped with commit refs; N25(e,g) + N21/N23/N24/N28(a,b,d) remain open with a pointer to this feature.
