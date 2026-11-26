# Recommended workflow

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
