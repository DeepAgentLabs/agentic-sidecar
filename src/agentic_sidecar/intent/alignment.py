"""Intent-drift detection and constraint validation -- is the current
proposed action still consistent with the active IntentEnvelope's goal,
constraints, and granted authority?

Deterministic where possible (e.g. `proposed_refund > envelope.constraints.maximum_refund`)
so this stays checkable without an LLM -- see the v0.2.x Early Validation
Benchmark in ROADMAP.md, which measures exactly this module's catch rate.

Planned for v0.2 -- see ROADMAP.md. Not implemented yet.
"""
