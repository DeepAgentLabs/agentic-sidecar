"""LangGraph interception adapter -- the first and, until it's proven out,
only decision-boundary hook. LangGraph was chosen as the starting framework
because its explicit graph/node structure gives `before_tool_call`-style
interception the clearest place to attach.

Planned for v0.1 -- see ROADMAP.md. Not implemented yet.
"""
