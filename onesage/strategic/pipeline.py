from __future__ import annotations

from datetime import datetime
import json

from .advisor import make_advice
from .commitment import analyze_commitment
from .context import parse_context
from .contradiction import analyze_contradiction
from .confidence import calculate_confidence
from .memory import save_judgment
from .pattern_memory import record_pattern_audit
from .pattern_retrieval import retrieve_relevant_patterns
from .retrieval import retrieve_relevant_memory
from .risk import analyze_risk
from .schemas import StrategicJudgment
from .situation import analyze_situation
from .solvability import analyze_solvability
from .timing import analyze_timing


def strategize(
    question: str,
    *,
    project_id: str | None = None,
    domain: str | None = None,
    save: bool = False,
) -> StrategicJudgment:
    context = parse_context(question, project_id=project_id, domain=domain)
    relevant_memory = retrieve_relevant_memory(context)
    relevant_patterns = retrieve_relevant_patterns(context)
    situation = analyze_situation(context)
    contradiction = analyze_contradiction(context, situation)
    contradiction.investigation_questions = list(
        dict.fromkeys(contradiction.investigation_questions + relevant_patterns.investigation_questions)
    )
    solvability = analyze_solvability(context, contradiction)
    timing = analyze_timing(context, situation, contradiction, solvability)
    commitment = analyze_commitment(context, timing, solvability)
    risk = analyze_risk(context, situation, contradiction, solvability, timing, commitment)
    confidence = calculate_confidence(context, situation, contradiction, solvability, timing, risk)
    if relevant_memory.confidence_adjustment:
        confidence.confidence = round(min(0.95, confidence.confidence + relevant_memory.confidence_adjustment), 2)
        confidence.confidence_factors.append(
            f"Strategic memory adjustment: +{relevant_memory.confidence_adjustment}"
        )
    if relevant_patterns.confidence_adjustment:
        confidence.confidence = round(min(0.95, confidence.confidence + relevant_patterns.confidence_adjustment), 2)
        confidence.confidence_factors.append(
            f"Strategic pattern adjustment: +{relevant_patterns.confidence_adjustment}"
        )
    advice = make_advice(context, situation, contradiction, solvability, timing, commitment, risk, confidence)
    judgment = StrategicJudgment(
        judgment_id=None,
        project_id=project_id,
        created_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        input_context=context,
        situation_analysis=situation,
        contradiction_analysis=contradiction,
        solvability_analysis=solvability,
        timing_analysis=timing,
        commitment_level=commitment,
        strategic_risk=risk,
        confidence=confidence,
        strategic_advice=advice,
        relevant_memory=relevant_memory,
        relevant_patterns=relevant_patterns,
        review_plan={
            "review_after": advice.review_after,
            "review_questions": [
                "最小行动是否完成？",
                "是否出现与主要矛盾相关的正向证据？",
                "是否触发停止条件？",
                "原判断的最大不确定性是否被验证？",
            ],
        },
    )
    if save:
        save_judgment(judgment)
    for match in relevant_patterns.matched_patterns:
        record_pattern_audit(
            match.pattern_id,
            judgment_id=judgment.judgment_id,
            matched_context={
                "question": context.question,
                "domain": context.domain,
                "user_bias": context.user_bias,
                "history": context.history,
                "competition": context.competition,
            },
            match_reason=match.match_reason,
        )
    return judgment


def render_markdown(judgment: StrategicJudgment) -> str:
    data = judgment.model_dump()
    advice = data["strategic_advice"]
    situation = data["situation_analysis"]
    contradiction = data["contradiction_analysis"]
    solvability = data["solvability_analysis"]
    timing = data["timing_analysis"]
    commitment = data["commitment_level"]
    risk = data["strategic_risk"]
    confidence = data["confidence"]
    context = data["input_context"]
    memory = data.get("relevant_memory", {"matches": [], "reminders": [], "confidence_adjustment": 0.0})

    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- 无"

    return "\n".join(
        [
            "== OneSage Strategic Judgment ==",
            "",
            f"结论：{advice['recommendation']}",
            f"一句话判断：{advice['plain_answer']}",
            "",
            "1. Input Context",
            f"- 问题：{context['question']}",
            f"- 领域：{context['domain']}",
            f"- 事实：{'; '.join(context['known_facts'])}",
            f"- 未知：{'; '.join(context['unknowns'])}",
            "",
            "2. Situation Analysis",
            f"- 阶段：{situation['stage_label']} ({situation['situation_stage']})",
            f"- 证据：{'; '.join(situation['evidence'])}",
            f"- 误判风险：{situation['risk_of_misreading']}",
            "",
            "3. Primary Contradiction",
            f"- 主要矛盾：{contradiction['primary_contradiction']}",
            f"- 矛盾主要方面：{contradiction['main_aspect']}",
            f"- 为什么是主要矛盾：{contradiction['why_primary']}",
            "",
            "4. Solvability Analysis",
            f"- 可解决性：{solvability['solvable']}",
            f"- 用户影响能力：{solvability['influence_level']}",
            f"- 解决概率：{solvability['probability']}",
            f"- 建议：{solvability['recommendation']}",
            "",
            "5. Timing Analysis",
            f"- 时机：{timing['timing_label']} ({timing['timing']})",
            f"- 理由：{timing['reason']}",
            f"- 观察信号：{'; '.join(timing['signals_to_watch'])}",
            "",
            "6. Commitment Level",
            f"- 等级：{commitment['level']}",
            f"- 理由：{commitment['reason']}",
            f"- 退出难度：{commitment['exit_difficulty']}",
            "",
            "7. Strategic Risk",
            f"- 最大风险：{risk['largest_risk']}",
            f"- 总结：{risk['risk_summary']}",
            "",
            "8. Strategic Advice",
            f"- 最小下一步：{advice['minimum_next_action']}",
            "- 不要做：",
            bullets(advice["do_not_do"]),
            "- 停止条件：",
            bullets(advice["stop_conditions"]),
            "",
            "9. Confidence",
            f"- 置信度：{confidence['confidence']}",
            f"- 主要不确定性：{confidence['main_uncertainty']}",
            f"- 置信来源：{'; '.join(confidence['confidence_factors'])}",
            "",
            "10. Review Plan",
            f"- 复盘时间：{advice['review_after']}",
            f"- 改变判断的条件：{'; '.join(advice['what_would_change_the_decision'])}",
            "",
        ]
    )


def render_json(judgment: StrategicJudgment) -> str:
    return json.dumps(judgment.model_dump(), ensure_ascii=False, indent=2)
