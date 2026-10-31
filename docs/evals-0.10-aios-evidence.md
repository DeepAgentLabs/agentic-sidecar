# Evals 0.10.0 evaluation evidence

[Agentic Evals 0.10.0](https://github.com/DeepAgentLabs/agentic-evals/releases/tag/v0.10.0)
exports its native evaluation reports as AI Operations Specification
`0.4-draft` `evaluation` evidence and merges it into an existing Run artifact,
with an `evaluates` link to every Step or object a case is mapped to.

## For Agent Alone vs Agent + Sidecar

- Evals scores what each arm answered. Exporting those scores as AIOS evidence
  does not turn a Sidecar decision into an evaluation. `ALLOW`, `BLOCK` and
  `ESCALATE` records, authority and redacted evidence remain Sidecar's own
  native outputs and are not exported by Evals.
- A case that a supervised agent reported as blocked is scored and exported
  like any other answer. A live case whose target raised because supervision
  stopped it has no observed output. Evals reports it in `unobserved_cases`
  and does not export it as an evaluation of the Run.
- An aligned Run with passing evaluations is not proof of containment. Scoring
  containment from observed dispatch evidence is Evals roadmap v0.11, which
  is still blocked on Sidecar lifecycle and dispatch evidence.

The `validation` extra (`agentic-evals>=0.9,<1`) already admits 0.10.0, and
Sidecar's full test suite passes against it (666 tests). No dependency
change or Sidecar release is needed.
See the [Evals guide](https://github.com/DeepAgentLabs/agentic-evals/blob/v0.10.0/docs/aios-evidence.md).
