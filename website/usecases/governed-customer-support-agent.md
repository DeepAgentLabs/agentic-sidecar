# Run a Governed Customer Support Agent

Combine Policy Advisor, Intent Guardian, Risk Evaluator, and Budget Guardrails into a unified synchronous supervision sidecar to secure enterprise customer support workflows.

| | |
|---|---|
| **For** | Enterprise AI platform engineers deploying production support agents |
| **Difficulty** | Intermediate |
| **Time** | ~15 minutes |
| **Capabilities** | [Policy Advisor](https://deepagentlabs.io/agentic-sidecar/docs/features/#policy-advisor), [Intent Guardian](https://deepagentlabs.io/agentic-sidecar/docs/features/#intent-guardian), [Risk Evaluator](https://deepagentlabs.io/agentic-sidecar/docs/features/#risk-evaluator), [Budget Guardrails](https://deepagentlabs.io/agentic-sidecar/docs/features/#budget-guardrails) |
| **Status** | Stable |

## The problem

Production customer support agents operate with broad toolsets: reading order details, issuing refunds, sending customer communications, and managing customer accounts. Single-layer guardrails (such as system prompt instructions or isolated regex filters) leave multiple attack surfaces exposed:

1. **Destructive Actions**: Rogue calls to delete customer records or wipe databases.
2. **Financial Drift**: Issuing refunds above specific user intent limits authorized by tier leads.
3. **High-Risk Operations**: Triggering unreviewed tier-2 operations without escalation.
4. **Cost Runaways**: Infinite agent loops consuming excessive API budget.

Building custom checks across each tool function results in tangled, duplicate code that is difficult to maintain or audit.

## Architecture

<figure class="refund-flow support-flow" data-support-flow aria-labelledby="support-flow-title">
  <div class="refund-flow-header"><div><span class="refund-eyebrow">MULTI-LAYER SUPERVISION / CUSTOMER SUPPORT</span><h3 id="support-flow-title">One agent. Four boundaries. An accountable decision.</h3></div><span class="refund-sim-label">Browser-only illustration</span></div>
  <div class="refund-controls"><div><button type="button" data-support-play hidden>Pause animation</button><button type="button" data-support-replay hidden>Replay example</button></div><span data-support-playback>Static example · $850 refund blocked</span></div>
  <label class="support-picker" data-support-picker hidden>Example scenario<select data-support-select><option value="refund-block" selected>Govern · $850 refund blocked</option><option value="delete">Govern · record deletion denied</option><option value="observe-refund">Observe · $850 refund logged, then executed</option><option value="budget">Govern · exhausted budget pauses work</option><option value="read">Govern · order read allowed</option><option value="refund-allow">Govern · $300 refund allowed</option></select></label>
  <div class="refund-progress" aria-hidden="true"><span></span></div>
  <div class="support-intent"><span>ORIGINAL INTENT</span><p>Assist the customer with order ORD-999, authorize refunds only up to $500 and preserve customer records.</p><small>Risk threshold: HIGH · Task budget: $5 · Sidecar failure: fail_closed</small></div>
  <div class="support-map">
    <div class="support-request support-node" data-support-node="request"><div><span class="refund-eyebrow">01 / AGENT REQUEST</span><h4>Customer support agent</h4><code data-support-call>issue_refund("ORD-999", 850)</code></div><div class="support-mode"><b data-support-mode>GOVERN</b><small data-support-mode-detail>Active enforcement</small></div><span class="support-tick" aria-label="Complete">✓</span></div>
    <div class="support-gates">
      <div class="support-gate support-blue support-node" data-support-node="policy"><div class="support-node-top"><span>02 / POLICY ADVISOR</span><span class="support-tick" aria-label="Complete">✓</span></div><h4>Protect the records.</h4><code>delete_* → deny</code><p data-support-policy-detail>Refund tool is not denied by the deletion rule.</p><small data-support-policy>PASS</small></div>
      <div class="support-gate support-purple support-node failed" data-support-node="risk"><div class="support-node-top"><span>03 / RISK EVALUATOR</span><span class="support-tick" aria-label="Blocked">×</span></div><h4>Bound financial risk.</h4><code>amount &gt; $500 → HIGH</code><p data-support-risk-detail>$850 exceeds the configured $500 threshold.</p><small data-support-risk>HIGH → BLOCK</small></div>
      <div class="support-gate support-teal support-node skipped" data-support-node="intent"><div class="support-node-top"><span>04 / INTENT GUARDIAN</span><span class="support-tick" aria-label="Not evaluated">–</span></div><h4>Keep the user's limit.</h4><code>maximum_refund ≤ $500</code><p data-support-intent-detail>Earlier risk decision already returned BLOCK.</p><small data-support-intent>NOT EVALUATED</small></div>
      <div class="support-gate support-amber support-node skipped" data-support-node="budget"><div class="support-node-top"><span>05 / BUDGET GUARDIAN</span><span class="support-tick" aria-label="Not evaluated">–</span></div><h4>Cap the task spend.</h4><code>max_cost = $5.00</code><p data-support-budget-detail>Earlier risk decision already returned BLOCK.</p><small data-support-budget>NOT EVALUATED</small></div>
    </div>
    <div class="support-outcomes"><div class="support-verdict support-node" data-support-node="verdict"><div class="support-node-top"><span>06 / DECISION GATE</span><span class="support-tick" aria-label="Complete">✓</span></div><h4 data-support-verdict>BLOCK</h4><p data-support-verdict-detail>Risk Evaluator: HIGH meets the blocking threshold.</p></div><div class="support-dispatch support-node" data-support-node="dispatch"><div class="support-node-top"><span>07 / TOOL BOUNDARY</span><span class="support-tick" aria-label="Complete">✓</span></div><h4 data-support-dispatch>Execution prevented</h4><code data-support-dispatch-code>SidecarBlockedError</code><p data-support-dispatch-detail>The inner refund tool is not invoked.</p></div></div>
    <div class="support-audit support-node active" data-support-node="audit"><div><span class="refund-eyebrow">08 / DECISION PROVENANCE</span><h4 data-support-audit-title>The decision is recorded.</h4><p data-support-audit>Tool, arguments, mode, decision and reason are retained in the illustrative record.</p></div><div class="support-audit-metrics"><b data-support-calls>0</b><span>Simulated tool calls</span><b data-support-funds>$0</b><span>Simulated refunds issued</span></div><span class="support-tick" aria-label="Complete">✓</span></div>
  </div>
  <div class="support-story" role="status" aria-live="off"><span class="refund-eyebrow" data-support-phase>08 / AUDIT</span><h4 data-support-heading>Govern mode holds the boundary.</h4><p data-support-story>The $850 refund is blocked before execution. Later evaluators are not falsely shown as having run.</p></div>
  <details class="support-record"><summary>Inspect the illustrative decision record</summary><pre data-support-record>{"simulation":true,"mode":"govern","tool":"issue_refund","amount":850,"decision":"BLOCK","risk":"HIGH","tool_executed":false,"reason":"Refund exceeds threshold ($500)"}</pre></details>
  <figcaption>Animated illustration of the walkthrough below. Evaluation can return early: a Policy deny or HIGH-risk refund produces a BLOCK before later checks. Observe mode records the decision without enforcing it. The exhausted-budget example illustrates PAUSE, as a separate variation. No SDK, model, database or payment service is called.</figcaption>
</figure>

## Prerequisites

- Python 3.10+ (Python 3.12 recommended)
- `agentic-sidecar` v`0.7.0` (or later) installed
- Runnable script: [`examples/governed_customer_support_agent.py`](https://github.com/DeepAgentLabs/agentic-sidecar/tree/main/examples/governed_customer_support_agent.py)

## Walkthrough

### 1. Define Support Agent Tools

Create standard support agent tools for order retrieval, refund issuance, and record deletion:

```python
def read_order(order_id: str) -> dict:
    """Retrieve order details by order ID."""
    print(f"  [EXEC] Executing read_order('{order_id}')...")
    return {"order_id": order_id, "amount": 450.0, "status": "delivered"}

def issue_refund(order_id: str, amount: float, reason: str = "customer dispute") -> dict:
    """Issue a monetary refund to customer."""
    print(f"  [EXEC] Executing issue_refund('{order_id}', amount=${amount})...")
    return {"status": "refund_processed", "order_id": order_id, "refund_amount": amount}

def delete_customer_record(customer_id: str) -> dict:
    """Permanently delete a customer record from database."""
    print(f"  [EXEC] Executing delete_customer_record('{customer_id}')...")
    return {"status": "deleted", "customer_id": customer_id}
```

### 2. Configure Multi-Gate Supervision Rules

Define policies for account deletion, financial risk thresholds, user intent envelopes, and budget limits:

```python
from agentic_sidecar import Sidecar, SidecarBlockedError
from agentic_sidecar.adapters.langgraph import attach
from agentic_sidecar.gate import BudgetGuardian
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule
from agentic_sidecar.gate.risk import RiskEvaluator, RiskRule
from agentic_sidecar.intent import ConstraintBinding, IntentEnvelope, IntentGuardian, Requester

# Policy: Hard DENY on database deletions
policy = PolicyAdvisor(rules=[
    PolicyRule(tool="delete_*", effect="deny", reason="Account deletion requires explicit admin authorization")
])

# Risk: Classify refunds over $500 as HIGH risk
risk = RiskEvaluator(rules=[
    RiskRule(tool="issue_refund", arg_name="amount", arg_op="gt", arg_value=500.0, risk="HIGH", reason="Refund exceeds threshold ($500)")
])

# Intent: User requested refund up to $500
envelope = IntentEnvelope(
    goal="Assist customer with order dispute up to $500",
    requested_by=Requester(type="human", id="support_lead_42"),
    constraints={"maximum_refund": 500.0}
)
intent_bindings = [
    ConstraintBinding(constraint="maximum_refund", tool="issue_refund", arg_name="amount", op="lte", severity="BLOCK")
]
guardian = IntentGuardian(envelope, intent_bindings)

# Budget: $5.00 spend ceiling
budget = BudgetGuardian(max_cost=5.00)
```

### 3. Initialize Sidecar in Observe Mode (Phase 1)

Instantiate `Sidecar` in `observe` mode to audit actions without blocking execution:

```python
sidecar_observe = Sidecar(
    on_sidecar_failure="fail_closed",
    mode="observe",
    roles=["policy", "risk", "intent_guardian", "budget"],
    policy=policy,
    risk=risk,
    intent=guardian,
    budget=budget,
    risk_block_threshold="HIGH",
)

obs_read, obs_refund, obs_delete = attach(sidecar_observe, [read_order, issue_refund, delete_customer_record])

# Execute actions in Observe Mode
obs_read("ORD-999")
obs_refund("ORD-999", 850.0)  # Exceeds limit; logged as BLOCK but allowed to run in observe mode
```

### 4. Transition to Govern Mode (Phase 2)

Instantiate `Sidecar` in `govern` mode for active enforcement:

```python
sidecar_govern = Sidecar(
    on_sidecar_failure="fail_closed",
    mode="govern",
    roles=["policy", "risk", "intent_guardian", "budget"],
    policy=policy,
    risk=risk,
    intent=guardian,
    budget=BudgetGuardian(max_cost=5.00),
    risk_block_threshold="HIGH",
)

gov_read, gov_refund, gov_delete = attach(sidecar_govern, [read_order, issue_refund, delete_customer_record])

# Valid read order
gov_read("ORD-999")

# Unauthorized refund ($850.0) -> BLOCKED
try:
    gov_refund("ORD-999", 850.0)
except SidecarBlockedError as exc:
    print(f"🛑 BLOCKED BY SIDECAR: {exc}")

# Forbidden deletion -> BLOCKED
try:
    gov_delete("cust_1001")
except SidecarBlockedError as exc:
    print(f"🛑 BLOCKED BY SIDECAR: {exc}")
```

## Expected output

Run the official example script directly from the codebase:

```bash
python examples/governed_customer_support_agent.py
```

Console Output (excerpt — representative key lines are shown; a complete run additionally prints steps `1.2`, `1.4`, `2.2` and the "Sidecar Decisions Recorded in Observe Mode" list, all with the same allow/block behavior):

```
================================================================================
      GOVERNED CUSTOMER SUPPORT AGENT — SIDECAR USE CASE DEMO
================================================================================
--- PHASE 1: OBSERVE MODE (Monitoring & Logging Only) ---
1.1 Agent calls read_order('ORD-999'):
INFO [agentic_sidecar] [OBSERVE] ALLOW tool=read_order args={'order_id': 'ORD-999'} risk=LOW reason=...
  [EXEC] Executing read_order('ORD-999')...

1.3 Agent calls issue_refund('ORD-999', amount=850.0) [Exceeds Limit]:
ERROR [agentic_sidecar] [OBSERVE] BLOCK tool=issue_refund args={'order_id': 'ORD-999', 'amount': 850.0} risk=HIGH reason=Risk Evaluator: Refund exceeds standard support representative threshold ($500)
  [EXEC] Executing issue_refund('ORD-999', amount=$850.0)...

================================================================================
--- PHASE 2: GOVERN MODE (Active Policy & Intent Enforcement) ---
================================================================================
2.1 Agent calls read_order('ORD-999'):
  [EXEC] Executing read_order('ORD-999')...
  -> Result: {'order_id': 'ORD-999', 'customer_id': 'cust_1001', 'amount': 450.0, 'status': 'delivered'}

2.3 Agent calls issue_refund('ORD-999', amount=850.0) [Over-Limit Refund]:
ERROR [agentic_sidecar] [GOVERN] BLOCK tool=issue_refund args={'order_id': 'ORD-999', 'amount': 850.0} risk=HIGH reason=Risk Evaluator: Refund exceeds standard support representative threshold ($500)
  🛑 BLOCKED BY SIDECAR: Sidecar blocked 'issue_refund'({'order_id': 'ORD-999', 'amount': 850.0}): Risk Evaluator: Refund exceeds standard support representative threshold ($500)

2.4 Agent calls delete_customer_record('cust_1001') [Policy Violation]:
ERROR [agentic_sidecar] [GOVERN] BLOCK tool=delete_customer_record args={'customer_id': 'cust_1001'} risk=None reason=Policy Advisor: Account deletion requires explicit admin authorization
  🛑 BLOCKED BY SIDECAR: Sidecar blocked 'delete_customer_record'({'customer_id': 'cust_1001'}): Policy Advisor: Account deletion requires explicit admin authorization

In-memory Decision Summary:
Total Interceptions: 4
  Allowed Actions: 2
  Blocked Actions: 2
================================================================================
```

## Verify it worked

1. Confirm that Phase 1 (Observe Mode) logs `BLOCK` status while permitting function execution (`[EXEC]` printed).
2. Confirm that Phase 2 (Govern Mode) intercepts unauthorized calls before execution (`[EXEC]` not printed, `SidecarBlockedError` caught).
3. Inspect `sidecar_govern.decisions` to verify decision provenance for all 4 tool calls.

## Clean up

To remove the repository copy or clean the Python virtual environment:

```bash
deactivate
```

## Variations and next steps

- **Inspect Decision Provenance**: Access full decision histories via `sidecar.decisions` for audit exports.
- **Budget Escalation**: Combine Budget Guardian with human-in-the-loop escalation workflows.
- Explore full details in [Configuration Reference](https://deepagentlabs.io/agentic-sidecar/docs/configuration/) and [API Reference](https://deepagentlabs.io/agentic-sidecar/docs/api-reference/).

## Tested with

- agentic-sidecar 0.7.0, Python 3.12, Ubuntu 24.04, verified 2026-10-15
