"""Offline cross-instance intent propagation with live ancestor revocation."""

from agentic_sidecar.contracts import IntentTransfer, ScopeContract, contract_schema
from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.intent.alignment import IntentGuardian
from agentic_sidecar.intent.authority import AuthorityBinding
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester

parent = IntentGuardian(
    IntentEnvelope(
        goal="Read inventory", requested_by=Requester(id="operator"), authority={"read": True}
    ),
    authority_bindings=[AuthorityBinding(authority="read", tool="read_inventory")],
    task_id="inventory",
    agent_id="planner",
)
proposal = IntentTransfer.propose(parent, agent_id="worker", authority={"read": True})
wire = proposal.model_dump_json()
child = IntentTransfer.model_validate_json(wire).receive(parent, agent_id="worker")
assert child.check_authority(DecisionContext(tool_name="read_inventory")).status == "ALLOW"
parent.revoke()
assert child.check_authority(DecisionContext(tool_name="read_inventory")).status == "BLOCK"
scope = ScopeContract(system_id="warehouse", task_id="inventory", agents=["worker"])
scope.build().bind("worker", on_sidecar_failure="fail_closed")
assert contract_schema("transfer")["properties"]["schema_version"]["const"] == "sidecar.transfer/1"
print("Cross-instance intent preserved; ancestor revocation blocks subsequent calls.")
