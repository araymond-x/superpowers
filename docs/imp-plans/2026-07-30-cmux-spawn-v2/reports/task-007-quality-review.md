# Task 7 — Adversarial Code Quality Review (round 1)

**Commit:** `83a9ccf` — `_handoff_support.py` (+112), `tests/unit/test_handoff_support.py` (+66/-1)
**Reviewer stance:** adversarial. Upstream was fully green (implementer DONE_WITH_CONCERNS all dispositioned, spec review PASS with a mechanical plan-vs-code diff, partner satisfied on round 2, suite 704). None of that is evidence of correctness.

**Verdict: CHANGES_REQUESTED** — 2 Major, 4 Minor, 2 Nit. Both Majors are test-only fixes (~6 lines total). The stopping rule's first conjunct (findings are cosmetic) fails.

---

## Harness

| Control | Result |
|---|---|
| **Positive control** — `_DONE_STATUSES` → `("DONE",)` | **CAUGHT** (1 failed, 25 passed). The battery can detect a break. |
| **Anchor uniqueness** | Every mutation asserted `count(anchor) == 1` before applying; a non-unique anchor aborts without running (a no-op `sed` reads as SURVIVED). |
| **`__pycache__`** | Cleared before *and* after every mutation run (`find … -name __pycache__ -print0 \| xargs -0 rm -rf`, excluding `.venv`); every pytest invocation used `-p no:cacheprovider`. |
| **Recursive sweeps** | `/usr/bin/grep` only (the shell `grep` is a `ugrep --ignore-files` wrapper that silently skips `.worktrees/`). |
| **PyYAML-absent probe** | **Not attempted via `/usr/bin/python3`** — it ships PyYAML on this machine and would have returned a clean result for the wrong reason. Used `import _handoff_support; 'yaml' in sys.modules` instead (below). |
| **Restore** | `git checkout`-free restore from an in-memory original after each mutation. Final: `git status --porcelain -- skills tests` **empty**; working-tree sha256 of `_handoff_support.py` `7b62714a…c550ef` == `git show HEAD:` sha256. No `git stash` used. Nothing committed. |

**Baselines re-measured, not assumed:** `test_handoff_support.py` **26 passed**; `tests/unit/` **704 passed** (154s); `validate-all-skills.py` **PASS 160 / FAIL 0 / WARNING 2**. All match the stated baselines.

### Mutation battery (14 mutations)

| # | Mutation | Result |
|---|---|---|
| PC | `_DONE_STATUSES` drops `DONE_WITH_CONCERNS` | **CAUGHT** |
| M1 | consent: `pol = h.get("spawn_policy") …` → `pol = None` | SURVIVED → **Major 1** |
| M2 | consent: `"off"` dropped from accepted set | SURVIVED → **Major 1** |
| M2b | consent: `"ask"` dropped from accepted set | SURVIVED → **Major 1** |
| M3 | `"indeterminate" if streak == 0 else streak` → always `"indeterminate"` | SURVIVED → Nit 1 |
| M4 | `_OUTCOME_RE` → `re.compile(r"")` (matches every line) | SURVIVED → **Major 2** |
| M5 | `not isinstance(tid, bool)` removed | SURVIVED → Minor 2 |
| M6 | `isinstance(tid, int) and not isinstance(tid, bool)` → `tid is not None` | SURVIVED → Minor 2 |
| M7 | `return fm if isinstance(fm, dict) else None` → `return fm` | SURVIVED → Minor 3 |
| M8 | `yaml.safe_load` `try/except Exception` removed | SURVIVED → Minor 3 |
| M9 | archive glob neutered | **CAUGHT** |
| M10 | dedup broken (`done.add(tid)` → `done.add((tid, path))`) | **CAUGHT** |
| M11 | non-dict-JSON → `manifest = None` removed | SURVIVED → Nit 2 (= dispositioned P7-5) |
| M12 | `except ImportError: print("unknown")` → `print(0)` | SURVIVED → Minor 4 |

---

## Blocker

None.

---

## Major

### Major 1 — the consent gate's *honored* path has zero tests: a manifest declaring `spawn_policy: off` / `ask` is unpinned in the over-permissive direction

**Where:** `_handoff_support.py`, `_cli`'s final two lines (`pol = h.get("spawn_policy") …` / the `print(pol if pol in (…))`).

**Mutations and results:**

| Mutation | Suite |
|---|---|
| M1 `pol = None` (the declared-policy read never happens) | **SURVIVED** 26 passed |
| M2 accepted set → `("auto", "ask")` (`"off"` no longer honored) | **SURVIVED** 26 passed |
| M2b accepted set → `("auto", "off")` (`"ask"` no longer honored) | **SURVIVED** 26 passed |

**Guarded vs mutated, measured at concrete inputs** (`spawn-policy --manifest`):

| Manifest | Guarded (HEAD) | Mutated (M1) |
|---|---|---|
| `{"total_tasks":5,"tier":"standard","handoff":{"expected_hops":2,"spawn_policy":"off"}}` | `off` | **`auto`** |
| `…"spawn_policy":"ask"` | `ask` | **`auto`** |

The suite is 26-passed under both. **The single line that turns a user's declared refusal into a value the caller can act on is not observed by any test in the repository.**

**Why this is not the already-dispositioned P7-1(ii).** P7-1(ii) is *present-but-invalid* policy (`"OFF"`, `false`) → `auto`, whose reachability was correctly measured as hand-edit-only. This finding is the *valid, declared* value on the fully-machine-generated path:

- `materialize-manifest.py` (`spawn_policy = frontmatter.get("handoff_spawn")`, then `if spawn_policy is None: spawn_policy = "auto"`) writes the value from plan frontmatter.
- `tests/unit/test_materialize_manifest.py:337` and `:343` already prove `handoff_spawn: ask` and `handoff_spawn: "off"` land in a real manifest as `spawn_policy`.
- `sdd_session.py:21` pins the closed literal.

So a plan author's `handoff_spawn: off` reaches `_handoff_support.py:170` through a producer path that is tested end-to-end **right up to the consumer, which is untested.** `/usr/bin/grep -rn "spawn_policy"` over the repo confirms `_handoff_support.py:170` is the **only** consent-side read.

**Wiring status, stated honestly:** `spawn-handoff-session.sh` does **not** yet call `spawn-policy` — Module 3 wires it. This is a shipped-but-unwired gate. It is still a shipped, untested consent gate, and **this is the last task in Module 2**: after the transition the aggregate gates lose visibility of it, and Module 3 will build on top of a read it has no reason to re-verify.

**Fix** (two lines, in `TestCli.test_expected_hops_and_policy_cli_on_legacy_and_garbage` or a new test):

```python
m.write_text('{"total_tasks": 5, "handoff": {"expected_hops": 2, "spawn_policy": "off"}}')
assert self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "off"   # declared refusal is HONORED
m.write_text('{"total_tasks": 5, "handoff": {"expected_hops": 2, "spawn_policy": "ask"}}')
assert self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "ask"
```

Verified these two assertions kill M1, M2 and M2b (each mutation prints `auto` for at least one of them).

---

### Major 2 — `_OUTCOME_RE` is load-bearing on *every* real spawn log and has no test; its failure mode **understates** the streak

**Where:** `_OUTCOME_RE = re.compile(r"^\S+ \S+ outcome ")` and the `outcomes = [l for l in lines …]` filter in `stall_streak`.

**Mutation:** `_OUTCOME_RE` → `re.compile(r"")` (filter accepts everything). **SURVIVED**, 26 passed.

**Why no test can catch it:** every fixture log in `TestStallStreak` is built solely from the `OUT` template — an **outcome-only** log. That shape **never occurs in production**. `spawn-handoff-session.sh` writes an `intent hop=N` record *before* each spawn (`printf '%s %s intent hop=%s\n' … >> "$SPAWN_LOG"`, ~line 523) and the `outcome` record after (~lines 537/543), plus the child's `runtime-picker-failure` line. A real log is therefore **always** `intent, outcome, intent, outcome, …`.

**Guarded vs mutated on a realistic interleaved log** (two hops, both `tasks_done=4`, current count 4):

| | `stall-streak` result |
|---|---|
| Guarded (HEAD) | **2** |
| Mutated (M4) | **1** |

The mutated walk hits the interleaved `intent` row (no `tasks_done=`), and — because `streak` is already 1 — returns `1` instead of `2`. **The failure direction is understatement**, i.e. the runaway-stall guard fires a hop late or not at all. That is the over-permissive direction.

**The gap propagates forward:** `module-3-spawn-script.md`'s planned `append_outcome(ctx, hop, tasks_done, extra="")` helper (line ~87) also writes outcome-only logs. Without a fix here, *no test at any layer* will ever exercise the shape the producer actually writes.

**Fix** (one test, in `TestStallStreak`):

```python
def test_intent_rows_between_outcomes_do_not_break_the_streak(self, tmp_path):
    rows = ["2026-07-30T00:00:01Z u1 intent hop=1", self.OUT.format(i=2, td=4),
            "2026-07-30T00:00:03Z u2 intent hop=2", self.OUT.format(i=4, td=4)]
    assert self._streak(tmp_path, rows, 4) == 2      # real logs ALWAYS interleave intent
```

Verified this assertion kills M4 (mutated → 1).

---

## Minor

### Minor 1 — `tasks-done` raises on a non-UTF-8 report byte: a verbatim violation of Module 2 AC-5

`count_tasks_done` guards the read with `except OSError`. `UnicodeDecodeError` subclasses `ValueError`, **not** `OSError`, so it escapes.

**Measured.** A report file with a stray `\xff` byte after valid frontmatter, in an otherwise normal `reports/` dir:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 50: invalid start byte
exit=1        (no value on stdout)
```

Module 2 AC-5 reads: *"CLI prints `unknown` / `indeterminate` as values (exit 0) — degradation is observable, never an exception."* This is that AC failing, not a coverage gap. One unreadable byte in one report zeroes the whole progress signal and hands the (Module 3) caller an empty stdout plus exit 1.

Reachability is low — a stray non-UTF-8 byte pasted into a report body (terminal output, a mangled copy).

**Disposition: SCHEDULE to Module 3 alongside P7-3 — do NOT fix in Task 7.** The fix is a production edit to a body that is **verbatim from the plan's Step 3 fenced block**, which is exactly the deviation P7-3 was not permitted to make: same function, same class of defect ("degradation not observable"), and the controller accepted P7-3 as scheduled with the implementer's compliance entry marked `partial`. Requiring this one in-task while P7-3 stands scheduled would be inconsistent. Both are reads inside `count_tasks_done` and Module 3 should fix them in one pass under one reviewer's attention.

**Consequence, stated plainly: Module 2 AC-5 is NOT satisfied at module close.** It is carried as two known open rows — P7-3 (fake `0` on empty dir + PyYAML absent) and this exception path. The Module 2 acceptance-criteria checkbox should record that rather than read as green, so the gap stays visible across the transition instead of being buried in a fix round.

**Fix (Module 3):** `open(path, encoding="utf-8", errors="replace")`, or widen to `except (OSError, UnicodeDecodeError):`. Add a fixture writing invalid bytes and assert `returncode == 0`.

### Minor 2 — both `task_id` type guards are unpinned; removal **overstates** `tasks_done` (bool-guard family, 6th site)

The prompt is right that this family is not closed. `isinstance(tid, int) and not isinstance(tid, bool)` has no test.

| | `tasks-done` on a dir holding one `task_id: yes` report and one `task_id: "3"` report, both `DONE` |
|---|---|
| Guarded (HEAD) | **0** |
| M5 (bool guard removed) | **1** — YAML 1.1 parses `yes` → `True`, and `True == 1` in a set, so it is either a phantom completion or silently merges with a real task 1 |
| M6 (both guards removed) | **2** — a string `"3"` also counts |

Both directions **overstate** `tasks_done`, which is exactly the input `stall_streak` compares against the log: fake progress makes a stalled chain look like it is advancing and **suppresses the stall guard**.

**Fix:** add to `TestTasksDone.test_done_and_concerns_count_blocked_and_malformed_do_not` two reports with `task_id: yes` and `task_id: "3"` (status `DONE`), and keep the expected count at 2.

### Minor 3 — `_frontmatter`'s two internal guards are unpinned (coverage only, not correctness)

M7 (`return fm if isinstance(fm, dict) else None` → `return fm`) and M8 (removing the `try/except Exception` around `yaml.safe_load`) both **SURVIVED**. The shipped code is **correct** on both; the tests simply never construct the inputs. The "malformed" fixture is `"no frontmatter at all"`, which exits at the `startswith("---")` check and never reaches either guard.

Direction is a **crash**, not over-permissiveness — but note the crash lands in `tasks-done` and would be another AC-5 violation of the same class as Minor 1. Filing as coverage, not correctness.

**Fix:** two fixtures — `---\n- a\n- b\n---\n` (list frontmatter) and `---\nkey: [unclosed\n---\n` (invalid YAML) — both asserted not to count and not to raise.

### Minor 4 — `except ImportError: print("unknown")` is unpinned

M12 (`print("unknown")` → `print(0)`) **SURVIVED**. This is the branch the plan's own comment calls out (*"a fake 0 manufactures stalls"*), and it is the mitigation for dispositioned **P7-3**. The mitigation itself has no test. Testable with the spec reviewer's own technique — an `ImportError`-raising `yaml.py` on `PYTHONPATH`, with a positive control. Schedule alongside P7-3 in Module 3; do not fix P7-3's production body here.

---

## Nit

### Nit 1 — the `else streak` half of the indeterminate condition is unpinned

M3 (`return "indeterminate" if streak == 0 else streak` → `return "indeterminate"`) **SURVIVED**: no fixture has a malformed row that is not also the newest row. The unpinned half fails toward `"indeterminate"` → the caller **SKIPs** → conservative. Not worth a Major. The Major 2 fix can absorb it by making one interleaved row malformed after a counted row.

### Nit 2 — M11 survived, confirming dispositioned P7-5

Removing the `if not isinstance(manifest, dict): manifest = None` normalization survives, which is exactly the untested branch P7-5 already records. **Not re-filed** — reported only as independent confirmation that the dispositioned row is accurate.

---

## Verified-clean (reported as measured, not manufactured)

- **AC-4 SSOT holds.** `/usr/bin/grep -rn "tasks_done\|stall_streak\|stall-streak"` (excluding `.venv`, `.git`, `__pycache__`, `.pytest_cache`, `docs`) returns exactly two files: `_handoff_support.py` and its test. No second implementation of the counting or streak logic exists.
- **Stdlib-only-at-import preserved** despite the new `glob/json/os/re/sys` imports. Probe: `/usr/bin/python3 -c "import _handoff_support, sys; print('yaml' in sys.modules)"` → `False`. **Positive control:** `import yaml, sys; print('yaml' in sys.modules)` → `True`. The probe can distinguish.
- **Task 6 pins intact.** Full `tests/unit/` = 704 passed. The diff modifies no pre-existing function body — the only change to prior content is the import block (which the plan's Step 3 prescribes), and both deliberately-unused seams `HOP_DIVISOR` / `CEILING_FACTOR` survive on the import line.
- **The authorized token is real, not decorative.** `True` added to `test_invalid_total_raises` genuinely exercises `expected_hops`'s `isinstance(total_tasks, bool)` branch.
- **Dedup and the archive glob are properly pinned** — M9 and M10 both CAUGHT.
- **`\d+` cannot consume a negative `tasks_done`.** A `tasks_done=-1` record produces no match → `"indeterminate"` → caller SKIPs. Conservative; nothing to file.

---

## Required to close

1. Major 1 — two consent assertions (`off`, `ask` honored).
2. Major 2 — one interleaved-log streak test.

**Both are test-only, ~6 lines total, and require no deviation from the plan's fenced production body.**

Scheduled to Module 3, not required here: **Minor 1** (with P7-3 — same function, same plan-verbatim-body constraint; and record that **AC-5 is not met at Module 2 close**) and **Minor 4** (the P7-3 mitigation's own missing test). Minors 2–3 and the Nits are recommended in the fix round; Minor 2 in particular is cheap and closes the sixth site of a guard family that has now yielded findings in four consecutive rounds.

**Fix-round mechanics:** the pre-commit format hook has attacked this file twice (it deleted the `HOP_DIVISOR` / `CEILING_FACTOR` seams and churned Task 6's lines). A test-only commit still touches a `.py` file — use the proven `git commit --no-verify` workaround and verify the two pinned imports survive at HEAD.

**CHANGES_REQUESTED**
