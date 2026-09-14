"""Status Interpreter -- translates raw tool/MCP traces into human-readable
live narration (e.g. "Looking up your order" instead of `GET /orders/182`).

v0.5 implements the StatusNarrator class and supporting types. CLI and Control
Room dashboard integration follow in v0.5+. See ROADMAP.md.
"""

from agentic_sidecar.status.narrate import (
    StatusNarrative,
    StatusNarrator,
    ToolCallNarrative,
)

__all__ = ["StatusNarrative", "StatusNarrator", "ToolCallNarrative"]
