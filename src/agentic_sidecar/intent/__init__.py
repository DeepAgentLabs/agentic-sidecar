"""Intent Guardian: `IntentEnvelope`, `ConstraintBinding`, and alignment
scoring/drift detection against an active envelope (concept.md §6-9).

Implemented as of v0.2. Answers "is this actually what the human asked you
to accomplish?" -- deliberately separate from `gate/policy.py`'s "are you
permitted to do this?" (see README.md's "How the Decision Gate evaluates a
decision" and ROADMAP.md's Design Constraint 5: a check that's really a
static allow/deny belongs in `gate/policy.py`, not here).
"""

from agentic_sidecar.intent.alignment import (
    AlignmentFinding,
    AlignmentResult,
    ConstraintBinding,
    IntentGuardian,
    evaluate_alignment,
)
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester

__all__ = [
    "AlignmentFinding",
    "AlignmentResult",
    "ConstraintBinding",
    "IntentEnvelope",
    "IntentGuardian",
    "Requester",
    "evaluate_alignment",
]
