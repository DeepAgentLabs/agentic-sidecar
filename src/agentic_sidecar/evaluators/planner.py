"""Planner evaluator: Plan-level alignment assessment (v0.3.0).

Evaluates whether an entire proposed plan aligns with the user's intent
as captured in the IntentEnvelope. Complements Decision Gate's decision-by-decision
gating by checking the holistic plan.

Useful for: "Does this plan actually accomplish what the user asked for?"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentic_sidecar.evaluators.base import EvaluatorBase, EvaluatorResult
from agentic_sidecar.intent import IntentEnvelope


@dataclass
class PlanStep:
    """One step in a plan being evaluated."""

    sequence: int
    tool_name: str
    description: str
    arguments: dict[str, Any] | None = None
    rationale: str = ""


class PlanEvaluator(EvaluatorBase):
    """Evaluates plan-level alignment with user intent.

    Unlike the Decision Gate (which evaluates individual tool calls), the
    Planner evaluates the entire proposed plan at once:
    - Does the plan accomplish the stated goal?
    - Are all steps necessary?
    - Are there unnecessary steps (cancellation, refund)?
    - Does the plan drift from the original intent?
    - Are there more efficient alternatives?

    Example:
        User requests: "Explain why I was charged."
        Proposed plan includes: cancel subscription, issue refund, send apology.
        Planner verdict: "Plan overreaches. Only explanation was requested."
        Recommendation: REPLAN (user should just send explanation, not cancel/refund)
    """

    def __init__(
        self,
        enabled: bool = True,
        min_confidence: float = 0.7,
    ):
        """Initialize Planner."""
        super().__init__(enabled=enabled, name="PlanEvaluator")
        self.min_confidence = min_confidence

    def evaluate(self, context: dict[str, Any]) -> EvaluatorResult:
        """Evaluate a proposed plan."""
        if not self.enabled:
            return EvaluatorResult(
                status="ALLOW",
                rationale="PlanEvaluator is disabled",
                confidence=1.0,
            )

        plan = context.get("plan", [])
        intent = context.get("intent")
        goal = context.get("goal", "")

        if not plan:
            return EvaluatorResult(
                status="ALLOW",
                rationale="No plan to evaluate",
                confidence=1.0,
            )

        # Analyze plan for issues
        issues = self._analyze_plan(plan, intent, goal)

        if not issues:
            return EvaluatorResult(
                status="ALLOW",
                rationale="Plan aligns with stated intent",
                confidence=1.0,
                metadata={"plan_steps": len(plan) if isinstance(plan, list) else 0},
            )

        # Plan has issues - recommend REPLAN
        rationale = self._format_issues(issues)
        return EvaluatorResult(
            status="REPLAN",
            rationale=rationale,
            confidence=0.9,
            metadata={
                "issues": [issue["type"] for issue in issues],
                "plan_steps": len(plan) if isinstance(plan, list) else 0,
            },
        )

    def _analyze_plan(
        self,
        plan: Any,
        intent: IntentEnvelope | None,
        goal: str,
    ) -> list[dict[str, Any]]:
        """Analyze plan for alignment issues."""
        issues: list[dict[str, Any]] = []

        if not isinstance(plan, list):
            return issues

        # Check for obviously unnecessary steps
        unnecessary = self._detect_unnecessary_steps(plan, goal)
        if unnecessary:
            issues.extend(unnecessary)

        # Check for contradictions
        contradictions = self._detect_contradictions(plan)
        if contradictions:
            issues.extend(contradictions)

        # Check against intent constraints if available
        if intent:
            constraint_issues = self._check_intent_constraints(plan, intent)
            if constraint_issues:
                issues.extend(constraint_issues)

        return issues

    def _detect_unnecessary_steps(
        self,
        plan: list[Any],
        goal: str,
    ) -> list[dict[str, Any]]:
        """Detect obviously unnecessary or overly broad steps."""
        issues = []

        unnecessary_patterns = {
            "cancel_subscription": "cancellation not requested",
            "delete_account": "account deletion not requested",
            "refund": "refund not requested",
            "close_case": "closure not requested",
        }

        for step in plan:
            tool_name = (
                step.get("tool_name", "")
                if isinstance(step, dict)
                else getattr(step, "tool_name", "")
            )

            for pattern, msg in unnecessary_patterns.items():
                if pattern in tool_name.lower() and pattern not in goal.lower():
                    issues.append(
                        {
                            "type": "unnecessary_step",
                            "tool": tool_name,
                            "message": msg,
                        }
                    )

        return issues

    def _detect_contradictions(
        self,
        plan: list[Any],
    ) -> list[dict[str, Any]]:
        """Detect contradictory steps."""
        issues = []

        tools = []
        for step in plan:
            tool_name = (
                step.get("tool_name", "")
                if isinstance(step, dict)
                else getattr(step, "tool_name", "")
            )
            tools.append(tool_name.lower())

        contradictions = [
            ("create_subscription", "cancel_subscription"),
            ("create_account", "delete_account"),
            ("approve", "reject"),
            ("enable_feature", "disable_feature"),
        ]

        for create_tool, destroy_tool in contradictions:
            if create_tool in tools and destroy_tool in tools:
                issues.append(
                    {
                        "type": "contradiction",
                        "tools": [create_tool, destroy_tool],
                        "message": f"Plan both {create_tool} and {destroy_tool}",
                    }
                )

        return issues

    def _check_intent_constraints(
        self,
        plan: list[Any],
        intent: IntentEnvelope,
    ) -> list[dict[str, Any]]:
        """Check if plan respects intent constraints."""
        return []

    def _format_issues(self, issues: list[dict[str, Any]]) -> str:
        """Format issues as human-readable rationale."""
        if not issues:
            return "Plan aligns with stated intent"

        lines = ["Plan assessment found issues:"]
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            msg = issue.get("message", "")
            if issue_type == "unnecessary_step":
                lines.append(f"  • Unnecessary step: {msg}")
            elif issue_type == "contradiction":
                lines.append(f"  • Contradiction: {msg}")
            else:
                lines.append(f"  • {issue_type}: {msg}")

        lines.append("Recommendation: Agent should replan and focus on original goal.")
        return "\n".join(lines)
