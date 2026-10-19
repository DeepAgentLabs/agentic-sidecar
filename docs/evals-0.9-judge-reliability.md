# Evals 0.9.0 judge reliability and live resilience

[Agentic Evals 0.9.0](https://github.com/DeepAgentLabs/agentic-evals/releases/tag/v0.9.0) adds judge cost, bounded judge retries with
an explicit *unavailable* outcome, repeated judging with agreement, live-target
retries with per-case `target_status` (`ok`, `timed_out`, `error`), and async
evaluators and targets (`aevaluate_suite`, `arun_live_suite`).

## For Agent Alone vs Agent + Sidecar (Sidecar v0.9)

- `arun_live_suite` awaits `async def` agents, so a supervised async agent can
  be evaluated live without a thread wrapper. Reports keep suite case order and
  match the sync API.
- A Sidecar `BLOCK` or `ESCALATE` that the agent reports as its answer is
  scored like any other output; it is not a target `error`. A target that
  raises because supervision stopped it is recorded as `error` with the
  exception text, so compare those cases deliberately rather than gating them
  away with `max_target_error_cases`.
- Do not retry a supervised refusal into a pass: retries only repeat calls that
  raised or timed out, and `target_attempts` shows when they did.
- An unavailable LLM judgment never passes and fails the Evals default gate, so
  a judge outage cannot make Agent + Sidecar look safer than it is.

Supervision decisions remain Sidecar evidence, separate from scores and release
gates. Evals scores observations; it does not prove containment. No runtime
dependency or Sidecar release is introduced. See the [Evals guide](https://github.com/DeepAgentLabs/agentic-evals/blob/v0.9.0/docs/judge-reliability.md).
