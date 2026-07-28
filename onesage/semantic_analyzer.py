from __future__ import annotations

import re

from .schemas import SemanticFrame


LEXICON = {
    "read": [
        "summarize", "summary", "analyze", "review", "read", "inspect", "explain",
        "总结", "分析", "阅读", "查看", "解释", "复盘", "审计",
    ],
    "local_write": [
        "draft", "write", "create", "generate", "save", "export", "update file",
        "起草", "写", "生成", "创建", "保存", "导出", "更新文件", "记录",
    ],
    "external_write": [
        "send", "email", "mail", "publish", "post", "submit", "launch", "campaign",
        "outreach", "broadcast", "blast", "deploy", "release", "form",
        "发送", "发邮件", "群发", "发布", "提交", "上线", "投放", "推广", "开发信",
        "营销", "活动", "表单", "客户", "外部写入",
    ],
    "financial": [
        "pay", "payment", "wire", "transfer", "invoice", "purchase", "buy", "sell",
        "account", "bank", "wallet", "货款", "打款", "打到", "账户", "银行卡", "转账",
        "付款", "支付", "交易", "买入", "卖出", "钱包", "发票",
    ],
    "destructive": [
        "delete", "remove", "drop", "wipe", "reset", "rm -rf", "destroy", "kill",
        "删除", "清空", "重置", "销毁", "删库", "下线", "关闭生产",
    ],
    "shell": ["shell", "sudo", "cmd", "powershell", "bash", "命令行", "终端", "脚本"],
    "credential": [
        "password", "token", "secret", "credential", "api key", "cookie", "login",
        "密码", "密钥", "凭据", "令牌", "登录", "授权", "权限",
    ],
    "browser": ["browser", "webpage", "website", "login", "cookie", "浏览器", "网页", "网站"],
    "urgent": [
        "immediately", "now", "right now", "asap", "directly", "don't ask", "without review",
        "立刻", "马上", "现在就", "直接", "不用看", "别问", "立即", "赶紧",
    ],
    "ambiguous": [
        "thing", "stuff", "something", "whatever", "搞个东西", "弄一下", "处理一下",
        "做一下", "搞一下", "那个", "随便",
    ],
    "production": ["prod", "production", "server", "线上", "生产", "服务器"],
}


OBJECT_PATTERNS = [
    r"campaign",
    r"meeting",
    r"email",
    r"server",
    r"account",
    r"会议",
    r"开发信",
    r"客户",
    r"账户",
    r"货款",
    r"服务器",
    r"文件",
    r"代码",
]


def _contains(command_lc: str, words: list[str]) -> list[str]:
    return [word for word in words if word.lower() in command_lc]


def _language(command: str) -> str:
    has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in command)
    has_ascii = any("a" <= ch.lower() <= "z" for ch in command)
    if has_cjk and has_ascii:
        return "mixed"
    if has_cjk:
        return "zh"
    if has_ascii:
        return "en"
    return "unknown"


def _objects(command_lc: str) -> list[str]:
    found: list[str] = []
    for pattern in OBJECT_PATTERNS:
        if re.search(pattern, command_lc, flags=re.IGNORECASE):
            found.append(pattern)
    return found


def analyze_command(command: str) -> SemanticFrame:
    command_lc = command.lower()
    hits = {name: _contains(command_lc, words) for name, words in LEXICON.items()}

    action_verbs = (
        hits["read"]
        + hits["local_write"]
        + hits["external_write"]
        + hits["financial"]
        + hits["destructive"]
        + hits["shell"]
    )
    objects = _objects(command_lc)

    urgency = min(1.0, 0.25 * len(hits["urgent"]))
    ambiguity = 0.15
    if hits["ambiguous"]:
        ambiguity += 0.55
    if not action_verbs:
        ambiguity += 0.35
    if not objects and not hits["read"]:
        ambiguity += 0.2
    ambiguity = min(1.0, ambiguity)

    externality = 0.0
    if hits["external_write"]:
        externality += 0.65
    if hits["browser"] or hits["production"]:
        externality += 0.2
    externality = min(1.0, externality)

    destructive = min(1.0, 0.65 * bool(hits["destructive"]) + 0.25 * bool(hits["production"]))
    financial = min(1.0, 0.8 * bool(hits["financial"]))
    credential = min(1.0, 0.75 * bool(hits["credential"]))

    if hits["financial"]:
        intent = "financial_transfer_or_commerce"
    elif hits["destructive"] or hits["shell"]:
        intent = "destructive_or_system_operation"
    elif hits["external_write"]:
        intent = "external_write_or_campaign"
    elif hits["local_write"]:
        intent = "local_creation_or_edit"
    elif hits["read"]:
        intent = "read_only_analysis"
    else:
        intent = "underspecified_request"

    facts = [f"用户命令文本：{command}", f"识别意图：{intent}"]
    if action_verbs:
        facts.append(f"动作线索：{', '.join(action_verbs)}")
    if objects:
        facts.append(f"对象线索：{', '.join(objects)}")

    risk_factors: list[str] = []
    if urgency > 0:
        risk_factors.append("命令带有即时/跳过审查压力")
    if ambiguity >= 0.6:
        risk_factors.append("命令对象或动作边界不清")
    if externality >= 0.6:
        risk_factors.append("可能影响外部用户、平台或公开环境")
    if destructive > 0:
        risk_factors.append("包含删除、重置、生产环境或破坏性操作线索")
    if financial > 0:
        risk_factors.append("包含付款、转账、账户或交易线索")
    if credential > 0:
        risk_factors.append("包含凭据、登录、token 或权限线索")

    side_effects: list[str] = []
    if externality >= 0.6:
        side_effects.append("external_users_or_systems_may_be_changed")
    if destructive > 0:
        side_effects.append("data_or_service_may_be_destroyed")
    if financial > 0:
        side_effects.append("money_or_asset_may_move")
    if credential > 0:
        side_effects.append("secret_or_session_may_be_exposed")
    if not side_effects and hits["local_write"]:
        side_effects.append("local_workspace_may_change")
    if not side_effects:
        side_effects.append("no_obvious_external_side_effect")

    fact_gaps = build_fact_gaps(intent, ambiguity, urgency, externality, destructive, financial, credential)
    assumptions = build_assumptions(intent, side_effects, ambiguity)

    target_scope = "external" if externality >= 0.6 else "local" if hits["local_write"] or hits["read"] else "unspecified"
    if financial > 0:
        target_scope = "financial"
    if destructive > 0 or hits["production"]:
        target_scope = "system_or_production"

    reversibility = "low" if destructive > 0 or financial > 0 else "medium" if externality >= 0.6 else "high" if hits["read"] else "unknown"
    confidence = max(0.25, min(0.9, 0.85 - ambiguity * 0.35 + bool(action_verbs) * 0.1))

    return SemanticFrame(
        raw_command=command,
        language=_language(command),
        intent_label=intent,
        action_verbs=action_verbs,
        objects=objects,
        facts=facts,
        assumptions=assumptions,
        fact_gaps=fact_gaps,
        risk_factors=risk_factors,
        side_effects=side_effects,
        target_scope=target_scope,
        reversibility=reversibility,
        urgency=urgency,
        ambiguity=ambiguity,
        externality=externality,
        destructive_potential=destructive,
        financial_potential=financial,
        credential_exposure=credential,
        confidence=confidence,
    )


def build_fact_gaps(
    intent: str,
    ambiguity: float,
    urgency: float,
    externality: float,
    destructive: float,
    financial: float,
    credential: float,
) -> list[str]:
    gaps: list[str] = []
    if ambiguity >= 0.6:
        gaps.append("需要明确具体对象、范围和完成标准")
    if intent == "read_only_analysis":
        gaps.extend(["需要确认要读取/总结的材料来源", "需要确认输出格式和受众"])
    if intent == "local_creation_or_edit":
        gaps.extend(["需要确认目标文件或工作区范围", "需要确认是否允许覆盖已有内容"])
    if externality >= 0.6:
        gaps.extend(["需要确认外部对象名单或发布范围", "需要确认小样本测试和回滚方案", "需要确认是否会影响客户、账号或公共声誉"])
    if destructive > 0:
        gaps.extend(["需要确认备份位置", "需要确认可逆性和恢复步骤"])
    if financial > 0:
        gaps.extend(["需要确认收款/付款主体、金额、账户和审批凭据", "需要二次人工确认"])
    if credential > 0:
        gaps.extend(["需要确认凭据最小权限、保存方式和撤销路径"])
    if urgency > 0:
        gaps.append("需要确认为什么必须立即行动，以及延迟的真实代价")
    return list(dict.fromkeys(gaps)) or ["需要确认任务目标和成功标准"]


def build_assumptions(intent: str, side_effects: list[str], ambiguity: float) -> list[str]:
    assumptions = [f"命令被暂定为 {intent}，后续可由用户补事实修正"]
    if "no_obvious_external_side_effect" in side_effects:
        assumptions.append("暂未发现外部副作用，但仍需在执行前按权限策略复核")
    else:
        assumptions.append("命令可能产生副作用，不能只按字面意图执行")
    if ambiguity >= 0.6:
        assumptions.append("当前语义边界不清，默认降低行动强度")
    return assumptions
