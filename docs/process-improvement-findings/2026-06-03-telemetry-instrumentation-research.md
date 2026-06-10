# Claude Code Telemetry — Instrumentation Research for the Superpowers Fork

**Date:** 2026-06-03
**Status:** Spike COMPLETE — tooling **extracted to a standalone repo**: `~/projects/claude-custom/telemetry-exp` (run `./start-capture.sh` → `./claude-telemetry` → `python3 analyze-capture.py`). First real capture done (accounts-dashboard `writing-plans`). This doc remains the *research + findings*; the *tool* now lives in that repo. (Note: the `~/.claude/otel/...` paths below are from the spike and were superseded by the repo.)
**Source:** `claude-code-guide` subagent, verified against current Anthropic docs (`code.claude.com/docs/en/monitoring-usage`)
**Driving question:** Can Claude Code's native OpenTelemetry support instrument a real superpowers skill execution well enough to answer Aaron's "gauges" — and is it the right layer vs. extending the existing `tests/claude-code/analyze-token-usage.py` `.jsonl` parser?

> This sits alongside the parallel LangChain/LangSmith evaluation. Both are candidate observability layers for the *same* goal. Key architectural fact: the superpowers fork is **not** a LangChain app, so LangSmith would see nothing natively. Claude Code telemetry (OTEL) and the `.jsonl` transcript are the layers that actually observe this system.

---

## The 6 gauges (measurement goals)

For any superpowers execution:
1. Which skills are invoked, **in what order**.
2. Which **tools** each skill runs, in what order.
3. **Token efficiency** per skill / per call / per chain.
4. What **errors** are encountered.
5. How often agents are **blocked by hooks/scripts**, and how blocks resolve.
6. Effect of **swapping the underlying model** on quality vs. speed.

---

## Verdict (read this first)

- **Telemetry is the right *native* instrument for gauges 2, 3, 6** (tool order, per-skill/per-model token + cost + latency, model comparison). It has real `skill.name`, `model`, `query_source`, and `agent_id` attributes on metrics/events/spans.
- **Gauge 5 (hook blocks) is INVISIBLE to telemetry.** A `PreToolUse` hook that denies a tool (exit 2) emits *no* event — the tool simply never produces a `tool_result`. Since the entire SDD enforcement system is hook gates, **this is the dealbreaker that forces a hybrid approach.** Hook-block auditing must come from `.jsonl` (`"decision": "reject"`).
- **Gauges 1 and 4 are partial in telemetry, complete in `.jsonl`.** No explicit "skill loaded" event (only fires when a skill *runs* a tool); telemetry sees API/tool errors but not hook/validation/script-stderr errors.
- **Recommendation: hybrid.** Telemetry for real-time metrics, traces, and model/cost comparison; extend `analyze-token-usage.py` for skill-load order, hook-block audit, and full error taxonomy.

### The one risk that could break per-skill attribution (verify FIRST)
Docs state: built-in / bundled / user-defined / official-marketplace skill names appear **verbatim** in `skill.name`, but **third-party plugin skill names are replaced with `"third-party"`**. The fork is **symlink-installed (custom), not a marketplace plugin** — so it *should* appear verbatim, but this is **unconfirmed**. If the fork's skills bucket as `"third-party"`, gauge 3 (per-skill token efficiency — arguably the #1 want) collapses for telemetry. **Spike checkpoint #1: confirm `skill.name` shows `brainstorming`, not `third-party`.**

---

## SPIKE RESULTS — empirical, Claude Code 2.1.161 (2026-06-03)

Ran telemetry to the **console exporter** (no collector) via two minimal headless `claude -p` probes (1s flush intervals; flushes cleanly on exit). All 4 checkpoints answered + 2 bonuses. *(Probe logs in `/tmp/otel-probe.log`, `/tmp/otel-skill-probe.log`; contain account IDs — local/ephemeral, not committed.)*

| # | Checkpoint | Result |
|---|---|---|
| 3 | `ttft_ms` present | ✅ `ttft_ms: 1794` on `llm_request` span. A **4-token** reply cost 1.85s total, **1.79s of it TTFT** → latency is **time-to-first-token-dominated**, near-independent of output size. Confirms: the cost is per-round-trip fixed latency. |
| 4 | `model` as a dimension | ✅ **Not anonymized.** `model: "claude-opus-4-8[1m]"` on `token.usage` + `cost.usage` metrics AND `llm_request` span, alongside `duration_ms`, `ttft_ms`, `cost_usd`, `effort` (e.g. `xhigh`), `speed`, cache tokens. **Opus-vs-Sonnet-as-reviewer (speed/cost) is fully supported.** |
| 2 | `blocked_on_user`/`tool.execution` spans | ✅ All emit: `claude_code.tool`, `.tool.execution`, `.tool.blocked_on_user`, `.tool_decision`, `.tool_result`. The compute-vs-permission-wait split the `.jsonl` can't do **is native here**. |
| 1 | skill name verbatim vs `third-party` | ⚠️ **SPLIT — workable, but not via metrics.** The **`token.usage`/`cost.usage` metrics and `api_request`/`llm_request` records anonymize to `skill.name:"third-party"` + `plugin.name:"third-party"`.** But the **`skill_activated` event** (`skill.name:"superpowers:using-superpowers"`, `invocation_trigger`, `skill.source`, `prompt.id`, `event.sequence`) and the **tool span** (`skill_name:"superpowers:using-superpowers"`, `duration_ms`) carry the **REAL name**. |

### What checkpoint 1's split means (important)
You **cannot** get free per-skill token/cost rollups from the metrics — every custom-fork skill collapses to `"third-party"` there (Anthropic anonymizes non-first-party plugin names in aggregated metrics). **But per-skill attribution is still achievable by correlation:** `skill_activated` events give *real skill name + timestamp + `prompt.id`*; request records give *model/duration/ttft/cost + `prompt.id`/`request_id`*. **Join on `prompt.id`/time-window** → per-skill cost & latency reconstructed locally. (This is the same correlation a `.jsonl` analyzer would do anyway.)

### Bonus 1 — `claude_code.active_time.total` (native idle-stripping)
Claude Code **itself** exports `active_time.total` ("Total active time in seconds", COUNTER). This is an **authoritative active-vs-idle number per session** — it replaces the crude 120s-gap heuristic the `.jsonl` probe used. Directly answers "execution time vs. session-left-open."

### Bonus 2 — hooks ARE instrumented (CORRECTS earlier doc-based claim)
The prior doc-research claim that "hook blocks are invisible to telemetry" is **empirically wrong for hook execution**. `claude_code.hook_execution_start`/`_complete` events carry `hook_event` (e.g. `PreToolUse`/`SessionStart`), `hook_name`, `num_hooks`, `num_success`, **`num_blocking`**, `num_non_blocking_error`. The `num_blocking` counter is a direct signal for **gauge 5 (how often agents are blocked by hooks)** — needs one interactive confirm with a real gate denial, but the field exists.

### Bonus 3 — subagents auto-inherit telemetry (NO skill changes needed)
A third probe dispatched a `general-purpose` subagent via the Task tool. Its activity emitted **30 records tagged `query_source:"subagent"` + `agent.name:"general-purpose"` + `agent_type` + `model`** — with **zero modification to any skill or prompt template.** Confirmed: superpowers dispatches subagents *in-process* (Task/Agent tool), not by spawning separate `claude` binaries, so the orchestrator + partner agents + implementer/reviewer subagents all share the **one** telemetry config set at the top-level launch. The whole execution tree appears in one trace, attributable per-subagent by `agent.name`/`query_source`. The `PreToolUse:Agent` hook fired (`hook_name:"PreToolUse:Agent"`) and passed the ad-hoc dispatch through. ⇒ **Telemetry is a launch-time, process-level concern — the skills never orchestrate it.**

### Data sink: where it lives & control
**No default file** — Claude Code emits nothing unless an exporter is configured; unconfigured = discarded. `console` → process stdout/stderr (ephemeral; persists only if redirected, as the probes did). `otlp` → network endpoint (`OTEL_EXPORTER_OTLP_ENDPOINT`, default `localhost:4317`) → needs a local **OTEL Collector** that you point at a local file / local TSDB — path fully under your control, all on localhost (satisfies [[no-cloud-exfiltration]]). This is **separate** from the session `.jsonl` transcripts, which auto-persist at `~/.claude/projects/...` (the source the free probe used). Enable via env at startup: per-session shell exports, OR a `settings(.local).json` `env` block (global or project-scoped) — cannot be toggled mid-session.

### Still needs an INTERACTIVE confirm (not blocking the verdict)
- A REAL permission prompt to see `blocked_on_user.duration_ms` > 0 (headless has no human to wait on, so it was ~0).
- A real SDD gate **denial** to confirm `num_blocking` increments on a block.

### Spike verdict
**Telemetry is viable and richer than expected.** It natively provides what the `.jsonl` can't: TTFT (inference vs network), true `tool.execution`/`blocked_on_user` timing, native `active_time`, model/effort/speed dimensions, and hook execution+blocking counts. The one limitation — skill names anonymized in metrics — is bypassed by correlating `skill_activated` events on `prompt.id`. **Recommended instrument: telemetry (events+traces) as primary for new runs; `.jsonl` for retroactive history.**

---

## Latency & reliability — PRIMARY concern (2026-06-03 follow-up research)

The driving question reframed from *token efficiency* to **time + reliability**: superpowers runs feel far too slow for the amount/quality of code produced, and API/connection-drop errors are rising. We need to decompose wall-clock and locate errors. Verified against `code.claude.com/docs/en/monitoring-usage`:

### Execution time vs. user-wait — telemetry separates this NATIVELY (with beta traces)
The earlier worry (that `duration_ms` would conflate human-wait with execution) is **resolved by the span tree itself**. A `claude_code.tool` span (`duration_ms` = *wall-clock incl. permission wait + execution*) has two child spans:
- **`claude_code.tool.blocked_on_user`** — `duration_ms` = time waiting for the permission decision.
- **`claude_code.tool.execution`** — `duration_ms` = time running the tool body.

So `tool = blocked_on_user + execution`, **measured directly** — no `.jsonl` subtraction needed for permission-wait. ⚠️ **This only exists with `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` (beta traces).** Without it, permission-wait is un-instrumented.
- `claude_code.llm_request.duration_ms` = *model+network round-trip incl. retries* (excludes human-wait); also carries **`ttft_ms`**, `input_tokens`, `output_tokens`.
- **Idle-between-turns** (user reading/typing between prompts) is **un-instrumented everywhere** — derive from `.jsonl` timestamp gaps between `interaction` spans. This is the one piece that *must* come from the transcript.

### Errors / connection drops / retries
- **`claude_code.api_error`** event fires **after retry exhaustion** (terminal), carrying `attempt=N` (total tries), `error` (message), `status_code` (absent for non-HTTP failures like connection drops).
- Each retry attempt also appears as a **`gen_ai.request.attempt`** span event (`attempt`, `client_request_id`) — **only with beta traces**. Without traces you see only the final `api_error`.
- **Connection drops are captured but NOT distinctly labeled** — no `status_code`; identify by `error` string pattern (confirm empirically).
- Whether the session `.jsonl` records errors/retries at all: **docs don't specify — verify empirically.** A `claude --debug` stderr capture may be the only durable record of transport drops; confirm in the spike.

### Latency attribution
`llm_request` span gives `ttft_ms` + `duration_ms` + `input_tokens` + `output_tokens`, so slowness is attributable to **(a) large prompt** (high `input_tokens`) and **(b) model** (compare same `query_source`). **(c) network vs. generation** is NOT cleanly separable without `ttft_ms` (⇒ beta traces required even to approximate it).

### Net effect on the spike design
**Beta traces (`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`) are now essential, not optional** — they unlock the `blocked_on_user`/`execution` split, per-retry events, and `ttft_ms`. Capture three streams in parallel: **OTEL traces+events+metrics** (timing, errors, retries, per-skill/model attribution), **`.jsonl` timestamps** (idle-between-turns + hook-block audit), and **`claude --debug` stderr** (candidate for connection-drop detail not in OTEL/`.jsonl`).

### FIRST EMPIRICAL CUT — `.jsonl` timing, zero setup (2026-06-03)
Before any telemetry, a read-only timing probe (`/tmp/jsonl_timing_probe.py`) was run against three real heavy superpowers sessions. **Transcripts carry reliable per-event ISO8601 timestamps** (checkpoint D1 ✓; permission-decision rows NOT found in the form checked — D2 still open). Decomposition (gaps bucketed by the event transition; HUMAN_IDLE = gap ≥120s before a human prompt):

| Session | raw span | HUMAN_IDLE | MODEL_GEN | TOOL_EXEC | SUBAGENT_EXEC |
|---|---|---|---|---|---|
| 2327df90 (May 29, SDD hooks) | 20.8h | **89%** | 1.23h (5.9%) | 0.22h / 140 calls (1%) | 0.35h / 4 |
| 02a7a511 (May 21) | 24.9h | **90%** | 0.97h (3.9%) | 0.12h / 299 calls (0.5%) | 0.51h / 23 |
| 3742d197 (suspend/resume outlier) | 23.8h | 27% | 0.66h | *10.06h ← suspend mislabeled* | 0.02h |

**Findings (robust on the two clean sessions):**
1. **~90% of a session's raw wall-clock is HUMAN_IDLE / session-left-open** — not compute. The felt "this took all day" is overwhelmingly idle, not execution.
2. Of the **~2.4h engine time**, the dominant active component is **MODEL_GEN (inference/output latency)**. **Tool execution is a rounding error** (~0.5–1.4s/call, ~1% of span across 140–299 calls). Hook blocks cost ~nothing in time. Subagent dispatch is modest (0.35–0.5h).
3. ⇒ **The bottleneck is sequential model round-trips, not tools/hooks/subagents.** Each skill step + each subagent turn + each review = another LLM call (n=350–540 MODEL_GEN events/session); those sum to the bulk of active time. Levers: **fewer sequential round-trips** and **right-size the model per step** (= gauge 6), NOT faster tools or fewer hooks.

**Hard limit of the `.jsonl` method (why telemetry is still needed):** it CANNOT distinguish "a tool/subagent genuinely ran N minutes" from "the laptop slept / session suspended mid-call." Session 3742d197 proves it — a single ~9.8h `assistant_tool→tool_result` gap was mislabeled TOOL_EXEC; it's almost certainly a suspend. Telemetry's `tool.execution` + `blocked_on_user` spans measure true on-process time and resolve this. And `.jsonl` can't split MODEL_GEN into inference-vs-network — that needs `ttft_ms`.

**⇒ The telemetry spike is now SHARPENED, not exploratory:** confirm (a) MODEL_GEN is inference (high `ttft_ms`/large `input_tokens`) vs network, and (b) the long ambiguous gaps are real subagent compute vs suspend — then attribute the MODEL_GEN bulk per-skill/per-model to find which superpowers steps force the most expensive round-trips.

### FIRST REAL CAPTURE — accounts-dashboard `writing-plans` (2026-06-03)
Live interactive capture via the local collector (tooling now in repo `~/projects/claude-custom/telemetry-exp`, analyzer `analyze-capture.py`). Confirms the interactive checkpoints (`blocked_on_user`>0, skill correlation) AND gives the first real diagnosis. Baseline + full report saved in the repo at `data/capture-2026-06-03-accounts-dashboard/`.

- **Scale:** 3.32 h wall-clock · 173 model round-trips · 202 tool calls · 2 interactions · **$34.85** · 0 errors / 0 retries / 0 hook blocks.
- **Time decomposition (verified via interaction-span timestamps):** the actual autonomous run = **interaction #1, 19:45→20:42 ≈ 57 min of NEAR-CONTINUOUS compute** (largest within-run gap between model calls ≈ 3 s — no stalls). Model generation totaled 3490 s / 58 min ≈ the whole of interaction #1 (main-thread Opus ~47 min, with subagent calls overlapping the Agent-tool waits). The **2.3 h "idle" is AFTER the work finished** (~20:45 → 23:04, session left open; `away_summary` fired meanwhile) — NOT a stall or a superpowers inefficiency. Non-Agent tool exec ~93 s; permission wait 70 s (human **17 s**/2 prompts). (`active_time.total`=338 s is a narrow harness-internal slice, not the denominator.) ⇒ Cleanly answers "separate wait from execution": execution ≈ 57 min solid; the rest is post-run idle.
- **Context-size signal (the round-trip multiplier):** 173 calls re-read **32.3 M cached-context tokens (~187 k/call)**. Every round-trip carries a ~187 k-token context, so "fewer sequential round-trips" and "smaller carried context" are the *same* lever; 173 × 187 k is what drives both the cache-read cost and the per-call latency floor.
- **Where the compute/cost goes (by `query_source`):** main thread (Opus) **2831 s / $27.80 (80%)** · general-purpose subagent (Opus) 333 s / $3.90 · **Explore subagent (Haiku) 315 s / $0.71** · `away_summary` (Opus) **1 call / $2.45 (7% of cost!)** · title 1 call / ~$0.
- **Cost is 98% Opus.** Superpowers **already** delegates codebase research to cheap Haiku (Explore ×68 = $0.71). The expensive center is **main-thread Opus reasoning/plan-writing**.
- **Latency shape:** median call 4.8 s, **Opus p90 79 s, slowest single call 7.4 min** (17.7 k-token plan-doc generations). TTFT = 44% of the median call → for these large-output calls the cost is **generation time**, not just TTFT (the trivial-probe TTFT-dominance flips when outputs are large).
- **Machinery is NOT the bottleneck (again):** hooks 0 blocks, permission wait 17 s, non-Agent tools ~93 s. The lever is model generation, specifically main-thread Opus.
- **Data-grounded levers:** (1) main-thread Opus plan-drafting ($27.80) — does drafting need Opus, or cheaper-draft + Opus-review? (2) `away_summary` = $2.45 for one auto-call when away — overhead worth questioning. (3) Explore-on-Haiku is already optimal — keep.

### Out of scope for this spike: code QUALITY
"How good is the code" is not a timing/telemetry signal. Quality would need a separate measure — e.g., review-rejection counts (in `.jsonl` hook decisions + report files), test pass rates, or rework deltas. Flagged so the spike isn't mistaken for a quality measurement.

### New empirical checkpoints (answer in the spike)
2. Does `claude_code.tool.blocked_on_user` actually appear for permission-gated tools in this setup?
3. What `error` string does a real connection drop produce (to build a detector)?
4. Do `.jsonl` entries carry reliable per-message timestamps, and do they record permission prompts / API errors?

---

## Capability matrix

| Gauge | Telemetry | `.jsonl` parsing | Best layer |
|---|---|---|---|
| 1. Skill invocation order | Partial — tool-execution order via timestamps; no "skill load" event | Full — transcript is ordered, skill invocations explicit | **.jsonl** |
| 2. Tools per skill, in order | Yes — `tool_result.tool_name` + `skill_name` (needs `OTEL_LOG_TOOL_DETAILS=1`) | Full | Either |
| 3. Token efficiency per skill | Yes — `token.usage` metric carries `skill.name` + `model` (⚠ cardinality risk above) | Full — `analyze-token-usage.py` already does per-subagent; extend for skill attribution | **Telemetry** (if names resolve) |
| 4. Errors | Partial — API + tool success/fail only | Full — incl. stderr, hook failures, permission denials | **Hybrid** |
| 5. Hook blocks / gate denials | **None** — blocked tools emit no event | Full — `"decision": "reject"` in tool entries | **.jsonl only** |
| 6. Model swap effect | Yes — `model` attr + latency (`duration_ms`, `ttft_ms`) per request | Partial — model in `message.model`, less structured | **Telemetry** |

---

## Enablement & scope (verified)

- Master switch: `CLAUDE_CODE_ENABLE_TELEMETRY=1` (off by default).
- Three independent signal exporters: `OTEL_METRICS_EXPORTER`, `OTEL_LOGS_EXPORTER`, `OTEL_TRACES_EXPORTER` (each `otlp|console|none`; metrics also `prometheus`).
- **Traces (the span hierarchy linking prompt → LLM calls → tools → subagents) require the beta flag** `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`.
- **Scoping:** global via `~/.claude/settings.json` `env`, OR per-project via `<project>/.claude/settings.json` `env`, OR per-session via `--settings '{...}'` (highest precedence). So a single superpowers run can be instrumented **without polluting all other Claude Code work**.
- **Not inherited by subprocesses:** Bash tool, hook scripts, and MCP servers do NOT get the OTEL env — only the Claude Code CLI emits telemetry.
- Export intervals: metrics 60s / logs 5s / traces 5s (all configurable; drop metrics to `OTEL_METRIC_EXPORT_INTERVAL=5000` for a short spike).

## What it emits (verified)
- **Metrics:** `claude_code.token.usage` (attrs `type`, `model`, `query_source` main/subagent, `agent.name`, `skill.name`), `claude_code.cost.usage`, `claude_code.session.count`, `lines_of_code.count`, `commit.count`, `code_edit_tool.decision` (Edit/Write/NotebookEdit only).
- **Events/logs:** `user_prompt`, `api_request` (`model`, tokens, `cost_usd`, `query_source`), `tool_result` (`tool_name`, `success`, `duration_ms`, `error_type`, `skill_name` — needs `OTEL_LOG_TOOL_DETAILS=1`). Correlate events via `prompt.id`.
- **Traces (beta):** root `claude_code.interaction` → `claude_code.llm_request` (model, tokens, `agent_id`, `parent_agent_id`) + `claude_code.tool` (`tool_name`, `skill_name`, `result_tokens`, `agent_id`) → nested subagent spans. Hook-execution spans only with detailed-beta tracing + allowlisting.

---

## Local-only spike recipe (no cloud — satisfies the exfiltration constraint)

All data stays on `localhost`; no SaaS (Honeycomb/Datadog/Grafana Cloud).

1. **Collector:** `brew install open-telemetry-contrib-collector` (or docker `otel/opentelemetry-collector-contrib`).
2. **Config** (`~/.claude/otel/collector-config.yaml`): OTLP receiver on `:4317`/`:4318` → `logging` (debug) + `file` exporter to `/tmp/claude-telemetry.jsonl`, pipelines for metrics/traces/logs.
3. **Run collector:** `otelcontribcol --config ~/.claude/otel/collector-config.yaml`.
4. **Enable in a scoped session** — project `.claude/settings.json` `env` (or exports) with:
   `CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`, `OTEL_EXPORTER_OTLP_PROTOCOL=grpc`, `OTEL_METRICS_EXPORTER=otlp`, `OTEL_LOGS_EXPORTER=otlp`, `OTEL_TRACES_EXPORTER=otlp`, `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`, `OTEL_METRIC_EXPORT_INTERVAL=5000`, `OTEL_LOG_TOOL_DETAILS=1`.
5. **Run a real execution** (e.g., a short brainstorming or a small SDD task) and `tail -f /tmp/claude-telemetry.jsonl | jq` to inspect: tools-in-order, tokens-by-skill, tokens-by-model.
6. **Cross-reference** the same run's session `.jsonl` (`~/.claude/projects/<encoded-path>/*.jsonl`) for the hook-block + skill-order data telemetry omits.

---

## Open questions (could not resolve from docs — answer empirically in the spike)
1. **Custom symlinked skill cardinality** — verbatim vs. `"third-party"` (checkpoint #1, see risk above).
2. Do subagents dispatched via the Agent tool each get their own traced spans + `agent_id`? (Span structure implies yes; unconfirmed.)
3. Are pending metric batches flushed on session end if it ends before the export window?
4. Telemetry has `agent_id` but no SDD "Task N" semantics — would need joining against `.sdd-session.json`.

---

## Suggested next steps
1. **Quick validation (~30 min):** stand up the local collector, instrument ONE brainstorming run, confirm checkpoint #1 (skill names resolve verbatim) + timestamp alignment vs `.jsonl`.
2. **Extend `analyze-token-usage.py` (~1–2 hr):** add skill-load order, hook-block detection (`decision: reject`), error taxonomy (API vs tool vs hook).
3. **Integration run (~1 hr):** one real multi-task SDD session with telemetry + extended parser; confirm the hybrid covers all 6 gauges.
4. **Decide:** hybrid (all 6, recommended) vs telemetry-only (loses gauge 5) vs `.jsonl`-only (no OTEL overhead).

## Sources
- https://code.claude.com/docs/en/monitoring-usage.md (metrics, events, traces, span hierarchy, scoping)
- https://code.claude.com/docs/en/settings (per-project / session env override)
- https://opentelemetry.io/docs/collector/ (local collector + file exporter)
