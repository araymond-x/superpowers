# SP2 — workspace `--env` / `--env-file` probe + disposition

**Written 2026-07-30** by the `cmux-spawn-v2` SDD run, Module 1 Task 1.
**Binary under test:** `cmux 0.64.20 (100) [14e3400b9]` — re-pinned live at execution time with
`cmux --version`; identical to the version the plan's Source Contracts pin.
**Closes/keeps the premise of:** BACKLOG **N67** (and sharpens **N70**, **N72**).
**Revised 2026-07-30** after the Task 1 adversarial quality review returned CHANGES_REQUESTED. Three
substantive changes: the **axis-3 limit was wrong and is withdrawn** (`cmux rpc` is a CLI path to
arbitrary RPC params, so "no CLI path exists" was unearned — see the corrected limit in §Axis 3, and
the new §Axis 4 that carries the conclusion instead); the **keystone read-back was re-captured live**
with a complete transcript (§Re-capture); and the **flip condition is now written against shipped
code** rather than against an unshipped topology decision. The headline disposition is unchanged —
what changed is which evidence supports it and how far it reaches.

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
   halves (configured view and inherited-process view) were verified independently, and both
   spellings were exercised: `cmux workspace create` in the first probe session, `cmux new-workspace`
   in the 2026-07-30 re-capture (§"Re-capture"). **a-run on both spellings**
2. **All four documented `--env-file` semantics hold**: `#` comments ignored, blank lines ignored,
   leading `export ` stripped, and `--env` overrides a same-key value from the file. **a-run**
3. **But the primary path has no env channel any *documented CLI verb* reaches.** `new-surface` has
   no `--env` (proved by a read-back, not by its absence from `--help`), an existing workspace's env
   **cannot be mutated** — no CLI verb does it and `cmux capabilities` exposes no env-setting
   *method* — and the per-surface env channel that does exist (`--layout` `surfaces[].env`) is
   **workspace-creation-time only**. (The contract names a second per-surface channel, SSH startup
   env; `cmux ssh` creates a workspace of its own, so it is likewise no route into an existing one —
   see §"Per-surface env channels".) **a-run.** Read the scope qualifier literally: a sweep of the
   documented top-level verbs (§Axis 4 — 127 unique names from the `Commands:` block, plus the
   alternation siblings that extraction collapses, probed separately) is what establishes this, and
   the sweep's own scope limits state what it does **not** reach. It does **not** exclude an
   undocumented param reached through `cmux rpc` — see the corrected limit in §Axis 3, which also
   gives the argument for why the disposition is unaffected.
4. **Therefore `--env` cannot subtract the quoting machinery**, which was N67's actual motivation.
   This sprint's *primary* topology is a surface in the caller's existing workspace (Decision 2),
   and that path can only receive state through the composed command string. Adopting `--env` on the
   fallback alone would **fork the shared wrapper's env channel** — the exact thing Decision 2's
   "ONE shared launch-and-handshake wrapper (same inline env…)" exists to prevent.

**N67's premise is therefore PARTIALLY closed, not fully closed.** The flags are real and work as
documented — that half of N67 is confirmed and upgraded to a-run. The *benefit* N67 claimed ("the
rare finding that **subtracts** shipped code") does **not** materialize, because the machinery it
would subtract is still required by the topology this sprint ships as primary. The recommendation is
**do not adopt in this sprint**; revisit whenever the shipped `spawn-handoff-session.sh` reaches
successor state only through workspace creation — which is true of the code today and stays true if
this sprint never lands. See §Disposition for both branches spelled out.

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
  ...                     [ELIDED: reconnect, disconnect, loading]
  group <subcommand>      Workspace group operations (see cmux workspace-group --help)
```

**This block is abridged, not verbatim** — the `...` stands for the `reconnect`, `disconnect` and
`loading` subcommand rows, and the real output continues past the block with a trailing paragraph
(`env/reconnect/disconnect accept a positional handle or --workspace …`) and a six-line `Examples:`
section. Neither omission touches the finding: the flags are absent from every line, elided or not.
H2 and H3 below are **complete**, byte-for-byte.

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

Complete stdout (exit 0, empty stderr), all 29 lines:

```
cmux new-workspace

Usage: cmux new-workspace [--name <title>] [--description <text>] [--cwd <path>] [--command <text>] [--env KEY=VALUE]... [--env-file <path>]... [--layout <json>] [--window <id|ref|index>] [--focus <true|false>] [--group <id|ref>] [--group-placement afterCurrent|top|end] [--group-reference <workspace>]

Create a new workspace in the caller's window.

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

Example:
  cmux new-workspace
  cmux new-workspace --name "Build Server"
  cmux new-workspace --name "Launch" --description "Ship checklist"
  cmux new-workspace --cwd ~/projects/myapp
  cmux new-workspace --cwd . --command "npm test"
  cmux new-workspace --name "Dev" --layout '{"direction":"horizontal","split":0.5,"children":[{"pane":{"surfaces":[{"type":"terminal","command":"vim"}]}},{"pane":{"surfaces":[{"type":"terminal","command":"npm run start"}]}}]}'
```

Note `--focus` already defaults to `false` here — the fork convention of passing `--focus false`
explicitly is belt-and-braces, not a correction.

### H3. `cmux new-surface --help` — no env flag

Complete stdout (exit 0, empty stderr), all 26 lines:

```
cmux new-surface

Usage: cmux new-surface [flags]

Create a new surface (tab) in a pane.

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

Example:
  cmux new-surface
  cmux new-surface --type browser --pane pane:1 --url https://example.com
  cmux new-surface --type agent-session --provider claude --renderer solid --focus true
  cmux new-surface --type browser --placement dock --url https://example.com
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

The fence below is the **literal file, copyable as-is** — line 2 is genuinely blank, and there are no
annotations inside it:

```
# sp2 probe env-file — comment line, must be ignored

SP2_FILE_PLAIN=file_plain
export SP2_FILE_EXPORT=file_export
SP2_PROBE=from_file_should_lose
```

Line by line: (1) a `#` comment, which must be ignored; (2) a blank line, which must be ignored;
(3) a plain `KEY=VALUE`; (4) a `KEY=VALUE` carrying a leading `export `, which must be stripped;
(5) a key that `--env` **also** sets on the command line, so the file value must lose.

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
per the Task 0 fixture). The first session recorded the **result** —
`SP2_WS_MARK=alpha|beta|file_plain|file_export` — but not the exact command bytes, and its
reconstructed rendering was wrong in a way that matters (a `"$SP2_PROBE"` inside local double quotes
expands in the *caller's* shell, not the surface's, and would have produced an empty field). Rather
than leave a rendering that could not have produced the recorded output, the whole read-back was
**re-run on 2026-07-30 with exact bytes** — see §"Re-capture", whose `surface:107` transcript shows
all four values arriving and shows the `$`-variables reaching the remote shell unexpanded.

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
exit=0   stdout: OK workspace:39

$ cmux workspace env workspace:39
CMUX_WORKSPACE_ID=BOGUS_WS
SP2_OK=yes
TERM=bogusterm

$ (read back inside the surface)
SP2_RES=46F6D0B0-7444-41BA-96B5-ADA8F85C21F8|xterm-256color|yes
```

Reading down: the create was **accepted with no warning**; the **configured** view happily reports
the bogus values back; the **inherited** view inside the surface shows the real ones.

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
Established on four axes, because "not in `--help`" is a documented-insufficient basis in this repo.
Axis 4 was added on 2026-07-30 in response to the Task 1 quality review, which found the original
axis-3 limit overstated; **read the limit at the end of axis 3 before quoting this answer.**

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
exit=0   stdout: OK surface:100 pane:38 workspace:38
$ cmux new-surface --workspace workspace:38 … --env-file <fixture>
exit=0   stdout: OK surface:101 pane:38 workspace:38
```

Both **accepted**, exit 0, no warning on either stream.

**A negative control settles it.** `new-surface` accepts a flag that certainly does not exist:

```
$ cmux new-surface --workspace workspace:38 … --sp2-not-a-real-flag zzz
exit=0   stdout: OK surface:102 pane:38 workspace:38
```

The **garbage flag is accepted too** — so `new-surface` **silently ignores unknown flags**, and its
acceptance of `--env` is worth nothing.

The read-back is what proves the value never arrives: a surface created with `--env SP2_SURF=gamma`,
where `SP2_SURF` is a name the workspace env does **not** carry, reports `SP2_SURF_MARK=|alpha` —
`SP2_SURF` empty, and `SP2_PROBE=alpha` still arriving from the *workspace* env as an in-band
positive control. The first session recorded that value without a transcript; **§"Re-capture" below
re-runs it end to end with surface refs, exit codes and both streams**. That re-capture also records
that `SP2_SURF` never appears in the configured view (**a-run**) — which rules out `new-surface
--env` being a covert *workspace*-env setter, but **cannot** adjudicate a surface-scoped
implementation either way, because the configured view reports no surface-scoped env at all. See
§Step C, where that limit is spelled out. The load-bearing datum is the read-back. **a-run**

Had the control been skipped, this task would have filed a third false-premise row claiming an
undocumented `new-surface --env`.

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

> **Honest limit of axis 3 — corrected 2026-07-30.**
>
> This section originally concluded that *"no **CLI path** reaches such a param, which is what the
> spawn script needs, since it is a CLI consumer."* **That inference was invalid and is withdrawn.**
> It requires "CLI" and "socket" to be disjoint layers, and on this binary they are not:
>
> ```
> $ cmux rpc --help
> exit=0
> cmux rpc
>
> Usage: cmux rpc <method> [json-params]
>
> Call a raw v2 method with an optional JSON object for params.
> Example: cmux rpc surface.report_tty '{"workspace_id":"...","surface_id":"...","tty_name":"ttys001"}'
> ```
>
> `cmux rpc` is a first-class top-level verb (it is in `cmux --help`'s Commands block) that calls
> **any** v2 method with **arbitrary** JSON params. So `cmux rpc surface.create '{…,"env":…}'` would
> be exactly a CLI path to an undocumented param on the method named as the residual exposure. It was
> **not** probed. **a-run** that the verb exists and returns a well-formed payload (this says nothing
> about whether the param below was honored — see immediately after):
>
> ```
> $ cmux rpc workspace.env '{"workspace":"workspace:2"}'
> exit=0
> { "count": 0, "env": {}, "window_id": "836F9638-…", "window_ref": "window:1",
>   "workspace_id": "5BC6A8A3-…", "workspace_ref": "workspace:2" }
> ```
>
> **That transcript is itself an instance of the silent-ignore trap, not a contrast to it.** The
> `workspace` key passed above is **not a param name this method honors**, so the matching
> `workspace_ref` in the payload is a coincidence of whatever that session's no-param default happened
> to be — not evidence the param routed. Measured read-only against the same pinned binary: `{}`,
> `{"workspace":"workspace:2"}`, `{"workspace":"workspace:9999"}` and
> `{"workspace":"totally-bogus-not-a-ref"}` all return the identical payload, while
> `{"workspace_id":"<uuid>"}` **is** honored and the camelCase `{"workspaceId":"<uuid>"}` is not. The
> no-param default was observed taking two different values on two calls; no mechanism for it is
> asserted here. **Measured by the round-2 adversarial re-review (2026-07-30, same pinned binary) —
> reviewer-sourced, not this document's own a-run.**
>
> So the section's *first* invocation already demonstrates silent-ignore; the bogus-param call below
> is a second, independent demonstration rather than the only one. And this does **not** resurrect the
> withdrawn bound: `{"workspace_id":"<uuid>"}` being honored proves `cmux rpc` routes
> correctly-**named** params to the method, so `cmux rpc surface.create '{…,"env":…}'` remains a live,
> unprobed CLI path.
>
> **What is actually established** is narrower and needs both halves stated separately:
>
> - **No *documented* CLI verb reaches a surface-scoped env param.** This is what axis 4's sweep
>   establishes, and it is the leg that genuinely carries the conclusion.
> - **`cmux capabilities` cannot settle the param question at all.** It returns method *names* with
>   no parameter schemas, so it is simply the wrong instrument — completeness does not even arise.
>   Its correct use is ruling out a missing *method*, which is all it is cited for above. And it is
>   another of this binary's **self-enumerations**: finding D2 below records that this binary's own
>   error-message flag enumeration omits a working flag, and N72 records three more such omissions.
>   No self-enumeration on this binary should be treated as decisive on its own. The original axis 3
>   rested decisively on one without inheriting that caution — the same defect this document names
>   elsewhere as its governing rule.
> - **A future probe cannot use an exit code.** `cmux rpc` **silently ignores unknown params**, the
>   same trap as `new-surface` one layer down:
>
>   ```
>   $ cmux rpc workspace.env '{"workspace":"workspace:2","sp2BogusParam":1}'
>   exit=0   → byte-identical normal payload, no error, no warning
>   ```
>
>   So settling `cmux rpc surface.create` requires **three** things, not two: a **correctly-guessed
>   parameter name**, a surface actually created, and an in-surface **read-back** — the discipline
>   axis 2 already teaches, plus a step axis 2 never faced. The name is the hard part: a wrong name is
>   silently ignored and is **indistinguishable from an unimplemented feature**, and the CLI's own ref
>   vocabulary is demonstrably *not* the RPC vocabulary (`workspace:2` ignored where
>   `workspace_id: <uuid>` is honored, above). That **strengthens** the do-not-adopt disposition
>   rather than weakening it — a channel whose param names must be guessed, whose wrong guesses fail
>   silently, and whose vocabulary diverges from the documented CLI's is not something the spawn
>   script should build on. That probe is left undone and is listed under §"What could not be
>   established".
>
> **Does the disposition survive?** Yes, but by argument rather than by inference — and the argument
> should be read as a judgment about adoption, not as a claim the param does not exist:
>
> 1. This repo has **already recorded a recommendation not to build on `rpc`**:
>    `2026-07-28-cmux-capability-usage-matrix.md` §2.9 classifies `rpc` as *unexamined* and concludes
>    *"Recommendation: do not build on `rpc`. Its value is as an enumeration tool."* That is a
>    recommendation in a findings doc, not ratified policy — cite it as such.
> 2. `CLAUDE.md`'s rule is that the CLI is the **contract** surface. `cmux rpc` is neither a
>    documented CLI verb for this purpose nor covered by `docs/cli-contract.md`'s flag tables, so an
>    env param reached that way would be an undocumented param on an unversioned internal surface.
> 3. That is precisely the drift exposure **N72** exists to guard against.
>
> So the residual is real and openly unknown: **an `rpc`-reachable env param on `surface.create` has
> not been excluded.** What is claimed is that the spawn script would not adopt one if it existed.
> This narrows the primary-path completeness claim; it does not touch the a-run fallback viability
> in §Step 2, and it does not change the do-not-adopt recommendation.

### Axis 4 — an exhaustive sweep of the documented CLI verbs

Added 2026-07-30. This is the leg that carries the primary-path conclusion, and it is stronger than
the capabilities-name argument it replaces, because it enumerates the surface a CLI consumer can
actually reach through documented verbs.

Every command name in `cmux --help`'s `Commands:` block was extracted and each one's own `--help`
was run and grepped for an `--env` flag. **Exact bytes as run** — copyable and re-runnable as-is
(a here-string, never a producer piped into `grep -q`, per this repo's SIGPIPE rule):

```
cmux --help >/tmp/top.out 2>/tmp/top.err
awk '/^Commands:/{f=1;next} /^[A-Za-z].*:$/{if(f)f=0} f && /^[ \t]+[a-z]/{print $1}' \
    /tmp/top.out | sort -u > /tmp/cmds.txt
printf 'command count = %s\n' "$(wc -l </tmp/cmds.txt)"
while read -r c; do
  out=$(cmux "$c" --help 2>&1)
  if grep -qi -- '--env' <<< "$out"; then printf 'ENV-FLAG: %s\n' "$c"; fi
done < /tmp/cmds.txt
```

Output:

```
command count =      127
ENV-FLAG: new-workspace
```

**Exactly one of the 127 probed command names exposes an `--env` flag**, and it is the
workspace-creation verb. (127 unique command *names* extracted from the `Commands:` block; alternation
siblings collapse to their first token and were probed separately — scope limit 3 below.) Broadening the grep from `--env` to any mention of `env` returns eight
commands; the other seven were read individually and none is a surface-env channel (`ai-accounts`,
`claude-teams`, `omc`, `omo`, `omx` refer to the caller's shell environment or a "tmux-like
environment"; `vm` is cloud-VM scope; `workspace` matches only because the noun help lists the `env`
**read** subcommand). `respawn-pane --help` offers `--command` and no env flag; the `surface` noun
help (`surface resume`) has none either. **a-run**

**Scope limits of this sweep, stated because they are the only way it could mislead — and one of
them is a genuine residual, not a formality.**

1. **It covers what `cmux --help` PRINTS, which is a floor, not a complete enumeration.** Per finding
   H1 and BACKLOG N72, hidden verbs exist. **This is a real residual: a hidden verb carrying env to a
   surface is not excluded by this sweep.** The two hidden verbs this repo currently knows about were
   probed directly and neither is one — `cmux workspace-group --help` and `cmux claude-hook --help`
   both exit 0 with zero `--env` occurrences, and `workspace-group`'s own `new-workspace <group>`
   subcommand takes only `[--placement …]`. **a-run.** That closes the two known cases; it does not
   close the class, which is exactly what N72's drift guard exists to do.
2. **Nouns with subcommands have no per-subcommand help** (finding H1), so `workspace create`'s flags
   are invisible to this sweep. Harmless here, and it is precisely why the contract (axis 1) and the
   live exercise (§Step 2) are separate legs — between them they cover the creation verb in full.
3. **The 127 are unique command *names*, not every member of the `Commands:` block.** The extractor
   takes the **first token** of each indented line, so an alternation row collapses to its first
   sibling. Seven real top-level names are printed by `cmux --help` and were therefore never given
   their own `--help` by the loop: `enable-browser`, `browser-status`, `logout`, `previous-window`,
   `last-window`, `unbind-key`, `copy-mode`. All seven were probed individually afterwards — exit 0,
   zero `--env` hits — so the gap is a naming artifact of the extraction and the conclusion is
   unaffected. **Probed by the round-2 adversarial re-review (2026-07-30, same pinned binary) —
   reviewer-sourced, not this document's own a-run.**

The residual in (1) is narrower than it looks for the question at hand, because axis 2 does not
depend on enumeration at all: the primary path's actual verb is `new-surface`, and a **read-back**
shows the value does not arrive. A hidden verb would have to be some *third* command that injects env
into an already-existing workspace's surfaces — possible, unexcluded, and unclaimed here.

### Per-surface env channels — both the contract names, and why neither helps

The contract states an *"explicit per-surface environment (a layout `surfaces[].env`, SSH startup
env) overrides the workspace value for that surface."*

**That sentence names two channels; this section exercises the layout one.** The SSH half is disposed
of rather than dropped: `cmux ssh --help` reads *"Create a new workspace, mark it as remote-SSH, and
start an SSH session in that workspace"* and carries **zero** `env` mentions. So whatever SSH startup
env is, it is **not a channel into an already-existing workspace's surfaces** — `cmux ssh` creates a
workspace of its own, and the primary path (a surface added to the caller's existing workspace) is
untouched by it. **Read by the round-2 adversarial re-review (2026-07-30, same pinned binary) —
reviewer-sourced, not this document's own a-run; the help prose was read, `cmux ssh` was not run.**

The layout half was exercised rather than assumed:

```
$ cmux workspace create --name "sp2-layout" … --layout '{"direction":"horizontal","split":0.5,
    "children":[{"pane":{"surfaces":[{"type":"terminal",
      "command":"printf SP2_LAYOUT=%s\\n \"$SP2_LAYOUT\"","env":{"SP2_LAYOUT":"delta"}}]}},
      {"pane":{"surfaces":[{"type":"terminal"}]}}]}'
exit=0   stdout: OK workspace:40

$ cmux read-screen --surface surface:105 --scrollback
SP2_LAYOUT=delta

$ cmux workspace env workspace:40
No environment variables
```

Two things at once: the per-surface env **works** (and the per-surface `command` ran, since the value
was printed by it), and that same per-surface env does **not** appear in the configured view.

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

## Re-capture — the keystone read-back, with a complete transcript

**Why this section exists.** The Task 1 quality review found that the single datum on which the
entire primary-path conclusion rests — `SP2_SURF_MARK=|alpha` — was recorded with **no `send`
command, no `read-screen` invocation, no surface ref and no exit code**, in a document whose §Step 2
opens by promising that every result was captured on separate streams and gated on the exit code.
That is the one place the promise was not visibly honored, and it is **un-re-verifiable read-only**,
because reproducing it requires creating a surface. So it was re-run.

This is a **second probe session with its own refs** (`workspace:41`, `surface:107`, `surface:108`),
deliberately not spliced into the first session's `workspace:38` / `surface:99–105` transcript. Same
binary, re-pinned: `cmux 0.64.20 (100) [14e3400b9]`, `cmux ping` → `PONG`. Throwaway workspace named
`sp2fix-env`, `--focus false`, deleted afterwards (§Cleanup).

**It also closes two other gaps at once:** the create below uses the `cmux new-workspace` spelling,
which the first session never exercised (it exercised `cmux workspace create`) — so the alias claim
is now **a-run on both spellings**, not a-run on one plus a-help on the other. And it re-captures the
workspace-level inherited-process read-back, whose command bytes the first session did not record.

### Step A — create, on the `new-workspace` spelling

```
$ cmux new-workspace --name "sp2fix-env" --cwd "$HOME" --focus false \
    --env SP2_PROBE=alpha --env SP2_SECOND=beta --env-file <fixture>
exit=0
stdout: OK workspace:41
stderr: cmux: 'new-workspace' is now an alias for 'cmux workspace create'. The legacy form keeps
        working indefinitely; set CMUX_QUIET=1 to silence this notice.
```

The `<fixture>` is the same five-line file as §"The env-file fixture". Note the deprecation hint on
**stderr** while stdout stays a clean parseable `OK workspace:41` — finding D5, and the reason
stream separation is not optional here.

### Step B — configured view

```
$ cmux workspace env workspace:41
exit=0   stderr: (empty)
SP2_FILE_EXPORT=file_export
SP2_FILE_PLAIN=file_plain
SP2_PROBE=alpha
SP2_SECOND=beta
```

All four `--env-file` semantics reproduced on this spelling too: `#` comment absent, blank line
absent, `export ` stripped, and `SP2_PROBE=alpha` beating the file's `from_file_should_lose`.

### Step C — create a surface carrying `--env SP2_SURF=gamma`

```
$ cmux new-surface --workspace workspace:41 --type terminal --focus false --env SP2_SURF=gamma
exit=0   stderr: (empty)
stdout: OK surface:108 pane:42 workspace:41

$ cmux workspace env workspace:41
exit=0
SP2_FILE_EXPORT=file_export
SP2_FILE_PLAIN=file_plain
SP2_PROBE=alpha
SP2_SECOND=beta
```

**What this second read establishes — and, deliberately, what it does not.** `SP2_SURF` is absent
from the configured view. That rules out exactly one alternative: `new-surface --env` is **not a
covert workspace-env setter** — it does not write into the workspace-level configured set. It
establishes nothing beyond that, and an earlier draft of this section overreached by concluding the
flag was therefore "never recorded at all."

That conclusion is refuted by this document's own §"Per-surface env channels". The `--layout`
`surfaces[].env` channel demonstrably **works** (`SP2_LAYOUT=delta` was printed by the surface's own
process) and is **equally invisible** to `cmux workspace env` — as measured, the configured view
reports the workspace-level configured set and nothing else. So silence from that view **cannot
distinguish** "`new-surface --env` is unimplemented" from "`new-surface --env` is implemented as
surface-scoped, exactly like layout env." Reading it as proof of the former would be "not in
`workspace env`, therefore absent" — the same absence-of-evidence move this document rejects
elsewhere, aimed at an instrument this document itself measured as blind.

The primary-path conclusion needs no help from here: **Step D's read-back is direct evidence** that
the value does not reach the process, and it carries the section on its own.

### Step D — drive the surface and read back

```
$ cmux send --surface surface:108 'echo "SP2_SURF_MARK=$SP2_SURF|$SP2_PROBE"\n'
exit=0   stdout: OK surface:108 workspace:41   stderr: (empty)

$ cmux read-screen --surface surface:108 --scrollback
exit=0   stderr: (empty)
echo "SP2_SURF_MARK=$SP2_SURF|$SP2_PROBE"
Last login: Thu Jul 30 17:07:47 on ttys017
araymond@Aarons-MacBook-Pro-3 ~ % echo "SP2_SURF_MARK=$SP2_SURF|$SP2_PROBE"
SP2_SURF_MARK=|alpha
araymond@Aarons-MacBook-Pro-3 ~ %
```

Reading the result:

- **`SP2_SURF` is empty** — the value passed to `new-surface --env` never reached the process.
- **`SP2_PROBE=alpha` is present** — and this is the **in-band positive control**, named explicitly
  because the argument is better once named. It proves the payload was delivered, the remote shell
  ran it, variable expansion happened, and the read reached a surface genuinely inside
  `workspace:41`. Without it, an empty first field would be indistinguishable from a probe that
  simply did not run.
- **The confound the first transcript could not exclude is now visually excluded.** The scrollback
  shows the command line echoed with `$SP2_SURF` and `$SP2_PROBE` **unexpanded**, which proves the
  payload was single-quoted locally and expanded remotely. A local expansion would have sent
  `echo "SP2_SURF_MARK=|"` and the recorded output would have had no `alpha` in it.
- **The surface ref is unambiguous** — `surface:108`, the same ref `new-surface` returned in Step C,
  is the ref `send` and `read-screen` were pointed at. The first session's fourth surface was never
  identified, which is what made a wrong-surface read impossible to rule out.

`cmux send`'s trailing `\n` is an escape *it* interprets as Enter — `send --help` states, in full:
*"Send text to a terminal surface. Escape sequences: `\n` and `\r` send Enter, `\t` sends Tab."* That
is why the payload deliberately contains no other backslash: a `printf` format string carrying its
own `\n` would have been consumed as an Enter keystroke mid-payload.

### Step E — the workspace-level read-back, with exact bytes

```
$ cmux send --surface surface:107 'echo "SP2_WS_MARK=$SP2_PROBE|$SP2_SECOND|$SP2_FILE_PLAIN|$SP2_FILE_EXPORT"\n'
exit=0   stdout: OK surface:107 workspace:41   stderr: (empty)

$ cmux read-screen --surface surface:107 --scrollback
exit=0   stderr: (empty)
echo "SP2_WS_MARK=$SP2_PROBE|$SP2_SECOND|$SP2_FILE_PLAIN|$SP2_FILE_EXPORT"
Last login: Thu Jul 30 17:41:08 on ttys012
araymond@Aarons-MacBook-Pro-3 ~ % echo "SP2_WS_MARK=$SP2_PROBE|$SP2_SECOND|$SP2_FILE_PLAIN|$SP2_FILE_EXPORT"
SP2_WS_MARK=alpha|beta|file_plain|file_export
```

`surface:107` is the workspace's own initial surface (`cmux list-pane-surfaces --workspace
workspace:41` → `* surface:107  sp2fix-env  [selected]`). **All four values reached the process
environment**, reproducing §"Half 2" — and doing so for `cmux new-workspace --env`, which is what
takes item 1 of the Bottom line to a-run on both spellings. `surface:108`, created *after* the
workspace, also carried `SP2_PROBE=alpha` (Step D), independently reproducing the contract's *"every
pane, surface, and split created later in that workspace"*.

## Where a document and the installed binary disagreed

| # | Claim | Source | Binary | Verdict |
|---|---|---|---|---|
| D1 | `cmux workspace env … [--json]` | contract, `a-file` | noun help lists only `[workspace] [--mask]`; **`--json` works** (exit 0, well-formed JSON with `count`/`env`/`window_ref`/`workspace_ref`) | **Contract right, help incomplete** |
| D2 | `workspace env` known flags are `--workspace, --window, --mask` | binary's own **error message** | but `--json` demonstrably works | **The binary's own error-message flag enumeration is incomplete** |
| D3 | "Reserved `CMUX_*` variables cannot be overridden" | `--help`, `a-help` | accepted + stored; overridden only at spawn | **Contract right (`"protected at spawn time"`), `--help` misleading** |
| D4 | `--help` caveats are enumerated in the contract's "Current Help Caveats" | contract, `a-file` | `workspace <sub> --help` printing noun help is absent from that list | **Contract incomplete** |
| D5 | Legacy verbs "keep working and print a **one-time** deprecation hint" | `workspace` noun help, `a-help` | printed on **every** invocation — `cmux list-workspaces` run 3 consecutive times emitted it 3/3, and `cmux new-workspace` emitted it again in the re-capture | **`--help` wrong; behavior is per-invocation, not one-time** |

D2 deserves emphasis: this is a **fourth** distinct instance of cmux's surface being incompletely
enumerated by its own machine-readable output, and a new *kind*. N72 records three (a command absent
from the list, flags absent from a summary line, a whole entrypoint absent). This adds: **an error
message that purports to enumerate a command's known flags, and omits a working one.** Any
capability-drift guard keying on help text or error text inherits this hole. Recommend N72 absorb D2.

**D5 is benign today but worth pinning**, because the spawn script parses `new-workspace` **stdout**
for the created ref: the hint goes to **stderr**, so an `OK <ref>` parse is unaffected. It was
re-observed live during the 2026-07-30 re-capture — `cmux new-workspace` printed it on stderr while
stdout carried a clean `OK workspace:41`. This is also a second, independent reason the plan's
`2>&1` + `awk '{print $2}'` recipe was departed from (Deviation 2): merged streams would put the
hint's words where the ref parse looks.

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

- the sprint's **primary** topology is `new-surface` into the caller's existing workspace, which
  **no documented CLI verb can carry env to** — read that qualifier literally: it is established by
  the 127-verb sweep in §Axis 4 and by the `new-surface` read-back in §Axis 2, and the corrected
  limit at the end of §Axis 3 states the one residual it does **not** exclude (an undocumented param
  reached through `cmux rpc`, and why the spawn script would not adopt one anyway). That path can
  only be reached by the composed command string, so the quoting machinery must stay;
- Decision 2 pins **both** topologies to ONE shared launch-and-handshake wrapper with the **same**
  inline env. Adopting `--env` on the fallback alone would fork that wrapper's env channel — adding a
  second mechanism while removing none, which is the opposite of N67's intent.

So the honest disposition is that the **flag works and the idea is sound**, while the **benefit is
blocked by topology, not by the flag**. N67's premise is confirmed-but-not-actionable rather than
refuted. It should stay open as a watch item conditioned on the topology, not be closed as
not-viable and not be scheduled as a subtraction.

**The condition under which this flips to "adopt" — written against SHIPPED code, not against a
planned decision.** The earlier phrasing ("if the surface topology is ever *abandoned*") presupposed
that the surface topology had been adopted. It has not: it is an unshipped decision in
`spec-distilled.md`, while the shipped `spawn-handoff-session.sh` reaches successor state through a
single `cmux new-workspace` call (the `nw=(cmux new-workspace --name … --focus false)` array in
`spawn_claude_workspace`; cite the construct, not a line number — this file's anchors rot). So the
old condition's consequent was **already satisfied on 2026-07-30**, and a reader six months from now
holding a repo where this sprint stalled would have read a flip condition that looked unsatisfied
while in fact it was.

State it against the code instead:

> **Actionable whenever the shipped `spawn-handoff-session.sh` reaches successor state ONLY through
> workspace creation.** That is true of the code as of 2026-07-30 — `cmux new-workspace` is its sole
> spawn verb — and it remains true if `cmux-spawn-v2`'s surface topology is never adopted. It stops
> being true once the surface path ships as primary, and becomes true again if that path is later
> withdrawn.

Both branches are therefore covered: **sprint landed** ⇒ not actionable (the surface path has no env
channel any *documented CLI verb* reaches, so the command string stays); **sprint never landed, or
landed and was reverted** ⇒
actionable, and `--env` becomes strictly better than the inline prefix, making N67's subtraction
available in full. The check is one `grep` over the shipped script, not a judgment about intent.

---

## What could not be established

Stated plainly, because a wrong disposition here becomes a third false-premise row.

1. **Whether `workspace.create` / `surface.create` accept an undocumented env param — and note this
   is reachable from the CLI, contrary to what this document originally said.** `cmux capabilities`
   gives method names only, no schemas, so it cannot answer a *parameter* question at all. The
   earlier bound ("no CLI path exists — sufficient for the spawn script, which is a CLI consumer") is
   **withdrawn as invalid**: `cmux rpc <method> [json-params]` is a documented top-level CLI verb
   that calls any v2 method with arbitrary params, so being a CLI consumer is not what puts this out
   of reach. See the corrected limit at the end of §Axis 3 for what *is* established and for the
   three-part argument that the disposition nonetheless holds.

   **What would close it:** `cmux rpc surface.create` with a **correctly-named** candidate env param,
   followed by an in-surface **read-back**. An exit code is useless here — `cmux rpc` silently ignores
   unknown params, so a bogus param returns exit 0 and a normal payload. The parameter *name* is a
   third requirement and the hardest one: a wrong name is silently ignored and is indistinguishable
   from the feature not existing, and the CLI's ref vocabulary is not the RPC vocabulary
   (`{"workspace":"workspace:2"}` is ignored on `workspace.env` where `{"workspace_id":"<uuid>"}` is
   honored — see §Axis 3's corrected limit). A channel with that property is one more reason the spawn
   script should not build on `rpc`. Deliberately not run:
   it mutates cmux state, it is discretionary per the Task 1 quality review, and its natural home is
   the capability matrix rather than this sprint.
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

**Re-capture session (2026-07-30).** One further throwaway workspace, `sp2fix-env` =
`workspace:41`, created `--focus false`, carrying `surface:107` (its own) and `surface:108`. Closed
with `cmux workspace close workspace:41` → exit 0, `OK workspace:41`; the local env-file fixture was
deleted too. Full list re-read afterwards:

```
$ cmux list-workspaces
  workspace:11  Telemetry Exp
* workspace:2  Superpowers  [selected]
  workspace:28  SDD resume: 2026-07-29-cmux-transport
  workspace:20  Handoff Skill
  workspace:22  IBKR Gateway
```

Mechanically checked rather than eyeballed: `grep -c sp2` → **0**, `grep -c 'workspace:41'` → **0**.
The assertion is on the **set** of five workspaces (`2, 11, 20, 22, 28`), not on their order —
the Task 1 quality review observed the sidebar order varying between two listings with no mutating
command in between, so a byte-identical listing is not something this probe can honestly claim.

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
| 8 | Disposition (a)'s consequent departed from: the BACKLOG row proposes a **topology-conditioned watch item**, not "the swap" | self-initiated | Raised by the Task 1 spec review, which asked it be carried as a deviation. The plan's (a) reads "viable → BACKLOG row proposing the swap"; the measured answer is viable-but-blocked-by-topology, so proposing the swap outright would misrecord it |
| 9 | **A second live probe session was run** (`sp2fix-env` = `workspace:41`), beyond the plan's single `sp2-env` workspace | quality-review-directed | Remediating the Task 1 quality review's I4/M1: the keystone `SP2_SURF_MARK` datum had no transcript and was un-re-verifiable read-only, and `new-workspace --env` had never been exercised. Same cleanup discipline; zero residuals |
| 10 | Added a **sweep of the documented top-level CLI verbs** (axis 4 — 127 unique names from the `Commands:` block, alternation siblings probed separately) | quality-review-directed | The quality review showed axis 3's "no CLI path exists" bound was unearned because `cmux rpc` is a CLI path to arbitrary RPC params. The sweep is what actually carries the primary-path conclusion |

## BACKLOG rows

Filed as **N79**. It was originally filed on this branch as **N76** — the next free id when the
actual ids were enumerated at execution time — but that enumeration covered only this branch, and
`main` had meanwhile claimed N76 for the sibling SP1 row (context-probe misattribution on
fix-marked dispatches), plus N77 and N78. Renumbered to N79, the first id free on both branches.

**N67 was also updated in place**, on the 2026-07-30 revision. It had been left reading *"not
exercised — probe before building"* with status `open` and no pointer to N79 — telling a future
reader to run a probe that has already been run, and leaving the file carrying two rows about one
item with contradictory guidance. The file's convention for a corrected premise is an in-place
UPDATE (precedent: N56's title records that its original premise *"was disproven 2026-07-28"*), so
N67 now carries an `UPDATE 2026-07-30` clause pointing at N79 and at this document.

**One item deliberately not done.** The Task 1 quality review's B1 asked that `cmux rpc` be routed to
`2026-07-28-cmux-capability-usage-matrix.md` as *"the single highest-leverage entry it is currently
missing."* **It is not missing** — the matrix already carries `rpc` in its §1 table (`unexamined`,
a-run) and drills into it at §2.9, concluding *"Recommendation: do not build on `rpc`."* That
recommendation is now cited from §Axis 3 rather than duplicated, and the matrix is outside this
task's write scope in any case.
