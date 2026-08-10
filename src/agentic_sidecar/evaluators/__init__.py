"""Planner, Critic, and Judge -- independent evaluation of a proposed plan
or decision.

Unlike `gate/` (Policy, Risk), these modules may call an LLM, and it should
never be the same model/provider as the Main Agent by default (see
README.md § Sidecar modules -- model independence). All three stay optional
and off by default (`judge.enabled: false`) given the cost/latency
tradeoff.

Planner evaluates the whole plan; Critic challenges one decision at a time;
Judge is the pluggable model-agnostic scoring interface both can call into.

Planned for v0.3 -- see ROADMAP.md. Not implemented yet.
"""
