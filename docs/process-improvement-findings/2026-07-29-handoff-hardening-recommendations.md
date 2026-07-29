<!--
PROVENANCE — added when this file was captured into the repo; everything below the
`---` rule is the original document, byte-for-byte unmodified.

  Author   : SDD/audit session `2b988cec-6c4c-435c-a76f-f75c636edb84` (the BACKLOG N60
             cmux capability audit), written 2026-07-29.
  Found at : ~/.claude-codex-handoff/bundles/2026-07-29T02-01-24Z-claude-codex-handoff/
             artifacts/included/handoff-hardening-recommendations.md
  Captured : 2026-07-29, unchanged apart from this header.

WHY IT MOVED. It was written into a /handoff bundle, which is the correct place for an
artifact that CARRIES work to another repo but the wrong place for the durable record of
a finding: `~/.claude-codex-handoff/` is not version-controlled, and
`claude-codex-handoff prune` deletes bundles. The analysis is reproduced here so it
survives; the bundle copy stays where it is for the toolkit session that will consume it.

SCOPE. These are RECOMMENDATIONS addressed to the `claude-codex-handoff` toolkit repo, not
to this fork. Nothing in either repo's `src/` was changed by their author. Read the
confidence labels the document defines (`a-run` / `a-file` / `a-help` / `inferred`) — they
are load-bearing, and one step in the trust-inheritance argument is explicitly `inferred`
and flagged as needing a two-minute test before anything relies on it.
-->

# Handoff/pickup hardening — surviving trust prompts, approval gates, and silent stalls

**Added 2026-07-29** as part of the N60 cmux capability audit, in response to: *"evaluate the handoff
skill approach and recommend hardening steps so that the handoff can survive a codex permissions
prompt or repo permissions step."*

**These are RECOMMENDATIONS, not changes.** Nothing in `src/` was edited. Implementing any of this
means editing a Claude command **and** its Codex skill mirror together —
`tests/test_command_skill_parity.py` fails on a half-done pair.

**Scope note.** `/handoff` and `/pickup` are used well beyond this repo — they are the transport for
the superpowers SDD context-handoff (N43), for cross-tool Claude↔Codex review, and for ad-hoc session
continuation. So hardening here is not a review-mode detail; a stall in this layer strands whatever
was using it. Where a recommendation is specific to the cmux review transport it says so.

**Confidence labels:** `a-run` = exercised; `a-file` = read from a live config/state file on this
machine; `a-help` = read from a binary's `--help`; `inferred` = reasoned from evidence, **not**
exercised. Labels are load-bearing — the audit that produced this document exists because an
unlabelled inference was once treated as a verified fact.

---

## 1. The headline: both tools' trust state is INSPECTABLE, and they behave OPPOSITELY

This is the most useful thing in this document, because it converts an unpredictable hang into a
preflightable refusal.

### Codex — ancestor-inherited *(a-file)*

`~/.codex/config.toml`:

```toml
[projects.'/Users/araymond']
trust_level = 'untrusted'
[projects.'/Users/araymond/projects']
trust_level = 'trusted'          # ← blanket over the whole tree
[projects.'/Users/araymond/projects/claude-custom/claude-codex-handoff']
trust_level = 'trusted'
```

Because `/Users/araymond/projects` is trusted wholesale, **a Codex trust prompt will essentially never
fire for normal repo work.** The exposure is paths outside that tree — and it is real, not
theoretical: the same table contains an explicitly trusted entry for a
`/private/tmp/.../scratchpad/boston-tea-party` path. A scratchpad does not become trusted by itself;
somebody answered a prompt to put it there.

### Claude — exact-path keyed, NO inheritance *(a-file, with one inferred step)*

`~/.claude.json` → `projects["<absolute path>"].hasTrustDialogAccepted`. Measured on this machine:
**36 paths tracked, 30 accepted, 6 not.**

The decisive observation is a parent/child pair where the flags disagree:

| Path | `hasTrustDialogAccepted` |
|---|---|
| `/Users/araymond/projects/qmd-search` | **true** |
| `/Users/araymond/projects/qmd-search/qmd` | **false** |

34 parent/child pairs are tracked as separate entries. A child carrying its own `false` under an
accepted parent is only meaningful if trust is **not** inherited — *(this last step is `inferred`; the
file contents are `a-file`, but Claude's resolution algorithm was not exercised. **Test it before
relying on it** — the test is two minutes: `cd` into a never-seen subdirectory of a trusted repo and
launch.)*

### Why the asymmetry is the whole point

| | Codex | Claude |
|---|---|---|
| Keying | ancestor-inherited blanket | exact absolute path |
| A brand-new directory | **trusted** if under a trusted ancestor | **untrusted** — never seen |
| Practical prompt frequency | almost never, for repo work | **on every new path** |

**A new git worktree is a new absolute path.** The superpowers convention puts worktrees at
`<project-root>/.worktrees/<name>`, which will not be in `projects`. So:

> **The SDD auto-spawn (N43(D)) spawning a successor into a freshly created worktree should be
> expected to raise Claude's trust dialog** — and `spawn-handoff-session.sh` would report `exit 0`,
> append its `outcome` record, and fire a "successor spawned" notification while the successor sits on
> a modal. That is superpowers BACKLOG **N56**'s hypothesised failure with a named mechanism and,
> now, a preflight.

The common-case mitigation already noted in N56 holds and is now explained: the successor's cwd is
`$WORKTREE_ROOT`, the parent's **already-accepted** worktree, so a same-worktree hop is safe. A
*fresh* worktree is the exposure.

---

## 2. Recommended hardening

### H1 — Preflight what is declarative, and refuse rather than hang *(highest value)*

Before any spawn or dispatch, resolve two facts from files:

1. **Trust.** Codex: walk the target cwd's ancestors against `[projects]`, nearest match wins, no
   match ⇒ untrusted. Claude: exact-path lookup of `hasTrustDialogAccepted` (pending the inheritance
   test above).
2. **Writability.** Codex only: is the bundle root inside
   `sandbox_workspace_write.writable_roots`? Today it contains `/Users/araymond/.claude-codex-handoff`
   (a-file), so the findings write is pre-approved — a **config dependency, not a guarantee**. This
   repo's `CLAUDE.md` already says *"If Codex reviews start stalling on write approvals, check that
   entry first."* Turn that troubleshooting note into a precondition. Note `approval_policy =
   "on-request"` (a-file).

Then route on the result:

| Preflight | Headless (`auto-cdx`) | Interactive (cmux transport) |
|---|---|---|
| trusted + writable | ✅ cheapest path | fine, but unnecessary |
| **untrusted** | ❌ **will hang to timeout** — refuse with guidance | ✅ **the correct choice** |
| bundle root not writable | ❌ stalls on write approval | ✅ operator can approve |

**This table is the concrete argument for the cmux mode's existence** that the bundle's blocker asks
for. It is demonstrable rather than asserted: run the same review into an untrusted path both ways and
show one hangs.

**Fail direction:** if the preflight itself cannot run (file missing, unparseable), do **not** silently
assume trusted. Report `unknown` and prefer the interactive transport — the mode that can survive a
prompt. Guessing "trusted" turns a visible refusal into an invisible hang.

### H2 — Positive liveness signals; never infer from screen appearance

Three states must be distinguishable, and today's design conflates the middle one with "slow":

| State | Signal to use |
|---|---|
| **started** | `cmux wait-for` token, signalled by the child after pickup runs *(a-run: cross-workspace proven; unsignalled `--timeout 3` exits **1** after a real 3.031 s)* |
| **finished** | Codex: `agent.hook.Stop` from `cmux events` *(a-run)*. Claude: findings-file/artifact polling — Claude emits no tool events |
| **blocked awaiting a human** | absence of new `agent.hook.PreToolUse` **and** no `Stop` for N seconds — a *positive* stall detection |

**Why not screen-scraping:** a blocked TUI looks completely normal. Verified live — driving `/model`
in a Claude session raised `Switch model? ❯ 1. Yes … 2. No`, which consumed input until answered while
the screen read as an ordinary session *(a-run)*. A `read-screen` pattern check would have called that
healthy.

**Codex-only caveat:** sessions launched via `claude-picker` emit **nothing** into `cmux events` — the
picker `exec`s an absolute `$VERSIONS_DIR/<version>` binary and never resolves `claude` through the
cmux wrapper shim *(a-run, plus picker source)*. Even wrapper-launched Claude emits only
`SessionStart`/`SessionEnd`. **Event-based detection is a Codex-reviewer capability, not a general
one.** Do not design a single code path that assumes it.

### H3 — Escalate, never auto-answer

On a detected prompt or stall: `cmux notify`, `cmux set-status <key> "needs approval"`, optionally
focus the tab — then **stop and wait**. Never send `y`, Enter, or any dismissal.

The operator's approval *is* the value the interactive transport adds over headless. Automating it
away deletes the reason the mode exists, and converts a safety gate into a rubber stamp. Write this
down where an implementer will see it, because it is the single most tempting "improvement" available.

*(Sidebar-write hazard, `a-run`: with the cmux env stripped, `cmux set-status` still returns `OK` and
exit 0 and writes to the **selected** workspace — silently mislabelling another session's sidebar. Gate
on `[ -n "$CMUX_WORKSPACE_ID" ]` **and** pass `--workspace` explicitly. Only a missing binary actually
fails, exit 127. ~55 ms per call.)*

### H4 — Preserve failure evidence

- Launch with `cmux send`, not `respawn-pane`: the latter destroys the surface when its command exits,
  deleting the error you need *(a-run)*.
- Leave the tab open on failure. Tear down only on success.
- Never treat `read-screen`'s `internal_error: Failed to read terminal text` as retryable — on a
  never-driven surface it is permanent *(a-run: still failing at T+6s)*, and it means **send first**.

### H5 — Make the degradation path a tested contract, not a comment

The bundle already warns cmux must not become a hard dependency. Strengthen it into assertions:

- `CMUX_WORKSPACE_ID` unset **or** `cmux ping` ≠ `PONG` ⇒ fall back to manual, print why, **exit 0**.
- `cmux` absent from `PATH` ⇒ same (exit 127 from the binary must not leak).
- A preflight that returns `unknown` ⇒ documented behavior, not incidental behavior.

The superpowers `spawn-handoff-session.sh` is the precedent worth copying: an explicit exit ladder
(0 spawned / 3 manual fallback / 1 refused precondition) where every rung is enumerable. Its lesson
learned the hard way — a guard whose input is malformed must **fail safe**, not fall through and
proceed.

### H6 — Cross-tool parity is a correctness property here

Any hardening lands in `src/claude-commands/X.md` **and** `src/codex-skills/X/SKILL.md`. Flag-set
parity is enforced by `tests/test_command_skill_parity.py`; **prose parity is not**. Since the two
tools have *opposite* trust semantics (§1), the natural failure is documenting the Codex rule in the
Codex skill, the Claude rule in the Claude command, and leaving each blind to the other — when the
whole point of this toolkit is that a bundle crosses between them. Document **both** rules in **both**
places.

---

## 3. Scenario table

| # | Scenario | Detect | Preflight? | Response |
|---|---|---|---|---|
| 1 | Codex trust prompt on a never-trusted path | screen pattern; stalled events | ✅ `[projects]` | interactive transport; escalate |
| 2 | Claude trust dialog on a **new worktree** | no `wait-for` signal | ✅ `hasTrustDialogAccepted` | pre-accept, or spawn into an accepted path, or escalate |
| 3 | Codex sandbox write approval (findings) | stall after review completes | ✅ `writable_roots` | escalate; fix config |
| 4 | Mid-run TUI confirmation dialog | stalled events + screen | ❌ | escalate, never answer |
| 5 | `codex-picker` drops to its interactive menu on a bad flag | no `wait-for` signal | partial — validate flags against source | refuse before spawn |
| 6 | Text typed but never submitted (wrapped composer) | `read-screen` shows text still in composer | ❌ | split send/`send-key`; verify between |
| 7 | Spawned but never started (N56) | `wait-for` timeout ⇒ exit 1 | ❌ | new exit rung; do **not** claim "nothing spawned" |
| 8 | Findings written, originator never notices | findings-file poll | ❌ | bounded poll + explicit timeout state |
| 9 | Status/notify write hits the wrong workspace | — | ✅ env gate | require `CMUX_WORKSPACE_ID` + explicit `--workspace` |

Rows 1–3 and 9 are preflightable **today**, from files, with no new cmux capability.

---

## 4. What to test

1. **Trust preflight unit tests**, both tools, over fixture config files: Codex nearest-ancestor match
   wins and an explicit `untrusted` beats a trusted grandparent; Claude exact-path lookup with a
   missing key ⇒ untrusted.
2. **Claude inheritance test** *(closes the one `inferred` step in §1)*: launch into a never-seen
   subdirectory of an accepted repo and record whether the dialog fires.
3. **Provoked-prompt run**, deterministic now: launch into a path with no trusted ancestor. Assert the
   operator can answer it **and** that headless `auto-cdx` into the same path hangs — that contrast is
   the mode's justification.
4. **Degradation test**: outside cmux, manual fallback with a clear message and exit 0.
5. **Ordering test**: the implementation sends before it polls; `read-screen`'s `internal_error` on a
   cold surface is not treated as retryable.
6. **Stall detection**: with a stubbed event stream, assert that "no `PreToolUse`, no `Stop` for N
   seconds" is reported as *blocked*, distinctly from *timed out*.
