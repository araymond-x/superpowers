# Plan Review Report — cmux-integration (repo-3 superpowers)

**Reviewer:** general-purpose plan-document-reviewer (model: sonnet), dispatched 2026-07-23
**Plan set:** `plan.md` + `module-1-spawn-script.md` + `module-2-protocol-e2e-docs.md`
**Spec:** `spec-distilled.md` (primary), `spec.md` (full)

## Verdict

**Status: APPROVED** (initial review found 1 blocking issue; it was fixed and the reviewer re-confirmed APPROVED — "No remaining gaps. This was the sole blocking issue; with it closed, the plan is ready for implementation." The re-check also verified the empty-argv path stays valid and there is no temp-file leak.)

The reviewer read all three plan files, both specs, `claude-codex-handoff` (`repo_identity()`/`evaluate_target_guard()`), `claude-usage-pace`, the current `context-handoff-protocol.md`, `sdd-e2e-test.sh`, and `test_context_gate_tier.py`; ran live `cmux new-workspace --help` / `cmux notify --help` / `cmux ping`; and confirmed `sdd-pre-dispatch-hook.sh:840` points at the protocol doc. Everything except one narrow correctness gap verified clean.

## Blocking Issue (RESOLVED)

**[CORRECTNESS] Module 1, Task 4, Step 2 — `ARGS_OK` only checked the `v1:` prefix, not decode success.**

A `v1:`-prefixed but corrupt-body `CLAUDE_CODE_PICKER_ARGS` produced an empty `FORWARDED` array while `ARGS_OK` stayed `1`, so `preflight_ok()` still qualified for `launch=auto` — silently dropping the user's forwarded CLI args instead of degrading to `launch=picker-manual`. This contradicted the pinned auto-preflight condition "ARGS v1-decodes OR absent" ("decodes" = succeeds, not merely prefix present).

**Fix applied (module-1 Task 4 Step 2 + Task 5 Step 1):**
- The decode python now `sys.exit(3)` on any base64/JSON/type failure and writes each argv element NUL-*terminated* (not NUL-joined) to a temp file.
- Bash sets `ARGS_OK=0` when the decode exits non-zero → `preflight_ok()` fails → `launch=picker-manual`.
- This also fixed a latent last-element-drop in the old `"\0".join(argv)` + `read -d ''` pattern (the final element lacked a terminator).
- Added `test_corrupt_v1_body_degrades_to_picker_manual` (Task 5) asserting `args_b64="v1:!!!not-base64!!!"` → `launch=picker-manual`.

## Snippet Verification (from reviewer)

- `validate_bundle()` (Task 2) — **VERIFIED.** Field paths `session.bundle_type`, `session.entry_skill`, `project.repo_id` match `create_manifest()` exactly; the worktree-invariant identity (`git rev-parse --git-common-dir` → realpath) is a faithful port of `repo_identity()`; the realpath-containment check defeats `..` traversal even though the id regex alone would permit it.
- v1-codec decode (Task 4) — **MISMATCH → fixed** (see above). Security posture otherwise sound (NUL-delimited capture, per-token `shlex.quote`, no eval).
- `check_quota()` (Task 3) — **VERIFIED** against live `claude-usage-pace`: `--json --no-log` exist; shape `{"windows":[{"key":...,"remaining_pct":...}]}`; all fail-open classes resolve to `unchecked` in bash and matching fixtures.
- Label rule (Task 4) — **VERIFIED.** All 4 parametrized cases + 255-boundary traced against the regex/truncation code; matches Decision 18.

## Cross-Document Audit (from reviewer)

- `project.repo_id`: source=`str` worktree-invariant realpath of git-common-dir → spec worktree-invariant → plan identical inline python — **MATCH** (confirmed against a real on-disk bundle: `repo_id` points at the main repo `.git`, not the worktree).
- `session.bundle_type`: source=`str` (`work|review`) → spec → plan `.get("session") or {}).get("bundle_type","")` — **MATCH.**
- `windows[key=="session"].remaining_pct`: source=`float` → spec → plan identical filter+key — **MATCH.**

## Verified-Clean (from reviewer)

Cross-repo scope discipline (Decision 19 — no repo-1/repo-2 file writes; repo-2 checklist has no frontmatter `tasks:` so it can't leak into `plan-manifest.txt`); SP_HOP definition-before-use across Tasks 2/4/5/6; reservation-before-spawn sequencing; Task 7's "replace this exact block" text byte-matches the live protocol doc with steps 1–2 untouched; e2e Step 14 insertion point + banner bump; live-confirmed `cmux new-workspace`/`notify` exact-argv; and `review_tier: minimum` on Task 9 (parent-only frontmatter) is correctly picked up by `_load_all_plan_contents()` despite module files having no frontmatter.

## Advisory Recommendations (non-blocking)

- Module 1 Task 1's precondition order runs the `.active-feature`-missing check before clean-tree, while the terse Contract Facts bullet lists clean-tree first — internally consistent with Module 1's Acceptance Criteria; a one-line note would clarify.
- The "picker-sanitizer-stable" label round-trip can't be verified until repo-1 lands; already gated by Task 0's cross-repo dependency check. Double-check repo-1's actual sanitizer regex matches `[^A-Za-z0-9_.-]` once it lands.

## Automated validation

`validate-plan.py`: all three files PASS (WARNING-only; zero FAIL/blockers). All tasks ≤200 lines. `validators.py plan` (Pydantic): parent frontmatter valid (exit 0).
