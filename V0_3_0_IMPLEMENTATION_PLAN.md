# v0.3.0 Implementation Plan: Planner, Critic & Judge

## Overview
v0.3.0 adds LLM-based evaluation capabilities to the Sidecar's Decision Gate:
- **Planner**: Evaluates entire plan against IntentEnvelope
- **Critic**: Challenges decisions for unsupported assumptions, contradictions, unnecessary actions
- **Judge**: LLM-based evaluation with model-agnostic interface (provider-independent)

## Architecture

```
Main Agent (Model A)
    ↓
Proposed Decision/Plan
    ↓
┌─────────────────────────────┐
│   Agentic Sidecar v0.3.0   │
│  ┌──────────────┐           │
│  │  Planner     │ (Plan-level evaluation)
│  ├──────────────┤           │
│  │  Critic      │ (Challenge assumptions)
│  ├──────────────┤           │
│  │  Judge       │ (Model-agnostic LLM)
│  │  (Model B)   │           │
│  └──────────────┘           │
└─────────────────────────────┘
    ↓
Decision (ALLOW/CHALLENGE/REPLAN/BLOCK)
    ↓
Main Agent (takes action or replan)
```

## Implementation Phases

### Phase 1: Core Evaluator Infrastructure
- [ ] Create `evaluators/__init__.py` with base classes
- [ ] Define `EvaluatorBase` abstract interface
- [ ] Create `EvaluatorResult` dataclass for results
- [ ] Create `JudgeProvider` interface (model-agnostic)

### Phase 2: Planner Implementation
- [ ] `evaluators/planner.py`: PlanEvaluator class
  - Input: full plan + IntentEnvelope + decision context
  - Output: approval status + rationale
  - Check: plan alignment with user intent
  - Return: ALLOW / REPLAN / BLOCK

### Phase 3: Critic Implementation
- [ ] `evaluators/critic.py`: CriticEvaluator class
  - Input: proposed decision + context
  - Challenge categories:
    - Unsupported assumptions
    - Incomplete reasoning
    - Unnecessary actions
    - Risky operations
    - Contradictions
    - Intent violations
    - Alternative approaches
  - Output: CHALLENGE / ACCEPT with rationale

### Phase 4: Judge Implementation
- [ ] `evaluators/judge.py`: Base JudgeEvaluator (model-agnostic)
- [ ] `providers/openai_judge.py`: OpenAI Judge implementation
- [ ] `providers/anthropic_judge.py`: Anthropic Judge implementation
- [ ] Judge interface:
  - Input: evaluation question + context
  - Output: decision + reasoning + confidence score
  - Model-independent: swap provider without changing Sidecar code

### Phase 5: Sidecar Integration
- [ ] Update `core/sidecar.py`:
  - Add planner, critic, judge as optional components
  - Add evaluation orchestration logic
  - Routing: which evaluator to invoke when
  - Cost tracking for LLM calls
- [ ] Update Decision outcomes to include new statuses
- [ ] Add configuration for enable/disable each evaluator

### Phase 6: Testing & Examples
- [ ] Comprehensive unit tests (90%+ coverage)
- [ ] Integration tests with mock LLM providers
- [ ] Example: `examples/v0_3_planner_critic_judge.py`
- [ ] Example: `examples/v0_3_judge_providers.py`

### Phase 7: Documentation & Release
- [ ] Update README.md with v0.3.0 features
- [ ] Update CHANGELOG.md with [0.3.0] section
- [ ] Create CLI documentation for v0.3.0 features
- [ ] Update examples/README.md
- [ ] Version bump: 0.5.0 → 0.6.0 (next dev version)

## Key Design Decisions

### 1. Model Agnostic Judge
```python
class JudgeProvider(ABC):
    """Provider-agnostic interface for LLM judges"""
    @abstractmethod
    async def evaluate(self, question: str, context: Dict) -> JudgeResult:
        """Evaluate a decision using the judge model"""
        pass

# Implementations:
class OpenAIJudge(JudgeProvider): ...
class AnthropicJudge(JudgeProvider): ...
class LocalJudge(JudgeProvider): ...  # For future v0.3.x
```

### 2. Cost Tracking
- All LLM calls tracked through existing BudgetGuardian
- Judge evaluation counts toward cost limits
- Metrics: tokens used, cost, latency per evaluation

### 3. Failure Modes
- Judge unavailable → fall back to rule-based Risk Evaluator
- Planner fails → use default routing
- Critic timeout → proceed with caution (WARN)

### 4. Configuration
```python
sidecar = Sidecar(
    mode="govern",
    on_sidecar_failure="fail_closed",
    planner=PlanEvaluator(enabled=True),
    critic=CriticEvaluator(enabled=True, threshold=0.7),
    judge=JudgeEvaluator(
        provider=OpenAIJudge(model="gpt-4"),
        enabled=True,
        cost_limit=0.10  # per decision
    )
)
```

## Files to Create/Modify

### New Files
- `src/agentic_sidecar/evaluators/planner.py` (150 LOC)
- `src/agentic_sidecar/evaluators/critic.py` (200 LOC)
- `src/agentic_sidecar/evaluators/judge.py` (250 LOC)
- `src/agentic_sidecar/evaluators/providers/openai_judge.py` (100 LOC)
- `src/agentic_sidecar/evaluators/providers/anthropic_judge.py` (100 LOC)
- `tests/test_planner.py` (150 LOC)
- `tests/test_critic.py` (150 LOC)
- `tests/test_judge.py` (200 LOC)
- `examples/v0_3_planner_critic_judge.py` (300 LOC)
- `examples/v0_3_judge_providers.py` (200 LOC)

### Modified Files
- `src/agentic_sidecar/core/sidecar.py` - Add evaluator integration
- `src/agentic_sidecar/core/decision.py` - Add CHALLENGE status
- `src/agentic_sidecar/__init__.py` - Export new classes
- `pyproject.toml` - Add LLM provider dependencies (optional)
- `README.md` - Document v0.3.0 features
- `CHANGELOG.md` - Add [0.3.0] section
- `examples/README.md` - Add v0.3.0 examples

## Testing Strategy

### Unit Tests
- Planner: plan evaluation logic, intent alignment scoring
- Critic: challenge detection, assumption analysis
- Judge: provider interface, model-agnostic handling

### Integration Tests
- Sidecar + Planner: plan-level gating
- Sidecar + Critic: decision challenge workflows
- Sidecar + Judge: LLM evaluation with fallback
- Cost tracking integration with BudgetGuardian

### Mock Tests
- Mock LLM providers to avoid real API calls
- Deterministic responses for testing
- Error scenarios (timeout, unavailable, rate limit)

## Success Criteria

- ✅ All evaluators implement the base interface
- ✅ Model-agnostic Judge works with 2+ LLM providers
- ✅ All code passes ruff linting and mypy type checking
- ✅ 90%+ test coverage
- ✅ Zero breaking changes to v0.4.0 API
- ✅ Optional features (don't impact agents not using them)
- ✅ Clear examples for each evaluator
- ✅ Performance overhead measured and documented

## Timeline Estimate

- Phase 1-2 (Core + Planner): 2-3 hours
- Phase 3 (Critic): 2-3 hours
- Phase 4 (Judge + Providers): 3-4 hours
- Phase 5-6 (Integration + Testing): 4-5 hours
- Phase 7 (Docs + Release): 2 hours

**Total: ~16-18 hours of focused development**

## Backward Compatibility

✅ All new features are optional and disabled by default
✅ Existing v0.4.0 agents work without changes
✅ New code path only activated when evaluators are enabled
✅ No changes to existing decision gate outcomes (only additions)
✅ BudgetGuardian tracks all LLM costs automatically

## Rollout Plan

1. Implement and test all phases
2. Create examples for each evaluator type
3. Update documentation
4. Version bump: pyproject.toml 0.5.0 → 0.6.0 (dev branch)
5. Create PR with all changes
6. Merge to main after review
7. Create v0.3.0 release tag
8. Publish to PyPI

---

**Status**: Ready to implement
**Created**: 2026-09-14
