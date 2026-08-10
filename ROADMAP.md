# agentic-sidecar — Roadmap & Architecture

## Release Status

- **v0.1** 🚧 Planned — Sidecar Runtime + Rule-Based Decision Gate (no LLM required)
- **v0.2** 🚧 Planned — Intent Guardian (Intent Envelope, drift detection)
- **v0.2.x** 🚧 Planned — Early Validation Benchmark (narrow, deterministic — intent-drift catch rate only)
- **v0.3** 🚧 Planned — Planner, Critic & Judge (optional, model-agnostic LLM evaluation)
- **v0.4** 🚧 Planned — Policy Advisor, Budget Guardian, full Decision Gate outcomes
- **v0.5** 🚧 Planned — Live Status & Human-Readable Narration
- **v0.6** 🚧 Planned — Multi-Framework Adapters (CrewAI, AutoGen, OpenAI Agents, Google ADK)
- **v0.7** 🚧 Planned — Control Room (dashboard: pause/resume/approve/reject)
- **v0.8** 🚧 Planned — Evaluation Framework & Benchmarks
- **v1.0** 🚧 Planned — Intent Envelope as a published interoperability schema

Nothing has shipped yet — this repo currently holds the architecture proposal
([`concept.md`](concept.md)) and this roadmap. Treat every
checkbox below as unstarted.

## Scaffold Gaps

What the current scaffold (directory layout, tooling config, CI/release
workflows, placeholder modules) deliberately does **not** include yet:

- **No marketing/docs site.** No `index.html` landing page or GitHub Pages
  `docs/` site. That's a real design effort in its own right, not part of a
  structural scaffold — add it separately if/when wanted.
- **No CLI entry point.** `pyproject.toml` has no `[project.scripts]`
  section, and `typer`/`rich` are not declared as dependencies. `cli/`
  exists as a directory with placeholder files only; wire both up once
  `cli/main.py` has a real Typer `app` (v0.5).
- **`ruff` is scoped to `src`/`tests`, not the repo root.** Current `ruff`
  versions format fenced ` ```python ` code blocks inside Markdown files by
  default, which would rewrite intentionally-abbreviated pseudocode in
  `README.md`/`ROADMAP.md`/`concept.md`. `make lint` / `make format` /
  the CI lint job all target `src tests` explicitly for this reason —
  worth remembering if a future contributor "fixes" that back to `.`.
- **Neither optional sibling integration has real code.** `agenticlens` and
  `agentic-chaos` are both declared as `pyproject.toml` extras with a
  docstring-only placeholder module under `integrations/` — the install
  path and package boundary exist, but `pip install
  agentic-sidecar[agenticlens]` (or `[agentic-chaos]`) currently installs a
  dependency that nothing imports yet.
- **No `uv.lock` committed intentionally beyond what a plain `uv sync`
  produces.** There's no `[tool.uv.sources]` override and no sibling-repo
  path dependency — the `agenticlens` extra resolves straight from PyPI.

## Design Constraints (read before building v0.1)

These four are additions to the original proposal, made explicit because
they change how early modules must be built — not just what they do.

1. **One framework adapter first, not nine.** [`concept.md`
   §30](concept.md) lists LangGraph, LangChain, CrewAI, AutoGen, OpenAI
   Agents, Microsoft Agent Framework, Google ADK, custom agents, and
   MCP-based agents as equally in-scope. They are not equally cheap, and two
   of them aren't even distinct integration surfaces: `LangChain` is
   intentionally folded into the `LangGraph` adapter rather than getting its
   own — LangGraph is LangChain's own agent-graph successor, and a separate
   LangChain adapter would mostly duplicate the same interception surface
   for older code. That leaves seven real targets. Build the
   `before_tool_call` interception point against **one** framework first —
   LangGraph, since it's the most structured of the group and gives the
   interception abstraction the best chance of surfacing real design
   problems early. Do not claim "framework independence" until a second
   adapter has actually been built and the interception abstraction has
   survived contact with a framework it wasn't designed against.
2. **Rules before models.** v0.1 ships with **zero** LLM calls. Policy
   Advisor (deterministic YAML rules) and a hand-written Risk Evaluator
   (allow/deny lists, tool-name classification, threshold checks) are the
   entire v0.1 Decision Gate. This de-risks "does interception even work"
   independently from "is the judge any good" — and gives Budget Guardian
   something free to enforce before Judge (v0.3) makes cost a real concern.
3. **Sidecar failure mode is a config, not an accident.** Every Decision
   Gate evaluation must resolve even when the Sidecar itself errors, times
   out, or (once v0.3 ships) the judge model is unreachable.
   `on_sidecar_failure: fail_open | fail_closed` is a required setting with
   no silent default — `Sidecar()` should refuse to run until the caller
   picks one. `fail_closed` is the safer choice for anything that reaches a
   Decision Gate at all (if the action didn't need gating, it wouldn't be at
   a decision boundary), so treat it as the recommended default rather than
   presenting the two as neutral.
4. **A risk classifier is not a free lunch.** [`concept.md`
   §32](concept.md) proposes routing only "high-risk" actions to an
   expensive judge. The classifier that makes that routing decision is
   itself doing real evaluation work and needs the same scrutiny as the
   judge it's gating — ship it as static rules (tool name / argument
   pattern / destination) in v0.1–v0.2, and only promote it to a small
   local model in v0.3+ once there's evidence the rule-based version is
   actually the bottleneck. `concept.md` §32 lists several other
   cost-control ideas — sampling, caching identical evaluations, and an
   asynchronous advisory mode — that are deliberately **not** scheduled to
   any version yet; revisit them only if rules-first-plus-risk-based-routing
   turns out not to be enough, rather than building them speculatively.
5. **Policy, Risk, and Intent ask different questions — don't merge them.**
   It's tempting to implement Intent Guardian as "one more set of rules"
   inside Policy Advisor, since both are config-driven in v0.1/v0.2. Resist
   this: Policy answers "are you permitted to do this?", Risk answers "how
   dangerous is this action?", and Intent answers "is this actually what the
   human asked you to accomplish?" — the third is the one that needs the
   `IntentEnvelope` and alignment scoring, not a permission list, and it is
   the project's actual differentiator (see
   [README.md](README.md#how-the-decision-gate-evaluates-a-decision)). A
   code-review smell to watch for: if a change adds a new field to Intent
   Guardian that's really just a static allow/deny check, it belongs in
   Policy Advisor instead.

## Cross-Project Dependencies

`agentic-sidecar` should stay standalone at runtime — no hard dependency on
any other DeepAgentLabs package. `pip install agentic-sidecar` should work
with zero other packages required.

- `ai-operations-spec`
  Coordinate with: the Intent Envelope and Decision record ([§36](concept.md))
  should be documented as artifacts against the shared AI Operations
  Specification model from the start, not retrofitted at v1.0 the way
  `concept.md` §36 suggests — a schema retrofitted after consumers
  already exist is expensive to change out from under them.
- `agenticlens`
  Validate in: Sidecar decisions (allow/warn/replan/block, intent-alignment
  score) are exactly the kind of event AgenticLens's `Workflow` schema
  already models. An optional `agentic_sidecar.integrations.agenticlens`
  adapter lets `agenticlens analyze` surface Sidecar interventions alongside
  cost/latency data. Optional extra, not a core dependency.
- `agentic-chaos`
  Coordinate with: an interesting integration once both are past v0.1 —
  inject faults into the *agent's* recovery attempt and have the Sidecar
  evaluate whether the recovery decision itself is appropriate
  ([`concept.md` §26](concept.md)). Also worth chaos-testing the
  Sidecar's own gate: what happens to the Main Agent when the Sidecar times
  out or returns garbage? That is exactly what `on_sidecar_failure` (design
  constraint 3, above) exists to make deterministic. An
  `agentic_sidecar.integrations.agentic_chaos` extra/placeholder is
  reserved for this (unlike the AgenticLens adapter, it's a two-way,
  same-run relationship rather than a one-way export, so its actual
  interface still needs designing before it's implemented).
- `mcp-server` (`deep-agentic-core-mcp`)
  Validate in: MCP tool calls are a natural decision boundary
  ([`concept.md` §27](concept.md)). A useful end-to-end check once
  v0.1's Decision Gate exists is gating a real MCP tool call through it.

For roadmap planning, treat ecosystem links as:

- `Depends on`: a sibling capability that must exist first.
- `Coordinate with`: a sibling repo that should be updated in the same window.
- `Validate in`: sibling integrations, fixtures, or CLIs that should be
  checked before closing the item.

## Definition of Done

A roadmap item is done only when all applicable work is complete:

- implementation is merged and usable through the intended Python API or CLI
- tests cover the behavior, including the `fail_open`/`fail_closed` path
- usage examples and user-facing docs are added or updated
- `README.md` and this roadmap are updated when the feature changes user
  expectations or milestone status
- AIOS alignment is documented for any artifact meant to be ecosystem-facing
  (Intent Envelope, Decision record)
- sibling-project dependency and integration checks are recorded where
  relevant
- release metadata (`pyproject.toml`, `src/agentic_sidecar/__init__.py`,
  `CHANGELOG.md`) is updated when the work is part of a release-ready
  change set

---

## Architecture

`agentic-sidecar` attaches to an already-running agent; it does not replace
it and is never counted as a worker in a multi-agent plan. The distinction
that must hold at every version:

- **The Main Agent acts.**
- **The Sidecar observes, thinks, advises, and governs.**

From a developer's perspective, the package exists to answer:

`Is my agent's next action still what the user actually asked for — and
should it happen right now, or should a human see it first?`

That keeps the package focused on decision-time supervision rather than
absorbing observability (AgenticLens), fault injection (Agentic Chaos), or
tool connectivity (Agentic MCP) work that belongs in sibling projects.

The package should focus on these domains:

- intent capture and drift detection
- semantic (not just permission-based) authorization
- independent plan critique
- risk classification and decision gating
- human-in-the-loop escalation
- live, human-readable execution status

### Package Layout (proposed)

```
agentic-sidecar/
  src/agentic_sidecar/
    core/                # Sidecar runtime, attach(), decision boundaries
      sidecar.py         # Sidecar class, attach()
      context.py         # DecisionContext passed to every evaluator
      decision.py         # Decision(status, risk, reason, ...)
    intent/              # Intent Guardian (v0.2)
      envelope.py         # IntentEnvelope model
      alignment.py         # drift detection, constraint validation
    gate/                 # Decision Gate (v0.1 rules, v0.4 full outcomes)
      policy.py            # Policy Advisor — deterministic YAML rules
      risk.py               # Risk Evaluator — rule-based, then pluggable
      budget.py             # Budget Guardian (v0.4)
    evaluators/            # Planner, Critic & Judge (v0.3)
      planner.py           # independently evaluates the whole plan
      critic.py
      judge.py              # model-agnostic judge interface
    status/                 # Status Interpreter (v0.5)
      narrate.py
    adapters/               # Framework adapters
      langgraph.py           # v0.1
      crewai.py               # v0.6
      autogen.py               # v0.6
      openai_agents.py          # v0.6
      google_adk.py              # v0.6
    integrations/               # Optional adapters to sibling projects
      agenticlens.py
    cli/                         # CLI entry point (status stream, v0.5)
```

One repo, one PyPI package — modules ship as minor-version bumps of the same
package rather than splitting into separate repos per capability, which
keeps releases frequent without fragmenting the codebase.

---

## Build Order

### v0.1 — Sidecar Runtime + Rule-Based Decision Gate

Narrowest possible slice that proves interception works at all, with zero
LLM dependency. Everything else in the proposal depends on this holding up
against a real framework.

**Scope:**
- `Sidecar.attach(agent)` + `@sidecar.before_tool_call` interception,
  LangGraph adapter only (see Design Constraint 1)
- `Decision(status, risk, reason)` with `status` in `ALLOW | BLOCK`
  (the smallest useful subset of [`concept.md` §15](concept.md)'s
  seven outcomes)
- Policy Advisor: deterministic YAML allow/deny rules
- Risk Evaluator: static rules only (tool name, argument pattern) — no model
- `on_sidecar_failure: fail_open | fail_closed`, required, no default
- Observe mode only (Sidecar cannot yet block in practice — logs what it
  *would* have decided) so the interception path can be validated against
  real traffic before it's given enforcement power

**Deliverables:**
- [ ] `agentic_sidecar.core` — `Sidecar`, `attach()`, `Decision`
- [ ] `agentic_sidecar.gate.policy` — YAML-driven Policy Advisor
- [ ] `agentic_sidecar.gate.risk` — rule-based Risk Evaluator
- [ ] `agentic_sidecar.adapters.langgraph`
- [ ] `on_sidecar_failure` required setting, both paths tested
- [ ] README section + 1 runnable example (plain LangGraph agent, Observe mode)

### v0.2 — Intent Guardian

**Scope:**
- Structured `IntentEnvelope` ([`concept.md` §6](concept.md)):
  goal, requester, constraints, authority granted/not granted, expiry
- Intent injection at decision boundaries ([§7](concept.md))
- Drift detection: is the current proposed action still consistent with the
  envelope? ([§8](concept.md))
- Constraint validation (e.g. `maximum_refund: 500` vs. a proposed `850`)
  as the first concrete semantic-authorization check
  ([§9](concept.md))
- Govern mode becomes available: Decision Gate can now `BLOCK` for real,
  gated behind `on_sidecar_failure` from v0.1

**Deliverables:**
- [ ] `agentic_sidecar.intent` — `IntentEnvelope`, alignment scoring
- [ ] Constraint validation against numeric/enum/allow-list fields
- [ ] Intent-drift `WARN`/`BLOCK` wired into the v0.1 Decision Gate
- [ ] README section + example reproducing the refund-limit scenario from
      [`concept.md` §22](concept.md)

### v0.2.x — Early Validation Benchmark (narrow)

Deliberately small and deliberately early — the point is a real, honest
number before the project leans on architecture claims alone, without
waiting for Judge/Critic (v0.3) to exist. Scope is intentionally limited to
what Intent Guardian can decide **deterministically**: did it catch an
injected intent violation, yes or no. This is not the full baseline-vs.-
Sidecar comparison — that stays at v0.8, where Judge and Critic make
"unsafe decision" and "task success" measurable in the first place.

**Scope:**
- 3–5 scenario fixtures reusing [`concept.md`
  §22](concept.md)'s pattern: a refund exceeding its authorized limit,
  a DEV-scoped cleanup that drifts into production resources, plus 1–2 new
  ones covering an unauthorized data-export and a scope-creep delegation
- Each fixture run twice: Intent Guardian off vs. on
- Metric: intent-violation catch rate and false-positive rate on clean runs
  — nothing about cost, latency, or general task success yet (v0.8 covers
  those once Judge/Critic exist to make them meaningful)

**Deliverables:**
- [ ] `tests/validation/` — 3–5 fixtures, each runnable standalone
- [ ] Small measured before/after table (catch rate, false-positive rate)
- [ ] README section publishing the numbers, explicitly scoped as
      "Intent Guardian only" — not a general Sidecar effectiveness claim

### v0.3 — Planner, Critic & Judge

**Scope:**
- Planner: independently evaluates the *whole plan* against the active
  IntentEnvelope, not just one decision — the "explain my charge" plan
  that also cancels a subscription and issues a refund example
  ([§10](concept.md)). Ships alongside Critic/Judge rather than earlier
  because, like them, it needs real reasoning rather than a deterministic
  check, so it has no place in the LLM-free v0.1/v0.2 phase (Design
  Constraint 2)
- Critic mode: pre-decision challenge for unsupported assumptions,
  unnecessary actions, contradictions ([§11](concept.md))
- Model-agnostic Judge interface — Main Agent model and Sidecar Judge model
  must be independently swappable ([§12](concept.md))
- Promote the risk classifier from static rules (v0.1) to an optional small
  local model, only for teams that have evidence the rule-based version is
  the bottleneck (Design Constraint 4)
- `judge.enabled` stays `false` by default; this is the first version where
  turning it on has a real cost/latency tradeoff to document

**Deliverables:**
- [ ] `agentic_sidecar.evaluators.planner`
- [ ] `agentic_sidecar.evaluators.critic`
- [ ] `agentic_sidecar.evaluators.judge` — provider-agnostic interface,
      at least two backends (e.g. OpenAI, Anthropic) to prove independence
      from the Main Agent's own model
- [ ] Optional local-model risk classifier, `rules` remains the default
- [ ] README section documenting measured added latency/cost per decision

### v0.4 — Full Decision Gate & Budget Guardian

**Scope:**
- Remaining Decision Gate outcomes from [§15](concept.md): `WARN`,
  `CHALLENGE`, `REPLAN`, `PAUSE`, `ESCALATE` (in addition to v0.1's
  `ALLOW`/`BLOCK` — all seven from the original list). `CHALLENGE` is
  Critic's (v0.3) natural output and needs its own status distinct from the
  others: it means the Sidecar pushes back and requires the Main Agent to
  justify or reconsider the specific decision before proceeding, without
  forcing a full plan regeneration (`REPLAN`) or a hard stop (`BLOCK`)
- Human-in-the-loop escalation flow ([§16](concept.md)): pause, present
  `[Approve Once] [Reject] [Modify Intent] [Ask Agent to Replan] [Stop Agent]`
- Budget Guardian: cost/token ceilings per task, enforced through the same
  gate rather than a side channel

**Deliverables:**
- [ ] All seven `Decision.status` values implemented and tested
- [ ] `agentic_sidecar.gate.budget` — `max_cost`, per-task tracking
- [ ] Human Escalation primitive (CLI prompt to start; UI comes in v0.7)
- [ ] README section + example exercising `REPLAN`

### v0.5 — Live Status & Human-Readable Narration

**Scope:**
- Status Interpreter: translate raw tool/MCP traces into the narrated form
  from [§19](concept.md) (`🔎 Looking up your order`, etc.)
- CLI status stream: current objective, current step, intent alignment,
  risk, budget — the non-UI subset of the Control Room from
  [§17](concept.md)

**Deliverables:**
- [ ] `agentic_sidecar.status.narrate`
- [ ] CLI `agentic-sidecar status --follow`
- [ ] README section + example

### v0.6 — Multi-Framework Adapters

**Scope:**
- Second, third, fourth adapters, now that the interception abstraction has
  survived one full round of real usage (Design Constraint 1): CrewAI,
  AutoGen, OpenAI Agents SDK, Google ADK
- Any interception-point changes the v0.1 abstraction needs, now driven by
  real friction instead of speculation

**Deliverables:**
- [ ] `agentic_sidecar.adapters.crewai`
- [ ] `agentic_sidecar.adapters.autogen`
- [ ] `agentic_sidecar.adapters.openai_agents`
- [ ] `agentic_sidecar.adapters.google_adk`
- [ ] Adapter conformance tests — same `Decision` behavior across all five
      frameworks for an identical scenario

### v0.7 — Control Room

**Scope:**
- The dashboard from [§20](concept.md): live agent state, plan, tool
  calls, intent alignment, risk, cost, and controls (`PAUSE`, `RESUME`,
  `STOP`, `INTERVENE`, `MODIFY INTENT`, `APPROVE ONCE`, `REJECT ACTION`,
  `ASK AGENT TO REPLAN`)
- Deliberately last — different skill set (frontend) than the rest of the
  ecosystem's CLI/library-first approach, and everything it displays already
  needs to exist from v0.1–v0.5

**Deliverables:**
- [ ] Control Room web UI consuming the v0.5 status stream
- [ ] Wired to v0.4's escalation/approval flow
- [ ] README section + demo GIF

### v0.8 — Evaluation Framework & Benchmarks

**Scope:**
- Broadens the v0.2.x narrow benchmark into the full empirical harness from
  [§35](concept.md): Agent Alone vs. Agent + Sidecar, now measuring
  task success, unsafe-action rate, false-intervention rate, and
  cost/latency overhead — metrics that need Judge (v0.3) and the full
  Decision Gate (v0.4) to be meaningful, which is why they waited
- Reuses the v0.2.x fixtures plus new ones covering Planner/Critic-catchable
  cases (unnecessary plan steps, unsupported assumptions) that a
  deterministic intent check can't detect
- Answers the research questions in [§34](concept.md) with data instead
  of architecture claims — in particular "how much reliability improvement
  per dollar of added inference cost"

**Deliverables:**
- [ ] Benchmark harness extending `tests/validation/` (v0.2.x) with
      Judge/Critic-dependent scenarios
- [ ] Published baseline-vs-Sidecar comparison table (task success, unsafe
      actions, false-intervention rate, cost/latency overhead)
- [ ] README section linking the results, updating the narrower v0.2.x
      numbers with the fuller picture

### v1.0 — Intent Envelope as an Interoperability Schema

**Scope:**
- Publish the Intent Envelope and Decision record as a versioned schema in
  `ai-operations-spec`, not just an internal Sidecar structure
  ([§36–37](concept.md))
- Cross-project intent propagation: an envelope created by one Sidecar
  instance stays valid and inspectable if the task hands off to a
  sub-agent, a different MCP host, or a different Sidecar instance

**Deliverables:**
- [ ] Intent Envelope schema documented in `ai-operations-spec`, versioned
- [ ] Decision record schema documented alongside it
- [ ] Cross-instance handoff example
- [ ] README + roadmap updated to reflect the stable schema

---

## Suggested Timeline

| Phase | Deliverable | Approx. effort |
| --- | --- | --- |
| 1 | v0.1 — Sidecar Runtime + Rule-Based Decision Gate (LangGraph, Observe mode) | 3–5 weeks |
| 2 | PyPI release v0.1, README, initial adoption push | ongoing |
| 3 | v0.2 — Intent Guardian | 2–4 weeks |
| 4 | PyPI release v0.2, v0.2.x narrow validation benchmark + published numbers | 1–2 weeks |
| 5 | v0.3 — Planner, Critic & Judge | 3–5 weeks |
| 6 | PyPI release v0.3 | ongoing |
| 7 | v0.4 — Full Decision Gate & Budget Guardian | 2–4 weeks |
| 8 | PyPI release v0.4 | ongoing |
| 9 | v0.5 — Live Status & Narration | 2–3 weeks |
| 10 | PyPI release v0.5 | ongoing |
| 11 | v0.6 — Multi-Framework Adapters | 4–6 weeks |
| 12 | PyPI release v0.6 | ongoing |
| 13 | v0.7 — Control Room | 4–6 weeks |
| 14 | PyPI release v0.7 | ongoing |
| 15 | v0.8 — Evaluation Framework & Benchmarks | 3–5 weeks |
| 16 | Publish baseline-vs-Sidecar results | ongoing |
| 17 | v1.0 — Intent Envelope interoperability schema | 2–4 weeks |
| 18 | PyPI release v1.0 | ongoing |

This is a rough estimate for a single primary contributor working
part-time — treat it as a planning anchor, not a commitment.
