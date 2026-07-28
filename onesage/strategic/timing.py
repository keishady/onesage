from __future__ import annotations

from .schemas import ContradictionAnalysis, SituationAnalysis, SolvabilityAnalysis, StrategicContext, TimingAnalysis


TIMING_LABELS = {"act": "行动", "test": "试探", "observe": "观察", "stop": "停止"}


def analyze_timing(
    context: StrategicContext,
    situation: SituationAnalysis,
    contradiction: ContradictionAnalysis,
    solvability: SolvabilityAnalysis,
) -> TimingAnalysis:
    if solvability.solvable == "no" or solvability.worth_solving == "no":
        timing = "stop"
        reason = "主要矛盾不可解或不值得解决，继续投入会放大损失。"
    elif context.user_bias == "sunk_cost_pressure" and situation.situation_stage == "decline":
        timing = "observe"
        reason = "存在沉没成本和衰退信号，不能直接继续，应先复盘未来边际收益。"
    elif solvability.probability == "unknown" or context.ambiguity >= 0.65:
        timing = "observe"
        reason = "关键信息不足，当前不支持高承诺行动。"
    elif situation.situation_stage == "breakout" and solvability.probability in {"high", "medium"}:
        timing = "test"
        reason = "可能存在行动窗口，但仍应先用小样本确认主要矛盾。"
    elif solvability.solvable in {"yes", "partially"}:
        timing = "test"
        reason = "主要矛盾可被用户影响，但证据仍不足以支持直接扩大投入。"
    else:
        timing = "observe"
        reason = "时机不清，优先补事实。"

    if timing == "test":
        action_window = "2-8 周或一个最小样本周期"
        cost_of_acting = "低承诺试验成本可控，但扩大投入会放大战略风险。"
        cost_of_waiting = "等待会损失少量学习机会。"
        reversibility = "high"
    elif timing == "observe":
        action_window = "补齐关键事实后重新判断"
        cost_of_acting = "现在行动可能建立在错误假设上。"
        cost_of_waiting = "等待成本低于错误行动成本。"
        reversibility = "medium"
    elif timing == "stop":
        action_window = "立即停止扩大投入"
        cost_of_acting = "继续行动可能放大资源损失和机会成本。"
        cost_of_waiting = "等待可能延迟止损。"
        reversibility = "low"
    else:
        action_window = "当前窗口"
        cost_of_acting = "行动成本可控。"
        cost_of_waiting = "等待可能错过机会窗口。"
        reversibility = "medium"

    return TimingAnalysis(
        timing=timing,
        timing_label=TIMING_LABELS[timing],
        reason=reason,
        action_window=action_window,
        cost_of_acting=cost_of_acting,
        cost_of_waiting=cost_of_waiting,
        reversibility=reversibility,
        signals_to_watch=contradiction.investigation_questions[:4],
        failure_mode="把当前时机判断升级为过大承诺，跳过复盘和停止条件。",
    )
