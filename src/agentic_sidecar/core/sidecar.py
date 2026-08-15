"""The `Sidecar` class -- owns module configuration (which of Policy/Risk/
Intent/Critic/Judge/Budget are enabled) and the required `on_sidecar_failure`
setting.

v0.1 wired up Policy Advisor + Risk Evaluator, in Observe mode. v0.2 adds
Intent Guardian and Govern mode: the Decision Gate now computes a `WARN`
outcome (intent-drift findings not severe enough to block) alongside
`ALLOW`/`BLOCK`, and `mode="govern"` is available for an adapter to
actually enforce a `BLOCK` rather than only logging it (see
`agentic_sidecar.adapters.langgraph`). `on_sidecar_failure:
fail_open | fail_closed` has no default: every Decision Gate evaluation
must resolve even when the Sidecar itself errors (ROADMAP.md's Design
Constraint 3).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Literal

from agentic_sidecar.core.context import DecisionContext, HistoryEntry
from agentic_sidecar.core.decision import Decision, DecisionStatus, RiskLevel
from agentic_sidecar.gate.policy import PolicyAdvisor
from agentic_sidecar.gate.risk import RISK_ORDER, RiskEvaluator
from agentic_sidecar.intent.alignment import AlignmentResult, IntentGuardian

logger = logging.getLogger("agentic_sidecar")

SidecarFailureMode = Literal["fail_open", "fail_closed"]
SidecarMode = Literal["observe", "govern"]
DecisionHook = Callable[[DecisionContext], Decision]

_SUPPORTED_ROLES = frozenset({"policy", "risk", "intent_guardian"})
_KNOWN_FUTURE_ROLES: dict[str, str] = {
    "planner": "v0.3",
    "critic": "v0.3",
    "judge": "v0.3",
    "budget": "v0.4",
}


class Sidecar:
    """Owns the Decision Gate: Policy Advisor, Risk Evaluator, and (v0.2)
    Intent Guardian, combined into a single `Decision` per proposed action.

    `on_sidecar_failure` is a required keyword argument with no default --
    pick `"fail_closed"` unless you have a specific reason to fail open (see
    ROADMAP.md's Design Constraint 3: anything that reaches a Decision Gate
    at all is, by definition, a decision boundary worth being conservative
    about).

    `mode="observe"` (the default) logs every `Decision` but enforces
    nothing. `mode="govern"` makes a `BLOCK` real -- but only once an
    adapter acts on it (`core/` computes decisions, it doesn't stop calls;
    see `agentic_sidecar.core.exceptions.SidecarBlockedError` and
    `agentic_sidecar.adapters.langgraph`).

    v0.1 has no `attach()` method here: routing a specific framework's
    tool-call surface through `evaluate()` is an adapter's job, not core's
    (AGENTS.md's Package Boundaries -- `core/` must not import from
    `adapters/`). See `agentic_sidecar.adapters.langgraph.attach()`.
    """

    def __init__(
        self,
        *,
        on_sidecar_failure: SidecarFailureMode,
        policy: PolicyAdvisor | None = None,
        risk: RiskEvaluator | None = None,
        intent: IntentGuardian | None = None,
        risk_block_threshold: RiskLevel = "HIGH",
        mode: SidecarMode = "observe",
        roles: Sequence[str] | None = None,
    ) -> None:
        if on_sidecar_failure not in ("fail_open", "fail_closed"):
            raise ValueError(
                f"on_sidecar_failure={on_sidecar_failure!r} is invalid -- it "
                "is a required setting with no default and must be "
                "'fail_open' or 'fail_closed' (ROADMAP.md's Design "
                "Constraint 3). 'fail_closed' is the recommended default."
            )
        if mode not in ("observe", "govern"):
            raise ValueError(
                f"mode={mode!r} is invalid -- must be 'observe' (logs "
                "decisions, enforces nothing) or 'govern' (a BLOCK is "
                "actually enforced by the attached adapter). See "
                "ROADMAP.md's Operating modes."
            )
        if risk_block_threshold not in RISK_ORDER:
            raise ValueError(
                f"risk_block_threshold={risk_block_threshold!r} is invalid "
                f"-- must be one of {list(RISK_ORDER)!r}. An unrecognized "
                "threshold would otherwise only surface as a KeyError "
                "inside evaluate(), silently resolved via "
                "on_sidecar_failure instead of failing fast here."
            )

        self.on_sidecar_failure = on_sidecar_failure
        self.policy = policy or PolicyAdvisor()
        self.risk = risk or RiskEvaluator()
        self.risk_block_threshold = risk_block_threshold
        self.mode = mode
        self.roles = self._validate_roles(roles)
        self.decisions: list[tuple[DecisionContext, Decision]] = []
        self._hook: DecisionHook | None = None
        self.intent: IntentGuardian | None = None
        self.set_intent(intent)

    @staticmethod
    def _validate_roles(roles: Sequence[str] | None) -> tuple[str, ...]:
        resolved = tuple(roles) if roles is not None else ("policy", "risk")
        for role in resolved:
            if role in _SUPPORTED_ROLES:
                continue
            if role in _KNOWN_FUTURE_ROLES:
                raise NotImplementedError(
                    f"role={role!r} is not implemented until "
                    f"{_KNOWN_FUTURE_ROLES[role]} -- see ROADMAP.md's build "
                    f"order. Currently supported: {sorted(_SUPPORTED_ROLES)}."
                )
            raise ValueError(
                f"Unknown role {role!r}. Currently supported: {sorted(_SUPPORTED_ROLES)}."
            )
        return resolved

    def set_intent(self, intent: IntentGuardian | None) -> None:
        """Set (or clear) the active `IntentGuardian` -- separate from
        `__init__` because a long-lived Sidecar is expected to serve one
        `IntentEnvelope` per task, not one for its whole lifetime (concept.md
        §6: the envelope is created "when a user initiates a task").

        Raises if `intent` is given but `"intent_guardian"` isn't in
        `self.roles` -- a `Sidecar` that would silently never consult the
        guardian you just handed it is exactly the kind of silent gap
        ROADMAP.md's Design Constraint 3 warns against for
        `on_sidecar_failure`, and the same principle applies here. The
        reverse (role enabled, no envelope yet) is *not* an error: a
        multi-task Sidecar may legitimately start before its first
        envelope arrives.
        """
        if intent is not None and "intent_guardian" not in self.roles:
            raise ValueError(
                "intent=... was given but 'intent_guardian' is not in "
                f"roles={list(self.roles)!r} -- it would never be "
                "consulted. Add 'intent_guardian' to roles, or don't pass "
                "intent."
            )
        self.intent = intent

    def before_tool_call(self, func: DecisionHook) -> DecisionHook:
        """Register a custom decision hook, overriding the default
        Policy + Risk + Intent Guardian evaluation for every subsequent
        `evaluate()` call.

        ```python
        @sidecar.before_tool_call
        def evaluate_action(context: DecisionContext) -> Decision:
            if context.tool_name == "delete_database":
                return Decision(status="BLOCK", risk="HIGH", reason="never")
            return Decision(status="ALLOW", risk="LOW", reason="ok")
        ```

        Mirrors the shape sketched in README.md's Planned Python API. Once
        registered, the hook fully replaces the built-in Decision Gate
        modules for every `evaluate()` call -- there is no v0.2 mechanism
        to run both a custom hook and the built-in modules together. The
        hook still receives a context with `intent`/`history` already
        injected (see `evaluate()`).
        """
        self._hook = func
        return func

    def evaluate(self, context: DecisionContext) -> Decision:
        """Evaluate one proposed action and return a `Decision`.

        Injects the active intent snapshot and this Sidecar's decision
        history into `context` first (concept.md §7, Intent Injection) --
        the caller only needs to supply `tool_name`/`tool_args`. This
        mutates the `context` object the caller passed in, in place (rather
        than evaluating a copy) -- `DecisionContext` is deliberately not
        frozen for exactly this reason, and it means a caller (e.g. an
        adapter constructing `SidecarBlockedError`) sees the fully-injected
        context on its own reference after `evaluate()` returns, not the
        bare one it originally built. Always resolves, per
        `on_sidecar_failure`, even if the registered hook (or the default
        evaluation) raises. Every call is recorded in `self.decisions`
        regardless of outcome. Never raises for a `BLOCK` decision itself,
        in either mode -- that a `BLOCK` should actually stop the call is
        enforced by the attached adapter in Govern mode, not by
        `evaluate()` (see `agentic_sidecar.core.exceptions.SidecarBlockedError`).
        """
        self._inject(context)
        try:
            evaluator = self._hook or self._default_evaluate
            decision = evaluator(context)
        except Exception as exc:  # noqa: BLE001 -- deliberate, see Design Constraint 3
            decision = self._on_failure(context, exc)
        self._log_decision(context, decision)
        self.decisions.append((context, decision))
        return decision

    def _inject(self, context: DecisionContext) -> None:
        history = [
            HistoryEntry(tool_name=c.tool_name, tool_args=c.tool_args, status=d.status)
            for c, d in self.decisions
        ]
        intent_snapshot = self.intent.envelope.to_snapshot() if self.intent is not None else None
        context.intent = intent_snapshot
        context.history = history

    def _default_evaluate(self, context: DecisionContext) -> Decision:
        policy_result = None
        if "policy" in self.roles:
            policy_result = self.policy.evaluate(context)
            if policy_result.effect == "deny":
                return Decision(
                    status="BLOCK",
                    risk=None,
                    reason=f"Policy Advisor: {policy_result.reason}",
                )

        risk_result = None
        if "risk" in self.roles:
            risk_result = self.risk.evaluate(context)
            if RISK_ORDER[risk_result.risk] >= RISK_ORDER[self.risk_block_threshold]:
                return Decision(
                    status="BLOCK",
                    risk=risk_result.risk,
                    reason=(
                        f"Risk Evaluator: {risk_result.reason} "
                        f"(risk >= block threshold '{self.risk_block_threshold}')"
                    ),
                )

        alignment_result: AlignmentResult | None = None
        if "intent_guardian" in self.roles and self.intent is not None:
            alignment_result = self.intent.evaluate(context)
            if alignment_result.status == "BLOCK":
                return Decision(
                    status="BLOCK",
                    risk=risk_result.risk if risk_result else None,
                    reason=f"Intent Guardian: {alignment_result.reason}",
                )

        reasons = [
            f"Policy Advisor: {policy_result.reason}" if policy_result else None,
            f"Risk Evaluator: {risk_result.reason}" if risk_result else None,
            f"Intent Guardian: {alignment_result.reason}" if alignment_result else None,
        ]
        reason = "; ".join(r for r in reasons if r) or (
            "No Decision Gate modules enabled in `roles`; defaulting to ALLOW."
        )
        status: DecisionStatus = (
            "WARN" if alignment_result and alignment_result.status == "WARN" else "ALLOW"
        )
        return Decision(
            status=status,
            risk=risk_result.risk if risk_result else None,
            reason=reason,
        )

    def _on_failure(self, context: DecisionContext, exc: Exception) -> Decision:
        status: Literal["ALLOW", "BLOCK"] = (
            "ALLOW" if self.on_sidecar_failure == "fail_open" else "BLOCK"
        )
        logger.error(
            "Sidecar evaluation failed for tool '%s': %s", context.tool_name, exc, exc_info=exc
        )
        return Decision(
            status=status,
            risk=None,
            reason=(
                f"Sidecar evaluation raised {exc.__class__.__name__}: {exc}. "
                f"Resolved via on_sidecar_failure='{self.on_sidecar_failure}'."
            ),
        )

    def _log_decision(self, context: DecisionContext, decision: Decision) -> None:
        level = logging.WARNING if decision.status != "ALLOW" else logging.INFO
        logger.log(
            level,
            "[%s] %s tool=%s args=%s risk=%s reason=%s",
            self.mode.upper(),
            decision.status,
            context.tool_name,
            context.tool_args,
            decision.risk,
            decision.reason,
        )
