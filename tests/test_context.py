"""Tests for `agentic_sidecar.core.context.DecisionContext`."""

from agentic_sidecar.core.context import DecisionContext, HistoryEntry, IntentSnapshot


def test_defaults_are_empty_dicts() -> None:
    context = DecisionContext(tool_name="read_order")
    assert context.tool_args == {}
    assert context.metadata == {}
    assert context.intent is None
    assert context.history == []


def test_intent_and_history_round_trip() -> None:
    snapshot = IntentSnapshot(goal="refund_customer", constraints={"maximum_refund": 500})
    history = [HistoryEntry(tool_name="look_up_order", tool_args={}, status="ALLOW")]
    context = DecisionContext(tool_name="issue_refund", intent=snapshot, history=history)
    assert context.intent is not None
    assert context.intent.goal == "refund_customer"
    assert context.history[0].status == "ALLOW"


def test_tool_args_and_metadata_are_preserved() -> None:
    context = DecisionContext(
        tool_name="issue_refund",
        tool_args={"order_id": "A100", "amount": 850.0},
        metadata={"trace_id": "abc123"},
    )
    assert context.tool_args == {"order_id": "A100", "amount": 850.0}
    assert context.metadata == {"trace_id": "abc123"}


def test_separate_instances_do_not_share_default_dicts() -> None:
    a = DecisionContext(tool_name="a")
    b = DecisionContext(tool_name="b")
    a.tool_args["x"] = 1
    assert b.tool_args == {}
