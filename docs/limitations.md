# Limitations

This page lists what the current Agentic Sidecar release (1.0.x) does not do,
so you can plan around it. The package is early-stage (PyPI classifier:
Pre-Alpha), and native contract schemas remain candidates. Planned improvements
appear in [Roadmap](roadmap.md). Topic guides list further limits for their own
features.

---

## Enforcement boundary

### Observe mode does not block

Observe computes and records verdicts, then executes the wrapped call anyway.
Only Govern mode enforces: ALLOW/WARN execute, BLOCK raises
`SidecarBlockedError`, and PAUSE/ESCALATE/CHALLENGE/REPLAN raise
`SidecarSuspendedError` when unresolved. `evaluate()` alone never stops a call.

### Only returned tools are governed

Adapters protect the tool objects they return. Prebuilt SDK tools, automatic
handoffs, raw functions the agent can still reach, nested calls, prompts,
memory and outputs are not intercepted automatically. Pass only the returned
tools to the agent and keep raw tools in the trusted host.

### Not a sandbox

In-process Python wrappers are not process isolation. They cannot contain
hostile code running in the same process. For containment, run protected tools
and credentials in an enforcing service under a separate identity; the
[MCP gateway example](examples.md) shows a separate-process boundary.

### Suspension is not workflow control

The suspension exceptions prevent one tool call. They do not checkpoint,
resume or replan the whole agent workflow; your harness owns retries and
replanning.

---

## Failure policy

### `fail_open` can permit failed evaluations

`on_sidecar_failure` has no default. With `fail_open`, an evaluator, provider,
validation or recording failure resolves to ALLOW. A recorder failure after a
genuine BLOCK therefore resolves to ALLOW under `fail_open` and to BLOCK under
`fail_closed`, and the audit entry may be missing. Use Govern with
`fail_closed` for containment.

### Custom hooks replace the built-in stages

A `before_tool_call` hook replaces the optional pipeline, including policy,
risk, intent, plan checks, budget and evaluators. Authority checks, the stop
latch and mandatory scoped checks still run, and hooks cannot rewrite the
proposed action.

---

## Intent and evaluators

### Intent checks are explicit, not semantic

The Intent Guardian checks constraints bound to tool arguments. A goal string
alone is not enforced, and absent constraints or arguments are skipped. Intent
drift is caught only where a constraint is bound. Expiry produces WARN for
constraint-only envelopes; authority-bearing envelopes expire with BLOCK.

### Planner and Critic are heuristics

`evaluate_plan()` checks the step dictionaries you supply; it does not discover
or execute the agent's plan. Planner and Critic use selected tool and goal
patterns, contradictory tool pairs and caller-supplied evidence flags
(`authorized`, `eligibility_verified`, `backup_verified`). These flags are
assertions, not verified authorization, and the heuristics are not a proof of
correctness.

### Risk classification is rule-based

The Risk Evaluator classifies tool and argument patterns. It is not a learned
risk model and only knows the rules you configure.

---

## Judges and budgets

### Live judges need your credentials and rates

`OpenAIJudge` and `AnthropicJudge` make real SDK calls with a model and token
rates you configure. `MockJudge` is an offline fixture and is never substituted
silently. Authenticated live-provider smoke results remain pending credentials.

### Cost limits apply after a response

Judge cost limits cannot reserve future spend. A synchronous provider call
cannot be cancelled at timeout and may still finish and account usage. Unknown
usage is never invented as a cost.

### Budgets count only what is recorded

Judge usage reaches the task budget automatically. Other framework or tool usage
must be recorded with `record_invocation()`; it is not inferred.

---

## Human in the loop

### One approval, one invocation

APPROVE_ONCE authorizes the current unchanged invocation only. BLOCK is never
offered for approval. MODIFY_INTENT needs a complete constraint-only envelope;
authority-bearing intents require explicit re-delegation by the harness.
Waiting for an approval times out into REPLAN.

### Async waiting runs in a worker thread

Async tools run evaluation and approval in a worker thread so the event loop
is not blocked. Cancelling the waiting coroutine cannot cancel a running
synchronous evaluator or prompt.

---

## Live operations and emergency stop

### Stop cannot undo dispatched work

Stop blocks all future dispatch, but already-dispatched synchronous calls may
finish and keep their side effects. Async cancellation is cooperative; a tool
can suppress it.

### Revocation is host-owned

Credential, MCP, session and delegation access belong to their issuer.
Revocation happens only through the `TaskRuntime(revokers=...)` callbacks you
supply. `access_revocation: not_configured` confirms only the local dispatch
stop. Restart does not renew credentials or task authority.

### Operator server is local only

`OperatorServer` binds to `127.0.0.1` with one task, one token and one actor.
There is no TLS, public deployment, CORS access or multi-tenant isolation.
`status --follow --json` prints formatted snapshots, not JSONL.

### Control Tower acknowledgements are bounded

A fleet-wide stop acknowledgement through Control Tower confirms the Sidecar
boundary, not end-to-end containment. In-flight calls and downstream
credentials are reported separately, and there is no fleet atomicity,
automatic rollback or automatic restart. See
[Control Tower integration](control-tower-integration.md#limits).

---

## Audit and records

### Hash chains need an external anchor

The event journal detects alteration relative to the supplied chain. Resisting a
full malicious rewrite requires an external trusted anchor.

### Records can contain sensitive data

Journals, decision records and correlation projections can contain tool
arguments, intent context and reasons. Protect their storage. Redacted summaries
cannot replace native decisions or a verifiable journal.

### In-memory decisions are mutable

`sidecar.decisions` holds deep copies made at recording time, but the list and
its nested dictionaries remain mutable. Use the runtime journal for durable,
immutable lifecycle evidence. `AuditRecord` is a caller-created export type.

---

## Scopes, authority and contracts

### Context delivery is explicit

Scoped context is delivered only through `context()` / `deliver()`. Private text
is not automatically enforcement policy or evaluator input. Expiry and
revocation block future reads but cannot retract copies already delivered.

### Identity comes from the host

Agent IDs, readers, actors, grants and the authority registry must be supplied
by the authenticated host. Revocation does not undo execution already reserved.

### Contracts and transfers grant nothing on their own

The five native schemas are candidates, not frozen. An `IntentTransfer`
proposal is not a signed credential, approval or resumable task; replay
prevention and registry replication across instances are host responsibilities.
Semantica export is reserved and not implemented.

---

## Evidence and benchmarks

### Benchmarks are synthetic

The 24-run supervision benchmark uses synthetic tools with zero token and cost
values. It does not establish live-provider benefit, statistical confidence or
economic savings.

---

## AIOS conformance

### Draft specification

The AI Operations Specification is a draft. AIOS audit projections are draft
operational artifacts, and package versions do not certify AIOS conformance or
production deployment readiness.

---

## Platform

### Python 3.10+ required

Agentic Sidecar supports Python 3.10 to 3.13. Optional framework and provider
adapters follow the SDK versions listed in [Integrations](integrations.md).
