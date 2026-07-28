from __future__ import annotations

from .schemas import ContradictionAnalysis, JudgmentConfidence, SituationAnalysis, SolvabilityAnalysis, StrategicContext, StrategicRisk, TimingAnalysis


def calculate_confidence(
    context: StrategicContext,
    situation: SituationAnalysis,
    contradiction: ContradictionAnalysis,
    solvability: SolvabilityAnalysis,
    timing: TimingAnalysis,
    risk: StrategicRisk,
) -> JudgmentConfidence:
    information = max(0.2, 1.0 - min(0.8, len(context.unknowns) * 0.12))
    fact_quality = 0.55 if len(context.known_facts) <= 2 else 0.68
    historical = 0.35 if not context.history.get("decline_signals") else 0.55
    contradiction_clarity = 0.78 if contradiction.primary_contradiction else 0.35
    timing_certainty = 0.7 if timing.timing in {"test", "stop"} else 0.55
    solvability_certainty = 0.7 if solvability.probability != "unknown" else 0.45

    breakdown = {
        "information_completeness": round(information, 2),
        "fact_quality": round(fact_quality, 2),
        "historical_case_support": round(historical, 2),
        "contradiction_clarity": round(contradiction_clarity, 2),
        "timing_certainty": round(timing_certainty, 2),
        "solvability_certainty": round(solvability_certainty, 2),
    }
    confidence = sum(breakdown.values()) / len(breakdown)
    if risk.largest_risk in {"resource_risk", "direction_risk"} and risk.model_dump()[risk.largest_risk]["level"] == "high":
        confidence -= 0.05

    factors = []
    if information < 0.55:
        factors.append("信息不完整")
    else:
        factors.append("基础信息可用于第一版判断")
    if solvability.probability == "unknown":
        factors.append("可解决性概率仍不明确")
    if context.competition.get("signals"):
        factors.append("存在竞争或同质化信号")
    if context.history.get("decline_signals"):
        factors.append("存在历史结果或增长停滞信号")

    return JudgmentConfidence(
        confidence=round(max(0.1, min(0.95, confidence)), 2),
        confidence_factors=factors,
        main_uncertainty=context.unknowns[0] if context.unknowns else "当前主要不确定性较低",
        confidence_breakdown=breakdown,
    )
