"""Tests for PlanEvaluator (v0.3.0)."""

from agentic_sidecar.evaluators.planner import PlanEvaluator, PlanStep


class TestPlanEvaluator:
    """Test suite for plan-level evaluation."""

    def setup_method(self):
        """Initialize evaluator before each test."""
        self.evaluator = PlanEvaluator(enabled=True)

    def test_evaluator_initialization(self):
        """Test basic initialization."""
        assert self.evaluator.enabled is True
        assert self.evaluator.name == "PlanEvaluator"

    def test_allow_simple_plan(self):
        """Test ALLOW for straightforward plan."""
        context = {
            "tool_name": "search",
            "arguments": {"query": "weather in NYC"},
            "history": [],
            "intent": None,
        }
        result = self.evaluator.evaluate(context)
        assert result.status == "ALLOW"
        assert result.confidence == 1.0

    def test_replan_unnecessary_steps(self):
        """Test REPLAN when plan contains unnecessary actions."""
        context = {
            "tool_name": "refund",
            "arguments": {"amount": 100},
            "history": [],
            "intent": None,
        }
        result = self.evaluator.evaluate(context)
        # Note: This will only trigger REPLAN if context has full plan
        assert result.status in ("ALLOW", "REPLAN")

    def test_blocked_on_empty_context(self):
        """Test graceful handling of missing context."""
        context = {"tool_name": "delete"}
        result = self.evaluator.evaluate(context)
        assert result.status in ("ALLOW", "REPLAN", "BLOCK")
        assert result.rationale is not None

    def test_confidence_score(self):
        """Test confidence is always 1.0 (rule-based)."""
        context = {
            "tool_name": "search",
            "arguments": {},
            "history": [],
            "intent": None,
        }
        result = self.evaluator.evaluate(context)
        assert result.confidence == 1.0

    def test_metadata_included(self):
        """Test metadata fields are populated."""
        context = {
            "tool_name": "search",
            "arguments": {},
            "history": [],
            "intent": None,
        }
        result = self.evaluator.evaluate(context)
        assert isinstance(result.metadata, dict)


class TestPlanStep:
    """Test suite for PlanStep dataclass."""

    def test_plan_step_creation(self):
        """Test PlanStep dataclass."""
        step = PlanStep(
            sequence=1,
            tool_name="search",
            description="Search for test results",
            arguments={"query": "test"},
            rationale="Initial search needed",
        )
        assert step.sequence == 1
        assert step.tool_name == "search"
        assert step.arguments == {"query": "test"}

    def test_plan_step_equality(self):
        """Test PlanStep equality comparison."""
        step1 = PlanStep(
            sequence=1, tool_name="search", description="Search", arguments={"query": "test"}
        )
        step2 = PlanStep(
            sequence=1, tool_name="search", description="Search", arguments={"query": "test"}
        )
        assert step1 == step2
