"""The Decision Gate: Policy Advisor, Risk Evaluator, and Budget Guardian.

Answers "are you permitted to do this?" (policy.py) and "how dangerous is
this action?" (risk.py) -- deliberately separate from `intent/`, which
answers the harder question "is this actually what the human asked you to
accomplish?" See README.md's "How the Decision Gate evaluates a decision"
and ROADMAP.md's Design Constraint 5 before adding a check here that's
really an intent question.

`policy.py` and `risk.py` are planned for v0.1 (rule-based, zero LLM calls).
`budget.py` is planned for v0.4. Not implemented yet.
"""
