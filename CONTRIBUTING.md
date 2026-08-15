# Contributing

Thanks for helping make `agentic-sidecar` better for everyone building
governable autonomous AI agents.

`agentic-sidecar` has v0.1 (Sidecar Runtime + Rule-Based Decision Gate)
implemented; everything from v0.2 onward is still a **scaffold** — see
[ROADMAP.md](ROADMAP.md) for what's planned and in what order before
starting on a module.

## Local setup

```bash
git clone https://github.com/pramodbn27/agentic-sidecar.git
cd agentic-sidecar
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Or with `uv`:

```bash
uv sync --extra dev
```

## Development workflow

1. Check [ROADMAP.md](ROADMAP.md) for the current build order — modules
   have a stated planned version for a reason (see its Design Constraints
   section); don't jump ahead (e.g. building Judge before the v0.1
   rule-based Decision Gate is solid).
2. Create a focused branch from `main`.
3. Add or update tests with every behavior change.
4. Add or update user-facing examples when the feature or expected workflow
   changes.
5. If a roadmap item is completed or its status changes, update
   `README.md` and `ROADMAP.md` in the same pull request.
6. If the work is release-ready, update `pyproject.toml`,
   `src/agentic_sidecar/__init__.py`, and `CHANGELOG.md` as part of the
   release.
7. Run:

```bash
ruff check .
ruff format --check .
mypy
pytest
```

8. Keep PRs focused — one concern per pull request.
9. Write clear commit messages describing *why*, not just *what*.

## Turning a placeholder module into a real one

1. Read the module's docstring in `src/agentic_sidecar/` — it states what
   the module is for and which ROADMAP version it belongs to.
2. Implement against the Python API sketched in `README.md`'s
   [Planned Python API](README.md#planned-python-api) section, adjusting
   the README if the real shape needs to differ.
3. Respect the Package Boundaries in [AGENTS.md](AGENTS.md) (e.g. `gate/`
   must not depend on `evaluators/`).
4. Add tests in `tests/`.
5. Add or update a usage example.
6. Update README, ROADMAP, and CHANGELOG in the same PR.

## Releases

Releases are automated via GitHub Actions when a version tag is pushed.

### Release checklist

1. Update the version string in all three locations:
   - `pyproject.toml` → `version = "X.Y.Z"`
   - `src/agentic_sidecar/__init__.py` → `__version__ = "X.Y.Z"`
   - `CHANGELOG.md` → add a `## [X.Y.Z] - YYYY-MM-DD` section
2. Commit: `git commit -am "release: vX.Y.Z"`
3. Tag: `git tag vX.Y.Z`
4. Push: `git push origin main --tags`

The `release-pypi.yml` workflow triggers on the tag push and publishes to
PyPI via Trusted Publishing (OIDC).
