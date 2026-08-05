---
schema_version: 1
feature_archetype: extension
enforcement_tier: standard
entry_mode: brainstorming
handoff_spawn: auto
source_contracts: "docs/imp-plans/2026-08-04-cmux-spawn-v2-remediation/spec-distilled.md"
shared_constants:
  - path: "handoff_spawn Literal from skills/scripts/models/plan.py"
    value: 'Literal["auto","ask","off"] = "auto"'
    reason: "The consent field already exists on the Plan model; this feature ADDS a coercion validator, not the field. Tasks 1, 5. Do not redefine the value set."
  - path: "SpawnPolicy / Handoff.spawn_policy from skills/scripts/models/sdd_session.py"
    value: 'Literal["auto","ask","off"] = "auto"'
    reason: "Manifest-side consent value; same set as handoff_spawn. Tasks 2, 3."
  - path: "reason codes emitted by spawn-handoff-session.sh"
    value: "policy-off | policy-ask | autospawn-disabled"
    reason: "policy-off/policy-ask already exist (Precondition 2b); autospawn-disabled is added Task 8. Tasks 3, 8, 13."
pattern_references:
  - name: "field-validator-mode-after"
    source_files: ["skills/scripts/models/plan.py"]
    reason: "IntegrationTest.path_must_be_relative_and_safe shows the @field_validator + @classmethod idiom on this codebase's models. The N83 validators use the same idiom with mode='before'. Tasks 1, 2."
  - name: "env-knob-validate-warn-revert"
    source_files: ["skills/subagent-driven-development/scripts/spawn-handoff-session.sh"]
    reason: "Layer-0 knobs (QUOTA_MIN_PCT ~lines 29-33, MAX_STALL_HOPS ~37-38) show the `if ! [[ $VAR =~ ^regex$ ]]; then WARN; VAR=default; fi` house style. AUTOSPAWN mirrors it (but exits 3 on the disable value, not just warn-revert). Task 8."
  - name: "author-doc-declaring-section"
    source_files: ["skills/writing-plans/SKILL.md"]
    reason: "The 'Declaring review_tier per Task' / 'Declaring task_type per Task' / 'Declaring integration_test per Plan' sections are the template the new 'Declaring handoff_spawn per Plan' section must mirror in structure and tone. Task 5."
  - name: "pytest-bash-stub-harness"
    source_files: ["tests/unit/spawn_handoff_helpers.py", "tests/unit/test_spawn_handoff.py"]
    reason: "How spawn-script behavior is unit-tested (PATH stubs, run_spawn driver, ctx dict). Extend this harness for the AUTOSPAWN precondition test; do not build a second one. Task 8."
  - name: "stop-hook-tests"
    source_files: ["tests/unit/test_honesty_log_capture.py"]
    reason: "The N86 fixed-behavior test (test_composes_with_checkpoint_fail_message) already exists here as xfail(strict=True); the N84 log-matching behavior is exercised in TestSpawnOutcomeWarning. Task 11 un-xfails one and adds the N84 metachar test here."
  - name: "regen-check-hooks-baseline"
    source_files: ["tests/ARaymond-hook-baseline/check-hooks.sh", "tests/ARaymond-hook-baseline/baseline.txt"]
    reason: "Baselined-hook edits re-capture with `bash tests/ARaymond-hook-baseline/check-hooks.sh --capture` and commit baseline.txt in the SAME change. Tasks 7 (pre-dispatch) and 11 (stop)."
integration_test:
  path: tests/integration/sdd-e2e-test.sh
modules:
  - id: 1
    title: "Consent model + YAML coercion (N83)"
    task_ids: [0, 1, 2, 3]
    file: module-1-consent-model-coercion.md
  - id: 2
    title: "Plan-time consent UX + author docs"
    task_ids: [4, 5]
    file: module-2-consent-ux-docs.md
  - id: 3
    title: "Discoverability sweep + kill switch"
    task_ids: [6, 7, 8, 9, 10]
    file: module-3-discoverability-killswitch.md
  - id: 4
    title: "Co-located hook papercuts + baseline recapture"
    task_ids: [11, 12, 13]
    file: module-4-hook-papercuts.md
tasks:
  - id: 0
    title: "Contract verification: YAML coercion ground truth + current model/reader shape (BLOCKING)"
    module_id: 1
  - id: 1
    title: "plan.py: handoff_spawn mode=before coercion validator"
    depends_on: [0]
    module_id: 1
    shared_constants_used: ["handoff_spawn Literal from skills/scripts/models/plan.py"]
    pattern_references: ["field-validator-mode-after"]
  - id: 2
    title: "sdd_session.py: Handoff.spawn_policy mode=before coercion validator"
    depends_on: [0]
    module_id: 1
    shared_constants_used: ["SpawnPolicy / Handoff.spawn_policy from skills/scripts/models/sdd_session.py"]
    pattern_references: ["field-validator-mode-after"]
  - id: 3
    title: "materialize-manifest.py: normalize False to off + cross-reader proof at validators.py layer"
    depends_on: [1, 2]
    module_id: 1
    shared_constants_used: ["SpawnPolicy / Handoff.spawn_policy from skills/scripts/models/sdd_session.py", "reason codes emitted by spawn-handoff-session.sh"]
  - id: 4
    title: "brainstorming/SKILL.md step 3.5: execution-mode consent prompt"
    depends_on: [3]
    module_id: 2
    review_tier: minimum
  - id: 5
    title: "writing-plans/SKILL.md: extract-to-references then add Declaring handoff_spawn + Step 0.5 + frontmatter var"
    depends_on: [4]
    module_id: 2
    review_tier: minimum
    pattern_references: ["author-doc-declaring-section"]
  - id: 6
    title: "SDD SKILL.md Context Health Protocol: name cmux auto-spawn as default block-response (ceiling-safe)"
    depends_on: [5]
    module_id: 3
    review_tier: minimum
  - id: 7
    title: "sdd-pre-dispatch-hook.sh: name spawn-handoff-session.sh in SOFT nudge + HARD block (baselined, recapture)"
    depends_on: [6]
    module_id: 3
    pattern_references: ["regen-check-hooks-baseline"]
  - id: 8
    title: "spawn-handoff-session.sh: SUPERPOWERS_CMUX_AUTOSPAWN precondition 0 (reason=autospawn-disabled)"
    depends_on: [7]
    module_id: 3
    shared_constants_used: ["reason codes emitted by spawn-handoff-session.sh"]
    pattern_references: ["env-knob-validate-warn-revert", "pytest-bash-stub-harness"]
  - id: 9
    title: "Env-registry docs: context-handoff-protocol.md + CLAUDE.md add SUPERPOWERS_CMUX_AUTOSPAWN"
    depends_on: [8]
    module_id: 3
    review_tier: minimum
  - id: 10
    title: "Skill-awareness audit: record which skills know about auto-spawn"
    depends_on: [9]
    module_id: 3
    review_tier: minimum
  - id: 11
    title: "sdd-stop-hook.sh: N84 grep escape + N86 fail-closed gate + un-xfail (baselined, recapture)"
    depends_on: [10]
    module_id: 4
    pattern_references: ["stop-hook-tests", "regen-check-hooks-baseline"]
  - id: 12
    title: "write-mechanics-card.py: N85 sys.executable regen line + validated MAX_HOPS ceiling"
    depends_on: [11]
    module_id: 4
    review_tier: minimum
  - id: 13
    title: "e2e AUTOSPAWN step + doc maintenance + full-suite verification"
    depends_on: [12]
    module_id: 4
    review_tier: minimum
---

# cmux-spawn-v2 Remediation — Implementation Plan (Parent / Coordination)

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first — direct implementation bypasses review enforcement, quality gates, and hooks.

**Goal:** Make cmux auto-spawn the discoverable, documented default of the SDD execution model — a mandatory plan-time execution-mode choice, proactive discoverability in skill bodies and gate messages, the N83 unquoted-`off` YAML coercion fix, a clean `SUPERPOWERS_CMUX_AUTOSPAWN` kill switch — plus three co-located hook/card papercuts (N84/N86/N85) while the files are open. **No default value changes** (`handoff_spawn` stays `auto`).

**Architecture:** Extension archetype across four sequential modules. Module 1 fixes the consent model (Pydantic `mode="before"` validators + materialize normalization) so unquoted `off` is accepted at the model boundary. Module 2 surfaces the consent choice at both plan entry points and documents it for authors. Module 3 makes the capability discoverable (skill bodies + hook messages) and adds the runtime kill switch. Module 4 ships the co-located hook papercuts and re-captures the hook baseline. Modules are **strictly sequential** (M1→M2→M3→M4): M2's author doc references M1's fix, and M3 and M4 both re-capture the single shared `baseline.txt` so they must serialize.

**Tech Stack:** Python 3 (stdlib + Pydantic v2 in the venv), Bash 3.2 (hook + spawn scripts, no `set -u/-e/pipefail`), Markdown skill bodies, pytest.

**Source Contracts:** None

(This is a coordination document. The distilled spec `docs/imp-plans/2026-08-04-cmux-spawn-v2-remediation/spec-distilled.md` — Contract Facts, scope fences, Decision Summary, Component Specs C1–C5 — is the feature's source contract; it is declared in this plan's `source_contracts` frontmatter and verified in Module 1's Task 0.)

**Contract Constraints (non-negotiable):**
- `handoff_spawn` is a plan-level `Literal["auto","ask","off"]` (default `auto`) on the `Plan` model; `spawn_policy` is the same on the `SddSession` manifest model's nested `Handoff`. **Do not change the value set or the default.**
- PyYAML 6.0.3 (YAML 1.1) coerces unquoted `off`→`False`, `on`→`True`, `no`→`False`, `yes`→`True` (empirically verified 2026-08-04). Quoted `"off"`→`'off'` (str, unchanged). The fix: `mode="before"` validators map `False`→`"off"` and **reject** `True` with an actionable message. Quoted `"off"` must remain untouched.
- The plan gate's real pydantic rejection is **Gate 1b** in `plan-validation-gate-hook.sh` (line ~193): `$PYTHON validators.py plan <file>` under the **venv** python. `validate-plan.py`'s own embedded pydantic subprocess (Gate 1, line ~165) runs under **bare `python3`** and is inert (no pydantic) in production. Therefore the primary test layer is **`validators.py plan <file>`** (exit 0 on unquoted `off`, exit 1 on `on`) — NOT `validate-plan.py --plan-file`, which passes under pytest for a different reason than in production.
- `validate-plan.py` is invoked with **bare `python3`** by the plan gate and MUST stay stdlib-only. Do not add an eager pydantic import to any module the gate imports (`validate-plan.py`, `_report_utils`). The N83 fix lives in the models (`plan.py`, `sdd_session.py`) + `materialize-manifest.py`, none of which `validate-plan.py` imports.
- Reason codes emitted by `spawn-handoff-session.sh`: `policy-off`, `policy-ask` (existing, Precondition 2b), `autospawn-disabled` (new, Precondition 0). The kill switch exits **3** (manual fallback), before the cmux-reachability check, and does **not** call `cmux notify` (parallels the 2b consent refusals — nothing is reserved).
- **Word ceiling:** `subagent-driven-development/SKILL.md` is at 4993/5000 words; `writing-plans/SKILL.md` at 4726. Every SKILL.md addition must be offset by extracting existing content to `references/` **first** (verify with an explicit `wc -w` number — the regression test's PASS is advisory, not proof of staying under the hard limit).
- **Baselined hooks:** `sdd-pre-dispatch-hook.sh` (Task 7) and `sdd-stop-hook.sh` (Task 11) are baselined. Each edit re-captures `tests/ARaymond-hook-baseline/baseline.txt` (`bash tests/ARaymond-hook-baseline/check-hooks.sh --capture`) in the **same commit**. `spawn-handoff-session.sh` and `write-mechanics-card.py` are **not** baselined.

**Shared Constants:** See YAML frontmatter `shared_constants`. The consent value set (`auto`/`ask`/`off`) is defined once per model — import/reference, do not re-list a new copy.

**Pattern References:** See YAML frontmatter `pattern_references`. Established idioms to follow: `@field_validator` + `@classmethod` (plan.py IntegrationTest), env-knob validate-warn-revert (spawn-handoff-session.sh Layer 0), the "Declaring X per Task/Plan" author sections (writing-plans/SKILL.md), the pytest bash-stub harness, the stop-hook test patterns, and the baseline re-capture command.

**Feature Archetype:** Extension. Adds validators, a prompt, an author-doc section, hook-message wording, a script precondition, and env-doc entries. One small behavior change (the `handoff_spawn` YAML coercion). **Nothing becomes obsolete** — no Obsolescence Verification task required.

**Code Footprint:**

| Category | Files / Functions | Action | Dependencies to Verify |
|----------|------------------|--------|----------------------|
| Modified | `skills/scripts/models/plan.py` (`Plan.handoff_spawn`) | Add `mode="before"` validator | Consumers: `validators.py`, `materialize-manifest.py` (both re-read raw frontmatter independently) |
| Modified | `skills/scripts/models/sdd_session.py` (`Handoff.spawn_policy`) | Add `field_validator` import + `mode="before"` validator | Consumer: `materialize-manifest.py` constructs `SddSession(handoff=...)` |
| Modified | `skills/subagent-driven-development/scripts/materialize-manifest.py` (handoff block, ~lines 117-122) | Normalize `False`→`"off"` | Reader: `spawn-handoff-session.sh` via `spawn-policy` support CLI |
| Modified | `skills/brainstorming/SKILL.md` (step 3.5) | Add consent prompt | Records choice into spec (plan execution variable) |
| Modified | `skills/writing-plans/SKILL.md` | Extract to `references/` + add "Declaring handoff_spawn" + Step 0.5 + frontmatter var | Word ceiling |
| Modified | `skills/subagent-driven-development/SKILL.md` (Context Health Protocol) | Extract to `references/` + rewrite pointer | Word ceiling (4993/5000) |
| Modified | `skills/subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh` (SOFT nudge, HARD block) | Reword to name auto-spawn | **Baselined** — recapture `baseline.txt` |
| Modified | `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` (new Precondition 0) | Add `SUPERPOWERS_CMUX_AUTOSPAWN` | Not baselined |
| Modified | `skills/subagent-driven-development/scripts/sdd-stop-hook.sh` (line ~89 grep, line ~181 gate) | N84 escape + N86 fail-closed | **Baselined** — recapture `baseline.txt` |
| Modified | `skills/subagent-driven-development/scripts/write-mechanics-card.py` (lines ~76, ~93) | N85 display fixes | Not baselined |
| Modified | `skills/subagent-driven-development/references/context-handoff-protocol.md` (Env knobs), `CLAUDE.md` (env registry) | Document `SUPERPOWERS_CMUX_AUTOSPAWN` | — |
| Modified | `tests/integration/sdd-e2e-test.sh` | Add AUTOSPAWN precondition step | C2 Check 10 (declared integration test must be in changeset) |
| New/Modified | Tests in `tests/unit/test_models/test_plan_model.py` (`TestHandoffSpawn`), `tests/unit/test_models/test_sdd_session_model.py` (`TestHandoffBlock`), `tests/unit/test_materialize_manifest.py` (`TestHandoffBlockMaterialization` — flip pre-fix test), `tests/unit/test_spawn_handoff*.py`, `tests/unit/test_honesty_log_capture.py`, `tests/unit/test_n83_yaml_contract.py` (new), card test | Extend existing / add | Do NOT create flat-path `tests/unit/test_plan_model.py` (collision) |

## Module Inventory

1. **`module-1-consent-model-coercion.md`** (Tasks 0–3) — the N83 fix at the model boundary + materialize normalization + per-reader proof. Contract foundation.
2. **`module-2-consent-ux-docs.md`** (Tasks 4–5) — plan-time consent choice at both entry points + the author doc.
3. **`module-3-discoverability-killswitch.md`** (Tasks 6–10) — SDD SKILL.md + hook-message discoverability, the `SUPERPOWERS_CMUX_AUTOSPAWN` kill switch, env docs, skill-awareness audit.
4. **`module-4-hook-papercuts.md`** (Tasks 11–13) — N84/N86 (stop hook, combined) + N85 (card) + e2e + doc maintenance + full-suite verification.

## Module Dependency Graph

```
Module 1 (consent model + coercion)     Tasks 0-3   — contract foundation
  └── Module 2 (consent UX + docs)       Tasks 4-5   — author doc references M1's fix
        └── Module 3 (discoverability     Tasks 6-10  — Task 7 recaptures baseline.txt
             + kill switch)
              └── Module 4 (papercuts)    Tasks 11-13 — Task 11 recaptures baseline.txt

Parallel candidates: NONE. Strictly sequential.
Rationale: (1) M2's "Declaring handoff_spawn" doc states that off is unquoted-safe
POST-N83, so M1 must land first. (2) baseline.txt is written by Task 7 (M3) AND
Task 11 (M4); a single shared file cannot be owned by two parallel modules, so
M3 must complete before M4.
```

## Shared Contract Section (cross-module)

- **`tests/ARaymond-hook-baseline/baseline.txt`** — written by Task 7 (after the pre-dispatch-hook edit) and again by Task 11 (after the stop-hook edit). Each re-capture re-pins ALL seven hook hashes; the second capture (Task 11) legitimately keeps Task 7's already-updated pre-dispatch hash. **Serialization is mandatory: Task 7 before Task 11** (guaranteed by the sequential module order). Never run these two tasks in parallel.
- **The consent value set `auto`/`ask`/`off`** — defined once in `plan.py` (`handoff_spawn`) and once in `sdd_session.py` (`SpawnPolicy`). Tasks 5, 6, 9, 13 (docs) must quote these values verbatim; they must not introduce a fourth value or rename one.
- **`context-handoff-protocol.md`** — cited by the SDD SKILL.md pointer (Task 6), the hook HARD-block message (Task 7), and gets the AUTOSPAWN env entry (Task 9). Keep the file path citation stable.

## Acceptance Criteria (feature-level; each module repeats its own subset)

- [x] Unquoted `handoff_spawn: off` passes `validators.py plan <file>` (exit 0) and yields `spawn_policy: off` in the materialized manifest and a `reason=policy-off` refusal from the script; `handoff_spawn: on` is rejected with an actionable message; quoted `"off"` is unchanged.
- [x] Brainstorming presents the execution-mode choice at the feature-name step; writing-plans presents it (direct path) and writes `handoff_spawn` into plan frontmatter; `writing-plans/SKILL.md` has a "Declaring `handoff_spawn` per Plan" section listing it as a mandatory execution variable.
- [x] SDD `SKILL.md` names the cmux auto-spawn as the default block-response (proactive discovery); both the SOFT nudge and HARD block hook messages name `spawn-handoff-session.sh` as the default response with manual as the alternative.
- [x] A skill-awareness audit result is recorded for every skill assessed (SDD, writing-plans, brainstorming, executing-plans, using-superpowers).
- [x] `SUPERPOWERS_CMUX_AUTOSPAWN=0` makes the spawn script exit 3 with `reason=autospawn-disabled` before the cmux-reachability check; documented in both env registries.
- [x] N84 (`$BID` regex-safe), N86 (checkpoint gate fail-closed; the `xfail(strict=True)` tripwire un-marked and passing), N85 (card `sys.executable` + validated ceiling) fixed; hook baseline re-captured in the same commit as each baselined-hook edit.
- [x] All suites green (unit, e2e, regression, install, hook baseline); SKILL.md additions offset by `references/` extraction (an explicit `wc -w` number recorded per SKILL.md edit, under 5000).
- [x] BACKLOG rows N55, N83, N84, N85, N86 updated/closed at merge (flag-not-overwrite; BACKLOG.md may be owned by a concurrent session).
