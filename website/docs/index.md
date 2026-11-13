# Agentic Sidecar

## Agentic Sidecar overview

Should this proposed action proceed under the declared policy and intent?

Proposed tool actions, policy rules, intent constraints, and recorded budgets. Decision records and adapter-mediated allow, block, or escalation behavior.

**When to start here**

Compute a deny verdict, then demonstrate governed execution.

## Inputs and outputs

| You provide | You receive |
| --- | --- |
| Proposed tool actions, policy rules, intent constraints, and recorded budgets. | Decision records and adapter-mediated allow, block, or escalation behavior. |

## Execution boundary

evaluate() produces a verdict. Actual enforcement requires the caller or a governed adapter; Observe mode does not block execution.

[Start the Agentic Sidecar quickstart →](guide/quickstart.md)

## Capabilities

Use these capabilities to address supervise tasks in your application.

| Capability | What it provides |
| --- | --- |
| Policy and risk | Match tool names and argument patterns against deterministic rules. |
| Intent constraints | Bind a declared task constraint to specific tool arguments. |
| Budget tracking | Track recorded cost/tokens and react to configured ceilings. |
| Plan, critic, and judge modules | Enable heuristic checks or explicitly configured live model evaluation. |
| Governed dispatch | Resolve, block, or suspend actions at a tool boundary. |
| Scoped supervision | Compose shared and exclusive context or guardrails according to declared scope. |

## Supported scope

evaluate() produces a verdict. Actual enforcement requires the caller or a governed adapter; Observe mode does not block execution.

## Core concepts

| Concept | Meaning |
| --- | --- |
| DecisionContext | Describes the proposed action before execution. |
| Observe | Records decisions while wrapped calls can still execute. |
| Govern | Enforces decisions at dispatch: proceed, block, resolve, or suspend as configured. |
| Role activation | Supplying a module is not sufficient if its role is not enabled. |
| Failure policy | Explicitly decide whether an error in supervision fails open or closed. |
| Intent lifecycle | Bind constraints to the current task, replace intent between tasks, and manage budgets separately. |

## Recommended workflow

## Start with an explicit policy

Match the actual tool name and arguments. Verify allowed and denied examples before connecting the wrapper to an agent.

## Enable the necessary roles

The default roles cover policy and risk. Intent, budget, plan, critic, and judge modules must be configured and enabled explicitly.

## Observe before enforcing

Observe mode helps inspect verdicts, but it is not blocking. Use Govern when the result should control dispatch and verify that the underlying callable was not invoked on a blocked case.

## Resolve approval outcomes

Govern permits ALLOW/WARN, blocks BLOCK, and uses configured resolution for PAUSE/ESCALATE. Unresolved outcomes and CHALLENGE/REPLAN suspend execution. Do not interpret a pending approval as permission to run.

## Manage task boundaries

Update the active intent for the new task and record actual usage in the relevant budget. Inspect scoped context and guardrail delivery when multiple agents participate.

## Next steps

Compute a deny verdict, then demonstrate governed execution.

[Open the developer quickstart →](guide/quickstart.md)
