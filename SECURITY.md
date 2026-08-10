# Security Policy

## Supported versions

Security fixes are provided for the latest released version. No version has
been released yet — this repository is currently a scaffold (see
[ROADMAP.md](ROADMAP.md)).

| Version | Supported |
| ------- | --------- |
| Latest  | Yes (once released) |
| Older   | Best effort |

## Reporting a vulnerability

Please report security issues privately using GitHub's private vulnerability
reporting feature on this repository.

Include:

- Affected version or commit
- Reproduction steps
- Impact assessment
- Any suggested mitigation

Please do not open a public issue for suspected vulnerabilities until the
issue has been reviewed.

## Scope

`agentic-sidecar` intercepts an agent's proposed tool calls and decisions to
evaluate and gate them. That means, once implemented, it will routinely see
data the calling application considers sensitive:

- tool-call arguments (which may contain customer data, credentials passed
  through as parameters, or internal identifiers)
- the `IntentEnvelope` (user identity, authorization scope, constraints)
- any context injected into a Critic/Judge evaluation

Sensitive values should be redacted before being logged, narrated (Status
Interpreter), or sent to an external Judge model — this is a design
requirement for those modules, not an afterthought (see `concept.md`
§18).

The library itself is not designed to store long-lived credentials, proxy
requests to external services, or execute arbitrary code on the caller's
behalf. If a defect allows either (a) an action that should have been
blocked to proceed, or (b) sensitive data to leak into a log, narration, or
third-party Judge call without redaction, please report it as a
vulnerability rather than a bug — both are security-relevant for this
package's stated purpose.
