"""Native correlation, journal verification and optional sibling consumers."""

from copy import deepcopy

import pytest

from agentic_sidecar import DecisionContext, Sidecar, SidecarBlockedError
from agentic_sidecar.integrations.agentic_chaos import evaluate_recovery
from agentic_sidecar.integrations.correlation import Correlation, export_decisions
from agentic_sidecar.operations.events import verify_events


def test_verified_export_and_tamper_rejection() -> None:
    sidecar = Sidecar(on_sidecar_failure="fail_closed")
    sidecar.evaluate(DecisionContext(tool_name="read"))
    correlation = Correlation(run_id="run", trace_id="trace", span_id="span")
    (evidence,) = export_decisions(sidecar, correlation)
    assert evidence.decision.decision_id == sidecar.decisions[0][1].decision_id
    assert evidence.correlation == correlation
    events = deepcopy(sidecar.runtime.journal.export())
    events[-1]["payload"]["decision"]["status"] = "BLOCK"
    with pytest.raises(ValueError, match="audit"):
        verify_events(events, task_id=sidecar.runtime.task_id)


def test_real_lens_correlation_and_timeline() -> None:
    pytest.importorskip("agenticlens.integrations.sidecar")
    from agenticlens.diagnosis import diagnose_run
    from agenticlens.models.trace import Run, Span, SpanType

    from agentic_sidecar.integrations.agenticlens import attach_decisions

    run = Run(
        application_name="sidecar-integration",
        spans=[Span(name="read", span_type=SpanType.TOOL_CALL)],
    )
    sidecar = Sidecar(on_sidecar_failure="fail_closed")
    sidecar.evaluate(DecisionContext(tool_name="read"))
    attach_decisions(sidecar, run, span_id=run.spans[0].span_id)
    attach_decisions(sidecar, run, span_id=run.spans[0].span_id)
    assert len(run.spans[0].attributes["sidecar.decisions"]) == 1
    assert any(event.kind == "supervision_decision" for event in diagnose_run(run).timeline.events)


def test_real_chaos_recovery_and_failure_policy() -> None:
    pytest.importorskip("agentic_chaos")
    from agentic_chaos.models.chaos_event import ChaosEvent

    from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule

    event = ChaosEvent(fault_type="tool_call_failure", outcome="errored", message="fixture")
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        mode="govern",
        policy=PolicyAdvisor([PolicyRule(tool="delete", effect="deny")]),
    )
    with pytest.raises(SidecarBlockedError):
        evaluate_recovery(sidecar, event.model_dump(mode="json"), tool_name="delete", arguments={})
    assert sidecar.decisions[0][0].metadata["chaos.event_id"] == event.id
    assert (
        evaluate_recovery(
            sidecar, event.model_dump(mode="json"), tool_name="read", arguments={}
        ).status
        == "ALLOW"
    )


@pytest.mark.parametrize("failure,expected", [("fail_open", "ALLOW"), ("fail_closed", "BLOCK")])
def test_actual_chaos_gate_timeout(failure, expected) -> None:
    pytest.importorskip("agentic_chaos")
    from agentic_chaos import chaos_call, chaos_session
    from agentic_chaos.chaos.faults import TokenTimeoutFault

    from agentic_sidecar import Decision

    sidecar = Sidecar(on_sidecar_failure=failure, mode="govern")
    sidecar.before_tool_call(
        lambda context: chaos_call(
            lambda: Decision(status="ALLOW", risk="LOW", reason="healthy"),
            step_name="sidecar-gate",
        )
    )
    with chaos_session([TokenTimeoutFault(hang_seconds=0)]) as session:
        decision = sidecar.evaluate(DecisionContext(tool_name="read"))
    assert decision.status == expected
    assert session.events[0].fault_type == "token_timeout"


def test_serialized_evidence_requires_original_decision_identity() -> None:
    import json
    from pathlib import Path

    from pydantic import ValidationError

    from agentic_sidecar.integrations.correlation import DecisionEvidence

    record = json.loads(
        (Path(__file__).parent / "fixtures/sidecar-correlation-v1.json").read_text()
    )
    del record["decision"]["decision_id"]
    with pytest.raises(ValidationError):
        DecisionEvidence.model_validate(record)


def test_chaos_v07_poisoning_retains_native_recovery_identity() -> None:
    pytest.importorskip("agentic_chaos", minversion="0.7.0")
    from agentic_chaos import PoisonedResponseFault, chaos_call, chaos_session

    from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule

    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        mode="govern",
        policy=PolicyAdvisor([PolicyRule(tool="delete", effect="deny")]),
    )
    with chaos_session([PoisonedResponseFault("policy_bypass", seed=7)]) as session:
        chaos_call(lambda: "safe")
    event = session.events[0]
    with pytest.raises(SidecarBlockedError):
        evaluate_recovery(sidecar, event.model_dump(mode="json"), tool_name="delete", arguments={})
    assert sidecar.decisions[0][0].metadata["chaos.event_id"] == event.id


def test_chaos_v08_workflow_events_retain_native_recovery_identity() -> None:
    pytest.importorskip("agentic_chaos", minversion="0.8.0")
    from agentic_chaos import PoisonedResponseFault, Scope, chaos_call
    from agentic_chaos.workflows import ChaosWorkflow, Step

    from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule

    workflow = ChaosWorkflow(
        "sidecar-recovery",
        [Step("poison", faults=[PoisonedResponseFault("policy_bypass", seed=7)])],
        scope=Scope(steps=["planner"]),
    )
    report = workflow.run(lambda: chaos_call(lambda: "safe", step_name="planner"))
    (event,) = report.chaos_events
    assert event["detail"]["workflow"]["step"] == "poison"

    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        mode="govern",
        policy=PolicyAdvisor([PolicyRule(tool="delete", effect="deny")]),
    )
    with pytest.raises(SidecarBlockedError):
        evaluate_recovery(sidecar, event, tool_name="delete", arguments={})
    assert sidecar.decisions[0][0].metadata["chaos.event_id"] == event["id"]


def test_chaos_v09_scored_reports_retain_native_recovery_identity() -> None:
    pytest.importorskip("agentic_chaos", minversion="0.9.0")
    from agentic_chaos import PoisonedResponseFault, Scope, chaos_call, chaos_run
    from agentic_chaos.probes import FunctionProbe

    from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule

    report = chaos_run(
        lambda: chaos_call(lambda: "safe", step_name="planner"),
        [PoisonedResponseFault("policy_bypass", seed=7, scope=Scope(steps=["planner"]))],
        probes=[FunctionProbe(lambda: "ok", name="ping")],
    )
    (event,) = report.model_dump(mode="json")["chaos_events"]
    assert report.resilience is not None
    # Sidecar containment does not make a poisoned response "recovered" in the
    # Chaos score: without a fidelity judge it stays unverified.
    assert report.resilience["faults"][0]["verdicts"] == {"unverified": 1}

    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        mode="govern",
        policy=PolicyAdvisor([PolicyRule(tool="delete", effect="deny")]),
    )
    with pytest.raises(SidecarBlockedError):
        evaluate_recovery(sidecar, event, tool_name="delete", arguments={})
    assert sidecar.decisions[0][0].metadata["chaos.event_id"] == event["id"]
