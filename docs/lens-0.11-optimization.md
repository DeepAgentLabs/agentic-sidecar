# Lens optimization and authority boundaries

## AgenticLens 0.11.0 optimization compatibility

AgenticLens 0.11.0 implements roadmap v0.9 Optimization Intelligence:
evidence-backed recommendations from recorded traces for prompts (caching,
compression), retrieval (top-k pruning, reranking), memory (summarization,
retention), tools (result caching, non-retryable errors), workflows (redundant
steps, handoffs that add no work) and models (quality-cost trade-offs between
variants). Projected benefit, confidence and quality risk stay separate; an
append-only ledger tracks accepted, rejected, adopted and reverted
recommendations; and adopted changes are evaluated against later traces, with
projected and observed outcomes side by side. Recommendations are advisory.
MCP 0.4.3 exposes read-only `lens.optimization_analyze` and pins hosted Lens
0.11.0. See the [optimization guide](https://github.com/DeepAgentLabs/agenticlens/blob/v0.11.0/docs/optimization.md)
and [offline example](https://github.com/DeepAgentLabs/agenticlens/blob/v0.11.0/examples/optimization_demo.py).

The optional `agenticlens>=0.7.1,<1` extra already admits 0.11.0, and the
locked integration CI now tests Lens 0.11.0. A Lens recommendation, or an
`adopted` entry in its local ledger, is not a Sidecar ALLOW or approval; policy
enforcement, authority and human approval remain Sidecar/host-owned. Tools that
declare `side_effects: true` or `idempotent: false` are never recommended for
caching. No runtime range change or Sidecar patch release is required.
