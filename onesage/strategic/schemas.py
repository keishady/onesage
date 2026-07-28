from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
import json
from typing import Any


class JsonModel:
    def model_dump(self) -> dict[str, Any]:
        return _to_plain(self)

    def model_dump_json(self) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False)


def _to_plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _to_plain(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    return value


@dataclass
class StrategicContext(JsonModel):
    question: str
    goal: str
    domain: str = "general"
    known_facts: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    resources: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    competition: dict[str, Any] = field(default_factory=dict)
    history: dict[str, Any] = field(default_factory=dict)
    user_bias: str = ""
    urgency: float = 0.0
    ambiguity: float = 0.0


@dataclass
class SituationAnalysis(JsonModel):
    situation_stage: str
    stage_label: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    key_forces: list[str] = field(default_factory=list)
    risk_of_misreading: str = ""


@dataclass
class ContradictionAnalysis(JsonModel):
    primary_contradiction: str
    side_a: str
    side_b: str
    main_aspect: str
    why_primary: str
    secondary_contradictions: list[str] = field(default_factory=list)
    resource_focus: list[str] = field(default_factory=list)
    deferred_issues: list[str] = field(default_factory=list)
    investigation_questions: list[str] = field(default_factory=list)


@dataclass
class SolvabilityAnalysis(JsonModel):
    solvable: str
    influence_level: str
    required_resources: dict[str, Any] = field(default_factory=dict)
    time_cost: str = "uncertain"
    probability: str = "unknown"
    worth_solving: str = "unknown"
    recommendation: str = ""


@dataclass
class TimingAnalysis(JsonModel):
    timing: str
    timing_label: str
    reason: str
    action_window: str
    cost_of_acting: str
    cost_of_waiting: str
    reversibility: str
    signals_to_watch: list[str] = field(default_factory=list)
    failure_mode: str = ""


@dataclass
class CommitmentLevel(JsonModel):
    level: str
    reason: str
    resource_lock_in: str
    exit_difficulty: str
    required_evidence_level: str
    minimum_evidence_before_action: list[str] = field(default_factory=list)
    exit_plan_required: bool = False


@dataclass
class StrategicRisk(JsonModel):
    direction_risk: dict[str, str]
    timing_risk: dict[str, str]
    resource_risk: dict[str, str]
    sunk_cost_risk: dict[str, str]
    opportunity_cost_risk: dict[str, str]
    largest_risk: str
    risk_summary: str


@dataclass
class JudgmentConfidence(JsonModel):
    confidence: float
    confidence_factors: list[str] = field(default_factory=list)
    main_uncertainty: str = ""
    confidence_breakdown: dict[str, float] = field(default_factory=dict)


@dataclass
class StrategicAdvice(JsonModel):
    recommendation: str
    plain_answer: str
    reasoning: list[str] = field(default_factory=list)
    minimum_next_action: str = ""
    do_not_do: list[str] = field(default_factory=list)
    success_metric: str = ""
    stop_conditions: list[str] = field(default_factory=list)
    review_after: str = ""
    what_would_change_the_decision: list[str] = field(default_factory=list)


@dataclass
class MemoryMatch(JsonModel):
    similarity_score: float
    lesson_id: int | None
    judgment_id: str
    domain: str
    situation_stage: str
    contradiction_type: str
    primary_contradiction: str
    commitment_level: str
    largest_risk: str
    historical_advice: str
    actual_outcome: str
    lesson: str
    lesson_status: str
    confidence: float
    match_reasons: list[str] = field(default_factory=list)


@dataclass
class RelevantMemory(JsonModel):
    matches: list[MemoryMatch] = field(default_factory=list)
    reminders: list[str] = field(default_factory=list)
    confidence_adjustment: float = 0.0
    retrieval_rules: list[str] = field(default_factory=list)


@dataclass
class PatternMatch(JsonModel):
    pattern_id: str
    domain: str
    situation_stage: str
    contradiction_type: str
    commitment_level: str
    risk_type: str
    status: str
    confidence: float
    match_score: float
    match_reason: list[str] = field(default_factory=list)
    applicability_check: dict[str, Any] = field(default_factory=dict)
    warning: str = ""
    supporting_lessons: list[int] = field(default_factory=list)


@dataclass
class RelevantPatterns(JsonModel):
    matched_patterns: list[PatternMatch] = field(default_factory=list)
    pattern_warnings: list[str] = field(default_factory=list)
    confidence_adjustment: float = 0.0
    investigation_questions: list[str] = field(default_factory=list)
    retrieval_rules: list[str] = field(default_factory=list)


@dataclass
class StrategicJudgment(JsonModel):
    judgment_id: str | None
    project_id: str | None
    created_at: str
    input_context: StrategicContext
    situation_analysis: SituationAnalysis
    contradiction_analysis: ContradictionAnalysis
    solvability_analysis: SolvabilityAnalysis
    timing_analysis: TimingAnalysis
    commitment_level: CommitmentLevel
    strategic_risk: StrategicRisk
    confidence: JudgmentConfidence
    strategic_advice: StrategicAdvice
    relevant_memory: RelevantMemory = field(default_factory=RelevantMemory)
    relevant_patterns: RelevantPatterns = field(default_factory=RelevantPatterns)
    review_plan: dict[str, Any] = field(default_factory=dict)


@dataclass
class JudgmentReview(JsonModel):
    judgment_id: str
    actual_outcome: str
    judgment_quality: str
    primary_error_type: str
    error_types: list[str] = field(default_factory=list)
    judgment_accuracy: str = ""
    reasoning_quality: str = ""
    decision_quality: str = ""
    outcome_influence: str = ""
    confidence_before: float = 0.0
    confidence_after: float = 0.0
    lesson_candidate: dict[str, Any] = field(default_factory=dict)
    review_notes: list[str] = field(default_factory=list)
    created_at: str = ""


def strategic_judgment_from_dict(data: dict[str, Any]) -> StrategicJudgment:
    return StrategicJudgment(
        judgment_id=data.get("judgment_id"),
        project_id=data.get("project_id"),
        created_at=data["created_at"],
        input_context=StrategicContext(**data["input_context"]),
        situation_analysis=SituationAnalysis(**data["situation_analysis"]),
        contradiction_analysis=ContradictionAnalysis(**data["contradiction_analysis"]),
        solvability_analysis=SolvabilityAnalysis(**data["solvability_analysis"]),
        timing_analysis=TimingAnalysis(**data["timing_analysis"]),
        commitment_level=CommitmentLevel(**data["commitment_level"]),
        strategic_risk=StrategicRisk(**data["strategic_risk"]),
        confidence=JudgmentConfidence(**data["confidence"]),
        strategic_advice=StrategicAdvice(**data["strategic_advice"]),
        relevant_memory=RelevantMemory(
            matches=[MemoryMatch(**item) for item in data.get("relevant_memory", {}).get("matches", [])],
            reminders=data.get("relevant_memory", {}).get("reminders", []),
            confidence_adjustment=data.get("relevant_memory", {}).get("confidence_adjustment", 0.0),
            retrieval_rules=data.get("relevant_memory", {}).get("retrieval_rules", []),
        ),
        relevant_patterns=RelevantPatterns(
            matched_patterns=[
                PatternMatch(**item) for item in data.get("relevant_patterns", {}).get("matched_patterns", [])
            ],
            pattern_warnings=data.get("relevant_patterns", {}).get("pattern_warnings", []),
            confidence_adjustment=data.get("relevant_patterns", {}).get("confidence_adjustment", 0.0),
            investigation_questions=data.get("relevant_patterns", {}).get("investigation_questions", []),
            retrieval_rules=data.get("relevant_patterns", {}).get("retrieval_rules", []),
        ),
        review_plan=data.get("review_plan", {}),
    )
