"""Optional adapters to sibling DeepAgentLabs projects.

Nothing in `agentic_sidecar`'s core ever imports this package -- each module
here is its own opt-in extra (`pip install agentic-sidecar[agenticlens]` /
`[agentic-chaos]`) and must degrade gracefully (auto-skip in tests) when the
target package isn't installed.

- `agenticlens.py` -- one-way export: Sidecar decisions -> AgenticLens Workflow.
- `agentic_chaos.py` -- two-way, same-run coordination for recovery-decision
  evaluation and chaos-testing the Sidecar's own gate.

Both are placeholders; neither has real code yet.
"""
