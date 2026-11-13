from agentic_sidecar import DecisionContext, Sidecar, SidecarBlockedError
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule
from agentic_sidecar.adapters.langgraph import attach

policy = PolicyAdvisor([PolicyRule(tool="delete_*", effect="deny")])
observer = Sidecar(on_sidecar_failure="fail_closed", policy=policy)
print("Verdict:", observer.evaluate(DecisionContext(tool_name="delete_customer")).status)

calls = []
def delete_customer(customer_id: str) -> str:
    """Synthetic function: record a call, without deleting anything."""
    calls.append(customer_id)
    return "simulated deletion"

governor = Sidecar(mode="govern", on_sidecar_failure="fail_closed", policy=policy)
(guarded_delete,) = attach(governor, [delete_customer])
try:
    guarded_delete("demo-123")
except SidecarBlockedError as exc:
    print("Governed decision:", exc.decision.status)
assert not calls, "The synthetic delete function must not execute."
print("Function calls:", len(calls))

