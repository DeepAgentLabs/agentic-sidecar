"""Critic and Judge -- independent evaluation of a proposed plan or decision.

Unlike `gate/` (Policy, Risk), these modules may call an LLM, and it should
never be the same model/provider as the Main Agent by default (see
README.md § Sidecar modules -- model independence). Both stay optional and
off by default (`judge.enabled: false`) given the cost/latency tradeoff.

Planned for v0.3 -- see ROADMAP.md. Not implemented yet.
"""
