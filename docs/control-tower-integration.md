# Control Tower integration

Agentic Sidecar supervises one task at its tool boundary. AgenticOps Control
Tower coordinates many deployments: inventory, heartbeats, alerts, incidents,
fleet-wide stop and approved runbooks. This page explains how the two fit
together for live visibility, pause/stop and emergency stop.

| Need | Single task (Sidecar) | Fleet (Control Tower) |
| --- | --- | --- |
| See what an agent is doing now | Control Room, `agentic-sidecar status --follow` | Inventory, alerts and incident console with joined Sidecar evidence |
| Pause / resume | `control pause` / `control resume` | Not offered; use the task's Sidecar controls |
| Stop (emergency stop) | `control stop` latches the task | Bulk `runtime.stop` across selected deployments |
| Restart | `control restart` after a clean stop | Adapter acknowledges restart; no bulk restart endpoint |
| Human approval | Per-decision approvals (human in the loop) | Separate approver for bulk actions and runbooks |
| Revoke MCP access | `TaskRuntime(revokers=...)` callbacks | Requires an issuer-backed `mcp` revoker on each runtime |

Ownership stays separate. Sidecar owns dispatch blocking, pre-action decisions,
scoped/private context and runtime approval authority. Tower owns fleet
targeting, approvals of bulk actions, runbooks and incident coordination. Tower
inventory does not confer task authority or prove containment, and a Sidecar
BLOCK is a supervision outcome, not an unhealthy deployment.

## Live view of a running task

Each supervised task can run an authenticated loopback `OperatorServer`. The
Control Room page shows the objective, plan, intent findings, risk, budget,
action lifecycle, pending approvals and audit events. The same data is available
from the CLI:

```bash
export SIDECAR_ENDPOINT=http://127.0.0.1:PORT/tasks/TASK_ID
# Set SIDECAR_OPERATOR_TOKEN securely in this terminal as well.
agentic-sidecar status --follow
agentic-sidecar control pause
agentic-sidecar control resume
agentic-sidecar control replan
```

Pause stops new dispatches until resume. Replan pauses dispatch and returns
control to the harness. See [live operations](live-operations.md#connect-a-real-task)
for server setup and the HTTP protocol.

Control Tower 0.8+ gives the fleet view: periodic detection over pushed
telemetry, durable alerts and acknowledgements, and a read-only incident console
that joins inventory, evidence (including explicit same-run Sidecar decisions),
approvals, commands and recovery checks. See
[Control Tower 0.8 live operations](tower-0.8-live-operations.md).

## Emergency stop

The Sidecar **stop** control is the emergency stop. It is designed to take
effect even when other parts of the system are failing:

- **Latches first.** Stop is set before the stop event is written and before
  any external callback runs, independently of Observe/Govern mode, approval
  state and `on_sidecar_failure`.
- **Blocks all future dispatch.** Queued proposals, approval retries and
  concurrently evaluated verdicts cannot dispatch. Decision epochs invalidate
  every pre-stop ALLOW.
- **Requests cancellation.** Owned async tools receive cooperative cancellation
  requests; already-dispatched synchronous work may finish and keep its effects.
- **Revokes access.** The task's authority grant is revoked and each configured
  revoker (for example an MCP issuer) is called. A broken audit sink cannot
  prevent revocation; the receipt reports `audit_error` instead.
- **Survives restoration.** A runtime restored from its journal comes back
  stopped and needs an explicit restart.

Trigger it from the Control Room, the CLI (`agentic-sidecar control stop`),
HTTP (`POST /tasks/TASK_ID/control` with `{"action": "stop"}`) or Python:

```python
from agentic_sidecar import Sidecar, TaskRuntime


def revoke_mcp_access(task_id: str) -> bool:
    """Revoke the task's issuer credential; return True only once confirmed."""
    return True


runtime = TaskRuntime("order-task", revokers={"mcp": revoke_mcp_access})
sidecar = Sidecar(
    on_sidecar_failure="fail_closed", mode="govern", runtime=runtime,
    escalation_handler=runtime,
)
receipt = runtime.control("stop", "on-call-operator")
assert receipt["action"] == "stop"
assert receipt["access_revocation"] == "acknowledged"
assert runtime.stopped
```

The receipt records `effective_at`, already-running invocation IDs, per-issuer
revocation results and `access_revocation` (`acknowledged`, `partial_failure`
or `not_configured`). `not_configured` confirms only the local dispatch stop.
Restart requires a stopped, idle task with successful revocations, and it does
not renew credentials. See
[stop, cancellation and access revocation](live-operations.md#stop-cancellation-and-access-revocation).

## Fleet-wide stop from Control Tower

Control Tower 0.7+ can stop many deployments in one approved bulk action. The
trusted host installs one `SidecarContainmentAdapter` per deployment, wrapping
that deployment's `TaskRuntime`:

```text
api.bulk.install(agent_id, SidecarContainmentAdapter(runtime))
```

The runtime must have an issuer-backed `mcp` revoker. A writer previews a bulk
request with `operation: runtime.stop`, a separate approver approves it, and the
writer executes it:

```bash
agenticops-control-tower --token "$WRITER_TOKEN" bulk preview fleet-stop.json
agenticops-control-tower --token "$APPROVER_TOKEN" bulk approve BULK_ID
agenticops-control-tower --token "$WRITER_TOKEN" bulk execute BULK_ID
agenticops-control-tower --token "$READER_TOKEN" bulk get BULK_ID
```

The adapter calls `runtime.control("stop", actor)` and maps the Sidecar receipt
to a per-target outcome: `acknowledged`, `incomplete` (calls still in flight),
`failed`, `unsupported` (no `mcp` revoker) or, from Tower, `timed_out`. Each
result reports dispatch blocking, MCP revocation, in-flight calls and
downstream credentials separately. There is no fleet atomicity, automatic
rollback or automatic restart; reconcile timed-out or requested stops before
approving a new action. See [Tower 0.7 fleet operations](tower-0.7-fleet-operations.md)
and Tower's
[fleet operations guide](https://github.com/DeepAgentLabs/agenticops-control-tower/blob/main/docs/fleet-operations.md).

## Runbooks and recovery

Control Tower 0.9+ runs versioned recovery runbooks with an exact-digest human
approval. Runbook steps go to host-installed runbook connectors, not to Sidecar.
Emergency stop and restart still go through the Sidecar containment adapter, and
Sidecar keeps dispatch blocking and pre-action decisions. See
[Control Tower 0.9 runbooks](tower-0.9-runbooks.md).

## Limits

- The operator server binds to `127.0.0.1` only; there is no TLS or public
  deployment. Remote fleet access goes through Tower and host adapters.
- Wrapped tools are the boundary. Unwrapped functions, independently created
  runtimes and downstream credentials are outside it.
- A boundary acknowledgement does not prove end-to-end containment or verified
  incident recovery.

See [limitations](limitations.md) for the full list.
