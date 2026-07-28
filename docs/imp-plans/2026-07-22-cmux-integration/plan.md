---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: "docs/imp-plans/2026-07-22-cmux-integration/spec-distilled.md"
shared_constants:
  - path: "env SUPERPOWERS_CMUX_MAX_HOPS"
    value: "3"
    reason: "Hop-limit default; Task 1 precondition + docs (Task 11)"
  - path: "env SUPERPOWERS_CMUX_QUOTA_MIN_PCT"
    value: "15"
    reason: "Quota-refusal threshold default; Task 2 + docs (Task 11)"
pattern_references:
  - name: "sdd-bash-hook-style"
    source_files: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    reason: "House bash style for SDD scripts: SUPERPOWERS_ROOT self-resolution, $PYTHON usage, no set -u, here-strings not pipe-into-grep-q"
  - name: "pytest-bash-stub-harness"
    source_files: ["tests/unit/test_context_gate_tier.py"]
    reason: "How to unit-test a bash script from pytest: subprocess.run(['bash', SCRIPT]), PATH stubs, tmp_path workspace, assert returncode + stdout/stderr + log files"
  - name: "e2e-step-structure"
    source_files: ["tests/integration/sdd-e2e-test.sh"]
    reason: "e2e step layout: set -e + ERR trap, PROJECT resolved from BASH_SOURCE, stub-on-PATH, `|| RC=$?` around expected-nonzero calls, PASS echo per step, final banner"
integration_test:
  path: tests/integration/sdd-e2e-test.sh
modules:
  - id: 1
    title: "spawn-handoff-session.sh + unit suite"
    task_ids: [0, 1, 2, 3, 4, 5, 6]
    file: module-1-spawn-script.md
  - id: 2
    title: "protocol rewrite + e2e Step 14 + docs"
    task_ids: [7, 8, 9, 10, 11]
    file: module-2-protocol-e2e-docs.md
tasks:
  - id: 0
    title: "Contract verification + prerequisite assertions (BLOCKING)"
    module_id: 1
  - id: 1
    title: "Script foundation + basic-refusal preconditions"
    depends_on: [0]
    module_id: 1
    pattern_references: ["sdd-bash-hook-style", "pytest-bash-stub-harness"]
  - id: 2
    title: "Bundle validation + cmux/hop preconditions"
    depends_on: [1]
    module_id: 1
    shared_constants_used: ["env SUPERPOWERS_CMUX_MAX_HOPS"]
    pattern_references: ["sdd-bash-hook-style", "pytest-bash-stub-harness"]
  - id: 3
    title: "Quota check (session-window, fail-open)"
    depends_on: [2]
    module_id: 1
    shared_constants_used: ["env SUPERPOWERS_CMUX_QUOTA_MIN_PCT"]
    pattern_references: ["pytest-bash-stub-harness"]
  - id: 4
    title: "Launch composition A: metadata decode, strip guard, label rule, telemetry"
    depends_on: [3]
    module_id: 1
    pattern_references: ["pytest-bash-stub-harness"]
  - id: 5
    title: "Launch composition B: auto preflight + compose-side quoting"
    depends_on: [4]
    module_id: 1
    pattern_references: ["pytest-bash-stub-harness"]
  - id: 6
    title: "Spawn sequence, reservation ordering, exit codes, --dry-run"
    depends_on: [5]
    module_id: 1
    pattern_references: ["pytest-bash-stub-harness"]
  - id: 7
    title: "Sweep A: zero-protection regression coverage + harness knobs"
    depends_on: [6]
    module_id: 2
    pattern_references: ["pytest-bash-stub-harness"]
  - id: 8
    title: "Sweep B: reservation-write hardening, residual coverage, plan-doc corrections"
    depends_on: [7]
    module_id: 2
    pattern_references: ["sdd-bash-hook-style", "pytest-bash-stub-harness"]
  - id: 9
    title: "Rewrite context-handoff-protocol.md steps 3-5"
    depends_on: [8]
    module_id: 2
  - id: 10
    title: "e2e Step 14 (spawn end-to-end) + banner 14->15"
    depends_on: [9]
    module_id: 2
    pattern_references: ["e2e-step-structure"]
  - id: 11
    title: "Docs: CLAUDE.md section, manifest, BACKLOG N43(D)"
    depends_on: [10]
    module_id: 2
    review_tier: minimum
---

# cmux Integration — Repo-3 (superpowers) Implementation Plan

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

> **This is the parent coordination plan for repo 3 only.** Module files hold the tasks. The cross-repo split (Decision 19) is deliberate: repo-1 (telemetry-exp picker) and repo-2 (cmux-custom-skills) are **separate repo-local deliverables** with their own review/commit trails — they are **NOT** tasks in this plan and do **NOT** appear in `plan-manifest.txt`. This plan consumes them as **asserted prerequisites** (Task 0) and never modifies them.

**Goal:** Add a deterministic, internally-layered `spawn-handoff-session.sh` that lets a context-blocked SDD controller auto-spawn its successor session through the extended claude-picker in a new cmux workspace, plus the protocol rewrite, unit + e2e tests, and docs that make it live.

**Architecture:** One new bash script under `skills/subagent-driven-development/scripts/` with a generic `spawn_claude_workspace()` core (cmux detect → spawn → notify; extraction-ready) wrapped by an SDD policy shell (preconditions → bundle validation → quota → reservation → launch composition → exit-code contract). The N43 context-handoff protocol's steps 3–5 are rewritten to capture the bundle id and drive the script. Everything else in the SDD pipeline is unchanged.

**Tech Stack:** Bash (house SDD-script style), python3 stdlib (JSON/base64 decode, no PyYAML/Pydantic needed for the script itself), pytest (unit suite with PATH stubs for `cmux`/`claude-picker`/`claude-usage-pace`), the existing `sdd-e2e-test.sh` harness.

**Source Contracts:** None

_Coordination document — Source Contracts is "None" at the parent level so the mechanical Task-0 gate resolves against the module that owns Task 0 (**Module 1**), the repo convention for modular parents. The feature's real external contracts — the repo-1 picker contract v1, the repo-2 vendored-skill symlinks, the live cmux CLI argv surface, the handoff bundle manifest fields, and the `claude-usage-pace` quota schema — are enumerated in the **Shared Contract Section** below and declared + verified in **Module 1 (Task 0)**, which freezes them into fixtures. Plan provenance (the reviewed distilled spec) is recorded in this plan's frontmatter `source_contracts`._

**Contract Constraints (non-negotiable):**
- `--handoff-contract` must print the string `1` **exactly** — auto preflight fails on any other value (a future v2 must degrade to picker-manual, not pass). Compare with string equality after trimming, not `-ge`.
- Repo identity match is **worktree-invariant**: `active_id = realpath(git rev-parse --git-common-dir)` at the worktree root must equal the bundle manifest's `project.repo_id`. (This mirrors the pickup guard's `repo_identity()` exactly — do not reinvent with `--show-toplevel`, whose basename differs per worktree.)
- `CLAUDE_CODE_PICKER_ARGS` is decoded **without eval**: strip the `v1:` prefix, base64-decode, `json.loads` into a list of strings via python3 stdlib. Absent ⇒ empty argv. A `v1:`-prefixed-but-corrupt body ⇒ decode failure ⇒ metadata unusable (degrade to picker-manual), never a silent arg-drop.
- **`CLAUDE_CODE_PICKER_APPEND_PROMPT`** (4th export; base64 of the `--append-system-prompt-file` **contents**) is the picker's designed remedy for a dead/temp append path and **must be consumed**: when non-empty, decode it to a stable absolute file outside any repo and **substitute** that path into the forwarded `--append-system-prompt-file` value (prefer content over path). Empty-but-flag-present ⇒ keep the original path (best effort). The picker keeps passthrough verbatim; rewriting the arg is the consumer's job by design.
- The picker's `--append-system-prompt-file` readability check **exits 3 only under `--non-interactive`** — so the auto command's residual fallback catches a dead path, but the interactive `picker-manual` branch does not validate it (attended fallback).
- `CLAUDE_CODE_ENABLE_TELEMETRY==1` ⇒ `--telemetry on`; **absent** ⇒ `--telemetry off` (never blocks auto). It is set indirectly via `telemetry-vars.sh` on the picker's telemetry-ON path and inherited into the session env (a `CLAUDE_CODE_*` var, so it survives Claude Code's subprocess env filter).
- Picker version discovery uses `find -type f -perm -u+x`, so `versions/<v>` is an **executable regular file** — the auto preflight asserts `-f` AND `-x` (not a lenient `-e`).
- Quota is **fail-open**: tool absent / non-zero / 60s timeout / unparseable / window-or-field missing / non-numeric ⇒ proceed with `quota=unchecked`. Only a parsed numeric `< SUPERPOWERS_CMUX_QUOTA_MIN_PCT` refuses (exit 3).
- Reservation (hop increment + `intent` log line) happens **before** `cmux new-workspace`. Post-spawn failures are non-retryable (warn, still exit 0). A spawn failure after reservation keeps the hop consumed and exits 3.
- Label ceiling is 255: reserve `len(suffix)` before truncating the base, then concatenate (round-trip must be picker-sanitizer-stable).
- Compose-side quoting: every interpolated element (each decoded arg, version, label) is shlex-style re-quoted when building the `--command` string (a shell re-parses it inside the workspace).

**Shared Constants:**
- `SUPERPOWERS_CMUX_MAX_HOPS` (default `3`) — env; hop-limit precondition (Task 1) and docs (Task 11). Do not hardcode `3` elsewhere.
- `SUPERPOWERS_CMUX_QUOTA_MIN_PCT` (default `15`) — env; quota refusal threshold (Task 2) and docs (Task 11).

**Pattern References:**
- `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` — house SDD-script bash style: `SUPERPOWERS_ROOT` self-resolution from `BASH_SOURCE`, `$PYTHON` for python calls, avoid `set -u`, never pipe a producer into `grep -q` under pipefail (use here-strings).
- `tests/unit/test_context_gate_tier.py` — pytest→bash harness (subprocess, PATH stubs, tmp_path, assert returncode/stdout/stderr/logs).
- `tests/integration/sdd-e2e-test.sh` — e2e step layout, stub-on-PATH, `|| RC=$?` around expected-nonzero calls, PASS echo, final banner.

**Feature Archetype:** Extension — adds a new script + tests + docs and rewrites the tail of one protocol doc. Nothing is replaced except protocol steps 3–5. No obsolescence verification task required (no code removed).

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| New | `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` | Create | — |
| New | `tests/unit/test_spawn_handoff.py` | Create | — |
| New | `tests/unit/fixtures/spawn-handoff/` (bundle manifest + argv fixtures) | Create | — |
| Modified | `skills/subagent-driven-development/references/context-handoff-protocol.md` | Rewrite steps 3–5 only (steps 1–2 unchanged) | Block message in `sdd-pre-dispatch-hook.sh:840` already points here — do not edit the hook |
| Modified | `tests/integration/sdd-e2e-test.sh` | Add Step 14, banner `14`→`15` steps | Existing Steps 1–13 unchanged |
| Modified | `CLAUDE.md` | Add "cmux Integration" section (env vars → Hook Dev Gotchas list) | Read-merge-validate; do not drop existing sections |
| Modified | `docs/ARaymond-customization-manifest.md` | Add inventory entries | Read-merge |
| Modified | `docs/process-improvement-findings/BACKLOG.md` | Close N43(D) with a new row | Read-merge |
| Retained (DO NOT TOUCH) | `sdd-pre-dispatch-hook.sh` | Keep — **no change, no baseline re-capture** | Block message already points to protocol doc |
| Retained (DO NOT TOUCH) | `skills/subagent-driven-development/SKILL.md` body | Keep — **no change** (word ceiling) | — |
| Retained (DO NOT TOUCH) | `tests/ARaymond-installation/verify-symlink-install.sh` | Keep — **no change** (cmux symlink checks live in repo-2) | — |

## Explicit Non-Goals (do not let a helpful subagent do these)

1. **Do NOT modify `sdd-pre-dispatch-hook.sh`** or any of the 7 baselined hooks. No hook change ⇒ no `tests/ARaymond-hook-baseline/baseline.txt` re-capture. The HARD-block message already ends with a pointer to `context-handoff-protocol.md` (verified at `sdd-pre-dispatch-hook.sh:840`).
2. **Do NOT edit the SDD `SKILL.md` body** — it is at the word ceiling. New prose goes in `CLAUDE.md` and the protocol doc.
3. **Do NOT edit `verify-symlink-install.sh`** — cmux symlink verification is repo-2's `verify-install.sh`; the repos stay decoupled (B does not depend on A's install checks).
4. **Do NOT build repo-1 or repo-2 in this plan.** Task 0 *asserts* they exist; it never creates them. Repo-2 is created as a separate repo-local effort (see `repo-2-cmux-custom-skills-checklist.md`), repo-1 in its own telemetry-exp session.
5. **Do NOT touch `context-observations.log` or its format.** The spawn event log is a **separate** file (`reports/handoff-spawn.log`) with its own format.
6. **Do NOT change the context gate's thresholds, tiers, probe, or observation-log format** (all out of scope per the spec).

## Module Inventory

| Module | File | Goal | Tasks |
|--------|------|------|-------|
| 1 | `module-1-spawn-script.md` | Build `spawn-handoff-session.sh` (layered) + `test_spawn_handoff.py` full unit matrix, TDD | 0–6 |
| 2 | `module-2-protocol-e2e-docs.md` | Rewrite protocol steps 3–5, add e2e Step 14, update docs | 7–9 |

## Module Dependency Graph

```
Module 1 (spawn-handoff-session.sh + unit suite)   ← Task 0 gates on repos 1+2 landing
  └── Module 2 (protocol rewrite + e2e Step 14 + docs)   ← depends on Module 1 (the finished script)
```

**No parallel candidates.** Both modules write into the same feature and Module 2's e2e (Step 14) drives the script Module 1 produces. Execute Module 1 fully, transition, then Module 2.

## Cross-Repo Execution Order (Decision 19) — READ BEFORE EXECUTING

This plan is the **last** of three ordered repo-local deliverables. Execution of **any Module 1 task past Task 0** is gated on the first two having landed:

1. **Repo 1 — telemetry-exp claude-picker contract v1** (separate session; handoff bundle `2026-07-23T01-19-24Z-telemetry-exp`). Must land first. **Current state at plan-writing: NOT landed** — `claude-picker --handoff-contract` falls through to the interactive version menu instead of printing `1`.
2. **Repo 2 — `~/projects/claude-custom/cmux-custom-skills`** (separate repo-local effort; checklist at `repo-2-cmux-custom-skills-checklist.md`). Must land second. **Current state: repo does not exist yet.**
3. **Repo 3 — this plan.** Task 0 asserts (1) and (2) are real. If either is missing, **Task 0 fails and blocks the whole plan by construction** — that is the intended gate, not a bug. You do not police execution timing manually; Task 0 does it.

## Shared Contract Section

All three modules share the same external contracts, verified once in **Task 0** and consumed thereafter:

- **Picker contract probe:** `claude-picker --handoff-contract` → stdout `1`, exit 0.
- **Picker exports (4, every launch path)** — verified against `telemetry-exp launchers/claude-picker` contract v1 (commits `f0ccba9`/`03795e3`/`dfca453`): `CLAUDE_CODE_PICKER_VERSION`, `CLAUDE_CODE_PICKER_LABEL`, `CLAUDE_CODE_PICKER_ARGS` (v1 codec), `CLAUDE_CODE_PICKER_APPEND_PROMPT` (base64 of the append-prompt file contents — **consumed** per Contract Constraints). Telemetry-on inferred from inherited `CLAUDE_CODE_ENABLE_TELEMETRY=1`.
- **cmux CLI argv** (frozen from live `cmux --help` in Task 0): `new-workspace --name/--cwd/--command/--focus`, `notify --title/--body`, `ping`.
- **Bundle manifest fields:** `session.bundle_type`, `session.entry_skill`, `project.repo_id`.
- **Quota field:** `windows[key=="session"].remaining_pct`.

## Write-Scope Partitioning (whole plan)

| Task | Owned Files (write) | Read-Only Files | Depends On |
|------|---------------------|-----------------|------------|
| Task 0 | `tests/unit/fixtures/spawn-handoff/*`, `tests/unit/test_spawn_handoff.py` (contract test only) | picker/cmux/bundle contracts (live) | — |
| Task 1 | `spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff.py` | fixtures | Task 0 |
| Task 2 | `spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff.py` | fixtures | Task 1 |
| Task 3 | `spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff.py` | fixtures | Task 2 |
| Task 4 | `spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff.py` | fixtures | Task 3 |
| Task 5 | `spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff.py` | fixtures | Task 4 |
| Task 6 | `spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff.py` | fixtures | Task 5 |
| Task 7 | `tests/unit/test_spawn_handoff.py`, `tests/unit/spawn_handoff_helpers.py` | `spawn-handoff-session.sh` | Task 6 |
| Task 8 | `spawn-handoff-session.sh`, `tests/unit/test_spawn_handoff.py`, `module-1-spawn-script.md` | `tests/unit/spawn_handoff_helpers.py` | Task 7 |
| Task 9 | `skills/subagent-driven-development/references/context-handoff-protocol.md` | `spawn-handoff-session.sh` | Task 8 |
| Task 10 | `tests/integration/sdd-e2e-test.sh` | `spawn-handoff-session.sh` | Task 9 |
| Task 11 | `CLAUDE.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | all of the above | Task 10 |

**Serialization note:** Tasks 1–6 all write the single file `spawn-handoff-session.sh` and the single file `test_spawn_handoff.py`. They are strictly serialized by `depends_on` — never dispatched in parallel. This is intentional: one script, built up concern-by-concern via TDD.

## Acceptance Criteria (plan-level)

- [ ] `spawn-handoff-session.sh <bundle-id> --dry-run` in a real picker-launched cmux SDD session prints a composed successor command with the same version, decoded+re-quoted forwarded args, and correctly incremented label — and spawns/increments nothing.
- [x] The full unit matrix (§7 of the spec) passes: preconditions, all quota classes, all label cases (incl. 255 boundary), strip guard, compose-quoting survival, reservation ordering, both launch modes, `--dry-run`.
- [x] e2e `sdd-e2e-test.sh` reaches Step 14 and passes; banner reads `15 steps`.
- [x] `context-handoff-protocol.md` steps 3–5 drive the script; steps 1–2 byte-identical.
- [x] `sdd-pre-dispatch-hook.sh` and `tests/ARaymond-hook-baseline/baseline.txt` are unchanged (git diff empty for both).
- [x] `CLAUDE.md`, customization manifest, and BACKLOG updated; N43(D) row closed.
- [x] All existing suites stay green: `validate-all-skills.py`, `verify-symlink-install.sh`, `pytest tests/unit/`, `sdd-e2e-test.sh`.

## Post-Merge Live Smoke (mandatory before declaring done — from spec §7)

The e2e proves the *checkout* path; the installed skill path resolves to the **main** checkout, so a post-merge live check is required (mirrors N43's discipline):

1. In a real cmux session launched via the extended claude-picker, run `spawn-handoff-session.sh <scratch-bundle-id> --dry-run`; verify the composed command shows the right version, decoded args, and incremented label.
2. Then one real spawn against a scratch `work`/SDD bundle; confirm the workspace opens, the picker launches non-interactively, `/pickup <id>` ingests, SDD resumes at the first unchecked task; close the workspace.
3. The first genuine HARD-block hop in a downstream project is the true acceptance test.
