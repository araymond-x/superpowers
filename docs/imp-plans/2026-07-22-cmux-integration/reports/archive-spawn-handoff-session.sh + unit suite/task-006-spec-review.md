# Task 6 — Spec Compliance Review

**Reviewer:** general-purpose spec compliance auditor
**Commit reviewed:** `5c6e4d9` (base `3f4f0ae`)
**Date:** 2026-07-24
**Verdict: FAIL** — 1 BLOCKING [MISSING], 1 ADVISORY

> Dispatch note: two earlier reviewer dispatches were terminated by transient API server errors
> mid-response (~110–130k subagent tokens each, no usable output). This review is the resumed
> third attempt, run with a hard output budget. The failures were infrastructure, not findings.

## Q1 — Ordering

Reservation (`:388–391`: `mkdir -p`, hop write, `intent` printf) is straight-line code
immediately before `spawn_claude_workspace` (`:393`). No `set -e`, no subshell, no early
`return` between them. The only skip path is the `--dry-run` short-circuit (`:375–379`, correct
per spec). All earlier exits (1/3) precede any spawn. **Order cannot invert.**

*Advisory:* neither reservation write's rc is checked and there is no `set -e`, so a failed
`.handoff-hops` write would still proceed to spawn — a hole in Decision 21's durability
guarantee. See findings.

## Q2 — REQUIRED DEVIATION #1, verified BY EXECUTION ✅

`xpg_echo` is `off` in this bash, so the diagnostic line is faithful; the reviewer nevertheless
captured the `--command` bytes losslessly via a `printf %s` cmux stub, then executed them with a
picker stubbed to `exit 7`:

```
2026-07-24T17:15:16Z ffbe48d3-0978-457f-8b58-33f9df781544 intent hop=1
2026-07-24T17:15:23Z ffbe48d3-0978-457f-8b58-33f9df781544 runtime-picker-failure hop=1
```

Parent uuid is field 2; field order is `timestamp, spawn-id, record-type, hop` per §5.4d; the
interactive fallback then ran (`picker: INTERACTIVE fallback launched with: /pickup b1`). The
worked-example comment (`:341–347`) matches the real emitted bytes. **Deviation #1 is complete
and correct.**

## Q3 — Exit-code ladder vs §5.5 (executed, 9 paths) ✅

`auto=0`, `picker-manual=0`, `notify-fail=0` (+ warn on stderr), `spawn-failed=3` with
`.handoff-hops` retained at `1`, `outcome … spawn-failed` written, and
`print_manual_instructions` emitted. Pre-existing refusals unchanged: dirty tree `1`,
bundle-invalid `1`, hop-limit `3`, quota-low `3`, not-in-cmux `3`. **Matches §5.5 exactly.**

## Q4 — REQUIRED DECISION #2 — **BLOCKING**

**The justification does not hold.** `cmux new-workspace` **does** return a usable ref on
stdout. Live probe (throwaway workspace created and closed):

```
$ cmux new-workspace --name REVIEW-PROBE-DELETEME --cwd /tmp --focus false
OK workspace:6          # rc=0; workspace:6 then confirmed in `cmux list-workspaces`
```

The report's supporting claim is also factually wrong: `identify` / `list-workspaces` have **no**
`--json` flag either (`grep -c -- --json` = 0 for all three) — `identify` simply emits JSON
unconditionally. Absence of `--json` was never evidence of absence of output, and the implementer
explicitly declined the one probe that would have settled it.

Capturing is a one-line change (`OK <ref>` on stdout; `CMUX_QUIET=1` suppresses the alias
deprecation notice), **not** the "parse layer" the deviation claimed was out of scope. §5.4d
step 3 (outcome `workspace ref`; notify `… spawned in <workspace-ref>`) and step 4 ("Print the
workspace ref and exit 0") are **unmet**.

## Q5 — The 7th test is spec-mandated, not scope creep ✅

M2a reproduced: moving the `intent` printf after the spawn leaves the plan's
`kinds.index("intent") < kinds.index("outcome")` **green** and fails **only**
`test_reservation_lands_before_cmux_new_workspace_runs`. Decision 21 / §5.4d is a *timing*
contract ("reserve **before** spawn"), so proving record order alone is insufficient. The test is
discriminating (also RED under M3, green on unmutated code).

## Q6 — `--dry-run` ✅

Executed *with* `CLAUDE_CODE_PICKER_APPEND_PROMPT` set (a case the plan's test omits): `rc=0`,
no `append-prompts/` dir, no `.handoff-hops`, no `handoff-spawn.log`, no `cmux.log`. Zero side
effects; the pre-short-circuit uuid is pure computation.

## Q7 — Scope discipline ✅

Diff is 3 hunks (`@@ -218`, `@@ -236`, `@@ -318`). `spawn_handoff_helpers.py` and
`tests/integration/` are byte-untouched. No deferred-list line appears in the diff
(`max(0,…)`/`255 - len(suffix)`, surrogate handling, `command -v claude-picker`, telemetry value,
`shq()` rc, `QUOTA_TIMEOUT`, `_successor_cmd`). No e2e step added.

## Q8 — `mkdir` → `os.makedirs` routing ✅

Executed with `append-prompts` pre-created as a *file*: `rc=0`, `launch=picker-manual`, successor
command degrades to `claude-picker '/pickup b1'`, and **no** raw `mkdir:` leak on stderr — i.e.
`sys.exit(4)` → `ARGS_OK=0` → picker-manual, exactly as required. `APPEND_TARGET_DIR` is
vestigial-but-used (only builds `APPEND_TARGET`); accurately reported.

## Q9 — Mutation credibility ✅

Reproduced 4 of the 6 the controller had not verified: **M1** (literal `spawn`) → 3 RED incl.
both spawn-id tests; **M2a** → 1 RED (reservation test only); **M3** (drop hop write) → 2 RED;
**M4** (drop dry-run block) → 1 RED. All match the report line-for-line. M2b/M5 not re-run —
claimed-and-consistent.

## Q10 — Report completeness ✅

`validate-report.py` → `sections_missing: []`; all 5 prose sections present and substantive. Root
`CLAUDE.md` read; correctly notes no subdirectory `CLAUDE.md` exists under `tests/`,
`tests/unit/`, or `skills/subagent-driven-development/` (verified).

## Contract Constraints — all 11 re-checked ✅

`--handoff-contract` string equality (`:301`); `--git-common-dir` realpath identity (`:105–115`);
no-eval v1 decode (`:222–230`); append-prompt consumed + substituted (`:233–255`, now executed);
readability check only under `--non-interactive` (untouched); telemetry on/off (`:285`); `-f`
**and** `-x` (`:298`); quota fail-open (5 malformed bodies → `unchecked`, only `low:` exits 3);
reservation-before-spawn (Q1/Q3); 255 label ceiling with suffix reserved (`:279–280`);
compose-side quoting.

**`$SPAWN_ID` not routed through `shq()` is COMPLIANT** — the constraint enumerates "each decoded
arg, version, label"; spawn-id and hop are script-generated uuid4/integer values, matching the
existing `$SP_HOP` treatment.

---

## Findings

- **`[BLOCKING] [MISSING]`** — `spawn-handoff-session.sh:395–400, :394`. §5.4d steps 3–4 require
  the workspace ref in the outcome record, the notify body, and stdout. `cmux new-workspace`
  **does** emit it (`OK workspace:6`, verified live); the deviation's premise ("cmux does not
  return one", `:396`) is false, as is the report's `identify`/`list-workspaces` `--json`
  contrast. Fix: capture stdout (`CMUX_QUIET=1`, take the `OK <ref>` token), use it in
  `workspace=<ref>`, the notify body, and the final `echo`; keep the `(spawned)` constant only as
  the empty-capture fallback. The code comment at `:395–398` must be corrected either way.

- **`[ADVISORY]`** — `:390–391`. Reservation writes are unchecked and the script has no `set -e`;
  a failed `.handoff-hops` / `intent` write still proceeds to spawn, weakening Decision 21's
  "hop consumption is durable" guarantee. Cheap fix: `|| { warn; print_manual_instructions;
  exit 3; }` before spawning.

Everything else — Deviation #1, the exit ladder, `--dry-run`, the `makedirs` move, the extra
reservation-timing test, scope discipline, and all 11 contract constraints — is **verified
compliant by execution**.

---

# SPEC RE-REVIEW after `[task 6 fix]` — **PASS**

**Re-reviewed:** commit `3491171` (fix) over `5c6e4d9` (feature)
**Verdict: PASS** — the blocking finding is CLOSED; no regression. 2 non-blocking advisories.

## R1 — Blocking finding CLOSED ✅

Auto happy path, cmux stub emitting `OK workspace:6`, rc=0:
- outcome: `… outcome hop=1 workspace=workspace:6 launch=auto bundle=b1 quota=ok:63.0`
- notify argv: `[notify] [--title] [SDD handoff] [--body] [Hop 1/3 — successor spawned in workspace:6]`
- stdout: `[spawn-handoff] spawned successor in workspace:6 (launch=auto). STOP this session.`

All three §5.4d step-3/4 consumers carry the real ref. The false code comment is replaced with an
accurate, dated one.

**Critical independent check — the reviewer did NOT accept the claimed format.** The cmux binary's
string table contains `OK workspace=%@ window=%@ index=%@` and **no** `OK workspace:N` literal, so
the reviewer ran its own live probe rather than trusting the fix report:
`CMUX_QUIET=1 cmux new-workspace --focus false` → stdout `OK workspace:10`, rc 0, stderr empty;
`awk '/^OK[ \t]/{print $2}'` → `workspace:10`. Probe workspace closed. The `%@` string belongs to a
different command. **Format confirmed correct.**

## R2 — Field order intact ✅
`<ts> <spawn-id> outcome hop=N workspace=<ref> launch=<mode> bundle=<id> quota=<st>` — matches
§5.4d's Log format exactly; the ref occupies the workspace-ref slot and displaced nothing
(failure path keeps the same order with `workspace=spawn-failed`).

## R3 — `(spawned)` correctly confined ✅
Stub printing nothing (rc=0) → `workspace=(spawned)`, notify `…spawned in (spawned)`. Stub
printing a non-`OK` line → same. No dangling empty tail in any rendering; `{workspace}` is always
substituted before notify.

## R4 — No regressions ✅
- (a) **Correlation:** intent id == outcome id == the uuid embedded in the successor command's
  `runtime-picker-failure` printf (set equality True). The spawn-failed outcome shares it too.
- (b) **Ladder:** auto **0**; picker-manual (contract probe → `2`) **0**; notify-fail (stub
  `exit 5`) **0** with the successor still logged; spawn-failed **3** with `hops=1` consumed,
  `workspace=spawn-failed`, manual instructions printed; not-in-cmux **3**; quota-low **3** (both
  leaving no log/hops).
- (c) `--dry-run`: rc 0, `reports/` empty, no `.handoff-hops`, no log.
- (d) `os.makedirs` failure → `sys.exit(4)` → `ARGS_OK=0` → `launch=picker-manual`, rc 0.

## R5 — Core still generic (Decision 15) ✅
`spawn_claude_workspace()` references only its 4 params + `cmux`; no bundle id, hop, feature, or
launch-mode leaks in. `{workspace}` substitution is a mechanical token, not policy. Publishing a
global is consistent with the script's established style (`SP_HOP`, `QUOTA_STATUS`, `LAUNCH_MODE`,
`ARGS_OK`, `SPAWN_ID` are all function-set globals); bash cannot return a string alongside an exit
code, and the exit code is load-bearing.

## R6 — mktemp-failure branch
Degradation is correct (`rc=$?` from the direct invocation; output goes to the terminal rather
than being discarded; empty ref → `(spawned)`). **Untested** — see advisory.

## R7 — Mutations independently reproduced ✅

| Mutation | Claimed | Reproduced |
|---|---|---|
| M-A drop awk capture | 2 RED | 2 RED ✔ |
| M-B notify loses `{workspace}` | 3 RED | 3 RED ✔ |
| M-D outcome reverted to `(spawned)` | 2 RED | 2 RED ✔ |
| M-E `awk` → `while read` | 1 RED | **1 RED, exactly `..._survives_missing_trailing_newline`** ✔ |
| M-G remove `cat "$out_f" >&2` | 1 RED | 1 RED ✔ |

**The M-E hazard is real**, verified two ways: the mutation goes RED only on that test, and a stub
emitting `printf 'OK workspace:6'` (no trailing newline) captures correctly under `awk` — a
`while read` loop would drop it, silently degrading *every real spawn* to `(spawned)` while
echo-based stubs stayed green. Non-obvious and genuinely load-bearing.

## R8 — Scope clean ✅
2 files, 2 hunks (`@@ -356` spawn core, `@@ -391` spawn sequence).
`tests/unit/spawn_handoff_helpers.py` byte-unchanged (identical sha at `5c6e4d9` and HEAD).
The deferred `:390-391` advisory is **still unfixed** (reservation writes at now-`:422-423` remain
unguarded) — correctly left for the sweep round.

## R9 — Report numbers hold ✅
5 new tests; `test_spawn_handoff.py` **56 passed**; full `tests/unit/` **609 passed**.
`CMUX_QUIET=1` is real — it appears at exactly one site in the binary, the alias-deprecation
string guarded by `CMUX_CLI_DEPRECATION_SHOWN`. It cannot suppress the `OK` line, and the live
quiet probe emitted `OK workspace:10` with empty stderr. Confirmed live that `new-workspace` IS
the deprecated alias, matching the code comment.

## Advisories (neither blocks; PASS stands)

- `[ADVISORY] [MISSING]` `spawn-handoff-session.sh:393-397` — the mktemp-failure branch is
  untested (nothing forces `mktemp` to fail). The degradation is safe as written, but a future
  edit could break rc propagation there undetected. Settle with a stub-`mktemp`-on-PATH test in
  the sweep round.
- `[ADVISORY] [EXTRA]` `spawn-handoff-session.sh:400` — `--title "SDD handoff"` is hardcoded
  inside the "extraction-ready" core. Pre-existing and passed by the first review; the fix touched
  only the `--body` substitution on that line, so it is not a regression. Noted for the eventual
  extraction, not for this task.

Nothing tagged `[UNVERIFIED]`.
