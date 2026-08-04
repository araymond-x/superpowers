# cmux-spawn-v2 Remediation — Distilled Implementation Spec

> **Source:** `spec.md` (approved 2026-08-04, extension archetype, 6 decisions). See it for full decision reasoning.
> **Planning disposition:** `planning-append.md` (right-sizing: `review_tier: minimum` for doc tasks; full review only for N83 coercion, `SUPERPOWERS_CMUX_AUTOSPAWN`, and the baselined-hook edits).
> **Distilled:** 2026-08-04
> **For:** Plan writer and implementation agents ONLY.
> **Note on size:** the source is already exploration-free at 117 lines; this document reorganizes (contract facts promoted, scope fences made explicit, carrier named), it does not compress. The <40% line target does not apply — no fence item, decision, or acceptance criterion is dropped to hit it.

## Out of scope — do not build

- **Changing the default value.** `auto` remains the default; this is doctrine + discoverability, not a behavior flip. → out of scope
- **cmux capability / runtime enhancements**: N56 (open-loop liveness), N58 (re-vendor cmux skills), N60 (enumerate cmux CLI surface), N64 (resumes-from-committed vs dirty-tree), N66 (sidebar telemetry), N67 (`new-workspace --env`), N68 (wrapper posture), N69 (workspace-group), N70 (deprecated-verb migration), N71 (todo mirror), N72 (capability-drift guard), N74 (session-label continuity). → future sprints
- **Codex-picker parity** (N51 — codex-side auto-spawn). → separate, blocked on codex-SDD triggering
- **Per-task `handoff_spawn` granularity.** Consent is plan-level (whole feature); handoffs happen at task boundaries. → out of scope
- **Wiring the spawn into a hook** (machine-driven auto-execution). The spawn stays agent-driven; only the hook *messages* change. → out of scope

## Contract Facts

**Consent field types:**
- `handoff_spawn` — plan-level `Literal["auto","ask","off"]`, default `auto`, on the `Plan` model (`plan.py`). A mandatory plan execution variable (materialized into plan frontmatter alongside `enforcement_tier`).
- `spawn_policy` — same `Literal["auto","ask","off"]` on the `SddSession` (manifest) model (`sdd_session.py`).

**YAML coercion (N83):** unquoted `off`→`False` and `on`→`True` under PyYAML 1.1. A `mode="before"` field validator (on `handoff_spawn` in `plan.py`, on `spawn_policy` in `sdd_session.py`) maps `False`→`"off"` and rejects `True` with an actionable message ("bare `on` is YAML 1.1 True; use one of auto/ask/off"). `materialize-manifest.py`'s existing `if spawn_policy is None` guard also normalizes `False`→`"off"`. `validate-plan.py` (the plan gate) runs the `Plan` model **before** `materialize-manifest.py`, so a materialize-only coercion is unreachable — the fix must live at the model boundary.

**Runtime reason codes** (emitted by `spawn-handoff-session.sh`): `reason=policy-off`, `reason=policy-ask`, `reason=autospawn-disabled`.

**Kill switch:** `SUPERPOWERS_CMUX_AUTOSPAWN` — when `0`/`false`, script exits 3 with `reason=autospawn-disabled` ("auto-spawn disabled by config — resume manually"), checked as **precondition 0** before cmux reachability. Regex-validated, fail-safe like the other knobs. Plan-less per-run opt-out; complementary to plan-level durable `handoff_spawn: off`.

**Consent-choice carrier:** the plan-time mode choice threads brainstorming → writing-plans via the spec / distilled spec as a **plan execution variable** — the same carrier `entry_mode` / `enforcement_tier` already use — NOT session memory (which does not survive a separate writing-plans invocation).

**Implementation constraints (contract, from source §6):**
- **Word ceiling:** SDD and writing-plans `SKILL.md` sit near the hard word-count limit. Offset every addition by extracting existing content to `references/` first (verify with `wc -w`; the regression test enforces it).
- **Baselined hooks:** `sdd-pre-dispatch-hook.sh` and `sdd-stop-hook.sh` are baselined — any edit re-captures `tests/ARaymond-hook-baseline/baseline.txt` (`check-hooks.sh --capture`) in the same commit.
- **Stdlib constraint:** hook scripts importing PyYAML/Pydantic use `$PYTHON` (venv), not system `python3`. But `validate-plan.py` is invoked with bare `python3` by the plan gate, so the `plan.py` validator addition must keep `validate-plan.py` stdlib-only (the model import chain must stay lazy where it already is — do not add an eager pydantic import).
- **BACKLOG ownership:** BACKLOG.md may be owned by a concurrent session — flag rather than overwrite; file/close rows N55/N83/N84/N85/N86 at merge.

## Open Decisions

| # | Decision | Options | Resolution Required By |
|---|----------|---------|----------------------|
| 1 | `handoff_spawn` value for THIS feature's own plan (its own execution) | auto / ask / off | writing-plans Step 0.5 (direct path) — the new mode-choice UX is not yet installed during this feature's planning, so present or default explicitly at plan time |

## Decision Summary

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Sprint scope | Core (caveats 1–4 + 3 discovery gaps + N55 + N83) + co-located hook fixes N84/N86/N85; excludes cmux capability/runtime items |
| 2 | Where to surface the consent choice | Both entry points (brainstorming 3.5 + writing-plans 0.5), materialized once in writing-plans |
| 3 | Default value | Unchanged — `auto` stays the default |
| 4 | N83 fix location | `mode="before"` validator at the model boundary (`plan.py` + `sdd_session.py`) + `materialize-manifest.py` normalization |
| 5 | Kill switch vs plan dial | Add `SUPERPOWERS_CMUX_AUTOSPAWN` (runtime, per-run) alongside the existing `handoff_spawn: off` (plan-level, durable) |
| 6 | Hook wiring | Keep the spawn agent-driven; change only the hook *messages* |

## Component Specifications

### C1 — Consent model + YAML coercion (N83) [full review]
`mode="before"` field validator on `handoff_spawn` (`plan.py`) and `spawn_policy` (`sdd_session.py`): `False`→`"off"`; `True` rejected with actionable message. `materialize-manifest.py` `if spawn_policy is None` guard normalizes `False`→`"off"` for defense in depth. Every reader accepts unquoted `off` as the off policy.
**Verification (per reader):** `validate-plan.py` on unquoted `off` PASSES the `handoff_spawn` field; `materialize-manifest.py` produces `spawn_policy: "off"`; `spawn-handoff-session.sh` refuses with `reason=policy-off`. Positive control: `handoff_spawn: on` → clear rejection. Negative control: quoted `"off"` unchanged.

### C2 — Plan-time consent UX + author docs
- **Brainstorming** — `brainstorming/SKILL.md` step 3.5, right after the feature name: present the mode choice (default `auto`, options `ask` / `off`-manual), record the answer in the spec (→ distilled spec) as a plan execution variable. Same "press enter to accept the default" interaction as the feature-name prompt.
- **Direct path** — `writing-plans/SKILL.md` Step 0.5: if the mode was not chosen upstream, present the same choice.
- **Materialization** — writing-plans writes `handoff_spawn: <choice>` into plan YAML frontmatter as a mandatory execution variable, listed alongside `enforcement_tier` in the plan-header conventions.
- **Author doc** — new **"Declaring `handoff_spawn` per Plan"** section in `writing-plans/SKILL.md`, mirroring the `review_tier` / `task_type` / `integration_test` sections: the three values' meaning, that `auto` is default, that `off` is unquoted-safe post-N83, and runtime effects (`reason=policy-ask` / `policy-off`).
- **The three values (plain language):** `auto` — successor SDD session spawns automatically in cmux when context fills; degrades to manual when cmux unreachable. `ask` — auto-spawn but the script refuses without `--user-approved` (controller asks the user each hop). `off` — never auto-spawn; controller does the manual handoff (build bundle → user `/pickup`) at each boundary.

### C3 — Discoverability sweep
- **SDD `SKILL.md` Context Health Protocol** — rewrite the pointer so a controller learns proactively (on reading the skill, before the gate fires) that the *default* block-response is the cmux auto-spawn (with manual fallback), citing `context-handoff-protocol.md`.
- **Hook messages** (`sdd-pre-dispatch-hook.sh`) — SOFT nudge and HARD block currently name only the manual flow; update both to name the auto-spawn mechanism (`spawn-handoff-session.sh <bundle>` per `context-handoff-protocol.md`) as the default response, manual as the alternative. HARD block stays stop-and-hand-off (not fix-and-retry); it just names the auto path first.
- **Skill-awareness audit** — enumerate which skills "need to know" and confirm each carries the awareness: SDD, writing-plans, brainstorming (edited here); assess `executing-plans` (does its flow reach the gate?) and `using-superpowers` (bootstrap — likely no change). Record the audit result even where no edit is needed.

### C4 — Clean kill switch (N55 remainder)
Add `SUPERPOWERS_CMUX_AUTOSPAWN` as precondition 0 in `spawn-handoff-session.sh` (before cmux reachability): `0`/`false` → exit 3, `reason=autospawn-disabled` ("auto-spawn disabled by config — resume manually"), never a borrowed "hop limit reached". Regex-validated, fail-safe. Documented in the `context-handoff-protocol.md` env-knob registry and the CLAUDE.md env-var registry. (The `MAX_HOPS` fail-open half of N55 was already fixed in `7425e38`.)

### C5 — Co-located hook papercuts + baseline recapture
- **N84** — `sdd-stop-hook.sh` interpolates `$BID` into `grep -qE` unescaped; switch to `grep -qF` (fixed strings) or `printf '%q'`-escape.
- **N86** — `sdd-stop-hook.sh`'s checkpoint-prerequisite gate silently swallows a genuine FAIL; make it fail-closed on the swallowed condition; verify against the existing `xfail(strict=True)` tripwire.
- **N85** — `write-mechanics-card.py` regen line emits literal `$PYTHON` (→ `sys.executable`) and the ceiling line renders `SUPERPOWERS_CMUX_MAX_HOPS` unvalidated (→ the script's validated value), for card↔script consistency.
- Editing any baselined hook re-captures `tests/ARaymond-hook-baseline/baseline.txt` in the same change.

## Acceptance Criteria

- [ ] Unquoted `handoff_spawn: off` in a plan passes `validate-plan.py`'s `handoff_spawn` field and yields `spawn_policy: off` in the manifest and a `reason=policy-off` refusal from the script; `handoff_spawn: on` is rejected with an actionable message; quoted `"off"` is unchanged.
- [ ] Brainstorming presents the execution-mode choice at the feature-name step; writing-plans presents it (direct path) and writes `handoff_spawn` into plan frontmatter.
- [ ] `writing-plans/SKILL.md` has a "Declaring `handoff_spawn` per Plan" section; the plan-header convention lists `handoff_spawn` as a mandatory execution variable.
- [ ] SDD `SKILL.md` names the cmux auto-spawn as the default block-response (proactive discovery); both the SOFT nudge and HARD block hook messages name `spawn-handoff-session.sh` as the default response with manual as the alternative.
- [ ] A skill-awareness audit result is recorded for every skill assessed (SDD, writing-plans, brainstorming, executing-plans, using-superpowers).
- [ ] `SUPERPOWERS_CMUX_AUTOSPAWN=0` makes the spawn script exit 3 with `reason=autospawn-disabled` before the cmux-reachability check; documented in both env registries.
- [ ] N84 (`grep -qF`), N86 (checkpoint gate fail-closed, tripwire green), N85 (card `sys.executable` + validated ceiling) fixed; hook baseline re-captured in the same change.
- [ ] All suites green (unit, e2e, regression, install, hook baseline); SKILL.md additions offset by `references/` extraction (word ceiling respected).
- [ ] BACKLOG rows N55, N83, N84, N85, N86 updated/closed at merge.
