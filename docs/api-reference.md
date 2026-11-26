# API Reference

Python API for `agentic-sidecar` **1.0.x** (current release 1.0.4). Imports below identify the supported
module for each symbol; intent and policy/risk types live in their subpackages.
Native contract schemas keep their own candidate versions, independent of the package version.

| Area | Symbols |
| --- | --- |
| Decisions | [`Sidecar`](#sidecar), [`Decision`](#decision), [`DecisionContext`](#decisioncontext), [`SidecarBlockedError`](#sidecarblockederror) |
| Guardrails | [`PolicyAdvisor`](#policyadvisor), [`RiskEvaluator`](#riskevaluator), [`BudgetGuardian`](#budgetguardian), [`IntentGuardian`](#intentguardian-intentenvelope-constraintbinding) |
| Human in the loop | [`EscalationHandler`, `ApprovalAction`](#escalationhandler-escalationrequest-approvalresponse-approvalaction), [`CLIApprovalHandler`](#cliapprovalhandler) |
| Live control and emergency stop | [`TaskRuntime`, `OperatorServer`, `EventJournal`](#runtime-operations) |
| Adapters | [LangGraph](#attach-langgraph-adapter), [other frameworks and MCP](#other-framework-adapters) |
| Scopes, authority, contracts | [Scoped supervision](#scoped-supervision-and-native-export-08), [authority and privacy](#authority-privacy-and-transfer-lifecycle) |
| Ecosystem | [Lens, Chaos and Control Tower](#ecosystem-integrations), [AIOS export](#aios-operational-audit-export) |

```python
import agentic_sidecar
```

---

## `Sidecar`

```python
from agentic_sidecar import Sidecar
```

The central class. Owns the Decision Gate and all evaluation module configuration.

### `__init__`

All arguments are keyword-only. See [Configuration](configuration.md) for rule formats and examples.

| Parameter | Default | Purpose |
| --- | --- | --- |
| `on_sidecar_failure` | required | `"fail_open"` or `"fail_closed"` when evaluation itself fails |
| `mode` | `"observe"` | `"observe"` records verdicts; `"govern"` enforces them |
| `policy` / `risk` | `None` | `PolicyAdvisor` / `RiskEvaluator` rule sets |
| `intent` | `None` | `IntentGuardian` with the task's `IntentEnvelope` and bindings |
| `budget` | `None` | `BudgetGuardian` cost/token ceilings |
| `planner` / `critic` / `judge` | `None` | Optional evaluators |
| `roles` | policy, risk | Which modules run, e.g. `["policy", "risk", "intent_guardian", "budget"]` |
| `risk_block_threshold` | `"HIGH"` | Risk level at which the gate intervenes |
| `escalation_handler` | `None` | Resolves PAUSE/ESCALATE (human in the loop); missing handlers suspend |
| `runtime` | `None` | `TaskRuntime` for live status, controls, emergency stop and audit |
| `mandatory_checks` | `()` | Trusted host checks that run before custom hooks |
| `context_metadata` / `mandatory_configuration` | `None` | Trusted metadata and configuration recorded in audit fingerprints |

### `evaluate(context: DecisionContext) -> Decision`

Evaluate one proposed tool call. Injects intent/history into the caller's context,
computes a verdict, and stores a deep context copy in `sidecar.decisions`. Errors
from injection, dispatch, validation or recording resolve via `on_sidecar_failure`. This method does
not dispatch tools or raise merely because a verdict is BLOCK. See
[Failure handling](architecture.md#failure-configuration) for scope.

```python
from agentic_sidecar import DecisionContext

context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 250.0})
decision = sidecar.evaluate(context)
print(decision.status)  # "ALLOW"
```

### `set_intent(intent: IntentGuardian | None) -> None`

Set or clear the active `IntentGuardian`. Raises `ValueError` if `intent` is provided but `"intent_guardian"` is not in `sidecar.roles`.

### `before_tool_call(func: Callable) -> Callable`

Decorator. Register a custom decision hook that replaces the entire built-in Decision Gate pipeline.

```python
@sidecar.before_tool_call
def my_hook(context: DecisionContext) -> Decision:
    ...
```

### `on_escalation_required(func: Callable) -> Callable`

Decorator. Register an approval hook invoked by `enforce()` or the Govern
adapter for PAUSE/ESCALATE. Responses must match the decision ID and use an
ApprovalAction. See [Governance](governance.md) for resolution semantics.

```python
@sidecar.on_escalation_required
def handle_escalation(request: EscalationRequest) -> ApprovalResponse:
    ...
```

### `sidecar.decisions: list[tuple[DecisionContext, Decision]]`

In-memory log of evaluated context/decision pairs. Contexts and nested data
are deep-copied when recorded but remain mutable; caller-created `AuditRecord` objects are a separate export API.

### `sidecar.mode: str`

Current mode — `"observe"` or `"govern"`.

---

## `Decision`

```python
from agentic_sidecar import Decision, DecisionStatus, RiskLevel
```

Frozen Pydantic result of a Decision Gate evaluation; nested dictionary values
are not deeply immutable.

| Field | Type | Description |
|---|---|---|
| `decision_id` | `str` | Generated UUID; approval correlation ID |
| `status` | `DecisionStatus` | ALLOW / WARN / BLOCK / CHALLENGE / REPLAN / PAUSE / ESCALATE |
| `risk` | `RiskLevel` \| `None` | LOW / MEDIUM / HIGH; None when no classification was produced, including early policy returns and failure fallback |
| `reason` | `str` | Human-readable verdict explanation |
| `decision_point` | `str` \| `None` | Boundary name, commonly `"tool_call"` for built-in verdicts; optional for hooks/fallback |
| `trigger_details` | `dict` \| `None` | Optional tool name and argument snapshot |
| `escalation_required` | `bool` | Explicit escalation marker (default False); built-in budget/Judge PAUSE sets it |
| `causal_link` | `str` \| `None` | Optional caller-supplied causal identifier |

---

## `DecisionContext`

```python
from agentic_sidecar import DecisionContext
```

The input to `sidecar.evaluate()`. Build one per tool call.

| Field | Type | Description |
|---|---|---|
| `tool_name` | `str` | Name of the proposed tool |
| `tool_args` | `dict[str, Any]` | Arguments for the tool call |
| `intent` | `IntentSnapshot` \| `None` | Injected by `evaluate()` — do not set manually |
| `history` | `list[HistoryEntry]` | Injected by `evaluate()` — do not set manually |
| `metadata` | `dict[str, Any]` | Caller metadata forwarded to evaluators |
| `boundary` | `"tool_call"` / `"plan"` | Evaluation boundary |
| `goal` | `str` | Goal when no active envelope exists |
| `plan` | `list[dict]` | Explicit plan steps |

---

## `SidecarBlockedError`

```python
from agentic_sidecar import SidecarBlockedError
```

Raised by the LangGraph callable wrapper in Govern mode when `decision.status == "BLOCK"`.

```python
try:
    (my_tool_wrapped,) = attach(sidecar, [my_tool])
    my_tool_wrapped()
except SidecarBlockedError as exc:
    print(exc.decision.reason)
    print(exc.context.tool_name)
```

| Attribute | Type | Description |
|---|---|---|
| `decision` | `Decision` | The blocking decision |
| `context` | `DecisionContext` | The context that triggered the block |

---

## `PolicyAdvisor`

```python
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule, PolicyResult
```

See [Configuration — PolicyAdvisor](configuration.md#policyadvisor-configuration) for full details.

### `PolicyAdvisor.evaluate(context: DecisionContext) -> PolicyResult`

Runs the rule set. Returns the first matching rule's result, or the default.

### `PolicyAdvisor.from_yaml(path) -> PolicyAdvisor` · `PolicyAdvisor.from_mapping(data) -> PolicyAdvisor`

Class methods to load rules from a YAML file or parsed dict.

---

## `RiskEvaluator`

```python
from agentic_sidecar.gate.risk import RiskEvaluator, RiskRule, RiskResult
```

### `RiskEvaluator.evaluate(context: DecisionContext) -> RiskResult`

Runs the rule set. Returns the first matching rule's risk classification, or the default.

---

## `BudgetGuardian`

```python
from agentic_sidecar.gate import BudgetGuardian, BudgetResult
```

### `BudgetGuardian.record_invocation(cost: float, tokens: int | None = None) -> None`

Accumulate cost and token usage.

### `BudgetGuardian.evaluate() -> BudgetResult`

Check current totals against ceilings. Returns `BudgetResult(exceeded, remaining_cost, remaining_tokens, reason)`.

### `BudgetGuardian.is_at_capacity() -> bool`

Quick check — returns `True` if already at or over budget.

### `BudgetGuardian.reset() -> None`

Reset cost and token counters to zero (for a new task).

---

## `IntentGuardian` / `IntentEnvelope` / `ConstraintBinding`

```python
from agentic_sidecar.intent import (
    IntentEnvelope, IntentGuardian, ConstraintBinding, Requester
)
```

See [Configuration — IntentEnvelope and IntentGuardian](configuration.md#intentenvelope-and-intentguardian-configuration).

### `IntentEnvelope.is_expired(now=None) -> bool`

Returns `True` if `expires` is set and the envelope has expired.

### `IntentEnvelope.to_snapshot() -> IntentSnapshot`

Returns a lightweight `IntentSnapshot(goal, constraints)` — the form injected into `DecisionContext`.

---

## `EscalationHandler` / `EscalationRequest` / `ApprovalResponse` / `ApprovalAction`

```python
from agentic_sidecar.gate import (
    EscalationHandler, EscalationRequest, ApprovalResponse, ApprovalAction
)
```

**`ApprovalAction` values:** `APPROVE_ONCE`, `REJECT`, `MODIFY_INTENT`, `ASK_AGENT_TO_REPLAN`, `STOP_AGENT`

This is the human-in-the-loop surface. In Govern mode, PAUSE and ESCALATE call the configured handler (a `CLIApprovalHandler`, a connected `TaskRuntime`, or your own `EscalationHandler`). The response binds to the decision ID; `APPROVE_ONCE` authorizes one unchanged invocation, `MODIFY_INTENT` reevaluates against a complete new envelope, and `STOP_AGENT` stops the whole task. BLOCK is never offered for approval. See [approval flow](governance.md#local-approval-flow).

---

## `StatusNarrator` / `StatusNarrative` / `ToolCallNarrative`

```python
from agentic_sidecar.status import StatusNarrator, StatusNarrative, ToolCallNarrative
```

### `StatusNarrator.set_objective(objective: str) -> None`

Record the top-level task objective.

### `StatusNarrator.record_tool_call(tool_name, arguments, decision=None, risk_level=None, intent_compliant=True) -> ToolCallNarrative`

Record a tool invocation and generate its narrative.

### `StatusNarrator.get_status(...) -> StatusNarrative`

Build a snapshot of application-supplied records and reporting state. This
does not fetch data from a running agent. `steps_completed` counts recorded calls.

### `StatusNarrator.get_narrative() -> str`

Return the full execution narrative as a human-readable string.

### `StatusNarrator.pause(reason: str) -> None` / `resume() -> None`

Record narrator pause/resume state; application code owns actual execution.

---

## `attach` (LangGraph adapter)

```python
from agentic_sidecar.adapters.langgraph import attach
```

### `attach(sidecar: Sidecar, tools: Sequence[F]) -> list[F]`

Wraps each tool in `tools` so calling it first runs `sidecar.evaluate()`. Returns a new list in the same order. Does not mutate the input list or original tool callables.

```python
tools = attach(sidecar, [read_order, issue_refund, delete_customer])
agent = create_react_agent(model, tools=tools)
```

## Other framework adapters

Each adapter runs the same Decision Gate and runtime lifecycle and returns the SDK's own tool type. Pass only the returned objects to the agent.

| Import | Signature | Returns | Extra |
| --- | --- | --- | --- |
| `agentic_sidecar.adapters.callable` | `attach(sidecar, tools)` | Wrapped sync/async callables | none |
| `agentic_sidecar.adapters.autogen` | `attach(sidecar, tools)` | AutoGen Core `FunctionTool` | `[autogen]` |
| `agentic_sidecar.adapters.crewai` | `attach(sidecar, tools)` | CrewAI tools | `[crewai]` |
| `agentic_sidecar.adapters.openai_agents` | `attach(sidecar, tools)` | OpenAI Agents `FunctionTool` | `[openai-agents]` |
| `agentic_sidecar.adapters.google_adk` | `attach(sidecar, tools)` | Google ADK `FunctionTool` | `[google-adk]` |
| `agentic_sidecar.adapters.mcp` | `attach(sidecar, session, tool_names)` | Async wrappers for allowlisted tools on an initialized `ClientSession` | `[mcp]` |

Prebuilt SDK tools, automatic handoffs and raw nested calls are not protected automatically. See [integrations](integrations.md#framework-adapters).

---

## Evaluators

```python
from agentic_sidecar import PlanEvaluator, CriticEvaluator, JudgeEvaluator
from agentic_sidecar.evaluators import EvaluatorResult, JudgeProvider
```

### `PlanEvaluator.evaluate(context: dict) -> EvaluatorResult`

Accepts plan dictionaries/PlanStep objects, goal, intent, constraints and
constraint_bindings. Selected tool/goal patterns and opposing tool pairs yield
REPLAN. Supplied bindings check plan arguments deterministically. min_confidence
filters the fixed 0.9 intervention score. No automatic natural-language bindings.

### `CriticEvaluator.evaluate(context: dict) -> EvaluatorResult`

Selected risky tool patterns, assumptions and permitted-action contradictions
yield CHALLENGE. Metadata authorized/eligibility_verified/backup_verified flags
can satisfy corresponding tool-call checks. threshold filters the fixed 0.85
score. These assertions are caller-supplied; full-plan checks are conservative.

### `JudgeEvaluator(provider, enabled=True, cost_limit=0.50, timeout_ms=5000, budget=None)`

Sync/async return validated EvaluatorResult with usage, provider, confidence and
latency. Errors propagate to Sidecar's failure policy. Returned usage is charged
once, including valid usage attached to an invalid verdict. cost_limit is a
post-response ceiling; exceeding it returns PAUSE. get_cost/reset_cost manage
tracked cost. See [Limitations](limitations.md) for late sync responses and async
cancellation. Choose MockJudge for offline examples; live OpenAIJudge and
AnthropicJudge require an explicit model, optional SDK and credentials.

### `JudgeProvider`

Implement evaluate(question, context) returning decision, reasoning, confidence
and usage with cost and total_tokens. Supported decisions are all seven statuses;
confidence must be finite in [0, 1], cost finite/nonnegative and tokens a
nonnegative integer. Override validate/evaluate_async as appropriate.
Without known cost, only cost_limit=None with no task budget is supported.

### `Sidecar.evaluate_plan(plan, *, goal="", metadata=None) -> Decision`

Requires a nonempty list of dictionaries with tool_name and optional arguments.
Checks policy/risk/intent per step, then enabled evaluators with full context.
Computes a verdict without executing steps. An active intent supplies the goal.

### `Sidecar.enforce(context, decision) -> Decision`

Adapter dispatch boundary: Observe returns unchanged; Govern resolves
PAUSE/ESCALATE and only returns ALLOW/WARN. BLOCK raises SidecarBlockedError;
other unresolved statuses raise SidecarSuspendedError. Both expose decision and
context. Applications must call enforce before dispatch in custom loops.

### `CLIApprovalHandler`

Import from agentic_sidecar.cli.approval and pass as escalation_handler.
Provides a local prompt for approve-once/reject/modify-intent/replan/stop.
The `approval-demo` CLI command tries the prompt without executing tools.

## Provenance exports

```python
from agentic_sidecar import AuditRecord, CausalLink, DecisionRationale, DecisionTrigger
```

Construct a caller-managed `AuditRecord` with decision ID, timestamp, outcome,
trigger, rationale, and optional causal/execution context. `to_dict()` serializes
the record, including ISO timestamp and structured causal links. TaskRuntime
automatically generates immutable event snapshots; EventJournal supplies
optional durable JSONL persistence. See [Live operations](live-operations.md).

## Top-level `__version__`

```python
from agentic_sidecar import __version__
print(__version__)  # the installed package version, e.g. "1.0.4"
```

## Runtime operations

Public exports: `TaskRuntime`, `RuntimeEvent`, `EventJournal`, `OperatorServer`
(`verify_events` is imported from `agentic_sidecar.operations.events`).
Supply `runtime=TaskRuntime(...)` to Sidecar and `escalation_handler=runtime`
for remote approvals.

```python
from agentic_sidecar import EventJournal, OperatorServer, TaskRuntime
```

| Symbol | Signature | Purpose |
| --- | --- | --- |
| `TaskRuntime` | `TaskRuntime(task_id=None, *, journal=None, approval_timeout=300, revokers=None)` | Task lifecycle, approvals, controls and stop latch |
| `TaskRuntime.control` | `control(action, actor) -> dict` | `action` is `pause`, `resume`, `replan`, `stop` or `restart`; returns a receipt |
| `TaskRuntime.approve` | `approve(response, actor) -> None` | Resolve a pending human approval |
| `TaskRuntime.modify_intent` | `modify_intent(envelope, actor) -> None` | Replace the task intent and invalidate earlier verdicts |
| `TaskRuntime.snapshot` | `snapshot() -> dict` | Objective, plan, findings, budget, actions, pending approvals, running calls |
| `TaskRuntime.stopped` / `epoch` | properties | Stop latch state and current decision epoch |
| `TaskRuntime.dispatch` / `complete` | `dispatch(context, decision, *, cancel=None) -> str`, `complete(invocation_id, error=None)` | Custom-loop admission and completion |
| `OperatorServer` | `OperatorServer(runtime, *, token, actor, port=0, reader_tokens=None)` | Loopback HTTP API and Control Room; use as a context manager, read `.url` |
| `EventJournal` | `EventJournal(task_id, path=None)` | Hash-chained events, optional durable JSONL; `export(after=0)` |
| `operations.events.verify_events` | `verify_events(events, task_id=...)` | Check a complete native chain before replay/export |

**Emergency stop.** `runtime.control("stop", actor)` latches before writing the
stop event or calling revokers, blocks all further dispatch, invalidates earlier
decisions, requests cancellation of owned async calls and calls each named
revoker (`revokers={"mcp": callback}`; each must return exactly `True` after
revocation). The receipt contains `action`, `actor`, `epoch`, `effective_at`,
`running`, `cancellations`, `revocations` and `access_revocation`
(`acknowledged`, `partial_failure` or `not_configured`), plus `audit_error` if
the stop event could not be persisted. `restart` requires a stopped, idle task
with successful revocations. See [emergency stop](control-tower-integration.md#emergency-stop).
 Inspect `sidecar.runtime.snapshot()` and
`sidecar.runtime.journal.export(after=0)`. DecisionContext accepts
`parent_decision_id` and `parent_plan_step` for supplied plan causality.
See [Live operations](live-operations.md) for the full lifecycle and HTTP surface.

## Scoped supervision and native export (0.8)

Public exports: `ScopedSystem`, `ScopeLayer`, `ContextSpec`, `GuardrailSpec`,
`BoundAgent`. `ScopedSystem.bind(agent_id, on_sidecar_failure=..., mode=...)`
returns a separate Sidecar and explicit `context()` / `deliver(receiver)` payload.
See [scoped supervision](scoped-supervision.md) for configuration and limits.
`Sidecar` also accepts trusted `mandatory_checks`, `mandatory_configuration` and
`context_metadata`; checks run before custom hooks and the configuration is
included in audit policy fingerprints.

`integrations.correlation.Correlation` and `export_decisions()` provide native
versioned projections. See [integration contracts](integrations.md).

See [v0.9 authority, privacy and migration](v0.9.md) for the current lifecycle APIs.


## Capability modules

| Module | Workflow and detailed contract |
| --- | --- |
| `agentic_sidecar.core`, `gate`, `intent` | [Decision outcomes, policy, risk, budgets, intent constraints and failure policy](configuration.md) |
| `agentic_sidecar.evaluators` | [Plan/Critic review, Judge providers, time/cost accounting and approval flows](governance.md) |
| `agentic_sidecar.adapters` | [Sync/async callable, LangGraph, AutoGen, CrewAI, OpenAI Agents, Google ADK and MCP boundaries](integrations.md) |
| `agentic_sidecar.operations` | [TaskRuntime, EventJournal, OperatorServer, dispatch, controls and native events](live-operations.md) |
| `agentic_sidecar.scopes` | [Shared/exclusive composition and mandatory checks](scoped-supervision.md) |
| `agentic_sidecar.scopes.privacy` | [Reader authorization, context update/expiry/revocation and redacted summaries](v0.9.md#context-privacy-and-readers) |
| `agentic_sidecar.intent.authority` | [AuthorityBinding/AuthorityRegistry, narrowed delegation and live ancestor revocation](v0.9.md#task-authority-and-delegation) |
| `agentic_sidecar.contracts` | [Five native wrappers, schema accessors, scope import and validated intent transfer](v0.10.md) |
| `agentic_sidecar.integrations.correlation`, `integrations.agenticlens` | [Native projections and exact Lens run/trace/span readback](integrations.md) |
| `agentic_sidecar.integrations.agentic_chaos` | [Evaluate/enforce a fault-correlated recovery proposal without executing it](integrations.md#agentic-chaos-and-evals) |
| `agentic_sidecar.integrations.aios` | [AIOS operational audit projection](aios-0.8-operational-artifacts.md) |
| `agentic_sidecar.status`, `cli` | [Standalone/measured narration and six CLI commands](cli-reference.md) |

The [AI Reference (robust)](https://deepagentlabs.io/agentic-sidecar/docs/llms-full.md) includes declarations from every package module and all five native JSON Schemas. Consult the [capability index](ai-reference-index.md) before selecting a workflow. Internal helpers stay internal; extraction does not promote them to public APIs.

## Authority, privacy and transfer lifecycle

`IntentGuardian.delegate(...)` narrows authority using its live `AuthorityRegistry`, and `revoke()` invalidates descendants for future dispatch reservations. `IntentTransfer.propose(...)` serializes a narrowed proposal; `IntentTransfer.receive(parent, *, agent_id)` validates it against the trusted live parent. Receive requires the host-authenticated agent identity and the same live registry, not an imported self-asserted grant. See [propagation and replay limits](v0.10.md#cross-instance-and-cross-agent-propagation).

`BoundAgent.context(reader=...)` returns an authorized defensive copy; `update_context(values, *, actor)` and `revoke_context(*, actor)` require the owner. `evidence()` returns an allowlisted summary, not a native Decision or journal. `OperatorServer(reader_tokens=...)` binds reader credentials to redacted status only. See [privacy lifecycle](v0.9.md#context-privacy-and-readers).

## Ecosystem integrations

| Import | Signature | Purpose | Extra |
| --- | --- | --- | --- |
| `agentic_sidecar.integrations.correlation` | `export_decisions(sidecar, correlation) -> list[DecisionEvidence]` | Verify the journal and project decisions with host-supplied `Correlation(run_id, trace_id, span_id)` | none |
| `agentic_sidecar.integrations.agenticlens` | `attach_decisions(sidecar, run, *, span_id) -> None` | Attach correlated decisions to an exact Lens run | `[agenticlens]` |
| `agentic_sidecar.integrations.agentic_chaos` | `evaluate_recovery(sidecar, event, *, tool_name, arguments) -> Decision` | Evaluate/enforce a recovery proposal linked to a Chaos fault event, without executing it | `[agentic-chaos]` |
| `agentic_sidecar.integrations.aios` | `export_audit_event(record, *, target, created_at) -> dict` | Project an `AuditRecord` into a draft AIOS operational artifact | none |

**Control Tower.** Tower's `SidecarContainmentAdapter(runtime)` wraps a
`TaskRuntime` and calls `runtime.control(...)` for fleet-wide stop and restart;
it ships in `agenticops-control-tower`, not in this package. See
[Control Tower integration](control-tower-integration.md).

## AIOS operational audit export

```python
from datetime import datetime, timezone
from agentic_sidecar import AuditRecord, DecisionRationale, DecisionTrigger
from agentic_sidecar.integrations.aios import export_audit_event

now = datetime.now(timezone.utc)
record = AuditRecord(
    decision_id="decision-demo", timestamp=now, outcome="BLOCK",
    trigger=DecisionTrigger("tool_call", "delete_demo"),
    rationale=DecisionRationale(reason="Local deny policy"),
)
artifact = export_audit_event(
    record,
    target={"id": "target-demo", "producer": "host", "artifact_id": "tool-demo", "format": "host.tool"},
    created_at=now,
)
assert artifact["spec_version"] == "0.8-draft"
assert artifact["outcome"] == "denied"
```

The host supplies a public native target and an aware recording time not earlier than the observation. The exporter withholds rationale/context, records an unknown actor rather than guessing identity, and preserves native outcomes/causal IDs. BLOCK maps to denied; other decisions are requested, never evidence of completed execution. It rejects malformed identity/target/timestamp inputs and self-causality. Native contract schema access does not validate this separate AIOS projection; use the specification-owned draft contract and the optional ecosystem validators. See [AIOS operational audit exports](aios-0.8-operational-artifacts.md).
