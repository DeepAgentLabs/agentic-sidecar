"""`Decision(status, risk, reason)` -- the Decision Gate's output type.

v0.1 shipped `status in {"ALLOW", "BLOCK"}` only. v0.2 adds `WARN` --
Intent Guardian's outcome for a finding that's worth surfacing (e.g. a
stale/expired envelope) but not severe enough to block. `CHALLENGE`,
`REPLAN`, `PAUSE`, and `ESCALATE` -- the rest of concept.md §15's seven
outcomes -- land at v0.4. See README.md's "How the Decision Gate evaluates
a decision" and ROADMAP.md's build order.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

DecisionStatus = Literal["ALLOW", "WARN", "BLOCK"]
"""v0.1 shipped ALLOW/BLOCK; v0.2 adds WARN. The remaining outcomes from
concept.md §15's seven land at v0.4.
"""

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
"""Risk Evaluator classification (gate/risk.py) -- static rules only in v0.1."""


class Decision(BaseModel):
    """The outcome of a single Decision Gate evaluation for one proposed
    action (tool call).

    `risk` is `None` only on the `on_sidecar_failure` path (core/sidecar.py)
    -- when the Sidecar itself errored before Policy/Risk ever ran, there is
    no risk classification to report, and reporting one would misrepresent
    what actually happened.

    Frozen: a `Decision` is a record of what was decided, not a value meant
    to be mutated after the fact.
    """

    model_config = ConfigDict(frozen=True)

    status: DecisionStatus
    risk: RiskLevel | None
    reason: str
