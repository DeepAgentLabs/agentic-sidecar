"""Optional Agentic Chaos coordination.

Unlike the AgenticLens adapter (a one-way export after the fact, merging a
completed Sidecar session onto a `Workflow`), this is a two-way, same-run
relationship: Agentic Chaos and the Sidecar both attach to the *same* agent
invocation. Agentic Chaos injects a fault; the Sidecar's Decision Gate
evaluates the agent's recovery attempt through its normal Policy/Risk/Intent
checks, answering not just "did it recover?" but "was the recovery decision
itself appropriate?".

Also relevant in the other direction: chaos-testing the Sidecar's own gate
by injecting a fault into the Sidecar's evaluation path itself, to verify
`on_sidecar_failure` (`fail_open` / `fail_closed`) behaves as configured
when the Sidecar times out or errors.

The concrete integration surface -- what this module reads from an active
chaos session, what it reports back, and whether that needs a shared schema
the way the AgenticLens adapter does -- isn't designed yet. See
ROADMAP.md's Cross-Project Dependencies (`agentic-chaos`: "Coordinate
with").

Not core-dependency: `agentic_sidecar`'s runtime never imports this module
on its own. Requires `pip install agentic-sidecar[agentic-chaos]`.

Not yet scheduled to a specific ROADMAP version. Not implemented yet.
"""
