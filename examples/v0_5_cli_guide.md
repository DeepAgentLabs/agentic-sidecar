# v0.5.0 CLI Guide

The `agentic-sidecar` command-line tool provides real-time monitoring and live narration of agent execution.

## Installation

```bash
pip install agentic-sidecar
```

## Commands

### 1. Status Command

Display agent execution status with live updates, JSON output, and custom refresh intervals.

#### Single Status Snapshot
```bash
agentic-sidecar status
```

Output:
```
                    Sidecar Status
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric                      ┃ Value                         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 📋 Objective                │ Find the cheapest hotel       │
│ ⚙️  Current Step             │ Searching for options...      │
│ ✅ Completed Steps          │ 3                             │
│ 📞 Tool Calls               │ 7                             │
│ 💰 Budget Remaining         │ $45.50                        │
│ 🔤 Tokens Remaining         │ 2500                          │
└─────────────────────────────┴───────────────────────────────┘
```

#### Live Stream (Real-time Updates)
```bash
agentic-sidecar status --follow
```

Continuously updates every second, showing live agent execution. Press `Ctrl+C` to stop.

```
🔴 Live Status Stream
Refreshing every 1s — Press Ctrl+C to stop

                    Sidecar Status
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
...
[Updated at 14:32:45]

                    Sidecar Status
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
...
[Updated at 14:32:46]

^C
⏸️  Stream stopped by user
```

#### Custom Refresh Interval
```bash
# Refresh every 2 seconds
agentic-sidecar status --follow --interval 2

# Refresh every 5 seconds
agentic-sidecar status --follow -i 5
```

#### JSON Output
```bash
# Single snapshot as JSON
agentic-sidecar status --json

# Live JSON stream
agentic-sidecar status --follow --json
```

Output:
```json
{
  "timestamp": "2026-09-14T14:32:45.123456",
  "objective": "Find the cheapest hotel",
  "current_step": "Searching for options...",
  "steps_completed": 3,
  "tool_calls": 7,
  "blocked_decisions": 0,
  "paused_decisions": 1,
  "intent_violations": 0,
  "max_risk": "MEDIUM",
  "budget_remaining": 45.50,
  "tokens_remaining": 2500,
  "is_paused": true,
  "pause_reason": "Awaiting manager approval"
}
```

#### Combined Options
```bash
# Live JSON stream with 2-second interval
agentic-sidecar status --follow --json --interval 2

# Short form
agentic-sidecar status -f -j -i 2
```

### 2. Demo Command

Run an interactive demonstration of StatusNarrator capabilities.

```bash
agentic-sidecar demo
```

Output:
```
🎬 StatusNarrator Demo

Executing demo... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

  🔍 Searching for information
  ❓ Querying database
  📥 Retrieving records

🎬 Demo Status:
                    Sidecar Status
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
│ 📋 Objective                │ Find and book the cheapest   │
│                             │ hotel in NYC                 │
│ ⚙️  Current Step             │ Booking hotel...             │
│ ✅ Completed Steps          │ 3                            │
│ 📞 Tool Calls               │ 3                            │
│ 💰 Budget Remaining         │ $25.50                       │
│ 🔤 Tokens Remaining         │ 4500                         │
└─────────────────────────────┴───────────────────────────────┘
```

### 3. Version Command

Display the installed version.

```bash
agentic-sidecar version
```

Output:
```
agentic-sidecar 0.5.0
```

## Features

### Human-Readable Narration

Tool calls are automatically translated into readable narratives with emoji indicators:

| Tool Type | Narration | Emoji |
|-----------|-----------|-------|
| search | Searching for information | 🔍 |
| lookup | Looking up data | 🔎 |
| retrieve | Retrieving records | 📥 |
| query | Querying database | ❓ |
| create | Creating new record | ✍️ |
| update | Updating record | 🔄 |
| delete | Deleting record | 🗑️ |
| send | Sending message | 📤 |
| fetch | Fetching data | ⬇️ |
| call | Making call | 📞 |
| refund | Processing refund | 💰 |
| payment | Processing payment | 💳 |
| custom_action | Executing custom_action | ⚙️ |

### Decision Tracking

Status display shows decision outcomes:

- **✓ ALLOW**: Decision approved, execution continues
- **⚠ WARN**: Warning issued, action taken with caution
- **✗ BLOCK**: Decision blocked, action prevented
- **⏸ PAUSE**: Decision paused, awaiting human approval

### Risk Level Display

Color-coded risk indicators:

- **LOW**: 🟢 Green
- **MEDIUM**: 🟡 Yellow
- **HIGH**: 🔴 Red

### Budget & Token Monitoring

Real-time tracking of remaining costs and tokens:

```
💰 Budget Remaining    $45.50
🔤 Tokens Remaining    2500
```

## Use Cases

### 1. Monitor Long-Running Agent
```bash
# Watch agent execution in real-time
agentic-sidecar status --follow
```

### 2. Integrate with Monitoring Tools
```bash
# Export JSON for parsing by other tools
agentic-sidecar status --json | jq '.budget_remaining'

# Log to file
agentic-sidecar status --json > status.json
```

### 3. Custom Refresh Rates
```bash
# Fast updates for critical operations
agentic-sidecar status -f -i 1

# Slow updates for background monitoring
agentic-sidecar status -f -i 10
```

### 4. Test Integration
```bash
# Run demo to verify installation
agentic-sidecar demo

# Check version compatibility
agentic-sidecar version
```

## Python API

To use StatusNarrator programmatically in your agent:

```python
from agentic_sidecar import StatusNarrator, Decision

narrator = StatusNarrator()

# Set objective
narrator.set_objective("Book a hotel")

# Record tool calls
call = narrator.record_tool_call(
    "search",
    {"query": "hotels in NYC"},
    decision=Decision(status="ALLOW", risk="LOW", reason="ok")
)

# Get status snapshot
status = narrator.get_status(
    current_budget_remaining=50.0,
    current_tokens_remaining=3000
)

# Display narrative
print(narrator.get_narrative())
```

## Examples

See [`examples/v0_5_status_narration.py`](v0_5_status_narration.py) for comprehensive code examples covering:

- Basic narration
- Decision tracking
- Budget monitoring
- Intent compliance
- Pause/resume workflows
- Complete workflows

## Troubleshooting

### Command Not Found
```bash
# Ensure agentic-sidecar is installed
pip install agentic-sidecar

# Verify installation
agentic-sidecar version
```

### No Status Displayed
```bash
# The CLI creates a demo narrator if none is running
# In production, integrate with your agent:
from agentic_sidecar import StatusNarrator
```

### JSON Parse Errors
```bash
# Validate JSON output
agentic-sidecar status --json | python -m json.tool
```

## Related

- **v0.4.0**: Budget Guardian, Human Escalation, Decision Provenance
- **v0.5.0**: Status Narration, CLI
- **Python API**: See [README.md](../README.md#python-api-implemented)
- **Examples**: See [`examples/`](./)
