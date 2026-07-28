from __future__ import annotations

from .schemas import StrategicContext


DOMAIN_KEYWORDS = {
    "content": ["youtube", "频道", "视频", "内容", "自媒体", "channel", "shorts"],
    "startup": ["创业", "项目", "产品", "mvp", "用户", "增长", "saas", "app"],
    "career": ["转型", "职业", "辞职", "岗位", "产品经理", "offer", "面试"],
    "learning": ["学习", "学", "编程", "技能", "课程", "rust", "python"],
    "side_project": ["副业", "朋友邀请", "每周", "合伙", "兼职"],
}

COMPETITION_WORDS = ["竞争", "同类", "类似", "饱和", "红海", "激烈", "competitor", "crowded"]
DECLINE_WORDS = ["没增长", "没有增长", "增长停", "失败", "亏", "低迷", "没人用", "没有起色", "下滑"]
BREAKOUT_WORDS = ["爆发", "快速增长", "风口", "机会窗口", "红利", "需求增长"]
SUNK_COST_WORDS = ["已经投入", "投入很多", "做了半年", "花了很多", "舍不得", "沉没"]
HIGH_COMMIT_WORDS = ["辞职", "一年", "大量投入", "全职", "all in", "借钱"]
MEDIUM_COMMIT_WORDS = ["三个月", "3个月", "每周", "持续", "mvp", "系统学习"]
STOP_WORDS = ["要不要放弃", "是否停止", "要不要停止", "要不要继续", "停掉"]
URGENCY_WORDS = ["马上", "立刻", "现在就", "尽快", "asap", "immediately"]


def _contains(text: str, words: list[str]) -> list[str]:
    lower = text.lower()
    return [word for word in words if word.lower() in lower]


def infer_domain(question: str, domain: str | None = None) -> str:
    if domain:
        return domain
    hits = {name: len(_contains(question, words)) for name, words in DOMAIN_KEYWORDS.items()}
    best = max(hits, key=hits.get)
    return best if hits[best] else "general"


def parse_context(question: str, *, project_id: str | None = None, domain: str | None = None) -> StrategicContext:
    inferred_domain = infer_domain(question, domain)
    competition_hits = _contains(question, COMPETITION_WORDS)
    decline_hits = _contains(question, DECLINE_WORDS)
    breakout_hits = _contains(question, BREAKOUT_WORDS)
    sunk_cost_hits = _contains(question, SUNK_COST_WORDS)
    high_commit_hits = _contains(question, HIGH_COMMIT_WORDS)
    medium_commit_hits = _contains(question, MEDIUM_COMMIT_WORDS)
    stop_hits = _contains(question, STOP_WORDS)
    urgency_hits = _contains(question, URGENCY_WORDS)

    known_facts = [f"用户问题：{question}", f"初步领域：{inferred_domain}"]
    if competition_hits:
        known_facts.append("用户问题包含竞争或同质化信号：" + "、".join(competition_hits))
    if decline_hits:
        known_facts.append("用户问题包含增长停滞或失败信号：" + "、".join(decline_hits))
    if breakout_hits:
        known_facts.append("用户问题包含机会窗口或增长信号：" + "、".join(breakout_hits))
    if high_commit_hits or medium_commit_hits:
        known_facts.append("用户问题包含投入周期或承诺信号：" + "、".join(high_commit_hits + medium_commit_hits))
    if sunk_cost_hits:
        known_facts.append("用户问题包含沉没成本信号：" + "、".join(sunk_cost_hits))

    assumptions = [
        "当前只根据用户问题做第一版战略判断，未使用外部数据。",
        "缺失信息必须进入 unknowns，不能当作事实。",
    ]

    unknowns = [
        "缺少目标的量化成功标准",
        "缺少用户当前可投入时间、资金和技能资源",
        "缺少真实历史数据和样本反馈",
    ]
    if inferred_domain in {"content", "startup"}:
        unknowns.append("缺少竞品表现、用户反馈和转化数据")
    if inferred_domain == "career":
        unknowns.append("缺少当前能力证据、作品集质量和目标岗位反馈")
    if inferred_domain == "learning":
        unknowns.append("缺少学习时长、练习方式和阶段成果")

    resources = {
        "time": "high_commitment_signal" if high_commit_hits else "medium_commitment_signal" if medium_commit_hits else "unspecified",
        "money": "unspecified",
        "skills": [],
        "channels": [],
        "project_id": project_id,
    }
    constraints = []
    if high_commit_hits:
        constraints.append("存在高承诺行动信号，必须要求更充分事实和退出路线")
    if medium_commit_hits:
        constraints.append("存在中承诺投入信号，需要阶段性指标")

    competition = {
        "intensity": "high" if competition_hits else "unknown",
        "signals": competition_hits,
    }
    history = {
        "decline_signals": decline_hits,
        "sunk_cost_signals": sunk_cost_hits,
        "stop_or_continue_question": bool(stop_hits),
    }
    user_bias = "sunk_cost_pressure" if sunk_cost_hits else "possible_action_bias" if urgency_hits else ""

    ambiguity = 0.25
    if len(question.strip()) < 12:
        ambiguity += 0.35
    if not competition_hits and not decline_hits and not breakout_hits and inferred_domain == "general":
        ambiguity += 0.25
    if unknowns:
        ambiguity += 0.1

    return StrategicContext(
        question=question,
        goal=question,
        domain=inferred_domain,
        known_facts=known_facts,
        assumptions=assumptions,
        unknowns=list(dict.fromkeys(unknowns)),
        resources=resources,
        constraints=constraints,
        competition=competition,
        history=history,
        user_bias=user_bias,
        urgency=min(1.0, 0.25 * len(urgency_hits)),
        ambiguity=min(1.0, ambiguity),
    )
