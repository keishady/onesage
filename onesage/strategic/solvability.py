from __future__ import annotations

from .schemas import ContradictionAnalysis, SolvabilityAnalysis, StrategicContext


def analyze_solvability(context: StrategicContext, contradiction: ContradictionAnalysis) -> SolvabilityAnalysis:
    if context.user_bias == "sunk_cost_pressure" and context.history.get("decline_signals"):
        return SolvabilityAnalysis(
            solvable="unknown",
            influence_level="medium",
            required_resources={"time": "需要先复盘关键指标", "money": "不应继续加码", "skills": ["数据复盘", "收缩决策"], "data": ["留存", "转化", "增长趋势"]},
            time_cost="short",
            probability="unknown",
            worth_solving="unknown",
            recommendation="先冻结扩大投入，判断主要矛盾是否真的可解。",
        )

    if context.domain in {"content", "learning", "career"}:
        return SolvabilityAnalysis(
            solvable="yes" if context.domain in {"learning", "career"} else "partially",
            influence_level="high",
            required_resources={"time": "2-8 周低承诺验证", "money": "低到可控", "skills": contradiction.resource_focus, "data": contradiction.investigation_questions},
            time_cost="short" if context.domain in {"content", "learning"} else "medium",
            probability="medium",
            worth_solving="yes" if context.domain in {"learning", "career"} else "conditional",
            recommendation="可以通过低承诺试验验证主要矛盾，不应直接高承诺投入。",
        )

    if context.domain in {"startup", "side_project"}:
        return SolvabilityAnalysis(
            solvable="partially" if context.domain == "startup" else "unknown",
            influence_level="medium",
            required_resources={"time": "2-8 周验证", "money": "暂不建议大投入", "skills": contradiction.resource_focus, "data": contradiction.investigation_questions},
            time_cost="medium",
            probability="unknown",
            worth_solving="conditional" if context.domain == "startup" else "unknown",
            recommendation="先验证关键假设，证据不足时不应接受长期承诺。",
        )

    return SolvabilityAnalysis(
        solvable="unknown",
        influence_level="medium",
        required_resources={"time": "需要补充", "money": "需要补充", "skills": contradiction.resource_focus, "data": contradiction.investigation_questions},
        time_cost="uncertain",
        probability="unknown",
        worth_solving="unknown",
        recommendation="主要矛盾可解决性不清，先补事实或做低承诺试探。",
    )
