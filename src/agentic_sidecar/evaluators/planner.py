"""Planner -- independently evaluates the Main Agent's *plan*, before
individual decisions within it reach the Decision Gate.

Distinct from Critic (critic.py), which challenges a single proposed
decision right before it executes: Planner looks at the whole multi-step
plan against the active IntentEnvelope and flags steps that exceed what
was actually asked for (e.g. the user requested an explanation, the plan
includes a cancellation and a refund -- see the DEV/production-cleanup and
"explain my charge" examples this mirrors). Its output feeds the
`CHALLENGE` / `REPLAN` Decision Gate outcomes the same way Critic's does.

Planned for v0.3, alongside Critic and Judge -- like both, it requires real
reasoning rather than a deterministic check, so it doesn't ship until v0.1/
v0.2's LLM-free phase is done (see ROADMAP.md's Design Constraint 2).

Not implemented yet.
"""
