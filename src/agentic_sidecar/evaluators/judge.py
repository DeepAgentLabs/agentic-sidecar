"""Judge evaluator: LLM-based decision evaluation (v0.3.0).

Uses an independent LLM model to evaluate decisions. Separates the Main Agent's
model from the Sidecar's judge model to reduce correlated reasoning failures.

Design principle: Main Agent Model A ≠ Sidecar Judge Model B
"""

from __future__ import annotations

import time
from typing import Any

from agentic_sidecar.evaluators.base import EvaluatorBase, EvaluatorResult, JudgeProvider


class JudgeEvaluator(EvaluatorBase):
    """LLM-based decision evaluation using a pluggable provider.

    The Judge asks: "Should this decision proceed?" It's designed to be
    model-agnostic, so you can swap LLM providers (OpenAI, Anthropic, local)
    without changing Sidecar code.

    Example:
        judge = JudgeEvaluator(
            provider=OpenAIJudge(model="gpt-4"),
            enabled=True,
            cost_limit=0.10  # Max cost per evaluation
        )

        result = judge.evaluate({
            "tool_name": "issue_refund",
            "arguments": {"amount": 500},
            "context": "Customer disputes charge"
        })
        # → Asks GPT-4: "Should we refund $500 given this context?"
        # → Returns: ALLOW, WARN, BLOCK, or CHALLENGE
    """

    def __init__(
        self,
        provider: JudgeProvider,
        enabled: bool = True,
        cost_limit: float = 0.50,
        timeout_ms: int = 5000,
    ):
        """Initialize Judge.

        Args:
            provider: LLM provider (OpenAI, Anthropic, etc.)
            enabled: Whether judge is active
            cost_limit: Max cost per evaluation (USD)
            timeout_ms: Max time for LLM call (milliseconds)
        """
        super().__init__(enabled=enabled, name="JudgeEvaluator")
        self.provider = provider
        self.cost_limit = cost_limit
        self.timeout_ms = timeout_ms
        self.total_cost = 0.0

    def evaluate(self, context: dict[str, Any]) -> EvaluatorResult:
        """Evaluate decision using LLM.

        Args:
            context: Decision context with tool_name, arguments, etc.

        Returns:
            EvaluatorResult with LLM's decision
        """
        if not self.enabled:
            return EvaluatorResult(
                status="ALLOW",
                rationale="JudgeEvaluator is disabled",
                confidence=1.0,
            )

        if not self.provider or not self.provider.validate():
            return EvaluatorResult(
                status="ALLOW",
                rationale="Judge provider not configured",
                confidence=0.5,
                metadata={"provider_error": "invalid_config"},
            )

        tool_name = context.get("tool_name", "")
        arguments = context.get("arguments", {})

        # Build evaluation question for LLM
        question = self._build_question(tool_name, arguments, context)

        # Call LLM provider
        start_time = time.time()
        try:
            result = self.provider.evaluate(question, context)
            latency_ms = (time.time() - start_time) * 1000

            # Extract decision
            status = result.get("decision", "ALLOW")
            reasoning = result.get("reasoning", "")
            confidence = result.get("confidence", 0.75)
            usage = result.get("usage", {})

            # Track cost
            cost = usage.get("cost", 0.0)
            self.total_cost += cost

            return EvaluatorResult(
                status=status,
                rationale=reasoning,
                confidence=confidence,
                metadata={
                    "provider": self.provider.__class__.__name__,
                    "cost": cost,
                    "usage": usage,
                },
                latency_ms=latency_ms,
            )

        except Exception as e:
            return EvaluatorResult(
                status="WARN",
                rationale=f"Judge evaluation failed: {str(e)}. Proceeding with caution.",
                confidence=0.3,
                metadata={"error": str(e)},
            )

    async def evaluate_async(self, context: dict[str, Any]) -> EvaluatorResult:
        """Async version of evaluate."""
        if not self.enabled:
            return EvaluatorResult(
                status="ALLOW",
                rationale="JudgeEvaluator is disabled",
                confidence=1.0,
            )

        tool_name = context.get("tool_name", "")
        arguments = context.get("arguments", {})
        question = self._build_question(tool_name, arguments, context)

        try:
            result = await self.provider.evaluate_async(question, context)
            status = result.get("decision", "ALLOW")
            reasoning = result.get("reasoning", "")
            confidence = result.get("confidence", 0.75)

            return EvaluatorResult(
                status=status,
                rationale=reasoning,
                confidence=confidence,
                metadata={"provider": self.provider.__class__.__name__},
            )
        except Exception as e:
            return EvaluatorResult(
                status="WARN",
                rationale=f"Judge evaluation failed: {str(e)}",
                confidence=0.3,
            )

    def _build_question(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        """Build the question to ask the judge LLM."""
        goal = context.get("goal", "")

        question = f"""Evaluate this decision:

Tool: {tool_name}
Arguments: {arguments}
User Goal: {goal}

Should this decision proceed? Consider:
- Is it necessary for the goal?
- Does it respect the user's constraints?
- Are there any risks or concerns?
- Has the decision been properly justified?

Respond with: ALLOW, WARN, BLOCK, or CHALLENGE."""

        return question

    def reset_cost(self) -> None:
        """Reset cost tracking (for testing or new task)."""
        self.total_cost = 0.0

    def get_cost(self) -> float:
        """Get total cost of evaluations."""
        return self.total_cost
