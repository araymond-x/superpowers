# Model Selection

> Part of the subagent-driven-development skill. Referenced from SKILL.md.

Use the least powerful model that can handle each role — but "powerful" has two independent dials. Tune both.

## Two dials

- **Capability** (the model tier): the floor of quality — latent judgment, code-generation fidelity, faithful instruction-following over long context. Buy it by picking a stronger model.
- **Reasoning effort** (thinking depth): how much the model deliberates before answering. A dial you turn up on *any* capable model, independent of tier.

**The rule that decides which dial to reach for:**

> **Effort substitutes for capability on _closed_ problems, not _open_ ones.**
>
> - **Closed** = the answer is fixed by material in front of the model; the work is *verification* (trace this data path, did every decision survive distillation, is a review missing from the trace). A cheaper model with more thinking gets there.
> - **Open** = the answer needs latent judgment the model either has or doesn't (is this the right decomposition, does this architecture smell wrong, what's the root cause). Effort can't manufacture taste — raise capability instead.

**Caveat:** the cheapest tier may not expose an effort dial at all. If a *closed* role needs more thinking than the cheap tier can give, move it up one tier to unlock the dial — don't jump straight to the top tier.

## Per-role defaults

Superpowers is an error funnel: mistakes at the front (design, plan) and at the adversarial gates (plan review, final review, root-cause) propagate into every downstream task; a mistake in one gate-backstopped task is caught immediately. Concentrate capability at the apex.

| Role | Profile | Capability | Effort |
|---|---|---|---|
| Design / brainstorming | Open | most-capable | high |
| Plan authoring (writing-plans) | Open | most-capable | high |
| Plan-document reviewer | Open | most-capable | high |
| **SDD controller (this loop)** | Open, sustained context | most-capable | med–high |
| Final code reviewer (pre-completion) | Open, highest-stakes | most-capable | high |
| Systematic-debugging root-cause (Phase 1–3) | Open | most-capable | high–max |
| Spec/quality review on contract, integration, or security tasks | Closed→open | standard–capable | high |
| Trace audit, distillation review, pre-execution audit | Closed | standard + effort | high |
| Controller-partner (6-item checklist verify) | Closed, checklist-bound | cheap | low–med |
| Implementer — well-specified 1–2 file task | Capability-floor (plan did the reasoning) | cheap | low |
| Implementer — integration / BLOCKED-needs-reasoning | Open-ish | standard→capable | med–high |
| Verification tasks, finishing-branch, routing | Closed / mechanical | cheap | low |
| Deterministic hooks & scripts | — | **no model** | — |

**Why the controller sits at the top:** it constructs every subagent prompt verbatim (Contract Constraints, Shared Constants, Pattern References passthroughs), routes statuses, declares review tiers, and catches escalations. Its errors propagate to every dispatch. It is capability-bound — faithful execution over long accumulating context — so a stronger model beats a cheaper-model-with-more-effort here. **Opus 4.8 is the strong half-price default:** its 4.8-specific gains (long-context handling, fewer compactions and post-compaction derailments, fewer skipped required tool calls) target the controller's exact failure modes. Reserve most-capable (Fable 5) for the hardest runs — multi-module, high-ambiguity; use `capable` + `high` otherwise.

**Cost:** the top-tier roles are a small fraction of total token volume (a handful of design/plan/review turns); the bulk is per-task implementer + reviewer turns. Paying the top tier only at the ~6 apex roles targets the funnel where a mistake multiplies, at low aggregate cost.

## Current model mapping (2026-07 — time-sensitive; verify via the `claude-api` skill)

| Tier | Model (API id) | Context | Effort dial? |
|---|---|---|---|
| cheap | Haiku 4.5 — `claude-haiku-4-5` | 200K | **no** (`effort` errors) |
| standard | Sonnet 5 — `claude-sonnet-5` | 1M | yes (`low`–`max`) |
| capable | Opus 4.8 — `claude-opus-4-8` | 1M | yes (`low`–`max`) |
| most-capable | Fable 5 — `claude-fable-5` | 1M | always-on; tune `effort` (its `low` often beats prior models' `max`) |

- **Context window:** Haiku's 200K is the odd one out — fine for the ~200K-budgeted subagent dispatches the pre-dispatch hook enforces, but a poor fit for the sustained-context **controller** role (prefer a 1M model). In Claude Code the 1M window is selected with the `[1m]` model-id suffix, e.g. `claude-opus-4-8[1m]`; Fable 5 and Sonnet 5 default to 1M.
- **Sonnet 5** is a drop-in upgrade to Sonnet 4.6 (same $3/$15 price, bigger coding/agentic gains) — so the standard tier now absorbs more of the integration-implementer / non-final-review band. Two catches: its new tokenizer produces ~30% more tokens for the same text (re-baseline `max_tokens` and expect the 200K subagent budget to trip sooner), and it is the first Sonnet with cybersecurity refusal classifiers.
- **Refusal risk on security-touching reviews:** Fable 5 and Sonnet 5 both carry cyber refusal classifiers; **Opus 4.8** is the capability-without-refusal-risk pick for auth/crypto/security code. Fable 5 also requires 30-day data retention (unavailable under ZDR — cap at Opus 4.8 / Sonnet 5 there).
- **Opus 4.8** defaults to `high` effort on all surfaces (tune *down* for cheap/mechanical roles, not up) and adds agentic gains over 4.7 (long-context, compaction recovery, tool-triggering) — the half-price alternative to Fable for the controller and hard agentic implementers. Its effort labels were recalibrated vs 4.7 (`medium` more, `high` less, `xhigh` much more) and shift across model versions — tune the Effort column empirically, don't treat it as absolute.

Model IDs churn — treat this table as a snapshot. The body above is model-neutral on purpose; resolve "most capable available" at dispatch time.
