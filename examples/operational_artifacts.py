"""Offline native-to-AIOS projection; grants no authority or stable conformance."""

import json
from datetime import datetime, timezone

from agentic_sidecar import AuditRecord, DecisionRationale, DecisionTrigger
from agentic_sidecar.integrations.aios import export_audit_event

at = datetime(2026, 11, 4, 18, tzinfo=timezone.utc)
record = AuditRecord(
    decision_id="decision-1",
    timestamp=at,
    outcome="BLOCK",
    trigger=DecisionTrigger("tool_call", "lookup"),
    rationale=DecisionRationale(),
)
target = {"id": "target", "producer": "example", "artifact_id": "lookup", "format": "host.tool"}
print(json.dumps(export_audit_event(record, target=target, created_at=at), indent=2))
