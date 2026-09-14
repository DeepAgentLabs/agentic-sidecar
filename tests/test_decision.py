"""Tests for `agentic_sidecar.core.decision.Decision`."""

import pytest
from pydantic import ValidationError

from agentic_sidecar.core.decision import Decision


def test_allow_decision_round_trips() -> None:
    decision = Decision(status="ALLOW", risk="LOW", reason="no rule matched")
    assert decision.status == "ALLOW"
    assert decision.risk == "LOW"
    assert decision.reason == "no rule matched"


def test_block_decision_round_trips() -> None:
    decision = Decision(status="BLOCK", risk="HIGH", reason="denied by policy")
    assert decision.status == "BLOCK"
    assert decision.risk == "HIGH"


def test_warn_decision_round_trips() -> None:
    decision = Decision(status="WARN", risk="LOW", reason="intent envelope expired")
    assert decision.status == "WARN"


def test_risk_may_be_none_for_failure_path() -> None:
    decision = Decision(status="BLOCK", risk=None, reason="sidecar evaluation raised")
    assert decision.risk is None


def test_decision_is_frozen() -> None:
    decision = Decision(status="ALLOW", risk="LOW", reason="ok")
    with pytest.raises(ValidationError):
        decision.status = "BLOCK"  # type: ignore[misc]


def test_invalid_status_rejected() -> None:
    with pytest.raises(ValidationError):
        Decision(status="INVALID_STATUS", risk="LOW", reason="not a real status")  # type: ignore[arg-type]


def test_invalid_risk_rejected() -> None:
    with pytest.raises(ValidationError):
        Decision(status="ALLOW", risk="CRITICAL", reason="not a real level")  # type: ignore[arg-type]


def test_v0_4_decision_statuses() -> None:
    """v0.4 adds CHALLENGE, REPLAN, PAUSE, ESCALATE to the seven outcomes."""
    for status in ["CHALLENGE", "REPLAN", "PAUSE", "ESCALATE"]:
        decision = Decision(status=status, risk="LOW", reason="v0.4 outcome")  # type: ignore[arg-type]
        assert decision.status == status


def test_decision_with_provenance_fields() -> None:
    """v0.4 adds provenance/audit fields to Decision."""
    decision = Decision(
        status="PAUSE",
        risk="MEDIUM",
        reason="Budget exceeded",
        decision_point="tool_call",
        trigger_details={"tool_name": "refund_payment", "amount": 850},
        escalation_required=True,
        causal_link="dec_initial_123",
    )
    assert decision.decision_point == "tool_call"
    assert decision.trigger_details["tool_name"] == "refund_payment"
    assert decision.escalation_required is True
    assert decision.causal_link == "dec_initial_123"
