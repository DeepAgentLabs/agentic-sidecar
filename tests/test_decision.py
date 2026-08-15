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
        Decision(status="REPLAN", risk="LOW", reason="not until v0.4")  # type: ignore[arg-type]


def test_invalid_risk_rejected() -> None:
    with pytest.raises(ValidationError):
        Decision(status="ALLOW", risk="CRITICAL", reason="not a real level")  # type: ignore[arg-type]
