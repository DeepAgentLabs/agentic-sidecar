"""Runnable example: a real LangGraph tool-calling agent with
`agentic-sidecar` attached via the v0.1 LangGraph adapter, in Observe mode.

Requires the `langgraph` extra:

    uv sync --extra langgraph
    # or: pip install agentic-sidecar[langgraph]

Run:

    uv run python examples/langgraph_refund_observe_mode.py

This script uses a small scripted chat model instead of a real LLM provider
so it runs deterministically and offline, with no API key required -- the
point of the example is the Sidecar's interception behavior, not model
quality.

What it demonstrates:
  - Policy Advisor blocking a destructive tool outright (`delete_customer_record`)
  - Risk Evaluator flagging a refund that exceeds its authorized amount
  - Observe mode (v0.1's scope): both proposed actions are still executed --
    the Sidecar only *logs* what it would have decided. Govern mode, where a
    BLOCK actually stops the call, ships in v0.2 (see ROADMAP.md).
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

# create_react_agent moved to langchain.agents.create_agent in LangGraph
# 1.0+ (still functional here, just deprecated) -- kept as the import here
# so this example only needs the `langgraph` extra, not the heavier
# `langchain` package.
from langgraph.prebuilt import create_react_agent

from agentic_sidecar import Sidecar
from agentic_sidecar.adapters.langgraph import attach
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule
from agentic_sidecar.gate.risk import RiskEvaluator, RiskRule

logging.basicConfig(level=logging.INFO, format="%(message)s")


# --- Tools the agent can call ------------------------------------------------


def look_up_order(order_id: str) -> str:
    """Look up an order's status and total."""
    return f"order {order_id}: status=delivered, total=$120.00"


def issue_refund(order_id: str, amount: float) -> str:
    """Issue a refund for an order."""
    return f"refunded ${amount:.2f} for order {order_id}"


def delete_customer_record(customer_id: str) -> str:
    """Permanently delete a customer's record."""
    return f"deleted customer {customer_id}"


# --- A scripted chat model, so this example runs with no API key ------------


class ScriptedToolCallingModel(BaseChatModel):
    """Replays a fixed sequence of `AIMessage`s instead of calling a real LLM
    provider -- just enough surface for `create_react_agent` to drive a real
    tool-calling loop deterministically and offline.
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


def main() -> None:
    # v0.1 Decision Gate: deterministic rules, zero LLM calls (ROADMAP.md's
    # Design Constraint 2). These could just as easily come from
    # PolicyAdvisor.from_yaml("policies.yaml") / RiskEvaluator.from_yaml(...).
    policy = PolicyAdvisor(
        [
            PolicyRule(
                tool="delete_*",
                effect="deny",
                reason="Destructive operations are never permitted by policy",
            )
        ]
    )
    risk = RiskEvaluator(
        [
            RiskRule(
                tool="issue_refund",
                arg_name="amount",
                arg_op="gt",
                arg_value=500,
                risk="HIGH",
                reason="Refund exceeds the standard $500 authorization limit",
            )
        ]
    )

    # fail_closed: if the Sidecar itself errors, block rather than silently
    # let an unevaluated action through (ROADMAP.md's Design Constraint 3).
    sidecar = Sidecar(on_sidecar_failure="fail_closed", policy=policy, risk=risk)

    tools = attach(sidecar, [look_up_order, issue_refund, delete_customer_record])

    model = ScriptedToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "issue_refund",
                        "args": {"order_id": "A100", "amount": 850.0},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "delete_customer_record",
                        "args": {"customer_id": "C42"},
                        "id": "call_2",
                    }
                ],
            ),
            AIMessage(content="Done: refunded order A100 and removed customer C42's record."),
        ]
    )
    agent = create_react_agent(model, tools=tools)

    print("--- Running agent (Observe mode: Sidecar logs decisions, never blocks) ---\n")
    result = agent.invoke(
        {"messages": [("user", "Refund order A100 for $850 and delete customer C42's record.")]}
    )

    print("\n--- Final agent message ---")
    print(result["messages"][-1].content)

    print("\n--- Sidecar decision log (what Govern mode, v0.2+, would enforce) ---")
    for context, decision in sidecar.decisions:
        print(
            f"{decision.status:>5}  risk={decision.risk!s:<6}  "
            f"{context.tool_name}({context.tool_args})  -- {decision.reason}"
        )


if __name__ == "__main__":
    main()
