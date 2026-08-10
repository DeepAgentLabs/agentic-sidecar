"""Intent Guardian -- structured IntentEnvelope, intent injection at decision
boundaries, drift detection, and constraint validation.

Answers "is this actually what the human asked you to accomplish?" -- the
project's actual differentiator (see README.md's "How the Decision Gate
evaluates a decision"). Keep this module's checks semantic, not a
permission list in disguise; static allow/deny checks belong in
`gate/policy.py` instead (ROADMAP.md's Design Constraint 5).

Planned for v0.2 -- see ROADMAP.md. Not implemented yet.
"""
