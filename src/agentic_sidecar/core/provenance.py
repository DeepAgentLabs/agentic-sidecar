"""Decision provenance and audit trail -- durable record of what was decided,
why, when, and what it triggered.

v0.4 introduces these shapes for decisions that reach a Human Escalation
boundary (PAUSE, ESCALATE, CHALLENGE, REPLAN). The full Decision object
already holds (status, risk, reason); these types layer audit/export detail
on top, particularly causal links: correlating a decision to the execution
history that prompted it and any prior decisions it revises.

See ROADMAP.md §v0.4 for the deliverable definition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


DecisionOutcome = Literal[
    "ALLOW", "WARN", "BLOCK", "CHALLENGE", "REPLAN", "PAUSE", "ESCALATE"
]


@dataclass
class DecisionTrigger:
    """Details of the action that triggered the decision boundary.

    Attributes:
        boundary_type: 'tool_call' or other decision boundary.
        tool_name: Name of the tool/MCP server being called.
        arguments: Arguments passed to the tool.
    """

    boundary_type: str  # 'tool_call' in v0.4
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionRationale:
    """Explains why the gate reached a particular outcome.

    Attributes:
        policy_findings: Any Policy Advisor matches (permit/deny rules).
        risk_findings: Risk Evaluator classification and threshold violations.
        intent_findings: Intent Guardian constraint violations or drift.
        budget_findings: Budget Guardian violations (cost/token exceeded).
        reason: Composite human-readable explanation.
    """

    policy_findings: list[str] = field(default_factory=list)
    risk_findings: list[str] = field(default_factory=list)
    intent_findings: list[str] = field(default_factory=list)
    budget_findings: list[str] = field(default_factory=list)
    reason: str = ""

    def all_findings(self) -> list[str]:
        """All findings across all modules."""
        return (
            self.policy_findings
            + self.risk_findings
            + self.intent_findings
            + self.budget_findings
        )


@dataclass
class CausalLink:
    """Links a decision to the prior decision or plan step that caused it.

    Attributes:
        parent_decision_id: ID of the decision that prompted this one (e.g. a
            CHALLENGE decision prompts a REPLAN).
        parent_plan_step: Step in the agent's plan that this decision evaluates.
        correlation_id: Unique identifier tying this decision to execution trace.
    """

    parent_decision_id: str | None = None
    parent_plan_step: int | None = None
    correlation_id: str | None = None


@dataclass
class AuditRecord:
    """Durable audit record of a consequential decision.

    Created when a decision reaches a Decision Gate outcome that's worth
    recording (PAUSE, ESCALATE, CHALLENGE, REPLAN, BLOCK, or WARN). Exported
    to governance/graph backends (v0.6+) and used by AgenticLens for
    provenance tracking.

    Attributes:
        decision_id: Unique identifier for this decision.
        timestamp: When the decision was made.
        outcome: The Decision.status (ALLOW, WARN, BLOCK, ...).
        trigger: DecisionTrigger describing the action that prompted it.
        rationale: DecisionRationale explaining the outcome.
        causal_link: CausalLink to parent decision or plan step.
        execution_context: Snapshot of agent state at decision time.
    """

    decision_id: str
    timestamp: datetime
    outcome: DecisionOutcome
    trigger: DecisionTrigger
    rationale: DecisionRationale
    causal_link: CausalLink | None = None
    execution_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for export to external systems."""
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp.isoformat(),
            "outcome": self.outcome,
            "trigger": {
                "boundary_type": self.trigger.boundary_type,
                "tool_name": self.trigger.tool_name,
                "arguments": self.trigger.arguments,
            },
            "rationale": {
                "policy_findings": self.rationale.policy_findings,
                "risk_findings": self.rationale.risk_findings,
                "intent_findings": self.rationale.intent_findings,
                "budget_findings": self.rationale.budget_findings,
                "reason": self.rationale.reason,
            },
            "causal_link": (
                {
                    "parent_decision_id": self.causal_link.parent_decision_id,
                    "parent_plan_step": self.causal_link.parent_plan_step,
                    "correlation_id": self.causal_link.correlation_id,
                }
                if self.causal_link
                else None
            ),
            "execution_context": self.execution_context,
        }
