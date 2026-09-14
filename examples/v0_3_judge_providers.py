"""v0.3.0 Judge Providers Demo: OpenAI and Anthropic.

Demonstrates how Judge works with different LLM providers,
and how to swap them without changing Sidecar code.

Features:
- OpenAI provider (GPT-4, GPT-3.5)
- Anthropic provider (Claude 3)
- Provider swapping
- Cost tracking per provider
- Error handling and fallback

Run: python examples/v0_3_judge_providers.py
"""

from agentic_sidecar import JudgeEvaluator, Sidecar
from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.evaluators.providers import AnthropicJudge, OpenAIJudge


def demo_1_openai_provider():
    """Example 1: Using OpenAI as the Judge provider."""
    print("\n=== Example 1: OpenAI Judge Provider ===")
    
    provider = OpenAIJudge(model="gpt-4")
    judge = JudgeEvaluator(provider=provider, enabled=True)
    
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        judge=judge,
        roles=["judge"],
    )
    
    test_cases = [
        ("transfer_funds", {"amount": 1000, "recipient": "alice@example.com"}),
        ("delete_account", {"user_id": "12345", "confirm": True}),
        ("update_profile", {"bio": "updated bio", "photo": "url"}),
    ]
    
    for tool_name, tool_args in test_cases:
        context = DecisionContext(tool_name=tool_name, tool_args=tool_args)
        decision = sidecar.evaluate(context)
        print(f"  {tool_name:20} → {decision.status:10} | {judge.get_cost():.4f}")


def demo_2_anthropic_provider():
    """Example 2: Using Anthropic (Claude) as the Judge provider."""
    print("\n=== Example 2: Anthropic Judge Provider ===")
    
    provider = AnthropicJudge(model="claude-3-opus")
    judge = JudgeEvaluator(provider=provider, enabled=True)
    
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        judge=judge,
        roles=["judge"],
    )
    
    test_cases = [
        ("send_email", {"to": "user@example.com", "subject": "notification"}),
        ("export_data", {"format": "csv", "table": "users"}),
        ("create_backup", {"target": "cloud_storage"}),
    ]
    
    for tool_name, tool_args in test_cases:
        context = DecisionContext(tool_name=tool_name, tool_args=tool_args)
        decision = sidecar.evaluate(context)
        print(f"  {tool_name:20} → {decision.status:10} | Cost: ${judge.get_cost():.4f}")


def demo_3_provider_swapping():
    """Example 3: Swapping providers without changing Sidecar code."""
    print("\n=== Example 3: Provider Swapping ===")
    
    # Start with OpenAI
    openai_provider = OpenAIJudge(model="gpt-4")
    judge = JudgeEvaluator(provider=openai_provider)
    
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        judge=judge,
        roles=["judge"],
    )
    
    context = DecisionContext(
        tool_name="approve_request",
        tool_args={"request_id": "123", "reason": "cost_analysis"},
    )
    
    print("  Using OpenAI provider...")
    decision1 = sidecar.evaluate(context)
    openai_cost = judge.get_cost()
    print(f"    Decision: {decision1.status} | Cost: ${openai_cost:.4f}")
    
    # Swap to Anthropic
    print("  Swapping to Anthropic provider...")
    judge.provider = AnthropicJudge(model="claude-3-opus")
    judge.reset_cost()
    
    decision2 = sidecar.evaluate(context)
    anthropic_cost = judge.get_cost()
    print(f"    Decision: {decision2.status} | Cost: ${anthropic_cost:.4f}")
    
    # Back to OpenAI
    print("  Swapping back to OpenAI...")
    judge.provider = OpenAIJudge(model="gpt-3.5-turbo")  # Different model
    judge.reset_cost()
    
    decision3 = sidecar.evaluate(context)
    print(f"    Decision: {decision3.status} | Cost: ${judge.get_cost():.4f}")


def demo_4_cost_comparison():
    """Example 4: Comparing costs across providers."""
    print("\n=== Example 4: Cost Comparison ===")
    
    providers_to_test = [
        ("OpenAI GPT-4", OpenAIJudge(model="gpt-4")),
        ("OpenAI GPT-3.5", OpenAIJudge(model="gpt-3.5-turbo")),
        ("Claude Opus", AnthropicJudge(model="claude-3-opus")),
        ("Claude Sonnet", AnthropicJudge(model="claude-3-sonnet")),
    ]
    
    test_context = DecisionContext(
        tool_name="process_payment",
        tool_args={"amount": 1000, "method": "card"},
    )
    
    costs = {}
    for provider_name, provider in providers_to_test:
        judge = JudgeEvaluator(provider=provider)
        judge.evaluate(
            {
                "tool_name": test_context.tool_name,
                "arguments": test_context.tool_args,
                "history": [],
                "intent": None,
            }
        )
        cost = judge.get_cost()
        costs[provider_name] = cost
        print(f"  {provider_name:20} → ${cost:.4f}")
    
    cheapest = min(costs, key=costs.get)
    print(f"\nCheapest option: {cheapest} (${costs[cheapest]:.4f})")


def demo_5_provider_validation():
    """Example 5: Validating providers before use."""
    print("\n=== Example 5: Provider Validation ===")
    
    # Valid provider
    valid_provider = OpenAIJudge(model="gpt-4")
    print(f"  Valid provider (model='gpt-4'): {valid_provider.validate()}")
    
    # Invalid provider (no model specified)
    invalid_provider = OpenAIJudge(model="")
    print(f"  Invalid provider (model=''): {invalid_provider.validate()}")
    
    # Anthropic provider
    claude_provider = AnthropicJudge(model="claude-3-opus")
    print(f"  Claude provider: {claude_provider.validate()}")
    
    # Creating Judge with invalid provider will fail validation
    try:
        judge = JudgeEvaluator(provider=OpenAIJudge(model=""))
        if not judge.provider.validate():
            print("  Judge created with invalid provider (validation failed)")
    except Exception as e:
        print(f"  Error: {e}")


def demo_6_different_models():
    """Example 6: Testing different models within a provider."""
    print("\n=== Example 6: Different Models ===")
    
    models = [
        ("gpt-4", OpenAIJudge),
        ("gpt-3.5-turbo", OpenAIJudge),
        ("claude-3-opus", AnthropicJudge),
        ("claude-3-sonnet", AnthropicJudge),
    ]
    
    context = DecisionContext(
        tool_name="classify_content",
        tool_args={"text": "review content", "category": "manual_review"},
    )
    
    for model_name, provider_class in models:
        provider = provider_class(model=model_name)
        judge = JudgeEvaluator(provider=provider)
        decision = judge.evaluate(
            {
                "tool_name": context.tool_name,
                "arguments": context.tool_args,
                "history": [],
                "intent": None,
            }
        )
        print(f"  {model_name:20} → {decision.status:10} (confidence: {decision.confidence})")


def main():
    """Run all provider demo examples."""
    print("=" * 70)
    print("v0.3.0 Judge Providers Demo: OpenAI and Anthropic")
    print("=" * 70)
    
    demo_1_openai_provider()
    demo_2_anthropic_provider()
    demo_3_provider_swapping()
    demo_4_cost_comparison()
    demo_5_provider_validation()
    demo_6_different_models()
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
