"""Privacy boundaries owned by Sidecar; harness transports are explicit."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from agentic_sidecar import ContextSpec, DecisionContext, ScopedSystem, ScopeLayer

SECRET = "exclusive-payment-secret-9831"


def agents(**context_options):
    return ScopedSystem(
        system_id="billing",
        task_id="case-1",
        agents=["research", "refund"],
        exclusive={
            "refund": ScopeLayer(
                context=ContextSpec(goal=SECRET, values={"payment": SECRET}, **context_options)
            )
        },
    )


def test_private_context_does_not_enter_evaluators_logs_journal_or_evidence(caplog):
    system = agents()
    refund = system.bind("refund", on_sidecar_failure="fail_closed")
    research = system.bind("research", on_sidecar_failure="fail_closed")
    delivered = []
    refund.deliver(delivered.append)
    assert delivered[0]["values"]["payment"] == SECRET
    assert SECRET not in json.dumps(research.context())
    with pytest.raises(PermissionError):
        refund.context(reader="research")
    observed = []
    from agentic_sidecar import Decision

    refund.sidecar.before_tool_call(
        lambda c: (
            observed.append(c.model_dump()) or Decision(status="ALLOW", risk=None, reason="ok")
        )
    )
    refund.sidecar.evaluate(DecisionContext(tool_name="read"))
    for value in [
        observed,
        refund.sidecar.runtime.snapshot(),
        refund.sidecar.runtime.journal.export(),
        refund.evidence(),
    ]:
        assert SECRET not in json.dumps(value)
    assert SECRET not in caplog.text


def test_authorized_reader_copies_and_owner_only_updates():
    refund = agents(readers={"auditor"}).bind("refund", on_sidecar_failure="fail_closed")
    copy = refund.context(reader="auditor")
    copy["values"].clear()
    assert refund.context()["values"]["payment"] == SECRET
    with pytest.raises(PermissionError):
        refund.update_context({}, actor="auditor")
    refund.update_context({"updated": 1}, actor="refund")
    assert refund.context()["values"] == {"updated": 1}
    with pytest.raises(PermissionError):
        refund.revoke_context(actor="auditor")
    refund.revoke_context(actor="refund")
    with pytest.raises(PermissionError):
        refund.context()


def test_context_expiry_and_naive_dates():
    refund = agents(expires=datetime.now(timezone.utc) - timedelta(seconds=1)).bind(
        "refund", on_sidecar_failure="fail_closed"
    )
    with pytest.raises(PermissionError):
        refund.context()
    with pytest.raises(ValueError):
        ContextSpec(expires=datetime(2026, 1, 1))


def test_redacted_evidence_removes_secrets_echoed_into_tool_arguments():
    refund = agents().bind("refund", on_sidecar_failure="fail_closed")
    refund.sidecar.evaluate(DecisionContext(tool_name="read", tool_args={"secret": SECRET}))
    assert SECRET in json.dumps(refund.sidecar.runtime.snapshot())
    assert SECRET not in json.dumps(refund.evidence())
    assert refund.evidence()["redacted"] is True


def test_concurrent_agents_do_not_share_private_state_or_history():
    system = agents()

    def run(name):
        bound = system.bind(name, on_sidecar_failure="fail_closed")
        bound.sidecar.evaluate(DecisionContext(tool_name=name))
        return name, bound.context(), bound.evidence()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = dict(
            (name, (context, evidence))
            for name, context, evidence in executor.map(run, ["research", "refund"])
        )
    assert SECRET not in json.dumps(results["research"])
    assert len(results["refund"][1]["decisions"]) == 1


def test_reader_operator_view_is_redacted_and_cannot_mutate_or_read_raw_events():
    from urllib.error import HTTPError

    from agentic_sidecar import OperatorServer
    from agentic_sidecar.operations.client import request

    refund = agents().bind("refund", on_sidecar_failure="fail_closed")
    refund.sidecar.evaluate(DecisionContext(tool_name="read", tool_args={"payment": SECRET}))
    token = "operator-" + "x" * 32
    reader = "reader-" + "y" * 32
    with OperatorServer(
        refund.sidecar.runtime, token=token, actor="owner", reader_tokens={reader: "auditor"}
    ) as server:
        summary = request(server.url, reader, "/status")
        assert SECRET not in json.dumps(summary)
        assert summary["redacted"] is True
        assert SECRET in json.dumps(request(server.url, token, "/status"))
        for route, body in [("/events", None), ("/control", {"action": "stop"})]:
            with pytest.raises(HTTPError) as error:
                request(server.url, reader, route, body)
            assert error.value.code == 403


def test_tool_results_and_handoff_do_not_implicitly_propagate_private_context():
    from agentic_sidecar.adapters.callable import attach

    system = agents()
    refund = system.bind("refund", on_sidecar_failure="fail_closed")
    research = system.bind("research", on_sidecar_failure="fail_closed")

    def read():
        """Return a private result to the owning agent only."""
        return SECRET

    assert attach(refund.sidecar, [read])[0]() == SECRET
    assert SECRET not in json.dumps(refund.sidecar.runtime.snapshot())
    assert SECRET not in json.dumps(research.context())
    assert SECRET not in json.dumps(research.evidence())
