"""The `Sidecar` class -- `Sidecar(roles=[...])` and `sidecar.attach(agent)`.

Owns module configuration (which of Policy/Risk/Intent/Critic/Judge/Budget
are enabled) and the required `on_sidecar_failure` setting (`fail_open` /
`fail_closed`, no default -- see README.md and ROADMAP.md's Design
Constraints).

Planned for v0.1 -- see ROADMAP.md. Not implemented yet.
"""
