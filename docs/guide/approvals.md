# Handle approvals and plan review

Reference examples below show API composition and configuration fragments. Start with the complete quickstart before adapting these to your application.

## Local approval flow

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

## Full-plan review

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

executing it. Planner/Critic remain scoped heuristics; see [Limitations](../limitations.md).
