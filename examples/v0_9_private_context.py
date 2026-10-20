"""Reader access and redacted evidence; trusted harness controls identities."""

import json

from agentic_sidecar import ContextSpec, DecisionContext, ScopedSystem, ScopeLayer

system = ScopedSystem(
    system_id="support",
    task_id="ticket-42",
    agents=["research", "refund"],
    exclusive={
        "refund": ScopeLayer(
            context=ContextSpec(
                values={"payment_reference": "private-reference"},
                readers={"auditor"},
            )
        )
    },
)
refund = system.bind("refund", on_sidecar_failure="fail_closed")
assert refund.context(reader="auditor")["values"]["payment_reference"] == "private-reference"
try:
    refund.context(reader="research")
except PermissionError:
    print("Research agent cannot read refund context.")
refund.sidecar.evaluate(DecisionContext(tool_name="read"))
print(json.dumps(refund.evidence(), indent=2))
refund.revoke_context(actor="refund")
