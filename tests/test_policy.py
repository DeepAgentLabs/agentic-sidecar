"""Tests for `agentic_sidecar.gate.policy.PolicyAdvisor`."""

from pathlib import Path

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule


def test_empty_policy_defaults_to_allow() -> None:
    advisor = PolicyAdvisor()
    result = advisor.evaluate(DecisionContext(tool_name="anything"))
    assert result.effect == "allow"
    assert result.matched_rule is None


def test_default_effect_can_be_deny() -> None:
    advisor = PolicyAdvisor(default_effect="deny")
    result = advisor.evaluate(DecisionContext(tool_name="anything"))
    assert result.effect == "deny"


def test_matching_deny_rule_wins() -> None:
    advisor = PolicyAdvisor([PolicyRule(tool="delete_*", effect="deny", reason="destructive")])
    result = advisor.evaluate(DecisionContext(tool_name="delete_database"))
    assert result.effect == "deny"
    assert result.reason == "destructive"
    assert result.matched_rule is not None
    assert result.matched_rule.tool == "delete_*"


def test_non_matching_rule_falls_through_to_default() -> None:
    advisor = PolicyAdvisor([PolicyRule(tool="delete_*", effect="deny")])
    result = advisor.evaluate(DecisionContext(tool_name="read_order"))
    assert result.effect == "allow"
    assert result.matched_rule is None


def test_first_matching_rule_wins() -> None:
    advisor = PolicyAdvisor(
        [
            PolicyRule(tool="tool_a", effect="deny"),
            PolicyRule(tool="tool_a", effect="allow"),
        ]
    )
    result = advisor.evaluate(DecisionContext(tool_name="tool_a"))
    assert result.effect == "deny"


def test_auto_generated_reason_when_none_given() -> None:
    advisor = PolicyAdvisor([PolicyRule(tool="tool_a", effect="deny")])
    result = advisor.evaluate(DecisionContext(tool_name="tool_a"))
    assert "tool_a" in result.reason
    assert "deny" in result.reason


def test_from_mapping_builds_rules_and_default() -> None:
    advisor = PolicyAdvisor.from_mapping(
        {
            "default": "deny",
            "rules": [{"tool": "read_*", "effect": "allow"}],
        }
    )
    assert advisor.default_effect == "deny"
    assert advisor.evaluate(DecisionContext(tool_name="read_order")).effect == "allow"
    assert advisor.evaluate(DecisionContext(tool_name="write_order")).effect == "deny"


def test_from_yaml_reads_a_file(tmp_path: Path) -> None:
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text(
        "default: allow\n"
        "rules:\n"
        "  - tool: 'delete_*'\n"
        "    effect: deny\n"
        "    reason: 'no destructive ops'\n"
    )
    advisor = PolicyAdvisor.from_yaml(policy_file)
    result = advisor.evaluate(DecisionContext(tool_name="delete_database"))
    assert result.effect == "deny"
    assert result.reason == "no destructive ops"
