# Lens routing integration boundary

## AgenticLens 0.10.0 routing compatibility

AgenticLens 0.10.0 implements roadmap v0.8: evidence-based runtime model
selection, fail-closed routing constraints, bounded provider failover,
confidence/escalation handoffs, shadow/canary modes and a local routing journal.
The default is advisory; execution uses explicit caller-owned callbacks.
MCP 0.3.12 exposes read-only `lens.routing_decide` and pins hosted Lens 0.10.0.
See the [routing guide](https://github.com/DeepAgentLabs/agenticlens/blob/v0.10.0/docs/routing.md)
and [offline example](https://github.com/DeepAgentLabs/agenticlens/blob/v0.10.0/examples/routing_demo.py).

The existing optional `agenticlens>=0.7.1,<1` extra already admits 0.10.0.
Decision Gate policy, authority and human approval remain Sidecar/host-owned;
a Lens route is not a Sidecar ALLOW or approval artifact. A blocked/escalated
route invokes no provider callback. No dependency change or Sidecar patch release
is required.
