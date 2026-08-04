# cmux-spawn-v2 Remediation — Design Spec

> **Status:** approved design (brainstorming), 2026-08-04
> **Archetype:** extension (adds to existing skills/hooks/models/docs; one small behavior change — the `handoff_spawn` YAML coercion — nothing becomes obsolete)
> **Predecessor:** `docs/imp-plans/2026-07-30-cmux-spawn-v2/` (shipped the cmux auto-spawn handoff, N43(D), merged 2026-08-03 `7f5c1a9`)

## 1. Problem

cmux auto-spawn shipped and works, but it is **invisible and undocumented as an execution mode**. Six concrete gaps, all confirmed against the merged code:

1. **No auto-loaded skill body mentions auto-spawn.** No `SKILL.md` changed in the predecessor feature. The SDD SKILL.md Context-Health pointer and both hook messages (SOFT nudge, HARD block) describe only the *manual* handoff ("build a fresh-session handoff… tell the user to run `/pickup`… STOP"). The auto-spawn is discovered **only** by reading the cited `context-handoff-protocol.md`.
2. **The `handoff_spawn` consent dial is undocumented for plan authors.** `writing-plans/SKILL.md` documents `review_tier`, `task_type`, `integration_test` — but not `handoff_spawn`. It exists only in `plan.py` and `materialize-manifest.py`. A plan author cannot discover the opt-in/opt-out from any skill doc. (BACKLOG **N55**.)
3. **Discovery is entirely reactive.** Nothing proactively tells a controller "cmux auto-spawn exists" — it surfaces only when the context gate fires, in a cmux-reachable session.
4. **The `off` opt-out has a YAML footgun.** Unquoted `handoff_spawn: off` → PyYAML 1.1 coerces to `False` → the plan-validation gate FAILs with a `Got: False` error. Safe (never silently auto-spawns) but a trap on the headline consent value. (BACKLOG **N83**.)
5. **No clean plan-less per-run kill switch.** To disable without editing the plan, today's only options are `SUPERPOWERS_CMUX_MAX_HOPS=0` (repurposes the runaway guard) or not being in cmux — both side-effect opt-outs. A clean `SUPERPOWERS_CMUX_AUTOSPAWN` was proposed in N55 but not built.
6. **No plan-time consent choice.** A plan author is never *asked* whether this feature should auto-spawn; `auto` is applied silently by default.

The user's intent: **auto-spawn is the documented default of the SDD execution model going forward**, every skill that needs to know is aware of it, and the plan author is offered a first-class manual opt-out at plan time — surfaced alongside the feature name and the other mandatory plan execution variables.

## 2. Goals

- Make auto-spawn the **explicit, documented default** execution mode (doctrine + discoverability), **without changing the default value** (`handoff_spawn` stays `auto`).
- Present the plan author a **mandatory execution-mode choice** (auto / ask / manual-`off`) at plan time, at both plan entry points, materialized into plan frontmatter.
- Make the capability **discoverable proactively** — in auto-loaded skill bodies and in the gate messages — not only by reading the runtime protocol doc when blocked.
- Close the consent ergonomics: fix the YAML footgun (N83) and add a clean plan-less kill switch (N55 remainder).
- Ship the co-located hook papercuts (N84, N86, N85) while their files are open.

## 3. Non-goals / Out of scope — do not build

- **Changing the default value.** `auto` remains the default; this is doctrine + discoverability, not a behavior flip. → out of scope
- **cmux capability / runtime enhancements**: N56 (open-loop liveness), N58 (re-vendor cmux skills), N60 (enumerate cmux CLI surface), N64 (resumes-from-committed vs dirty-tree), N66 (sidebar telemetry), N67 (`new-workspace --env`), N68 (wrapper posture), N69 (workspace-group), N70 (deprecated-verb migration), N71 (todo mirror), N72 (capability-drift guard), N74 (session-label continuity). → future sprints
- **Codex-picker parity** (N51 — codex-side auto-spawn). → separate, blocked on codex-SDD triggering
- **Per-task `handoff_spawn` granularity.** Consent is plan-level (whole feature); handoffs happen at task boundaries. → out of scope
- **Wiring the spawn into a hook** (machine-driven auto-execution). The spawn stays agent-driven; only the hook *messages* change. → out of scope

## 4. Design

### 4.1 Consent model + YAML coercion (caveat 2 / N83)

`handoff_spawn` is a plan-level `Literal["auto","ask","off"]` (default `auto`) on the `Plan` model; `spawn_policy` is the same on the `SddSession` (manifest) model. The footgun: PyYAML (YAML 1.1) coerces unquoted `off`→`False`, `on`→`True`, and the Literal rejects the booleans. `validate-plan.py` (the plan gate) runs the Pydantic `Plan` model and rejects the unquoted value **before** `materialize-manifest.py` runs — so a materialize-only coercion is never reached.

**Fix:** a `mode="before"` field validator on `handoff_spawn` (in `plan.py`) and on `spawn_policy` (in `sdd_session.py`) that maps `False`→`"off"` and rejects `True` (bare `on` is not a valid mode) with an actionable message ("bare `on` is YAML 1.1 True; use one of auto/ask/off"). `materialize-manifest.py`'s existing `if spawn_policy is None` guard also normalizes `False`→`"off"` for defense in depth. Every reader accepts unquoted `off` as the off policy.

**Verification:** unit tests per reader — `validate-plan.py` on unquoted `off` PASSES the `handoff_spawn` field; `materialize-manifest.py` produces `spawn_policy: "off"`; `spawn-handoff-session.sh` refuses with `reason=policy-off`. A positive control (`handoff_spawn: on` → clear rejection) and a negative control (quoted `"off"` unchanged) are included.

### 4.2 Plan-time consent UX (goal: mandatory choice at both entry points)

Two entry paths reach a plan; the choice is presented at both and materialized once.

- **Brainstorming path** — `brainstorming/SKILL.md` step 3.5, immediately after the feature name is established: present the mode choice (default `auto`, options `ask` / `off`-manual), and **record the answer in the spec (and thus the distilled spec) as a plan execution variable**, so writing-plans reads it from the distilled spec — the same carrier `entry_mode`/`enforcement_tier` already flow through (not session memory, which does not survive a separate writing-plans invocation). Follows the same "press enter to accept the default" interaction as the feature-name prompt.
- **Direct path** (`entry_mode: direct`) — `writing-plans/SKILL.md` Step 0.5 ("Resolve feature directory"): if the mode was not already chosen upstream, present the same choice.
- **Materialization** — `writing-plans` writes `handoff_spawn: <choice>` into the plan's YAML frontmatter as a **mandatory execution variable**, listed alongside `enforcement_tier` in the plan header conventions.
- **Author doc** — new **"Declaring `handoff_spawn` per Plan"** section in `writing-plans/SKILL.md`, mirroring the existing `review_tier` / `task_type` / `integration_test` sections: what the three values mean, that `auto` is the default, that `off` must be written unquoted-safe (post-N83 it is), and the runtime effects (`reason=policy-ask`/`policy-off`).

The three values, presented to the user in plain language:
- **`auto` (default)** — the successor SDD session spawns automatically in cmux when the controller's context fills; degrades to manual when cmux is unreachable.
- **`ask`** — auto-spawn, but the script refuses without `--user-approved`, so the controller must ask the user first each hop.
- **`off`** — never auto-spawn; the controller performs the manual handoff (build bundle → user `/pickup`) at each boundary.

### 4.3 Discoverability sweep (caveat 1 + gaps 1 & 3)

- **SDD `SKILL.md` Context Health Protocol**: rewrite the pointer so a controller learns, on reading the skill (i.e. proactively, before the gate fires), that the *default* block-response is the cmux auto-spawn (with the manual fallback), citing `context-handoff-protocol.md`.
- **Hook messages** (`sdd-pre-dispatch-hook.sh`): the SOFT nudge and HARD block currently name only the manual flow. Update both to **name the auto-spawn mechanism** (`spawn-handoff-session.sh <bundle>` per `context-handoff-protocol.md`) as the default response, with manual as the alternative. The HARD block remains a stop-and-hand-off (not a fix-and-retry); it simply names the auto path first.
- **Skill-awareness audit**: enumerate which skills "need to know" and confirm each carries the awareness — SDD, writing-plans, brainstorming (edited here); assess `executing-plans` (the parallel-session variant — does its flow reach the gate?) and `using-superpowers` (bootstrap — likely no change). Record the audit result even where no edit is needed, so the "which skills know" question has a durable answer.

### 4.4 Clean kill switch (caveat 4 / N55 remainder)

Add `SUPERPOWERS_CMUX_AUTOSPAWN` as **precondition 0** in `spawn-handoff-session.sh` (checked before cmux reachability): when set to `0`/`false`, the script exits 3 with an honest `reason=autospawn-disabled` message ("auto-spawn disabled by config — resume manually"), never a borrowed "hop limit reached". Regex-validated and fail-safe like the other knobs. Documented in the `context-handoff-protocol.md` env-knob registry and the CLAUDE.md env-var registry. (The `MAX_HOPS` fail-open half of N55 was already fixed in `7425e38`; this closes the remainder.)

This is the **plan-less, per-run** opt-out; `handoff_spawn: off` remains the **plan-level, durable** opt-out. They are complementary, not redundant.

### 4.5 Co-located hook papercuts (opportunistic)

Bundled because they edit files this sprint already touches (and `sdd-stop-hook.sh` is baselined — one re-capture amortizes all hook edits):

- **N84** — `sdd-stop-hook.sh` interpolates `$BID` into `grep -qE` unescaped; switch to `grep -qF` (fixed strings) or `printf '%q'`-escape.
- **N86** — `sdd-stop-hook.sh`'s checkpoint-prerequisite gate silently swallows a genuine FAIL; make it fail-closed on the swallowed condition; verify against the existing `xfail(strict=True)` tripwire.
- **N85** — `write-mechanics-card.py` regen line emits literal `$PYTHON` (→ `sys.executable`) and the ceiling line renders `SUPERPOWERS_CMUX_MAX_HOPS` unvalidated (→ the script's validated value), for card↔script consistency.

Editing any baselined hook requires re-capturing `tests/ARaymond-hook-baseline/baseline.txt` in the same change.

## 5. Module structure (proposed; the plan writer finalizes)

1. **Consent model + coercion (N83)** — `plan.py`/`sdd_session.py` `mode="before"` validators, `materialize-manifest.py` normalization, per-reader tests. Contract foundation (likely Task 0 verifying the current model shape).
2. **Plan-time consent UX + author docs** — brainstorming 3.5 prompt, writing-plans Step 0.5 + "Declaring `handoff_spawn`" section + frontmatter materialization + plan-header convention.
3. **Discoverability sweep + kill switch** — SDD SKILL.md Context-Health rewrite, hook nudge/block message updates, `SUPERPOWERS_CMUX_AUTOSPAWN` precondition-0, env-registry docs, skill-awareness audit.
4. **Co-located hook papercuts + baseline recapture (N84/N86/N85)** — plus e2e coverage and doc maintenance.

## 6. Constraints

- **Word ceiling:** SDD and writing-plans `SKILL.md` sit near the hard word-count limit. Every addition must be offset by extracting existing content to `references/` first (verify with `wc -w`; the regression test enforces it).
- **Baselined hooks:** `sdd-pre-dispatch-hook.sh` and `sdd-stop-hook.sh` are baselined — any edit re-captures `baseline.txt` in the same commit.
- **`$PYTHON` in hooks:** hook scripts that import PyYAML/Pydantic must use `$PYTHON` (the venv python), not system `python3`. But `validate-plan.py` is invoked with bare `python3` by the plan gate, so the `plan.py` validator addition must keep `validate-plan.py` stdlib-only (the model import chain must stay lazy where it already is).
- **BACKLOG ownership:** BACKLOG.md may be owned by a concurrent session; flag rather than overwrite, and file/close the N55/N83/N84/N85/N86 rows at merge per convention.

## 7. Acceptance criteria

- [ ] Unquoted `handoff_spawn: off` in a plan passes `validate-plan.py`'s `handoff_spawn` field and yields `spawn_policy: off` in the manifest and a `reason=policy-off` refusal from the script; `handoff_spawn: on` is rejected with an actionable message; quoted `"off"` is unchanged.
- [ ] Brainstorming presents the execution-mode choice at the feature-name step; writing-plans presents it (direct path) and writes `handoff_spawn` into plan frontmatter.
- [ ] `writing-plans/SKILL.md` has a "Declaring `handoff_spawn` per Plan" section; the plan-header convention lists `handoff_spawn` as a mandatory execution variable.
- [ ] SDD `SKILL.md` names the cmux auto-spawn as the default block-response (proactive discovery); both the SOFT nudge and HARD block hook messages name `spawn-handoff-session.sh` as the default response with manual as the alternative.
- [ ] A skill-awareness audit result is recorded for every skill assessed (SDD, writing-plans, brainstorming, executing-plans, using-superpowers).
- [ ] `SUPERPOWERS_CMUX_AUTOSPAWN=0` makes the spawn script exit 3 with `reason=autospawn-disabled` before the cmux-reachability check; documented in both env registries.
- [ ] N84 (`grep -qF`), N86 (checkpoint gate fail-closed, tripwire green), N85 (card `sys.executable` + validated ceiling) fixed; hook baseline re-captured in the same change.
- [ ] All suites green (unit, e2e, regression, install, hook baseline); SKILL.md additions offset by `references/` extraction (word ceiling respected).
- [ ] BACKLOG rows N55, N83, N84, N85, N86 updated/closed at merge.

## 8. Decision log

| # | Decision | Chosen | Rationale |
|---|----------|--------|-----------|
| 1 | Sprint scope | Core (caveats 1–4 + 3 discovery gaps + N55 + N83) + co-located hook fixes (N84/N86/N85) | Amortizes the mandatory hook-baseline re-capture; ships papercuts while files are open. Excludes cmux capability/runtime items (different theme). |
| 2 | Where to surface the consent choice | Both entry points (brainstorming 3.5 + writing-plans 0.5), materialized in writing-plans | Covers both plan entry paths at the "feature name established" moment; single materialization site. Brainstorming-only would miss the direct path. |
| 3 | Default value | Unchanged — `auto` stays the default | User intent is doctrine + discoverability + clean opt-out, not a behavior flip. |
| 4 | N83 fix location | `mode="before"` validator at the model boundary (plan.py + sdd_session.py) + materialize normalization | The plan gate rejects unquoted `off` before materialize runs, so a materialize-only fix is unreachable; the model boundary is the earliest correct site. |
| 5 | Kill switch vs plan dial | Add `SUPERPOWERS_CMUX_AUTOSPAWN` (runtime, per-run) alongside the existing `handoff_spawn: off` (plan-level, durable) | Complementary: plan-time durable opt-out vs plan-less per-run opt-out. Caveat 4 explicitly asked for the latter. |
| 6 | Hook wiring | Keep the spawn agent-driven; change only the hook *messages* | Machine-wiring the spawn is out of scope; discoverability is a messaging/doc problem, not an automation one. |
