"""Tests for `agentic_sidecar.core.exceptions.SidecarBlockedError`."""

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.core.decision import Decision
from agentic_sidecar.core.exceptions import SidecarBlockedError


def test_message_includes_tool_name_args_and_reason() -> None:
    context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 850.0})
    decision = Decision(status="BLOCK", risk="HIGH", reason="exceeds refund limit")
    error = SidecarBlockedError(decision, context)
    assert "issue_refund" in str(error)
    assert "850.0" in str(error)
    assert "exceeds refund limit" in str(error)
    assert error.decision is decision
    assert error.context is context


def test_is_a_runtime_error() -> None:
    context = DecisionContext(tool_name="anything")
    decision = Decision(status="BLOCK", risk=None, reason="blocked")
    assert isinstance(SidecarBlockedError(decision, context), RuntimeError)
