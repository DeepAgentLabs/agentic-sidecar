"""v0.4 Example: Budget Guardian and Human Escalation.

Demonstrates:
- Budget Guardian with cost tracking
- PAUSE and ESCALATE outcomes
- Custom escalation handler
- Provenance/audit trail

Usage:
    python examples/v0_4_budget_and_escalation.py
"""

from agentic_sidecar import (
    ApprovalAction,
    ApprovalResponse,
    Sidecar,
    BudgetGuardian,
    EscalationRequest,
)
from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.gate.escalation import EscalationHandler


class MockApprovalHandler(EscalationHandler):
    """Mock handler that simulates user approval decisions."""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.escalations: list[EscalationRequest] = []

    def handle_escalation(self, request: EscalationRequest) -> ApprovalResponse:
        """Simulate human approval flow."""
        self.escalations.append(request)

        if self.auto_approve:
            print(f"[AUTO] Approving escalation: {request.decision_id}")
            return ApprovalResponse(
                decision_id=request.decision_id,
                action=ApprovalAction.APPROVE_ONCE,
                explanation="Auto-approved for demo",
            )

        print(f"\n⚠️  ESCALATION REQUIRED")
        print(f"Decision ID: {request.decision_id}")
        print(f"Reason: {request.reason}")
        print(f"Context: {request.context}")
        print(f"Available actions: {[a.value for a in request.available_actions]}")

        user_choice = input("\nEnter action (a=approve_once, r=reject, q=quit): ")
        if user_choice == "a":
            return ApprovalResponse(
                decision_id=request.decision_id,
                action=ApprovalAction.APPROVE_ONCE,
                explanation="Manually approved",
            )
        else:
            return ApprovalResponse(
                decision_id=request.decision_id,
                action=ApprovalAction.REJECT,
                explanation="User rejected the action",
            )


def demo_budget_guardian():
    """Demonstrate Budget Guardian in action."""
    print("=" * 60)
    print("DEMO: Budget Guardian (v0.4)")
    print("=" * 60)

    budget = BudgetGuardian(max_cost=2.0)

    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        budget=budget,
        roles=["policy", "risk", "budget"],
        mode="observe",
    )

    handler = MockApprovalHandler(auto_approve=True)
    sidecar.escalation_handler = handler

    print("\n1. Making LLM calls within budget...")
    budget.record_invocation(cost=0.5)
    context = DecisionContext(tool_name="search", tool_args={"query": "refund policy"})
    decision = sidecar.evaluate(context)
    print(f"   Decision: {decision.status} (cost: $0.50, remaining: $1.50)")

    budget.record_invocation(cost=1.0)
    context = DecisionContext(tool_name="query_db", tool_args={"customer_id": "C123"})
    decision = sidecar.evaluate(context)
    print(f"   Decision: {decision.status} (cost: $1.50, remaining: $0.50)")

    print("\n2. Attempting to exceed budget...")
    budget.record_invocation(cost=0.75)
    context = DecisionContext(tool_name="refund_payment", tool_args={"amount": 500})
    decision = sidecar.evaluate(context)
    print(f"   Decision: {decision.status}")
    print(f"   Reason: {decision.reason}")
    print(f"   Escalation required: {decision.escalation_required}")


def demo_decision_outcomes():
    """Demonstrate all v0.4 Decision outcomes."""
    print("\n" + "=" * 60)
    print("DEMO: Full Decision Gate Outcomes (v0.4)")
    print("=" * 60)

    from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule

    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        policy=PolicyAdvisor(
            rules=[
                PolicyRule(tool="delete_*", effect="deny", reason="Destructive ops blocked"),
                PolicyRule(tool="system_*", effect="deny", reason="System ops restricted"),
            ]
        ),
        roles=["policy"],
        mode="observe",
    )

    test_cases = [
        ("read_order", "ALLOW"),
        ("delete_customer", "BLOCK"),
        ("system_shutdown", "BLOCK"),
        ("refund_payment", "ALLOW"),
    ]

    for tool_name, expected_status in test_cases:
        context = DecisionContext(tool_name=tool_name, tool_args={})
        decision = sidecar.evaluate(context)
        status_indicator = "✓" if decision.status == expected_status else "✗"
        print(f"\n{status_indicator} Tool: {tool_name}")
        print(f"  Outcome: {decision.status} (expected: {expected_status})")
        print(f"  Reason: {decision.reason}")


def demo_audit_trail():
    """Demonstrate Decision provenance/audit trail."""
    print("\n" + "=" * 60)
    print("DEMO: Decision Provenance & Audit Trail (v0.4)")
    print("=" * 60)

    from agentic_sidecar.core.provenance import (
        AuditRecord,
        CausalLink,
        DecisionRationale,
        DecisionTrigger,
    )
    from datetime import datetime

    trigger = DecisionTrigger(
        boundary_type="tool_call",
        tool_name="issue_refund",
        arguments={"customer_id": "C123", "amount": 850},
    )

    rationale = DecisionRationale(
        intent_findings=["Refund amount $850 exceeds authorized limit $500"],
        reason="Intent violation: refund exceeds constraint maximum_refund",
    )

    link = CausalLink(
        parent_decision_id="dec_initial_plan",
        correlation_id="trace_abc123",
    )

    record = AuditRecord(
        decision_id="dec_pause_001",
        timestamp=datetime.now(),
        outcome="PAUSE",
        trigger=trigger,
        rationale=rationale,
        causal_link=link,
        execution_context={"agent_step": 3, "plan_index": 2},
    )

    print("\nAudit Record for PAUSE Decision:")
    print(f"  Decision ID: {record.decision_id}")
    print(f"  Outcome: {record.outcome}")
    print(f"  Trigger Tool: {record.trigger.tool_name}")
    print(f"  Trigger Args: {record.trigger.arguments}")
    print(f"  Rationale: {record.rationale.reason}")
    print(f"  Intent Findings: {record.rationale.intent_findings}")
    print(f"  Causal Link (parent): {record.causal_link.parent_decision_id}")
    print(f"  Correlation ID: {record.causal_link.correlation_id}")

    print("\nSerialized to audit log:")
    import json

    serialized = record.to_dict()
    print(json.dumps(serialized, indent=2, default=str))


if __name__ == "__main__":
    demo_budget_guardian()
    demo_decision_outcomes()
    demo_audit_trail()

    print("\n" + "=" * 60)
    print("v0.4 Demo Complete!")
    print("=" * 60)
