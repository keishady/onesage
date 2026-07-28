from __future__ import annotations

from .schemas import Decision, RiskLevel

OVERRIDE_PHRASE = "确认override并承担风险"


def override_allowed(decision: Decision, phrase: str) -> tuple[bool, str]:
    if decision.risk_level == RiskLevel.L3_CRITICAL:
        return False, "L3 critical actions cannot be overridden in v0.2. Generate a plan and approval checklist only."

    if not decision.override_allowed:
        return False, "This decision does not allow override."

    if phrase.strip() != OVERRIDE_PHRASE:
        return False, f"Override phrase mismatch. Required phrase: {OVERRIDE_PHRASE}"

    return True, "Override accepted."
