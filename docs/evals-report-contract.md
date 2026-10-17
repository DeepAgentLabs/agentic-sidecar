# Evals native contract compatibility

Agentic Evals 0.7.2 publishes native report (`schema_version: "1.0"`) and
gate-decision JSON Schemas, with offline `report_schema()` and
`gate_decision_schema()` accessors. Contract 1.x evolves additively; readers
should tolerate unknown fields. Sidecar supervision decisions remain separate from evaluation scores. Agent Alone vs Agent + Sidecar and containment evidence remain v0.9 work.

See the [contract, examples and compatibility policy](https://github.com/DeepAgentLabs/agentic-evals/blob/main/docs/report-contract.md). Existing dependency
ranges remain sufficient; using the new accessors directly requires
`agentic-evals>=0.7.2`. This documentation alignment needs no sibling patch release.
