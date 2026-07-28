from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import JsonModel


PATTERN_STATUSES = {"candidate", "validated", "trusted", "challenged", "expired"}


@dataclass
class StrategicPattern(JsonModel):
    pattern_id: str | None
    domain: str
    situation_stage: str
    contradiction_type: str
    commitment_level: str
    risk_type: str
    supporting_lessons: list[int] = field(default_factory=list)
    confidence: float = 0.0
    applicability: dict[str, Any] = field(default_factory=dict)
    counter_examples: list[dict[str, Any]] = field(default_factory=list)
    status: str = "candidate"


def strategic_pattern_from_dict(data: dict[str, Any]) -> StrategicPattern:
    return StrategicPattern(
        pattern_id=data.get("pattern_id"),
        domain=data["domain"],
        situation_stage=data["situation_stage"],
        contradiction_type=data["contradiction_type"],
        commitment_level=data["commitment_level"],
        risk_type=data["risk_type"],
        supporting_lessons=list(data.get("supporting_lessons", [])),
        confidence=float(data.get("confidence", 0.0)),
        applicability=dict(data.get("applicability", {})),
        counter_examples=list(data.get("counter_examples", [])),
        status=data.get("status", "candidate"),
    )
