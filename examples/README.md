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

## v0.4 — Budget Guardian + Human Escalation + Decision Provenance

[`v0_4_budget_and_escalation.py`](v0_4_budget_and_escalation.py) --
demonstrates the v0.4 human-in-the-loop escalation workflow: a Budget Guardian
tracks cost/token limits per task and returns a PAUSE decision when limits are
exceeded, triggering structured approval workflows. Includes Decision Provenance
(audit trails with JSON serialization) and all seven decision outcomes (ALLOW,
WARN, BLOCK, CHALLENGE, REPLAN, PAUSE, ESCALATE).

Key features:
- Budget Guardian: cost and token ceiling enforcement
- Human Escalation: EscalationRequest/ApprovalResponse workflow
- Decision Provenance: full audit trail with DecisionTrigger, DecisionRationale, CausalLink
- Seven-outcome Decision Gate

```bash
python examples/v0_4_budget_and_escalation.py
```

## v0.5 — Status Narration + CLI

### Python API Example

[`v0_5_status_narration.py`](v0_5_status_narration.py) --
demonstrates StatusNarrator for live agent execution narration:

- **Human-readable narration**: Translates tool calls into emoji-based narrative
  (e.g., `search` → "🔍 Searching for information")
- **Decision tracking**: Records ALLOW/WARN/BLOCK/PAUSE outcomes with risk levels
- **Intent compliance**: Detects and reports intent drift
- **Budget monitoring**: Tracks remaining costs and tokens
- **Pause/resume**: Workflow for human escalation and approval

Six comprehensive examples covering:
1. Basic narration
2. Decision tracking
3. Budget tracking
4. Intent compliance
5. Pause and resume
6. Complete workflow

```bash
python examples/v0_5_status_narration.py
```

### CLI Usage Guide

[`v0_5_cli_guide.md`](v0_5_cli_guide.md) --
complete guide to the `agentic-sidecar` command-line tool:

```bash
# Single status snapshot
agentic-sidecar status

# Live status stream (real-time updates, Ctrl+C to stop)
agentic-sidecar status --follow

# JSON output for integration with other tools
agentic-sidecar status --json

# Custom refresh interval
agentic-sidecar status --follow --interval 2

# Interactive demo
agentic-sidecar demo

# Show version
agentic-sidecar version
```

Features:
- Live agent monitoring with Rich terminal formatting
- JSON output for tool integration
- Emoji-based narration with decision indicators
- Real-time budget/token tracking
- Custom refresh intervals
