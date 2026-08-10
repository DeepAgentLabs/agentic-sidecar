"""Optional AgenticLens adapter -- surfaces Sidecar Decision events
(allow/warn/replan/block, intent-alignment score) as AgenticLens `Workflow`
step data, so `agenticlens analyze` can report on them alongside cost and
latency. Expected shape: an `attach_events()` / `step_kwargs()`-style pair --
one call to merge a completed Sidecar session onto a `Workflow`, one helper
to pass Sidecar's own step correlation IDs through cleanly.

Not core-dependency: `agentic_sidecar`'s runtime never imports this module
on its own. Requires `pip install agentic-sidecar[agenticlens]`.

Not yet scheduled to a specific ROADMAP version -- see ROADMAP.md's
Cross-Project Dependencies (`agenticlens`: "Validate in"). Not implemented
yet.
"""
