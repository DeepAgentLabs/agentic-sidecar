"""Tests for `agentic_sidecar.core.provenance` -- Decision audit trail."""

from datetime import datetime

from agentic_sidecar.core.provenance import (
    AuditRecord,
    CausalLink,
    DecisionRationale,
    DecisionTrigger,
)


def test_decision_trigger_creation() -> None:
    trigger = DecisionTrigger(
        boundary_type="tool_call",
        tool_name="issue_refund",
        arguments={"customer_id": "C123", "amount": 850},
    )
    assert trigger.boundary_type == "tool_call"
    assert trigger.tool_name == "issue_refund"
    assert trigger.arguments["amount"] == 850


def test_decision_rationale_single_finding() -> None:
    rationale = DecisionRationale(
        policy_findings=["Matched deny rule: refund_limit"],
        reason="Refund exceeds policy limit",
    )
    assert len(rationale.policy_findings) == 1
    assert rationale.reason == "Refund exceeds policy limit"


def test_decision_rationale_multiple_findings() -> None:
    rationale = DecisionRationale(
        policy_findings=["Policy check 1"],
        risk_findings=["Risk check 1", "Risk check 2"],
        intent_findings=["Intent violation"],
        budget_findings=["Budget exceeded"],
        reason="Multiple issues detected",
    )
    all_findings = rationale.all_findings()
    assert len(all_findings) == 5


def test_causal_link_to_parent_decision() -> None:
    link = CausalLink(
        parent_decision_id="dec_initial",
        correlation_id="corr_12345",
    )
    assert link.parent_decision_id == "dec_initial"
    assert link.correlation_id == "corr_12345"
    assert link.parent_plan_step is None


def test_causal_link_to_plan_step() -> None:
    link = CausalLink(
        parent_plan_step=3,
        correlation_id="corr_12345",
    )
    assert link.parent_plan_step == 3
    assert link.parent_decision_id is None


def test_audit_record_creation() -> None:
    trigger = DecisionTrigger(
        boundary_type="tool_call",
        tool_name="issue_refund",
        arguments={"amount": 850},
    )
    rationale = DecisionRationale(reason="Intent violation: refund exceeds limit")
    link = CausalLink(correlation_id="corr_123")

    record = AuditRecord(
        decision_id="dec_pause_1",
        timestamp=datetime(2026, 1, 15, 10, 30, 0),
        outcome="PAUSE",
        trigger=trigger,
        rationale=rationale,
        causal_link=link,
        execution_context={"agent_step": 3},
    )

    assert record.decision_id == "dec_pause_1"
    assert record.outcome == "PAUSE"
    assert record.trigger.tool_name == "issue_refund"
    assert record.execution_context["agent_step"] == 3


def test_audit_record_serialization() -> None:
    trigger = DecisionTrigger(
        boundary_type="tool_call",
        tool_name="delete_customer",
        arguments={"customer_id": "C123"},
    )
    rationale = DecisionRationale(
        policy_findings=["Policy deny"],
        reason="Deletion not permitted",
    )

    record = AuditRecord(
        decision_id="dec_block_1",
        timestamp=datetime(2026, 1, 15, 10, 0, 0),
        outcome="BLOCK",
        trigger=trigger,
        rationale=rationale,
    )

    serialized = record.to_dict()
    assert serialized["decision_id"] == "dec_block_1"
    assert serialized["outcome"] == "BLOCK"
    assert serialized["trigger"]["tool_name"] == "delete_customer"
    assert serialized["rationale"]["policy_findings"] == ["Policy deny"]
    assert serialized["causal_link"] is None


def test_audit_record_all_outcomes() -> None:
    trigger = DecisionTrigger(boundary_type="tool_call", tool_name="test")
    rationale = DecisionRationale(reason="Test")

    outcomes = ["ALLOW", "WARN", "BLOCK", "CHALLENGE", "REPLAN", "PAUSE", "ESCALATE"]
    for outcome in outcomes:
        record = AuditRecord(
            decision_id=f"dec_{outcome}",
            timestamp=datetime.now(),
            outcome=outcome,
            trigger=trigger,
            rationale=rationale,
        )
        assert record.outcome == outcome
