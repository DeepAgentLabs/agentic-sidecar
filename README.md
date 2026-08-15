# agentic-sidecar

**A companion intelligence and real-time supervision layer for autonomous AI agents.**

> The Main Agent acts. The Sidecar observes, thinks, advises, and governs.

## Status

**Concept / pre-implementation.** This repository currently contains the
architecture proposal ([`concept.md`](concept.md)) and this README
— no package code, no PyPI release, no CI yet. See
[ROADMAP.md](ROADMAP.md) for the build plan, starting with a narrow,
LLM-free v0.1.

## Contents

- [Why](#why)
- [What it is not](#what-it-is-not)
- [Architecture](#architecture)
- [Sidecar vs. Agent Harness](#sidecar-vs-agent-harness)
- [Main Agent vs. Sidecar](#main-agent-vs-sidecar)
- [How the Decision Gate evaluates a decision](#how-the-decision-gate-evaluates-a-decision)
- [Sidecar modules](#sidecar-modules)
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
the rest (see [Design Constraints](ROADMAP.md#design-constraints-read-before-building-v01)
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
[ROADMAP.md](ROADMAP.md)). Intent is the one that requires understanding
what the user actually meant, and it's where the project's distinctive
value lives.

The diagram above shows the target outcome set. **v0.1 ships a narrower
slice**: only `ALLOW`/`BLOCK`, in Observe mode — the Sidecar logs what it
*would* have decided but cannot yet stop an action in practice. `WARN`,
`CHALLENGE`, `REPLAN`, `PAUSE`, and `ESCALATE` arrive across v0.2–v0.4 as
Intent Guardian and the full Decision Gate ship. Version-by-version build
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

## Planned Python API

This is the target developer experience — **not yet implemented** (tracked
as v0.1 in [ROADMAP.md](ROADMAP.md)):

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
| **Observe** | Sidecar monitors and logs; cannot affect execution. |
| **Advise** | Sidecar returns a recommendation; the agent decides whether to follow it. |
| **Govern** | Sidecar's Decision Gate can allow, warn, replan, pause, or block. |
| **Human-supervised** | High-risk decisions route to a human for approve/reject. |

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
