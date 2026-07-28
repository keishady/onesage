from __future__ import annotations

from .schemas import SituationAnalysis, StrategicContext


STAGE_LABELS = {
    "emergence": "萌芽期",
    "breakout": "爆发期",
    "competition": "竞争期",
    "decline": "衰退期",
    "unknown": "未知期",
}


def analyze_situation(context: StrategicContext) -> SituationAnalysis:
    evidence: list[str] = []
    key_forces: list[str] = []
    decline_signals = context.history.get("decline_signals", [])
    competition_signals = context.competition.get("signals", [])

    if context.user_bias == "sunk_cost_pressure" and decline_signals:
        stage = "decline"
        evidence.append("出现增长停滞/失败信号，并伴随沉没成本压力。")
        key_forces.extend(["投入产出下降", "沉没成本压力", "收缩或转向压力"])
        risk = "可能把沉没成本误当作继续投入的理由。"
    elif decline_signals:
        stage = "decline"
        evidence.append("用户问题包含增长停滞、失败或下滑信号。")
        key_forces.extend(["增长放缓", "继续投入风险", "复盘需求"])
        risk = "可能把短期波动误判为结构性衰退。"
    elif competition_signals:
        stage = "competition"
        evidence.append("用户问题包含竞争、同质化或供给密集信号。")
        key_forces.extend(["竞争加剧", "差异化压力", "注意力或用户选择成本上升"])
        risk = "可能把竞争期误判为衰退期，从而过早放弃。"
    elif any("机会窗口" in fact or "增长信号" in fact for fact in context.known_facts):
        stage = "breakout"
        evidence.append("用户问题包含机会窗口或增长信号。")
        key_forces.extend(["需求增长", "速度窗口", "资源承接压力"])
        risk = "可能把短期红利误判为长期趋势。"
    elif context.domain in {"learning", "career"}:
        stage = "emergence"
        evidence.append("用户处于能力建设或方向探索阶段。")
        key_forces.extend(["学习曲线", "反馈机制", "能力验证"])
        risk = "可能因早期挫败过早放弃。"
    else:
        stage = "unknown"
        evidence.append("当前问题缺少足够阶段信号。")
        key_forces.extend(["信息缺口", "阶段不确定"])
        risk = "可能在阶段不清时过早行动。"

    confidence = {
        "decline": 0.68,
        "competition": 0.72,
        "breakout": 0.62,
        "emergence": 0.58,
        "unknown": 0.42,
    }[stage]
    if context.ambiguity >= 0.7:
        confidence -= 0.12

    return SituationAnalysis(
        situation_stage=stage,
        stage_label=STAGE_LABELS[stage],
        confidence=round(max(0.1, confidence), 2),
        evidence=evidence,
        uncertainties=context.unknowns[:4],
        key_forces=list(dict.fromkeys(key_forces)),
        risk_of_misreading=risk,
    )
