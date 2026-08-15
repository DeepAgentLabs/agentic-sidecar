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

v0.1 (Sidecar runtime, LangGraph adapter, deterministic policy/risk Decision
Gate, Observe mode) and v0.2 (Intent Guardian, Govern mode) have shipped.
The current build focus is v0.2.x, the narrow Early Validation Benchmark
(see ROADMAP.md). Work in this repo should reinforce that sequencing rather
than jumping ahead to Planner/Critic/Judge (v0.3) or multi-framework
features (v0.6).

### Before You Build Here

- Ask whether the feature is a pre-action governance concern; if it is
  retrospective analysis, it likely belongs in `agenticlens` instead
- Keep the Decision Gate deterministic where the roadmap says it should be
  (`gate/`, `intent/`); do not solve that behavior with model-based
  evaluators
- Avoid designing sidecar abstractions as if all frameworks are already
  supported; the first real adapter is still shaping the boundary

## Status

v0.1 and v0.2 are implemented: `core/` (`Sidecar`, `Decision`,
`DecisionContext`, `operators.py`, `exceptions.py`), `gate/policy.py`,
`gate/risk.py`, `intent/` (`IntentEnvelope`, `IntentGuardian`,
`ConstraintBinding`), and `adapters/langgraph.py` (both Observe and Govern
mode) have real code and tests. Everything else under
`src/agentic_sidecar/` (`evaluators/`, `status/`, `cli/`, `gate/budget.py`,
the remaining `adapters/*.py`, `integrations/*.py`) is still a placeholder
(docstring only) until its version lands. See [ROADMAP.md](ROADMAP.md) for
the build order before adding real logic to any of those.

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
[ROADMAP.md § Design Constraints](ROADMAP.md#design-constraints-read-before-building-v01v02)
for the full rationale on each:

1. **One framework adapter first.** `adapters/langgraph.py` before any of
   the other four. Do not claim framework independence until a second
   adapter has been built against real usage.
2. **Rules before models.** `gate/policy.py`, `gate/risk.py`, and (v0.2)
   `intent/alignment.py` must all work with zero LLM calls. Don't reach for
   `evaluators/judge.py` (v0.3) to solve a problem these can answer
   deterministically.
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

| Path | Purpose | Version |
|------|---------|------------------|
| `src/agentic_sidecar/core/` | `Sidecar` class (`evaluate()`, `before_tool_call` hook), `Decision` type, `DecisionContext`. `attach()` is *not* here — see AGENTS.md's Package Boundaries, adapters own it | v0.1 (implemented) |
| `src/agentic_sidecar/gate/policy.py` | Policy Advisor — deterministic YAML allow/deny rules | v0.1 (implemented) |
| `src/agentic_sidecar/gate/risk.py` | Risk Evaluator — rule-based classification | v0.1 (implemented) |
| `src/agentic_sidecar/gate/budget.py` | Budget Guardian — cost/token ceilings | v0.4 |
| `src/agentic_sidecar/adapters/langgraph.py` | LangGraph interception adapter, incl. `attach(sidecar, tools)`; enforces `BLOCK` in Govern mode (v0.2) | v0.1/v0.2 (implemented) |
| `src/agentic_sidecar/intent/` | `IntentEnvelope`, `IntentGuardian`, `ConstraintBinding` — constraint validation only, no `authority` enforcement yet | v0.2 (implemented) |
| `src/agentic_sidecar/evaluators/planner.py` | Planner — evaluates the whole plan against intent | v0.3 |
| `src/agentic_sidecar/evaluators/critic.py` | Critic mode — pre-decision challenge | v0.3 |
| `src/agentic_sidecar/evaluators/judge.py` | Model-agnostic LLM Judge interface | v0.3 |
| `src/agentic_sidecar/gate/` (remaining outcomes) | `CHALLENGE` / `REPLAN` / `PAUSE` / `ESCALATE`, human-in-the-loop escalation (`ALLOW`/`WARN`/`BLOCK` shipped in v0.1/v0.2) | v0.4 |
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
  reverse). `core/` *does* import from `gate/` and `intent/` directly
  (`Sidecar` wires in Policy Advisor, Risk Evaluator, and Intent Guardian as
  built-in Decision Gate modules) — that's the expected direction, not an
  exception to this rule. The distinction: `gate/`/`intent/` are modules
  Sidecar orchestrates itself; `adapters/` are alternate entry points into
  Sidecar, one per framework, and core has no business knowing any of them
  exist.
- `gate/` (Policy, Risk) must work with zero dependency on `evaluators/`
  (Planner, Critic, Judge) or `intent/` — v0.1's Decision Gate has to
  function before Judge or Intent Guardian exist at all, and Policy/Risk
  answer different questions than Intent (see Design Constraint 5).
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

Two phases, split by the merge to `main` — bumping happens before, tagging
and releasing happen after:

**1. Pre-release (on the feature branch, before merge):** Bump version in
`pyproject.toml`, `src/agentic_sidecar/__init__.py`, and `CHANGELOG.md`
(a dated release section under `[Unreleased]`). Commit as part of the
branch's normal history; goes in with the rest of the PR.

**2. Release (on `main`, once that branch has merged):** plain `git`, no
`gh` CLI required.

1. Pull the merge commit on `main`.
2. Tag: create an annotated `vX.Y.Z` tag pointing at the merge commit,
   using the CHANGELOG's release section as the tag message:
   `git tag -a vX.Y.Z -F <file-with-that-section> --cleanup=verbatim`.
   `--cleanup=verbatim` is required — git's default cleanup silently strips
   lines starting with `#`, which would eat the CHANGELOG's `###` headers.
3. Push the tag: `git push origin vX.Y.Z`.

That's the whole release: `release-pypi.yml` triggers on the tag push and
publishes to PyPI via Trusted Publishing (OIDC) — no API token/secret
required, but the `pypi` GitHub Environment must exist and be configured
as a Trusted Publisher on PyPI before the first release.

Note this deliberately does not create a GitHub Release object (that's a
`gh`/API-only action, not a `git` one) — the tag alone is enough to
publish to PyPI, but it means the repo's Releases tab stays empty unless
someone creates one by hand later (GitHub UI: Releases → Draft a new
release → pick the existing tag). That's an accepted tradeoff here, not
an oversight.
