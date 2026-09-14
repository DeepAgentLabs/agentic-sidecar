"""v0.4 Web Demo - No external dependencies, uses only Python stdlib.

Run with:
    python demo_web_server.py

Then open: http://localhost:5000 in your browser
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from agentic_sidecar import Sidecar, BudgetGuardian
from agentic_sidecar.core.context import DecisionContext
from agentic_sidecar.gate.policy import PolicyAdvisor, PolicyRule
from agentic_sidecar.intent.alignment import ConstraintBinding, IntentGuardian
from agentic_sidecar.intent.envelope import IntentEnvelope, Requester

# Global Sidecar instances
budget = BudgetGuardian(max_cost=10.0)
sidecar = Sidecar(
    on_sidecar_failure="fail_closed",
    policy=PolicyAdvisor(
        rules=[
            PolicyRule(tool="delete_*", effect="deny", reason="Destructive ops blocked"),
            PolicyRule(tool="system_*", effect="deny", reason="System ops restricted"),
        ]
    ),
    budget=budget,
    roles=["policy", "risk", "budget"],
    mode="observe",
)

# Intent Guardian setup
envelope = IntentEnvelope(
    goal="refund_customer",
    requested_by=Requester(type="human", id="user123"),
    constraints={"maximum_refund": 500},
)
binding = ConstraintBinding(
    constraint="maximum_refund",
    tool="issue_refund",
    arg_name="amount",
    op="lte",
)
intent_guardian = IntentGuardian(envelope, [binding])

HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>agentic-sidecar v0.4 Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1 { color: #333; font-size: 28px; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 16px; }
        .version {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-top: 10px;
        }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        .input-group { margin-bottom: 15px; }
        label {
            display: block;
            color: #555;
            font-weight: 600;
            margin-bottom: 5px;
            font-size: 14px;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        button {
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            width: 100%;
            transition: background 0.3s;
        }
        button:hover { background: #5568d3; }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #ddd;
            display: none;
            font-size: 13px;
        }
        .result.show { display: block; }
        .result.allow { background: #d4edda; border-left-color: #28a745; color: #155724; }
        .result.block { background: #f8d7da; border-left-color: #dc3545; color: #721c24; }
        .result.pause { background: #fff3cd; border-left-color: #ffc107; color: #856404; }
        .result.warn { background: #cfe2ff; border-left-color: #0d6efd; color: #084298; }
        .result-title { font-weight: bold; margin-bottom: 10px; font-size: 16px; }
        .result-detail { margin: 8px 0; }
        .budget-bar {
            width: 100%;
            height: 20px;
            background: #eee;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .budget-bar-fill {
            height: 100%;
            background: #28a745;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 11px;
            font-weight: bold;
        }
        .budget-bar-fill.warning { background: #ffc107; }
        .budget-bar-fill.danger { background: #dc3545; }
        .info-box {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 12px;
            margin: 10px 0;
            font-size: 13px;
            color: #666;
        }
        .decision-outcomes {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        .outcome-badge {
            text-align: center;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
            background: #d4edda;
            color: #28a745;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>agentic-sidecar v0.4 Demo</h1>
            <p class="subtitle">Interactive showcase of Budget Guardian, Policy Blocking, and Intent Validation</p>
            <span class="version">v0.4.0</span>
        </header>

        <div class="grid">
            <div class="card">
                <h2>Budget Guardian</h2>
                <p style="color: #666; margin-bottom: 15px; font-size: 13px;">Test cost/token tracking and limits</p>
                <div class="info-box">
                    <strong>Budget Limit:</strong> $10.00<br>
                    <strong>Current Cost:</strong> <span id="current-cost">$0.00</span>
                </div>
                <div class="budget-bar">
                    <div class="budget-bar-fill" id="budget-bar" style="width: 0%">0%</div>
                </div>
                <div class="input-group">
                    <label>Add Cost ($)</label>
                    <input type="number" id="cost-input" placeholder="e.g., 2.50" step="0.01" value="2.50">
                </div>
                <div class="input-group">
                    <label>Tool Name</label>
                    <input type="text" id="budget-tool" placeholder="e.g., search_docs" value="query_database">
                </div>
                <button onclick="testBudget()">Test Budget Decision</button>
                <div class="result" id="budget-result"></div>
            </div>

            <div class="card">
                <h2>Policy Blocking</h2>
                <p style="color: #666; margin-bottom: 15px; font-size: 13px;">Test dangerous operation blocking</p>
                <div class="info-box">
                    <strong>Blocked Tools:</strong> delete_*, system_*
                </div>
                <div class="input-group">
                    <label>Tool Name</label>
                    <select id="policy-tool">
                        <option value="read_order">read_order (allowed)</option>
                        <option value="delete_customer">delete_customer (blocked)</option>
                        <option value="system_shutdown">system_shutdown (blocked)</option>
                        <option value="query_database">query_database (allowed)</option>
                    </select>
                </div>
                <button onclick="testPolicy()">Test Policy Decision</button>
                <div class="result" id="policy-result"></div>
            </div>

            <div class="card">
                <h2>Intent Guardian</h2>
                <p style="color: #666; margin-bottom: 15px; font-size: 13px;">Test constraint validation</p>
                <div class="info-box">
                    <strong>Goal:</strong> refund_customer<br>
                    <strong>Max Refund:</strong> $500
                </div>
                <div class="input-group">
                    <label>Refund Amount ($)</label>
                    <input type="number" id="refund-amount" placeholder="e.g., 300" value="300" min="0" max="2000">
                </div>
                <div class="input-group">
                    <label>Customer ID</label>
                    <input type="text" id="customer-id" placeholder="e.g., C123" value="C123">
                </div>
                <button onclick="testIntent()">Test Refund Decision</button>
                <div class="result" id="intent-result"></div>
            </div>

            <div class="card">
                <h2>v0.4 Decision Outcomes</h2>
                <p style="color: #666; margin-bottom: 15px; font-size: 13px;">All seven outcomes are now implemented</p>
                <div class="decision-outcomes">
                    <div class="outcome-badge">ALLOW</div>
                    <div class="outcome-badge">WARN</div>
                    <div class="outcome-badge">BLOCK</div>
                    <div class="outcome-badge">CHALLENGE</div>
                    <div class="outcome-badge">REPLAN</div>
                    <div class="outcome-badge">PAUSE</div>
                    <div class="outcome-badge">ESCALATE</div>
                </div>
                <div class="info-box">
                    <strong>Implemented Features:</strong>
                    <ul style="margin-top: 10px; padding-left: 20px;">
                        <li>Budget Guardian</li>
                        <li>Policy Advisor</li>
                        <li>Risk Evaluator</li>
                        <li>Intent Guardian</li>
                        <li>Decision Gate</li>
                        <li>Provenance/Audit Trail</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function callAPI(endpoint, data) {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return response.json();
        }

        function showResult(elementId, decision, statusClass) {
            const result = document.getElementById(elementId);
            result.className = 'result show ' + statusClass;
            result.innerHTML = `
                <div class="result-title">Status: ${decision.status}</div>
                <div class="result-detail"><strong>Risk:</strong> ${decision.risk || 'N/A'}</div>
                <div class="result-detail"><strong>Reason:</strong> ${decision.reason}</div>
                ${decision.escalation_required ? '<div class="result-detail" style="color: red; font-weight: bold;">ESCALATION REQUIRED</div>' : ''}
            `;
        }

        function updateBudgetDisplay(cost) {
            const budget = 10.0;
            const percent = Math.min((cost / budget) * 100, 100);
            const bar = document.getElementById('budget-bar');
            bar.style.width = percent + '%';
            bar.textContent = Math.round(percent) + '%';
            if (percent > 90) {
                bar.className = 'budget-bar-fill danger';
            } else if (percent > 70) {
                bar.className = 'budget-bar-fill warning';
            } else {
                bar.className = 'budget-bar-fill';
            }
            document.getElementById('current-cost').textContent = '$' + cost.toFixed(2);
        }

        async function testBudget() {
            const cost = parseFloat(document.getElementById('cost-input').value);
            const tool = document.getElementById('budget-tool').value;
            if (!cost || cost <= 0) { alert('Enter valid cost'); return; }
            const data = await callAPI('/api/budget', { cost, tool });
            updateBudgetDisplay(data.current_cost);
            showResult('budget-result', data.decision, data.decision.status.toLowerCase());
        }

        async function testPolicy() {
            const tool = document.getElementById('policy-tool').value;
            const data = await callAPI('/api/policy', { tool });
            showResult('policy-result', data.decision, data.decision.status.toLowerCase());
        }

        async function testIntent() {
            const amount = parseFloat(document.getElementById('refund-amount').value);
            const customerId = document.getElementById('customer-id').value;
            if (!amount || amount < 0) { alert('Enter valid amount'); return; }
            const data = await callAPI('/api/intent', { amount, customer_id: customerId });
            showResult('intent-result', data.decision, data.decision.status.toLowerCase());
        }

        updateBudgetDisplay(0);
    </script>
</body>
</html>"""

class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode())

        if self.path == '/api/budget':
            cost = data.get('cost', 0)
            tool = data.get('tool', 'unknown')
            budget.record_invocation(cost=cost)
            context = DecisionContext(tool_name=tool, tool_args={"cost": cost})
            decision = sidecar.evaluate(context)
            response = {
                "decision": {
                    "status": decision.status,
                    "risk": decision.risk,
                    "reason": decision.reason,
                    "escalation_required": decision.escalation_required,
                },
                "current_cost": budget.current_cost,
            }

        elif self.path == '/api/policy':
            tool = data.get('tool', 'unknown')
            context = DecisionContext(tool_name=tool, tool_args={})
            decision = sidecar.evaluate(context)
            response = {
                "decision": {
                    "status": decision.status,
                    "risk": decision.risk,
                    "reason": decision.reason,
                    "escalation_required": decision.escalation_required,
                }
            }

        elif self.path == '/api/intent':
            amount = data.get('amount', 0)
            customer_id = data.get('customer_id', 'unknown')
            sidecar_intent = Sidecar(
                on_sidecar_failure="fail_closed",
                intent=intent_guardian,
                roles=["intent_guardian"],
                mode="observe",
            )
            context = DecisionContext(
                tool_name="issue_refund",
                tool_args={"customer_id": customer_id, "amount": amount}
            )
            decision = sidecar_intent.evaluate(context)
            response = {
                "decision": {
                    "status": decision.status,
                    "risk": decision.risk,
                    "reason": decision.reason,
                    "escalation_required": decision.escalation_required,
                }
            }
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        return

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("agentic-sidecar v0.4 Web Demo")
    print("=" * 70)
    print("\n🚀 Starting server on http://localhost:5000")
    print("\nFeatures:")
    print("  ✓ Budget Guardian - Test cost tracking and PAUSE on budget exceed")
    print("  ✓ Policy Blocking - Test dangerous operation blocking")
    print("  ✓ Intent Guardian - Test constraint validation")
    print("  ✓ All 7 Decision Outcomes - ALLOW/WARN/BLOCK/CHALLENGE/REPLAN/PAUSE/ESCALATE")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 70 + "\n")

    server = HTTPServer(('127.0.0.1', 5000), DemoHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        server.server_close()
