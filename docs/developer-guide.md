# Agentic Sidecar developer guide

Use this simple guide to choose a capability and connect it to an explicit tool boundary. The [AI Reference (robust)](https://deepagentlabs.io/agentic-sidecar/docs/llms-full.md) includes detailed topic guides, current package/CLI declarations and all five native schemas. Observe mode records decisions; Govern enforces them through the returned tools.

[Capability index](#capability-index) · [Quickstart](#quickstart) · [Configuration](#settings) · [Troubleshooting](#troubleshooting) · [Reference](#reference)

## Capability index

Every row links to a short workflow below. Detailed references explain configuration, inputs, outputs and limitations.

| Capability | What you can do |
| --- | --- |
| [Decision Gate and enforcement](#gate) | Evaluate seven outcomes, then enforce through governed dispatch. |
| [Policy and risk rules](#policy-risk) | Apply ordered allow/deny policies and tool/argument risk classifications. |
| [Intent constraints](#intent) | Bind user constraints to tool arguments, catch intent drift and retain intent identity and expiry. |
| [Budget accounting](#budget) | Track explicit cost/tokens and pause at configured ceilings. |
| [Plan review and Critic](#plan-review) | Review supplied plans, unnecessary steps, contradictions and unsupported assumptions. |
| [Offline and live judges](#judges) | Use MockJudge or optional OpenAI/Anthropic providers with limits and usage accounting. |
| [Human in the loop: approvals and escalation](#approvals) | Approve once, reject, modify intent, replan or stop a suspended proposal. |
| [Custom hooks and failure policies](#hooks) | Extend decision evaluation while preserving mandatory checks and explicit failure behavior. |
| [Framework and MCP adapters](#adapters) | Govern sync/async tools in LangGraph, AutoGen, CrewAI, OpenAI Agents, Google ADK and MCP. |
| [Task runtime and execution lifecycle](#runtime) | Track proposals, decisions, dispatch reservations, completion and failure. |
| [Operator server and Control Room](#operators) | Watch a task live and pause, resume, replan, stop or restart it, with remote approvals. |
| [Emergency stop, cancellation and revocation](#stop) | Latch dispatch stop, invalidate old decisions, cancel owned async calls and revoke host-owned access. |
| [Control Tower fleet operations](#control-tower) | Join Sidecar evidence to fleet incidents and stop many deployments through one approved bulk action. |
| [Audit journal and restoration](#audit) | Persist immutable hash-chained events, verify snapshots and restore stopped state. |
| [Shared/exclusive supervision](#scopes) | Compose agent-specific context and mandatory guardrails without weakening shared rules. |
| [Context privacy and lifecycle](#privacy) | Authorize readers, deliver defensive copies, update, expire and revoke context. |
| [Redacted evidence and operator readers](#evidence) | Expose allowlisted summaries separately from privileged native artifacts. |
| [Task authority and delegation](#authority) | Require grants, narrow child permissions and enforce ancestor expiry/revocation at dispatch. |
| [Native interchange contracts](#contracts) | Validate intent, decision, audit, scope and transfer wrappers against five candidate schemas. |
| [Cross-agent intent transfer](#transfer) | Serialize narrowed proposals and receive them against a trusted live parent registry. |
| [Native correlation and Lens](#lens) | Export correlated decisions and attach them to exact Lens run/trace/span identities. |
| [Chaos recovery supervision](#chaos) | Evaluate recovery proposals linked to native fault events without executing the tool. |
| [AIOS audit projections](#aios) | Project public native audit identifiers and outcomes into a draft operational artifact. |
| [Narration and CLI](#narration) | Display standalone or measured runtime status and use six CLI commands. |
| [Supervision benchmarks and acceptance](#validation) | Reproduce synthetic paired dispatch measurements with explicit validation limits. |
| [Configuration and limitations](#settings) | Configure roles, optional integrations and trusted-host boundaries. |

## Quickstart

Requires Python 3.10 or newer in an activated virtual environment:

```bash
python -m pip install agentic-sidecar
```

Save this complete file as `sidecar_quickstart.py`. Its delete tool only appends to a list. The LangGraph adapter accepts plain callables here without requiring a running graph:

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

```bash
python sidecar_quickstart.py
```

Expect a BLOCK verdict, blocked governed dispatch and zero calls. When connecting real tools, verify both the decision and actual execution evidence. Keep raw tools and runtime configuration in the trusted host.

## Usage

Examples under `examples/` or `scripts/` assume a source checkout and run from its root. Other named files, endpoints and IDs are inputs supplied by your host. See the linked topic before using a provider, SDK or operator fragment.

<span id="gate"></span>

### Decision Gate and enforcement

Sidecar supports `ALLOW`, `WARN`, `BLOCK`, `CHALLENGE`, `REPLAN`, `PAUSE` and `ESCALATE`. `evaluate()` returns a decision; it does not execute a tool. Governed adapters dispatch ALLOW/WARN, block BLOCK, return replanning/challenge outcomes to the loop, and resolve or suspend approval outcomes. Observe evaluates but calls through.

Custom loops must evaluate, enforce, reserve dispatch with `runtime.dispatch(...)`, execute only after admission, and call `runtime.complete(...)` on success or failure. Prefer a supported adapter for this lifecycle. See [outcome and approval semantics](governance.md) and [dispatch freshness](v0.9.md#task-authority-and-delegation).

<span id="policy-risk"></span>

### Policy and risk rules

`PolicyAdvisor` evaluates ordered tool-name globs; first match wins, with an allow default unless configured otherwise. `RiskEvaluator` classifies tool/argument rules as LOW/MEDIUM/HIGH, and `risk_block_threshold` determines intervention. Load YAML or mapping definitions, or construct `PolicyRule`/`RiskRule` objects. The quickstart demonstrates a deny rule. See [rule fields, comparison operators and configuration](configuration.md).

<span id="intent"></span>

### Intent constraints

Create an `IntentEnvelope` containing the goal, requester, constraints and optional expiry. `ConstraintBinding` maps each enforced constraint to a tool argument; `IntentGuardian` checks the bound values. Supply it as `intent=` and enable the `intent_guardian` role. A step that breaks a bound constraint (intent drift, such as a refund above the authorized amount) is blocked even when the tool itself is permitted. Goals alone are not deterministic constraints, and an authority dictionary requires explicit authority bindings to enforce grants. See [constraint setup](configuration.md) and [authority semantics](v0.9.md).

<span id="budget"></span>

### Budget accounting

```python
from agentic_sidecar import BudgetGuardian, DecisionContext, Sidecar

budget = BudgetGuardian(max_cost=5.0, max_tokens=10000)
sidecar = Sidecar(on_sidecar_failure="fail_closed", roles=["budget"], budget=budget)
budget.record_invocation(cost=5.0, tokens=1200)
assert sidecar.evaluate(DecisionContext(tool_name="read_order")).status == "PAUSE"
```

Record actual external usage explicitly, and call `reset()` for the next task. Judge usage reaches a configured task budget once; other framework/tool usage is not inferred. Govern pauses dispatch until resolved. See [budget and Judge accounting](governance.md).

<span id="plan-review"></span>

### Plan review and Critic

```python
from agentic_sidecar import PlanEvaluator, Sidecar

sidecar = Sidecar(on_sidecar_failure="fail_closed", roles=["planner"], planner=PlanEvaluator())
decision = sidecar.evaluate_plan(
    [{"tool_name": "read_charge"}, {"tool_name": "issue_refund"}],
    goal="Explain the disputed charge",
)
assert decision.status == "REPLAN"
```

Full-plan review runs enabled deterministic gates on each supplied step. `CriticEvaluator` challenges selected unsafe actions and assumptions; verification metadata must be step-scoped. These are scoped heuristics, not general semantic reasoning. See [plan review](governance.md#full-plan-review), [Critic behavior](features.md) and [migration details](v0.9.md#review-fixes-and-migration).

<span id="judges"></span>

### Offline and live judges

Configure `JudgeEvaluator(MockJudge(...))` for explicit offline responses. `OpenAIJudge` and `AnthropicJudge` use optional provider SDKs and never silently substitute mocks. Install `[openai]` or `[anthropic]`, supply credentials/model, and enable the `judge` role.

Configure timeout, cost limit and caller-supplied token rates when accounting is required. Provider errors follow the explicit Sidecar failure policy; limits are not a hard cancellation mechanism for arbitrary blocking code. See [provider setup and smoke commands](governance.md#optional-live-judge-providers) and [Judge limits](limitations.md).

<span id="approvals"></span>

### Human in the loop: approvals and escalation

```python
from agentic_sidecar import Sidecar
from agentic_sidecar.cli.approval import CLIApprovalHandler

sidecar = Sidecar(
    on_sidecar_failure="fail_closed", mode="govern",
    escalation_handler=CLIApprovalHandler(),
)
```

Use returned governed tools. PAUSE/ESCALATE can request `approve_once`, `reject`, `modify_intent`, `ask_agent_to_replan` or `stop_agent`. BLOCK is never offered for approval. Responses bind to the decision ID; approval authorizes one unchanged invocation. Missing handlers suspend. `TaskRuntime` supports connected operator approvals; `on_escalation_required` supports notification callbacks. See [approval transitions and malformed-response handling](governance.md#local-approval-flow).

<span id="hooks"></span>

### Custom hooks and failure policies

`before_tool_call` installs a custom decision hook; `on_sidecar_failure` must explicitly be `fail_open` or `fail_closed`. Govern/fail_closed blocks when evaluation fails; fail_open can permit that failure path. Hooks receive copied proposals and cannot rewrite the enforced tool/arguments. Mandatory scope and authority checks still apply before optional evaluation. See [hook API](api-reference.md), [mandatory guardrails](scoped-supervision.md) and [failure limits](limitations.md).

<span id="adapters"></span>

### Framework and MCP adapters

Start with `adapters.callable.attach()` or `adapters.langgraph.attach()` for plain typed sync/async functions. The optional framework adapters convert the returned supervised boundary to each SDK's tool object:

| Module | Install extra / surface |
| --- | --- |
| `adapters.langgraph` | `[langgraph]` for real graphs; wrapped callables |
| `adapters.autogen` | `[autogen]`; AutoGen Core FunctionTool |
| `adapters.crewai` | `[crewai]`; CrewAI Tool |
| `adapters.openai_agents` | `[openai-agents]`; OpenAI Agents FunctionTool |
| `adapters.google_adk` | `[google-adk]`; ADK FunctionTool |
| `adapters.mcp` | `[mcp]`; async wrappers for allowlisted tools on an initialized ClientSession |

Most adapters use `attach(sidecar, tools)`; MCP uses `attach(sidecar, session, tool_names)`. Pass only the returned objects to the agent. Prebuilt SDK tools, automatic handoffs and arbitrary nested/raw calls are not automatically protected. See [SDK versions, Python requirements and examples](integrations.md#framework-adapters) and [MCP gateway boundaries](integrations.md#mcp).

<span id="runtime"></span>

### Task runtime and execution lifecycle

`TaskRuntime` records proposed, evaluated, dispatched, completed and failed actions. Supply `runtime=` to Sidecar and use that runtime as `escalation_handler` for connected approvals. Inspect `runtime.snapshot()` and `runtime.journal.export(after=0)`. The guarded quickstart creates runtime evidence automatically. Evaluating a proposal alone is not evidence that it executed. See [runtime construction and lifecycle](live-operations.md).

<span id="operators"></span>

### Operator server and Control Room

Host a configured task inside `OperatorServer(runtime, token=..., actor=...)`, using a locally generated secret of at least 32 characters. The server exposes a task-specific loopback endpoint and Control Room. Keep the server context alive for the task's lifetime, then connect an operator terminal:

```bash
export SIDECAR_ENDPOINT=http://127.0.0.1:PORT/tasks/TASK_ID
# Set SIDECAR_OPERATOR_TOKEN securely in this terminal as well.
agentic-sidecar status --json
agentic-sidecar control pause
agentic-sidecar control resume
```

The Control Room and `POST /control` accept `pause`, `resume`, `replan`, `stop` and `restart`. Pause and replan hold new dispatches until resume; restart is allowed only after a clean stop. Replace PORT/TASK_ID with the running server's values. Status/events/control/approval/intent API routes require the operator token. See [complete server setup, protocol and Control Room](live-operations.md#connect-a-real-task).

<span id="stop"></span>

### Emergency stop, cancellation and revocation

```bash
agentic-sidecar control stop
```

Stop is the emergency stop. It latches before audit writes or callbacks, independently of evaluation mode and failure policy, blocks queued dispatch and invalidates old decisions. Already-dispatched sync work may finish; owned async tools receive cooperative cancellation requests. Configure named `TaskRuntime(revokers=...)` callbacks for host-owned credentials and delegated access; acknowledgement requires each issuer to return exactly `True` after revocation. A broken audit sink cannot prevent revocation, and a restored runtime comes back stopped. Restart does not renew credentials or task authority. See [stop receipts, partial failures and restart rules](live-operations.md#stop-cancellation-and-access-revocation) and the [emergency stop guide](control-tower-integration.md#emergency-stop).

<span id="control-tower"></span>

### Control Tower fleet operations

AgenticOps Control Tower reads explicitly linked Sidecar decisions into its inventory, alerts and incident console. For a fleet-wide stop, the trusted host installs a `SidecarContainmentAdapter(runtime)` per deployment; a writer previews a `runtime.stop` bulk action, a separate approver approves it, and each target reports acknowledged, incomplete, failed, unsupported or timed_out. The runtime needs an issuer-backed `mcp` revoker. Sidecar keeps dispatch blocking and pre-action decisions; Tower coordinates targeting, approvals, runbooks and incidents. See [Control Tower integration](control-tower-integration.md).

<span id="audit"></span>

### Audit journal and restoration

`EventJournal(task_id, path)` can persist JSONL events with sequence, event identity, timestamp, previous hash and digest. `verify_events(events, task_id=...)` checks a complete native chain before replay/export. Reopen `EventJournal(task_id, path)` and pass it to `TaskRuntime` to restore supported snapshots in a stopped state; approvals are not silently reauthorized. This is distinct from serializing a caller-managed `AuditRecord`.

Protect native records because they may contain arguments and reasons. Hash chaining detects alteration relative to the supplied chain; an external trusted anchor is needed to resist a full malicious rewrite. See [journal formats, restoration and replay](live-operations.md#audit-snapshots-and-restoration).

<span id="scopes"></span>

### Shared/exclusive supervision

Configure `ScopedSystem` with declared agents, a shared `ScopeLayer`, and optional exclusive layers. `ContextSpec` carries goal/values, while `GuardrailSpec` carries explicit policies/constraint bindings. `bind(agent_id, on_sidecar_failure=...)` creates a separate supervised agent boundary.

Shared and exclusive context conflicts fail validation; every applicable guardrail must pass. Exclusive allows cannot weaken shared denies. Context delivery is explicit through `context()`/`deliver()`, and private text is not automatically enforcement policy or evaluator input. See [composition, mandatory checks and trusted identities](scoped-supervision.md).

<span id="privacy"></span>

### Context privacy and lifecycle

```python
from agentic_sidecar import ContextSpec, ScopedSystem, ScopeLayer

system = ScopedSystem(
    system_id="support", task_id="ticket-42", agents=["refund"],
    exclusive={"refund": ScopeLayer(
        context=ContextSpec(values={"reference": "demo-1"}, readers={"auditor"}),
    )},
)
refund = system.bind("refund", on_sidecar_failure="fail_closed")
assert refund.context(reader="auditor")["values"]["reference"] == "demo-1"
refund.update_context({"reference": "demo-2"}, actor="refund")
refund.revoke_context(actor="refund")
```

Readers/actors come from the authenticated host. Owners update/revoke context; expiry/revocation blocks future reads but cannot retract delivered copies. Combined layers intersect extra readers and use the earliest expiry. See [reader authorization, delivery and lifecycle](v0.9.md#context-privacy-and-readers).

<span id="evidence"></span>

### Redacted evidence and operator readers

`BoundAgent.evidence()` returns an allowlisted summary of identity, verdict/risk, counts and lifecycle state, excluding private arguments, goals, reasons, plans and pending approvals. `OperatorServer(reader_tokens={secret: "auditor"})` permits redacted GET `/status` only; those tokens cannot control, approve or read raw events. A summary cannot replace a native decision or verifiable journal. See [reader token and evidence contracts](v0.9.md#context-privacy-and-readers).

<span id="authority"></span>

### Task authority and delegation

Configure an `IntentGuardian` with `AuthorityBinding` entries, trusted task/agent IDs and explicit grants. `delegate(agent_id=..., authority=...)` creates a child whose permissions may only narrow. Missing/denied grants block; expiry and ancestor revocation invalidate future dispatch reservations. Bindings and inherited constraints remain intact.

Run the offline synthetic-tool example from the checkout:

```bash
uv run python examples/v0_9_authority_delegation.py
```

The parent registry and raw tools stay host-owned. Revocation does not undo already reserved execution. Observe records authority decisions without enforcing them; use the governed dispatch boundary. See [grants, narrowing, revocation and restart](v0.9.md#task-authority-and-delegation).

<span id="contracts"></span>

### Native interchange contracts

```python
from agentic_sidecar import Decision
from agentic_sidecar.contracts import DecisionContract, contract_schema

native = Decision(status="BLOCK", risk=None, reason="local example")
wire = DecisionContract(schema_version="sidecar.decision/1", decision=native).model_dump_json()
restored = DecisionContract.model_validate_json(wire)
assert restored.decision.decision_id == native.decision_id
assert contract_schema("decision")["properties"]["schema_version"]["const"] == "sidecar.decision/1"
```

The five families are intent, decision, audit, scope and transfer. Top-level wrappers require exact markers and reject unknown fields. `ScopeContract.build()` validates composition; `export_audit()` validates a native record including timezone-aware timestamps. Native contracts are candidate surfaces, independent of package and AIOS versions. See [schema policy and migration](v0.10.md#schema-and-migration-policy).

<span id="transfer"></span>

### Cross-agent intent transfer

`IntentTransfer.propose(parent, agent_id=..., authority=...)` creates a narrowed serialized proposal. After transport, the trusted receiver validates it and calls `.receive(parent, agent_id=...)` against the live parent registry. Imported proposals cannot invent bindings, widen authority, extend expiry or bypass ancestor revocation.

```bash
uv run python examples/v0_10_contracts.py
```

A proposal is not a signed credential, approval or resumable task. Disconnected registry replication and one-time replay prevention are host responsibilities. See [cross-instance receive checks and limitations](v0.10.md#cross-instance-and-cross-agent-propagation).

<span id="lens"></span>

### Native correlation and Lens

`Correlation(run_id=..., trace_id=..., span_id=...)` and `export_decisions()` emit `sidecar.correlation/1` projections after verifying the native journal. The host supplies exact IDs. Install `[agenticlens]` to use `integrations.agenticlens.attach_decisions(sidecar, run, span_id=...)` for Lens readback.

BLOCK/ESCALATE remain supervision outcomes rather than failed deployments. Projections may retain sensitive reasons and are not independent execution evidence. See [correlation fields, Lens identity checks and access boundaries](integrations.md#versioned-native-decision-evidence).

<span id="chaos"></span>

### Chaos recovery supervision

Install `[agentic-chaos]` for optional resilience experiments. `integrations.agentic_chaos.evaluate_recovery(sidecar, event, tool_name=..., arguments=...)` evaluates/enforces a recovery proposal linked to a native Chaos event ID; it does not execute the tool. Actual execution still passes through a supervised adapter. See [Chaos/Evals ownership and examples](integrations.md#agentic-chaos-and-evals).

<span id="aios"></span>

### AIOS audit projections

`integrations.aios.export_audit_event(record, target=..., created_at=...)` projects a native `AuditRecord` into a `0.8-draft` operational audit artifact. The host supplies public target references and an aware recording timestamp. The projection withholds rationale/context, marks the actor unknown, and maps BLOCK to denied while other outcomes remain requested. Permission to proceed is not proof of execution. See [AIOS operational projection](aios-0.8-operational-artifacts.md) and [export API](api-reference.md#aios-operational-audit-export).

<span id="narration"></span>

### Narration and CLI

`StatusNarrator` records supplied tool narratives and formats task status independently of a connected runtime:

```bash
agentic-sidecar version
agentic-sidecar status --json
```

`demo` illustrates simulated narrator calls; `approval-demo` prompts without executing tools. `status --endpoint` reads measured task events; `--follow --json` is formatted display, not JSONL. `control` and `approve` operate on authenticated live tasks. See the [complete six-command inventory and flags](cli-reference.md).

<span id="validation"></span>

### Supervision benchmarks and acceptance

```bash
uv run python scripts/supervision_benchmark.py --output /tmp/sidecar-evidence.json
```

The fixed 24-run synthetic benchmark compares actual wrapped dispatches with and without supervision across unsafe and clean controls. Outage controls expose fail_closed availability costs. Optional `--ecosystem` validation uses Chaos and Evals through the `[validation]` extra. Synthetic zero token/cost values do not establish live-provider benefit, statistical confidence or economic savings. See [reproducible evidence and recorded limits](v0.9.md#reproducible-evidence) and [coordinated acceptance](coordinated-v1-readiness.md).

<span id="settings"></span>

## Configuration and limitations

Choose `on_sidecar_failure` explicitly, choose Observe/Govern, supply modules and enable their roles. Defaults enable policy/risk; an empty policy allows actions. Supported optional roles include intent_guardian, budget, planner, critic and judge. Mandatory scope/authority checks retain their own semantics. See [constructor arguments, rules, bindings and module setup](configuration.md).

Core installation has no sibling dependency. Framework/provider integrations use their corresponding extras; `[agenticlens]`, `[agentic-chaos]` and `[validation]` add ecosystem dependencies. Semantica is reserved and has no implemented export. Protect raw tools, credentials, identity and runtime configuration at the host boundary. Wrappers do not sandbox hostile Python or automatically govern arbitrary memory, prompts, outputs or nested calls. See [limitations](limitations.md), [scoped boundaries](scoped-supervision.md) and [contract maturity](v0.10.md).

## Troubleshooting

If a denied tool still runs, check Observe/Govern, the returned tool object and actual dispatch evidence. If approval stalls, inspect the pending decision ID and handler/runtime. If an old ALLOW stops working, check intent epochs, consumed approvals, stop state and authority expiry/revocation. See [troubleshooting](troubleshooting.md).

## Reference

- [API reference](api-reference.md) and [CLI reference](cli-reference.md).
- [AI Reference (robust)](https://deepagentlabs.io/agentic-sidecar/docs/llms-full.md) and [capability/source index](ai-reference-index.md).
- [Source manifest and checksums](ai-docs-manifest.json).
