# Core concepts

| Concept | Meaning |
| --- | --- |
| DecisionContext | Describes the proposed action before execution. |
| Observe | Records decisions while wrapped calls can still execute. |
| Govern | Enforces decisions at dispatch: proceed, block, resolve, or suspend as configured. |
| Role activation | Supplying a module is not sufficient if its role is not enabled. |
| Failure policy | Explicitly decide whether an error in supervision fails open or closed. |
| Intent lifecycle | Bind constraints to the current task, replace intent between tasks, and manage budgets separately. |
