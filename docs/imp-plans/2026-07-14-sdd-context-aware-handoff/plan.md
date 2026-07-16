---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
source_contracts: "docs/imp-plans/2026-07-14-sdd-context-aware-handoff/spec-distilled.md"
shared_constants:
  - path: "skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
    value: "SOFT=300000 HARD=400000 FALLBACK_STREAK=3"
    reason: "Canonical default thresholds — tests must override via SUPERPOWERS_CTX_* env vars, never hardcode fresh copies"
pattern_references:
  - name: "transcript-path-read"
    source_files: ["skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh"]
    reason: "The sibling hook already reads .transcript_path from the PreToolUse stdin payload (line ~35) — mirror this exact jq pattern"
  - name: "ctx-check-parity"
    source_files: ["/Users/araymond/.claude/bin/claude-ctx-check"]
    reason: "Proven transcript-scan + 4-field usage sum the probe must mirror; the parity/differential test pins them together"
  - name: "hook-python-shellout"
    source_files: ["skills/subagent-driven-development/scripts/estimate-task-tokens.py"]
    reason: "How the hook shells to a stdlib python3 script and parses its stdout (precedent for calling context-probe.py)"
  - name: "hook-unit-test"
    source_files: ["tests/unit/test_sdd_classification.py", "tests/unit/sdd_test_helpers.py"]
    reason: "How hook branches are tested — make_hook_input builds the stdin payload, hook run via subprocess in a manifest workspace"
  - name: "reference-pointer"
    source_files: ["skills/subagent-driven-development/references/context-health-protocol.md"]
    reason: "Pattern for a short SKILL.md pointer into a references/ doc — the new protocol doc + word-offset extraction follow this shape"
integration_test:
  path: tests/integration/sdd-e2e-test.sh
modules:
  - id: 1
    title: "Context probe + fixtures"
    task_ids: [0, 1, 2]
    file: module-1-probe.md
  - id: 2
    title: "Hook context gate"
    task_ids: [3, 4, 5, 6]
    file: module-2-hook-gate.md
  - id: 3
    title: "Docs, integration, verification"
    task_ids: [7, 8, 9, 10]
    file: module-3-docs-integration.md
tasks:
  - id: 0
    title: "Contract verification + fixture transcripts"
    module_id: 1
  - id: 1
    title: "context-probe.py core (--transcript / --json)"
    module_id: 1
    depends_on: [0]
    pattern_references: ["ctx-check-parity"]
  - id: 2
    title: "context-probe.py --session-id resolution + parity"
    module_id: 1
    depends_on: [1]
    pattern_references: ["ctx-check-parity"]
  - id: 3
    title: "Hoist session_id + helpers + thread into non-implementer exit paths"
    module_id: 2
    depends_on: [2]
    shared_constants_used: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    pattern_references: ["transcript-path-read", "hook-python-shellout", "hook-unit-test"]
  - id: 4
    title: "Implementer-path observation logging + hoist proof"
    module_id: 2
    depends_on: [3]
    pattern_references: ["hook-unit-test"]
  - id: 5
    title: "Nudge/block tier in the implementer new-task path"
    module_id: 2
    depends_on: [4]
    shared_constants_used: ["skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"]
    pattern_references: ["hook-unit-test"]
  - id: 6
    title: "K-consecutive-fallback escalation"
    module_id: 2
    depends_on: [5]
    pattern_references: ["hook-unit-test"]
  - id: 7
    title: "Handoff-protocol reference + SKILL.md pointer (word-offset)"
    module_id: 3
    depends_on: [6]
    pattern_references: ["reference-pointer"]
  - id: 8
    title: "Operational + troubleshooting documentation"
    module_id: 3
    depends_on: [7]
    review_tier: minimum
  - id: 9
    title: "e2e integration step (over-threshold block)"
    module_id: 3
    depends_on: [8]
    pattern_references: ["hook-unit-test"]
  - id: 10
    title: "Final verification (all suites + baseline verify)"
    module_id: 3
    depends_on: [9]
    task_type: verification
    review_tier: minimum
---

# SDD Context-Aware Auto-Handoff — Implementation Plan (Parent)

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Add a deterministic context-pressure gate to the SDD pre-dispatch hook that reads the controller's actual accumulated token count and, at a clean new-task boundary, nudges (soft) then blocks (hard) the next implementer dispatch so the controller hands off to a fresh session before quality degrades.

**Architecture:** A new stdlib-only `context-probe.py` mirrors the proven `claude-ctx-check` (scan the controller's transcript from the end, sum the four `usage` token fields). The hook reads `.transcript_path` from its PreToolUse stdin payload, runs the probe, appends one observation-log line per dispatch (all types), and — only on the implementer new-task path — applies a two-tier nudge/block against env-overridable thresholds (SOFT 300k / HARD 400k). Probe failure degrades to the existing Check-7 byte-proxy (advisory), with a K-consecutive-fallback escalation to a block so a silently-broken gate cannot stay inert. The controller's block-response protocol reuses the existing N39 fresh-session handoff and the documented mid-plan resume.

**Tech Stack:** Bash (the hook), stdlib-only Python 3 (the probe), pytest (unit), bash e2e, `jq`.

**Source Contracts:** None

_Coordination document — Source Contracts is "None" at the parent level so the mechanical Task-0 gate resolves against the module that owns Task 0 (the repo convention for modular parents). The feature's real external contracts — the transcript JSONL `usage` block (`input_tokens` + `cache_creation_input_tokens` + `cache_read_input_tokens` + `output_tokens` on an assistant `message`), the PreToolUse payload fields `.transcript_path` / `.session_id`, and `claude-ctx-check` parity — are declared and verified in **Module 1 (Task 0)**, which freezes them into fixtures. Plan provenance (the reviewed distilled spec) is recorded in this plan's frontmatter `source_contracts`._

**Contract Constraints (non-negotiable):**
- Metric is **absolute tokens**: `T = input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens`, from the most recent assistant `usage` block. No window, no percentage.
- Thresholds: `SOFT = 300000`, `HARD = 400000` (env-overridable). `T < SOFT` → allow; `SOFT ≤ T < HARD` → allow + nudge; `T ≥ HARD` → block (`exit 2`).
- Missing or non-numeric `usage` fields count as **0**; a malformed trailing JSONL line is **skipped** (not fatal). Probe records the vendored `claude-ctx-check` source version.
- Transcript resolution: hook reads `.transcript_path` from the stdin payload → `context-probe.py --transcript <path>`; if empty → `--session-id "$SESSION_ID"`. **Never** `CLAUDE_CODE_SESSION_ID` inside the hook. `.session_id` must be hoisted to right after the `INPUT` parse, before dispatch classification.
- Nudge/block predicate: `IS_IMPLEMENTER && ! MARKED_FIX` (implementer new-task path only). Reviewer / partner / fix / re-review / passthrough dispatches are never nudged/blocked. A `task_type: verification` task **is** an implementer dispatch → **eligible** for nudge/block (not exempt).
- Observation log is a **separate** file: `reports/context-observations.log` (never `.dispatch-log`). Format: `<ISO-8601> task=<N> type=<implementer|spec-review|quality-review|partner|other> tokens=<T> source=<probe|byte-proxy|bypass> tier=<below|soft|hard> action=<allow|nudge|block|fallback>`. Append is best-effort — a write failure logs to stderr and never breaks the dispatch. Threshold tuning consumes only `source=probe` rows.
- Probe is **stdlib-only** (no pydantic/PyYAML) — invoked with bare `python3`.
- Byte-proxy fallback is **advisory** (undercounts, only warns) — it is NOT a hard ceiling. `SUPERPOWERS_CTX_FALLBACK_STREAK` (default 3) consecutive fallbacks escalate to a block + diagnostic.
- **Guarantee boundary:** the block guarantees the next task will not dispatch; it does NOT by itself force a clean handoff (that depends on the controller following the taught protocol). Do not over-promise.

**Shared Constants:** `SOFT=300000`, `HARD=400000`, `FALLBACK_STREAK=3` — the canonical default thresholds, defined as bash literals in `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`. Tests MUST override them via the `SUPERPOWERS_CTX_SOFT_TOKENS` / `_HARD_TOKENS` / `_FALLBACK_STREAK` env vars — never hardcode fresh copies that can silently drift from the hook.

**Pattern References:**
- `skills/subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh` (~L35) — reads `.transcript_path` from the stdin payload; mirror this `jq` pattern.
- `~/.claude/bin/claude-ctx-check` — the proven transcript-scan + 4-field sum the probe mirrors; the differential test pins parity.
- `skills/subagent-driven-development/scripts/estimate-task-tokens.py` — precedent for the hook shelling to a stdlib `python3` script and parsing stdout.
- `tests/unit/test_sdd_classification.py`, `tests/unit/sdd_test_helpers.py` — hook unit-test conventions (`make_hook_input`, subprocess run in a manifest workspace).
- `skills/subagent-driven-development/references/context-health-protocol.md` — pattern for a short SKILL.md pointer into a `references/` doc.

**Feature Archetype:** Extension — adds a context-pressure gate to the existing hook + SKILL; reuses the N39 handoff and `session-recovery.md` resume. One localized obsolescence: Check 7's *standalone* byte-sum warning is retired (the byte-sum computation is repurposed as the probe-failure fallback).

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| New | `skills/subagent-driven-development/scripts/context-probe.py` | Create | — |
| New | `skills/subagent-driven-development/references/context-handoff-protocol.md` | Create | — |
| New | `tests/unit/fixtures/context-probe/*.jsonl` | Create | — |
| New | `tests/unit/test_context_probe_fixtures.py`, `test_context_probe.py`, `test_context_probe_sessionid.py`, `test_context_gate_log.py`, `test_context_gate_impl_log.py`, `test_context_gate_tier.py`, `test_context_gate_fallback.py` | Create | — |
| New | `skills/subagent-driven-development/references/controller-health-checkpoints.md` (word-offset extraction target) | Create | — |
| New | `reports/context-observations.log` (runtime artifact) | Written at runtime | — |
| Obsolete | Check 7 standalone byte-sum warning (`sdd-pre-dispatch-hook.sh` ~L754-789 block + ~L814 `CONTEXT_LOAD_WARNING` injection) | Remove — byte-sum moved into the probe-failure fallback branch | Grep confirms no other consumer of `CONTEXT_LOAD_WARNING` / `CONTEXT_LOAD_WARNING_BYTES` outside the moved code |
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` | Extend — hoist session_id, add helpers, thread observation logging into all exit paths, add nudge/block + escalation | Existing dispatch classification (reviewer/fix/passthrough/implementer) must be preserved |
| Modified | `skills/subagent-driven-development/SKILL.md` | Add a short protocol pointer, offset by extracting existing prose | Must stay < 5000 words (regression gate) |
| Modified | `tests/unit/sdd_test_helpers.py` | Extend `make_hook_input` to carry `transcript_path` + `session_id` | Existing callers unaffected (new params default to empty) |
| Modified | `tests/integration/sdd-e2e-test.sh` | Add an over-threshold-block step | Existing 13 steps must still pass |
| Modified | `tests/ARaymond-hook-baseline/baseline.txt` | Re-capture in the same task/commit as each hook edit (Tasks 2/3/4) | `check-hooks.sh` must be green at each commit boundary |
| Modified | `CLAUDE.md`, `docs/ARaymond-skills-best-practices.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | Operational docs + BACKLOG N43 status | — |

## File Map

The full file inventory is the **Code Footprint** table above. Each module file carries its own `## File Map`. Summary by module:
- **Module 1** (Tasks 0–2) — `context-probe.py` + fixture transcripts + probe tests (`test_context_probe_fixtures.py`, `test_context_probe.py`, `test_context_probe_sessionid.py`) — all new.
- **Module 2** (Tasks 3–6) — `sdd-pre-dispatch-hook.sh` (modified across Tasks 3–6), `sdd_test_helpers.py`, four new hook-gate test files (`test_context_gate_log.py`, `test_context_gate_impl_log.py`, `test_context_gate_tier.py`, `test_context_gate_fallback.py`), `baseline.txt` (re-captured per hook-editing task).
- **Module 3** (Tasks 7–10) — the protocol reference + checkpoints extraction, `SKILL.md`, operational docs, the e2e step, and read-only verification.

## Module Inventory

| Module | File | Goal | Tasks |
|--------|------|------|-------|
| 1 | `module-1-probe.md` | Vendored stdlib-only `context-probe.py` (core + session-id resolution) + fixture transcripts + parity test | 0, 1, 2 |
| 2 | `module-2-hook-gate.md` | Hoist session_id; shared probe/observation helpers threaded into all exit paths; two-tier nudge/block; K-fallback escalation; baseline re-captured per hook edit | 3, 4, 5, 6 |
| 3 | `module-3-docs-integration.md` | Protocol reference + SKILL pointer (word-offset); operational/troubleshooting docs; e2e block step; final verification | 7, 8, 9, 10 |

## Module Dependency Graph

```
Module 1 (probe + fixtures)
  └── Module 2 (hook gate) ← depends on Module 1 (the hook calls context-probe.py)
        └── Module 3 (docs, e2e, verify) ← depends on Module 2 (docs describe the gate; e2e exercises it; final verify)
```

**Parallel candidates: none.** The plan is a strict serial chain. Modularization here is for controller context-window management (each module is an independently reviewable, committable unit), not parallelism. Modules 2/3 also share write-scope on the hook / SKILL / tests, which forbids parallelism regardless.

## Shared Contract — the probe CLI (produced by Module 1, consumed by Module 2)

`context-probe.py` is the internal contract between the modules. Its surface is frozen by Module 1 and Module 2 must consume it exactly:

- `--transcript <path>` — explicit transcript file (primary input; the test seam). Highest priority.
- `--session-id <id>` — resolve `~/.claude/projects/*/<id>.jsonl`. Used only when `--transcript` is empty.
- `--json` — emit `{"total_tokens": <int>, "transcript": "<path>", "source_version": "<str>"}`; default (no flag) prints the bare integer `total_tokens` to stdout.
- **Exit 0** on success; **exit non-zero** with a stderr diagnostic when the session id is unset, no transcript exists, or no completed turn carries a `usage` block. The hook treats any non-zero exit as "probe unavailable" → byte-proxy fallback.
- Priority order: `--transcript` → `--session-id` → `$CLAUDE_CODE_SESSION_ID` (standalone/CLI use only; the hook never relies on the env var).

## Write-Scope Partitioning (whole plan)

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| 0 | `tests/unit/fixtures/context-probe/*.jsonl`, `tests/unit/test_context_probe_fixtures.py`, `.../reports/task-000-*` | `~/.claude/bin/claude-ctx-check`, real transcript | — |
| 1 | `skills/subagent-driven-development/scripts/context-probe.py`, `tests/unit/test_context_probe.py` | fixtures (Task 0), `claude-ctx-check` | 0 |
| 2 | `skills/subagent-driven-development/scripts/context-probe.py`, `tests/unit/test_context_probe_sessionid.py` | fixtures, `claude-ctx-check` | 1 |
| 3 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`, `tests/unit/sdd_test_helpers.py`, `tests/unit/test_context_gate_log.py`, `tests/ARaymond-hook-baseline/baseline.txt` | `context-probe.py`, sibling hook | 2 |
| 4 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`, `tests/unit/test_context_gate_impl_log.py`, `tests/ARaymond-hook-baseline/baseline.txt` | `sdd_test_helpers.py` | 3 |
| 5 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`, `tests/unit/test_context_gate_tier.py`, `tests/ARaymond-hook-baseline/baseline.txt` | `sdd_test_helpers.py` | 4 |
| 6 | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh`, `tests/unit/test_context_gate_fallback.py`, `tests/ARaymond-hook-baseline/baseline.txt` | `sdd_test_helpers.py` | 5 |
| 7 | `skills/subagent-driven-development/references/context-handoff-protocol.md`, `skills/subagent-driven-development/references/controller-health-checkpoints.md`, `skills/subagent-driven-development/SKILL.md` | `tests/ARaymond-skill-regression/validate-all-skills.py` | 6 |
| 8 | `CLAUDE.md`, `docs/ARaymond-skills-best-practices.md`, `docs/ARaymond-customization-manifest.md`, `docs/process-improvement-findings/BACKLOG.md` | the hook, the probe | 7 |
| 9 | `tests/integration/sdd-e2e-test.sh` | the hook, fixtures | 8 |
| 10 | (none — verification only; runs test suites, no file writes) | all | 9 |

**Note on the shared files:** Tasks 1–2 both write `context-probe.py`; Tasks 3–6 all write `sdd-pre-dispatch-hook.sh` and `baseline.txt`. Each group is a forced serial chain (each `depends_on` the previous) — never parallel. Every hook-editing task (3, 4, 5, 6) re-captures the hook baseline in its own commit (see Module 2), so `check-hooks.sh` is green at every commit boundary. Task 10 runs `check-hooks.sh` in verify mode only.

- [x] `context-probe.py` returns the correct summed `T` from a fixture transcript (`--transcript`) and resolves via `--session-id`; exits non-zero on the three unavailable cases.
- [x] Hook allows with a normal reminder when `T < SOFT`.
- [x] Hook injects a nudge when `SOFT ≤ T < HARD` on an implementer new-task dispatch.
- [x] Hook blocks (`exit 2`, non-retryable message) when `T ≥ HARD` on an implementer new-task dispatch.
- [x] Hook never nudges/blocks on reviewer / partner / fix / re-review dispatches; a `verification` task IS eligible.
- [x] `--session-id` fallback resolves the transcript for every dispatch class with `transcript_path` omitted (`.session_id` hoisted before classification).
- [x] Every dispatch that reaches the gate appends one line (with `source=<probe|byte-proxy|bypass>`) to `reports/context-observations.log` — blocked-by-prior-check implementer dispatches excepted (they log on the clean re-dispatch), mirroring the spec's pre-parse early-exit carve-out; append failure never breaks a dispatch; tuning excludes non-`probe` rows.
- [x] Probe failure → byte-proxy advisory (degraded, `source=byte-proxy action=fallback`, no crash); `K` consecutive fallbacks escalate to a block + diagnostic.
- [x] Probe parity with `claude-ctx-check` (missing/non-numeric usage → 0; malformed trailing JSONL skipped) pinned by a differential test.
- [x] Reading-across-auto-compaction (reading drops, tier resets) covered by a test.
- [x] Retry + bypass after a hard block is tested.
- [x] `SUPERPOWERS_CTX_SOFT_TOKENS` / `_HARD_TOKENS` / `_FALLBACK_STREAK` override defaults; invalid values fall back with a warning.
- [x] `SUPERPOWERS_CTX_HANDOFF_BYPASS` skips the gate with a stderr warning.
- [x] SDD SKILL.md stays under the hard word limit; hook baseline re-captured; e2e labeled checkout-path proof + post-merge live smoke check noted; regression + unit + e2e green.
- [x] Operational + troubleshooting docs written (CLAUDE.md hook entry + `SUPERPOWERS_CTX_*` env-var list + test counts; skills-best-practices runbook; manifest inventory); BACKLOG N43 → done-pending-merge.
