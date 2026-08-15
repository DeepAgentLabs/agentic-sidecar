"""Risk Evaluator -- classifies a proposed action's risk level.

v0.1-v0.2: static rules only (tool name, argument pattern). Promote to an
optional small local model only once there's measured evidence the
rule-based version is the bottleneck (ROADMAP.md's Design Constraint 4 --
a risk classifier is not a free lunch).
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, model_validator

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.core.decision import RiskLevel
from agentic_sidecar.core.operators import ArgOp, compare

RISK_ORDER: dict[RiskLevel, int] = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
"""Ordinal ranking used by `Sidecar` to compare a classified risk level
against `risk_block_threshold` (core/sidecar.py).
"""


class RiskRule(BaseModel):
    """One risk classification rule.

    `tool` is an `fnmatch` glob matched against `DecisionContext.tool_name`.
    The optional `arg_name`/`arg_op`/`arg_value` triple adds an argument
    pattern check (e.g. "risk is HIGH when `amount` `gt` `500`") --
    ROADMAP.md's Design Constraint 4 names "tool name / argument pattern /
    destination" as the intended static-rule surface. A rule with no
    `arg_name` matches on tool name alone. Rules are evaluated in order; the
    first match wins.
    """

    tool: str
    risk: RiskLevel
    reason: str | None = None
    arg_name: str | None = None
    arg_op: ArgOp = "eq"
    arg_value: Any = None

    @model_validator(mode="after")
    def _require_arg_name_for_argument_checks(self) -> RiskRule:
        if self.arg_value is not None and self.arg_name is None:
            raise ValueError("arg_value is set but arg_name is missing")
        return self


class RiskResult(BaseModel):
    """What the Risk Evaluator decided for one `DecisionContext`, and why."""

    risk: RiskLevel
    reason: str
    matched_rule: RiskRule | None = None


class RiskEvaluator:
    """Rule-based risk classifier.

    With no rules configured, every action resolves to `default_risk`
    (`"LOW"` by default). Use `from_yaml` / `from_mapping` to load a real
    rule set, e.g.:

    ```yaml
    default: LOW
    rules:
      - tool: "issue_refund"
        arg_name: amount
        arg_op: gt
        arg_value: 500
        risk: HIGH
        reason: "Refund exceeds the standard authorization limit"
      - tool: "delete_*"
        risk: HIGH
    ```
    """

    def __init__(
        self,
        rules: list[RiskRule] | None = None,
        *,
        default_risk: RiskLevel = "LOW",
    ) -> None:
        self.rules = rules or []
        self.default_risk = default_risk

    @classmethod
    def from_yaml(cls, path: str | Path) -> RiskEvaluator:
        """Load a rule set from a YAML file (see class docstring for shape)."""
        data = yaml.safe_load(Path(path).read_text())
        return cls.from_mapping(data or {})

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> RiskEvaluator:
        """Load a rule set from an already-parsed mapping (e.g. for tests
        that don't want to touch the filesystem).
        """
        rules = [RiskRule.model_validate(rule) for rule in data.get("rules", [])]
        default_risk = data.get("default", "LOW")
        return cls(rules, default_risk=default_risk)

    def evaluate(self, context: DecisionContext) -> RiskResult:
        for rule in self.rules:
            if not fnmatch.fnmatch(context.tool_name, rule.tool):
                continue
            if rule.arg_name is not None and not self._arg_matches(rule, context):
                continue
            reason = rule.reason or (f"Matched risk rule tool='{rule.tool}' -> risk={rule.risk}")
            return RiskResult(risk=rule.risk, reason=reason, matched_rule=rule)
        return RiskResult(
            risk=self.default_risk,
            reason=(
                f"No risk rule matched tool '{context.tool_name}'; "
                f"default risk is '{self.default_risk}'"
            ),
        )

    @staticmethod
    def _arg_matches(rule: RiskRule, context: DecisionContext) -> bool:
        if rule.arg_name not in context.tool_args:
            return False
        return compare(context.tool_args[rule.arg_name], rule.arg_op, rule.arg_value)
