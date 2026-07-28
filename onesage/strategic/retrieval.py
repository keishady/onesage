from __future__ import annotations

import json
import re
from typing import Any

from ..db import connect, init_db, now
from .schemas import MemoryMatch, RelevantMemory, StrategicContext


ACTIVE_STATUSES = {"candidate", "validated", "trusted"}
IGNORED_STATUSES = {"expired", "rejected"}


def retrieve_relevant_memory(context: StrategicContext, *, limit: int = 5) -> RelevantMemory:
    init_db()
    ensure_lesson_schema()
    update_lesson_statuses()

    rows = _load_memory_rows()
    rough_stage = _rough_stage(context)
    current_tokens = _tokens(context.question)
    matches: list[MemoryMatch] = []
    for row in rows:
        if row["lesson_status"] in IGNORED_STATUSES:
            continue
        judgment_data = json.loads(row["judgment_json"])
        score, reasons = _similarity_score(context, rough_stage, current_tokens, row, judgment_data)
        if score <= 0:
            continue
        matches.append(
            MemoryMatch(
                similarity_score=score,
                lesson_id=row["lesson_id"],
                judgment_id=str(row["judgment_id"]),
                domain=row["domain"],
                situation_stage=row["situation_stage"],
                contradiction_type=_contradiction_type(row["primary_contradiction"], row["largest_risk"]),
                primary_contradiction=row["primary_contradiction"],
                commitment_level=row["commitment_level"],
                largest_risk=row["largest_risk"],
                historical_advice=row["recommendation"],
                actual_outcome=row["actual_outcome"] or "",
                lesson=row["lesson"] or "",
                lesson_status=row["lesson_status"],
                confidence=float(row["lesson_confidence"] or 0.0),
                match_reasons=reasons,
            )
        )

    matches.sort(key=lambda item: item.similarity_score, reverse=True)
    matches = matches[:limit]
    return RelevantMemory(
        matches=matches,
        reminders=_memory_reminders(matches),
        confidence_adjustment=_confidence_adjustment(matches),
        retrieval_rules=[
            "current_facts_override_memory",
            "candidate_lessons_are_reminders_only",
            "validated_or_trusted_lessons_may_adjust_confidence",
            "expired_lessons_are_excluded",
        ],
    )


def list_lessons() -> list[dict[str, Any]]:
    init_db()
    ensure_lesson_schema()
    update_lesson_statuses()
    conn = connect()
    rows = conn.execute(
        """
        SELECT l.id, l.domain, l.lesson, l.scope, l.confidence, l.status,
               l.source_review_id, r.judgment_id, l.created_at, l.updated_at
        FROM strategic_lessons l
        LEFT JOIN judgment_reviews r ON r.id = l.source_review_id
        ORDER BY l.id DESC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_lessons(query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    init_db()
    ensure_lesson_schema()
    update_lesson_statuses()
    query_tokens = _tokens(query)
    rows = _load_memory_rows()
    scored = []
    for row in rows:
        if row["lesson_status"] in IGNORED_STATUSES:
            continue
        haystack = " ".join(
            [
                row["domain"] or "",
                row["scope"] or "",
                row["lesson"] or "",
                row["question"] or "",
                row["primary_contradiction"] or "",
                row["actual_outcome"] or "",
            ]
        )
        score = _keyword_overlap(query_tokens, _tokens(haystack))
        if query.lower() in haystack.lower():
            score += 0.4
        if score > 0:
            item = {
                "id": row["lesson_id"],
                "domain": row["domain"],
                "lesson": row["lesson"],
                "scope": row["scope"],
                "confidence": row["lesson_confidence"],
                "status": row["lesson_status"],
                "source_review_id": row["source_review_id"],
                "judgment_id": row["judgment_id"],
                "question": row["question"],
            }
            item["similarity_score"] = round(min(1.0, score), 2)
            scored.append(item)
    scored.sort(key=lambda item: item["similarity_score"], reverse=True)
    return scored[:limit]


def update_lesson_statuses() -> None:
    conn = connect()
    rows = conn.execute(
        """
        SELECT l.id, l.domain, l.scope, l.status
        FROM strategic_lessons l
        """
    ).fetchall()
    groups: dict[tuple[str, str], list[Any]] = {}
    for row in rows:
        if row["status"] in {"expired", "rejected"}:
            continue
        key = (row["domain"], _scope_key(row["scope"]))
        groups.setdefault(key, []).append(row)

    timestamp = now()
    for group_rows in groups.values():
        count = len(group_rows)
        next_status = "trusted" if count >= 4 else "validated" if count >= 2 else "candidate"
        for row in group_rows:
            if _status_rank(next_status) > _status_rank(row["status"]):
                conn.execute(
                    "UPDATE strategic_lessons SET status = ?, updated_at = ? WHERE id = ?",
                    (next_status, timestamp, row["id"]),
                )
    conn.commit()
    conn.close()


def ensure_lesson_schema() -> None:
    conn = connect()
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(strategic_lessons)").fetchall()}
    if "scope" not in columns:
        conn.execute("ALTER TABLE strategic_lessons ADD COLUMN scope TEXT NOT NULL DEFAULT ''")
    if "updated_at" not in columns:
        conn.execute("ALTER TABLE strategic_lessons ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
        conn.execute("UPDATE strategic_lessons SET updated_at = created_at WHERE updated_at = ''")
    conn.commit()
    conn.close()


def _load_memory_rows() -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute(
        """
        SELECT l.id AS lesson_id, l.source_review_id, l.domain, l.lesson, l.scope,
               l.confidence AS lesson_confidence, l.status AS lesson_status,
               r.actual_outcome, r.judgment_quality, r.primary_error_type,
               j.judgment_id, j.question, j.recommendation, j.situation_stage,
               j.primary_contradiction, j.commitment_level, j.largest_risk,
               j.judgment_json
        FROM strategic_lessons l
        JOIN judgment_reviews r ON r.id = l.source_review_id
        JOIN strategic_judgments j ON j.judgment_id = r.judgment_id
        ORDER BY l.id DESC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _similarity_score(
    context: StrategicContext,
    rough_stage: str,
    current_tokens: set[str],
    row: dict[str, Any],
    judgment_data: dict[str, Any],
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if context.domain == row["domain"]:
        score += 0.28
        reasons.append("domain")
    if rough_stage != "unknown" and rough_stage == row["situation_stage"]:
        score += 0.18
        reasons.append("situation_stage")
    current_type = _context_contradiction_type(context)
    historical_type = _contradiction_type(row["primary_contradiction"], row["largest_risk"])
    if current_type != "general" and current_type == historical_type:
        score += 0.2
        reasons.append("contradiction_type")
    if _context_commitment(context) == row["commitment_level"]:
        score += 0.12
        reasons.append("commitment_level")
    if row["largest_risk"] == _context_risk_hint(context):
        score += 0.12
        reasons.append("risk")

    historical_text = " ".join(
        [
            row["question"] or "",
            row["primary_contradiction"] or "",
            row["lesson"] or "",
            row["actual_outcome"] or "",
            json.dumps(judgment_data.get("input_context", {}), ensure_ascii=False),
        ]
    )
    overlap = _keyword_overlap(current_tokens, _tokens(historical_text))
    if overlap:
        score += min(0.1, overlap)
        reasons.append("keyword_overlap")

    status = row["lesson_status"]
    if status == "trusted":
        score += 0.08
        reasons.append("trusted_lesson")
    elif status == "validated":
        score += 0.04
        reasons.append("validated_lesson")
    elif status == "candidate":
        reasons.append("candidate_reminder_only")
    return round(min(1.0, score), 2), reasons


def _memory_reminders(matches: list[MemoryMatch]) -> list[str]:
    if not matches:
        return ["No relevant strategic memory found; rely on current facts and explicit unknowns."]
    reminders = ["Current facts override historical experience."]
    for match in matches[:3]:
        if match.lesson_status == "candidate":
            reminders.append(f"Candidate lesson #{match.lesson_id} can only remind, not decide: {match.lesson}")
        else:
            reminders.append(f"{match.lesson_status} lesson #{match.lesson_id} may inform confidence: {match.lesson}")
    return reminders


def _confidence_adjustment(matches: list[MemoryMatch]) -> float:
    adjustment = 0.0
    for match in matches[:3]:
        if match.lesson_status == "trusted":
            adjustment += 0.03
        elif match.lesson_status == "validated":
            adjustment += 0.015
    return round(min(0.08, adjustment), 3)


def _rough_stage(context: StrategicContext) -> str:
    if context.history.get("decline_signals"):
        return "decline"
    if context.competition.get("signals"):
        return "competition"
    question = context.question
    if any(word in question for word in ["爆发", "风口", "增长很快", "机会窗口"]):
        return "breakout"
    return "unknown"


def _context_commitment(context: StrategicContext) -> str:
    if context.resources.get("time") == "high_commitment_signal":
        return "high"
    if context.resources.get("time") == "medium_commitment_signal":
        return "medium"
    return "low"


def _context_risk_hint(context: StrategicContext) -> str:
    if context.user_bias == "sunk_cost_pressure":
        return "sunk_cost_risk"
    if context.domain == "side_project" or any(word in context.question for word in ["主业", "副业", "机会成本", "每周"]):
        return "opportunity_cost_risk"
    if _context_commitment(context) == "high":
        return "resource_risk"
    return "direction_risk"


def _context_contradiction_type(context: StrategicContext) -> str:
    if context.user_bias == "sunk_cost_pressure":
        return "sunk_cost"
    if context.domain == "content" or any(word.lower() in context.question.lower() for word in ["youtube", "视频", "频道", "差异化"]):
        return "difference"
    if context.domain in {"career", "learning"}:
        return "resource"
    if context.domain == "side_project":
        return "opportunity_cost"
    if context.domain == "startup":
        return "demand_validation"
    return "general"


def _contradiction_type(primary_contradiction: str, largest_risk: str) -> str:
    text = primary_contradiction.lower()
    if largest_risk == "sunk_cost_risk" or any(word in text for word in ["沉没", "继续投入"]):
        return "sunk_cost"
    if largest_risk == "opportunity_cost_risk" or any(word in text for word in ["机会成本", "时间承诺"]):
        return "opportunity_cost"
    if largest_risk == "resource_risk" or any(word in text for word in ["资源", "能力", "现金流"]):
        return "resource"
    if any(word in text for word in ["差异化", "供给过剩", "difference"]):
        return "difference"
    if any(word in text for word in ["需求", "场景", "验证"]):
        return "demand_validation"
    return "general"


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    words = set(re.findall(r"[a-z0-9_]{2,}", lowered))
    chinese_terms = [
        "youtube", "视频", "频道", "内容", "竞争", "差异化", "创业", "项目", "产品",
        "用户", "需求", "转型", "职业", "辞职", "学习", "技能", "副业", "主业",
        "沉没成本", "已经投入", "继续", "停止", "增长", "机会成本", "每周",
    ]
    words.update(term for term in chinese_terms if term in lowered)
    return words


def _keyword_overlap(current_tokens: set[str], historical_tokens: set[str]) -> float:
    if not current_tokens or not historical_tokens:
        return 0.0
    overlap = current_tokens & historical_tokens
    return len(overlap) / max(len(current_tokens), 1)


def _scope_key(scope: str) -> str:
    parts = []
    for item in scope.split(";"):
        item = item.strip()
        if item.startswith("recommendation=") or item.startswith("error_type="):
            continue
        if item:
            parts.append(item)
    return ";".join(parts) if parts else scope


def _status_rank(status: str) -> int:
    return {"candidate": 1, "validated": 2, "trusted": 3, "expired": 0, "rejected": 0}.get(status, 1)
