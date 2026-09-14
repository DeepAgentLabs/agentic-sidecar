"""v0.3.0 Evaluators Demo: Planner, Critic, and Judge in action.

Shows how the three evaluators work together to assess plans and decisions:
1. Planner: Checks if entire plan aligns with user intent
2. Critic: Challenges decisions for assumptions and risks
3. Judge: LLM-based evaluation with confidence scoring

Run: python examples/v0_3_planner_critic_judge.py
"""

from agentic_sidecar import (
    Sidecar,
    CriticEvaluator,
    JudgeEvaluator,
    PlanEvaluator,
)
from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.evaluators.providers import OpenAIJudge


def demo_1_planner_alignment():
    """Example 1: Planner evaluates plan alignment with intent."""
    print("\n=== Example 1: Planner Evaluation ===")
    
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        planner=PlanEvaluator(enabled=True),
        roles=["planner"],
    )
    
    # Safe action aligned with intent
    context = DecisionContext(
        tool_name="search",
        tool_args={"query": "find affordable flights to NYC"},
    )
    decision = sidecar.evaluate(context)
    print(f"Search decision: {decision.status} | Reason: {decision.reason}")
    
    # Potentially misaligned action
    context = DecisionContext(
        tool_name="refund",
        tool_args={"amount": 500, "customer_id": "123"},
    )
    decision = sidecar.evaluate(context)
    print(f"Refund decision: {decision.status} | Reason: {decision.reason}")


def demo_2_critic_challenges():
    """Example 2: Critic identifies risky patterns and assumptions."""
    print("\n=== Example 2: Critic Evaluation ===")
    
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        critic=CriticEvaluator(enabled=True),
        roles=["critic"],
    )
    
    # Safe read operation
    context = DecisionContext(
        tool_name="get_customer",
        tool_args={"customer_id": "123"},
    )
    decision = sidecar.evaluate(context)
    print(f"Read decision: {decision.status} | Reason: {decision.reason}")
    
    # Risky delete operation
    context = DecisionContext(
        tool_name="delete_records",
        tool_args={"table": "users", "count": 1000},
    )
    decision = sidecar.evaluate(context)
    print(f"Delete decision: {decision.status} | Reason: {decision.reason}")
    
    # Large refund
    context = DecisionContext(
        tool_name="issue_refund",
        tool_args={"amount": 5000, "reason": "customer_request"},
    )
    decision = sidecar.evaluate(context)
    print(f"Large refund decision: {decision.status} | Reason: {decision.reason}")


def demo_3_judge_evaluation():
    """Example 3: Judge uses LLM for nuanced decision-making."""
    print("\n=== Example 3: Judge Evaluation (LLM-based) ===")
    
    # Create Judge with OpenAI provider
    judge = JudgeEvaluator(
        provider=OpenAIJudge(model="gpt-4"),
        enabled=True,
    )
    
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        judge=judge,
        roles=["judge"],
    )
    
    # Straightforward decision
    context = DecisionContext(
        tool_name="send_email",
        tool_args={"to": "customer@example.com", "subject": "Order confirmation"},
    )
    decision = sidecar.evaluate(context)
    print(f"Email decision: {decision.status} | Reason: {decision.reason}")
    
    # Complex decision with multiple factors
    context = DecisionContext(
        tool_name="approve_transfer",
        tool_args={
            "amount": 10000,
            "destination": "unknown_account",
            "reason": "new_investment",
        },
    )
    decision = sidecar.evaluate(context)
    print(f"Transfer decision: {decision.status} | Reason: {decision.reason}")
    print(f"Judge confidence: {decision.reason}")


def demo_4_all_evaluators():
    """Example 4: All three evaluators working together."""
    print("\n=== Example 4: Integrated Evaluation ===")
    
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        planner=PlanEvaluator(enabled=True),
        critic=CriticEvaluator(enabled=True),
        judge=JudgeEvaluator(provider=OpenAIJudge(model="gpt-4")),
        roles=["policy", "risk", "planner", "critic", "judge"],
    )
    
    decisions_to_test = [
        ("search", {"query": "hotels in NYC"}),
        ("delete", {"table": "temp_data", "id": 456}),
        ("refund", {"amount": 1000, "reason": "defective_product"}),
        ("send_notification", {"user_id": "789", "message": "order_shipped"}),
    ]
    
    for tool_name, tool_args in decisions_to_test:
        context = DecisionContext(tool_name=tool_name, tool_args=tool_args)
        decision = sidecar.evaluate(context)
        status_icon = "✓" if decision.status == "ALLOW" else "✗"
        print(f"{status_icon} {tool_name:20} → {decision.status:10} ({decision.reason[:50]}...)")


def demo_5_cost_tracking():
    """Example 5: Judge cost tracking."""
    print("\n=== Example 5: Cost Tracking ===")
    
    judge = JudgeEvaluator(
        provider=OpenAIJudge(model="gpt-4"),
        enabled=True,
    )
    
    print(f"Initial cost: ${judge.get_cost():.4f}")
    
    # Simulate multiple evaluations
    for i in range(3):
        context = {
            "tool_name": f"action_{i}",
            "arguments": {"data": "test"},
            "history": [],
            "intent": None,
        }
        judge.evaluate(context)
        cost = judge.get_cost()
        print(f"Cost after evaluation {i+1}: ${cost:.4f}")
    
    print(f"Total evaluation cost: ${judge.get_cost():.4f}")
    judge.reset_cost()
    print(f"Cost after reset: ${judge.get_cost():.4f}")


def main():
    """Run all demo examples."""
    print("=" * 60)
    print("v0.3.0 Evaluators Demo: Planner, Critic, Judge")
    print("=" * 60)
    
    demo_1_planner_alignment()
    demo_2_critic_challenges()
    demo_3_judge_evaluation()
    demo_4_all_evaluators()
    demo_5_cost_tracking()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
