"""The Decision Gate: Policy Advisor, Risk Evaluator, and (v0.4) Budget
Guardian.

Answers "are you permitted to do this?" (policy.py) and "how dangerous is
this action?" (risk.py) -- deliberately separate from `intent/`, which
answers the harder question "is this actually what the human asked you to
accomplish?" See README.md's "How the Decision Gate evaluates a decision"
and ROADMAP.md's Design Constraint 5 before adding a check here that's
really an intent question.

`policy.py` and `risk.py` are implemented as of v0.1 (rule-based, zero LLM
calls). `budget.py` is planned for v0.4 and not implemented yet.
"""

from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyEffect, PolicyResult, PolicyRule
from agentic_sidecar.gate.risk import RISK_ORDER, RiskEvaluator, RiskResult, RiskRule

__all__ = [
    "RISK_ORDER",
    "PolicyAdvisor",
    "PolicyEffect",
    "PolicyResult",
    "PolicyRule",
    "RiskEvaluator",
    "RiskResult",
    "RiskRule",
]
