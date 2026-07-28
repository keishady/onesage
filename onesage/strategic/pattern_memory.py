from __future__ import annotations

from collections import Counter, defaultdict
import json
import re
from typing import Any

from ..db import connect, init_db, now
from .patterns import PATTERN_STATUSES, StrategicPattern, strategic_pattern_from_dict
from .retrieval import ensure_lesson_schema, update_lesson_statuses


def sync_patterns_from_lessons() -> list[StrategicPattern]:
    init_db()
    ensure_pattern_schema()
    ensure_lesson_schema()
    update_lesson_statuses()

    rows = _load_lesson_rows()
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["lesson_status"] in {"expired", "rejected"}:
            continue
        risk_type = _row_risk_type(row)
        key = (
            row["domain"],
            _contradiction_type(row["primary_contradiction"], risk_type),
            risk_type,
            row["commitment_level"],
        )
        groups[key].append(row)

    patterns: list[StrategicPattern] = []
    for (domain, contradiction_type, risk_type, commitment_level), group in groups.items():
        if len(group) < 2:
            continue
        stage = Counter(row["situation_stage"] for row in group).most_common(1)[0][0]
        supporting_lessons = [int(row["lesson_id"]) for row in group]
        confidence = _pattern_confidence(group)
        status = _initial_status(group, confidence)
        pattern = StrategicPattern(
            pattern_id=_pattern_key(domain, stage, contradiction_type, commitment_level, risk_type),
            domain=domain,
            situation_stage=stage,
            contradiction_type=contradiction_type,
            commitment_level=commitment_level,
            risk_type=risk_type,
            supporting_lessons=supporting_lessons,
            confidence=confidence,
            applicability=_build_applicability(group, domain, contradiction_type, risk_type, commitment_level),
            counter_examples=_counter_examples(group),
            status=status,
        )
        save_pattern(pattern)
        patterns.append(pattern)
    return patterns


def save_pattern(pattern: StrategicPattern) -> str:
    if pattern.status not in PATTERN_STATUSES:
        raise ValueError(f"Invalid pattern status: {pattern.status}")
    init_db()
    ensure_pattern_schema()
    timestamp = now()
    conn = connect()
    existing = conn.execute(
        "SELECT id, created_at FROM strategic_patterns WHERE pattern_id = ?",
        (pattern.pattern_id,),
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE strategic_patterns
            SET domain = ?, situation_stage = ?, contradiction_type = ?,
                commitment_level = ?, risk_type = ?, confidence = ?, status = ?,
                pattern_json = ?, updated_at = ?
            WHERE pattern_id = ?
            """,
            (
                pattern.domain,
                pattern.situation_stage,
                pattern.contradiction_type,
                pattern.commitment_level,
                pattern.risk_type,
                pattern.confidence,
                pattern.status,
                pattern.model_dump_json(),
                timestamp,
                pattern.pattern_id,
            ),
        )
    else:
        conn.execute(
            """
            INSERT INTO strategic_patterns
            (pattern_id, domain, situation_stage, contradiction_type,
             commitment_level, risk_type, confidence, status, pattern_json,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pattern.pattern_id,
                pattern.domain,
                pattern.situation_stage,
                pattern.contradiction_type,
                pattern.commitment_level,
                pattern.risk_type,
                pattern.confidence,
                pattern.status,
                pattern.model_dump_json(),
                timestamp,
                timestamp,
            ),
        )
    conn.commit()
    conn.close()
    return pattern.pattern_id or ""


def load_pattern(pattern_id: str) -> StrategicPattern:
    init_db()
    ensure_pattern_schema()
    conn = connect()
    row = conn.execute(
        "SELECT pattern_json FROM strategic_patterns WHERE pattern_id = ? OR id = ?",
        (pattern_id, _as_int_or_none(pattern_id)),
    ).fetchone()
    conn.close()
    if not row:
        raise KeyError(f"Strategic pattern not found: {pattern_id}")
    return strategic_pattern_from_dict(json.loads(row["pattern_json"]))


def list_patterns() -> list[dict[str, Any]]:
    sync_patterns_from_lessons()
    conn = connect()
    rows = conn.execute(
        """
        SELECT id, pattern_id, domain, situation_stage, contradiction_type,
               commitment_level, risk_type, confidence, status, pattern_json,
               created_at, updated_at
        FROM strategic_patterns
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()
    return [_pattern_row_to_dict(dict(row)) for row in rows]


def search_patterns(query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    patterns = list_patterns()
    query_tokens = _tokens(query)
    scored = []
    for pattern in patterns:
        haystack = " ".join(
            [
                pattern["domain"],
                pattern["situation_stage"],
                pattern["contradiction_type"],
                pattern["commitment_level"],
                pattern["risk_type"],
                json.dumps(pattern.get("applicability", {}), ensure_ascii=False),
            ]
        )
        score = _keyword_overlap(query_tokens, _tokens(haystack))
        if query.lower() in haystack.lower():
            score += 0.4
        if score > 0:
            item = dict(pattern)
            item["similarity_score"] = round(min(1.0, score), 2)
            scored.append(item)
    scored.sort(key=lambda item: item["similarity_score"], reverse=True)
    return scored[:limit]


def update_pattern_status(pattern_id: str, status: str) -> None:
    if status not in PATTERN_STATUSES:
        raise ValueError(f"Invalid pattern status: {status}")
    pattern = load_pattern(pattern_id)
    pattern.status = status
    save_pattern(pattern)


def record_pattern_audit(
    pattern_id: str,
    *,
    judgment_id: str | None,
    matched_context: dict[str, Any],
    match_reason: list[str],
) -> int:
    init_db()
    ensure_pattern_schema()
    conn = connect()
    cur = conn.execute(
        """
        INSERT INTO pattern_audit
        (pattern_id, judgment_id, matched_context, match_reason, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            pattern_id,
            judgment_id,
            json.dumps(matched_context, ensure_ascii=False),
            json.dumps(match_reason, ensure_ascii=False),
            now(),
        ),
    )
    conn.commit()
    audit_id = int(cur.lastrowid)
    conn.close()
    return audit_id


def ensure_pattern_schema() -> None:
    init_db()
    conn = connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS strategic_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT UNIQUE,
            domain TEXT NOT NULL,
            situation_stage TEXT NOT NULL,
            contradiction_type TEXT NOT NULL,
            commitment_level TEXT NOT NULL,
            risk_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            status TEXT NOT NULL,
            pattern_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pattern_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT NOT NULL,
            judgment_id TEXT,
            matched_context TEXT NOT NULL,
            match_reason TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _load_lesson_rows() -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute(
        """
        SELECT l.id AS lesson_id, l.domain, l.lesson, l.scope,
               l.confidence AS lesson_confidence, l.status AS lesson_status,
               r.judgment_id, r.actual_outcome, r.judgment_quality, r.primary_error_type,
               j.question, j.recommendation, j.situation_stage,
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


def _pattern_confidence(rows: list[dict[str, Any]]) -> float:
    avg_lesson_confidence = sum(float(row["lesson_confidence"] or 0.0) for row in rows) / len(rows)
    quality_bonus = 0.0
    for row in rows:
        if row["judgment_quality"] == "excellent":
            quality_bonus += 0.03
        elif row["judgment_quality"] == "good":
            quality_bonus += 0.02
        elif row["judgment_quality"] == "poor":
            quality_bonus -= 0.06
    diversity_bonus = min(0.08, 0.015 * len({row["judgment_id"] for row in rows}))
    confidence = avg_lesson_confidence + quality_bonus + diversity_bonus
    return round(min(0.85, max(0.05, confidence)), 2)


def _initial_status(rows: list[dict[str, Any]], confidence: float) -> str:
    if len(rows) >= 5 and confidence >= 0.72:
        return "trusted"
    if len(rows) >= 3 and confidence >= 0.55:
        return "validated"
    return "candidate"


def _build_applicability(
    rows: list[dict[str, Any]],
    domain: str,
    contradiction_type: str,
    risk_type: str,
    commitment_level: str,
) -> dict[str, Any]:
    questions = [row["question"] for row in rows[:3]]
    return {
        "applies_when": [
            f"domain is {domain}",
            f"contradiction_type is {contradiction_type}",
            f"dominant risk is {risk_type}",
            f"commitment level is {commitment_level}",
        ],
        "does_not_apply_when": [
            "current facts conflict with the pattern",
            "primary contradiction has changed",
            "historical examples are too narrow for the current case",
        ],
        "required_facts": [
            "current goal",
            "available resources",
            "evidence for the primary contradiction",
            "stop conditions",
        ],
        "minimum_case_count": len(rows),
        "example_questions": questions,
    }


def _counter_examples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples = []
    for row in rows:
        if row["judgment_quality"] == "poor":
            examples.append(
                {
                    "lesson_id": row["lesson_id"],
                    "judgment_id": row["judgment_id"],
                    "reason": row["primary_error_type"],
                    "actual_outcome": row["actual_outcome"],
                }
            )
    return examples


def _row_risk_type(row: dict[str, Any]) -> str:
    text = " ".join(
        [
            row.get("largest_risk") or "",
            row.get("lesson") or "",
            row.get("actual_outcome") or "",
            row.get("question") or "",
            row.get("primary_contradiction") or "",
        ]
    ).lower()
    if any(term in text for term in ["sunk_cost", "sunk cost", "沉没", "已经投入", "舍不得"]):
        return "sunk_cost_risk"
    if any(term in text for term in ["opportunity_cost", "opportunity cost", "机会成本", "副业", "主业", "占用"]):
        return "opportunity_cost_risk"
    if any(term in text for term in ["resource_risk", "现金流", "辞职", "作品集", "resource"]):
        return "resource_risk"
    return row.get("largest_risk") or "direction_risk"


def _pattern_row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    pattern = json.loads(row["pattern_json"])
    row.update(
        {
            "supporting_lessons": pattern.get("supporting_lessons", []),
            "applicability": pattern.get("applicability", {}),
            "counter_examples": pattern.get("counter_examples", []),
        }
    )
    return row


def _pattern_key(
    domain: str,
    situation_stage: str,
    contradiction_type: str,
    commitment_level: str,
    risk_type: str,
) -> str:
    raw = f"{domain}:{situation_stage}:{contradiction_type}:{commitment_level}:{risk_type}"
    safe = re.sub(r"[^a-zA-Z0-9_:-]+", "-", raw)
    return f"pattern:{safe}"


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
    words = set(re.findall(r"[a-z0-9_:-]{2,}", lowered))
    terms = [
        "youtube", "content", "startup", "career", "side_project", "sunk_cost",
        "difference", "demand_validation", "resource", "opportunity_cost",
        "direction_risk", "resource_risk", "sunk_cost_risk", "opportunity_cost_risk",
        "视频", "频道", "内容", "创业", "项目", "职业", "副业", "沉没成本",
        "需求", "差异化", "机会成本",
    ]
    words.update(term for term in terms if term.lower() in lowered)
    return words


def _keyword_overlap(query_tokens: set[str], target_tokens: set[str]) -> float:
    if not query_tokens or not target_tokens:
        return 0.0
    return len(query_tokens & target_tokens) / max(len(query_tokens), 1)


def _as_int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
