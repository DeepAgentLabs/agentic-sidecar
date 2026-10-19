# MCP 0.4.0 unified workflows

[MCP 0.4.0](https://github.com/DeepAgentLabs/mcp-server/releases/tag/v0.4.0) completes Phase 4 with its unified workflows: `core.compare_runs`, a fail-closed `core.release_check`, `core.incident_summary` and `core.export_report`. MCP judges nothing itself; it composes Lens comparisons, the Evals release gate and Chaos run reports. Malformed or failed-call evidence always blocks readiness, and so does missing evidence of a required kind; all three kinds are required by default and `required_evidence` narrows that.

## Scope

- The unified tools gate Lens, Evals and Chaos evidence only.
- MCP exposes Sidecar discovery only; it does not bridge Sidecar runtime controls.

## Still open

Authenticated Tower/Sidecar stop/revoke enforced at MCP dispatch, tool-level
authorization and correlated denial evidence are open MCP Phase 5 (hosted access
control) items, moved there from Phase 4.

## Compatibility

No Sidecar API change, dependency bump or release. Sidecar's `mcp` extra pins the
MCP SDK for its own gateway and is unrelated to `deep-agentic-core-mcp`.

See the [MCP unified workflows guide](https://github.com/DeepAgentLabs/mcp-server/blob/v0.4.0/docs/unified-workflows.md).
