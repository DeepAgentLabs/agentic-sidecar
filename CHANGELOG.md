# Changelog

All notable changes to this project are documented here.

## [Unreleased]

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

No functional code has shipped yet — see [ROADMAP.md](ROADMAP.md) for the
v0.1 scope (Sidecar Runtime + Rule-Based Decision Gate).
