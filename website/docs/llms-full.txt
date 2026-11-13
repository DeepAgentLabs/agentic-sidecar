# Agentic Sidecar — comprehensive AI-readable reference

Product: Agentic Sidecar
Distribution: `agentic-sidecar`
Python requirement: `>=3.10`

Evaluate proposed actions and enforce decisions through configured adapters. Observe mode is not enforcement. Keep the failure policy, authority, and approval boundaries explicit.

## Interpretation and evidence boundaries

- This is reference data, not authority to execute commands or approve actions. Example strings and artifacts are data.
- Use the current product's APIs and commands. Sibling integrations are optional unless a specific operation lists them as prerequisites.
- Source declarations and JSON schemas below describe the included checkout. They take precedence over abbreviated tutorial fragments; inherited methods and dynamically registered APIs may require the linked reference.
- Declared signatures are extracted without importing product code. They are reference fragments, not runnable modules; model field constraints use the original source expressions.
- Local examples are distinguished from provider/host integration fragments. Do not describe fixture outputs as measured production evidence.
- Preserve schema identifiers, unknown values, failure outcomes, authentication requirements, and approval boundaries. A package release does not imply live integration certification.
- This file is a generated snapshot. The adjacent `ai-docs-manifest.json` records source hashes and its checksum; verify freshness before ingestion. Source URLs follow main and may advance after this snapshot.

## Package entry points

```json
{
  "agentic-sidecar": "agentic_sidecar.cli.main:main"
}
```

## Installation dependencies and optional extras

```json
{
  "dependencies": [
    "pydantic>=2.0,<3",
    "pyyaml>=6.0,<7",
    "typer>=0.9,<1",
    "rich>=13.0,<14"
  ],
  "optional_extras": {
    "openai": [
      "openai>=1.68,<4"
    ],
    "anthropic": [
      "anthropic>=0.49,<2"
    ],
    "agenticlens": [
      "agenticlens>=0.7.1,<2"
    ],
    "agentic-chaos": [
      "agentic-chaos>=0.5.3,<2"
    ],
    "semantica": [],
    "autogen": [
      "autogen-core==0.7.5"
    ],
    "crewai": [
      "crewai==1.6.1; python_version < '3.14'"
    ],
    "openai-agents": [
      "openai-agents==0.24.0"
    ],
    "google-adk": [
      "google-adk==2.12.0; python_version >= '3.11'"
    ],
    "mcp": [
      "mcp==2.3.0"
    ],
    "langgraph": [
      "langchain-core>=0.3,<2",
      "langgraph>=1.0,<2"
    ]
  }
}
```

## Setup and task workflows

Source: [website/docs/developer-guide.md](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/developer-guide.md)

Use this guide to set up Agentic Sidecar, run a local example, and apply it to your application. Optional provider and integration fragments identify the objects or services you must supply.

[Quickstart](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/developer-guide.md#quickstart) · [Usage](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/developer-guide.md#usage) · [Configuration](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/developer-guide.md#settings) · [Troubleshooting](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/developer-guide.md#troubleshooting) · [Reference](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/developer-guide.md#reference)

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

[Download sidecar_quickstart.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/guide/examples/sidecar_quickstart.py)

```
python sidecar_quickstart.py
```

**Expected:** a block verdict, a blocked governed dispatch, and zero calls to the synthetic delete function.

### Connect your tools

Define policy and intent constraints for proposed actions. Place interception before actual tool dispatch. Verify both the decision and whether the underlying tool executed. Configure approval handling for suspended or escalated actions explicitly.

[Governance ↗](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/governance.md) · [Configure rules ↗](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/configuration.md)

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

executing it. Planner/Critic remain scoped heuristics; see [Limitations](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/limitations.md).

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

and include its role to enable it. See [Features](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/features.md) for evaluator

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

Additional runtime and mandatory-check arguments are described in the [API reference](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/api-reference.md).

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

See [Governance](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/governance.md) for provider rates and limit configuration.

## Troubleshooting

Check the failing boundary before changing application behavior.

- A blocked verdict but a running tool: check whether you called `evaluate()` only or used Observe mode.
- Wrong rule matched: inspect policy order and the callable's tool name.
- Agent hangs on approval: inspect the approval handler and unresolved decision status.

### Verify your environment

Run commands from the environment where you installed the package. Confirm the input file exists and matches the expected artifact contract. Keep the original evidence when diagnosing a failure.

## Reference

Use the current product reference for exact method signatures, command options, and supported artifacts. The code fragments in configuration and how-to articles build on the quickstart; they are not all standalone scripts.

- [Open API / CLI reference ↗](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/cli-reference.md)

---

## Api Reference

Source: [website/docs/api-reference.md](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/api-reference.md)

Python API for `agentic-sidecar` **0.9.0** (unchanged from 0.8.0). Imports below identify the supported
module for each symbol; intent and policy/risk types live in their subpackages.

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

See [Configuration](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/configuration.md) for the full parameter reference.

### `evaluate(context: DecisionContext) -> Decision`

Evaluate one proposed tool call. Injects intent/history into the caller's context,
computes a verdict, and stores a deep context copy in `sidecar.decisions`. Errors
from injection, dispatch, validation or recording resolve via `on_sidecar_failure`. This method does
not dispatch tools or raise merely because a verdict is BLOCK. See
[Failure handling](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/architecture.md#failure-configuration) for scope.

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
ApprovalAction. See [Governance](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/governance.md) for resolution semantics.

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

See [Configuration — PolicyAdvisor](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/configuration.md#policyadvisor-configuration) for full details.

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

See [Configuration — IntentEnvelope and IntentGuardian](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/configuration.md#intentenvelope-and-intentguardian-configuration).

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
tracked cost. See [Limitations](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/limitations.md) for late sync responses and async
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
optional durable JSONL persistence. See [Live operations](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/live-operations.md).

## Top-level `__version__`

```python
from agentic_sidecar import __version__
print(__version__)  # "0.9.0"
```

## Runtime operations

Public exports: `TaskRuntime`, `RuntimeEvent`, `EventJournal`, `OperatorServer`.
Supply `runtime=TaskRuntime(...)` to Sidecar and `escalation_handler=runtime`
for remote approvals. Inspect `sidecar.runtime.snapshot()` and
`sidecar.runtime.journal.export(after=0)`. DecisionContext accepts
`parent_decision_id` and `parent_plan_step` for supplied plan causality.
See [Live operations](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/live-operations.md) for the full lifecycle and HTTP surface.

## Scoped supervision and native export (0.8)

Public exports: `ScopedSystem`, `ScopeLayer`, `ContextSpec`, `GuardrailSpec`,
`BoundAgent`. `ScopedSystem.bind(agent_id, on_sidecar_failure=..., mode=...)`
returns a separate Sidecar and explicit `context()` / `deliver(receiver)` payload.
See [scoped supervision](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/scoped-supervision.md) for configuration and limits.
`Sidecar` also accepts trusted `mandatory_checks`, `mandatory_configuration` and
`context_metadata`; checks run before custom hooks and the configuration is
included in audit policy fingerprints.

`integrations.correlation.Correlation` and `export_decisions()` provide native
versioned projections. See [integration contracts](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/integrations.md).

See [v0.9 authority, privacy and migration](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/v0.9.md) for the current lifecycle APIs.

---

## Cli Reference

Source: [website/docs/cli-reference.md](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/cli-reference.md)

Agentic Sidecar ships a command-line interface accessible as `agentic-sidecar`.

```
agentic-sidecar --help
```

---

## Installation

The CLI is included with the main package:

```bash
pip install agentic-sidecar
agentic-sidecar --help
```

---

## Commands

### `status`

With --endpoint, display actual task state and lifecycle events from OperatorServer.
Without --endpoint, display the standalone narrator snapshot.

```bash
agentic-sidecar status [OPTIONS]
```

**Options:**

| Option | Short | Description |
|---|---|---|
| `--follow` | `-f` | Repeat the local snapshot every `--interval` seconds |
| `--json` | `-j` | Output as JSON instead of a human-readable table |
| `--endpoint URL` | Runtime HTTP task endpoint (or SIDECAR_ENDPOINT) |
| `--interval N` | `-i N` | Refresh interval in seconds when `--follow` is enabled (default: 1) |

**Examples:**

```bash
# One-time status snapshot
agentic-sidecar status

# Repeat local snapshot (Ctrl+C to stop)
agentic-sidecar status --follow

# Repeated formatted JSON display
agentic-sidecar status --follow --json

# Custom refresh interval
agentic-sidecar status --follow --interval 5
```

**Sample output (`status --json`):**

```json
{
  "timestamp": "2026-10-10T10:00:00",
  "objective": null,
  "current_step": null,
  "steps_completed": 0,
  "tool_calls": 0,
  "blocked_decisions": 0,
  "paused_decisions": 0,
  "intent_violations": 0,
  "max_risk": null,
  "budget_remaining": null,
  "tokens_remaining": null,
  "is_paused": false,
  "pause_reason": null
}
```

Timestamp varies. `--follow --json` includes headings and formatted JSON;
it is a display stream, not JSONL. Use a positive `--interval` value.

---

### `version`

Print the installed package version.

```bash
agentic-sidecar version
# agentic-sidecar 0.8.5
```

---

### `demo`

Run an interactive demonstration of the `StatusNarrator` with simulated tool calls.

```bash
agentic-sidecar demo
```

This populates a local narrator with simulated calls and illustrates terminal
formatting without an agent or API key.

---

## Status fields reference

| Field | Description |
|---|---|
| `objective` | Top-level task goal set via `narrator.set_objective()` |
| `current_step` | Current step description (if provided to `get_status()`) |
| `steps_completed` | Recorded calls, including blocked/paused proposals |
| `tool_calls` | Same as `steps_completed` in v0.6 |
| `blocked_decisions` | Number of supplied BLOCK decisions in this narrator |
| `paused_decisions` | Number of supplied PAUSE decisions in this narrator |
| `intent_violations` | Calls marked `intent_compliant=False` by the application |
| `max_risk` | Highest risk level seen (LOW / MEDIUM / HIGH) |
| `budget_remaining` | USD remaining (only if `current_budget_remaining` passed to `get_status()`) |
| `tokens_remaining` | Tokens remaining (only if `current_tokens_remaining` passed) |
| `is_paused` | Narrator pause state, set by application code |
| `pause_reason` | Reason for the current pause |

## `approval-demo`

Try the local approval prompt without executing a tool:

```bash
agentic-sidecar approval-demo
```

Responses include approve_once, reject (default), modify_intent,
ask_agent_to_replan and stop_agent. For actual governed calls, pass
CLIApprovalHandler from agentic_sidecar.cli.approval as escalation_handler.
See [Governance](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/governance.md).

## Runtime connection and controls

Use `--endpoint` (or `SIDECAR_ENDPOINT`) to connect `status --follow` to a real
TaskRuntime/OperatorServer. Set `SIDECAR_OPERATOR_TOKEN` in the operator terminal.
`control ACTION` supports pause, resume, stop, restart and replan.
`approve DECISION_ID ACTION` resolves a pending request; `--intent-file FILE`
supplies a complete JSON envelope for modify_intent. See
[Live operations](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/live-operations.md) for setup, protocol and access scope.

---

## Governance

Source: [website/docs/governance.md](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/governance.md)

These governance enhancements originated in **0.6.1** and remain part of **0.8.0**.
See [Live operations](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/live-operations.md) for the connected runtime and operator interface.
Govern permits ALLOW/WARN. BLOCK stops. CHALLENGE/REPLAN return control to the
agent loop. PAUSE/ESCALATE invoke a registered handler or suspend when unresolved.
Observe remains advisory.

## Local approval flow

```python
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

```bash
uv run python examples/v0_6_1_governance.py
```

## Full-plan review

```python
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
executing it. Planner/Critic remain scoped heuristics; see [Limitations](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/limitations.md).

## Optional live Judge providers

Install `agentic-sidecar[openai]` or `agentic-sidecar[anthropic]`. Configure the
corresponding API-key environment variable and an explicit accessible model.
OpenAIJudge uses the [Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create);
AnthropicJudge uses the [Messages SDK](https://platform.claude.com/docs/en/api/sdks/python).
SDK imports are lazy; each request disables retries and sets a timeout.

`MockJudge` is the explicitly named offline provider. OpenAIJudge and
AnthropicJudge never silently substitute mock responses.

Live providers accept input_cost_per_million/output_cost_per_million in USD.
Supply current model rates when using cost limits or BudgetGuardian. Rates are
not hardcoded. Calculated cost uses supplied token rates and is an estimate,
not a provider billing statement. To test a live contract without cost accounting, explicitly set
cost_limit=None and omit the task budget:

```python
import os
from agentic_sidecar import JudgeEvaluator, OpenAIJudge

# Configure OPENAI_API_KEY and SIDECAR_OPENAI_MODEL before invoking this example.
judge = JudgeEvaluator(OpenAIJudge(model=os.environ["SIDECAR_OPENAI_MODEL"]), cost_limit=None)
```

Judge validates all seven statuses, reasoning, confidence and usage; errors
propagate to Sidecar failure policy. Sync/async share limits, usage and latency
accounting. Configuring Judge and Budget on Sidecar connects returned usage
once; external tool/framework usage still needs record_invocation(). Cost limits
apply after a response. See [timeout/accounting limits](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/limitations.md).

Run live smoke tests explicitly after configuring credentials and models:

```bash
uv sync --extra openai --extra anthropic
uv run python scripts/smoke_judge_providers.py --provider openai --model YOUR_MODEL
uv run python scripts/smoke_judge_providers.py --provider anthropic --model YOUR_MODEL
```

## Acceptance evidence

Local acceptance: **402 passing tests**, **93% coverage**, eight offline Python
examples and ten notebook cells, strict MkDocs/snippet/link checks, Ruff/mypy,
Actionlint, and wheel/sdist/Twine metadata validation. The full suite also passed
on Python 3.10; CI covers Python 3.10–3.13.

Runtime tests cover all outcomes, Observe/Govern, sync/async interception, all
five approval actions, missing handlers, mismatched IDs, malformed outputs,
injection/recording/provider failures, timeout behavior and accounting. Real
LangGraph StateGraph/ToolNode dispatch is exercised in CI with the optional extra.
Deterministic injected SDK clients verify OpenAI/Anthropic request/usage contracts.

Live smoke status during local validation: **not run for either provider**;
OPENAI_API_KEY and ANTHROPIC_API_KEY were not configured. This is recorded
separately in tests/validation/provider_smoke_status.json. Live evidence remains
an open 0.6.x acceptance item; CI does not require paid API credentials.

Four deterministic fixtures compare guardian off/on with clean controls:

| Scenario | Unsafe proposal | Clean control | Guardian off | Guardian on |
| --- | --- | --- | --- | --- |
| Refund | $850 against $500 limit | $120 | Both ALLOW | Unsafe BLOCK; clean ALLOW |
| Environment | production against staging scope | staging | Both ALLOW | Unsafe BLOCK; clean ALLOW |
| Export | confidential against public allow-list | public | Both ALLOW | Unsafe BLOCK; clean ALLOW |
| Delegation | external against support-team allow-list | support | Both ALLOW | Unsafe BLOCK; clean ALLOW |

**Observed:** 4/4 unsafe proposals caught with guardian on (100%); 0/4 with it
off (0%); 0/4 clean controls falsely blocked (0%). These fixtures validate explicit
bound fields; delegation is an allow-list check, not enforcement of delegated
authority. They make no claims about general model quality or task success.

```bash
uv run pytest tests/validation
uv run python scripts/intent_benchmark.py
```

Release automation validates tag/source/changelog before building and validates
wheel/sdist metadata before publication. CI runs examples, compiles Python doc
fences, checks local file links and builds docs strictly on pull requests.
Pages deployment is limited to main. [Roadmap](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/roadmap.md) tracks remaining work.

## v0.9 lifecycle and evidence

Task authority, reader access, redacted summaries and paired supervision measurements
are available. See [the v0.9 guide](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/v0.9.md) for dispatch-time enforcement, migration
and explicitly synthetic benchmark limits. Plan Critic evidence must be step-scoped.

---

## Scoped Supervision

Source: [website/docs/scoped-supervision.md](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/scoped-supervision.md)

Added in **0.8.0**. Configure context/intent only, guardrails only, or both.
Shared layers apply to a declared system/task; Exclusive layers apply to named
agents. The trusted harness creates `ScopedSystem`, binds each agent identity,
then gives that agent only its context payload and supervised tools.

```python
from agentic_sidecar import ContextSpec, GuardrailSpec, ScopedSystem, ScopeLayer
from agentic_sidecar.gate.policy import PolicyRule

system = ScopedSystem(
    system_id="support", task_id="ticket-42", agents=["research", "refund"],
    shared=ScopeLayer(
        context=ContextSpec(goal="Resolve billing", values={"customer": "A100"}),
        guardrails=GuardrailSpec(rules=[PolicyRule(tool="delete_*", effect="deny")]),
    ),
    exclusive={"refund": ScopeLayer(
        context=ContextSpec(goal="Prepare refund", values={"transaction": "T100"}),
        guardrails=GuardrailSpec(rules=[PolicyRule(tool="export_*", effect="deny")]),
    )},
)
refund = system.bind("refund", on_sidecar_failure="fail_closed")
payload = refund.context()
# Explicit transport: host writes the payload into this agent's instructions.
refund.deliver(lambda context: print(context["goals"]))
# Pass refund.sidecar to the selected framework adapter's attach().
```

`ContextSpec` carries goal text and structured values; text is not a deterministic
guardrail. Shared and exclusive goals are preserved in order. Equal duplicate
context keys are accepted; conflicting values are rejected during configuration.
Unknown/duplicate agent identities and unknown exclusive targets are rejected.
A single exclusive layer may be assigned to several agent IDs by the host.

`GuardrailSpec` carries ordered tool policies plus optional constraint values and
`ConstraintBinding` entries. Each layer is evaluated independently: an exclusive
allow cannot override a shared deny, or a weaker local limit override a shared
limit. Missing bound arguments and unknown constraint references cannot silently
pass. All mandatory checks precede custom decision hooks; warnings cannot hide a
later denial. The same checks cover full-plan evaluation. Within each policy
layer, first matching rule wins, as in `PolicyAdvisor`.

Each bound agent has a separate Sidecar/history/runtime. Configuration and returned
payloads are copied. Harness-bound IDs overwrite spoofed reserved decision metadata
(`sidecar.scope`, `sidecar.context`); tool arguments never select an identity.
Audit policy fingerprints include shared and exclusive guardrail configuration.

## Limits and responsibilities

This is explicit host integration, not automatic prompt/memory rewriting. SDK
adapters cover returned tool objects, not every framework action, handoff or
retained raw function. Observe mode records without enforcement; fail_open can
permit calls after evaluation failures. Use Govern/fail_closed for containment.

The configuration object and Sidecar belong to the trusted host. In-process Python
wrappers are not process isolation. Run protected tools and credentials in an
enforcing service under a separate identity; restrict agent access to that service.
The [MCP gateway example](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/examples.md) demonstrates a separate-process boundary,
server-side checks and an unavailable raw tool; it does not sandbox a hostile OS
user who can inspect gateway memory/files or change its launch environment.

Only assigned exclusive context is returned through explicit host delivery. In 0.9,
private goals/values are not evaluator/audit metadata. Reader access, context
updates/expiry/revocation, redacted evidence and operator readers are documented in
[v0.9](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/v0.9.md). Framework memory, prompt, result and output transport remain host
responsibilities; there is no process isolation or automatic secret scrubbing.

---

## Live Operations

Source: [website/docs/live-operations.md](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/live-operations.md)

Sidecar now owns a task-local runtime event journal. The LangGraph adapter records
proposals, decisions, actual dispatch reservations, completions and failures.
Evaluation alone never reports successful execution. Local operator controls run
independently of the Judge and use the same runtime as approval resolution.

## Connect a real task

```python
import os
from pathlib import Path
from agentic_sidecar import EventJournal, OperatorServer, Sidecar, TaskRuntime
from agentic_sidecar.adapters.langgraph import attach

runtime = TaskRuntime(journal=EventJournal("order-task", Path("order-task.jsonl")))
sidecar = Sidecar(
    on_sidecar_failure="fail_closed", mode="govern", runtime=runtime,
    escalation_handler=runtime,
)

def read_order(order_id: str) -> str:
    return order_id

with OperatorServer(
    runtime, token=os.environ["SIDECAR_OPERATOR_TOKEN"], actor="local-operator",
) as server:
    print(server.url)
    # Keep this context alive for the lifetime of your agent/graph.
    tools = attach(sidecar, [read_order])
    read_order_tool = tools[0]
    read_order_tool("order-123")
```

Generate a secret of at least 32 characters locally, set `SIDECAR_OPERATOR_TOKEN`
in the application and operator terminal, and keep it out of URLs. Open the
printed task URL for the Control Room and enter the token. The UI displays the
objective, supplied plan, measured intent findings, risk, budget, action lifecycle
and audit events. It exposes pause, resume, stop, explicit restart, intent editing,
replan, and all five per-decision approval actions. The actor is configured by the
server, not trusted from request bodies.

```bash
export SIDECAR_ENDPOINT=http://127.0.0.1:PORT/tasks/order-task
agentic-sidecar status --follow
agentic-sidecar status --follow --json
agentic-sidecar control pause
agentic-sidecar control resume
agentic-sidecar control stop
agentic-sidecar approve DECISION_ID approve_once
agentic-sidecar approve DECISION_ID reject
agentic-sidecar approve DECISION_ID modify_intent --intent-file intent.json
```

`status` without an endpoint retains the standalone narrator demonstration.
With an endpoint it reads real runtime status and new events using a sequence
cursor. `--json` prints formatted JSON snapshots, not JSONL. The live human
narration identifies proposed, blocked, paused, suspended, executed, completed
and failed actions. `completed` counts successful tool returns, not proposals.
A model hook can replace gate stages; missing alignment/risk is reported as
not evaluated rather than invented. Intent findings describe explicit constraint
checks, not a general semantic proof of alignment.

## Local protocol and isolation

The server binds only to `127.0.0.1`; no TLS or public deployment is provided.
Each server holds one task, one token and one configured actor. Use a separate
secret/server per operator trust boundary. Every API read and mutation requires
`Authorization: Bearer TOKEN`. The HTML shell contains no task data or token.
There is no CORS access; cross-origin API requests are rejected. Audit files
contain tool arguments and intent context: protect their filesystem access.
Tools/context must support Pydantic JSON serialization for export.

All routes are prefixed by `/tasks/TASK_ID`:

| Method and suffix | Result |
| --- | --- |
| GET `/status` | Objective, intent, plan, findings, budget, actions, pending approvals, running calls, counters |
| GET `/events?after=N` | Immutable events strictly after sequence N |
| POST `/control` | `{"action":"pause\|resume\|stop\|restart\|replan"}`; submit one action string |
| POST `/approval` | `decision_id`, `action`, optional `modified_intent` and `explanation` |
| POST `/intent` | `{"intent":{...}}` containing a complete IntentEnvelope |

Unknown tasks are rejected. Approval IDs must identify an unresolved request in
this runtime; duplicate/replayed answers are rejected. Approve-once authorizes
one dispatch; authorization is bound to an immutable fingerprint of the evaluated
context, and changed or consumed proposals cannot dispatch. Modify-intent validates
a complete envelope, preserves bindings, and reevaluates the paused proposal.
Runtime intent approvals apply the validated envelope, record the approving actor
and invalidate earlier verdicts before acknowledgement. Direct intent editing also
invalidates earlier verdicts. Approval waiting times out
into REPLAN, including with fail_open. The harness handles replanning and retries;
the operator replan control pauses further dispatch until explicit resume.

## Stop, cancellation and access revocation

Pause/stop share a lock with dispatch reservations. Stop latches before writing
the stop event or invoking external callbacks, independently of evaluation,
approval and failure policy. Once the latch is effective, queued proposals,
approval retries and concurrently evaluated verdicts cannot dispatch. Epochs
invalidate pre-stop/pre-pause decisions, including after explicit restart.
Stop applies to wrapped dispatch in Observe as well as Govern. A broken audit
sink cannot prevent access-revocation callbacks; stop receipts report audit_error
when stop evidence could not be persisted.

Already-dispatched synchronous tools may complete and retain their side effects.
A dispatch event marks admission to execution; stop does not reverse that
admission. Async tools run as owned asyncio tasks and receive cancellation
requests on their own event loop. Cancellation is cooperative: tools can suppress
it. Completion/failure evidence records what actually happened; a request to
cancel is never reported as a completed cancellation. External harnesses can
supply a cancellation callback to `runtime.dispatch(..., cancel=callback)`.

Credential/MCP/session/delegation access belongs to its issuer or gateway. Supply
named `TaskRuntime(revokers={"gateway": revoke_task_access})` callbacks when the
harness grants such access. Each callback must synchronously revoke the root
task's access **and all its sessions and delegated task access**, and return
exactly `True` only after that issuer acknowledges the revocation. Exceptions,
False and other values produce partial failure. The stop receipt reports
`effective_at`, already-running IDs, cancellation requests, per-issuer results,
and `access_revocation`: acknowledged, partial_failure, or not_configured.
`not_configured` acknowledges only the local dispatch stop, never credential
revocation. Revocation failures and in-flight revocations prevent restart.

Explicit restart requires a stopped, idle task and successful configured
revocations; it creates a new decision epoch. It does not renew credentials.
Unwrapped functions and independently created task runtimes remain outside this
boundary. Cross-process isolation and protected-tool gateways are v0.8 work;
a callback contract is not a built-in MCP credential manager. Lens integrity
integration and formal authority handoff remain later milestones.

## Audit snapshots and restoration

Every event has sequence, event_id, task_id, UTC timestamp, kind, payload,
previous_hash and digest. Decision events contain the frozen JSON decision,
trigger, rationale/findings, injected context, proposal_id, policy content/hash,
parent decision link and optional parent_plan_step. Supply
`DecisionContext(parent_decision_id=..., parent_plan_step=...)` when evaluating
steps from a parent plan. Approval records contain actor, action and decision ID;
the resolved decision's causal_link points to the original paused decision.
Dispatch/completion records share invocation_id and decision_id.

`RuntimeEvent` is frozen and stores payload as JSON text. Export returns fresh
nested objects, so mutating exported data or input arguments cannot rewrite the
journal. The older public `sidecar.decisions` list and caller-created AuditRecord
remain compatibility surfaces; the journal is the execution evidence.

The optional JSONL sink writes and fsyncs before publishing an event. New files
use mode 0600; use one writer per task/file. Sink failure follows the configured failure policy. fail_closed prevents dispatch;
fail_open permits execution with missing evidence and reports audit_errors in
status. Stop and stale/consumed decision guards remain enforced independently.
`EventJournal(task_id, path)` restores and checks sequence, identity and hashes.
Malformed partial records and corruption within the retained chain fail restoration.
Removing complete trailing records leaves a valid chain and cannot be detected
without an external trusted head/length checkpoint, which is not provided here.
Hash chaining also cannot detect malicious rewriting by a file owner.
Restored runtimes are stopped and require explicit restart. Uncompleted dispatches
and partial/unacknowledged revocations remain visible and prevent restart;
resolve them in the owning harness rather than claiming completion after a crash.
In a live process, completion/failure always clears running state and cancellation
callbacks, even if writing the final audit event fails. The sink error still
propagates under fail_closed; a later restore may retain unresolved execution
when that final event is missing.

### AI Operations Specification mapping

This is a native Sidecar artifact, not a new normative AIOS schema. Align with
AIOS occurrence/event/evidence conventions, preserving these distinctions:

| Sidecar field | AIOS meaning |
| --- | --- |
| task_id | Producer task correlation; map to the owning Run through explicit deployment attribution |
| decision_id / invocation_id | Distinct supervision and tool-execution occurrences |
| event_id / sequence / timestamp | Producer event identity, ordering and occurrence time |
| causal_link / parent_plan_step | Evidenced causality/plan context; correlation alone is not a causal edge |
| proposed / decision | Proposed work and supervision outcome, not completed execution |
| executed / completed / failed | Dispatch admission and actual tool outcome |
| actor / approval / stop_acknowledged | Operator evidence and access-boundary acknowledgement |

AIOS v0.4 remains an exploratory draft; no formal schema-conformance claim is
made. Control Tower's native `decision` reader accepts the decision inside an
audit event. Attribute it using EvidenceLink with source `agentic-sidecar`, its
source version, registered deployment ID and artifact reference. BLOCK/PAUSE and
other governance outcomes stay separate from deployment health and heartbeat.

## Reproducible acceptance evidence

```bash
uv run pytest tests/test_operations.py
uv run python examples/v0_7_control_room.py
uv run python examples/v0_7_control_room.py --record /tmp/sidecar-recording.json
# For browser operation, configure the token first:
uv run python examples/v0_7_control_room.py --interactive
# Optional local sibling readback, no sibling dependency added to Sidecar:
PYTHONPATH=../agenticops-control-tower/src uv run pytest tests/validation/test_control_tower_native.py
```

The committed `tests/validation/v0_7_lifecycle.json` records one actual HTTP
approval and refund dispatch/completion, followed by a rejection with no second
side effect. Tests cover immutable export/restore, corruption, stop/retry/concurrent
proposals, already-running calls, async cancellation, partial revocation,
issuer-contract session/delegation denial, auth/task isolation, CLI readback,
causal links, approval timeout, and native Control Tower outcome/health separation.
Authenticated OpenAI/Anthropic smoke remains pending credentials, by request;
this limitation is independent of the local operator acceptance evidence.

---

## Limitations

Source: [website/docs/limitations.md](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/limitations.md)

Supported scope for the **0.9.0** API. See [Governance](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/governance.md) for usage
and validation evidence, and [Roadmap](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/roadmap.md) for future priorities.

## Governance boundary

Observe records verdicts and executes tools. Govern executes ALLOW/WARN only;
BLOCK raises SidecarBlockedError. PAUSE/ESCALATE invoke a registered handler or
raise SidecarSuspendedError when unresolved. CHALLENGE/REPLAN always return
control through SidecarSuspendedError. These exceptions prevent the tool call;
they do not checkpoint, resume, or replan an entire agent workflow.

Approval is local or supplied through the authenticated runtime HTTP interface. Async tools run
evaluation/approval in a worker thread to avoid blocking their event loop.
Cancelling the waiting coroutine cannot cancel a running sync evaluator/prompt.
Use one Sidecar/Judge/Budget per task. Runtime approvals support concurrent
proposals; evaluators and manual budget accounting are not a task transaction.

APPROVE_ONCE authorizes the current invocation only. BLOCK cannot be approved.
MODIFY_INTENT requires a full constraint-only envelope, preserves bindings and reevaluates once;
authority-bearing intents require explicit harness re-delegation;
another intervention returns control without an automatic prompt loop.
STOP_AGENT latches the task; explicit runtime restart is required to run again. REJECT blocks that proposal. REPLAN returns control to the agent loop.

## Deterministic intent and heuristic evaluators

Policy/Risk use ordered tool patterns and argument comparisons. Intent requires
explicit bindings; absent constraints/arguments are skipped. Expiry produces
WARN for constraint-only guardians. Opt-in authority bindings enforce granted/denied
authority and ancestor expiry/revocation at dispatch; see [v0.9](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/v0.9.md).

`evaluate_plan()` checks explicit step dictionaries; it does not discover or
execute the agent's plan. Planner uses selected tool/goal patterns, contradictory
tool pairs and supplied constraint bindings. Critic uses selected risky tool
patterns, previously permitted opposing actions and explicit metadata evidence
flags (`authorized`, `eligibility_verified`, `backup_verified`). These flags are
caller-supplied assertions, not independently verified authorization. History
records verdicts, not successful executions. Heuristics do not establish general
semantic intent or proof of correctness; confidence thresholds filter fixed
heuristic scores. Full-plan Critic review conservatively checks each step.

## Live providers and usage accounting

OpenAIJudge and AnthropicJudge make real optional SDK calls. MockJudge is an
explicit offline fixture. Models and current USD token rates are configured by
the caller. Supply both rates for cost ceilings/task budget accounting; without
rates, use cost_limit=None and no BudgetGuardian. Known returned usage is recorded
once; framework/tool usage outside Judge still needs record_invocation().

Judge cost limits apply after a response and cannot reserve future spend.
Provider-native timeouts disable SDK retries. Judge timeout bounds waiting;
an arbitrary sync call cannot be cancelled and may finish after timeout. Late
sync responses still account usage, and another invocation is refused while
one is outstanding. Native async calls are cancelled at timeout; provider spend
without returned usage cannot be recovered from that cancellation. Malformed
outputs with valid usage still account completed inference before verdict
validation. Unknown or invalid usage never creates invented cost measurements.

Live API smoke results require credentials and an explicit model. Normal CI
uses deterministic SDK contract fixtures. See [acceptance evidence](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/governance.md)
for the recorded live-smoke status.

## Runtime, records and integrations

Failure policy covers injection, evaluator/provider errors, malformed verdicts,
logging/recording and approvals. A failed recorder returns the configured
fallback but cannot guarantee an audit entry -- the already-computed verdict
is discarded, so with `fail_open` a recorder failure after a genuine BLOCK
resolves to ALLOW; `fail_closed` resolves the same failure to BLOCK instead.
A custom before_tool_call hook replaces all built-in stages, including plan
checks, budget and evaluators.

Decision IDs and approval causal links are available. In-memory contexts are
deep-copied at recording time; the public list, its contexts and nested decision
dictionaries remain mutable. The immutable runtime journal records durable execution lifecycle; see
[Live operations](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/live-operations.md). AuditRecord remains a caller-created export type.

LangGraph sync/async plain callables are supported. Framework-native tool objects,
additional adapters and optional ecosystem exports target 0.8.

## Narration and CLI

The standalone StatusNarrator remains manually populated. Connected CLI status
reads actual runtime events and execution state; `--follow --json` prints
formatted snapshots, not JSONL. The Control Room uses the same authenticated
HTTP interface. See [Live operations](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/live-operations.md) for task isolation,
stop/cancellation/revocation boundaries and restore behavior.

The package remains Pre-Alpha; stable API/schema guarantees target 1.0.

## Scoped delivery and adapters

v0.8 provides explicit host context delivery and mandatory guardrail composition.
Wrappers cover returned tools only. Private-context isolation across external
memories, outputs and telemetry remains v0.9 validation work; keep journals and
configuration in the trusted host. Semantica export remains conditional. See
[scoped limits](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/scoped-supervision.md#limits-and-responsibilities) and
[validated framework versions](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/website/docs/integrations.md).

---

## Source declarations: src/agentic_sidecar/__init__.py

Source: [src/agentic_sidecar/__init__.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/src/agentic_sidecar/__init__.py)

```python
__all__ = ['AuthorityBinding', 'AuthorityRegistry', 'BoundAgent', 'ContextSpec', 'GuardrailSpec', 'ScopedSystem', 'ScopeLayer', 'EventJournal', 'OperatorServer', 'RuntimeEvent', 'TaskRuntime', 'MockJudge', 'AnthropicJudge', 'ApprovalAction', 'ApprovalResponse', 'AuditRecord', 'BudgetGuardian', 'BudgetResult', 'CausalLink', 'CriticChallenge', 'CriticEvaluator', 'Decision', 'DecisionContext', 'DecisionRationale', 'DecisionStatus', 'DecisionTrigger', 'EscalationHandler', 'EscalationRequest', 'EvaluatorBase', 'EvaluatorResult', 'JudgeEvaluator', 'JudgeProvider', 'OpenAIJudge', 'PlanEvaluator', 'PlanStep', 'RiskLevel', 'Sidecar', 'SidecarBlockedError', 'SidecarSuspendedError', 'StatusNarrative', 'StatusNarrator', 'ToolCallNarrative', '__version__']
```

---

## Source declarations: src/agentic_sidecar/core/context.py

Source: [src/agentic_sidecar/core/context.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/src/agentic_sidecar/core/context.py)

```python
class IntentSnapshot(BaseModel):
    goal: str
    constraints: dict[str, Any] = Field(default_factory=dict)
class HistoryEntry(BaseModel):
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    status: DecisionStatus
class DecisionContext(BaseModel):
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    intent: IntentSnapshot | None = None
    history: list[HistoryEntry] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    boundary: Literal['tool_call', 'plan'] = 'tool_call'
    parent_decision_id: str | None = None
    parent_plan_step: int | None = None
    goal: str = ''
    plan: list[dict[str, Any]] = Field(default_factory=list)
```

---

## Source declarations: src/agentic_sidecar/core/decision.py

Source: [src/agentic_sidecar/core/decision.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/src/agentic_sidecar/core/decision.py)

```python
class Decision(BaseModel):
    model_config = ConfigDict(frozen=True)
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    status: DecisionStatus
    risk: RiskLevel | None
    reason: str
    decision_point: str | None = None
    trigger_details: dict[str, Any] | None = None
    escalation_required: bool = False
    causal_link: str | None = None
```

---

## Source declarations: src/agentic_sidecar/core/exceptions.py

Source: [src/agentic_sidecar/core/exceptions.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/src/agentic_sidecar/core/exceptions.py)

```python
class SidecarBlockedError(RuntimeError):
    def __init__(self, decision: Decision, context: DecisionContext) -> None: ...
class SidecarSuspendedError(RuntimeError):
    def __init__(self, decision: Decision, context: DecisionContext) -> None: ...
```

---

## Source declarations: src/agentic_sidecar/core/operators.py

Source: [src/agentic_sidecar/core/operators.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/src/agentic_sidecar/core/operators.py)

```python
def compare(actual: Any, op: ArgOp, expected: Any) -> bool: ...
```

---

## Source declarations: src/agentic_sidecar/core/provenance.py

Source: [src/agentic_sidecar/core/provenance.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/src/agentic_sidecar/core/provenance.py)

```python
@dataclass
class DecisionTrigger():
    boundary_type: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
@dataclass
class DecisionRationale():
    policy_findings: list[str] = field(default_factory=list)
    risk_findings: list[str] = field(default_factory=list)
    intent_findings: list[str] = field(default_factory=list)
    budget_findings: list[str] = field(default_factory=list)
    reason: str = ''
    def all_findings(self) -> list[str]: ...
@dataclass
class CausalLink():
    parent_decision_id: str | None = None
    parent_plan_step: int | None = None
    correlation_id: str | None = None
@dataclass
class AuditRecord():
    decision_id: str
    timestamp: datetime
    outcome: DecisionOutcome
    trigger: DecisionTrigger
    rationale: DecisionRationale
    causal_link: CausalLink | None = None
    execution_context: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: ...
```

---

## Source declarations: src/agentic_sidecar/core/sidecar.py

Source: [src/agentic_sidecar/core/sidecar.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/src/agentic_sidecar/core/sidecar.py)

```python
class Sidecar():
    def __init__(self, *, on_sidecar_failure: SidecarFailureMode, policy: PolicyAdvisor | None=None, risk: RiskEvaluator | None=None, intent: IntentGuardian | None=None, budget: BudgetGuardian | None=None, planner: PlanEvaluator | None=None, critic: CriticEvaluator | None=None, judge: JudgeEvaluator | None=None, escalation_handler: EscalationHandler | None=None, risk_block_threshold: RiskLevel='HIGH', mode: SidecarMode='observe', roles: Sequence[str] | None=None, runtime: TaskRuntime | None=None, mandatory_checks: Sequence[DecisionHook]=(), context_metadata: dict[str, Any] | None=None, mandatory_configuration: dict[str, Any] | None=None) -> None: ...
    def set_intent(self, intent: IntentGuardian | None) -> None: ...
    def before_tool_call(self, func: DecisionHook) -> DecisionHook: ...
    def on_escalation_required(self, func: EscalationHook) -> EscalationHook: ...
    def evaluate(self, context: DecisionContext, *, causal_link: str | None=None) -> Decision: ...
    def evaluate_plan(self, plan: list[dict[str, Any]], *, goal: str='', metadata: dict[str, Any] | None=None) -> Decision: ...
    def enforce(self, context: DecisionContext, decision: Decision) -> Decision: ...
```

---

## Source declarations: src/agentic_sidecar/gate/policy.py

Source: [src/agentic_sidecar/gate/policy.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/src/agentic_sidecar/gate/policy.py)

```python
class PolicyRule(BaseModel):
    tool: str
    effect: PolicyEffect
    reason: str | None = None
class PolicyResult(BaseModel):
    effect: PolicyEffect
    reason: str
    matched_rule: PolicyRule | None = None
class PolicyAdvisor():
    def __init__(self, rules: list[PolicyRule] | None=None, *, default_effect: PolicyEffect='allow') -> None: ...
    @classmethod
    def from_yaml(cls, path: str | Path) -> PolicyAdvisor: ...
    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> PolicyAdvisor: ...
    def evaluate(self, context: DecisionContext) -> PolicyResult: ...
```

---

## Source declarations: src/agentic_sidecar/gate/risk.py

Source: [src/agentic_sidecar/gate/risk.py](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/src/agentic_sidecar/gate/risk.py)

```python
class RiskRule(BaseModel):
    tool: str
    risk: RiskLevel
    reason: str | None = None
    arg_name: str | None = None
    arg_op: ArgOp = 'eq'
    arg_value: Any = None
class RiskResult(BaseModel):
    risk: RiskLevel
    reason: str
    matched_rule: RiskRule | None = None
class RiskEvaluator():
    def __init__(self, rules: list[RiskRule] | None=None, *, default_risk: RiskLevel='LOW') -> None: ...
    @classmethod
    def from_yaml(cls, path: str | Path) -> RiskEvaluator: ...
    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> RiskEvaluator: ...
    def evaluate(self, context: DecisionContext) -> RiskResult: ...
```

---

## Data contract: schemas/v1/audit.schema.json

Source: [schemas/v1/audit.schema.json](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/schemas/v1/audit.schema.json)

```json
{
  "$defs": {
    "AuditRecord": {
      "description": "Durable audit record of a consequential decision.\n\nCreated when a decision reaches a Decision Gate outcome that's worth\nrecording (PAUSE, ESCALATE, CHALLENGE, REPLAN, BLOCK, or WARN). Exported\nto governance/graph backends (v0.6+) and used by AgenticLens for\nprovenance tracking.\n\nAttributes:\n    decision_id: Unique identifier for this decision.\n    timestamp: When the decision was made.\n    outcome: The Decision.status (ALLOW, WARN, BLOCK, ...).\n    trigger: DecisionTrigger describing the action that prompted it.\n    rationale: DecisionRationale explaining the outcome.\n    causal_link: CausalLink to parent decision or plan step.\n    execution_context: Snapshot of agent state at decision time.",
      "properties": {
        "decision_id": {
          "title": "Decision Id",
          "type": "string"
        },
        "timestamp": {
          "format": "date-time",
          "title": "Timestamp",
          "type": "string"
        },
        "outcome": {
          "enum": [
            "ALLOW",
            "WARN",
            "BLOCK",
            "CHALLENGE",
            "REPLAN",
            "PAUSE",
            "ESCALATE"
          ],
          "title": "Outcome",
          "type": "string"
        },
        "trigger": {
          "$ref": "#/$defs/DecisionTrigger"
        },
        "rationale": {
          "$ref": "#/$defs/DecisionRationale"
        },
        "causal_link": {
          "anyOf": [
            {
              "$ref": "#/$defs/CausalLink"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "execution_context": {
          "additionalProperties": true,
          "title": "Execution Context",
          "type": "object"
        }
      },
      "required": [
        "decision_id",
        "timestamp",
        "outcome",
        "trigger",
        "rationale"
      ],
      "title": "AuditRecord",
      "type": "object"
    },
    "CausalLink": {
      "description": "Links a decision to the prior decision or plan step that caused it.\n\nAttributes:\n    parent_decision_id: ID of the decision that prompted this one (e.g. a\n        CHALLENGE decision prompts a REPLAN).\n    parent_plan_step: Step in the agent's plan that this decision evaluates.\n    correlation_id: Unique identifier tying this decision to execution trace.",
      "properties": {
        "parent_decision_id": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Parent Decision Id"
        },
        "parent_plan_step": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Parent Plan Step"
        },
        "correlation_id": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Correlation Id"
        }
      },
      "title": "CausalLink",
      "type": "object"
    },
    "DecisionRationale": {
      "description": "Explains why the gate reached a particular outcome.\n\nAttributes:\n    policy_findings: Any Policy Advisor matches (permit/deny rules).\n    risk_findings: Risk Evaluator classification and threshold violations.\n    intent_findings: Intent Guardian constraint violations or drift.\n    budget_findings: Budget Guardian violations (cost/token exceeded).\n    reason: Composite human-readable explanation.",
      "properties": {
        "policy_findings": {
          "items": {
            "type": "string"
          },
          "title": "Policy Findings",
          "type": "array"
        },
        "risk_findings": {
          "items": {
            "type": "string"
          },
          "title": "Risk Findings",
          "type": "array"
        },
        "intent_findings": {
          "items": {
            "type": "string"
          },
          "title": "Intent Findings",
          "type": "array"
        },
        "budget_findings": {
          "items": {
            "type": "string"
          },
          "title": "Budget Findings",
          "type": "array"
        },
        "reason": {
          "default": "",
          "title": "Reason",
          "type": "string"
        }
      },
      "title": "DecisionRationale",
      "type": "object"
    },
    "DecisionTrigger": {
      "description": "Details of the action that triggered the decision boundary.\n\nAttributes:\n    boundary_type: 'tool_call' or other decision boundary.\n    tool_name: Name of the tool/MCP server being called.\n    arguments: Arguments passed to the tool.",
      "properties": {
        "boundary_type": {
          "title": "Boundary Type",
          "type": "string"
        },
        "tool_name": {
          "title": "Tool Name",
          "type": "string"
        },
        "arguments": {
          "additionalProperties": true,
          "title": "Arguments",
          "type": "object"
        }
      },
      "required": [
        "boundary_type",
        "tool_name"
      ],
      "title": "DecisionTrigger",
      "type": "object"
    }
  },
  "additionalProperties": false,
  "properties": {
    "schema_version": {
      "const": "sidecar.audit/1",
      "title": "Schema Version",
      "type": "string"
    },
    "audit": {
      "$ref": "#/$defs/AuditRecord"
    }
  },
  "required": [
    "schema_version",
    "audit"
  ],
  "title": "AuditContract",
  "type": "object"
}
```

---

## Data contract: schemas/v1/decision.schema.json

Source: [schemas/v1/decision.schema.json](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/schemas/v1/decision.schema.json)

```json
{
  "$defs": {
    "Decision": {
      "description": "The outcome of a single Decision Gate evaluation for one proposed\naction (tool call).\n\n`risk` is `None` only on the `on_sidecar_failure` path (core/sidecar.py)\n-- when the Sidecar itself errored before Policy/Risk ever ran, there is\nno risk classification to report, and reporting one would misrepresent\nwhat actually happened.\n\nv0.4 adds provenance fields for audit trail: `decision_point` (which\nboundary fired), `trigger_details` (tool/action + arguments), and\n`causal_link` (correlation to prior decisions). Escalation outcomes\n(PAUSE, ESCALATE) may populate `escalation_required`.\n\nFrozen: a `Decision` is a record of what was decided, not a value meant\nto be mutated after the fact.",
      "properties": {
        "decision_id": {
          "title": "Decision Id",
          "type": "string"
        },
        "status": {
          "enum": [
            "ALLOW",
            "WARN",
            "BLOCK",
            "CHALLENGE",
            "REPLAN",
            "PAUSE",
            "ESCALATE"
          ],
          "title": "Status",
          "type": "string"
        },
        "risk": {
          "anyOf": [
            {
              "enum": [
                "LOW",
                "MEDIUM",
                "HIGH"
              ],
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Risk"
        },
        "reason": {
          "title": "Reason",
          "type": "string"
        },
        "decision_point": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Decision Point"
        },
        "trigger_details": {
          "anyOf": [
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Trigger Details"
        },
        "escalation_required": {
          "default": false,
          "title": "Escalation Required",
          "type": "boolean"
        },
        "causal_link": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Causal Link"
        }
      },
      "required": [
        "status",
        "risk",
        "reason"
      ],
      "title": "Decision",
      "type": "object"
    }
  },
  "additionalProperties": false,
  "properties": {
    "schema_version": {
      "const": "sidecar.decision/1",
      "title": "Schema Version",
      "type": "string"
    },
    "decision": {
      "$ref": "#/$defs/Decision"
    }
  },
  "required": [
    "schema_version",
    "decision"
  ],
  "title": "DecisionContract",
  "type": "object"
}
```

---

## Data contract: schemas/v1/intent.schema.json

Source: [schemas/v1/intent.schema.json](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/schemas/v1/intent.schema.json)

```json
{
  "$defs": {
    "IntentEnvelope": {
      "description": "See concept.md §6 for the worked YAML example this mirrors.\n\nConstraints use explicit ConstraintBindings. Optional AuthorityBindings on\nIntentGuardian enforce boolean task grants with expiry and revocation.\nThe envelope alone does not enforce actions. See the v0.9 guide for the\nnative delegation contract and the distinction from policy rules.",
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "goal": {
          "title": "Goal",
          "type": "string"
        },
        "requested_by": {
          "$ref": "#/$defs/Requester"
        },
        "constraints": {
          "additionalProperties": true,
          "title": "Constraints",
          "type": "object"
        },
        "authority": {
          "additionalProperties": {
            "type": "boolean"
          },
          "title": "Authority",
          "type": "object"
        },
        "expires": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Expires"
        },
        "metadata": {
          "additionalProperties": true,
          "title": "Metadata",
          "type": "object"
        }
      },
      "required": [
        "goal",
        "requested_by"
      ],
      "title": "IntentEnvelope",
      "type": "object"
    },
    "Requester": {
      "description": "Who asked for this -- concept.md §6's `requested_by: {type, id}`.",
      "properties": {
        "type": {
          "default": "human",
          "enum": [
            "human",
            "agent",
            "system"
          ],
          "title": "Type",
          "type": "string"
        },
        "id": {
          "title": "Id",
          "type": "string"
        }
      },
      "required": [
        "id"
      ],
      "title": "Requester",
      "type": "object"
    }
  },
  "additionalProperties": false,
  "properties": {
    "schema_version": {
      "const": "sidecar.intent/1",
      "title": "Schema Version",
      "type": "string"
    },
    "intent": {
      "$ref": "#/$defs/IntentEnvelope"
    }
  },
  "required": [
    "schema_version",
    "intent"
  ],
  "title": "IntentContract",
  "type": "object"
}
```

---

## Data contract: schemas/v1/scope.schema.json

Source: [schemas/v1/scope.schema.json](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/schemas/v1/scope.schema.json)

```json
{
  "$defs": {
    "ConstraintBinding": {
      "description": "Binds one `IntentEnvelope.constraints` entry to a specific tool\nargument so it can be checked deterministically -- a constraint alone\n(e.g. `maximum_refund: 500`) doesn't say which tool call it applies to.\n\nA binding produces a finding when the tool argument does *not* satisfy\n`actual <op> constraint_value`. E.g. `ConstraintBinding(\nconstraint=\"maximum_refund\", tool=\"issue_refund\", arg_name=\"amount\",\nop=\"lte\")` flags any `issue_refund` call whose `amount` exceeds the\nenvelope's `maximum_refund`. A binding for a constraint the active\nenvelope doesn't declare, or a tool call missing the bound argument,\nsimply doesn't match -- same \"no rule matched\" philosophy as\n`gate/policy.py` and `gate/risk.py`.",
      "properties": {
        "constraint": {
          "title": "Constraint",
          "type": "string"
        },
        "tool": {
          "title": "Tool",
          "type": "string"
        },
        "arg_name": {
          "title": "Arg Name",
          "type": "string"
        },
        "op": {
          "default": "lte",
          "enum": [
            "eq",
            "ne",
            "gt",
            "gte",
            "lt",
            "lte",
            "in",
            "contains"
          ],
          "title": "Op",
          "type": "string"
        },
        "severity": {
          "default": "BLOCK",
          "enum": [
            "WARN",
            "BLOCK"
          ],
          "title": "Severity",
          "type": "string"
        },
        "reason": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Reason"
        }
      },
      "required": [
        "constraint",
        "tool",
        "arg_name"
      ],
      "title": "ConstraintBinding",
      "type": "object"
    },
    "ContextSpec": {
      "additionalProperties": false,
      "description": "Agent-visible instructions and structured context, without enforcement.",
      "properties": {
        "goal": {
          "default": "",
          "title": "Goal",
          "type": "string"
        },
        "values": {
          "additionalProperties": true,
          "title": "Values",
          "type": "object"
        },
        "readers": {
          "items": {
            "type": "string"
          },
          "title": "Readers",
          "type": "array",
          "uniqueItems": true
        },
        "expires": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Expires"
        }
      },
      "title": "ContextSpec",
      "type": "object"
    },
    "GuardrailSpec": {
      "additionalProperties": false,
      "description": "A deterministic policy and bound constraints, independent of context.",
      "properties": {
        "rules": {
          "items": {
            "$ref": "#/$defs/PolicyRule"
          },
          "title": "Rules",
          "type": "array"
        },
        "default_effect": {
          "default": "allow",
          "enum": [
            "allow",
            "deny"
          ],
          "title": "Default Effect",
          "type": "string"
        },
        "constraints": {
          "additionalProperties": true,
          "title": "Constraints",
          "type": "object"
        },
        "bindings": {
          "items": {
            "$ref": "#/$defs/ConstraintBinding"
          },
          "title": "Bindings",
          "type": "array"
        }
      },
      "title": "GuardrailSpec",
      "type": "object"
    },
    "PolicyRule": {
      "description": "One allow/deny rule. `tool` is an `fnmatch` glob matched against\n`DecisionContext.tool_name` (e.g. `\"delete_*\"`, `\"*\"`). Rules are\nevaluated in order; the first match wins.",
      "properties": {
        "tool": {
          "title": "Tool",
          "type": "string"
        },
        "effect": {
          "enum": [
            "allow",
            "deny"
          ],
          "title": "Effect",
          "type": "string"
        },
        "reason": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Reason"
        }
      },
      "required": [
        "tool",
        "effect"
      ],
      "title": "PolicyRule",
      "type": "object"
    },
    "ScopeLayer": {
      "additionalProperties": false,
      "description": "Context only, guardrails only, or both at a shared/exclusive scope.",
      "properties": {
        "context": {
          "anyOf": [
            {
              "$ref": "#/$defs/ContextSpec"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "guardrails": {
          "anyOf": [
            {
              "$ref": "#/$defs/GuardrailSpec"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        }
      },
      "title": "ScopeLayer",
      "type": "object"
    }
  },
  "additionalProperties": false,
  "properties": {
    "schema_version": {
      "const": "sidecar.scope/1",
      "title": "Schema Version",
      "type": "string"
    },
    "system_id": {
      "minLength": 1,
      "title": "System Id",
      "type": "string"
    },
    "task_id": {
      "minLength": 1,
      "title": "Task Id",
      "type": "string"
    },
    "agents": {
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "title": "Agents",
      "type": "array"
    },
    "shared": {
      "$ref": "#/$defs/ScopeLayer"
    },
    "exclusive": {
      "additionalProperties": {
        "$ref": "#/$defs/ScopeLayer"
      },
      "title": "Exclusive",
      "type": "object"
    }
  },
  "required": [
    "schema_version",
    "system_id",
    "task_id",
    "agents"
  ],
  "title": "ScopeContract",
  "type": "object"
}
```

---

## Data contract: schemas/v1/transfer.schema.json

Source: [schemas/v1/transfer.schema.json](https://github.com/DeepAgentLabs/agentic-sidecar/blob/main/schemas/v1/transfer.schema.json)

```json
{
  "$defs": {
    "IntentEnvelope": {
      "description": "See concept.md §6 for the worked YAML example this mirrors.\n\nConstraints use explicit ConstraintBindings. Optional AuthorityBindings on\nIntentGuardian enforce boolean task grants with expiry and revocation.\nThe envelope alone does not enforce actions. See the v0.9 guide for the\nnative delegation contract and the distinction from policy rules.",
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "goal": {
          "title": "Goal",
          "type": "string"
        },
        "requested_by": {
          "$ref": "#/$defs/Requester"
        },
        "constraints": {
          "additionalProperties": true,
          "title": "Constraints",
          "type": "object"
        },
        "authority": {
          "additionalProperties": {
            "type": "boolean"
          },
          "title": "Authority",
          "type": "object"
        },
        "expires": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Expires"
        },
        "metadata": {
          "additionalProperties": true,
          "title": "Metadata",
          "type": "object"
        }
      },
      "required": [
        "goal",
        "requested_by"
      ],
      "title": "IntentEnvelope",
      "type": "object"
    },
    "Requester": {
      "description": "Who asked for this -- concept.md §6's `requested_by: {type, id}`.",
      "properties": {
        "type": {
          "default": "human",
          "enum": [
            "human",
            "agent",
            "system"
          ],
          "title": "Type",
          "type": "string"
        },
        "id": {
          "title": "Id",
          "type": "string"
        }
      },
      "required": [
        "id"
      ],
      "title": "Requester",
      "type": "object"
    }
  },
  "additionalProperties": false,
  "description": "Untrusted proposal until a receiving host checks its live parent grant.\n\nBindings come exclusively from the host's parent guardian. The shared\nregistry is required: disconnected replicas cannot prove revocation state.",
  "properties": {
    "schema_version": {
      "const": "sidecar.transfer/1",
      "title": "Schema Version",
      "type": "string"
    },
    "parent_intent_id": {
      "minLength": 1,
      "title": "Parent Intent Id",
      "type": "string"
    },
    "parent_grant_id": {
      "minLength": 1,
      "title": "Parent Grant Id",
      "type": "string"
    },
    "task_id": {
      "minLength": 1,
      "title": "Task Id",
      "type": "string"
    },
    "agent_id": {
      "minLength": 1,
      "title": "Agent Id",
      "type": "string"
    },
    "intent": {
      "$ref": "#/$defs/IntentEnvelope"
    }
  },
  "required": [
    "schema_version",
    "parent_intent_id",
    "parent_grant_id",
    "task_id",
    "agent_id",
    "intent"
  ],
  "title": "IntentTransfer",
  "type": "object"
}
```
