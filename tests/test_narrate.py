"""Tests for `agentic_sidecar.status.narrate`."""

from agentic_sidecar.core.decision import Decision
from agentic_sidecar.status.narrate import StatusNarrator, ToolCallNarrative


def test_narrator_initialization() -> None:
    narrator = StatusNarrator()
    assert narrator.objectives == []
    assert narrator.tool_calls == []
    assert narrator.blocked_decisions == 0
    assert narrator.paused_decisions == 0
    assert narrator.is_paused is False


def test_set_objective() -> None:
    narrator = StatusNarrator()
    narrator.set_objective("Find the best hotel")
    assert narrator.objectives == ["Find the best hotel"]
    narrator.set_objective("Book the hotel")
    assert len(narrator.objectives) == 2


def test_record_tool_call_success() -> None:
    narrator = StatusNarrator()
    call = narrator.record_tool_call(tool_name="search", arguments={"query": "hotels in NYC"})
    assert isinstance(call, ToolCallNarrative)
    assert call.tool_name == "search"
    assert call.narrative == "🔍 Searching for information"
    assert len(narrator.tool_calls) == 1


def test_record_tool_call_with_decision_block() -> None:
    narrator = StatusNarrator()
    decision = Decision(status="BLOCK", risk=None, reason="Policy violation")

    call = narrator.record_tool_call(tool_name="delete", arguments={"id": "123"}, decision=decision)

    assert narrator.blocked_decisions == 1
    assert call.decision == decision


def test_record_tool_call_with_decision_pause() -> None:
    narrator = StatusNarrator()
    decision = Decision(
        status="PAUSE",
        risk=None,
        reason="Budget exceeded",
        escalation_required=True,
    )

    call = narrator.record_tool_call(
        tool_name="refund", arguments={"amount": 850}, decision=decision
    )

    assert narrator.paused_decisions == 1
    assert call.decision == decision


def test_intent_violation_tracking() -> None:
    narrator = StatusNarrator()
    narrator.record_tool_call(tool_name="search", arguments={}, intent_compliant=False)
    narrator.record_tool_call(tool_name="search", arguments={}, intent_compliant=False)

    assert narrator.intent_violations == 2


def test_max_risk_tracking() -> None:
    narrator = StatusNarrator()
    narrator.record_tool_call(tool_name="search", arguments={}, risk_level="LOW")
    assert narrator.max_risk_seen == "LOW"

    narrator.record_tool_call(tool_name="query", arguments={}, risk_level="HIGH")
    assert narrator.max_risk_seen == "HIGH"


def test_pause_and_resume() -> None:
    narrator = StatusNarrator()
    narrator.pause("Awaiting budget approval")
    assert narrator.is_paused is True
    assert narrator.pause_reason == "Awaiting budget approval"

    narrator.resume()
    assert narrator.is_paused is False
    assert narrator.pause_reason is None


def test_get_status() -> None:
    narrator = StatusNarrator()
    narrator.set_objective("Find hotels")
    narrator.record_tool_call(tool_name="search", arguments={})

    status = narrator.get_status(
        current_objective="Searching...",
        current_budget_remaining=10.5,
        current_tokens_remaining=2000,
    )

    assert status.current_objective == "Searching..."
    assert status.current_step == "Searching..."
    assert status.tool_calls_made == 1
    assert status.current_budget_remaining == 10.5
    assert status.current_tokens_remaining == 2000
    assert status.is_paused is False


def test_get_narrative_empty() -> None:
    narrator = StatusNarrator()
    narrative = narrator.get_narrative()
    assert "No objectives" in narrative or narrative == ""


def test_get_narrative_with_objectives_and_calls() -> None:
    narrator = StatusNarrator()
    narrator.set_objective("Find the best hotel")
    narrator.record_tool_call(tool_name="search", arguments={})
    narrator.record_tool_call(
        tool_name="retrieve",
        arguments={},
        decision=Decision(status="ALLOW", risk="LOW", reason="ok"),
    )

    narrative = narrator.get_narrative()
    assert "Find the best hotel" in narrative
    assert "Steps taken:" in narrative
    assert "🔍" in narrative or "📥" in narrative


def test_get_narrative_with_blocked_decisions() -> None:
    narrator = StatusNarrator()
    narrator.record_tool_call(
        tool_name="delete",
        arguments={},
        decision=Decision(status="BLOCK", risk=None, reason="Policy"),
    )
    narrator.record_tool_call(
        tool_name="delete",
        arguments={},
        decision=Decision(status="BLOCK", risk=None, reason="Policy"),
    )

    narrative = narrator.get_narrative()
    assert "Blocked decisions: 2" in narrative


def test_tool_call_narration_patterns() -> None:
    narrator = StatusNarrator()

    # Test exact match
    call1 = narrator.record_tool_call("search", {})
    assert call1.narrative == "🔍 Searching for information"

    # Test substring match
    call2 = narrator.record_tool_call("user_lookup", {})
    assert call2.narrative == "🔎 Looking up data"

    # Test fallback
    call3 = narrator.record_tool_call("custom_action", {})
    assert call3.narrative == "⚙️ Executing custom_action"


def test_tool_call_with_multiple_statuses() -> None:
    narrator = StatusNarrator()

    # Record allow
    narrator.record_tool_call(
        "search",
        {},
        decision=Decision(status="ALLOW", risk="LOW", reason="ok"),
    )
    # Record warn
    narrator.record_tool_call(
        "update",
        {},
        decision=Decision(status="WARN", risk="MEDIUM", reason="warning"),
    )
    # Record block
    narrator.record_tool_call(
        "delete",
        {},
        decision=Decision(status="BLOCK", risk="HIGH", reason="blocked"),
    )
    # Record pause
    narrator.record_tool_call(
        "refund",
        {},
        decision=Decision(
            status="PAUSE",
            risk=None,
            reason="escalate",
            escalation_required=True,
        ),
    )

    assert narrator.blocked_decisions == 1
    assert narrator.paused_decisions == 1
    assert len(narrator.tool_calls) == 4
