"""Regression cases from the full-project review."""

import pytest

from agentic_sidecar import CriticEvaluator, Decision, DecisionContext, Sidecar, SidecarBlockedError
from agentic_sidecar.adapters.callable import attach
from agentic_sidecar.gate.risk import RiskEvaluator, RiskRule
from agentic_sidecar.intent import ConstraintBinding, IntentEnvelope, IntentGuardian


def guardian(limit):
    return IntentGuardian(
        IntentEnvelope(goal="refund", requested_by={"id": "u"}, constraints={"max": limit}),
        [ConstraintBinding(constraint="max", tool="refund", arg_name="amount")],
    )


def test_replacing_intent_invalidates_existing_authorizations():
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        mode="govern",
        roles=["intent_guardian"],
        intent=guardian(500),
    )
    context = DecisionContext(tool_name="refund", tool_args={"amount": 400})
    decision = sidecar.evaluate(context)
    sidecar.set_intent(guardian(100))
    with pytest.raises(SidecarBlockedError):
        sidecar.runtime.dispatch(context, sidecar.enforce(context, decision))
    assert sidecar.evaluate(context).status == "BLOCK"


@pytest.mark.parametrize("asynchronous", [False, True])
def test_hooks_cannot_rewrite_the_authorized_action(asynchronous):
    import asyncio

    calls = []
    sidecar = Sidecar(on_sidecar_failure="fail_closed", mode="govern")

    @sidecar.before_tool_call
    def rewrite(context):
        context.tool_args["amount"] = 1
        return Decision(status="ALLOW", risk="LOW", reason="checked")

    def pay(amount):
        calls.append(amount)

    async def apay(amount):
        calls.append(amount)

    tool = attach(sidecar, [apay if asynchronous else pay])[0]
    with pytest.raises(SidecarBlockedError):
        if asynchronous:
            asyncio.run(tool(999))
        else:
            tool(999)
    assert calls == []


def test_plan_retains_highest_step_risk_and_findings():
    sidecar = Sidecar(
        on_sidecar_failure="fail_closed",
        risk=RiskEvaluator([RiskRule(tool="refund", risk="MEDIUM")]),
    )
    result = sidecar.evaluate_plan([{"tool_name": "refund"}, {"tool_name": "read"}])
    assert result.status == "ALLOW"
    assert result.risk == "MEDIUM"
    findings = sidecar.runtime.snapshot()["decisions"][-1]["rationale"]["findings"]
    assert findings["plan_steps"][0]["risk"]["risk"] == "MEDIUM"


def test_critic_uses_step_scoped_verification():
    critic = CriticEvaluator()
    evidence = {"authorized": True, "backup_verified": True}
    assert critic.evaluate({"tool_name": "delete_record", "metadata": evidence}).status == "ALLOW"
    assert (
        critic.evaluate({"plan": [{"tool_name": "delete_record", "metadata": evidence}]}).status
        == "ALLOW"
    )
    assert (
        critic.evaluate({"metadata": evidence, "plan": [{"tool_name": "delete_record"}]}).status
        == "CHALLENGE"
    )
