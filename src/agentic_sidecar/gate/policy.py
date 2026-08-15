"""Policy Advisor -- deterministic, YAML-driven allow/deny rules.

Answers "are you permitted to do this?" only. No LLM calls, no intent
awareness -- that's `intent/` and `evaluators/`, deliberately kept separate
(see ROADMAP.md's Design Constraint 5 and AGENTS.md's Package Boundaries:
`gate/` must work with zero dependency on `evaluators/`).
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel

from agentic_sidecar.core.context import DecisionContext

PolicyEffect = Literal["allow", "deny"]


class PolicyRule(BaseModel):
    """One allow/deny rule. `tool` is an `fnmatch` glob matched against
    `DecisionContext.tool_name` (e.g. `"delete_*"`, `"*"`). Rules are
    evaluated in order; the first match wins.
    """

    tool: str
    effect: PolicyEffect
    reason: str | None = None


class PolicyResult(BaseModel):
    """What the Policy Advisor decided for one `DecisionContext`, and why."""

    effect: PolicyEffect
    reason: str
    matched_rule: PolicyRule | None = None


class PolicyAdvisor:
    """Deterministic allow/deny rule set.

    With no rules configured, every action resolves to `default_effect`
    (`"allow"` by default) -- an empty Policy Advisor is a no-op, not an
    implicit deny-all. Use `from_yaml` / `from_mapping` to load a real rule
    set, e.g.:

    ```yaml
    default: allow
    rules:
      - tool: "delete_*"
        effect: deny
        reason: "Destructive operations require Risk Evaluator + human sign-off"
      - tool: "read_*"
        effect: allow
    ```
    """

    def __init__(
        self,
        rules: list[PolicyRule] | None = None,
        *,
        default_effect: PolicyEffect = "allow",
    ) -> None:
        self.rules = rules or []
        self.default_effect = default_effect

    @classmethod
    def from_yaml(cls, path: str | Path) -> PolicyAdvisor:
        """Load a rule set from a YAML file (see class docstring for shape)."""
        data = yaml.safe_load(Path(path).read_text())
        return cls.from_mapping(data or {})

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> PolicyAdvisor:
        """Load a rule set from an already-parsed mapping (e.g. for tests
        that don't want to touch the filesystem).
        """
        rules = [PolicyRule.model_validate(rule) for rule in data.get("rules", [])]
        default_effect = data.get("default", "allow")
        return cls(rules, default_effect=default_effect)

    def evaluate(self, context: DecisionContext) -> PolicyResult:
        for rule in self.rules:
            if fnmatch.fnmatch(context.tool_name, rule.tool):
                reason = rule.reason or (
                    f"Matched policy rule tool='{rule.tool}' -> effect={rule.effect}"
                )
                return PolicyResult(effect=rule.effect, reason=reason, matched_rule=rule)
        return PolicyResult(
            effect=self.default_effect,
            reason=(
                f"No policy rule matched tool '{context.tool_name}'; "
                f"default effect is '{self.default_effect}'"
            ),
        )
