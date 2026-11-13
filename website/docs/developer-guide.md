# Agentic Sidecar developer guide

Use this guide to set up Agentic Sidecar, run a local example, and apply it to your application. Optional provider and integration fragments identify the objects or services you must supply.

[Quickstart](#quickstart) · [Usage](#usage) · [Configuration](#settings) · [Troubleshooting](#troubleshooting) · [Reference](#reference)

## Quickstart

Requires Python 3.10 or newer. Run commands in an activated virtual environment. Download referenced files into the same working directory before running them.

### Install

```
python -m pip install agentic-sidecar
```

### Check a decision, then enforce it

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

[Download sidecar_quickstart.py](guide/examples/sidecar_quickstart.py)

```
python sidecar_quickstart.py
```

**Expected:** a block verdict, a blocked governed dispatch, and zero calls to the synthetic delete function.

### Connect your tools

Define policy and intent constraints for proposed actions. Place interception before actual tool dispatch. Verify both the decision and whether the underlying tool executed. Configure approval handling for suspended or escalated actions explicitly.

[Governance ↗](governance.md) · [Configure rules ↗](configuration.md)

## Usage

<span id="approvals"></span>

### Handle approvals and plan review

#### Local approval flow

```
from agentic_sidecar import Sidecar
from agentic_sidecar.cli.approval import CLIApprovalHandler

sidecar = Sidecar(
    on_sidecar_failure="fail_closed", mode="govern",
    escalation_handler=CLIApprovalHandler(),
)
```

Attach configured tools with `adapters.langgraph.attach()`. The handler prompts

when evaluation produces PAUSE/ESCALATE. Try `agentic-sidecar approval-demo`

without executing a tool. You can also register `on_escalation_required`.

| Action | Result |
| --- | --- |
| approve_once | Authorizes this invocation; the next proposal is evaluated and approved separately |
| reject | BLOCK for this proposal |
| modify_intent | Validates a full IntentEnvelope, preserves bindings, reevaluates once; another intervention suspends |
| ask_agent_to_replan | REPLAN; return control to the agent loop |
| stop_agent | BLOCK and stop subsequent proposals on this Sidecar instance |

Responses must reference the request's decision ID. Each resolution gets its

own ID and causal_link to the originating decision. BLOCK is never offered

for approval. Missing handlers suspend, independently of failure mode. Handler

errors/malformed responses follow the configured failure policy.

Custom loops call `evaluate(context)` then `enforce(context, decision)` before

dispatch. Catch SidecarBlockedError/SidecarSuspendedError to handle outcomes;

neither exception executes the proposed tool. Review the offline walkthrough:

```
uv run python examples/v0_6_1_governance.py
```

#### Full-plan review

```
from agentic_sidecar import PlanEvaluator, Sidecar

sidecar = Sidecar(on_sidecar_failure="fail_closed", roles=["planner"], planner=PlanEvaluator())
decision = sidecar.evaluate_plan(
    [{"tool_name": "read_charge"}, {"tool_name": "issue_refund"}],
    goal="Explain the disputed charge",
)
assert decision.status == "REPLAN"
```

An active envelope supplies the goal/constraints. Enabled deterministic gates

check every plan step; evaluators receive goal, constraints, history, intent,

plan, bindings and metadata. This boundary reviews a supplied plan without

executing it. Planner/Critic remain scoped heuristics; see [Limitations](limitations.md).

<span id="settings"></span>

## Configuration

### Configure supervision modules

#### `Sidecar` constructor

```
from agentic_sidecar import Sidecar

sidecar = Sidecar(
    on_sidecar_failure="fail_closed",
    mode="observe",
    roles=["policy", "risk"],
)
```

The following table lists constructor arguments. Configure each optional module

and include its role to enable it. See [Features](features.md) for evaluator

and narrator examples.

#### Parameters

| Parameter | Default | Behavior |
| --- | --- | --- |
| `on_sidecar_failure` | Required | Choose `fail_open` or `fail_closed` explicitly. |
| `mode` | `observe` | Use `govern` with an enforcement adapter to block or suspend dispatch. |
| `roles` | `policy`, `risk` | Select which evaluation modules run. |
| `policy` | Empty `PolicyAdvisor` | The empty policy allows actions. |
| `risk` | Empty `RiskEvaluator` | Unmatched actions are classified as low risk. |
| `risk_block_threshold` | `HIGH` | Risk at or above this level produces a block. |
| `intent`, `budget`, `planner`, `critic`, `judge` | `None` | Supply the module and enable its role. Providing intent without the intent role is rejected. |
| `escalation_handler` | `None` | Govern mode uses it to resolve paused or escalated actions. |

Additional runtime and mandatory-check arguments are described in the [API reference](api-reference.md).

#### `roles` — controlling which modules run

The `roles` parameter is the main switch for enabling/disabling evaluation modules. Only modules listed in `roles` are consulted during `evaluate()`.

**Supported roles:**

| Role | Module |
| --- | --- |
| `"policy"` | Policy Advisor |
| `"risk"` | Risk Evaluator |
| `"intent_guardian"` | Intent Guardian |
| `"budget"` | Budget Guardian |
| `"planner"` | Plan Evaluator |
| `"critic"` | Critic Evaluator |
| `"judge"` | Judge Evaluator |

**Default roles when `roles=None`:** `["policy", "risk"]`

**Composition example — using the configured `policy`, `risk`, `guardian`, and `budget` objects below:**

```
sidecar = Sidecar(
    on_sidecar_failure="fail_closed",
    mode="govern",
    policy=policy,
    risk=risk,
    intent=guardian,
    budget=budget,
    roles=["policy", "risk", "intent_guardian", "budget"],
)
```

#### `PolicyAdvisor` configuration

```
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule

# In-code rules
policy = PolicyAdvisor(
    rules=[PolicyRule(tool="delete_*", effect="deny")],
    default_effect="allow",   # default when no rule matches
)

# From YAML file
policy = PolicyAdvisor.from_yaml("policies/my_policy.yaml")

# From a dict (useful in tests)
policy = PolicyAdvisor.from_mapping({
    "default": "allow",
    "rules": [{"tool": "delete_*", "effect": "deny"}],
})
```

**`PolicyRule` fields:**

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `tool` | `str` | Required | `fnmatch` glob pattern matched against tool name |
| `effect` | `"allow"` or `"deny"` | Required | Verdict when this rule matches |
| `reason` | `str` or `None` | `None` | Human-readable explanation |

#### `RiskEvaluator` configuration

```
from agentic_sidecar.gate.risk import RiskEvaluator, RiskRule

risk = RiskEvaluator(
    rules=[
        RiskRule(tool="issue_refund", arg_name="amount", arg_op="gt", arg_value=500, risk="HIGH"),
        RiskRule(tool="delete_*", risk="HIGH"),
    ],
    default_risk="LOW",
)
```

**`RiskRule` fields:**

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `tool` | `str` | Required | `fnmatch` glob pattern |
| `risk` | `"LOW"`, `"MEDIUM"`, or `"HIGH"` | Required | Risk level when this rule matches |
| `reason` | `str` or `None` | `None` | Human-readable explanation |
| `arg_name` | `str` or `None` | `None` | Argument to check (optional) |
| `arg_op` | `ArgOp` | `"eq"` | Comparison operator: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `contains` |
| `arg_value` | `Any` | `None` | Value to compare against |

#### `BudgetGuardian` configuration

```
from agentic_sidecar.gate import BudgetGuardian

budget = BudgetGuardian(
    max_cost=5.00,       # USD ceiling
    max_tokens=10_000,   # token ceiling (optional)
)

# Record usage manually after each LLM/tool invocation
budget.record_invocation(cost=0.03, tokens=1200)

# Reset for the next task
budget.reset()
```

#### `IntentEnvelope` and `IntentGuardian` configuration

```
from agentic_sidecar.intent import (
    IntentEnvelope, IntentGuardian, ConstraintBinding, Requester
)
from datetime import datetime, timezone

envelope = IntentEnvelope(
    goal="Assist customer dispute — refund up to $500",
    requested_by=Requester(type="human", id="user_42"),
    constraints={"maximum_refund": 500.0},
    authority={"can_delete": False},
    expires=datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc),  # optional
)

bindings = [
    ConstraintBinding(
        constraint="maximum_refund",
        tool="issue_refund",
        arg_name="amount",
        op="lte",
        severity="BLOCK",
    )
]

guardian = IntentGuardian(envelope, bindings)
```

**`ConstraintBinding` fields:**

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `constraint` | `str` | Required | Key in `envelope.constraints` |
| `tool` | `str` | Required | `fnmatch` glob for tool name |
| `arg_name` | `str` | Required | Argument to check |
| `op` | `ArgOp` | `"lte"` | Comparison operator |
| `severity` | `"WARN"` | `"BLOCK"` | `"BLOCK"` | Decision outcome when violated |
| `reason` | `str` or `None` | `None` | Override the auto-generated reason |

Budget counters are shared with the object passed to Sidecar. Record actual

usage explicitly for external calls; Judge usage reaches this budget once.

PAUSE suspends Govern dispatch or invokes the configured approval handler.

See [Governance](governance.md) for provider rates and limit configuration.

## Troubleshooting

Check the failing boundary before changing application behavior.

- A blocked verdict but a running tool: check whether you called `evaluate()` only or used Observe mode.
- Wrong rule matched: inspect policy order and the callable's tool name.
- Agent hangs on approval: inspect the approval handler and unresolved decision status.

### Verify your environment

Run commands from the environment where you installed the package. Confirm the input file exists and matches the expected artifact contract. Keep the original evidence when diagnosing a failure.

## Reference

Use the current product reference for exact method signatures, command options, and supported artifacts. The code fragments in configuration and how-to articles build on the quickstart; they are not all standalone scripts.

- [Open API / CLI reference ↗](cli-reference.md)
