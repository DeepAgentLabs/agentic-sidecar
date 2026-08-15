# Changelog

All notable changes to this project are documented here.

## [Unreleased]

## [0.2.0] - 2026-08-15

### Added

- Intent Guardian (`agentic_sidecar.intent`): `IntentEnvelope` (goal,
  requester, constraints, authority, expiry — concept.md §6), `Requester`,
  `ConstraintBinding` (binds one envelope constraint to a specific tool
  argument and comparison op), `IntentGuardian` (mirrors
  `PolicyAdvisor`/`RiskEvaluator`'s construction shape), and
  `evaluate_alignment()`. Scope is deliberately narrow: constraint
  validation only (numeric/enum/allow-list, e.g. `maximum_refund: 500` vs.
  a proposed `850`) and envelope-expiry detection. `authority` is carried
  on the envelope (matching concept.md §6's shape, for future
  `ai-operations-spec` alignment) but has no binding/enforcement mechanism
  yet — deferred for the same reason Design Constraint 4 defers a
  model-based risk classifier: build it once a real scenario motivates the
  shape, not speculatively.
- `WARN` added to `Decision.status` (previously `ALLOW`/`BLOCK` only) —
  Intent Guardian's outcome for a finding worth surfacing (a stale/expired
  envelope) but not severe enough to block.
- Govern mode (`Sidecar(mode="govern")`): a `BLOCK` decision is now
  actually enforced. `agentic_sidecar.core.exceptions.SidecarBlockedError`
  is raised by an adapter (not by `Sidecar.evaluate()` itself, which only
  ever computes a `Decision` — see its docstring) when Govern mode's
  `BLOCK` should stop the call. `agentic_sidecar.adapters.langgraph.attach`
  now raises it instead of calling the real tool when
  `sidecar.mode == "govern"` and the decision is `BLOCK`; `WARN` and
  `ALLOW` still call through in both modes.
- `Sidecar.set_intent(guardian)` — swaps the active `IntentGuardian`
  between tasks (an `IntentEnvelope` is meant to be per-task, concept.md
  §6, not fixed for a Sidecar's whole lifetime). Raises if `intent=...` is
  given (at construction or via `set_intent`) without `"intent_guardian"`
  in `roles` — the same "no silent gap" principle `on_sidecar_failure`
  already applies, extended to this footgun.
- `"intent_guardian"` is now a supported `Sidecar` role (previously raised
  `NotImplementedError` naming v0.2).
- `core/context.py`: `IntentSnapshot` (goal + constraints only — the
  lightweight view attached to `DecisionContext.intent`, not the full
  `IntentEnvelope`, which `core/` does not depend on) and `HistoryEntry`.
  `Sidecar.evaluate()` now injects both into every `DecisionContext` before
  dispatching to an evaluator (concept.md §7, Intent Injection), built from
  `self.decisions` and the active `IntentGuardian` automatically.
- `core/operators.py`: shared `ArgOp` + `compare()`, extracted so
  `gate/risk.py`'s argument-pattern rules and `intent/alignment.py`'s
  constraint bindings don't duplicate identical comparator logic.
  `gate/risk.py` refactored to use it; its own rule-matching behavior is
  unchanged.
- `examples/langgraph_intent_guardian_govern_mode.py` — the refund-limit
  scenario from concept.md §9 end to end against a real
  `langgraph.prebuilt.create_react_agent` agent: an $850 refund request
  raises `SidecarBlockedError` before the real tool runs; a $120 request
  goes through normally.
- Test suite extended: `test_operators.py`, `test_envelope.py`,
  `test_alignment.py`, `test_exceptions.py`, plus new coverage in
  `test_sidecar.py` and `test_langgraph_adapter.py` for Govern mode, the
  intent/role consistency checks, and injected intent/history.

### Fixed

- `risk_block_threshold` was never validated at construction — an
  unrecognized value (e.g. a typo like `"SEVERE"`) passed straight through
  `Sidecar.__init__` and only surfaced as a `KeyError` deep inside
  `evaluate()`, silently resolved via `on_sidecar_failure` instead of
  failing fast. A misconfigured threshold could therefore fail open on a
  genuinely high-risk action. Now validated against `RISK_ORDER` at
  construction, raising immediately.
- `IntentEnvelope.is_expired()` raised an unhandled `TypeError` for a naive
  (no `tzinfo`) `expires` value — a realistic input shape from YAML or a
  caller that forgot `tzinfo=timezone.utc` — comparing it against the
  timezone-aware `datetime.now(timezone.utc)`. Inside `evaluate()` that
  error was swallowed into `on_sidecar_failure`'s fallback instead of
  producing the deterministic intent-expiry `WARN` it should have. Now
  rejected explicitly, at `IntentEnvelope` construction (a `field_validator`
  on `expires`) and in `is_expired()`'s own `now=` parameter, with an error
  naming the fix rather than a bare `TypeError`.
- `SidecarBlockedError`, raised by the LangGraph adapter in Govern mode,
  carried the bare pre-evaluation `DecisionContext` the adapter built, not
  the one Intent Guardian actually evaluated — `Sidecar.evaluate()`
  injected `intent`/`history` into a *copy* (`context.model_copy(...)`)
  rather than the object the caller held, so `SidecarBlockedError.context`
  always had `intent=None`, even when an intent-drift finding was exactly
  why the call was blocked. `evaluate()` now injects by mutating the
  caller's `DecisionContext` in place (documented as intentional on the
  model itself — it's why `DecisionContext`, unlike `Decision`, isn't
  frozen), so any caller's own reference — not just `sidecar.decisions` —
  reflects the fully-evaluated context once `evaluate()` returns.
- ROADMAP.md's v0.2 deliverable cited concept.md §22 (the DEV/production
  cleanup scenario, actually used by the v0.2.x benchmark) for the
  refund-limit worked example; corrected to §9, which is where that
  scenario actually appears.

## [0.1.0] - 2026-08-15

### Added

- Sidecar runtime (`agentic_sidecar.core`): `Sidecar`, `Decision(status,
  risk, reason)`, `DecisionContext`. `on_sidecar_failure: fail_open |
  fail_closed` is a required setting with no default; both paths are
  tested. `roles` validates against v0.1's supported set (`policy`, `risk`)
  and raises `NotImplementedError` (naming the version) for roles planned
  but not yet built, rather than silently ignoring them.
- Decision Gate (`agentic_sidecar.gate`): YAML-driven Policy Advisor
  (`policy.py`, allow/deny rules by tool-name glob) and rule-based Risk
  Evaluator (`risk.py`, tool-name glob plus an optional argument-pattern
  check). Zero LLM calls, per ROADMAP.md's Design Constraint 2.
- LangGraph adapter (`agentic_sidecar.adapters.langgraph.attach`): wraps a
  list of tool callables so every call is evaluated by a `Sidecar` first.
  v0.1 ships Observe mode only — the wrapped call always executes; nothing
  yet enforces a `BLOCK`. No import-time dependency on the `langgraph`
  package itself; a `langgraph` extra is declared in `pyproject.toml` for
  code that actually builds a graph around the wrapped tools.
- `examples/langgraph_refund_observe_mode.py` — a runnable, offline
  (no API key) example against a real `langgraph.prebuilt.create_react_agent`
  agent, demonstrating a Policy Advisor deny rule and a Risk Evaluator
  argument-threshold rule both firing in Observe mode.
- Test suite covering `Decision`, `DecisionContext`, `PolicyAdvisor`,
  `RiskEvaluator`, `Sidecar` (including both `on_sidecar_failure` paths),
  and the LangGraph adapter.

### Changed

- `Sidecar.attach(agent)` from README.md's Planned Python API is *not* how
  v0.1 actually ships attach: `core/` must not import from `adapters/`
  (AGENTS.md's Package Boundaries), so wrapping a specific framework's
  tool-call surface is each adapter's own function
  (`agentic_sidecar.adapters.langgraph.attach(sidecar, tools)`) rather than
  a generic method on `Sidecar`. README.md documents both the real v0.1
  shape and the longer-term generic shape this is expected to grow toward
  once a second adapter exists (Design Constraint 1).

### Fixed

- ROADMAP.md's Release Status/summary described v0.1 as "Rule-Based
  Decision Gate" without noting it's Observe-mode-only (advisory logging,
  not enforcement) — a reader skimming just the top could overestimate
  what shipped. Now says so explicitly in both places.
- ROADMAP.md's Package Layout diagram listed a `semantica.py` placeholder
  under `integrations/` as if it already existed, alongside `agenticlens.py`
  and `agentic_chaos.py`, which do. It doesn't yet (no code, no
  `pyproject.toml` extra) — it's a v0.6 deliverable; the diagram now says
  so. Same diagram also still described `core/sidecar.py` as owning
  `attach()`, which isn't how v0.1 actually shipped it (see "Changed"
  above) — corrected to match.
- ROADMAP.md's Design Constraints section header said "these four" while
  listing five items.
- ROADMAP.md's top summary said v0.2-onward modules were "still unstarted"
  when docstring-only placeholders for several of them already exist in
  the tree — reworded to distinguish "no real logic yet" from "doesn't
  exist yet."

## [0.0.1] - 2026-08-12

### Added

- Initial repository scaffold: proposed package layout under
  `src/agentic_sidecar/` (placeholder modules only, no logic), `pyproject.toml`,
  `Makefile`, CI and PyPI-release GitHub Actions workflows, and contributor
  docs (`AGENTS.md`, `CONTRIBUTING.md`, `CI.md`, `SECURITY.md`).
- `README.md` and `ROADMAP.md` describing the architecture and v0.1–v1.0
  build plan.
- Reserved (not implemented) optional integration seats for both sibling
  projects: `agenticlens` and `agentic-chaos` extras in `pyproject.toml`,
  each with a docstring-only placeholder under
  `src/agentic_sidecar/integrations/`.

### Fixed

- Audited `README.md`/`ROADMAP.md` against the original concept doc and
  corrected two gaps: the `Planner` module was named throughout the docs
  but had no package file, version, or repo-map entry (now
  `evaluators/planner.py`, v0.3); the `CHALLENGE` Decision Gate outcome was
  dropped from every enumeration while `ROADMAP.md` still claimed "all
  seven" outcomes (now restored, v0.4). Also documented two previously
  silent scope cuts (`LangChain` folded into the `LangGraph` adapter;
  sampling/caching/async-advisory cost-control ideas left unscheduled)
  instead of leaving them unexplained.

### Changed

- Renamed `future-plans.md` to `concept.md` and updated every reference.
