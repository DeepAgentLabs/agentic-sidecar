"""`IntentEnvelope` -- goal, requester, constraints, granted/denied
authority, and expiry (see README.md § Sidecar modules for the YAML shape).

When this is actually designed, account for the v1.0 target of publishing
it as a cross-project interoperability schema (README.md's "Long-term: an
intent propagation layer") -- e.g. a `parent_intent_id` for delegation
chains -- even though nothing consumes that field until v1.0.

Planned for v0.2 -- see ROADMAP.md. Not implemented yet.
"""
