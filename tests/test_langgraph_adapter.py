"""Tests for `agentic_sidecar.adapters.langgraph`.

These exercise the wrapping/interception logic directly against plain
Python callables -- no `langgraph` install required (the adapter module has
no import-time dependency on the `langgraph` package; see its docstring).
An end-to-end example against a real LangGraph graph lives in `examples/`.
"""

import inspect
from datetime import datetime, timedelta, timezone

import pytest

from agentic_sidecar.adapters.langgraph import _bind_args, attach
from agentic_sidecar.core.exceptions import SidecarBlockedError
from agentic_sidecar.core.sidecar import Sidecar
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule
from agentic_sidecar.gate.risk import RiskEvaluator, RiskRule
from agentic_sidecar.intent.alignment import ConstraintBinding, IntentGuardian
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester


def read_order(order_id: str) -> str:
    """Look up an order by id."""
    return f"order {order_id}: shipped"


def issue_refund(order_id: str, amount: float) -> str:
    """Issue a refund for an order."""
    return f"refunded {amount} for {order_id}"


def test_wrapped_tool_preserves_name_and_docstring() -> None:
    sidecar = Sidecar(on_sidecar_failure="fail_closed")
    (wrapped,) = attach(sidecar, [read_order])
    assert wrapped.__name__ == "read_order"
    assert wrapped.__doc__ == "Look up an order by id."


def test_wrapped_tool_still_returns_the_real_result() -> None:
    sidecar = Sidecar(on_sidecar_failure="fail_closed")
    (wrapped,) = attach(sidecar, [read_order])
    assert wrapped(order_id="A100") == "order A100: shipped"


def test_wrapped_call_is_recorded_as_a_decision() -> None:
    sidecar = Sidecar(on_sidecar_failure="fail_closed")
    (wrapped,) = attach(sidecar, [read_order])
    wrapped(order_id="A100")
    assert len(sidecar.decisions) == 1
    context, decision = sidecar.decisions[0]
    assert context.tool_name == "read_order"
    assert context.tool_args == {"order_id": "A100"}
    assert decision.status == "ALLOW"


def test_positional_and_keyword_args_both_bind_correctly() -> None:
    sidecar = Sidecar(on_sidecar_failure="fail_closed")
    (wrapped,) = attach(sidecar, [issue_refund])
    wrapped("A100", 850.0)
    context, _ = sidecar.decisions[0]
    assert context.tool_args == {"order_id": "A100", "amount": 850.0}


def test_observe_mode_still_executes_a_blocked_call() -> None:
    """v0.1 is Observe mode only -- a BLOCK decision is logged/recorded but
    does not stop the wrapped call (ROADMAP.md's v0.1 scope)."""
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        policy=PolicyAdvisor([PolicyRule(tool="issue_refund", effect="deny")]),
    )
    (wrapped,) = attach(sidecar, [issue_refund])

    result = wrapped(order_id="A100", amount=850.0)

    assert result == "refunded 850.0 for A100"
    _, decision = sidecar.decisions[0]
    assert decision.status == "BLOCK"


def test_high_risk_argument_pattern_is_still_observed_only() -> None:
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        risk=RiskEvaluator(
            [
                RiskRule(
                    tool="issue_refund", arg_name="amount", arg_op="gt", arg_value=500, risk="HIGH"
                )
            ]
        ),
    )
    (wrapped,) = attach(sidecar, [issue_refund])

    wrapped(order_id="A100", amount=850.0)

    _, decision = sidecar.decisions[0]
    assert decision.status == "BLOCK"
    assert decision.risk == "HIGH"


def test_govern_mode_blocks_and_does_not_call_the_real_tool() -> None:
    executed = []

    def issue_refund_tracked(order_id: str, amount: float) -> str:
        executed.append((order_id, amount))
        return f"refunded {amount} for {order_id}"

    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        policy=PolicyAdvisor([PolicyRule(tool="issue_refund_tracked", effect="deny")]),
        mode="govern",
    )
    (wrapped,) = attach(sidecar, [issue_refund_tracked])

    with pytest.raises(SidecarBlockedError) as exc_info:
        wrapped(order_id="A100", amount=850.0)

    assert executed == []
    assert exc_info.value.decision.status == "BLOCK"
    assert exc_info.value.context.tool_name == "issue_refund_tracked"


def test_govern_mode_block_exception_carries_the_evaluated_context() -> None:
    """`SidecarBlockedError.context` must reflect what Intent Guardian
    actually saw (injected intent/history), not the bare pre-evaluation
    context the adapter originally built."""
    envelope = IntentEnvelope(
        goal="refund_customer",
        requested_by=Requester(id="user123"),
        constraints={"maximum_refund": 500},
    )
    binding = ConstraintBinding(
        constraint="maximum_refund", tool="issue_refund", arg_name="amount", op="lte"
    )
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        roles=["policy", "risk", "intent_guardian"],
        intent=IntentGuardian(envelope, [binding]),
        mode="govern",
    )
    (wrapped,) = attach(sidecar, [issue_refund])

    with pytest.raises(SidecarBlockedError) as exc_info:
        wrapped(order_id="A100", amount=850.0)

    assert exc_info.value.context.intent is not None
    assert exc_info.value.context.intent.goal == "refund_customer"


def test_govern_mode_still_allows_a_permitted_call() -> None:
    sidecar = Sidecar(on_sidecar_failure="fail_closed", mode="govern")
    (wrapped,) = attach(sidecar, [read_order])
    assert wrapped(order_id="A100") == "order A100: shipped"


def test_govern_mode_does_not_block_on_warn() -> None:
    """WARN is advisory in both modes -- only BLOCK stops the call."""
    past = datetime.now(timezone.utc) - timedelta(days=1)
    envelope = IntentEnvelope(
        goal="refund_customer", requested_by=Requester(id="user123"), expires=past
    )
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        roles=["policy", "risk", "intent_guardian"],
        intent=IntentGuardian(envelope),
        mode="govern",
    )
    (wrapped,) = attach(sidecar, [issue_refund])

    result = wrapped(order_id="A100", amount=10.0)

    assert result == "refunded 10.0 for A100"
    _, decision = sidecar.decisions[0]
    assert decision.status == "WARN"


def test_bind_args_falls_back_to_raw_kwargs_on_mismatch() -> None:
    """A call that doesn't bind against the tool's declared signature
    shouldn't crash Decision Context construction -- fall back to the raw
    kwargs rather than raising (see `_bind_args`'s docstring comment)."""
    signature = inspect.signature(read_order)
    result = _bind_args(signature, (), {"unexpected": "extra"})
    assert result == {"unexpected": "extra"}


def test_attach_returns_a_new_list_without_mutating_input() -> None:
    sidecar = Sidecar(on_sidecar_failure="fail_closed")
    tools = [read_order, issue_refund]
    wrapped = attach(sidecar, tools)
    assert wrapped is not tools
    assert wrapped[0] is not read_order
    assert tools == [read_order, issue_refund]
