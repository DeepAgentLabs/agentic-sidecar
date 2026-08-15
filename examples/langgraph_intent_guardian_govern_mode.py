"""Runnable example: Intent Guardian + Govern mode actually blocking a real
LangGraph tool call -- the refund-limit scenario from concept.md §9.

Requires the `langgraph` extra:

    uv sync --extra langgraph
    # or: pip install agentic-sidecar[langgraph]

Run:

    uv run python examples/langgraph_intent_guardian_govern_mode.py

Uses a small scripted chat model instead of a real LLM provider, so it runs
deterministically and offline, with no API key required.

What it demonstrates, in contrast to `langgraph_refund_observe_mode.py`
(v0.1, Observe mode -- logs but never stops a call):
  - An `IntentEnvelope` with a `maximum_refund` constraint, bound to the
    `issue_refund` tool's `amount` argument via `ConstraintBinding`
  - `mode="govern"`: a refund over the envelope's authorized limit raises
    `SidecarBlockedError` *before* the real tool runs -- the call never
    executes
  - A refund within the limit still goes through normally
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

# create_react_agent moved to langchain.agents.create_agent in LangGraph
# 1.0+ (still functional here, just deprecated) -- kept as the import here
# so this example only needs the `langgraph` extra, not the heavier
# `langchain` package.
from langgraph.prebuilt import create_react_agent

from agentic_sidecar import Sidecar, SidecarBlockedError
from agentic_sidecar.adapters.langgraph import attach
from agentic_sidecar.intent.alignment import ConstraintBinding, IntentGuardian
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester


def issue_refund(order_id: str, amount: float) -> str:
    """Issue a refund for an order."""
    return f"refunded ${amount:.2f} for order {order_id}"


class ScriptedToolCallingModel(BaseChatModel):
    """Replays a fixed sequence of `AIMessage`s -- see
    `langgraph_refund_observe_mode.py` for why this exists.
    """

    responses: list[AIMessage]
    step: int = 0

    def bind_tools(self, tools: Any, **kwargs: Any) -> ScriptedToolCallingModel:
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


def main() -> None:
    # concept.md §6's worked example: a $500 refund authorization.
    envelope = IntentEnvelope(
        goal="refund_customer",
        requested_by=Requester(type="human", id="user123"),
        constraints={"maximum_refund": 500},
    )
    binding = ConstraintBinding(
        constraint="maximum_refund", tool="issue_refund", arg_name="amount", op="lte"
    )
    guardian = IntentGuardian(envelope, [binding])

    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        roles=["policy", "risk", "intent_guardian"],
        intent=guardian,
        mode="govern",  # v0.2: BLOCK is now enforced, not just logged
    )
    tools = attach(sidecar, [issue_refund])

    print("--- Attempt 1: refund of $850 (exceeds the $500 authorization) ---")
    agent_over_limit = create_react_agent(
        ScriptedToolCallingModel(responses=[refund_request("A100", 850.0)]), tools=tools
    )
    try:
        agent_over_limit.invoke({"messages": [("user", "Refund order A100 for $850.")]})
        print("Refund went through -- this shouldn't happen with an $850 request.")
    except SidecarBlockedError as exc:
        print(f"Blocked before the real tool ran: {exc}")

    print("\n--- Attempt 2: refund of $120 (within the $500 authorization) ---")
    agent_within_limit = create_react_agent(
        ScriptedToolCallingModel(
            responses=[refund_request("A100", 120.0), AIMessage(content="Refund issued.")]
        ),
        tools=tools,
    )
    result = agent_within_limit.invoke({"messages": [("user", "Refund order A100 for $120.")]})
    print(f"Final agent message: {result['messages'][-1].content}")

    print("\n--- Sidecar decision log ---")
    for context, decision in sidecar.decisions:
        print(
            f"{decision.status:>5}  {context.tool_name}({context.tool_args})  -- {decision.reason}"
        )


if __name__ == "__main__":
    main()
