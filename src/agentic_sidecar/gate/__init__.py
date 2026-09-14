"""The Decision Gate: Policy Advisor, Risk Evaluator, Budget Guardian (v0.4),
and Human Escalation (v0.4).

Answers "are you permitted to do this?" (policy.py), "how dangerous is this
action?" (risk.py), and "are we within budget?" (budget.py) -- deliberately
separate from `intent/`, which answers the harder question "is this actually
what the human asked you to accomplish?" See README.md's "How the Decision
Gate evaluates a decision" and ROADMAP.md's Design Constraint 5 before adding
a check here that's really an intent question.

Policy and Risk are implemented as of v0.1 (rule-based, zero LLM calls).
Budget Guardian and Escalation are fully implemented in v0.4.
"""

from agentic_sidecar.gate.budget import BudgetGuardian, BudgetResult
from agentic_sidecar.gate.escalation import (
    ApprovalAction,
    ApprovalResponse,
    EscalationHandler,
    EscalationRequest,
)
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyEffect, PolicyResult, PolicyRule
from agentic_sidecar.gate.risk import RISK_ORDER, RiskEvaluator, RiskResult, RiskRule

__all__ = [
    "RISK_ORDER",
    "ApprovalAction",
    "ApprovalResponse",
    "BudgetGuardian",
    "BudgetResult",
    "EscalationHandler",
    "EscalationRequest",
    "PolicyAdvisor",
    "PolicyEffect",
    "PolicyResult",
    "PolicyRule",
    "RiskEvaluator",
    "RiskResult",
    "RiskRule",
]
