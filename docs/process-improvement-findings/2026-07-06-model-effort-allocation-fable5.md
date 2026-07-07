# Model & Effort Allocation Across the Superpowers Pipeline (Fable 5 context)

> Analysis for Aaron's consideration — 2026-07-06. Where should the new Anthropic **Fable 5** model be spent in the Superpowers process, and where do cheaper models (Opus / Sonnet / Haiku) — possibly with more *thinking effort* — do the job just as well?
>
> Evidence base: the actual skill files (`brainstorming`, `writing-plans`, `subagent-driven-development` + its role prompts, `systematic-debugging`, `test-driven-development`), the fork's existing `subagent-driven-development/references/model-selection.md`, and the `claude-api` skill for authoritative Fable 5 facts (capability tier, pricing, effort/thinking behavior).

> **Update 2026-07-06 (post-publication): Claude Sonnet 5 launched** (`claude-sonnet-5`) — a drop-in upgrade to Sonnet 4.6. **Read every "Sonnet 4.6" below as "Sonnet 5."** Same standard-tier price ($3/$15; intro $2/$10 through 2026-08-31), 1M context, adaptive thinking on by default, effort dial retained, largest gains in **coding and agentic tasks**. This **confirms** the framework and the six Fable apex points (Anthropic positions Sonnet 5 *below* Opus-class) and **strengthens** the closed-verifier recommendations (a better standard-tier verifier at the same price). One fine-tune: Sonnet 5's coding/agentic gains let the **standard tier absorb more of the middle band** (integration implementers, non-final reviews) that this doc assigned to Opus — a cost win. New caveats: (a) new tokenizer ≈ **+30% tokens** for the same text (re-baseline `max_tokens`; the 200K subagent context-budget gate trips sooner); (b) Sonnet 5 is the **first Sonnet with cybersecurity refusal classifiers**, so the "keep security-adjacent work off Fable" caveat now also applies to Sonnet 5 → **Opus 4.8 is the capability-without-refusal-risk pick** for auth/crypto/security-touching reviews; (c) Sonnet 5 supports **ZDR** (Fable requires 30-day retention), so under a ZDR org Sonnet 5 / Opus 4.8 are the ceiling.

---

## 1. The two dials (this is the whole point)

The question conflates two knobs that are actually orthogonal. Naming them precisely is what makes the answer tractable.

| Dial | What it is | Helps with | How you turn it |
|---|---|---|---|
| **Model capability** | Raw quality of the base model — latent knowledge, code-generation fidelity, instruction adherence over long context, judgment/taste. This is the *floor* of quality regardless of how long the model deliberates. | Open-ended judgment, broad codebase understanding, "is this architecture sound?", idiomatic first-shot code, faithfully following a 200-line multi-section prompt without dropping a requirement. | Pick the model: Haiku 4.5 → Sonnet 4.6 → Opus 4.8 → **Fable 5**. |
| **Reasoning effort** (test-time compute) | How much the model deliberates before answering — extended/adaptive thinking depth. | Multi-step logical chains, adversarial self-checking, exploring a solution space, catching subtle contradictions, careful mechanical cross-referencing. | `output_config.effort`: `low → medium → high → xhigh → max`. |

**The load-bearing principle:**

> **Effort substitutes for capability on *closed* problems, not *open* ones.**
>
> - **Closed problem** = the answer is determined by material in front of the model; the work is *verification* (trace this data path, does every decision survive distillation, does the code match the constraint, is a review missing from the trace). More thinking on a cheaper model gets there.
> - **Open problem** = the answer requires latent judgment the model either has or doesn't (is this the right decomposition, does this architecture smell wrong, what's the root cause under uncertainty, is this design good). Effort can't manufacture taste. Here **capability is the binding constraint** and Fable 5 earns its premium.

### Two facts from the `claude-api` skill that sharpen this

1. **The effort dial is not universal.** `output_config.effort` works on Fable 5, Sonnet 4.6, and Opus 4.5+ — but **errors on Haiku 4.5**. So Haiku is simultaneously the capability floor *and* has no effort dial. Consequence: a genuinely hard *closed* check assigned to Haiku can't be rescued with more thinking — you must bump it to Sonnet just to *unlock* the effort dial.

2. **For Fable 5 the two dials are partly fused.** Fable's thinking is always-on (you can't disable it), and Anthropic's own guidance says *lower* effort on Fable "often exceeds the `xhigh` or even `max` performance of previous models." So you don't reach Fable-quality by cranking effort on Opus — the model floor delivers it. This is exactly why capability, not effort, is the right lever at the open-judgment chokepoints.

### Pricing (the cost side of the tradeoff)

| Model | Input $/1M | Output $/1M | vs Opus 4.8 |
|---|---|---|---|
| **Fable 5** | $10.00 | $50.00 | **2×** |
| Opus 4.8 | $5.00 | $25.00 | 1× |
| Sonnet 5 | $3.00 | $15.00 | 0.6× |
| Haiku 4.5 | $1.00 | $5.00 | 0.2× |

(Sonnet 5 standard price $3/$15; introductory $2/$10 through 2026-08-31. Its new tokenizer emits ~30% more tokens for the same text, so effective per-task cost runs ~30% above Sonnet 4.6 despite unchanged per-token pricing.)

Fable is 2× Opus, ~3.3× Sonnet, 10× Haiku. That ratio is what makes *targeting* it matter.

---

## 2. The pipeline is an error funnel

Superpowers is deliberately front-loaded and gated. A mistake's cost depends on **where** it happens:

```
brainstorm → spec → distill → PLAN → [Task0] → per-task loop(impl → spec-review → quality-review) → pre-completion gate(trace audit, final review) → finish
   \_______________ errors here propagate & multiply _______________/        \__ errors here are caught by the very next review __/
```

- A wrong decision in **brainstorming or the plan** silently encodes itself into every one of N downstream tasks — the CLAUDE.md incident file is full of these ("built from scratch, corrected 10 times"; "all tests passed, all 3 bugs shipped").
- A wrong line in **one mechanical implementer task** is caught by the spec + quality review that fires immediately after it.

So capability/effort investment should concentrate at **(a) the front of the funnel** (design, plan) and **(b) the adversarial verification chokepoints** (plan review, final code review, contract-touching task reviews, root-cause investigation). These are exactly the "irreversible / high-blast-radius" points. The high-*volume* roles (per-task implementers, the partner check, verification tasks) sit downstream of a gate and are individually cheap to get wrong.

**This is what makes the Fable recommendation cost-rational:** the chokepoints are a *small fraction of total token volume* (a handful of design/plan/review turns), while the bulk of tokens are spent in the N implementer + reviewer subagent turns. Concentrating Fable at ~6 apex points while keeping the high-volume roles on Sonnet/Haiku targets the funnel's apex for a small absolute cost.

---

## 3. Per-role analysis (entry → exit)

Cognitive-profile legend: **Open** = latent-judgment-bound (capability wins) · **Closed** = verification-bound (effort substitutes) · **Mechanical** = deterministic transform/routing · **Deterministic** = no model at all.

The two needs are scored **separately** (the whole point of the question), then a recommended model + effort follows.

| # | Role / skill | Deliverable | Profile | **Effort need** | **Capability need** | Recommendation |
|---|---|---|---|---|---|---|
| 1 | `using-superpowers` bootstrap | route to a skill | Mechanical | Low | Haiku-floor | Haiku (session model) |
| 2 | **brainstorming** (main) | spec.md — design, tradeoffs, archetype | **Open** | **High** | **Fable** | **Fable 5**, high effort |
| 3 | spec-document-reviewer | approve/return spec | Open (adversarial) | High | Opus–Fable | Fable 5 or Opus 4.8 + high |
| 4 | spec distillation | spec-distilled.md (strip rationale, promote contract facts) | Mechanical (must not invert a decision) | Med | Sonnet | Sonnet 4.6 + medium |
| 5 | distillation-reviewer | did every decision survive? | **Closed** | Med–High | Sonnet | Sonnet 4.6 + high |
| 6 | **writing-plans** (main) | plan.md — decomposition, contract constraints, pattern discovery, write-scope | **Open** | **High** | **Fable** | **Fable 5**, high effort |
| 7 | `validate-plan.py` | structural gate | **Deterministic** | — | — | **No model** |
| 8 | **plan-document-reviewer** | semantic cross-doc audit, 15 checks, type-mismatch vs source contracts | **Open** (adversarial) | **High** | **Fable** | **Fable 5** (or Opus 4.8 + xhigh) |
| 9 | **SDD controller** (main loop) | orchestration: build every subagent prompt verbatim, route statuses, pick review tiers, catch escalations, log deviations | **Open**, sustained context | Med–High | **Fable** | **Fable 5** — see §4 |
| 10 | implementer subagent (mechanical task) | code + tests for a well-specified 1–2 file task | Capability-bound but the *plan already did the reasoning* | Low | Sonnet/Haiku | Sonnet 4.6 (Haiku for trivial), low effort |
| 10b | implementer subagent (integration / BLOCKED-retry) | multi-file coordination, or a task that came back BLOCKED "needs more reasoning" | Open-ish | Med–High | Opus–Fable | Opus 4.8 + high; escalate to Fable on repeat-BLOCKED |
| 11 | spec-compliance reviewer | "assume the report is incomplete until code proves otherwise"; trace contract data paths | **Closed→Open** (contract tasks) | High | Sonnet–Opus | Sonnet 4.6 + high (minimum tier); Opus 4.8 + high on contract/integration tasks |
| 12 | code-quality reviewer | dead code, responsibility, contract trace, security | Closed→Open | High | Opus | Opus 4.8 + high |
| 13 | **controller-partner** | 6-item checklist: does the dispatch prompt contain/accurately reflect the plan sections | **Closed** (checklist-bound) | Med | Haiku-floor | **Haiku** (already assigned) — see §5 |
| 14 | pre-execution auditor | honesty gate on the controller's self-assessment | Closed | Med | Sonnet | Sonnet 4.6 + medium |
| 15 | **trace-auditor** | parse session trace JSON, flag skipped reviews / unlogged concerns / missing reports | **Closed** (rule-based cross-ref) | **High** | Sonnet | **Sonnet 4.6 + high** (or Opus + medium) — *poster child for effort-substitutes* |
| 16 | **final code reviewer** (pre-completion) | whole-diff review with deviations.md, final contract trace | **Open** (highest stakes) | **High** | **Fable** | **Fable 5** (or Opus 4.8 + xhigh) |
| 17 | **systematic-debugging** Phase 1–3 | root-cause hypothesis under uncertainty ("ultrathink") | **Open** | **High/Max** | **Fable** | **Fable 5**, high/max effort |
| 17b | systematic-debugging Phase 4 | apply the point fix | Mechanical | Low | Sonnet | Sonnet 4.6 |
| 18 | verification-before-completion | run tests, observe, check | Closed/Mechanical | Low–Med | Sonnet | Sonnet 4.6 |
| 19 | finishing-a-development-branch | merge/PR/cleanup decision | Mechanical | Low | Sonnet | Sonnet 4.6 |
| 20 | handoff-acceptance | verify external package against contract | Closed→Open | High | Opus | Opus 4.8 + high |
| — | all Python hooks (`controller-checkpoint`, `sdd-pre-dispatch`, `materialize-manifest`, `transition-module`, …) | enforcement | **Deterministic** | — | — | **No model** — they already replace judgment with mechanism |

---

## 4. The controller is the strongest single Fable candidate

The SDD controller (the main loop in `subagent-driven-development`) is easy to overlook because it isn't a named subagent — but it is the role whose errors have the widest blast radius:

- It **constructs every implementer/reviewer prompt verbatim** — the Contract Constraints, Shared Constants, and Pattern References passthroughs are copied by the controller into each dispatch. A paraphrase or omission here corrupts *that task and every review of it* (the skill spends three sections warning about exactly this failure mode).
- It **routes four implementer statuses**, **declares review tiers before seeing the report** (an explicit anti-rationalization design), **catches escalations**, and **logs deviations** — all sustained-context judgment where dropping one thread compounds over 17 tasks.
- Fable's documented strengths include *"reliably sustains ongoing communications with long-running sub-agents and peer agents"* and *"parallel sub-agent delegation"* — this is literally the controller's job description.

The controller is **capability-bound more than effort-bound**: the work is faithful instruction-execution over a long, accumulating context, not deep deliberation on any single step. That is precisely where a stronger base model beats a cheaper-model-with-more-thinking. **If you spend Fable in exactly one place, spend it on the controller.**

**Fine-tune (Opus 4.8 launch page):** Opus 4.8's documented gains over 4.7 — *"better long-context handling, fewer compactions, and better compaction recovery,"* *"long agentic traces stay on task with fewer derailments after compaction,"* and *"less likely to skip a tool call the task required"* — are a near-verbatim description of the controller's failure modes (context accumulation across N tasks; never skipping a required review/dispatch/deviation-log step). That makes **Opus 4.8 + `high` a strong half-price controller** ($5/$25 vs Fable's $10/$50). So the sharper statement is: *the controller is the highest-leverage single place to spend capability — Fable 5 at the ceiling (multi-module, high-ambiguity), Opus 4.8 as the default floor for it.* (Opus 4.8 also defaults to `high` effort and is the only tier with mid-conversation system messages — a future cache-cost lever if the controller loop is ever restructured to mutate its system prompt in place rather than dispatch fresh subagents.)

---

## 5. Where *not* to spend Fable (and why)

- **controller-partner → keep Haiku.** Its own prompt says *"Use haiku for cost efficiency. The partner reads and compares — it doesn't write code."* It is a 6-item checklist verifier — a closed problem whose judgment is fully constrained by the checklist. Capability floor is genuinely low here. (Caveat: Haiku has *no effort dial*, so if you ever find the partner missing things, the fix is Sonnet + low effort to unlock thinking, **not** Fable.)
- **trace-auditor → Sonnet + high effort, not Fable.** It cross-references a trace against fixed anomaly rules — the archetypal closed problem where effort substitutes for capability. Spending Fable here is pure waste.
- **mechanical implementers → Sonnet/Haiku.** When the plan is well-specified (which the writing-plans gate enforces), the reasoning is *already in the plan*; the implementer just needs to produce correct idiomatic code and follow the multi-section prompt. That's a capability-*floor* task, not a capability-*ceiling* one. Reserve the Opus/Fable bump for the `BLOCKED — needs more reasoning` escalation path the SDD skill already defines.
- **distillation, verification tasks, finishing-branch, pre-execution audit → Sonnet.** Closed/mechanical, gate-backstopped.
- **all deterministic hooks → no model.** The fork's entire enforcement layer (checkpoints, provenance, tier gates) exists *because* mechanism beats judgment for these checks. Don't reintroduce a model where a script already suffices.

Two operational reasons beyond cost to keep the high-frequency roles off Fable: Fable runs **minutes-long single turns** at higher effort (bad for the tight per-task loop), and its **safety classifiers can false-positive on security-adjacent work** (`refusal` stop reason) — a real consideration for a dev toolchain that occasionally touches auth/crypto/security code. It also requires **30-day data retention** (not available under ZDR).

---

## 6. Recommendation summary

**Spend Fable 5 (high effort) at the six error-funnel apex points:**

1. **brainstorming** — design under ambiguity (Fable's headline strength)
2. **writing-plans** — decomposition + contract reasoning + pattern discovery
3. **plan-document-reviewer** — the semantic gate that catches type/contract drift before N tasks inherit it
4. **SDD controller** — orchestration fidelity; errors propagate to every dispatch (see §4)
5. **final code reviewer** (+ spec/quality reviews on contract/integration/security tasks) — last line before merge
6. **systematic-debugging root-cause** (Phase 1–3) — hypothesis under uncertainty

**Keep cheaper models everywhere else:**
- **Opus 4.8 + high** for non-final adversarial reviews and integration/BLOCKED implementers.
- **Sonnet 4.6 + (medium/high effort)** for the *closed* verification roles — trace-audit, distillation-review, pre-execution audit, verification tasks — where **effort substitutes for capability**.
- **Haiku 4.5** for the checklist-bound partner, routing, and trivial single-file tasks.
- **No model** for the deterministic hook layer.

**Why this is cost-rational:** the six Fable chokepoints are a *small fraction of total token volume* (a handful of design/plan/review turns), while the token bulk lives in the high-volume implementer/partner/verification roles that stay on Sonnet/Haiku. You buy the highest-capability model exactly where a mistake multiplies, and pay Sonnet/Haiku rates where mistakes are gate-caught.

**One-line mental model:** *Capability at the front and at the adversarial gates; effort (on a cheaper model) for the closed verifiers; mechanism (no model) for the enforcement hooks.*

### Relationship to the existing `model-selection.md`

The fork already ships `subagent-driven-development/references/model-selection.md`, which tiers **by capability only** (cheap / standard / most-capable → haiku / standard / most-capable for mechanical / integration / architecture-review). This analysis **adds the orthogonal effort axis** and slots Fable 5 into the "most capable" tier — but with a refinement: *"architecture, design, and review"* is not monolithic. The *open-judgment* subset (design, plan, final review, root-cause) wants Fable; the *closed-verification* subset that also lives under "review" (trace-audit, distillation-review, partner) does **not** — it wants a cheaper model with the effort dial turned up. If this framing is adopted, `model-selection.md` is the natural place to record it (a small "effort" column + the closed-vs-open split), and the per-role model/effort defaults could eventually be encoded as `opts.model` / `opts.effort` hints in the dispatch templates.
