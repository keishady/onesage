from __future__ import annotations

from .audit import record_event
from .schemas import Decision, RiskLevel


def execute(decision: Decision, user_override: bool = False, *, decision_id: int | None = None) -> dict:
    """
    v0.2 still avoids real external side effects.
    It enforces policy, records an audit event, and returns a structured execution result.
    """
    policy = decision.policy

    if decision.risk_level == RiskLevel.L3_CRITICAL:
        result = {
            "executed": False,
            "result": "blocked",
            "message": "L3 critical action blocked. OneSage can generate a plan only.",
            "required_confirmations": 2,
            "safer_alternative": policy.safer_alternative if policy else decision.minimum_next_action,
        }
        record_event("execution_blocked", result, project_id=decision.project_id, decision_id=decision_id)
        return result

    if decision.human_confirm_required and not user_override:
        result = {
            "executed": False,
            "result": "needs_confirmation",
            "message": "This action needs human confirmation or override.",
            "required_confirmations": policy.confirmations_required if policy else 1,
            "minimum_next_action": decision.minimum_next_action,
        }
        record_event("execution_needs_confirmation", result, project_id=decision.project_id, decision_id=decision_id)
        return result

    result = {
        "executed": True,
        "result": "simulated_success",
        "action_type": decision.action_type.value,
        "risk_level": decision.risk_level.value,
        "should_act_now": decision.should_act_now,
        "model_route": decision.model_route.model_dump() if decision.model_route else None,
        "message": "Simulated execution only. No email, browser action, shell command, remote write, or payment was performed.",
    }
    record_event("execution_simulated", result, project_id=decision.project_id, decision_id=decision_id)
    return result
