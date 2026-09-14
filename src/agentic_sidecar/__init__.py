"""agentic-sidecar: a companion intelligence and real-time decision
supervision layer for autonomous AI agents.

    The Main Agent acts. The Sidecar observes, thinks, advises, and governs.

v0.1 shipped the Sidecar runtime and a rule-based, LLM-free Decision Gate
(Policy Advisor + Risk Evaluator), attached via the LangGraph adapter, in
Observe mode. v0.2 adds Intent Guardian (`agentic_sidecar.intent`) and
Govern mode, where a `BLOCK` decision is actually enforced. v0.4 adds the
full Decision Gate outcomes (CHALLENGE, REPLAN, PAUSE, ESCALATE), Budget
Guardian for cost/token ceilings, and Human Escalation primitives. See
ROADMAP.md for the full build order and README.md for the architecture and
Python API.
"""

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.core.decision import Decision, DecisionStatus, RiskLevel
from agentic_sidecar.core.exceptions import SidecarBlockedError
from agentic_sidecar.core.provenance import (
    AuditRecord,
    CausalLink,
    DecisionRationale,
    DecisionTrigger,
)
from agentic_sidecar.core.sidecar import Sidecar
from agentic_sidecar.evaluators import (
    AnthropicJudge,
    CriticChallenge,
    CriticEvaluator,
    EvaluatorBase,
    EvaluatorResult,
    JudgeEvaluator,
    JudgeProvider,
    OpenAIJudge,
    PlanEvaluator,
    PlanStep,
)
from agentic_sidecar.gate import (
    ApprovalAction,
    ApprovalResponse,
    BudgetGuardian,
    BudgetResult,
    EscalationHandler,
    EscalationRequest,
)
from agentic_sidecar.status import (
    StatusNarrative,
    StatusNarrator,
    ToolCallNarrative,
)

__version__ = "0.5.0"

__all__ = [
    "AnthropicJudge",
    "ApprovalAction",
    "ApprovalResponse",
    "AuditRecord",
    "BudgetGuardian",
    "BudgetResult",
    "CausalLink",
    "CriticChallenge",
    "CriticEvaluator",
    "Decision",
    "DecisionContext",
    "DecisionRationale",
    "DecisionStatus",
    "DecisionTrigger",
    "EscalationHandler",
    "EscalationRequest",
    "EvaluatorBase",
    "EvaluatorResult",
    "JudgeEvaluator",
    "JudgeProvider",
    "OpenAIJudge",
    "PlanEvaluator",
    "PlanStep",
    "RiskLevel",
    "Sidecar",
    "SidecarBlockedError",
    "StatusNarrative",
    "StatusNarrator",
    "ToolCallNarrative",
    "__version__",
]
