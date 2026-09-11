# agentic-sidecar roadmap implementation audit

Audit date: 2026-09-11. Baseline: commit `3ea6047c21f0f73309fdcaaa958161d493b094d5`
(clean working tree, `main`). Scope: [ROADMAP.md](ROADMAP.md) (Release Status,
Scaffold Gaps, Design Constraints, Cross-Project Dependencies, Package Layout,
Definition of Done, and the v0.1–v1.0 Build Order), cross-checked against
[AGENTS.md](AGENTS.md), [README.md](README.md), [CHANGELOG.md](CHANGELOG.md),
and [concept.md](concept.md).

**Headline finding: this roadmap's checkbox state is unusually accurate.**
v0.1 and v0.2 are both genuinely implemented at the exact scope claimed —
narrower or broader claims were not found for any `[x]` item. Every `[ ]`
item from v0.2.x onward is a docstring-only placeholder module with zero
executable logic, exactly as ROADMAP.md's own top-of-file caveat already
states. The main value of this audit is independent, file-level confirmation
of that self-assessment, plus a few small documentation staleness issues
found in adjacent docs (not the roadmap's checkboxes themselves) and an
environment limitation on running the test suite (see Verification below).

## How to read this audit

- **Implemented (I):** usable code exists for the stated scope; evidence and
  test limits are recorded below. This does not assert publication, PyPI
  release, or independent (non-repo) validation.
- **Partial (P):** a subset, extension point, or narrower related capability
  exists.
- **Missing (M):** no implementation of the stated capability was found in
  the inspected source, tests, examples, or configuration.
- **Unverified (U):** the claim depends on a sibling repository, external
  service, or process step (e.g. a PyPI release) not observable from this
  repository alone.

## Milestone summary

| Milestone | Assessment | Main open work |
| --- | --- | --- |
| v0.1 Sidecar Runtime + Rule-Based Decision Gate | Implemented as scoped | None outstanding for the stated v0.1 scope |
| v0.2 Intent Guardian | Implemented as scoped | `authority` binding is explicitly out of scope, as documented |
| v0.2.x Early Validation Benchmark | Missing (correctly marked `[ ]`) | No `tests/validation/` fixtures or published numbers exist yet |
| v0.3 Planner, Critic & Judge | Missing (docstring-only placeholders) | No code beyond module docstrings |
| v0.4 Full Decision Gate & Budget Guardian | Missing (docstring-only placeholder) | `gate/budget.py` is a docstring; remaining `Decision.status` values not in the `Literal` |
| v0.5 Live Status & Narration | Missing (docstring-only placeholders) | `status/narrate.py`, `cli/main.py` are docstrings; no `[project.scripts]` entry |
| v0.6 Multi-Framework Adapters | Missing (docstring-only placeholders) | `adapters/{crewai,autogen,openai_agents,google_adk}.py` are docstrings; no `semantica.py` file (roadmap says so itself) |
| v0.7 Control Room | Missing | No web UI code or assets found |
| v0.8 Evaluation Framework & Benchmarks | Missing | Depends on v0.2.x/v0.3/v0.4 groundwork, none of which exists yet |
| v1.0 Intent Envelope as Interoperability Schema | Missing / Unverified | No `ai-operations-spec` publication observable from this repo |

## Evidence index

Paths are relative to this repository. Tests substantiate their covered
cases, not every possible behavior of an entire milestone.

| Key | Source | Regression evidence |
| --- | --- | --- |
| CORE | [sidecar.py](src/agentic_sidecar/core/sidecar.py), [decision.py](src/agentic_sidecar/core/decision.py), [context.py](src/agentic_sidecar/core/context.py), [operators.py](src/agentic_sidecar/core/operators.py), [exceptions.py](src/agentic_sidecar/core/exceptions.py) | [test_sidecar.py](tests/test_sidecar.py), [test_decision.py](tests/test_decision.py), [test_context.py](tests/test_context.py), [test_operators.py](tests/test_operators.py), [test_exceptions.py](tests/test_exceptions.py) |
| POLICY | [gate/policy.py](src/agentic_sidecar/gate/policy.py) | [test_policy.py](tests/test_policy.py) |
| RISK | [gate/risk.py](src/agentic_sidecar/gate/risk.py) | [test_risk.py](tests/test_risk.py) |
| INTENT | [intent/envelope.py](src/agentic_sidecar/intent/envelope.py), [intent/alignment.py](src/agentic_sidecar/intent/alignment.py) | [test_envelope.py](tests/test_envelope.py), [test_alignment.py](tests/test_alignment.py) |
| LANGGRAPH | [adapters/langgraph.py](src/agentic_sidecar/adapters/langgraph.py) | [test_langgraph_adapter.py](tests/test_langgraph_adapter.py) |
| PKG | [__init__.py](src/agentic_sidecar/__init__.py) | [test_package.py](tests/test_package.py) |
| EXAMPLES | [langgraph_refund_observe_mode.py](examples/langgraph_refund_observe_mode.py), [langgraph_intent_guardian_govern_mode.py](examples/langgraph_intent_guardian_govern_mode.py) | Not exercised by pytest; runnable scripts only (see Verification) |
| PLACEHOLDERS | [gate/budget.py](src/agentic_sidecar/gate/budget.py), [evaluators/](src/agentic_sidecar/evaluators/), [status/narrate.py](src/agentic_sidecar/status/narrate.py), [cli/main.py](src/agentic_sidecar/cli/main.py), [adapters/crewai.py](src/agentic_sidecar/adapters/crewai.py), [adapters/autogen.py](src/agentic_sidecar/adapters/autogen.py), [adapters/openai_agents.py](src/agentic_sidecar/adapters/openai_agents.py), [adapters/google_adk.py](src/agentic_sidecar/adapters/google_adk.py), [integrations/agenticlens.py](src/agentic_sidecar/integrations/agenticlens.py), [integrations/agentic_chaos.py](src/agentic_sidecar/integrations/agentic_chaos.py) | None — module bodies are a docstring only, confirmed by direct read (no test files reference them) |
| CI | [.github/workflows/ci.yml](.github/workflows/ci.yml) | Runs ruff/mypy/pytest on Python 3.10–3.13; not re-executed by this audit (see Verification) |

## v0.1 — Sidecar Runtime + Rule-Based Decision Gate

| Roadmap deliverable | Status | Evidence / remaining boundary |
| --- | --- | --- |
| `agentic_sidecar.core` — `Sidecar`, `Decision(status, risk, reason)` | I | CORE. `attach()` correctly lives in `adapters/langgraph.py`, not on `Sidecar` — confirmed no `attach` method exists on the class |
| `agentic_sidecar.gate.policy` — YAML-driven Policy Advisor | I | POLICY. `from_yaml`/`from_mapping`, first-match-wins, `default_effect` all present and tested |
| `agentic_sidecar.gate.risk` — rule-based Risk Evaluator | I | RISK. Tool-name glob plus optional argument-pattern check (`arg_name`/`arg_op`/`arg_value`) via shared `core/operators.py`; type-mismatch-safe (`compare()` returns `False`, never raises) |
| `agentic_sidecar.adapters.langgraph` | I | LANGGRAPH. No import-time dependency on the `langgraph` package itself, confirmed by reading the module's imports |
| `on_sidecar_failure` required setting, both paths tested | I | CORE (`Sidecar.__init__` raises `ValueError` with no default); `test_fail_open_allows_when_hook_raises` / `test_fail_closed_blocks_when_hook_raises` in test_sidecar.py cover both paths |
| README section + 1 runnable example (Observe mode) | I | EXAMPLES: `langgraph_refund_observe_mode.py`; README's "Python API (implemented)" v0.1 section matches the actual `Sidecar`/`attach` call shape |

**Package-boundary claim ("`core/` must not import `adapters/`"):** confirmed
by direct read of every import statement under `src/agentic_sidecar/` — no
file under `core/` imports from `adapters/`. `core/sidecar.py` does import
from `gate/` and `intent/` directly, which AGENTS.md documents as the
expected direction, not an exception.

Acceptance: v0.1's claimed scope (`ALLOW`/`BLOCK` only, Observe mode, zero
LLM calls) matches the code exactly — `DecisionStatus` was `Literal["ALLOW",
"BLOCK"]` in that phase and `WARN` was added only in v0.2's `Decision`
model, consistent with the CHANGELOG.

## v0.2 — Intent Guardian

| Roadmap deliverable | Status | Evidence / remaining boundary |
| --- | --- | --- |
| `agentic_sidecar.intent` — `IntentEnvelope`, `IntentGuardian` + `evaluate_alignment()` | I | INTENT. `authority` is present on `IntentEnvelope` as a plain `dict[str, bool]` field with no binding/enforcement code anywhere in `alignment.py` — the "no binding mechanism yet" scope note is accurate, not an understatement or overstatement |
| Lightweight `DecisionContext` snapshot type (`IntentSnapshot`, `HistoryEntry`) | I | CORE (`core/context.py`). `IntentSnapshot` carries goal+constraints only, not the full envelope, matching the claim that `core/` does not depend on `intent/envelope.py`'s `IntentEnvelope` type itself (only the lighter `IntentSnapshot`) |
| Constraint validation via `ConstraintBinding` | I | INTENT (`intent/alignment.py`'s `ConstraintBinding`, reusing `core/operators.py`'s `compare()` — the same comparator vocabulary `gate/risk.py` uses, confirmed via shared import) |
| Intent-drift `WARN`/`BLOCK` wired into the Decision Gate | I | CORE (`Sidecar._default_evaluate` calls `self.intent.evaluate(context)` and returns `BLOCK` immediately on an alignment `BLOCK`, else folds a `WARN` into the final status) + `test_intent_guardian_blocks_refund_over_limit`, `test_intent_guardian_warns_on_expired_envelope` in test_sidecar.py |
| `IntentEnvelope` field shapes documented against `ai-operations-spec` | I (as scoped: informal only) | `intent/envelope.py`'s module docstring states the informal alignment; no formal schema publication is claimed at v0.2, and none exists — consistent |
| README section + example reproducing the refund-limit scenario (concept.md §9) | I | EXAMPLES: `langgraph_intent_guardian_govern_mode.py`. concept.md's headers are numbered (`# 9. Semantic Authorization`) rather than literally prefixed with "§", but the numbering the docs reference resolves correctly throughout (§6→Intent Guardian, §9→Semantic Authorization, §15→Decision Gates, §22→Example Scenario, §37→Intent Envelope primitive) |

**Govern mode enforcement:** `adapters/langgraph.py`'s wrapped tool raises
`SidecarBlockedError` only when `sidecar.mode == "govern" and decision.status
== "BLOCK"`; `WARN` and `ALLOW` call through in both modes. Confirmed by
reading `_wrap_tool` and by `test_govern_mode_blocks_and_does_not_call_the_real_tool`,
`test_govern_mode_does_not_block_on_warn`, `test_govern_mode_still_allows_a_permitted_call`
in test_langgraph_adapter.py.

Acceptance: v0.2's checkbox list matches the code exactly, including the
narrow "authority has no binding mechanism yet" caveat already present in
ROADMAP.md and AGENTS.md — this audit found no case where that caveat
undersells or oversells what exists.

## v0.2.x — Early Validation Benchmark (narrow)

All three deliverables remain **Missing**, correctly marked `[ ]` already:

| Roadmap deliverable | Status | Evidence / remaining boundary |
| --- | --- | --- |
| `tests/validation/` — 3–5 fixtures | M | No `tests/validation/` directory exists anywhere in the repository |
| Measured before/after table (catch rate, false-positive rate) | M | No such table in README.md, ROADMAP.md, or elsewhere in the repo |
| README section publishing the numbers | M | README's Status section only claims v0.1/v0.2; no benchmark numbers present |

No correction needed here — ROADMAP.md already marks all three `[ ]`.

## v0.3 — Planner, Critic & Judge

All deliverables **Missing**. `evaluators/planner.py`, `evaluators/critic.py`,
and `evaluators/judge.py` each contain a module docstring only (verified by
reading each file in full — no classes, functions, or imports beyond the
docstring). `Sidecar._validate_roles` explicitly raises `NotImplementedError`
for `"planner"`, `"critic"`, and `"judge"` roles, naming v0.3 — an accurate,
enforced (not just documented) placeholder boundary, confirmed by
`test_future_role_raises_not_implemented` in test_sidecar.py.

## v0.4 — Full Decision Gate & Budget Guardian

All deliverables **Missing**. `DecisionStatus` is still
`Literal["ALLOW", "WARN", "BLOCK"]` (core/decision.py) — none of
`CHALLENGE`/`REPLAN`/`PAUSE`/`ESCALATE` exist in code anywhere in the
repository (confirmed by grep). `gate/budget.py` is a docstring only, and
`"budget"` is in `Sidecar`'s `_KNOWN_FUTURE_ROLES` map (raises
`NotImplementedError`, naming v0.4) rather than being silently accepted.

## v0.5 — Live Status & Narration

All deliverables **Missing**. `status/narrate.py` and `cli/main.py` are
docstring-only. `pyproject.toml` has no `[project.scripts]` entry and does
not declare `typer`/`rich` as dependencies, matching ROADMAP.md's own
Scaffold Gaps bullet exactly.

## v0.6 — Multi-Framework Adapters

All deliverables **Missing**. `adapters/crewai.py`, `adapters/autogen.py`,
`adapters/openai_agents.py`, and `adapters/google_adk.py` are docstring-only.
`integrations/agenticlens.py` and `integrations/agentic_chaos.py` are also
docstring-only placeholders (confirmed no imports, no functions). No
`integrations/semantica.py` file exists at all — the Package Layout section
of ROADMAP.md explicitly says this file "isn't created yet," which is
accurate; there is also no `semantica` extra in `pyproject.toml`'s
`[project.optional-dependencies]`, consistent with that claim.

## v0.7 — Control Room

**Missing.** No web UI code, frontend build tooling, or related assets found
anywhere in the repository tree.

## v0.8 — Evaluation Framework & Benchmarks

**Missing**, and correctly unscheduled — this milestone's own stated
prerequisites (v0.2.x fixtures, v0.3 Judge/Critic, v0.4 full Decision Gate)
are themselves all Missing, so no partial benchmark harness was expected or
found.

## v1.0 — Intent Envelope as an Interoperability Schema

**Missing / Unverified.** No schema file, publication script, or reference
to a completed `ai-operations-spec` submission exists in this repository.
Whether `ai-operations-spec` itself has ever received such a submission is
**U** — outside what this repository can attest to.

## Cross-Project Dependencies — verifiable-from-here claims only

| Claim | Status | Evidence / boundary |
| --- | --- | --- |
| Standalone at runtime — `pip install agentic-sidecar` needs no other DeepAgentLabs package | I | `pyproject.toml`'s `dependencies` list is exactly `pydantic`, `pyyaml`; `agenticlens` and `agentic-chaos` are optional extras only, and neither is imported by any non-placeholder module (confirmed by grep — no `import agenticlens` or `import agentic_chaos` outside the two placeholder docstrings) |
| `agenticlens` extra installs a dependency nothing imports yet | I | `integrations/agenticlens.py` has zero import statements |
| `agentic-chaos` extra installs a dependency nothing imports yet | I | `integrations/agentic_chaos.py` has zero import statements |
| AIOS alignment "documented... from v0.2 onward" | I (as scoped: documentation only) | `intent/envelope.py` module docstring; no code-level AIOS schema validation exists anywhere in this repo (none is claimed at this stage either) |
| `agenticlens`'s `Workflow` schema can already model Sidecar decisions; `semantica` correlation-ID contract; `mcp-server` end-to-end gating; `agenticops-control-tower` summarization | U | These are claims about sibling repositories' schemas/behavior, or about integration work not yet started on either side. Nothing in this repository proves or disproves them |

## Verification

**The test suite was not executed by this audit.** This environment has no
functioning Python interpreter or `uv` installation: `uv` is not on `PATH`,
the only `python`/`python3` on `PATH` are Windows Store app-execution-alias
stubs that refuse to run, and a discovered sibling `.venv`
(`agenticlens/.venv`, a `uv`-managed CPython 3.14) points at a
`%APPDATA%\uv\python\...` install that no longer exists on this machine. No
WSL distribution or Docker installation was available as a fallback. `uv run
pytest -q` and the Makefile's `make test` target were both attempted and
could not run.

In place of an executed run, this audit verified test coverage statically:
every non-placeholder source file has a corresponding test file (see the
Evidence index), test function names were read in full for all eleven test
files (104 named `test_` functions, two of which are `@pytest.mark.parametrize`
functions covering multiple cases each — `test_compare_operators` and
`test_remaining_comparison_operators`), and the specific behaviors ROADMAP.md
and AGENTS.md call out by name (both `on_sidecar_failure` paths, both
`Sidecar` modes, the intent-drift `WARN`/`BLOCK` split, `SidecarBlockedError`
carrying the post-evaluation context) were each traced to a specific test
function that exercises exactly that behavior. CI (`.github/workflows/ci.yml`)
runs `ruff check`, `ruff format --check`, `mypy`, and `pytest` across Python
3.10–3.13 on every push/PR; this audit did not re-run or inspect the actual
GitHub Actions run history (no `gh` CLI available, and it was out of scope
to query GitHub's API directly for this).

This is a materially weaker verification standard than an executed pytest
run: static reading confirms the tests *exist* and *appear* to assert the
right things, not that they currently pass. Anyone relying on this audit for
a release decision should run `make check` (or `uv run pytest -q`) themselves
before treating v0.1/v0.2 as release-ready.

## Issues worth addressing (not fixed by this audit)

1. **README.md's License section is stale.** It reads "MIT (planned —
   `LICENSE` file to be added alongside the first code commit...)", but a
   real `LICENSE` file (MIT, copyright 2026) has been committed and tracked
   in git since the `v0.0.1` scaffold commit. This is a README wording gap,
   not a ROADMAP.md checkbox, so it was left uncorrected per this audit's
   scope — flagging it here for a follow-up doc fix.
2. **README's Operating modes table lists "Advise" mode with no target
   version.** Every other row ("Observe", "Govern", "Human-supervised")
   names an implemented or planned version; "Advise" has neither an
   "Implemented" tag nor a "Planned vX" tag, and no `Sidecar` mode value
   other than `"observe"`/`"govern"` exists in code. It's unclear from the
   docs alone whether Advise mode is still intended as a distinct mode or
   was superseded by Observe→Govern's direct jump.
3. **`v0.1.0` was never tagged.** `git tag` shows only `v0.0.1` and `v0.2.0`
   — v0.1 and v0.2 were developed and released together under a single
   `v0.2.0` tag. This doesn't contradict any roadmap claim (ROADMAP.md and
   README.md both say "shipped," not "independently released to PyPI," and
   README.md separately states "No PyPI release yet"), but it's worth the
   maintainer knowing in case `v0.1.0`'s absence as a tag is unintentional.
4. **`uv.lock` is committed** despite the Scaffold Gaps bullet's framing
   ("No `uv.lock` committed intentionally beyond what a plain `uv sync`
   produces"). Read literally as "no lock file is committed," this bullet
   is inaccurate — `uv.lock` has been tracked since commit `31dfc29`. Read as
   intended ("no *customized* lock file — no `[tool.uv.sources]` override"),
   it's accurate. The wording is ambiguous enough to misread; worth
   tightening in a future docs pass.

No source code, tests, or configuration were modified to investigate or
address any of the above — they are flagged for a maintainer decision, not
fixed here.

## No product fixes were made by this audit

This audit only read source, tests, examples, and documentation, and wrote
this file plus targeted corrections to ROADMAP.md's own status markers (see
that file's changelog-style diff). No application code, test, or
configuration behavior was changed. All relative links above were checked
against the actual repository tree before finishing this audit.
