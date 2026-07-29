# cmux CLI Capability-vs-Usage Matrix (BACKLOG N60)

**Date:** 2026-07-28
**Deliverable for:** BACKLOG **N60** — "Enumerate the full cmux CLI surface against our integration."
**Predecessor:** `2026-07-28-cmux-cli-capability-gap-analysis.md` (findings cited, not re-derived).
**Verification baseline:** `cmux --version` → **`cmux 0.64.20 (100) [14e3400b9]`**, recorded at run time
this session. Matches the version the gap analysis used.

> **Line citations are pinned to `df46c76`, not to the working tree.** Every `:NNN` reference to
> `spawn-handoff-session.sh` in this document was read at commit **`df46c76`** ("docs: move the cmux
> runtime contract into the skill…"), which was `HEAD` throughout this audit. **A concurrent session
> began hardening that script while this document was being written** — adding the N55 `MAX_HOPS`
> numeric guard and `.active-feature` path-traversal validation (+59 lines near the top), plus
> `tests/unit/test_spawn_handoff_hardening.py`. That work is **uncommitted and still in flux**, and it
> shifts every citation below line ~67: `:122` → 164, `:414` → 471, `:419` → 476. Resolve any
> `:NNN` here against `df46c76` (`git show df46c76:<path>`), or better, search for the quoted anchor
> text — the anchors are stable, the numbers are not. Citations to `claude-picker` (`:324`, `:435`,
> `:442`) are unaffected; that file was not modified.

**Governing rule applied throughout** (CLAUDE.md § "cmux documentation, versions, and which source
wins"): for flag-level facts, `cmux <cmd> --help` **on the installed binary** outranks the web docs,
the vendored skills, and the raw-GitHub URLs. Every capability claim below was checked against the
installed binary. Where a claim is *not* category (a), it is labelled.

---

## Confidence legend

Used as an explicit column in the matrix, because the failure this audit exists to correct is exactly
a category-(b) claim treated as category-(a).

| Label | Meaning |
|---|---|
| **a-run** | **Exercised** against the installed binary this session — command run, output and/or exit code observed. |
| **a-help** | Existence and flags read from the **installed binary's own `--help`**. Contract-level per the fork rule, but behavior not exercised. |
| **b-doc** | Read in a document — vendored skill, web docs, raw-GitHub URL. Not authoritative for flags. |
| **c-2nd** | Secondhand — a community README's description of a repo I did not read. |

---

## Headline counts

Classification is **as of the shipped integration** (N43(D), merged 2026-07-28). Commands the
2026-07-28 gap analysis or this audit examined *after* the integration shipped are annotated
`[audited 2026-07-28]` in Notes — they were still unexamined when the design was made, which is the
point of the exercise.

| Class | Count | Share |
|---|---|---|
| **used** | **3** | 2.4% |
| **considered-and-rejected** | **4** | 3.1% |
| **unexamined** | **120** | 94.5% |
| **Total top-level commands enumerated** | **127** | |

**Counting rule, so the number is reproducible.** 127 is the count of distinct first tokens in the
`Commands:` block of `cmux --help` on 0.64.20, mechanically extracted:

```bash
cmux --help | awk '/^Commands:/{f=1;next} /^Environment:/{f=0} f' \
  | grep -vE '^\s*$|^\s*#' | sed -E 's/^[[:space:]]+//' | awk '{print $1}' \
  | sed 's/|.*//' | sort -u | wc -l      # → 127
```

Alternation groups (`login | logout`, `next-window | previous-window | last-window`,
`bind-key | unbind-key | copy-mode`, `disable-browser | enable-browser | browser-status`) count once
by their first token, and the whole `browser *` subtree counts once. Every one of the 127 tokens
appears in a matrix row below (verified mechanically; `surface` appears as `surface resume`, its only
top-level subcommand). **`workspace-group` is a 128th command that is NOT in that list** — it is
reachable only via `cmux workspace group` or `cmux workspace-group --help`, which is precisely how
N57 came to call it unverified (see §2.11).

Of the 4 considered-and-rejected, **4 of 4 rested on a premise that is now false.** Not one rejection
reason survives contact with the installed binary.

> **Insight — what the 93.9% actually measures**
>
> It is not a to-do list; most of that column is `browser *`, `vm`, `ssh*`, `remotes` — genuinely
> out of scope for a handoff-spawn feature, and they should stay unexamined. The number matters
> because *nobody knew which 94% it was.* An unexamined column you have never printed cannot tell
> you that `--env`, `workspace-group`, `events`, and `set-progress` are sitting in it. The deliverable
> is the printing, not the percentage.

---

## 1. The matrix

Every top-level command from `cmux --help` on 0.64.20, grouped functionally for legibility. Grouped
subtrees (`browser`, `ssh*`, `vm`) are one row each and are counted as one command.

### Used by our integration (3)

| Command | Class | Conf. | Where / Notes |
|---|---|---|---|
| `new-workspace` | **used** | a-run | `spawn-handoff-session.sh:414` — `--name --cwd --command --focus false`. **Uses 4 of its 11 flags.** See drill-down §2.7: `--env`, `--env-file`, `--layout`, `--group*` are all unused, and `--env`/`--env-file` are **absent from the top-level help summary**. |
| `notify` | **used** | a-run | `:429` (success), `:134` (hop limit), `:192` (quota low), `:488` (spawn-failed). Deliberately *not* called at `:125`/`:464`/`:469` — see CLAUDE.md "notify asymmetry". |
| `ping` | **used** | a-run | `:122` reachability probe, `!= PONG` → exit 3. |

### Considered and rejected — all 4 reasons now invalid (4)

| Command | Class | Conf. | Rejection reason, and whether it still holds |
|---|---|---|---|
| `read-screen` | rejected | **a-run** | **Reason: "cmux has no surface-read" (N56). INVALID — the command exists and works.** **Exercised §4:** read a marker back from a surface in an **unfocused background** workspace. This single false premise propagated into N56 *and* N57. **Caveat found only by running it: a COLD surface is unreadable** — `internal_error: Failed to read terminal text` until something is sent to it; `surface-health`'s `in_window` does not predict it. |
| `send` | rejected | **a-run** | **Reason: "races shell readiness, no way to know the shell is ready" (N57). INVALID** — `wait-for` removes the race. **Exercised §4:** `cmux send --surface surface:45 "echo …\n"` → `OK surface:45 workspace:19`, marker echoed. `\n`/`\r` send Enter, `\t` sends Tab. |
| `send-key` | rejected | **a-run** | Same rejection, same invalidation as `send`. **Exercised §4.1:** `cmux send-key --surface <ref> Enter` submitted a line into a live Claude Code TUI. In a TUI, `send` the text and `send-key Enter` separately — you can `read-screen` between them and confirm the buffer holds what you think before committing. |
| `new-surface` | rejected | **a-run** | **Reason: "no `--command`, so surfaces can't launch atomically" (N57). INVALID IN EFFECT.** `--command` is indeed still absent (flags are `--type --pane --placement --workspace --window --url --provider --renderer --working-directory --focus`). But **exercised §4**: `new-surface` into an existing workspace returns `OK surface:43 pane:19 workspace:19` and lands in the SAME pane (`pane:19 [2 surfaces]`) — i.e. a top **tab**; `respawn-pane` or `send` then drives it, and `wait-for` removes the readiness race. Two steps, not a wall. |

### Unexamined (120)

**Agent integration & lifecycle** — the highest-value block. Drill-downs in §2.

| Command | Class | Conf. | Notes |
|---|---|---|---|
| `hooks` | unexamined | a-run | Native agent lifecycle. **Claude Code is absent from the agent list because the cmux Claude wrapper injects hooks automatically.** `[audited 2026-07-28]` — §2.1, and Question 1 in §3. |
| `events` | unexamined | a-run | Structured NDJSON stream, durable cursor. **Already carrying live Claude data.** `[audited 2026-07-28]` — §2.2. |
| `set-hook` | unexamined | a-run | tmux-compat hook definitions. `cmux set-hook --list` → **"No hooks configured"** — a second, entirely empty lifecycle channel. `[audited 2026-07-28]` §2.3. |
| `feed` | unexamined | a-help | `feed tui\|clear`. The Feed surface that `feed.item.*` events populate. |
| `agent-hibernation` | unexamined | a-help | `<on\|off>`. Idle/live-terminal limits. Relevant to a parked successor. |
| `restore-session` | unexamined | a-help | "Reopen the previous saved cmux session." App-level, not per-workspace. |
| `surface resume` | unexamined | a-help | `set\|show\|get\|clear` — attach restart-command metadata to a surface. §2.6. |
| `claude-teams`, `codex-teams`, `omo`, `omx`, `omc` | unexamined | a-help | Multi-agent launchers. Overlap with `claude-picker`'s role — worth a look before extending ours. |

**Sidebar telemetry** — the cheapest win in the whole surface (§2.4, Question 2 in §3).

| Command | Class | Conf. | Notes |
|---|---|---|---|
| `set-progress` / `clear-progress` | unexamined | a-run | `<0.0-1.0> [--label]`. **Measured 55 ms.** `[audited 2026-07-28]` |
| `set-status` / `clear-status` / `list-status` | unexamined | a-run | `<key> <value> [--icon] [--color] [--priority]`. **Measured 54 ms.** Keyed, so tools don't collide. `[audited 2026-07-28]` |
| `log` / `clear-log` / `list-log` | unexamined | a-help | `--level info\|progress\|success\|warning\|error`, `--source`. An activity feed the flight recorders could mirror into. |
| `todo` | unexamined | a-run | Per-workspace checklist, 50-item cap, `--origin user\|agent`, **`cmux todo set` replaces the whole list from a JSON array on stdin**. Maps onto SDD plan checkboxes — §2.8. |
| `sidebar-state` | unexamined | a-run | Read-only dump: cwd, `git_branch=main dirty`, progress, status_count, log_count. A free health probe. |
| `right-sidebar`, `sidebar` | unexamined | a-help | Sidebar mode/selection control. |

**Sync, I/O and inspection**

| Command | Class | Conf. | Notes |
|---|---|---|---|
| `wait-for` | unexamined | a-run | Named sync token, **proven cross-workspace 2026-07-28**. Carried by **N61**. `[audited 2026-07-28]` |
| `capture-pane` | unexamined | a-help | tmux-compat alias of `read-screen`. |
| `pipe-pane` | unexamined | a-run | **Correction to the gap analysis — see §2.5.** It is a **one-shot capture**, not a stream. `[audited 2026-07-28]` |
| `respawn-pane` | unexamined | **a-run** | "Send a command … to a surface." **Exercised §4** — drives a command into an existing surface, `OK` exit 0, and the `wait-for` handshake fired from inside it. **Caveat found only by running it: the surface is DESTROYED when the command exits** (short-lived probe → `Error: not_found: Surface not found`; adding `sleep 300` kept it alive). `[audited 2026-07-28]` |
| `find-window` | unexamined | a-help | `[--content] [--select] <query>` — search workspaces by title, optionally by terminal content. |
| `identify` | unexamined | a-run | "Print server identity and caller context details." |
| `capabilities` | unexamined | a-run | 255 JSON-RPC methods, `access_mode: cmuxOnly`. §2.9. |
| `rpc` | unexamined | a-run | Raw v2 method call. §2.9. |
| `tree`, `top`, `memory`, `surface-health`, `debug-terminals` | unexamined | a-run (`surface-health`) / a-help | Introspection. `surface-health` returns e.g. `surface:40 type=terminal in_window=false`. |
| `send-panel`, `send-key-panel` | unexamined | a-help | Panel-targeted write. |
| `set-buffer`, `list-buffers`, `paste-buffer` | unexamined | a-help | tmux-compat buffers. A paste-buffer handoff is an alternative to a composed command string. |
| `display-message`, `popup`, `bind-key`, `unbind-key`, `copy-mode` | unexamined | a-help | tmux-compat UI. |
| `clear-history` | unexamined | a-help | Per-surface scrollback clear. |

**Workspace / window / pane topology** — bears directly on N57.

| Command | Class | Conf. | Notes |
|---|---|---|---|
| `workspace` (canonical noun) | unexamined | a-run | **`cmux workspace <sub>` is the canonical form; `new-workspace`/`list-workspaces`/`close-workspace`/`rename-workspace`/`select-workspace` are LEGACY verbs that "print a one-time deprecation hint."** Our script uses the legacy form and already suppresses the notice with `CMUX_QUIET=1` (`:417`). Latent deprecation exposure — §2.10. Adds `workspace env`, `workspace loading`, `workspace status`, `workspace reconnect/disconnect`. |
| `workspace-group` (= `cmux workspace group`) | unexamined | a-run | **Settles an open N57 question — §2.11.** Full CRUD: `list --json`, `create`, `ungroup`, `delete`, `rename`, `collapse`, `expand`, `pin`, `unpin`, `add`, `remove`, `set-anchor`, `new-workspace`, `set-color`, `set-icon`, `move`, `focus`. `cmux workspace group list` → `No groups`. `[audited 2026-07-28]` |
| `workspace status` | unexamined | a-help | `set <lane\|auto>` — pin the workspace todo status. |
| `list-workspaces`, `close-workspace`, `select-workspace`, `rename-workspace`, `current-workspace`, `reorder-workspace`, `reorder-workspaces`, `workspace-action`, `move-workspace-to-window`, `move-tab-to-new-workspace` | unexamined | a-run (`list-workspaces`, `current-workspace`) / a-help | Workspace management. |
| `list-windows`, `current-window`, `new-window`, `focus-window`, `close-window`, `rename-window`, `next-window`, `previous-window`, `last-window` | unexamined | a-help | Window management. A successor could go to a new *window* — a third topology option N57 never considered. |
| `new-split`, `list-panes`, `list-pane-surfaces`, `focus-pane`, `new-pane`, `last-pane`, `resize-pane`, `swap-pane`, `break-pane`, `join-pane` | unexamined | a-help | Pane management. |
| `rename-tab` | unexamined | **a-run** | **Exercised §4.1** — `cmux rename-tab --surface <ref> "DEMO haiku"` → `OK action=rename tab=tab:46 workspace=workspace:17`. **This is the mechanism for the incremented session numbering N73's topology implies** ("Session 2", "Session 3" as tab labels); nothing else in the surface API names a tab. `[audited 2026-07-28]` |
| `close-surface` | unexamined | **a-run** | Closes a surface. **Ref wart worth knowing — see §4.2:** closing `surface:46` returned **`OK surface:47`**. The surface *was* closed, but the ref in the `OK` line is not the object acted on. `[audited 2026-07-28]` |
| `move-surface`, `split-off`, `reorder-surface`, `drag-surface-to-split`, `tab-action`, `refresh-surfaces`, `trigger-flash` | unexamined | a-help | Surface management. |
| `list-panels`, `focus-panel` | unexamined | a-help | Panel management. |

**Notifications** — we use only `notify`.

| Command | Class | Conf. | Notes |
|---|---|---|---|
| `list-notifications`, `dismiss-notification`, `mark-notification-read`, `open-notification`, `jump-to-unread`, `clear-notifications` | unexamined | a-help | The read/manage half. Our integration is write-only here; a successor could acknowledge the parent's notification. |

**Out of scope for a handoff-spawn feature** — correctly unexamined; listed so the column is complete.

| Command | Class | Conf. | Notes |
|---|---|---|---|
| `browser *` (subtree, ~60 subcommands) | unexamined | a-help | Full Playwright-class browser automation. Not handoff-related. |
| `disable-browser`, `enable-browser`, `browser-status` | unexamined | a-help | Browser toggles. |
| `ssh`, `ssh-tmux`, `ssh-session-list`, `ssh-session-attach`, `ssh-session-cleanup`, `remote-daemon-status` | unexamined | a-help | Remote workspaces. Would matter only for a remote successor. |
| `vm` (alias `cloud`), `remotes`, `ai-accounts` | unexamined | a-help | Cloud VMs, routing, account upload. |
| `auth`, `login`, `logout` | unexamined | a-help | cmux account auth. |
| `open`, `diff`, `markdown`, `themes`, `feedback`, `welcome`, `docs`, `settings`, `config`, `shortcuts`, `version`, `help` | unexamined | a-run (`docs`, `version`) / a-help | UI/meta. `markdown` is already covered by the vendored `cmux-markdown` skill. |
| `reload-config`, `set-app-focus`, `simulate-app-active`, `simulate-sidebar-drag` | unexamined | a-help | App-level/test affordances. |

---

## 2. Drill-down on the high-value unexamined commands

### 2.1 `hooks` — native agent lifecycle *(a-run)*

```
Usage: cmux hooks setup [agent] [--agent <name>] [--yes|-y]
       cmux hooks <agent> <install|uninstall|event> [options]
       cmux hooks feed --source <agent> [--event <event>]

Manage and run cmux agent hooks without adding one top-level command per
agent. Claude Code hooks are injected automatically by the cmux Claude wrapper.

Agents:
  codex, grok, opencode, pi, omp, campfire, amp, cursor, gemini, kiro,
  antigravity (agy), rovodev (rovo), hermes-agent, copilot, codebuddy, factory, qoder
```

**What it gives us:** nothing to install — Claude is not in the list *because* it is handled by the
wrapper. The operative question is whether the wrapper is actually in our path. Answered empirically
in §3, Question 1.

**Cost:** zero to inspect. Non-zero to *adopt* — see the settings-merge hazard in §3.

### 2.2 `events` — structured lifecycle stream *(a-run)*

```
Stream cmux events as newline-delimited JSON.
  --after <seq>          Replay retained events after this sequence
  --cursor-file <path>   Read the starting sequence from a file and update it after each event
  --name <event>         Filter by event name, repeatable
  --category <name>      Filter by category, repeatable
  --reconnect            Reconnect forever and resume from the last received sequence
  --limit <n>            Exit after printing n event frames
  --no-ack / --no-heartbeat
```

**Verified live.** Replaying `--after 9000 --limit 900` returned 897 frames. The ack frame reports
the retention window explicitly (`oldest_seq: 5799`, `latest_seq: 9894`, `replay_count: 4096`), and
`gap_reason` names truncation when you ask for something older — so a cursor consumer can *detect*
that it missed events rather than silently skipping them.

Observed event names and volumes:

| Name | Count | Name | Count |
|---|---|---|---|
| `feed.item.received` / `.completed` | 122 / 122 | `agent.hook.UserPromptSubmit` | 26 |
| `agent.hook.PreToolUse` | 82 | `agent.hook.Stop` | 26 |
| `agent.hook.PostToolUse` | 82 | `agent.hook.SessionStart` / `SessionEnd` | 14 / 14 |
| `surface.selected` / `.focused` | 50 / 50 | `workspace.prompt.submitted` | 13 |
| `workspace.selected` | 49 | `surface.created` / `.closed` | 6 / 7 |
| `notification.*` | 129 | `sidebar.metadata.updated` | 26 |

Sources: `codex` 432, `workspace.lifecycle` 191, `notification.store` 101, **`claude` 56**,
`socket.v1` 52, `window.lifecycle` 38, `workspace.prompt_submit` 13, `socket.v2` 13.

Each `agent.hook.*` payload carries `session_id`, `cwd`, `workspace_id`, `hook_event_name`,
`tool_name`, `phase` (`received` → `completed`), and `redacted_fields` (codex redacts `tool_input`;
Claude's payloads carry no tool fields at all — see §3).

**What it would let us do:** an out-of-band observer of SDD sessions that needs no hook of our own —
a durable-cursor tail could reconstruct a session timeline across restarts. **Cost:** it is a
long-running stream, so a consumer is a daemon, not a hook. `--limit`/`--after` make one-shot polling
possible, but the retention window is in-memory and bounded (~4096 events), so a poller that sleeps
too long loses data — the `gap` flag tells you, which is the redeeming detail.

### 2.3 `set-hook` — a second, empty lifecycle channel *(a-run)*

```
Usage: cmux set-hook [--list] [--unset <event>] | <event> <command>
Manage tmux-compat hook definitions.
```

`cmux set-hook --list` → **`No hooks configured`**. Distinct from `cmux hooks` (agent integrations).
This is the tmux-style "run this shell command on this cmux event" mechanism, and it is entirely
unused on this machine. **What it would let us do:** react to workspace/surface events without a
daemon. **Cost:** the event-name vocabulary is undocumented in `--help`; it would need probing before
anything depends on it.

### 2.4 `set-status` / `set-progress` / `log` — sidebar telemetry *(a-run)*

Measured on the installed binary, against this session's own workspace, cleared immediately after:

| Call | Result | Latency |
|---|---|---|
| `cmux set-status sdd_probe "audit" --icon sparkle --priority 10` | `OK`, visible in `list-status` | **54 ms** |
| `cmux set-progress 0.42 --label "ctx"` | `OK` | **55 ms** |
| `cmux clear-status` / `clear-progress` | `OK`, `No status entries` | — |

`set-status` is **keyed**, and `--help` says so explicitly: *"Use a unique key so different tools
(e.g. `claude_code`, `build`) can manage their own entries."* We would not collide with anything else
writing to the sidebar. Full details and the failure modes in §3, Question 2.

### 2.5 `pipe-pane` — **correction to the gap analysis** *(a-run)*

The gap analysis (`2026-07-28-cmux-cli-capability-gap-analysis.md`, table row) describes `pipe-pane`
as *"**Stream** pane text into a shell command."* That was read from the top-level help summary
(category **a-help**). **Exercised, it is a one-shot capture, not a stream:**

```
cmux pipe-pane --surface "$CMUX_SURFACE_ID" --command 'head -c 3000 > /tmp/pp-probe.txt'
→ OK, exit 0; file = 1751 bytes of plaintext pane content
after 5 further seconds of pane output: still 1751 bytes  → no growth
```

Its own `--help` is the more accurate source: *"Capture pane text and pipe it to a shell command via
stdin."* It is `read-screen` with a consumer attached. `cmux pipe-pane` without `--command` errors
(`pipe-pane requires --command`), so there is no tmux-style toggle-off idiom.

This is worth recording for its own sake: the gap analysis corrected a category-(b) error and then,
one row later, made a smaller category-(a-help) one. **The word "stream" would have shaped a design.**

### 2.6 `surface resume` / `restore-session` / `agent-hibernation` — persistence *(a-help)*

```
cmux surface resume set [--kind <kind>] [--checkpoint <id>] [--cwd <path>] -- <argv...>
cmux surface resume show|get [--json] | clear
Attach restart command metadata to a terminal surface.
Public CLI bindings are stored for inspection and manual restore.
```

**What it would let us do:** this is the closest first-party analogue to what our spawn script does by
hand. We compose a `claude-picker …` command string and hand it to `new-workspace --command`; `surface
resume set` would *record* that command against the surface, with `--kind agent` and `--checkpoint
<session id>` fields that look purpose-built for exactly our case. The examples even show
`--kind opencode --checkpoint ses_123 -- opencode --session ses_123`.

**Cost / caveat:** `--help` says the bindings are *"stored for inspection and manual restore"* — it
does not promise automatic re-launch. Adopting it would be **additive metadata**, not a replacement
for the spawn. `restore-session` is app-level ("reopen the previous saved cmux session") and
`agent-hibernation <on|off>` is a global toggle — neither is per-handoff. All three are **a-help
only; none were exercised.**

### 2.7 `new-workspace --env` — the highest-leverage find *(a-help)*

`cmux new-workspace --help` lists two flags that **do not appear in the top-level `cmux --help`
summary line for the same command** — precisely the flags below:

```
  --env KEY=VALUE      Set a workspace environment variable. Repeatable.   ← absent from top-level
                       Reserved CMUX_* variables cannot be overridden.
  --env-file <path>    Load KEY=VALUE lines from a file. Repeatable.       ← absent from top-level
```

**To be exact about which claim is which:** the top-level summary reads
`new-workspace [--name] [--description] [--cwd] [--command] [--layout] [--window] [--focus] [--group]
[--group-placement] [--group-reference]`. Only the two `--env*` flags are missing from it. A third
flag is relevant here but was **not** hidden — `--layout <json>` appears in both places, and is called
out below on its own merits, not as a discovery gap:

```
  --layout <json>      Create workspace with a predefined split layout.
                       Layout surfaces define their own commands.
```

**Why this matters more than anything else in the matrix.** `spawn-handoff-session.sh` currently
passes *all* successor state through a single composed shell string: a v1 base64 argv codec, a
base64 append-prompt rematerialized to `~/.claude-codex-handoff/append-prompts/<bundle>-hop<N>.md`,
`shlex.quote` re-quoting of every element, and a `printf`-not-`echo` workaround for `xpg_echo`. That
machinery exists because a command string is the only channel we knew about.

`--env` is a second channel. Hop number, spawn id, and any `SUPERPOWERS_CMUX_*` override could ride
as environment variables instead of being interpolated into a string a shell will re-parse.

This is the rare finding that **subtracts** code rather than adding surface. Caveats, stated plainly:
the append-prompt is *content*, not a scalar, so `--env` does not obviously replace the
rematerialization; reserved `CMUX_*` names cannot be overridden; and **this is a-help — the flag was
not exercised.** Anyone acting on it should probe it first.

`--layout <json>`, where *"Layout surfaces define their own commands,"* partially dissolves N57's
"`new-surface` has no `--command`" — a multi-surface workspace *can* be created with per-surface
commands atomically.

### 2.8 `todo` — per-workspace checklist *(a-run)*

```
Per-workspace checklist, writable by you and by agents. Items are capped at 50 per workspace.
  add "text" [--state <pending|in-progress|completed>] [--origin <user|agent>]
  list | check | uncheck | start | edit | rm | clear
  set ['<json>']   Atomically replace the whole checklist from a JSON array of
                   {text, state?, id?, origin?} objects (inline, or piped on stdin).
                   Items whose id matches an existing item keep their identity.
  open             Open (or focus) the workspace's todo pane
```

**What it would let us do:** SDD plans already carry per-task checkboxes, and `controller-checkpoint.py`
already knows the task range and completion state. `cmux todo set` takes a whole JSON array on stdin
with **stable ids**, so a checkpoint run could mirror plan state into the sidebar idempotently — not
append-and-drift. `--origin agent` distinguishes machine-written items from the user's own.

**Cost:** 50-item cap (fine — plans are ~10–15 tasks). Needs a JSON projection of plan state that does
not exist yet. Strictly cosmetic: nothing may gate on it.

### 2.9 `rpc` + `capabilities` — the control plane *(a-run)*

```
cmux rpc <method> [json-params]
Call a raw v2 method with an optional JSON object for params.
```

`cmux capabilities` returns **255 methods**, of which **163 are non-browser**, and
**`"access_mode": "cmuxOnly"`** — a real constraint: the socket is not a general-purpose API surface.

The non-browser methods confirm the CLI is a thin shell over the RPC layer, and expose a few things
with no obvious CLI verb:

- `surface.read_text` (the `read-screen` backend), `surface.report_shell_state`, `surface.report_tty`,
  `surface.report_pwd` — **`report_shell_state` is interesting for the N56 liveness question**, though
  it is plainly an inbound report from the shell integration, not a query for us to call.
- `workspace.group.*` — 17 methods, matching the `workspace-group` CLI one-for-one (§2.11).
- `workspace.env`, `workspace.prompt_submit`, `workspace.set_auto_title`.
- `feed.*` (`push`, `list`, `jump`, `permission.reply`, `question.reply`, `exit_plan.reply`) — the Feed
  is interactive, not just a log.
- `mobile.*`, `remote.tmux.*`, `vm.*` — out of scope.

**What it would let us do:** nothing today that a CLI verb does not. **Cost:** using `rpc` means
depending on an unversioned-in-`--help` internal surface, against the fork's own "CLI is for contract"
rule. **Recommendation: do not build on `rpc`.** Its value is as an *enumeration* tool — it tells you
what exists so you can look for the supported CLI verb.

### 2.10 `workspace` as canonical noun — latent deprecation exposure *(a-run)*

```
Canonical noun for workspace operations. Legacy verbs
(new-workspace, list-workspaces, close-workspace, rename-workspace, select-workspace)
keep working and print a one-time deprecation hint pointing here.
```

Our integration uses `new-workspace` — a legacy verb — and `spawn_claude_workspace()` already sets
`CMUX_QUIET=1` (`:417`) specifically to suppress that deprecation notice, with a comment explaining
the alias. So the fork already *encountered* the deprecation and worked around the symptom without
recording that a canonical replacement (`cmux workspace create`) exists.

Not urgent: `--help` says the legacy verbs "keep working." But it is exactly the kind of thing that
becomes urgent on a cmux upgrade, and the one-line change is known now.

### 2.11 `workspace-group` — settles an open N57 question *(a-run)*

N57 states: *"Still genuinely unverified … how workspace **groups** are created/referenced —
`list-workspace-groups` is confirmed ABSENT from `cmux --help` on 0.64.20."*

`list-workspace-groups` is indeed absent. **The functionality is not.** It lives under a different
name, reachable two ways — `cmux workspace group <sub>` (via `cmux workspace --help`) and
`cmux workspace-group --help`:

```
Manage collapsible workspace groups in the sidebar. Each group is owned by an
"anchor" workspace; the group header IS the anchor's sidebar representation.
Closing the anchor dissolves the group while preserving its other members.

  list [--json] | create [--name] [--cwd] [--from <id>,<id>...] | ungroup | delete
  rename | collapse | expand | pin | unpin | add --group --workspace | remove --workspace
  set-anchor | new-workspace <group> [--placement] | set-color | set-icon | move | focus
```

`cmux workspace group list` → `No groups` (exit 0). All 17 operations are mirrored in
`capabilities` as `workspace.group.*`.

**This is the second instance of the same error class as `read-screen`:** a capability declared
"unverified/absent" on the strength of one guessed command name, when the real name was one
`--help` away. Worth naming, because two instances is a pattern, not an accident.

Note for whoever implements the N57 middle path: **the anchor semantics are load-bearing.** The group
header *is* the anchor workspace, and closing the anchor dissolves the group. A successor chain
grouped under its parent inherits a lifecycle dependency on that parent — closing hop 1 dissolves
the grouping for hops 2 and 3. That is a design constraint N57 does not currently mention.

---

## 3. The two specific questions

### Question 1 — is a cmux-side Claude lifecycle channel already live?

**Answer: yes, the channel is real and live — but our sessions are not on it, and it carries far less
than the codex traffic suggests.** Three findings, each labelled.

**(i) The wrapper exists and is on PATH.** *(a-run)*

`which -a claude` resolves **first** to a cmux shim:

```
/var/folders/…/T/cmux-cli-shims/2385488F-…/claude      ← cmux shim (bash, 38 lines)
/Users/araymond/.local/bin/claude                      ← the real one
```

The shim `exec`s `/Applications/cmux.app/Contents/Resources/bin/cmux-claude-wrapper`, falling back to
stripping itself from `PATH` and re-`exec`ing `claude` if the wrapper is missing. Every cmux terminal
gets the shim directory on `PATH`, and `CMUX_CLAUDE_WRAPPER_SHIM` / `_SHIM_ROOT` in the environment.

**(ii) The wrapper injects hooks by merging settings.** *(a-run, via `strings` on the wrapper)*

The wrapper is a 39 KB bash script. Its own strings show the mechanism:

```
CMUX_BASE_SETTINGS="$HOOKS_JSON"      HOOKS_JSON="$CMUX_MERGED_SETTINGS"
CMUX_USER_SETTINGS+=("${arg#--settings=}")
export CLAUDE_CONFIG_DIR="$candidate"
printf 'cmux: warning: --settings merge failed; your --settings was ignored\n' >&2
```

It composes a cmux hooks JSON, merges any user `--settings` into it, and sets `CLAUDE_CONFIG_DIR`.

> **This is the flag before anyone proposes "just route through the shim."** This fork's *entire*
> enforcement layer — the SDD pre-dispatch hook, the report guard, the plan-validation gate, the
> handoff gate, the session-start hook — lives in `~/.claude/settings.json`, and 7 of those hook
> scripts are pinned by sha256 in `tests/ARaymond-hook-baseline/baseline.txt`. Adopting the wrapper
> means putting a third-party settings-merge step in front of that layer, with a documented failure
> mode in which **your `--settings` is silently dropped with a one-line warning**. That is a
> hook-composition change requiring its own test plan, not a free upgrade.

**(iii) Our sessions are not on the channel.** Two independent halves — stated separately, because
conflating them would be the exact category error this audit exists to correct.

*Code-verified (a-run, source read):* `claude-picker` never resolves `claude` via `PATH`. It discovers
versions under `$VERSIONS_DIR` (`$HOME/.local/share/claude/versions`) and, on all three launch paths
(`:324`, `:435`, `:442`), does:

```bash
exec caffeinate -i "$binary" "$FLAG" "$@"     # $binary = $VERSIONS_DIR/$selected
```

A direct absolute-path exec of the version binary. **The shim is structurally unreachable on every
picker path** — not by configuration, by construction.

*Live-verified (a-run):* this session runs
`/Users/araymond/.local/share/claude/versions/2.1.220 --dangerously-skip-permissions` (parent `zsh`,
no wrapper in the ancestry) and **emits nothing**. Its session id `2b988cec-…` appears **zero** times
in the retained event log; a 15-second live `cmux events --category agent` stream captured during
active tool use returned **0 lines**; `latest_seq` advanced only 9894 → 9896 across the whole session.

*(Honest caveat: this session's ancestry shows no `caffeinate`, so I cannot prove it was itself
launched by `claude-picker`. What is proven is the general fact that matters — a direct-version-binary
session emits nothing — plus the source-level fact that the picker always produces exactly that.)*

**(iv) What the channel actually carries for Claude — the ceiling is low.** *(a-run)*

Of 56 `claude`-sourced events across 7 distinct sessions, all in this repo's cwd:

| Source | Hook events emitted |
|---|---|
| **claude** | `SessionStart`, `SessionEnd` — **and nothing else** |
| **codex** | `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop` |

Every Claude session contributed exactly 8 frames (SessionStart/SessionEnd × received/completed ×
`agent.hook.*`/`feed.item.*` mirrors). Claude payloads carry `session_id`, `cwd`, `workspace_id`,
`hook_event_name`, `phase` — and `tool_name: null`.

**So even for a wrapper-launched session, the channel fires twice per session.** It cannot see task
dispatches, cannot see tool use, and cannot see prompts. The rich codex traffic is a red herring:
that comes from `cmux hooks codex install`, an integration Claude does not have.

**Could `sdd-pre-dispatch-hook.sh` consume it? No — and it should not try.** The hook needs
per-dispatch context tokens, which it already reads from the transcript via `context-probe.py`. The
cmux channel offers nothing at dispatch granularity for Claude. **Should we coordinate with it? Only
in one direction:** the interesting asymmetry is that cmux would *like* SDD lifecycle signal and
cannot get it. Writing to the sidebar (Question 2) is the cheap, correct version of coordination —
push, not pull.

> **AMENDED 2026-07-29 — the "push, not pull" conclusion is right, but the push channel is bigger
> than this section knew.** `cmux claude-hook` (hidden from `cmux --help`; documented in
> `docs/cli-contract.md:160,371`) accepts **seven** Claude lifecycle events from stdin JSON —
> `session-start`, `active`, `stop`, `idle`, `notification`, `notify`, `prompt-submit`. So the
> asymmetry named above ("cmux would *like* SDD lifecycle signal and cannot get it") is resolvable
> with a supported first-party verb, callable from our own `settings.json` hooks, **without adopting
> the wrapper** — and therefore without the settings-merge hazard flagged in (ii). The ceiling
> measured here (SessionStart/SessionEnd, `tool_name: null`) is the ceiling on what the wrapper
> *emits*, not on what we can *send*. Carried by **N68**.

**Generated config files checked:** `~/.claude/settings.json` contains **zero** cmux references;
`~/.claude/` has no cmux-generated file. `~/.config/cmux/cmux.json` exists (cmux's own settings). The
generated-file list in `cmux hooks --help` covers opencode, pi, omp, campfire, amp, kiro — no Claude
entry, consistent with the wrapper mechanism.

---

### Question 2 — sidebar telemetry: assessment and diff sketch

**Verdict: worth doing, with one non-obvious guard. Lead with the failure mode.**

#### The failure mode that decides the design *(a-run)*

```
$ env -u CMUX_WORKSPACE_ID -u CMUX_SOCKET_PATH -u CMUX_SOCKET -u CMUX_SURFACE_ID \
      bash -c 'cmux set-status x y; echo "exit=$?"'
OK
exit=0
```

**It did not fail. It returned `OK`, exit 0 — and wrote to the wrong workspace.** The CLI
auto-discovers the socket at `~/.local/state/cmux/cmux.sock`, so stripping the environment does not
disconnect it; it falls back to the **selected** workspace. Verified: the write landed on
`workspace:2` ("Superpowers", `[selected]`), not on this session's `workspace:17`. *(Cleaned up:
`cmux clear-status x --workspace workspace:2` → `No status entries`.)*

The only genuinely failing case is `cmux` absent from `PATH` — `command not found`, exit **127**.

So the naive `cmux set-status … 2>/dev/null || true` is **not** safe. It never errors; it silently
mislabels a *different session's* sidebar. Two SDD controllers running concurrently would overwrite
each other's status, and a non-cmux invocation would scribble on whatever the user happened to have
selected. Belt and braces required: **gate on `$CMUX_WORKSPACE_ID` being set, AND pass
`--workspace "$CMUX_WORKSPACE_ID"` explicitly.**

#### Cost

54–55 ms per call, measured. Two calls ≈ **110 ms added to every implementer dispatch**. Acceptable,
but not free — background them (`&`) if the hook's latency budget is tight.

#### Where it belongs: **both, different fields**

The clean split follows the data, not preference:

- **The hook** owns context/progress. `sdd-pre-dispatch-hook.sh` is the only place the controller's
  token count exists (`context-probe.py`), and it already knows `SOFT`/`HARD` and the task number.
- **The spawn script** owns hop. `spawn-handoff-session.sh` is the only place `SP_HOP` and `MAX_HOPS`
  exist.

Neither can write the other's field without plumbing that does not exist. Do not centralize.

#### Diff sketch — hook side (`sdd-pre-dispatch-hook.sh`, context gate, after `$CTX_TOKENS` resolves)

```bash
# --- Sidebar telemetry (cosmetic; MUST never affect the gate decision) -------
# Gated on CMUX_WORKSPACE_ID *and* passed --workspace explicitly: with the env
# stripped, `cmux set-status` still returns OK/exit 0 and writes to the SELECTED
# workspace — silently mislabelling a different session's sidebar. Verified
# 2026-07-28. Backgrounded: each call measured ~55 ms.
sdd_sidebar_telemetry() {
  [ -n "$CMUX_WORKSPACE_ID" ] || return 0
  command -v cmux >/dev/null 2>&1 || return 0
  local frac tier_color
  frac="$(awk "BEGIN{f=$CTX_TOKENS/$CTX_HARD; if(f>1)f=1; printf \"%.3f\", f}")"
  case "$CTX_TIER" in
    hard) tier_color="#ff3b30" ;;
    soft) tier_color="#ff9500" ;;
    *)    tier_color="#34c759" ;;
  esac
  {
    cmux set-progress "$frac" --label "ctx $((CTX_TOKENS/1000))k/$((CTX_HARD/1000))k" \
         --workspace "$CMUX_WORKSPACE_ID" >/dev/null 2>&1
    cmux set-status sdd_ctx "$CTX_TIER" --icon sparkle --color "$tier_color" --priority 80 \
         --workspace "$CMUX_WORKSPACE_ID" >/dev/null 2>&1
    cmux set-status sdd_task "$TASK_NUM" --icon hammer --priority 70 \
         --workspace "$CMUX_WORKSPACE_ID" >/dev/null 2>&1
  } &
  return 0
}
sdd_sidebar_telemetry     # unconditional `return 0`; the gate decision is unchanged
```

Key properties: `return 0` on every path; the whole block backgrounded; `>/dev/null 2>&1` on each
call; unique `sdd_*` keys so we never collide with another tool's pills (per `set-status --help`).
`sdd_ctx` doubles as the fastest possible answer to "why did it block?"

#### Diff sketch — spawn-script side (`spawn-handoff-session.sh`, after the hop-limit check)

```bash
if [ -n "$CMUX_WORKSPACE_ID" ]; then
  cmux set-status sdd_hop "$SP_HOP/$MAX_HOPS" --priority 60 \
       --workspace "$CMUX_WORKSPACE_ID" >/dev/null 2>&1 || true
fi
```

`|| true` is genuinely sufficient *here*: the script has already proven reachability with
`cmux ping` (`:122`) and refuses at `:125` otherwise, so `CMUX_WORKSPACE_ID` is known-good by this
point. The hook has no such precondition, which is why it needs the stricter form.

#### Failure modes, enumerated

| Condition | Behavior | Handled by |
|---|---|---|
| Not in cmux (`CMUX_WORKSPACE_ID` unset) | Would write to the **selected** workspace, `OK`/exit 0 | Explicit env gate — **the load-bearing guard** |
| `cmux` not on `PATH` | exit 127, `command not found` on stderr | `command -v cmux` gate + `2>/dev/null` |
| cmux app not running / socket dead | Non-zero, message on stderr | `>/dev/null 2>&1`, backgrounded, `return 0` |
| Two SDD controllers concurrently | Each writes its **own** workspace | Explicit `--workspace` |
| Stale pills after a session ends | Persist until cleared | Add `clear-status sdd_*` to the SDD completion path |
| Telemetry call hangs | Backgrounded — hook does not block | `&` |

#### One constraint the brief does not state

`sdd-pre-dispatch-hook.sh` is **one of the 7 baselined hooks**. Any change to it must re-capture the
integrity baseline in the same commit (`bash tests/ARaymond-hook-baseline/check-hooks.sh --capture`,
commit `tests/ARaymond-hook-baseline/baseline.txt`) or `check-hooks.sh` goes red. `spawn-handoff-session.sh`
is **not** a hook and needs no re-capture. The proposed row below says so explicitly.

---

## 4. Addendum — surface-per-session topology, EXERCISED *(a-run, 2026-07-28)*

**Raised by the user after the matrix was delivered:** *"we could spawn the left-channel workspaces
only … the top tab UI 'surfaces' were not capable of being spawned directly and interacted with"* —
against a working model of **repo = one left-sidebar workspace, each agent session = a top tab inside
it**. The question asked whether that had been *exercised*.

**It had not.** §1 classified `new-surface` as considered-and-rejected and `respawn-pane` / `send` /
`send-key` as **a-help**. The claim in §2 that N57's blockers were "largely dissolved" was an
inference from help text. This addendum discharges it with commands.

### The chain, end to end

All against `cmux 0.64.20`, in a throwaway workspace created and closed by this probe.

| # | Command | Result |
|---|---|---|
| 1 | `cmux new-workspace --name PROBE-surface-model --cwd /tmp --focus false` | `OK workspace:19` |
| 2 | `cmux new-surface --workspace workspace:19 --type terminal --working-directory /tmp --focus false` | **`OK surface:43 pane:19 workspace:19`** — richer than `new-workspace`'s `OK <ref>`; carries pane and workspace too |
| 3 | `cmux list-panes --workspace workspace:19` | **`pane:19 [2 surfaces]`** — the new surface joined the SAME pane, i.e. it is a **top tab, not a split** |
| 4 | `cmux respawn-pane --workspace workspace:19 --surface surface:44 --command "echo PROBE_MARKER_BETA; cmux wait-for -S $TOK; sleep 300"` | `OK`, exit 0 — command ran in the existing surface |
| 5 | parent: `cmux wait-for $TOK --timeout 25` | **`PARENT-WAIT-EXIT=0`** — reproduced twice. Closed-loop handshake INTO A SURFACE confirmed |
| 6 | `cmux read-screen --workspace workspace:19 --surface surface:44` | returned `PROBE_MARKER_BETA` **from an unfocused background workspace** |
| 7 | `cmux send --workspace workspace:19 --surface surface:45 "echo SEND_MARKER_GAMMA\n"` | `OK surface:45 workspace:19`; `read-screen` then showed the echoed marker — `\n` submits |
| 8 | `cmux close-workspace --workspace workspace:19` | `OK`; `list-workspaces` shows no residue |

**Verdict: the surface-per-session topology is fully achievable.** `new-surface`'s missing `--command`
is not a wall — `respawn-pane` or `send` drives the surface after creation, and `wait-for` removes the
readiness race that made that two-step look unsafe.

### Two behaviors invisible from `--help`, found only by running it

**(a) `respawn-pane --command` destroys the surface when the command exits.** The first probe used a
short-lived command (`echo …; cmux wait-for -S $TOK`). The token fired and the parent unblocked —
**and then `surface:43` vanished**; `read-screen` returned `Error: not_found: Surface not found`, and
`list-pane-surfaces` showed only the original. Re-running with a trailing `sleep 300` kept the surface
alive. Consistent with the gap analysis's incidental workspace finding ("a spawned workspace whose
command terminates does not linger") — it holds for surfaces too.

*Implication:* harmless for a real `claude-picker` launch (Claude runs indefinitely), but a launch that
fails fast **leaves no tab to inspect** — the diagnostic evidence deletes itself. An exit ladder cannot
rely on post-mortem surface inspection; it needs the handshake.

**(b) A cold surface has no readable terminal — `read-screen` errors until something drives it.**

```
new-surface → (nothing sent) → read-screen  → Error: internal_error: Failed to read terminal text
same on the workspace's own original surface → Error: internal_error: Failed to read terminal text
after `cmux send` into it                    → reads fine
the respawn-driven surface                   → reads fine
```

`surface-health` reports `in_window=false` for **both** readable and unreadable surfaces, so it does
**not** predict this. The terminal appears to be instantiated lazily on first input.

*Implication — this quietly vindicates `wait-for` over screen-scraping.* A liveness check built on
`read-screen` polling would return `internal_error` on precisely the case it exists to detect (created
but never started), and an implementer would plausibly treat that as transient and retry. `wait-for`
has no such blind spot: the token fires or times out, and both outcomes are unambiguous.

### 4.1 Trial run — the PRODUCTION launch path in a tab *(a-run, 2026-07-29)*

The probe above drove surfaces with toy commands (`echo`, `sleep`). At the user's request the same
chain was then run with the **real** launch path — `claude-picker` — in a tab of the caller's own
workspace, driven entirely from the parent session.

| Step | Command | Result |
|---|---|---|
| Tab in the **caller's** workspace | `cmux new-surface --workspace $CMUX_WORKSPACE_ID --type terminal --working-directory <repo> --focus false` | `OK surface:46 pane:17 workspace:17` — same pane as the parent, i.e. a sibling tab |
| Label it | `cmux rename-tab --surface surface:46 "DEMO haiku"` | `OK action=rename tab=tab:46 workspace=workspace:17` |
| **Launch the real picker** | `cmux send --surface surface:46 "claude-picker --non-interactive --pick-version 2.1.220 --telemetry off --session-label demo-haiku\n"` | **Claude Code v2.1.220 live in ~3 s** |
| Drive its TUI | `cmux send … "/model haiku"` then `cmux send-key … Enter` | `Set model to Haiku 4.5` |
| Ask + read back | `send` + `send-key Enter`, then `cmux read-screen --surface surface:46 --scrollback --lines 60` | full multi-sentence answer recovered from an **unfocused background tab** |
| Close | `cmux close-surface --surface surface:46` | tab gone (`list-pane-surfaces` shows only the parent) |

`--focus false` held throughout — the tab never stole focus from the parent, confirming the fork
convention is honored at surface level as well as workspace level.

**This upgrades N73's evidence from "surfaces are drivable" to "the shipped launch command works in a
tab."** It is the closest thing to a live rehearsal of the N73 topology short of a real HARD-block hop.

#### Design consequence: prefer `send` over `respawn-pane` for the launch

The trial used `cmux send` to start the picker; the §4 probe used `respawn-pane --command`. **They
differ in a way that matters, and `send` is the better choice** — which inverts the natural reading of
§4, where `respawn-pane` looks like the purpose-built tool:

| | `respawn-pane --command <cmd>` | `cmux send "<cmd>\n"` |
|---|---|---|
| Mechanism | Replaces the surface's process with `<cmd>` | Types into the surface's existing shell |
| When `<cmd>` exits | **Surface is destroyed** (§4 caveat (a)) | Shell survives; **the tab stays open with the error on screen** |
| Post-mortem | Nothing to inspect | `read-screen` still works |

Caveat (a) of §4 says a fast-failing launch under `respawn-pane` deletes its own evidence. **`send`
does not have that problem** — the shell outlives the failed command, so a picker that dies on a bad
`--pick-version` leaves a readable tab. For a launcher whose entire failure story is "we could not see
what happened," that is decisive. `respawn-pane` remains the right tool for *replacing* a surface's
process; it is the wrong tool for *starting a session you may need to debug*.

#### The TUI hazard, reproduced live

The trial needed **seven** sends where four were planned. Two unplanned obstacles, both invisible from
`--help`:

1. `/model opus` resolved to plain **Opus 5**, not the **Opus 5 (1M context)** the session started on
   — a silently wrong result that only a banner diff caught.
2. The switch raised a blocking confirmation — `Switch model? ❯ 1. Yes … 2. No` — that consumed input
   until answered.

**This is N56's directory-trust-modal failure mode, reproduced.** A session sitting on a modal while
every outward signal reads success. It also sharpens the argument against screen-pattern liveness
checks: a `read-screen` poll would have seen a plausible, populated, entirely normal-looking screen at
the moment the session was blocked. The `wait-for` token cannot be fooled that way, because the child
signals only *after* the work runs.

*(Operational note, not a cmux finding: `/model <name>` writes the **global** default — "saved as your
default for new sessions". The menu's `s` key — "use this session only" — is the correct key for a
throwaway session. The trial's change was reverted and verified against the launch banner.)*

### 4.2 `OK <ref>` is not uniform across commands *(a-run)*

`spawn_claude_workspace()` parses cmux's stdout with `awk '/^OK[ \t]/{print $2; exit}'` (`:419`),
which is correct for `new-workspace` (`OK workspace:8`). The surface commands are **not** consistent
with it:

| Command | `OK` line | Field 2 is… |
|---|---|---|
| `new-workspace` | `OK workspace:19` | the created workspace ✓ |
| `new-surface` | `OK surface:43 pane:19 workspace:19` | the created surface ✓ — **but two more refs follow** |
| `rename-tab` | `OK action=rename tab=tab:46 workspace=workspace:17` | `action=rename` — **a key=value pair, not a ref** |
| `close-surface` | `OK surface:47` (when closing `surface:46`) | **not the surface acted on** |

Any N73 implementation that reuses the existing parser must re-derive which field it wants per
command rather than assuming field 2 generalizes. The `close-surface` case is the dangerous one: it
returns a well-formed ref that is simply the wrong one, so a naive parser gets a plausible value and
no error.

### What this does to N57

N57's stated blockers are now empirically dead, and its *recommendation* is now the weaker option:

- N57 proposes `new-workspace --group` as the "cheap middle path" **because surfaces looked blocked.**
  They are not blocked. The premise for preferring groups is gone.
- Groups additionally carry the anchor lifecycle dependency documented in §2.11 — closing the anchor
  dissolves the group. The surface model has no equivalent coupling.
- **The one real cost N57 names still stands, unchanged:** `SPAWN_WORKSPACE_REF`, the `workspace=`
  field pinned by spec §5.4d, e2e Step 14 and CLAUDE.md all speak "workspace". That is schema, test and
  doc churn — mechanical, not architectural.

Carried as proposed row **N73**.

---

## 5. Community prior art — all **c-2nd** (unverified; README summaries, repos unread)

Per the brief's instruction to resist recommending a dependency where a first-party command exists:

| Project | README claim | Assessment |
|---|---|---|
| `cmux-agent-toolkit` | "barrier-style sync primitives" | **Do not adopt.** This is almost certainly `wait-for`, which is first-party and already proven cross-workspace. N61 covers it. |
| `niaeee/cmux_skill` | 802-line IDLE/STALL/ERROR state machine | **Do not adopt wholesale.** A state machine inferring liveness from screen state is precisely what `wait-for` makes unnecessary. Possibly worth reading for its *taxonomy* of failure states — our exit ladder has no STALL rung. |
| `owizdom/context-brdige-for-cmux` | "cold-start context injection via briefing handoff" | **Worth reading — the only one I would spend time on.** It is N43(D) by another name; a different design for the same problem is useful even if we adopt nothing. Note the typo'd repo name is the README's. |
| `hummer98/using-cmux` | "the complete orchestrator reference" | **Low priority.** Our authoritative reference is `cmux --help`; a community orchestrator doc ranks below it by the fork's own rule. |

**Net recommendation: read one repo (`context-brdige`), depend on none.** Everything the other three
advertise is already in the binary.

> **RETRACTED 2026-07-29 — "depend on none" holds; "read one repo" was wrong, and this section's
> method was the error it warns against elsewhere.** `umitaltintas/cmux-agent-toolkit` was read in
> full on 2026-07-29 (0 stars; created and last updated 2026-03-05, a single day; its "confirmed
> through testing (March 2025)" predates its own repo by ~12 months). **The c-2nd guess was correct
> on the narrow point** — "barrier-style sync primitives" is verbatim `cmux wait-for`. **But three of
> its behavioral claims are contradicted by our own a-run observations on 0.64.20**, each in a place
> that would have broken our code: it says `new-workspace` returns *"a UUID, not a ref"* (we observe
> `OK workspace:19`, which our spawn parser depends on); that surfaces in non-selected workspaces
> *"will reject `send`"* and you *"MUST `select-workspace`"* first (§4 sent to and read from an
> unfocused background workspace without ever selecting it); and it uses `pipe-pane` for continuous
> monitoring (§2.5 proved one-shot). **And yet reading it surfaced `cmux claude-hook`** — a hidden,
> fully-functional first-party command that this document's own 127-command enumeration, all four
> vendored skills, and both analysis docs missed (see **N68**, **N72**). Community repos are
> unreliable as *contracts* and valuable as *pointers*: their wrong claims cost nothing when the
> binary is the authority, and their right ones can name surface no enumeration finds. **Correct
> posture: verify everything, dismiss nothing.** Ranking a repo by its README blurb — which is what
> produced this section — is the same category error the rest of this document exists to correct.

---

## 6. Proposed BACKLOG rows

> **SUPERSEDED 2026-07-29 — these rows were APPLIED to `BACKLOG.md` (commit `cf1fb65`), which is now
> the single source of truth for them. The block below is preserved as the historical proposal; do not
> edit it and do not paste from it.** Two rows have already diverged: **N68** and **N72** were amended
> at apply time for the `cmux claude-hook` discovery, and **N72** gained a *third* axis afterwards
> (release-channel watching) when `Fork Conversation` turned out to have no programmatic surface at all
> — see **N75**. Read the live rows in `BACKLOG.md`.

**Originally NOT applied** — `BACKLOG.md` was owned by another session at the time of writing.
Copy-paste ready, matching the file's column format.

> **Renumbered N62–N69 → N66–N73 on 2026-07-29 to avoid a real ID collision.** These rows were drafted
> as N62–N69 per the original brief. While this document was being written, the concurrent session
> committed `b5e56e5` ("docs(cmux): capability audit — correct N56/N57's false premise, add N60–N65"),
> which claimed **N62** (`.active-feature` unchecked path authority), **N63** (unchecked post-spawn
> `outcome` writes), **N64** (protocol-vs-dirty-tree contradiction) and **N65** (ship the cmux
> transport for `/handoff-review`) for entirely different content. Highest ID in `BACKLOG.md` at
> renumber time: **N65**. Cross-references inside these rows were remapped with them — but verify
> against the live file before pasting, since that session may have continued.
>
> **One overlap is worth knowing about:** their **N65** — "ship the cmux transport for
> `/handoff-review` into the handoff toolkit" — is the same work as the amended handoff bundle
> `2026-07-29T02-01-24Z-claude-codex-handoff`. **N73** below (surface topology) and that bundle's
> amended recipe are the same decision seen from two repos; whoever picks up either should read both.

```markdown
| N66 | Sidebar telemetry: surface SDD context pressure, task and hop in the cmux sidebar | N60 capability audit 2026-07-28 (quick win (a) named in N60's notes) | quality, friction | S | open | **The 300k/400k context thresholds are invisible folklore today; this makes them a live gauge.** Design + measurements: `docs/process-improvement-findings/2026-07-28-cmux-capability-usage-matrix.md` §3 Q2 (diff sketches for both sites). **Split by data ownership, not preference:** the **hook** (`sdd-pre-dispatch-hook.sh`) owns `set-progress <ctx/HARD> --label` + `set-status sdd_ctx <tier>` + `sdd_task <N>` — it is the only place the token count exists; the **spawn script** owns `set-status sdd_hop "$SP_HOP/$MAX_HOPS"` — the only place those exist. **The load-bearing guard is NOT `\|\| true`:** measured 2026-07-28, with the cmux env stripped `cmux set-status x y` returns **`OK`, exit 0** and writes to the **selected** workspace (landed on `workspace:2` "Superpowers", not the caller's `workspace:17`). It never errors — it silently mislabels ANOTHER session's sidebar, and two concurrent controllers would overwrite each other. So: gate on `[ -n "$CMUX_WORKSPACE_ID" ]` **and** pass `--workspace "$CMUX_WORKSPACE_ID"` explicitly. Only a missing `cmux` binary actually fails (exit 127). **Cost:** 54–55 ms per call measured → ~110 ms per dispatch; background the block. Use unique `sdd_*` keys (`set-status --help` documents keys as the anti-collision mechanism). Add `clear-status sdd_*` to the SDD completion path or pills go stale. **Ship with:** `check-hooks.sh --capture` in the SAME commit — `sdd-pre-dispatch-hook.sh` is one of the 7 baselined hooks (the spawn script is not, and needs no re-capture). Cosmetic only: nothing may gate on a status write. |
| N67 | Use `cmux new-workspace --env` to carry successor state instead of the composed command string | N60 capability audit 2026-07-28 | quality, friction | S–M | open | **The one finding that SUBTRACTS shipped code rather than adding surface.** `cmux new-workspace --help` on 0.64.20 exposes **`--env KEY=VALUE` (repeatable) and `--env-file <path>`** — **both ABSENT from the top-level `cmux --help` summary line for the same command** (which reads `new-workspace [--name] [--description] [--cwd] [--command] [--layout] [--window] [--focus] [--group] [--group-placement] [--group-reference]` — the two `--env*` flags and only those are missing), which is why the design never saw them (confidence: a-help, read from the installed binary; **not exercised — probe before building**). Today `spawn-handoff-session.sh` forces ALL successor state through one composed shell string: the v1 base64 argv codec (`:222-264`), `shlex.quote` re-quoting of every element (`:333`), the `printf`-not-`echo` xpg_echo workaround (`:347`), and base64 append-prompt rematerialization. A shell re-parses that string in the spawned workspace — hence the quoting machinery. `--env` is a second channel needing none of it: hop number, `$SPAWN_ID`, and `SUPERPOWERS_CMUX_*` overrides could ride as env vars. **Scope honestly:** the append-prompt is CONTENT, not a scalar, so `--env` does not obviously replace rematerialization (`--env-file` may — probe it); reserved `CMUX_*` names cannot be overridden. Also unexamined on the same command, though this one WAS in the top-level summary and so is a plain miss rather than a discovery gap: **`--layout <json>`, whose "Layout surfaces define their own commands"** partially dissolves N57's "`new-surface` has no `--command`". Full detail: `2026-07-28-cmux-capability-usage-matrix.md` §2.7. |
| N68 | Decide the cmux Claude-wrapper posture: picker launches bypass it, and the channel is thinner than it looks | N60 capability audit 2026-07-28 (answers N60's "is a cmux-side lifecycle channel already live?") | quality | S (decide) / M (adopt) | open | **Answer to the question N60 posed: the channel is real and live — but our sessions are not on it, and its Claude ceiling is two events per session.** Evidence: `2026-07-28-cmux-capability-usage-matrix.md` §3 Q1. **(1) The wrapper exists:** `which -a claude` resolves FIRST to a cmux shim (`/var/folders/…/cmux-cli-shims/<uuid>/claude`) that `exec`s `/Applications/cmux.app/Contents/Resources/bin/cmux-claude-wrapper`. **(2) It injects hooks by MERGING SETTINGS** — the wrapper's own strings show `CMUX_BASE_SETTINGS="$HOOKS_JSON"`, `CMUX_USER_SETTINGS+=("${arg#--settings=}")`, `export CLAUDE_CONFIG_DIR=…`, and the failure string `cmux: warning: --settings merge failed; your --settings was ignored`. **(3) We bypass it, two independent proofs:** *code-verified* — `claude-picker` never resolves `claude` via PATH; all three launch paths (`:324`, `:435`, `:442`) `exec caffeinate -i "$binary"` where `$binary` is an absolute `$VERSIONS_DIR/<version>`, so the shim is unreachable BY CONSTRUCTION; *live-verified* — this direct-version-binary session emitted ZERO agent events (session id absent from the retained log; a 15s live `cmux events --category agent` stream during active tool use captured 0 lines; `latest_seq` advanced only 9894→9896). **(4) The prize is small:** of 56 claude-sourced events across 7 sessions, the ONLY hook events are `SessionStart`/`SessionEnd` — no `PreToolUse`, no `Stop`, `tool_name: null`. Codex emits all six because `cmux hooks codex install` exists; Claude has no equivalent. So the channel CANNOT serve `sdd-pre-dispatch-hook.sh`, which needs per-dispatch granularity it already gets from `context-probe.py`. **⚠ Before anyone proposes "just route through the shim":** this fork's ENTIRE enforcement layer lives in `~/.claude/settings.json` (7 scripts pinned by sha256 in `tests/ARaymond-hook-baseline/baseline.txt`). Adopting the wrapper puts a third-party settings-merge in front of it, with a documented mode where your `--settings` is silently dropped. That is a hook-composition change needing its own test plan, NOT a free upgrade. **Recommended disposition: accept the bypass, record why, and coordinate by PUSHING to cmux (N66) rather than pulling from it.** Also verified: `~/.claude/settings.json` has zero cmux references; no cmux-generated Claude config exists; `cmux set-hook --list` → "No hooks configured" (a second, entirely unused lifecycle channel). **AMENDED 2026-07-29 — `cmux claude-hook` is a first-party PUSH entrypoint this row did not know about, and it upgrades the recommendation from "push cosmetics" to "push real lifecycle".** Verified a-run on 0.64.20: `cmux claude-hook --help` → *"Hook for Claude Code integration. Reads JSON from stdin"*, with **seven** subcommands — `session-start`, `active`, `stop`, `idle`, `notification`, `notify`, `prompt-submit` — plus `--workspace`/`--surface`. It is **hidden from `cmux --help`** (not among the 127 this audit enumerated), **absent from all four vendored skills**, and **present in `docs/cli-contract.md`** (lines 160, 371 — where `hooks claude <event>` is named the canonical form and `claude-hook` "remains as the main-compatibility alias"). **What changes:** this row's "the prize is small" holds for what the wrapper *emits* (SessionStart/SessionEnd, `tool_name: null`) but NOT for what we can *send*. Our own `settings.json` hooks — which already fire on exactly these moments — can `echo '<json>' \| cmux claude-hook prompt-submit` etc., giving cmux real SDD lifecycle signal **with no wrapper adoption, and therefore none of the settings-merge risk this row flags as its blocker.** The wrapper decision and the push decision are now independent; only the wrapper one carries the enforcement-layer hazard. **Do NOT treat this as free:** it is unexercised beyond `--help` (a-help for behavior, a-run for existence), the stdin JSON schema is undocumented outside the wrapper, and per this fork's rule a hidden command may change without notice — so probe it, and pin what you observe. Discovery provenance worth recording: it surfaced from reading an unmaintained 0-star community repo (`umitaltintas/cmux-agent-toolkit`) that this document's §5 recommended NOT reading — see the amendment to **N72**. |
| N69 | N57's workspace-group premise is settled — `cmux workspace-group` exists with full CRUD, and anchors have a lifecycle catch | N60 capability audit 2026-07-28 | quality | XS (amend N57) | open | **Amends N57, which currently says "how workspace **groups** are created/referenced [is] genuinely unverified — `list-workspace-groups` is confirmed ABSENT".** `list-workspace-groups` is indeed absent; **the functionality is not** — it lives under a different name, reachable as `cmux workspace group <sub>` or `cmux workspace-group <sub>`, with 17 operations: `list [--json]`, `create [--name] [--cwd] [--from <id>,…]`, `ungroup`, `delete`, `rename`, `collapse`, `expand`, `pin`, `unpin`, `add`, `remove`, `set-anchor`, `new-workspace <group> [--placement]`, `set-color`, `set-icon`, `move`, `focus`. Verified a-run: `cmux workspace group list` → `No groups`, exit 0; all 17 mirrored in `cmux capabilities` as `workspace.group.*`. **This is the SECOND instance of the same error class as `read-screen`** — a capability declared absent on the strength of one guessed command name when the real name was one `--help` away. Two instances is a pattern (see N72). **New design constraint N57 does not mention: anchor semantics are load-bearing.** `--help`: *"Each group is owned by an 'anchor' workspace; the group header IS the anchor's sidebar representation. Closing the anchor dissolves the group while preserving its other members."* So grouping a successor chain under its parent creates a lifecycle dependency — closing hop 1 dissolves the grouping for hops 2–3. Detail: `2026-07-28-cmux-capability-usage-matrix.md` §2.11. |
| N70 | Migrate the spawn script off cmux's deprecated legacy workspace verbs | N60 capability audit 2026-07-28 | quality | XS | open | **The fork already hit this deprecation and suppressed the symptom without recording the fix.** `cmux workspace --help`: *"Canonical noun for workspace operations. Legacy verbs (new-workspace, list-workspaces, close-workspace, rename-workspace, select-workspace) keep working and **print a one-time deprecation hint** pointing here."* `spawn-handoff-session.sh:414` calls `cmux new-workspace`, and `spawn_claude_workspace()` sets `CMUX_QUIET=1` (`:417`) specifically to silence that notice — the code comment even names the `new-workspace` → `workspace create` alias. Canonical form is `cmux workspace create` (same flags). **Not urgent** — `--help` says legacy verbs keep working — but it is one line, it is known now, and it becomes urgent on a cmux upgrade rather than at a time of our choosing. **Ship with:** the e2e Step 14 stub and `tests/unit/test_spawn_handoff.py` both assert on the literal `new-workspace`, so they change in the same commit. Not a baselined hook → no `check-hooks.sh --capture`. Also available on the canonical noun and unexamined: `workspace env`, `workspace loading <on\|off>`, `workspace status`, `workspace reconnect/disconnect`. |
| N71 | Mirror SDD plan checkboxes into the cmux per-workspace todo list | N60 capability audit 2026-07-28 | friction | S | open | **`cmux todo` is a per-workspace checklist explicitly designed to be agent-written, and SDD already has exactly the state it wants.** Verified a-run on 0.64.20: `add\|list\|check\|uncheck\|start\|edit\|rm\|clear\|set\|open`, `--state pending\|in-progress\|completed`, `--origin user\|agent`, 50-item cap, `--json`. The key subcommand is **`cmux todo set`**, which atomically replaces the whole list from a JSON array of `{text, state?, id?, origin?}` (inline or piped on stdin) and **preserves identity for items whose `id` matches** — so a controller can mirror plan state IDEMPOTENTLY rather than append-and-drift. `controller-checkpoint.py` already knows the task range and per-task completion. **Cost:** needs a JSON projection of plan state that does not exist yet; 50-item cap is a non-issue (plans run ~10–15 tasks). **Strictly cosmetic — nothing may gate on it**, same contract as N66. Pairs naturally with N66 (same "make SDD state visible in the sidebar" motivation, same never-fail discipline). Detail: `2026-07-28-cmux-capability-usage-matrix.md` §2.8. |
| N72 | Add a capability-drift guard so the cmux surface is re-enumerated, not re-guessed | N60 capability audit 2026-07-28 — the durable fix for the error class N60 identified | quality | S | open | **N60 named the root cause ("the rule existed; the enumeration never happened"); this is the mechanism that stops it recurring.** The audit found the error class has now occurred **twice**: `read-screen` declared nonexistent in N56, and workspace groups declared unverified in N57 — both refuted by one `--help` call. A third instance is a matter of time, because nothing re-runs the enumeration. **Proposal:** a checked-in snapshot of `cmux --help`'s command list plus a test that re-enumerates against the installed binary and FAILS on drift, reporting added/removed commands. Added commands are the signal that matters — they are exactly the "we didn't know it existed" case. **Design notes:** key on the top-level command list; record `cmux --version` in the snapshot (`0.64.20 (100) [14e3400b9]` at capture); **skip cleanly when `cmux` is absent** so the suite stays green off-cmux and in CI. **AMENDED 2026-07-29 — the original "top-level command list ONLY" design cannot detect the failure class this row exists to prevent, and the row half-spotted it.** Its own baseline note already concedes `workspace-group` is *"reachable but not listed at top level"* — so the motivating example is invisible to the proposed mechanism. **`cmux --help` is not a complete enumeration.** Three confirmed instances on 0.64.20: (1) `workspace-group` — a command absent from the list, reachable as `cmux workspace group` / `cmux workspace-group`; (2) `new-workspace --env` / `--env-file` — flags absent from the top-level summary line for a command that IS listed (see N67); (3) `cmux claude-hook` — a fully-functional 7-subcommand entrypoint absent from the list entirely (see N68). A snapshot diff of the 127 would have caught **none** of them, in either direction. **Required second axis: source divergence.** `docs/cli-contract.md` documents all three (`claude-hook` at :160/:371; `--env`/`--env-file` at :106/:236-239), so the guard must diff the **contract doc's** command/flag tables against `cmux --help` and **treat any name the contract mentions but the help omits as a hidden-surface finding** — that is the signal, and it is mechanically checkable. Add a small probe list of known-hidden names (`workspace-group`, `claude-hook`) asserted to still resolve via `cmux <name> --help`, so a silent removal is caught too. **Consequence for this whole document:** the headline "127 top-level commands" is a precise, reproducible count of what `--help` PRINTS, not of what cmux ACCEPTS — the denominator is a floor, and every percentage derived from it is optimistic. Provenance worth keeping: `claude-hook` was found by reading `umitaltintas/cmux-agent-toolkit`, the 0-star unmaintained repo §5 of this document assessed as "do not adopt" from its README alone. Three of that repo's behavioral claims ARE contradicted by our own a-run observations (it says `new-workspace` returns a UUID not a ref; that unfocused-workspace surfaces reject `send`; and it treats `pipe-pane` as a stream) — so "do not depend on it" was right, while **"do not read it" was wrong**, and §5's "read one repo, depend on none" should be retired in favor of "verify everything, dismiss nothing." **Baseline established by this audit: 127 top-level commands — 3 used, 4 considered-and-rejected (all 4 reasons now invalid), 120 unexamined** (plus `workspace-group`, reachable but not listed at top level — exactly the discovery gap that produced N69) (`2026-07-28-cmux-capability-usage-matrix.md` §1). **Related correction the audit produced, worth noting as evidence the guard is needed:** the gap-analysis doc describes `pipe-pane` as *"**Stream** pane text into a shell command"* (read from the top-level summary); exercised, it is a **one-shot capture** — 1751 bytes captured, zero growth over 5 further seconds of pane output. A category-(a-help) claim presented as behavior, made in the same document that corrected a category-(b) one. |
| N73 | Adopt surface-per-session topology (repo = workspace, each SDD session = a top tab) — EXERCISED, and it supersedes N57's group recommendation | user-raised 2026-07-28 during the N60 audit ("I put projects/repos in a dedicated workspace then independent work sessions in separate surfaces"); probe run same day | friction, quality | M | open | **N57 asks whether this topology is possible and recommends a workaround because it looked blocked. It is not blocked — the whole chain was EXERCISED against `cmux 0.64.20` on 2026-07-28.** Probe transcript: `docs/process-improvement-findings/2026-07-28-cmux-capability-usage-matrix.md` §4. **Proven, in order:** `cmux new-surface --workspace <ws> --type terminal --working-directory <path> --focus false` → `OK surface:43 pane:19 workspace:19` (a **richer** ref line than `new-workspace`'s, carrying pane + workspace); `cmux list-panes` → `pane:19 [2 surfaces]`, i.e. the surface joined the SAME pane and is therefore a **top tab, not a split** — the user's model exactly; `cmux respawn-pane --surface <ref> --command <cmd>` runs a command in the existing surface (`OK`, exit 0); a `cmux wait-for -S $TOK` inside that command released a parent blocked on `cmux wait-for $TOK --timeout 25` (**`PARENT-WAIT-EXIT=0`, reproduced twice**) — the closed-loop handshake works INTO A SURFACE; `cmux read-screen --workspace <ws> --surface <ref>` read the marker back from an **unfocused background** workspace; `cmux send --surface <ref> "…\n"` is an equivalent driver (`OK surface:45 workspace:19`). **Two behaviors invisible from `--help`, found only by running it — both must shape the implementation: (1) `respawn-pane --command` DESTROYS the surface when the command exits** (short-lived probe → `Error: not_found: Surface not found`; a trailing `sleep 300` kept it alive). Harmless for a real `claude-picker` launch (Claude runs indefinitely), but a fast-failing launch **leaves no tab to inspect** — the evidence deletes itself, so the exit ladder must rely on the handshake, not post-mortem inspection. **(2) A COLD surface has no readable terminal** — `read-screen` on a never-driven surface returns `internal_error: Failed to read terminal text` until something is sent to it; `surface-health` reports `in_window=false` for readable and unreadable surfaces alike, so it does NOT predict this. This **vindicates `wait-for` over screen-scraping**: a `read-screen` liveness poll would error on exactly the case it exists to detect and would plausibly be retried as transient. **Effect on N57: its blockers are empirically dead and its RECOMMENDATION is now the weaker option** — N57 proposes `new-workspace --group` as the cheap middle path *because surfaces looked blocked*, and groups additionally carry the anchor lifecycle coupling (closing the anchor dissolves the group, see N69) that the surface model does not have. **The one real cost N57 names still stands, unchanged and mechanical:** `SPAWN_WORKSPACE_REF`, the `workspace=` log field pinned by spec §5.4d, e2e Step 14 and CLAUDE.md all speak "workspace" — schema/test/doc churn, not architecture. **LIVE REHEARSAL 2026-07-29 (§4.1) — the SHIPPED launch command was run in a tab, not a toy command:** `cmux new-surface` into the caller's own workspace → `cmux rename-tab "DEMO haiku"` → `cmux send --surface <ref> "claude-picker --non-interactive --pick-version 2.1.220 --telemetry off --session-label demo-haiku\n"` → **Claude Code v2.1.220 live in ~3 s**, its TUI then driven (`send` + `send-key Enter`) and its output read back from an **unfocused background tab**, then `close-surface`. `--focus false` held; the tab never stole focus. **`rename-tab` is the mechanism for the incremented session numbering this topology implies** ("Session 2", "Session 3") — nothing else in the surface API names a tab. **DESIGN DECISION CHANGED BY THE REHEARSAL: use `cmux send`, NOT `respawn-pane`, to start the successor.** `respawn-pane` replaces the surface's process, so when the command exits **the surface is destroyed** and the failure evidence goes with it (caveat (1) above); `send` types into the surface's existing shell, so a picker that dies on a bad `--pick-version` **leaves the tab open with the error readable via `read-screen`**. For a launcher whose entire failure story is "we could not see what happened," that is decisive — `respawn-pane` is the right tool for replacing a process, the wrong one for starting a session you may need to debug. **Also required — the `OK <ref>` parser does NOT generalize (§4.2):** `spawn_claude_workspace()`'s `awk '/^OK[ \t]/{print $2}'` (`:419`) is correct for `new-workspace` (`OK workspace:19`) but `new-surface` returns `OK surface:43 pane:19 workspace:19` (three refs), `rename-tab` returns `OK action=rename tab=tab:46 …` (field 2 is a key=value pair, not a ref), and **`close-surface` returned `OK surface:47` when closing `surface:46` — a well-formed ref that is simply the wrong one**, so a naive parser gets a plausible value and no error. Re-derive the field per command. **Sequence after N61** (the `wait-for` handshake is a precondition for doing this safely, and both touch `spawn_claude_workspace()`). **Do NOT reach for `new-surface --type agent-session --provider claude`** — N57's warning stands: it bypasses `claude-picker` and discards version pinning, telemetry routing, session-label increment and append-prompt forwarding. Not a baselined hook → no `check-hooks.sh --capture`; but `tests/unit/test_spawn_handoff.py` and e2e Step 14 both assert the workspace vocabulary and change with it. |
| N74 | Session-label continuity across spawns is trapped in one SDD script — move label composition into the pickers so every consumer inherits it | user-raised 2026-07-29 ("carry forward the telemetry settings… continue the telemetry label… update the label indicating the type of invocation and the model provider, with a session increment") | quality, friction | M | open | **The forwarding mechanism ALREADY EXISTS and was built for exactly this; what is missing is that the COMPOSITION RULE lives in one file that only SDD can reach.** **What exists (verified against the installed scripts 2026-07-29):** `claude-picker:178-186` `_set_picker_env()` exports four vars — `CLAUDE_CODE_PICKER_{VERSION,LABEL,ARGS,APPEND_PROMPT}`; `codex-picker:213-216` mirrors them as `CODEX_PICKER_*`. **The `CLAUDE_CODE_*` prefix is load-bearing, not cosmetic** — `claude-picker:429` carries the comment *"OTEL_* does NOT survive Claude Code's subprocess env filter; CLAUDE_CODE_* (below) does"*, i.e. the prefix was chosen precisely so launch metadata reaches a spawned successor. Telemetry resource attrs are built by `_build_resource_attrs` (`claude-picker:63-71`): `project`, `branch`, **`launcher=claude-picker`**, `launch_id`, optional `label`, optional `sys_prompt_append{,_sha}`; `codex-picker:63,71` emits `launcher=codex-picker`. **CORRECTION TO THE ASK — provider is ALREADY a clean telemetry dimension** via `launcher=`; duplicating it into the label is redundant *for querying*. It is still defensible for HUMAN legibility (the label surfaces in the status line and in cmux tab names) — just do it knowing it duplicates an existing attribute. **The genuinely missing dimension is INVOCATION TYPE** (`review` \| `work` \| `sdd`), which is captured nowhere today and arguably belongs as a resource attr (`invocation=<type>`) *as well as* in the label. **THE GAP, precisely:** the increment rule exists in exactly ONE place — `spawn-handoff-session.sh:341-360` (at `b5e56e5`), an inline Python block; `grep` for the regex across `skills/` and `~/.local/bin/` returns that file alone. **Neither picker increments anything** — both take `--session-label` verbatim and only sanitize it (`claude-picker:254`, `codex-picker:342`). So SDD gets label continuity and every other consumer (the `claude-codex-handoff` toolkit, ad-hoc launches) gets none. Second, subtler gap: outside a picker-launched session the `*_PICKER_*` vars are simply ABSENT, so there is no label to continue — today that degrades correctly (empty ⇒ omit `--session-label`, `spawn-handoff-session.sh:395-398`) but the successor loses attribution entirely. **⚠ HARD CONSTRAINT — THE INCREMENT REGEX IS END-ANCHORED.** `re.search(r"-Session-(\\d+)$", raw)` (`:344`). Append ANY segment after `-Session-N` and the match fails, execution takes the `else` branch (`n=2`, `base=` the whole string), and `Foo-Session-3` becomes **`Foo-Session-3-codex-Session-2`** — the chain silently restarts at 2 and the label grows without bound on every hop. **Every new segment MUST be inserted BEFORE `-Session-N`**; target shape `<base>-<type>-<provider>-Session-<N>`. Two siblings: the charset filter strips anything outside `[A-Za-z0-9_.-]` (`:350`), and the 255-char ceiling (`:361`, `max(0, 255 - len(suffix))`) means each added segment eats the base's budget — that `max(0, …)` exists because a negative slice bound silently truncated the base from the RIGHT and leaked a middle fragment of the old label. **RECOMMENDED BOUNDARY — put composition in the PICKERS, not in either consumer.** `_set_picker_env` is already what WRITES `*_PICKER_LABEL`, so label semantics are already picker-owned, and repo-1 `telemetry-exp` owns `claude-picker` and its v1 forwarding contract under Decision 19. Moving it there: superpowers **deletes** its Python block (code subtracted, one less thing to drift), the handoff toolkit gets it FREE and never implements it, `codex-picker` gains parity in the same change, and the end-anchor rule is enforced in exactly one place. Callers supply only what the picker cannot know — the invocation type: e.g. `claude-picker --session-label-role review` composes `<base>-review-Session-<N+1>`. **⚠ DESIGN THIS DELIBERATELY — CHAINS CROSS PROVIDERS.** A Claude session dispatching a Codex reviewer READS `CLAUDE_CODE_PICKER_LABEL` and WRITES via `codex-picker --session-label`: **the picker that reads is not the picker that writes.** If increment lives in the pickers, each must also read the OTHER's label var (preferring its own) or the chain resets to `-Session-2` at every provider hop — the same silent failure as the end-anchor bug, arriving from a different direction. It cannot be fixed by collapsing to one shared variable name, because `CLAUDE_CODE_*` is mandatory on the Claude side for the subprocess-env-filter reason above. **SCOPE — three repos, three owners:** pickers in `telemetry-exp` (repo-1), existing logic in this fork, consumer in `claude-codex-handoff`. **Keep this OUT of the handoff toolkit's round-trip transport feature** (scoped 2026-07-29 as transport-only) — folding it in blurs a clean scope decision and spans an ownership boundary that feature does not cross. **Ship with:** a test that a label already ending `-Session-N` increments rather than restarting; a test that an added role/provider segment lands BEFORE `-Session-N`; a cross-provider chain test (claude→codex→claude preserves the counter); and the existing empty-label ⇒ omit-flag behavior pinned so attribution-less launches still work. Related: **N51** (codex-picker parity — already notes codex has no `--pick-version` and a picker-OWNED `--developer-instructions-file` rather than a passthrough, both of which the composition must respect). |
```

---

## Related

- `docs/process-improvement-findings/2026-07-28-cmux-cli-capability-gap-analysis.md` — the analysis
  that triggered this audit (and whose `pipe-pane` "stream" framing §2.5 corrects).
- BACKLOG **N60** (this deliverable), **N56** / **N57** (premises corrected — N69 amends N57 further),
  **N61** (`wait-for` handshake), **N58** (re-vendor decision), **N43(D)** (the integration audited).
- `docs/imp-plans/2026-07-22-cmux-integration/` — the feature's spec and deviations.
- CLAUDE.md § "cmux Auto-Spawn Handoff" and § "cmux documentation, versions, and which source wins".
