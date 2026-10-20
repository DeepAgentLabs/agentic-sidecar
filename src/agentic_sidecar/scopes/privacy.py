"""Explicit reader access to host-held context and allowlisted evidence views."""

from __future__ import annotations

import threading
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


class ProtectedContext:
    """Host-owned context; identities must come from authenticated harness code.

    Revocation prevents future reads, never retracts copies already delivered.
    Context values are not injected into evaluator inputs or runtime evidence.
    """

    def __init__(
        self,
        payload: dict[str, Any],
        *,
        owner: str,
        readers: set[str],
        expires: datetime | None = None,
    ) -> None:
        self._payload = deepcopy(payload)
        self.owner = owner
        self.readers = frozenset({owner, *readers})
        self.expires = expires
        self._revoked = False
        self._lock = threading.RLock()

    def read(self, reader: str) -> dict[str, Any]:
        with self._lock:
            self._check(reader)
            return deepcopy(self._payload)

    def _check(self, reader: str) -> None:
        if self._revoked or (
            self.expires is not None and datetime.now(timezone.utc) >= self.expires
        ):
            raise PermissionError("Context expired or revoked")
        if reader not in self.readers:
            raise PermissionError("Context reader is not authorized")

    def update(self, values: dict[str, Any], *, actor: str) -> None:
        with self._lock:
            self._check(actor)
            if actor != self.owner:
                raise PermissionError("Only the context owner may update context")
            self._payload["values"] = deepcopy(values)

    def revoke(self, *, actor: str) -> None:
        with self._lock:
            if actor != self.owner:
                raise PermissionError("Only the context owner may revoke context")
            self._revoked = True


def redact_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """A safe summary, not a verifiable journal or a native Decision artifact.

    Use an allowlist: arguments, goal, plan, findings, reasons, intent, pending
    requests and arbitrary metadata never cross this boundary.
    """
    return {
        "task_id": snapshot["task_id"],
        "mode": snapshot["mode"],
        "stopped": snapshot["stopped"],
        "paused": snapshot["paused"],
        "executed": snapshot["executed"],
        "completed": snapshot["completed"],
        "sequence": snapshot["sequence"],
        "redacted": True,
        "decisions": [
            {
                "decision_id": item["decision"]["decision_id"],
                "status": item["decision"]["status"],
                "risk": item["decision"]["risk"],
            }
            for item in snapshot["decisions"]
        ],
    }
