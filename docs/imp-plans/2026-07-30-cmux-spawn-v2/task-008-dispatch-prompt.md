You are an implementer subagent executing **Task 8** of the cmux-spawn-v2 implementation plan. You follow TDD: write failing tests first, then implement.

## Where you are

Repo (worktree — work here, not in the main checkout):
`/Users/araymond/projects/claude-custom/superpowers/.worktrees/cmux-spawn-v2`
Branch `cmux-spawn-v2`. Feature dir: `docs/imp-plans/2026-07-30-cmux-spawn-v2/`.

This is Module 3 of 4 ("Spawn script core rework"), tasks 8–11. Modules 1 and 2 are complete and transitioned: Module 1 froze external cmux contracts into fixtures, Module 2 built the Python support layer (`_handoff_support.py`) that this module's shell consumes. Task 8 is the first task of Module 3.

**Read these before writing anything:**
1. `docs/imp-plans/2026-07-30-cmux-spawn-v2/module-3-spawn-script.md` — your plan. Read the whole file (header, Contract Constraints, File Map, Write-Scope table), then Task 8 in full.
2. `docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md` — the deferred-order register. Read rows B1, P7-1, P7-2, P7-3, P7-4, P7-5, P7-6, P7-7, P7-8, P7-9 and the row titled "STANDING RULE (bool-guard family)". Enumerate them yourself rather than trusting this list — an earlier version of this dispatch was BLOCKED for carrying nine when there are eleven. They are scheduled onto THIS task and summarized below, but the register rows carry measurements and reasoning the summaries do not.
3. `CLAUDE.md` at the repo root, and any `CLAUDE.md` in directories you modify.
4. `skills/subagent-driven-development/scripts/_handoff_support.py` and `tests/unit/test_handoff_support.py` — you are editing both.

## Your task

Task 8: **Policy gate, stall/ceiling rework, intent `tasks_done`.** Implement Steps 1–6 exactly as the plan specifies. The plan's fenced code blocks are the contract — the spec reviewer will mechanically diff your landed code against them. Where you must deviate, say so in your report rather than silently reconciling.

## Contract Constraints (verbatim from the plan — do not paraphrase)

> Bash ≥ 3.2; NO `set -u`/`set -e`/pipefail; `printf` not `echo` for composed strings; never pipe a producer into `grep -q` (use here-strings); all env knobs validate-warn-revert (`.handoff-hops`'s fail-closed numeric guard is the ONE fail-closed guard and stays untouched; `SUPERPOWERS_CMUX_MAX_HOPS` keeps its validate-warn-revert contract but its validation MOVES into the ceiling derivation — Task 8(b)/(e)); reservation BEFORE spawn; a received token is the ONLY exit-0 path; fallback fires ONLY before the launch command is accepted (`cmux send` rc 0 = accepted — after that, NEVER spawn again); `policy-off`/`policy-ask` are pre-reservation (no hop consumed); exit codes stay 0/3/1.

If your implementation contradicts these constraints, STOP and report BLOCKED. Do not work around a constraint — surface the conflict.

## Write scope

**You own (write):** `skills/subagent-driven-development/scripts/spawn-handoff-session.sh`, `skills/subagent-driven-development/scripts/_handoff_support.py`, `tests/unit/test_spawn_handoff_v2.py`, `tests/unit/test_spawn_handoff.py`, `tests/unit/spawn_handoff_helpers.py`, `tests/unit/test_handoff_support.py`, `tests/unit/test_spawn_handoff_hardening.py`, `tests/unit/fixtures/spawn-handoff/*`.

`_handoff_support.py` and `test_handoff_support.py` were read-only for Module 3 as originally written; the scope was widened for **Task 8 only** (commit `ca70612`) because **EIGHT** scheduled rows are edits to them — P7-1(ii), P7-2, P7-3, P7-5, P7-6, P7-7, P7-8, P7-9, all carried as required edits in the plan's **Step 2b**, which is authoritative. (The plan's scope paragraph and an earlier version of this line both said "seven" and omitted **P7-2** — the exact row a partner review already BLOCKED this dispatch over once. Count them yourself.) It reverts to read-only for Tasks 9–11. `test_spawn_handoff_hardening.py` was added by deferred order B1 (`3f6cbe6`). Do not touch anything else.

## Shared Constants

`_handoff_support.py` defines `HOP_DIVISOR = 2.5`, `CEILING_FLOOR = 6`, `CEILING_FACTOR = 2`. **Import them; do not redefine, hardcode, or approximate them in Python.**

The one sanctioned exception is the shell: step (e) writes the literals `6` and `* 2` because bash cannot import Python constants. That duplication is deliberate and is now NAMED by a comment at the site citing `_handoff_support.py` as SSOT. **If you change either side, change both** — and keep the comment truthful. Do not silently let them diverge, and do not "fix" the duplication by inventing an export mechanism.

Env-knob defaults in the script (`MAX_STALL_HOPS_DEFAULT`, and the `SPAWN_WAIT_TIMEOUT_DEFAULT` Task 9 adds) follow the existing validate-warn-revert pattern already in the file — match it rather than inventing a new one.

## Pattern References

Before building, read these existing implementations. Your code should be structurally consistent with them; if you find yourself inventing a convention, check these first.

- **`spawn-script-layer-style`** — `skills/subagent-driven-development/scripts/spawn-handoff-session.sh` itself. Its existing config layer, `validate-warn-revert` knob blocks, `print_manual_instructions`, checked-write `if !` wrappers, and exit ladder are the house style you are extending. Match them.
- **`import-only-helper-ssot`** — `skills/subagent-driven-development/scripts/_handoff_support.py`. The stdlib-only-at-import property is load-bearing (see P7-9(B)); the lazy `import yaml` placement is the mechanism.
- **`pytest-bash-stub-harness`** — `tests/unit/spawn_handoff_helpers.py` and the existing `test_spawn_handoff.py`. Follow the established `run_spawn` / stub-script conventions rather than writing a new harness.

## The ELEVEN scheduled deferred rows — these are part of Task 8, not optional extras

A round-1 partner review BLOCKED an earlier version of this dispatch that carried only nine. The register schedules **eleven** rows onto Task 8 / Module 3 (B1, P7-1 through P7-9, and OP-1 which the controller has already discharged). **Do not trust a count you inherit, including this one — enumerate the register yourself and say what you found.**

Several are consent/safety, and **every one of those is an OVER-PERMISSIVE defect: the failure mode is the code saying "yes" when it should say "no" or "I don't know."** That direction is where every real defect in this feature has lived.

**B1 — OVERDUE, and it is a fail-open regression you will otherwise cause invisibly.** `tests/unit/test_spawn_handoff_hardening.py` is **10/10 green right now**. `test_nonnumeric_max_hops_reverts_to_default_and_still_refuses` seeds `.handoff-hops="3"` against today's `MAX_HOPS_DEFAULT=3`, sets the knob to `"abc"`, and asserts refusal **and** `_did_not_spawn`. Your step (b) deletes that default and step (e) reverts an invalid knob to the DERIVED ceiling — which is `6` for that fixture (it ships no `.sdd-session.json`, so `EXPECTED_HOPS="unknown"`). **3 < 6, so the gate stops refusing and the script SPAWNS.** It fails only HALF-loudly: of three assertions only two flip, and the `WARNING:` one still passes. Pin it deliberately — seed above the new derived ceiling, or set `SUPERPOWERS_CMUX_MAX_HOPS` explicitly — whichever preserves each test's stated intent. **The sweep is FOUR unit tests, not two, and an identifier grep returns a clean FALSE closure:** `/usr/bin/grep -rlc 'MAX_HOPS' tests/unit/*.py` matches ONLY the hardening file — `test_spawn_handoff.py` scores 0 while containing two breaking consumers. A dependency on a value is not a textual reference to its name. **The plan's Step 2 carries a four-item migration block naming each one and its fix — that block, not the B1 prose, is what you work from.** Sweep the RENDERED strings (`Hop N/M`, intent field sets) as well as the identifiers, and do not trust a grep that returns the answer you expect. Step 2's fourth item also tells you to sweep for OTHER exact-equality field-set assertions before fixing the intent one — `outcome` records grow too.

**P7-2 — `stall-streak` has ZERO CLI coverage.** `TestCli` has exactly two tests and neither invokes `stall-streak` — the very subcommand the Module 3 stall gate calls. Task 8 is the ONLY task that may write `test_handoff_support.py` (it reverts to read-only afterwards), so this is not deferrable past you. Add CLI coverage, and make it cover the new degraded return you introduce for P7-8.

**P7-1 — a fail-open on the SOLE consent gate for automated spawning. TWO fixes, BOTH required. Neither subsumes the other; say why in your report or a later reader will merge them away.**
- **(i) Shell — ALREADY APPLIED TO THE PLAN, implement it as written.** The plan's fenced step (d) now yields `*) SPAWN_POLICY="ask"` and no longer discards stderr. This is no longer a deviation to make; the fence is the contract. Do not "restore" the old `*) SPAWN_POLICY="auto"` or the `2>/dev/null`.
- **(ii) Python** (`_handoff_support.py`): a **readable** manifest with a **present but invalid** `spawn_policy` still returns `auto` — `"OFF"`, `"Off"`, JSON `false`, `null`, or a non-dict `handoff` all print `auto`. A refusal expressed in the wrong case is silently inverted into consent. **The shell fix (i) CANNOT cover this**, because `auto` is a recognized value that matches its own `case` arm. Fail closed to `ask`.
- **The third path, so you do not "fix" it by accident:** an **absent manifest FILE** never consults the CLI at all — the `[ -f "$MANIFEST_FILE" ]` guard short-circuits and `SPAWN_POLICY` stays `auto`. The Python CLI *does* fail closed to `ask` on a missing `--manifest`, so the two layers deliberately disagree on this one input. **That is intentional and stays:** every pre-v2 handoff ships without `.sdd-session.json` and must still spawn. The plan now says so at the site. Do not harmonize them, and do not cite P7-1(ii) as evidence the fail-open is closed end-to-end — for this input the Python branch is unreachable.

**P7-8 — `stall_streak` returns `0` (meaning "no stall, proceed") for ANY `OSError` on the spawn log.** An unreadable or corrupt spawn log therefore silently disables the runaway-stall guard. `0` is legitimately "first hop or progress", which is exactly why conflating it with "could not read" is invisible.

**Do NOT apply this as a blanket `except OSError: return "indeterminate"`.** That single handler serves TWO cases: `FileNotFoundError` = "no log yet, first hop", which is a *legitimate* `0` documented in the function's own docstring and pinned by `TestStallStreak::test_first_hop_and_progress_are_zero` and by plan Step 2's `test_first_hop_baseline_not_stall`; and unreadable/corrupt, which is the defect. A blanket conversion breaks the first, and — worse — **it passes any test that only pins "unreadable ⇒ indeterminate", so the test cannot tell a correct fix from a wrong one.** Split it: `FileNotFoundError` → `0`, other `OSError` → `indeterminate`. **Required positive control:** assert that a *missing* log still returns `0` in the same battery that asserts an unreadable one returns `indeterminate`. Without that paired assertion your pin is vacuous.

(Severity note, so you do not mis-rank it: this one is NOT over-permissive in the consent sense — `0` and `indeterminate` both proceed. Its cost is a silently disabled runaway guard.)

**P7-3 — `tasks-done` prints a fake `0` instead of `unknown` when PyYAML is unavailable AND `reports/` is empty or missing.** `count_tasks_done` reaches its lazy `import yaml` only *inside* the glob loop, so with zero matches the loop never runs and the `ImportError` never fires. A fake `0` fed to the stall gate makes every hop look like zero progress — **manufacturing** a stall. The plan's own comment forbids exactly this ("a fake 0 manufactures stalls"). Fix: probe the import once before the glob. **Keep the lazy placement's stdlib-only-at-import property** (see P7-9(B)).

**P7-6 — a non-UTF-8 byte in ANY report file makes `tasks-done` raise and exit 1 with empty stdout.** `UnicodeDecodeError` subclasses `ValueError`, not the `OSError` that `count_tasks_done` catches, so the `continue` never fires. Verbatim violation of Module 2 AC-5 ("CLI prints `unknown`/`indeterminate` as values (exit 0) — degradation is observable"). Fix: `open(path, encoding="utf-8", errors="replace")` or widen to `except (OSError, UnicodeDecodeError):`. Add a fixture writing invalid bytes; assert `returncode == 0`.

**P7-4 — `stall-streak --tasks-done` is `type=int`, so it cannot accept the `unknown` that `tasks-done` legitimately prints.** The two CLI contracts do not compose. **Verify before acting:** the plan's step (e) already branches on `unknown` before calling `stall-streak`. Confirm that empirically. **Expected result, stated so that only a DISAGREEMENT is reportable:** two independent partner rounds measured that step (e)'s `unknown` branch fully covers this, and that `stall-streak --tasks-done unknown` is rejected by argparse (exit 2) — so the row should close as **already-satisfied**. Run it anyway. **If your measurement disagrees with that, say so LOUDLY in your report** — a wrong conclusion here is otherwise invisible, because "I checked and it was fine" and "I never really checked" produce identical report text.

**P7-5 — the valid-JSON-but-non-object consent branch is unpinned by any test.** Nothing asserts `spawn-policy` on `5` / `null` / `[1,2]`. These return `ask` correctly today, but by hand is not a regression test — and this is precisely where a register row (R3-2) once prescribed `manifest = {}`, which would have silently flipped them to `auto` with no test to catch it. Add assertions.

**P7-7 — the `except ImportError: print("unknown")` mitigation has no test; the mutation `print("unknown")` → `print(0)` SURVIVED.** This is the designated mitigation for P7-3, so the mitigation for a scheduled defect is itself unpinned. Technique: an `ImportError`-raising `yaml.py` on `PYTHONPATH`. **Positive-control it** — `/usr/bin/python3` on this machine DOES ship PyYAML, so the naive probe passes for the wrong reason.

**P7-9 — three test-only invariants, none over-permissive, all cheap.** (A) `expected-hops` on an unreadable manifest is unpinned (contract-pinning only). (B) **the lazy `import yaml` placement invariant is unpinned** — hoisting it to module scope passes all tests, and you are editing that exact function for P7-3, so nothing would catch a hoist that breaks the stdlib-only-at-import property. Pin it. (D) `derive_expected_hops`'s `isinstance(h, dict)` guard is unpinned while its `_cli` twin is pinned.

**STANDING RULE — the bool-guard family (six sites plus a live near-miss; four rounds have each believed it closed).** A bool fixture only discriminates if its coerced value is NOT already in the expected set. YAML `yes` → `True`, and `True == 1`, so `done.add(True)` collapses into an already-counted task 1 and the guard mutation SURVIVES. `no` → `False` → `0` works because `0` is not in `{1,2}`. **When pinning a bool guard: assert the MUTATED count differs, and never pick a sibling id the coerced bool would alias.**

**Step 2b is where eight of these rows actually get done.** A partner review BLOCKED an earlier version of this dispatch because NO step wrote `_handoff_support.py` or `test_handoff_support.py` — the rows were described in preamble, the files appeared in the staging list, and no checkbox commanded the work. You could have ticked every box, passed the fence diff, and done zero P7 work. Step 2b now carries all eight as required edits. **Standing rule this produced: every path in a staging list must have a step that writes it.**

## Things that are NOT findings — do not spend effort on them

- **The plan's own `validate-plan.py` WARNING that "Task 8 exceeds 200-line limit".** That is a **recorded, reasoned over-200 exception** (see the `OP-1 endgame` row in `deviations.md`), and the limit is **advisory in the enforcing code** — `validate-plan.py` appends to `warnings`, never `blockers`, and `plan-validation-gate-hook.sh` blocks only on `FAIL`. **Do not report it, and do not helpfully split the task** — splitting renumbers Tasks 9–18 into the manifest `task_range`, the hook's Check 4c, and cross-references across all four modules.
- **`BACKLOG.md` is owned by a CONCURRENT session. Do not edit it.** If you find something systemic, record it in `deviations.md` — which is also the artifact that survives `transition-module.py`'s archival at the module boundary. A finding recorded only in a report is one you are about to lose.
- **`module-2-models-budget.md` is out of your write scope — do not touch it.** It carries a deliberate `[~]` annotated-partial acceptance checkbox — the one reading **"CLI prints `unknown` / `indeterminate` as values (exit 0) — degradation is observable"** — held that way until P7-3, P7-6 and P7-8 land. (Search that text, not the label "AC-5": the string `AC-5` does not appear in that file.) Those three are your rows, so your work is what satisfies it — but flipping the checkbox is the controller's call, not yours. **Note in your report that its condition is now met; do not edit the file.**

## How to verify your own work

Green tests are not evidence. For every guard you add or fix, **run the mutation**: break the guard, confirm the test goes RED, restore with `git checkout --` (never `git stash` — the stash stack is shared across worktrees here and has swept in-flight artifacts before). Ask explicitly of each battery: **which of these makes the code accept something it should not?** Enforce mutation-anchor uniqueness — a `sed` matching 0 or 3 sites silently no-ops, and a no-op mutation reads as SURVIVED. Clear `__pycache__` between runs and pass `-p no:cacheprovider`.

## Environment traps that have already cost this sprint real time

- **The shell's `grep` is a function wrapping `ugrep -G --ignore-files --hidden`, which honors `.gitignore` and so silently skips `.worktrees/` — where this repo executes all SDD work.** It has produced one false blocking review finding and one false corroboration. **Use `/usr/bin/grep` or `find -print0 | xargs -0` for every recursive sweep.**
- **The pre-commit format hook attacks every Python commit** (three consecutive so far). It black-rewrites the whole file between `git add` and `git commit` and deletes intentionally-unused imports that are pinned seams. **Standing procedure: check `git diff --cached --stat` before committing; if it exceeds your intended change, reset, re-stage, and commit with `--no-verify`, then verify the imports survive at HEAD.**
- **Commit with `git commit -F -` and a QUOTED heredoc (`<<'EOF'`), never `-m`.** This task's message naturally contains `$MAX_HOPS`, backtick-quoted identifiers and the `*)` case arm; zsh command-substituted a commit message earlier this sprint and **silently ate two clauses**. You will not notice — the commit succeeds. **This overrides plan Step 6's literal `git commit -m` form** — that message happens to be `-m`-safe, but write it as a quoted heredoc anyway rather than deciding per-message. It is the one place where "the fence is the contract" yields.
- **B7 inverts by directory.** `check_python39_compat` flat-globs `skills/subagent-driven-development/scripts/*.py` only. So in `_handoff_support.py` use `Optional[X]` and `Dict[str,int]`, **never** `X | None` or `dict[str,int]`. (`skills/scripts/models/` is not scanned and uses the modern syntax — do not harmonize them.)
- The worktree `.venv` is a **symlink** to the main checkout's venv. Never delete or recreate it; ~60 tests spawn `.venv/bin/python3` by relative path.
- **Never `git add -A`** — stage explicit paths. Bash cwd persists between calls; `cd` to the repo root explicitly in each verification command.
- An empty or passing probe result is a **claim, not a fact**. Ten instrument failures this sprint. Positive-control every probe: run something that must match and confirm it does.

## Acceptance

**Task 8 moves a GLOBAL default (`MAX_HOPS`), so a file-list acceptance is not honest here — run the full suite.**

`cd <worktree> && .venv/bin/python3 -m pytest tests/unit/ -q -p no:cacheprovider`

The full suite was **707 green** at the start of this task; do not regress it. Report the actual number you measure, not the one you were given — if it differs from 707 + your new tests, investigate before reporting DONE.

While iterating you may narrow to `tests/unit/test_spawn_handoff.py tests/unit/test_spawn_handoff_v2.py tests/unit/test_handoff_support.py tests/unit/test_spawn_handoff_hardening.py -v`, but the number you report must come from the full-suite run. Commit with an explicit path list.

## Report Format

When done, report using this exact structure. Your report MUST begin with a YAML frontmatter block (between --- delimiters), followed by the prose sections below. Do not omit sections. **Copy this structure verbatim — do not write it from memory.** `contract_compliance` is a LIST and its `status` is an enum; `PASS` is NOT a valid value. `tests.written` is an int, and `tests.passing` must not exceed it.

---
schema_version: 1
task_id: 8
task_type: implementation
status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
files_changed:
  - path: "path/to/file.py"
    description: "what changed and why"
tests:
  written: [count]
  passing: [count]
  command: "[exact command run]"
  result: PASS | FAIL
contract_compliance:
  - constraint: "[constraint text from plan]"
    status: compliant | non_compliant | partial | not_applicable
    detail: "[how you complied]"
---

**Implementation Summary:**
[2-3 sentences: what you built and the approach taken]

**Source Files Read:**
- `path/to/source.py` — [what you learned from reading it]

**CLAUDE.md Files Read:**
- `path/to/CLAUDE.md` — [key conventions or patterns found]

**Deviations from Plan:**
- [Any decisions differing from the plan's instructions; anything skipped or deferred; dead code identified but not removed, and why]

**Self-Review Findings:**
- [Issues found during self-review and how you resolved them]

**Concerns:**
- [Anything you're uncertain about or think the controller should know]

Use DONE_WITH_CONCERNS if you have any entries in Deviations or Concerns. Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need information that wasn't provided. Never silently produce work you're unsure about.

**Additionally, report per row: fixed / already-satisfied / not-done-and-why, with the evidence.** The set to report on is the ELEVEN scheduled rows — **B1, P7-1 through P7-9, and OP-1** (already discharged by the controller; say so and move on). Report on the **STANDING RULE (bool-guard family)** row as well: it is not one of the eleven — it is gated on "every future test touching this family," so it constrains your work rather than being a unit of it. (Two lists appear above and they differ by TWO rows — the reading list at the top includes STANDING RULE but not OP-1; the eleven includes OP-1 but not STANDING RULE. This sentence is the authoritative one.) A row you silently drop is a row that is lost — `transition-module.py` archives reports at the module boundary.
