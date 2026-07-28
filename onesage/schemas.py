from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
import json
from typing import Any, Optional, TypeVar


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


TEnum = TypeVar("TEnum", bound=Enum)


def _enum(enum_cls: type[TEnum], value: Any) -> TEnum:
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)


class ActionType(str, Enum):
    OBSERVE = "observe"
    WAIT = "wait"
    TEST = "test"
    ADVANCE = "advance"
    RETREAT = "retreat"
    STOP = "stop"
    COOPERATE = "cooperate"


class DimensionState(str, Enum):
    STRONG = "strong"
    WEAK = "weak"
    CHANGING = "changing"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    L0_READ_ONLY = "L0_read_only"
    L1_WRITE_LOCAL = "L1_write_local"
    L2_WRITE_EXTERNAL = "L2_write_external"
    L3_CRITICAL = "L3_critical"


class Permission(str, Enum):
    READ_LOCAL = "read_local"
    WRITE_LOCAL = "write_local"
    NETWORK = "network"
    BROWSER = "browser"
    CREDENTIALS = "credentials"
    EXTERNAL_WRITE = "external_write"
    SHELL = "shell"
    FINANCIAL = "financial"


class ModelRole(str, Enum):
    FAST_DRAFT = "fast_draft"
    STRUCTURED_EXTRACTION = "structured_extraction"
    TOOL_PLANNING = "tool_planning"
    VERIFY = "verify"
    FINAL_SYNTHESIS = "final_synthesis"


@dataclass
class SemanticFrame(JsonModel):
    raw_command: str
    language: str
    intent_label: str
    action_verbs: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    fact_gaps: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)
    target_scope: str = "local_or_unspecified"
    reversibility: str = "unknown"
    urgency: float = 0.0
    ambiguity: float = 0.0
    externality: float = 0.0
    destructive_potential: float = 0.0
    financial_potential: float = 0.0
    credential_exposure: float = 0.0
    confidence: float = 0.5
    analysis_method: str = "deterministic_semantic_frame"


@dataclass
class StateDimension(JsonModel):
    state: DimensionState
    confidence: float
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateDimension":
        return cls(state=_enum(DimensionState, data["state"]), confidence=float(data["confidence"]), reason=data.get("reason", ""))


@dataclass
class StateVector(JsonModel):
    environment: StateDimension
    internal_resource: StateDimension
    friction: StateDimension
    opportunity: StateDimension
    dominant_force: StateDimension
    tail_risk: StateDimension

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateVector":
        return cls(
            environment=StateDimension.from_dict(data["environment"]),
            internal_resource=StateDimension.from_dict(data["internal_resource"]),
            friction=StateDimension.from_dict(data["friction"]),
            opportunity=StateDimension.from_dict(data["opportunity"]),
            dominant_force=StateDimension.from_dict(data["dominant_force"]),
            tail_risk=StateDimension.from_dict(data["tail_risk"]),
        )


@dataclass
class Contradiction(JsonModel):
    name: str
    side_a: str
    side_b: str
    severity: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Contradiction":
        return cls(
            name=data["name"],
            side_a=data["side_a"],
            side_b=data["side_b"],
            severity=float(data["severity"]),
        )


@dataclass
class PolicyDecision(JsonModel):
    should_act_now: bool
    risk_level: RiskLevel
    required_permissions: list[Permission] = field(default_factory=list)
    approval_required: bool = False
    approval_reason: str = ""
    blocked: bool = False
    blocked_reason: str = ""
    safer_alternative: str = ""
    confirmations_required: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyDecision":
        return cls(
            should_act_now=bool(data["should_act_now"]),
            risk_level=_enum(RiskLevel, data["risk_level"]),
            required_permissions=[_enum(Permission, item) for item in data.get("required_permissions", [])],
            approval_required=bool(data.get("approval_required", False)),
            approval_reason=data.get("approval_reason", ""),
            blocked=bool(data.get("blocked", False)),
            blocked_reason=data.get("blocked_reason", ""),
            safer_alternative=data.get("safer_alternative", ""),
            confirmations_required=int(data.get("confirmations_required", 0)),
        )


@dataclass
class ModelRoute(JsonModel):
    role: ModelRole
    provider: str
    model: str
    reason: str
    mercury_compatible: bool = False
    validation_required: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelRoute":
        return cls(
            role=_enum(ModelRole, data["role"]),
            provider=data["provider"],
            model=data["model"],
            reason=data["reason"],
            mercury_compatible=bool(data.get("mercury_compatible", False)),
            validation_required=bool(data.get("validation_required", True)),
        )


@dataclass
class Decision(JsonModel):
    project_id: str
    objective: str
    facts: list[str]
    unknowns: list[str]
    assumptions: list[str]
    contradictions: list[Contradiction]
    primary_contradiction: str
    state_vector: StateVector
    active_variable: str
    stage: str
    position: str
    timing_judgment: str
    action_type: ActionType
    minimum_next_action: str
    forbidden_actions: list[str]
    reeval_conditions: list[str]
    human_confirm_required: bool
    objection_required: bool
    objection_reasons: list[str]
    override_allowed: bool
    risk_level: RiskLevel
    success_metric: str
    raw_command: str
    should_act_now: bool = False
    policy: Optional[PolicyDecision] = None
    model_route: Optional[ModelRoute] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def model_validate_json(cls, text: str) -> "Decision":
        data = json.loads(text)
        return cls(
            project_id=data["project_id"],
            objective=data["objective"],
            facts=list(data["facts"]),
            unknowns=list(data["unknowns"]),
            assumptions=list(data["assumptions"]),
            contradictions=[Contradiction.from_dict(item) for item in data["contradictions"]],
            primary_contradiction=data["primary_contradiction"],
            state_vector=StateVector.from_dict(data["state_vector"]),
            active_variable=data["active_variable"],
            stage=data["stage"],
            position=data["position"],
            timing_judgment=data["timing_judgment"],
            action_type=_enum(ActionType, data["action_type"]),
            minimum_next_action=data["minimum_next_action"],
            forbidden_actions=list(data["forbidden_actions"]),
            reeval_conditions=list(data["reeval_conditions"]),
            human_confirm_required=bool(data["human_confirm_required"]),
            objection_required=bool(data["objection_required"]),
            objection_reasons=list(data["objection_reasons"]),
            override_allowed=bool(data["override_allowed"]),
            risk_level=_enum(RiskLevel, data["risk_level"]),
            success_metric=data["success_metric"],
            raw_command=data["raw_command"],
            should_act_now=bool(data.get("should_act_now", False)),
            policy=PolicyDecision.from_dict(data["policy"]) if data.get("policy") else None,
            model_route=ModelRoute.from_dict(data["model_route"]) if data.get("model_route") else None,
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class SkillManifest(JsonModel):
    name: str
    owner: str = "local"
    version: str = "0.1.0"
    description: str = ""
    entrypoint: str = ""
    permissions: list[Permission] = field(default_factory=list)
    allowed_domains: list[str] = field(default_factory=list)
    filesystem_scope: list[str] = field(default_factory=list)
    update_policy: str = "manual"
    provenance: str = "local"
    enabled: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillManifest":
        return cls(
            name=data["name"],
            owner=data.get("owner", "local"),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            entrypoint=data.get("entrypoint", ""),
            permissions=[_enum(Permission, item) for item in data.get("permissions", [])],
            allowed_domains=list(data.get("allowed_domains", [])),
            filesystem_scope=list(data.get("filesystem_scope", [])),
            update_policy=data.get("update_policy", "manual"),
            provenance=data.get("provenance", "local"),
            enabled=bool(data.get("enabled", False)),
        )


@dataclass
class SandboxResult(JsonModel):
    skill_name: str
    accepted: bool
    risk_level: RiskLevel
    required_approvals: int
    findings: list[str]
    blocked_permissions: list[Permission] = field(default_factory=list)


@dataclass
class WorkflowStep(JsonModel):
    name: str
    action_type: ActionType
    required_permissions: list[Permission] = field(default_factory=list)
    safety_gate: str = ""
    retry_policy: str = "manual"
    evaluation_check: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        return cls(
            name=data["name"],
            action_type=_enum(ActionType, data["action_type"]),
            required_permissions=[_enum(Permission, item) for item in data.get("required_permissions", [])],
            safety_gate=data.get("safety_gate", ""),
            retry_policy=data.get("retry_policy", "manual"),
            evaluation_check=data.get("evaluation_check", ""),
        )


@dataclass
class WorkflowSpec(JsonModel):
    name: str
    objective: str
    steps: list[WorkflowStep]
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    review_required: bool = True

    @classmethod
    def model_validate_json(cls, text: str) -> "WorkflowSpec":
        data = json.loads(text)
        return cls(
            name=data["name"],
            objective=data["objective"],
            steps=[WorkflowStep.from_dict(item) for item in data["steps"]],
            inputs=dict(data.get("inputs", {})),
            outputs=dict(data.get("outputs", {})),
            review_required=bool(data.get("review_required", True)),
        )


@dataclass
class OutcomeReview(JsonModel):
    agent_was_right: Optional[bool]
    user_was_right: Optional[bool]
    lesson: str
    memory_update: dict[str, Any]
    rule_candidate: dict[str, Any]
    review_report: dict[str, Any]
