from __future__ import annotations

import re

from .schemas import Decision, OutcomeReview


NEGATIVE_SIGNALS = {
    "退订": "unsubscribe",
    "投诉": "complaint",
    "失败": "failure",
    "报错": "error",
    "低": "low_result",
    "无回复": "no_response",
    "损失": "loss",
    "refund": "refund",
    "failed": "failure",
    "error": "error",
    "unsubscribe": "unsubscribe",
    "complaint": "complaint",
    "low": "low_result",
}

POSITIVE_SIGNALS = {
    "回复": "reply",
    "成交": "conversion",
    "成功": "success",
    "增长": "growth",
    "通过": "passed",
    "success": "success",
    "reply": "reply",
    "converted": "conversion",
    "passed": "passed",
}


def outcome_features(actual_outcome: str, score: float) -> dict:
    text = actual_outcome.lower()
    negatives = [label for key, label in NEGATIVE_SIGNALS.items() if key.lower() in text]
    positives = [label for key, label in POSITIVE_SIGNALS.items() if key.lower() in text]
    numbers = re.findall(r"-?\d+(?:\.\d+)?%?", actual_outcome)
    if score < 0 and not negatives:
        negatives.append("negative_score")
    if score > 0 and not positives:
        positives.append("positive_score")
    if score < 0:
        positives = [item for item in positives if item not in {"reply", "success", "growth", "passed"}]
    return {
        "negative_signals": list(dict.fromkeys(negatives)),
        "positive_signals": list(dict.fromkeys(positives)),
        "numbers_mentioned": numbers,
        "outcome_polarity": "negative" if score < 0 else "positive" if score > 0 else "neutral",
    }


def lesson_from_context(decision: Decision, actual_outcome: str, score: float, features: dict) -> tuple[str, str, float, bool | None, bool | None]:
    semantic = decision.metadata.get("semantic_frame", {}) if decision.metadata else {}
    gua = decision.metadata.get("onesage64gua", {}) if decision.metadata else {}
    intent = semantic.get("intent_label", "unknown")
    gaps = semantic.get("fact_gaps", [])
    risk_factors = semantic.get("risk_factors", [])
    gua_name = gua.get("gua_name", "未知")

    if score < 0:
        agent_was_right = bool(decision.objection_required)
        user_was_right = False if decision.objection_required else None
        confidence = 0.65
        if "unsubscribe" in features["negative_signals"] or "complaint" in features["negative_signals"]:
            lesson = (
                f"结果出现 {', '.join(features['negative_signals'])}，说明该命令的外部副作用真实存在；"
                f"{gua_name}卦的等待/小样本倾向应加强，后续同类任务必须先验证对象名单、话术和退出机制。"
            )
            rule = "外部触达任务若缺少对象来源、成功标准、退订/投诉预案，默认 wait，不进入批量执行。"
            confidence = 0.82
        elif intent == "underspecified_request" or gaps:
            lesson = (
                "负面结果与信息缺口相关："
                + "；".join(gaps[:3])
                + "。后续应先补齐这些事实，再允许 test。"
            )
            rule = "语义帧 ambiguity>=0.6 或存在关键 fact_gaps 时，不得直接执行，只能追问或生成澄清清单。"
            confidence = 0.78
        else:
            lesson = (
                f"结果为负，风险因素为：{'；'.join(risk_factors) or '未显式记录'}。"
                "后续应提高 action 降级力度，并把 outcome 作为同类命令的反例。"
            )
            rule = "同类命令若 outcome negative，应降低 action_intensity 并增加 review_required。"
        return lesson, rule, confidence, agent_was_right, user_was_right

    if score > 0:
        agent_was_right = not decision.objection_required
        user_was_right = True if decision.objection_required else None
        confidence = 0.58
        if decision.objection_required:
            lesson = (
                f"override 后结果为正，说明原判断可能过于保守；但仍需保留触发条件："
                f"只有当用户补齐关键事实或实际 outcome 证明可控时，才允许从 wait 升到 test。"
            )
            rule = "若 objection 后正向 outcome 且无外部投诉/损失，可把同类任务从 wait 调整为 test，但不得直接 advance。"
            confidence = 0.62
        else:
            lesson = (
                f"正向结果验证了当前最小动作；可保留 {decision.action_type.value}，"
                "但仍需继续记录样本，避免单次成功造成过拟合。"
            )
            rule = "同类低风险任务若连续正向 outcome，可维持当前 action_bias。"
        return lesson, rule, confidence, agent_was_right, user_was_right

    lesson = "结果中性，无法证明 agent 或用户判断优劣；继续积累样本，不升级规则。"
    rule = "中性 outcome 只记录，不改变默认策略。"
    return lesson, rule, 0.4, None, None


def review(decision: Decision, actual_outcome: str, score: float) -> dict:
    features = outcome_features(actual_outcome, score)
    lesson, rule, confidence, agent_was_right, user_was_right = lesson_from_context(decision, actual_outcome, score, features)

    memory_update = {
        "scope": f"project:{decision.project_id}",
        "status": "candidate",
        "confidence": confidence,
        "source": "outcome_review",
        "lesson": lesson,
        "outcome_features": features,
    }
    rule_candidate = {
        "name": "auto_rule_from_review",
        "description": rule,
        "trigger_condition": f"risk_level={decision.risk_level.value}; active_variable={decision.active_variable}; intent={decision.metadata.get('semantic_frame', {}).get('intent_label', 'unknown')}",
        "action_effect": "adjust_action_intensity",
        "status": "candidate",
        "confidence": confidence,
    }
    review_report = {
        "original_command": decision.raw_command,
        "agent_action_type": decision.action_type.value,
        "should_act_now": decision.should_act_now,
        "objection_required": decision.objection_required,
        "objection_reasons": decision.objection_reasons,
        "actual_outcome": actual_outcome,
        "score": score,
        "outcome_features": features,
        "primary_contradiction": decision.primary_contradiction,
        "active_variable": decision.active_variable,
        "lesson": lesson,
        "memory_update_status": "candidate_requires_review",
    }

    return OutcomeReview(
        agent_was_right=agent_was_right,
        user_was_right=user_was_right,
        lesson=lesson,
        memory_update=memory_update,
        rule_candidate=rule_candidate,
        review_report=review_report,
    ).model_dump()
