"""Human-readable status narration for agent execution.

Translates raw tool calls, decisions, and MCP traces into readable narrative
form: current objective, active step, intent alignment, risk, and budget status.

v0.5 implements narration; CLI and Control Room dashboard integration follow.
See concept.md §19 for the narration design.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agentic_sidecar.core.decision import Decision, RiskLevel


@dataclass
class ToolCallNarrative:
    """Human-readable narration of a single tool invocation."""

    tool_name: str
    timestamp: datetime
    narrative: str  # e.g., "🔎 Looking up order #1234"
    arguments: dict[str, Any] = field(default_factory=dict)
    decision: Decision | None = None
    risk_level: RiskLevel | None = None
    intent_compliant: bool = True


@dataclass
class StatusNarrative:
    """Live status snapshot: current objective, step, alignment, risk, budget."""

    timestamp: datetime
    current_objective: str | None = None
    current_step: str | None = None
    steps_completed: int = 0
    tool_calls_made: int = 0
    decisions_blocked: int = 0
    decisions_paused: int = 0
    intent_violations: int = 0
    max_risk_seen: RiskLevel | None = None
    current_budget_remaining: float | None = None
    current_tokens_remaining: int | None = None
    last_tool_narrative: ToolCallNarrative | None = None
    is_paused: bool = False
    pause_reason: str | None = None


class StatusNarrator:
    """Tracks agent execution and generates human-readable status updates.

    Builds a narrative from tool calls, Decision Gate outcomes, and context.
    """

    def __init__(self) -> None:
        self.objectives: list[str] = []
        self.tool_calls: list[ToolCallNarrative] = []
        self.blocked_decisions: int = 0
        self.paused_decisions: int = 0
        self.intent_violations: int = 0
        self.max_risk_seen: RiskLevel | None = None
        self.is_paused: bool = False
        self.pause_reason: str | None = None

    def set_objective(self, objective: str) -> None:
        """Set the top-level objective the agent is working toward."""
        self.objectives.append(objective)

    def record_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        decision: Decision | None = None,
        risk_level: RiskLevel | None = None,
        intent_compliant: bool = True,
    ) -> ToolCallNarrative:
        """Record a tool invocation with its narration and decision outcome.

        Args:
            tool_name: The tool/function name.
            arguments: Arguments passed to the tool.
            decision: The Sidecar Decision for this call (if evaluated).
            risk_level: Risk level assigned by Risk Evaluator.
            intent_compliant: Whether the call is aligned with intent.

        Returns:
            The recorded narrative for this tool call.
        """
        narrative = self._narrate_tool_call(tool_name, arguments)

        if decision and decision.status == "BLOCK":
            self.blocked_decisions += 1
        elif decision and decision.status == "PAUSE":
            self.paused_decisions += 1

        if not intent_compliant:
            self.intent_violations += 1

        if risk_level:
            self._update_max_risk(risk_level)

        tool_narrative = ToolCallNarrative(
            tool_name=tool_name,
            timestamp=datetime.now(),
            narrative=narrative,
            arguments=arguments,
            decision=decision,
            risk_level=risk_level,
            intent_compliant=intent_compliant,
        )

        self.tool_calls.append(tool_narrative)
        return tool_narrative

    def pause(self, reason: str) -> None:
        """Record that execution has been paused pending human approval."""
        self.is_paused = True
        self.pause_reason = reason

    def resume(self) -> None:
        """Record that execution has resumed after pause."""
        self.is_paused = False
        self.pause_reason = None

    def get_status(
        self,
        current_objective: str | None = None,
        current_budget_remaining: float | None = None,
        current_tokens_remaining: int | None = None,
    ) -> StatusNarrative:
        """Build a complete status snapshot.

        Args:
            current_objective: The current step/objective in progress.
            current_budget_remaining: Remaining cost budget (USD).
            current_tokens_remaining: Remaining token budget.

        Returns:
            A complete StatusNarrative with all tracked metrics.
        """
        return StatusNarrative(
            timestamp=datetime.now(),
            current_objective=(
                current_objective or (self.objectives[-1] if self.objectives else None)
            ),
            current_step=current_objective,
            steps_completed=len(self.tool_calls),
            tool_calls_made=len(self.tool_calls),
            decisions_blocked=self.blocked_decisions,
            decisions_paused=self.paused_decisions,
            intent_violations=self.intent_violations,
            max_risk_seen=self.max_risk_seen,
            current_budget_remaining=current_budget_remaining,
            current_tokens_remaining=current_tokens_remaining,
            last_tool_narrative=self.tool_calls[-1] if self.tool_calls else None,
            is_paused=self.is_paused,
            pause_reason=self.pause_reason,
        )

    def get_narrative(self) -> str:
        """Return the full narrative of the execution so far as a string."""
        lines = []

        if self.objectives:
            lines.append(f"📋 Objective: {self.objectives[-1]}")
            lines.append("")

        if self.tool_calls:
            lines.append("Steps taken:")
            for i, call in enumerate(self.tool_calls, 1):
                status = "✓"
                if call.decision and call.decision.status == "BLOCK":
                    status = "✗ BLOCKED"
                elif call.decision and call.decision.status == "PAUSE":
                    status = "⏸ PAUSED"
                elif not call.intent_compliant:
                    status = "⚠ INTENT DRIFT"

                lines.append(f"  {i}. {status} {call.narrative}")

            lines.append("")

        if self.is_paused:
            lines.append(f"⏸️ PAUSED: {self.pause_reason or 'Awaiting approval'}")
            lines.append("")

        if self.blocked_decisions > 0:
            lines.append(f"🚫 Blocked decisions: {self.blocked_decisions}")

        if self.paused_decisions > 0:
            lines.append(f"⏸️ Paused decisions: {self.paused_decisions}")

        if self.intent_violations > 0:
            lines.append(f"⚠️ Intent violations detected: {self.intent_violations}")

        if self.max_risk_seen:
            lines.append(f"⚠️ Max risk encountered: {self.max_risk_seen}")

        return "\n".join(lines)

    @staticmethod
    def _narrate_tool_call(tool_name: str, arguments: dict[str, Any]) -> str:
        """Generate a human-readable narration for a tool call.

        Heuristic-based narration that generates narrative from common tool
        names and argument patterns. Future versions can use model-based
        narration for more sophisticated descriptions.

        Args:
            tool_name: Name of the tool being called.
            arguments: Arguments passed to the tool.

        Returns:
            A human-readable narrative of the tool call.
        """
        narrations = {
            "search": "🔍 Searching for information",
            "lookup": "🔎 Looking up data",
            "retrieve": "📥 Retrieving records",
            "query": "❓ Querying database",
            "create": "✍️ Creating new record",
            "update": "🔄 Updating record",
            "delete": "🗑️ Deleting record",
            "send": "📤 Sending message",
            "fetch": "⬇️ Fetching data",
            "call": "📞 Making call",
            "refund": "💰 Processing refund",
            "payment": "💳 Processing payment",
        }

        if tool_name.lower() in narrations:
            return narrations[tool_name.lower()]

        for keyword, narrative in narrations.items():
            if keyword in tool_name.lower():
                return narrative

        return f"⚙️ Executing {tool_name}"

    def _update_max_risk(self, risk_level: RiskLevel) -> None:
        """Update the maximum risk seen so far."""
        risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        if self.max_risk_seen is None or risk_order.get(risk_level, -1) > risk_order.get(
            self.max_risk_seen, -1
        ):
            self.max_risk_seen = risk_level
