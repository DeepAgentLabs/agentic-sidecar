"""Sidecar runtime: `Sidecar`, `Decision`, `DecisionContext`, the shared
comparator vocabulary (`operators.py`), and `SidecarBlockedError`
(`exceptions.py`) -- the primitives every adapter
(`agentic_sidecar.adapters`) and Decision Gate module
(`agentic_sidecar.gate`, `agentic_sidecar.intent`) is built on.

Implemented as of v0.1 (Sidecar, Decision, DecisionContext) and v0.2
(Govern mode, `operators.py`, `exceptions.py`) -- see ROADMAP.md. `core/`
must not import from `adapters/` (AGENTS.md's Package Boundaries): adapters
route a specific framework's decision boundaries through
`Sidecar.evaluate()`, not the other way around. `core/` *does* import from
`gate/` and `intent/` directly (Sidecar wires in Policy Advisor, Risk
Evaluator, and Intent Guardian as built-in modules), which is the expected
direction -- those are Decision Gate modules Sidecar orchestrates, not
alternate entry points the way adapters are.
"""
