from __future__ import annotations

from .core.onesage64gua import (
    choose_active_dimension,
    infer_gua_from_command,
    should_act_now_from_gua,
    state_overlay,
)
from .model_router import route_for
from .safety import build_policy
from .schemas import (
    ActionType,
    Contradiction,
    Decision,
    DimensionState,
    ModelRole,
    RiskLevel,
    SemanticFrame,
    StateDimension,
    StateVector,
)
from .semantic_analyzer import analyze_command


def contradiction_candidates(frame: SemanticFrame, template_name: str, json_should_act: bool) -> list[Contradiction]:
    candidates: list[Contradiction] = []

    if frame.urgency > 0 or "命令带有即时/跳过审查压力" in frame.risk_factors:
        candidates.append(
            Contradiction(
                name="行动冲动 vs 调查不足",
                side_a="命令要求快速行动或跳过审查",
                side_b="语义帧仍存在信息缺口：" + "；".join(frame.fact_gaps[:3]),
                severity=min(0.95, 0.55 + frame.urgency * 0.25 + frame.ambiguity * 0.25),
            )
        )

    if frame.externality > 0 or frame.side_effects != ["no_obvious_external_side_effect"]:
        candidates.append(
            Contradiction(
                name="行动收益 vs 外部副作用",
                side_a="执行可能推进目标",
                side_b="可能产生副作用：" + "；".join(frame.side_effects),
                severity=min(0.95, 0.45 + frame.externality * 0.35 + frame.destructive_potential * 0.3 + frame.financial_potential * 0.3),
            )
        )

    if frame.ambiguity >= 0.5:
        candidates.append(
            Contradiction(
                name="目标模糊 vs 可执行性",
                side_a="用户给出了行动意图",
                side_b="对象、范围或成功标准不清，不能形成可靠执行计划",
                severity=min(0.9, 0.45 + frame.ambiguity * 0.45),
            )
        )

    candidates.append(
        Contradiction(
            name="卦象趋势 vs 授权边界",
            side_a=f"{template_name}卦给出趋势模板，should_act_now={json_should_act}",
            side_b="OneSage 仍必须受权限、sandbox、override 与 outcome review 约束",
            severity=0.65 if not json_should_act else 0.35,
        )
    )
    return sorted(candidates, key=lambda item: item.severity, reverse=True)


def build_state_vector(command: str, risk_level: RiskLevel, gua_state: dict, frame: SemanticFrame) -> StateVector:
    lower = gua_state.get("lower_trigram", {})
    upper = gua_state.get("upper_trigram", {})
    phase = gua_state.get("yin_yang_balance", {}).get("phase", "unknown")
    trend = gua_state.get("phase_mapping", {}).get("trend_prediction", "")
    lower_name = lower.get("name", "")
    upper_name = upper.get("name", "")

    environment_state = DimensionState.CHANGING if frame.externality > 0 or upper_name in {"离", "兑", "巽", "震"} else DimensionState.UNKNOWN
    internal_state = DimensionState.STRONG if frame.intent_label in {"read_only_analysis", "local_creation_or_edit"} else DimensionState.UNKNOWN
    friction_state = DimensionState.STRONG if risk_level in {RiskLevel.L2_WRITE_EXTERNAL, RiskLevel.L3_CRITICAL} or frame.ambiguity >= 0.6 else DimensionState.WEAK
    opportunity_state = DimensionState.CHANGING if frame.urgency > 0 or lower_name in {"震", "巽", "离"} else DimensionState.UNKNOWN
    dominant_state = DimensionState.CHANGING if frame.ambiguity >= 0.5 or frame.risk_factors else DimensionState.UNKNOWN
    tail_state = DimensionState.CHANGING if risk_level in {RiskLevel.L2_WRITE_EXTERNAL, RiskLevel.L3_CRITICAL} or phase in {"yin_growth_cycle", "strong_yang_or_overextension_watch"} else DimensionState.WEAK

    return StateVector(
        environment=StateDimension(
            state=environment_state,
            confidence=round(0.45 + frame.externality * 0.35, 2),
            reason=f"语义帧 target_scope={frame.target_scope}；外卦为{upper_name}，工程语义：{upper.get('engineering_semantic', '未标注')}。",
        ),
        internal_resource=StateDimension(
            state=internal_state,
            confidence=round(0.5 + (0.2 if frame.intent_label in {'read_only_analysis', 'local_creation_or_edit'} else 0), 2),
            reason=f"语义帧 intent={frame.intent_label}；内卦为{lower_name}，工程语义：{lower.get('engineering_semantic', '未标注')}。",
        ),
        friction=StateDimension(
            state=friction_state,
            confidence=round(min(0.95, 0.45 + frame.externality * 0.25 + frame.ambiguity * 0.25 + frame.destructive_potential * 0.25), 2),
            reason=f"风险等级={risk_level.value}；信息缺口={len(frame.fact_gaps)}；卦象趋势：{trend}",
        ),
        opportunity=StateDimension(
            state=opportunity_state,
            confidence=round(0.45 + frame.urgency * 0.3, 2),
            reason=f"命令紧急度={frame.urgency}; 卦象 phase={phase}。",
        ),
        dominant_force=StateDimension(
            state=dominant_state,
            confidence=round(min(0.9, 0.45 + frame.ambiguity * 0.25 + len(frame.risk_factors) * 0.05), 2),
            reason="主要矛盾来自语义帧的最高 severity contradiction，而不是固定模板。",
        ),
        tail_risk=StateDimension(
            state=tail_state,
            confidence=round(min(0.95, 0.45 + frame.financial_potential * 0.3 + frame.destructive_potential * 0.3 + frame.credential_exposure * 0.25 + frame.externality * 0.15), 2),
            reason=f"副作用={', '.join(frame.side_effects)}；可逆性={frame.reversibility}。",
        ),
    )


def provisional_action_from_frame(frame: SemanticFrame, risk_level: RiskLevel) -> ActionType:
    if risk_level == RiskLevel.L3_CRITICAL:
        return ActionType.STOP
    if risk_level == RiskLevel.L2_WRITE_EXTERNAL:
        return ActionType.WAIT
    if frame.ambiguity >= 0.6:
        return ActionType.WAIT
    if frame.intent_label == "read_only_analysis":
        return ActionType.OBSERVE
    if frame.intent_label == "local_creation_or_edit":
        return ActionType.TEST
    return ActionType.OBSERVE


def decide(project_id: str, command: str, *, prefer_mercury: bool = False) -> Decision:
    frame = analyze_command(command)
    policy = build_policy(command, frame=frame)
    provisional_action = provisional_action_from_frame(frame, policy.risk_level)
    template = infer_gua_from_command(command, provisional_action.value, policy.risk_level.value, frame=frame)
    json_should_act = should_act_now_from_gua(template, policy, frame=frame)
    active = choose_active_dimension(template, policy, command, frame=frame)
    gua_state = state_overlay(template, active, json_should_act)
    state = build_state_vector(command, policy.risk_level, gua_state, frame)

    facts = frame.facts + [
        f"初步风险等级：{policy.risk_level.value}",
        f"所需权限：{', '.join(permission.value for permission in policy.required_permissions)}",
        f"周易模板：{template.gua_name}卦第{template.gua_number}",
        f"卦象趋势：{template.trend_prediction}",
    ]
    unknowns = frame.fact_gaps
    assumptions = frame.assumptions + [
        "v0.4 使用语义帧生成事实缺口、风险因素与局势特征；关键词只作为语义线索之一。",
        "周易模板由局势特征选择，再反向影响 action/should_act_now。",
    ]

    contradictions = contradiction_candidates(frame, template.gua_name, json_should_act)
    primary = contradictions[0].name

    objection_required = policy.approval_required or not json_should_act
    objection_reasons: list[str] = []
    action = provisional_action
    minimum_next_action = policy.safer_alternative
    forbidden = ["不要扩大执行范围", "不要跳过复盘", "不要绕过权限策略"]

    if policy.risk_level == RiskLevel.L3_CRITICAL:
        action = ActionType.STOP
        objection_reasons = [
            policy.blocked_reason,
            "v0.4 默认阻断 L3：资金、破坏性、shell、凭据或权限配置变更。",
            f"{template.gua_name}卦趋势要求先止住边界风险，只生成计划、风险清单、回滚方案和确认问题。",
        ]
        forbidden += ["禁止直接执行 L3 动作", "禁止让 skill 自行提权"]
    elif policy.risk_level == RiskLevel.L2_WRITE_EXTERNAL:
        action = ActionType.WAIT
        objection_reasons = [
            policy.approval_reason,
            "语义帧显示外部影响或公开副作用，必须先明确范围、对象和回滚方式。",
            f"{template.gua_name}卦 should_act_now={json_should_act}，默认降级为 wait/test。",
        ]
        forbidden += ["禁止直接群发/批量发布", "禁止无审计执行外部写入"]
    elif frame.ambiguity >= 0.6:
        action = ActionType.WAIT
        objection_reasons = [
            "语义帧显示命令对象或动作边界不清。",
            "先补齐对象、范围、成功标准，再做最小可逆动作。",
        ]
    elif not json_should_act:
        action = ActionType.WAIT
        objection_reasons = [
            f"{template.gua_name}卦 phase 推演不支持立即行动。",
            "按照守中原则，应先补事实、等待条件或做更小的试探。",
        ]
    else:
        objection_required = False

    route_role = ModelRole.TOOL_PLANNING if action in {ActionType.TEST, ActionType.ADVANCE} else ModelRole.VERIFY
    model_route = route_for(route_role, risk_level=policy.risk_level, prefer_mercury=prefer_mercury)

    return Decision(
        project_id=project_id,
        objective=command,
        facts=facts,
        unknowns=unknowns,
        assumptions=assumptions,
        contradictions=contradictions,
        primary_contradiction=primary,
        state_vector=state,
        active_variable=active,
        stage=f"判断/试探阶段；周易 phase={gua_state['yin_yang_balance'].get('phase')}; semantic_intent={frame.intent_label}",
        position="用户保留最终授权；OneSage 提供判断、反对、执行、审计与复盘。",
        timing_judgment=(
            f"当前引用{template.gua_name}卦模板：{template.trend_prediction}"
            if objection_required
            else f"当前引用{template.gua_name}卦模板，可做最小有效行动并记录结果。"
        ),
        action_type=action,
        minimum_next_action=minimum_next_action,
        forbidden_actions=forbidden,
        reeval_conditions=[
            "补充关键事实后",
            "完成最小样本测试后",
            "风险等级变化后",
            "用户明确 override 后",
            "skill 权限或模型路由变化后",
            "动爻规则触发后",
        ],
        human_confirm_required=policy.approval_required,
        objection_required=objection_required,
        objection_reasons=objection_reasons,
        override_allowed=policy.risk_level != RiskLevel.L3_CRITICAL,
        risk_level=policy.risk_level,
        success_metric="执行后达到用户目标，且没有产生不可接受副作用；结果必须进入 outcome review。",
        raw_command=command,
        should_act_now=json_should_act,
        policy=policy,
        model_route=model_route,
        metadata={
            "semantic_frame": frame.model_dump(),
            "onesage64gua": {
                **gua_state,
                "dynamic_rules": template.dynamic_rules,
            },
        },
    )
