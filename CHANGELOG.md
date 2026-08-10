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

No functional code has shipped yet — see [ROADMAP.md](ROADMAP.md) for the
v0.1 scope (Sidecar Runtime + Rule-Based Decision Gate).
