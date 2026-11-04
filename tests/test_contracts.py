"""Offline candidate contracts, migration and live authority propagation."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from agentic_sidecar.contracts import (
    AuditContract,
    DecisionContract,
    IntentContract,
    IntentTransfer,
    ScopeContract,
    contract_schema,
    export_audit,
)
from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.core.decision import Decision
from agentic_sidecar.core.provenance import AuditRecord, DecisionRationale, DecisionTrigger
from agentic_sidecar.intent.alignment import ConstraintBinding, IntentGuardian
from agentic_sidecar.intent.authority import AuthorityBinding
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester
from agentic_sidecar.scopes import ContextSpec, ScopeLayer


def parent():
    return IntentGuardian(
        IntentEnvelope(
            goal="Refund within limit",
            requested_by=Requester(id="operator"),
            constraints={"limit": 10},
            authority={"refund": True},
            expires=datetime.now(timezone.utc) + timedelta(hours=1),
        ),
        [ConstraintBinding(constraint="limit", tool="refund", arg_name="amount")],
        authority_bindings=[AuthorityBinding(authority="refund", tool="refund")],
        task_id="task",
        agent_id="planner",
    )


def test_native_migration_preserves_identity_and_unknown_markers_fail():
    decision = Decision(status="BLOCK", risk=None, reason="gate failed", causal_link="parent")
    migrated = DecisionContract(
        schema_version="sidecar.decision/1", decision=Decision.model_validate(decision.model_dump())
    )
    assert DecisionContract.model_validate_json(migrated.model_dump_json()).decision == decision
    intent = parent().envelope
    assert (
        IntentContract.model_validate_json(
            IntentContract(schema_version="sidecar.intent/1", intent=intent).model_dump_json()
        ).intent
        == intent
    )
    with pytest.raises(ValidationError):
        DecisionContract.model_validate(
            {"schema_version": "sidecar.decision/2", "decision": decision}
        )
    with pytest.raises(ValidationError):
        DecisionContract.model_validate({"decision": decision, "authorization": True})
    with pytest.raises(ValueError, match="Unknown"):
        contract_schema("unknown")


def test_cross_instance_propagation_and_ancestor_revocation():
    root = parent()
    wire = IntentTransfer.propose(root, agent_id="worker", authority={"refund": True})
    restored = IntentTransfer.model_validate_json(wire.model_dump_json())
    child = restored.receive(root, agent_id="worker")
    assert child.envelope.constraints == root.envelope.constraints
    assert child.envelope.expires == root.envelope.expires
    assert child.envelope.metadata["parent_intent_id"] == root.envelope.id
    assert (
        child.evaluate(DecisionContext(tool_name="refund", tool_args={"amount": 11})).status
        == "BLOCK"
    )
    assert (
        child.evaluate(DecisionContext(tool_name="refund", tool_args={"amount": 5})).status
        == "ALLOW"
    )
    grandchild = IntentTransfer.propose(
        child, agent_id="auditor", authority={"refund": False}
    ).receive(child, agent_id="auditor")
    assert grandchild.check_authority(DecisionContext(tool_name="refund")).status == "BLOCK"
    root.revoke()
    assert child.check_authority(DecisionContext(tool_name="refund")).status == "BLOCK"
    with pytest.raises(ValueError, match="revoked"):
        restored.receive(root, agent_id="worker")
    with pytest.raises(ValueError):
        restored.receive(parent(), agent_id="worker")


@pytest.mark.parametrize(
    "field,value",
    [
        ("authority", {"admin": True}),
        ("constraints", {}),
        ("expires", None),
        ("goal", "Different task"),
        ("metadata", {}),
    ],
)
def test_tampered_transfer_fails_closed(field, value):
    root = parent()
    wire = IntentTransfer.propose(root, agent_id="worker", authority={"refund": True}).model_dump(
        mode="json"
    )
    wire["intent"][field] = value
    with pytest.raises(ValueError):
        IntentTransfer.model_validate(wire).receive(root, agent_id="worker")


def test_identity_expiry_and_restart_fail_closed():
    root = parent()
    wire = IntentTransfer.propose(root, agent_id="worker", authority={})
    with pytest.raises(ValueError):
        wire.receive(root, agent_id="impostor")
    root.envelope.expires = datetime.now(timezone.utc) - timedelta(seconds=1)
    with pytest.raises(ValueError):
        IntentTransfer.propose(root, agent_id="worker", authority={})
    with pytest.raises(ValueError):
        IntentTransfer.propose(parent(), agent_id="worker", authority={"admin": True})


def test_scope_roundtrip_conflicts_and_reader_privacy():
    scope = ScopeContract(
        schema_version="sidecar.scope/1",
        system_id="system",
        task_id="task",
        agents=["a", "b"],
        shared=ScopeLayer(context=ContextSpec(values={"public": 1})),
        exclusive={"a": ScopeLayer(context=ContextSpec(values={"secret": 2}))},
    )
    rebuilt = ScopeContract.model_validate_json(scope.model_dump_json()).build()
    a = rebuilt.bind("a", on_sidecar_failure="fail_closed")
    b = rebuilt.bind("b", on_sidecar_failure="fail_closed")
    assert "secret" not in b.context()["values"]
    with pytest.raises(PermissionError):
        a.context(reader="b")
    scope.exclusive["a"].context.values["public"] = 3
    with pytest.raises(ValueError, match="Conflicting"):
        scope.build()


def test_audit_roundtrip_preserves_causality():
    record = AuditRecord(
        decision_id="decision",
        timestamp=datetime.now(timezone.utc),
        outcome="BLOCK",
        trigger=DecisionTrigger(boundary_type="tool_call", tool_name="refund"),
        rationale=DecisionRationale(reason="limit"),
    )
    assert AuditContract.model_validate(export_audit(record)).audit == record
    record.timestamp = datetime(2026, 1, 1)
    with pytest.raises(ValueError, match="timezone"):
        export_audit(record)


@pytest.mark.parametrize("kind", ["intent", "decision", "audit", "scope", "transfer"])
def test_published_schema_matches_runtime(kind):
    path = Path(__file__).parents[1] / "schemas" / "v1" / f"{kind}.schema.json"
    assert json.loads(path.read_text()) == contract_schema(kind)


def test_transferred_intent_enforces_dispatch_and_stop_across_sidecar_instances():
    from agentic_sidecar import Sidecar, SidecarBlockedError

    root = parent()
    child = IntentTransfer.model_validate_json(
        IntentTransfer.propose(
            root, agent_id="worker", authority={"refund": True}
        ).model_dump_json()
    ).receive(root, agent_id="worker")
    supervisor = Sidecar(
        on_sidecar_failure="fail_closed", mode="govern", roles=["intent_guardian"], intent=root
    )
    worker = Sidecar(
        on_sidecar_failure="fail_closed", mode="govern", roles=["intent_guardian"], intent=child
    )
    context = DecisionContext(tool_name="refund", tool_args={"amount": 5})
    decision = worker.evaluate(context)
    assert decision.status == "ALLOW"
    supervisor.runtime.control("stop", "operator")
    with pytest.raises(SidecarBlockedError, match="revoked"):
        worker.runtime.dispatch(context, decision)
    supervisor.runtime.control("restart", "operator")
    assert worker.evaluate(DecisionContext(tool_name="refund")).status == "BLOCK"


@pytest.mark.parametrize(
    "model,kind",
    [
        (IntentContract, "intent"),
        (DecisionContract, "decision"),
        (AuditContract, "audit"),
        (ScopeContract, "scope"),
        (IntentTransfer, "transfer"),
    ],
)
def test_portable_example_roundtrip(model, kind):
    path = Path(__file__).parents[1] / "schemas" / "v1" / f"{kind}.example.json"
    data = json.loads(path.read_text())
    assert model.model_validate(data).model_dump(mode="json") == data


@pytest.mark.parametrize(
    "model,kind",
    [
        (IntentContract, "intent"),
        (DecisionContract, "decision"),
        (AuditContract, "audit"),
        (ScopeContract, "scope"),
        (IntentTransfer, "transfer"),
    ],
)
def test_missing_marker_is_not_silently_migrated(model, kind):
    path = Path(__file__).parents[1] / "schemas" / "v1" / f"{kind}.example.json"
    data = json.loads(path.read_text())
    del data["schema_version"]
    with pytest.raises(ValidationError, match="schema_version"):
        model.model_validate(data)
    assert "schema_version" in contract_schema(kind)["required"]


@pytest.mark.parametrize("identity", ["", "   ", "parent"])
def test_child_identity_cannot_be_empty_or_reuse_parent(identity):
    root = parent()
    wire = IntentTransfer.propose(root, agent_id="worker", authority={}).model_dump(mode="json")
    wire["intent"]["id"] = root.envelope.id if identity == "parent" else identity
    with pytest.raises(ValueError):
        IntentTransfer.model_validate(wire).receive(root, agent_id="worker")


def test_receipt_rejects_expired_child_before_registering_grant():
    root = parent()
    proposal = IntentTransfer.propose(root, agent_id="worker", authority={})
    wire = proposal.model_dump(mode="json")
    wire["intent"]["expires"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError):
        IntentTransfer.model_validate(wire).receive(root, agent_id="worker")
