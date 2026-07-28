from __future__ import annotations

import json
import re
from typing import Any

from .pattern_memory import list_patterns
from .schemas import PatternMatch, RelevantPatterns, StrategicContext


IGNORED_PATTERN_STATUSES = {"expired"}


def retrieve_relevant_patterns(context: StrategicContext, *, limit: int = 5) -> RelevantPatterns:
    patterns = list_patterns()
    context_stage = _context_stage(context)
    context_contradiction = _context_contradiction_type(context)
    context_commitment = _context_commitment(context)
    context_risk = _context_risk_hint(context)
    context_tokens = _tokens(context.question)

    matches: list[PatternMatch] = []
    for pattern in patterns:
        if pattern["status"] in IGNORED_PATTERN_STATUSES:
            continue
        score, reasons = _score_pattern(
            pattern=pattern,
            context=context,
            context_stage=context_stage,
            context_contradiction=context_contradiction,
            context_commitment=context_commitment,
            context_risk=context_risk,
            context_tokens=context_tokens,
        )
        if score < 0.25:
            continue
        applicability_check = _applicability_check(pattern, context, reasons)
        matches.append(
            PatternMatch(
                pattern_id=pattern["pattern_id"],
                domain=pattern["domain"],
                situation_stage=pattern["situation_stage"],
                contradiction_type=pattern["contradiction_type"],
                commitment_level=pattern["commitment_level"],
                risk_type=pattern["risk_type"],
                status=pattern["status"],
                confidence=float(pattern["confidence"]),
                match_score=score,
                match_reason=reasons,
                applicability_check=applicability_check,
                warning=_pattern_warning(pattern, applicability_check),
                supporting_lessons=list(pattern.get("supporting_lessons", [])),
            )
        )

    matches.sort(key=lambda item: item.match_score, reverse=True)
    matches = matches[:limit]
    return RelevantPatterns(
        matched_patterns=matches,
        pattern_warnings=[match.warning for match in matches if match.warning],
        confidence_adjustment=_confidence_adjustment(matches),
        investigation_questions=_investigation_questions(matches),
        retrieval_rules=[
            "current_facts_override_patterns",
            "patterns_cannot_change_recommendation",
            "patterns_cannot_raise_commitment_level",
            "patterns_cannot_lower_current_risk",
            "candidate_patterns_are_reminders_only",
        ],
    )


def _score_pattern(
    *,
    pattern: dict[str, Any],
    context: StrategicContext,
    context_stage: str,
    context_contradiction: str,
    context_commitment: str,
    context_risk: str,
    context_tokens: set[str],
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if pattern["domain"] == context.domain:
        score += 0.25
        reasons.append("domain")
    if context_stage != "unknown" and pattern["situation_stage"] == context_stage:
        score += 0.16
        reasons.append("situation_stage")
    if context_contradiction != "general" and pattern["contradiction_type"] == context_contradiction:
        score += 0.2
        reasons.append("contradiction_type")
    if pattern["commitment_level"] == context_commitment:
        score += 0.12
        reasons.append("commitment_level")
    if pattern["risk_type"] == context_risk:
        score += 0.17
        reasons.append("risk_type")

    pattern_text = " ".join(
        [
            pattern["pattern_id"],
            pattern["domain"],
            pattern["situation_stage"],
            pattern["contradiction_type"],
            pattern["commitment_level"],
            pattern["risk_type"],
            json.dumps(pattern.get("applicability", {}), ensure_ascii=False),
        ]
    )
    overlap = _keyword_overlap(context_tokens, _tokens(pattern_text))
    if overlap:
        score += min(0.1, overlap)
        reasons.append("keyword_overlap")
    return round(min(1.0, score), 2), reasons


def _applicability_check(pattern: dict[str, Any], context: StrategicContext, reasons: list[str]) -> dict[str, Any]:
    required = {"domain", "contradiction_type", "risk_type"}
    matched_required = required.intersection(reasons)
    current_fact_conflict = False
    if context.user_bias == "sunk_cost_pressure" and pattern["risk_type"] != "sunk_cost_risk":
        current_fact_conflict = True
    if context.domain == "side_project" and pattern["risk_type"] == "direction_risk":
        current_fact_conflict = True
    return {
        "current_facts_override": True,
        "matched_required_dimensions": sorted(matched_required),
        "missing_required_dimensions": sorted(required - matched_required),
        "current_fact_conflict": current_fact_conflict,
        "can_adjust_confidence": (
            pattern["status"] in {"validated", "trusted"}
            and not current_fact_conflict
            and len(matched_required) >= 2
        ),
        "can_change_recommendation": False,
    }


def _pattern_warning(pattern: dict[str, Any], applicability_check: dict[str, Any]) -> str:
    if applicability_check["current_fact_conflict"]:
        return f"Pattern {pattern['pattern_id']} conflicts with current facts; reminder only."
    if pattern["status"] == "candidate":
        return f"Pattern {pattern['pattern_id']} is candidate; reminder only."
    if pattern["status"] == "challenged":
        return f"Pattern {pattern['pattern_id']} is challenged; do not use for confidence increase."
    return f"Pattern {pattern['pattern_id']} may inform confidence and investigation questions."


def _confidence_adjustment(matches: list[PatternMatch]) -> float:
    adjustment = 0.0
    for match in matches[:3]:
        if not match.applicability_check.get("can_adjust_confidence"):
            continue
        if match.status == "trusted":
            adjustment += 0.04
        elif match.status == "validated":
            adjustment += 0.02
    return round(min(0.1, adjustment), 3)


def _investigation_questions(matches: list[PatternMatch]) -> list[str]:
    questions: list[str] = []
    for match in matches[:3]:
        if match.risk_type == "direction_risk":
            questions.append("Pattern reminder: what current evidence proves the direction or demand is real?")
        elif match.risk_type == "resource_risk":
            questions.append("Pattern reminder: what resource or cash-flow constraint could make this judgment unsafe?")
        elif match.risk_type == "opportunity_cost_risk":
            questions.append("Pattern reminder: what valuable alternative is being displaced by this commitment?")
        elif match.risk_type == "sunk_cost_risk":
            questions.append("Pattern reminder: what future marginal return justifies continued investment?")
    return list(dict.fromkeys(questions))


def _context_stage(context: StrategicContext) -> str:
    if context.history.get("decline_signals"):
        return "decline"
    if context.competition.get("signals"):
        return "competition"
    if any(word in context.question for word in ["爆发", "风口", "增长很快", "机会窗口"]):
        return "breakout"
    return "unknown"


def _context_commitment(context: StrategicContext) -> str:
    if context.resources.get("time") == "high_commitment_signal":
        return "high"
    if context.resources.get("time") == "medium_commitment_signal":
        return "medium"
    return "low"


def _context_risk_hint(context: StrategicContext) -> str:
    question = context.question
    if context.user_bias == "sunk_cost_pressure" or any(word in question for word in ["沉没", "已经投入", "投入很多"]):
        return "sunk_cost_risk"
    if context.domain == "side_project" or any(word in question for word in ["副业", "主业", "机会成本", "每周"]):
        return "opportunity_cost_risk"
    if _context_commitment(context) == "high":
        return "resource_risk"
    return "direction_risk"


def _context_contradiction_type(context: StrategicContext) -> str:
    question = context.question.lower()
    if _context_risk_hint(context) == "sunk_cost_risk":
        return "sunk_cost"
    if _context_risk_hint(context) == "opportunity_cost_risk":
        return "opportunity_cost"
    if context.domain == "content" or any(word in question for word in ["youtube", "视频", "频道", "差异化"]):
        return "difference"
    if context.domain in {"career", "learning"}:
        return "resource"
    if context.domain == "startup":
        return "demand_validation"
    return "general"


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    words = set(re.findall(r"[a-z0-9_:-]{2,}", lowered))
    terms = [
        "youtube", "content", "startup", "career", "side_project", "sunk_cost",
        "difference", "demand_validation", "resource", "opportunity_cost",
        "direction_risk", "resource_risk", "sunk_cost_risk", "opportunity_cost_risk",
        "视频", "频道", "内容", "创业", "项目", "职业", "副业", "主业", "沉没成本",
        "需求", "差异化", "机会成本", "已经投入",
    ]
    words.update(term for term in terms if term.lower() in lowered)
    return words


def _keyword_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / max(len(left), 1)
