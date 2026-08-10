# CI Readiness — Pre-push Checklist

Run these checks locally before every push or PR.

## Docs-only shortcut

If your diff only touches `.md` files, skip code checks. Verify with:

```bash
git status --short
```

## Required checks (all code changes)

```bash
make check
```

This runs lint → format-check → typecheck → test in sequence. If any step
fails, fix it before pushing.

Or run steps individually:

1. **Clean tree** — no accidental untracked files, no `.env` or secrets

   ```bash
   git status --short
   ```

2. **Lint**

   ```bash
   make lint
   ```

3. **Format**

   ```bash
   make format-check
   ```

   If it fails: `make format && make format-check`

4. **Type check**

   ```bash
   make typecheck
   ```

5. **Test**

   ```bash
   make test
   ```

## When to run full coverage

Run `make test-cov` instead of `make test` for any change to `core/`,
`gate/`, or `intent/` — those hold the Decision Gate logic every other
module depends on.

## CI parity

The GitHub Actions CI workflow runs one job today: lint, format-check,
type-check, and test across Python 3.10–3.13, then a build/package check.
If `make check` passes locally, CI should pass too.

A second job testing `agentic_sidecar.integrations.agenticlens` against a
real `agenticlens` checkout should be added once that module has real code,
not before.
