# Examples

One runnable script per shipped capability, added in the same PR as the
code it demonstrates (see [../ROADMAP.md](../ROADMAP.md)).

## v0.1 — Sidecar Runtime + Rule-Based Decision Gate

[`langgraph_refund_observe_mode.py`](langgraph_refund_observe_mode.py) --
a real `langgraph.prebuilt.create_react_agent` agent with a plain LangGraph
adapter (`agentic_sidecar.adapters.langgraph.attach`) wired up, showing the
v0.1 rule-based Decision Gate (Policy Advisor + Risk Evaluator, zero LLM
calls) evaluate two proposed tool calls in Observe mode: a refund over its
authorized amount and a destructive delete blocked by policy. Both actions
still execute -- Observe mode only logs what the Sidecar *would* have
decided; Govern mode (where `BLOCK` actually stops the call) ships in v0.2.

Uses a small scripted chat model instead of a real LLM provider, so it runs
deterministically offline with no API key.

```bash
uv sync --extra dev --extra langgraph
uv run python examples/langgraph_refund_observe_mode.py
```

## v0.2 — Intent Guardian

[`langgraph_intent_guardian_govern_mode.py`](langgraph_intent_guardian_govern_mode.py)
-- the refund-limit scenario from concept.md §9, but in Govern mode: an
`IntentEnvelope` with a `maximum_refund: 500` constraint, bound to
`issue_refund`'s `amount` argument via a `ConstraintBinding`. A refund
request for $850 raises `SidecarBlockedError` *before* the real tool
runs -- unlike the v0.1 example, the call genuinely never executes. A
second, compliant $120 refund goes through normally.

```bash
uv sync --extra dev --extra langgraph
uv run python examples/langgraph_intent_guardian_govern_mode.py
```
