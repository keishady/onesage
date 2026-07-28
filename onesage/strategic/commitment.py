from __future__ import annotations

from .schemas import CommitmentLevel, SolvabilityAnalysis, StrategicContext, TimingAnalysis


def analyze_commitment(context: StrategicContext, timing: TimingAnalysis, solvability: SolvabilityAnalysis) -> CommitmentLevel:
    time_signal = str(context.resources.get("time", ""))
    question = context.question.lower()
    high = "high_commitment_signal" in time_signal or any(word in question for word in ["辞职", "all in", "大量投入"])
    medium = "medium_commitment_signal" in time_signal or any(word in question for word in ["半年", "三个月", "3个月", "每周", "mvp"])

    if high:
        return CommitmentLevel(
            level="high",
            reason="用户问题包含辞职、半年以上投入或大量资源绑定信号。",
            resource_lock_in="高：会绑定现金流、时间、身份或机会成本。",
            exit_difficulty="hard",
            required_evidence_level="high",
            minimum_evidence_before_action=["主要矛盾清楚且可解", "有连续正向样本", "失败损失可承受", "退出路线清晰"],
            exit_plan_required=True,
        )
    if medium:
        return CommitmentLevel(
            level="medium",
            reason="用户问题包含持续数月或每周固定投入信号。",
            resource_lock_in="中：会占用稳定时间和机会成本。",
            exit_difficulty="moderate",
            required_evidence_level="medium",
            minimum_evidence_before_action=["完成低承诺试验", "明确阶段指标", "设置资源上限"],
            exit_plan_required=True,
        )

    return CommitmentLevel(
        level="low",
        reason=f"当前建议时机为{timing.timing_label}，适合用低承诺行动获取信息。",
        resource_lock_in="低：可快速撤回，主要价值是学习。",
        exit_difficulty="easy",
        required_evidence_level="low",
        minimum_evidence_before_action=["明确要验证的假设", "限制样本和成本", "设定复盘时间"],
        exit_plan_required=False,
    )
