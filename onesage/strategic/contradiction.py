from __future__ import annotations

from .schemas import ContradictionAnalysis, SituationAnalysis, StrategicContext


def analyze_contradiction(context: StrategicContext, situation: SituationAnalysis) -> ContradictionAnalysis:
    domain = context.domain

    if domain == "content":
        return ContradictionAnalysis(
            primary_contradiction="内容差异化不足 vs AI/同类内容供给过剩",
            side_a="用户希望继续获得频道增长",
            side_b="同类内容供给增加，普通内容更难被选择",
            main_aspect="内容差异化不足",
            why_primary="如果不能证明内容为什么值得被持续观看，提高产量只会放大无效成本。",
            secondary_contradictions=["制作效率 vs 选题质量", "短期数据焦虑 vs 长期定位"],
            resource_focus=["选题差异化", "用户反馈", "低成本内容测试"],
            deferred_issues=["扩大团队", "购买昂贵设备", "复杂自动化流程"],
            investigation_questions=["哪类内容完播率最高？", "评论是否出现差异化反馈？", "竞品哪些选题已经同质化？"],
        )

    if domain == "startup":
        return ContradictionAnalysis(
            primary_contradiction="用户需求/具体场景未验证 vs 长周期产品投入",
            side_a="用户希望投入项目或产品方向",
            side_b="市场、用户和场景证据不足",
            main_aspect="需求和场景未验证",
            why_primary="如果目标用户和场景不清，继续做产品会把资源投入到可能不存在的需求上。",
            secondary_contradictions=["产品功能 vs 真实留存", "投入周期 vs 用户验证"],
            resource_focus=["目标用户访谈", "垂直场景验证", "低成本原型"],
            deferred_issues=["完整 MVP", "大规模开发", "品牌包装"],
            investigation_questions=["谁是最痛的目标用户？", "用户是否愿意重复使用？", "用户是否愿意付费或迁移流程？"],
        )

    if domain == "career":
        return ContradictionAnalysis(
            primary_contradiction="目标岗位要求上升 vs 用户可证明能力不足",
            side_a="用户希望转型到新职业方向",
            side_b="目标岗位需要可证明作品、经验和反馈",
            main_aspect="可证明能力不足",
            why_primary="职业转型不是表态问题，而是能否用作品和反馈证明自己能胜任。",
            secondary_contradictions=["兴趣动机 vs 市场要求", "辞职冲动 vs 现金流保护"],
            resource_focus=["作品集", "行业反馈", "模拟面试", "能力缺口"],
            deferred_issues=["直接辞职", "长期脱产准备"],
            investigation_questions=["目标岗位真实要求是什么？", "当前作品集能否获得面试？", "现金流能支撑多久？"],
        )

    if domain == "learning":
        return ContradictionAnalysis(
            primary_contradiction="学习反馈不稳定 vs 用户期待快速看到成果",
            side_a="用户希望判断是否继续学习",
            side_b="当前进展慢导致放弃冲动",
            main_aspect="反馈机制不清",
            why_primary="早期学习失败感未必说明方向错误，可能是练习方式和反馈闭环不对。",
            secondary_contradictions=["长期能力建设 vs 短期挫败", "学习输入 vs 项目输出"],
            resource_focus=["小项目练习", "卡点记录", "反馈节奏"],
            deferred_issues=["长期承诺", "昂贵课程", "彻底否定方向"],
            investigation_questions=["每周实际练习多久？", "能否完成小项目？", "卡点主要集中在哪里？"],
        )

    if domain == "side_project":
        return ContradictionAnalysis(
            primary_contradiction="高时间承诺 vs 项目收益与可行性未验证",
            side_a="用户考虑投入副业或合伙项目",
            side_b="分工、收益、需求和退出机制不清",
            main_aspect="收益与可行性未验证",
            why_primary="高时间承诺会挤压其他机会，必须先证明项目值得占用长期资源。",
            secondary_contradictions=["朋友关系 vs 商业规则", "机会想象 vs 真实需求"],
            resource_focus=["两周试运行", "分工边界", "收益模型", "退出机制"],
            deferred_issues=["半年承诺", "长期绑定"],
            investigation_questions=["用户是谁？", "如何获客？", "如何分钱？", "如何退出？"],
        )

    if situation.situation_stage == "decline":
        return ContradictionAnalysis(
            primary_contradiction="继续投入冲动 vs 新证据不足",
            side_a="用户希望判断是否继续",
            side_b="结果停滞或失败信号提示继续投入风险",
            main_aspect="新证据不足",
            why_primary="如果未来投入不能改善主要瓶颈，继续投入只是放大沉没成本。",
            secondary_contradictions=["沉没成本 vs 未来边际收益"],
            resource_focus=["复盘关键指标", "收缩成本", "验证转向机会"],
            deferred_issues=["继续扩大投入", "情绪化加码"],
            investigation_questions=["核心指标连续几个周期无改善？", "失败原因是否可被用户影响？", "是否存在更优替代方向？"],
        )

    return ContradictionAnalysis(
        primary_contradiction="目标不清晰 vs 行动承诺可能过早",
        side_a="用户希望获得战略建议",
        side_b="当前事实不足以支撑高承诺决策",
        main_aspect="目标和事实不足",
        why_primary="主要矛盾不清时，行动方案容易变成忙乱而不是战略推进。",
        secondary_contradictions=["行动冲动 vs 调查不足"],
        resource_focus=["补充事实", "明确成功标准", "低成本试探"],
        deferred_issues=["高承诺投入", "长期绑定"],
        investigation_questions=["目标是什么？", "成功标准是什么？", "当前可投入资源是多少？"],
    )
