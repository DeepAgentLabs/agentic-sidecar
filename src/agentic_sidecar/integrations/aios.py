"""Optional AIOS audit projection; native decisions remain governance evidence."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from agentic_sidecar import __version__
from agentic_sidecar.core.provenance import AuditRecord
from agentic_sidecar.integrations._aios import identifier, reference, timestamp


def export_audit_event(
    record: AuditRecord, *, target: Mapping[str, Any], created_at: datetime
) -> dict[str, Any]:
    """Export public identifiers/outcome only, withholding rationale and context.

    ALLOW/WARN request permission to proceed, never prove execution. Actor is
    unknown because the native record does not carry authenticated attribution.
    Host-supplied target references must identify the native action's public target.
    """
    identifier(record.decision_id)
    occurred = timestamp(record.timestamp)
    created = timestamp(created_at)
    if created_at < record.timestamp:
        raise ValueError("Recording time cannot precede the decision observation")
    if record.outcome not in {"ALLOW", "WARN", "BLOCK", "CHALLENGE", "REPLAN", "PAUSE", "ESCALATE"}:
        raise ValueError("Unknown native decision outcome")
    parent = record.causal_link.parent_decision_id if record.causal_link else None
    if parent == record.decision_id:
        raise ValueError("An audit event cannot cause itself")
    result: dict[str, Any] = {
        "spec_version": "0.8-draft",
        "artifact_type": "audit_event",
        "id": f"sidecar:audit:{record.decision_id}",
        "created_at": created,
        "producer": {"name": "agentic-sidecar", "version": __version__},
        "source": {
            "id": "native-audit",
            "producer": "agentic-sidecar",
            "artifact_id": record.decision_id,
            "format": "sidecar.audit/1",
        },
        "occurred_at": occurred,
        "actor": {"kind": "unknown"},
        "action": "sidecar.decision",
        "target": reference(target),
        "outcome": "denied" if record.outcome == "BLOCK" else "requested",
        "native_outcome": {"format": "sidecar.audit/1", "value": record.outcome},
        "causal_event_ids": [f"sidecar:audit:{identifier(parent)}"] if parent else [],
    }
    if record.causal_link and record.causal_link.correlation_id:
        result["correlation_id"] = identifier(record.causal_link.correlation_id)
    return result
