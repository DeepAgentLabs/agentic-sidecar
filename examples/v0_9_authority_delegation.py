"""Narrowed delegation and revocation; offline, with no real refunds."""

from agentic_sidecar import AuthorityBinding, Sidecar, SidecarBlockedError
from agentic_sidecar.adapters.callable import attach
from agentic_sidecar.intent import ConstraintBinding, IntentEnvelope, IntentGuardian

parent = IntentGuardian(
    IntentEnvelope(
        goal="Resolve a billing issue",
        requested_by={"id": "operator"},
        authority={"refund": True},
        constraints={"maximum_refund": 100},
    ),
    [ConstraintBinding(constraint="maximum_refund", tool="refund", arg_name="amount")],
    authority_bindings=[AuthorityBinding(authority="refund", tool="refund")],
    task_id="billing-42",
    agent_id="supervisor",
)
child = parent.delegate(agent_id="refund-agent", authority={"refund": True})
sidecar = Sidecar(
    on_sidecar_failure="fail_closed", mode="govern", roles=["intent_guardian"], intent=child
)


def refund(amount: int) -> str:
    """Return a simulated refund result."""
    return f"Simulated refund: {amount}"


(tool,) = attach(sidecar, [refund])
print(tool(50))
parent.revoke()
try:
    tool(50)
except SidecarBlockedError:
    print("Ancestor authority revoked; no second refund executed.")
assert sidecar.runtime.snapshot()["executed"] == 1
