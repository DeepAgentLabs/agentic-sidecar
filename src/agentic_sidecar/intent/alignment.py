"""Intent Guardian -- drift detection and constraint validation against an
active `IntentEnvelope` (concept.md §8/§9).

v0.2 scope is deliberately narrow: constraint validation only (numeric/
enum/allow-list fields, e.g. `maximum_refund: 500` vs. a proposed `850`) --
concept.md §9 and ROADMAP.md's v0.2 scope both frame this as the *first*
concrete semantic-authorization check, not the only one ever needed.
Authority-based blocking (`IntentEnvelope.authority`, e.g.
`refund_allowed: false`) is left for a later version: the envelope already
carries the field (see envelope.py), but there's no concrete tool-to-
authority binding shape yet, and Design Constraint 4's spirit applies here
too -- that shape deserves a real scenario before being built, not
speculative generality.
"""

from __future__ import annotations

import fnmatch
from typing import Literal

from pydantic import BaseModel, Field

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.core.operators import ArgOp, compare
from agentic_sidecar.intent.envelope import IntentEnvelope

AlignmentStatus = Literal["ALLOW", "WARN", "BLOCK"]


class ConstraintBinding(BaseModel):
    """Binds one `IntentEnvelope.constraints` entry to a specific tool
    argument so it can be checked deterministically -- a constraint alone
    (e.g. `maximum_refund: 500`) doesn't say which tool call it applies to.

    A binding produces a finding when the tool argument does *not* satisfy
    `actual <op> constraint_value`. E.g. `ConstraintBinding(
    constraint="maximum_refund", tool="issue_refund", arg_name="amount",
    op="lte")` flags any `issue_refund` call whose `amount` exceeds the
    envelope's `maximum_refund`. A binding for a constraint the active
    envelope doesn't declare, or a tool call missing the bound argument,
    simply doesn't match -- same "no rule matched" philosophy as
    `gate/policy.py` and `gate/risk.py`.
    """

    constraint: str
    tool: str
    arg_name: str
    op: ArgOp = "lte"
    severity: Literal["WARN", "BLOCK"] = "BLOCK"
    reason: str | None = None


class AlignmentFinding(BaseModel):
    """One violated binding, or the envelope-expiry check."""

    status: Literal["WARN", "BLOCK"]
    reason: str
    constraint: str | None = None


class AlignmentResult(BaseModel):
    """What Intent Guardian decided for one `DecisionContext`, and why.

    `status` is the single most severe finding (`BLOCK` beats `WARN` beats
    `ALLOW`); `findings` keeps every finding that fired, for callers that
    want the full picture rather than just the headline verdict.
    """

    status: AlignmentStatus
    reason: str
    findings: list[AlignmentFinding] = Field(default_factory=list)


def evaluate_alignment(
    context: DecisionContext,
    envelope: IntentEnvelope,
    bindings: list[ConstraintBinding] | None = None,
) -> AlignmentResult:
    """Check one proposed action against an `IntentEnvelope`: is the
    envelope still valid (not expired), and does the action satisfy every
    `ConstraintBinding` that applies to it?
    """
    findings: list[AlignmentFinding] = []

    if envelope.expires is not None and envelope.is_expired():
        findings.append(
            AlignmentFinding(
                status="WARN",
                reason=f"Intent envelope expired at {envelope.expires.isoformat()}",
            )
        )

    for binding in bindings or []:
        if not fnmatch.fnmatch(context.tool_name, binding.tool):
            continue
        if binding.constraint not in envelope.constraints:
            continue
        if binding.arg_name not in context.tool_args:
            continue
        constraint_value = envelope.constraints[binding.constraint]
        actual = context.tool_args[binding.arg_name]
        if compare(actual, binding.op, constraint_value):
            continue  # satisfies the constraint
        reason = binding.reason or (
            f"'{binding.arg_name}'={actual!r} on '{context.tool_name}' violates "
            f"constraint '{binding.constraint}' (must be {binding.op} {constraint_value!r})"
        )
        findings.append(
            AlignmentFinding(status=binding.severity, reason=reason, constraint=binding.constraint)
        )

    if not findings:
        return AlignmentResult(
            status="ALLOW",
            reason=f"No intent constraints violated for '{context.tool_name}'",
        )

    blocking = [f for f in findings if f.status == "BLOCK"]
    if blocking:
        return AlignmentResult(
            status="BLOCK",
            reason="; ".join(f.reason for f in blocking),
            findings=findings,
        )
    return AlignmentResult(
        status="WARN",
        reason="; ".join(f.reason for f in findings),
        findings=findings,
    )


class IntentGuardian:
    """Wraps an active `IntentEnvelope` plus its `ConstraintBinding`s --
    mirrors `PolicyAdvisor`/`RiskEvaluator`'s shape (`gate/policy.py`,
    `gate/risk.py`) for a consistent construction pattern across Decision
    Gate modules: `Sidecar(intent=IntentGuardian(envelope, bindings), ...)`.
    """

    def __init__(
        self,
        envelope: IntentEnvelope,
        bindings: list[ConstraintBinding] | None = None,
    ) -> None:
        self.envelope = envelope
        self.bindings = bindings or []

    def evaluate(self, context: DecisionContext) -> AlignmentResult:
        return evaluate_alignment(context, self.envelope, self.bindings)
