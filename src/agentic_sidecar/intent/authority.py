"""Task-local authority grants with narrowed delegation and atomic revocation.

This is a native Sidecar contract, not a credential issuer or AIOS schema.
The trusted harness holds the registry; agents receive only supervised tools.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from agentic_sidecar.intent.envelope import IntentEnvelope


class AuthorityBinding(BaseModel):
    """Require a named boolean task authority for matching tool names."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    authority: str
    tool: str


class AuthorityRegistry:
    """One shared registry per authority tree; revocation includes descendants.

    Grants are defensive snapshots. All dispatch reservations and revocations
    use the same lock. An already reserved call may finish after revocation.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._grants: dict[str, tuple[IntentEnvelope, str, str, str | None]] = {}
        self._revoked: set[str] = set()

    def grant(
        self, envelope: IntentEnvelope, *, task_id: str, agent_id: str, parent: str | None = None
    ) -> str:
        if not task_id or not agent_id:
            raise ValueError("Authority requires explicit task and agent identity")
        with self._lock:
            if parent is not None:
                reason = self.invalid_reason(parent)
                if reason:
                    raise ValueError(reason)
                original, task, _, _ = self._grants[parent]
                if task != task_id:
                    raise ValueError("Delegation cannot change task scope")
                if any(
                    value and original.authority.get(key) is not True
                    for key, value in envelope.authority.items()
                ):
                    raise ValueError("Delegation cannot widen authority")
                if original.expires is not None and (
                    envelope.expires is None or envelope.expires > original.expires
                ):
                    raise ValueError("Delegation cannot extend expiry")
                # Generic constraints have no universal ordering: registry-level
                # delegation preserves them exactly. Guardian.delegate can supply
                # additional restrictions through independently enforced bindings.
                if envelope.constraints != original.constraints:
                    raise ValueError("Delegation must preserve inherited constraints")
            grant_id = str(uuid4())
            self._grants[grant_id] = (envelope.model_copy(deep=True), task_id, agent_id, parent)
            return grant_id

    def invalid_reason(self, grant_id: str) -> str | None:
        with self._lock:
            current: str | None = grant_id
            while current is not None:
                if current not in self._grants:
                    return "Unknown authority grant"
                envelope, _, _, parent = self._grants[current]
                if current in self._revoked:
                    return "Task authority revoked"
                if envelope.expires is not None and datetime.now(timezone.utc) >= envelope.expires:
                    return "Task authority expired"
                current = parent
            return None

    def permits(self, grant_id: str, authority: str) -> bool:
        with self._lock:
            return (
                self.invalid_reason(grant_id) is None
                and self._grants[grant_id][0].authority.get(authority) is True
            )

    def revoke(self, grant_id: str) -> None:
        with self._lock:
            if grant_id not in self._grants:
                raise ValueError("Unknown authority grant")
            self._revoked.add(grant_id)

    @contextmanager
    def reservation(self) -> Iterator[None]:
        """Serialize a dispatch reservation against ancestor revocation."""
        with self._lock:
            yield
