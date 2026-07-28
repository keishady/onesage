from __future__ import annotations

from pathlib import Path
import json
import os

DEFAULT_WORKSPACE = Path(os.environ.get("ONESAGE_HOME", Path.home() / ".onesage")).expanduser()


METHOD_TEXT = """# OneSage METHOD.md

OneSage 的内核只保留两条根：

1. 《毛选》方法：没有调查就没有发言权；先分清事实、假设、未知，再抓主要矛盾。
2. 《周易》方法：先辨时位，再看动爻；进、退、守、试、止都可以是正确行动。

## 判断顺序

1. 事实是否足够。
2. 主要矛盾是否清楚。
3. 当前时位是否适合行动。
4. 风险是否可控。
5. 有没有更小、更稳的替代动作。
6. 是否需要人工确认或 override。

## 七类行动

- observe：观，继续观察。
- wait：待，等待条件。
- test：试，小样本试探。
- advance：进，推进。
- retreat：退，降低暴露。
- stop：止，停止。
- cooperate：合，借力合作。

## v0.3 强化原则

- should_act_now 必须由 onesage64gua.jsonl 的卦象 phase 与 policy 共同推导。
- L2/L3 行动默认进入确认或阻断。
- skill 不能拥有环境中的默认全权；必须声明权限并经过沙箱检查。
- outcome review 必须产生可审查的 lesson / rule candidate / memory update。
- initial_state_vector、dynamic_rules、phase_mapping 必须可从 64 卦 JSON 模板直接调用。
- Mercury / diffusion LLM 只作为低延迟执行流水线的可选模型路由，不替代安全判断。
"""


SOUL_TEXT = """# OneSage SOUL.md

你是 OneSage，一个有方法论、有执行纪律、会复盘成长的本地 Agent。

你可以参考 OpenClaw 的多入口和工具执行，也可以参考 Hermes Agent 的长期记忆和自我改进，但你的核心差异是 Method Kernel：调查、矛盾、时位、进退、复盘。

你要做到：

- 会判断，而不是盲从。
- 敢反对，但给出更小的可行动替代方案。
- 能执行，但任何执行都经过权限和审计。
- 会复盘，但所有学习都可审查、可撤回。
"""


PERMISSIONS = {
    "levels": {
        "L0_read_only": {
            "description": "Read-only actions such as reading local context, searching, summarizing.",
            "auto_execute": True,
            "confirmations_required": 0,
        },
        "L1_write_local": {
            "description": "Write local files or local database records inside the workspace.",
            "auto_execute": True,
            "confirmations_required": 0,
        },
        "L2_write_external": {
            "description": "Send messages, submit forms, edit remote systems, or publish content.",
            "auto_execute": False,
            "confirmations_required": 1,
        },
        "L3_critical": {
            "description": "Financial, destructive, shell, credential, permission, or production changes.",
            "auto_execute": False,
            "confirmations_required": 2,
            "blocked_by_default": True,
        },
    },
    "skill_policy": {
        "default_enabled": False,
        "require_manifest": True,
        "block_permissions": ["shell", "financial"],
        "confirm_permissions": ["credentials", "external_write", "browser", "network"],
    },
}


EXAMPLE_SKILL = {
    "name": "local_summary",
    "owner": "onesage",
    "version": "0.2.0",
    "description": "Example read-only skill manifest.",
    "entrypoint": "skills/local_summary.py",
    "permissions": ["read_local"],
    "allowed_domains": [],
    "filesystem_scope": ["~/.onesage/projects"],
    "update_policy": "manual",
    "provenance": "bundled",
    "enabled": False,
}


def init_workspace(path: Path = DEFAULT_WORKSPACE) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "projects").mkdir(exist_ok=True)
    (path / "skills").mkdir(exist_ok=True)
    (path / "sandbox_skills").mkdir(exist_ok=True)
    (path / "logs").mkdir(exist_ok=True)
    (path / "traces").mkdir(exist_ok=True)

    (path / "METHOD.md").write_text(METHOD_TEXT, encoding="utf-8")
    (path / "SOUL.md").write_text(SOUL_TEXT, encoding="utf-8")
    (path / "permissions.json").write_text(json.dumps(PERMISSIONS, ensure_ascii=False, indent=2), encoding="utf-8")
    example_path = path / "sandbox_skills" / "local_summary.skill.json"
    if not example_path.exists():
        example_path.write_text(json.dumps(EXAMPLE_SKILL, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
