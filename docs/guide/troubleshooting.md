# Troubleshooting

Check the failing boundary before changing application behavior.

- A blocked verdict but a running tool: check whether you called `evaluate()` only or used Observe mode.
- Wrong rule matched: inspect policy order and the callable's tool name.
- Agent hangs on approval: inspect the approval handler and unresolved decision status.

## Verify your environment

Run commands from the environment where you installed the package. Confirm the input file exists and matches the expected artifact contract. Keep the original evidence when diagnosing a failure.
