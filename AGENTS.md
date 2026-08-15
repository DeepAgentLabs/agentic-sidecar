## agentic-sidecar Development Reference

## Ecosystem Context

### Role in DeepAgentLabs

`agentic-sidecar` is the decision-supervision layer in DeepAgentLabs. It sits
alongside an autonomous agent runtime and evaluates whether the next action is
still aligned with user intent, policy, risk tolerance, and escalation rules
before the action is allowed to proceed.

At the ecosystem-role level, the preferred keyword is **SUPERVISE**. In
practice, the package covers both supervision and governance.

### Owns

- Decision Gate behavior, policy/risk evaluation, and intent-preservation
  boundaries
- Framework adapters that intercept agent decisions and route them through the
  sidecar runtime
- Sidecar-specific decision artifacts that can later be represented through the
  shared specification

### Does Not Own

- The shared operational contract or normative object model — that belongs in
  `ai-operations-spec`
- Core workflow instrumentation, profiling, or retrospective evaluation — those
  belong in `agenticlens`
- Failure injection and resilience experiments — those belong in
  `agentic-chaos`
- The main ecosystem control surface or remote tool interface — that belongs in
  `deep-agentic-core-mcp`

### Integrates With

- `ai-operations-spec` for export-compatible decision artifacts and shared
  terminology
- `agenticlens` when sidecar decisions should appear in traces, analysis, or
  evidence workflows
- `agentic-chaos` when testing whether agent supervision still behaves
  correctly under induced failures or degraded conditions
- `deep-agentic-core-mcp` if sidecar capabilities are later exposed through a
  unified MCP surface

### Current Roadmap Focus

The current build focus is the v0.1 runtime: LangGraph adapter first, then the
deterministic policy/risk Decision Gate. Work in this repo should reinforce
that sequencing rather than jumping ahead to later judge- or multi-framework
features.

### Before You Build Here

- Ask whether the feature is a pre-action governance concern; if it is
  retrospective analysis, it likely belongs in `agenticlens` instead
- Keep v0.1 deterministic where the roadmap says it should be deterministic;
  do not solve early gate behavior with model-based evaluators
- Avoid designing sidecar abstractions as if all frameworks are already
  supported; the first real adapter is still shaping the boundary

## Status

This repository is a **scaffold** — directory layout, tooling config, and
CI/release workflows exist; `src/agentic_sidecar/` modules are placeholders
(docstring only, `NotImplementedError` on any callable if one exists) until
their version lands. See [ROADMAP.md](ROADMAP.md) for the build order before
adding real logic to any module.

## Build and Run

- Install: `make install` (runs `uv sync --extra dev`)
- Test: `make test` or `make check` (lint + format + typecheck + test)
- Lint: `make lint`
- Type check: `make typecheck`
- CLI: not implemented yet — `[project.scripts]` is intentionally absent
  from `pyproject.toml` until `cli/main.py` has a real Typer `app` (v0.5)

## Code Style

- Strict typing (mypy strict mode, Python 3.10+)
- Line length: 100
- Ruff rules: E, F, I, UP, B, SIM, N
- One purpose per file (separation of concerns)
- Decision and Intent Envelope artifacts must be exportable as AI Operations
  Specification objects once implemented (see `ai-operations-spec`)

## Design Constraints

These are load-bearing, not preferences — see
[ROADMAP.md § Design Constraints](ROADMAP.md#design-constraints-read-before-building-v01)
for the full rationale on each:

1. **One framework adapter first.** `adapters/langgraph.py` before any of
   the other four. Do not claim framework independence until a second
   adapter has been built against real usage.
2. **Rules before models.** v0.1's `gate/policy.py` and `gate/risk.py` must
   work with zero LLM calls. Don't reach for `evaluators/judge.py` (v0.3)
   to solve a v0.1 problem.
3. **`on_sidecar_failure` has no default.** Every Decision Gate path must
   handle `fail_open` and `fail_closed` explicitly — this is a governance
   property, not an implementation detail.
4. **A risk classifier is not a free lunch.** Keep `gate/risk.py` rule-based
   until there's measured evidence (see the v0.2.x benchmark in
   [ROADMAP.md](ROADMAP.md)) that a model-based classifier is actually
   needed.
5. **Policy, Risk, and Intent ask different questions.** A change that adds
   a static allow/deny check to `intent/` belongs in `gate/policy.py`
   instead. See
   [README.md](README.md#how-the-decision-gate-evaluates-a-decision).

## Repo Map

| Path | Purpose | Planned version |
|------|---------|------------------|
| `src/agentic_sidecar/core/` | `Sidecar` class, `attach()`, decision-boundary interception, `Decision` type | v0.1 |
| `src/agentic_sidecar/gate/policy.py` | Policy Advisor — deterministic YAML allow/deny rules | v0.1 |
| `src/agentic_sidecar/gate/risk.py` | Risk Evaluator — rule-based classification | v0.1 |
| `src/agentic_sidecar/gate/budget.py` | Budget Guardian — cost/token ceilings | v0.4 |
| `src/agentic_sidecar/adapters/langgraph.py` | LangGraph interception adapter | v0.1 |
| `src/agentic_sidecar/intent/` | `IntentEnvelope`, alignment scoring, drift detection | v0.2 |
| `src/agentic_sidecar/evaluators/planner.py` | Planner — evaluates the whole plan against intent | v0.3 |
| `src/agentic_sidecar/evaluators/critic.py` | Critic mode — pre-decision challenge | v0.3 |
| `src/agentic_sidecar/evaluators/judge.py` | Model-agnostic LLM Judge interface | v0.3 |
| `src/agentic_sidecar/gate/` (full outcome set) | `WARN` / `CHALLENGE` / `REPLAN` / `PAUSE` / `ESCALATE`, human-in-the-loop escalation | v0.4 |
| `src/agentic_sidecar/status/narrate.py` | Human-readable status narration | v0.5 |
| `src/agentic_sidecar/cli/` | CLI entry point (`agentic-sidecar status --follow`) | v0.5 |
| `src/agentic_sidecar/adapters/{crewai,autogen,openai_agents,google_adk}.py` | Additional framework adapters | v0.6 |
| `src/agentic_sidecar/integrations/agenticlens.py` | Optional AgenticLens adapter (surfaces Sidecar decisions in `agenticlens analyze`) | optional, coordinate with `agenticlens` |
| `src/agentic_sidecar/integrations/agentic_chaos.py` | Optional Agentic Chaos coordination (recovery-decision evaluation, chaos-testing the Sidecar's own gate) | optional, coordinate with `agentic-chaos` |
| `tests/` | Pytest test suite | ongoing |
| `Makefile` | Local dev automation | — |

Full architecture and build order: [ROADMAP.md](ROADMAP.md).

## Entry Points (planned)

- Injection API: `from agentic_sidecar import Sidecar`
- CLI: `agentic-sidecar status --follow` (v0.5)

## Package Boundaries

- This package is **standalone** — `pip install agentic-sidecar` must work
  with zero other DeepAgentLabs dependencies.
- AgenticLens integration is optional (`agentic_sidecar.integrations.agenticlens`)
  and must auto-skip in tests if `agenticlens` is not installed.
- `core/` must not import from `adapters/` (adapters depend on core, not the
  reverse).
- `gate/` (Policy, Risk) must work with zero dependency on `evaluators/`
  (Planner, Critic, Judge) — v0.1's Decision Gate has to function before
  Judge exists at all.
- `evaluators/judge.py` must stay model-agnostic — no hardcoded provider SDK
  imports at module scope.

## Adding a New Framework Adapter

1. Confirm a first adapter (`adapters/langgraph.py`) is done and stable —
   don't start a second adapter to "save time" in parallel; the interception
   abstraction needs to survive one real framework before generalizing.
2. Add the adapter module under `adapters/`.
3. Add conformance tests asserting identical `Decision` behavior for an
   equivalent scenario across all adapters shipped so far.
4. Update README's `Design Constraints` note if the abstraction had to
   change to accommodate the new framework.

## Feature Completion Expectations

- Every behavior change must include tests.
- User-facing features must include or update examples in `README.md` or
  `examples/`.
- When a roadmap item or milestone meaningfully changes status, update
  `README.md` and `ROADMAP.md` in the same change.
- If that milestone or release changes the public ecosystem story, also update
  the shared org-profile docs in the `.github` repository:
  `profile/README.md` and, when relevant, `profile/ROADMAP.md`.
- When work is packaged as a release-ready change, also update
  `pyproject.toml`, `src/agentic_sidecar/__init__.py`, and `CHANGELOG.md`.

## Pre-push Checklist

Run `make check` before every push. It runs: lint → format-check → typecheck → test.

## Release

1. Bump version in `pyproject.toml`, `src/agentic_sidecar/__init__.py`, and `CHANGELOG.md`
2. Commit: `git commit -am "release: vX.Y.Z"`
3. Tag: create an annotated `vX.Y.Z` tag and use the latest `CHANGELOG.md`
   release section as the tag description
4. Push: `git push origin main --tags`

The `release-pypi.yml` workflow triggers on the tag push and publishes to
PyPI via Trusted Publishing (OIDC) — no API token/secret required, but the
`pypi` GitHub Environment must exist and be configured as a Trusted
Publisher on PyPI before the first release.
