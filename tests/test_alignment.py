"""Tests for `agentic_sidecar.intent.alignment` -- constraint validation and
drift detection against an `IntentEnvelope` (the refund-limit scenario from
concept.md §9, reproduced here as the primary worked example).
"""

from datetime import datetime, timedelta, timezone

from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.intent.alignment import ConstraintBinding, IntentGuardian, evaluate_alignment
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester

REFUND_BINDING = ConstraintBinding(
    constraint="maximum_refund",
    tool="issue_refund",
    arg_name="amount",
    op="lte",
    severity="BLOCK",
)


def _refund_envelope(**overrides: object) -> IntentEnvelope:
    defaults: dict[str, object] = {
        "goal": "refund_customer",
        "requested_by": Requester(type="human", id="user123"),
        "constraints": {"maximum_refund": 500},
    }
    defaults.update(overrides)
    return IntentEnvelope.model_validate(defaults)


def test_within_constraint_allows() -> None:
    envelope = _refund_envelope()
    context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 120})
    result = evaluate_alignment(context, envelope, [REFUND_BINDING])
    assert result.status == "ALLOW"
    assert result.findings == []


def test_exceeding_constraint_blocks() -> None:
    envelope = _refund_envelope()
    context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 850})
    result = evaluate_alignment(context, envelope, [REFUND_BINDING])
    assert result.status == "BLOCK"
    assert "maximum_refund" in result.reason
    assert len(result.findings) == 1
    assert result.findings[0].constraint == "maximum_refund"


def test_binding_for_unrelated_tool_does_not_match() -> None:
    envelope = _refund_envelope()
    context = DecisionContext(tool_name="look_up_order", tool_args={"order_id": "A100"})
    result = evaluate_alignment(context, envelope, [REFUND_BINDING])
    assert result.status == "ALLOW"


def test_binding_for_constraint_the_envelope_does_not_declare_does_not_match() -> None:
    envelope = _refund_envelope(constraints={})
    context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 850})
    result = evaluate_alignment(context, envelope, [REFUND_BINDING])
    assert result.status == "ALLOW"


def test_binding_for_missing_arg_does_not_match() -> None:
    envelope = _refund_envelope()
    context = DecisionContext(tool_name="issue_refund", tool_args={})
    result = evaluate_alignment(context, envelope, [REFUND_BINDING])
    assert result.status == "ALLOW"


def test_warn_severity_binding_does_not_block() -> None:
    binding = REFUND_BINDING.model_copy(update={"severity": "WARN"})
    envelope = _refund_envelope()
    context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 850})
    result = evaluate_alignment(context, envelope, [binding])
    assert result.status == "WARN"


def test_block_finding_wins_over_warn_finding() -> None:
    warn_binding = ConstraintBinding(
        constraint="soft_limit", tool="issue_refund", arg_name="amount", op="lte", severity="WARN"
    )
    envelope = _refund_envelope(constraints={"maximum_refund": 500, "soft_limit": 200})
    context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 850})
    result = evaluate_alignment(context, envelope, [REFUND_BINDING, warn_binding])
    assert result.status == "BLOCK"
    assert len(result.findings) == 2


def test_enum_allow_list_constraint_via_in_operator() -> None:
    binding = ConstraintBinding(
        constraint="allowed_environments",
        tool="delete_resource",
        arg_name="environment",
        op="in",
        severity="BLOCK",
    )
    envelope = _refund_envelope(
        goal="clean_unused_resources", constraints={"allowed_environments": ["dev"]}
    )
    prod_call = DecisionContext(tool_name="delete_resource", tool_args={"environment": "prod"})
    dev_call = DecisionContext(tool_name="delete_resource", tool_args={"environment": "dev"})
    assert evaluate_alignment(prod_call, envelope, [binding]).status == "BLOCK"
    assert evaluate_alignment(dev_call, envelope, [binding]).status == "ALLOW"


def test_expired_envelope_warns_even_with_no_bindings() -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)
    envelope = _refund_envelope(expires=past)
    context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 10})
    result = evaluate_alignment(context, envelope, [])
    assert result.status == "WARN"
    assert "expired" in result.reason


def test_expiry_warn_does_not_hide_a_constraint_block() -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)
    envelope = _refund_envelope(expires=past)
    context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 850})
    result = evaluate_alignment(context, envelope, [REFUND_BINDING])
    assert result.status == "BLOCK"
    assert len(result.findings) == 2


def test_no_bindings_and_not_expired_allows() -> None:
    envelope = _refund_envelope()
    context = DecisionContext(tool_name="issue_refund", tool_args={"amount": 999999})
    result = evaluate_alignment(context, envelope, None)
    assert result.status == "ALLOW"


def test_intent_guardian_wraps_evaluate_alignment() -> None:
    envelope = _refund_envelope()
    guardian = IntentGuardian(envelope, [REFUND_BINDING])
    over_limit = DecisionContext(tool_name="issue_refund", tool_args={"amount": 850})
    within_limit = DecisionContext(tool_name="issue_refund", tool_args={"amount": 100})
    assert guardian.evaluate(over_limit).status == "BLOCK"
    assert guardian.evaluate(within_limit).status == "ALLOW"
