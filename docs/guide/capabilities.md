# Capabilities

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
