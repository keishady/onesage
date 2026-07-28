from __future__ import annotations

import json
from typing import Any, Optional

from .db import connect, init_db, now


def record_event(
    event_type: str,
    content: dict[str, Any],
    *,
    project_id: Optional[str] = None,
    decision_id: Optional[int] = None,
    actor: str = "onesage",
) -> int:
    init_db()
    conn = connect()
    cur = conn.execute(
        """
        INSERT INTO audit_events
        (event_type, project_id, decision_id, actor, content_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            event_type,
            project_id,
            decision_id,
            actor,
            json.dumps(content, ensure_ascii=False),
            now(),
        ),
    )
    conn.commit()
    event_id = int(cur.lastrowid)
    conn.close()
    return event_id


def recent_events(limit: int = 20) -> list[dict[str, Any]]:
    init_db()
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM audit_events ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    events: list[dict[str, Any]] = []
    for row in rows:
        events.append(
            {
                "id": row["id"],
                "event_type": row["event_type"],
                "project_id": row["project_id"],
                "decision_id": row["decision_id"],
                "actor": row["actor"],
                "content": json.loads(row["content_json"]),
                "created_at": row["created_at"],
            }
        )
    return events
