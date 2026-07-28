from __future__ import annotations

from .schemas import CommitmentLevel, ContradictionAnalysis, SituationAnalysis, SolvabilityAnalysis, StrategicContext, StrategicRisk, TimingAnalysis


def _risk(level: str, reason: str, mitigation: str) -> dict[str, str]:
    return {"level": level, "reason": reason, "mitigation": mitigation}


def analyze_risk(
    context: StrategicContext,
    situation: SituationAnalysis,
    contradiction: ContradictionAnalysis,
    solvability: SolvabilityAnalysis,
    timing: TimingAnalysis,
    commitment: CommitmentLevel,
) -> StrategicRisk:
    direction_level = "high" if solvability.probability == "unknown" else "medium"
    if context.domain in {"content", "startup"}:
        direction_reason = "需求、差异化或具体场景尚未被充分验证。"
    else:
        direction_reason = "目标方向仍存在证据缺口。"

    timing_level = "high" if timing.timing == "observe" and commitment.level != "low" else "medium"
    if timing.timing == "test":
        timing_level = "medium"
    if timing.timing == "stop":
        timing_level = "high"

    resource_level = "high" if commitment.level == "high" else "medium" if commitment.level == "medium" else "low"
    sunk_level = "high" if context.user_bias == "sunk_cost_pressure" else "low"
    opp_level = "high" if commitment.level in {"high", "medium"} else "medium"
    opportunity_signals = ["副业", "主业", "每周", "20小时", "时间", "机会成本", "兼职"]
    if context.domain == "side_project" or any(signal in context.question for signal in opportunity_signals):
        opp_level = "high"

    risks = {
        "direction_risk": _risk(direction_level, direction_reason, "用低承诺试验验证主要假设。"),
        "timing_risk": _risk(timing_level, timing.reason, "先匹配证据强度与行动强度。"),
        "resource_risk": _risk(resource_level, commitment.resource_lock_in, "设定资源上限和退出路线。"),
        "sunk_cost_risk": _risk(sunk_level, "用户问题存在沉没成本信号。" if sunk_level == "high" else "未发现强沉没成本信号。", "把过去投入和未来边际收益分开。"),
        "opportunity_cost_risk": _risk(opp_level, "行动会占用可选择性和长期时间资源。", "比较替代方向，避免过早锁定。"),
    }
    order = ["resource_risk", "direction_risk", "opportunity_cost_risk", "timing_risk", "sunk_cost_risk"]
    rank = {"high": 3, "medium": 2, "low": 1, "unknown": 2}
    largest = max(order, key=lambda name: rank[risks[name]["level"]])
    if risks["sunk_cost_risk"]["level"] == "high":
        largest = "sunk_cost_risk"
    elif risks["opportunity_cost_risk"]["level"] == "high" and context.domain == "side_project":
        largest = "opportunity_cost_risk"

    return StrategicRisk(
        direction_risk=risks["direction_risk"],
        timing_risk=risks["timing_risk"],
        resource_risk=risks["resource_risk"],
        sunk_cost_risk=risks["sunk_cost_risk"],
        opportunity_cost_risk=risks["opportunity_cost_risk"],
        largest_risk=largest,
        risk_summary=f"最大战略风险是 {largest}：{risks[largest]['reason']}",
    )
