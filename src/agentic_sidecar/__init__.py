"""agentic-sidecar: a companion intelligence and real-time decision
supervision layer for autonomous AI agents.

    The Main Agent acts. The Sidecar observes, thinks, advises, and governs.

v0.1 shipped the Sidecar runtime and a rule-based, LLM-free Decision Gate
(Policy Advisor + Risk Evaluator), attached via the LangGraph adapter, in
Observe mode. v0.2 adds Intent Guardian (`agentic_sidecar.intent`) and
Govern mode, where a `BLOCK` decision is actually enforced. See ROADMAP.md
for the full build order and README.md for the architecture and Python API.
"""

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.core.decision import Decision, DecisionStatus, RiskLevel
from agentic_sidecar.core.exceptions import SidecarBlockedError
from agentic_sidecar.core.sidecar import Sidecar

__version__ = "0.2.0"

__all__ = [
    "Decision",
    "DecisionContext",
    "DecisionStatus",
    "RiskLevel",
    "Sidecar",
    "SidecarBlockedError",
    "__version__",
]
