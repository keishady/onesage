from __future__ import annotations

from dataclasses import dataclass
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "onesage64gua.jsonl"


ACTION_GUA_HINTS = {
    "observe": 20,
    "wait": 5,
    "test": 24,
    "advance": 35,
    "retreat": 33,
    "stop": 52,
    "cooperate": 13,
}


@dataclass(frozen=True)
class GuaTemplate:
    gua_name: str
    gua_number: int
    initial_state_vector: dict[str, Any]
    dynamic_rules: list[dict[str, Any]]
    trend_prediction: str
    source_reference: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GuaTemplate":
        return cls(
            gua_name=str(data["gua_name"]),
            gua_number=int(data["gua_number"]),
            initial_state_vector=dict(data["initial_state_vector"]),
            dynamic_rules=list(data["dynamic_rules"]),
            trend_prediction=str(data["trend_prediction"]),
            source_reference=str(data["source_reference"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gua_name": self.gua_name,
            "gua_number": self.gua_number,
            "initial_state_vector": self.initial_state_vector,
            "dynamic_rules": self.dynamic_rules,
            "trend_prediction": self.trend_prediction,
            "source_reference": self.source_reference,
        }


@lru_cache(maxsize=1)
def load_gua_templates() -> tuple[GuaTemplate, ...]:
    records: list[GuaTemplate] = []
    with DATA_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(GuaTemplate.from_dict(json.loads(line)))
    if len(records) != 64:
        raise ValueError(f"Expected 64 gua templates, got {len(records)} from {DATA_PATH}")
    return tuple(records)


def get_gua(identifier: int | str) -> GuaTemplate:
    templates = load_gua_templates()
    if isinstance(identifier, int):
        if not 1 <= identifier <= 64:
            raise KeyError(f"gua_number out of range: {identifier}")
        return templates[identifier - 1]

    value = identifier.replace("卦", "").strip()
    for template in templates:
        if template.gua_name == value or f"{template.gua_name}卦" == identifier:
            return template
    raise KeyError(f"Unknown gua: {identifier}")


def gua_for_action(action_type: str) -> GuaTemplate:
    return get_gua(ACTION_GUA_HINTS.get(action_type, 20))


def infer_gua_from_situation(frame: Any, action_type: str) -> GuaTemplate:
    """Select a gua from situation features, not from the final risk label."""
    if frame.financial_potential > 0 or frame.credential_exposure > 0 or frame.destructive_potential > 0:
        return get_gua(52)  # 艮: stop at boundary
    if frame.ambiguity >= 0.75:
        return get_gua(4)  # 蒙: unclear request needs clarification
    if frame.externality >= 0.6 and frame.urgency > 0:
        return get_gua(5)  # 需: danger ahead, wait and provision
    if frame.externality >= 0.6:
        return get_gua(9)  # 小畜: small controlled batch before expansion
    if frame.intent_label == "read_only_analysis":
        return get_gua(20)  # 观: observe and interpret
    if frame.intent_label == "local_creation_or_edit" and frame.ambiguity < 0.45:
        return get_gua(24)  # 复: return to a small starting step
    if any("阻" in factor or "risk" in factor.lower() for factor in frame.risk_factors):
        return get_gua(39)  # 蹇: obstacle, seek route/help
    return gua_for_action(action_type)


def infer_gua_from_command(command: str, action_type: str, risk_level: str, frame: Any | None = None) -> GuaTemplate:
    if frame is not None:
        return infer_gua_from_situation(frame, action_type)
    if risk_level == "L3_critical":
        return get_gua(52)
    if risk_level == "L2_write_external":
        return get_gua(5)
    return gua_for_action(action_type)


def dynamic_rule_for_line(template: GuaTemplate, moving_line: int | str) -> dict[str, Any]:
    target = str(moving_line)
    for rule in template.dynamic_rules:
        if str(rule.get("moving_line")) == target:
            return rule
    raise KeyError(f"No dynamic rule for {template.gua_name} moving_line={moving_line}")


def phase_mapping(template: GuaTemplate) -> dict[str, Any]:
    state = template.initial_state_vector
    yin_yang = state.get("yin_yang_balance", {})
    rules = []
    for rule in template.dynamic_rules:
        update = rule.get("state_update", {})
        rules.append(
            {
                "trigger_condition": rule.get("trigger_condition"),
                "moving_line": rule.get("moving_line"),
                "phase_update": update.get("phase_update"),
                "action_bias": update.get("action_bias"),
                "risk_delta": update.get("risk_delta", 0),
                "opportunity_delta": update.get("opportunity_delta", 0),
                "review_required": update.get("review_required", False),
            }
        )
    return {
        "base_phase": yin_yang.get("phase", "unknown"),
        "trend_prediction": template.trend_prediction,
        "rules": rules,
    }


def choose_active_dimension(template: GuaTemplate, policy: Any, command: str, frame: Any | None = None) -> str:
    if frame is not None:
        if frame.financial_potential > 0 or frame.destructive_potential > 0 or frame.credential_exposure > 0:
            return "tail_risk"
        if frame.externality >= 0.6:
            return "friction"
        if frame.ambiguity >= 0.6:
            return "dominant_force"
        if frame.intent_label == "read_only_analysis":
            return "environment"
        if frame.intent_label == "local_creation_or_edit":
            return "internal_resource"
        if frame.urgency > 0:
            return "opportunity"

    state = template.initial_state_vector
    upper = state.get("upper_trigram", {}).get("name", "")
    lower = state.get("lower_trigram", {}).get("name", "")
    phase = state.get("yin_yang_balance", {}).get("phase", "")
    policy_risk = getattr(getattr(policy, "risk_level", None), "value", "")

    if getattr(policy, "blocked", False) or policy_risk == "L3_critical":
        return "tail_risk"
    if getattr(policy, "approval_required", False):
        return "friction"
    if upper in {"坎", "艮"} or "risk" in phase:
        return "tail_risk"
    if lower in {"震", "巽"} and any(word in command for word in ["启动", "推进", "立刻", "马上", "launch", "start"]):
        return "opportunity"
    if upper in {"兑", "离"}:
        return "environment"
    if lower in {"坤", "艮"}:
        return "internal_resource"
    return "dominant_force"


def should_act_now_from_gua(template: GuaTemplate, policy: Any, frame: Any | None = None) -> bool:
    if getattr(policy, "blocked", False) or getattr(policy, "approval_required", False):
        return False
    if frame is not None:
        if frame.ambiguity >= 0.6:
            return False
        if frame.intent_label == "read_only_analysis" and frame.externality == 0:
            return True
        if frame.urgency > 0 and frame.fact_gaps:
            return False

    phase = template.initial_state_vector.get("yin_yang_balance", {}).get("phase", "")
    if phase == "yin_growth_cycle":
        return False
    if phase == "strong_yang_or_overextension_watch" and frame is not None and frame.externality > 0:
        return False
    if template.gua_number in {5, 6, 12, 23, 29, 33, 36, 39, 47, 52, 54, 56, 60, 62}:
        return False
    return True


def state_overlay(template: GuaTemplate, active_dimension: str, should_act_now: bool) -> dict[str, Any]:
    state = template.initial_state_vector
    return {
        "gua_name": template.gua_name,
        "gua_number": template.gua_number,
        "hexagram_pattern_bottom_to_top": state.get("hexagram_pattern_bottom_to_top"),
        "lower_trigram": state.get("lower_trigram"),
        "upper_trigram": state.get("upper_trigram"),
        "bagua_relation": state.get("bagua_relation"),
        "yin_yang_balance": state.get("yin_yang_balance"),
        "plain_explanations": state.get("plain_explanations"),
        "semantic_mappings": state.get("semantic_mappings"),
        "active_dimension": active_dimension,
        "should_act_now": should_act_now,
        "phase_mapping": phase_mapping(template),
        "source_reference": template.source_reference,
    }


def apply_moving_line(template: GuaTemplate, moving_line: int | str) -> dict[str, Any]:
    rule = dynamic_rule_for_line(template, moving_line)
    return {
        "gua_name": template.gua_name,
        "gua_number": template.gua_number,
        "trigger_condition": rule.get("trigger_condition"),
        "moving_line": rule.get("moving_line"),
        "position_logic": rule.get("position_logic"),
        "state_update": rule.get("state_update"),
        "plain_meaning_hint": rule.get("plain_meaning_hint"),
        "source_reference": template.source_reference,
    }
