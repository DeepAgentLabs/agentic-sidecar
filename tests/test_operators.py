"""Tests for `agentic_sidecar.core.operators.compare`."""

import pytest

from agentic_sidecar.core.operators import compare


@pytest.mark.parametrize(
    ("actual", "op", "expected", "result"),
    [
        (500, "eq", 500, True),
        (500, "eq", 501, False),
        (500, "ne", 501, True),
        (500, "ne", 500, False),
        (850, "gt", 500, True),
        (500, "gt", 500, False),
        (500, "gte", 500, True),
        (100, "gte", 500, False),
        (100, "lt", 500, True),
        (500, "lt", 500, False),
        (500, "lte", 500, True),
        (850, "lte", 500, False),
        ("offshore-1", "in", ["offshore-1", "offshore-2"], True),
        ("onshore", "in", ["offshore-1", "offshore-2"], False),
        ("prod-db-1", "contains", "prod", True),
        ("dev-db-1", "contains", "prod", False),
    ],
)
def test_compare_operators(actual: object, op: str, expected: object, result: bool) -> None:
    assert compare(actual, op, expected) is result  # type: ignore[arg-type]


def test_type_mismatch_returns_false_instead_of_raising() -> None:
    assert compare("not-a-number", "gt", 500) is False


def test_unhashable_or_wrong_container_for_in_returns_false() -> None:
    assert compare(500, "in", None) is False


def test_contains_on_non_container_returns_false() -> None:
    assert compare(500, "contains", "prod") is False
