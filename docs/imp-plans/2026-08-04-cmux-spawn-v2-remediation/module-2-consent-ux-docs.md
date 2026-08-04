# Module 2 — Plan-time consent UX + author docs

**Goal:** Present the execution-mode choice (`auto` / `ask` / `off`) at both plan entry points as a mandatory plan execution variable, and document `handoff_spawn` for plan authors — mirroring the existing `review_tier` / `task_type` / `integration_test` author sections. The choice threads brainstorming → writing-plans via the spec (the same carrier `entry_mode` / `enforcement_tier` use), and writing-plans materializes it into plan frontmatter.

**Source Contracts:** None

(Contract verified in Module 1's Task 0; consent value set defined in `plan.py`/`sdd_session.py`; see the parent plan and `spec-distilled.md` §C2.)

**Contract Constraints:**
- Consent values are exactly `auto` (default) / `ask` / `off`. Do not add a fourth or rename.
- The choice is a **plan execution variable** carried in the spec/distilled spec — NOT session memory (it must survive a separate writing-plans invocation).
- Word ceiling: `writing-plans/SKILL.md` is 4726 words; brainstorming is 2481 (headroom). The writing-plans additions must be offset by a `references/` extraction (Task 5). Verify with an explicit `wc -w` number under 5000.
- `off` must be documented as unquoted-safe (post-N83) AND quotable — both accepted.

**Pattern References:**
- `skills/writing-plans/SKILL.md` "Declaring `review_tier` per Task" (§line 387), "Declaring `task_type` per Task" (§416), "Declaring `integration_test` per Plan" (§435) — the author-section template to mirror (Task 5).

## File Map

| File | Responsibility |
|------|----------------|
| `skills/brainstorming/SKILL.md` | Present the execution-mode choice at feature-name time + record it in the spec (Task 4) |
| `skills/writing-plans/SKILL.md` | Step 0.5 direct-path choice + "Declaring `handoff_spawn`" section + mandatory-var listing + frontmatter materialization (Task 5) |
| `skills/writing-plans/references/plan-header-template.md` (new) | Extracted Plan Document Header example (ceiling offset) (Task 5) |

## Write-Scope Partitioning

| Task | Owned Files (write) | Read-Only | Depends On |
|------|---------------------|-----------|------------|
| Task 4 | `skills/brainstorming/SKILL.md` | spec-distilled.md | Module 1 (Task 3) |
| Task 5 | `skills/writing-plans/SKILL.md`, `skills/writing-plans/references/plan-header-template.md` | brainstorming/SKILL.md | Task 4 |

---

### Task 4: brainstorming/SKILL.md step 3.5 — execution-mode consent prompt

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (step 3.5 area + the Spec Distillation Contract-Facts guidance)

Brainstorming has ample word headroom (2481/5000) — no extraction needed.

- [x] **Step 1: Add the execution-mode choice after the feature name is established**

In `skills/brainstorming/SKILL.md`, immediately after the step **3.5 "Establish feature name"** block (which ends with the conflict-detection bullets, ~line 37), add a new step:

````markdown
3.6. **Establish execution mode (`handoff_spawn`)** — right after the feature name, present the plan-time execution-mode choice. This is a mandatory plan execution variable; record the answer in the spec so writing-plans reads it (session memory does not survive a separate writing-plans invocation — the same carrier `entry_mode` / `enforcement_tier` use).

   Present this choice (its own message; "press enter to accept the default", like the feature-name prompt):

   > "How should this feature's SDD session hand off when the controller's context fills (cmux auto-spawn consent)? Recorded in the spec, materialized into the plan.
   > - **auto** (default) — the successor SDD session spawns automatically in cmux; degrades to a manual handoff when cmux is unreachable.
   > - **ask** — auto-spawn, but the controller asks you first each hop.
   > - **off** — never auto-spawn; the controller hands off manually (you run `/pickup`) at each boundary.
   >
   > Press enter to accept **auto**, or type `ask` / `off`."

   Remember the answer; you will record it as a Contract Fact when the spec is written (step 6) and carry it into the distilled spec.
````

- [x] **Step 2: Record the choice as a Contract Fact in the spec**

In the **Spec Distillation** section's "Contract Facts" guidance (the description of what belongs in Contract Facts), add one line so the chosen mode lands durably:

```markdown
- Record the execution mode from step 3.6 as a Contract Fact: `handoff_spawn: <auto|ask|off>` — a plan execution variable the plan writer materializes into plan frontmatter.
```

- [x] **Step 3: Verify word ceiling + regression**

Run: `wc -w skills/brainstorming/SKILL.md` (must stay well under 5000 — expect ~2550).
Run: `.venv/bin/python3 tests/ARaymond-skill-regression/validate-all-skills.py 2>&1 | tail -5`
Expected: no new FAIL; brainstorming not over the hard word limit.

- [x] **Step 4: Commit**

```bash
git add skills/brainstorming/SKILL.md
git commit -m "feat(consent): brainstorming presents execution-mode choice at feature-name step"
```

---

### Task 5: writing-plans/SKILL.md — extract-to-references then add Declaring handoff_spawn + Step 0.5 + frontmatter var

**Files:**
- Create: `skills/writing-plans/references/plan-header-template.md`
- Modify: `skills/writing-plans/SKILL.md` (extract the Plan Document Header example; add Step 0.5 direct-path choice; add "Declaring `handoff_spawn` per Plan"; list `handoff_spawn` in the plan-header + YAML frontmatter as a mandatory execution variable)

**Pattern References:** the three existing "Declaring X" sections (§387/§416/§435) — mirror their structure and tone.

- [ ] **Step 1: Extract the Plan Document Header example to references/ (ceiling offset — do this FIRST)**

The additions below add ~270 words; writing-plans is at 4726, so extract first. Move the fenced ```markdown example block inside `## Plan Document Header` (the `# [Feature Name] Implementation Plan` … Code Footprint table block, ~lines 189-219) to a new `skills/writing-plans/references/plan-header-template.md`, and replace it in SKILL.md with a one-line pointer:

```markdown
## Plan Document Header

**Every plan MUST start with the header shown in `references/plan-header-template.md`** — Goal, Architecture, Tech Stack, Source Contracts, Contract Constraints, Shared Constants, Pattern References, Feature Archetype, and the Code Footprint table.
```

Keep the explanatory prose that follows the block (the paragraphs describing Source Contracts / Contract Constraints / Shared Constants fields) in SKILL.md — only the example block moves.

- [ ] **Step 2: Add the "Declaring `handoff_spawn` per Plan" author section**

Add after "Declaring `integration_test` per Plan" (~line 439):

```markdown
## Declaring `handoff_spawn` per Plan

Every plan declares `handoff_spawn` in its YAML frontmatter — a **mandatory execution variable**, listed alongside `enforcement_tier`. It sets whether the SDD controller's successor session auto-spawns in cmux when the context-pressure gate blocks. Default `auto`. If the feature came through brainstorming, this value was chosen at the feature-name step (recorded in the spec); on the direct path, choose it at Step 0.5.

| Value | Behavior |
|-------|----------|
| `auto` (default) | The successor SDD session spawns automatically in cmux when the controller's context fills; degrades to a manual handoff when cmux is unreachable. |
| `ask` | Auto-spawn, but `spawn-handoff-session.sh` refuses without `--user-approved` (runtime `reason=policy-ask`) — the controller asks the user first each hop. |
| `off` | Never auto-spawn; the controller performs the manual handoff (build bundle → user `/pickup`) at each boundary (runtime `reason=policy-off`). |

Write `off` unquoted or quoted — both are accepted (the model coerces YAML-1.1 `off`→`False`→`"off"`); `handoff_spawn: on` is rejected. Consent is plan-level (whole feature); handoffs happen at task boundaries. For a per-run, plan-less opt-out without editing the plan, set `SUPERPOWERS_CMUX_AUTOSPAWN=0` (see `subagent-driven-development/references/context-handoff-protocol.md`).
```

- [ ] **Step 3: Add the Step 0.5 direct-path choice + materialization**

In the checklist item **0.5 "Resolve feature directory"** (the "Entry mode recording" area, ~line 43), add:

```markdown
**Execution-mode materialization**: Resolve `handoff_spawn` for this plan. If the spec / distilled spec records an execution mode (`handoff_spawn: <auto|ask|off>` from brainstorming step 3.6), use it. On the direct path (no such record), present the same choice now:

> "Execution mode for auto-spawn handoff — **auto** (default, spawns the successor in cmux when context fills), **ask** (spawns but asks you first each hop), or **off** (never auto-spawn; manual `/pickup` handoff). Press enter for **auto**, or type `ask` / `off`."

Write the resolved value as `handoff_spawn: <choice>` in the plan's YAML frontmatter (mandatory execution variable).
```

- [ ] **Step 4: List `handoff_spawn` as a mandatory execution variable in the frontmatter reference**

In the "YAML Frontmatter (Required)" example (~line 234), add `handoff_spawn` next to `enforcement_tier`:

```yaml
enforcement_tier: standard  # micro | standard (default: standard)
handoff_spawn: auto  # auto | ask | off (default: auto) — cmux auto-spawn consent; see "Declaring handoff_spawn per Plan"
```

- [ ] **Step 5: Verify word ceiling (explicit number) + regression**

Run: `wc -w skills/writing-plans/SKILL.md`
Expected: **under 5000** (extraction of the header block offsets the ~270 added words; expect ~4750).

Run: `.venv/bin/python3 tests/ARaymond-skill-regression/validate-all-skills.py 2>&1 | tail -8`
Expected: no new FAIL; writing-plans not over the hard word limit; the new `references/plan-header-template.md` cross-reference resolves.

- [ ] **Step 6: Commit**

```bash
git add skills/writing-plans/SKILL.md skills/writing-plans/references/plan-header-template.md
git commit -m "feat(consent): writing-plans Declaring handoff_spawn + Step 0.5 choice + frontmatter var (extract header to references)"
```

## Acceptance Criteria (Module 2)

- [x] `brainstorming/SKILL.md` presents the `auto`/`ask`/`off` choice at the feature-name step and records it in the spec as a Contract Fact (plan execution variable).
- [ ] `writing-plans/SKILL.md` has a "Declaring `handoff_spawn` per Plan" section; Step 0.5 presents/reads the choice; the YAML frontmatter reference lists `handoff_spawn` alongside `enforcement_tier` as a mandatory execution variable.
- [ ] The Plan Document Header example was extracted to `references/plan-header-template.md`; `wc -w skills/writing-plans/SKILL.md` is under 5000; regression test has no new FAIL.
