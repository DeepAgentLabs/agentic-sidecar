# MCP 0.5.0 hosted access control

[MCP 0.5.0](https://github.com/DeepAgentLabs/mcp-server/releases/tag/v0.5.0) completes MCP Phase 5 with hosted access control. Each hosted key can carry allow and deny tool globs, an expiry and a task scope. The server enforces them at dispatch, outside the model: before each hosted handler runs, it re-authenticates the key and reloads its policy. Revocation, a narrower policy or expiry therefore stops queued calls, retries and calls on existing connections. Calls already running finish. Denied calls return an MCP-local `mcp.access-decision.v1` record, and every hosted call logs `dispatch`/`completion` records that share a `correlation_id`. These records are not AIOS artifacts. `core.access_status` reports a key's effective policy, and operators use `deep-agentic-core-mcp-admin` to narrow or revoke a key by user ID.

## What changes for Sidecar

- Nothing in Sidecar's runtime. `sidecar.status` and `sidecar.module_inventory`
  remain discovery tools, and a key's policy can allow or deny them.
- A Sidecar `TaskRuntime` whose `mcp` revoker revokes the task's hosted MCP key
  (for example through Tower's `MCPAccessRevoker`) now also stops calls that are
  queued behind that task's running call. Those calls leave a
  `revocation_acknowledged` record. In-flight calls and downstream credentials
  stay outside complete containment.
- An authenticated MCP-to-Sidecar stop/revoke bridge moves to MCP Phase 6. It
  needs a task-scoped Sidecar runtime control API that MCP can reach.

## Compatibility

No Sidecar API change, dependency bump or release. MCP's hosted pins stay at
`agentic-sidecar==0.9.1`.

See the [MCP hosted access control guide](https://github.com/DeepAgentLabs/mcp-server/blob/v0.5.0/docs/access-control.md).
