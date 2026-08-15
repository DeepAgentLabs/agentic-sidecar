"""Tests for `agentic_sidecar.intent.envelope.IntentEnvelope`."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from agentic_sidecar.intent.envelope import IntentEnvelope, Requester


def _envelope(**overrides: object) -> IntentEnvelope:
    defaults: dict[str, object] = {
        "goal": "refund_customer",
        "requested_by": Requester(type="human", id="user123"),
        "constraints": {"maximum_refund": 500},
    }
    defaults.update(overrides)
    return IntentEnvelope.model_validate(defaults)


def test_id_is_auto_generated_and_unique() -> None:
    a, b = _envelope(), _envelope()
    assert a.id
    assert a.id != b.id


def test_defaults() -> None:
    envelope = _envelope()
    assert envelope.authority == {}
    assert envelope.metadata == {}
    assert envelope.expires is None


def test_never_expires_with_no_expires_set() -> None:
    envelope = _envelope()
    assert envelope.is_expired() is False


def test_is_expired_in_the_past() -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)
    envelope = _envelope(expires=past)
    assert envelope.is_expired() is True


def test_is_expired_in_the_future() -> None:
    future = datetime.now(timezone.utc) + timedelta(days=1)
    envelope = _envelope(expires=future)
    assert envelope.is_expired() is False


def test_is_expired_accepts_explicit_now_for_determinism() -> None:
    expires = datetime(2026, 8, 10, tzinfo=timezone.utc)
    envelope = _envelope(expires=expires)
    before = datetime(2026, 8, 9, tzinfo=timezone.utc)
    at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    after = datetime(2026, 8, 11, tzinfo=timezone.utc)
    assert envelope.is_expired(now=before) is False
    assert envelope.is_expired(now=at) is True  # at-or-past expiry counts as expired
    assert envelope.is_expired(now=after) is True


def test_to_snapshot_carries_goal_and_constraints_only() -> None:
    envelope = _envelope(
        goal="clean_unused_resources",
        constraints={"allowed_environments": ["dev"]},
        metadata={"customer": "C8291"},
    )
    snapshot = envelope.to_snapshot()
    assert snapshot.goal == "clean_unused_resources"
    assert snapshot.constraints == {"allowed_environments": ["dev"]}


def test_to_snapshot_does_not_share_the_constraints_dict() -> None:
    envelope = _envelope()
    snapshot = envelope.to_snapshot()
    snapshot.constraints["extra"] = 1
    assert "extra" not in envelope.constraints


def test_naive_expires_rejected_at_construction() -> None:
    naive = datetime(2026, 8, 14, 12, 0, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        _envelope(expires=naive)


def test_is_expired_rejects_a_naive_explicit_now() -> None:
    envelope = _envelope(expires=datetime.now(timezone.utc) + timedelta(days=1))
    with pytest.raises(ValueError, match="timezone-aware"):
        envelope.is_expired(now=datetime(2026, 8, 14, 12, 0, 0))
