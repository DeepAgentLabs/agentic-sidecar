# Agentic Sidecar

Should this proposed action proceed right now, given what the user actually asked for?

The Main Agent acts. The Sidecar observes, evaluates, advises and governs each
proposed tool call or plan step before it executes.

## What it does

Pre-action supervision for autonomous agents, grouped by area below. Each area
links to its detailed guide; for runnable code, see the
[developer guide](developer-guide.md).

### 1. Intent and context

- **Intent Envelope**
    - Goal, requester and constraints for the task (for example `maximum_refund: 500`)
    - Optional timezone-aware expiry: an expired envelope produces WARN, or BLOCK when it carries authority
- **Constraint bindings**
    - Bind each constraint to a tool argument (`amount <= maximum_refund` on `issue_refund`)
    - Operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `contains`
- **Intent Guardian**
    - Checks every step against the bound constraints
    - Catches intent drift: a permitted tool used beyond what the user authorized
- **Changing intent**
    - Replace the active intent with `set_intent()`
    - Modify intent during an approval; earlier verdicts are invalidated
- **Task history**
    - Intent and history are injected into each decision, across the whole task

Guides: [Features](features.md) · [Configuration](configuration.md)

### 2. Shared and exclusive scopes

- **Shared scope (generic)**
    - Context and guardrails that apply to every agent in the system
- **Exclusive scope (specific)**
    - Context and guardrails for one agent; exclusive allows cannot weaken shared denies
- **Context**
    - `ContextSpec`: goal and values the agent can see
    - Explicit delivery with `context()` / `deliver()`
- **Guardrails**
    - `GuardrailSpec`: policies and constraint bindings enforced separately from context
    - Every applicable layer must pass; deny wins
    - Mandatory checks run before custom hooks and cannot be bypassed by tool arguments
- **Privacy and lifecycle**
    - Authorized readers, defensive copies, update, expiry and revocation
    - Redacted evidence summaries that exclude private arguments, goals and plans

Guides: [Scoped supervision](scoped-supervision.md) ·
[Authority and privacy](v0.9.md#context-privacy-and-readers)

### 3. Guardrails (Decision Gate checks)

- **Policy Advisor**
    - Ordered allow/deny rules on tool-name globs, from YAML or Python
    - Deterministic, zero LLM calls; runs first
- **Risk Evaluator**
    - LOW / MEDIUM / HIGH classification from tool and argument rules
    - `risk_block_threshold` sets when the gate intervenes
- **Budget Guardian**
    - Cost and token ceilings per task
    - Manual usage records plus automatic Judge usage; reaching a ceiling pauses
- **Task authority**
    - Explicit tool grants through `AuthorityBinding`
    - Delegation that can only narrow permissions
    - Ancestor revocation and expiry checked at dispatch time
- **Failure policy**
    - `on_sidecar_failure` is required: `fail_closed` or `fail_open`

Guides: [Configuration](configuration.md) · [Governance](governance.md) ·
[Task authority](v0.9.md#task-authority-and-delegation)

### 4. Evaluators (optional)

- **Planner**
    - Reviews a full supplied plan before execution; can return REPLAN
- **Critic**
    - Challenges unsafe actions, contradictions and unsupported assumptions
- **Judge**
    - Independent model evaluation: `MockJudge` offline, OpenAI or Anthropic live
    - Validated verdicts, timeouts, cost limits and usage accounting
- **Custom hooks**
    - `before_tool_call` replaces the optional pipeline; mandatory checks still apply

Guides: [Governance and evaluators](governance.md) · [Features](features.md)

### 5. Decisions and operating modes

- **Seven outcomes**
    - ALLOW, WARN, CHALLENGE, REPLAN, PAUSE, BLOCK, ESCALATE
- **Observe mode**
    - Computes and records verdicts; wrapped calls still execute
- **Govern mode**
    - ALLOW/WARN execute; BLOCK raises `SidecarBlockedError`
    - PAUSE/ESCALATE request approval; CHALLENGE/REPLAN raise `SidecarSuspendedError`
- **Dry run**
    - `evaluate()` and `evaluate_plan()` return a verdict without dispatching a tool

Guides: [Governance](governance.md) · [API reference](api-reference.md#sidecar)

### 6. Human in the loop

- **Approval requests**
    - PAUSE and ESCALATE wait for a human decision
- **Where to approve**
    - Terminal (`CLIApprovalHandler`), Control Room, HTTP or `agentic-sidecar approve`
- **Approval actions**
    - Approve once, reject, modify intent, ask the agent to replan, stop the agent
    - BLOCK is never offered for approval
- **Safety**
    - Approval binds to the decision ID and one unchanged invocation
    - Replayed or duplicate answers are rejected; waiting times out into REPLAN
- **Notifications**
    - `on_escalation_required` callbacks

Guides: [Approvals](guide/approvals.md) · [Governance](governance.md#local-approval-flow)

### 7. Live view and control

- **Control Room**
    - Authenticated local web page: objective, plan, intent findings, risk, budget,
      action lifecycle, pending approvals and audit events
- **Task controls**
    - Pause, resume, replan, stop and restart
    - Available from the Control Room, the CLI, HTTP and `runtime.control()`
- **CLI**
    - `status --follow`, `control`, `approve`, `demo`, `approval-demo`, `version`
- **Narration**
    - Raw tool and MCP traces translated into human-readable status

Guides: [Live operations](live-operations.md) · [CLI reference](cli-reference.md)

### 8. Emergency stop

- **Latches first**
    - Takes effect before audit writes or callbacks, in Observe and Govern, regardless of failure policy
- **Halts dispatch**
    - Queued proposals and approval retries cannot dispatch; earlier ALLOWs are invalidated
- **Cancels and revokes**
    - Cancellation requests for owned async calls
    - Task authority revoked and configured revokers called (for example MCP access)
- **Robust**
    - A broken audit sink cannot prevent revocation
    - A restored runtime comes back stopped and needs an explicit restart

Guides: [Emergency stop](control-tower-integration.md#emergency-stop) ·
[Stop and revocation](live-operations.md#stop-cancellation-and-access-revocation)

### 9. Audit and provenance

- **Decision records**
    - Trigger, rationale and causal links for every decision
- **Event journal**
    - Hash-chained events with optional durable JSONL; `verify_events()` checks the chain
- **Restoration**
    - Reopen a journal to restore a task in a stopped state
- **Exports**
    - Five native contracts: intent, decision, audit, scope and transfer
    - Correlated decision projections and AIOS operational audit artifacts

Guides: [Live operations](live-operations.md#audit-snapshots-and-restoration) ·
[Contracts](v0.10.md) · [AIOS export](aios-0.8-operational-artifacts.md)

### 10. Framework adapters

- **Frameworks**
    - LangGraph, AutoGen, CrewAI, OpenAI Agents and Google ADK
- **Tools**
    - MCP tools on an initialized client session
    - Plain sync/async Python callables
- **Boundary**
    - Pass only the returned governed tools to the agent

Guides: [Integrations](integrations.md#framework-adapters) ·
[API reference](api-reference.md#other-framework-adapters)

### 11. Ecosystem interoperability

- **Control Tower**
    - Fleet view: inventory, alerts and incident console with joined Sidecar evidence
    - Fleet-wide stop through `SidecarContainmentAdapter` with separate human approval
    - Runbooks still use the Sidecar for emergency stop and restart
- **AgenticLens**
    - Attach correlated decisions to exact Lens run, trace and span IDs
- **Agentic Chaos**
    - Evaluate recovery proposals linked to injected fault events
- **Agentic Evals**
    - Score supervision evidence from offline benchmark fixtures
- **AIOS**
    - Project native audit records into draft operational artifacts

Guides: [Control Tower integration](control-tower-integration.md) ·
[Integrations](integrations.md)

## What you need

Proposed tool actions, policy rules, intent constraints and, optionally,
recorded budgets and an approval handler.

## Start here

Compute a deny verdict, then demonstrate governed execution:
[follow the quickstart](developer-guide.md#quickstart).

## Limits

- `evaluate()` produces a verdict; enforcement needs Govern mode and the returned governed tools.
- Observe mode never blocks execution.
- Stop cannot undo side effects of calls that were already dispatched.
- Wrappers do not sandbox hostile code or govern unwrapped functions, prompts or nested calls.
- The operator server is loopback-only; there is no TLS or public deployment.

See [Limitations](limitations.md).

## Documentation

- [Developer Guide (simple)](developer-guide.md): short task workflows and a capability index
- [API Reference (detailed)](api-reference.md): exact Python classes, parameters and return values
- [AI Readable Documentation](ai-reference-index.md): the full reference as one file for AI tools, with source declarations and schemas
