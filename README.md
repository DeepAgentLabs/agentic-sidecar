# agentic-sidecar

**A companion intelligence and real-time supervision layer for autonomous AI agents.**

> The Main Agent acts. The Sidecar observes, thinks, advises, and governs.

## Status

**v0.1 and v0.2 implemented.** The Sidecar runtime, a rule-based Decision
Gate (Policy Advisor + Risk Evaluator), and Intent Guardian (`IntentEnvelope`
+ constraint validation) are real code, attached via the LangGraph adapter.
Observe mode (v0.1, logs only) and Govern mode (v0.2, a `BLOCK` is actually
enforced) both work today — see [Python API
(implemented)](#python-api-implemented) below and [`examples/`](examples/)
for two runnable scripts. No PyPI release yet. See [ROADMAP.md](ROADMAP.md)
for the full build plan (v0.2.x onward).

## Contents

- [Why](#why)
- [What it is not](#what-it-is-not)
- [Architecture](#architecture)
- [Sidecar vs. Agent Harness](#sidecar-vs-agent-harness)
- [Main Agent vs. Sidecar](#main-agent-vs-sidecar)
- [How the Decision Gate evaluates a decision](#how-the-decision-gate-evaluates-a-decision)
- [Sidecar modules](#sidecar-modules)
- [Python API (implemented)](#python-api-implemented)
- [Planned Python API](#planned-python-api)
- [Operating modes](#operating-modes)
- [Long-term: an intent propagation layer](#long-term-an-intent-propagation-layer)
- [The DeepAgentLabs ecosystem](#the-deepagentlabs-ecosystem)
- [Roadmap](#roadmap)
- [License](#license)

## Why

Autonomous agents chain a lot of reasoning and tool calls between a user's
request and a real-world effect:

```text
User → Agent → Planning → Sub-Agent → MCP → Tool → API → External System
```

Three things go wrong in that chain that permission checks alone don't catch:

- **Intent drift** — "investigate why production is slow" quietly becomes
  "restart the production database." Nobody revoked authority; the agent's
  plan just wandered.
- **Technically-allowed, contextually-wrong actions** — `refund_customer()`
  is a permitted tool call. Refunding $850 against a $500 authorization is
  not a permitted *decision*, even though the tool call succeeds.
- **No live visibility** — long-running agents act for minutes at a time
  with no answer to "what is it doing right now, and can I stop it?"

`agentic-sidecar` is designed to attach to any agent framework, but the first
release proves that against one framework only — LangGraph — before claiming
the rest (see [Design Constraints](ROADMAP.md#design-constraints-read-before-building-v01v02)
in ROADMAP.md). Either way, it answers a different question than permission
checks or observability tools do:

> **Not** "can this agent call this tool?" — **"should it, right now, given
> what the user actually asked for?"**

## What it is not

- **Not a multi-agent framework.** The Sidecar never owns or executes the
  task plan, and it never replaces a worker agent. It may independently
  critique the Main Agent's plan or propose alternatives (the Planner
  module) — but the Main Agent decides whether to act on that critique, and
  remains the one that executes.
- **Not a content-safety guardrail.** Libraries like NeMo Guardrails or
  Guardrails AI validate a single prompt/response turn against rules. The
  Sidecar evaluates a *decision* — a tool call or plan step — against intent
  and context accumulated across an entire task.
- **Not a tracing/observability tool.** That's
  [AgenticLens](https://github.com/DeepAgentLabs/agenticlens)'s job:
  "what did the agent do, and why did it fail?" — after the fact. The
  Sidecar's job is "should it continue?" — while it's still running.
- **Not just LLM-as-a-Judge.** A judge model is one possible evaluator inside
  one Sidecar module (§ [Sidecar modules](#sidecar-modules)). Most decisions
  should never reach an LLM at all — see [Operating
  modes](#operating-modes) and the cost-control design in
  [ROADMAP.md](ROADMAP.md).
- **Not an agent harness.** It doesn't run the agent loop, manage tools, or
  handle retries — that's LangGraph's, CrewAI's, or your custom loop's job.
  The Sidecar attaches to whatever harness is already running the agent; see
  [Sidecar vs. Agent Harness](#sidecar-vs-agent-harness).

## Architecture

```text
                    USER
                      │
                 User Intent
                      │
                      ▼
              ┌───────────────┐
              │  MAIN AGENT   │
              │   EXECUTOR    │
              └───────┬───────┘
                      │
              Plans / Decisions
                      │
                      ▼
            ┌─────────────────────┐
            │   AGENTIC SIDECAR   │
            │                     │
            │ Intent Guardian     │
            │ Planner             │
            │ Critic              │
            │ Judge               │
            │ Risk Evaluator      │
            │ Policy Advisor      │
            │ Decision Gate       │
            │ Status Interpreter  │
            └──────────┬──────────┘
                       │
          Advice / Approval / Challenge
                       │
                       ▼
                 MAIN AGENT
                       │
                       ▼
                  MCP / Tools
                       │
                       ▼
                External Systems
```

The Sidecar is attached to the execution lifecycle. It does not own the
user's task and is never a second worker in the plan.

## Sidecar vs. Agent Harness

An **agent harness** (LangGraph, a custom loop, OpenAI Agents SDK, Microsoft
Agent Framework, ...) is the control and execution environment: it runs the
agent loop and manages tools, state, context, retries, and lifecycle.
`agentic-sidecar` doesn't replace that — it attaches to it as a decision-time
supervision layer:

```text
Agent Harness   = control and execution loop.
Agentic Sidecar = decision-time supervision layer for that loop.
```

The harness answers *"how do I execute this workflow?"* The Sidecar answers
*"should this decision happen, given what the human originally asked for?"*

This distinction matters most once a task fans out across a delegation
chain — Agent A → Agent B → Agent C → MCP/Tool — where each hop tends to
receive only the sub-task it needs to perform, not the original constraints
and authority behind it:

```text
Human Intent → Agent A → delegates → Agent B → delegates → Agent C → MCP/Tool
```

The Sidecar's Intent Envelope (§ [Sidecar modules](#sidecar-modules)) is
designed to travel with the task through that chain instead of being
reconstructed from conversation history at every hop — see [Long-term: an
intent propagation layer](#long-term-an-intent-propagation-layer).

Where it pays for itself: without a supervision layer, a harness typically
discovers a bad decision only after acting on it —

```text
Plan → Act → Fail → Recover → Replan
```

— versus catching it before execution:

```text
Plan → Sidecar Check → Act
          ├── ALLOW
          ├── CHALLENGE
          ├── REPLAN
          ├── BLOCK
          └── ESCALATE
```

That's primarily a reliability and control win, not a speed win — the
Sidecar doesn't make the underlying model faster, it reduces unnecessary
actions, unsafe retries, and repeated context reconstruction. Full treatment:
[concept.md § 23](concept.md#23-sidecar-vs-agent-harness).

## Main Agent vs. Sidecar

| Main Agent | Agentic Sidecar |
| --- | --- |
| Accomplishes the task | Maintains original intent |
| Reasons about the domain problem | Independently evaluates plans and decisions |
| Selects and calls tools | Challenges questionable decisions |
| Interacts with MCP servers / APIs | Evaluates risk and checks policy |
| Executes actions | Decides when human approval is required |
| Produces the final result | Explains live execution; recommends replanning; pauses or blocks when configured |

## How the Decision Gate evaluates a decision

Three modules ask three genuinely different questions about the same
proposed action, and the roadmap's job is to keep them from collapsing into
one generic "policy engine":

```text
             USER INTENT
                  │
          Intent Envelope
                  │
                  ▼
             MAIN AGENT
                  │
           proposed action
                  │
                  ▼
              SIDECAR
          ┌───────┼────────┐
          │       │        │
       Policy    Risk    Intent
          │       │        │
   "Are you    "How      "Is this
   permitted   dangerous  actually what
   to do       is this    the human
   this?"      action?"   asked you to
                          accomplish?"
          │       │        │
          └───────┼────────┘
                  │
             DECISION GATE
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
     ALLOW      REPLAN     ESCALATE
                              │
                            HUMAN
```

Policy and Risk are largely mechanical — permission lists, thresholds,
tool-argument patterns — and v0.1 ships them with zero LLM calls (see
[ROADMAP.md](ROADMAP.md)). Intent (v0.2) is still deterministic, not
LLM-based, but is the one that gets closest to "what the user actually
meant" so far, via structured `IntentEnvelope` constraints rather than
free-form judgment — full semantic understanding is further out on the
roadmap.

The diagram above shows the target outcome set. **v0.1 shipped a narrower
slice** (`ALLOW`/`BLOCK` only, Observe mode: the Sidecar logs what it
*would* have decided but cannot stop an action in practice). **v0.2 adds
`WARN`** (an Intent Guardian finding worth surfacing but not severe enough
to block, e.g. a stale envelope) **and Govern mode**, where a `BLOCK` is
actually enforced by the attached adapter — see
`agentic_sidecar.core.exceptions.SidecarBlockedError`. `CHALLENGE`,
`REPLAN`, `PAUSE`, and `ESCALATE` remain v0.4. Version-by-version build
order is in [ROADMAP.md](ROADMAP.md#build-order).

## Sidecar modules

Users enable only what they need:

```text
Agentic Sidecar
│
├── Intent Guardian     — Intent Envelope, alignment checks, drift detection
├── Planner              — independently evaluates the agent's plan
├── Critic                — challenges a proposed decision before it executes
├── Judge                 — optional independent (and independent-model) evaluation
├── Risk Evaluator        — classifies an action's risk before deciding whether to escalate
├── Policy Advisor        — deterministic policy rules (cheapest check, runs first)
├── Decision Gate         — turns evaluations into ALLOW / WARN / CHALLENGE / REPLAN / PAUSE / BLOCK / ESCALATE
├── Budget Guardian       — cost/token ceilings per task
├── Status Interpreter    — translates raw tool/MCP traces into human-readable narration
└── Human Escalation      — pauses execution and requests approval
```

```yaml
sidecar:
  intent:
    enabled: true
    preserve_original_intent: true
  planner:
    enabled: false        # off by default — see cost design in ROADMAP.md
  critic:
    enabled: false        # off by default — see cost design in ROADMAP.md
  policy:
    enabled: true
    source: policies.yaml
  risk:
    enabled: true
    intervention_threshold: 0.80
  judge:
    enabled: false        # off by default — see cost design in ROADMAP.md
    model: independent-model
  budget:
    enabled: true
    max_cost: 2.00
  human_approval:
    enabled: true
  on_sidecar_failure: fail_closed   # or fail_open — see ROADMAP.md
```

## Python API (implemented)

v0.1 (Policy Advisor + Risk Evaluator, Observe mode):

```python
from agentic_sidecar import Sidecar
from agentic_sidecar.adapters.langgraph import attach
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule
from agentic_sidecar.gate.risk import RiskEvaluator, RiskRule

sidecar = Sidecar(
    on_sidecar_failure="fail_closed",  # required, no default -- see Design Constraints
    policy=PolicyAdvisor([PolicyRule(tool="delete_*", effect="deny")]),
    risk=RiskEvaluator(
        [RiskRule(tool="issue_refund", arg_name="amount", arg_op="gt", arg_value=500, risk="HIGH")]
    ),
)

# Wrap the tools you'd otherwise pass straight to
# langgraph.prebuilt.create_react_agent(model, tools=...) -- every call is
# evaluated by the Sidecar first.
tools = attach(sidecar, [read_order, issue_refund, delete_customer_record])
agent = create_react_agent(model, tools=tools)

# mode="observe" is the default: agent.invoke(...) still executes every
# tool call. Nothing is enforced -- inspect what the Sidecar would have
# decided:
for context, decision in sidecar.decisions:
    print(decision.status, decision.risk, context.tool_name, decision.reason)
```

v0.2 adds Intent Guardian and Govern mode, where `BLOCK` is actually
enforced -- the refund-limit scenario from concept.md §9:

```python
from agentic_sidecar import Sidecar, SidecarBlockedError
from agentic_sidecar.adapters.langgraph import attach
from agentic_sidecar.intent.alignment import ConstraintBinding, IntentGuardian
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester

envelope = IntentEnvelope(
    goal="refund_customer",
    requested_by=Requester(type="human", id="user123"),
    constraints={"maximum_refund": 500},
)
binding = ConstraintBinding(
    constraint="maximum_refund", tool="issue_refund", arg_name="amount", op="lte"
)

sidecar = Sidecar(
    on_sidecar_failure="fail_closed",
    roles=["policy", "risk", "intent_guardian"],
    intent=IntentGuardian(envelope, [binding]),
    mode="govern",  # a BLOCK now actually stops the call
)
tools = attach(sidecar, [issue_refund])
agent = create_react_agent(model, tools=tools)

try:
    agent.invoke({"messages": [("user", "Refund order A100 for $850.")]})
except SidecarBlockedError as exc:
    print(exc)  # "Sidecar blocked 'issue_refund'(...): Intent Guardian: ..."
```

`sidecar.set_intent(guardian)` swaps the active envelope between tasks --
`IntentEnvelope`s are meant to be per-task (concept.md §6), not fixed for a
Sidecar's whole lifetime.

`Sidecar.before_tool_call` registers a custom hook that fully replaces the
default Policy + Risk + Intent Guardian evaluation:

```python
@sidecar.before_tool_call
def evaluate_action(context):
    if context.tool_name == "delete_customer_record":
        return Decision(status="BLOCK", risk="HIGH", reason="never allowed")
    return Decision(status="ALLOW", risk="LOW", reason="ok")
```

Note the shape: `agentic_sidecar.adapters.langgraph.attach(sidecar, tools)`,
not `sidecar.attach(my_agent)`. `core/` intentionally has zero dependency on
`adapters/` (see AGENTS.md's Package Boundaries), so wrapping a specific
framework's decision boundaries is the adapter's job, not a generic method
on `Sidecar`. The "Planned Python API" below is the longer-term target this
is expected to grow toward once framework independence has actually been
proven (ROADMAP.md's Design Constraint 1) — not a regression.

## Planned Python API

This is the longer-term target developer experience once a second framework
adapter exists and `roles` covers Planner/Critic too (v0.3) —
**not yet implemented**. `roles=["intent_guardian", "policy", "risk"]` and
`Sidecar(...)` construction already work today (see [Python API
(implemented)](#python-api-implemented) above); what's still aspirational
here is specifically `sidecar.attach(my_agent)` wrapping the *whole* agent
generically (today it's per-adapter, e.g.
`agentic_sidecar.adapters.langgraph.attach`) and `sidecar.evaluate(intent=,
action=, risk=)`'s keyword-argument call shape:

```python
from agentic_sidecar import Sidecar

sidecar = Sidecar(roles=["intent_guardian", "policy", "risk", "planner", "critic"])
agent = sidecar.attach(my_agent)

agent.run("Investigate the production issue but do not modify production.")
```

```python
@sidecar.before_tool_call
def evaluate_action(context):
    return sidecar.evaluate(
        intent=context.intent,
        action=context.tool_call,
        risk=context.risk,
    )
```

```python
Decision(
    status="REPLAN",
    risk="HIGH",
    reason="Action exceeds original user intent",
)
```

## Operating modes

| Mode | Behavior |
| --- | --- |
| **Observe** | Sidecar monitors and logs; cannot affect execution. **Implemented (v0.1).** |
| **Advise** | Sidecar returns a recommendation; the agent decides whether to follow it. |
| **Govern** | Sidecar's Decision Gate can allow, warn, or block for real. **Implemented (v0.2)** — `replan`/`pause` outcomes arrive at v0.4. |
| **Human-supervised** | High-risk decisions route to a human for approve/reject. Planned v0.4. |

Modes are meant to be adopted in that order — organizations start in Observe
and move to Govern once they trust the signal.

## Long-term: an intent propagation layer

The nearer-term modules above are the whole of what v0.1–v0.8 ship. But the
`IntentEnvelope` (§ [Sidecar modules](#sidecar-modules)) is designed to
survive being handed off — not just checked once and discarded:

```text
Human
  │
  └── Intent Envelope #182
            │
            ▼
         Agent A
            │
        delegates
            ▼
         Agent B
            │
           MCP
            ▼
         Agent C
            │
           Tool
```

If every hop in a delegation chain can answer *what was originally
requested, who authorized it, what constraints apply, what authority was
actually delegated, and whether intent has since changed* — that's no
longer just a feature of one package. It's closer to an interoperability
concern for autonomous systems generally, which is why v1.0 targets
publishing the envelope as a versioned schema in `ai-operations-spec`
rather than keeping it as an internal Sidecar structure (see the v1.0 entry
in [ROADMAP.md](ROADMAP.md#build-order)).
This is explicitly a v1.0 target, not something v0.1 needs to anticipate —
noted here because it's the reason the envelope's shape deserves care early,
even though nothing consumes it across process boundaries yet.

## The DeepAgentLabs ecosystem

```text
                 DeepAgentLabs
              Autonomous AI Systems
                      │
        ┌─────────────┼─────────────┐
        │             │             │
     OBSERVE         GUIDE        CONNECT
        │             │             │
 AgenticLens    Agentic Sidecar  Agentic MCP
        │             │             │
        └─────────────┼─────────────┘
                      │
                     TEST
                      │
                Agentic Chaos
```

| Project | Question it answers |
| --- | --- |
| [AgenticLens](https://github.com/DeepAgentLabs/agenticlens) | What did the agent do, and what happened? |
| [Agentic Chaos](https://github.com/DeepAgentLabs/agentic-chaos) | How does the agent behave when things go wrong? |
| [Agentic MCP](https://github.com/DeepAgentLabs/mcp-server) | How does the agent interact with tools and external capabilities? |
| [AgenticOps Control Tower](https://github.com/DeepAgentLabs/agenticops-control-tower) | What is deployed, what governance posture exists across agents, and how do operators manage it centrally? |
| **Agentic Sidecar** | Should the agent continue with this decision, and is it still acting according to intent? |

Each project is independently installable; none requires another as a hard
dependency (see [Cross-Project Dependencies](ROADMAP.md#cross-project-dependencies)
in the roadmap).

## Roadmap

Full build plan, version sequencing, and design constraints:
[ROADMAP.md](ROADMAP.md).

Original architecture proposal: [concept.md](concept.md).

## License

MIT (planned — `LICENSE` file to be added alongside the first code commit,
matching sibling DeepAgentLabs projects).
