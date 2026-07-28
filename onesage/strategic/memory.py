from __future__ import annotations

import json

from ..db import connect, init_db, now
from .schemas import JudgmentReview, StrategicJudgment, strategic_judgment_from_dict


def save_judgment(judgment: StrategicJudgment) -> str:
    init_db()
    conn = connect()
    cur = conn.execute(
        """
        INSERT INTO strategic_judgments
        (judgment_id, question, domain, recommendation, situation_stage,
         primary_contradiction, timing, commitment_level, largest_risk,
         confidence, judgment_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            judgment.judgment_id,
            judgment.input_context.question,
            judgment.input_context.domain,
            judgment.strategic_advice.recommendation,
            judgment.situation_analysis.situation_stage,
            judgment.contradiction_analysis.primary_contradiction,
            judgment.timing_analysis.timing,
            judgment.commitment_level.level,
            judgment.strategic_risk.largest_risk,
            judgment.confidence.confidence,
            judgment.model_dump_json(),
            judgment.created_at,
        ),
    )
    judgment_id = str(cur.lastrowid)
    judgment.judgment_id = judgment_id
    conn.execute(
        """
        UPDATE strategic_judgments
        SET judgment_id = ?, judgment_json = ?
        WHERE id = ?
        """,
        (judgment_id, judgment.model_dump_json(), cur.lastrowid),
    )
    conn.commit()
    conn.close()
    return judgment_id


def load_judgment(judgment_id: str) -> StrategicJudgment:
    init_db()
    conn = connect()
    row = conn.execute(
        """
        SELECT judgment_json
        FROM strategic_judgments
        WHERE judgment_id = ? OR id = ?
        """,
        (judgment_id, _as_int_or_none(judgment_id)),
    ).fetchone()
    conn.close()
    if not row:
        raise KeyError(f"Strategic judgment not found: {judgment_id}")
    return strategic_judgment_from_dict(json.loads(row["judgment_json"]))


def save_review_and_lesson(review: JudgmentReview, judgment: StrategicJudgment) -> int:
    init_db()
    conn = connect()
    cur = conn.execute(
        """
        INSERT INTO judgment_reviews
        (judgment_id, actual_outcome, judgment_quality, primary_error_type,
         confidence_before, confidence_after, review_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review.judgment_id,
            review.actual_outcome,
            review.judgment_quality,
            review.primary_error_type,
            review.confidence_before,
            review.confidence_after,
            review.model_dump_json(),
            review.created_at,
        ),
    )
    review_id = int(cur.lastrowid)
    lesson = review.lesson_candidate.get("lesson", "")
    conn.execute(
        """
        INSERT INTO strategic_lessons
        (source_review_id, domain, lesson, scope, confidence, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review_id,
            judgment.input_context.domain,
            lesson,
            review.lesson_candidate.get("scope", judgment.input_context.domain),
            float(review.lesson_candidate.get("confidence", review.confidence_after)),
            "candidate",
            now(),
            now(),
        ),
    )
    review.lesson_candidate["source_review_id"] = review_id
    review.lesson_candidate["status"] = "candidate"
    conn.execute(
        "UPDATE judgment_reviews SET review_json = ? WHERE id = ?",
        (review.model_dump_json(), review_id),
    )
    conn.commit()
    conn.close()
    return review_id


def _as_int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
