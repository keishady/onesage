from __future__ import annotations

from ..db import now
from .schemas import JudgmentReview, StrategicJudgment


ERROR_TYPES = [
    "Fact Error",
    "Stage Error",
    "Contradiction Error",
    "Solvability Error",
    "Timing Error",
    "Commitment Error",
    "Strategic Risk Error",
    "Advice Error",
    "Calibration Error",
]


def review_judgment(judgment: StrategicJudgment, actual_outcome: str) -> JudgmentReview:
    outcome = _classify_outcome(actual_outcome)
    recommendation = judgment.strategic_advice.recommendation
    timing = judgment.timing_analysis.timing
    commitment = judgment.commitment_level.level
    largest_risk = judgment.strategic_risk.largest_risk

    quality, errors, notes = _evaluate_quality(
        recommendation=recommendation,
        timing=timing,
        commitment=commitment,
        largest_risk=largest_risk,
        outcome=outcome,
    )
    confidence_before = judgment.confidence.confidence
    confidence_after = _calibrate_confidence(confidence_before, quality, outcome, recommendation)
    lesson_candidate = _build_lesson_candidate(judgment, actual_outcome, quality, errors, confidence_after)

    return JudgmentReview(
        judgment_id=judgment.judgment_id or "",
        actual_outcome=actual_outcome,
        judgment_quality=quality,
        primary_error_type=errors[0],
        error_types=errors,
        judgment_accuracy=_judgment_accuracy(quality, outcome),
        reasoning_quality=_reasoning_quality(quality, judgment),
        decision_quality=_decision_quality(quality, recommendation, commitment),
        outcome_influence=_outcome_influence(outcome, recommendation),
        confidence_before=confidence_before,
        confidence_after=confidence_after,
        lesson_candidate=lesson_candidate,
        review_notes=notes,
        created_at=now(),
    )


def render_review_markdown(review: JudgmentReview) -> str:
    data = review.model_dump()
    lesson = data["lesson_candidate"]
    return "\n".join(
        [
            "== OneSage Judgment Review ==",
            "",
            f"Judgment ID: {data['judgment_id']}",
            f"Judgment Quality: {data['judgment_quality']}",
            f"Primary Error Type: {data['primary_error_type']}",
            f"Error Types: {', '.join(data['error_types'])}",
            f"Confidence: {data['confidence_before']} -> {data['confidence_after']}",
            "",
            "Outcome Influence",
            data["outcome_influence"],
            "",
            "Lesson Candidate",
            f"- Lesson: {lesson.get('lesson', '')}",
            f"- Scope: {lesson.get('scope', '')}",
            f"- Status: {lesson.get('status', 'candidate')}",
            f"- Confidence: {lesson.get('confidence', data['confidence_after'])}",
            "",
            "Review Notes",
            *[f"- {item}" for item in data["review_notes"]],
            "",
        ]
    )


def _evaluate_quality(
    *,
    recommendation: str,
    timing: str,
    commitment: str,
    largest_risk: str,
    outcome: dict[str, bool],
) -> tuple[str, list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    if recommendation == "B_small_test" and outcome["negative"] and outcome["learning"]:
        notes.append("Bad outcome did not invalidate the judgment because the test produced useful data.")
        return "good", ["Calibration Error"], notes

    if recommendation in {"C_observe", "D_stop"} and (outcome["negative"] or outcome["sunk_cost"]):
        errors.append("Calibration Error")
        notes.append("The outcome supports a cautious judgment under incomplete information.")
        return "good", errors, notes

    if recommendation == "A_act_now" and outcome["negative"]:
        errors.extend(["Timing Error", "Advice Error"])
        if commitment == "high":
            errors.append("Commitment Error")
        notes.append("The advice was too strong for a negative or invalidating outcome.")
        return "poor", errors, notes

    if recommendation == "D_stop" and outcome["positive"]:
        errors.extend(["Stage Error", "Advice Error"])
        notes.append("The result suggests the stop advice may have underestimated remaining upside.")
        return "poor", errors, notes

    if recommendation == "C_observe" and outcome["positive"]:
        errors.append("Advice Error")
        notes.append("The direction may have been right, but the advice may have been too conservative.")
        return "acceptable", errors, notes

    if recommendation == "B_small_test" and outcome["positive"]:
        errors.append("Calibration Error")
        notes.append("The positive result supports the low-commitment test path without proving a broad rule.")
        return "excellent", errors, notes

    if largest_risk == "opportunity_cost_risk" and outcome["opportunity_cost"]:
        errors.append("Strategic Risk Error")
        notes.append("Opportunity cost became the dominant review signal.")
        return "acceptable", errors, notes

    if outcome["negative"] and timing in {"act", "test"}:
        errors.append("Solvability Error")
        notes.append("The result may indicate the primary contradiction was less solvable than expected.")
        return "acceptable", errors, notes

    errors.append("Calibration Error")
    notes.append("Outcome signal is mixed or incomplete; preserve the lesson as a candidate only.")
    return "acceptable", errors, notes


def _calibrate_confidence(
    confidence_before: float,
    quality: str,
    outcome: dict[str, bool],
    recommendation: str,
) -> float:
    if quality == "excellent":
        delta = 0.04
    elif quality == "good":
        delta = 0.02
    elif quality == "acceptable":
        delta = -0.03
    else:
        delta = -0.12

    if recommendation == "B_small_test" and outcome["negative"] and outcome["learning"]:
        delta = max(delta, -0.01)
    if quality == "poor" and outcome["positive"]:
        delta = min(delta, 0.0)
    return round(min(0.95, max(0.05, confidence_before + delta)), 2)


def _build_lesson_candidate(
    judgment: StrategicJudgment,
    actual_outcome: str,
    quality: str,
    errors: list[str],
    confidence_after: float,
) -> dict[str, object]:
    domain = judgment.input_context.domain
    recommendation = judgment.strategic_advice.recommendation
    contradiction = judgment.contradiction_analysis.primary_contradiction
    scope = f"domain={domain}; recommendation={recommendation}; error_type={errors[0]}"
    lesson = (
        f"When facing '{contradiction}', keep future advice tied to evidence quality, "
        f"commitment level, and explicit stop conditions. Outcome reviewed: {actual_outcome}"
    )
    if recommendation == "B_small_test" and quality in {"excellent", "good"}:
        lesson = (
            f"In {domain}, low-commitment tests are valid when evidence is incomplete, "
            "especially if the result produces discriminating data before larger investment."
        )
    elif judgment.strategic_risk.largest_risk == "sunk_cost_risk":
        lesson = (
            f"In {domain}, sunk cost pressure must be separated from future marginal return "
            "before recommending continued investment."
        )
    elif judgment.strategic_risk.largest_risk == "opportunity_cost_risk":
        lesson = (
            f"In {domain}, opportunity cost should be reviewed as a strategic risk, "
            "not treated as a mere scheduling problem."
        )
    return {
        "judgment_id": judgment.judgment_id,
        "lesson": lesson,
        "scope": scope,
        "confidence": confidence_after,
        "status": "candidate",
    }


def _classify_outcome(actual_outcome: str) -> dict[str, bool]:
    text = actual_outcome.lower()
    positive_words = ["增长", "成功", "提高", "更高", "有效", "盈利", "offer", "转化", "留存"]
    negative_words = ["失败", "没有增长", "没增长", "亏", "无效", "放弃", "停止", "没人", "没效果"]
    learning_words = ["发现", "数据", "反馈", "验证", "样本", "完播率", "访谈", "证据"]
    sunk_words = ["沉没", "已经投入", "继续亏", "舍不得", "回本"]
    opportunity_words = ["机会成本", "错过", "占用", "耽误", "时间不够"]
    return {
        "positive": _has_any(text, positive_words),
        "negative": _has_any(text, negative_words),
        "learning": _has_any(text, learning_words),
        "sunk_cost": _has_any(text, sunk_words),
        "opportunity_cost": _has_any(text, opportunity_words),
    }


def _has_any(text: str, words: list[str]) -> bool:
    return any(word.lower() in text for word in words)


def _judgment_accuracy(quality: str, outcome: dict[str, bool]) -> str:
    if quality in {"excellent", "good"}:
        return "reasonable_under_original_information"
    if quality == "acceptable":
        return "partially_supported_with_missing_information"
    if outcome["positive"]:
        return "bad_judgment_with_good_result_possible"
    return "weakly_supported_by_outcome"


def _reasoning_quality(quality: str, judgment: StrategicJudgment) -> str:
    if judgment.input_context.unknowns and quality in {"excellent", "good"}:
        return "good_unknown_handling"
    if quality == "poor":
        return "reasoning_misaligned_with_outcome_signal"
    return "adequate_but_needs_more_evidence"


def _decision_quality(quality: str, recommendation: str, commitment: str) -> str:
    if commitment == "high" and recommendation == "A_act_now" and quality == "poor":
        return "overcommitted"
    if recommendation == "B_small_test":
        return "properly_limited_commitment"
    if recommendation in {"C_observe", "D_stop"}:
        return "protective_of_resources"
    return "acceptable"


def _outcome_influence(outcome: dict[str, bool], recommendation: str) -> str:
    if outcome["positive"] and recommendation in {"C_observe", "D_stop"}:
        return "Outcome was positive, but this does not automatically prove the original cautious judgment was wrong."
    if outcome["negative"] and recommendation == "B_small_test" and outcome["learning"]:
        return "The result was negative but produced learning, so judgment quality should not be heavily penalized."
    if outcome["negative"]:
        return "The negative result should reduce future confidence only if the original advice exceeded the evidence."
    return "Outcome is mixed or incomplete; calibration should remain conservative."
