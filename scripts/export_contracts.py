"""Regenerate candidate native schemas and deterministic portable fixtures."""

import json
from datetime import datetime, timezone
from pathlib import Path

from agentic_sidecar.contracts import (
    AuditContract,
    DecisionContract,
    IntentContract,
    IntentTransfer,
    ScopeContract,
    contract_schema,
)
from agentic_sidecar.core.decision import Decision
from agentic_sidecar.core.provenance import AuditRecord, DecisionRationale, DecisionTrigger
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester

root = Path(__file__).resolve().parents[1] / "schemas" / "v1"
intent = IntentEnvelope(
    id="intent-child",
    goal="Read inventory",
    requested_by=Requester(type="agent", id="planner"),
    authority={"read": True},
    metadata={"parent_intent_id": "intent-parent"},
)
examples = {
    "intent": IntentContract(intent=intent),
    "decision": DecisionContract(
        decision=Decision(
            decision_id="decision-1",
            status="BLOCK",
            risk=None,
            reason="gate unavailable",
            causal_link="decision-parent",
        )
    ),
    "audit": AuditContract(
        audit=AuditRecord(
            decision_id="decision-1",
            timestamp=datetime(2026, 11, 4, tzinfo=timezone.utc),
            outcome="BLOCK",
            trigger=DecisionTrigger(boundary_type="tool_call", tool_name="read"),
            rationale=DecisionRationale(reason="gate unavailable"),
        )
    ),
    "scope": ScopeContract(system_id="warehouse", task_id="inventory", agents=["worker"]),
    "transfer": IntentTransfer(
        parent_intent_id="intent-parent",
        parent_grant_id="grant-parent",
        task_id="inventory",
        agent_id="worker",
        intent=intent,
    ),
}
for kind, example in examples.items():
    (root / f"{kind}.schema.json").write_text(json.dumps(contract_schema(kind), indent=2) + "\n")
    (root / f"{kind}.example.json").write_text(example.model_dump_json(indent=2) + "\n")
