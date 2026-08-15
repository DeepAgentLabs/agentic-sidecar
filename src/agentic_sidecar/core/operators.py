"""Shared comparison-operator vocabulary.

Used by both `gate/risk.py`'s argument-pattern rules (v0.1) and
`intent/alignment.py`'s constraint bindings (v0.2) so the two don't
duplicate identical comparator logic -- both ultimately answer the same
question ("does this tool argument satisfy this comparison against this
value?"), just for different callers.
"""

from __future__ import annotations

from typing import Any, Literal

ArgOp = Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"]


def compare(actual: Any, op: ArgOp, expected: Any) -> bool:
    """Evaluate `actual <op> expected`.

    Never raises: a type mismatch (e.g. comparing a string argument with
    `gt`) returns `False` rather than propagating a `TypeError` -- a
    malformed rule or an unexpectedly-typed argument shouldn't crash the
    Decision Gate (see core/sidecar.py's `on_sidecar_failure` for the
    analogous handling one layer up).
    """
    try:
        if op == "eq":
            return bool(actual == expected)
        if op == "ne":
            return bool(actual != expected)
        if op == "gt":
            return bool(actual > expected)
        if op == "gte":
            return bool(actual >= expected)
        if op == "lt":
            return bool(actual < expected)
        if op == "lte":
            return bool(actual <= expected)
        if op == "in":
            return bool(actual in expected)
        if op == "contains":
            return bool(expected in actual)
    except TypeError:
        return False
    return False
