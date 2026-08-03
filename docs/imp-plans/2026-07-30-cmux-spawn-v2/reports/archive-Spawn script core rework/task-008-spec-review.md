# Task 8 — Spec Compliance Review

**Status:** PASS

Reviewed at HEAD `a85d347` across commits `239532a`, `43ff224`, `31519be`. Model: opus.

## 1. Fence fidelity

All 7 fenced blocks in Task 8's span extracted programmatically and diffed against landed code.

| Fence | Result |
|---|---|
| Step 4(b) config knob (bash, 7 ln) | **matches** — contiguous byte-identical at `spawn-handoff-session.sh:35` |
| Step 4(d) Precondition 2b consent gate (bash, 22 ln) | **matches** — byte-identical at `:165` |
| Step 4(e) progress/ceiling derivation (bash, 25 ln) | **matches** — byte-identical at `:218` |
| Step 4(e) stall + over-expected (bash, 19 ln) | **matches** — byte-identical at `:252` |
| Step 1 helpers (python, 35 ln) | **matches** — all five functions **AST-identical** incl. docstrings |
| Step 2 `TestPolicyDial` | **matches** — all 6 names; every prescribed assertion present; landed adds a strict superset |
| Step 2 `TestStallAndCeiling` | **diverges (DECLARED)** — ceiling test split in two; 3 extra test functions. Declared in the report, accepted in `deviations.md` |

**Non-fence additions inventoried exhaustively** — fence-matching alone does not prove nothing else landed. Every added shell line not belonging to a Task-8 fence: **19 lines, all accounted for, zero undeclared.** 5-line `# NOTE:` stub at the deleted Layer-0 block (declared); 6-line fail-open rationale above step (e) (declared); 2 section headers matching the file's existing `# --- Precondition 3 ---` convention; step (a) 2 lines, (c) 1, (f) 1 verbatim per prose; 2 messages changed `hop limit` → `hop ceiling`, which step (e)'s prose mandates. **Both declared comment blocks verified as exactly what they claim — nothing extra hides inside them.**

## 2. Step completeness

Steps 1, 2, 2b, 4(a)–(f), 5, 6 all **landed**; Step 3 is a process step accepted on report evidence. Step 2's migration block: all four breaking consumers landed (#1 via the declared `.handoff-hops=6` variant).

**All EIGHT Step-2b bullets verified IN CODE, not from the report's claims:** P7-1(ii) key-presence discriminator + 8-form battery + legacy positive control; P7-2 three `stall-streak` CLI tests; P7-3 `_require_yaml()` **before** the glob, pinned on empty AND absent dirs with 2 positive controls; P7-5 five non-object forms → `ask`; P7-6 `except (OSError, UnicodeDecodeError)` function + CLI; P7-7 populated-dir fixture kept separate from P7-3, positive-controlled; P7-8 `FileNotFoundError` arm **first**, missing-log control in the same battery; P7-9 (A)(B)(D) all three.

## 3. Register table accuracy — all 11 rows verified

- **B1 PARTIAL claim is CORRECT.** `_did_not_spawn` is `"new-workspace" not in _cmux_log(...)` and the script still emits `cmux new-workspace` (`:546`). The assertion is sound today and only goes fail-open when Task 9 switches the verb — **deferring the rewrite is right; pinning it now would pin the wrong verb.**
- **P7-4 both halves VERIFIED.** `stall-streak --tasks-done unknown` → **rc 2** (positive control `--tasks-done 3` → `0`, rc 0). The shell's `unknown` branch precedes the call. The bonus finding is real and now pinned by the new test + its byte-identical control.
- **P7-1(ii) VERIFIED live:** `"OFF"` → `ask`, `handoff: null` → `ask`, legacy no-key → **still `auto`**, explicit `auto` → `auto`.
- P7-1(i), P7-3, P7-5, P7-6, P7-7, P7-8, P7-9 — each "fixed" claim located in the diff. OP-1 discharged. STANDING RULE complied non-vacuously (no count-based bool fixture added; the one `true` body discriminates via the non-dict guard, so the `True == 1` trap is unreachable).

## 4. Contract constraints — all verified first-hand

`/bin/bash -n` **OK** on `GNU bash 3.2.57(1) arm64-apple-darwin25`. No `set -u/-e/pipefail` added (only 3 pre-existing comments; positive-controlled). `printf` for the intent record; every new `echo` is a fence-verbatim diagnostic. No producer piped into `grep -q` (no new `grep` at all). **`.handoff-hops` guard: `diff` of the 16-line region old vs new → byte-identical.** Reservation unchanged at `:590`+. Consent gate at `:165`, before the cmux-reachable check at `:187`; tests assert `.handoff-hops` absent and no intent record. Exit ladder: 12 `exit 0|1|3`, zero others. Shared-constants seam imported and now **load-bearing**.

**Caller audit re-run independently** (not accepted from the report): `count_tasks_done` has exactly one non-test caller (`_cli`, wrapped in `except ImportError`); `_frontmatter` exists only in `_handoff_support.py`; every other `*frontmatter*` hit is a differently-named function elsewhere. `materialize-manifest.py` imports only `expected_hops`, **AST-verified semantically unchanged**. No regression surface.

## 5. Test result — **741 passed**, 1 warning, 186.65s

Exactly the reported number (707 + 34). Test count independently recounted: 15 + 19 = 34. Also re-ran unprompted: regression validator **PASS 160/0/2**, `sdd-e2e-test.sh` **PASS, 15 steps** — including Step 14, which drives this very script (the new pre-reservation consent gate does not break it: that fixture ships no manifest, so the `[ -f ]` short-circuit keeps it `auto`).

## 6. Write-scope — clean

`git diff --name-only 239532a~1 31519be` = the 7 owned paths + `deviations.md` (dispatch-directed). `module-2-models-budget.md` and `BACKLOG.md` **untouched** (positive control: the filter pattern matches 2 tracked files, so it reaches). Module 2's file last changed at `c28e33d` (Task 7).

## Findings

1. **(Informational, not a divergence)** A formatter reflowed ~100 lines of *untouched* pre-existing code across four files, inflating the diff beyond the semantic change. Probed rather than assumed: an **AST comparison of every pre-existing top-level construct** shows the only semantically changed ones are exactly the intended P7 targets — `_frontmatter`, `count_tasks_done`, `stall_streak`, `_cli`, plus test classes that gained tests. `expected_hops`, `derive_total_tasks` and all Task-0 assertions are **formatting-only. Nothing rode in under cover of the reflow.** Declared, with the mitigation upgraded from "restore" to "make load-bearing".
2. **(Informational)** The report says "two tests beyond Step 2's list" but names three functions. A wording slip, not a hidden addition — all three are described in the same sentence and accepted in the register.

## Premises verified first-hand vs. accepted

**Measured:** all 7 fence diffs (byte- and AST-level); the 19-line non-fence inventory; 741 passed; regression 160/0/2; e2e 15 steps; `bash -n` on 3.2.57; the `.handoff-hops` byte-identity by `diff`; absence of `set` flags and `grep -q` pipes with positive controls; the exit ladder; write-scope with a positive control; `stall-streak --tasks-done unknown` → rc 2 with a numeric control; the P7-1(ii) battery with the legacy → `auto` control; B1's second-clause reasoning against `:546`; the caller audit; the single exact-equality field-set assertion; the semantic-vs-formatting AST split.

**Accepted on trust:** that each P7 pin is *discriminating* — the mutation-RED claims. The pins were verified to **exist and be shaped as the plan requires** (correct fixtures, required positive controls, correct handler ordering); measuring that each mutation actually goes RED is **the adversarial quality reviewer's job**, not spec compliance. Also accepted: Step 3's "ran to verify failures", which leaves no artifact.

---

## Controller disposition

**PASS accepted.** The review did the thing spec review is supposed to do and usually does not: it **inventoried the non-fence additions exhaustively** rather than only diffing the fences, which is the only way to prove nothing undeclared landed. Zero undeclared divergences across 19 added non-fence lines.

**The formatter finding is the most valuable thing here.** A ~100-line reflow of untouched code is exactly the cover under which a semantic change rides in unnoticed, and the reviewer refused to assume — it AST-compared every pre-existing top-level construct and demonstrated that the only semantic changes are the intended P7 targets. That is a positive control applied to a diff.

The controller's own independent full-suite run also returned **741 passed**, agreeing with the implementer and the spec reviewer — three independent measurements.

Proceeding to the adversarial code-quality review, which is where the mutation-discriminating claims this review explicitly deferred will be tested. It is 13-for-13 at finding real defects on green upstreams.
