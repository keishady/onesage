from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3

from .workspace import DEFAULT_WORKSPACE


def db_path() -> Path:
    DEFAULT_WORKSPACE.mkdir(parents=True, exist_ok=True)
    return DEFAULT_WORKSPACE / "onesage.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        objective TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        raw_command TEXT NOT NULL,
        decision_json TEXT NOT NULL,
        action_type TEXT NOT NULL,
        objection_required INTEGER NOT NULL,
        override_allowed INTEGER NOT NULL,
        user_override INTEGER DEFAULT 0,
        executed INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS outcomes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        decision_id INTEGER NOT NULL,
        actual_outcome TEXT NOT NULL,
        score REAL NOT NULL,
        review_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        trigger_condition TEXT NOT NULL,
        action_effect TEXT NOT NULL,
        status TEXT NOT NULL,
        evidence_count INTEGER DEFAULT 0,
        success_count INTEGER DEFAULT 0,
        failure_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS growth_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT,
        growth_type TEXT NOT NULL,
        content TEXT NOT NULL,
        source_decision_id INTEGER,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        project_id TEXT,
        decision_id INTEGER,
        actor TEXT NOT NULL,
        content_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS skill_manifests (
        name TEXT PRIMARY KEY,
        manifest_json TEXT NOT NULL,
        sandbox_json TEXT NOT NULL,
        enabled INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory_lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT,
        source_decision_id INTEGER,
        lesson TEXT NOT NULL,
        scope TEXT NOT NULL,
        confidence REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS strategic_judgments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        judgment_id TEXT UNIQUE,
        question TEXT NOT NULL,
        domain TEXT NOT NULL,
        recommendation TEXT NOT NULL,
        situation_stage TEXT NOT NULL,
        primary_contradiction TEXT NOT NULL,
        timing TEXT NOT NULL,
        commitment_level TEXT NOT NULL,
        largest_risk TEXT NOT NULL,
        confidence REAL NOT NULL,
        judgment_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS judgment_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        judgment_id TEXT NOT NULL,
        actual_outcome TEXT NOT NULL,
        judgment_quality TEXT NOT NULL,
        primary_error_type TEXT NOT NULL,
        confidence_before REAL NOT NULL,
        confidence_after REAL NOT NULL,
        review_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS strategic_lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_review_id INTEGER NOT NULL,
        domain TEXT NOT NULL,
        lesson TEXT NOT NULL,
        scope TEXT NOT NULL,
        confidence REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cur.execute("""
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
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pattern_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_id TEXT NOT NULL,
        judgment_id TEXT,
        matched_context TEXT NOT NULL,
        match_reason TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS workflows (
        name TEXT PRIMARY KEY,
        workflow_json TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"
