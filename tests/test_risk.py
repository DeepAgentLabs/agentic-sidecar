"""Tests for `agentic_sidecar.gate.risk.RiskEvaluator`."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.gate.risk import RISK_ORDER, RiskEvaluator, RiskRule


def test_empty_risk_evaluator_defaults_to_low() -> None:
    evaluator = RiskEvaluator()
    result = evaluator.evaluate(DecisionContext(tool_name="anything"))
    assert result.risk == "LOW"


def test_default_risk_is_configurable() -> None:
    evaluator = RiskEvaluator(default_risk="MEDIUM")
    result = evaluator.evaluate(DecisionContext(tool_name="anything"))
    assert result.risk == "MEDIUM"


def test_tool_name_only_rule_matches() -> None:
    evaluator = RiskEvaluator([RiskRule(tool="delete_*", risk="HIGH")])
    result = evaluator.evaluate(DecisionContext(tool_name="delete_database"))
    assert result.risk == "HIGH"
    assert result.matched_rule is not None


def test_argument_pattern_gt_matches_over_threshold() -> None:
    evaluator = RiskEvaluator(
        [
            RiskRule(
                tool="issue_refund",
                arg_name="amount",
                arg_op="gt",
                arg_value=500,
                risk="HIGH",
                reason="over refund limit",
            )
        ]
    )
    over = DecisionContext(tool_name="issue_refund", tool_args={"amount": 850})
    result = evaluator.evaluate(over)
    assert result.risk == "HIGH"
    assert result.reason == "over refund limit"


def test_argument_pattern_does_not_match_under_threshold() -> None:
    evaluator = RiskEvaluator(
        [
            RiskRule(
                tool="issue_refund",
                arg_name="amount",
                arg_op="gt",
                arg_value=500,
                risk="HIGH",
            )
        ],
        default_risk="LOW",
    )
    under = DecisionContext(tool_name="issue_refund", tool_args={"amount": 100})
    result = evaluator.evaluate(under)
    assert result.risk == "LOW"


def test_missing_arg_never_matches() -> None:
    evaluator = RiskEvaluator(
        [RiskRule(tool="issue_refund", arg_name="amount", arg_op="gt", arg_value=500, risk="HIGH")],
        default_risk="LOW",
    )
    result = evaluator.evaluate(DecisionContext(tool_name="issue_refund", tool_args={}))
    assert result.risk == "LOW"


def test_type_mismatch_never_matches_instead_of_raising() -> None:
    evaluator = RiskEvaluator(
        [RiskRule(tool="issue_refund", arg_name="amount", arg_op="gt", arg_value=500, risk="HIGH")],
        default_risk="LOW",
    )
    result = evaluator.evaluate(
        DecisionContext(tool_name="issue_refund", tool_args={"amount": "not-a-number"})
    )
    assert result.risk == "LOW"


def test_in_operator() -> None:
    evaluator = RiskEvaluator(
        [
            RiskRule(
                tool="transfer_funds",
                arg_name="destination",
                arg_op="in",
                arg_value=["offshore-1", "offshore-2"],
                risk="HIGH",
            )
        ]
    )
    result = evaluator.evaluate(
        DecisionContext(tool_name="transfer_funds", tool_args={"destination": "offshore-1"})
    )
    assert result.risk == "HIGH"


def test_first_matching_rule_wins() -> None:
    evaluator = RiskEvaluator(
        [
            RiskRule(tool="tool_a", risk="HIGH"),
            RiskRule(tool="tool_a", risk="LOW"),
        ]
    )
    result = evaluator.evaluate(DecisionContext(tool_name="tool_a"))
    assert result.risk == "HIGH"


@pytest.mark.parametrize(
    ("arg_op", "arg_value", "actual", "expected_match"),
    [
        ("ne", 500, 100, True),
        ("ne", 500, 500, False),
        ("gte", 500, 500, True),
        ("lt", 500, 100, True),
        ("lte", 500, 500, True),
        ("contains", "prod", "prod-db-1", True),
        ("contains", "prod", "dev-db-1", False),
    ],
)
def test_remaining_comparison_operators(
    arg_op: str, arg_value: object, actual: object, expected_match: bool
) -> None:
    evaluator = RiskEvaluator(
        [
            RiskRule(
                tool="tool_a", arg_name="value", arg_op=arg_op, arg_value=arg_value, risk="HIGH"
            )
        ],  # type: ignore[arg-type]
        default_risk="LOW",
    )
    result = evaluator.evaluate(DecisionContext(tool_name="tool_a", tool_args={"value": actual}))
    assert result.risk == ("HIGH" if expected_match else "LOW")


def test_arg_value_without_arg_name_is_rejected() -> None:
    with pytest.raises(ValidationError, match="arg_name"):
        RiskRule(tool="tool_a", arg_value=500, risk="HIGH")


def test_risk_order_is_ascending() -> None:
    assert RISK_ORDER["LOW"] < RISK_ORDER["MEDIUM"] < RISK_ORDER["HIGH"]


def test_from_yaml_reads_a_file(tmp_path: Path) -> None:
    risk_file = tmp_path / "risk_rules.yaml"
    risk_file.write_text(
        "default: LOW\n"
        "rules:\n"
        "  - tool: 'delete_*'\n"
        "    risk: HIGH\n"
        "    reason: 'destructive by default'\n"
    )
    evaluator = RiskEvaluator.from_yaml(risk_file)
    result = evaluator.evaluate(DecisionContext(tool_name="delete_database"))
    assert result.risk == "HIGH"
    assert result.reason == "destructive by default"
