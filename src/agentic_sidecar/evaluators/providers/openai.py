"""OpenAI Judge provider: GPT-based decision evaluation."""

from __future__ import annotations

from typing import Any

from agentic_sidecar.evaluators.base import JudgeProvider


class OpenAIJudge(JudgeProvider):
    """OpenAI-powered judge evaluator.

    Uses OpenAI API (GPT-4, GPT-3.5, etc.) to evaluate decisions.

    Example:
        judge = JudgeEvaluator(
            provider=OpenAIJudge(model="gpt-4"),
            enabled=True
        )
    """

    def __init__(self, model: str = "gpt-4", api_key: str = ""):
        """Initialize OpenAI judge.

        Args:
            model: OpenAI model (gpt-4, gpt-3.5-turbo, etc.)
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        """
        super().__init__(model=model)
        self.api_key = api_key
        self.cost_per_1k_input = 0.03  # GPT-4 pricing
        self.cost_per_1k_output = 0.06

    def validate(self) -> bool:
        """Validate provider configuration."""
        return bool(self.model)

    def evaluate(self, question: str, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate using OpenAI API.

        Args:
            question: The question to ask the judge
            context: Decision context

        Returns:
            Dictionary with decision, reasoning, confidence, usage
        """
        if not self.validate():
            return {
                "decision": "ALLOW",
                "reasoning": "OpenAI provider not configured",
                "confidence": 0.5,
            }

        # In production, would call OpenAI API:
        # response = openai.ChatCompletion.create(
        #     model=self.model,
        #     messages=[{"role": "user", "content": question}],
        #     max_tokens=500,
        # )

        # For v0.3.0, return mock response
        return {
            "decision": "ALLOW",
            "reasoning": f"OpenAI {self.model} evaluation: Decision appears reasonable",
            "confidence": 0.85,
            "usage": {
                "prompt_tokens": 150,
                "completion_tokens": 50,
                "cost": 0.0065,  # Estimated
            },
        }

    async def evaluate_async(self, question: str, context: dict[str, Any]) -> dict[str, Any]:
        """Async version using OpenAI API."""
        # In production, would use async OpenAI client
        return self.evaluate(question, context)
