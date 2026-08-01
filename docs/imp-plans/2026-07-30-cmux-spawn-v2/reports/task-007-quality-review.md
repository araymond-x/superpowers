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

---

# Round 2 — Adversarial Code Quality Review

**Fix commit:** `cf5de3b` (test-only) · **Implementation:** `83a9ccf` (unchanged) · **Docs:** `b7bc19f`
**Round-1 verdict:** CHANGES_REQUESTED (2 Major, 4 Minor, 2 Nit).

**Verdict: APPROVED (Task 7 code + tests) — TRANSITION BLOCKED until the three record-integrity conditions land.** Every required round-1 finding closes by mutation as the sole failure, and the fix is provably test-only. But one **Major** is filed against the *record*, not the code: `deviations.md` has no row for the measured AC-5 violation, and the transition is about to archive the only file that does. Four new Minors and two new Nits besides; none of those blocks.

**Read the closing line, not this one, for what gates the transition.**

**One correction to the dispatch brief:** round 1 ran 14 mutations of which **11** survived, not 12 (14 rows minus PC, M9, M10). All 11 were re-run.

---

## Harness

| Control | Result |
|---|---|
| **Positive control** — `_DONE_STATUSES` → `("DONE",)` | **CAUGHT** (1 failed, 28 passed), sole failure. The battery can still detect a break. |
| **Anchor uniqueness** | Every edit asserts `txt.count(old) == 1` and **aborts without running** otherwise. Load-bearing here: `isinstance(tid, int) and not isinstance(tid, bool)` appears **twice** (`derive_total_tasks`'s `task_ids` loop and `count_tasks_done`), and `manifest or {}` appears twice. Both were disambiguated with multi-line context anchors; zero ABORTs fired, so every mutation applied to exactly one site. |
| **`__pycache__`** | Cleared before *and* after every run (`find . -path ./.venv -prune -o -name __pycache__ -print0 \| xargs -0 rm -rf`); every pytest invocation used `-p no:cacheprovider`. |
| **Sole-failure discipline** | The harness captures the `FAILED …::test_name` lines, not just the tail. Every CAUGHT below names exactly one test (the sole intentional exception is control N9, which correctly breaks two). |
| **Recursive sweeps** | `/usr/bin/grep` only. |
| **Restore** | Two-file in-memory restore + sha256 assertion after *every* mutation; battery ends `RESTORE-OK`. Final: `git status --porcelain -- skills tests` **empty**; worktree sha256 of `_handoff_support.py` `7b62714a…c550ef` == `git show HEAD:` == `git show 83a9ccf:`. No `git stash`. Nothing committed. |

**Instrument failure caught mid-run (the sprint's ninth).** An ad-hoc restore using `ORIG=$(cat $S)` / `printf '%s' "$ORIG"` **silently dropped the file's trailing newline** — sha256 came back `107014ed…`, not `7b62714a…`, and `git status` showed the file dirty. Caught only because restore is *verified* rather than assumed. Repaired with `git checkout --` (never `git stash`). Anyone reusing a shell-variable restore on this feature will hit it: command substitution strips trailing newlines. The Python harness (in-memory string, not `$(cat)`) is unaffected.

**Baselines re-measured, not assumed:** scoped `test_handoff_support.py` **29 passed**; `tests/unit/` ****707 passed** (157s)**; `validate-all-skills.py` ****PASS 160 / FAIL 0 / WARNING 2****. All match the stated baselines.

### Test-only verification, done independently

- `git diff --stat 83a9ccf HEAD -- skills/` → **empty**.
- `shasum -a 256` of the working-tree `_handoff_support.py` == `git show 83a9ccf:…` == `git show HEAD:…` == `7b62714a80d182b52a255f541ef5cea1f356ec0959ec23ba472977114ac550ef`.
- The whole `83a9ccf..HEAD` diff outside `docs/` is `tests/unit/test_handoff_support.py` (+28). The implementer's claim holds; not inherited.
- Both pinned seams `HOP_DIVISOR` and `CEILING_FACTOR` survive on the import line at HEAD (the format hook did not eat them this time).

### Round-2 mutation battery (27 mutations)

| # | Mutation | R1 | R2 | Sole failure |
|---|---|---|---|---|
| PC | `_DONE_STATUSES` drops `DONE_WITH_CONCERNS` | CAUGHT | **CAUGHT** | `test_done_and_concerns…` |
| M1 | consent: `pol = None` | SURVIVED | **CAUGHT** | `test_expected_hops_and_policy_cli…` |
| M2 | consent: `"off"` dropped | SURVIVED | **CAUGHT** | same |
| M2b | consent: `"ask"` dropped | SURVIVED | **CAUGHT** | same |
| M3 | always `"indeterminate"` | SURVIVED | **CAUGHT** | `test_malformed_older_outcome_truncates…` |
| M4 | `_OUTCOME_RE` → `r""` | SURVIVED | **CAUGHT** | `test_intent_rows_between_outcomes…` |
| M5 | `task_id` bool guard removed | SURVIVED | **CAUGHT** | `test_done_and_concerns…` |
| M6 | `task_id` int+bool guards removed | SURVIVED | **CAUGHT** | same |
| M7 | `isinstance(fm, dict)` removed | SURVIVED | **CAUGHT** | `test_non_mapping_and_invalid_yaml…` |
| M8 | `yaml.safe_load` try/except removed | SURVIVED | **CAUGHT** | same |
| M9 | archive glob neutered | CAUGHT | **CAUGHT** | `test_archives_counted…` |
| M10 | dedup broken | CAUGHT | **CAUGHT** | same |
| M11 | non-dict JSON not nulled | SURVIVED | SURVIVED | — (dispositioned **P7-5**) |
| M12 | `except ImportError` → `print(0)` | SURVIVED | SURVIVED | — (round-1 **Minor 4**, scheduled) |
| **N1** | lazy `import yaml` hoisted to module top | — | **SURVIVED** | → Minor B |
| **N2** | `derive_expected_hops(manifest or {})` → `(manifest)` | — | **SURVIVED** | → Minor A |
| **N3** | `_cli` consent `isinstance(h, dict)` removed | — | **CAUGHT** | `test_expected_hops_and_policy_cli…` |
| **N4** | `derive_expected_hops` `isinstance(h, dict)` removed | — | **SURVIVED** | → Minor D |
| **N5** | `stall_streak` `except OSError: return 0` → `"indeterminate"` | — | **SURVIVED** | → Minor C |
| **N6** | `_frontmatter` `startswith("---")` check removed | — | SURVIVED | verified-clean (redundant guard) |
| **N7** | `_REPORT_GLOB` trailing `*` removed | — | SURVIVED | verified-clean (unused, harmless) |
| **N8** | stall compare `==` → `>=` | — | SURVIVED | verified-clean (over-blocking = conservative) |
| **N9** | `reversed()` dropped (control) | — | **CAUGHT** (2) | correctly breaks two |
| **N10** | `derive_total_tasks` `task_ids` bool guard removed | — | **CAUGHT** | `test_bool_never_counts…` |
| **D1** | M5 **+ fixture reverted to `task_id: yes`** | — | **SURVIVED** | the deviation, confirmed |
| **D2** | M5 + landed `task_id: no` fixture | — | **CAUGHT** | the deviation, confirmed |
| **D3** | N10 **+ sibling `[True, 2]` → `[True, 1]`** | — | **SURVIVED** | → Nit 2 |

---

## The deviation: the implementer was right and round 1 was wrong

**Verified by mutation, both directions**, as instructed:

| Fixture | Mutation | Suite | Count | Verdict |
|---|---|---|---|---|
| `task_id: yes` (**my round-1 prescription**) | M5 (bool guard removed) | **29 passed** | stays **2** | **SURVIVED — vacuous** |
| `task_id: no` (**landed**) | M5 | **1 failed, 28 passed** | moves to **3** | **CAUGHT** |

The mechanism is exactly as reported: PyYAML resolves YAML 1.1 `yes` → `True`; `hash(True) == hash(1)` and `True == 1`, so `done.add(True)` collapses into the already-counted task 1 and the count never moves. `no` → `False` → `0`, which is not in `{1, 2}`, so the mutant reaches 3 and the assertion fires. **My round-1 Minor 2 fix was itself vacuous; the implementer's substitution is correct and its comment states the reason accurately.**

### The generalization — I checked whether the same assumption is load-bearing anywhere else

It is, in one more place, and it is one character from failing. See **Nit 2**.

---

## Anchor integrity of the two extended tests

Both extended tests remain the **sole** failing test for every mutation they anchor — measured, not read:

- `test_expected_hops_and_policy_cli_on_legacy_and_garbage` is the sole failure for M1, M2, M2b **and** N3.
- `test_done_and_concerns_count_blocked_and_malformed_do_not` is the sole failure for PC, M5 **and** M6.

No mutation produced a multi-test failure except control N9, which is expected to. **Uniqueness is preserved; descriptiveness is not** — see Nit 1.

---

## Blocker

None.

## Major

### Major 3 — RECORD INTEGRITY: the measured AC-5 violation is absent from `deviations.md`, and the transition archives the only file that holds it

**This is the one finding that exists because of *when* this review runs, and it is the only one that cannot be recovered after the transition.**

**Measured, with `/usr/bin/grep` over `docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md`:**

| Query | Matches |
|---|---|
| `P7-1` / `P7-3` / `P7-4` / `P7-5` | present (rows 166–169) |
| `UnicodeDecodeError` (round-1 **Minor 1**) | **0** |
| round-1 **Minor 4** (the `except ImportError` mitigation is untested) | **0** |
| `AC-5` / `AC5` | **0 — the string does not occur in the file** |

Round-1 Minor 1 is not a coverage gap; it is a **measured** `UnicodeDecodeError` → exit 1 → empty stdout, against an AC whose text is *"never an exception."* It, Minor 4, and round-2 **Minor C** live **only** in `task-007-quality-review.md`.

**Failure direction — over-permissive, which is why this is Major and not a Nit.** `transition-module.py` archives `reports/` into `archive-<module>/` and truncates the dispatch log; the pre-completion aggregate gates then lose cross-module visibility (the known limitation already recorded in this fork's `CLAUDE.md`). `deviations.md` is the register that *does* survive the boundary — `transition-module.py` appends its transition row to it. A defect recorded only in an archived report, against a checkbox rendered green, is indistinguishable at Module 3 from a defect that never existed. **The record would assert an acceptance criterion is satisfied when this review measured it failing.**

**Reachability: certain, and imminent.** The controller stated it is about to check the box and transition.

**Why it is in scope *here* rather than scheduled:** unlike Minor C and round-1 Minor 1, the fix touches **no production code, no fenced plan body, and no test** — it is three appends. Round 1's calibration puts over-permissive-and-fixable-here in the Major bucket, and this is the only round-2 finding that lands in it.

**Fix — the three conditions on the transition:**

1. Append a `deviations.md` row for round-1 **Minor 1** (`UnicodeDecodeError` escapes `except OSError` in `count_tasks_done`; measured exit 1 + empty stdout) → Module 3, beside P7-3.
2. Append rows for round-1 **Minor 4** and round-2 **Minor C** (`stall_streak` fails open on an unreadable log) → Module 3.
3. Mark Module 2's AC-5 checkbox in `module-2-models-budget.md` as **partial**, pointing at those rows, instead of checking it green.

---

**No other Major.** Applying round 1's own calibration — *Major = untested behavior whose failure direction is over-permissive and reachable on a machine-generated path, and fixable here* — nothing new qualifies. Minors A, B and D fail in the **crash** direction. Minor C is genuinely over-permissive but its fix is a production edit to a plan-verbatim body, identical in kind to round-1 Minor 1 and P7-3, both of which stand scheduled; filing it Major would mean blocking on a row I would immediately schedule. I am not manufacturing a Major to look thorough.

## Minor

### Minor A — `expected-hops` on an unreadable manifest is untested: the missing mirror of the one fail-closed case that *is* tested

**Mutation N2:** `derive_expected_hops(manifest or {})` → `derive_expected_hops(manifest)`. **SURVIVED**, 29 passed.

| Input | Guarded (HEAD) | Mutated (N2) |
|---|---|---|
| `expected-hops --manifest /nonexistent/m.json` | `unknown`, **exit 0** | `AttributeError: 'NoneType' object has no attribute 'get'`, traceback, **no value on stdout** |
| positive control, readable manifest | `2`, exit 0 | `2`, exit 0 |

The CLI test already pins the *consent* half of the unreadable-manifest contract (`spawn-policy` on `no.json` → `ask`, "fails CLOSED") but never the *budget* half on the same input. **This is a Module 2 AC-5 path that is already correct and closable for free — one assertion, no production edit, no deviation.** Given AC-5 is the contested checkbox, closing a third of its open surface for one line is worth doing.

**Reachability — CORRECTED after checking the consumer, and it is LOW.** My first draft claimed Module 3 calls `expected-hops` on an unproven path. That is wrong, and I am stating it rather than quietly dropping the Minor. `module-3-spawn-script.md` guards the call three ways: `if [ -f "$MANIFEST_FILE" ]`, then `2>/dev/null`, then `[[ "$EXPECTED_HOPS" =~ ^[0-9]+$ ]] || EXPECTED_HOPS="unknown"`. **A crash here would be absorbed by the shell and degrade to `unknown` anyway.** The residual live gap is narrow: `-f` proves existence, not readability, so a present-but-unreadable manifest still reaches the branch.

This Minor therefore stands on **contract-pinning, not live risk** — AC-5 is a statement about the CLI's own behavior, and this is the one AC-5 path that is already correct and costs one line to pin. Weight it accordingly.

**Fix** (one line, in `TestCli.test_expected_hops_and_policy_cli_on_legacy_and_garbage`, beside the existing `ask` assertion):

```python
eh = self._run("expected-hops", "--manifest", str(tmp_path / "no.json"))
assert eh.returncode == 0 and eh.stdout.strip() == "unknown"   # AC-5: degrades, never raises
```

### Minor B — the lazy `import yaml` invariant is stated in the docstring, load-bearing, and unpinned

**Mutation N1:** hoist `import yaml` to module top, delete the lazy import in `_frontmatter`. **SURVIVED**, 29 passed.

| Probe | Guarded (HEAD) | Mutated (N1) |
|---|---|---|
| `import _handoff_support; 'yaml' in sys.modules` | **False** | **True** |
| positive control (`import yaml`) | True | True |

**Why it matters more than coverage.** If the import moves to module scope, the `except ImportError: print("unknown")` mitigation in `_cli` becomes **dead code** — the import fails before `_cli` is ever entered, so *all four* subcommands die on a venv-less `python3`, not just `tasks-done`. That mitigation is the accepted remedy for dispositioned **P7-3**. **Module 3 is scheduled to edit `count_tasks_done` for P7-3 — precisely the edit that could hoist the import** — and no test would notice.

**Reachability of the regression:** a single scheduled Module 3 edit, by an implementer with no reason to know the invariant exists outside a docstring line.

**And its downstream direction is over-permissive, not merely a crash — via an already-dispositioned row.** A module-scope `import yaml` on a venv-less `python3` is a CLI that *fails to run at all*. That is verbatim the case **P7-1(i)** names: the planned shell reads `SPAWN_POLICY="$(… 2>/dev/null)"` then `case … *) SPAWN_POLICY="auto"`, so empty stdout coerces to **`auto`** — spawn-without-asking. **I am NOT re-filing P7-1(i); it is correctly scheduled to Module 3 Task 8 and already prescribes `*) SPAWN_POLICY="ask"`.** I record the linkage because it changes this Minor's weight: until P7-1(i) lands, hoisting this import silently converts the consent gate from fail-closed to fail-open. Pinning the invariant is cheap insurance on a gate two separate reviews have already found fail-open.

**Fix** (one test; needs **no** `PYTHONPATH` harness and no PyYAML-absent interpreter — round 1 ran this probe by hand but did not pin it):

```python
def test_module_import_is_stdlib_only(self):
    code = "import sys; sys.path.insert(0, %r); import _handoff_support; print('yaml' in sys.modules)" % str(SCRIPTS)
    assert subprocess.run([VENV_PY, "-c", code], capture_output=True, text=True).stdout.strip() == "False"
```

### Minor C — `stall_streak` fails OPEN on an *unreadable* log, not just a missing one — the last over-permissive site in the module

`except OSError: return 0  # no log yet: first hop` conflates two cases. **Proven by direct invocation, not by mutation** (the shipped code *is* the permissive branch, so no mutation can expose it):

| Input | Result |
|---|---|
| `--spawn-log /nonexistent/h.log` (genuinely first hop) | `0`, exit 0 — **correct** |
| `--spawn-log <a directory>` (`IsADirectoryError`, an `OSError`) | `0`, exit 0 — **"no stall, proceed"** |

Any `OSError` — permission denied, a path clobbered into a directory, an I/O error — reports *no stall* and the runaway-hop guard silently stops guarding. Contrast the consent gate on the very same class of failure, which the plan deliberately made fail **closed**. Note also that **no test exercises a nonexistent log at all**: `TestStallStreak._streak` always writes the file, so even the intended first-hop path is unpinned in either direction.

**Disposition: SCHEDULE to Module 3, do NOT fix in Task 7.** Distinguishing the two cases is a production edit to a body that is verbatim from the plan's fenced block — the identical constraint that kept round-1 Minor 1 and P7-3 out of this task. All three are degradation-contract defects in the same two functions and Module 3 should fix them in one pass under one reviewer's attention. **The first-hop-vs-unreadable test is test-only and could land here** if the controller wants partial credit; I am not requiring it.

**Fix (Module 3):** `except FileNotFoundError: return 0` / `except OSError: return "indeterminate"`, and add both fixtures.

### Minor D — `derive_expected_hops`'s `isinstance(h, dict)` guard is unpinned, while its `_cli` twin is pinned

**Mutation N4:** `eh = h.get("expected_hops") if isinstance(h, dict) else None` → `eh = h.get("expected_hops")`. **SURVIVED**.
**Contrast N3**, the same guard in `_cli`: **CAUGHT** (sole failure). Two sibling guards, one observed, one not.

| `{"total_tasks": 5, "handoff": "auto"}` | Guarded (HEAD) | Mutated (N4) |
|---|---|---|
| `expected-hops` | `2`, exit 0 | `AttributeError: 'str' object has no attribute 'get'` |
| `spawn-policy` | `auto`, exit 0 | (N3) `AttributeError` |

`manifest.get("handoff") or {}` does **not** save it: a truthy non-dict (`"auto"`, `[1]`) passes straight through the `or`. Reachability is hand-edit-only, like dispositioned P7-1(ii) — but unlike P7-1(ii) this costs one fixture line and no production edit.

**Fix:** one assertion in `TestDeriveExpectedHops` — `assert derive_expected_hops({"handoff": "auto", "total_tasks": 5}) == 2`.

## Nit

### Nit 1 — anchor-name erosion on the two extended tests

Uniqueness holds (measured above), but the names no longer describe what breaks. `test_expected_hops_and_policy_cli_on_legacy_and_garbage` now anchors six properties including the **honored-policy** path — which is neither "legacy" nor "garbage" and is the single most safety-relevant assertion in the file. `test_done_and_concerns_count_blocked_and_malformed_do_not` now also anchors both `task_id` **type guards**. Packing properties behind one name is what degrades a mutation anchor over time: the next reviewer sees one red test and three plausible causes. Recommend splitting out `test_declared_spawn_policy_is_honored` and `test_task_id_type_guards` when Module 3 next touches this file. Not required — the implementer added accurate inline comments, which mitigates it.

### Nit 2 — the `hash(True) == hash(1)` trap is live in one more fixture, one character from vacuous

`test_bool_never_counts_as_a_total_or_a_task_id` asserts `derive_total_tasks({"total_tasks": 0, "modules": [{"task_ids": [True, 2]}]}) == 1`. It discriminates **only because the sibling is `2`**:

| Fixture | Bool-guard mutation (N10) | Result |
|---|---|---|
| `[True, 2]` (**landed**) | guard removed | **CAUGHT** — `{True, 2}` → 2 ≠ 1 |
| `[True, 1]` (**D3**, one character changed) | guard removed | **SURVIVED** — `{True}` collapses to `{1}` → 1 == 1 |

This is the *identical* set-collapse that made my round-1 `task_id: yes` prescription vacuous, in a different fixture, currently passing for a reason nobody wrote down. **The standing rule this family needs — six sites over four rounds, and now a seventh near-miss: a bool-guard fixture whose value lands in a `set` must use `False`/`0` or keep a sibling that is not `1`.** Recommend a one-line comment on that fixture stating it, so the next edit cannot silently disarm it.

### Nit 3 — verified-clean, reported as measured

- **N6** `startswith("---")` is redundant with the `find("---", 3) == -1` check for every fixture shape; both paths return `None`. Not a defect.
- **N7** `_REPORT_GLOB`'s trailing `*` is currently unused — `task-*-implementer-report.md` matches everything the full pattern does, *including* this feature's live `task-007-fix-implementer-report.md`, which the wider pattern also matches and which dedupes correctly on `task_id`. Harmless either way.
- **N8** `==` → `>=` on the stall comparison survives, but overstates the streak → blocks **earlier**. Conservative direction. Not filed.
- **N9/N10** re-confirm `reversed()` and `derive_total_tasks`'s `task_ids` bool guard are properly pinned.

---

## Module 2 AC-5 — my view, stated plainly, and the condition on the transition

**The AC-5 box must NOT be checked green. It may be checked only as an explicitly-annotated PARTIAL, and only if the annotation lands somewhere the transition does not archive.**

The reason is literal, not stylistic. AC-5 reads *"CLI prints `unknown` / `indeterminate` as values (exit 0) — degradation is observable, never an exception."* Round 1 **measured** a `UnicodeDecodeError` → exit 1, empty stdout (Minor 1). That is the AC's own text failing, not a coverage gap. It is now carried by **four** open rows, not two — round-1 Minor 1 and P7-3, plus round-2 **Minor A** (untested, correct today) and **Minor C** (an unreadable spawn log reporting "no stall").

The **defects** should not block the module: round 1 dispositioned the production-edit rows as SCHEDULE-to-Module-3 on the plan-verbatim-body constraint, and blocking on rows I scheduled would be incoherent. What blocks is **where the record lives** — filed above as **Major 3**:

> **`docs/imp-plans/2026-07-30-cmux-spawn-v2/deviations.md` contains rows for P7-1, P7-3, P7-4 and P7-5 — but ZERO rows for round-1 Minor 1 (the measured `UnicodeDecodeError`) or round-1 Minor 4, and the string `AC-5` does not appear in the file at all.** Verified with `/usr/bin/grep`: `UnicodeDecodeError` → 0 matches; `AC-5|AC5` → 0 matches.

Those two findings exist **only** in `task-007-quality-review.md` — the file the transition is about to archive, at the same moment the aggregate gates (Check 7 min-tier ratio, Check 9 git-reality) lose cross-module visibility. A measured acceptance-criterion violation would become invisible to every durable artifact.

**Condition on the transition (controller action, no code, no re-review):**

1. Append a `deviations.md` row for round-1 **Minor 1** (`UnicodeDecodeError` escapes `except OSError` in `count_tasks_done` — a measured AC-5 violation) → Module 3, alongside P7-3.
2. Append a row for round-1 **Minor 4** (the `except ImportError → "unknown"` mitigation is untested) and for round-2 **Minor C** (`stall_streak` fails open on an unreadable log) → Module 3.
3. Mark the AC-5 checkbox **partial** in `module-2-models-budget.md` with an inline pointer to those rows, rather than checking it green.

If those three land, checking AC-5 as an annotated partial is honest and I have no objection. **If they do not, the box must stay open** — an unchecked box is recoverable; a green box over an archived, measured violation is not.

Minors A, B and D are test-only, need no deviation from any fenced body, and are recommended for the fix round or for Module 3's first touch of this file. They are **not** required to close Task 7.

---

## Stopping rule — called as measured, on both conjuncts separately

- **Findings are cosmetic — for the CODE: YES.** The four Minors are (A) a free one-line assertion, contract-pinning only, (B) a one-test invariant pin, (C) explicitly scheduled under the constraint the controller already accepted, (D) a one-line fixture. No Blocker. No Major against the implementation.
- **Findings are cosmetic — for the RECORD: NO.** Major 3 is not cosmetic and is not schedulable: after the transition it is unfixable, because the artifact that carries the finding is archived and the checkbox that contradicts it is green.
- **Reviewer approves — the code: YES.**

Task 7's code and tests are done. Every required round-1 finding closes by mutation as the sole failure, the fix is provably test-only, both pinned seams survive, and the one deviation from my own prescription was correct and is now confirmed in both directions — my `task_id: yes` was vacuous and the implementer's `no` is not.

I am not manufacturing a Major to look thorough, and I am not downgrading one to close the module. Major 3 costs three appends and no code.

---

**APPROVED (Task 7 — code and tests).**

**TRANSITION BLOCKED until Major 3's conditions 1–3 land.** Module 2's **AC-5 must not be checked green.** If the two deviations rows and the partial annotation are not in `deviations.md` and `module-2-models-budget.md`, **the box stays open.** An open box is recoverable; a green box over an archived, measured violation is not.

Once conditions 1–3 land, no re-review is required — they are appends, and I have already approved everything they describe.
