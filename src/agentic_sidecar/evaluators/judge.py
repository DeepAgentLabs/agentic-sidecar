"""Model-agnostic LLM Judge interface.

Main Agent model and Sidecar Judge model must be independently swappable --
at least two provider backends should exist to prove this isn't just a
wrapper around whichever SDK is imported first (README.md § Sidecar
modules, "model independence").

Planned for v0.3 -- see ROADMAP.md. Not implemented yet.
"""
