"""LangGraph interception adapter -- the first and, until it's proven out,
only decision-boundary hook (ROADMAP.md's Design Constraint 1).

`attach()` wraps a list of tool callables -- the same list you'd otherwise
hand to `langgraph.prebuilt.create_react_agent(model, tools=...)` -- so that
every invocation is evaluated by a `Sidecar` first. This module has no
import-time dependency on the `langgraph` package itself: it only relies on
LangGraph/LangChain's convention that a tool is a plain callable with a
stable `__name__` and a type-annotated signature, which is exactly what
`create_react_agent` accepts without an explicit `@tool` decorator. Install
`agentic-sidecar[langgraph]` to actually build and run a graph around the
wrapped tools (see `examples/`).

In `sidecar.mode="observe"` (v0.1's only mode, still the default), the
wrapped tool always calls through to the real tool regardless of
`Decision.status` -- the Sidecar's verdict is only computed and recorded
(`sidecar.decisions`). In `mode="govern"` (v0.2+), a `BLOCK` verdict raises
`SidecarBlockedError` instead of calling the real tool; `ALLOW` and `WARN` both
still call through -- `WARN` is advisory, not a stop signal (see README.md's
Operating modes).
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.core.exceptions import SidecarBlockedError
from agentic_sidecar.core.sidecar import Sidecar

F = TypeVar("F", bound=Callable[..., Any])


def attach(sidecar: Sidecar, tools: Sequence[F]) -> list[F]:
    """Wrap each tool in `tools` so calling it first runs `sidecar.evaluate()`.

    Returns a new list in the same order -- pass it straight to
    `create_react_agent(model, tools=attach(sidecar, tools))`. Does not
    mutate the input list or the original tool callables.
    """
    return [_wrap_tool(sidecar, tool) for tool in tools]


def _wrap_tool(sidecar: Sidecar, tool: F) -> F:
    signature = inspect.signature(tool)
    tool_name = getattr(tool, "__name__", repr(tool))

    @functools.wraps(tool)
    def _sidecar_wrapped_tool(*args: Any, **kwargs: Any) -> Any:
        context = DecisionContext(
            tool_name=tool_name,
            tool_args=_bind_args(signature, args, kwargs),
        )
        decision = sidecar.evaluate(context)
        # Enforcement only exists in Govern mode -- Observe mode (v0.1's
        # only mode, still the default) always calls through regardless of
        # `decision.status`. `WARN` never stops the call in either mode.
        if sidecar.mode == "govern" and decision.status == "BLOCK":
            raise SidecarBlockedError(decision, context)
        return tool(*args, **kwargs)

    return _sidecar_wrapped_tool  # type: ignore[return-value]


def _bind_args(
    signature: inspect.Signature, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    try:
        bound = signature.bind(*args, **kwargs)
    except TypeError:
        # A call that doesn't match the tool's declared signature shouldn't
        # crash the Decision Gate -- fall back to raw kwargs (positional
        # args are lost in this case, but LangGraph's ToolNode always calls
        # tools with keyword arguments derived from the model's structured
        # tool call, so this path is a defensive fallback, not the norm).
        return dict(kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)
