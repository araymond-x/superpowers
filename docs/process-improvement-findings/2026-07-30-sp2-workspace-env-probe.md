# SP2 — workspace `--env` / `--env-file` probe + disposition

**Written 2026-07-30** by the `cmux-spawn-v2` SDD run, Module 1 Task 1.
**Binary under test:** `cmux 0.64.20 (100) [14e3400b9]` — re-pinned live at execution time with
`cmux --version`; identical to the version the plan's Source Contracts pin.
**Closes/keeps the premise of:** BACKLOG **N67** (and sharpens **N70**, **N72**).

Confidence labels follow this directory's existing convention (`2026-07-29-cmux-mode-option-surface.md`):
**a-run** = exercised against the installed binary; **a-help** = read from `--help`; **a-file** = read
from a document; **inferred** = reasoned, not observed. N67 self-graded its `--env` finding as
**a-help — "not exercised — probe before building."** Everything below marked **a-run** is this
document's contribution: it moves that claim to exercised.

---

## The question

Carried verbatim from the plan, with its scoping qualifier intact — the qualifier is load-bearing:

> Can `--env` replace the inline-env command-string prefix on the FALLBACK path
> **(scalars only; the append-prompt is content and stays on the rematerialization path)**?

Dropping "scalars only" turns this into a different question — "can `--env` carry *everything*?" —
whose answer is no, and which would wrongly close N67 as not-viable.

## Bottom line

**Disposition (a) — viable, for the fallback path, for scalars, with a recorded caveat that argues
against adopting it in this sprint.**

1. **The flags work.** `--env` / `--env-file` are accepted on **both** spellings, and they do not
   merely *record* values — they **export** them into every shell spawned in the workspace. Both
   halves (configured view and inherited-process view) were verified independently. **a-run**
2. **All four documented `--env-file` semantics hold**: `#` comments ignored, blank lines ignored,
   leading `export ` stripped, and `--env` overrides a same-key value from the file. **a-run**
3. **But the primary path has no env channel at all.** `new-surface` has no `--env`, an existing
   workspace's env **cannot be mutated** by any CLI verb or socket method, and the one per-surface
   env channel that does exist (`--layout` `surfaces[].env`) is **workspace-creation-time only**.
   **a-run**
4. **Therefore `--env` cannot subtract the quoting machinery**, which was N67's actual motivation.
   This sprint's *primary* topology is a surface in the caller's existing workspace (Decision 2),
   and that path can only receive state through the composed command string. Adopting `--env` on the
   fallback alone would **fork the shared wrapper's env channel** — the exact thing Decision 2's
   "ONE shared launch-and-handshake wrapper (same inline env…)" exists to prevent.

**N67's premise is therefore PARTIALLY closed, not fully closed.** The flags are real and work as
documented — that half of N67 is confirmed and upgraded to a-run. The *benefit* N67 claimed ("the
rare finding that **subtracts** shipped code") does **not** materialize, because the machinery it
would subtract is still required by the topology this sprint ships as primary. The recommendation is
**do not adopt in this sprint**; revisit only if the surface topology is ever abandoned.

---

## Step 1 — three help surfaces

The plan named two (`workspace create`, `new-surface`). A third (`new-workspace`) was added because
`CLAUDE.md` documents the flags on that spelling. Probing all three is what surfaced finding H1.

### H1. `cmux workspace create --help` never shows the flags — it prints the *noun* help

`cmux workspace create --help` (exit 0) does **not** print create-specific help. It prints the
`cmux workspace` noun help, verbatim:

```
cmux workspace

Usage: cmux workspace <subcommand> [flags]

Canonical noun for workspace operations. Legacy verbs
(new-workspace, list-workspaces, close-workspace,
rename-workspace, select-workspace) keep working and print a
one-time deprecation hint pointing here.

Subcommands:
  list                    List workspaces in a window
  create [flags]          Create a workspace (same flags as new-workspace)
  env [workspace] [--mask]
                          Print a workspace's configured environment
                          variables (--mask redacts the values)
  close <workspace>       Close a workspace
  rename <workspace> --title <new>
  select <workspace>      Make a workspace active
  status [set <lane|auto>]
                          Show or pin the workspace todo status
  ...
  group <subcommand>      Workspace group operations (see cmux workspace-group --help)
```

This is **uniform, not create-specific**: `cmux workspace env --help` and `cmux workspace close --help`
print the identical noun help (both exit 0). There is no per-subcommand help under the `workspace`
noun. **a-run**

**Consequence, and it is an irony worth recording:** the **canonical** spelling's `--help` *never*
mentions `--env`. The only `--help` that documents these flags belongs to the **deprecated legacy
verb**. N70 wants the spawn script migrated to `cmux workspace create`; after that migration, nothing
in the canonical command's own help will tell a reader the env flags exist.

This help-dispatch behavior is **not** listed in the upstream contract's own "Current Help Caveats"
section, which enumerates only `version`, `claude-teams`, `codex-teams`, and `remote-daemon-status`.
It is a fifth instance of the same class.

### H2. `cmux new-workspace --help` — the flags, verbatim

```
Usage: cmux new-workspace [--name <title>] [--description <text>] [--cwd <path>] [--command <text>] [--env KEY=VALUE]... [--env-file <path>]... [--layout <json>] [--window <id|ref|index>] [--focus <true|false>] [--group <id|ref>] [--group-placement afterCurrent|top|end] [--group-reference <workspace>]

Flags:
  --name <title>       Set a custom name for the new workspace
  --description <text> Set a custom description for the new workspace
  --cwd <path>         Set the working directory for the new workspace
  --command <text>     Send text+Enter to the new workspace after creation
  --env KEY=VALUE      Set a workspace environment variable. Repeatable.
                       Reserved CMUX_* variables cannot be overridden.
  --env-file <path>    Load KEY=VALUE lines from a file. Repeatable.
  --layout <json>      Create workspace with a predefined split layout.
                       Layout surfaces define their own commands.
  --window <id|ref|index> Target window (default: caller's window)
  --focus <true|false> Focus the new workspace (default: false)
  --group <id|ref>     Add the new workspace to a workspace group
  --group-placement afterCurrent|top|end Placement within --group (default: top)
  --group-reference <workspace> Reference workspace for afterCurrent placement
```

Note `--focus` already defaults to `false` here — the fork convention of passing `--focus false`
explicitly is belt-and-braces, not a correction.

### H3. `cmux new-surface --help` — no env flag

```
Usage: cmux new-surface [flags]

Flags:
  --type <terminal|browser|agent-session>   Surface type (default: terminal)
  --pane <id|ref|index>       Target pane
  --placement <workspace|dock>  Target container (default: workspace).
                               dock adds the surface to the right-sidebar Dock
                               (terminal and browser only).
  --workspace <id|ref|index>  Target workspace (default: $CMUX_WORKSPACE_ID)
  --window <id|ref|index>     Window context for workspace/pane refs and indexes
  --url <url>                 URL for browser surfaces
  --provider <codex|claude|opencode>
                               Provider for agent-session surfaces (default: codex)
  --renderer <react|solid>    Renderer for agent-session surfaces (default: react)
  --working-directory <path>   Working directory for terminal and agent surfaces
  --focus <true|false>        Focus the new surface (default: false)
```

`grep -i env` over **both** streams of `cmux new-surface --help`: no match. **a-help**

**This is deliberately not treated as proof of absence.** "I ran `--help`, saw nothing, confirmed
none" is the N56 pattern this repo has already filed a false-premise row for. Two further independent
checks were run — see §"The primary path".

### H4. The alias question (N70), resolved

Three sources agree that `create` and `new-workspace` take the **same** flags:

| Source | Evidence | Confidence |
|---|---|---|
| Installed binary, noun help | `create [flags]   Create a workspace (same flags as new-workspace)` | a-help |
| Upstream `docs/cli-contract.md` | *"`cmux new-workspace --env KEY=VALUE …` (and the same flags on `cmux workspace create`)"* | a-file |
| Installed binary, **exercised** | `cmux workspace create … --env … --env-file …` → exit 0, `OK workspace:38` | **a-run** |

Plus a fourth, discovered incidentally and stronger than any help text — see D2 below: `workspace
create`'s **error message** enumerates its known flags, and that enumeration includes
`--env KEY=VALUE, --env-file <path>`.

`cmux list-workspaces` also emitted the deprecation hint live during cleanup, confirming N70's
premise verbatim:

```
cmux: 'list-workspaces' is now an alias for 'cmux workspace list'. The legacy form keeps working indefinitely; set CMUX_QUIET=1 to silence this notice.
```

---

## Step 2 — exercising the fallback path

All work ran in throwaway workspaces named `sp2-*`, all `--focus false`, all deleted (see §Cleanup).
**Stdout and stderr were captured to separate files and every result gated on the exit code**, never
on a parsed field — see §Deviations.

### The env-file fixture

Deliberately built to test all four documented semantics in one shot (the plan's `/dev/null` would
have proved nothing, and N67 explicitly asks that `--env-file` be probed):

```
# sp2 probe env-file — comment line, must be ignored
                                    ← blank line
SP2_FILE_PLAIN=file_plain
export SP2_FILE_EXPORT=file_export
SP2_PROBE=from_file_should_lose      ← same key --env also sets, to test precedence
```

### Create — the canonical spelling, exercised

```
$ cmux workspace create --name "sp2-env" --cwd "$HOME" --focus false \
    --env SP2_PROBE=alpha --env SP2_SECOND=beta --env-file <fixture>
exit=0
stdout: OK workspace:38
stderr: (empty)
```

### Half 1 — the configured view

```
$ cmux workspace env workspace:38
exit=0
SP2_FILE_EXPORT=file_export
SP2_FILE_PLAIN=file_plain
SP2_PROBE=alpha
SP2_SECOND=beta
```

All four documented `--env-file` semantics confirmed **a-run** in this single output:

| Documented semantic | Evidence |
|---|---|
| `#` comment lines ignored | no comment key present |
| blank lines ignored | no empty key present |
| leading `export ` stripped | key is `SP2_FILE_EXPORT`, not `export SP2_FILE_EXPORT` |
| `--env` overrides a file value | `SP2_PROBE=alpha`, not `from_file_should_lose` |

`--mask` works (`SP2_PROBE=••••`; longer values keep a 2-char prefix, e.g. `SP2_FILE_PLAIN=fi••••`).

### Half 2 — the inherited-process view

This half is the one that decides *sufficiency*. A flag that records a value without exporting it
would look successful from the configured view alone.

Driven in the workspace's surface (never read cold — a never-driven surface returns `internal_error`,
per the Task 0 fixture):

```
$ cmux send --surface surface:99 "printf 'SP2_WS_MARK=%s|%s|%s|%s\n' \"$SP2_PROBE\" …"
$ cmux read-screen --surface surface:99 --scrollback
SP2_WS_MARK=alpha|beta|file_plain|file_export
```

**All four values reached the process environment.** `--env` and `--env-file` genuinely export.
**a-run**

A surface created **later** in the same workspace also inherited the workspace env
(`SP2_PROBE=alpha` read back from `surface:103`), confirming the contract's *"apply to … every pane,
surface, and split created later in that workspace"*. **a-run**

### Reserved `CMUX_*` — the help text is misleading, the contract is right

`--help` says *"Reserved CMUX_* variables cannot be overridden"*, which reads as **rejected at
create**. What actually happens is different, and it is a trap:

```
$ cmux workspace create --name "sp2-reserved" … \
    --env CMUX_WORKSPACE_ID=BOGUS_WS --env TERM=bogusterm --env SP2_OK=yes
exit=0   stdout: OK workspace:39            ← ACCEPTED, no warning

$ cmux workspace env workspace:39           ← the CONFIGURED view happily reports the bogus values
CMUX_WORKSPACE_ID=BOGUS_WS
SP2_OK=yes
TERM=bogusterm

$ (read back inside the surface)            ← the INHERITED view shows the real ones
SP2_RES=46F6D0B0-7444-41BA-96B5-ADA8F85C21F8|xterm-256color|yes
```

So protected keys are **silently accepted and stored**, and only overridden **at shell spawn** —
exactly as the upstream contract states (*"protected at spawn time and silently win"*), and
**not** as `--help` implies. Terminal identity vars (`TERM`) are protected too. **a-run**

**Operational consequence:** `cmux workspace env` **misreports the effective environment** for any
protected key. Nothing may treat the configured view as ground truth for `CMUX_*` or `TERM`. This is
the concrete vindication of requiring both halves.

---

## The primary path — is there a surface-scoped env equivalent?

This sprint's primary topology is a **surface in the caller's existing workspace**; `workspace create`
is the demoted fallback. So this is the more important half of the question.

**Answer: there is no env channel that can reach a surface added to an already-existing workspace.**
Established on three independent axes, because "not in `--help`" is a documented-insufficient basis
in this repo.

### Axis 1 — the upstream contract's flag table

`docs/cli-contract.md` (URL obtained at execution time from `cmux docs api`, not hardcoded; note it
resolves to `main`, not necessarily the installed version) documents `--env`/`--env-file` **only** for
`new-workspace` / `workspace create`. Its `new-surface` row reads, in full:

```
| `new-surface` | Create a surface inside a pane. |
```

This is the source that documented `--env` when `--help` did not, so its silence here carries weight
it would not otherwise. **a-file**

### Axis 2 — the live rejection probe, and its negative control

The probe was run as directed — and it came back **accepted**, which looked at first like the
discovery of an undocumented flag:

```
$ cmux new-surface --workspace workspace:38 --type terminal … --env SP2_PROBE=alpha
exit=0   stdout: OK surface:100 pane:38 workspace:38          ← accepted!
$ cmux new-surface --workspace workspace:38 … --env-file <fixture>
exit=0   stdout: OK surface:101 pane:38 workspace:38          ← also accepted
```

**A negative control settles it.** `new-surface` accepts a flag that certainly does not exist:

```
$ cmux new-surface --workspace workspace:38 … --sp2-not-a-real-flag zzz
exit=0   stdout: OK surface:102 pane:38 workspace:38          ← garbage flag ALSO accepted
```

`new-surface` **silently ignores unknown flags**. Its acceptance of `--env` is therefore worth
nothing. And the read-back proves the value never arrives — a surface created with
`--env SP2_SURF=gamma`, where `SP2_SURF` is a name the workspace env does **not** carry:

```
SP2_SURF_MARK=|alpha
                ↑ SP2_SURF is EMPTY (flag ignored); SP2_PROBE=alpha arrives from the WORKSPACE env
```

**a-run.** Had the control been skipped, this task would have filed a third false-premise row
claiming an undocumented `new-surface --env`.

The contrast is sharp and is itself a finding — `workspace create` **strictly validates**:

```
$ cmux workspace create --name "sp2-ctl" … --sp2-not-a-real-flag zzz
exit=1
Error: workspace create: unknown flag '--sp2-not-a-real-flag'. Known flags: --name <title>,
  --description <text>, --command <text>, --cwd <path>, --env KEY=VALUE, --env-file <path>,
  --layout <json>, --window <id|ref|index>, --focus <true|false>, --group <id|ref>,
  --group-placement <afterCurrent|top|end>, --group-reference <workspace>
```

**Two commands on the same binary have opposite unknown-flag policies.** Anything that infers
capability from an exit code must know which it is talking to.

### Axis 3 — can an existing workspace's env be mutated?

If it could, the primary path would be served by mutate-then-add-surface. It cannot:

| Probe | Exit | Result |
|---|---|---|
| `cmux workspace env set workspace:38 SP2_MUT=beta` | 1 | `Error: Invalid workspace handle: set (expected UUID, ref like workspace:1, or index)` — `set` parsed as a handle; no such subcommand |
| `cmux workspace env workspace:38 SP2_MUT=beta` | **0** | **Silently ignored the extra arg and printed the read view** — looks like success, mutates nothing |
| `cmux workspace env workspace:38 --env SP2_MUT=beta` | 1 | `Error: workspace env: unknown flag '--env'. Known flags: --workspace <id\|ref\|index>, --window <id\|ref\|index>, --mask` |
| `cmux set-environment SP2_MUT=beta` | 2 | `Error: Unknown command 'set-environment'.` |

And the socket surface agrees — `cmux capabilities` lists exactly one env-related method across the
whole RPC set:

```
$ cmux capabilities | grep -o -i '"[a-zA-Z_.]*env[a-zA-Z_.]*"' | sort -u
"workspace.env"
```

`workspace.env` is the read. There is no `workspace.set_env` / `workspace.update_env`, and no
env-related method among the 26 `surface.*` methods. **a-run**

> **Honest limit of axis 3.** `cmux capabilities` returns a flat list of method *names* with no
> parameter schemas. It can rule out a missing *method*; it cannot rule out an undocumented *param*
> on `workspace.create` or `surface.create`. The socket was not driven directly. What is established
> is that **no CLI path** reaches such a param, which is what the spawn script needs.

### The one per-surface env channel that does exist — and why it does not help

The contract states an *"explicit per-surface environment (a layout `surfaces[].env`, SSH startup
env) overrides the workspace value for that surface."* This was exercised rather than assumed:

```
$ cmux workspace create --name "sp2-layout" … --layout '{"direction":"horizontal","split":0.5,
    "children":[{"pane":{"surfaces":[{"type":"terminal",
      "command":"printf SP2_LAYOUT=%s\\n \"$SP2_LAYOUT\"","env":{"SP2_LAYOUT":"delta"}}]}},
      {"pane":{"surfaces":[{"type":"terminal"}]}}]}'
exit=0   stdout: OK workspace:40

$ cmux read-screen --surface surface:105 --scrollback
SP2_LAYOUT=delta            ← per-surface env WORKS, and the per-surface command ran

$ cmux workspace env workspace:40
No environment variables    ← per-surface env does NOT appear in the configured view
```

**A per-surface env channel is real. a-run.** It is also **workspace-creation-time only** — `--layout`
is a flag on workspace creation, and there is no way to add a layout-defined surface to an existing
workspace. So it does **not** serve the primary path.

Two side findings worth carrying forward, neither of which changes this disposition:

- `--layout` delivers per-surface **`command` + `env` atomically at create**, which further dissolves
  N57's "`new-surface` has no `--command`" (N67 already flagged the `--layout` half). A *fallback*
  spawn could in principle be one call instead of create → new-surface → send.
- `cmux workspace env` shows **neither** protected-key effective values **nor** per-surface layout
  env. It reports the workspace-level configured set and nothing else.

---

## Where a document and the installed binary disagreed

| # | Claim | Source | Binary | Verdict |
|---|---|---|---|---|
| D1 | `cmux workspace env … [--json]` | contract, `a-file` | noun help lists only `[workspace] [--mask]`; **`--json` works** (exit 0, well-formed JSON with `count`/`env`/`window_ref`/`workspace_ref`) | **Contract right, help incomplete** |
| D2 | `workspace env` known flags are `--workspace, --window, --mask` | binary's own **error message** | but `--json` demonstrably works | **The binary's own error-message flag enumeration is incomplete** |
| D3 | "Reserved `CMUX_*` variables cannot be overridden" | `--help`, `a-help` | accepted + stored; overridden only at spawn | **Contract right (`"protected at spawn time"`), `--help` misleading** |
| D4 | `--help` caveats are enumerated in the contract's "Current Help Caveats" | contract, `a-file` | `workspace <sub> --help` printing noun help is absent from that list | **Contract incomplete** |

D2 deserves emphasis: this is a **fourth** distinct instance of cmux's surface being incompletely
enumerated by its own machine-readable output, and a new *kind*. N72 records three (a command absent
from the list, flags absent from a summary line, a whole entrypoint absent). This adds: **an error
message that purports to enumerate a command's known flags, and omits a working one.** Any
capability-drift guard keying on help text or error text inherits this hole. Recommend N72 absorb D2.

---

## Disposition

**(a) viable — fallback path, scalars only — with a recommendation NOT to adopt it in this sprint.**

**Why viable.** Every element of the scalars-only substitution is confirmed a-run: the flags exist on
the canonical spelling, are accepted, are stored, and are **exported into the process environment** of
every surface in the workspace. The scalars N67 names — hop number, `$SPAWN_ID`, `SUPERPOWERS_CMUX_*`
overrides — are ordinary non-reserved `KEY=VALUE` pairs and are exactly what this channel carries.
The scoping qualifier is honored: the append-prompt is content and stays on the rematerialization
path (`--env-file` reads `KEY=VALUE` lines, i.e. it is a scalar loader, so it does not change that).

**Why not to adopt it here.** N67's value proposition was subtraction — retire the base64 argv codec,
the `shlex.quote` re-quoting, the `printf`-not-`echo` workaround. That subtraction **does not
happen**, because:

- the sprint's **primary** topology is `new-surface` into the caller's existing workspace, which has
  **no env channel on any axis** (§"The primary path"); it can only be reached by the composed
  command string, so the quoting machinery must stay;
- Decision 2 pins **both** topologies to ONE shared launch-and-handshake wrapper with the **same**
  inline env. Adopting `--env` on the fallback alone would fork that wrapper's env channel — adding a
  second mechanism while removing none, which is the opposite of N67's intent.

So the honest disposition is that the **flag works and the idea is sound**, while the **benefit is
blocked by topology, not by the flag**. N67's premise is confirmed-but-not-actionable rather than
refuted. It should stay open as a watch item conditioned on the topology, not be closed as
not-viable and not be scheduled as a subtraction.

**The condition under which this flips to "adopt":** if the surface topology is ever abandoned and
`workspace create` becomes the only spawn path, `--env` becomes strictly better than the inline
prefix and the subtraction N67 imagined becomes available in full.

---

## What could not be established

Stated plainly, because a wrong disposition here becomes a third false-premise row.

1. **Whether `workspace.create` / `surface.create` accept an undocumented env param over the raw
   socket.** `cmux capabilities` gives method names only, no schemas, and the socket was not driven
   directly. This bounds axis 3 to "no CLI path exists" — sufficient for the spawn script, which is a
   CLI consumer, but not a claim about the RPC layer.
2. **Whether `--layout` can express the sprint's full fallback spawn** (correct cwd, the composed
   command, and the handshake) in one call. Only a minimal two-pane layout with one `command` + `env`
   was exercised. The capability is proven; its fitness for the spawn is not, and nothing here should
   be read as a green light to rewrite the fallback around `--layout`.
3. **Dotfile-precedence exposure.** The contract states an `export` in `~/.zshrc` / `~/.zprofile` for
   the same key **wins** over workspace env for the interactive shell, because init files run after
   the variable is seeded. Not exercised — the probe keys are `SP2_*`, which no dotfile touches. It is
   harmless for `SUPERPOWERS_*` names for the same reason, but any future adoption should not assume
   workspace env is authoritative for a key a dotfile might export.
4. **Behavior on a cmux version other than `0.64.20 (100) [14e3400b9]`.** Every a-run claim is pinned
   to that build. The contract URL resolves to `main` and may already describe a different one.

## Cleanup

Three `sp2-*` workspaces were created (`sp2-env` = `workspace:38`, `sp2-reserved` = `workspace:39`,
`sp2-layout` = `workspace:40`); `sp2-ctl` was never created (its create was the exit-1 negative
control). All three were closed (`cmux workspace close`, each exit 0), and the full list re-read:

```
$ cmux list-workspaces
* workspace:2  Superpowers  [selected]
  workspace:28  SDD resume: 2026-07-29-cmux-transport
  workspace:11  Telemetry Exp
  workspace:20  Handoff Skill
  workspace:22  IBKR Gateway
```

Zero residual `sp2-*` entries, satisfying Module 1's acceptance criterion.

## Deviations from the plan's literal text

`deviations.md` is outside this task's write scope, so these are recorded here and in the Task 1
implementer report — the only path by which they reach the deviations register.

| # | Departure | Origin | Why |
|---|---|---|---|
| 1 | Probed **three** help surfaces, not the plan's two | prompt-directed | `CLAUDE.md` documents the flags on `new-workspace`; the third spelling produced finding H1 |
| 2 | Captured stdout/stderr **separately** and gated on **exit code**, not the plan's `2>&1` + `awk '{print $2}'` | prompt-directed | Task 0's precedent; merged streams would feed error text into `cmux workspace env` as a garbage ref |
| 3 | Used a **real** `--env-file` fixture instead of the plan's `/dev/null` | self-initiated | `/dev/null` proves nothing; N67 explicitly asks that `--env-file` be probed |
| 4 | Added workspace-env **mutation-verb** probes (4 spellings + `cmux capabilities`) | self-initiated | The primary-path answer rested on two documents and zero probes — the N56/N57 shape |
| 5 | Added an **unknown-flag negative control** on both commands | self-initiated | `new-surface --env` was *accepted*; without the control this would have been filed as an undocumented flag |
| 6 | Added a **reserved-`CMUX_*`** probe | self-initiated | a-help behavior claim; this repo has a documented case of one being wrong (`pipe-pane` "stream") |
| 7 | Exercised **`--layout` `surfaces[].env`** | self-initiated | The contract asserts a per-surface env channel; the primary-path answer is only honest if it is tested |

## Proposed BACKLOG row

Filed as **N76** (next free id, confirmed by enumerating actual ids at execution time).
