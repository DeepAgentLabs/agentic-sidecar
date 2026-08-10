"""Framework adapters -- the `before_tool_call` / decision-boundary
interception point for each supported agent framework.

`langgraph.py` is the only adapter planned for v0.1. Do not start a second
adapter before it is done and stable -- the interception abstraction needs
to survive contact with one real framework first (ROADMAP.md's Design
Constraint 1). The other four are placeholders for v0.6.
"""
