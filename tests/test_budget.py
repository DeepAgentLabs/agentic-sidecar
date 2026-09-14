"""Tests for `agentic_sidecar.gate.budget.BudgetGuardian`."""

import pytest

from agentic_sidecar.gate.budget import BudgetGuardian, BudgetResult


def test_budget_guardian_tracks_cost() -> None:
    guardian = BudgetGuardian(max_cost=10.0)
    assert guardian.current_cost == 0.0
    guardian.record_invocation(cost=2.5)
    assert guardian.current_cost == 2.5
    guardian.record_invocation(cost=1.5)
    assert guardian.current_cost == 4.0


def test_budget_guardian_tracks_tokens() -> None:
    guardian = BudgetGuardian(max_cost=10.0, max_tokens=1000)
    assert guardian.current_tokens == 0
    guardian.record_invocation(cost=1.0, tokens=100)
    assert guardian.current_tokens == 100
    guardian.record_invocation(cost=2.0, tokens=250)
    assert guardian.current_tokens == 350


def test_budget_not_exceeded_when_under_limit() -> None:
    guardian = BudgetGuardian(max_cost=10.0)
    guardian.record_invocation(cost=5.0)
    result = guardian.evaluate()
    assert result.exceeded is False
    assert result.remaining_cost == 5.0


def test_budget_exceeded_when_over_cost_limit() -> None:
    guardian = BudgetGuardian(max_cost=10.0)
    guardian.record_invocation(cost=10.5)
    result = guardian.evaluate()
    assert result.exceeded is True
    assert "cost" in result.reason


def test_budget_exceeded_when_over_token_limit() -> None:
    guardian = BudgetGuardian(max_cost=10.0, max_tokens=1000)
    guardian.record_invocation(cost=5.0, tokens=1500)
    result = guardian.evaluate()
    assert result.exceeded is True
    assert "tokens" in result.reason


def test_budget_exceeded_reports_both_limits() -> None:
    guardian = BudgetGuardian(max_cost=5.0, max_tokens=100)
    guardian.record_invocation(cost=10.0, tokens=500)
    result = guardian.evaluate()
    assert result.exceeded is True
    assert "cost" in result.reason
    assert "tokens" in result.reason


def test_remaining_budget_calculation() -> None:
    guardian = BudgetGuardian(max_cost=10.0, max_tokens=1000)
    guardian.record_invocation(cost=3.5, tokens=300)
    result = guardian.evaluate()
    assert result.remaining_cost == 6.5
    assert result.remaining_tokens == 700


def test_remaining_budget_never_negative() -> None:
    guardian = BudgetGuardian(max_cost=5.0)
    guardian.record_invocation(cost=10.0)
    result = guardian.evaluate()
    assert result.remaining_cost == 0.0


def test_is_at_capacity_when_exceeded() -> None:
    guardian = BudgetGuardian(max_cost=5.0)
    guardian.record_invocation(cost=5.0)
    assert guardian.is_at_capacity() is True


def test_is_at_capacity_when_not_exceeded() -> None:
    guardian = BudgetGuardian(max_cost=10.0)
    guardian.record_invocation(cost=5.0)
    assert guardian.is_at_capacity() is False


def test_reset_clears_tracking() -> None:
    guardian = BudgetGuardian(max_cost=10.0, max_tokens=1000)
    guardian.record_invocation(cost=5.0, tokens=500)
    guardian.reset()
    assert guardian.current_cost == 0.0
    assert guardian.current_tokens == 0
    result = guardian.evaluate()
    assert result.exceeded is False


def test_budget_with_no_token_limit() -> None:
    guardian = BudgetGuardian(max_cost=10.0, max_tokens=None)
    guardian.record_invocation(cost=5.0, tokens=9999)
    result = guardian.evaluate()
    assert result.exceeded is False
    assert result.remaining_tokens is None
