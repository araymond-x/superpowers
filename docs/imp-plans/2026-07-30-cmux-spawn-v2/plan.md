---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: "docs/imp-plans/2026-07-30-cmux-spawn-v2/spec-distilled.md"
shared_constants:
  - path: "TIER_PROFILES from skills/scripts/models/sdd_session.py"
    value: "micro|standard"
    reason: "expected_hops formula branches on tier (micro=1); Tasks 6, 8"
  - path: "REQUIRED_SECTIONS from skills/subagent-driven-development/scripts/_report_utils.py"
    value: "5 prose sections"
    reason: "Mechanics-card report skeleton must emit these sections, imported not retyped; Task 12"
  - path: "EXPECTED_BUNDLE_TYPE / EXPECTED_ENTRY_SKILL from spawn-handoff-session.sh"
    value: "work / superpowers:subagent-driven-development"
    reason: "Bundle validation constants stay the SSOT in the script; Tasks 8-13 must not redefine"
  - path: "HOP_DIVISOR / CEILING_FLOOR / CEILING_FACTOR from skills/subagent-driven-development/scripts/_handoff_support.py"
    value: "2.5 / 6 / 2"
    reason: "Decision 9 formula constants live ONLY in _handoff_support.py (created Task 6); spawn script and materialize-manifest.py both consume them via that module"
  - path: "env SUPERPOWERS_CMUX_MAX_STALL_HOPS"
    value: "1"
    reason: "Stall-refusal threshold default; Task 8 + protocol doc (Task 16)"
  - path: "env SUPERPOWERS_CMUX_POST_SPAWN"
    value: "rename,rc"
    reason: "Post-spawn step list default; Task 11 + protocol doc (Task 16)"
pattern_references:
  - name: "spawn-script-layer-style"
    source_files: ["skills/subagent-driven-development/scripts/spawn-handoff-session.sh"]
    reason: "House style for the script under rework: layer comments, validate-warn-revert env knobs, checked reservation writes, per-branch [spawn-handoff] message prefixes, no set -u/-e/pipefail, printf not echo, here-strings not pipe-into-grep -q"
  - name: "pytest-bash-stub-harness"
    source_files: ["tests/unit/spawn_handoff_helpers.py", "tests/unit/test_spawn_handoff.py"]
    reason: "How spawn-script behavior is unit-tested: run_spawn() driver, PATH stubs, ctx dict, _spawn_log_records/_recorded_argv helpers; extend this harness, do not build a second one"
  - name: "e2e-step-structure"
    source_files: ["tests/integration/sdd-e2e-test.sh"]
    reason: "e2e step layout: PROJECT from BASH_SOURCE, stub-on-PATH, subshell cd into fixture worktree, assert-first-on-load-bearing-mode, PASS echo per step, final banner"
  - name: "model-field-addition"
    source_files: ["skills/scripts/models/plan.py"]
    reason: "Precedent for adding optional fields to extra=forbid models without a schema bump: review_tier, task_type, integration_test all landed this way"
  - name: "manifest-materialization"
    source_files: ["skills/subagent-driven-development/scripts/materialize-manifest.py"]
    reason: "Frontmatter -> SddSession -> .sdd-session.json flow the handoff block must join; idempotent-write behavior to preserve"
  - name: "import-only-helper-ssot"
    source_files: ["skills/subagent-driven-development/scripts/_midpoint.py"]
    reason: "The fork's precedent for extracting a shared formula into an underscore module so two consumers cannot drift; _handoff_support.py follows it"
  - name: "stop-hook-systemmessage"
    source_files: ["skills/subagent-driven-development/scripts/sdd-stop-hook.sh"]
    reason: "Stop hooks emit systemMessage (NOT hookSpecificOutput); jq-based payload parsing; always exit 0"
integration_test:
  path: tests/integration/sdd-e2e-test.sh
modules:
  - id: 1
    title: "Contracts, cold-start measurement, spikes"
    task_ids: [0, 1, 2, 3]
    file: module-1-contracts-spikes.md
  - id: 2
    title: "Models + hop-budget support layer"
    task_ids: [4, 5, 6, 7]
    file: module-2-models-budget.md
  - id: 3
    title: "Spawn script core rework"
    task_ids: [8, 9, 10, 11]
    file: module-3-spawn-script.md
  - id: 4
    title: "Mechanics card, hooks, compatibility, docs, e2e"
    task_ids: [12, 13, 14, 15, 16, 17, 18]
    file: module-4-card-hooks-docs.md
tasks:
  - id: 0
    title: "Contract verification + cold-start handshake measurement (BLOCKING)"
    module_id: 1
  - id: 1
    title: "SP2: workspace --env / --env-file probe + disposition"
    depends_on: [0]
    module_id: 1
    review_tier: minimum
  - id: 2
    title: "SP1: context-probe.py [task N fix] attribution root cause"
    depends_on: [0]
    module_id: 1
  - id: 3
    title: "SP3 + SP4 design docs + BACKLOG rows"
    depends_on: [0]
    module_id: 1
    review_tier: minimum
  - id: 4
    title: "plan.py: handoff_spawn field"
    depends_on: [0]
    module_id: 2
    pattern_references: ["model-field-addition"]
  - id: 5
    title: "sdd_session.py: optional handoff block"
    depends_on: [4]
    module_id: 2
    pattern_references: ["model-field-addition"]
  - id: 6
    title: "_handoff_support.py: expected_hops formula + derivation precedence; materialize-manifest.py writes the handoff block"
    depends_on: [5]
    module_id: 2
    shared_constants_used: ["TIER_PROFILES from skills/scripts/models/sdd_session.py", "HOP_DIVISOR / CEILING_FLOOR / CEILING_FACTOR from skills/subagent-driven-development/scripts/_handoff_support.py"]
    pattern_references: ["import-only-helper-ssot", "manifest-materialization"]
  - id: 7
    title: "_handoff_support.py: tasks_done counting + stall streak + CLI"
    depends_on: [6]
    module_id: 2
    pattern_references: ["import-only-helper-ssot"]
  - id: 8
    title: "Spawn script: policy gate, stall/ceiling rework, intent tasks_done"
    depends_on: [7]
    module_id: 3
    shared_constants_used: ["env SUPERPOWERS_CMUX_MAX_STALL_HOPS", "HOP_DIVISOR / CEILING_FLOOR / CEILING_FACTOR from skills/subagent-driven-development/scripts/_handoff_support.py", "EXPECTED_BUNDLE_TYPE / EXPECTED_ENTRY_SKILL from spawn-handoff-session.sh"]
    pattern_references: ["spawn-script-layer-style", "pytest-bash-stub-harness"]
  - id: 9
    title: "Spawn script: surface topology + shared launch wrapper + workspace fallback"
    depends_on: [8]
    module_id: 3
    pattern_references: ["spawn-script-layer-style", "pytest-bash-stub-harness"]
  - id: 10
    title: "Spawn script: wait-for handshake, re-wait, read-screen diagnosis"
    depends_on: [9]
    module_id: 3
    pattern_references: ["spawn-script-layer-style", "pytest-bash-stub-harness"]
  - id: 11
    title: "Spawn script: post-spawn setup (/rename, /rc) + knobs"
    depends_on: [10]
    module_id: 3
    shared_constants_used: ["env SUPERPOWERS_CMUX_POST_SPAWN"]
    pattern_references: ["spawn-script-layer-style", "pytest-bash-stub-harness"]
  - id: 12
    title: "write-mechanics-card.py + golden-file test"
    depends_on: [7]
    module_id: 4
    shared_constants_used: ["REQUIRED_SECTIONS from skills/subagent-driven-development/scripts/_report_utils.py"]
  - id: 13
    title: "Checked outcome writes (N63) + bookkeeping commit + card invocation"
    depends_on: [11, 12]
    module_id: 4
    pattern_references: ["spawn-script-layer-style", "pytest-bash-stub-harness"]
  - id: 14
    title: "Hooks trio: session-start signal, stop-hook spawn-outcome WARNING, Check 3b allowlist + one baseline re-capture"
    depends_on: [13]
    module_id: 4
    pattern_references: ["stop-hook-systemmessage"]
  - id: 15
    title: "Check 9 :(exclude) pathspec + both-direction tests"
    depends_on: [13]
    module_id: 4
  - id: 16
    title: "context-handoff-protocol.md rewrite"
    depends_on: [14]
    module_id: 4
  - id: 17
    title: "e2e Step 14 rewrite (surface topology + handshake + policy dial)"
    depends_on: [14, 15]
    module_id: 4
    pattern_references: ["e2e-step-structure"]
  - id: 18
    title: "Full-suite verification + banner counts"
    depends_on: [16, 17]
    module_id: 4
    task_type: verification
---

# cmux-spawn-v2 Implementation Plan (parent)

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Second-pass rework of the SDD auto-spawn handoff: the successor spawns as a **surface (top tab) in the caller's cmux workspace** with a **closed-loop `wait-for` handshake as the ONLY success signal**, script-driven `/rename` + `/rc` post-spawn setup, a progress-aware hop budget (stall rule + advisory `expected_hops` + absolute ceiling), a script-generated mechanics card, and a `handoff_spawn: auto|ask|off` consent dial.

**Architecture:** Everything lands in this fork. The spawn script keeps its five-layer shape (config → preconditions → composition → spawn core → sequence) and its 0/3/1 exit ladder; new exit-3 rungs are reasons, not codes. A new import-only Python module `_handoff_support.py` is the SSOT for the hop-budget formula, derivation precedence, tasks_done counting, and stall streaks — consumed by `materialize-manifest.py` (import) and the spawn script (CLI via `$PYTHON`). Model fields land BEFORE any frontmatter or manifest uses them (`Plan` is `extra="forbid"`). The three changed baselined hooks (`hooks/session-start`, `sdd-stop-hook.sh`, `sdd-pre-dispatch-hook.sh`) ship in ONE task with ONE `check-hooks.sh --capture`.

**Tech Stack:** bash ≥ 3.2 (spawn script; no `set -u`/`set -e`/pipefail, `printf` not `echo`, never pipe a producer into `grep -q`), Python 3.9+ (models, support module, card generator; Pydantic v2 via `.venv`), pytest, cmux CLI 0.64.20 (installed-binary contract), stubbed cmux/picker for all tests.

**Source Contracts:** None

_Coordination document — Source Contracts is "None" at the parent level so the mechanical Task-0 gate resolves against the module that owns Task 0 (**Module 1**), the repo convention for modular parents. The feature's real external contracts — the spec-distilled Contract Facts + Decision Summary (binding), the installed cmux binary (`cmux --version` = `cmux 0.64.20 (100) [14e3400b9]`) for verb contracts, and the capability matrix `docs/process-improvement-findings/2026-07-28-cmux-capability-usage-matrix.md` §4.2 for per-verb `OK` shapes — are enumerated in the **Shared Contract Section** below and declared + verified in **Module 1 (Task 0)**, which freezes them into fixtures. Plan provenance (the reviewed distilled spec) is recorded in this plan's frontmatter `source_contracts`._

**Contract Constraints:**
- **A received `cmux wait-for` token is the ONLY exit-0 path** (`handshake=ok`). Screen reading is post-timeout diagnosis ONLY — it enriches the record and instructions, never selects the exit code.
- Exit ladder shape unchanged: 0 spawned / 3 manual fallback / 1 refused. New exit-3 reasons: `reason=policy-off`, `reason=policy-ask` (retryable, checked BEFORE reservation, no hop consumed), `reason=stall`, `handshake=timeout` + `diagnosis=banner|trust-dialog|picker-error|unreadable|none`. (Spec-internal discrepancy resolved: the distilled spec's acceptance criterion says `reason=policy`; its Contract Facts and Decision 14 say `reason=policy-off` — this plan follows Contract Facts. Record as an accepted deviation at SDD ingestion.)
- Reservation ordering unchanged: reserve (`.handoff-hops`, intent record) BEFORE spawn; hop stays consumed on any post-spawn failure; messages never claim "nothing was spawned" after a spawn.
- `.handoff-hops` stays a single integer; the malformed-value fail-closed guard is untouched.
- Per-verb `OK` parsing — never reuse a generic field-2 parser: `new-workspace`/`workspace create` → field 2 is the workspace ref; `new-surface` → `OK surface:N pane:M workspace:K` (field 2 = surface ref); `rename-tab` → field 2 is `action=rename`, NOT a ref; `close-surface` returns a plausible WRONG ref.
- A `cmux send` command runs in the workspace shell env, not the parent session's: everything the successor needs rides inline in the command string (`SUPERPOWERS_SPAWN_ID=<uuid>` prefix + needed `SUPERPOWERS_CMUX_*` overrides).
- `read-screen` on a never-driven surface errors (`internal_error`) — diagnosis code treats that as "no diagnosis", not a crash.
- `Plan` model is `extra="forbid"`: the `handoff_spawn` field (Task 4) must land before any plan frontmatter uses it. No `CURRENT_SCHEMA_VERSION` bump anywhere in this sprint.
- `expected_hops` = `ceil(total_tasks / 2.5)` standard tier, `1` micro. Ceiling default = `max(6, 2 × expected_hops)`; explicit `SUPERPOWERS_CMUX_MAX_HOPS` wins absolutely. Stall rule: consecutive zero-progress hops > `SUPERPOWERS_CMUX_MAX_STALL_HOPS` (default 1) → refuse exit 3.
- `tasks_done` = UNIQUE task IDs across `reports/` + `archive-*/` whose implementer-report frontmatter parses AND records completed status; filenames alone never count; first-hop baseline 0; missing/malformed prior outcome → `stall=indeterminate` SKIP.
- SDD SKILL.md is near its word ceiling: protocol content goes in `references/`, never the SKILL body.
- Baselined-hook edits ship with ONE `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture` + committed `baseline.txt` in the same change (Task 14).

**Shared Constants:** (see frontmatter — enforced per task) `TIER_PROFILES`, `REQUIRED_SECTIONS`, spawn-script bundle constants, `_handoff_support.py` formula constants, env-knob defaults.

**Pattern References:** (see frontmatter) spawn-script-layer-style, pytest-bash-stub-harness, e2e-step-structure, model-field-addition, manifest-materialization, import-only-helper-ssot, stop-hook-systemmessage.

**Feature Archetype:** Extension — nothing removed; workspace spawn is demoted to a fallback, not deleted. No Obsolescence Verification task required; the e2e/test vocabulary changes land in the same tasks that change the topology.

## Code Footprint

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| New | `skills/subagent-driven-development/scripts/_handoff_support.py` | Create | consumed by materialize-manifest.py + spawn script |
| New | `skills/subagent-driven-development/scripts/write-mechanics-card.py` | Create | imports implementer_report, _report_utils |
| New | `tests/unit/test_handoff_support.py`, `tests/unit/test_mechanics_card.py`, `tests/unit/test_spawn_handoff_v2.py` | Create | — |
| New | `tests/unit/fixtures/spawn-handoff/cold-start-timing.json`, `tests/unit/fixtures/spawn-handoff/cmux-verb-shapes.json` | Create (Task 0) | — |
| Modified | `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` | Extend (Tasks 8-11, 13) | tests/unit/test_spawn_handoff*.py, e2e Step 14 |
| Modified | `skills/scripts/models/plan.py`, `skills/scripts/models/sdd_session.py` | Extend (Tasks 4-5) | validate-plan.py, validators.py, materialize-manifest.py, unit model tests |
| Modified | `skills/subagent-driven-development/scripts/materialize-manifest.py` | Extend (Task 6) | e2e Steps 1-13, unit tests |
| Modified | `hooks/session-start`, `skills/subagent-driven-development/scripts/sdd-stop-hook.sh`, `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Extend (Task 14, one change) | `tests/ARaymond-hook-baseline/baseline.txt` re-capture, hook unit tests |
| Modified | `skills/subagent-driven-development/scripts/controller-checkpoint.py` (`_check_verification_git_reality`) | Extend (Task 15) | checkpoint unit tests |
| Modified | `skills/subagent-driven-development/references/context-handoff-protocol.md` | Rewrite step-4/exit-code text (Task 16) | cited by hook block message |
| Modified | `tests/integration/sdd-e2e-test.sh` Step 14 + closing banner | Rewrite (Task 17) | — |
| Modified | `docs/process-improvement-findings/BACKLOG.md` | Rows for SP1-SP4 dispositions, N63 close (Tasks 1-3, 13) | — |
| Retained | Workspace spawn path (`spawn_claude_workspace`) | Keep as fallback, migrate verb to `workspace create` (Task 9) | e2e stub + unit tests change same task |

## Module Inventory

| Module | File | Goal |
|--------|------|------|
| 1 | `module-1-contracts-spikes.md` | Ground truth: live cmux verb-shape fixtures, cold-start handshake timing (pins `SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT` default), SP1/SP2 probes, SP3/SP4 design docs |
| 2 | `module-2-models-budget.md` | `handoff_spawn` plan field, manifest `handoff` block, `_handoff_support.py` (formula, precedence, tasks_done, stall streak), materialize-manifest wiring |
| 3 | `module-3-spawn-script.md` | Spawn script rework: policy gate, stall/ceiling, surface topology + shared launch wrapper + workspace fallback, handshake + diagnosis, post-spawn setup |
| 4 | `module-4-card-hooks-docs.md` | Mechanics card, N63 checked writes + bookkeeping commit, hooks trio + one baseline capture, Check 9 pathspec, protocol rewrite, e2e Step 14, final verification |

## Module Dependency Graph

```
Module 1 (contracts + spikes)
  └── Module 2 (models + budget support)   ← needs Task 0 fixtures for import assertions
      └── Module 3 (spawn script rework)   ← reads manifest handoff block + _handoff_support CLI
          └── Module 4 (card/hooks/docs/e2e) ← card invoked by script; e2e asserts final behavior
```

No parallel modules: each consumes the previous module's artifacts. Within modules, tasks are serialized (shared files).

## Write-Scope Partitioning (module-level)

| Module | Owned Files (write) | Read-Only |
|--------|---------------------|-----------|
| 1 | `tests/unit/fixtures/spawn-handoff/{cold-start-timing.json,cmux-verb-shapes.json}`, `docs/process-improvement-findings/{2026-07-30-sp2-*.md,2026-07-30-sp3-*.md,2026-07-30-sp4-*.md}`, `skills/subagent-driven-development/scripts/context-probe.py` (SP1, only if fix), `tests/unit/test_context_probe*.py` (SP1), `BACKLOG.md` (rows) | installed cmux binary, spec |
| 2 | `skills/scripts/models/{plan.py,sdd_session.py}`, `skills/subagent-driven-development/scripts/{_handoff_support.py,materialize-manifest.py}`, `tests/unit/test_models/*`, `tests/unit/test_handoff_support.py` | Task 0 fixtures |
| 3 | `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff_v2.py`, `tests/unit/test_spawn_handoff.py` (topology migrations), `tests/unit/spawn_handoff_helpers.py` (extensions), `tests/unit/fixtures/spawn-handoff/*` (new manifests, screens) | `_handoff_support.py`, models |
| 4 | `skills/subagent-driven-development/scripts/{write-mechanics-card.py,sdd-stop-hook.sh,sdd-pre-dispatch-hook.sh,controller-checkpoint.py,spawn-handoff-session.sh (Task 13 only)}`, `hooks/session-start`, `tests/ARaymond-hook-baseline/baseline.txt`, `skills/subagent-driven-development/references/context-handoff-protocol.md`, `tests/integration/sdd-e2e-test.sh`, `tests/unit/{test_mechanics_card.py,test_spawn_handoff_v2.py,test_sdd_stop_hook*.py,test_sdd_pre_dispatch*.py,test_controller_checkpoint*.py}`, `BACKLOG.md` (N63 close) | everything from Modules 1-3 |

`spawn-handoff-session.sh` is written by Modules 3 and 4 (Task 13) — strictly serialized by the module order and `depends_on: [11, 12]`.

## Shared Contract Section (all modules)

1. **Per-verb `OK` shapes** (capability matrix §4.2, verified on 0.64.20; re-captured live in Task 0):
   - `cmux workspace create` / legacy `new-workspace` → stdout `OK workspace:N`, ref = field 2.
   - `cmux new-surface` → stdout `OK surface:N pane:M workspace:K`, surface ref = field 2.
   - `cmux rename-tab` → field 2 is `action=rename` — NOT a ref; parse for success only (`^OK` + exit 0).
   - `cmux send` / `send-key` → `OK` only; `\n`/`\r` in `send` text = Enter.
   - `cmux wait-for <name> --timeout <s>` → blocks; exit 0 = token received. `-S` signals.
   - `cmux read-screen --surface <ref> --scrollback` → plain text; errors `internal_error: Failed to read terminal text` on a never-driven surface.
2. **Spawn-log record grammar** (append-only; fields space-separated `key=value` after the 3 positional fields `<ISO-8601Z> <spawn-uuid|-> <record-type>`):
   - `intent hop=<N> tasks_done=<N>`
   - `outcome hop=<N> workspace=<ref> surface=<ref|-> launch=<auto|picker-manual> bundle=<id> quota=<status> tasks_done=<N> handshake=<ok|timeout|none> [diagnosis=<state>] [topology=workspace-fallback] [post_spawn=partial:<step>] [budget=over-expected]` — `workspace=` RETAINED; `workspace=spawn-failed` on the failure branch.
   - `decline bundle=<id> reason=<word>` (spawn-uuid position holds `-`; controller-written one-liner, documented in the protocol).
   - `runtime-picker-failure hop=<N>` (unchanged; written by the spawned child).
3. **Env knobs** (all validate-warn-revert like the existing quota knobs): `SUPERPOWERS_CMUX_SPAWN_WAIT_TIMEOUT` (integer seconds; default pinned by Task 0), `SUPERPOWERS_CMUX_MAX_STALL_HOPS` (integer, default 1), `SUPERPOWERS_CMUX_POST_SPAWN` (comma list from {rename,rc}; default `rename,rc`; empty string disables), `SUPERPOWERS_CMUX_TITLE_FORMAT` (default `hop{hop} SDD {feature}`; tokens `{hop}` `{feature}`), existing `SUPERPOWERS_CMUX_MAX_HOPS` (numeric validate-warn-revert guard unchanged — fail-closed belongs ONLY to `.handoff-hops`; default becomes derived `max(6, 2×expected_hops)`).
4. **Manifest `handoff` block** (optional; absent → `spawn_policy=auto`, `expected_hops` re-derived at spawn time): `{"expected_hops": int, "spawn_policy": "auto"|"ask"|"off"}`. Derivation precedence for total tasks: (1) validated manifest `total_tasks`; (2) union of unique module task IDs; (3) inclusive active `task_range`. Invalid/zero → absent-with-warning (notify suppressed, WARN logged).

## Acceptance Criteria (sprint-level; module files carry per-task criteria)

- [ ] A HARD/soft handoff spawns the successor as a top tab in the caller's workspace, `--focus false` held, tab renamed `hop<N> SDD <feature>`.
- [ ] The successor is visible in the Claude phone app with that name and `/rc` active, with zero human keystrokes.
- [ ] `handoff-spawn.log` outcome records carry `surface=`, `tasks_done=`, launch mode, and handshake status; e2e Step 14 asserts them.
- [ ] A chain completing tasks every hop is never refused below the ceiling; two consecutive zero-progress hops are refused with a progress-bearing message.
- [ ] `expected_hops` appears in the manifest and the over-expected notify fires (e2e stub).
- [ ] The successor's first dispatch requires no report-naming, checkpoint, or Check 9 remediation caused by handoff artifacts.
- [ ] `handoff_spawn: ask` blocks scripted spawn without `--user-approved`; `off` refuses with `reason=policy-off`.
- [ ] The wait-for token is the only exit-0 path: stubbed banner/dialog screens with no token exit 3 with the matching `diagnosis=` field; a received token exits 0 (`handshake=ok`).
- [ ] All suites green (unit, e2e with updated banner count, regression, install); hook baseline re-captured in the same change as the hook edits.
- [ ] SP1–SP4 deliverables committed under `docs/process-improvement-findings/` (SP1 may instead land as a `context-probe.py` fix with tests).

## Post-merge (not plan tasks — recorded so nobody forgets)

Live sessions resolve `~/.claude/skills/superpowers/...` to the MAIN checkout: after merge, run the live smoke check (dry-run + one real surface spawn into a throwaway workspace). The next real SDD run is the acceptance test.
