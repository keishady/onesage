from __future__ import annotations

from .schemas import CommitmentLevel, ContradictionAnalysis, JudgmentConfidence, SituationAnalysis, SolvabilityAnalysis, StrategicAdvice, StrategicContext, StrategicRisk, TimingAnalysis


def _small_test_action(context: StrategicContext, contradiction: ContradictionAnalysis) -> str:
    if context.domain == "content":
        return "用 2-3 个差异化方向做 10-20 条低成本内容，记录点击率、完播率、评论质量和订阅转化。"
    if context.domain == "startup":
        return "选择一个垂直场景，访谈 10-15 个目标用户，并用低成本原型验证真实需求。"
    if context.domain == "career":
        return "保留当前现金流，用 6-8 周完成 1-2 个作品集项目，并找从业者反馈。"
    if context.domain == "learning":
        return "用 4 周完成 3-4 个小项目，记录卡点、独立完成度和兴趣变化。"
    if context.domain == "side_project":
        return "只接受 2 周试运行，明确分工、目标用户、收益模型和退出机制。"
    return "先做一个低成本、可撤回的小样本试验，验证主要矛盾是否成立。"


def make_advice(
    context: StrategicContext,
    situation: SituationAnalysis,
    contradiction: ContradictionAnalysis,
    solvability: SolvabilityAnalysis,
    timing: TimingAnalysis,
    commitment: CommitmentLevel,
    risk: StrategicRisk,
    confidence: JudgmentConfidence,
) -> StrategicAdvice:
    if solvability.solvable == "no" or solvability.worth_solving == "no" or timing.timing == "stop":
        recommendation = "D_stop"
        plain = "停止扩大投入，先收缩损失并复盘是否存在可转向方向。"
    elif timing.timing == "observe" and commitment.level in {"medium", "high"}:
        recommendation = "C_observe"
        plain = "现在不适合接受中高承诺行动，先补齐关键事实。"
    elif timing.timing == "observe" and confidence.confidence < 0.5:
        recommendation = "C_observe"
        plain = "信息不足，先观察和补事实，不要直接推进。"
    elif timing.timing == "act" and confidence.confidence >= 0.85 and commitment.level != "high":
        recommendation = "A_act_now"
        plain = "可以行动，但仍需限定范围和复盘条件。"
    else:
        recommendation = "B_small_test"
        plain = "适合小规模试验，不适合直接扩大投入。"

    minimum_next_action = _small_test_action(context, contradiction)
    if recommendation == "C_observe":
        minimum_next_action = "补齐目标、资源、历史数据和成功标准，再重新判断是否进入低承诺试验。"
    if recommendation == "D_stop":
        minimum_next_action = "停止新增投入，整理已投入资源，复盘关键指标，并保留低成本转向选项。"

    stop_conditions = [
        "到达复盘时间仍没有高于基线的正向信号",
        "主要矛盾被证明不可由用户当前资源解决",
        "投入超过预设时间或资金上限",
    ]
    if context.domain == "content":
        stop_conditions.append("10-20 条内容后没有任何方向出现差异化反馈")
    if context.domain == "startup":
        stop_conditions.append("目标用户不愿试用、复用或付费")
    if context.domain == "career":
        stop_conditions.append("作品集和行业反馈连续指向岗位不匹配")
    if context.domain == "learning":
        stop_conditions.append("4-6 周稳定练习后仍无可观察进步或兴趣")

    return StrategicAdvice(
        recommendation=recommendation,
        plain_answer=plain,
        reasoning=[
            f"局势判断为{situation.stage_label}。",
            f"主要矛盾是：{contradiction.primary_contradiction}。",
            f"可解决性：{solvability.solvable}，解决概率：{solvability.probability}。",
            f"当前承诺等级：{commitment.level}，最大战略风险：{risk.largest_risk}。",
        ],
        minimum_next_action=minimum_next_action,
        do_not_do=["不要因沉没成本继续加码", "不要在证据不足时做高承诺行动", "不要跳过复盘和停止条件"],
        success_metric="出现与主要矛盾直接相关的正向证据，而不是只完成动作本身。",
        stop_conditions=list(dict.fromkeys(stop_conditions)),
        review_after="2-8 周或完成最小样本后复盘",
        what_would_change_the_decision=["出现连续正向样本，可升级承诺等级", "关键事实反向或资源不足，应转为停止或收缩"],
    )
