"""Tests for `agentic_sidecar.gate.escalation` -- Human Escalation primitives."""

import pytest

from agentic_sidecar.gate.escalation import (
    ApprovalAction,
    ApprovalResponse,
    EscalationHandler,
    EscalationRequest,
)


def test_escalation_request_creation() -> None:
    request = EscalationRequest(
        decision_id="dec_123",
        reason="Budget exceeded",
        context={"tool_name": "issue_refund", "amount": 850},
        available_actions=[ApprovalAction.APPROVE_ONCE, ApprovalAction.REJECT],
    )
    assert request.decision_id == "dec_123"
    assert request.reason == "Budget exceeded"
    assert len(request.available_actions) == 2


def test_approval_response_creation() -> None:
    response = ApprovalResponse(
        decision_id="dec_123",
        action=ApprovalAction.APPROVE_ONCE,
        explanation="Approved once with notes",
    )
    assert response.decision_id == "dec_123"
    assert response.action == ApprovalAction.APPROVE_ONCE
    assert response.explanation == "Approved once with notes"


def test_approval_response_with_modified_intent() -> None:
    new_intent = {"maximum_refund": 1000}
    response = ApprovalResponse(
        decision_id="dec_123",
        action=ApprovalAction.MODIFY_INTENT,
        modified_intent=new_intent,
    )
    assert response.modified_intent == new_intent


def test_escalation_handler_raises_not_implemented() -> None:
    handler = EscalationHandler()
    request = EscalationRequest(
        decision_id="dec_123",
        reason="Test",
        context={},
        available_actions=[ApprovalAction.REJECT],
    )
    with pytest.raises(NotImplementedError):
        handler.handle_escalation(request)


def test_approval_action_enum_values() -> None:
    assert ApprovalAction.APPROVE_ONCE.value == "approve_once"
    assert ApprovalAction.REJECT.value == "reject"
    assert ApprovalAction.MODIFY_INTENT.value == "modify_intent"
    assert ApprovalAction.ASK_AGENT_TO_REPLAN.value == "ask_agent_to_replan"
    assert ApprovalAction.STOP_AGENT.value == "stop_agent"


def test_approval_response_all_actions() -> None:
    for action in ApprovalAction:
        response = ApprovalResponse(decision_id="dec_123", action=action)
        assert response.action == action
