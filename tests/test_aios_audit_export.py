from datetime import datetime, timedelta, timezone

import pytest

from agentic_sidecar.core.provenance import (
    AuditRecord,
    CausalLink,
    DecisionRationale,
    DecisionTrigger,
)
from agentic_sidecar.integrations.aios import export_audit_event
from aios08_helpers import assert_schema

NOW = datetime(2026, 11, 4, 18, tzinfo=timezone.utc)
TARGET = {"id": "target", "producer": "host", "artifact_id": "tool", "format": "host.tool"}


def native(outcome="BLOCK"):
    return AuditRecord(
        decision_id="decision-1",
        timestamp=NOW,
        outcome=outcome,
        trigger=DecisionTrigger("tool_call", "private-tool", {"secret": "private"}),
        rationale=DecisionRationale(reason="secret"),
        causal_link=CausalLink(parent_decision_id="prior", correlation_id="call-1"),
        execution_context={"secret": "private"},
    )


@pytest.mark.parametrize(
    "outcome,projected",
    [("BLOCK", "denied"), ("ALLOW", "requested"), ("WARN", "requested"), ("PAUSE", "requested")],
)
def test_native_governance_is_not_execution(outcome, projected):
    result = export_audit_event(native(outcome), target=TARGET, created_at=NOW)
    assert_schema(result)
    assert result["outcome"] == projected
    assert result["native_outcome"]["value"] == outcome
    assert result["actor"] == {"kind": "unknown"}
    assert result["correlation_id"] == "call-1"
    assert result["source"]["artifact_id"] == "decision-1"
    assert "private" not in str(result) and "secret" not in str(result)


def test_rejects_invented_time_self_causation_and_privileged_reference_fields():
    with pytest.raises(ValueError, match="precede"):
        export_audit_event(native(), target=TARGET, created_at=NOW - timedelta(seconds=1))
    record = native()
    record.causal_link.parent_decision_id = record.decision_id
    with pytest.raises(ValueError, match="cause itself"):
        export_audit_event(record, target=TARGET, created_at=NOW)
    with pytest.raises(ValueError, match="Reference fields"):
        export_audit_event(native(), target={**TARGET, "arguments": "secret"}, created_at=NOW)


def test_release_smoke_fails_when_required_credentials_are_missing(monkeypatch):
    import os
    import subprocess
    import sys
    from pathlib import Path

    env = {
        key: value
        for key, value in os.environ.items()
        if key
        not in {
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "SIDECAR_OPENAI_MODEL",
            "SIDECAR_ANTHROPIC_MODEL",
        }
    }
    run = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parents[1] / "scripts/smoke_judge_providers.py"),
            "--require-all",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 2 and '"status": "not_run"' in run.stdout
