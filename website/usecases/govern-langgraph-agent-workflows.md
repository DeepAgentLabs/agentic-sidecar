# Govern LangGraph Agent Workflows with Sidecar Adapter

Attach Agentic Sidecar's native LangGraph adapter to intercept graph tool invocations and enforce intent constraints in govern mode without changing core agent logic.

| | |
|---|---|
| **For** | LangGraph agent developers adding real-time decision supervision |
| **Difficulty** | Intermediate |
| **Time** | ~15 minutes |
| **Capabilities** | [LangGraph Adapter](https://deepagentlabs.io/agentic-sidecar/docs/integrations/#langgraph), [Intent Guardian](https://deepagentlabs.io/agentic-sidecar/docs/features/#intent-guardian) |
| **Status** | Stable |

## The problem

LangGraph agents organize complex LLM applications into state graphs where nodes execute tool calls autonomously. While LangGraph provides workflow control, it does not evaluate whether tool parameters chosen by the LLM comply with runtime user authorization limits, financial risk boundaries, or organization policies.

Attempting to embed hardcoded validation logic inside every LangGraph tool or node couples governance rules to agent orchestration. Furthermore, modifying graph nodes directly prevents reusing tools across different security roles or operating modes.

## Architecture

<figure class="refund-flow lg-flow" data-langgraph-flow aria-labelledby="lg-flow-title">
  <div class="refund-flow-header"><div><span class="refund-eyebrow">LANGGRAPH ADAPTER / GOVERN MODE</span><h3 id="lg-flow-title">Keep the graph. Govern the tool boundary.</h3></div><span class="refund-sim-label">Browser-only illustration</span></div>
  <div class="refund-controls"><div><button type="button" data-lg-play hidden>Pause animation</button><button type="button" data-lg-replay hidden>Replay example</button></div><span data-lg-playback>Illustrative result · $850 request blocked</span></div>
  <label class="lg-picker" data-lg-picker hidden>Example request<select data-lg-select><option value="850" selected>$850 · exceeds the authorized limit</option><option value="120">$120 · within the authorized limit</option></select></label>
  <div class="refund-progress" aria-hidden="true"><span></span></div>
  <div class="lg-setup"><span>WIRE ONCE / BEFORE GRAPH CREATION</span><code>governed_tools = attach(sidecar, [issue_refund])</code><i aria-hidden="true">↓</i><code>create_react_agent(model, tools=governed_tools)</code><small>Core graph logic stays unchanged. The adapter wraps the callable tools.</small></div>
  <div class="lg-intent"><span>AUTHORIZED INTENT</span><p><strong>refund_customer</strong> · requester <code>user123</code> · order <code>A100</code></p><code>issue_refund.amount ≤ maximum_refund ($500)</code><small>Policy: default allow · Risk: LOW · Sidecar failure: fail_closed</small></div>
  <div class="lg-map">
    <ol class="lg-stages">
      <li class="lg-node lg-blue" data-lg-node="0"><div class="lg-node-top"><span>01 / GRAPH AGENT NODE</span><span class="lg-check" aria-label="Complete">✓</span></div><i class="lg-icon" aria-hidden="true">◈</i><h4>A model proposes a call.</h4><code>AIMessage.tool_calls</code><p data-lg-call>issue_refund("A100", 850)</p><small data-lg-status="0">TOOL CALL EMITTED</small></li>
      <li class="lg-node lg-purple" data-lg-node="1"><div class="lg-node-top"><span>02 / SIDECAR ADAPTER</span><span class="lg-check" aria-label="Complete">✓</span></div><i class="lg-icon" aria-hidden="true">⇄</i><h4>Intercept before execution.</h4><code>governed_tools</code><p>The wrapped callable checks the proposed arguments before invoking the original tool.</p><small data-lg-status="1">BOUNDARY INTERCEPTED</small></li>
      <li class="lg-node lg-teal failed" data-lg-node="2"><div class="lg-node-top"><span>03 / INTENT GUARDIAN</span><span class="lg-check" aria-label="Constraint violated">×</span></div><i class="lg-icon" aria-hidden="true">◇</i><h4 data-lg-verdict>BLOCK</h4><code data-lg-comparison>$850 &gt; $500</code><p data-lg-intent-detail>The amount violates the user-authorized maximum. Risk remains LOW.</p><small data-lg-status="2">INTENT CONSTRAINT VIOLATED</small></li>
      <li class="lg-node lg-amber skipped" data-lg-node="3"><div class="lg-node-top"><span>04 / ORIGINAL TOOL</span><span class="lg-check" aria-label="Not called">–</span></div><i class="lg-icon" aria-hidden="true">⌁</i><h4 data-lg-tool-title>Tool not called.</h4><code>issue_refund()</code><p data-lg-tool-detail>The block prevents the original callable from executing.</p><small data-lg-status="3">NOT DISPATCHED</small></li>
      <li class="lg-node lg-red" data-lg-node="4"><div class="lg-node-top"><span>05 / GRAPH OUTCOME</span><span class="lg-check" aria-label="Complete">✓</span></div><i class="lg-icon" aria-hidden="true">↩</i><h4 data-lg-outcome>Exception reaches the caller.</h4><code data-lg-return-code>SidecarBlockedError</code><p data-lg-return-detail>The surrounding try/except catches the blocked invocation. No successful final reply is produced.</p><small data-lg-status="4">agent.invoke RAISES</small></li>
      <li class="lg-node lg-green active" data-lg-node="5"><div class="lg-node-top"><span>06 / DECISION PROVENANCE</span><span class="lg-check" aria-label="Complete">✓</span></div><i class="lg-icon" aria-hidden="true">▤</i><h4>The verdict stays inspectable.</h4><code>sidecar.decisions</code><p data-lg-record-summary>BLOCK · issue_refund · risk LOW · Intent Guardian constraint violation.</p><small data-lg-status="5">ILLUSTRATIVE DECISION LOG</small></li>
    </ol>
  </div>
  <div class="lg-story" role="status" aria-live="off"><div><span class="refund-eyebrow" data-lg-phase>06 / DECISION PROVENANCE</span><h4 data-lg-heading>Blocked at the tool boundary.</h4><p data-lg-story>The $850 attempt raises SidecarBlockedError before the real tool runs. The graph’s host handles the exception.</p></div><div class="lg-metrics"><div><b data-lg-calls>0</b><span>Simulated tool calls</span></div><div><b data-lg-funds>$0</b><span>Simulated funds issued</span></div></div></div>
  <details class="lg-record"><summary>Inspect the illustrative graph result</summary><pre data-lg-record>{"simulation":true,"amount":850,"decision":"BLOCK","risk":"LOW","reason":"maximum_refund constraint violated","tool_executed":false,"exception":"SidecarBlockedError","final_message":null}</pre></details>
  <figcaption>Animated illustration of the scripted LangGraph example below: $850 is blocked by the intent constraint; $120 runs and returns “Refund issued.” Both have default LOW risk. Setup wraps the tools before graph creation; it does not modify graph logic. No model, LangGraph runtime or payment API is invoked by this animation.</figcaption>
</figure>

## Prerequisites

- Python 3.10+ (Python 3.12 recommended)
- `agentic-sidecar` package with `langgraph` extra dependencies installed:
  ```bash
  pip install "agentic-sidecar[langgraph]"
  ```
- Runnable script: [`examples/langgraph_intent_guardian_govern_mode.py`](https://github.com/DeepAgentLabs/agentic-sidecar/tree/main/examples/langgraph_intent_guardian_govern_mode.py)

## Walkthrough

### 1. Install Required Extra Dependencies

Install `agentic-sidecar` with LangGraph adapter support:

```bash
uv sync --extra langgraph
# Or with pip:
pip install "agentic-sidecar[langgraph]"
```

### 2. Define LangGraph Tool and Scripted Model

Define the target tool `issue_refund` and import LangGraph components:

```python
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.prebuilt import create_react_agent

def issue_refund(order_id: str, amount: float) -> str:
    """Issue a refund for an order."""
    return f"refunded ${amount:.2f} for order {order_id}"


class ScriptedToolCallingModel(BaseChatModel):
    """Replays a fixed sequence of `AIMessage`s -- see
    `langgraph_refund_observe_mode.py` for why this exists.
    """

    responses: list[AIMessage]
    step: int = 0

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedToolCallingModel":
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        message = self.responses[self.step]
        self.step += 1
        return ChatResult(generations=[ChatGeneration(message=message)])

    @property
    def _llm_type(self) -> str:
        return "scripted"


def refund_request(order_id: str, amount: float) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "issue_refund",
                "args": {"order_id": order_id, "amount": amount},
                "id": "call_1",
            }
        ],
    )
```

### 3. Build Intent Envelope and Constraint Bindings

Create an `IntentEnvelope` authorizing refunds up to $500.00 and bind the constraint to the `issue_refund` tool's `amount` argument:

```python
from agentic_sidecar import Sidecar, SidecarBlockedError
from agentic_sidecar.adapters.langgraph import attach
from agentic_sidecar.intent import ConstraintBinding, IntentEnvelope, IntentGuardian, Requester

# Define authorized intent envelope
envelope = IntentEnvelope(
    goal="refund_customer",
    requested_by=Requester(type="human", id="user123"),
    constraints={"maximum_refund": 500.0},
)

# Bind constraint to tool argument
binding = ConstraintBinding(
    constraint="maximum_refund",
    tool="issue_refund",
    arg_name="amount",
    op="lte",
)
guardian = IntentGuardian(envelope, [binding])

# Initialize Sidecar runtime in GOVERN mode
sidecar = Sidecar(
    on_sidecar_failure="fail_closed",
    roles=["policy", "risk", "intent_guardian"],
    intent=guardian,
    mode="govern",
)
```

### 4. Attach Adapter to LangGraph Tools

Wrap the tool array using `attach(sidecar, tools)` before instantiating the LangGraph agent:

```python
# Wrap tools with Agentic Sidecar governance adapter
governed_tools = attach(sidecar, [issue_refund])

# Pass governed tools directly into LangGraph create_react_agent
model = ScriptedToolCallingModel(responses=[refund_request("A100", 850.0)])
agent = create_react_agent(model, tools=governed_tools)
```

### 5. Execute Graph and Enforce Governance

Invoke the agent with an out-of-bounds request ($850.00) followed by a valid request ($120.00):

```python
# Attempt 1: $850.00 refund (Exceeds $500.00 limit) -> Raises SidecarBlockedError
try:
    agent.invoke({"messages": [("user", "Refund order A100 for $850.")]})
except SidecarBlockedError as exc:
    print(f"Blocked before tool ran: {exc}")

# Attempt 2: $120.00 refund (Within limit) -> Allowed
model = ScriptedToolCallingModel(
    responses=[refund_request("A100", 120.0), AIMessage(content="Refund issued.")]
)
agent = create_react_agent(model, tools=governed_tools)
result = agent.invoke({"messages": [("user", "Refund order A100 for $120.")]})
print(f"Agent response: {result['messages'][-1].content}")
```

## Expected output

Run the complete runnable example script:

```bash
uv run --extra langgraph python examples/langgraph_intent_guardian_govern_mode.py
```

Console Output:

```
--- Attempt 1: refund of $850 (exceeds the $500 authorization) ---
[GOVERN] BLOCK tool=issue_refund args={'order_id': 'A100', 'amount': 850.0} risk=LOW reason=Intent Guardian: 'amount'=850.0 on 'issue_refund' violates constraint 'maximum_refund' (must be lte 500)
Blocked before the real tool ran: Sidecar blocked 'issue_refund'({'order_id': 'A100', 'amount': 850.0}): Intent Guardian: 'amount'=850.0 on 'issue_refund' violates constraint 'maximum_refund' (must be lte 500)

--- Attempt 2: refund of $120 (within the $500 authorization) ---
Final agent message: Refund issued.

--- Sidecar decision log ---
BLOCK  issue_refund({'order_id': 'A100', 'amount': 850.0})  -- Intent Guardian: 'amount'=850.0 on 'issue_refund' violates constraint 'maximum_refund' (must be lte 500)
ALLOW  issue_refund({'order_id': 'A100', 'amount': 120.0})  -- Policy Advisor: No policy rule matched tool 'issue_refund'; default effect is 'allow'; Risk Evaluator: No risk rule matched tool 'issue_refund'; default risk is 'LOW'; Intent Guardian: No intent constraints violated for 'issue_refund'
```

## Verify it worked

1. Verify that `SidecarBlockedError` is thrown on Attempt 1 ($850.00 refund), preventing tool execution.
2. Confirm that Attempt 2 ($120.00 refund) completes successfully and returns `"Refund issued."`.
3. Check the decision log output to confirm `BLOCK` and `ALLOW` statuses recorded in `sidecar.decisions`.

## Clean up

To remove installed extras or deactivate virtual environment:

```bash
deactivate
```

## Variations and next steps

- **Observe Mode Auditing**: Run in `mode="observe"` first to monitor LangGraph tool calls without blocking graph transitions.
- Learn more in [Integrations Documentation](https://deepagentlabs.io/agentic-sidecar/docs/integrations/#langgraph) and [Features](https://deepagentlabs.io/agentic-sidecar/docs/features/#intent-guardian).

## Tested with

- agentic-sidecar 0.7.0, LangGraph 1.x (`>=1.0,<2`), Python 3.12, Ubuntu 24.04, verified 2026-10-15
