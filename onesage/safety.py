from __future__ import annotations

import json
from pathlib import Path

from .schemas import Permission, PolicyDecision, RiskLevel, SandboxResult, SemanticFrame, SkillManifest
from .semantic_analyzer import analyze_command


IMMEDIATE_WORDS = [
    "立刻", "马上", "现在就", "直接", "不用看", "别问", "立即", "赶紧",
    "immediately", "right now", "asap", "directly", "don't ask",
]


def infer_permissions(command: str, frame: SemanticFrame | None = None) -> list[Permission]:
    frame = frame or analyze_command(command)
    permissions: set[Permission] = set()

    if frame.intent_label == "read_only_analysis":
        permissions.add(Permission.READ_LOCAL)
    if frame.intent_label == "local_creation_or_edit":
        permissions.add(Permission.WRITE_LOCAL)
    if frame.externality >= 0.6:
        permissions.add(Permission.EXTERNAL_WRITE)
        permissions.add(Permission.NETWORK)
    if frame.financial_potential > 0:
        permissions.add(Permission.FINANCIAL)
        permissions.add(Permission.NETWORK)
    if frame.destructive_potential > 0:
        permissions.add(Permission.SHELL)
    if frame.credential_exposure > 0:
        permissions.add(Permission.CREDENTIALS)
    if any(word in frame.action_verbs for word in ["browser", "login", "cookie", "浏览器", "登录"]):
        permissions.add(Permission.BROWSER)

    if not permissions:
        permissions.add(Permission.READ_LOCAL)
    return sorted(permissions, key=lambda item: item.value)


def infer_risk_level(command: str, frame: SemanticFrame | None = None) -> RiskLevel:
    frame = frame or analyze_command(command)
    if frame.financial_potential > 0 or frame.destructive_potential > 0 or frame.credential_exposure > 0:
        return RiskLevel.L3_CRITICAL
    if frame.externality >= 0.6:
        return RiskLevel.L2_WRITE_EXTERNAL
    if frame.intent_label == "local_creation_or_edit":
        return RiskLevel.L1_WRITE_LOCAL
    return RiskLevel.L0_READ_ONLY


def should_act_now(command: str, risk_level: RiskLevel, unknown_count: int, frame: SemanticFrame | None = None) -> bool:
    frame = frame or analyze_command(command)
    if risk_level in {RiskLevel.L2_WRITE_EXTERNAL, RiskLevel.L3_CRITICAL}:
        return False
    if frame.ambiguity >= 0.6:
        return False
    if frame.urgency > 0 and unknown_count >= 2:
        return False
    return risk_level in {RiskLevel.L0_READ_ONLY, RiskLevel.L1_WRITE_LOCAL}


def build_policy(command: str, unknown_count: int | None = None, frame: SemanticFrame | None = None) -> PolicyDecision:
    frame = frame or analyze_command(command)
    unknown_count = len(frame.fact_gaps) if unknown_count is None else unknown_count
    risk = infer_risk_level(command, frame)
    permissions = infer_permissions(command, frame)
    act_now = should_act_now(command, risk, unknown_count, frame)

    if risk == RiskLevel.L3_CRITICAL:
        return PolicyDecision(
            should_act_now=False,
            risk_level=risk,
            required_permissions=permissions,
            approval_required=True,
            approval_reason="L3 关键动作需要两次确认，并且在 v0.4 默认阻断。",
            blocked=True,
            blocked_reason="语义分析发现资金/凭据/破坏性/系统级风险，不能直接执行。",
            safer_alternative="只生成可回滚计划、风险清单、审批清单和必要的人工确认问题。",
            confirmations_required=2,
        )

    if risk == RiskLevel.L2_WRITE_EXTERNAL:
        return PolicyDecision(
            should_act_now=False,
            risk_level=risk,
            required_permissions=permissions,
            approval_required=True,
            approval_reason="语义分析发现外部写入或公开影响，需要人工确认和小样本测试。",
            blocked=False,
            safer_alternative="先明确对象/范围/成功标准，再执行 3-5 个对象的小样本测试并记录日志。",
            confirmations_required=1,
        )

    if frame.ambiguity >= 0.6:
        return PolicyDecision(
            should_act_now=False,
            risk_level=risk,
            required_permissions=permissions,
            approval_required=False,
            approval_reason="",
            blocked=False,
            safer_alternative="先把任务对象、范围和成功标准问清楚，再做最小动作。",
            confirmations_required=0,
        )

    return PolicyDecision(
        should_act_now=act_now,
        risk_level=risk,
        required_permissions=permissions,
        approval_required=False,
        safer_alternative="执行最小可逆动作，并记录 outcome。",
        confirmations_required=0,
    )


def load_skill_manifest(path: Path) -> SkillManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    return SkillManifest.from_dict(data)


def sandbox_skill(manifest: SkillManifest) -> SandboxResult:
    findings: list[str] = []
    blocked: list[Permission] = []
    risk = RiskLevel.L0_READ_ONLY
    approvals = 0

    if not manifest.entrypoint:
        findings.append("缺少 entrypoint。")

    if manifest.enabled:
        findings.append("新导入 skill 在审核前必须保持 disabled。")

    if Permission.SHELL in manifest.permissions or Permission.FINANCIAL in manifest.permissions:
        risk = RiskLevel.L3_CRITICAL
        approvals = 2
        blocked.extend([p for p in manifest.permissions if p in {Permission.SHELL, Permission.FINANCIAL}])
        findings.append("shell 或 financial 权限默认阻断。")
    elif any(
        p in manifest.permissions
        for p in [Permission.CREDENTIALS, Permission.EXTERNAL_WRITE, Permission.BROWSER, Permission.NETWORK]
    ):
        risk = RiskLevel.L2_WRITE_EXTERNAL
        approvals = 1
        findings.append("外部写入、浏览器、网络或凭据权限需要确认。")
    elif Permission.WRITE_LOCAL in manifest.permissions:
        risk = RiskLevel.L1_WRITE_LOCAL
        findings.append("本地写入权限只允许在声明的 filesystem_scope 内使用。")
        if not manifest.filesystem_scope:
            findings.append("write_local 权限缺少 filesystem_scope。")

    accepted = not blocked and not any(f.startswith("缺少") for f in findings)
    return SandboxResult(
        skill_name=manifest.name,
        accepted=accepted,
        risk_level=risk,
        required_approvals=approvals,
        findings=findings or ["只读 skill 已通过沙箱检查，可进入审核。"],
        blocked_permissions=blocked,
    )


def validate_skill_file(path: Path) -> tuple[SkillManifest | None, SandboxResult]:
    try:
        manifest = load_skill_manifest(path)
        return manifest, sandbox_skill(manifest)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return None, SandboxResult(
            skill_name=path.name,
            accepted=False,
            risk_level=RiskLevel.L3_CRITICAL,
            required_approvals=2,
            findings=[f"Manifest 校验失败：{exc}"],
        )
