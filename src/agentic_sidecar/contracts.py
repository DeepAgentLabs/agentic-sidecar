"""Candidate native interchange contracts; importing evidence never grants authority.

AIOS mappings are documented in the specification repository. These markers
are independent of package versions and do not claim normative conformance.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agentic_sidecar.core.decision import Decision
from agentic_sidecar.core.provenance import AuditRecord
from agentic_sidecar.intent.alignment import IntentGuardian
from agentic_sidecar.intent.authority import AuthorityRegistry
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester
from agentic_sidecar.scopes import ScopedSystem, ScopeLayer


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class IntentContract(_Contract):
    schema_version: Literal["sidecar.intent/1"]
    intent: IntentEnvelope


class DecisionContract(_Contract):
    schema_version: Literal["sidecar.decision/1"]
    decision: Decision


class AuditContract(_Contract):
    schema_version: Literal["sidecar.audit/1"]
    audit: AuditRecord

    @field_validator("audit")
    @classmethod
    def aware_timestamp(cls, value: AuditRecord) -> AuditRecord:
        if value.timestamp.tzinfo is None or value.timestamp.utcoffset() is None:
            raise ValueError("Audit timestamp must be timezone-aware")
        return value


class ScopeContract(_Contract):
    schema_version: Literal["sidecar.scope/1"]
    system_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    agents: list[str] = Field(min_length=1)
    shared: ScopeLayer = Field(default_factory=ScopeLayer)
    exclusive: dict[str, ScopeLayer] = Field(default_factory=dict)

    def build(self) -> ScopedSystem:
        """Trusted-host import; validates conflicts before any agent can bind."""
        return ScopedSystem(
            system_id=self.system_id,
            task_id=self.task_id,
            agents=self.agents,
            shared=self.shared,
            exclusive=self.exclusive,
        )


class IntentTransfer(_Contract):
    """Untrusted proposal until a receiving host checks its live parent grant.

    Bindings come exclusively from the host's parent guardian. The shared
    registry is required: disconnected replicas cannot prove revocation state.
    """

    schema_version: Literal["sidecar.transfer/1"]
    parent_intent_id: str = Field(min_length=1)
    parent_grant_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    intent: IntentEnvelope

    def receive(self, parent: IntentGuardian, *, agent_id: str) -> IntentGuardian:
        """Revalidate scope, expiry, constraints and authority in the live registry."""
        if (
            not self.intent.id.strip()
            or self.intent.id == self.parent_intent_id
            or self.intent.is_expired()
            or not parent.authority_bindings
            or self.parent_intent_id != parent.envelope.id
            or self.parent_grant_id != parent.grant_id
            or self.task_id != parent.task_id
            or self.agent_id != agent_id
            or self.intent.goal != parent.envelope.goal
            or self.intent.requested_by.type != "agent"
            or self.intent.requested_by.id != parent.agent_id
            or self.intent.metadata.get("parent_intent_id") != parent.envelope.id
        ):
            raise ValueError("Intent transfer identity or goal mismatch")
        return IntentGuardian(
            self.intent,
            parent.bindings,
            authority_bindings=list(parent.authority_bindings),
            registry=parent.registry,
            task_id=self.task_id,
            agent_id=agent_id,
            parent_grant=self.parent_grant_id,
        )

    @classmethod
    def propose(
        cls, parent: IntentGuardian, *, agent_id: str, authority: dict[str, bool]
    ) -> IntentTransfer:
        """Create a narrowed proposal without installing a new authority grant."""
        if parent.grant_id is None:
            raise ValueError("Transfer requires a live parent authority grant")
        # Validate narrowing in an isolated registry; no live grants are created.
        check = AuthorityRegistry()
        root = check.grant(parent.envelope, task_id=parent.task_id, agent_id=parent.agent_id)
        intent = parent.envelope.model_copy(deep=True)
        intent.id = str(uuid4())
        intent.requested_by = Requester(type="agent", id=parent.agent_id)
        intent.authority = dict(authority)
        intent.metadata = {"parent_intent_id": parent.envelope.id}
        check.grant(intent, task_id=parent.task_id, agent_id=agent_id, parent=root)
        if parent.registry.invalid_reason(parent.grant_id):
            raise ValueError("Parent authority is no longer valid")
        return cls(
            schema_version="sidecar.transfer/1",
            parent_intent_id=parent.envelope.id,
            parent_grant_id=parent.grant_id,
            task_id=parent.task_id,
            agent_id=agent_id,
            intent=intent,
        )


_CONTRACTS: dict[str, type[BaseModel]] = {
    "intent": IntentContract,
    "decision": DecisionContract,
    "audit": AuditContract,
    "scope": ScopeContract,
    "transfer": IntentTransfer,
}


def contract_schema(kind: str) -> dict[str, Any]:
    """Return a fresh offline JSON Schema; unknown contract families fail explicitly."""
    try:
        return _CONTRACTS[kind].model_json_schema()
    except KeyError as error:
        raise ValueError(f"Unknown Sidecar contract: {kind}") from error


def export_audit(record: AuditRecord) -> dict[str, Any]:
    """Validate and serialize an existing audit; no timestamps or IDs invented."""
    return AuditContract(schema_version="sidecar.audit/1", audit=record).model_dump(mode="json")
