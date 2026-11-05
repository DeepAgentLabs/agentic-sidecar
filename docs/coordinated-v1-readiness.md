# Coordinated v1.0 engineering readiness

Sidecar 0.11.0 adds the optional
`agentic_sidecar.integrations.aios.export_audit_event(record, target=..., created_at=...)`
projection for native AuditRecord values. It requires a host-supplied public
reference and a timezone-aware recording time. BLOCK becomes denied; other
native governance outcomes become requested, never succeeded. Native decision
id, outcome, correlation and parent decision links are preserved. Actor remains
unknown because AuditRecord has no authenticated actor field.

The exporter omits raw arguments, rationale, execution context and private tool
names. Callers remain responsible for using public opaque identifiers in supplied
references and correlation ids. Importing/exporting evidence grants no authority
and does not alter enforcement. Run `python examples/operational_artifacts.py`.

The live provider command now accepts `--require-all`. It exits 2 if a selected
provider was not run and 1 on a failed call. Release acceptance uses
`uv run python scripts/smoke_judge_providers.py --require-all` with both explicit
models and credentials supplied through the environment. Missing credentials
remain not_run, never a passing acceptance record. Provider calls are opt-in;
no model or key is selected automatically.

Migration/rollback: existing native contracts and runtime flows are unchanged.
Optional callers can disable companion emission and pin 0.10.1. Preserve native
audit records; do not reinterpret an ALLOW as dispatch/completion or relabel
0.8-draft evidence as a native Sidecar contract.

Independent acceptance, live/deployment evidence and the stable freeze remain
separate gates. See the [shared release policy](https://github.com/DeepAgentLabs/.github/blob/main/profile/RELEASE_POLICY.md).
