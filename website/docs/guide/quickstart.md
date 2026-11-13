# Quickstart

**Supervise: Should this proposed action proceed under the declared policy and intent?**

**Input:** Proposed tool actions, policy rules, intent constraints, and recorded budgets.  
**Output:** Decision records and adapter-mediated allow, block, or escalation behavior.

## Install

```
python -m pip install agentic-sidecar
```

## Check a decision, then enforce it

This example uses a synthetic delete function that only appends to a list. The wrapper accepts plain callables; a running LangGraph agent is not required for this example.

sidecar_quickstart.py · complete file

```python
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
```

[Download sidecar_quickstart.py](examples/sidecar_quickstart.py)

```
python sidecar_quickstart.py
```

**Expected:** a block verdict, a blocked governed dispatch, and zero calls to the synthetic delete function.

## Connect your tools

Define policy and intent constraints for proposed actions. Place interception before actual tool dispatch. Verify both the decision and whether the underlying tool executed. Configure approval handling for suspended or escalated actions explicitly.

[Governance ↗](../governance.md)[Configure rules ↗](../configuration.md)
