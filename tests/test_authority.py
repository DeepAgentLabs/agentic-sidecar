"""Task authority, delegation narrowing, expiry, revocation and dispatch races."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from agentic_sidecar import (
    AuthorityBinding,
    Decision,
    DecisionContext,
    Sidecar,
    SidecarBlockedError,
)
from agentic_sidecar.intent import ConstraintBinding, IntentEnvelope, IntentGuardian


def root(**kwargs):
    return IntentGuardian(
        IntentEnvelope(
            goal="Refund",
            requested_by={"id": "operator"},
            authority={"refund": True, "delete": False},
            constraints={"max": 500},
            **kwargs,
        ),
        [ConstraintBinding(constraint="max", tool="refund", arg_name="amount")],
        authority_bindings=[
            AuthorityBinding(authority="refund", tool="refund"),
            AuthorityBinding(authority="delete", tool="delete*"),
        ],
        task_id="billing-1",
        agent_id="supervisor",
    )


def sidecar(guardian, **kwargs):
    return Sidecar(
        on_sidecar_failure="fail_closed",
        mode="govern",
        roles=["intent_guardian"],
        intent=guardian,
        **kwargs,
    )


def test_granted_denied_and_missing_task_authority():
    guardian = root()
    governed = sidecar(guardian)
    assert (
        governed.evaluate(DecisionContext(tool_name="refund", tool_args={"amount": 100})).status
        == "ALLOW"
    )
    assert governed.evaluate(DecisionContext(tool_name="delete_account")).status == "BLOCK"
    child = guardian.delegate(agent_id="researcher", authority={})
    assert sidecar(child).evaluate(DecisionContext(tool_name="refund")).status == "BLOCK"


def test_hook_cannot_override_authority_and_plan_checks_every_step():
    governed = sidecar(root())
    governed.before_tool_call(lambda _: Decision(status="ALLOW", risk=None, reason="override"))
    assert governed.evaluate(DecisionContext(tool_name="delete_account")).status == "BLOCK"
    assert (
        governed.evaluate_plan([{"tool_name": "read"}, {"tool_name": "delete_account"}]).status
        == "BLOCK"
    )


def test_delegation_preserves_constraints_scope_and_narrows_permissions():
    parent = root(expires=datetime.now(timezone.utc) + timedelta(hours=1))
    child = parent.delegate(agent_id="refund-agent", authority={"refund": True})
    assert child.task_id == parent.task_id
    assert child.envelope.metadata["parent_intent_id"] == parent.envelope.id
    assert (
        sidecar(child)
        .evaluate(DecisionContext(tool_name="refund", tool_args={"amount": 999}))
        .status
        == "BLOCK"
    )
    with pytest.raises(ValueError, match="widen"):
        parent.delegate(agent_id="bad", authority={"delete": True})
    with pytest.raises(ValueError, match="extend"):
        parent.delegate(
            agent_id="bad", authority={}, expires=parent.envelope.expires + timedelta(hours=1)
        )
    with pytest.raises(ValueError, match="task scope"):
        parent.registry.grant(
            child.envelope, task_id="other", agent_id="bad", parent=parent.grant_id
        )


def test_ancestor_revocation_invalidates_outstanding_child_authorization():
    parent = root()
    child = parent.delegate(agent_id="refund-agent", authority={"refund": True})
    governed = sidecar(child)
    context = DecisionContext(tool_name="refund", tool_args={"amount": 100})
    decision = governed.evaluate(context)
    parent.revoke()
    with pytest.raises(SidecarBlockedError, match="revoked"):
        governed.runtime.dispatch(context, decision)
    with pytest.raises(ValueError, match="revoked"):
        child.delegate(agent_id="retry", authority={"refund": True})


def test_expired_authority_blocks_even_when_tool_has_no_matching_binding():
    governed = sidecar(root(expires=datetime.now(timezone.utc) - timedelta(seconds=1)))
    assert governed.evaluate(DecisionContext(tool_name="read")).status == "BLOCK"


def test_stop_revokes_descendants_and_restart_does_not_restore_grants():
    parent = root()
    supervisor = sidecar(parent)
    child = sidecar(parent.delegate(agent_id="child", authority={"refund": True}))
    supervisor.runtime.control("stop", "operator")
    supervisor.runtime.control("restart", "operator")
    assert child.evaluate(DecisionContext(tool_name="refund")).status == "BLOCK"
    assert supervisor.evaluate(DecisionContext(tool_name="refund")).status == "BLOCK"


def test_no_forbidden_reservations_after_revocation_acknowledgement():
    parent = root()
    children = [
        sidecar(parent.delegate(agent_id=f"agent-{i}", authority={"refund": True}))
        for i in range(8)
    ]
    proposals = [
        (s, DecisionContext(tool_name="refund", tool_args={"amount": 10})) for s in children
    ]
    decisions = [(s, c, s.evaluate(c)) for s, c in proposals]
    parent.revoke()

    def dispatch(proposal):
        s, context, decision = proposal
        with pytest.raises(SidecarBlockedError):
            s.runtime.dispatch(context, decision)
        return s.runtime.snapshot()["executed"]

    with ThreadPoolExecutor(max_workers=8) as executor:
        assert list(executor.map(dispatch, decisions)) == [0] * 8


def test_operator_intent_update_cannot_escape_delegation():
    governed = sidecar(root())
    with pytest.raises(ValueError, match="re-delegation"):
        governed.runtime.modify_intent(governed.intent.envelope.model_dump(mode="json"), "operator")
    assert not any(e["kind"] == "intent_modified" for e in governed.runtime.journal.export())


def test_expiry_is_rechecked_at_dispatch(monkeypatch):
    import agentic_sidecar.intent.authority as authority_module

    clock = datetime.now(timezone.utc)

    class Clock:
        @staticmethod
        def now(tz):
            return clock

    monkeypatch.setattr(authority_module, "datetime", Clock)
    governed = sidecar(root(expires=clock + timedelta(seconds=1)))
    context = DecisionContext(tool_name="refund", tool_args={"amount": 10})
    decision = governed.evaluate(context)
    assert decision.status == "ALLOW"
    clock += timedelta(seconds=2)
    with pytest.raises(SidecarBlockedError, match="expired"):
        governed.runtime.dispatch(context, decision)
