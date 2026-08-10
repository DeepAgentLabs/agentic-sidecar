"""Smoke test for the repository scaffold.

There is no module-level behavior to test yet -- once a module in
src/agentic_sidecar/ gets real code (see ROADMAP.md for the build order),
add tests/test_<module>.py alongside it instead of extending this file.
"""

from agentic_sidecar import __version__


def test_version_is_set() -> None:
    assert __version__
