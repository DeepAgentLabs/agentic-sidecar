"""`IntentEnvelope` -- the structured, portable representation of what a
human (or a delegating agent) actually asked for: goal, requester,
constraints, granted/denied authority, and expiry (concept.md §6).

Informal `ai-operations-spec` alignment note (ROADMAP.md's Cross-Project
Dependencies -- formal publication as a versioned schema is a v1.0 target,
not v0.2): the field shape here -- `goal` / `requested_by {type, id}` /
`constraints` / `authority` / `expires` -- mirrors what an AIOS operational-
intent object is expected to need, so the shape shouldn't require reworking
later. `metadata` is the escape hatch for task-specific context
(concept.md's worked example's `customer`/`reason` fields) that doesn't yet
have a settled home in that alignment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from agentic_sidecar.core.context import IntentSnapshot


class Requester(BaseModel):
    """Who asked for this -- concept.md §6's `requested_by: {type, id}`."""

    type: Literal["human", "agent", "system"] = "human"
    id: str


class IntentEnvelope(BaseModel):
    """See concept.md §6 for the worked YAML example this mirrors.

    `constraints` and `authority` are intentionally freeform dicts here --
    what actually *enforces* them against a specific tool call is a list of
    `ConstraintBinding`s (see `agentic_sidecar.intent.alignment`), not the
    envelope itself. This keeps the envelope's shape stable (and
    AIOS-alignable) independent of how any one Sidecar happens to wire its
    bindings. v0.2 only builds enforcement for `constraints`; `authority`
    is carried on the model now (matching concept.md §6's shape) but has no
    binding/enforcement mechanism yet -- see alignment.py's module
    docstring for why that's deliberately deferred.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    goal: str
    requested_by: Requester
    constraints: dict[str, Any] = Field(default_factory=dict)
    authority: dict[str, bool] = Field(default_factory=dict)
    expires: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("expires")
    @classmethod
    def _require_timezone_aware_expires(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError(
                "expires must be timezone-aware (e.g. "
                "datetime(..., tzinfo=timezone.utc)) -- a naive datetime "
                "can't be compared against datetime.now(timezone.utc) in "
                "is_expired() without silently guessing which timezone was "
                "intended, and that comparison would otherwise only fail "
                "deep inside evaluate(), swallowed by on_sidecar_failure."
            )
        return value

    def is_expired(self, *, now: datetime | None = None) -> bool:
        """True once `now` (default: the current UTC time) is at or past
        `expires`. Always `False` for an envelope with no `expires` set --
        an envelope isn't stale by default, only once it's told when it
        stops being valid.
        """
        if self.expires is None:
            return False
        current = now if now is not None else datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("`now` must be timezone-aware if provided.")
        return current >= self.expires

    def to_snapshot(self) -> IntentSnapshot:
        """The lightweight view attached to `DecisionContext.intent` at
        evaluation time (concept.md §7, Intent Injection: only the
        relevant intent needs to reach a decision boundary, not the whole
        envelope) -- goal and constraints only.
        """
        return IntentSnapshot(goal=self.goal, constraints=dict(self.constraints))
