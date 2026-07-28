from __future__ import annotations

from .schemas import ModelRole, ModelRoute, RiskLevel


DEFAULT_ROUTES = {
    ModelRole.FAST_DRAFT: ("local", "rule-engine"),
    ModelRole.STRUCTURED_EXTRACTION: ("local", "schema-validator"),
    ModelRole.TOOL_PLANNING: ("local", "safe-planner"),
    ModelRole.VERIFY: ("local", "method-kernel"),
    ModelRole.FINAL_SYNTHESIS: ("local", "method-kernel"),
}

MERCURY_ROLES = {
    ModelRole.FAST_DRAFT,
    ModelRole.STRUCTURED_EXTRACTION,
    ModelRole.TOOL_PLANNING,
}


def route_for(role: ModelRole, *, risk_level: RiskLevel, prefer_mercury: bool = False) -> ModelRoute:
    if prefer_mercury and role in MERCURY_ROLES and risk_level != RiskLevel.L3_CRITICAL:
        return ModelRoute(
            role=role,
            provider="inception",
            model="mercury-coder-or-compatible",
            mercury_compatible=True,
            validation_required=True,
            reason=(
                "Use a Mercury/diffusion-style model only for low-latency draft, "
                "structured extraction, or tool planning. OneSage still validates the output."
            ),
        )

    provider, model = DEFAULT_ROUTES[role]
    return ModelRoute(
        role=role,
        provider=provider,
        model=model,
        mercury_compatible=False,
        validation_required=True,
        reason="Local deterministic route selected for safety and reproducibility.",
    )
