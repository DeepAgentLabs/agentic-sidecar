"""Intent Guardian -- drift detection and constraint validation against an
active `IntentEnvelope` (concept.md §8/§9).

Constraint bindings and optional task-authority grants are deterministic.
Authority requires explicit tool bindings and trusted task/agent identities.
"""

from __future__ import annotations

import fnmatch
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.core.operators import ArgOp, compare
from agentic_sidecar.intent.authority import AuthorityBinding, AuthorityRegistry
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester

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
        *,
        authority_bindings: list[AuthorityBinding] | None = None,
        registry: AuthorityRegistry | None = None,
        task_id: str = "",
        agent_id: str = "",
        parent_grant: str | None = None,
    ) -> None:
        self.envelope = envelope.model_copy(deep=True)
        self.bindings = [binding.model_copy(deep=True) for binding in bindings or []]
        self.authority_bindings = tuple(authority_bindings or ())
        self.registry = registry or AuthorityRegistry()
        self.task_id = task_id
        self.agent_id = agent_id
        self.grant_id = (
            self.registry.grant(envelope, task_id=task_id, agent_id=agent_id, parent=parent_grant)
            if self.authority_bindings
            else None
        )

    def evaluate(self, context: DecisionContext) -> AlignmentResult:
        authority = self.check_authority(context)
        if authority.status == "BLOCK":
            return authority
        return evaluate_alignment(context, self.envelope, self.bindings)

    def check_authority(self, context: DecisionContext) -> AlignmentResult:
        if self.grant_id is None:
            return AlignmentResult(status="ALLOW", reason="No authority bindings configured")
        reason = self.registry.invalid_reason(self.grant_id)
        if reason:
            return AlignmentResult(status="BLOCK", reason=reason)
        names = (
            [step["tool_name"] for step in context.plan]
            if context.boundary == "plan"
            else [context.tool_name]
        )
        for name in names:
            for binding in self.authority_bindings:
                if fnmatch.fnmatch(name, binding.tool) and not self.registry.permits(
                    self.grant_id, binding.authority
                ):
                    return AlignmentResult(
                        status="BLOCK", reason=f"Task authority required: {binding.authority}"
                    )
        return AlignmentResult(status="ALLOW", reason="Task authority granted")

    def revoke(self) -> None:
        if self.grant_id is None:
            raise ValueError("No task authority grant configured")
        self.registry.revoke(self.grant_id)

    def delegate(
        self, *, agent_id: str, authority: dict[str, bool], expires: datetime | None = None
    ) -> IntentGuardian:
        """Narrow permissions and expiry; preserve all inherited constraints/bindings."""
        if self.grant_id is None:
            raise ValueError("Delegation requires task authority bindings")
        child = IntentEnvelope(
            goal=self.envelope.goal,
            requested_by=Requester(type="agent", id=self.agent_id),
            constraints=self.envelope.constraints,
            authority=authority,
            expires=expires if expires is not None else self.envelope.expires,
            metadata={"parent_intent_id": self.envelope.id},
        )
        return IntentGuardian(
            child,
            self.bindings,
            authority_bindings=list(self.authority_bindings),
            registry=self.registry,
            task_id=self.task_id,
            agent_id=agent_id,
            parent_grant=self.grant_id,
        )
